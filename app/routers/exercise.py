from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_services import exercise_grading_service


router = APIRouter(
    prefix="/exercise",
    tags=["练习作答与 AI 批改"],
)


class ExerciseAnswer(BaseModel):
    question_id: Optional[str] = ""
    question: str = ""
    answer: str = ""


class ExerciseGradeRequest(BaseModel):
    username: Optional[str] = "student"
    artifact_id: str = Field(min_length=1)
    answers: List[ExerciseAnswer] = Field(default_factory=list)


@router.post("/grade")
async def grade_exercise(data: ExerciseGradeRequest, db: Session = Depends(get_db)):
    result = exercise_grading_service.grade_exercise_attempt(
        db=db,
        username=data.username or "student",
        artifact_id=data.artifact_id,
        answers=[item.dict() for item in data.answers],
    )
    return {
        "code": 200,
        "message": result.get("message", "AI 批改完成"),
        "data": result,
    }
