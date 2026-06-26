import datetime
import json
import uuid
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.schemas import Resource, ResourceArtifact
from app.services.data_services import content_guard_service, resource_artifact_type_service as artifact_types


def _json_dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_load(value, default):
    try:
        return json.loads(value) if value else default
    except Exception:
        return default


def _status_from_resource(status: str) -> str:
    return {
        "已通过": "published",
        "待审核": "needs_review",
        "未通过": "needs_review",
    }.get(status or "", "needs_review")


def _format_from_type(resource_type: str) -> str:
    return artifact_types.get_format(artifact_types.normalize_artifact_type(resource_type)) or "markdown"


def upsert_from_resource(
    db: Session,
    *,
    resource: Resource,
    plan_item: Dict = None,
    semantic_result: Dict = None,
    agent_trace_id: str = "",
) -> Dict:
    plan_item = plan_item or {}
    semantic_result = semantic_result or {}
    safety_review = content_guard_service.extract_review(resource.agent_notes or "")
    unit_id = plan_item.get("unit_id") or semantic_result.get("unit_id") or ""
    evidence_refs = plan_item.get("evidence_refs") or []
    if not evidence_refs and unit_id:
        evidence_refs = [unit_id]

    artifact = (
        db.query(ResourceArtifact)
        .filter(ResourceArtifact.resource_id == resource.id)
        .first()
    )
    now = datetime.datetime.now()
    if not artifact:
        artifact = ResourceArtifact(
            artifact_id=f"artifact_{uuid.uuid4().hex[:16]}",
            resource_id=resource.id,
            created_at=now,
        )
        db.add(artifact)

    artifact.course_id = plan_item.get("course_id") or semantic_result.get("course_id") or "deep_learning"
    artifact.unit_ids_json = _json_dump([unit_id] if unit_id else [])
    artifact.student_id = resource.applicant_username or ""
    artifact.type = artifact_types.normalize_artifact_type(resource.type)
    artifact.title = resource.title
    artifact.summary = resource.summary or ""
    artifact.content_format = plan_item.get("content_format") or _format_from_type(resource.type)
    artifact.content = resource.content or ""
    artifact.assets_json = _json_dump(plan_item.get("assets") or [])
    artifact.personalization_reason = plan_item.get("personalization_reason") or "根据本轮深度学习主题、学生画像和学习目标生成。"
    artifact.evidence_refs_json = _json_dump(evidence_refs)
    artifact.quality_score = float(safety_review.get("score") or plan_item.get("quality_score") or 0)
    artifact.risk_level = safety_review.get("risk_level") or "待复核"
    artifact.status = _status_from_resource(resource.status)
    artifact.agent_name = plan_item.get("agent_name") or "ResourcePlanningAgent"
    artifact.agent_trace_id = agent_trace_id or plan_item.get("agent_trace_id") or ""
    artifact.source = resource.source or ""
    artifact.updated_at = now
    db.flush()
    return to_dict(artifact)


def sync_resource_status(db: Session, resource_id: str, status: str) -> None:
    artifact = (
        db.query(ResourceArtifact)
        .filter(ResourceArtifact.resource_id == resource_id)
        .first()
    )
    if artifact:
        artifact.status = _status_from_resource(status)
        artifact.updated_at = datetime.datetime.now()
        db.flush()


def to_dict(row: ResourceArtifact) -> Dict:
    return {
        "artifact_id": row.artifact_id,
        "resource_id": row.resource_id,
        "course_id": row.course_id,
        "unit_ids": _json_load(row.unit_ids_json, []),
        "student_id": row.student_id,
        "type": row.type,
        "title": row.title,
        "summary": row.summary or "",
        "content_format": row.content_format,
        "content": row.content or "",
        "assets": _json_load(row.assets_json, []),
        "personalization_reason": row.personalization_reason or "",
        "evidence_refs": _json_load(row.evidence_refs_json, []),
        "quality_score": row.quality_score or 0,
        "risk_level": row.risk_level or "待复核",
        "status": row.status,
        "agent_name": row.agent_name,
        "agent_trace_id": row.agent_trace_id,
        "source": row.source or "",
        "created_at": row.created_at.isoformat(timespec="seconds") if row.created_at else "",
        "updated_at": row.updated_at.isoformat(timespec="seconds") if row.updated_at else "",
    }


def list_artifacts(db: Session, username: str = "", status: str = "", limit: int = 50) -> List[Dict]:
    query = db.query(ResourceArtifact)
    if username:
        query = query.filter(ResourceArtifact.student_id.in_([username, ""]))
    if status:
        query = query.filter(ResourceArtifact.status == status)
    rows = (
        query.order_by(ResourceArtifact.updated_at.desc())
        .limit(max(1, min(int(limit or 50), 200)))
        .all()
    )
    return [to_dict(row) for row in rows]


def get_artifact(db: Session, artifact_id: str) -> Dict:
    row = (
        db.query(ResourceArtifact)
        .filter(ResourceArtifact.artifact_id == artifact_id)
        .first()
    )
    return to_dict(row) if row else {}
