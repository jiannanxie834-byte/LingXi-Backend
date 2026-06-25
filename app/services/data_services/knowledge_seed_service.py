import datetime
import json
from pathlib import Path
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.schemas import CourseKnowledge, Resource
from app.services.data_services import content_guard_service


COURSE_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "knowledge_base"
    / "artificial_intelligence_intro"
)
MANIFEST_PATH = COURSE_DIR / "manifest.json"


def _load_manifest() -> Dict:
    with MANIFEST_PATH.open("r", encoding="utf-8") as file:
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
        "系统内置初始课程知识库资源，来源于参赛团队自构建的人工智能课程文档集；"
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
        changed += 1

    return changed


def seed_initial_course_knowledge_base(db: Session) -> Dict:
    if not MANIFEST_PATH.exists():
        return {
            "success": False,
            "message": f"知识库 manifest 不存在: {MANIFEST_PATH}",
            "knowledge_points": 0,
            "resources": 0,
        }

    try:
        manifest = _load_manifest()
        knowledge_count = _upsert_knowledge_points(db, manifest.get("knowledge_points", []))
        resource_count = _upsert_resource_documents(db, manifest)
        db.commit()
        return {
            "success": True,
            "course": manifest.get("course_name", "人工智能"),
            "knowledge_points": knowledge_count,
            "resources": resource_count,
        }
    except Exception as exc:
        db.rollback()
        return {
            "success": False,
            "message": str(exc),
            "knowledge_points": 0,
            "resources": 0,
        }
