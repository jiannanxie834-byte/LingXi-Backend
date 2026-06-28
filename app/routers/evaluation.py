from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_services import evaluation_service

router = APIRouter(
    prefix="/evaluation",
    tags=["学习评价与错题诊断"]
)


class EvaluationRequest(BaseModel):
    username: Optional[str] = "student"
    course_id: str = Field(default="data_structures_algorithms")
    chapter_id: str = Field(default="")
    section_id: str = Field(default="")
    unit_ids: List[str] = Field(default_factory=list)
    topic: str = Field(default="")
    wrong_notes: str = Field(default="")
    answer_summary: str = Field(default="")
    confidence: int = Field(default=60, ge=0, le=100)


class AutoEvaluationRequest(BaseModel):
    username: Optional[str] = "student"


class RemediationRequest(BaseModel):
    username: Optional[str] = "student"
    record_id: str = Field(default="")
    topic: str = Field(default="")
    wrong_notes: str = Field(default="")
    answer_summary: str = Field(default="")
    chapter_id: str = Field(default="")
    section_id: str = Field(default="")
    unit_ids: List[str] = Field(default_factory=list)


# =========================
# 自动诊断
# =========================
@router.post("/auto")
async def auto_evaluation(
    data: AutoEvaluationRequest,
    db: Session = Depends(get_db)
):

    result = evaluation_service.handle_auto_evaluation(
        db=db,
        username=data.username or "student",
    )

    return {
        "code": 200,
        "message": "平台自动诊断完成",
        "data": result
    }


# =========================
# 学生提交评价
# =========================
@router.post("/submit")
async def submit_evaluation(
    data: EvaluationRequest,
    db: Session = Depends(get_db)
):

    if not data.topic.strip() and not data.wrong_notes.strip() and not data.answer_summary.strip():
        return {
            "code": 400,
            "message": "请至少填写一个学习内容"
        }

    result = evaluation_service.handle_learning_evaluation(
        db=db,
        username=data.username or "student",
        topic=data.topic.strip(),
        wrong_notes=data.wrong_notes.strip(),
        answer_summary=data.answer_summary.strip(),
        confidence=data.confidence,
        course_id=data.course_id or "data_structures_algorithms",
        chapter_id=data.chapter_id,
        section_id=data.section_id,
        unit_ids=data.unit_ids,
    )

    return {
        "code": 200,
        "message": "学习评价完成",
        "data": result
    }


# =========================
# 历史记录
# =========================
@router.get("/history")
async def list_history(
    username: str = "student",
    db: Session = Depends(get_db)
):

    data = evaluation_service.get_evaluation_records(
        db,
        username
    )

    # 防止前端 rows is not iterable
    if isinstance(data, dict):
        return {
            "code": 500,
            "data": [],
            "message": data.get("message", "获取失败")
        }

    return {
        "code": 200,
        "data": data
    }


@router.post("/remediation-package")
async def generate_remediation_package(
    data: RemediationRequest,
    db: Session = Depends(get_db),
):
    result = evaluation_service.generate_remediation_package(
        db=db,
        username=data.username or "student",
        record_id=data.record_id,
        payload=data.dict(),
    )
    return {
        "code": 200,
        "message": "补弱学习包已生成",
        "data": result,
    }
