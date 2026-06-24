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


def _compact_text(value: str) -> str:
    return "".join(str(value or "").lower().split())


def _topic_matches_text(topic: str, subject_category: str, text: str) -> bool:
    compact = _compact_text(text)
    topic_compact = _compact_text(topic)
    if topic_compact and topic_compact in compact:
        return True

    subject_aliases = {
        "foreign_language": ["法语", "英语", "日语", "德语", "西班牙语", "韩语", "俄语", "意大利语", "语法", "词汇", "口语", "阅读"],
        "computer_science": ["人工智能", "机器学习", "深度学习", "信息安全", "编程", "代码", "算法", "数据库", "计算机网络"],
        "mathematics": ["数学", "高等数学", "线性代数", "概率论", "统计学", "微积分"],
        "physics": ["物理", "力学", "电磁学", "热学", "光学"],
        "general_course": ["管理学", "经济学", "心理学", "历史", "文学", "哲学", "通识"],
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
            .filter(EvaluationRecord.username == username)
            .order_by(EvaluationRecord.created_at.desc())
            .limit(20)
            .all()
        )
        matched_scores = [
            record.score or 0
            for record in records
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
    db=None,
    semantic_result: Optional[Dict] = None
) -> Dict:
    """
    构建学习画像（核心函数）
    """

    old_tags = split_tags(user.tags if user else "")
    hours = user.hours if user else 0
    username = user.username if user else ""
    evidence = _load_profile_evidence(db, username)
    semantic_result = semantic_result or {}
    subject_category = semantic_result.get("subject_category", "unknown")
    topic_level = semantic_result.get("level") or "未确认"
    level_source = semantic_result.get("level_source") or "none"
    level_evidence = semantic_result.get("level_evidence") or ""
    needs_level_diagnosis = semantic_result.get("needs_level_diagnosis", True)

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
    base_score = 50
    recent_avg_score = evidence.get("recent_avg_score")
    history_score = recent_avg_score if recent_avg_score is not None else (score or 70)

    final_score = round(
        min(
            100,
            base_score + intent_boost + engagement + history_score * 0.18
        )
    )

    intensity = calculate_learning_intensity(hours)
    knowledge_base_score = {
        "零基础": 35,
        "入门": 45,
        "基础": 60,
        "进阶": 75,
        "高级": 88,
    }.get(topic_level, 50)

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
            "知识基础": knowledge_base_score,
            "自驱探索力": self_drive_score,
            "学习强度": intensity,
            "学习目标": intent,
            "认知水平": topic_level,
            "认知风格": style,
            "高频主题": "、".join(high_frequency_topics) if high_frequency_topics else (tags[0] if tags else knowledge_topic),
            "知识短板": "；".join(weak_points[:3]),
            "实践能力": practice_score,
            "学习专注度": focus_score,
            "计划完成率": f"{plan_rate}%" if plan_rate is not None else "暂无计划完成记录",
            "待办完成率": f"{todo_rate}%" if todo_rate is not None else "暂无待办完成记录",
            "历史评价均分": recent_avg_score if recent_avg_score is not None else "暂无评价记录",
            "画像依据": "同主题证据、本轮交互、平台活跃度；全局学习时长不作为当前学科水平依据",
            "水平证据": level_evidence or "暂无同主题水平证据",
            "学科分类": subject_category,
        },
        "radar": {
            "知识基础": _clamp(knowledge_base_score),
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
            "topic_level": topic_level,
            "level_source": level_source,
            "level_evidence": level_evidence,
            "needs_level_diagnosis": needs_level_diagnosis,
            "subject_category": subject_category,
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
