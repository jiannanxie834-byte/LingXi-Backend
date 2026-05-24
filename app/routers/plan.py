# app/routers/plan.py 全量覆盖
from fastapi import APIRouter
from typing import Any, Union
import app.services.db_service as db_service

router = APIRouter()

@router.get("/plan/list")
async def get_plan_list(username: str):
    """【全真接通】拉取用户的规划路线"""
    plans = db_service.get_plans_by_username(username)
    return {"code": 200, "data": plans}


@router.post("/plan/save")
async def save_plan(data: Union[dict, Any]):
    """【全真接通】当学生添加、勾选、或删除路线任务时，前端会调用此接口持久化"""
    username = data.username if hasattr(data, "username") else data.get("username")
    # 拿到前端传过来的最新全量 plans 数组
    plans_list = data.plans if hasattr(data, "plans") else data.get("plans", [])
    
    db_service.save_user_plans(username, plans_list)
    return {"code": 200, "message": "智能规划路线同步保存成功"}


@router.delete("/plan/route/delete")
async def delete_route(username: str, route_id: str):
    """删除整条学习路线。"""
    db_service.delete_plan_route(username, route_id)
    return {"code": 200, "message": "学习路线已删除"}


@router.delete("/plan/node/delete")
async def delete_node(username: str, route_id: str, node_id: str):
    """删除学习路线中的某个任务节点。"""
    db_service.delete_plan_task(username, route_id, node_id)
    return {"code": 200, "message": "任务节点已删除"}
