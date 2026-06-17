import datetime
import json
import uuid

from sqlalchemy.orm import Session

from app.models.schemas import ChatMessage, ChatSession


def _now():
    return datetime.datetime.now()


def _new_id(prefix: str):
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _build_title(message: str):
    text = " ".join((message or "").strip().split())
    if not text:
        return "新对话"
    return text[:18] + ("..." if len(text) > 18 else "")


def _session_to_dict(session: ChatSession):
    return {
        "id": session.id,
        "username": session.username,
        "title": session.title or "新对话",
        "created_at": session.created_at.isoformat(sep=" ", timespec="seconds") if session.created_at else "",
        "updated_at": session.updated_at.isoformat(sep=" ", timespec="seconds") if session.updated_at else "",
    }


def _message_to_dict(message: ChatMessage):
    try:
        metadata = json.loads(message.metadata_json or "{}")
    except Exception:
        metadata = {}

    data = {
        "id": message.id,
        "session_id": message.session_id,
        "username": message.username,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(sep=" ", timespec="seconds") if message.created_at else "",
    }

    if isinstance(metadata, dict):
        data.update({
            "progress_steps": metadata.get("pipeline_steps") or metadata.get("progress_steps") or [],
            "pipeline_steps": metadata.get("pipeline_steps") or [],
            "safety_summary": metadata.get("safety_summary"),
            "evidence": metadata.get("evidence") or [],
            "intent": metadata.get("intent") or "",
        })

    return data


def list_sessions(db: Session, username: str):
    try:
        sessions = (
            db.query(ChatSession)
            .filter(ChatSession.username == username)
            .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
            .all()
        )
        return [_session_to_dict(item) for item in sessions]
    except Exception:
        return []


def get_session(db: Session, username: str, session_id: str):
    if not session_id:
        return None
    try:
        return (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.username == username)
            .first()
        )
    except Exception:
        return None


def create_session(db: Session, username: str, title: str = ""):
    session = ChatSession(
        id=_new_id("chat"),
        username=username,
        title=(title or "新对话").strip() or "新对话",
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_or_create_session(db: Session, username: str, session_id: str = "", first_message: str = ""):
    session = get_session(db, username, session_id)
    if session:
        return session
    return create_session(db, username, _build_title(first_message))


def list_messages(db: Session, username: str, session_id: str):
    session = get_session(db, username, session_id)
    if not session:
        return []

    try:
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id, ChatMessage.username == username)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        return [_message_to_dict(item) for item in messages]
    except Exception:
        return []


def save_message(db: Session, username: str, session_id: str, role: str, content: str, metadata=None):
    message = ChatMessage(
        id=_new_id("msg"),
        session_id=session_id,
        username=username,
        role=role,
        content=content or "",
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
        created_at=_now(),
    )

    session = get_session(db, username, session_id)
    if session:
        session.updated_at = _now()
        if role == "user" and (not session.title or session.title == "新对话"):
            session.title = _build_title(content)

    db.add(message)
    db.commit()
    db.refresh(message)
    return _message_to_dict(message)


def to_session_dict(session: ChatSession):
    return _session_to_dict(session)
