# app/services/data_services/profile_service.py

import json
import datetime
from collections import Counter
from typing import List, Dict, Optional

from app.models.schemas import EvaluationRecord, LearningPlan, TodoList
from app.services.data_services.knowledge_tag_service import (
    extract_knowledge_tags_from_text,
    normalize_knowledge_tag,
    summarize_knowledge_tags,
)


# =========================
# 🔹 Tag 处理
# =========================

def merge_tags(old_tags: List[str], new_tags: List[str]) -> List[str]:
    """
    合并标签（去重 + 保序）
    """
    return summarize_knowledge_tags(old_tags + new_tags)


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


def _safe_json_load(data, default):
    try:
        return json.loads(data) if data else default
    except Exception:
        return default


def _clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, int(round(value))))


def _is_task_completed(task: dict) -> bool:
    status = str(task.get("status", "")).lower()
    return bool(task.get("done")) or status in {"completed", "done", "已完成", "finished"}


def _load_profile_evidence(db, username: str) -> Dict:
    evidence = {
        "evaluation_count": 0,
        "recent_avg_score": None,
        "weak_points": [],
        "evaluated_topics": [],
        "plan_count": 0,
        "plan_total_tasks": 0,
        "plan_completed_tasks": 0,
        "plan_completion_rate": None,
        "todo_total": 0,
        "todo_done": 0,
        "todo_completion_rate": None,
    }

    if not db or not username:
        return evidence

    try:
        records = (
            db.query(EvaluationRecord)
            .filter(EvaluationRecord.username == username)
            .order_by(EvaluationRecord.created_at.desc())
            .limit(10)
            .all()
        )

        scores = []
        weak_points = []
        topics = []

        for record in records:
            scores.append(record.score or 0)
            if record.topic:
                topics.append(record.topic)
            weak_points.extend(_safe_json_load(record.weak_points, []))

        evidence["evaluation_count"] = len(records)
        evidence["recent_avg_score"] = round(sum(scores) / len(scores)) if scores else None
        evidence["weak_points"] = [item for item, _ in Counter(weak_points).most_common(5)]
        evidence["evaluated_topics"] = topics
    except Exception:
        pass

    try:
        plan_record = (
            db.query(LearningPlan)
            .filter(LearningPlan.username == username)
            .first()
        )
        plans = _safe_json_load(plan_record.plans_json if plan_record else "", [])
        total_tasks = 0
        completed_tasks = 0

        for plan in plans:
            for task in plan.get("tasks", []):
                total_tasks += 1
                if _is_task_completed(task):
                    completed_tasks += 1

        evidence["plan_count"] = len(plans)
        evidence["plan_total_tasks"] = total_tasks
        evidence["plan_completed_tasks"] = completed_tasks
        evidence["plan_completion_rate"] = round(completed_tasks / total_tasks * 100) if total_tasks else None
    except Exception:
        pass

    try:
        todo_record = (
            db.query(TodoList)
            .filter(TodoList.username == username)
            .first()
        )
        todos = _safe_json_load(todo_record.todos_json if todo_record else "", [])
        todo_total = len(todos)
        todo_done = sum(1 for item in todos if item.get("done"))

        evidence["todo_total"] = todo_total
        evidence["todo_done"] = todo_done
        evidence["todo_completion_rate"] = round(todo_done / todo_total * 100) if todo_total else None
    except Exception:
        pass

    return evidence


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
    score: Optional[int] = None,
    db=None
) -> Dict:
    """
    构建学习画像（核心函数）
    """

    old_tags = split_tags(user.tags if user else "")
    hours = user.hours if user else 0
    username = user.username if user else ""
    evidence = _load_profile_evidence(db, username)

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
    recent_avg_score = evidence.get("recent_avg_score")
    history_score = recent_avg_score if recent_avg_score is not None else (score or 70)

    final_score = round(
        min(
            100,
            base_score + intent_boost + engagement + history_score * 0.18
        )
    )

    level = calculate_level(hours, score or 0)
    intensity = calculate_learning_intensity(hours)

    topic_candidates = (
        [knowledge_topic]
        + extract_knowledge_tags_from_text(message)
        + evidence.get("evaluated_topics", [])
        + old_tags
    )
    normalized_topic_candidates = [
        normalized
        for normalized in (normalize_knowledge_tag(item) for item in topic_candidates)
        if normalized
    ]
    high_frequency_topics = [
        item for item, _ in Counter(normalized_topic_candidates).most_common(3)
    ]
    weak_points = evidence.get("weak_points") or ["需要进一步强化核心概念理解"]

    plan_rate = evidence.get("plan_completion_rate")
    todo_rate = evidence.get("todo_completion_rate")
    plan_score = plan_rate if plan_rate is not None else min(80, 45 + evidence.get("plan_count", 0) * 12)
    todo_score = todo_rate if todo_rate is not None else min(75, 45 + evidence.get("todo_done", 0) * 8)
    execution_score = _clamp(plan_score * 0.6 + todo_score * 0.4)

    self_drive_score = _clamp(
        45
        + engagement * 3
        + min(20, evidence.get("plan_count", 0) * 5)
        + min(20, evidence.get("todo_done", 0) * 4)
    )
    practice_score = _clamp(
        (85 if intent == "实操训练" else 55)
        + (plan_rate or 0) * 0.18
        + (todo_rate or 0) * 0.12
    )
    weak_fix_score = _clamp(
        (recent_avg_score if recent_avg_score is not None else 65)
        + min(10, evidence.get("evaluation_count", 0) * 2)
    )
    cognitive_match_score = _clamp(
        62
        + min(18, len(high_frequency_topics) * 6)
        + (10 if knowledge_topic in old_tags else 0)
    )
    focus_score = _clamp(engagement * 5 + min(25, hours // 2))

    style = "问题修复型" if evidence.get("evaluation_count") else "探索理解型"
    if intent == "路径规划":
        style = "规划执行型"
    elif intent == "实操训练":
        style = "实践应用型"
    elif intent == "练习巩固":
        style = "练习复盘型"

    tags = summarize_knowledge_tags(topic_candidates)

    return {
        "tags": tags,
        "knowledge_tags": tags,
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "dimensions": {
            "知识基础": round(final_score),
            "自驱探索力": self_drive_score,
            "学习强度": intensity,
            "学习目标": intent,
            "认知水平": level,
            "认知风格": style,
            "高频主题": "、".join(high_frequency_topics) if high_frequency_topics else (tags[0] if tags else knowledge_topic),
            "知识短板": "；".join(weak_points[:3]),
            "实践能力": practice_score,
            "学习专注度": focus_score,
            "计划完成率": f"{plan_rate}%" if plan_rate is not None else "暂无计划完成记录",
            "待办完成率": f"{todo_rate}%" if todo_rate is not None else "暂无待办完成记录",
            "历史评价均分": recent_avg_score if recent_avg_score is not None else "暂无评价记录",
            "画像依据": "近期知识点、历史诊断、学习计划、待办完成度、本轮交互",
        },
        "radar": {
            "知识基础": _clamp(final_score),
            "自驱探索力": self_drive_score,
            "实践动手能力": practice_score,
            "学习专注度": focus_score,
            "易错点修复": weak_fix_score,
            "认知匹配度": cognitive_match_score,
        },
        "evidence": {
            "evaluation_count": evidence.get("evaluation_count", 0),
            "recent_avg_score": recent_avg_score,
            "weak_points": weak_points[:3],
            "plan_count": evidence.get("plan_count", 0),
            "plan_completion_rate": plan_rate,
            "todo_completion_rate": todo_rate,
            "high_frequency_topics": high_frequency_topics,
            "knowledge_tags": tags,
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
