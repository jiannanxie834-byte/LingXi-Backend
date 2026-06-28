import re

from app.services.data_services import dsa_course_map_service


PRIMARY_COURSE_DISPLAY_NAME = "数据结构与算法"
PRIMARY_COURSE_TITLE = dsa_course_map_service.COURSE_DISPLAY_NAME

CANONICAL_TOPIC_NAMES = {
    "dsa": PRIMARY_COURSE_DISPLAY_NAME,
    "data structures": PRIMARY_COURSE_DISPLAY_NAME,
    "algorithm": "算法",
    "algorithms": "算法",
    "big-o": "大 O 记号",
    "bigo": "大 O 记号",
    "bfs": "广度优先搜索 BFS",
    "dfs": "深度优先搜索 DFS",
    "dp": "动态规划",
    "kmp": "KMP 算法入门",
    "dijkstra": "Dijkstra 算法",
    "union find": "并查集",
    "并查集": "并查集",
}

OUT_OF_COURSE_ALIASES = {
    "英语": ["英语", "英文", "english"],
    "高数": ["高数", "高等数学", "微积分"],
    "数据库": ["数据库", "mysql", "sql"],
    "操作系统": ["操作系统", "进程", "线程", "linux内核"],
    "计算机网络": ["计算机网络", "tcp", "udp", "http"],
    "信息安全": ["信息安全", "网络安全"],
    "物理": ["物理"],
    "法语": ["法语", "french"],
    "金融": ["金融", "股票", "基金"],
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
    if semantic_result.get("subject_category") == "computer_science":
        return True
    if semantic_result.get("course_id") == dsa_course_map_service.COURSE_ID:
        return True
    if (semantic_result.get("ai_course_map") or {}).get("course_id") == dsa_course_map_service.COURSE_ID:
        return True
    topic = normalize_course_topic(semantic_result.get("topic") or "")
    message = semantic_result.get("message") or semantic_result.get("raw_message") or ""
    return bool(dsa_course_map_service.match_dsa_topic(topic, message).get("matched"))


def build_out_of_scope_reply(topic: str = "", raw_message: str = "") -> str:
    requested_topic = extract_requested_topic(raw_message, topic)
    topic_text = requested_topic if requested_topic and requested_topic != "未确认主题" else "这个主题"
    return f"本系统聚焦{PRIMARY_COURSE_TITLE}课程，「{topic_text}」暂未纳入课程图谱，请期待后续资源完善哦。"
