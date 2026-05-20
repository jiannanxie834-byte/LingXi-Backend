from fastapi import APIRouter
from pydantic import BaseModel
from app.services import db_service

router = APIRouter(prefix="/resource", tags=["高校初始知识库模块"])

class ResourceCreate(BaseModel):
    title: str
    type: str

class TypeCreateRequest(BaseModel):
    name: str

@router.get("/list/passed")
async def list_passed():
    """学生前台：只看审核通过的初始资源"""
    return {"code": 200, "data": db_service.get_passed_resources()}

@router.get("/list/all")
async def list_all():
    """管理后台：看全量资源（包含待审核）"""
    return {"code": 200, "data": db_service.get_all_resources()}

@router.post("/upload")
async def upload_resource(data: ResourceCreate):
    """提交上传新资源"""
    item = db_service.insert_new_resource(data.title, data.type)
    return {"code": 200, "message": "提交成功，已送往管理后台审核！", "data": item}

@router.post("/approve/{res_id}")
async def approve(res_id: str):
    """管理员点击同意"""
    if db_service.approve_resource(res_id):
        return {"code": 200, "message": "该资源已成功流转至前台知识库！"}
    return {"code": 400, "message": "资源不存在"}

@router.delete("/reject/{res_id}")
async def reject(res_id: str):
    """管理员点击拒绝/删除"""
    if db_service.reject_resource(res_id):
        return {"code": 200, "message": "资源已成功驳回并销毁！"}
    return {"code": 400, "message": "资源不存在"}

@router.get("/types/passed")
async def list_passed_types():
    """学生前台：动态拉取已通过的 Tab 分类"""
    return {"code": 200, "data": db_service.get_passed_resource_types()}

@router.get("/types/all")
async def list_all_types():
    """管理后台：获取所有类型用于表格审核"""
    return {"code": 200, "data": db_service.get_all_resource_types()}

@router.post("/types/propose")
async def propose_type(data: TypeCreateRequest):
    """学生前台：提交新类型申请"""
    if db_service.propose_new_type(data.name):
        return {"code": 200, "message": "新类型申请成功，已送往管理中枢审核！"}
    return {"code": 400, "message": "该类型已存在，无需重复申请"}

@router.post("/types/approve")
async def approve_type(data: TypeCreateRequest):
    """管理员：同意新类型通过"""
    if db_service.approve_resource_type(data.name):
        return {"code": 200, "message": "新分类已全站动态激活！"}
    return {"code": 400, "message": "未找到该类型记录"}