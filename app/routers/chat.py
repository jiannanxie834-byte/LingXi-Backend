from typing import List, Optional
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_services import (
    agent_trace_service,
    chat_history_service,
    orchestrator_service,
    profile_event_service,
)

router = APIRouter(
    prefix="/chat",
    tags=["多智能体学习助手"]
)

logger = logging.getLogger(__name__)


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


@router.delete("/sessions/{session_id}")
def delete_chat_session(
    session_id: str,
    username: str = "student",
    db: Session = Depends(get_db)
):
    ok = chat_history_service.delete_session(db, username or "student", session_id)
    return {
        "code": 200 if ok else 404,
        "message": "对话已删除" if ok else "对话不存在"
    }


@router.delete("/messages/{message_id}")
def delete_chat_message(
    message_id: str,
    username: str = "student",
    db: Session = Depends(get_db)
):
    ok = chat_history_service.delete_message(db, username or "student", message_id)
    return {
        "code": 200 if ok else 404,
        "message": "消息已删除" if ok else "消息不存在"
    }


# =========================
# AI多智能体统一入口
# =========================
@router.post("/send")
def send_message(
    data: ChatRequest,
    background_tasks: BackgroundTasks,
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

        user_message = chat_history_service.save_message(
            db=db,
            username=username,
            session_id=session.id,
            role="user",
            content=message
        )

        # =========================
        # 调用总控编排器
        # =========================
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        result = orchestrator_service.handle_learning_chat(
            username=username,
            message=message,
            db=db,
            background_tasks=background_tasks,
            session_id=session.id
        )

        agent_trace_service.save_pipeline_trace(
            db,
            trace_id=trace_id,
            username=username,
            session_id=session.id,
            pipeline_steps=result.get("pipeline_steps", []),
        )
        if result.get("profile"):
            profile_event_service.record_profile_event(
                db,
                username=username,
                source_type="chat",
                source_id=session.id,
                profile=result.get("profile", {}),
                reason=f"本轮对话围绕「{result.get('topic') or '算法学习主题'}」更新画像。",
            )

        student_response = orchestrator_service.build_student_response(result, trace_id)
        reply = student_response.get("message", {}).get("content", "")
        assistant_message = chat_history_service.save_message(
            db=db,
            username=username,
            session_id=session.id,
            role="ai",
            content=reply,
            metadata={
                "student_message": student_response.get("message", {}),
                "progress": student_response.get("progress", []),
                "cards": student_response.get("cards", []),
                "resource_status": student_response.get("resource_status", {}),
                "trace_id": trace_id,
                "pipeline_steps": result.get("pipeline_steps", []),
                "safety_summary": result.get("safety_summary"),
                "evidence": result.get("evidence", []),
                "intent": result.get("intent", ""),
                "topic": result.get("topic", ""),
                "route_type": result.get("route_type", ""),
                "session_state": result.get("session_state", {}),
            }
        )
        student_response["user_message_id"] = user_message.get("id", "")
        student_response["assistant_message_id"] = assistant_message.get("id", "")
        student_response["message_id"] = assistant_message.get("id", "")

        if result.get("topic") and result.get("route_type") == "learning_request":
            session_data = chat_history_service.update_session_context(
                db,
                username,
                session.id,
                result.get("topic", "")
            )
            if session_data:
                student_response["session"] = session_data

        student_response["session_id"] = session.id
        if not student_response.get("session"):
            student_response["session"] = chat_history_service.to_session_dict(session)

        return {
            "code": 200,
            "message": result.get("response_message") or "学习建议已生成",
            "data": student_response
        }

    except Exception:
        logger.exception("Chat generation failed for username=%s", data.username or "student")
        return {
            "code": 500,
            "message": "学习包生成失败，请稍后重试，或尝试输入更具体的问题，例如“我不懂动态规划状态转移”。"
        }


@router.get("/traces/{trace_id}")
def get_chat_trace(trace_id: str, db: Session = Depends(get_db)):
    return {
        "code": 200,
        "message": "ok",
        "data": agent_trace_service.list_trace(db, trace_id),
    }
