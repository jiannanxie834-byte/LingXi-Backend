import json
import logging
import re
import uuid
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
    agent_trace_service,
    course_scope_service,
    dsa_course_map_service,
    resource_artifact_type_service as artifact_types,
    video_catalog_service,
)

from app.agents.agent_result_dto import AgentResultDTO
from app.agents.evaluation_agent import run as eval_run
from app.agents.profile_agent import run as profile_run
from app.agents.planner_agent import run as planner_run
from app.agents.resource_agent import run as resource_run
from app.agents.interactive_animation_agent import run as interactive_animation_run
from app.agents.animation_storyboard_agent import run as animation_storyboard_run
from app.agents.course_locator_agent import run as course_locator_run
from app.agents.resource_retrieval_agent import run as resource_retrieval_run
from app.agents.package_agent import run as package_agent_run
from app.agents.quality_agent import run as quality_agent_run


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
    "数据结构": "数据结构与算法",
    "算法": "数据结构与算法",
    "复杂度": "复杂度分析",
    "数组": "数组",
    "链表": "链表",
    "栈": "栈",
    "队列": "队列",
    "递归": "递归",
    "排序": "排序算法",
    "二分": "二分查找",
    "哈希": "哈希表",
    "堆": "堆与优先队列",
    "树": "树与二叉树",
    "图": "图搜索",
    "动态规划": "动态规划",
    "dp": "动态规划",
    "字符串": "字符串匹配",
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


def _fallback_tutor_result(topic: str, message: str = ""):
    topic = str(topic or message or "当前主题").strip()
    return {
        "summary": f"我先围绕「{topic}」帮你整理学习入口，并把配套资料按你的学习情况组织起来。",
        "key_points": [
            {
                "title": "先定位核心概念",
                "detail": "先确认定义、输入输出、适用场景和常见边界条件，避免直接背模板。",
            },
            {
                "title": "再配合题目和代码",
                "detail": "概念看懂后，用小题和最小代码实验验证自己是否真的能迁移使用。",
            },
        ],
        "next_actions": [
            {
                "title": "查看个性化学习包",
                "detail": "系统会优先从课程资源库中匹配讲解、导图、练习、代码实验、补弱报告和视频指南。",
            }
        ],
        "caveats": [],
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
    is_course_note = artifact_types.normalize_artifact_type(resource_type) == artifact_types.COURSE_NOTE

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
    course_match = item.get("dsa_course_map") or item.get("ai_course_map") or {}
    topic = course_match.get("normalized_topic") or item.get("unit_title") or item.get("topic") or "数据结构与算法知识点"
    unit_id = course_match.get("unit_id") or item.get("unit_id") or ""
    personalization_reason = item.get("personalization_reason") or "根据本轮数据结构与算法主题、学生画像和学习目标生成。"

    if resource_type == artifact_types.VIDEO_RECOMMENDATION:
        videos = video_catalog_service.search_videos(
            unit_id=unit_id,
            topic=topic,
            profile=profile_result,
            chapter_id=course_match.get("chapter_id", ""),
            section_id=course_match.get("section_id", ""),
            unit_ids=course_match.get("unit_ids") or ([unit_id] if unit_id else []),
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


def _is_dsa_plan_item(item: dict) -> bool:
    course_map = item.get("dsa_course_map") or item.get("ai_course_map") or {}
    return (
        item.get("course_id") == dsa_course_map_service.COURSE_ID
        or course_map.get("course_id") == dsa_course_map_service.COURSE_ID
    )


def _dsa_item_context(item: dict):
    course_map = item.get("dsa_course_map") or item.get("ai_course_map") or {}
    unit_id = item.get("unit_id") or course_map.get("unit_id") or course_map.get("primary_unit_id") or ""
    unit = dsa_course_map_service.get_unit(unit_id) or course_map.get("unit") or {}
    chapter_id = item.get("chapter_id") or course_map.get("chapter_id") or unit.get("chapter_id") or ""
    chapter = dsa_course_map_service.CHAPTER_BY_ID.get(chapter_id, {})
    topic = (
        item.get("display_topic")
        or item.get("unit_title")
        or course_map.get("display_topic")
        or course_map.get("normalized_topic")
        or unit.get("title")
        or item.get("topic")
        or "数据结构与算法学习主题"
    )
    return {
        "course_map": course_map,
        "unit": unit,
        "unit_id": unit_id,
        "chapter": chapter,
        "chapter_id": chapter_id,
        "section_id": item.get("section_id") or course_map.get("section_id") or unit.get("section_id") or "",
        "chapter_title": chapter.get("title") or item.get("chapter_title") or course_map.get("chapter_title") or "",
        "topic": topic,
        "core_concepts": unit.get("core_concepts") or course_map.get("core_topics") or [topic],
        "prerequisites": unit.get("prerequisites") or item.get("prerequisite_units") or course_map.get("prerequisites") or [],
        "related_units": unit.get("related_units") or item.get("related_units") or course_map.get("related_units") or [],
        "common_misconceptions": unit.get("common_misconceptions") or unit.get("pitfalls") or [],
    }


def _profile_focus(profile_result: dict, item: dict):
    profile_result = profile_result or {}
    reason = item.get("personalization_reason") or "依据本轮学习主题和课程知识单元生成。"
    fragments = [reason]
    level = profile_result.get("level") or item.get("level")
    if level and level != "未确认":
        fragments.append(f"按「{level}」水平安排学习顺序")
    dimensions = profile_result.get("dimensions") if isinstance(profile_result.get("dimensions"), dict) else {}
    media = dimensions.get("媒介偏好") or profile_result.get("media_preference")
    if media:
        fragments.append(f"媒介偏好：{media}")
    weak = dimensions.get("知识短板") or profile_result.get("weakness") or profile_result.get("weak_points")
    if weak:
        fragments.append(f"重点补弱：{weak}")
    if item.get("type") == artifact_types.CODE_LAB or item.get("allow_code_content"):
        fragments.append("增加代码实验和边界样例检查")
    return "；".join(str(part) for part in fragments if str(part or "").strip())


def _evidence_summary(item: dict):
    chunks = item.get("evidence_chunks") or []
    if not chunks:
        return {
            "titles": ["数据结构与算法课程知识库"],
            "bullets": ["本资源依据课程图谱中的章节、小节和知识单元进行个性化组装。"],
            "refs": [],
        }
    titles = []
    bullets = []
    refs = []
    for chunk in chunks[:5]:
        title = str(chunk.get("title") or "课程资料").strip()
        excerpt = str(chunk.get("content_excerpt") or "").strip()
        ref = str(chunk.get("evidence_id") or "").strip()
        titles.append(title)
        if excerpt:
            bullets.append(f"{title}：{excerpt[:220]}")
        if ref:
            refs.append(ref)
    return {
        "titles": list(dict.fromkeys(titles)) or ["数据结构与算法课程知识库"],
        "bullets": bullets or ["已匹配课程知识库中的同主题资料。"],
        "refs": list(dict.fromkeys(refs)),
    }


def _source_note_lines(evidence_info):
    refs = evidence_info.get("refs") or []
    lines = ["## 来源与个性化依据", ""]
    lines.append("- 来源：数据结构与算法课程资源库、章节知识单元和已接入公开视频目录。")
    if refs:
        lines.append("- 课程依据：已根据当前主题匹配课程知识单元，内部证据已记录。")
    lines.append("- 个性化方式：优先匹配本轮主题，再结合画像中的薄弱点、媒介偏好和实践需求调整学习顺序。")
    return lines


def _dsa_course_note(item, ctx, evidence_info, personalization):
    topic = ctx["topic"]
    concepts = ctx["core_concepts"][:6]
    misconceptions = ctx["common_misconceptions"][:4] or ["只记结论，不说明适用条件", "忽略边界输入和复杂度来源"]
    lines = [
        f"# {topic} 个性化课程讲解",
        "",
        "## 学习定位",
        "",
        f"这份讲解从资源库中匹配「{topic}」相关资料，并按你的当前问题整理为先理解、再验证、最后练习的顺序。{personalization}",
        "",
        "## 核心概念",
        "",
    ]
    for concept in concepts:
        lines.append(f"- **{concept}**：先说明它解决什么问题，再观察输入输出、操作步骤和复杂度来源。")
    lines.extend(["", "## 课程依据摘要", ""])
    lines.extend([f"- {bullet}" for bullet in evidence_info["bullets"][:5]])
    lines.extend(["", "## 直观理解", ""])
    lines.append(f"学习「{topic}」时，不要把它当成孤立定义。更稳的方式是把它放回问题规模、数据组织方式和操作代价中观察：输入是什么、允许做哪些操作、每一步会访问多少元素、是否需要额外空间。")
    lines.extend(["", "## 例子", ""])
    lines.append(f"例子 1：如果题目要求你说明「{topic}」的效率，不要只写 O(1) 或 O(n)，还要指出是哪一个操作、在哪一种数据组织方式下成立。")
    lines.append(f"例子 2：如果题目要求你实现「{topic}」，先写最小输入、空输入和边界输入，再补普通样例。")
    lines.extend(["", "## 常见误区", ""])
    lines.extend([f"- {item}" for item in misconceptions])
    lines.extend(["", "## 小结", ""])
    lines.extend([
        f"学完「{topic}」后，你应该能把它解决的问题、关键操作、边界条件和复杂度来源串成一条完整解释。",
        "如果还只能背关键词，说明需要回到核心概念和例子部分重新梳理。",
    ])
    lines.extend(["", "## 下一步建议", ""])
    lines.extend([
        "- 先看本包的思维导图，确认概念关系。",
        "- 再做练习题集，重点检查边界条件和复杂度解释。",
        "- 如果涉及实现，完成代码实验中的最小函数和测试样例。",
    ])
    lines.extend(["", *_source_note_lines(evidence_info)])
    return "\n".join(lines)


def _dsa_mind_map(item, ctx, evidence_info, personalization):
    topic = ctx["topic"]
    concepts = ctx["core_concepts"][:5] or [topic]
    prerequisites = ctx["prerequisites"][:3] or ["问题规模", "基本操作", "复杂度分析"]
    related = ctx["related_units"][:3] or ["题型迁移", "边界条件", "代码验证"]
    mistakes = ctx["common_misconceptions"][:3] or ["混淆定义与实现", "忽略边界条件", "只背复杂度结论"]
    lines = [
        "mindmap",
        f"  root(({topic}))",
        "    学习定位",
        f"      {ctx['chapter_title'] or '数据结构与算法'}",
        "      个性化资源库匹配",
        "    前置知识",
        *[f"      {item}" for item in prerequisites],
        "    核心概念",
        *[f"      {item}" for item in concepts],
        "    易错点",
        *[f"      {item}" for item in mistakes],
        "    练习路径",
        "      概念题",
        "      边界样例",
        "      代码实验",
        "    拓展关联",
        *[f"      {item}" for item in related],
    ]
    return "\n".join(lines)


def _dsa_exercise_set(item, ctx, evidence_info, personalization):
    topic = ctx["topic"]
    concepts = ctx["core_concepts"][:4] or [topic]
    lines = [
        f"# {topic} 个性化练习题集",
        "",
        f"适用对象：{personalization}",
        "",
    ]
    question_specs = [
        ("选择题", f"关于「{topic}」的适用场景，下列哪一项最能体现它要解决的核心问题？", "选择能同时说明输入、输出和操作代价的选项。"),
        ("判断题", f"只要记住「{topic}」的结论，就可以跳过边界样例验证。", "错误。算法学习必须用边界样例检验理解。"),
        ("简答题", f"用 3 句话解释「{topic}」的核心思想。", "应包含问题目标、关键操作和复杂度来源。"),
        ("计算题", f"给定一个规模为 n 的输入，分析「{topic}」相关操作的时间复杂度。", "先数循环或递归层数，再说明每层成本。"),
        ("代码理解题", f"阅读一段实现「{topic}」的伪代码，指出终止条件或边界判断。", "重点检查空输入、单元素和左右边界。"),
        ("实验分析题", f"设计 3 组测试样例验证「{topic}」的正确性。", "至少包含普通样例、边界样例和异常/极端样例。"),
    ]
    for index, (q_type, question, answer) in enumerate(question_specs, start=1):
        concept = concepts[(index - 1) % len(concepts)]
        lines.extend([
            f"### 题目 {index}：{q_type}",
            "",
            f"题干：{question}",
            "",
            f"知识点：{concept}",
            "",
            f"答案：{answer}",
            "",
            "解析：不要只给结论，要能说明每一步为什么成立，以及它和输入规模、数据组织方式之间的关系。",
            "",
            "常见错误：忽略边界条件，或者把某一种实现方式误认为该概念的全部。",
            "",
        ])
    lines.extend(_source_note_lines(evidence_info))
    return "\n".join(lines)


def _dsa_code_lab(item, ctx, evidence_info, personalization):
    topic = ctx["topic"]
    safe_name = re.sub(r"[^a-zA-Z0-9_]+", "_", ctx["unit_id"] or "dsa_task").strip("_") or "dsa_task"
    return "\n".join([
        f"# {topic} 代码实验",
        "",
        f"实验目标：用最小可运行程序验证「{topic}」的输入、输出、边界条件和复杂度表现。",
        "",
        "## 学习定位",
        "",
        f"这不是让你直接复制答案，而是把「{topic}」拆成可观察的程序行为：先确认输入规模，再写出核心操作，最后用边界样例证明实现没有遗漏。完成实验后，你应该能解释每一行关键代码和复杂度之间的关系。",
        "",
        "## 环境依赖",
        "",
        "- Python 3.10+",
        "- 无第三方依赖，方便在本地或在线评测环境运行。",
        "",
        "## 算法流程",
        "",
        f"1. 明确「{topic}」对应的问题输入和期望输出。",
        "2. 写出最小可行逻辑，再逐步补充边界处理。",
        "3. 用普通样例、空输入样例、单元素样例和极端规模样例验证。",
        "4. 记录每一步访问了多少元素，从而得到时间复杂度和空间复杂度。",
        "",
        "## 完整代码",
        "",
        "```python",
        f"def solve_{safe_name}(data):",
        "    \"\"\"根据本节主题补全核心逻辑，并保留边界样例。\"\"\"",
        "    if data is None:",
        "        return None",
        "    # TODO: 根据课程讲解补全算法步骤",
        "    return data",
        "",
        "def run_tests():",
        "    cases = [",
        "        [],",
        "        [1],",
        "        [3, 1, 2],",
        "    ]",
        "    for case in cases:",
        f"        print(case, '->', solve_{safe_name}(case))",
        "",
        "if __name__ == '__main__':",
        "    run_tests()",
        "```",
        "",
        "## 运行命令",
        "",
        "```bash",
        f"python {safe_name}.py",
        "```",
        "",
        "## 学生任务",
        "",
        f"- 任务 1：补全 `solve_{safe_name}` 的核心逻辑。",
        "- 任务 2：新增 3 个边界样例，并说明预期输出。",
        "- 任务 3：记录最坏情况下的时间复杂度和空间复杂度。",
        "- 任务 4：写一段 100 字以内的反思，说明你最容易漏掉哪个边界条件。",
        "",
        "## 复杂度记录",
        "",
        "- 时间复杂度：先根据循环、递归层数或数据访问次数写出推导过程，再写结论。",
        "- 空间复杂度：记录是否使用额外数组、栈、队列、哈希表或递归调用栈。",
        "- 边界条件：空输入、单元素、重复元素、极端有序或极端无序输入都要单独验证。",
        "",
        "## 常见报错",
        "",
        "- 空输入没有提前处理，导致下标越界。",
        "- 循环边界多一位或少一位。",
        "- 只验证普通样例，没有验证极端规模。",
        "",
        "## 实验报告",
        "",
        f"- 写明你对「{topic}」的理解、关键代码、测试样例、复杂度分析和仍然不确定的问题。",
        "",
        *_source_note_lines(evidence_info),
    ])


def _dsa_remediation_report(item, ctx, evidence_info, personalization):
    topic = ctx["topic"]
    weak_points = ctx["common_misconceptions"][:4] or [
        "概念定义与应用场景没有对应起来",
        "边界条件检查不足",
        "复杂度分析只背结论，没有解释来源",
    ]
    lines = [
        f"# {topic} 诊断与补弱报告",
        "",
        f"个性化依据：{personalization}",
        "",
        "## 薄弱点",
        "",
        *[f"- {point}" for point in weak_points],
        "",
        "## 修复建议",
        "",
        "- 用一张图整理定义、输入输出、操作流程和复杂度。",
        "- 做 3 道不同边界条件的题，写出错误原因。",
        "- 用代码实验验证最小样例、边界样例和极端样例。",
        "",
        "## 下一步学习任务",
        "",
        f"1. 阅读「{topic}」课程讲解文档。",
        "2. 完成练习题集中前 4 题，并核对解析。",
        "3. 若仍然不稳定，先补前置知识，再回到本主题。",
        "",
        *_source_note_lines(evidence_info),
    ]
    return "\n".join(lines)


def _dsa_video_guide(item, ctx, evidence_info, personalization):
    topic = ctx["topic"]
    videos = video_catalog_service.search_videos(
        unit_id=ctx["unit_id"],
        topic=topic,
        profile=item.get("_profile_result") or {},
        chapter_id=ctx.get("chapter_id", ""),
        section_id=ctx.get("section_id", ""),
        unit_ids=[ctx["unit_id"]] if ctx.get("unit_id") else [],
        limit=3,
    )
    lines = [
        f"# {topic} 个性化视频观看指南",
        "",
        f"个性化依据：{personalization}",
        "",
        "## 观看/阅读前准备",
        "",
        f"- 先浏览本包的思维导图，确认「{topic}」和前置知识的关系。",
        "- 准备记录 3 个问题：概念是什么、为什么这样做、边界在哪里。",
        "",
        "## 观看/阅读中关注点",
        "",
        "- 重点看输入输出如何变化。",
        "- 暂停记录关键步骤，不要只跟着视频抄代码。",
        "- 遇到公式或复杂度时，写出它来自哪一层循环或递归。",
        "",
        "## 推荐公开视频入口",
        "",
    ]
    if videos:
        for video in videos:
            lines.append(f"- {video.get('title', '公开视频')}｜{video.get('platform', 'Bilibili')}｜{video.get('source_url', '')}")
    else:
        lines.append("- 当前小节暂无精确匹配视频，只保留课程资源库讲解、导图、练习和代码实验。")
    lines.extend([
        "",
        "## 观看/阅读后任务",
        "",
        "- 合上视频后复述核心流程。",
        "- 做练习题集中的 2 道题，检查是否能独立完成。",
        "- 若涉及代码，运行代码实验并记录边界样例。",
        "",
        "## 版权说明",
        "",
        "- 本系统只提供公开视频原始链接和学习建议，不复制、不下载、不重新分发视频内容。",
        "",
        *_source_note_lines(evidence_info),
    ])
    return "\n".join(lines)


def _generate_dsa_resource_from_library(item, profile_result, intent):
    resource_type = artifact_types.normalize_artifact_type(item.get("type", ""))
    ctx = _dsa_item_context(item)
    evidence_info = _evidence_summary(item)
    personalization = _profile_focus(profile_result, item)
    builders = {
        artifact_types.COURSE_NOTE: _dsa_course_note,
        artifact_types.MIND_MAP: _dsa_mind_map,
        artifact_types.EXERCISE_SET: _dsa_exercise_set,
        artifact_types.CODE_LAB: _dsa_code_lab,
        artifact_types.DIAGNOSTIC_REPORT: _dsa_remediation_report,
        artifact_types.PERSONALIZED_VIDEO_GUIDE: _dsa_video_guide,
    }
    builder = builders.get(resource_type, _dsa_course_note)
    item = {**item, "_profile_result": profile_result or {}}
    content = builder(item, ctx, evidence_info, personalization)
    summary = item.get("summary") or f"从课程资源库匹配「{ctx['topic']}」并结合画像生成的{resource_type}。"
    source_titles = evidence_info.get("titles") or ["数据结构与算法课程资源库"]
    return {
        "summary": summary,
        "content": content,
        "source": "；".join(source_titles[:3]),
    }


def _build_resource_prompt(item, profile_result, intent, evidence_prompt, teaching_sources_prompt):
    subject_category = item.get("subject_category", "unknown")
    level = item.get("level") or profile_result.get("level") or "未确认"
    level_source = item.get("level_source") or profile_result.get("level_source") or "none"
    allow_code = bool(item.get("allow_code_content"))
    quality_constraints = "\n".join([f"- {rule}" for rule in item.get("quality_constraints", [])])
    forbidden_terms = "、".join(item.get("forbidden_terms", [])) or "无"
    course_map = item.get("dsa_course_map") or item.get("ai_course_map") or {}
    course_map_prompt = json.dumps({
        "course": dsa_course_map_service.COURSE_DISPLAY_NAME,
        "chapter": course_map.get("chapter_title") or course_map.get("chapter") or item.get("chapter_title"),
        "unit": course_map.get("display_topic") or course_map.get("normalized_topic") or item.get("unit_title"),
        "unit_id": course_map.get("unit_id") or item.get("unit_id"),
    }, ensure_ascii=False)
    return f"""
你是高校《数据结构与算法》课程学习资源生成助手，请严格根据课程图谱和 Artifact 类型生成内容。

输出边界：
- 只输出 JSON 对象
- 不输出解释
- 不输出思考过程
- 不面向学生说话
- 不输出 Markdown 代码块包裹 JSON
- sections 必须是对象数组，items 必须是字符串数组
- items 中不要出现英文双引号、反引号或多行字符串；需要强调时使用中文括号或单引号

课程范围：{dsa_course_map_service.COURSE_DISPLAY_NAME}
语义类别：{subject_category}
主题：{item.get('topic')}
学生水平：{level}
水平证据：{level_source}
资源类型：{item.get('type')}
是否允许代码内容：{"true" if allow_code else "false"}
学习目标：{intent}
资源规格：{'、'.join(item.get('requirements') or [])}
《数据结构与算法》课程图谱：
{course_map_prompt}
禁止词/禁用方向：{forbidden_terms}
质量约束：
{quality_constraints or "- 练习题必须考查主题本身，不得改写成学习规划题"}

可参考的课程资料：
{evidence_prompt}

外部教学资料候选（MOOC、教材试读/样章、教学视频优先）：
{teaching_sources_prompt}

要求：
- 内容必须适合高校《数据结构与算法》课程学习场景
- 如果主题没有命中《数据结构与算法》课程图谱，不得生成资源正文。
- 如果已匹配《数据结构与算法》课程图谱，正文必须出现对应课程章节、知识单元 ID 或至少 2 个核心知识点，避免泛泛而谈。
- 课程讲解文档必须解释学习目标、前置知识、核心概念、公式/流程、例子、易错点和下一步建议。
- 思维导图必须体现章节关系、前置知识和核心概念连接。
- 练习题集必须覆盖选择题、判断题、简答题、计算题、代码补全题、实验分析题或项目任务题，并给出答案、解析、知识点、难度和常见错误。
- 拓展阅读包必须给出教材章节建议、公开课入口、官方文档、阅读顺序和阅读目标。
- 代码实验必须写清实验目标、环境依赖、输入输出样例、完整代码、运行方式、复杂度记录、调试任务和实验报告模板。
- 视频推荐和观看指南只提供公开视频原始链接、推荐片段、观看重点和任务，不下载、不搬运、不重托管视频。
- 交互动画规格只输出前端可渲染的结构化规格或分镜，不要求生成 MP4。
- 课程实践项目任务书必须写清项目背景、目标、数据集建议、技术路线、任务拆解、验收标准、提交物和评分 Rubric。
- 如果学生水平为“未确认”，不得写“进阶学习者”“高阶学习者”“B1/B2/C1/C2”“已经具备”等具体水平。
- 如果 Artifact 类型不是代码实验、算法项目任务书，且是否允许代码内容为 false，不得生成代码、伪代码、函数或算法实现。
- 练习题必须考查主题本身，不得考查“如何规划学习路径”。
- 不得虚构已引用教材、MOOC、官方链接或外部资料。
- 无依据内容可在来源说明中标注“需管理员复核”，但正文仍要保持学生可读。
- 优先把外部教学资料作为学生可用的学习入口，不要把论文作为主要学习材料
- 结合外部教学资料时必须保留来源平台、标题和链接
- 教材正文、课件包、视频内容只能引用公开入口或授权内容，不得虚构“已节选”的正文
- 避免绝对化和不可验证结论
- 多模态效果由同一主题下的讲解、导图、题集、阅读、代码实验、视频推荐、交互动画和项目任务组合呈现，最终由主题学习包聚合展示，不得再生成平级的总包型资源正文。
- 需要代码时只能放在“代码实验”“算法项目任务书”或课程讲解中的短代码示例；其他 Artifact 不要硬塞代码。
- Mermaid 和代码示例如确有必要，也必须作为普通 JSON 字符串逐条放入 items，不要使用 Markdown 围栏。

JSON 字段：
{{
  "summary": "不超过 120 字的资源摘要",
  "sections": [
    {{
      "heading": "学习目标",
      "items": ["每一项是一句完整、可直接展示的内容，避免使用英文双引号"]
    }}
  ],
  "source_notes": ["数据结构与算法课程资料或外部教学入口说明"]
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
  "source_notes": ["《数据结构与算法》课程图谱", "系统自构建课程知识库"]
}}
"""


def _request_resource_output(prompt, item):
    max_tokens = 7200 if artifact_types.normalize_artifact_type(item.get("type", "")) == artifact_types.COURSE_NOTE else 3600
    res = chat_json(
        [{"role": "user", "content": prompt}],
        required_fields=["summary", "sections", "source_notes"],
        temperature=0.1,
        max_tokens=max_tokens
    )
    if not res.get("ok"):
        raise RuntimeError(f"{item.get('type', '资源')} 内容结构化输出失败：{res.get('error', '未知错误')}")
    return _validate_resource_output(res.get("data") or {}, resource_type=item.get("type", ""))


def _public_generation_message(success_count: int, failed_count: int) -> str:
    if success_count > 0 and failed_count <= 0:
        return f"已为你生成 {success_count} 类个性化学习资源。"
    if success_count > 0:
        return f"已为你生成 {success_count} 类个性化学习资源，另外 {failed_count} 类生成失败，可稍后重试。"
    return "学习包生成失败，请稍后重试，或尝试输入更具体的问题，例如“我不懂动态规划状态转移”。"


def _build_resource_repair_prompt(item, draft, quality_result, evidence_prompt, teaching_sources_prompt):
    issues = "\n".join(f"- {issue}" for issue in quality_result.get("issues", []))
    suggestions = "\n".join(f"- {item}" for item in quality_result.get("repair_suggestions", []))
    resource_type = artifact_types.normalize_artifact_type(item.get("type", ""))
    course_note_requirements = """
- 课程讲解文档只负责把概念讲清楚，不生成成套练习题。
- 正文不少于 1200 个中文字符。
- 至少包含：学习定位、核心概念、关键流程、例子、常见误区、小结、下一步建议。
- 例子用于解释概念，不要写成“题目/答案/解析”的练习题格式。
"""
    generic_requirements = """
- 正文不少于 1800 个中文字符
- 至少 8 个二级标题
- 至少 5 个核心概念解释
- 至少 2 个具体例子
- 至少 3 道自测题并附参考答案
- 必须引用 evidence_id
"""
    type_requirements = course_note_requirements if resource_type == artifact_types.COURSE_NOTE else generic_requirements
    return f"""
以下课程资源教学质量不达标。请根据问题清单重写，不要只小修小补。
必须补齐缺失章节，扩展知识点解释，增加例子、公式/流程和证据引用。

资源主题：{item.get('unit_title') or item.get('topic')}
资源类型：{item.get('type')}
课程章节：{item.get('chapter') or item.get('chapter_id')}
知识单元 ID：{item.get('unit_id')}

当前质量分：{quality_result.get('teaching_quality_score', quality_result.get('score', 0))}
问题清单：
{issues or '- 结构和内容深度不足'}

修订建议：
{suggestions or '- 按数据结构与算法讲义结构重写'}

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
{type_requirements}
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
    if _is_dsa_plan_item(item):
        return _generate_dsa_resource_from_library(item, profile_result, intent)

    resource_type = artifact_types.normalize_artifact_type(item.get("type", ""))
    structured_only_types = {
        artifact_types.VIDEO_RECOMMENDATION,
        artifact_types.PERSONALIZED_VIDEO_GUIDE,
        artifact_types.INTERACTIVE_ANIMATION,
        artifact_types.ANIMATION_STORYBOARD,
    }
    if resource_type in structured_only_types:
        summary = item.get("summary") or f"{item.get('topic', '数据结构与算法主题')} · {resource_type}"
        resource_output = {
            "summary": summary,
            "content": "",
            "source_notes": ["《数据结构与算法》课程图谱", "公开视频目录" if "视频" in resource_type or "观看" in resource_type else "前端交互动画规格"],
        }
        return {
            "summary": summary,
            "content": _structured_artifact_content(item, resource_output, profile_result),
            "source": "；".join(resource_output["source_notes"][:3]),
        }

    item_evidence = item.get("evidence_chunks") or []
    if not item_evidence and item.get("course_id") == dsa_course_map_service.COURSE_ID:
        raise RuntimeError("当前知识库中该知识点证据不足，已生成知识库补充任务。")
    if item.get("course_id") and item.get("course_id") != dsa_course_map_service.COURSE_ID:
        raise RuntimeError("当前系统主线仅支持《数据结构与算法》课程资源生成。")
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
            "dsa_course_map": item.get("dsa_course_map") or item.get("ai_course_map") or {},
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
    course_id = semantic_result.get("course_id") or dsa_course_map_service.COURSE_ID
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

    if all(_is_dsa_plan_item(item) for item in items):
        return _generate_dsa_package_outputs(resource_plan, profile_result, intent)

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


def _profile_agent_trace(profile_result: dict, intent: str) -> AgentResultDTO:
    profile_result = profile_result or {}
    dimensions = profile_result.get("dimensions") if isinstance(profile_result.get("dimensions"), dict) else {}
    return AgentResultDTO(
        agent_name="ProfileAgent",
        input_summary=profile_result.get("knowledge_topic") or profile_result.get("topic") or "当前学生画像",
        output={
            "level": profile_result.get("level") or "未确认",
            "intent": intent or profile_result.get("intent") or "",
            "preference": dimensions.get("媒介偏好") or profile_result.get("media_preference") or "未确认",
            "weakness": dimensions.get("知识短板") or profile_result.get("weakness") or "待进一步诊断",
        },
        quality_score=1.0,
    )


def _intent_agent_trace(resource_plan: dict, intent: str) -> AgentResultDTO:
    semantic_result = resource_plan.get("semantic_result") or {}
    return AgentResultDTO(
        agent_name="IntentAgent",
        input_summary=semantic_result.get("topic") or semantic_result.get("display_topic") or "学习需求",
        output={
            "intent": intent or semantic_result.get("learning_need_type") or "综合学习",
            "topic": semantic_result.get("display_topic") or semantic_result.get("topic") or "",
            "resource_goal": "生成 6 类个性化学习包",
        },
        quality_score=1.0,
    )


def _generate_dsa_package_outputs(resource_plan, profile_result, intent):
    items = resource_plan.get("resources", [])
    semantic_result = resource_plan.get("semantic_result") or {}
    generation_context = resource_plan.get("generation_context") or {}

    intent_result = _intent_agent_trace(resource_plan, intent)
    locator_result = course_locator_run(semantic_result, generation_context)
    location = locator_result.output or {}
    profile_result_dto = _profile_agent_trace(profile_result, intent)
    retrieval_result = resource_retrieval_run(location)
    package_result = package_agent_run(
        resources=items,
        location=location,
        profile=profile_result or {},
        retrieval=retrieval_result.get("retrieval") or {},
    )
    quality_result = quality_agent_run(package_result.get("outputs") or [])

    unit_ids = location.get("unit_ids") or []
    primary_unit_id = unit_ids[0] if unit_ids else ""
    for item in items:
        item["course_id"] = dsa_course_map_service.COURSE_ID
        item["chapter_id"] = location.get("chapter_id") or item.get("chapter_id") or ""
        item["section_id"] = location.get("section_id") or item.get("section_id") or ""
        item["unit_id"] = item.get("unit_id") or primary_unit_id
        item["unit_ids"] = unit_ids or item.get("unit_ids") or ([primary_unit_id] if primary_unit_id else [])
        item["evidence_refs"] = location.get("evidence_refs") or unit_ids
        item["student_question"] = semantic_result.get("message") or generation_context.get("message") or item.get("student_question") or ""
        item["agent_name"] = "PersonalizedGenerationAgent"

    resource_plan["agent_results"] = [
        intent_result,
        locator_result,
        profile_result_dto,
        retrieval_result["dto"],
        package_result["dto"],
        quality_result["dto"],
    ]
    resource_plan["resources"] = items
    resource_plan["generation_failures"] = []
    return quality_result.get("outputs") or []


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


def run_resource_generation_job(username, resource_plan, profile_result, intent, evidence_query, evidence_prompt, job_id: str = "", plan_title: str = ""):
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
                agent="ResourceGroundingAgent / PersonalizedGenerationAgent",
                message="正在读取课程库依据并逐类生成个性化 ResourceArtifact",
                progress=45,
            )

        llm_outputs = _generate_resource_outputs(
            resource_plan=resource_plan,
            profile_result=profile_result,
            intent=intent,
            evidence_prompt=evidence_prompt,
            teaching_sources_prompt=teaching_sources_prompt,
        )
        trace_id = job_id or f"resource_trace_{uuid.uuid4().hex[:16]}"
        agent_results = resource_plan.get("agent_results") or []
        if agent_results:
            for plan_item in resource_plan.get("resources", []):
                plan_item["agent_trace_id"] = trace_id
            agent_trace_service.save_agent_results(
                db,
                trace_id=trace_id,
                username=username,
                results=agent_results,
            )
        if job_id:
            generation_job_service.add_event(
                db,
                job_id,
                event="agent_started",
                agent="QualityAgent",
                message="正在执行可读性、资源缺失和学生端字段检查",
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
        failed_count = len(skipped_resources)
        public_message = _public_generation_message(count, failed_count)
        if count:
            learning_plan_service.attach_artifacts_to_plan(
                db=db,
                username=username,
                plan_title=plan_title,
                resources=resources,
            )
            if job_id:
                job_status = "partial_success" if failed_count else "completed"
                generation_job_service.update_job(
                    db,
                    job_id,
                    status=job_status,
                    progress=100,
                    message=public_message,
                    artifact_ids=artifact_ids,
                )
                generation_job_service.add_event(
                    db,
                    job_id,
                    event="job_partial_success" if failed_count else "job_completed",
                    agent="RecommendationAgent",
                    message=public_message,
                    progress=100,
                )
            _notify_resource_generation(
                db,
                username,
                "配套资料已进入审核队列",
                f"{public_message} 已整理完成的资源正在等待管理员审核；审核通过后会进入资源工厂。",
            )
        else:
            if job_id:
                generation_job_service.update_job(
                    db,
                    job_id,
                    status="failed",
                    progress=100,
                    message=public_message,
                    artifact_ids=[],
                )
            _notify_resource_generation(
                db,
                username,
                "配套资料整理未完成",
                public_message,
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
                message=_public_generation_message(0, 1),
            )
            generation_job_service.add_event(
                db,
                job_id,
                event="job_failed",
                agent="QualityGuardAgent",
                message=_public_generation_message(0, 1),
                progress=100,
            )
        _notify_resource_generation(
            db,
            username,
            "配套资料整理失败",
            _public_generation_message(0, 1),
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
        logger.warning("Continue-topic JSON failed: %s", reply_res.get("error"))
        return _route_result(route, tutor_result=_fallback_tutor_result(route.topic, message))
    try:
        tutor_result = _validate_tutor_result(reply_res.get("data") or {})
    except Exception as exc:
        logger.warning("Continue-topic validation failed: %s", exc)
        tutor_result = _fallback_tutor_result(route.topic, message)
    return _route_result(route, tutor_result=tutor_result)


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
        logger.warning("Concept answer JSON failed: %s", reply_res.get("error"))
        tutor_result = _fallback_tutor_result(topic, message)
    else:
        try:
            tutor_result = _validate_tutor_result(reply_res.get("data") or {})
        except Exception as exc:
            logger.warning("Concept answer validation failed: %s", exc)
            tutor_result = _fallback_tutor_result(topic, message)
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

《数据结构与算法》课程图谱：
{json.dumps(semantic_result.get("dsa_course_map") or semantic_result.get("ai_course_map") or {}, ensure_ascii=False)}

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
        logger.warning("Learning tutor JSON failed: %s", reply_res.get("error"))
        tutor_result = _fallback_tutor_result(topic, message)
    else:
        try:
            tutor_result = _validate_tutor_result(reply_res.get("data") or {})
        except Exception as exc:
            logger.warning("Learning tutor validation failed: %s", exc)
            tutor_result = _fallback_tutor_result(topic, message)
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
            course_id=semantic_result.get("course_id", dsa_course_map_service.COURSE_ID),
            message="已创建 Artifact 生成任务，完成后会通过系统消息通知",
        )
        resource_status = {
            "status": "pending_review",
            "count": len(resources),
            "message": "已创建 Artifact 生成任务，系统会基于课程依据和你的学习画像生成个性化学习包，完成后通过系统消息通知。",
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
                plan_result.get("title", "学习路径"),
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
