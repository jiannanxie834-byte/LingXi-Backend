from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_services import generation_job_service, resource_artifact_service


router = APIRouter(prefix="/generation", tags=["生成任务与进度"])


class GenerationJobCreate(BaseModel):
    username: str = "student"
    topic: str = ""
    unit_id: str = ""


@router.post("/jobs")
async def create_generation_job(data: GenerationJobCreate, db: Session = Depends(get_db)):
    job = generation_job_service.create_job(
        db,
        username=data.username or "student",
        topic=data.topic,
        unit_id=data.unit_id,
        message="已创建手动 Artifact 生成任务",
    )
    return {"code": 200, "message": "ok", "data": job}


@router.get("/jobs/{job_id}")
async def get_generation_job(job_id: str, db: Session = Depends(get_db)):
    return {"code": 200, "message": "ok", "data": generation_job_service.get_job(db, job_id)}


@router.get("/jobs/{job_id}/events")
async def list_generation_job_events(job_id: str, db: Session = Depends(get_db)):
    return {"code": 200, "message": "ok", "data": generation_job_service.list_events(db, job_id)}


@router.get("/jobs/{job_id}/artifacts")
async def list_generation_job_artifacts(job_id: str, db: Session = Depends(get_db)):
    job = generation_job_service.get_job(db, job_id)
    artifact_ids = set(job.get("artifacts") or [])
    artifacts = [
        item for item in resource_artifact_service.list_artifacts(db, limit=200)
        if item.get("artifact_id") in artifact_ids
    ]
    return {"code": 200, "message": "ok", "data": artifacts}
