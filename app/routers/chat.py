from typing import List, Optional
import json
import time
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
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
                reason=f"本轮对话围绕「{result.get('topic') or '深度学习主题'}」更新画像。",
            )

        student_response = orchestrator_service.build_student_response(result, trace_id)
        reply = student_response.get("message", {}).get("content", "")
        chat_history_service.save_message(
            db=db,
            username=username,
            session_id=session.id,
            role="ai",
            content=reply,
            metadata={
                "student_message": student_response.get("message", {}),
                "progress": student_response.get("progress", []),
                "cards": student_response.get("cards", []),
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

    except Exception as e:
        return {
            "code": 500,
            "message": f"AI生成失败: {str(e)}"
        }


@router.get("/traces/{trace_id}")
def get_chat_trace(trace_id: str, db: Session = Depends(get_db)):
    return {
        "code": 200,
        "message": "ok",
        "data": agent_trace_service.list_trace(db, trace_id),
    }


def _sse(data: dict, event: str = "message"):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/stream")
def stream_message(
    data: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    def generate():
        progress_events = [
            ("已识别学习需求", 10, "IntentSemanticAgent"),
            ("已归一到《深度学习》课程知识单元", 25, "CourseMapAgent"),
            ("已更新学生画像", 40, "ProfileAgent"),
            ("已检索课程知识库", 55, "EvidenceRetrievalAgent"),
            ("正在生成学习路径与资源计划", 70, "LearningPathAgent"),
        ]
        for message, progress, agent in progress_events:
            yield _sse({"message": message, "progress": progress, "agent": agent}, event="progress")
            time.sleep(0.05)
        result = send_message(data, background_tasks, db)
        yield _sse({"message": "已完成学生端回答组装", "progress": 100, "agent": "FinalResponseComposer"}, event="progress")
        yield _sse(result, event="result")

    return StreamingResponse(generate(), media_type="text/event-stream")
