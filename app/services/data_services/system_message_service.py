import datetime

from sqlalchemy.orm import Session

from app.models.schemas import SystemMessage, User


def _new_message_id():
    return f"MSG{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"


def _message_to_dict(message: SystemMessage):
    return {
        "id": message.id,
        "username": message.username,
        "title": message.title,
        "content": message.content,
        "category": message.category,
        "related_resource_id": message.related_resource_id or "",
        "status": message.status,
        "created_at": message.created_at.isoformat(sep=" ", timespec="seconds") if message.created_at else "",
    }


def user_exists(db: Session, username: str):
    if not username:
        return False
    return db.query(User).filter(User.username == username).first() is not None


def create_message(
    db: Session,
    username: str,
    title: str,
    content: str,
    category: str = "资源审核",
    related_resource_id: str = "",
    commit: bool = True,
):
    if not username or not title or not content:
        return None

    if not user_exists(db, username):
        return None

    message = SystemMessage(
        id=_new_message_id(),
        username=username,
        title=title,
        content=content,
        category=category,
        related_resource_id=related_resource_id or "",
        status="未读",
        created_at=datetime.datetime.now(),
    )

    db.add(message)
    if commit:
        db.commit()
        db.refresh(message)

    return _message_to_dict(message)


def list_messages(db: Session, username: str, limit: int = 50):
    if not username:
        return []

    rows = (
        db.query(SystemMessage)
        .filter(SystemMessage.username == username)
        .order_by(SystemMessage.created_at.desc())
        .limit(max(1, min(limit, 100)))
        .all()
    )

    return [_message_to_dict(row) for row in rows]


def get_unread_count(db: Session, username: str):
    if not username:
        return 0

    return (
        db.query(SystemMessage)
        .filter(SystemMessage.username == username, SystemMessage.status == "未读")
        .count()
    )


def mark_read(db: Session, username: str, message_id: str):
    row = (
        db.query(SystemMessage)
        .filter(SystemMessage.username == username, SystemMessage.id == message_id)
        .first()
    )

    if not row:
        return False

    row.status = "已读"
    db.commit()
    return True


def mark_all_read(db: Session, username: str):
    if not username:
        return 0

    count = (
        db.query(SystemMessage)
        .filter(SystemMessage.username == username, SystemMessage.status == "未读")
        .update({"status": "已读"}, synchronize_session=False)
    )
    db.commit()
    return count
