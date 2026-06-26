import re

from app.services.data_services import deep_learning_course_map_service


PRIMARY_COURSE_DISPLAY_NAME = "深度学习"
PRIMARY_COURSE_TITLE = deep_learning_course_map_service.COURSE_DISPLAY_NAME

CANONICAL_TOPIC_NAMES = {
    "cnn": "卷积神经网络",
    "rnn": "RNN",
    "lstm": "LSTM",
    "gru": "GRU",
    "transformer": "Transformer",
    "attention": "自注意力机制",
    "qkv": "自注意力机制",
    "pytorch": "PyTorch 深度学习工程实践",
    "torch": "PyTorch 深度学习工程实践",
    "dl": PRIMARY_COURSE_DISPLAY_NAME,
    "deep learning": PRIMARY_COURSE_DISPLAY_NAME,
}

OUT_OF_COURSE_ALIASES = {
    "英语": ["英语", "英文", "english"],
    "高数": ["高数", "高等数学", "微积分"],
    "JavaScript": ["javascript", "js", "前端"],
    "Java": ["java"],
    "信息安全": ["信息安全", "网络安全"],
    "物理": ["物理"],
    "法语": ["法语", "french"],
}


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").lower())


def normalize_course_topic(topic: str) -> str:
    value = str(topic or "").strip()
    if not value:
        return ""
    canonical = CANONICAL_TOPIC_NAMES.get(_compact(value))
    if canonical:
        return canonical
    return value


def extract_requested_topic(message: str, fallback: str = "") -> str:
    text = str(message or "").strip()
    compact = _compact(text)
    for canonical, aliases in OUT_OF_COURSE_ALIASES.items():
        if any(_compact(alias) in compact for alias in aliases):
            return canonical

    patterns = [
        r"(?:我)?(?:想|要|准备|打算|希望)(?:开始)?(?:学习|学|复习|了解)\s*(?P<topic>[A-Za-z0-9+#.\u4e00-\u9fff -]{1,30})",
        r"(?:帮我|给我)?(?:规划|制定|安排)\s*(?P<topic>[A-Za-z0-9+#.\u4e00-\u9fff -]{1,30})(?:路线|计划|学习路线|学习计划)?",
        r"(?:帮我|给我|请你)?(?:讲讲|讲一下|解释|介绍)\s*(?P<topic>[A-Za-z0-9+#.\u4e00-\u9fff -]{1,30})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            topic = " ".join(match.group("topic").split()).strip("，。！？,.!?：:；;、")
            if topic:
                return normalize_course_topic(topic[:30])

    fallback_text = str(fallback or "").strip()
    if fallback_text and fallback_text not in {"未确认主题", "当前主题"}:
        return normalize_course_topic(fallback_text[:30])
    return text[:30] or "这个主题"


def is_supported_learning_scope(semantic_result: dict) -> bool:
    semantic_result = semantic_result or {}
    topic = normalize_course_topic(semantic_result.get("topic") or "")
    message = semantic_result.get("message") or semantic_result.get("raw_message") or ""
    return bool(deep_learning_course_map_service.match_deep_learning_topic(topic, message).get("matched"))


def build_out_of_scope_reply(topic: str = "", raw_message: str = "") -> str:
    requested_topic = extract_requested_topic(raw_message, topic)
    topic_text = requested_topic if requested_topic and requested_topic != "未确认主题" else "这个主题"
    return f"本系统聚焦{PRIMARY_COURSE_TITLE}课程，「{topic_text}」暂未纳入课程图谱，请期待后续资源完善哦。"
