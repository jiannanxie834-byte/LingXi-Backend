from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_services import chat_history_service, orchestrator_service

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
    session_id: Optional[str] = ""
    message: str
    history: List[ChatMessage] = Field(default_factory=list)


class ChatSessionCreateRequest(BaseModel):
    username: Optional[str] = "student"
    title: Optional[str] = "新对话"


@router.get("/sessions")
def list_chat_sessions(
    username: str = "student",
    db: Session = Depends(get_db)
):
    return {
        "code": 200,
        "data": chat_history_service.list_sessions(db, username or "student")
    }


@router.post("/session/new")
def create_chat_session(
    data: ChatSessionCreateRequest,
    db: Session = Depends(get_db)
):
    session = chat_history_service.create_session(
        db,
        data.username or "student",
        data.title or "新对话"
    )
    return {
        "code": 200,
        "data": chat_history_service.to_session_dict(session)
    }


@router.get("/sessions/{session_id}/messages")
def list_chat_messages(
    session_id: str,
    username: str = "student",
    db: Session = Depends(get_db)
):
    return {
        "code": 200,
        "data": chat_history_service.list_messages(db, username or "student", session_id)
    }


# =========================
# AI多智能体统一入口
# =========================
@router.post("/send")
def send_message(
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

    username = data.username or "student"
    message = data.message.strip()

    try:
        session = chat_history_service.get_or_create_session(
            db=db,
            username=username,
            session_id=data.session_id or "",
            first_message=message
        )

        chat_history_service.save_message(
            db=db,
            username=username,
            session_id=session.id,
            role="user",
            content=message
        )

        # =========================
        # 调用总控编排器
        # =========================
        result = orchestrator_service.handle_learning_chat(
            username=username,
            message=message,
            db=db
        )

        reply = result.get("reply", "")
        chat_history_service.save_message(
            db=db,
            username=username,
            session_id=session.id,
            role="ai",
            content=reply,
            metadata={
                "pipeline_steps": result.get("pipeline_steps", []),
                "safety_summary": result.get("safety_summary"),
                "evidence": result.get("evidence", []),
                "intent": result.get("intent", ""),
            }
        )

        result["session_id"] = session.id
        result["session"] = chat_history_service.to_session_dict(session)

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
