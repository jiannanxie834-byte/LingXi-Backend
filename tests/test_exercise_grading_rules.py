import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.schemas import ExerciseAnswerReveal
from app.services.data_services.exercise_grading_service import (
    grade_objective_question,
    has_answer_reveal,
    record_answer_reveal,
    validate_subjective_grading,
)


def test_choice_and_boolean_questions_are_graded_deterministically():
    choice = {
        "question_id": "q1",
        "question_index": 1,
        "type": "single_choice",
        "options": [{"key": "A", "text": "先定义状态"}, {"key": "B", "text": "先写代码"}],
        "reference_answer": "A",
        "explanation": "状态定义是前提。",
        "knowledge_point": "状态定义",
        "points": 50,
    }
    boolean = {
        "question_id": "q2",
        "question_index": 2,
        "type": "true_false",
        "options": [],
        "reference_answer": "错。",
        "explanation": "还需要其他条件。",
        "knowledge_point": "适用条件",
        "points": 50,
    }

    assert grade_objective_question(choice, "A")["score"] == 50
    assert grade_objective_question(choice, "先定义状态")["is_correct"] is True
    assert grade_objective_question(choice, "B")["status"] == "incorrect"
    assert grade_objective_question(boolean, "错误")["score"] == 50
    assert grade_objective_question(boolean, "")["status"] == "skipped"


def test_subjective_grading_requires_exact_question_ids_and_score_bounds():
    questions = [{
        "question_id": "q1",
        "question_index": 1,
        "type": "short_answer",
        "student_answer": "先定义状态，再写转移。",
        "reference_answer": "定义状态、转移和初始化。",
        "explanation": "关键是依赖关系。",
        "knowledge_point": "状态设计",
        "points": 40,
    }]
    valid = validate_subjective_grading({
        "per_question": [{
            "question_id": "q1",
            "question_index": 1,
            "score": 32,
            "is_correct": True,
            "feedback": "思路正确，但缺少初始化。",
        }],
        "weak_points": ["初始化"],
        "suggestions": ["补充边界状态。"],
        "diagnostic_report": "## 错因\n缺少初始化。",
    }, questions)

    assert valid["per_question"][0]["score"] == 32
    assert valid["per_question"][0]["status"] == "correct"

    with pytest.raises(ValueError, match="超出"):
        validate_subjective_grading({
            "per_question": [{
                "question_id": "q1",
                "question_index": 1,
                "score": 41,
                "is_correct": True,
                "feedback": "超分。",
            }],
            "weak_points": [],
            "suggestions": [],
            "diagnostic_report": "报告",
        }, questions)

    with pytest.raises(ValueError, match="未知或重复"):
        validate_subjective_grading({
            "per_question": [{
                "question_id": "client_fake_id",
                "question_index": 1,
                "score": 20,
                "is_correct": False,
                "feedback": "无效题号。",
            }],
            "weak_points": [],
            "suggestions": [],
            "diagnostic_report": "报告",
        }, questions)


def test_answer_reveal_is_recorded_server_side_once():
    engine = create_engine("sqlite:///:memory:")
    ExerciseAnswerReveal.__table__.create(bind=engine)
    db = sessionmaker(bind=engine)()
    try:
        assert has_answer_reveal(db, username="student", artifact_id="artifact_demo") is False
        record_answer_reveal(db, username="student", artifact_id="artifact_demo")
        record_answer_reveal(db, username="student", artifact_id="artifact_demo")
        db.commit()

        assert has_answer_reveal(db, username="student", artifact_id="artifact_demo") is True
        assert db.query(ExerciseAnswerReveal).count() == 1
    finally:
        db.close()
