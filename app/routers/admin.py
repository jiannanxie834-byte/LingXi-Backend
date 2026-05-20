# app/routers/admin.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import db_service

router = APIRouter(prefix="/admin", tags=["超级管理员控制中枢"])

# ================= 1. 管理员统计大盘 =================
@router.get("/dashboard/stats")
async def get_admin_stats():
    """获取大盘顶部四个卡片的活数据"""
    return {"code": 200, "data": db_service.get_dashboard_stats()}

# ================= 2. 全量学生画像管理 =================
@router.get("/students/list")
async def list_all_students():
    """拉取全量学生列表，绑定后台表格"""
    return {"code": 200, "data": db_service.get_all_students()}

# ================= 3. 初始课程资源库审核 =================
@router.get("/resources/all")
async def list_all_resources():
    """获取所有资源（包括待审核、已通过）"""
    return {"code": 200, "data": db_service.get_all_resources()}

class ResourceActionRequest(BaseModel):
    id: str

@router.post("/resources/approve")
async def approve_resource(data: ResourceActionRequest):
    """管理员：审核通过资源"""
    if db_service.approve_resource(data.id):
        return {"code": 200, "message": "该课程资源已成功放行至学生前台！"}
    raise HTTPException(status_code=400, detail="未找到该资源记录")

@router.post("/resources/reject")
async def reject_resource(data: ResourceActionRequest):
    """管理员：下架或拒绝该资源"""
    if db_service.reject_resource(data.id):
        return {"code": 200, "message": "该资源已被成功驳回/下架！"}
    raise HTTPException(status_code=400, detail="操作失败，未找到记录")

# ================= 4. 学生新分类申请审核 =================
class TypeActionRequest(BaseModel):
    name: str

@router.post("/types/approve")
async def approve_resource_type(data: TypeActionRequest):
    """管理员：审核通过学生提议的新Tab分类"""
    if db_service.approve_resource_type(data.name):
        return {"code": 200, "message": f"新分类【{data.name}】已全站激活！"}
    raise HTTPException(status_code=400, detail="未找到该分类申请")

# ================= 5. 用户反馈中心模块（修复点不了的核心） =================
@router.get("/feedback/all")
async def list_all_feedbacks():
    """拉取所有学生提出来的报错与反馈"""
    return {"code": 200, "data": db_service.get_all_feedback()}

class FeedbackActionRequest(BaseModel):
    id: str

@router.post("/feedback/process")
async def process_feedback(data: FeedbackActionRequest):
    """管理员点击【处理】：标记为已处理"""
    if db_service.mark_feedback_processed(data.id):
        return {"code": 200, "message": "已成功归档并处理该用户反馈！"}
    raise HTTPException(status_code=400, detail="反馈ID不存在")

@router.post("/feedback/delete")
async def delete_feedback(data: FeedbackActionRequest):
    """管理员点击【删除】"""
    if db_service.delete_feedback_by_id(data.id):
        return {"code": 200, "message": "已成功删除该反馈记录！"}
    raise HTTPException(status_code=400, detail="删除失败")