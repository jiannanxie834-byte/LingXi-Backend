import json
import logging
import re

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
    system_message_service,
    conversation_router,
    semantic_analysis_service,
)

from app.agents.evaluation_agent import run as eval_run
from app.agents.profile_agent import run as profile_run
from app.agents.planner_agent import run as planner_run
from app.agents.resource_agent import run as resource_run


logger = logging.getLogger(__name__)

PUBLIC_PROFILE_DIMENSIONS = {
    "知识基础",
    "自驱探索力",
    "学习强度",
    "学习目标",
    "认知水平",
    "认知风格",
    "高频主题",
    "知识短板",
    "实践能力",
    "学习专注度",
    "计划完成率",
    "待办完成率",
    "历史评价均分",
}

KNOWN_TOPIC_ALIASES = {
    "rnn": "RNN",
    "lstm": "LSTM",
    "transformer": "Transformer",
    "rag": "RAG",
    "信息安全": "信息安全",
    "人工智能": "人工智能",
    "机器学习": "机器学习",
    "深度学习": "深度学习",
    "神经网络": "神经网络",
    "法语": "法语",
    "英语": "英语",
    "日语": "日语",
    "德语": "德语",
}


def _fallback_topic_from_message(message: str):
    text = (message or "").strip()
    compact = re.sub(r"\s+", "", text.lower())
    for alias, topic in KNOWN_TOPIC_ALIASES.items():
        if alias in compact:
            return topic

    match = re.search(r"(?:学习|想学|了解|解释|讲讲|讲一下)([A-Za-z0-9+#.\u4e00-\u9fff]{2,30})", text)
    if match:
        return match.group(1).strip("，。！？,.!? ")
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


def _validate_resource_output(data):
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
        "content": _render_resource_content(summary, normalized_sections),
        "source_notes": source_notes,
    }


def _render_resource_content(summary, sections):
    lines = [f"# {summary}", ""]

    for section in sections:
        heading = section["heading"]
        items = section["items"]
        lines.extend([f"## {heading}", ""])

        if "Mermaid" in heading or "流程图" in heading:
            lines.extend(["```mermaid", *items, "```", ""])
            continue

        if "代码" in heading:
            lines.extend(["```python", *items, "```", ""])
            continue

        lines.extend([f"- {item}" for item in items])
        lines.append("")

    return "\n".join(lines).strip()


def _build_resource_prompt(item, profile_result, intent, evidence_prompt, teaching_sources_prompt):
    subject_category = item.get("subject_category", "unknown")
    level = item.get("level") or profile_result.get("level") or "未确认"
    level_source = item.get("level_source") or profile_result.get("level_source") or "none"
    allow_code = bool(item.get("allow_code_content"))
    quality_constraints = "\n".join([f"- {rule}" for rule in item.get("quality_constraints", [])])
    forbidden_terms = "、".join(item.get("forbidden_terms", [])) or "无"
    foreign_language_rules = ""
    if subject_category == "foreign_language":
        foreign_language_rules = """
外语学习资源额外规则：
- 资源应围绕词汇、语法、例句、阅读、听说、写作和文化语境。
- 练习题必须包含参考答案和解析。
- 多模态学习包应包含对话脚本、词汇卡片、语法图解、角色扮演任务和 PPT 页纲。
- 不得出现代码注释、伪代码、函数、算法实现、模型训练或编程框架。
"""
    return f"""
你是高校课程学习资源生成助手，请严格根据“学科类型”和“资源类型”生成内容。

输出边界：
- 只输出 JSON 对象
- 不输出解释
- 不输出思考过程
- 不面向学生说话
- 不输出 Markdown 代码块包裹 JSON
- sections 必须是对象数组，items 必须是字符串数组
- items 中不要出现英文双引号、反引号或多行字符串；需要强调时使用中文括号或单引号

学科类型：{subject_category}
主题：{item.get('topic')}
学生水平：{level}
水平证据：{level_source}
资源类型：{item.get('type')}
是否允许代码内容：{"true" if allow_code else "false"}
学习目标：{intent}
资源规格：{'、'.join(item.get('requirements') or [])}
禁止词/禁用方向：{forbidden_terms}
质量约束：
{quality_constraints or "- 练习题必须考查主题本身，不得改写成学习规划题"}

可参考的课程资料：
{evidence_prompt}

外部教学资料候选（MOOC、教材试读/样章、教学视频优先）：
{teaching_sources_prompt}

要求：
- 内容必须适合高校课程学习场景
- 如果学生水平为“未确认”，不得写“进阶学习者”“高阶学习者”“B1/B2/C1/C2”“已经具备”等具体水平。
- 如果学科类型不是 computer_science，且是否允许代码内容为 false，不得生成代码、伪代码、函数、编程框架、算法实现。
- 练习题必须考查主题本身，不得考查“如何规划学习路径”。
- 拓展阅读材料必须给出具体阅读短文或明确外部来源条目，不能只有泛泛推荐。
- 不得虚构已引用教材、MOOC、官方链接或外部资料。
- 无依据内容可在来源说明中标注“需管理员复核”，但正文仍要保持学生可读。
- 优先把外部教学资料作为学生可用的学习入口，不要把论文作为主要学习材料
- 结合外部教学资料时必须保留来源平台、标题和链接
- 教材正文、课件包、视频内容只能引用公开入口或授权内容，不得虚构“已节选”的正文
- 避免绝对化和不可验证结论
- 如果类型是多模态学习包，请按当前学科类型输出合适模态；不得默认加入代码注释案例。
- Mermaid 和代码示例也必须作为普通 JSON 字符串逐条放入 items，不要使用 Markdown 围栏
{foreign_language_rules}

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


def _generate_resource_outputs(resource_plan, profile_result, intent, evidence_prompt, teaching_sources_prompt):
    llm_outputs = []

    for item in resource_plan.get("resources", []):
        prompt = _build_resource_prompt(
            item=item,
            profile_result=profile_result,
            intent=intent,
            evidence_prompt=evidence_prompt,
            teaching_sources_prompt=teaching_sources_prompt,
        )
        res = chat_json(
            [{"role": "user", "content": prompt}],
            required_fields=["summary", "sections", "source_notes"],
            temperature=0.1,
            max_tokens=3600
        )
        if not res.get("ok"):
            raise RuntimeError(f"资源内容结构化输出失败：{res.get('error', '未知错误')}")

        resource_output = _validate_resource_output(res.get("data") or {})
        llm_outputs.append({
            "summary": resource_output["summary"],
            "content": resource_output["content"],
            "source": "；".join(resource_output["source_notes"][:3]),
        })

    return llm_outputs


def _preview_resource_plan(resource_plan):
    preview = []
    for item in resource_plan.get("resources", []):
        title = str(item.get("title") or item.get("topic") or "配套学习资料").strip()
        r_type = str(item.get("type") or "学习资源").strip()
        if title and r_type:
            preview.append({
                "title": title,
                "type": r_type,
                "status": "整理中",
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


def run_resource_generation_job(username, resource_plan, profile_result, intent, evidence_query, evidence_prompt):
    db = SessionLocal()
    try:
        teaching_sources = teaching_source_service.select_teaching_sources(
            evidence_query,
            limit=8
        )
        teaching_sources_prompt = teaching_source_service.format_teaching_sources_for_prompt(
            teaching_sources,
            max_items=6
        )

        llm_outputs = _generate_resource_outputs(
            resource_plan=resource_plan,
            profile_result=profile_result,
            intent=intent,
            evidence_prompt=evidence_prompt,
            teaching_sources_prompt=teaching_sources_prompt,
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
            skipped_resources = save_result.get("skipped_resources", [])
        else:
            resources = save_result
            skipped_resources = []
        count = len(resources)
        if count:
            skipped_text = f"；{len(skipped_resources)} 份资源因语义门禁未入库" if skipped_resources else ""
            _notify_resource_generation(
                db,
                username,
                "配套资料已进入审核队列",
                f"本轮学习需求的 {count} 份配套资料已整理完成，正在等待管理员审核；审核通过后会进入资源库{skipped_text}。",
            )
        else:
            _notify_resource_generation(
                db,
                username,
                "配套资料整理未完成",
                "本轮学习需求暂未生成可提交审核的配套资料，请稍后补充学习主题后再试。",
            )
    except Exception as exc:
        logger.exception("Resource generation job failed for user=%s", username)
        db.rollback()
        _notify_resource_generation(
            db,
            username,
            "配套资料整理失败",
            f"本轮配套资料整理失败，原因：{str(exc)[:120]}。你可以稍后重新发起学习需求。",
        )
    finally:
        db.close()


def _route_result(route, content=None, tutor_result=None):
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
    topic = semantic_result.get("topic") or eval_result.get("topic", "") or route.topic or _fallback_topic_from_message(message)

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
        "pipeline_steps": [],
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
            result = _route_result(turn_route)
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
    topic = semantic_result.get("topic") or eval_result.get("topic", "") or _fallback_topic_from_message(message)
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
        resource_plan = resource_run(plan_result, profile_result, semantic_result=semantic_result)
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
        resource_status = {
            "status": "queued",
            "count": len(resources),
            "message": "配套资料正在整理，完成后会进入资源库。",
            "items": resources,
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
    pending_action = "awaiting_topic" if is_unknown_semantic else ("resource_review_pending" if resource_status.get("status") == "queued" else "continue_learning_help")
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
