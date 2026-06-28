import re
from typing import Dict

from app.services.llm_provider import chat_json, is_enabled
from app.services.data_services import (
    course_scope_service,
    dsa_course_map_service,
    topic_scope_resolver,
)


SUBJECT_CATEGORIES = {
    "computer_science",
    "out_of_course",
    "unknown",
}

PROGRAMMING_MARKERS = {
    "代码",
    "编程",
    "python",
    "java",
    "c++",
    "脚本",
    "程序",
    "实现",
    "debug",
    "调试",
}

ACTION_MAP = {
    "概念讲解": "concept_explain",
    "路径规划": "path_plan",
    "生成资源": "resource_generation",
    "练习巩固": "exercise",
    "实操训练": "practice",
    "综合学习": "path_plan",
}

SCOPE_ACTION_MAP = {
    "course": "path_plan",
    "chapter": "path_plan",
    "unit": "concept_explain",
    "concept": "concept_explain",
    "comparison": "resource_generation",
    "project": "practice",
    "diagnostic": "exercise",
}

SCOPE_NEED_TYPE_MAP = {
    "course": "course_orientation",
    "chapter": "path_planning",
    "unit": "concept_explanation",
    "concept": "concept_explanation",
    "comparison": "comparison",
    "project": "project",
    "diagnostic": "evaluation",
}

COURSE_NEED_ACTION_MAP = {
    "concept_explanation": "concept_explain",
    "resource_generation": "resource_generation",
    "practice": "exercise",
    "code_lab": "practice",
    "path_planning": "path_plan",
    "course_orientation": "path_plan",
    "evaluation": "exercise",
    "project": "practice",
    "comparison": "resource_generation",
}


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "").lower())


def _contains_any(text: str, words) -> bool:
    compact = _compact(text)
    return any(_compact(word) in compact for word in words if word)


def _detect_subject_by_rule(text: str, topic: str) -> Dict:
    user_text = text or ""
    topic_scope = topic_scope_resolver.resolve_topic_scope(user_text, topic)
    scope_level = topic_scope.get("scope_level")

    if scope_level and scope_level != "out_of_course":
        course_match = topic_scope.get("course_match") or {}
        requested_action = COURSE_NEED_ACTION_MAP.get(
            course_match.get("learning_need_type"),
            SCOPE_ACTION_MAP.get(scope_level, "concept_explain"),
        )
        return {
            "topic": topic_scope.get("display_topic") or course_match.get("normalized_topic") or course_match.get("topic"),
            "subject_category": "computer_science",
            "language": "",
            "confidence": int(float(course_match.get("confidence", 0.8)) * 100),
            "topic_source": "topic_scope_resolver",
            "course_match": course_match,
            "topic_scope": topic_scope,
            "requested_action": requested_action,
        }

    out_topic = topic_scope.get("display_topic") or topic_scope.get("primary_topic") or ""
    if out_topic and out_topic not in {"未确认主题", "当前主题", "这个主题"}:
        return {
            "topic": out_topic,
            "subject_category": "out_of_course",
            "language": "",
            "confidence": 70,
            "topic_source": "topic_scope_resolver",
            "topic_scope": topic_scope,
            "requested_action": "unknown",
        }

    course_match = dsa_course_map_service.match_dsa_topic(topic, user_text)
    if course_match.get("matched"):
        return {
            "topic": course_match.get("normalized_topic") or course_match.get("topic"),
            "subject_category": "computer_science",
            "language": "",
            "confidence": int(course_match.get("confidence", 0.8) * 100),
            "topic_source": "dsa_course_map",
            "course_match": course_match,
            "requested_action": COURSE_NEED_ACTION_MAP.get(course_match.get("learning_need_type"), "concept_explain"),
        }

    if topic and topic not in {"未确认主题", "当前主题"} and _topic_grounded_in_message(topic, user_text):
        return {
            "topic": topic,
            "subject_category": "out_of_course",
            "language": "",
            "confidence": 70,
            "topic_source": "eval_grounded",
        }

    if _compact(topic) in {"语法", "grammar", "语言"}:
        return {
            "topic": "未确认主题",
            "subject_category": "unknown",
            "language": "",
            "confidence": 30,
            "topic_source": "unknown",
        }

    return {
        "topic": "未确认主题",
        "subject_category": "unknown",
        "language": "",
        "confidence": 30,
        "topic_source": "unknown",
    }


def _topic_grounded_in_message(topic: str, message: str) -> bool:
    topic_compact = _compact(topic)
    message_compact = _compact(message)
    if not topic_compact or topic_compact in {"未确认主题", "当前主题"}:
        return False
    if topic_compact in message_compact:
        return True

    topic_chinese_chars = {
        char for char in topic_compact if "\u4e00" <= char <= "\u9fff"
    }
    if len(topic_chinese_chars) <= 2:
        return False

    overlap = topic_chinese_chars & {
        char for char in message_compact if "\u4e00" <= char <= "\u9fff"
    }
    return len(overlap) >= 2


def _llm_result_is_grounded(message: str, data: Dict) -> bool:
    subject_category = data.get("subject_category")
    topic = data.get("topic") or ""
    if subject_category == "unknown":
        return True
    if subject_category == "computer_science":
        return dsa_course_map_service.match_dsa_topic(topic, message).get("matched")
    if subject_category == "out_of_course":
        return bool(topic and topic not in {"未确认主题", "当前主题"}) and _topic_grounded_in_message(topic, message)
    if _topic_grounded_in_message(topic, message):
        return True
    return False


def _infer_by_llm(message: str, eval_topic: str) -> Dict:
    if not is_enabled():
        return {}

    prompt = f"""
你是《数据结构与算法》课程学习平台的语义接地模块。请判断学生输入是否属于本课程范围、真实主题、请求类型和是否需要代码内容。
不要生成学习建议。
不要猜测用户水平。如果用户没有明确说明水平，level 必须返回“未确认”。
只有命中《数据结构与算法》课程图谱的主题才能返回 computer_science；数据库、操作系统、计算机网络、外语、高数、金融等课程外主题返回 out_of_course；主题不明确返回 unknown。

学生输入：{message}
初步主题：{eval_topic}

只返回 JSON：
{{
  "topic": "",
  "subject_category": "computer_science | out_of_course | unknown",
  "requested_action": "concept_explain | path_plan | resource_generation | exercise | practice | chat | unknown",
  "is_programming_related": false,
  "level": "未确认",
  "level_source": "none | user_explicit",
  "needs_level_diagnosis": true,
  "confidence": 0
}}
"""
    result = chat_json(
        [{"role": "user", "content": prompt}],
        required_fields=[
            "topic",
            "subject_category",
            "requested_action",
            "is_programming_related",
            "level",
            "level_source",
            "needs_level_diagnosis",
            "confidence",
        ],
        temperature=0.1,
        max_tokens=800,
    )
    if not result.get("ok"):
        return {}
    data = result.get("data") or {}
    subject_category = data.get("subject_category")
    if subject_category not in SUBJECT_CATEGORIES:
        return {}
    if not _llm_result_is_grounded(message, data):
        return {}
    return data


def analyze_learning_request(db, username: str, message: str, eval_result: Dict) -> Dict:
    from app.services.data_services import profile_service

    eval_topic = (eval_result or {}).get("topic") or ""
    rule_result = _detect_subject_by_rule(message, eval_topic)

    ambiguous_language_topic = _compact(eval_topic) in {"语法", "grammar", "语言"}
    if (
        rule_result.get("subject_category") == "unknown"
        and rule_result.get("confidence", 0) < 60
        and not ambiguous_language_topic
    ):
        llm_result = _infer_by_llm(message, eval_topic)
        if llm_result:
            rule_result = {
                **rule_result,
                **llm_result,
                "topic": llm_result.get("topic") or rule_result.get("topic") or "未确认主题",
                "topic_source": "llm",
            }

    requested_action = ACTION_MAP.get((eval_result or {}).get("intent") or "", "unknown")
    if rule_result.get("requested_action"):
        requested_action = rule_result["requested_action"]

    is_programming_related = (
        rule_result.get("subject_category") == "computer_science"
        or _contains_any(message, PROGRAMMING_MARKERS)
        or bool(rule_result.get("is_programming_related"))
    )

    normalized_topic = course_scope_service.normalize_course_topic(
        rule_result.get("topic") or eval_topic or "未确认主题"
    )
    topic_scope = (
        rule_result.get("topic_scope")
        or topic_scope_resolver.resolve_topic_scope(message, normalized_topic)
    )
    ai_course_match = (
        rule_result.get("course_match")
        or topic_scope.get("course_match")
        or dsa_course_map_service.match_dsa_topic(normalized_topic, message)
    )
    if topic_scope.get("scope_level") != "out_of_course" and topic_scope.get("display_topic"):
        normalized_topic = course_scope_service.normalize_course_topic(topic_scope.get("display_topic"))
        rule_result["topic"] = normalized_topic
        if ai_course_match.get("matched"):
            ai_course_match = {
                **ai_course_match,
                "display_topic": topic_scope.get("display_topic"),
                "scope_level": topic_scope.get("scope_level"),
                "primary_unit_id": topic_scope.get("primary_unit_id"),
                "chapter_title": topic_scope.get("chapter_title"),
                "compare_units": topic_scope.get("compare_units", []),
                "expansion_policy": topic_scope.get("expansion_policy"),
                "should_generate_full_chapter": topic_scope.get("should_generate_full_chapter", False),
            }
        if rule_result.get("subject_category") == "unknown":
            rule_result["subject_category"] = "computer_science"
    elif ai_course_match.get("matched"):
        normalized_topic = course_scope_service.normalize_course_topic(
            ai_course_match.get("normalized_topic")
            or ai_course_match.get("topic")
            or normalized_topic
        )
        rule_result["topic"] = normalized_topic
        if rule_result.get("subject_category") == "unknown":
            rule_result["subject_category"] = "computer_science"

    level_info = profile_service.infer_topic_level_from_evidence(
        db=db,
        username=username,
        topic=normalized_topic,
        subject_category=rule_result.get("subject_category") or "unknown",
        message=message,
    )

    subject_category = rule_result.get("subject_category") or "unknown"
    scoped_result = {
        **rule_result,
        "topic": normalized_topic,
        "subject_category": subject_category,
        "message": message,
    }
    is_supported_scope = course_scope_service.is_supported_learning_scope(scoped_result)
    should_generate_resources = (
        is_supported_scope
        and ai_course_match.get("scope_type", "in_course") == "in_course"
        and topic_scope.get("scope_level") != "out_of_course"
        and requested_action in {
        "path_plan",
        "resource_generation",
        "exercise",
        "practice",
        }
    )
    learning_need_type = (
        ai_course_match.get("learning_need_type")
        or SCOPE_NEED_TYPE_MAP.get(topic_scope.get("scope_level"))
        or {
            "concept_explain": "concept_explanation",
            "path_plan": "path_planning",
            "resource_generation": "resource_generation",
            "exercise": "practice",
            "practice": "code_lab" if is_programming_related else "practice",
        }.get(requested_action, "concept_explanation")
    )
    confidence = int(rule_result.get("confidence") or 50)
    if ai_course_match.get("matched"):
        confidence = max(confidence, int(float(ai_course_match.get("confidence", 0.6)) * 100))

    return {
        "course_id": ai_course_match.get("course_id", ""),
        "course_name": ai_course_match.get("course_name", ""),
        "course_display_name": ai_course_match.get("course_display_name", ""),
        "topic": normalized_topic,
        "raw_topic": eval_topic or rule_result.get("topic") or "",
        "normalized_topic": normalized_topic,
        "display_topic": topic_scope.get("display_topic") or normalized_topic,
        "scope_level": topic_scope.get("scope_level", ""),
        "primary_topic": topic_scope.get("primary_topic", ""),
        "primary_unit_id": topic_scope.get("primary_unit_id", ""),
        "chapter_id": ai_course_match.get("chapter_id", ""),
        "chapter": ai_course_match.get("chapter", ""),
        "chapter_title": topic_scope.get("chapter_title") or ai_course_match.get("chapter", ""),
        "prerequisite_units": topic_scope.get("prerequisite_units", []),
        "related_units": topic_scope.get("related_units", []),
        "compare_units": topic_scope.get("compare_units", []),
        "expansion_policy": topic_scope.get("expansion_policy", ""),
        "should_generate_full_chapter": bool(topic_scope.get("should_generate_full_chapter", False)),
        "unit_id": ai_course_match.get("unit_id", ""),
        "learning_need_type": learning_need_type,
        "scope_type": ai_course_match.get("scope_type", "in_course" if is_supported_scope else "out_of_course"),
        "difficulty": ai_course_match.get("difficulty", "beginner"),
        "requires_code": bool(ai_course_match.get("requires_code") or is_programming_related),
        "requires_multimodal": bool(ai_course_match.get("requires_multimodal")),
        "matched_aliases": ai_course_match.get("matched_aliases", []),
        "subject_category": subject_category,
        "language": rule_result.get("language") or "",
        "requested_action": requested_action,
        "is_learning_request": requested_action not in {"chat", "unknown"},
        "is_supported_scope": is_supported_scope,
        "ai_course_map": ai_course_match,
        "dsa_course_map": ai_course_match,
        "topic_scope": topic_scope,
        "is_programming_related": is_programming_related,
        "level": level_info.get("level", "未确认"),
        "level_source": level_info.get("level_source", "none"),
        "level_evidence": level_info.get("level_evidence", ""),
        "needs_level_diagnosis": level_info.get("needs_level_diagnosis", True),
        "should_generate_resources": should_generate_resources,
        "should_generate_code_content": bool(is_programming_related or ai_course_match.get("requires_code")),
        "confidence": confidence,
        "topic_source": rule_result.get("topic_source") or "unknown",
    }
