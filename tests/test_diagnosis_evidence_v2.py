import datetime
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.schemas import (
    ChatMessage,
    EvaluationRecord,
    ExerciseAttempt,
    LearningPlan,
    ResourceArtifact,
    ResourceFeedback,
    TodoList,
)
from app.services.data_services import diagnosis_engine_service, evaluation_service


RESOLVED_DP = {
    "topic": "动态规划",
    "chapter_id": "chapter_10_dynamic_programming",
    "section_id": "sec_10_dp_intro",
    "unit_ids": ["dsa_dp_intro"],
    "unit_titles": ["动态规划基本思想"],
    "matched": True,
    "weak_points": [],
    "suggestions": [],
}


def _db_session():
    engine = create_engine("sqlite:///:memory:")
    for model in [
        EvaluationRecord,
        ExerciseAttempt,
        LearningPlan,
        TodoList,
        ResourceArtifact,
        ResourceFeedback,
        ChatMessage,
    ]:
        model.__table__.create(bind=engine)
    return sessionmaker(bind=engine)()


def _valid_attempt(attempt_id, score, created_at, answers=4):
    submitted = [
        {"question_id": f"q{index}", "answer": "A"}
        for index in range(1, answers + 1)
    ]
    rows = [
        {
            "question_id": f"q{index}",
            "type": "single_choice",
            "student_answer": "A",
            "status": "correct" if score else "incorrect",
        }
        for index in range(1, answers + 1)
    ]
    return ExerciseAttempt(
        attempt_id=attempt_id,
        username="student",
        course_id="data_structures_algorithms",
        unit_id="dsa_dp_intro",
        artifact_id="artifact_dp",
        answers_json=json.dumps({"answers": submitted, "grading": {"per_question": rows}}),
        score=score,
        error_pattern_json="[]",
        created_at=created_at,
    )


def test_blank_legacy_attempt_and_auto_snapshots_do_not_become_mastery_evidence():
    db = _db_session()
    try:
        legacy_answers = [{"question_id": "1", "question": "题集简介", "answer": "1"}]
        legacy_answers.extend(
            {"question_id": str(index), "question": f"题目 {index - 1}", "answer": ""}
            for index in range(2, 8)
        )
        grading_rows = [
            {"question_index": index, "score": 0, "is_correct": False, "feedback": "学生答案为空，未作答。"}
            for index in range(1, 7)
        ]
        db.add(ExerciseAttempt(
            attempt_id="legacy_blank",
            username="student",
            course_id="data_structures_algorithms",
            unit_id="dsa_dp_intro",
            artifact_id="artifact_old",
            answers_json=json.dumps({"answers": legacy_answers, "grading": {"per_question": grading_rows}}),
            score=0,
            error_pattern_json="[]",
            created_at=datetime.datetime.now(),
        ))
        db.add(EvaluationRecord(
            id="auto_snapshot",
            username="student",
            diagnosis_type="auto_multi_factor",
            topic="动态规划",
            score=20,
            level="重点补救",
            weak_points="[]",
            suggestions="[]",
            answers_json="{}",
            created_at=datetime.datetime.now(),
        ))
        db.commit()

        result = diagnosis_engine_service.calculate_diagnosis(
            db=db,
            username="student",
            resolved=RESOLVED_DP,
            mode="auto",
        )

        assert result["score"] is None
        assert result["level"] == "证据不足"
        assert result["diagnosis_status"] == "insufficient_evidence"
        assert result["evidence"]["evidence_count"] == 0
        assert result["evidence"]["excluded_evidence_count"] == 2
        assert result["weak_points"] == ["尚无足够的有效作答，当前不能据此判断知识薄弱点。"]
    finally:
        db.close()


def test_completed_recent_exercise_produces_reproducible_mastery_and_confidence():
    db = _db_session()
    try:
        db.add(_valid_attempt("attempt_recent", 80, datetime.datetime.now(), answers=4))
        db.commit()

        result = diagnosis_engine_service.calculate_diagnosis(
            db=db,
            username="student",
            resolved=RESOLVED_DP,
            mode="auto",
        )

        assert result["score"] == 80
        assert result["diagnosis_status"] == "established"
        assert result["confidence_score"] >= 70
        assert result["score_breakdown"][0]["weight"] == 1.0
        assert result["score_breakdown"][0]["contribution"] == 80.0
        assert result["evidence"]["answered_item_count"] == 4
    finally:
        db.close()


def test_recency_is_based_on_timestamps_across_one_event_stream():
    db = _db_session()
    try:
        db.add(_valid_attempt("attempt_old", 100, datetime.datetime.now() - datetime.timedelta(days=60)))
        db.add(_valid_attempt("attempt_new", 0, datetime.datetime.now()))
        db.commit()

        result = diagnosis_engine_service.calculate_diagnosis(
            db=db,
            username="student",
            resolved=RESOLVED_DP,
            mode="auto",
        )

        assert 15 <= result["score"] <= 25
        assert result["score_breakdown"][0]["source_id"] == "attempt_new"
        assert result["score_breakdown"][0]["weight"] > result["score_breakdown"][1]["weight"]
    finally:
        db.close()


def test_long_manual_reflection_is_scored_separately_from_mastery():
    db = _db_session()
    try:
        result = diagnosis_engine_service.calculate_diagnosis(
            db=db,
            username="student",
            resolved=RESOLVED_DP,
            current_text="我写错是因为状态定义不清，应该重新调整转移式，并用边界例子测试验证。",
            confidence=100,
            mode="manual",
        )

        assert result["score"] is None
        assert result["reflection_score"] == 100
        assert result["diagnosis_status"] == "insufficient_evidence"
    finally:
        db.close()


def test_cold_start_record_preserves_semantic_null_despite_legacy_column_default():
    db = _db_session()
    try:
        record = EvaluationRecord(
            id="cold_start",
            username="student",
            diagnosis_type="auto_multi_factor",
            topic="动态规划",
            score=None,
            level="证据不足",
            weak_points=json.dumps(["照搬公式不看状态"], ensure_ascii=False),
            suggestions="[]",
            answers_json=json.dumps({
                "diagnosis_status": "insufficient_evidence",
                "rubric_version": diagnosis_engine_service.RUBRIC_VERSION,
            }),
            created_at=datetime.datetime.now(),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        result = evaluation_service._evaluation_to_dict(record)

        assert record.score == 0
        assert result["score"] is None
        assert result["algorithm_status"] == "current"
        assert result["weak_points"] == ["尚无足够的有效作答，当前不能据此判断知识薄弱点。"]
    finally:
        db.close()
