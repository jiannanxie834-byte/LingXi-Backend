import datetime
import json
import uuid
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.schemas import GenerationJob, GenerationJobEvent


def _json_dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def create_job(
    db: Session,
    *,
    username: str,
    topic: str = "",
    unit_id: str = "",
    course_id: str = "deep_learning",
    message: str = "已创建资源生成任务",
) -> Dict:
    now = datetime.datetime.now()
    job = GenerationJob(
        job_id=f"job_{uuid.uuid4().hex[:16]}",
        username=username,
        course_id=course_id,
        topic=topic or "",
        unit_id=unit_id or "",
        status="queued",
        progress=0,
        message=message,
        artifacts_json="[]",
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    db.flush()
    add_event(db, job.job_id, event="job_created", agent="CoordinatorAgent", message=message, progress=0, commit=False)
    db.commit()
    return to_dict(job)


def add_event(
    db: Session,
    job_id: str,
    *,
    event: str,
    agent: str,
    message: str,
    progress: int,
    commit: bool = True,
) -> Dict:
    row = GenerationJobEvent(
        id=f"jevt_{uuid.uuid4().hex[:16]}",
        job_id=job_id,
        event=event,
        agent=agent,
        message=message,
        progress=max(0, min(int(progress or 0), 100)),
        created_at=datetime.datetime.now(),
    )
    db.add(row)
    if commit:
        db.commit()
    return event_to_dict(row)


def update_job(
    db: Session,
    job_id: str,
    *,
    status: str = None,
    progress: int = None,
    message: str = None,
    artifact_ids: List[str] = None,
) -> Dict:
    job = db.query(GenerationJob).filter(GenerationJob.job_id == job_id).first()
    if not job:
        return {}
    if status:
        job.status = status
    if progress is not None:
        job.progress = max(0, min(int(progress), 100))
    if message is not None:
        job.message = message
    if artifact_ids is not None:
        job.artifacts_json = _json_dump(artifact_ids)
    job.updated_at = datetime.datetime.now()
    db.commit()
    return to_dict(job)


def to_dict(job: GenerationJob) -> Dict:
    return {
        "job_id": job.job_id,
        "username": job.username,
        "course_id": job.course_id,
        "topic": job.topic,
        "unit_id": job.unit_id,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "artifacts": json.loads(job.artifacts_json or "[]"),
        "created_at": job.created_at.isoformat(timespec="seconds") if job.created_at else "",
        "updated_at": job.updated_at.isoformat(timespec="seconds") if job.updated_at else "",
    }


def event_to_dict(row: GenerationJobEvent) -> Dict:
    return {
        "id": row.id,
        "job_id": row.job_id,
        "event": row.event,
        "agent": row.agent,
        "message": row.message,
        "progress": row.progress,
        "created_at": row.created_at.isoformat(timespec="seconds") if row.created_at else "",
    }


def get_job(db: Session, job_id: str) -> Dict:
    job = db.query(GenerationJob).filter(GenerationJob.job_id == job_id).first()
    return to_dict(job) if job else {}


def list_events(db: Session, job_id: str) -> List[Dict]:
    rows = (
        db.query(GenerationJobEvent)
        .filter(GenerationJobEvent.job_id == job_id)
        .order_by(GenerationJobEvent.created_at.asc())
        .all()
    )
    return [event_to_dict(row) for row in rows]
