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


def is_supported_learning_scope(semantic_result: dict) -> bool:
    semantic_result = semantic_result or {}
    topic = normalize_course_topic(semantic_result.get("topic") or "")
    message = semantic_result.get("message") or semantic_result.get("raw_message") or ""
    return bool(deep_learning_course_map_service.match_deep_learning_topic(topic, message).get("matched"))


def build_out_of_scope_reply(topic: str = "") -> str:
    topic = normalize_course_topic(topic)
    topic_text = f"「{topic}」" if topic and topic != "未确认主题" else "这个主题"
    return (
        f"当前演示主线聚焦{PRIMARY_COURSE_TITLE}课程，"
        f"{topic_text}暂未纳入本轮课程图谱。"
        "我可以先帮你澄清学习目标；如果要生成学习路径、题库、代码实验或视频观看指南，"
        "请围绕 CNN、反向传播、Transformer、PyTorch 实战等深度学习知识点提出需求。"
    )
