import datetime
import uuid

from sqlalchemy.orm import Session

from app.models.schemas import Feedback


# =========================
# tools
# =========================

def _feedback_to_dict(feedback: Feedback):

    return {
        "id": feedback.id,
        "username": feedback.username,
        "content": feedback.content,
        "status": feedback.status,
        "date": feedback.date,
    }


# =========================
# 获取全部反馈
# =========================

def get_all_feedbacks(db: Session):

    try:

        feedbacks = (
            db.query(Feedback)
            .order_by(Feedback.date.desc())
            .all()
        )

        return [
            _feedback_to_dict(f)
            for f in feedbacks
        ]

    except Exception:

        return []


# =========================
# 兼容旧接口
# =========================

def get_all_feedback(db: Session):

    return get_all_feedbacks(db)


# =========================
# 新增反馈
# =========================

def insert_feedback(
    db: Session,
    username: str,
    content: str
):

    try:

        fb = Feedback(
            id=str(uuid.uuid4()),

            username=username,

            content=content,

            status="待处理",

            date=datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

        db.add(fb)

        db.commit()

        db.refresh(fb)

        return {
            "success": True,
            "data": _feedback_to_dict(fb)
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": str(e)
        }


# =========================
# 更新反馈状态
# =========================

def handle_feedback_status(
    db: Session,
    feedback_id: str
):

    try:

        fb = (
            db.query(Feedback)
            .filter(Feedback.id == feedback_id)
            .first()
        )

        if not fb:
            return False

        fb.status = "已处理"

        db.commit()

        return True

    except Exception:

        db.rollback()

        return False


# =========================
# 标记处理
# =========================

def mark_feedback_processed(
    db: Session,
    feedback_id: str
):

    return handle_feedback_status(
        db,
        feedback_id
    )


# =========================
# 删除反馈
# =========================

def delete_feedback_by_id(
    db: Session,
    feedback_id: str
):

    try:

        fb = (
            db.query(Feedback)
            .filter(Feedback.id == feedback_id)
            .first()
        )

        if not fb:
            return False

        db.delete(fb)

        db.commit()

        return True

    except Exception:

        db.rollback()

        return False