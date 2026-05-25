# app/services/data_services/profile_service.py

from typing import List, Dict, Optional


# =========================
# 🔹 Tag 处理
# =========================

def merge_tags(old_tags: List[str], new_tags: List[str]) -> List[str]:
    """
    合并标签（去重 + 保序）
    """
    return list(dict.fromkeys([t for t in old_tags + new_tags if t]))


def split_tags(tag_str: Optional[str]) -> List[str]:
    """
    将字符串 tags 转换为 list
    """
    if not tag_str:
        return []
    return [t.strip() for t in tag_str.split(",") if t.strip()]


def join_tags(tags: List[str]) -> str:
    """
    list -> string
    """
    return ",".join(tags)


# =========================
# 🔹 学习强度 / 活跃度
# =========================

def calculate_learning_intensity(hours: int) -> str:
    """
    根据学习时长判断学习强度
    """
    if hours < 20:
        return "低"
    elif hours < 60:
        return "中"
    return "高"


def calculate_engagement(message_len: int) -> int:
    """
    根据输入长度判断参与度
    """
    return max(1, min(15, message_len // 10))


# =========================
# 🔹 学习等级
# =========================

def calculate_level(hours: int, score: int = 0) -> str:
    """
    综合判断学习等级
    """
    base = hours + score / 2

    if base < 30:
        return "初学者"
    elif base < 70:
        return "进阶"
    elif base < 110:
        return "熟练"
    return "高级"


# =========================
# 🔹 学习画像构建（核心）
# =========================

def build_profile(
    user,
    message: str,
    intent: str,
    knowledge_topic: str,
    score: Optional[int] = None
) -> Dict:
    """
    构建学习画像（核心函数）
    """

    old_tags = split_tags(user.tags if user else "")
    hours = user.hours if user else 0

    # 学习意图影响
    intent_boost_map = {
        "概念讲解": 5,
        "实操训练": 10,
        "路径规划": 7,
        "练习巩固": 8,
        "综合学习": 6
    }

    intent_boost = intent_boost_map.get(intent, 5)

    # 参与度
    engagement = calculate_engagement(len(message))

    # 综合评分（画像基础值）
    base_score = 50 + min(30, hours * 1.2)
    final_score = round(
    min(
        100,
        base_score + intent_boost + engagement + (score or 0) * 0.3
    )
)

    level = calculate_level(hours, score or 0)
    intensity = calculate_learning_intensity(hours)

    tags = merge_tags(old_tags, [knowledge_topic, intent])

    return {
        "tags": tags,
        "dimensions": {
            "知识基础": round(final_score),
            "学习强度": intensity,
            "学习目标": intent,
            "认知水平": level,
            "知识短板": "需要进一步强化核心概念理解",
            "实践能力": 85 if intent == "实操训练" else 60,
            "学习专注度": engagement * 5,
        },
        "radar": {
            "base_score": round(base_score),
            "intent_boost": intent_boost,
            "engagement": engagement,
            "final_score": round(final_score)
        }
    }


# =========================
# 🔹 学习状态更新（不操作DB，只算结果）
# =========================

def update_learning_state(
    user,
    new_tags: List[str],
    hours_delta: int
) -> Dict:
    """
    更新学习状态（只计算，不落库）
    """

    old_tags = split_tags(user.tags if user else "")
    merged = merge_tags(old_tags, new_tags)

    new_hours = (user.hours or 0) + hours_delta if user else hours_delta

    return {
        "tags": merged,
        "hours": new_hours,
        "intensity": calculate_learning_intensity(new_hours)
    }


# =========================
# 🔹 学习路径辅助判断
# =========================

def infer_learning_focus(intent: str) -> List[str]:
    """
    根据意图给出学习侧重点
    """

    mapping = {
        "概念讲解": ["理解核心概念", "建立知识框架"],
        "实操训练": ["动手实践", "代码实现", "案例训练"],
        "路径规划": ["规划学习路线", "分阶段目标"],
        "练习巩固": ["刷题", "错题复盘"],
        "综合学习": ["全面学习", "知识整合"]
    }

    return mapping.get(intent, ["基础学习", "理解知识"])