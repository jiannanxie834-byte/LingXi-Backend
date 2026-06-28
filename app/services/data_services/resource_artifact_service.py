import datetime
import json
import uuid
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.schemas import Resource, ResourceArtifact
from app.services.data_services import (
    content_guard_service,
    resource_artifact_type_service as artifact_types,
    resource_quality_gate,
)


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
        "framework_placeholder": "framework_placeholder",
        "待审核": "needs_review",
        "未通过": "needs_review",
        "archived_shallow": "archived",
        "merged_into_chapter_pack": "archived",
        "legacy_demo_only": "archived",
    }.get(status or "", "needs_review")


def _format_from_type(resource_type: str) -> str:
    return artifact_types.get_format(artifact_types.normalize_artifact_type(resource_type)) or "markdown"


def _review_bundle_from_notes(notes: str, evidence_refs: List[str]) -> Dict:
    safety_review = content_guard_service.extract_review(notes or "")
    teaching_quality_review = resource_quality_gate.extract_teaching_quality_review(notes or "")
    evidence_refs = [item for item in (evidence_refs or []) if item]
    return {
        "kind": "quality_review",
        "safety_review": {
            "score": safety_review.get("score", 0),
            "risk_level": safety_review.get("risk_level", "待复核"),
            "issues": safety_review.get("checks", []),
            "suggestions": safety_review.get("suggestions", []),
        },
        "teaching_quality_review": {
            "score": teaching_quality_review.get("teaching_quality_score", teaching_quality_review.get("score", 0)),
            "teaching_quality_score": teaching_quality_review.get("teaching_quality_score", teaching_quality_review.get("score", 0)),
            "status": teaching_quality_review.get("status", "unreviewed"),
            "passed": teaching_quality_review.get("passed", False),
            "fatal": teaching_quality_review.get("fatal", False),
            "issues": teaching_quality_review.get("issues", []),
            "repair_suggestions": teaching_quality_review.get("repair_suggestions", []),
        },
        "evidence_review": {
            "evidence_ok": bool(evidence_refs),
            "evidence_refs": evidence_refs,
            "evidence_count": len(evidence_refs),
        },
    }


def _extract_review_bundle(assets: List[Dict]) -> Dict:
    for item in assets or []:
        if isinstance(item, dict) and item.get("kind") == "quality_review":
            return item
    return {
        "safety_review": {},
        "teaching_quality_review": {},
        "evidence_review": {"evidence_ok": False, "evidence_refs": [], "evidence_count": 0},
    }


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
    unit_id = plan_item.get("unit_id") or semantic_result.get("unit_id") or ""
    evidence_refs = plan_item.get("evidence_refs") or []
    if not evidence_refs and unit_id:
        evidence_refs = [unit_id]
    review_bundle = _review_bundle_from_notes(resource.agent_notes or "", evidence_refs)
    safety_review = review_bundle.get("safety_review") or {}
    teaching_review = review_bundle.get("teaching_quality_review") or {}

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

    artifact.course_id = plan_item.get("course_id") or semantic_result.get("course_id") or "data_structures_algorithms"
    artifact.unit_ids_json = _json_dump([unit_id] if unit_id else [])
    artifact.student_id = resource.applicant_username or ""
    artifact.type = artifact_types.normalize_artifact_type(resource.type)
    artifact.title = resource.title
    artifact.summary = resource.summary or ""
    artifact.content_format = plan_item.get("content_format") or _format_from_type(resource.type)
    artifact.content = resource.content or ""
    assets = [
        item for item in (plan_item.get("assets") or [])
        if not (isinstance(item, dict) and item.get("kind") == "quality_review")
    ]
    assets.append(review_bundle)
    artifact.assets_json = _json_dump(assets)
    artifact.personalization_reason = plan_item.get("personalization_reason") or "根据本轮算法学习主题、学生画像和学习目标生成。"
    artifact.evidence_refs_json = _json_dump(evidence_refs)
    artifact.quality_score = float(
        teaching_review.get("teaching_quality_score")
        or teaching_review.get("score")
        or plan_item.get("quality_score")
        or 0
    )
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
    assets = _json_load(row.assets_json, [])
    review_bundle = _extract_review_bundle(assets)
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
        "assets": [item for item in assets if not (isinstance(item, dict) and item.get("kind") == "quality_review")],
        "personalization_reason": row.personalization_reason or "",
        "evidence_refs": _json_load(row.evidence_refs_json, []),
        "quality_score": row.quality_score or 0,
        "risk_level": row.risk_level or "待复核",
        "safety_review": review_bundle.get("safety_review", {}),
        "teaching_quality_review": review_bundle.get("teaching_quality_review", {}),
        "evidence_review": review_bundle.get("evidence_review", {}),
        "status": row.status,
        "agent_name": row.agent_name,
        "agent_trace_id": row.agent_trace_id,
        "source": row.source or "",
        "created_at": row.created_at.isoformat(timespec="seconds") if row.created_at else "",
        "updated_at": row.updated_at.isoformat(timespec="seconds") if row.updated_at else "",
    }


def list_artifacts(db: Session, username: str = "", status: str = "", limit: int = 50) -> List[Dict]:
    query = db.query(ResourceArtifact)
    if status == "published":
        query = (
            query
            .join(Resource, ResourceArtifact.resource_id == Resource.id)
            .filter(Resource.status == "已通过")
        )
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
