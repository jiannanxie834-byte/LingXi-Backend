from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_services import system_message_service


router = APIRouter(prefix="/user/messages", tags=["学生系统消息"])


class MessageReadRequest(BaseModel):
    username: str
    id: str = ""


@router.get("/list")
async def list_messages(username: str, db: Session = Depends(get_db)):
    return {
        "code": 200,
        "data": system_message_service.list_messages(db, username)
    }


@router.get("/unread-count")
async def unread_count(username: str, db: Session = Depends(get_db)):
    return {
        "code": 200,
        "data": {
            "count": system_message_service.get_unread_count(db, username)
        }
    }


@router.post("/read")
async def mark_message_read(data: MessageReadRequest, db: Session = Depends(get_db)):
    ok = system_message_service.mark_read(db, data.username, data.id)
    if ok:
        return {"code": 200, "message": "已标记为已读"}
    raise HTTPException(status_code=400, detail="消息不存在")


@router.post("/read-all")
async def mark_all_read(data: MessageReadRequest, db: Session = Depends(get_db)):
    count = system_message_service.mark_all_read(db, data.username)
    return {
        "code": 200,
        "message": "已全部标记为已读",
        "data": {
            "count": count
        }
    }
