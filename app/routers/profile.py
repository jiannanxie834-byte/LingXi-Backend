from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_services import profile_event_service, user_service


router = APIRouter(prefix="/profile", tags=["动态学习画像"])


@router.get("/me")
async def get_my_profile(username: str = "student", db: Session = Depends(get_db)):
    user = user_service.get_user_by_username(db, username or "student")
    events = profile_event_service.list_profile_events(db, username or "student", limit=10)
    return {
        "code": 200,
        "message": "ok",
        "data": {
            "user": user,
            "events": events,
            "latest_event": events[0] if events else None,
        },
    }


@router.get("/me/events")
async def list_my_profile_events(
    username: str = "student",
    limit: int = 30,
    db: Session = Depends(get_db),
):
    return {
        "code": 200,
        "message": "ok",
        "data": profile_event_service.list_profile_events(db, username or "student", limit=limit),
    }
