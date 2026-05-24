from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services import agent_service, db_service

router = APIRouter(prefix="/evaluation", tags=["学习评价与错题诊断"])


class EvaluationRequest(BaseModel):
    username: Optional[str] = "student"
    topic: str = Field(default="")
    wrong_notes: str = Field(default="")
    answer_summary: str = Field(default="")
    confidence: int = Field(default=60, ge=0, le=100)


class AutoEvaluationRequest(BaseModel):
    username: Optional[str] = "student"


@router.post("/auto")
async def auto_evaluation(data: AutoEvaluationRequest):
    """基于平台学习画像、规划状态、历史评价和资源记录自动生成诊断。"""
    result = agent_service.handle_auto_evaluation(username=data.username or "student")
    return {"code": 200, "message": "平台数据自动诊断已完成", "data": result}


@router.post("/submit")
async def submit_evaluation(data: EvaluationRequest):
    """学生提交自测/错题描述，生成诊断报告和补救路线。"""
    if not data.topic.strip() and not data.wrong_notes.strip() and not data.answer_summary.strip():
        return {"code": 400, "message": "请至少填写一个学习主题或错题描述"}

    result = agent_service.handle_learning_evaluation(
        username=data.username or "student",
        topic=data.topic.strip(),
        wrong_notes=data.wrong_notes.strip(),
        answer_summary=data.answer_summary.strip(),
        confidence=data.confidence,
    )
    return {"code": 200, "message": "学习评价已完成", "data": result}


@router.get("/history")
async def list_history(username: str = "student"):
    """获取学生历史评价记录。"""
    return {"code": 200, "data": db_service.get_evaluation_records(username)}
