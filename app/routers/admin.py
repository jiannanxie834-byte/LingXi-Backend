import os

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from pydantic import BaseModel
from app.models.schemas import ChatSession, CourseKnowledge, EvaluationRecord, ResourceType

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
    pending_types = len([
    t for t in resource_service.get_all_resource_types(db)
    if (t.get("status") or "").strip() == "待审核"
])

    return {
        "code": 200,
        "data": {
            "total_users": len(users),
            "total_resources": len(resources),
            "pending_resources": pending_resources,
            "pending_types": pending_types,
            "pending_feedback": pending_feedback,
            "todo_count": pending_resources + pending_feedback + pending_types
        }
    }


@router.get("/readiness")
async def demo_readiness(db: Session = Depends(get_db)):
    users = user_service.get_all_students(db)
    resources = resource_service.get_all_resources(db)
    feedbacks = feedback_service.get_all_feedbacks(db)
    resource_types = resource_service.get_all_resource_types(db)

    passed_resources = [
        item for item in resources
        if (item.get("status") or "").strip() == "已通过"
    ]
    pending_resources = [
        item for item in resources
        if (item.get("status") or "").strip() == "待审核"
    ]
    pending_types = [
        item for item in resource_types
        if (item.get("status") or "").strip() == "待审核"
    ]
    pending_feedback = [
        item for item in feedbacks
        if (item.get("status") or "").strip() == "待处理"
    ]

    checks = [
        {
            "key": "course_knowledge",
            "label": "初始课程知识库",
            "ok": db.query(CourseKnowledge).count() >= 8,
            "value": f"{db.query(CourseKnowledge).count()} 个知识点",
            "target": "不少于 1 门完整高校课程知识库",
        },
        {
            "key": "resource_types",
            "label": "个性化资源类型",
            "ok": len(resource_service.get_passed_resource_types(db)) >= 6,
            "value": f"{len(resource_service.get_passed_resource_types(db))} 类",
            "target": "至少覆盖 5 类具体资源生成，主题学习包由多类资源聚合呈现",
        },
        {
            "key": "passed_resources",
            "label": "已开放学习资源",
            "ok": len(passed_resources) >= 10,
            "value": f"{len(passed_resources)} 份",
            "target": "演示资源工厂可查阅、可导出",
        },
        {
            "key": "review_queue",
            "label": "管理员审核队列",
            "ok": len(pending_resources) + len(pending_types) + len(pending_feedback) > 0,
            "value": f"{len(pending_resources)} 资源 / {len(pending_types)} 分类 / {len(pending_feedback)} 反馈",
            "target": "可演示资源审核、分类审核、反馈处理",
        },
        {
            "key": "evaluation",
            "label": "学习效果评价",
            "ok": db.query(EvaluationRecord).count() > 0,
            "value": f"{db.query(EvaluationRecord).count()} 条记录",
            "target": "可演示诊断与补弱报告、路线调整",
        },
        {
            "key": "chat_history",
            "label": "对话历史沉淀",
            "ok": db.query(ChatSession).count() > 0,
            "value": f"{db.query(ChatSession).count()} 个会话",
            "target": "刷新页面后可恢复对话",
        },
        {
            "key": "llm",
            "label": "大模型配置",
            "ok": bool(os.getenv("DEEPSEEK_API_KEY") or os.getenv("SPARK_API_PASSWORD")),
            "value": os.getenv("LINGXI_LLM_PROVIDER", "local"),
            "target": "DeepSeek / 星火等模型密钥已配置即可调用",
        },
    ]

    return {
        "code": 200,
        "data": {
            "ready": all(item["ok"] for item in checks),
            "checks": checks,
            "summary": {
                "students": len(users),
                "resources": len(resources),
                "resource_types": db.query(ResourceType).count(),
                "feedbacks": len(feedbacks),
            }
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
    comment: str = ""


class LatestResourceApproveRequest(BaseModel):
    username: str
    limit: int = 10


@router.post("/resources/approve")
async def approve_resource(
    data: ResourceActionRequest,
    db: Session = Depends(get_db)
):
    ok = resource_service.approve_resource(db, data.id, data.comment)

    if ok:
        return {"code": 200, "message": "资源已通过审核"}

    raise HTTPException(status_code=400, detail="未找到资源")


@router.post("/resources/approve-latest")
async def approve_latest_resources(
    data: LatestResourceApproveRequest,
    db: Session = Depends(get_db)
):
    username = (data.username or "").strip()
    if not username:
        raise HTTPException(status_code=400, detail="缺少 username")

    approved = resource_service.approve_pending_resources_by_applicant(
        db,
        applicant_username=username,
        limit=data.limit,
    )

    return {
        "code": 200,
        "message": f"已通过该学生最近生成的 {len(approved)} 份资源",
        "data": {
            "count": len(approved),
            "resources": approved,
        },
    }

@router.post("/resources/reject")
async def reject_resource(
    data: ResourceActionRequest,
    db: Session = Depends(get_db)
):
    ok = resource_service.reject_resource(db, data.id, data.comment)

    if ok:
        return {"code": 200, "message": "资源已归入未通过"}

    raise HTTPException(status_code=400, detail="操作失败")


@router.post("/resources/reopen")
async def reopen_resource(
    data: ResourceActionRequest,
    db: Session = Depends(get_db)
):
    ok = resource_service.approve_resource(
        db,
        data.id,
        data.comment or "资源已根据审核要求重新上线。"
    )

    if ok:
        return {"code": 200, "message": "资源已重新上线"}

    raise HTTPException(status_code=400, detail="操作失败")


@router.post("/resources/comment")
async def update_resource_comment(
    data: ResourceActionRequest,
    db: Session = Depends(get_db)
):
    ok = resource_service.update_resource_review_comment(db, data.id, data.comment)

    if ok:
        return {"code": 200, "message": "修改意见已发送"}

    raise HTTPException(status_code=400, detail="操作失败")

class TypeActionRequest(BaseModel):
    name: str
    comment: str = ""


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


@router.post("/types/reject")
async def reject_resource_type(
    data: TypeActionRequest,
    db: Session = Depends(get_db)
):
    ok = resource_service.reject_resource_type(db, data.name, data.comment)

    if ok:
        return {
            "code": 200,
            "message": f"分类 {data.name} 已归入未通过"
        }

    raise HTTPException(status_code=400, detail="分类不存在")


@router.post("/types/reopen")
async def reopen_resource_type(
    data: TypeActionRequest,
    db: Session = Depends(get_db)
):
    ok = resource_service.approve_resource_type(db, data.name)

    if ok:
        return {
            "code": 200,
            "message": f"分类 {data.name} 已重新上线"
        }

    raise HTTPException(status_code=400, detail="分类不存在")


@router.post("/types/comment")
async def update_resource_type_comment(
    data: TypeActionRequest,
    db: Session = Depends(get_db)
):
    ok = resource_service.update_resource_type_comment(db, data.name, data.comment)

    if ok:
        return {
            "code": 200,
            "message": "分类修改意见已发送"
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
