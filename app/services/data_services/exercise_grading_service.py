import datetime
import json
import uuid
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.schemas import EvaluationRecord, ExerciseAttempt
from app.services import llm_provider
from app.services.data_services import (
    diagnosis_engine_service,
    dsa_topic_resolver,
    profile_event_service,
    profile_service,
    resource_artifact_service,
    resource_artifact_type_service as artifact_types,
    user_service,
)


COURSE_ID = "data_structures_algorithms"
COURSE_TITLE = "数据结构与算法"


def _json_dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_load(value, default):
    try:
        return json.loads(value) if value else default
    except Exception:
        return default


def _level_from_score(score: int) -> str:
    if score >= 85:
        return "掌握较好"
    if score >= 70:
        return "基本掌握"
    if score >= 55:
        return "需要巩固"
    return "重点补救"


def _artifact_location(artifact: Dict) -> Dict:
    unit_ids = artifact.get("unit_ids") or []
    return {
        "course_id": artifact.get("course_id") or COURSE_ID,
        "chapter_id": artifact.get("chapter_id") or "",
        "section_id": artifact.get("section_id") or "",
        "unit_ids": unit_ids,
        "chapter_title": dsa_topic_resolver.get_chapter_title(artifact.get("chapter_id") or ""),
        "section_title": dsa_topic_resolver.get_section_title(artifact.get("section_id") or ""),
        "unit_titles": dsa_topic_resolver.get_unit_titles(unit_ids) or [],
    }


def _build_prompt(artifact: Dict, answers: List[Dict]) -> List[Dict]:
    answer_lines = []
    for index, item in enumerate(answers or [], 1):
        answer_lines.append(
            f"题目 {index}：{item.get('question') or item.get('stem') or ''}\n"
            f"学生答案：{item.get('answer') or ''}"
        )
    location = _artifact_location(artifact)
    return [
        {
            "role": "system",
            "content": (
                "你是《数据结构与算法》课程的 AI 批改与补弱诊断 Agent。"
                "请根据题集正文、学生作答和课程定位进行批改。"
                "必须输出 JSON，不要输出 Markdown 代码块。"
                "不要暴露内部 ID，不要编造学生没写过的作答。"
            ),
        },
        {
            "role": "user",
            "content": f"""
课程：{COURSE_TITLE}
章节：{location.get('chapter_title') or '待定位'}
小节：{location.get('section_title') or '待定位'}
知识点：{'、'.join(location.get('unit_titles') or []) or '待定位'}

题集标题：{artifact.get('title') or ''}
题集原文：
{artifact.get('content') or artifact.get('summary') or ''}

学生作答：
{chr(10).join(answer_lines)}

请输出 JSON 对象，字段必须包含：
- score: 0-100 整数
- level: 掌握等级
- per_question: 数组，每项包含 question_index、is_correct、score、feedback
- standard_answers: 数组，每项包含 question_index、answer、explanation
- weak_points: 字符串数组
- suggestions: 字符串数组
- diagnostic_report: 面向学生的 Markdown 报告，包含错因分析、补弱步骤和下一次练习建议
""",
        },
    ]


def _validate_grading(data: Dict, total_questions: int) -> Dict:
    score = int(data.get("score") or 0)
    score = max(0, min(100, score))
    per_question = data.get("per_question") if isinstance(data.get("per_question"), list) else []
    standard_answers = data.get("standard_answers") if isinstance(data.get("standard_answers"), list) else []
    weak_points = data.get("weak_points") if isinstance(data.get("weak_points"), list) else []
    suggestions = data.get("suggestions") if isinstance(data.get("suggestions"), list) else []
    report = str(data.get("diagnostic_report") or "").strip()
    if not report:
        raise ValueError("AI 未生成诊断报告")
    return {
        "score": score,
        "level": str(data.get("level") or _level_from_score(score)),
        "per_question": per_question[: max(total_questions, 1)],
        "standard_answers": standard_answers[: max(total_questions, 1)],
        "weak_points": [str(item) for item in weak_points if str(item).strip()],
        "suggestions": [str(item) for item in suggestions if str(item).strip()],
        "diagnostic_report": report,
    }


def grade_exercise_attempt(db: Session, *, username: str, artifact_id: str, answers: List[Dict]) -> Dict:
    artifact = resource_artifact_service.get_artifact(db, artifact_id)
    if not artifact:
        return {"success": False, "message": "练习题集不存在", "grading": None}

    normalized_type = artifact_types.normalize_artifact_type(artifact.get("type") or "")
    if normalized_type != artifact_types.EXERCISE_SET:
        return {"success": False, "message": "当前资源不是练习题集，不能进入作答批改", "grading": None}

    answers = [
        {
            "question_id": str(item.get("question_id") or item.get("id") or index + 1),
            "question": str(item.get("question") or item.get("stem") or "").strip(),
            "answer": str(item.get("answer") or "").strip(),
        }
        for index, item in enumerate(answers or [])
    ]
    answers = [item for item in answers if item["question"] or item["answer"]]
    if not answers:
        return {"success": False, "message": "请至少填写一道题的答案", "grading": None}

    result = llm_provider.chat_json(
        _build_prompt(artifact, answers),
        required_fields=["score", "per_question", "standard_answers", "weak_points", "suggestions", "diagnostic_report"],
        temperature=0.2,
        max_tokens=5200,
    )
    if not result.get("ok"):
        return {
            "success": False,
            "message": f"AI 批改失败：{result.get('error') or '模型未返回有效结果'}",
            "grading": None,
            "raw_output": result.get("content", ""),
        }

    try:
        grading = _validate_grading(result.get("data") or {}, len(answers))
    except ValueError as exc:
        return {"success": False, "message": str(exc), "grading": None, "raw_output": result.get("content", "")}

    now = datetime.datetime.now()
    location = _artifact_location(artifact)
    resolved = {
        "topic": artifact.get("title") or "练习题集作答诊断",
        "chapter_id": location["chapter_id"],
        "section_id": location["section_id"],
        "unit_ids": location["unit_ids"],
        "unit_titles": location["unit_titles"],
        "chapter_title": location["chapter_title"],
        "section_title": location["section_title"],
        "matched": bool(location["chapter_id"] or location["unit_ids"]),
        "weak_points": grading["weak_points"],
        "suggestions": grading["suggestions"],
        "evidence_refs": [artifact_id],
    }
    diagnosis = diagnosis_engine_service.calculate_diagnosis(
        db=db,
        username=username or "student",
        resolved=resolved,
        current_text=json.dumps({"answers": answers, "grading": grading}, ensure_ascii=False),
        confidence=70,
        current_score=grading["score"],
        current_weak_points=grading["weak_points"],
        current_suggestions=grading["suggestions"],
    )
    grading["raw_ai_score"] = grading["score"]
    grading["score"] = diagnosis["score"]
    grading["level"] = diagnosis["level"]
    grading["weak_points"] = diagnosis["weak_points"]
    grading["suggestions"] = diagnosis["suggestions"]
    grading["score_breakdown"] = diagnosis.get("score_breakdown") or []
    grading["diagnosis_evidence"] = {
        "recent_avg_score": (diagnosis.get("evidence") or {}).get("recent_avg_score"),
        "topic_avg_score": (diagnosis.get("evidence") or {}).get("topic_avg_score"),
        "exercise_avg_score": (diagnosis.get("evidence") or {}).get("exercise_avg_score"),
        "execution_rate": (diagnosis.get("evidence") or {}).get("execution_rate"),
        "evidence_count": (diagnosis.get("evidence") or {}).get("evidence_count"),
    }
    breakdown_text = "\n".join(
        f"- {item.get('name')}：{item.get('value')} 分，权重 {round(float(item.get('weight') or 0) * 100)}%"
        for item in grading["score_breakdown"]
    )
    grading["diagnostic_report"] = (
        grading["diagnostic_report"].rstrip()
        + "\n\n## 多因素诊断依据\n"
        + (breakdown_text or "- 本次主要依据练习作答进行诊断。")
    )
    attempt = ExerciseAttempt(
        attempt_id=f"attempt_{uuid.uuid4().hex[:16]}",
        username=username or "student",
        course_id=location["course_id"] or COURSE_ID,
        unit_id=(location["unit_ids"] or [""])[0],
        artifact_id=artifact_id,
        answers_json=_json_dump({"answers": answers, "grading": grading}),
        score=grading["score"],
        error_pattern_json=_json_dump(grading["weak_points"]),
        created_at=now,
    )
    db.add(attempt)

    diagnostic_artifact = resource_artifact_service.create_artifact(
        db,
        username=username or "student",
        course_id=location["course_id"] or COURSE_ID,
        chapter_id=location["chapter_id"],
        section_id=location["section_id"],
        unit_ids=location["unit_ids"],
        artifact_type=artifact_types.DIAGNOSTIC_REPORT,
        title=f"{artifact.get('title') or '练习题集'} 作答诊断与补弱报告",
        summary=f"{grading['level']}，本报告基于本次练习作答生成。",
        content=grading["diagnostic_report"],
        evidence_refs=[artifact_id, attempt.attempt_id],
        personalization_reason="根据学生本次练习作答、AI 批改结果和课程知识点定位生成。",
        source="exercise_ai_grading",
        status="published",
        agent_name="ExerciseGradingAgent",
    )

    record = EvaluationRecord(
        id=f"eval_{uuid.uuid4().hex[:16]}",
        username=username or "student",
        course_id=location["course_id"] or COURSE_ID,
        chapter_id=location["chapter_id"],
        section_id=location["section_id"],
        unit_ids_json=_json_dump(location["unit_ids"]),
        evidence_refs_json=_json_dump([artifact_id, attempt.attempt_id]),
        diagnosis_type="exercise_ai_grading",
        topic=artifact.get("title") or "练习题集作答诊断",
        score=grading["score"],
        level=grading["level"],
        weak_points=_json_dump(grading["weak_points"]),
        suggestions=_json_dump(grading["suggestions"]),
        wrong_notes="学生完成练习题集后由 AI 批改生成。",
        answers_json=_json_dump({"answers": answers, "grading": grading}),
        generated_resource_id=diagnostic_artifact.get("artifact_id") or "",
        created_at=now,
    )
    db.add(record)
    profile_user = user_service.get_user_by_username(db, username or "student")
    profile = profile_service.build_profile(
        user=profile_user,
        message=json.dumps({"answers": answers, "weak_points": grading["weak_points"]}, ensure_ascii=False),
        intent="练习批改与补弱",
        knowledge_topic=artifact.get("title") or "练习题集作答诊断",
        score=grading["score"],
        db=db,
        semantic_result={
            "course_id": location["course_id"] or COURSE_ID,
            "chapter_id": location["chapter_id"],
            "section_id": location["section_id"],
            "unit_ids": location["unit_ids"],
            "unit_titles": location["unit_titles"],
            "topic_title": artifact.get("title") or "练习题集作答诊断",
            "subject_category": "data_structures_algorithms",
            "level": grading["level"],
            "level_source": "exercise_ai_grading",
            "level_evidence": f"本次练习综合诊断得分 {grading['score']}，AI 原始批改分 {grading.get('raw_ai_score')}。",
            "needs_level_diagnosis": False,
        },
    )
    profile_event_service.record_profile_event(
        db,
        username=username or "student",
        source_type="exercise_attempt",
        source_id=attempt.attempt_id,
        profile=profile,
        reason="完成练习题集作答后，系统结合批改结果和历史行为自动更新画像。",
        course_id=location["course_id"] or COURSE_ID,
    )
    db.commit()

    return {
        "success": True,
        "message": "AI 批改完成，诊断与补弱报告已生成。",
        "attempt": {
            "attempt_id": attempt.attempt_id,
            "score": attempt.score,
            "created_at": attempt.created_at.isoformat(timespec="seconds"),
        },
        "grading": grading,
        "diagnostic_report": diagnostic_artifact,
        "evaluation_record_id": record.id,
        "profile": profile,
    }
