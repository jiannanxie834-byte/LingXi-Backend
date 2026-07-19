from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import ResourceArtifact
from app.services.data_services import profile_event_service, user_service


router = APIRouter(prefix="/profile", tags=["动态学习画像"])


def _current_username(request: Request, requested_username: str = "") -> str:
    claims = getattr(request.state, "auth", {}) or {}
    if claims.get("role") == "admin" and requested_username:
        return requested_username
    return str(claims.get("sub") or requested_username or "student")


def _public_user(user):
    if not user:
        return None
    return {
        "username": user.username,
        "nickname": user.nickname or user.username,
        "role": user.role,
        "avatar": user.avatar or "",
        "bio": user.bio or "",
        "hours": int(user.hours or 0),
        "tags": [item.strip() for item in (user.tags or "").split(",") if item.strip()],
    }


def _profile_stats(db: Session, username: str, profile: dict, user, events: list) -> dict:
    public_dimensions = profile.get("public_dimensions") if isinstance(profile.get("public_dimensions"), dict) else {}
    knowledge_entry = public_dimensions.get("当前知识水平") if isinstance(public_dimensions.get("当前知识水平"), dict) else {}
    knowledge_value = knowledge_entry.get("value")
    latest_features = (events[0].get("extracted_features") or {}) if events else {}
    evidence = latest_features.get("evidence") if isinstance(latest_features.get("evidence"), dict) else {}
    weak_entry = public_dimensions.get("薄弱知识点") if isinstance(public_dimensions.get("薄弱知识点"), dict) else {}
    weak_values = weak_entry.get("value") if isinstance(weak_entry.get("value"), list) else evidence.get("weak_points") or []
    weak_points = [str(item).strip() for item in weak_values if str(item).strip()]
    published_resources = (
        db.query(ResourceArtifact)
        .filter(
            ResourceArtifact.student_id == username,
            ResourceArtifact.status == "published",
        )
        .count()
    )
    return {
        "learning_hours": int(getattr(user, "hours", 0) or 0),
        "published_resources": published_resources,
        "knowledge_mastery": round(float(knowledge_value)) if knowledge_value is not None else 0,
        "current_weak_points": len(dict.fromkeys(weak_points)),
    }


@router.get("/me")
async def get_my_profile(request: Request, username: str = "", db: Session = Depends(get_db)):
    username = _current_username(request, username)
    user = user_service.get_user_by_username(db, username)
    events = profile_event_service.list_profile_events(db, username, limit=10)
    profile = profile_event_service.get_current_profile_snapshot(
        db,
        username,
        user=user,
    )
    return {
        "code": 200,
        "message": "ok",
        "data": {
            "user": _public_user(user),
            "profile": profile,
            "stats": _profile_stats(db, username, profile, user, events),
            "events": events,
            "latest_event": events[0] if events else None,
        },
    }


@router.get("/me/events")
async def list_my_profile_events(
    request: Request,
    username: str = "",
    limit: int = 30,
    db: Session = Depends(get_db),
):
    username = _current_username(request, username)
    return {
        "code": 200,
        "message": "ok",
        "data": profile_event_service.list_profile_events(db, username, limit=limit),
    }
