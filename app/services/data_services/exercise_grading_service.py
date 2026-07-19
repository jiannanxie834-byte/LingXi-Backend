import datetime
import json
import re
import uuid
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.schemas import EvaluationRecord, ExerciseAnswerReveal, ExerciseAttempt
from app.services import llm_provider
from app.services.data_services import (
    diagnosis_engine_service,
    dsa_topic_resolver,
    exercise_question_service,
    profile_event_service,
    profile_service,
    resource_artifact_service,
    resource_artifact_type_service as artifact_types,
    user_service,
)


COURSE_ID = "data_structures_algorithms"
COURSE_TITLE = "数据结构与算法"
OBJECTIVE_TYPES = {"single_choice", "true_false"}


def _json_dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def record_answer_reveal(db: Session, *, username: str, artifact_id: str) -> None:
    exists = (
        db.query(ExerciseAnswerReveal)
        .filter(
            ExerciseAnswerReveal.username == username,
            ExerciseAnswerReveal.artifact_id == artifact_id,
        )
        .first()
    )
    if exists:
        return
    db.add(ExerciseAnswerReveal(
        reveal_id=f"reveal_{uuid.uuid4().hex[:16]}",
        username=username,
        artifact_id=artifact_id,
        revealed_at=datetime.datetime.now(),
    ))


def has_answer_reveal(db: Session, *, username: str, artifact_id: str) -> bool:
    return bool(
        db.query(ExerciseAnswerReveal.reveal_id)
        .filter(
            ExerciseAnswerReveal.username == username,
            ExerciseAnswerReveal.artifact_id == artifact_id,
        )
        .first()
    )


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


def _normalize_boolean(value: str) -> str:
    text = re.sub(r"[\s。，,.;；！!]", "", str(value or "").strip().lower())
    if text in {"对", "正确", "是", "true", "t", "1", "对的", "正确的"}:
        return "true"
    if text in {"错", "错误", "否", "false", "f", "0", "错的", "错误的"}:
        return "false"
    return text


def _normalize_choice(value: str, options: List[Dict]) -> str:
    text = str(value or "").strip()
    compact = re.sub(r"\s+", "", text).upper()
    key_match = re.match(r"^(?:选项)?\(?([A-H])\)?(?:[.、:：）)]|$)", compact)
    if key_match:
        return key_match.group(1)
    for option in options or []:
        if re.sub(r"\s+", "", str(option.get("text") or "")).lower() == re.sub(r"\s+", "", text).lower():
            return str(option.get("key") or "").upper()
    return compact


def grade_objective_question(question: Dict, student_answer: str) -> Dict:
    question_type = question.get("type")
    reference = str(question.get("reference_answer") or "").strip()
    if question_type == "true_false":
        expected = _normalize_boolean(reference)
        actual = _normalize_boolean(student_answer)
    else:
        expected = _normalize_choice(reference, question.get("options") or [])
        actual = _normalize_choice(student_answer, question.get("options") or [])

    skipped = not str(student_answer or "").strip()
    correct = bool(not skipped and expected and actual == expected)
    points = int(question.get("points") or 0)
    status = "skipped" if skipped else ("correct" if correct else "incorrect")
    if skipped:
        feedback = "本题未作答。"
    elif correct:
        feedback = "作答正确，已掌握本题的关键判断。"
    else:
        feedback = "作答不正确，请对照解析重新检查判断依据。"
    return {
        "question_id": question["question_id"],
        "question_index": question["question_index"],
        "type": question_type,
        "status": status,
        "is_correct": correct,
        "score": points if correct else 0,
        "max_score": points,
        "student_answer": str(student_answer or "").strip(),
        "reference_answer": reference,
        "explanation": question.get("explanation") or "",
        "feedback": feedback,
        "knowledge_point": question.get("knowledge_point") or "",
    }


def _build_subjective_prompt(artifact: Dict, questions: List[Dict]) -> List[Dict]:
    location = _artifact_location(artifact)
    question_payload = [
        {
            "question_id": item["question_id"],
            "question_index": item["question_index"],
            "type": item["type"],
            "stem": item["stem"],
            "student_answer": item["student_answer"] or "未作答",
            "reference_answer": item.get("reference_answer") or "",
            "explanation": item.get("explanation") or "",
            "rubric": item.get("rubric") or "",
            "knowledge_point": item.get("knowledge_point") or "",
            "max_score": item["points"],
        }
        for item in questions
    ]
    return [
        {
            "role": "system",
            "content": (
                "你是《数据结构与算法》主观题批改 Agent。只批改给定的主观题，"
                "不得改变 question_id、question_index 或 max_score。"
                "学生答案可以与参考答案表述不同，应根据关键步骤和逻辑正确性给分。"
                "空白、无关内容、自相矛盾或无法支撑结论的作答不得给高分。"
                "必须输出 JSON，不要输出 Markdown 代码块。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"课程：{COURSE_TITLE}\n"
                f"章节：{location.get('chapter_title') or '待定位'} / {location.get('section_title') or '待定位'}\n"
                f"题集：{artifact.get('title') or ''}\n\n"
                f"待批改题目 JSON：\n{json.dumps(question_payload, ensure_ascii=False)}\n\n"
                "输出 JSON 字段：\n"
                "- per_question：数组，顺序与输入一致，每项包含 question_id、question_index、score、is_correct、feedback\n"
                "- weak_points：仅基于本次错答的薄弱点数组\n"
                "- suggestions：2-4 条可执行补弱建议\n"
                "feedback 每题限 1-2 句，所有字段保持简短，不要在 JSON 中输出 Markdown 长报告。"
            ),
        },
    ]


def validate_subjective_grading(data: Dict, questions: List[Dict]) -> Dict:
    rows = data.get("per_question") if isinstance(data.get("per_question"), list) else []
    expected = {question["question_id"]: question for question in questions}
    if len(rows) != len(expected):
        raise ValueError("AI 批改结果题目数量与作答不一致")

    validated = {}
    for row in rows:
        question_id = str(row.get("question_id") or "")
        question = expected.get(question_id)
        if not question or question_id in validated:
            raise ValueError("AI 批改结果包含未知或重复题号")
        if int(row.get("question_index") or 0) != int(question["question_index"]):
            raise ValueError("AI 批改结果题号错位")
        try:
            score = int(round(float(row.get("score") or 0)))
        except (TypeError, ValueError) as exc:
            raise ValueError("AI 批改结果得分无效") from exc
        max_score = int(question.get("points") or 0)
        if score < 0 or score > max_score:
            raise ValueError("AI 批改结果超出本题分值")
        feedback = str(row.get("feedback") or "").strip()
        if not feedback:
            raise ValueError("AI 批改结果缺少逐题反馈")
        skipped = not question.get("student_answer")
        is_correct = bool(row.get("is_correct")) and score >= max_score * 0.8 and not skipped
        status = "skipped" if skipped else ("correct" if is_correct else ("partial" if score > 0 else "incorrect"))
        validated[question_id] = {
            "question_id": question_id,
            "question_index": question["question_index"],
            "type": question["type"],
            "status": status,
            "is_correct": is_correct,
            "score": 0 if skipped else score,
            "max_score": max_score,
            "student_answer": question.get("student_answer") or "",
            "reference_answer": question.get("reference_answer") or "",
            "explanation": question.get("explanation") or "",
            "feedback": feedback,
            "knowledge_point": question.get("knowledge_point") or "",
        }

    return {
        "per_question": list(validated.values()),
        "weak_points": [str(item).strip() for item in data.get("weak_points", []) if str(item).strip()][:8],
        "suggestions": [str(item).strip() for item in data.get("suggestions", []) if str(item).strip()][:6],
    }


def _attempt_report(score: int, rows: List[Dict], weak_points: List[str], suggestions: List[str]) -> str:
    wrong = [row for row in rows if row["status"] != "correct"]
    if not wrong:
        return f"## 本次结果\n\n本次作答 {score} 分，全部题目均已通过。\n\n## 下一步\n\n请用自己的话复述每道题的判断依据，确认不是猜对。"
    indexes = "、".join(str(row["question_index"]) for row in wrong)
    feedback_lines = "\n".join(
        f"- 第 {row['question_index']} 题：{row.get('feedback') or '请对照解析重做。'}"
        for row in wrong
    )
    weak_lines = "\n".join(f"- {item}" for item in weak_points) or "- 请根据错题反馈定位遗漏的概念或步骤。"
    suggestion_lines = "\n".join(f"{index}. {item}" for index, item in enumerate(suggestions, 1))
    return (
        f"## 本次结果\n\n本次作答 {score} 分，第 {indexes} 题需要重做。\n\n"
        f"## 逐题错因\n\n{feedback_lines}\n\n"
        f"## 薄弱点\n\n{weak_lines}\n\n"
        f"## 改正方法\n\n{suggestion_lines}\n\n"
        "## 下次练习\n\n只重做错题，并在答案后写出判断依据或关键步骤。"
    )


def _normalize_answers(questions: List[Dict], answers: List[Dict]) -> Dict[str, str]:
    known_ids = {question["question_id"] for question in questions}
    normalized = {}
    for item in answers or []:
        question_id = str(item.get("question_id") or "").strip()
        if not question_id or question_id not in known_ids:
            raise ValueError("作答中包含未知题号，请刷新后重试")
        if question_id in normalized:
            raise ValueError("同一道题不能重复提交")
        normalized[question_id] = str(item.get("answer") or "").strip()[:12000]
    if not any(normalized.values()):
        raise ValueError("请至少填写一道题的答案")
    return {question["question_id"]: normalized.get(question["question_id"], "") for question in questions}


def grade_exercise_attempt(
    db: Session,
    *,
    username: str,
    artifact_id: str,
    answers: List[Dict],
    answers_viewed: bool = False,
) -> Dict:
    artifact = resource_artifact_service.get_artifact(db, artifact_id)
    if not artifact:
        return {"success": False, "message": "练习题集不存在", "grading": None}

    normalized_type = artifact_types.normalize_artifact_type(artifact.get("type") or "")
    if normalized_type != artifact_types.EXERCISE_SET:
        return {"success": False, "message": "当前资源不是练习题集，不能进入作答批改", "grading": None}

    answers_viewed = bool(
        answers_viewed
        or has_answer_reveal(db, username=username, artifact_id=artifact_id)
    )

    questions = exercise_question_service.parse_exercise_content(artifact.get("content") or "")
    if not questions:
        return {"success": False, "message": "这份题集没有可批改的结构化题目", "grading": None}
    try:
        answer_map = _normalize_answers(questions, answers)
    except ValueError as exc:
        return {"success": False, "message": str(exc), "grading": None}

    objective_rows = []
    subjective_questions = []
    for question in questions:
        student_answer = answer_map[question["question_id"]]
        if question["type"] in OBJECTIVE_TYPES:
            objective_rows.append(grade_objective_question(question, student_answer))
        else:
            subjective_questions.append({**question, "student_answer": student_answer})

    subjective_result = {"per_question": [], "weak_points": [], "suggestions": []}
    if subjective_questions:
        result = llm_provider.chat_json(
            _build_subjective_prompt(artifact, subjective_questions),
            required_fields=["per_question", "weak_points", "suggestions"],
            temperature=0.15,
            max_tokens=2800,
        )
        if not result.get("ok"):
            return {
                "success": False,
                "retryable": True,
                "message": f"讯飞星火主观题批改失败：{result.get('error') or '模型未返回有效结果'}",
                "grading": None,
            }
        try:
            subjective_result = validate_subjective_grading(result.get("data") or {}, subjective_questions)
        except ValueError as exc:
            return {"success": False, "retryable": True, "message": str(exc), "grading": None}

    rows_by_id = {
        row["question_id"]: row
        for row in [*objective_rows, *subjective_result["per_question"]]
    }
    per_question = [rows_by_id[question["question_id"]] for question in questions]
    attempt_score = max(0, min(100, sum(int(row["score"]) for row in per_question)))
    wrong_knowledge = [
        row.get("knowledge_point") or f"第 {row['question_index']} 题"
        for row in per_question
        if row["status"] != "correct"
    ]
    attempt_weak_points = list(dict.fromkeys([*wrong_knowledge, *subjective_result["weak_points"]]))[:8]
    attempt_suggestions = subjective_result["suggestions"] or ["只重做本次错题，并在答案后写出判断依据。"]
    report = _attempt_report(attempt_score, per_question, attempt_weak_points, attempt_suggestions)
    standard_answers = exercise_question_service.answer_sheet(questions)

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
        "weak_points": attempt_weak_points,
        "suggestions": attempt_suggestions,
        "evidence_refs": [artifact_id],
    }
    submitted_answers = [
        {
            "question_id": question["question_id"],
            "question_index": question["question_index"],
            "answer": answer_map[question["question_id"]],
        }
        for question in questions
    ]
    answered_count = sum(1 for item in submitted_answers if str(item.get("answer") or "").strip())
    question_count = len(submitted_answers)
    reliability_values = [
        1.0 if question.get("type") in OBJECTIVE_TYPES else (0.95 if question.get("type") == "code" else 0.8)
        for question in questions
    ]
    current_reliability = sum(reliability_values) / len(reliability_values) if reliability_values else 0.85
    diagnosis = diagnosis_engine_service.calculate_diagnosis(
        db=db,
        username=username,
        resolved=resolved,
        current_text=json.dumps({"answers": submitted_answers, "attempt_score": attempt_score}, ensure_ascii=False),
        confidence=70,
        current_score=attempt_score,
        current_answered_count=answered_count,
        current_question_count=question_count,
        current_reliability=current_reliability,
        mode="exercise",
        current_weak_points=attempt_weak_points,
        current_suggestions=attempt_suggestions,
    )
    mastery_score = int(diagnosis["score"])
    mastery_level = diagnosis["level"]
    score_breakdown = diagnosis.get("score_breakdown") or []
    breakdown_text = "\n".join(
        f"- {item.get('name')}：{item.get('value')} 分，实际权重 {round(float(item.get('weight') or 0) * 100)}%，贡献 {item.get('contribution', 0)} 分"
        for item in score_breakdown
    )
    grading = {
        "score": attempt_score,
        "attempt_score": attempt_score,
        "level": _level_from_score(attempt_score),
        "mastery_score": mastery_score,
        "mastery_level": mastery_level,
        "diagnosis_status": diagnosis.get("diagnosis_status"),
        "confidence_score": diagnosis.get("confidence_score"),
        "rubric_version": diagnosis.get("rubric_version"),
        "valid_for_mastery": True,
        "answered_count": answered_count,
        "question_count": question_count,
        "completion_rate": round(answered_count / question_count, 4) if question_count else 0,
        "per_question": per_question,
        "standard_answers": standard_answers,
        "weak_points": diagnosis["weak_points"],
        "attempt_weak_points": attempt_weak_points,
        "suggestions": diagnosis["suggestions"],
        "score_breakdown": score_breakdown,
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
            "rubric_version": diagnosis.get("rubric_version"),
        },
        "diagnostic_report": (
            report.rstrip()
            + "\n\n## 长期掌握度依据\n"
            + (breakdown_text or "- 当前主要依据本次练习作答。")
        ),
        "answers_viewed": bool(answers_viewed),
        "profile_updated": False,
    }

    if answers_viewed:
        return {
            "success": True,
            "message": "批改已完成；因作答前查看过答案，本次不记入学生画像。",
            "attempt": None,
            "grading": grading,
            "diagnostic_report": None,
            "evaluation_record_id": "",
            "profile": None,
            "profile_updated": False,
        }

    now = datetime.datetime.now()
    attempt = ExerciseAttempt(
        attempt_id=f"attempt_{uuid.uuid4().hex[:16]}",
        username=username,
        course_id=location["course_id"] or COURSE_ID,
        unit_id=(location["unit_ids"] or [""])[0],
        artifact_id=artifact_id,
        answers_json=_json_dump({"answers": submitted_answers, "grading": grading}),
        score=attempt_score,
        error_pattern_json=_json_dump(attempt_weak_points),
        created_at=now,
    )
    try:
        db.add(attempt)
        diagnostic_artifact = resource_artifact_service.create_artifact(
            db,
            username=username,
            course_id=location["course_id"] or COURSE_ID,
            chapter_id=location["chapter_id"],
            section_id=location["section_id"],
            unit_ids=location["unit_ids"],
            artifact_type=artifact_types.DIAGNOSTIC_REPORT,
            title=f"{artifact.get('title') or '练习题集'} 作答诊断与补弱报告",
            summary=f"本次作答 {attempt_score} 分，长期掌握度 {mastery_score} 分。",
            content=grading["diagnostic_report"],
            evidence_refs=[artifact_id, attempt.attempt_id],
            personalization_reason="根据学生本次作答、逐题批改和历史学习证据生成。",
            source="exercise_ai_grading",
            status="published",
            agent_name="ExerciseGradingAgent",
        )
        record = EvaluationRecord(
            id=f"eval_{uuid.uuid4().hex[:16]}",
            username=username,
            course_id=location["course_id"] or COURSE_ID,
            chapter_id=location["chapter_id"],
            section_id=location["section_id"],
            unit_ids_json=_json_dump(location["unit_ids"]),
            evidence_refs_json=_json_dump([artifact_id, attempt.attempt_id]),
            diagnosis_type="exercise_ai_grading",
            topic=artifact.get("title") or "练习题集作答诊断",
            score=mastery_score,
            level=mastery_level,
            weak_points=_json_dump(diagnosis["weak_points"]),
            suggestions=_json_dump(diagnosis["suggestions"]),
            wrong_notes="学生完成练习题集后由系统逐题批改并生成。",
            answers_json=_json_dump({"answers": submitted_answers, "grading": grading}),
            generated_resource_id=diagnostic_artifact.get("artifact_id") or "",
            created_at=now,
        )
        db.add(record)
        profile_user = user_service.get_user_by_username(db, username)
        profile = profile_service.build_profile(
            user=profile_user,
            message=json.dumps({"answers": submitted_answers, "weak_points": diagnosis["weak_points"]}, ensure_ascii=False),
            intent="练习批改与补弱",
            knowledge_topic=artifact.get("title") or "练习题集作答诊断",
            score=mastery_score,
            db=db,
            semantic_result={
                "course_id": location["course_id"] or COURSE_ID,
                "chapter_id": location["chapter_id"],
                "section_id": location["section_id"],
                "unit_ids": location["unit_ids"],
                "unit_titles": location["unit_titles"],
                "topic_title": artifact.get("title") or "练习题集作答诊断",
                "weak_points": diagnosis.get("weak_points") or [],
                "subject_category": "data_structures_algorithms",
                "level": mastery_level,
                "level_source": "exercise_ai_grading",
                "level_evidence": f"本次作答 {attempt_score} 分，结合历史证据后长期掌握度 {mastery_score} 分。",
                "needs_level_diagnosis": False,
            },
        )
        profile_event_service.record_profile_event(
            db,
            username=username,
            source_type="exercise_attempt",
            source_id=attempt.attempt_id,
            profile=profile,
            reason="完成练习作答后，系统使用本次得分、错题知识点和历史证据更新画像。",
            course_id=location["course_id"] or COURSE_ID,
        )
        grading["profile_updated"] = True
        db.commit()
    except Exception:
        db.rollback()
        return {"success": False, "message": "批改已完成，但学习记录保存失败，本次未更新画像", "grading": None}

    return {
        "success": True,
        "message": "批改完成，诊断与学生画像已更新。",
        "attempt": {
            "attempt_id": attempt.attempt_id,
            "score": attempt.score,
            "created_at": attempt.created_at.isoformat(timespec="seconds"),
        },
        "grading": grading,
        "diagnostic_report": diagnostic_artifact,
        "evaluation_record_id": record.id,
        "profile": profile,
        "profile_updated": True,
    }
