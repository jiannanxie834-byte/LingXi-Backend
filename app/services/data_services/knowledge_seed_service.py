import datetime
import json
from pathlib import Path
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.schemas import CourseKnowledge, Resource, VideoResource
from app.services.data_services import (
    content_guard_service,
    deep_learning_course_map_service,
    resource_artifact_service,
    resource_artifact_type_service as artifact_types,
)


COURSE_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "knowledge_base"
    / "deep_learning"
)
COURSE_MANIFEST_PATH = COURSE_DIR / "course_manifest.json"
LEGACY_MANIFEST_PATH = COURSE_DIR / "manifest.json"
VIDEO_CATALOG_PATH = COURSE_DIR / "video_catalog.json"


def _manifest_path() -> Path:
    return COURSE_MANIFEST_PATH if COURSE_MANIFEST_PATH.exists() else LEGACY_MANIFEST_PATH


def _load_manifest() -> Dict:
    with _manifest_path().open("r", encoding="utf-8") as file:
        return json.load(file)


def _read_markdown(filename: str) -> str:
    path = COURSE_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _json_dumps(value: List[str]) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def _upsert_knowledge_points(db: Session, points: List[Dict]) -> int:
    changed = 0

    for point in points:
        topic = (point.get("topic") or "").strip()
        if not topic:
            continue

        row = db.query(CourseKnowledge).filter(CourseKnowledge.topic == topic).first()
        if not row:
            row = CourseKnowledge(topic=topic)
            db.add(row)

        row.keywords = _json_dumps(point.get("keywords", []))
        row.chapter = point.get("chapter", "")
        row.core = point.get("core", "")
        row.pitfalls = _json_dumps(point.get("pitfalls", []))
        row.practice = point.get("practice", "")
        row.practice_kind = point.get("practice_kind", "analysis")
        row.practice_output = point.get("practice_output", "")
        row.code_lang = point.get("code_lang")
        row.code = point.get("code")
        changed += 1

    return changed


def _build_resource_notes(resource: Dict, content: str, manifest: Dict) -> str:
    source = f"{manifest.get('source_prefix', '课程知识库')} / {resource.get('title', '')}"
    review = content_guard_service.review_resource_content(
        title=resource.get("title", ""),
        resource_type=resource.get("type", ""),
        summary=resource.get("summary", ""),
        content=content,
        source=source,
        reviewer="课程知识库预审 Agent",
    )
    base_note = (
        "系统内置初始课程知识库资源，来源于参赛团队自构建的《深度学习》课程文档集；"
        "已通过预审，可直接作为学生端初始资源和智能体生成依据。"
    )
    return content_guard_service.attach_review_note(base_note, review)


def _upsert_resource_documents(db: Session, manifest: Dict) -> int:
    changed = 0
    uploader = manifest.get("resource_uploader", "课程知识库种子")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for doc in manifest.get("resource_documents", []):
        resource_id = (doc.get("id") or "").strip()
        title = (doc.get("title") or "").strip()
        resource_type = (doc.get("type") or "").strip()
        if not resource_id or not title or not resource_type:
            continue

        content = _read_markdown(doc.get("file", ""))
        source = f"{manifest.get('source_prefix', '课程知识库')} / {title}"
        row = (
            db.query(Resource)
            .filter((Resource.id == resource_id) | ((Resource.title == title) & (Resource.type == resource_type)))
            .first()
        )

        if not row:
            row = Resource(id=resource_id)
            db.add(row)

        row.title = title
        row.type = resource_type
        row.status = "已通过"
        row.uploader = uploader
        row.time = now
        row.summary = doc.get("summary", "")
        row.content = content
        row.source = source
        row.agent_notes = _build_resource_notes(doc, content, manifest)
        db.flush()
        course_match = deep_learning_course_map_service.match_deep_learning_topic(title, content[:500])
        unit_id = course_match.get("unit_id", "")
        resource_artifact_service.upsert_from_resource(
            db,
            resource=row,
            plan_item={
                "course_id": manifest.get("course_id", "deep_learning"),
                "unit_id": unit_id,
                "content_format": artifact_types.get_format(row.type),
                "evidence_refs": [unit_id] if unit_id else [row.id],
                "personalization_reason": "系统内置《深度学习》初始知识库资源，可作为学生端学习入口和智能体生成依据。",
                "agent_name": "KnowledgeSeedAgent",
            },
            semantic_result={
                "course_id": manifest.get("course_id", "deep_learning"),
                "unit_id": unit_id,
            },
        )
        changed += 1

    return changed


def _load_video_catalog() -> List[Dict]:
    if not VIDEO_CATALOG_PATH.exists():
        return []
    with VIDEO_CATALOG_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data if isinstance(data, list) else []


def _upsert_video_catalog(db: Session) -> int:
    changed = 0
    now = datetime.datetime.now()

    for item in _load_video_catalog():
        video_id = (item.get("video_id") or "").strip()
        title = (item.get("title") or "").strip()
        if not video_id or not title:
            continue

        row = db.query(VideoResource).filter(VideoResource.video_id == video_id).first()
        if not row:
            row = VideoResource(video_id=video_id, created_at=now)
            db.add(row)

        row.course_id = item.get("course_id") or "deep_learning"
        row.unit_ids_json = json.dumps(item.get("unit_ids") or [], ensure_ascii=False)
        row.title = title
        row.platform = item.get("platform") or ""
        row.source = item.get("source") or ""
        row.source_url = item.get("source_url") or ""
        row.tags_json = json.dumps(item.get("tags") or [], ensure_ascii=False)
        row.difficulty = item.get("difficulty") or "beginner"
        row.duration = item.get("duration") or ""
        row.recommended_segments_json = json.dumps(item.get("recommended_segments") or [], ensure_ascii=False)
        row.copyright_policy = item.get("copyright_policy") or "link_only"
        changed += 1

    return changed


def seed_initial_course_knowledge_base(db: Session) -> Dict:
    if not _manifest_path().exists():
        return {
            "success": False,
            "message": f"知识库 manifest 不存在: {COURSE_MANIFEST_PATH}",
            "knowledge_points": 0,
            "resources": 0,
        }

    try:
        manifest = _load_manifest()
        knowledge_count = _upsert_knowledge_points(db, manifest.get("knowledge_points", []))
        resource_count = _upsert_resource_documents(db, manifest)
        video_count = _upsert_video_catalog(db)
        db.commit()
        return {
            "success": True,
            "course": manifest.get("course_name", "深度学习"),
            "knowledge_points": knowledge_count,
            "resources": resource_count,
            "video_resources": video_count,
        }
    except Exception as exc:
        db.rollback()
        return {
            "success": False,
            "message": str(exc),
            "knowledge_points": 0,
            "resources": 0,
        }
