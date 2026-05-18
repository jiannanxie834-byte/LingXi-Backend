# app/routers/plan.py
from fastapi import APIRouter, HTTPException
from app.database import PLANS_DB

router = APIRouter(prefix="/plan", tags=["智能学习规划中心"])

# 1. 获取指定学生的全部学习路线
@router.get("/list")
async def get_user_plans(username: str):
    # 如果该新注册学生还没有规划，天然返回空列表，触发前端优雅的 el-empty 空状态
    return {"code": 200, "data": PLANS_DB.get(username, [])}

# 2. 废弃整条学习路线
@router.delete("/route/delete")
async def delete_entire_route(username: str, route_id: str):
    if username in PLANS_DB:
        # 过滤掉当前要删除的路线 id
        PLANS_DB[username] = [r for r in PLANS_DB[username] if r["id"] != route_id]
        return {"code": 200, "message": "整条学习路线已从核心库成功抹除！"}
    raise HTTPException(status_code=400, detail="用户不存在")

# 3. 剥离路线中的某个具体节点
@router.delete("/node/delete")
async def delete_plan_node(username: str, route_id: str, node_id: int):
    if username in PLANS_DB:
        for route in PLANS_DB[username]:
            if route["id"] == route_id:
                # 过滤掉当前要抹杀的节点 id
                route["nodes"] = [n for n in route["nodes"] if n["id"] != node_id]
                return {"code": 200, "message": "该学情任务节点已成功剥离！"}
        raise HTTPException(status_code=400, detail="未找到对应的路线")
    raise HTTPException(status_code=400, detail="用户不存在")