from fastapi import APIRouter
from typing import Any, Union

from app.database import SessionLocal

from app.services.data_services import learning_plan_service as todo_service

router = APIRouter()


# =========================
# 获取待办
# =========================

@router.get("/todo/list")
async def get_todo_list(username: str):
    db = SessionLocal()

    try:
        todos = todo_service.get_todos_by_username(
            db,
            username
        )

        return {
            "code": 200,
            "data": todos
        }

    finally:
        db.close()


# =========================
# 保存待办
# =========================

@router.post("/todo/save")
async def save_todo(data: Union[dict, Any]):
    db = SessionLocal()

    try:
        username = (
            data.username
            if hasattr(data, "username")
            else data.get("username")
        )

        todos = (
            data.todos
            if hasattr(data, "todos")
            else data.get("todos", [])
        )

        todo_service.save_user_todos(
            db,
            username,
            todos
        )

        return {
            "code": 200,
            "message": "待办事项保存成功"
        }

    finally:
        db.close()
