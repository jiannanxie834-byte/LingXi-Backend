from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_services import resource_service
from app.services.data_services import pptx_export_service
from app.services.data_services import knowledge_evidence_service

router = APIRouter(prefix="/resource", tags=["知识库模块"])


# =========================
# 请求模型
# =========================
class ResourceCreate(BaseModel):
    title: str
    type: str
    username: str = ""
    summary: str = ""
    content: str = ""
    source: str = ""
    agent_notes: str = ""


class TypeCreateRequest(BaseModel):
    name: str
    username: str = ""
    reason: str = ""


# =========================
# 获取已通过资源
# =========================
@router.get("/list/passed")
async def list_passed(db: Session = Depends(get_db)):

    data = resource_service.get_passed_resources(db)

    return {
        "code": 200,
        "data": data or []
    }


@router.get("/recommendations")
async def list_recommendations(
    username: str = "",
    limit: int = 12,
    db: Session = Depends(get_db)
):
    data = resource_service.get_recommended_resources(
        db=db,
        username=username,
        limit=limit
    )

    return {
        "code": 200,
        "data": data or []
    }


# =========================
# 获取全部资源
# =========================
@router.get("/list/all")
async def list_all(db: Session = Depends(get_db)):

    data = resource_service.get_all_resources(db)

    return {
        "code": 200,
        "data": data or []
    }


@router.get("/evidence/search")
async def search_evidence(query: str, db: Session = Depends(get_db)):
    data = knowledge_evidence_service.search_course_evidence(db, query or "", limit=8)
    return {
        "code": 200,
        "data": data
    }


@router.get("/export/pptx/{res_id}")
async def export_resource_pptx(res_id: str, db: Session = Depends(get_db)):
    resource = resource_service.get_resource_by_id(db, res_id)

    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    output, filename = pptx_export_service.build_resource_pptx(resource)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"
        }
    )


# =========================
# 上传资源
# =========================
@router.post("/upload")
async def upload_resource(data: ResourceCreate, db: Session = Depends(get_db)):

    item = resource_service.insert_new_resource(
        db=db,
        title=data.title,
        r_type=data.type,
        summary=data.summary,
        content=data.content,
        source=data.source,
        agent_notes=data.agent_notes,
        uploader=data.username or "student",
        applicant_username=data.username or "",
    )

    if not item:
        return {
            "code": 400,
            "message": "提交失败",
            "data": None
        }

    return {
        "code": 200,
        "message": "提交成功",
        "data": item
    }


# =========================
# 审核通过
# =========================
@router.post("/approve/{res_id}")
async def approve(res_id: str, db: Session = Depends(get_db)):

    ok = resource_service.approve_resource(db, res_id)

    return {
        "code": 200 if ok else 400,
        "message": "已通过" if ok else "资源不存在"
    }


# =========================
# 驳回
# =========================
@router.delete("/reject/{res_id}")
async def reject(res_id: str, db: Session = Depends(get_db)):

    ok = resource_service.reject_resource(db, res_id)

    return {
        "code": 200 if ok else 400,
        "message": "已驳回" if ok else "资源不存在"
    }


# =========================
# 分类（全部统一兜底数组）
# =========================
@router.get("/types/all")
async def list_all_types(db: Session = Depends(get_db)):

    data = resource_service.get_all_resource_types(db)

    return {
        "code": 200,
        "data": data or []
    }


@router.get("/types/passed")
async def list_passed_types(db: Session = Depends(get_db)):

    data = resource_service.get_passed_resource_types(db)

    return {
        "code": 200,
        "data": data or []
    }


# =========================
# 提交分类
# =========================
@router.post("/types/propose")
async def propose_type(data: TypeCreateRequest, db: Session = Depends(get_db)):

    ok = resource_service.propose_new_type(db, data.name, data.username, data.reason)

    return {
        "code": 200 if ok else 400,
        "message": "提交成功" if ok else "已存在"
    }


# =========================
# 审核分类
# =========================
@router.post("/types/approve")
async def approve_type(data: TypeCreateRequest, db: Session = Depends(get_db)):

    ok = resource_service.approve_resource_type(db, data.name)

    return {
        "code": 200 if ok else 400,
        "message": "已通过" if ok else "未找到"
    }
