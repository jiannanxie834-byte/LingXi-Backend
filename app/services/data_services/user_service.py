from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.schemas import User


# =========================
# 获取数据库会话
# =========================

def get_db_context():
    return SessionLocal()


# =========================
# USER -> DICT
# =========================

def _user_to_dict(user: User):
    return {
        "username": user.username,
        "role": user.role,
        "avatar": user.avatar,
        "bio": user.bio,
        "hours": user.hours,
        "tags": [t for t in user.tags.split(",") if t] if user.tags else []
    }


# =========================
# 登录校验
# =========================

def check_user_login(username: str, password: str):
    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.username == username
        ).first()

        if not user:
            return {
                "success": False,
                "message": "用户不存在"
            }

        if user.password != password:
            return {
                "success": False,
                "message": "密码错误"
            }

        return {
            "success": True,
            "data": _user_to_dict(user)
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()


# =========================
# 注册用户
# =========================

def create_user(username: str, password: str):
    db = SessionLocal()

    try:
        old_user = db.query(User).filter(
            User.username == username
        ).first()

        if old_user:
            return {
                "success": False,
                "message": "用户已存在"
            }

        user = User(
            username=username,
            password=password,
            role="student",
            avatar="",
            bio="这个人十分神秘什么都没留下哟",
            hours=0,
            tags=""
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "success": True,
            "data": _user_to_dict(user)
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()


# =========================
# GET USER
# =========================

def get_user_by_username(db: Session, username: str):
    try:
        return db.query(User).filter(
            User.username == username
        ).first()

    except Exception:
        return None


# =========================
# UPDATE PROFILE
# =========================

def update_user_profile(
    db: Session,
    username: str,
    bio: str = None,
    avatar: str = None,
    password: str = None
):
    try:
        user = db.query(User).filter(
            User.username == username
        ).first()

        if not user:
            return False

        if bio is not None:
            user.bio = bio

        if avatar is not None:
            user.avatar = avatar

        if password is not None and password != "":
            user.password = password

        db.commit()
        db.refresh(user)

        return user

    except Exception:
        db.rollback()
        return False


# =========================
# UPDATE LEARNING FIELDS
# =========================

def update_user_learning_fields(
    db: Session,
    username: str,
    hours_delta: int = 0
):
    try:
        user = db.query(User).filter(
            User.username == username
        ).first()

        if not user:
            return None

        user.hours = (user.hours or 0) + hours_delta

        db.commit()
        db.refresh(user)

        return user

    except Exception:
        db.rollback()
        return None


def update_user_learning_profile(
    db: Session,
    username: str,
    tags: list,
    hours_delta: int = 0
):
    try:
        user = db.query(User).filter(
            User.username == username
        ).first()

        if not user:
            return None

        old_tags = [
            tag.strip()
            for tag in (user.tags or "").split(",")
            if tag.strip()
        ]
        merged_tags = list(dict.fromkeys(old_tags + [tag for tag in tags if tag]))
        user.tags = ",".join(merged_tags)
        user.hours = max(0, (user.hours or 0) + hours_delta)

        db.commit()
        db.refresh(user)

        return _user_to_dict(user)

    except Exception:
        db.rollback()
        return None


# =========================
# GET ALL STUDENTS
# =========================

def get_all_students(db: Session):
    try:
        students = db.query(User).filter(
            User.role == "student"
        ).all()

        return [
            _user_to_dict(student)
            for student in students
        ]

    except Exception:
        return []
