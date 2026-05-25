from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from pydantic import BaseModel

from app.services.data_services import (
    user_service,
    resource_service,
    feedback_service
)

router = APIRouter(prefix="/admin", tags=["超级管理员控制中枢"])

@router.get("/dashboard/stats")
async def dashboard_stats(db: Session = Depends(get_db)):

    users = user_service.get_all_students(db)
    resources = resource_service.get_all_resources(db)
    feedbacks = feedback_service.get_all_feedbacks(db)

    pending_resources = len([
    r for r in resources
    if (r.get("status") or "").strip() == "待审核"
])

    pending_feedback = len([
    f for f in feedbacks
    if (f.get("status") or "").strip() == "待处理"
])

    return {
        "code": 200,
        "data": {
            "total_users": len(users),
            "total_resources": len(resources),
            "pending_resources": pending_resources,
            "pending_feedback": pending_feedback,
            "todo_count": pending_resources + pending_feedback
        }
    }

@router.get("/students/list")
async def list_all_students(
    db: Session = Depends(get_db)
):
    students = user_service.get_all_students(db)
    return {
        "code": 200,
        "data": students
    }

@router.get("/resources/all")
async def list_all_resources(
    db: Session = Depends(get_db)
):
    return {
        "code": 200,
        "data": resource_service.get_all_resources(db)
    }

class ResourceActionRequest(BaseModel):
    id: str

@router.post("/resources/approve")
async def approve_resource(
    data: ResourceActionRequest,
    db: Session = Depends(get_db)
):
    ok = resource_service.approve_resource(db, data.id)

    if ok:
        return {"code": 200, "message": "资源已通过审核"}

    raise HTTPException(status_code=400, detail="未找到资源")

@router.post("/resources/reject")
async def reject_resource(
    data: ResourceActionRequest,
    db: Session = Depends(get_db)
):
    ok = resource_service.reject_resource(db, data.id)

    if ok:
        return {"code": 200, "message": "资源已驳回"}

    raise HTTPException(status_code=400, detail="操作失败")

class TypeActionRequest(BaseModel):
    name: str


@router.post("/types/approve")
async def approve_resource_type(
    data: TypeActionRequest,
    db: Session = Depends(get_db)
):
    ok = resource_service.approve_resource_type(
        db,
        data.name
    )

    if ok:
        return {
            "code": 200,
            "message": f"分类 {data.name} 已通过"
        }

    raise HTTPException(status_code=400, detail="分类不存在")

@router.get("/feedback/all")
async def list_all_feedbacks(
    db: Session = Depends(get_db)
):
    return {
        "code": 200,
        "data": feedback_service.get_all_feedbacks(db)
    }

class FeedbackActionRequest(BaseModel):
    id: str


@router.post("/feedback/process")
async def process_feedback(
    data: FeedbackActionRequest,
    db: Session = Depends(get_db)
):
    ok = feedback_service.mark_feedback_processed(
        db,
        data.id
    )

    if ok:
        return {"code": 200, "message": "已处理"}

    raise HTTPException(status_code=400, detail="不存在")

@router.post("/feedback/delete")
async def delete_feedback(
    data: FeedbackActionRequest,
    db: Session = Depends(get_db)
):
    ok = feedback_service.delete_feedback_by_id(
        db,
        data.id
    )

    if ok:
        return {"code": 200, "message": "已删除"}

    raise HTTPException(status_code=400, detail="删除失败")