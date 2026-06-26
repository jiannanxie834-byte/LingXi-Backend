import json
import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models.schemas import ChatMessage, ChatSession, TurnRoute
from app.services.data_services import student_reply_templates as replies


ACKNOWLEDGEMENTS = {
    "好",
    "好的",
    "嗯",
    "嗯嗯",
    "可以",
    "行",
    "收到",
    "明白",
    "知道了",
    "了解",
    "谢谢",
    "谢了",
    "谢谢你",
    "ok",
    "okay",
}

CONTINUE_PREVIOUS_TEXTS = {
    "继续",
    "继续说",
    "继续讲",
    "接着说",
    "接着讲",
    "展开说",
    "展开讲",
    "详细点",
    "详细一点",
    "再详细点",
    "再具体点",
    "再讲讲",
    "多讲一点",
}

FOLLOWUP_TEXTS = {
    "举个例子",
    "举例",
    "这个地方不懂",
    "这块不懂",
    "没懂",
    "不太懂",
    "再举例",
    "换个例子",
}

TOPIC_SWITCH_TEXTS = {
    "聊点别的吧",
    "聊点别的",
    "换个话题",
    "换个方向",
    "讲点别的",
    "不想学这个了",
    "换一个",
    "换个",
}

CASUAL_CHAT_TEXTS = {
    "我想和你聊天",
    "我想要和你聊天",
    "陪我聊聊",
    "随便聊聊",
    "聊聊天",
    "你好",
    "您好",
    "在吗",
}

META_UNKNOWN_TEXTS = {
    "你知道我要说什么吗",
    "你知道我想说什么吗",
    "你猜我要说什么",
}

META_CAPABILITY_TEXTS = {
    "你能干什么",
    "你可以帮我什么",
    "你会什么",
    "你是谁",
}

AMBIGUOUS_TEXTS = {
    "随便",
    "不知道",
    "你说呢",
    "这个",
    "那个",
    "然后",
    "然后呢",
    "？",
    "?",
    "...",
    "。。。",
}

RESOURCE_ACTION_MARKERS = (
    "规划",
    "路线",
    "计划",
    "练习",
    "题",
    "错题",
    "资源",
    "资料",
    "课件",
    "ppt",
    "导图",
    "实操",
    "项目",
    "生成",
)

LEARNING_START_PATTERNS = (
    r"(?:我)?(?:想|要|准备|打算|希望)(?:开始)?(?:学习|学|复习|了解)\s*(?P<topic>[A-Za-z0-9+#.\u4e00-\u9fff -]{1,40})",
    r"(?:帮我|给我)?(?:规划|制定|安排)\s*(?P<topic>[A-Za-z0-9+#.\u4e00-\u9fff -]{1,40})(?:路线|计划|学习路线|学习计划)?",
    r"(?:给我|帮我)(?:出|生成|整理)\s*(?P<topic>[A-Za-z0-9+#.\u4e00-\u9fff -]{1,40})(?:练习题|题|资料|资源|课件|导图|项目|案例)",
)

CONCEPT_QUESTION_PATTERNS = (
    r"(?P<topic>[A-Za-z0-9+#.\u4e00-\u9fff -]{1,40})(?:是什么|什么意思|怎么理解|介绍一下|解释一下|原理是什么)",
    r"(?:解释|介绍|讲讲|讲一下)\s*(?P<topic>[A-Za-z0-9+#.\u4e00-\u9fff -]{1,40})",
)

KNOWN_TOPIC_ALIASES = {
    "深度学习": "深度学习",
    "神经网络": "神经网络基础",
    "cnn": "卷积神经网络",
    "卷积神经网络": "卷积神经网络",
    "卷积": "卷积神经网络",
    "反向传播": "反向传播",
    "bp": "反向传播",
    "backprop": "反向传播",
    "sgd": "优化算法",
    "adam": "优化算法",
    "dropout": "正则化",
    "batchnorm": "正则化",
    "rnn": "RNN/LSTM/GRU",
    "lstm": "RNN/LSTM/GRU",
    "gru": "RNN/LSTM/GRU",
    "transformer": "Transformer",
    "attention": "自注意力机制",
    "自注意力": "自注意力机制",
    "qkv": "自注意力机制",
    "gan": "生成模型",
    "扩散模型": "生成模型",
    "pytorch": "PyTorch 深度学习工程实践",
    "图像分类项目": "深度学习课程综合项目",
}


def _normalize(text: str) -> str:
    lowered = (text or "").strip().lower()
    return re.sub(r"[\s,，.。!！?？、~～]+", "", lowered)


def _clean_topic(value: Optional[str]) -> str:
    topic = " ".join(str(value or "").replace("...", "").split()).strip()
    topic = topic.strip("，。！？,.!?：:；;、")
    if not topic or topic in {"新对话", "好", "好的", "继续", "这个", "那个"}:
        return ""
    normalized = topic.lower()
    return KNOWN_TOPIC_ALIASES.get(normalized, topic[:80])


def _safe_metadata(message: ChatMessage) -> dict:
    try:
        data = json.loads(message.metadata_json or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_session_state(db: Session, username: str, session_id: str) -> dict:
    if not username or not session_id:
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


def get_last_topic(db: Session, username: str, session_id: str) -> str:
    if not username or not session_id:
        return ""

    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.username == username)
        .first()
    )
    if session:
        try:
            state = json.loads(session.state_json or "{}")
            state_topic = _clean_topic(state.get("last_topic"))
            if state_topic:
                return state_topic
        except Exception:
            pass

    if session and _clean_topic(session.last_topic):
        return _clean_topic(session.last_topic)

    latest_ai = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
            ChatMessage.username == username,
            ChatMessage.role == "ai",
        )
        .order_by(ChatMessage.created_at.desc())
        .first()
    )
    if latest_ai:
        metadata = _safe_metadata(latest_ai)
        topic = _clean_topic(metadata.get("topic"))
        if topic:
            return topic
        if session:
            return _clean_topic(session.title)

    return ""


def _extract_known_topic(text: str) -> str:
    compact = _normalize(text)
    for alias, topic in KNOWN_TOPIC_ALIASES.items():
        if alias in compact:
            return topic
    return ""


def _extract_topic_by_patterns(text: str, patterns, allow_known_fallback: bool = True) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            topic = _clean_topic(match.groupdict().get("topic"))
            if topic:
                return _extract_known_topic(topic) or topic
    return _extract_known_topic(text) if allow_known_fallback else ""


def _extract_rejected_topic(text: str, last_topic: str) -> str:
    normalized = _normalize(text)
    for alias, topic in KNOWN_TOPIC_ALIASES.items():
        if alias in normalized:
            return topic

    patterns = [
        r"(?:不|别|先不)(?:聊|学|看|讲|说)\s*(?P<topic>[A-Za-z0-9+#.\u4e00-\u9fff -]{1,40})",
        r"(?:不要|换掉)\s*(?P<topic>[A-Za-z0-9+#.\u4e00-\u9fff -]{1,40})",
    ]
    topic = _extract_topic_by_patterns(text, patterns)
    return topic or last_topic


def _is_topic_rejection(text: str) -> bool:
    normalized = _normalize(text)
    if normalized in {"不要这个", "不学这个", "先不看这个", "别讲这个", "不要了", "不聊了"}:
        return True
    return bool(re.search(r"(?:不|别|先不)(?:聊|学|看|讲|说)|(?:不要|换掉)这个", text, re.IGNORECASE))


def _looks_like_learning_request(text: str) -> bool:
    normalized = _normalize(text)
    if any(marker in normalized for marker in RESOURCE_ACTION_MARKERS):
        return True
    return bool(_extract_topic_by_patterns(text, LEARNING_START_PATTERNS))


def _looks_like_concept_question(text: str) -> bool:
    normalized = _normalize(text)
    if any(marker in normalized for marker in RESOURCE_ACTION_MARKERS):
        return False
    return bool(_extract_topic_by_patterns(text, CONCEPT_QUESTION_PATTERNS, allow_known_fallback=False))


def route_turn(db: Session, username: str, session_id: str, text: str) -> TurnRoute:
    raw_text = (text or "").strip()
    normalized = _normalize(raw_text)
    last_topic = get_last_topic(db, username, session_id)

    if not normalized or normalized in {"?", "？", "...", "。。。"}:
        return TurnRoute(
            route_type="clarification_needed",
            topic=last_topic,
            student_reply=replies.reply_clarification_needed(),
        )

    if _is_topic_rejection(raw_text):
        topic = _extract_rejected_topic(raw_text, last_topic)
        return TurnRoute(
            route_type="topic_rejection",
            should_clear_topic=True,
            topic=topic,
            student_reply=replies.reply_topic_rejection(topic),
        )

    if normalized in TOPIC_SWITCH_TEXTS:
        return TurnRoute(
            route_type="topic_switch",
            should_clear_topic=True,
            student_reply=replies.reply_topic_switch(),
        )

    if normalized in ACKNOWLEDGEMENTS:
        return TurnRoute(
            route_type="acknowledgement",
            topic=last_topic,
            student_reply=replies.reply_acknowledgement(last_topic),
        )

    if normalized in CONTINUE_PREVIOUS_TEXTS:
        if last_topic:
            return TurnRoute(
                route_type="continue_previous",
                should_run_retrieval=True,
                topic=last_topic,
            )
        return TurnRoute(
            route_type="clarification_needed",
            student_reply=replies.reply_continue_without_topic(),
        )

    if normalized in FOLLOWUP_TEXTS and last_topic:
        return TurnRoute(
            route_type="followup",
            should_run_retrieval=True,
            topic=last_topic,
        )

    if normalized in CASUAL_CHAT_TEXTS:
        return TurnRoute(
            route_type="casual_chat",
            topic=last_topic,
            student_reply=replies.reply_casual_chat(),
        )

    if normalized in META_UNKNOWN_TEXTS:
        return TurnRoute(
            route_type="meta_question",
            topic=last_topic,
            student_reply=replies.reply_meta_question(),
        )

    if normalized in META_CAPABILITY_TEXTS:
        return TurnRoute(
            route_type="meta_question",
            topic=last_topic,
            student_reply=replies.reply_capability_intro(),
        )

    if normalized in AMBIGUOUS_TEXTS or (len(normalized) <= 2 and not last_topic):
        return TurnRoute(
            route_type="clarification_needed",
            topic=last_topic,
            student_reply=replies.reply_clarification_needed(),
        )

    if _looks_like_concept_question(raw_text):
        return TurnRoute(
            route_type="concept_question",
            should_run_intent_agent=True,
            should_run_retrieval=True,
            should_update_profile=True,
            topic=_extract_topic_by_patterns(raw_text, CONCEPT_QUESTION_PATTERNS, allow_known_fallback=False),
        )

    if _looks_like_learning_request(raw_text):
        return TurnRoute(
            route_type="learning_request",
            should_run_full_agents=True,
            should_run_intent_agent=True,
            should_run_retrieval=True,
            should_run_planner=True,
            should_generate_resources=True,
            should_update_profile=True,
            topic=_extract_topic_by_patterns(raw_text, LEARNING_START_PATTERNS),
        )

    if last_topic and len(normalized) <= 12:
        return TurnRoute(
            route_type="followup",
            should_run_retrieval=True,
            topic=last_topic,
        )

    return TurnRoute(
        route_type="out_of_scope",
        topic=last_topic,
        student_reply=replies.reply_out_of_scope(),
    )
