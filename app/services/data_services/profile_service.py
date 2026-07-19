# app/services/data_services/profile_service.py

import json
import datetime
from collections import Counter
from typing import List, Dict, Optional

from app.models.schemas import EvaluationRecord, LearningPlan, TodoList
from app.services.data_services import diagnosis_engine_service
from app.services.data_services.knowledge_tag_service import (
    extract_knowledge_tags_from_text,
    normalize_knowledge_tag,
    summarize_knowledge_tags,
)


LEGACY_PROFILE_TERMS = []


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


def _compact_text(value: str) -> str:
    return "".join(str(value or "").lower().split())


def _contains_legacy_terms(value: str) -> bool:
    return any(term.lower() in str(value or "").lower() for term in LEGACY_PROFILE_TERMS)


def _topic_matches_text(topic: str, subject_category: str, text: str) -> bool:
    compact = _compact_text(text)
    topic_compact = _compact_text(topic)
    if topic_compact and topic_compact in compact:
        return True

    subject_aliases = {
        "data_structures_algorithms": [
            "数据结构",
            "算法",
            "复杂度",
            "数组",
            "链表",
            "栈",
            "队列",
            "递归",
            "二分查找",
            "排序",
            "哈希表",
            "堆",
            "树",
            "图",
            "bfs",
            "dfs",
            "最短路径",
            "贪心",
            "动态规划",
            "字符串匹配",
        ],
    }.get(subject_category, [])
    return any(_compact_text(alias) in compact for alias in subject_aliases)


def _level_from_explicit_text(message: str) -> Dict:
    text = str(message or "")
    compact = _compact_text(text)
    explicit_patterns = [
        ("零基础", ["零基础", "完全不会", "没学过", "从零开始"]),
        ("入门", ["入门", "初学", "初级", "刚开始"]),
        ("基础", ["有基础", "学过一点", "基础"]),
        ("进阶", ["进阶", "中级", "b1", "b2", "n2", "n1", "四级", "六级"]),
        ("高级", ["高级", "熟练", "c1", "c2", "专八"]),
    ]
    for level, aliases in explicit_patterns:
        if any(_compact_text(alias) in compact for alias in aliases):
            return {
                "level": level,
                "level_source": "user_explicit",
                "level_evidence": f"本轮输入包含水平表达：{level}",
                "needs_level_diagnosis": False,
            }
    return {}


def _level_from_score(score: int) -> str:
    if score < 60:
        return "入门"
    if score < 75:
        return "基础"
    if score < 88:
        return "进阶"
    return "高级"


def infer_topic_level_from_evidence(db, username: str, topic: str, subject_category: str, message: str) -> Dict:
    explicit = _level_from_explicit_text(message)
    if explicit:
        return explicit

    result = {
        "level": "未确认",
        "level_source": "none",
        "level_evidence": "",
        "needs_level_diagnosis": True,
    }
    if not db or not username or not topic or topic == "未确认主题":
        return result

    try:
        records = (
            db.query(EvaluationRecord)
            .filter(
                EvaluationRecord.username == username,
                ~EvaluationRecord.diagnosis_type.like("legacy_invalid%"),
            )
            .order_by(EvaluationRecord.created_at.desc())
            .limit(20)
            .all()
        )
        matched_scores = [
            record.score
            for record in records
            if record.score is not None
            and str(record.diagnosis_type or "") in diagnosis_engine_service.VERIFIED_EVALUATION_TYPES
            if _topic_matches_text(topic, subject_category, " ".join([
                record.topic or "",
                record.level or "",
                record.weak_points or "",
                record.suggestions or "",
            ]))
        ]
        if matched_scores:
            avg_score = round(sum(matched_scores) / len(matched_scores))
            return {
                "level": _level_from_score(avg_score),
                "level_source": "same_topic_evaluation",
                "level_evidence": f"同主题评价记录 {len(matched_scores)} 条，均分 {avg_score}",
                "needs_level_diagnosis": False,
            }
    except Exception:
        pass

    try:
        plan_record = (
            db.query(LearningPlan)
            .filter(LearningPlan.username == username)
            .first()
        )
        plans = _safe_json_load(plan_record.plans_json if plan_record else "", [])
        matched_total = 0
        matched_done = 0
        for plan in plans:
            plan_text = " ".join([plan.get("title", ""), json.dumps(plan.get("tasks", []), ensure_ascii=False)])
            if not _topic_matches_text(topic, subject_category, plan_text):
                continue
            for task in plan.get("tasks", []):
                matched_total += 1
                if _is_task_completed(task):
                    matched_done += 1
        if matched_total and matched_done:
            rate = round(matched_done / matched_total * 100)
            return {
                "level": "基础" if rate < 70 else "进阶",
                "level_source": "same_topic_plan",
                "level_evidence": f"同主题学习路线完成 {matched_done}/{matched_total}",
                "needs_level_diagnosis": False,
            }
    except Exception:
        pass

    try:
        todo_record = (
            db.query(TodoList)
            .filter(TodoList.username == username)
            .first()
        )
        todos = _safe_json_load(todo_record.todos_json if todo_record else "", [])
        matched = [
            item for item in todos
            if _topic_matches_text(topic, subject_category, json.dumps(item, ensure_ascii=False))
        ]
        done = [item for item in matched if item.get("done")]
        if matched and done:
            return {
                "level": "基础",
                "level_source": "same_topic_todo",
                "level_evidence": f"同主题待办完成 {len(done)}/{len(matched)}",
                "needs_level_diagnosis": False,
            }
    except Exception:
        pass

    return result


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
            .filter(
                EvaluationRecord.username == username,
                ~EvaluationRecord.diagnosis_type.like("legacy_invalid%"),
            )
            .order_by(EvaluationRecord.created_at.desc())
            .limit(10)
            .all()
        )

        scores = []
        weak_points = []
        topics = []

        for record in records:
            record_text = " ".join([record.topic or "", record.weak_points or "", record.suggestions or "", record.wrong_notes or ""])
            if _contains_legacy_terms(record_text):
                continue
            if (
                record.score is not None
                and str(record.diagnosis_type or "") in diagnosis_engine_service.VERIFIED_EVALUATION_TYPES
            ):
                scores.append(record.score)
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
    db=None,
    semantic_result: Optional[Dict] = None
) -> Dict:
    """
    构建动态学习画像。

    画像不再只看标签或固定文案，而是统一复用 diagnosis_engine_service
    聚合的评价、练习、规划、资源反馈和对话行为证据。
    """
    return diagnosis_engine_service.build_behavior_profile(
        db=db,
        user=user,
        message=message,
        intent=intent,
        knowledge_topic=knowledge_topic,
        score=score,
        semantic_result=semantic_result or {},
    )


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
