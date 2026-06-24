import re
from typing import Dict, Tuple

from app.services.llm_provider import chat_json, is_enabled


SUBJECT_CATEGORIES = {
    "foreign_language",
    "computer_science",
    "mathematics",
    "physics",
    "general_course",
    "unknown",
}

FOREIGN_LANGUAGE_TERMS = {
    "法语": {"language": "French", "aliases": ["法语", "french", "delf", "dalf", "cefr", "法语语法", "法语口语"]},
    "英语": {"language": "English", "aliases": ["英语", "english", "cet", "ielts", "toefl", "英语语法"]},
    "日语": {"language": "Japanese", "aliases": ["日语", "japanese", "jlpt", "n1", "n2", "日语语法"]},
    "德语": {"language": "German", "aliases": ["德语", "german", "德语语法"]},
    "西班牙语": {"language": "Spanish", "aliases": ["西班牙语", "spanish"]},
    "韩语": {"language": "Korean", "aliases": ["韩语", "korean"]},
    "俄语": {"language": "Russian", "aliases": ["俄语", "russian"]},
    "意大利语": {"language": "Italian", "aliases": ["意大利语", "italian"]},
}

COMPUTER_TERMS = {
    "人工智能",
    "机器学习",
    "深度学习",
    "神经网络",
    "rnn",
    "lstm",
    "transformer",
    "rag",
    "信息安全",
    "网络安全",
    "数据库",
    "操作系统",
    "计算机网络",
    "算法",
    "数据结构",
    "python",
    "java",
    "c++",
    "编程",
    "代码",
}

MATHEMATICS_TERMS = {
    "数学",
    "高等数学",
    "线性代数",
    "概率论",
    "统计学",
    "微积分",
    "离散数学",
    "矩阵",
    "函数",
    "导数",
    "积分",
}

PHYSICS_TERMS = {
    "物理",
    "大学物理",
    "力学",
    "电磁学",
    "热学",
    "光学",
    "量子",
}

GENERAL_TERMS = {
    "管理学",
    "经济学",
    "心理学",
    "历史",
    "文学",
    "哲学",
    "通识",
    "写作",
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


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "").lower())


def _contains_any(text: str, words) -> bool:
    compact = _compact(text)
    return any(_compact(word) in compact for word in words if word)


def _detect_foreign_language(text: str) -> Tuple[str, str]:
    lowered = str(text or "").lower()
    for topic, config in FOREIGN_LANGUAGE_TERMS.items():
        aliases = [str(alias or "").lower() for alias in config["aliases"]]
        if any(alias and alias in lowered for alias in aliases):
            return topic, config["language"]
    return "", ""


def _detect_subject_by_rule(text: str, topic: str) -> Dict:
    user_text = text or ""
    source_text = " ".join([user_text, topic or ""])

    language_topic, language_name = _detect_foreign_language(user_text)
    if language_topic:
        return {
            "topic": language_topic,
            "subject_category": "foreign_language",
            "language": language_name,
            "confidence": 96,
            "topic_source": "rule",
        }

    if _contains_any(user_text, COMPUTER_TERMS):
        normalized_topic = _first_matching_term(user_text, COMPUTER_TERMS) or topic or "计算机相关主题"
        return {
            "topic": normalized_topic,
            "subject_category": "computer_science",
            "language": "",
            "confidence": 88,
            "topic_source": "rule",
        }

    if _contains_any(user_text, MATHEMATICS_TERMS):
        normalized_topic = _first_matching_term(user_text, MATHEMATICS_TERMS) or topic or "数学"
        return {
            "topic": normalized_topic,
            "subject_category": "mathematics",
            "language": "",
            "confidence": 86,
            "topic_source": "rule",
        }

    if _contains_any(user_text, PHYSICS_TERMS):
        normalized_topic = _first_matching_term(user_text, PHYSICS_TERMS) or topic or "物理"
        return {
            "topic": normalized_topic,
            "subject_category": "physics",
            "language": "",
            "confidence": 86,
            "topic_source": "rule",
        }

    if _contains_any(user_text, GENERAL_TERMS):
        normalized_topic = _first_matching_term(user_text, GENERAL_TERMS) or topic or "通识课程"
        return {
            "topic": normalized_topic,
            "subject_category": "general_course",
            "language": "",
            "confidence": 80,
            "topic_source": "rule",
        }

    if _compact(topic) in {"语法", "grammar", "语言"}:
        return {
            "topic": "未确认主题",
            "subject_category": "unknown",
            "language": "",
            "confidence": 30,
            "topic_source": "unknown",
        }

    if topic and topic not in {"未确认主题", "当前主题"} and _topic_grounded_in_message(topic, user_text):
        return {
            "topic": topic,
            "subject_category": "unknown",
            "language": "",
            "confidence": 55,
            "topic_source": "llm",
        }

    return {
        "topic": "未确认主题",
        "subject_category": "unknown",
        "language": "",
        "confidence": 30,
        "topic_source": "unknown",
    }


def _first_matching_term(text: str, terms) -> str:
    compact = _compact(text)
    ordered_terms = sorted([term for term in terms if term], key=lambda item: len(_compact(item)), reverse=True)
    for term in ordered_terms:
        if _compact(term) in compact:
            return term
    return ""


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
    if subject_category == "foreign_language":
        return bool(_detect_foreign_language(message)[0])
    if _topic_grounded_in_message(topic, message):
        return True
    term_map = {
        "computer_science": COMPUTER_TERMS,
        "mathematics": MATHEMATICS_TERMS,
        "physics": PHYSICS_TERMS,
        "general_course": GENERAL_TERMS,
    }
    return _contains_any(message, term_map.get(subject_category, set()))


def _infer_by_llm(message: str, eval_topic: str) -> Dict:
    if not is_enabled():
        return {}

    prompt = f"""
你是学习平台的语义接地模块。请判断学生要学的真实学科、主题、请求类型和是否需要代码内容。
不要生成学习建议。
不要猜测用户水平。如果用户没有明确说明水平，level 必须返回“未确认”。

学生输入：{message}
初步主题：{eval_topic}

只返回 JSON：
{{
  "topic": "",
  "subject_category": "foreign_language | computer_science | mathematics | physics | general_course | unknown",
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

    level_info = profile_service.infer_topic_level_from_evidence(
        db=db,
        username=username,
        topic=rule_result.get("topic") or eval_topic,
        subject_category=rule_result.get("subject_category") or "unknown",
        message=message,
    )

    subject_category = rule_result.get("subject_category") or "unknown"
    should_generate_resources = subject_category != "unknown" and requested_action in {
        "path_plan",
        "resource_generation",
        "exercise",
        "practice",
    }

    return {
        "topic": rule_result.get("topic") or eval_topic or "未确认主题",
        "raw_topic": eval_topic or rule_result.get("topic") or "",
        "subject_category": subject_category,
        "language": rule_result.get("language") or "",
        "requested_action": requested_action,
        "is_learning_request": requested_action not in {"chat", "unknown"},
        "is_programming_related": is_programming_related,
        "level": level_info.get("level", "未确认"),
        "level_source": level_info.get("level_source", "none"),
        "level_evidence": level_info.get("level_evidence", ""),
        "needs_level_diagnosis": level_info.get("needs_level_diagnosis", True),
        "should_generate_resources": should_generate_resources,
        "should_generate_code_content": bool(is_programming_related),
        "confidence": int(rule_result.get("confidence") or 50),
        "topic_source": rule_result.get("topic_source") or "unknown",
    }
