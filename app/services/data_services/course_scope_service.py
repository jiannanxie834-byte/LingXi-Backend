import re

from app.services.data_services import ai_course_map_service


PRIMARY_COURSE_DISPLAY_NAME = "人工智能"

LEGACY_PRIMARY_COURSE_NAMES = {
    "人工智能导论",
    "ai导论",
    "AI导论",
}

SUPPORTED_TOPIC_ALIASES = {
    "人工智能",
    "ai",
    "机器学习",
    "深度学习",
    "神经网络",
    "rnn",
    "lstm",
    "transformer",
    "attention",
    "注意力",
    "nlp",
    "自然语言处理",
    "大语言模型",
    "llm",
    "rag",
    "检索增强",
    "多模态",
    "智能体",
    "搜索",
    "状态空间",
    "a*",
    "astar",
    "监督学习",
    "模型评估",
    "混淆矩阵",
    "信息安全",
    "网络安全",
    "密码学",
    "访问控制",
}

CANONICAL_TOPIC_NAMES = {
    "rnn": "RNN",
    "lstm": "LSTM",
    "transformer": "Transformer",
    "rag": "RAG",
    "nlp": "NLP",
    "llm": "大语言模型",
    "ai": PRIMARY_COURSE_DISPLAY_NAME,
}


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").lower())


def normalize_course_topic(topic: str) -> str:
    value = str(topic or "").strip()
    if not value:
        return ""
    if _compact(value) in {_compact(item) for item in LEGACY_PRIMARY_COURSE_NAMES}:
        return PRIMARY_COURSE_DISPLAY_NAME
    canonical = CANONICAL_TOPIC_NAMES.get(_compact(value))
    if canonical:
        return canonical
    return value


def is_supported_learning_scope(semantic_result: dict) -> bool:
    semantic_result = semantic_result or {}
    topic = normalize_course_topic(semantic_result.get("topic") or "")
    message = semantic_result.get("message") or semantic_result.get("raw_message") or ""
    if ai_course_map_service.match_ai_course_topic(topic, message).get("matched"):
        return True

    topic_compact = _compact(topic)
    return any(alias and alias in topic_compact for alias in SUPPORTED_TOPIC_ALIASES)


def build_out_of_scope_reply(topic: str = "") -> str:
    topic = normalize_course_topic(topic)
    topic_text = f"「{topic}」" if topic and topic != "未确认主题" else "这个主题"
    return (
        f"当前演示课程库主要围绕「{PRIMARY_COURSE_DISPLAY_NAME}」和 AI/计算机相关主题建设，"
        f"{topic_text}暂未配置完整课程知识库。"
        "我可以先帮你明确学习方向，但不会为它生成学习路径、题库、阅读材料或审核资源。"
        "如果后续要正式支持这门课，需要先由管理员新增课程知识库、资源模板和审核标准。"
    )
