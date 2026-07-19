import datetime
import json
import uuid
from collections import Counter
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.schemas import EvaluationRecord, ExerciseAttempt, LearningPlan, ResourceArtifact
from app.services.data_services import (
    diagnosis_engine_service,
    dsa_topic_resolver,
    generation_job_service,
    profile_event_service,
    profile_service,
    resource_artifact_service,
    resource_artifact_type_service as artifact_types,
    user_service,
)


COURSE_ID = dsa_topic_resolver.COURSE_ID
COURSE_TITLE = dsa_topic_resolver.COURSE_TITLE
LEGACY_TERMS = diagnosis_engine_service.LEGACY_EVALUATION_TERMS


def _json_dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _safe_json_load(data, default):
    try:
        return json.loads(data) if data else default
    except Exception:
        return default


def _safe_created_at(value):
    if not value:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat(sep=" ", timespec="seconds")
    return str(value)


def _diagnosis_source_labels(evidence: Dict) -> List[str]:
    events = evidence.get("mastery_events") or []
    labels = []
    if any(item.get("source_type") == "exercise_attempt" for item in events):
        labels.append("有效练习作答")
    if any(item.get("source_type") == "verified_evaluation" for item in events):
        labels.append("认证评价")
    if evidence.get("execution_rate") is not None:
        labels.append("当前主题规划进度（不计入掌握度）")
    return labels or ["暂无有效掌握度证据"]


def _recommended_exercise(db: Session, username: str, resolved: Dict) -> Optional[Dict]:
    rows = (
        db.query(ResourceArtifact)
        .filter(
            ResourceArtifact.student_id == username,
            ResourceArtifact.type == artifact_types.EXERCISE_SET,
            ResourceArtifact.status == "published",
        )
        .order_by(ResourceArtifact.updated_at.desc())
        .limit(30)
        .all()
    )
    unit_ids = set(resolved.get("unit_ids") or [])
    chapter_id = str(resolved.get("chapter_id") or "")

    def rank(row):
        row_units = set(_safe_json_load(row.unit_ids_json, []))
        return (
            2 if unit_ids.intersection(row_units) else 0,
            1 if chapter_id and row.chapter_id == chapter_id else 0,
            row.updated_at or datetime.datetime.min,
        )

    if not rows:
        return None
    row = max(rows, key=rank)
    return {
        "artifact_id": row.artifact_id,
        "title": row.title,
        "route": f"/exercise/{row.artifact_id}",
    }


def _level_from_score(score: Optional[int]) -> str:
    if score is None:
        return "证据不足"
    if score >= 85:
        return "掌握较好"
    if score >= 70:
        return "基本掌握"
    if score >= 55:
        return "需要巩固"
    return "重点补救"


def _score_evaluation(text: str, confidence: int, resolved: Dict) -> int:
    content = (text or "").strip()
    compact = content.lower()
    length_score = min(24, len(content) // 10)
    unit_hits = sum(1 for title in resolved.get("unit_titles") or [] if title and title.lower() in compact)
    reflection_score = 12 if any(word in content for word in ["因为", "原因", "错因", "边界", "步骤", "复盘", "例子"]) else 0
    uncertainty_penalty = 10 if any(word in content for word in ["不会", "不懂", "总是错", "混淆", "卡住", "看不懂"]) else 0
    confidence_score = max(0, min(24, int(confidence or 0) // 4))
    match_score = 12 if resolved.get("matched") else 2
    return max(35, min(96, 38 + length_score + unit_hits * 4 + reflection_score + confidence_score + match_score - uncertainty_penalty))


def _record_titles(record: EvaluationRecord) -> Dict:
    unit_ids = _safe_json_load(getattr(record, "unit_ids_json", ""), [])
    return {
        "chapter_title": dsa_topic_resolver.get_chapter_title(getattr(record, "chapter_id", "") or ""),
        "section_title": dsa_topic_resolver.get_section_title(getattr(record, "section_id", "") or ""),
        "unit_titles": dsa_topic_resolver.get_unit_titles(unit_ids) or ["待定位"],
    }


def _evaluation_to_dict(record: EvaluationRecord) -> Dict:
    unit_ids = _safe_json_load(getattr(record, "unit_ids_json", ""), [])
    evidence_refs = _safe_json_load(getattr(record, "evidence_refs_json", ""), [])
    answers = _safe_json_load(record.answers_json, {})
    diagnosis_status = answers.get("diagnosis_status") if isinstance(answers, dict) else None
    grading = answers.get("grading") if isinstance(answers, dict) and isinstance(answers.get("grading"), dict) else {}
    rubric_version = (answers.get("rubric_version") if isinstance(answers, dict) else None) or grading.get("rubric_version")
    is_insufficient = diagnosis_status in {"insufficient", "insufficient_evidence"}
    display_score = None if is_insufficient else record.score
    titles = _record_titles(record)
    resolved = {
        "topic": record.topic or "",
        "chapter_id": getattr(record, "chapter_id", "") or "",
        "section_id": getattr(record, "section_id", "") or "",
        "unit_ids": unit_ids,
        "chapter_title": titles["chapter_title"],
        "section_title": titles["section_title"],
        "unit_titles": titles["unit_titles"],
    }
    source_text = " ".join([record.topic or "", titles["chapter_title"], titles["section_title"], " ".join(titles["unit_titles"])])
    weak_points = diagnosis_engine_service.filter_relevant_items(
        _safe_json_load(record.weak_points, []),
        resolved=resolved,
        source_text=source_text,
    )
    if is_insufficient:
        weak_points = ["尚无足够的有效作答，当前不能据此判断知识薄弱点。"]
    suggestions = diagnosis_engine_service.filter_relevant_items(
        _safe_json_load(record.suggestions, []),
        resolved=resolved,
        source_text=source_text,
    )
    return {
        "id": record.id,
        "username": record.username,
        "course_id": getattr(record, "course_id", "") or COURSE_ID,
        "course_title": COURSE_TITLE,
        "chapter_id": getattr(record, "chapter_id", "") or "",
        "section_id": getattr(record, "section_id", "") or "",
        "unit_ids": unit_ids,
        "chapter_title": titles["chapter_title"],
        "section_title": titles["section_title"],
        "unit_titles": titles["unit_titles"],
        "evidence_refs": evidence_refs,
        "diagnosis_type": getattr(record, "diagnosis_type", "") or "manual",
        "rubric_version": rubric_version or "",
        "algorithm_status": (
            "current"
            if rubric_version == diagnosis_engine_service.RUBRIC_VERSION
            else "legacy"
            if getattr(record, "diagnosis_type", "") == "auto_multi_factor"
            else "evidence"
        ),
        "topic": record.topic,
        # The legacy table has a database-side score default of 0.  Evidence-v2
        # keeps the semantic null in answers_json so cold-start records are never
        # presented as a real zero score.
        "score": display_score,
        "level": record.level,
        "weak_points": weak_points,
        "suggestions": suggestions,
        "wrong_notes": record.wrong_notes or "",
        "answers": answers,
        "generated_resource_id": record.generated_resource_id or "",
        "created_at": _safe_created_at(record.created_at),
    }


def _contains_legacy_terms(*values) -> bool:
    text = " ".join(str(value or "") for value in values)
    return any(term in text for term in LEGACY_TERMS)


def _build_report_content(
    resolved: Dict,
    notes: str,
    score: Optional[int],
    level: str,
    weak_points: List[str],
    suggestions: List[str],
    score_breakdown: List[Dict] = None,
    evidence_summary: Dict = None,
) -> str:
    weak_lines = "\n".join([f"- {item}" for item in weak_points])
    suggestion_lines = "\n".join([f"{idx}. {item}" for idx, item in enumerate(suggestions, 1)])
    unit_titles = "、".join(resolved.get("unit_titles") or ["待定位"])
    breakdown_lines = "\n".join(
        [
            f"- {item.get('name')}：{item.get('value')} 分，实际权重 {round(float(item.get('weight') or 0) * 100)}%，贡献 {item.get('contribution', 0)} 分"
            for item in (score_breakdown or [])
        ]
    ) or "- 本次诊断依据较少，建议通过练习和评价继续补充证据。"
    evidence_summary = evidence_summary or {}
    return f"""# {resolved['topic']} 诊断与补弱报告

## 课程
{COURSE_TITLE}

## 定位信息
- 章节：{resolved.get('chapter_title') or '待定位'}
- 小节：{resolved.get('section_title') or '待定位'}
- 知识单元：{unit_titles}

## 得分与等级
- 掌握度：{score if score is not None else '暂无（证据不足）'}
- 等级：{level}
- 证据置信度：{evidence_summary.get('confidence_score', 0)} / 100
- 评分规则版本：{evidence_summary.get('rubric_version') or diagnosis_engine_service.RUBRIC_VERSION}

## 诊断依据
{breakdown_lines}

## 证据概览
- 有效掌握度证据：{evidence_summary.get('evidence_count', 0)} 条
- 有效作答题数：{evidence_summary.get('answered_item_count', 0)} 题
- 已排除的无效/派生记录：{evidence_summary.get('excluded_evidence_count', 0)} 条
- 当前主题计划执行率：{evidence_summary.get('execution_rate') if evidence_summary.get('execution_rate') is not None else '暂无'}

## 学生反馈
{notes or "本次未填写详细错题说明，系统根据平台学习记录生成阶段性诊断。"}

## 薄弱点
{weak_lines}

## 补救建议
{suggestion_lines}

## 下一步学习任务
{resolved.get('practice') or '完成 3 道基础题、1 道边界题和 1 个代码小实验，并记录错因。'}
"""


def _build_remediation_content(kind: str, resolved: Dict, weak_points: List[str], suggestions: List[str]) -> Dict:
    topic = resolved.get("topic") or "数据结构与算法学习诊断"
    chapter_title = resolved.get("chapter_title") or "待定位"
    section_title = resolved.get("section_title") or "待定位"
    unit_titles = resolved.get("unit_titles") or ["待定位"]
    weak_text = "\n".join(f"- {item}" for item in weak_points)
    suggestion_text = "\n".join(f"{idx}. {item}" for idx, item in enumerate(suggestions, 1))

    if kind == "course_note":
        title = f"{topic} 补弱讲解"
        content = f"""# {title}

## 定位
- 课程：{COURSE_TITLE}
- 章节：{chapter_title}
- 小节：{section_title}
- 知识单元：{"、".join(unit_titles)}

## 先理解什么
先把问题拆成“定义、适用条件、边界情况、代码验证”四层。不要只背模板，要能说明每一步为什么能缩小问题规模或保持结果正确。

## 常见薄弱点
{weak_text}

## 学习顺序
{suggestion_text}
"""
        summary = "按知识单元定位生成的补弱讲解。"
    elif kind == "exercise_set":
        title = f"{topic} 补弱练习集"
        content = f"""# {title}

1. 概念判断：说明「{unit_titles[0]}」的适用前提，并给出一个不适用的反例。
2. 边界分析：设计一个最小输入、一个空输入或极端输入，判断算法是否仍然正确。
3. 过程追踪：手写一轮核心变量变化，标出每一步的判断条件。
4. 综合题：把本题和上一节知识联系起来，说明复杂度来源。

## 答题要求
每题都写出“为什么”，不要只写结果。
"""
        summary = "覆盖概念、边界、过程和综合迁移的补弱题。"
    elif kind == "code_lab":
        title = f"{topic} 代码小实验"
        content = f"""# {title}

## 实验目标
用一段最小可运行代码验证「{unit_titles[0]}」的关键逻辑。

## 建议步骤
1. 写出函数签名，明确输入输出。
2. 准备 3 组样例：正常样例、边界样例、错误高发样例。
3. 打印关键变量，观察每一步状态变化。
4. 记录时间复杂度和空间复杂度。

```python
def solve(data):
    # TODO: 根据本节知识单元补全核心逻辑
    return data

cases = [
    [],          # 边界样例
    [1],         # 最小非空样例
    [1, 2, 3],   # 正常样例
]

for case in cases:
    print(case, solve(case))
```
"""
        summary = "可直接运行和改写的补弱代码任务。"
    else:
        title = f"{topic} 诊断与补弱报告"
        content = _build_report_content(resolved, "", 0, "待复盘", weak_points, suggestions)
        summary = "评价记录对应的补弱报告。"

    return {"title": title, "summary": summary, "content": content}


def _make_artifact(
    db: Session,
    username: str,
    resolved: Dict,
    artifact_type: str,
    title: str,
    summary: str,
    content: str,
    reason: str,
) -> Dict:
    return resource_artifact_service.create_artifact(
        db,
        username=username,
        course_id=COURSE_ID,
        chapter_id=resolved.get("chapter_id") or "",
        section_id=resolved.get("section_id") or "",
        unit_ids=resolved.get("unit_ids") or [],
        artifact_type=artifact_type,
        title=title,
        summary=summary,
        content=content,
        evidence_refs=resolved.get("evidence_refs") or [],
        personalization_reason=reason,
        source=f"{COURSE_TITLE} / {resolved.get('chapter_title') or '待定位'} / 学习评价",
        status="published",
        agent_name="EvaluationRemediationAgent",
    )


def save_evaluation_record(
    db: Session,
    *,
    username: str,
    resolved: Dict,
    score: Optional[int],
    level: str,
    weak_points: List[str],
    suggestions: List[str],
    wrong_notes: str,
    answers: Dict,
    generated_resource_id: str = "",
) -> Dict:
    record = EvaluationRecord(
        id=str(uuid.uuid4()),
        username=username,
        course_id=COURSE_ID,
        chapter_id=resolved.get("chapter_id") or "",
        section_id=resolved.get("section_id") or "",
        unit_ids_json=_json_dump(resolved.get("unit_ids") or []),
        evidence_refs_json=_json_dump(resolved.get("evidence_refs") or []),
        diagnosis_type=resolved.get("diagnosis_type") or "manual",
        topic=resolved.get("topic") or "数据结构与算法学习诊断",
        score=score,
        level=level,
        weak_points=_json_dump(weak_points or []),
        suggestions=_json_dump(suggestions or []),
        wrong_notes=wrong_notes or "",
        answers_json=_json_dump(answers or {}),
        generated_resource_id=generated_resource_id,
        created_at=datetime.datetime.now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _evaluation_to_dict(record)


def get_evaluation_records(db: Session, username: str) -> List[Dict]:
    rows = (
        db.query(EvaluationRecord)
        .filter(
            EvaluationRecord.username == username,
            ~EvaluationRecord.diagnosis_type.like("legacy_invalid%"),
        )
        .order_by(EvaluationRecord.created_at.desc())
        .all()
    )
    return [
        _evaluation_to_dict(row)
        for row in rows
        if not _contains_legacy_terms(row.topic, row.weak_points, row.suggestions, row.wrong_notes)
    ]


def _update_profile(db: Session, username: str, merged_text: str, resolved: Dict, score: Optional[int], level: str) -> Dict:
    updated_user = user_service.update_user_learning_profile(
        db,
        username,
        [resolved.get("topic") or "数据结构与算法"],
        hours_delta=1 if score is not None and score < 75 else 0,
        replace_tags=True,
    )
    profile_user = user_service.get_user_by_username(db, username)
    profile = profile_service.build_profile(
        user=profile_user,
        message=merged_text,
        intent="练习巩固",
        knowledge_topic=resolved.get("topic") or "数据结构与算法",
        score=score,
        db=db,
        semantic_result={
            "course_id": COURSE_ID,
            "chapter_id": resolved.get("chapter_id") or "",
            "section_id": resolved.get("section_id") or "",
            "unit_ids": resolved.get("unit_ids") or [],
            "topic_title": resolved.get("topic") or "",
            "weak_points": resolved.get("weak_points") or [],
            "subject_category": "data_structures_algorithms",
            "level": level,
            "level_source": "current_evaluation" if score is not None else "insufficient_evidence",
            "level_evidence": (
                f"本次有效学习证据估算掌握度 {score}，反馈主题：{resolved.get('topic')}"
                if score is not None
                else f"当前主题「{resolved.get('topic')}」尚缺少有效作答证据"
            ),
            "needs_level_diagnosis": score is None,
        },
    )
    if updated_user:
        profile["tags"] = profile_service.merge_tags(updated_user["tags"], profile.get("tags", []))
        profile["knowledge_tags"] = profile["tags"]
        profile["hours"] = updated_user["hours"]
    profile_event_service.record_profile_event(
        db,
        username=username,
        source_type="evaluation",
        source_id=resolved.get("topic") or "",
        profile=profile,
        reason=f"完成「{resolved.get('topic')}」学习诊断后自动更新画像。",
        course_id=COURSE_ID,
    )
    return profile


def handle_learning_evaluation(
    db: Session,
    username: str,
    topic: str,
    wrong_notes: str,
    answer_summary: str,
    confidence: int = 60,
    course_id: str = COURSE_ID,
    chapter_id: str = "",
    section_id: str = "",
    unit_ids: Optional[List[str]] = None,
) -> Dict:
    merged_text = "\n".join([topic or "", wrong_notes or "", answer_summary or ""]).strip()
    resolved = dsa_topic_resolver.resolve_topic(
        merged_text,
        course_id=course_id or COURSE_ID,
        chapter_id=chapter_id or "",
        section_id=section_id or "",
        unit_ids=unit_ids or [],
        fallback_topic=topic or "数据结构与算法学习诊断",
    )
    diagnosis = diagnosis_engine_service.calculate_diagnosis(
        db=db,
        username=username,
        resolved=resolved,
        current_text=merged_text,
        confidence=confidence,
        mode="manual",
    )
    score = diagnosis["score"]
    level = diagnosis["level"]
    weak_points = diagnosis["weak_points"]
    suggestions = diagnosis["suggestions"]
    resolved["weak_points"] = weak_points
    resolved["diagnosis_type"] = "manual_multi_factor"
    report_content = _build_report_content(
        resolved,
        wrong_notes or answer_summary,
        score,
        level,
        weak_points,
        suggestions,
        diagnosis.get("score_breakdown") or [],
        diagnosis.get("evidence") or {},
    )
    report = _make_artifact(
        db,
        username,
        resolved,
        artifact_types.DIAGNOSTIC_REPORT,
        f"{resolved['topic']} 诊断与补弱报告",
        f"{level}：已定位到 {resolved.get('section_title') or '待定位'}。",
        report_content,
        "根据本次评价提交内容、章节定位和知识单元证据生成。",
    )
    db.commit()

    record = save_evaluation_record(
        db=db,
        username=username,
        resolved=resolved,
        score=score,
        level=level,
        weak_points=weak_points,
        suggestions=suggestions,
        wrong_notes=wrong_notes,
        answers={
            "topic": topic,
            "wrong_notes": wrong_notes,
            "answer_summary": answer_summary,
            "confidence": confidence,
            "rubric_version": diagnosis.get("rubric_version"),
            "evidence_hash": diagnosis.get("evidence_hash"),
            "diagnosis_status": diagnosis.get("diagnosis_status"),
            "confidence_score": diagnosis.get("confidence_score"),
            "score_breakdown": diagnosis.get("score_breakdown") or [],
        },
        generated_resource_id=report.get("artifact_id") or "",
    )
    profile = _update_profile(db, username, merged_text, resolved, score, level)

    return {
        "record": record,
        "score": score,
        "level": level,
        "diagnosis_status": diagnosis.get("diagnosis_status"),
        "confidence_score": diagnosis.get("confidence_score"),
        "rubric_version": diagnosis.get("rubric_version"),
        "reflection_score": diagnosis.get("reflection_score"),
        "course_title": COURSE_TITLE,
        "chapter_title": record.get("chapter_title", "待定位"),
        "section_title": record.get("section_title", "待定位"),
        "unit_titles": record.get("unit_titles", ["待定位"]),
        "weak_points": weak_points,
        "suggestions": suggestions,
        "score_breakdown": diagnosis.get("score_breakdown") or [],
        "diagnosis_evidence": {
            "recent_avg_score": (diagnosis.get("evidence") or {}).get("recent_avg_score"),
            "topic_avg_score": (diagnosis.get("evidence") or {}).get("topic_avg_score"),
            "exercise_avg_score": (diagnosis.get("evidence") or {}).get("exercise_avg_score"),
            "execution_rate": (diagnosis.get("evidence") or {}).get("execution_rate"),
            "evidence_count": (diagnosis.get("evidence") or {}).get("evidence_count"),
            "answered_item_count": (diagnosis.get("evidence") or {}).get("answered_item_count"),
            "excluded_evidence_count": (diagnosis.get("evidence") or {}).get("excluded_evidence_count"),
            "confidence_score": diagnosis.get("confidence_score"),
            "confidence_components": (diagnosis.get("evidence") or {}).get("confidence_components") or {},
            "reflection_score": diagnosis.get("reflection_score"),
            "rubric_version": diagnosis.get("rubric_version"),
            "excluded_evidence": (diagnosis.get("evidence") or {}).get("excluded_evidence") or [],
        },
        "generated_resource": report,
        "recommended_exercise": _recommended_exercise(db, username, resolved),
        "profile": profile,
    }


def _collect_auto_source_text(db: Session, username: str) -> str:
    parts = []
    try:
        records = (
            db.query(EvaluationRecord)
            .filter(
                EvaluationRecord.username == username,
                EvaluationRecord.diagnosis_type.in_(list(diagnosis_engine_service.VERIFIED_EVALUATION_TYPES)),
            )
            .order_by(EvaluationRecord.created_at.desc())
            .limit(8)
            .all()
        )
        for row in records:
            if not _contains_legacy_terms(row.topic, row.wrong_notes):
                parts.extend([row.topic or "", row.wrong_notes or ""])
    except Exception:
        pass
    try:
        attempts = (
            db.query(ExerciseAttempt)
            .filter(ExerciseAttempt.username == username)
            .order_by(ExerciseAttempt.created_at.desc())
            .limit(8)
            .all()
        )
        for row in attempts:
            answers = _safe_json_load(row.answers_json, {})
            stats = diagnosis_engine_service._answer_stats(answers)
            if stats.get("valid_for_mastery"):
                parts.extend([row.unit_id or "", row.error_pattern_json or ""])
    except Exception:
        pass
    try:
        plan = db.query(LearningPlan).filter(LearningPlan.username == username).first()
        plans = _safe_json_load(plan.plans_json if plan else "", [])
        for plan_item in plans[:3]:
            for task in plan_item.get("tasks", []):
                status = str(task.get("status") or "").lower()
                if status in {"active", "completed", "done", "已完成", "finished"} or task.get("isCustom"):
                    parts.extend([task.get("unit_id") or "", task.get("title") or "", task.get("desc") or ""])
    except Exception:
        pass
    return " ".join(parts)


def handle_auto_evaluation(db: Session, username: str) -> Dict:
    user = user_service.get_user_by_username(db, username)
    source_text = _collect_auto_source_text(db, username)
    if not source_text.strip() and user:
        source_text = f"{user.tags or ''} {user.bio or ''}"
    resolved = dsa_topic_resolver.resolve_topic(source_text, fallback_topic="数据结构与算法学习诊断")
    diagnosis = diagnosis_engine_service.calculate_diagnosis(
        db=db,
        username=username,
        resolved=resolved,
        current_text=source_text,
        confidence=60,
        mode="auto",
    )
    score = diagnosis["score"]
    level = diagnosis["level"]
    weak_points = diagnosis["weak_points"]
    suggestions = diagnosis["suggestions"]
    resolved["weak_points"] = weak_points
    resolved["diagnosis_type"] = "auto_multi_factor"
    auto_notes = (
        f"系统仅基于有效作答和认证评价估算知识掌握度，规划执行单独展示；"
        f"当前定位主题为「{resolved.get('topic')}」。"
    )

    latest_auto = (
        db.query(EvaluationRecord)
        .filter(
            EvaluationRecord.username == username,
            EvaluationRecord.diagnosis_type == "auto_multi_factor",
            ~EvaluationRecord.diagnosis_type.like("legacy_invalid%"),
        )
        .order_by(EvaluationRecord.created_at.desc())
        .first()
    )
    latest_answers = _safe_json_load(latest_auto.answers_json, {}) if latest_auto else {}
    if (
        latest_auto
        and latest_answers.get("rubric_version") == diagnosis.get("rubric_version")
        and latest_answers.get("evidence_hash") == diagnosis.get("evidence_hash")
    ):
        record = _evaluation_to_dict(latest_auto)
        report = (
            resource_artifact_service.get_artifact(db, latest_auto.generated_resource_id)
            if latest_auto.generated_resource_id
            else None
        )
        evidence = diagnosis.get("evidence") or {}
        return {
            "record": record,
            "score": score,
            "level": level,
            "diagnosis_status": diagnosis.get("diagnosis_status"),
            "confidence_score": diagnosis.get("confidence_score"),
            "rubric_version": diagnosis.get("rubric_version"),
            "course_title": COURSE_TITLE,
            "chapter_title": record.get("chapter_title", "待定位"),
            "section_title": record.get("section_title", "待定位"),
            "unit_titles": record.get("unit_titles", ["待定位"]),
            "weak_points": weak_points,
            "suggestions": suggestions,
            "score_breakdown": diagnosis.get("score_breakdown") or [],
            "diagnosis_evidence": {
                "recent_avg_score": evidence.get("recent_avg_score"),
                "topic_avg_score": evidence.get("topic_avg_score"),
                "exercise_avg_score": evidence.get("exercise_avg_score"),
                "execution_rate": evidence.get("execution_rate"),
                "evidence_count": evidence.get("evidence_count"),
                "answered_item_count": evidence.get("answered_item_count"),
                "excluded_evidence_count": evidence.get("excluded_evidence_count"),
                "confidence_score": diagnosis.get("confidence_score"),
                "confidence_components": evidence.get("confidence_components") or {},
                "rubric_version": diagnosis.get("rubric_version"),
                "excluded_evidence": evidence.get("excluded_evidence") or [],
            },
            "generated_resource": report,
            "recommended_exercise": _recommended_exercise(db, username, resolved),
            "profile": None,
            "auto_summary": auto_notes,
            "data_sources": _diagnosis_source_labels(evidence),
            "is_reused": True,
        }
    report_content = _build_report_content(
        resolved,
        auto_notes,
        score,
        level,
        weak_points,
        suggestions,
        diagnosis.get("score_breakdown") or [],
        diagnosis.get("evidence") or {},
    )
    report = _make_artifact(
        db,
        username,
        resolved,
        artifact_types.DIAGNOSTIC_REPORT,
        f"{resolved['topic']} 诊断与补弱报告",
        f"{level}：平台自动诊断已完成。",
        report_content,
        "根据平台历史学习数据自动生成。",
    )
    db.commit()
    record_answers = {
        "mode": "auto",
        "source": "valid_exercise/verified_evaluation/relevant_plan",
        "rubric_version": diagnosis.get("rubric_version"),
        "evidence_hash": diagnosis.get("evidence_hash"),
        "diagnosis_status": diagnosis.get("diagnosis_status"),
        "confidence_score": diagnosis.get("confidence_score"),
        "score_breakdown": diagnosis.get("score_breakdown") or [],
    }
    record = save_evaluation_record(
        db=db,
        username=username,
        resolved=resolved,
        score=score,
        level=level,
        weak_points=weak_points,
        suggestions=suggestions,
        wrong_notes=auto_notes,
        answers=record_answers,
        generated_resource_id=report.get("artifact_id") or "",
    )
    profile = _update_profile(db, username, auto_notes, resolved, score, level)
    evidence = diagnosis.get("evidence") or {}
    return {
        "record": record,
        "score": score,
        "level": level,
        "diagnosis_status": diagnosis.get("diagnosis_status"),
        "confidence_score": diagnosis.get("confidence_score"),
        "rubric_version": diagnosis.get("rubric_version"),
        "course_title": COURSE_TITLE,
        "chapter_title": record.get("chapter_title", "待定位"),
        "section_title": record.get("section_title", "待定位"),
        "unit_titles": record.get("unit_titles", ["待定位"]),
        "weak_points": weak_points,
        "suggestions": suggestions,
        "score_breakdown": diagnosis.get("score_breakdown") or [],
        "diagnosis_evidence": {
            "recent_avg_score": (diagnosis.get("evidence") or {}).get("recent_avg_score"),
            "topic_avg_score": (diagnosis.get("evidence") or {}).get("topic_avg_score"),
            "exercise_avg_score": (diagnosis.get("evidence") or {}).get("exercise_avg_score"),
            "execution_rate": (diagnosis.get("evidence") or {}).get("execution_rate"),
            "evidence_count": (diagnosis.get("evidence") or {}).get("evidence_count"),
            "answered_item_count": evidence.get("answered_item_count"),
            "excluded_evidence_count": evidence.get("excluded_evidence_count"),
            "confidence_score": diagnosis.get("confidence_score"),
            "confidence_components": evidence.get("confidence_components") or {},
            "rubric_version": diagnosis.get("rubric_version"),
            "excluded_evidence": evidence.get("excluded_evidence") or [],
        },
        "generated_resource": report,
        "recommended_exercise": _recommended_exercise(db, username, resolved),
        "profile": profile,
        "auto_summary": auto_notes,
        "data_sources": _diagnosis_source_labels(evidence),
        "is_reused": False,
    }


def generate_remediation_package(db: Session, username: str, record_id: str = "", payload: Dict = None) -> Dict:
    payload = payload or {}
    record = None
    if record_id:
        record = (
            db.query(EvaluationRecord)
            .filter(
                EvaluationRecord.id == record_id,
                EvaluationRecord.username == username,
                ~EvaluationRecord.diagnosis_type.like("legacy_invalid%"),
            )
            .first()
        )
    if record:
        record_dict = _evaluation_to_dict(record)
        resolved = dsa_topic_resolver.resolve_topic(
            record.topic,
            chapter_id=record_dict.get("chapter_id") or "",
            section_id=record_dict.get("section_id") or "",
            unit_ids=record_dict.get("unit_ids") or [],
            fallback_topic=record.topic or "数据结构与算法学习诊断",
        )
        weak_points = record_dict.get("weak_points") or []
        suggestions = record_dict.get("suggestions") or []
    else:
        resolved = dsa_topic_resolver.resolve_topic(
            " ".join([payload.get("topic", ""), payload.get("wrong_notes", ""), payload.get("answer_summary", "")]),
            chapter_id=payload.get("chapter_id", ""),
            section_id=payload.get("section_id", ""),
            unit_ids=payload.get("unit_ids") or [],
        )
        weak_points = resolved.get("weak_points") or []
        suggestions = resolved.get("suggestions") or []

    job = generation_job_service.create_job(
        db,
        username=username,
        course_id=COURSE_ID,
        topic=resolved.get("topic") or "数据结构与算法学习诊断",
        unit_id=(resolved.get("unit_ids") or [""])[0],
        message="正在生成数据结构与算法补弱学习包",
    )

    type_map = [
        ("course_note", artifact_types.COURSE_NOTE),
        ("exercise_set", artifact_types.EXERCISE_SET),
        ("code_lab", artifact_types.CODE_LAB),
        ("remediation_report", artifact_types.DIAGNOSTIC_REPORT),
    ]
    artifacts = []
    reason = f"依据「{resolved.get('topic')}」诊断记录、章节定位和知识单元证据生成。"
    for kind, artifact_type in type_map:
        content_data = _build_remediation_content(kind, resolved, weak_points, suggestions)
        artifacts.append(_make_artifact(
            db,
            username,
            resolved,
            artifact_type,
            content_data["title"],
            content_data["summary"],
            content_data["content"],
            reason,
        ))
    db.commit()

    artifact_ids = [item["artifact_id"] for item in artifacts]
    job = generation_job_service.update_job(
        db,
        job["job_id"],
        status="completed",
        progress=100,
        message="补弱学习包已生成，可立即查看。",
        artifact_ids=artifact_ids,
    )
    generation_job_service.add_event(
        db,
        job["job_id"],
        event="job_completed",
        agent="EvaluationRemediationAgent",
        message="已生成讲解、练习、代码实验和补弱报告。",
        progress=100,
    )
    return {"generation_job": job, "artifacts": artifacts}
