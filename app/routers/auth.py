from fastapi import APIRouter
from typing import Any, Union

from app.database import SessionLocal

from app.services.data_services import (
    auth_service,
    user_service,
    feedback_service
)
from app.services.data_services.knowledge_tag_service import summarize_knowledge_tags

router = APIRouter()


# =========================
# 登录
# =========================
@router.post("/user/login")
async def login(data: Union[dict, Any]):

    db = SessionLocal()

    try:
        username = data.username if hasattr(data, "username") else data.get("username")
        password = data.password if hasattr(data, "password") else data.get("password")

        result = auth_service.check_user_login(
            db,
            username,
            password
        )

        if result["success"]:

            user_info = result["data"]

            return {
                "code": 200,
                "message": "登录成功",
                "token": f"lingxi_{user_info['username']}",
                "data": user_info
            }

        return {
            "code": 400,
            "message": result["message"]
        }

    finally:
        db.close()


# =========================
# 注册
# =========================
@router.post("/user/register")
async def register(data: Union[dict, Any]):

    db = SessionLocal()

    try:
        username = data.username if hasattr(data, "username") else data.get("username")
        nickname = data.nickname if hasattr(data, "nickname") else data.get("nickname", "")
        password = data.password if hasattr(data, "password") else data.get("password")

        result = auth_service.create_user(
            db,
            username,
            password,
            nickname
        )

        if result["success"]:
            return {
                "code": 200,
                "message": "注册成功",
                "data": result["data"]
            }

        return {
            "code": 400,
            "message": result["message"]
        }

    finally:
        db.close()


# =========================
# 提交反馈
# =========================
@router.post("/user/feedback/submit")
async def submit_feedback(data: Union[dict, Any]):

    db = SessionLocal()

    try:
        username = data.username if hasattr(data, "username") else data.get("username")
        content = data.content if hasattr(data, "content") else data.get("content")

        result = feedback_service.insert_feedback(
            db,
            username,
            content
        )

        if result["success"]:
            return {
                "code": 200,
                "message": "反馈提交成功",
                "data": result["data"]
            }

        return {
            "code": 400,
            "message": result.get("message", "反馈提交失败")
        }

    finally:
        db.close()


# =========================
# 更新用户资料
# =========================
@router.put("/user/profile/update")
async def update_profile(data: Union[dict, Any]):

    db = SessionLocal()

    try:
        username = data.username if hasattr(data, "username") else data.get("username")
        nickname = data.nickname if hasattr(data, "nickname") else data.get("nickname", None)
        bio = data.bio if hasattr(data, "bio") else data.get("bio")
        avatar = data.avatar if hasattr(data, "avatar") else data.get("avatar", "")
        password = data.password if hasattr(data, "password") else data.get("password", "")

        result = user_service.update_user_profile(
            db=db,
            username=username,
            nickname=nickname,
            bio=bio,
            avatar=avatar,
            password=password
        )

        if not result:
            return {
                "code": 400,
                "message": "更新失败"
            }

        return {
            "code": 200,
            "message": "更新成功",
            "data": {
                "username": result.username,
                "nickname": result.nickname or result.username,
                "role": result.role,
                "avatar": result.avatar,
                "bio": result.bio,
                "hours": result.hours,
                "tags": summarize_knowledge_tags(
                    [t for t in (result.tags or "").split(",") if t.strip()]
                )
            }
        }

    finally:
        db.close()
