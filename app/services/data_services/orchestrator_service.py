import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.database import SessionLocal
from app.services.llm_provider import chat_json
from app.models.schemas import ChatSession

from app.services.data_services import (
    user_service,
    resource_service,
    learning_plan_service,
    profile_service,
    knowledge_evidence_service,
    teaching_source_service,
    final_response_composer,
    generation_job_service,
    system_message_service,
    conversation_router,
    semantic_analysis_service,
    resource_policy_service,
    resource_quality_gate,
    deep_learning_resource_blueprint,
    course_scope_service,
    deep_learning_course_map_service,
    resource_artifact_type_service as artifact_types,
    video_catalog_service,
)

from app.agents.evaluation_agent import run as eval_run
from app.agents.profile_agent import run as profile_run
from app.agents.planner_agent import run as planner_run
from app.agents.resource_agent import run as resource_run
from app.agents.interactive_animation_agent import run as interactive_animation_run
from app.agents.animation_storyboard_agent import run as animation_storyboard_run


logger = logging.getLogger(__name__)

PUBLIC_PROFILE_DIMENSIONS = {
    "知识基础",
    "学习目标",
    "学习阶段",
    "知识短板",
    "认知风格",
    "媒介偏好",
    "实践能力",
    "学习节奏",
    "易错模式",
    "兴趣方向",
}

KNOWN_TOPIC_ALIASES = {
    "rnn": "RNN",
    "lstm": "LSTM",
    "transformer": "Transformer",
    "深度学习": "深度学习",
    "神经网络": "神经网络",
    "cnn": "卷积神经网络",
    "卷积神经网络": "卷积神经网络",
    "反向传播": "反向传播",
    "pytorch": "PyTorch 深度学习工程实践",
    "attention": "自注意力机制",
}


def _fallback_topic_from_message(message: str):
    text = (message or "").strip()
    compact = re.sub(r"\s+", "", text.lower())
    for alias, topic in KNOWN_TOPIC_ALIASES.items():
        if alias in compact:
            return course_scope_service.normalize_course_topic(topic)

    match = re.search(r"(?:学习|想学|了解|解释|讲讲|讲一下)([A-Za-z0-9+#.\u4e00-\u9fff]{2,30})", text)
    if match:
        return course_scope_service.normalize_course_topic(match.group(1).strip("，。！？,.!? "))
    return ""


def _pipeline_step(key: str, label: str, agent: str, status: str = "completed", detail: str = ""):
    return {
        "key": key,
        "label": label,
        "agent": agent,
        "status": status,
        "detail": detail,
    }


def _load_session_state(db, username: str, session_id: str):
    if not session_id:
        return {}
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.username == username)
        .first()
    )
    if not session:
        return {}
    try:
        state = json.loads(session.state_json or "{}")
        return state if isinstance(state, dict) else {}
    except Exception:
        return {}


def _save_session_state(db, username: str, session_id: str, **updates):
    if not session_id:
        return {}

    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.username == username)
        .first()
    )
    if not session:
        return {}

    state = _load_session_state(db, username, session_id)
    clear_keys = updates.pop("clear_keys", []) or []
    for key in clear_keys:
        state.pop(key, None)
        if key == "last_topic":
            session.last_topic = ""

    rejected_topic = updates.pop("append_rejected_topic", "")
    if rejected_topic:
        rejected_topics = state.get("rejected_topics")
        if not isinstance(rejected_topics, list):
            rejected_topics = []
        if rejected_topic not in rejected_topics:
            rejected_topics.append(str(rejected_topic)[:80])
        state["rejected_topics"] = rejected_topics[-20:]

    for key, value in updates.items():
        if value is None:
            continue
        state[key] = value

    last_topic = state.get("last_topic") or ""
    session.last_topic = str(last_topic)[:255] if last_topic else ""
    session.state_json = json.dumps(state, ensure_ascii=False)
    db.commit()
    return state


def _build_public_profile(profile):
    if not isinstance(profile, dict):
        return {}

    dimensions = profile.get("dimensions") if isinstance(profile.get("dimensions"), dict) else {}
    radar = profile.get("radar") if isinstance(profile.get("radar"), dict) else {}
    tags = profile.get("tags", [])
    if not dimensions and not radar and not tags and profile.get("hours") is None and not profile.get("updated_at"):
        return {}
    public_dimensions = {
        key: value
        for key, value in dimensions.items()
        if key in PUBLIC_PROFILE_DIMENSIONS
    }

    return {
        "tags": tags,
        "knowledge_tags": profile.get("knowledge_tags", tags),
        "hours": profile.get("hours"),
        "updated_at": profile.get("updated_at"),
        "dimensions": public_dimensions,
        "radar": radar,
    }


def build_student_response(result, trace_id: str):
    response = final_response_composer.compose_student_answer(
        intent_result={"intent": result.get("intent", "")},
        knowledge_result={"items": result.get("evidence", [])},
        profile_result=result.get("profile", {}),
        tutor_result=result.get("tutor_result") or {"content": result.get("reply", "")},
        plan_result=result.get("path"),
        resource_result=result.get("resources", []),
        resource_status=result.get("resource_status", {}),
        safety_result=result.get("safety_summary", {}),
        pipeline_steps=result.get("pipeline_steps", []),
        trace_id=trace_id,
    )
    if result.get("content_type"):
        response["message"]["content_type"] = result.get("content_type")
    if result.get("route_type"):
        response["route_type"] = result.get("route_type")
    public_profile = _build_public_profile(result.get("profile", {}))
    if public_profile:
        response["profile"] = public_profile
    return response


def _summarize_safety(resources):
    reviews = [item.get("safety_review") or {} for item in resources or []]
    reviews = [item for item in reviews if item]
    if not reviews:
        return {
            "risk_level": "待复核",
            "avg_score": 0,
            "total": 0,
            "high_risk": 0,
        }

    scores = [item.get("score", 0) for item in reviews]
    high_risk = len([item for item in reviews if item.get("risk_level") == "高风险"])
    medium_risk = len([item for item in reviews if item.get("risk_level") == "中风险"])
    risk_level = "高风险" if high_risk else ("中风险" if medium_risk else "低风险")

    return {
        "risk_level": risk_level,
        "avg_score": round(sum(scores) / len(scores)),
        "total": len(reviews),
        "high_risk": high_risk,
    }


def _normalize_structured_items(value, field):
    if not isinstance(value, list):
        raise RuntimeError(f"学习辅导结构化结果 {field} 必须是列表")

    items = []
    for index, item in enumerate(value, start=1):
        if isinstance(item, dict):
            title = str(item.get("title") or "").strip()
            detail = str(item.get("detail") or item.get("description") or "").strip()
            if not title and not detail:
                raise RuntimeError(f"学习辅导结构化结果 {field} 第 {index} 项为空")
            items.append({"title": title or detail, "detail": detail})
            continue
        if isinstance(item, str) and item.strip():
            items.append({"title": item.strip(), "detail": ""})
            continue
        raise RuntimeError(f"学习辅导结构化结果 {field} 第 {index} 项格式错误")

    return items


def _normalize_text_list(value, field):
    if not isinstance(value, list):
        raise RuntimeError(f"结构化结果 {field} 必须是列表")
    return [str(item).strip() for item in value if str(item or "").strip()]


def _validate_tutor_result(data):
    if not isinstance(data, dict):
        raise RuntimeError("学习辅导结构化结果必须是对象")

    summary = str(data.get("summary") or "").strip()
    if not summary:
        raise RuntimeError("学习辅导结构化结果缺少 summary")

    return {
        "summary": summary,
        "key_points": _normalize_structured_items(data.get("key_points"), "key_points"),
        "next_actions": _normalize_structured_items(data.get("next_actions"), "next_actions"),
        "caveats": _normalize_text_list(data.get("caveats"), "caveats"),
    }


def _validate_resource_output(data, resource_type: str = ""):
    if not isinstance(data, dict):
        raise RuntimeError("资源内容结构化结果必须是对象")

    summary = str(data.get("summary") or "").strip()
    source_notes = _normalize_text_list(data.get("source_notes"), "source_notes")
    sections = data.get("sections")

    if not summary:
        raise RuntimeError("资源内容结构化结果缺少 summary")
    if not isinstance(sections, list) or not sections:
        raise RuntimeError("资源内容结构化结果 sections 必须是非空列表")

    normalized_sections = []
    for index, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            raise RuntimeError(f"资源内容结构化结果 sections 第 {index} 项必须是对象")
        heading = str(section.get("heading") or "").strip()
        items = _normalize_text_list(section.get("items"), f"sections[{index}].items")
        if not heading:
            raise RuntimeError(f"资源内容结构化结果 sections 第 {index} 项缺少 heading")
        if not items:
            raise RuntimeError(f"资源内容结构化结果 sections 第 {index} 项 items 不能为空")
        normalized_sections.append({"heading": heading, "items": items})

    return {
        "summary": summary,
        "content": _render_resource_content(summary, normalized_sections, resource_type=resource_type),
        "source_notes": source_notes,
    }


def _render_resource_content(summary, sections, resource_type: str = ""):
    lines = [f"# {summary}", ""]
    is_course_note = deep_learning_resource_blueprint.is_course_note(resource_type)

    for section in sections:
        heading = section["heading"]
        items = section["items"]
        lines.extend([f"## {heading}", ""])

        if is_course_note:
            for item in items:
                lines.extend([str(item).strip(), ""])
            continue

        if "Mermaid" in heading or "流程图" in heading:
            lines.extend(["```mermaid", *items, "```", ""])
            continue

        if "代码" in heading:
            lines.extend(["```python", *items, "```", ""])
            continue

        lines.extend([f"- {item}" for item in items])
        lines.append("")

    return "\n".join(lines).strip()


def _json_artifact_content(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _structured_artifact_content(item, resource_output, profile_result):
    resource_type = artifact_types.normalize_artifact_type(item.get("type", ""))
    course_match = item.get("deep_learning_course_map") or item.get("ai_course_map") or {}
    topic = course_match.get("normalized_topic") or item.get("unit_title") or item.get("topic") or "深度学习知识点"
    unit_id = course_match.get("unit_id") or item.get("unit_id") or ""
    personalization_reason = item.get("personalization_reason") or "根据本轮深度学习主题、学生画像和学习目标生成。"

    if resource_type == artifact_types.VIDEO_RECOMMENDATION:
        videos = video_catalog_service.search_videos(
            unit_id=unit_id,
            topic=topic,
            profile=profile_result,
            limit=4,
        )
        first_video = videos[0] if videos else {}
        return _json_artifact_content({
            "type": "video_recommendation",
            "title": item.get("title") or f"{topic} 外部公开视频推荐卡",
            "source": first_video.get("source", "公开视频目录"),
            "source_url": first_video.get("source_url", ""),
            "platform": first_video.get("platform", first_video.get("source", "公开课程入口")),
            "knowledge_units": [unit_id] if unit_id else [],
            "recommended_segments": first_video.get("recommended_segments", []),
            "recommended_videos": videos,
            "personalization_reason": personalization_reason,
            "watch_priority": 1,
            "content_notes": ["公开视频原始链接", "推荐片段", "版权说明"],
            "copyright_note": "仅提供原始链接和学习建议，不复制、不下载、不重新分发视频内容。",
            "summary": resource_output.get("summary", ""),
        })

    if resource_type == artifact_types.PERSONALIZED_VIDEO_GUIDE:
        guide = video_catalog_service.build_personalized_video_guide(course_match, profile=profile_result)
        guide.update({
            "title": item.get("title") or f"{topic} 个性化视频观看指南",
            "personalization_reason": personalization_reason,
        })
        return _json_artifact_content(guide)

    if resource_type == artifact_types.INTERACTIVE_ANIMATION:
        dto = interactive_animation_run(unit_id=unit_id, topic=topic)
        payload = dto.output or {}
        payload.update({
            "title": item.get("title") or f"{topic} 交互动画规格",
            "personalization_reason": personalization_reason,
        })
        return _json_artifact_content(payload)

    if resource_type == artifact_types.ANIMATION_STORYBOARD:
        dto = animation_storyboard_run(topic=topic, unit_id=unit_id)
        payload = dto.output or {}
        payload.update({
            "title": item.get("title") or f"{topic} 动画分镜",
            "personalization_reason": personalization_reason,
        })
        return _json_artifact_content(payload)

    return resource_output["content"]


def _build_resource_prompt(item, profile_result, intent, evidence_prompt, teaching_sources_prompt):
    if deep_learning_resource_blueprint.is_course_note(item.get("type", "")):
        evidence_chunks = item.get("evidence_chunks") or []
        return deep_learning_resource_blueprint.build_course_note_prompt(
            plan_item=item,
            profile=profile_result or {},
            intent=intent,
            evidence_chunks=evidence_chunks,
            teaching_sources_prompt=teaching_sources_prompt,
        )

    subject_category = item.get("subject_category", "unknown")
    level = item.get("level") or profile_result.get("level") or "未确认"
    level_source = item.get("level_source") or profile_result.get("level_source") or "none"
    allow_code = bool(item.get("allow_code_content"))
    quality_constraints = "\n".join([f"- {rule}" for rule in item.get("quality_constraints", [])])
    forbidden_terms = "、".join(item.get("forbidden_terms", [])) or "无"
    feedback_sources = item.get("feedback_evidence_sources") or []
    course_map_prompt = deep_learning_course_map_service.format_course_map_for_prompt(
        item.get("deep_learning_course_map") or item.get("ai_course_map") or {}
    )
    feedback_rules = ""
    if item.get("type") == resource_policy_service.FEEDBACK_RESOURCE_TYPE:
        feedback_rules = f"""
诊断与补弱报告额外规则：
- 只能依据以下真实反馈来源生成：{'；'.join(feedback_sources) or '无'}。
- 必须在正文中写明诊断依据来自评价记录、错题描述、测验结果或本轮反馈。
- 不得用“可能薄弱点”“推测错因”伪装真实诊断。
- 如果没有真实反馈来源，应返回空的 sections 并在 source_notes 说明不能生成该报告。
"""
    return f"""
你是高校《深度学习》课程学习资源生成助手，请严格根据课程图谱和 Artifact 类型生成内容。

输出边界：
- 只输出 JSON 对象
- 不输出解释
- 不输出思考过程
- 不面向学生说话
- 不输出 Markdown 代码块包裹 JSON
- sections 必须是对象数组，items 必须是字符串数组
- items 中不要出现英文双引号、反引号或多行字符串；需要强调时使用中文括号或单引号

课程范围：{deep_learning_course_map_service.COURSE_DISPLAY_NAME}
语义类别：{subject_category}
主题：{item.get('topic')}
学生水平：{level}
水平证据：{level_source}
资源类型：{item.get('type')}
是否允许代码内容：{"true" if allow_code else "false"}
学习目标：{intent}
资源规格：{'、'.join(item.get('requirements') or [])}
《深度学习》课程图谱：
{course_map_prompt}
禁止词/禁用方向：{forbidden_terms}
质量约束：
{quality_constraints or "- 练习题必须考查主题本身，不得改写成学习规划题"}

可参考的课程资料：
{evidence_prompt}

外部教学资料候选（MOOC、教材试读/样章、教学视频优先）：
{teaching_sources_prompt}

要求：
- 内容必须适合高校《深度学习》课程学习场景
- 如果主题没有命中《深度学习》课程图谱，不得生成资源正文。
- 如果已匹配《深度学习》课程图谱，正文必须出现对应课程章节、知识单元 ID 或至少 2 个核心知识点，避免泛泛而谈。
- 课程讲解文档必须解释学习目标、前置知识、核心概念、公式/流程、例子、易错点和下一步建议。
- 思维导图必须体现章节关系、前置知识和核心概念连接。
- 练习题集必须覆盖选择题、判断题、简答题、计算题、代码补全题、实验分析题或项目任务题，并给出答案、解析、知识点、难度和常见错误。
- 拓展阅读包必须给出教材章节建议、公开课入口、官方文档、阅读顺序和阅读目标。
- PyTorch 实操案例必须写清实验目标、环境依赖、数据集说明、模型结构、完整代码、运行方式、调参任务和实验报告模板。
- 视频推荐和观看指南只提供公开视频原始链接、推荐片段、观看重点和任务，不下载、不搬运、不重托管视频。
- 交互动画规格只输出前端可渲染的结构化规格或分镜，不要求生成 MP4。
- 课程实践项目任务书必须写清项目背景、目标、数据集建议、技术路线、任务拆解、验收标准、提交物和评分 Rubric。
- 如果学生水平为“未确认”，不得写“进阶学习者”“高阶学习者”“B1/B2/C1/C2”“已经具备”等具体水平。
- 如果 Artifact 类型不是 PyTorch 实操案例、课程实践项目任务书，且是否允许代码内容为 false，不得生成代码、伪代码、函数、编程框架、算法实现。
- 练习题必须考查主题本身，不得考查“如何规划学习路径”。
- 不得虚构已引用教材、MOOC、官方链接或外部资料。
- 无依据内容可在来源说明中标注“需管理员复核”，但正文仍要保持学生可读。
- 优先把外部教学资料作为学生可用的学习入口，不要把论文作为主要学习材料
- 结合外部教学资料时必须保留来源平台、标题和链接
- 教材正文、课件包、视频内容只能引用公开入口或授权内容，不得虚构“已节选”的正文
- 避免绝对化和不可验证结论
- 多模态效果由同一主题下的讲解、导图、题集、阅读、代码实验、视频推荐、交互动画和项目任务组合呈现，最终由主题学习包聚合展示，不得再生成平级的总包型资源正文。
- 需要代码时只能放在“PyTorch 实操案例”“课程实践项目任务书”或课程讲解中的短代码示例；其他 Artifact 不要硬塞代码。
- Mermaid 和代码示例如确有必要，也必须作为普通 JSON 字符串逐条放入 items，不要使用 Markdown 围栏。
{feedback_rules}

JSON 字段：
{{
  "summary": "不超过 120 字的资源摘要",
  "sections": [
    {{
      "heading": "学习目标",
      "items": ["每一项是一句完整、可直接展示的内容，避免使用英文双引号"]
    }}
  ],
  "source_notes": ["课程资料或外部教学入口说明"]
}}
"""


def _build_resource_retry_prompt(item, error_message: str):
    headings = item.get("requirements") or ["学习目标", "核心内容", "例子", "练习", "复盘建议"]
    normalized_headings = [str(heading).strip() for heading in headings if str(heading).strip()][:8]
    section_examples = ",\n    ".join(
        f'{{"heading": "{heading}", "items": ["围绕{item.get("unit_title") or item.get("topic") or "当前主题"}补充{heading}，内容必须具体可用"]}}'
        for heading in normalized_headings
    )
    return f"""
你刚才生成的资源 JSON 不符合 schema，错误是：{error_message}

请重新生成「{item.get('type')}」资源，只返回一个合法 JSON 对象，不要输出 Markdown，不要输出解释。

硬性要求：
- summary 必须是字符串
- sections 必须是非空数组
- sections 每一项必须包含 heading 和 items
- items 必须是非空字符串数组
- source_notes 必须是非空字符串数组
- 不要使用空数组

资源主题：{item.get('unit_title') or item.get('topic')}
资源类型：{item.get('type')}
课程章节：{item.get('chapter') or item.get('chapter_id')}
知识单元 ID：{item.get('unit_id')}

JSON 形状示例：
{{
  "summary": "一句话说明这份资源能帮助学生解决什么问题",
  "sections": [
    {section_examples}
  ],
  "source_notes": ["《深度学习》课程图谱", "系统自构建课程知识库"]
}}
"""


def _request_resource_output(prompt, item):
    max_tokens = 7200 if deep_learning_resource_blueprint.is_course_note(item.get("type", "")) else 3600
    res = chat_json(
        [{"role": "user", "content": prompt}],
        required_fields=["summary", "sections", "source_notes"],
        temperature=0.1,
        max_tokens=max_tokens
    )
    if not res.get("ok"):
        raise RuntimeError(f"{item.get('type', '资源')} 内容结构化输出失败：{res.get('error', '未知错误')}")
    return _validate_resource_output(res.get("data") or {}, resource_type=item.get("type", ""))


def _build_resource_repair_prompt(item, draft, quality_result, evidence_prompt, teaching_sources_prompt):
    issues = "\n".join(f"- {issue}" for issue in quality_result.get("issues", []))
    suggestions = "\n".join(f"- {item}" for item in quality_result.get("repair_suggestions", []))
    return f"""
以下课程资源教学质量不达标。请根据问题清单重写，不要只小修小补。
必须补齐缺失章节，扩展知识点解释，增加例子、公式、练习和证据引用。

资源主题：{item.get('unit_title') or item.get('topic')}
资源类型：{item.get('type')}
课程章节：{item.get('chapter') or item.get('chapter_id')}
知识单元 ID：{item.get('unit_id')}

当前质量分：{quality_result.get('teaching_quality_score', quality_result.get('score', 0))}
问题清单：
{issues or '- 结构和内容深度不足'}

修订建议：
{suggestions or '- 按深度学习讲义蓝图重写'}

原摘要：
{draft.get('summary', '')}

原正文：
{draft.get('content', '')[:2600]}

课程证据：
{evidence_prompt}

外部教学资料候选：
{teaching_sources_prompt}

输出要求：
- 只输出 JSON 对象
- summary、sections、source_notes 字段必须完整
- 正文不少于 1800 个中文字符
- 至少 8 个二级标题
- 至少 5 个核心概念解释
- 至少 2 个具体例子
- 至少 3 道自测题并附参考答案
- 必须引用 evidence_id
"""


def repair_resource_content_with_feedback(plan_item, draft, quality_result, evidence_prompt, teaching_sources_prompt):
    prompt = _build_resource_repair_prompt(
        item=plan_item,
        draft=draft,
        quality_result=quality_result,
        evidence_prompt=evidence_prompt,
        teaching_sources_prompt=teaching_sources_prompt,
    )
    return _request_resource_output(prompt, plan_item)


def _generate_one_resource_output(item, profile_result, intent, evidence_prompt, teaching_sources_prompt):
    resource_type = artifact_types.normalize_artifact_type(item.get("type", ""))
    structured_only_types = {
        artifact_types.VIDEO_RECOMMENDATION,
        artifact_types.PERSONALIZED_VIDEO_GUIDE,
        artifact_types.INTERACTIVE_ANIMATION,
        artifact_types.ANIMATION_STORYBOARD,
    }
    if resource_type in structured_only_types:
        summary = item.get("summary") or f"{item.get('topic', '深度学习主题')} · {resource_type}"
        resource_output = {
            "summary": summary,
            "content": "",
            "source_notes": ["《深度学习》课程图谱", "公开视频目录" if "视频" in resource_type or "观看" in resource_type else "前端交互动画规格"],
        }
        return {
            "summary": summary,
            "content": _structured_artifact_content(item, resource_output, profile_result),
            "source": "；".join(resource_output["source_notes"][:3]),
        }

    item_evidence = item.get("evidence_chunks") or []
    if not item_evidence and item.get("course_id") == deep_learning_course_map_service.COURSE_ID:
        raise RuntimeError("当前知识库中该知识点证据不足，已生成知识库补充任务。")
    item_evidence_prompt = knowledge_evidence_service.format_evidence_chunks_for_prompt(item_evidence) if item_evidence else evidence_prompt
    prompt = _build_resource_prompt(
        item=item,
        profile_result=profile_result,
        intent=intent,
        evidence_prompt=item_evidence_prompt,
        teaching_sources_prompt=teaching_sources_prompt,
    )
    try:
        resource_output = _request_resource_output(prompt, item)
    except Exception as exc:
        retry_prompt = _build_resource_retry_prompt(item, str(exc))
        resource_output = _request_resource_output(retry_prompt, item)
    teaching_quality = resource_quality_gate.validate_teaching_quality(
        {**item, **resource_output, "evidence_chunks": item_evidence},
        {
            "topic": item.get("topic", ""),
            "normalized_topic": item.get("unit_title", ""),
            "unit_id": item.get("unit_id", ""),
            "resource_type": item.get("type", ""),
            "evidence_chunks": item_evidence,
            "deep_learning_course_map": item.get("deep_learning_course_map") or {},
        },
    )
    score = teaching_quality.get("teaching_quality_score", 0)
    if 60 <= score < 80:
        resource_output = repair_resource_content_with_feedback(
            plan_item=item,
            draft=resource_output,
            quality_result=teaching_quality,
            evidence_prompt=item_evidence_prompt,
            teaching_sources_prompt=teaching_sources_prompt,
        )
    return {
        "summary": resource_output["summary"],
        "content": _structured_artifact_content(item, resource_output, profile_result),
        "source": "；".join(resource_output["source_notes"][:3]),
    }


def _attach_evidence_to_resource_plan(db, resource_plan, fallback_query):
    semantic_result = resource_plan.get("semantic_result") or {}
    course_id = semantic_result.get("course_id") or deep_learning_course_map_service.COURSE_ID
    for item in resource_plan.get("resources", []):
        unit_id = item.get("unit_id") or semantic_result.get("unit_id", "")
        evidence_chunks = []
        if unit_id:
            evidence_chunks = knowledge_evidence_service.get_evidence_for_unit(
                db=db,
                course_id=course_id,
                unit_id=unit_id,
                limit=6,
            )
        if not evidence_chunks:
            evidence_chunks = knowledge_evidence_service.search_evidence(
                db=db,
                course_id=course_id,
                query=" ".join([
                    item.get("unit_title", ""),
                    item.get("topic", ""),
                    fallback_query or "",
                ]),
                limit=6,
            )
        item["evidence_chunks"] = evidence_chunks
        if evidence_chunks:
            item["evidence_refs"] = [chunk.get("evidence_id", "") for chunk in evidence_chunks if chunk.get("evidence_id")]
    return resource_plan


def _generate_resource_outputs(resource_plan, profile_result, intent, evidence_prompt, teaching_sources_prompt):
    items = resource_plan.get("resources", [])
    if not items:
        return []

    llm_outputs = [None] * len(items)
    failures = []
    max_workers = min(4, len(items))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                _generate_one_resource_output,
                item,
                profile_result,
                intent,
                evidence_prompt,
                teaching_sources_prompt,
            ): index
            for index, item in enumerate(items)
        }
        for future in as_completed(future_map):
            index = future_map[future]
            try:
                llm_outputs[index] = future.result()
            except Exception as exc:
                item = items[index]
                failures.append({
                    "title": item.get("title") or item.get("topic") or "未命名 Artifact",
                    "type": item.get("type") or "学习资源",
                    "issues": [str(exc)],
                })

    kept_items = []
    kept_outputs = []
    for index, output in enumerate(llm_outputs):
        if output is None:
            continue
        kept_items.append(items[index])
        kept_outputs.append(output)

    resource_plan["resources"] = kept_items
    resource_plan["generation_failures"] = failures
    return kept_outputs


def _preview_resource_plan(resource_plan):
    preview = []
    for item in resource_plan.get("resources", []):
        title = str(item.get("title") or item.get("topic") or "配套学习资料").strip()
        r_type = str(item.get("type") or "学习资源").strip()
        if title and r_type:
            preview.append({
                "title": title,
                "type": r_type,
                "summary": str(item.get("summary") or "").strip(),
                "status": "待审核",
                "unit_id": item.get("unit_id") or "",
            })
    return preview


def _notify_resource_generation(db, username, title, content):
    return system_message_service.create_message(
        db=db,
        username=username,
        title=title,
        content=content,
        category="资源生成",
        commit=True,
    )


def run_resource_generation_job(username, resource_plan, profile_result, intent, evidence_query, evidence_prompt, job_id: str = ""):
    db = SessionLocal()
    try:
        if job_id:
            generation_job_service.update_job(
                db,
                job_id,
                status="running",
                progress=15,
                message="正在筛选教学资料并准备生成 Artifact",
            )
            generation_job_service.add_event(
                db,
                job_id,
                event="agent_started",
                agent="TeachingSourceAgent",
                message="正在匹配教材、公开视频和官方文档入口",
                progress=20,
            )
        teaching_sources = teaching_source_service.select_teaching_sources(
            evidence_query,
            limit=8
        )
        teaching_sources_prompt = teaching_source_service.format_teaching_sources_for_prompt(
            teaching_sources,
            max_items=6
        )
        resource_plan = _attach_evidence_to_resource_plan(db, resource_plan, evidence_query)

        if job_id:
            generation_job_service.add_event(
                db,
                job_id,
                event="agent_started",
                agent="ArtifactGenerationAgents",
                message="正在生成讲解、题集、代码实验、视频指南、动画规格和项目任务",
                progress=45,
            )

        llm_outputs = _generate_resource_outputs(
            resource_plan=resource_plan,
            profile_result=profile_result,
            intent=intent,
            evidence_prompt=evidence_prompt,
            teaching_sources_prompt=teaching_sources_prompt,
        )
        if job_id:
            generation_job_service.add_event(
                db,
                job_id,
                event="agent_started",
                agent="QualityGuardAgent",
                message="正在执行课程范围、证据、版权和内容安全门禁",
                progress=75,
            )
        save_result = resource_service.save_ai_generated_resources(
            db=db,
            resource_plan=resource_plan,
            llm_outputs=llm_outputs,
            uploader="资源生成 Agent",
            applicant_username=username,
        )
        if isinstance(save_result, dict):
            resources = save_result.get("resources", [])
            skipped_resources = [
                *(save_result.get("skipped_resources", []) or []),
                *(resource_plan.get("generation_failures", []) or []),
            ]
        else:
            resources = save_result
            skipped_resources = resource_plan.get("generation_failures", []) or []
        artifact_ids = [
            item.get("artifact", {}).get("artifact_id")
            for item in resources
            if item.get("artifact", {}).get("artifact_id")
        ]
        count = len(resources)
        if count:
            if job_id:
                generation_job_service.update_job(
                    db,
                    job_id,
                    status="completed",
                    progress=100,
                    message=f"已生成 {count} 份 Artifact，等待教师审核",
                    artifact_ids=artifact_ids,
                )
                generation_job_service.add_event(
                    db,
                    job_id,
                    event="job_completed",
                    agent="RecommendationAgent",
                    message=f"已完成 {count} 份 Artifact 推荐排序，等待教师审核",
                    progress=100,
                )
            skipped_text = f"；{len(skipped_resources)} 份资源因语义门禁未入库" if skipped_resources else ""
            _notify_resource_generation(
                db,
                username,
                "配套资料已进入审核队列",
                f"本轮学习需求的 {count} 份配套 Artifact 已整理完成，正在等待管理员审核；审核通过后会进入资源工厂{skipped_text}。",
            )
        else:
            if job_id:
                generation_job_service.update_job(
                    db,
                    job_id,
                    status="failed",
                    progress=100,
                    message="未生成可提交审核的 Artifact",
                    artifact_ids=[],
                )
            _notify_resource_generation(
                db,
                username,
                "配套资料整理未完成",
                "本轮学习需求暂未生成可提交审核的配套资料，请稍后补充学习主题后再试。",
            )
    except Exception as exc:
        logger.exception("Resource generation job failed for user=%s", username)
        db.rollback()
        if job_id:
            generation_job_service.update_job(
                db,
                job_id,
                status="failed",
                progress=100,
                message=f"Artifact 生成失败：{str(exc)[:120]}",
            )
            generation_job_service.add_event(
                db,
                job_id,
                event="job_failed",
                agent="QualityGuardAgent",
                message=f"Artifact 生成失败：{str(exc)[:120]}",
                progress=100,
            )
        _notify_resource_generation(
            db,
            username,
            "配套资料整理失败",
            f"本轮配套资料整理失败，原因：{str(exc)[:120]}。你可以稍后重新发起学习需求。",
        )
    finally:
        db.close()


def _route_result(route, content=None, tutor_result=None, raw_message: str = ""):
    if route.route_type == "out_of_scope":
        content = course_scope_service.build_out_of_scope_reply(route.topic, raw_message)
    return {
        "reply": "",
        "tutor_result": tutor_result or {"content": content or route.student_reply},
        "profile": {},
        "path": None,
        "resources": [],
        "resource_status": {},
        "intent": route.route_type,
        "topic": route.topic,
        "route_type": route.route_type,
        "content_type": "conversation_reply",
        "response_message": "已回复",
        "auto_generated": False,
        "pipeline_steps": [],
        "safety_summary": _summarize_safety([]),
        "evidence": [],
        "teaching_sources": {"items": [], "meta": {"strategy": "未启用"}},
        "external_evidence": {"items": [], "meta": {"strategy": "未启用"}},
    }


def _state_for_route(route):
    if route.route_type == "acknowledgement":
        return {
            "last_route_type": route.route_type,
            "last_assistant_action": "acknowledged_pending_action",
        }
    if route.route_type in {"continue_previous", "followup"}:
        return {
            "last_topic": route.topic,
            "last_route_type": route.route_type,
            "last_assistant_action": "continued_explanation" if route.route_type == "continue_previous" else "answered_followup",
            "pending_action": "continue_learning_help",
        }
    if route.route_type == "clarification_needed":
        return {
            "last_route_type": route.route_type,
            "last_assistant_action": "asked_clarification",
            "pending_action": "awaiting_topic",
        }
    if route.route_type == "topic_rejection":
        return {
            "clear_keys": ["last_topic", "pending_action"],
            "append_rejected_topic": route.topic or "",
            "last_route_type": route.route_type,
            "last_assistant_action": "rejected_topic",
        }
    if route.route_type == "topic_switch":
        return {
            "clear_keys": ["last_topic", "pending_action"],
            "last_route_type": route.route_type,
            "last_assistant_action": "switched_topic",
        }
    if route.route_type == "casual_chat":
        return {
            "last_route_type": route.route_type,
            "last_assistant_action": "casual_chat_reply",
        }
    if route.route_type == "meta_question":
        return {
            "last_route_type": route.route_type,
            "last_assistant_action": "answered_meta_question",
        }
    if route.route_type == "out_of_scope":
        return {
            "last_route_type": route.route_type,
            "last_assistant_action": "out_of_scope_reply",
        }
    return {}


def _run_continue_topic(route, message):
    prompt = f"""
你是大学学习辅导工具，请基于上一轮主题继续展开说明。

输出边界：
- 只输出 JSON 对象
- 不输出解释
- 不输出思考过程
- 不出现“知识库依据”“Agent”“推理过程”等系统内部表达
- 不生成学习路线
- 不生成资源

上一轮主题：{route.topic}
学生追问：{message}

要求：
- 直接承接上一轮主题，补充更清楚的讲解或例子
- 如果学生只说“继续/详细点/展开说”，就按上一主题继续讲
- 不要说资料不足、需要人工复核或无法基于现有内容

JSON 字段：
{{
  "summary": "一句话承接上一主题并继续说明",
  "key_points": [
    {{"title": "展开点标题", "detail": "具体解释"}}
  ],
  "next_actions": [
    {{"title": "下一步动作", "detail": "学生可以怎么继续学"}}
  ],
  "caveats": []
}}
"""
    reply_res = chat_json(
        [{"role": "user", "content": prompt}],
        required_fields=["summary", "key_points", "next_actions", "caveats"],
        temperature=0.2,
        max_tokens=1000,
    )
    if not reply_res.get("ok"):
        raise RuntimeError(f"承接回复结构化输出失败：{reply_res.get('error', '未知错误')}")
    return _route_result(route, tutor_result=_validate_tutor_result(reply_res.get("data") or {}))


def _run_concept_question(username: str, message: str, db, route, session_id: str = ""):
    user = user_service.get_user_by_username(db, username)

    eval_result = eval_run(message)
    intent = eval_result.get("intent", "") or "概念讲解"
    semantic_result = semantic_analysis_service.analyze_learning_request(db, username, message, eval_result)
    topic = course_scope_service.normalize_course_topic(
        semantic_result.get("topic") or eval_result.get("topic", "") or route.topic or _fallback_topic_from_message(message)
    )
    semantic_result["topic"] = topic

    if not semantic_result.get("is_supported_scope", True):
        session_state = _save_session_state(
            db,
            username,
            session_id,
            last_topic="",
            last_intent=intent,
            last_route_type="out_of_scope",
            last_assistant_action="out_of_scope_reply",
            pending_action="awaiting_supported_course",
        )
        return {
            "reply": "",
            "tutor_result": {"content": course_scope_service.build_out_of_scope_reply(topic, message)},
            "profile": {},
            "path": None,
            "resources": [],
            "resource_status": {},
            "intent": intent,
            "topic": topic,
            "route_type": "out_of_scope",
            "session_state": session_state,
            "auto_generated": False,
            "pipeline_steps": [],
            "safety_summary": _summarize_safety([]),
            "evidence": [],
            "teaching_sources": {"items": [], "meta": {"strategy": "未启用"}},
            "external_evidence": {"items": [], "meta": {"strategy": "未启用"}},
            "content_type": "conversation_reply",
            "response_message": "已回复",
        }

    evidence_query = " ".join([message, topic or "", intent or ""]).strip()
    evidence = knowledge_evidence_service.search_course_evidence(db, evidence_query, limit=4)
    evidence_prompt = knowledge_evidence_service.format_evidence_for_prompt(evidence)

    profile_result = profile_run(user, message, eval_result, semantic_result=semantic_result, db=db)
    profile_update = profile_service.build_profile(
        user=user,
        message=message,
        intent=intent,
        knowledge_topic=topic,
        score=eval_result.get("score", 0),
        db=db,
        semantic_result=semantic_result,
    )

    prompt = f"""
你是学生端学习助手的内部结构化回答模块，请把概念问题整理成面向学生的学习解释素材。

输出边界：
- 只输出 JSON 对象
- 不输出解释
- 不输出思考过程
- 不出现“知识库依据”“内部链路”“Agent”“推理过程”“资料局限”“人工复核”等系统内部表达
- 不生成学习路线
- 不生成资源

学生问题：{message}
识别主题：{topic}
学科类型：{semantic_result.get("subject_category", "unknown")}
学生水平：{semantic_result.get("level", "未确认")}
水平证据：{semantic_result.get("level_source", "none")}
可参考的课程资料：
{evidence_prompt}

要求：
- 直接解释概念，语言自然清楚
- 如果课程资料不足，也不要暴露检索状态；可以用通用专业知识给出基础解释
- 不要以“基于当前课程资料”作为开头
- 若学生水平为“未确认”，不得写“进阶学习者”“高阶学习者”或具体等级
- 给出 2-4 个关键理解点和 1-3 个下一步建议
- caveats 尽量为空，除非确实需要提醒学生补充前置背景

JSON 字段：
{{
  "summary": "一句话回答学生的问题",
  "key_points": [
    {{"title": "关键点标题", "detail": "具体解释"}}
  ],
  "next_actions": [
    {{"title": "下一步动作", "detail": "学生可以怎么继续学"}}
  ],
  "caveats": []
}}
"""
    reply_res = chat_json(
        [{"role": "user", "content": prompt}],
        required_fields=["summary", "key_points", "next_actions", "caveats"],
        temperature=0.2,
        max_tokens=1200,
    )
    if not reply_res.get("ok"):
        raise RuntimeError(f"概念讲解结构化输出失败：{reply_res.get('error', '未知错误')}")

    tutor_result = _validate_tutor_result(reply_res.get("data") or {})
    updated_user = user_service.update_user_learning_profile(
        db,
        username,
        profile_update.get("tags", []),
        hours_delta=1,
        replace_tags=True,
    )
    if updated_user:
        profile_update["tags"] = updated_user["tags"]
        profile_update["hours"] = updated_user["hours"]

    session_state = _save_session_state(
        db,
        username,
        session_id,
        last_topic=topic,
        last_intent=intent,
        last_route_type=route.route_type,
        last_assistant_action="answered_concept_question",
        pending_action="continue_learning_help",
    )
    pipeline_steps = [
        _pipeline_step(
            "intent",
            "识别学习意图与课程主题",
            "IntentSemanticAgent",
            detail=f"{intent} / {topic}"
        ),
        _pipeline_step(
            "evidence",
            "检索课程知识库依据",
            "EvidenceRetrievalAgent",
            status="completed" if evidence else "requires_review",
            detail=f"命中 {len(evidence)} 条课程资料" if evidence else "未命中高置信课程资料"
        ),
        _pipeline_step(
            "profile",
            "更新动态学习画像",
            "ProfileAgent",
            detail="已融合本轮概念提问与历史学习证据"
        ),
        _pipeline_step(
            "answer",
            "生成个性化辅导回复",
            "TutorAgent",
            detail="概念讲解已生成"
        ),
    ]

    return {
        "reply": "",
        "tutor_result": tutor_result,
        "profile": profile_update,
        "path": None,
        "resources": [],
        "resource_status": {},
        "intent": intent,
        "topic": topic,
        "route_type": route.route_type,
        "session_state": session_state,
        "auto_generated": False,
        "pipeline_steps": pipeline_steps,
        "safety_summary": _summarize_safety([]),
        "evidence": evidence,
        "teaching_sources": {"items": [], "meta": {"strategy": "未启用"}},
        "external_evidence": {"items": [], "meta": {"strategy": "未启用"}},
        "content_type": "student_answer",
        "response_message": "已回复",
    }


def handle_learning_chat(username: str, message: str, db, background_tasks=None, session_id: str = ""):
    """
    🎯 多智能体学习系统主入口
    """

    # =========================
    # 1. 轮次路由：弱语义输入不进入完整多智能体链路
    # =========================
    turn_route = conversation_router.route_turn(db, username, session_id, message)

    if turn_route.route_type == "concept_question":
        return _run_concept_question(username, message, db, turn_route, session_id=session_id)

    if not turn_route.should_run_full_agents:
        if turn_route.route_type in {"continue_previous", "followup"}:
            result = _run_continue_topic(turn_route, message)
        else:
            result = _route_result(turn_route, raw_message=message)
        state_updates = _state_for_route(turn_route)
        if state_updates:
            result["session_state"] = _save_session_state(db, username, session_id, **state_updates)
        return result

    # =========================
    # 2. 获取用户信息
    # =========================
    user = user_service.get_user_by_username(db, username)

    # =========================
    # 3. 意图识别
    # =========================
    eval_result = eval_run(message)
    intent = eval_result.get("intent", "")
    semantic_result = semantic_analysis_service.analyze_learning_request(db, username, message, eval_result)
    topic = course_scope_service.normalize_course_topic(
        semantic_result.get("topic") or eval_result.get("topic", "") or _fallback_topic_from_message(message)
    )
    semantic_result["topic"] = topic

    if not semantic_result.get("is_supported_scope", True):
        session_state = _save_session_state(
            db,
            username,
            session_id,
            last_topic="",
            last_intent=intent,
            last_route_type="out_of_scope",
            last_assistant_action="out_of_scope_reply",
            pending_action="awaiting_supported_course",
        )
        return {
            "reply": "",
            "tutor_result": {"content": course_scope_service.build_out_of_scope_reply(topic, message)},
            "profile": {},
            "path": None,
            "resources": [],
            "resource_status": {},
            "intent": intent,
            "topic": topic,
            "route_type": "out_of_scope",
            "session_state": session_state,
            "auto_generated": False,
            "pipeline_steps": [],
            "safety_summary": _summarize_safety([]),
            "evidence": [],
            "teaching_sources": {"items": [], "meta": {"strategy": "未启用"}},
            "external_evidence": {"items": [], "meta": {"strategy": "未启用"}},
            "content_type": "conversation_reply",
            "response_message": "已回复",
        }
    pipeline_steps = [
        _pipeline_step(
            "intent",
            "识别学习意图与课程主题",
            "意图识别 Agent",
            detail=f"{intent} / {topic} / {semantic_result.get('subject_category', 'unknown')}"
        )
    ]

    # =========================
    # 4. 课程知识库依据检索
    # =========================
    evidence_query = " ".join([message, topic or "", intent or ""]).strip()
    evidence = knowledge_evidence_service.search_course_evidence(
        db,
        evidence_query,
        limit=4
    )
    evidence_prompt = knowledge_evidence_service.format_evidence_for_prompt(evidence)
    pipeline_steps.append(_pipeline_step(
        "evidence",
        "检索课程知识库依据",
        "知识检索 Agent",
        status="completed" if evidence else "requires_review",
        detail=f"命中 {len(evidence)} 条高置信课程资料" if evidence else "未命中高置信课程资料"
    ))

    # =========================
    # 5. 用户画像分析
    # =========================
    profile_result = profile_run(user, message, eval_result, semantic_result=semantic_result, db=db)

    profile_update = profile_service.build_profile(
        user=user,
        message=message,
        intent=intent,
        knowledge_topic=topic,
        score=eval_result.get("score", 0),
        db=db,
        semantic_result=semantic_result,
    )
    pipeline_steps.append(_pipeline_step(
        "profile",
        "更新动态学习画像",
        "画像建模 Agent",
        detail="已融合本轮对话、历史评价、规划和待办数据"
    ))

    # =========================
    # 6. 聊天回复
    # =========================
    chat_prompt = f"""
你是大学学习辅导内部工具，请把本轮学习需求整理成结构化素材。

输出边界：
- 只输出 JSON 对象
- 不输出解释
- 不输出思考过程
- 不面向学生说话
- 不出现“知识库依据”“内部链路”“Agent”“推理过程”等系统内部表达

用户问题：{message}

可参考的课程资料：
{evidence_prompt}

当前用户状态：
- 意图：{intent}
- 学科类型：{semantic_result.get("subject_category", "unknown")}
- 知识水平：{semantic_result.get("level", "未确认")}
- 水平证据：{semantic_result.get("level_source", "none")}

《深度学习》课程图谱：
{deep_learning_course_map_service.format_course_map_for_prompt(semantic_result.get("deep_learning_course_map") or semantic_result.get("ai_course_map") or {})}

要求：
- 优先依据课程资料回答，并把无法确定的内容放入 caveats
- 如果学科类型为 unknown 或主题为“未确认主题”，必须先追问具体课程/语言/知识点，不要生成学习路线或资源建议。
- 如果知识水平为“未确认”，必须自然说明“我还不知道你的{topic}基础，先按入门诊断和基础路线帮你开始”，不得写进阶、高阶或具体等级。
- 不要使用“我先分析”“下面是我的推理”这类过程性说法
- 不要使用“基于当前课程资料”“当前课程库资料不足”“资料局限”“需要人工复核”“本回答基于当前课程库状态”等后台审核措辞
- 不要输出相关性分数、置信度、内部评分、命中条数、匹配标签等系统检索指标
- 不要生成学习计划
- 不要生成资源
- 输出用于最终回答汇总的中性素材

JSON 字段：
{{
  "summary": "一句话概括本轮学习建议",
  "key_points": [
    {{"title": "关键点标题", "detail": "关键点说明"}}
  ],
  "next_actions": [
    {{"title": "下一步动作", "detail": "具体执行建议"}}
  ],
  "caveats": ["学习前提或适用边界；不要写系统资料状态"]
}}
"""

    reply_res = chat_json(
        [{"role": "user", "content": chat_prompt}],
        required_fields=["summary", "key_points", "next_actions", "caveats"],
        temperature=0.2,
        max_tokens=1200
    )
    if not reply_res.get("ok"):
        raise RuntimeError(f"学习辅导结构化输出失败：{reply_res.get('error', '未知错误')}")

    tutor_result = _validate_tutor_result(reply_res.get("data") or {})
    pipeline_steps.append(_pipeline_step(
        "answer",
        "生成个性化辅导回复",
        "学习辅导 Agent",
        status="completed",
        detail="大模型回复已生成"
    ))
    # =========================
    # 7. 是否生成学习路径和资源
    # =========================
    should_plan = (
        semantic_result.get("should_generate_resources", True)
        and (
            turn_route.should_generate_resources
            or intent in ["路径规划", "生成学习路径", "制定计划", "生成资源", "练习巩固", "实操训练"]
        )
    )

    path = None
    resources = []
    resource_status = {}
    teaching_sources = {
        "items": [],
        "meta": {
            "strategy": "课程知识点目录匹配",
        }
    }
    external_evidence = {"items": [], "meta": {"strategy": "未启用"}}

    if should_plan:
        teaching_sources = teaching_source_service.select_teaching_sources(evidence_query, limit=8)
        teaching_meta = teaching_sources.get("meta", {})
        pipeline_steps.append(_pipeline_step(
            "teaching-source",
            "自动筛选教学资料",
            "教学资源筛选 Agent",
            status="completed" if teaching_meta.get("total_count", 0) else "requires_review",
            detail=(
                f"命中 {teaching_meta.get('total_count', 0)} 条，覆盖 "
                f"{'、'.join(teaching_meta.get('material_types', [])[:4]) or '待补充资料类型'}"
            )
        ))

        # 6.1 规划路径
        plan_result = planner_run(profile_result, semantic_result=semantic_result)
        pipeline_steps.append(_pipeline_step(
            "plan",
            "规划学习路径",
            "路径规划 Agent",
            detail=f"生成 {len(plan_result.get('steps', []))} 个学习步骤"
        ))

        # 6.2 资源规划
        generation_context = resource_policy_service.build_generation_context(
            db=db,
            username=username,
            topic=topic,
            subject_category=semantic_result.get("subject_category", "unknown"),
            intent=intent,
            message=message,
        )
        resource_plan = resource_run(
            plan_result,
            profile_result,
            semantic_result=semantic_result,
            generation_context=generation_context,
        )
        pipeline_steps.append(_pipeline_step(
            "resource-plan",
            "规划配套资源类型",
            "资源设计 Agent",
            detail=f"规划 {len(resource_plan.get('resources', []))} 类个性化资源"
        ))

        # 6.3 保存路径
        path = learning_plan_service.save_generated_plan(
            db=db,
            username=username,
            title=plan_result.get("title", "学习路径"),
            path_steps=plan_result.get("steps", []),
            resources=resource_plan.get("resources", [])
        )

        # 6.4 资源内容生成进入后台任务，不阻塞聊天接口
        resources = _preview_resource_plan(resource_plan)
        job_data = generation_job_service.create_job(
            db,
            username=username,
            topic=topic,
            unit_id=semantic_result.get("unit_id", ""),
            course_id=semantic_result.get("course_id", "deep_learning"),
            message="已创建 Artifact 生成任务，资源会在审核通过后进入资源工厂",
        )
        resource_status = {
            "status": "pending_review",
            "count": len(resources),
            "message": "配套 Artifact 已生成，正在进行教师审核。审核通过后会进入资源工厂。",
            "items": resources,
            "job_id": job_data.get("job_id"),
        }
        if background_tasks is not None:
            background_tasks.add_task(
                run_resource_generation_job,
                username,
                resource_plan,
                profile_result,
                intent,
                evidence_query,
                evidence_prompt,
                job_data.get("job_id", ""),
            )
            pipeline_steps.append(_pipeline_step(
                "safety",
                "完成内容安全与防幻觉自检",
                "内容安全 Agent",
                status="pending",
                detail="资源内容生成和审核前自检已进入后台任务"
            ))
        else:
            pipeline_steps.append(_pipeline_step(
                "safety",
                "完成内容安全与防幻觉自检",
                "内容安全 Agent",
                status="requires_review",
                detail="未注入后台任务调度器，资源内容尚未生成"
            ))
    else:
        pipeline_steps.extend([
            _pipeline_step("plan", "规划学习路径", "路径规划 Agent", "skipped", "本轮意图不需要生成新路径"),
            _pipeline_step("resource-plan", "规划配套资源类型", "资源设计 Agent", "skipped", "本轮意图不需要生成新资源"),
            _pipeline_step("teaching-source", "自动筛选教学资料", "教学资源筛选 Agent", "skipped", "本轮未生成资源，暂不筛选外部教学资料"),
            _pipeline_step("safety", "完成内容安全与防幻觉自检", "内容安全 Agent", "skipped", "无新增资源需要自检"),
        ])

    # =========================
    # 8. 更新用户状态
    # =========================
    updated_user = user_service.update_user_learning_profile(
        db,
        username,
        profile_update.get("tags", []),
        hours_delta=1,
        replace_tags=True
    )

    if updated_user:
        profile_update["tags"] = updated_user["tags"]
        profile_update["hours"] = updated_user["hours"]

    # =========================
    # 9. 返回
    # =========================
    is_unknown_semantic = semantic_result.get("subject_category") == "unknown"
    public_route_type = "clarification_needed" if is_unknown_semantic else turn_route.route_type
    last_assistant_action = "asked_clarification" if is_unknown_semantic else ("generated_learning_path" if should_plan else "answered_learning_question")
    pending_action = "awaiting_topic" if is_unknown_semantic else ("resource_review_pending" if resource_status.get("status") in {"queued", "pending_review"} else "continue_learning_help")
    session_state = _save_session_state(
        db,
        username,
        session_id,
        last_topic=None if is_unknown_semantic else topic,
        last_intent=intent,
        last_route_type=public_route_type,
        last_assistant_action=last_assistant_action,
        pending_action=pending_action,
    )

    return {
        "reply": "",
        "tutor_result": tutor_result,
        "profile": profile_update,
        "path": path,
        "resources": resources,
        "resource_status": resource_status,
        "intent": intent,
        "topic": topic,
        "route_type": public_route_type,
        "session_state": session_state,
        "auto_generated": should_plan,
        "pipeline_steps": [] if is_unknown_semantic else pipeline_steps,
        "safety_summary": _summarize_safety(resources),
        "evidence": evidence,
        "teaching_sources": teaching_sources,
        "external_evidence": external_evidence,
        "content_type": "conversation_reply" if is_unknown_semantic else "student_answer",
        "response_message": "已回复" if is_unknown_semantic else None,
    }
