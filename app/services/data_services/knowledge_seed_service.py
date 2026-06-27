import datetime
import json
from pathlib import Path
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.schemas import CourseKnowledge, Resource, VideoResource
from app.services.data_services import (
    chapter_resource_service,
    content_guard_service,
    deep_learning_course_map_service,
    resource_artifact_service,
    resource_artifact_type_service as artifact_types,
    resource_quality_gate,
)


COURSE_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "knowledge_base"
    / "deep_learning_v2"
)
COURSE_MANIFEST_PATH = COURSE_DIR / "course_manifest.json"
LEGACY_MANIFEST_PATH = COURSE_DIR / "manifest.json"
VIDEO_CATALOG_PATH = COURSE_DIR / "video_catalog.json"
KNOWLEDGE_UNITS_PATH = COURSE_DIR / "knowledge_units.jsonl"


def _manifest_path() -> Path:
    return COURSE_MANIFEST_PATH if COURSE_MANIFEST_PATH.exists() else LEGACY_MANIFEST_PATH


def _load_manifest() -> Dict:
    with _manifest_path().open("r", encoding="utf-8") as file:
        return json.load(file)


def _load_knowledge_units() -> List[Dict]:
    if not KNOWLEDGE_UNITS_PATH.exists():
        return []

    units = []
    with KNOWLEDGE_UNITS_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("unit_id") and item.get("title"):
                units.append(item)
    return units


def _chapter_title_map() -> Dict[str, str]:
    return {
        item.get("chapter_id", ""): item.get("title", "")
        for item in deep_learning_course_map_service.DEEP_LEARNING_CHAPTERS
    }


def _read_markdown(filename: str) -> str:
    path = COURSE_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _json_dumps(value: List[str]) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def _knowledge_points_from_units(units: List[Dict]) -> List[Dict]:
    chapters = _chapter_title_map()
    points = []
    for unit in units:
        title = unit.get("title", "").strip()
        if not title:
            continue
        aliases = unit.get("aliases") or []
        core_concepts = unit.get("core_concepts") or []
        outcomes = unit.get("learning_outcomes") or []
        prerequisites = unit.get("prerequisites") or []
        related_units = unit.get("related_units") or []
        compare_units = unit.get("compare_units") or []
        misconceptions = unit.get("common_misconceptions") or []
        formulas = unit.get("formulas") or []
        resource_focus = unit.get("resource_focus") or []
        chapter_title = chapters.get(unit.get("chapter_id", ""), unit.get("chapter_id", ""))

        points.append({
            "topic": title,
            "keywords": list(dict.fromkeys([
                unit.get("unit_id", ""),
                *aliases,
                *core_concepts,
            ])),
            "chapter": chapter_title,
            "core": "\n".join([
                f"知识单元 ID：{unit.get('unit_id', '')}",
                f"核心概念：{'、'.join(core_concepts) or '待补充'}",
                f"学习产出：{'；'.join(outcomes) or '待补充'}",
                f"前置知识：{'、'.join(prerequisites) or '无'}",
                f"关联单元：{'、'.join(related_units) or '无'}",
                f"对比拓展：{'、'.join(compare_units) or '无'}",
                f"公式/机制：{'；'.join(formulas) or '按章节材料理解'}",
            ]),
            "pitfalls": misconceptions,
            "practice": "；".join(resource_focus or outcomes or [f"围绕「{title}」完成概念解释、练习和复盘"]),
            "practice_kind": "knowledge_unit",
            "practice_output": unit.get("code_lab") or f"完成「{title}」学习检查清单与 3 道自测题。",
            "code_lang": "python" if "PyTorch" in " ".join([title, *aliases, unit.get("code_lab", "")]) else None,
            "code": unit.get("code_lab") or None,
        })
    return points


def _unit_resource_id(unit_id: str) -> str:
    safe_unit_id = "".join(ch if ch.isalnum() else "_" for ch in str(unit_id or "").upper())
    return f"KB-DL-UNIT-{safe_unit_id}"[:64]


def _build_unit_resource_content(unit: Dict) -> str:
    chapters = _chapter_title_map()
    title = unit.get("title", "深度学习知识点")
    chapter_title = chapters.get(unit.get("chapter_id", ""), unit.get("chapter_id", ""))
    core_concepts = unit.get("core_concepts") or []
    outcomes = unit.get("learning_outcomes") or []
    prerequisites = unit.get("prerequisites") or []
    related_units = unit.get("related_units") or []
    compare_units = unit.get("compare_units") or []
    misconceptions = unit.get("common_misconceptions") or []
    formulas = unit.get("formulas") or []
    focus = unit.get("resource_focus") or []

    lines = [
        f"# {title} · 初始知识点资源卡",
        "",
        "## 课程位置",
        f"本资源属于《深度学习》课程的「{chapter_title or '未标注章节'}」部分，知识单元 ID 为 `{unit.get('unit_id', '')}`。",
        "",
        "## 前置知识",
        "、".join(prerequisites) if prerequisites else "该知识点暂无强制前置知识，可从课程导学或本章导论开始。",
        "",
        "## 核心概念",
        *([f"- {item}" for item in core_concepts] if core_concepts else ["- 待教师在课程资料中继续扩展核心概念。"]),
        "",
        "## 学习目标",
        *([f"- {item}" for item in outcomes] if outcomes else [f"- 能解释「{title}」的基本含义、适用场景和常见误区。"]),
        "",
        "## 公式、流程或机制",
        *([f"- {item}" for item in formulas] if formulas else ["- 本知识点以概念理解、流程说明或实验观察为主。"]),
        "",
        "## 常见误区",
        *([f"- {item}" for item in misconceptions] if misconceptions else ["- 只记术语而没有结合输入输出、适用条件或实验边界。"]),
        "",
        "## 关联学习",
        f"- 前置/关联单元：{'、'.join(related_units) or '暂无'}",
        f"- 对比拓展单元：{'、'.join(compare_units) or '暂无'}",
        f"- 推荐资源形态：{'、'.join(focus) or '课程讲解、练习题和学习复盘'}",
        "",
        "## 学习检查",
        f"1. 能用自己的话解释「{title}」是什么。",
        "2. 能说明它在深度学习模型训练、结构设计或项目实践中的作用。",
        "3. 能指出至少一个常见误区，并给出纠正方式。",
        "",
        "## 参考依据",
        f"- evidence_id: {unit.get('unit_id', '')}",
        f"- 知识来源：data/knowledge_base/deep_learning_v2/knowledge_units.jsonl；{chapter_title}",
    ]
    return "\n".join(lines)


def _unit_resource_documents(units: List[Dict]) -> List[Dict]:
    docs = []
    for unit in units:
        unit_id = unit.get("unit_id", "")
        title = unit.get("title", "").strip()
        if not unit_id or not title:
            continue
        docs.append({
            "id": _unit_resource_id(unit_id),
            "title": f"{title} · 初始知识点资源卡",
            "type": artifact_types.COURSE_NOTE,
            "summary": f"由《深度学习》细粒度课程图谱生成的「{title}」初始学习入口。",
            "content": _build_unit_resource_content(unit),
            "unit_id": unit_id,
        })
    return docs


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
    metadata = resource.get("metadata") or {}
    chapter_id = metadata.get("chapter_id", "")
    review_unit_id = resource.get("unit_id") or chapter_id
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
    notes = content_guard_service.attach_review_note(base_note, review)
    teaching_review = resource_quality_gate.validate_teaching_quality(
        {
            "title": resource.get("title", ""),
            "type": resource.get("type", ""),
            "summary": resource.get("summary", ""),
            "content": content,
            "source": source,
            "chapter_id": chapter_id,
            "unit_id": review_unit_id,
            "evidence_chunks": [
                review_unit_id,
                metadata.get("source_file", ""),
            ],
        },
        {
            "resource_type": resource.get("type", ""),
            "chapter_id": chapter_id,
            "unit_id": review_unit_id,
            "topic": resource.get("title", ""),
            "evidence_chunks": [
                review_unit_id,
                metadata.get("source_file", ""),
            ],
        },
    )
    notes = resource_quality_gate.attach_teaching_quality_note(notes, teaching_review)
    if resource.get("metadata"):
        notes = "\n\n".join([
            notes,
            chapter_resource_service.metadata_block(resource.get("metadata") or {}),
        ])
    return notes


def _upsert_resource_documents(db: Session, manifest: Dict, resource_documents: List[Dict] = None) -> int:
    changed = 0
    uploader = manifest.get("resource_uploader", "课程知识库种子")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for doc in resource_documents if resource_documents is not None else manifest.get("resource_documents", []):
        resource_id = (doc.get("id") or "").strip()
        title = (doc.get("title") or "").strip()
        resource_type = (doc.get("type") or "").strip()
        if not resource_id or not title or not resource_type:
            continue

        content = doc.get("content") or _read_markdown(doc.get("file", ""))
        source = doc.get("source") or f"{manifest.get('source_prefix', '课程知识库')} / {title}"
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
        unit_id = doc.get("unit_id") or course_match.get("unit_id", "")
        metadata = doc.get("metadata") or {}
        resource_artifact_service.upsert_from_resource(
            db,
            resource=row,
            plan_item={
                "course_id": manifest.get("course_id", "deep_learning_v2"),
                "unit_id": unit_id,
                "content_format": artifact_types.get_format(row.type),
                "evidence_refs": [unit_id] if unit_id else [row.id],
                "personalization_reason": "系统内置《深度学习》初始知识库资源，可作为学生端学习入口和智能体生成依据。",
                "agent_name": "KnowledgeSeedAgent",
                "chapter_id": metadata.get("chapter_id", ""),
                "chapter": metadata.get("chapter_title", ""),
                "quality_score": 96 if metadata.get("quality_level") == "curated" else 88,
            },
            semantic_result={
                "course_id": manifest.get("course_id", "deep_learning_v2"),
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

        row.course_id = item.get("course_id") or "deep_learning_v2"
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
        knowledge_units = _load_knowledge_units()
        knowledge_points = [
            *(manifest.get("knowledge_points", []) or []),
            *_knowledge_points_from_units(knowledge_units),
        ]
        resource_documents = [
            *chapter_resource_service.iter_courseware_resource_documents(),
        ]
        knowledge_count = _upsert_knowledge_points(db, knowledge_points)
        resource_count = _upsert_resource_documents(db, manifest, resource_documents)
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
