from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_services import (
    evaluation_service,
    orchestrator_service
)

router = APIRouter(
    prefix="/evaluation",
    tags=["学习评价与错题诊断"]
)


class EvaluationRequest(BaseModel):
    username: Optional[str] = "student"
    topic: str = Field(default="")
    wrong_notes: str = Field(default="")
    answer_summary: str = Field(default="")
    confidence: int = Field(default=60, ge=0, le=100)


class AutoEvaluationRequest(BaseModel):
    username: Optional[str] = "student"


# =========================
# 自动诊断
# =========================
@router.post("/auto")
async def auto_evaluation(
    data: AutoEvaluationRequest,
    db: Session = Depends(get_db)
):

    result = orchestrator_service.handle_learning_chat(
        username=data.username or "student",
        message="自动学习诊断请求",
        db=db
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

    message = f"""
学习主题: {data.topic}
错题记录: {data.wrong_notes}
答案总结: {data.answer_summary}
置信度: {data.confidence}
"""

    result = orchestrator_service.handle_learning_chat(
        username=data.username or "student",
        message=message,
        db=db
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