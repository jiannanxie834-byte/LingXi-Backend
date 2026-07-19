from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_services import (
    exercise_grading_service,
    exercise_question_service,
    resource_artifact_service,
    resource_artifact_type_service as artifact_types,
)


router = APIRouter(
    prefix="/exercise",
    tags=["练习作答与 AI 批改"],
)


class ExerciseAnswer(BaseModel):
    question_id: Optional[str] = ""
    answer: str = Field(default="", max_length=12000)


class ExerciseGradeRequest(BaseModel):
    artifact_id: str = Field(min_length=1)
    answers: List[ExerciseAnswer] = Field(default_factory=list)
    answers_viewed: bool = False


def _current_user(request: Request):
    claims = getattr(request.state, "auth", {}) or {}
    return str(claims.get("sub") or ""), str(claims.get("role") or "student")


def _can_access(artifact, username: str, role: str) -> bool:
    owner = str((artifact or {}).get("student_id") or "")
    return role == "admin" or not owner or owner == username


@router.post("/grade")
async def grade_exercise(data: ExerciseGradeRequest, request: Request, db: Session = Depends(get_db)):
    username, role = _current_user(request)
    artifact = resource_artifact_service.get_artifact(db, data.artifact_id)
    if artifact and not _can_access(artifact, username, role):
        return {"code": 403, "message": "无权作答这份练习", "data": {"success": False, "grading": None}}
    result = exercise_grading_service.grade_exercise_attempt(
        db=db,
        username=username,
        artifact_id=data.artifact_id,
        answers=[item.dict() for item in data.answers],
        answers_viewed=data.answers_viewed,
    )
    return {
        "code": 200,
        "message": result.get("message", "AI 批改完成"),
        "data": result,
    }


@router.get("/{artifact_id}/answers")
async def reveal_exercise_answers(artifact_id: str, request: Request, db: Session = Depends(get_db)):
    username, role = _current_user(request)
    artifact = resource_artifact_service.get_artifact(db, artifact_id)
    if not artifact:
        return {"code": 404, "message": "练习题集不存在", "data": []}
    if not _can_access(artifact, username, role):
        return {"code": 403, "message": "无权查看这份练习", "data": []}
    if artifact_types.normalize_artifact_type(artifact.get("type") or "") != artifact_types.EXERCISE_SET:
        return {"code": 400, "message": "当前资源不是练习题集", "data": []}
    questions = exercise_question_service.parse_exercise_content(artifact.get("content") or "")
    if questions:
        exercise_grading_service.record_answer_reveal(
            db,
            username=username,
            artifact_id=artifact_id,
        )
        db.commit()
    return {
        "code": 200,
        "message": "查看答案后的作答不记入学生画像",
        "data": exercise_question_service.answer_sheet(questions),
    }
