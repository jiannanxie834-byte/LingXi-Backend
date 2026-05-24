from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services import agent_service

router = APIRouter(prefix="/chat", tags=["多智能体学习助手"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    username: Optional[str] = "student"
    message: str
    history: List[ChatMessage] = Field(default_factory=list)


@router.post("/send")
async def send_message(data: ChatRequest):
    """学生端对话入口：调用多智能体协作服务生成学习建议和资源。"""
    if not data.message.strip():
        return {"code": 400, "message": "消息不能为空"}

    result = agent_service.handle_learning_chat(
        username=data.username or "student",
        message=data.message.strip(),
        history=[item.model_dump() for item in data.history],
    )
    return {"code": 200, "message": "多智能体协作完成", "data": result}
