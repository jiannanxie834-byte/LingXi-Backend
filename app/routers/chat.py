from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_services import orchestrator_service

router = APIRouter(
    prefix="/chat",
    tags=["多智能体学习助手"]
)


# =========================
# 对话消息结构
# =========================
class ChatMessage(BaseModel):
    role: str
    content: str


# =========================
# AI聊天请求结构
# =========================
class ChatRequest(BaseModel):
    username: Optional[str] = "student"
    message: str
    history: List[ChatMessage] = Field(default_factory=list)


# =========================
# AI多智能体统一入口
# =========================
@router.post("/send")
async def send_message(
    data: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    多智能体统一聊天入口
    """

    # 空消息拦截
    if not data.message.strip():
        return {
            "code": 400,
            "message": "消息不能为空"
        }

    try:
        # =========================
        # 调用总控编排器
        # =========================
        result = orchestrator_service.handle_learning_chat(
            username=data.username or "student",
            message=data.message.strip(),
            db=db
        )

        return {
            "code": 200,
            "message": "多智能体协作完成",
            "data": result
        }

    except Exception as e:
        return {
            "code": 500,
            "message": f"AI生成失败: {str(e)}"
        }