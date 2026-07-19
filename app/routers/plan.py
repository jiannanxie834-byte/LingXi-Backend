from typing import Any, Union

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_services import learning_plan_service

router = APIRouter(
    prefix="/plan",
    tags=["学习路径管理"]
)


# =========================
# 获取学习路径
# =========================
@router.get("/list")
async def get_plan_list(
    username: str,
    db: Session = Depends(get_db)
):
    """
    获取用户学习路线
    """

    try:
        plans = learning_plan_service.get_plans_by_username(
            db,
            username
        )

        return {
            "code": 200,
            "data": plans
        }

    except Exception as e:
        return {
            "code": 500,
            "message": f"获取学习路线失败: {str(e)}"
        }


# =========================
# 保存学习路径
# =========================
@router.post("/save")
async def save_plan(
    data: Union[dict, Any],
    db: Session = Depends(get_db)
):
    """
    保存学习路线
    """

    try:
        username = (
            data.username
            if hasattr(data, "username")
            else data.get("username")
        )

        plans_list = (
            data.plans
            if hasattr(data, "plans")
            else data.get("plans", [])
        )

        learning_plan_service.save_user_plans(
            db,
            username,
            plans_list
        )

        return {
            "code": 200,
            "message": "智能规划路线同步保存成功"
        }

    except Exception as e:
        return {
            "code": 500,
            "message": f"保存学习路线失败: {str(e)}"
        }


# =========================
# 删除整条路线
# =========================
@router.delete("/route/delete")
async def delete_route(
    username: str,
    route_id: str,
    db: Session = Depends(get_db)
):
    """
    删除学习路线
    """

    try:
        learning_plan_service.delete_plan_route(
            db,
            username,
            route_id
        )

        return {
            "code": 200,
            "message": "路线已删除"
        }

    except Exception as e:
        return {
            "code": 500,
            "message": f"删除路线失败: {str(e)}"
        }


# =========================
# 删除节点
# =========================
@router.delete("/node/delete")
async def delete_node(
    username: str,
    route_id: str,
    node_id: str,
    db: Session = Depends(get_db)
):
    """
    删除学习节点
    """

    try:
        learning_plan_service.delete_plan_task(
            db,
            username,
            route_id,
            node_id
        )

        return {
            "code": 200,
            "message": "节点已删除"
        }

    except Exception as e:
        return {
            "code": 500,
            "message": f"删除节点失败: {str(e)}"
        }
