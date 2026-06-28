import datetime
import json
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
            .filter(EvaluationRecord.username == username)
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
            item = {
                "id": row.id,
                "topic": row.topic,
                "score": row.score or 0,
                "level": row.level,
                "weak_points": display_weak_points,
                "suggestions": display_suggestions,
                "diagnosis_type": getattr(row, "diagnosis_type", "") or "manual",
                "created_at": row.created_at.isoformat(timespec="seconds") if row.created_at else "",
            }
            evidence["evaluation_records"].append(item)
            evidence["evaluation_scores"].append(row.score or 0)
            if row.topic:
                evidence["topics"].append(row.topic)
            if relevant_to_current:
                evidence["topic_evaluation_scores"].append(row.score or 0)
                evidence["weak_points"].extend(display_weak_points)
                evidence["suggestions"].extend(display_suggestions)
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
                "score": row.score or 0,
                "weak_points": display_weak_points,
                "suggestions": display_suggestions,
                "created_at": row.created_at.isoformat(timespec="seconds") if row.created_at else "",
            }
            evidence["exercise_attempts"].append(item)
            evidence["exercise_scores"].append(row.score or 0)
            if relevant_to_current:
                evidence["weak_points"].extend(display_weak_points)
                evidence["suggestions"].extend(display_suggestions)
                evidence["topic_exercise_scores"].append(row.score or 0)
    except Exception:
        pass

    try:
        plan_record = db.query(LearningPlan).filter(LearningPlan.username == username).first()
        plans = _safe_json_load(plan_record.plans_json if plan_record else "", [])
        for plan in plans:
            evidence["learning_plans"].append({"title": plan.get("title"), "tasks": plan.get("tasks", [])})
            for task in plan.get("tasks", []):
                evidence["plan_total_tasks"] += 1
                if _is_task_completed(task):
                    evidence["plan_completed_tasks"] += 1
    except Exception:
        pass

    try:
        todo_record = db.query(TodoList).filter(TodoList.username == username).first()
        todos = _safe_json_load(todo_record.todos_json if todo_record else "", [])
        evidence["todo_total"] = len(todos)
        evidence["todo_done"] = sum(1 for item in todos if item.get("done"))
    except Exception:
        pass

    try:
        rows = (
            db.query(ResourceArtifact)
            .filter(ResourceArtifact.student_id.in_([username, ""]))
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
                "updated_at": row.updated_at.isoformat(timespec="seconds") if row.updated_at else "",
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
                "created_at": row.created_at.isoformat(timespec="seconds") if row.created_at else "",
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
    evidence["recent_avg_score"] = _weighted_average(evidence["evaluation_scores"][:10] + evidence["exercise_scores"][:10])
    evidence["topic_avg_score"] = _weighted_average(evidence["topic_evaluation_scores"][:8] + evidence["topic_exercise_scores"][:8])
    evidence["exercise_avg_score"] = _weighted_average(evidence["exercise_scores"][:10])
    evidence["evaluation_avg_score"] = _weighted_average(evidence["evaluation_scores"][:10])
    total_tasks = evidence["plan_total_tasks"] + evidence["todo_total"]
    done_tasks = evidence["plan_completed_tasks"] + evidence["todo_done"]
    evidence["execution_rate"] = round(done_tasks / total_tasks * 100) if total_tasks else None
    evidence["evidence_count"] = (
        len(evidence["evaluation_records"])
        + len(evidence["exercise_attempts"])
        + len(evidence["learning_plans"])
        + len(evidence["resource_feedback"])
    )
    return evidence


def calculate_diagnosis(
    *,
    db: Session,
    username: str,
    resolved: Dict,
    current_text: str = "",
    confidence: int = 60,
    current_score: Optional[int] = None,
    current_weak_points: Optional[List[str]] = None,
    current_suggestions: Optional[List[str]] = None,
) -> Dict:
    evidence = collect_learning_evidence(db, username, resolved=resolved, current_text=current_text)
    topic_avg = evidence.get("topic_avg_score")
    recent_avg = evidence.get("recent_avg_score")
    exercise_avg = evidence.get("exercise_avg_score")
    execution_rate = evidence.get("execution_rate")

    text_len = len(str(current_text or "").strip())
    reflection_score = _clamp(35 + min(30, text_len / 4) + (10 if resolved.get("matched") else 0) + (int(confidence or 0) - 50) * 0.15)
    evidence_score = _clamp(45 + min(35, evidence.get("evidence_count", 0) * 5))

    components = []
    if current_score is not None:
        components.append(("本次作答/评价", _clamp(current_score), 0.45))
    if topic_avg is not None:
        components.append(("同主题历史表现", topic_avg, 0.22))
    if recent_avg is not None:
        components.append(("近期综合表现", recent_avg, 0.14))
    if exercise_avg is not None:
        components.append(("练习题作答表现", exercise_avg, 0.10))
    if execution_rate is not None:
        components.append(("规划执行率", execution_rate, 0.06))
    components.append(("当前反馈质量", reflection_score, 0.08))
    components.append(("行为证据充分度", evidence_score, 0.05))

    total_weight = sum(weight for _, _, weight in components)
    score = _clamp(sum(value * weight for _, value, weight in components) / total_weight)
    if current_score is None and evidence.get("evidence_count", 0) == 0:
        score = _clamp((reflection_score * 0.65) + (int(confidence or 60) * 0.35))

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
    if exercise_avg is not None and exercise_avg < 70:
        suggestions.append("下一轮学习先做同主题基础题，再做一题边界条件题，并记录错因。")
    if not suggestions:
        suggestions = ["先完成一组同主题练习，再用错题反馈触发下一次补弱诊断。"]
    suggestions = [item for item, _ in Counter(filter_relevant_items(suggestions, resolved=resolved, source_text=current_text)).most_common(5)]

    return {
        "score": score,
        "level": level_from_score(score),
        "weak_points": weak_points,
        "suggestions": suggestions,
        "evidence": evidence,
        "score_breakdown": [
            {"name": name, "value": value, "weight": weight}
            for name, value, weight in components
        ],
    }


def level_from_score(score: int) -> str:
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
    topic_level = semantic_result.get("level") or level_from_score(score or evidence.get("topic_avg_score") or evidence.get("recent_avg_score") or 55)
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

    base_score = score or evidence.get("topic_avg_score") or evidence.get("recent_avg_score") or 55
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
    concept_understanding = _clamp((evidence.get("evaluation_avg_score") or base_score) * 0.75 + goal_clarity * 0.25)
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
    return {
        "tags": tags,
        "knowledge_tags": tags,
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "dimensions": dimensions,
        "radar": radar,
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
