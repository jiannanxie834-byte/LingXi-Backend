from sqlalchemy.orm import Session
from app.models.schemas import User
from app.services.security_service import hash_password, verify_password
from app.services.data_services.knowledge_tag_service import summarize_knowledge_tags


# =========================
# 工具函数
# =========================

def _format_user(user: User):
    """统一用户返回结构"""
    tags = summarize_knowledge_tags(
        [t for t in (user.tags or "").split(",") if t.strip()]
    )
    return {
        "username": user.username,
        "nickname": user.nickname or user.username,
        "role": user.role,
        "avatar": user.avatar,
        "bio": user.bio,
        "hours": user.hours,
        "tags": tags
    }


# =========================
# 登录
# =========================
def check_user_login(db: Session, username: str, password: str):
    """
    校验用户登录
    """

    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return {
                "success": False,
                "message": "用户不存在，请先注册！"
            }

        password_ok, upgraded_hash = verify_password(password, user.password)
        if not password_ok:
            return {
                "success": False,
                "message": "密码错误，请重新输入"
            }

        if upgraded_hash:
            user.password = upgraded_hash
            db.commit()

        return {
            "success": True,
            "data": _format_user(user)
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"服务器异常: {str(e)}"
        }


# =========================
# 注册
# =========================
def create_user(db: Session, username: str, password: str, nickname: str = ""):
    """
    创建用户
    """

    try:
        exists = db.query(User).filter(User.username == username).first()

        if exists:
            return {
                "success": False,
                "message": "账号已存在，请直接登录"
            }

        user = User(
            username=username,
            nickname=(nickname or username).strip(),
            password=hash_password(password),
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
            "data": _format_user(user)
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"注册失败: {str(e)}"
        }
