import datetime
import hashlib
import json
import math
from collections import Counter
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.schemas import (
    ChatMessage,
    EvaluationRecord,
    ExerciseAttempt,
    LearningPlan,
    ResourceArtifact,
    ResourceFeedback,
    TodoList,
)
from app.services.data_services.knowledge_tag_service import (
    extract_knowledge_tags_from_text,
    normalize_knowledge_tag,
    summarize_knowledge_tags,
)
from app.services.data_services.profile_dimension_service import (
    make_score_dimension,
    make_tags_dimension,
    make_text_dimension,
)


PROFILE_DIMENSIONS = [
    "知识基础",
    "学习目标",
    "概念理解",
    "练习表现",
    "实践能力",
    "规划执行",
    "复盘能力",
    "易错修复",
    "媒介偏好",
    "兴趣方向",
]

RUBRIC_VERSION = "evidence_v2_2026_07"
DERIVED_DIAGNOSIS_TYPES = {
    "auto_multi_factor",
    "manual_multi_factor",
    "exercise_ai_grading",
    "topic_matched",
    "course_general",
}
VERIFIED_EVALUATION_TYPES = {
    "teacher_assessment",
    "verified_assessment",
}

LEGACY_EVALUATION_TERMS = [
    "深度学习导论",
    "深度学习等同",
    "等同于所有人工智能",
    "所有人工智能",
    "神经网络",
    "CNN",
    "RNN",
    "LSTM",
    "Transformer",
    "PyTorch",
    "图像分类",
]

ARRAY_SCOPE_TERMS = [
    "数组",
    "线性表",
    "连续存储",
    "随机访问",
    "下标访问",
    "链表",
]

DSA_TOPIC_TERMS = [
    "复杂度",
    "数组",
    "链表",
    "栈",
    "队列",
    "递归",
    "分治",
    "回溯",
    "排序",
    "二分",
    "二分查找",
    "哈希",
    "哈希表",
    "堆",
    "优先队列",
    "树",
    "二叉树",
    "二叉搜索树",
    "BFS",
    "DFS",
    "广度优先",
    "深度优先",
    "最短路径",
    "Dijkstra",
    "Floyd",
    "最小生成树",
    "并查集",
    "贪心",
    "动态规划",
    "状态转移",
    "字符串",
    "KMP",
    "Trie",
    "图",
]


def _safe_json_load(data, default):
    try:
        return json.loads(data) if data else default
    except Exception:
        return default


def _clamp(value, low: int = 0, high: int = 100) -> int:
    try:
        return max(low, min(high, int(round(float(value)))))
    except Exception:
        return low


def _weighted_average(values: List[float]) -> Optional[int]:
    clean = [float(item) for item in values if item is not None]
    if not clean:
        return None
    weights = [1 / (idx + 1) for idx, _ in enumerate(clean)]
    return _clamp(sum(value * weights[idx] for idx, value in enumerate(clean)) / sum(weights))


def _iso_time(value) -> str:
    if not value:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat(timespec="seconds")
    return str(value)


def _answer_stats(answers: Dict) -> Dict:
    answers = answers if isinstance(answers, dict) else {}
    grading = answers.get("grading") if isinstance(answers.get("grading"), dict) else {}
    submitted = answers.get("answers") if isinstance(answers.get("answers"), list) else []
    rows = grading.get("per_question") if isinstance(grading.get("per_question"), list) else []
    legacy_submission = any(isinstance(item, dict) and "question" in item for item in submitted)
    answered_count = sum(
        1
        for item in submitted
        if isinstance(item, dict) and str(item.get("answer") or "").strip()
    )
    if (not submitted or legacy_submission) and rows:
        answered_count = sum(
            1
            for item in rows
            if isinstance(item, dict)
            and str(item.get("student_answer") or "").strip()
            and str(item.get("status") or "") != "skipped"
        )
        if not any("student_answer" in (item or {}) for item in rows):
            all_rows_report_blank = all(
                any(marker in str((item or {}).get("feedback") or "") for marker in ["答案为空", "未作答"])
                for item in rows
            )
            if all_rows_report_blank:
                answered_count = 0
    question_count = len(rows) if legacy_submission and rows else (len(submitted) or len(rows))
    answers_viewed = bool(grading.get("answers_viewed") or answers.get("answers_viewed"))
    explicitly_invalid = grading.get("valid_for_mastery") is False
    valid = bool(answered_count > 0 and not answers_viewed and not explicitly_invalid)
    if answers_viewed:
        invalid_reason = "作答前已查看参考答案"
    elif answered_count <= 0:
        invalid_reason = "没有填写任何答案"
    elif explicitly_invalid:
        invalid_reason = str(grading.get("invalid_reason") or "记录已标记为无效")
    else:
        invalid_reason = ""
    return {
        "answered_count": answered_count,
        "question_count": question_count,
        "completion_rate": round(answered_count / question_count, 4) if question_count else 0,
        "answers_viewed": answers_viewed,
        "valid_for_mastery": valid,
        "invalid_reason": invalid_reason,
    }


def _attempt_reliability(answers: Dict) -> float:
    grading = answers.get("grading") if isinstance(answers, dict) and isinstance(answers.get("grading"), dict) else {}
    rows = grading.get("per_question") if isinstance(grading.get("per_question"), list) else []
    if not rows:
        return 0.85
    weights = []
    for row in rows:
        question_type = str((row or {}).get("type") or "")
        if question_type in {"single_choice", "true_false"}:
            weights.append(1.0)
        elif question_type == "code":
            weights.append(0.95)
        else:
            weights.append(0.8)
    return round(sum(weights) / len(weights), 3)


def _event_age_days(created_at) -> float:
    if not created_at:
        return 365.0
    value = created_at
    if isinstance(value, str):
        try:
            value = datetime.datetime.fromisoformat(value)
        except ValueError:
            return 365.0
    if not isinstance(value, datetime.datetime):
        return 365.0
    now = datetime.datetime.now(tz=value.tzinfo) if value.tzinfo else datetime.datetime.now()
    return max(0.0, (now - value).total_seconds() / 86400)


def _event_weight(event: Dict) -> float:
    reliability = max(0.0, min(1.0, float(event.get("reliability") or 0)))
    completion = max(0.0, min(1.0, float(event.get("completion_rate") or 0)))
    recency = math.pow(0.5, _event_age_days(event.get("created_at")) / 30)
    return reliability * completion * recency


def _evidence_hash(resolved: Dict, events: List[Dict], execution_rate) -> str:
    payload = {
        "rubric_version": RUBRIC_VERSION,
        "topic": str((resolved or {}).get("topic") or ""),
        "unit_ids": sorted((resolved or {}).get("unit_ids") or []),
        "execution_rate": execution_rate,
        "events": [
            {
                "source_id": item.get("source_id"),
                "source_type": item.get("source_type"),
                "score": item.get("score"),
                "answered_count": item.get("answered_count"),
                "question_count": item.get("question_count"),
                "created_at": _iso_time(item.get("created_at")),
            }
            for item in sorted(events, key=lambda row: str(row.get("source_id") or ""))
        ],
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _is_task_completed(task: dict) -> bool:
    status = str(task.get("status", "")).lower()
    return bool(task.get("done")) or status in {"completed", "done", "已完成", "finished"}


def _normalized_terms(*values) -> List[str]:
    terms = []
    for value in values:
        if isinstance(value, list):
            terms.extend(value)
        elif value:
            terms.append(str(value))
    return [
        normalized
        for normalized in (normalize_knowledge_tag(item) for item in terms)
        if normalized
    ]


def _overlaps_topic(record_text: str, resolved: Dict) -> bool:
    resolved = resolved or {}
    topic = str((resolved or {}).get("topic") or "").strip()
    if topic and topic in str(record_text or ""):
        return True
    unit_titles = resolved.get("unit_titles") or []
    if any(title and title in str(record_text or "") for title in unit_titles):
        return True
    unit_ids = resolved.get("unit_ids") or []
    return any(unit_id and unit_id in str(record_text or "") for unit_id in unit_ids)


def contains_legacy_term(value) -> bool:
    text = str(value or "")
    return any(term and term in text for term in LEGACY_EVALUATION_TERMS)


def _is_general_diagnosis(resolved: Dict) -> bool:
    resolved = resolved or {}
    if resolved.get("chapter_id") or resolved.get("section_id") or resolved.get("unit_ids"):
        return False
    topic = str(resolved.get("topic") or "")
    return not topic or "数据结构与算法学习诊断" in topic or topic == "数据结构与算法"


def _allows_array_misconception(resolved: Dict, source_text: str = "") -> bool:
    scope_text = " ".join(
        [
            str((resolved or {}).get("topic") or ""),
            str((resolved or {}).get("chapter_title") or ""),
            str((resolved or {}).get("section_title") or ""),
            " ".join((resolved or {}).get("unit_titles") or []),
            " ".join((resolved or {}).get("unit_ids") or []),
            str(source_text or ""),
        ]
    )
    return any(term in scope_text for term in ARRAY_SCOPE_TERMS)


def _scope_text(resolved: Dict, source_text: str = "") -> str:
    return " ".join(
        [
            str((resolved or {}).get("topic") or ""),
            str((resolved or {}).get("chapter_title") or ""),
            str((resolved or {}).get("section_title") or ""),
            " ".join((resolved or {}).get("unit_titles") or []),
            " ".join((resolved or {}).get("unit_ids") or []),
            str(source_text or ""),
        ]
    )


def _is_scope_compatible_item(text: str, resolved: Dict, source_text: str = "") -> bool:
    if _is_general_diagnosis(resolved):
        return True
    mentioned_terms = [term for term in DSA_TOPIC_TERMS if term in text]
    if not mentioned_terms:
        return True
    scope = _scope_text(resolved, source_text)
    return any(term in scope for term in mentioned_terms)


def filter_relevant_items(items, *, resolved: Dict = None, source_text: str = "") -> List[str]:
    resolved = resolved or {}
    clean = []
    for item in items or []:
        text = str(item or "").strip()
        if not text or contains_legacy_term(text):
            continue
        if "认为数组所有操作都是 O(1)" in text and not _allows_array_misconception(resolved, source_text):
            continue
        if not _is_scope_compatible_item(text, resolved, source_text):
            continue
        clean.append(text)
    return list(dict.fromkeys(clean))


def _record_can_contribute_topic_diagnosis(record_text: str, resolved: Dict) -> bool:
    return _is_general_diagnosis(resolved) or _overlaps_topic(record_text, resolved)


def collect_learning_evidence(db: Session, username: str, resolved: Dict = None, current_text: str = "") -> Dict:
    resolved = resolved or {}
    evidence = {
        "evaluation_records": [],
        "exercise_attempts": [],
        "learning_plans": [],
        "resource_artifacts": [],
        "resource_feedback": [],
        "chat_messages": [],
        "mastery_events": [],
        "excluded_evidence": [],
        "evaluation_scores": [],
        "topic_evaluation_scores": [],
        "exercise_scores": [],
        "topic_exercise_scores": [],
        "weak_points": [],
        "suggestions": [],
        "topics": [],
        "resource_types": [],
        "plan_total_tasks": 0,
        "plan_completed_tasks": 0,
        "todo_total": 0,
        "todo_done": 0,
        "average_resource_rating": None,
    }
    if not db or not username:
        return evidence

    try:
        rows = (
            db.query(EvaluationRecord)
            .filter(
                EvaluationRecord.username == username,
                ~EvaluationRecord.diagnosis_type.like("legacy_invalid%"),
            )
            .order_by(EvaluationRecord.created_at.desc())
            .limit(30)
            .all()
        )
        for row in rows:
            row_text = " ".join([row.topic or "", row.weak_points or "", row.suggestions or "", row.wrong_notes or ""])
            row_scope_text = " ".join([
                row.topic or "",
                getattr(row, "chapter_id", "") or "",
                getattr(row, "section_id", "") or "",
                getattr(row, "unit_ids_json", "") or "",
                row.wrong_notes or "",
            ])
            if contains_legacy_term(row.topic) or contains_legacy_term(row.wrong_notes):
                continue
            weak_points = _safe_json_load(row.weak_points, [])
            suggestions = _safe_json_load(row.suggestions, [])
            relevant_to_current = _record_can_contribute_topic_diagnosis(row_text, resolved)
            display_weak_points = filter_relevant_items(
                weak_points,
                resolved=resolved if relevant_to_current else {},
                source_text=row_scope_text,
            ) if relevant_to_current else []
            display_suggestions = filter_relevant_items(
                suggestions,
                resolved=resolved if relevant_to_current else {},
                source_text=row_scope_text,
            ) if relevant_to_current else []
            diagnosis_type = getattr(row, "diagnosis_type", "") or "manual"
            item = {
                "id": row.id,
                "topic": row.topic,
                "score": row.score,
                "level": row.level,
                "weak_points": display_weak_points,
                "suggestions": display_suggestions,
                "diagnosis_type": diagnosis_type,
                "created_at": _iso_time(row.created_at),
            }
            evidence["evaluation_records"].append(item)
            if row.topic:
                evidence["topics"].append(row.topic)
            contributes_mastery = bool(
                relevant_to_current
                and row.score is not None
                and diagnosis_type in VERIFIED_EVALUATION_TYPES
            )
            if contributes_mastery:
                score_value = _clamp(row.score)
                evidence["evaluation_scores"].append(score_value)
                evidence["topic_evaluation_scores"].append(score_value)
                evidence["mastery_events"].append({
                    "source_id": row.id,
                    "source_type": "verified_evaluation",
                    "source_name": "教师/认证评价",
                    "score": score_value,
                    "unit_id": "",
                    "answered_count": 1,
                    "question_count": 1,
                    "completion_rate": 1.0,
                    "reliability": 1.0,
                    "created_at": row.created_at,
                })
                evidence["weak_points"].extend(display_weak_points)
                evidence["suggestions"].extend(display_suggestions)
            elif relevant_to_current and diagnosis_type in DERIVED_DIAGNOSIS_TYPES:
                evidence["excluded_evidence"].append({
                    "source_id": row.id,
                    "source_type": diagnosis_type,
                    "reason": "系统诊断快照不能反向作为掌握度证据",
                })
    except Exception:
        pass

    try:
        rows = (
            db.query(ExerciseAttempt)
            .filter(ExerciseAttempt.username == username)
            .order_by(ExerciseAttempt.created_at.desc())
            .limit(30)
            .all()
        )
        for row in rows:
            answers = _safe_json_load(row.answers_json, {})
            grading = answers.get("grading") if isinstance(answers, dict) else {}
            stats = _answer_stats(answers)
            weak_points = grading.get("weak_points") if isinstance(grading, dict) else _safe_json_load(row.error_pattern_json, [])
            suggestions = grading.get("suggestions") if isinstance(grading, dict) else []
            row_text = " ".join([row.unit_id or "", row.error_pattern_json or "", row.answers_json or ""])
            row_scope_text = row.unit_id or ""
            relevant_to_current = (
                _is_general_diagnosis(resolved)
                or (row.unit_id and row.unit_id in (resolved.get("unit_ids") or []))
                or _overlaps_topic(row_text, resolved)
            )
            display_weak_points = filter_relevant_items(
                weak_points or [],
                resolved=resolved if relevant_to_current else {},
                source_text=row_scope_text,
            ) if relevant_to_current else []
            display_suggestions = filter_relevant_items(
                suggestions or [],
                resolved=resolved if relevant_to_current else {},
                source_text=row_scope_text,
            ) if relevant_to_current else []
            item = {
                "attempt_id": row.attempt_id,
                "artifact_id": row.artifact_id,
                "unit_id": row.unit_id,
                "score": row.score,
                **stats,
                "weak_points": display_weak_points,
                "suggestions": display_suggestions,
                "created_at": _iso_time(row.created_at),
            }
            evidence["exercise_attempts"].append(item)
            if relevant_to_current and stats["valid_for_mastery"] and row.score is not None:
                score_value = _clamp(row.score)
                evidence["exercise_scores"].append(score_value)
                evidence["topic_exercise_scores"].append(score_value)
                evidence["mastery_events"].append({
                    "source_id": row.attempt_id,
                    "source_type": "exercise_attempt",
                    "source_name": "有效练习作答",
                    "score": score_value,
                    "unit_id": row.unit_id or "",
                    "answered_count": stats["answered_count"],
                    "question_count": stats["question_count"],
                    "completion_rate": stats["completion_rate"],
                    "reliability": _attempt_reliability(answers),
                    "created_at": row.created_at,
                })
                evidence["weak_points"].extend(display_weak_points)
                evidence["suggestions"].extend(display_suggestions)
            elif relevant_to_current and not stats["valid_for_mastery"]:
                evidence["excluded_evidence"].append({
                    "source_id": row.attempt_id,
                    "source_type": "exercise_attempt",
                    "reason": stats["invalid_reason"],
                })
    except Exception:
        pass

    try:
        plan_record = db.query(LearningPlan).filter(LearningPlan.username == username).first()
        plans = _safe_json_load(plan_record.plans_json if plan_record else "", [])
        current_units = set(resolved.get("unit_ids") or [])
        general_scope = _is_general_diagnosis(resolved)
        for plan in plans:
            evidence["learning_plans"].append({"title": plan.get("title"), "tasks": plan.get("tasks", [])})
            for task in plan.get("tasks", []):
                task_unit = str(task.get("unit_id") or "")
                task_text = " ".join([str(task.get("title") or ""), str(task.get("desc") or "")])
                relevant_task = general_scope or (task_unit and task_unit in current_units) or _overlaps_topic(task_text, resolved)
                status = str(task.get("status") or "").lower()
                started_or_owned = bool(task.get("isCustom")) or status not in {"", "pending", "待开始"}
                if not relevant_task or not started_or_owned:
                    continue
                evidence["plan_total_tasks"] += 1
                if _is_task_completed(task):
                    evidence["plan_completed_tasks"] += 1
    except Exception:
        pass

    try:
        todo_record = db.query(TodoList).filter(TodoList.username == username).first()
        todos = _safe_json_load(todo_record.todos_json if todo_record else "", [])
        relevant_todos = []
        for item in todos:
            text = json.dumps(item, ensure_ascii=False)
            if _is_general_diagnosis(resolved) or _overlaps_topic(text, resolved):
                relevant_todos.append(item)
        evidence["todo_total"] = len(relevant_todos)
        evidence["todo_done"] = sum(1 for item in relevant_todos if item.get("done"))
    except Exception:
        pass

    try:
        rows = (
            db.query(ResourceArtifact)
            .filter(ResourceArtifact.student_id == username)
            .order_by(ResourceArtifact.updated_at.desc())
            .limit(40)
            .all()
        )
        for row in rows:
            evidence["resource_artifacts"].append({
                "artifact_id": row.artifact_id,
                "type": row.type,
                "title": row.title,
                "status": row.status,
                "updated_at": _iso_time(row.updated_at),
            })
            if row.type:
                evidence["resource_types"].append(row.type)
            if row.title:
                evidence["topics"].append(row.title)
    except Exception:
        pass

    try:
        rows = (
            db.query(ResourceFeedback)
            .filter(ResourceFeedback.username == username)
            .order_by(ResourceFeedback.created_at.desc())
            .limit(30)
            .all()
        )
        ratings = []
        for row in rows:
            ratings.append(row.rating or 0)
            evidence["resource_feedback"].append({
                "artifact_id": row.artifact_id,
                "rating": row.rating or 0,
                "comment": row.comment or "",
            })
        evidence["average_resource_rating"] = round(sum(ratings) / len(ratings), 1) if ratings else None
    except Exception:
        pass

    try:
        rows = (
            db.query(ChatMessage)
            .filter(ChatMessage.username == username)
            .order_by(ChatMessage.created_at.desc())
            .limit(20)
            .all()
        )
        for row in rows:
            evidence["chat_messages"].append({
                "role": row.role,
                "content": (row.content or "")[:240],
                "created_at": _iso_time(row.created_at),
            })
    except Exception:
        pass

    current_tags = extract_knowledge_tags_from_text(current_text or "")
    evidence["topics"] = summarize_knowledge_tags(evidence["topics"] + current_tags)
    evidence["weak_points"] = [
        item
        for item, _ in Counter(filter_relevant_items(evidence["weak_points"], resolved=resolved, source_text=current_text)).most_common(8)
    ]
    evidence["suggestions"] = [
        item
        for item, _ in Counter(filter_relevant_items(evidence["suggestions"], resolved=resolved, source_text=current_text)).most_common(8)
    ]
    evidence["mastery_events"].sort(key=lambda item: _iso_time(item.get("created_at")), reverse=True)
    weighted_events = [(item, _event_weight(item)) for item in evidence["mastery_events"]]
    total_event_weight = sum(weight for _, weight in weighted_events)
    observed_score = (
        _clamp(sum(float(item.get("score") or 0) * weight for item, weight in weighted_events) / total_event_weight)
        if total_event_weight > 0
        else None
    )
    evidence["recent_avg_score"] = observed_score
    evidence["topic_avg_score"] = observed_score
    evidence["exercise_avg_score"] = _weighted_average(evidence["exercise_scores"][:10])
    evidence["evaluation_avg_score"] = _weighted_average(evidence["evaluation_scores"][:10])
    total_tasks = evidence["plan_total_tasks"] + evidence["todo_total"]
    done_tasks = evidence["plan_completed_tasks"] + evidence["todo_done"]
    evidence["execution_rate"] = round(done_tasks / total_tasks * 100) if total_tasks else None
    evidence["evidence_count"] = len(evidence["mastery_events"])
    evidence["answered_item_count"] = sum(int(item.get("answered_count") or 0) for item in evidence["mastery_events"])
    evidence["valid_source_count"] = len({item.get("source_type") for item in evidence["mastery_events"]})
    evidence["excluded_evidence_count"] = len(evidence["excluded_evidence"])
    evidence["rubric_version"] = RUBRIC_VERSION
    evidence["evidence_hash"] = _evidence_hash(resolved, evidence["mastery_events"], evidence["execution_rate"])
    return evidence


def calculate_diagnosis(
    *,
    db: Session,
    username: str,
    resolved: Dict,
    current_text: str = "",
    confidence: int = 60,
    current_score: Optional[int] = None,
    current_answered_count: int = 0,
    current_question_count: int = 0,
    current_reliability: float = 0.9,
    mode: str = "auto",
    current_weak_points: Optional[List[str]] = None,
    current_suggestions: Optional[List[str]] = None,
) -> Dict:
    evidence = collect_learning_evidence(db, username, resolved=resolved, current_text=current_text)
    execution_rate = evidence.get("execution_rate")
    events = [dict(item) for item in evidence.get("mastery_events") or []]
    if current_score is not None:
        answered = max(1, int(current_answered_count or current_question_count or 1))
        question_total = max(answered, int(current_question_count or answered))
        events.append({
            "source_id": "current_attempt",
            "source_type": "exercise_attempt",
            "source_name": "本次练习作答",
            "score": _clamp(current_score),
            "unit_id": ((resolved.get("unit_ids") or [""])[0]),
            "answered_count": answered,
            "question_count": question_total,
            "completion_rate": answered / question_total,
            "reliability": max(0.0, min(1.0, float(current_reliability or 0.9))),
            "created_at": datetime.datetime.now(),
        })

    weighted_events = [(item, _event_weight(item)) for item in events]
    total_weight = sum(weight for _, weight in weighted_events)
    observed_score = (
        _clamp(sum(float(item.get("score") or 0) * weight for item, weight in weighted_events) / total_weight)
        if total_weight > 0
        else None
    )
    answered_item_count = sum(int(item.get("answered_count") or 0) for item in events)
    source_count = len({item.get("source_type") for item in events})
    quantity_confidence = min(25.0, answered_item_count / 10 * 25)
    diversity_confidence = min(25.0, source_count / 2 * 25)
    coverage_confidence = 25.0 if events else 0.0
    newest_age = min((_event_age_days(item.get("created_at")) for item in events), default=999)
    recency_confidence = 25.0 if newest_age <= 7 else (18.0 if newest_age <= 30 else (8.0 if newest_age <= 90 else 0.0))
    confidence_score = _clamp(quantity_confidence + diversity_confidence + coverage_confidence + recency_confidence)

    if observed_score is None or confidence_score < 40:
        score = None
        diagnosis_status = "insufficient_evidence"
        level = "证据不足"
    else:
        score = observed_score
        diagnosis_status = "established" if confidence_score >= 70 else "provisional"
        base_level = level_from_score(score)
        level = base_level if diagnosis_status == "established" else f"暂估 · {base_level}"

    score_breakdown = []
    if total_weight > 0:
        for item, raw_weight in sorted(weighted_events, key=lambda pair: _iso_time(pair[0].get("created_at")), reverse=True)[:8]:
            normalized_weight = raw_weight / total_weight
            score_breakdown.append({
                "name": item.get("source_name") or "有效学习证据",
                "source_id": item.get("source_id"),
                "value": _clamp(item.get("score")),
                "weight": round(normalized_weight, 4),
                "contribution": round(_clamp(item.get("score")) * normalized_weight, 1),
                "answered_count": item.get("answered_count") or 0,
                "question_count": item.get("question_count") or 0,
                "created_at": _iso_time(item.get("created_at")),
            })

    reflection_score = None
    if mode == "manual":
        text = str(current_text or "").strip()
        reflection_score = 25 * sum([
            len(text) >= 12,
            any(word in text for word in ["因为", "原因", "错因", "导致"]),
            any(word in text for word in ["改成", "修正", "重做", "调整", "应该"]),
            any(word in text for word in ["验证", "测试", "例子", "边界"]),
        ])

    if score is None:
        weak_points = ["尚无足够的有效作答，当前不能据此判断知识薄弱点。"]
    else:
        weak_points = []
        weak_points.extend(filter_relevant_items(current_weak_points or [], resolved=resolved, source_text=current_text))
        weak_points.extend(filter_relevant_items(evidence.get("weak_points") or [], resolved=resolved, source_text=current_text))
        weak_points.extend(filter_relevant_items(resolved.get("weak_points") or [], resolved=resolved, source_text=current_text))
        if score < 60:
            weak_points.append("当前主题掌握度偏低，需要先修复基础概念和典型题型。")
        elif score < 75:
            weak_points.append("当前主题处于可学习但不稳定状态，需要通过练习巩固边界条件和迁移题。")
    weak_points = [item for item, _ in Counter(filter_relevant_items(weak_points, resolved=resolved, source_text=current_text)).most_common(5)]

    suggestions = []
    suggestions.extend(filter_relevant_items(current_suggestions or [], resolved=resolved, source_text=current_text))
    suggestions.extend(filter_relevant_items(evidence.get("suggestions") or [], resolved=resolved, source_text=current_text))
    suggestions.extend(filter_relevant_items(resolved.get("suggestions") or [], resolved=resolved, source_text=current_text))
    if execution_rate is not None and execution_rate < 60:
        suggestions.append("把学习路线拆成更小任务，优先完成当前小节的讲解、练习和一次代码复现。")
    exercise_avg = evidence.get("exercise_avg_score")
    if exercise_avg is not None and exercise_avg < 70:
        suggestions.append("下一轮学习先做同主题基础题，再做一题边界条件题，并记录错因。")
    if not suggestions:
        suggestions = ["先完成一组同主题练习，再用错题反馈触发下一次补弱诊断。"]
    suggestions = [item for item, _ in Counter(filter_relevant_items(suggestions, resolved=resolved, source_text=current_text)).most_common(5)]

    evidence["mastery_events"] = events
    evidence["evidence_count"] = len(events)
    evidence["answered_item_count"] = answered_item_count
    evidence["valid_source_count"] = source_count
    evidence["confidence_score"] = confidence_score
    evidence["confidence_components"] = {
        "题量": round(quantity_confidence),
        "来源多样性": round(diversity_confidence),
        "主题覆盖": round(coverage_confidence),
        "时效性": round(recency_confidence),
    }
    evidence["reflection_score"] = reflection_score
    evidence["rubric_version"] = RUBRIC_VERSION
    evidence["evidence_hash"] = _evidence_hash(resolved, events, execution_rate)
    return {
        "score": score,
        "level": level,
        "diagnosis_status": diagnosis_status,
        "confidence_score": confidence_score,
        "rubric_version": RUBRIC_VERSION,
        "evidence_hash": evidence["evidence_hash"],
        "reflection_score": reflection_score,
        "weak_points": weak_points,
        "suggestions": suggestions,
        "evidence": evidence,
        "score_breakdown": score_breakdown,
    }


def level_from_score(score: Optional[int]) -> str:
    if score is None:
        return "证据不足"
    if score >= 85:
        return "掌握较好"
    if score >= 70:
        return "基本掌握"
    if score >= 55:
        return "需要巩固"
    return "重点补救"


def build_behavior_profile(
    *,
    db: Session,
    user,
    message: str,
    intent: str,
    knowledge_topic: str,
    score: Optional[int] = None,
    semantic_result: Optional[Dict] = None,
) -> Dict:
    semantic_result = semantic_result or {}
    username = getattr(user, "username", "") if user else ""
    old_tags = [
        item.strip()
        for item in str(getattr(user, "tags", "") or "").split(",")
        if item.strip()
    ]
    resolved = {
        "topic": semantic_result.get("topic_title") or knowledge_topic,
        "chapter_id": semantic_result.get("chapter_id") or "",
        "section_id": semantic_result.get("section_id") or "",
        "unit_ids": semantic_result.get("unit_ids") or [],
        "unit_titles": semantic_result.get("unit_titles") or [],
        "matched": bool(semantic_result.get("chapter_id") or semantic_result.get("unit_ids")),
    }
    evidence = collect_learning_evidence(db, username, resolved=resolved, current_text=message)
    inferred_score = score
    if inferred_score is None:
        inferred_score = evidence.get("topic_avg_score")
    if inferred_score is None:
        inferred_score = evidence.get("recent_avg_score")
    topic_level = semantic_result.get("level") or level_from_score(inferred_score)
    level_source = semantic_result.get("level_source") or ("behavior_evidence" if evidence.get("evidence_count") else "current_interaction")
    level_evidence = semantic_result.get("level_evidence") or f"综合 {evidence.get('evidence_count', 0)} 条评价/练习/规划行为证据。"
    topic_candidates = _normalized_terms(
        knowledge_topic,
        message,
        evidence.get("topics") or [],
        old_tags,
    )
    tags = summarize_knowledge_tags(topic_candidates)
    high_frequency_topics = [item for item, _ in Counter(topic_candidates).most_common(4)]

    current_topic = semantic_result.get("topic_title") or knowledge_topic or "当前主题"
    goal_text = " · ".join(
        item for item in [str(intent or "").strip(), str(current_topic or "").strip()]
        if item
    )
    assessment_intent = any(
        marker in str(intent or "")
        for marker in ["练习批改", "评价", "诊断", "补弱"]
    )
    preference_terms = []
    if not assessment_intent:
        message_text = str(message or "")
        preference_rules = [
            ("图解与导图", ["图解", "导图", "思维导图"]),
            ("视频与动画", ["视频", "动画"]),
            ("代码案例", ["代码", "示例", "实操"]),
            ("练习题", ["练习", "题目", "题库", "刷题"]),
            ("文字讲解", ["文档", "讲义", "文字", "讲解"]),
        ]
        preference_terms = [
            label
            for label, markers in preference_rules
            if any(marker in message_text for marker in markers)
        ]

    base_score = inferred_score if inferred_score is not None else 55
    exercise_score = evidence.get("exercise_avg_score") if evidence.get("exercise_avg_score") is not None else base_score
    execution_rate = evidence.get("execution_rate")
    practice_resources = sum(
        1 for item in evidence.get("resource_types") or []
        if any(marker in str(item) for marker in ["代码", "实验", "项目", "练习"])
    )
    code_or_practice_intent = any(marker in str(intent or "") + str(message or "") for marker in ["实操", "代码", "项目", "练习"])
    message_len = len(str(message or "").strip())

    knowledge_base = _clamp(base_score)
    goal_clarity = _clamp(45 + min(25, message_len / 5) + (15 if intent else 0) + (10 if resolved.get("matched") else 0))
    evaluation_avg = evidence.get("evaluation_avg_score")
    concept_understanding = _clamp((evaluation_avg if evaluation_avg is not None else base_score) * 0.75 + goal_clarity * 0.25)
    exercise_performance = _clamp(exercise_score)
    practice_ability = _clamp(45 + min(24, practice_resources * 6) + (20 if code_or_practice_intent else 0) + (exercise_performance - 50) * 0.25)
    plan_execution = _clamp(execution_rate if execution_rate is not None else 45 + min(25, len(evidence.get("learning_plans") or []) * 10))
    reflection = _clamp(40 + min(24, len(evidence.get("evaluation_records") or []) * 3) + min(16, len(evidence.get("weak_points") or []) * 3) + min(20, message_len / 8))
    error_repair = _clamp((exercise_performance * 0.45) + (concept_understanding * 0.35) + (reflection * 0.20))
    media_preference = _clamp(55 + (15 if any(word in str(message) for word in ["图", "导图", "视频", "动画"]) else 0) + (15 if any(word in str(message) for word in ["代码", "示例", "题"]) else 0))
    interest_focus = _clamp(50 + min(30, len(high_frequency_topics) * 7) + (10 if tags else 0))

    weak_points = evidence.get("weak_points") or ["需要通过练习和评价继续定位薄弱点"]
    dimensions = {
        "知识基础": f"{topic_level}；依据：{level_evidence}",
        "学习目标": intent or "待确认",
        "概念理解": f"{concept_understanding} 分；结合评价均分与当前表达清晰度。",
        "练习表现": f"{exercise_performance} 分；来自最近练习与批改记录。",
        "实践能力": f"{practice_ability} 分；结合代码/项目资源使用和练习表现。",
        "规划执行": f"{plan_execution} 分；来自学习路线和待办完成情况。",
        "复盘能力": f"{reflection} 分；来自错因说明、评价记录和作答反馈。",
        "易错修复": "；".join(weak_points[:3]),
        "媒介偏好": "图解/导图/代码示例优先" if media_preference >= 70 else "文字讲解 + 练习巩固",
        "兴趣方向": "、".join(high_frequency_topics) if high_frequency_topics else (knowledge_topic or "数据结构与算法"),
    }
    radar = {
        "知识基础": knowledge_base,
        "学习目标": goal_clarity,
        "概念理解": concept_understanding,
        "练习表现": exercise_performance,
        "实践能力": practice_ability,
        "规划执行": plan_execution,
        "复盘能力": reflection,
        "易错修复": error_repair,
        "媒介偏好": media_preference,
        "兴趣方向": interest_focus,
    }

    observed_knowledge_score = evidence.get("recent_avg_score")
    observed_knowledge_source = "learning_evidence"
    if score is not None:
        observed_knowledge_score = _clamp(score)
        observed_knowledge_source = semantic_result.get("level_source") or "current_assessment"
    knowledge_status = "observed" if observed_knowledge_score is not None else (
        "reported" if level_source in {"user_explicit", "current_interaction"} and topic_level not in {"", "未确认", "证据不足"}
        else "pending"
    )
    knowledge_display = (
        f"{_clamp(observed_knowledge_score)} 分 · {level_from_score(observed_knowledge_score)}"
        if observed_knowledge_score is not None
        else (f"{topic_level}（学生自述）" if knowledge_status == "reported" else "待有效作答诊断")
    )

    exercise_value = evidence.get("exercise_avg_score")
    exercise_source = "exercise_attempts"
    if score is not None:
        exercise_value = _clamp(score)
        exercise_source = semantic_result.get("level_source") or "current_assessment"
    exercise_display = f"最近有效作答 {_clamp(exercise_value)} 分" if exercise_value is not None else "暂无有效作答"

    current_weak_points = semantic_result.get("weak_points") or []
    public_weak_points = filter_relevant_items(
        list(current_weak_points) + list(evidence.get("weak_points") or []),
        resolved=resolved,
        source_text=message,
    )[:5]
    public_weak_points = [
        item for item in public_weak_points
        if "继续定位" not in item and "尚无足够" not in item
    ]

    public_dimensions = {
        "当前知识水平": make_score_dimension(
            observed_knowledge_score,
            display=knowledge_display,
            evidence=(
                level_evidence
                if observed_knowledge_score is not None or knowledge_status == "reported"
                else "当前只有学习主题和目标，尚无有效作答分数。"
            ),
            source=observed_knowledge_source if observed_knowledge_score is not None else level_source,
            status=knowledge_status,
        ),
        "学习目标": make_text_dimension(
            goal_text,
            evidence=f"本轮对话识别到学习意图“{intent or '待确认'}”，主题为“{current_topic}”。",
            source="dialogue",
            status="reported",
        ),
        "练习表现": make_score_dimension(
            exercise_value,
            display=exercise_display,
            evidence=(
                f"当前有效作答/评价分数为 {_clamp(exercise_value)} 分。"
                if exercise_value is not None
                else "完成可批改练习或有效学习评价后生成。"
            ),
            source=exercise_source if exercise_value is not None else "none",
        ),
        "薄弱知识点": make_tags_dimension(
            public_weak_points,
            pending_text="待练习诊断",
            evidence=(
                "根据错题知识点、作答反馈和学习评价归纳。"
                if public_weak_points
                else "当前没有足够的错题或评价证据。"
            ),
            source="evaluation_records/exercise_attempts" if public_weak_points else "none",
        ),
        "路径执行": make_score_dimension(
            execution_rate,
            display=f"已完成 {_clamp(execution_rate)}%" if execution_rate is not None else "尚无执行记录",
            evidence=(
                f"当前主题的学习路径与待办共完成 {_clamp(execution_rate)}%。"
                if execution_rate is not None
                else "开始执行学习路径或待办后生成。"
            ),
            source="learning_plans/todos" if execution_rate is not None else "none",
        ),
        "资源偏好": make_tags_dimension(
            preference_terms,
            pending_text="待确认",
            evidence=(
                "由学生在本轮对话中主动表达，后续结合资源反馈校正。"
                if preference_terms
                else "在对话中说明希望使用的资源形式后生成。"
            ),
            source="dialogue" if preference_terms else "none",
            status="reported",
        ),
    }
    return {
        "tags": tags,
        "knowledge_tags": tags,
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "dimensions": dimensions,
        "radar": radar,
        "public_dimensions": public_dimensions,
        "evidence": {
            "course_id": semantic_result.get("course_id") or "data_structures_algorithms",
            "chapter_id": semantic_result.get("chapter_id") or "",
            "section_id": semantic_result.get("section_id") or "",
            "unit_ids": semantic_result.get("unit_ids") or [],
            "topic_title": semantic_result.get("topic_title") or knowledge_topic,
            "topic_level": topic_level,
            "level_source": level_source,
            "level_evidence": level_evidence,
            "needs_level_diagnosis": semantic_result.get("needs_level_diagnosis", not bool(evidence.get("evidence_count"))),
            "evidence_count": evidence.get("evidence_count", 0),
            "confidence_score": evidence.get("confidence_score", 0),
            "rubric_version": evidence.get("rubric_version") or RUBRIC_VERSION,
            "recent_avg_score": evidence.get("recent_avg_score"),
            "topic_avg_score": evidence.get("topic_avg_score"),
            "exercise_avg_score": evidence.get("exercise_avg_score"),
            "execution_rate": execution_rate,
            "weak_points": weak_points[:5],
            "high_frequency_topics": high_frequency_topics,
            "dimension_evidence": [
                {"dimension": "知识基础", "evidence": level_evidence, "source": level_source},
                {"dimension": "练习表现", "evidence": f"最近练习均分：{evidence.get('exercise_avg_score') or '暂无'}", "source": "exercise_attempts"},
                {"dimension": "规划执行", "evidence": f"任务完成率：{execution_rate if execution_rate is not None else '暂无'}", "source": "learning_plans/todos"},
                {"dimension": "易错修复", "evidence": "；".join(weak_points[:3]), "source": "evaluation_records/exercise_attempts"},
            ],
        },
    }
