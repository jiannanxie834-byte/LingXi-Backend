from sqlalchemy.orm import Session
from app.models.schemas import User


# =========================
# 工具函数
# =========================

def _format_user(user: User):
    """统一用户返回结构"""
    return {
        "username": user.username,
        "role": user.role,
        "avatar": user.avatar,
        "bio": user.bio,
        "hours": user.hours,
        "tags": [
            t for t in (user.tags or "").split(",")
            if t.strip()
        ]
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

        if user.password != password:
            return {
                "success": False,
                "message": "密码错误，请重新输入"
            }

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
def create_user(db: Session, username: str, password: str):
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
            "data": _format_user(user)
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"注册失败: {str(e)}"
        }