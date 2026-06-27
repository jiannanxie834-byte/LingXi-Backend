import json
import re
from pathlib import Path
from typing import Dict, List

from app.services.data_services import resource_artifact_type_service as artifact_types


COURSE_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "knowledge_base"
    / "deep_learning"
)
COURSEWARE_DIR = COURSE_DIR / "courseware"
CHAPTER_INDEX_PATH = COURSE_DIR / "chapter_resource_index.json"
METADATA_START = "[[LINGXI_RESOURCE_METADATA]]"
METADATA_END = "[[/LINGXI_RESOURCE_METADATA]]"


def _json_load(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _resource_id(chapter_no: int, resource_key: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9]+", "-", resource_key).strip("-").upper()
    return f"KB-DL-CH{chapter_no:02d}-{stem}"[:64]


def _read_resource_file(resource_key: str):
    path = COURSEWARE_DIR / resource_key
    if not path.exists():
        return ""
    if path.suffix == ".json":
        try:
            return json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False, indent=2)
        except Exception:
            return path.read_text(encoding="utf-8")
    return path.read_text(encoding="utf-8")


def metadata_block(metadata: Dict) -> str:
    return "\n".join([
        METADATA_START,
        json.dumps(metadata, ensure_ascii=False, sort_keys=True),
        METADATA_END,
    ])


def extract_metadata(value: str) -> Dict:
    match = re.search(
        re.escape(METADATA_START) + r"\s*(\{.*?\})\s*" + re.escape(METADATA_END),
        value or "",
        re.S,
    )
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except Exception:
        return {}


def strip_metadata(value: str) -> str:
    return re.sub(
        re.escape(METADATA_START) + r".*?" + re.escape(METADATA_END),
        "",
        value or "",
        flags=re.S,
    ).strip()


def load_chapter_index() -> List[Dict]:
    items = _json_load(CHAPTER_INDEX_PATH, [])
    return items if isinstance(items, list) else []


def _resource_summary(chapter: Dict, item: Dict) -> str:
    if item.get("type") == artifact_types.COURSE_NOTE:
        return f"{chapter.get('chapter_title')} 的教材式主讲义，覆盖章节定位、核心机制、例子、自测题和参考来源。"
    if item.get("type") == artifact_types.MIND_MAP:
        return f"{chapter.get('chapter_title')} 的结构化 Mermaid 思维导图，帮助快速把握章节关系。"
    if item.get("type") == artifact_types.EXERCISE_SET:
        return f"{chapter.get('chapter_title')} 的章节题库，包含答案、解析和常见错误。"
    if item.get("type") in {artifact_types.READING_PACK, artifact_types.PERSONALIZED_VIDEO_GUIDE, artifact_types.VIDEO_RECOMMENDATION}:
        return f"{chapter.get('chapter_title')} 的阅读与视频学习指南，提供 link_only 外部资料学习任务。"
    if item.get("type") == artifact_types.CODE_LAB:
        return f"{chapter.get('chapter_title')} 的可运行 PyTorch 实验，包含完整代码、运行方式和实验报告要求。"
    if item.get("type") == artifact_types.INTERACTIVE_ANIMATION:
        return f"{chapter.get('chapter_title')} 的交互动画规格，用于解释关键机制。"
    return f"{chapter.get('chapter_title')} 的章节配套资源。"


def iter_courseware_resource_documents() -> List[Dict]:
    documents = []
    for chapter in load_chapter_index():
        chapter_no = int(chapter.get("chapter_no") or 0)
        resources = [
            *((chapter.get("primary_resources") or [])),
            *((chapter.get("optional_resources") or [])),
        ]
        for item in resources:
            resource_key = item.get("resource_key") or ""
            resource_type = artifact_types.normalize_artifact_type(item.get("type") or "")
            content = _read_resource_file(resource_key)
            if not resource_key or not resource_type or not content:
                continue
            source_file = f"courseware/{resource_key}"
            metadata = {
                "chapter_id": chapter.get("chapter_id", ""),
                "chapter_no": chapter_no,
                "chapter_title": chapter.get("chapter_title", ""),
                "is_chapter_primary": bool(item.get("is_required")),
                "display_in_chapter_hub": True,
                "is_preset_resource": True,
                "quality_level": "curated",
                "source_file": source_file,
                "resource_key": resource_key,
                "suggested_minutes": 45 if resource_type == artifact_types.COURSE_NOTE else 25,
                "student_visible": True,
            }
            documents.append({
                "id": _resource_id(chapter_no, resource_key),
                "title": item.get("title") or f"{chapter.get('chapter_title')} {resource_type}",
                "type": resource_type,
                "summary": _resource_summary(chapter, item),
                "content": content,
                "source": f"《深度学习》课程底座 / {chapter.get('chapter_title')} / {source_file}",
                "metadata": metadata,
                "unit_id": chapter.get("chapter_id", ""),
            })
    return documents


def _resources_by_source_file(resources: List[Dict]) -> Dict[str, Dict]:
    mapping = {}
    for item in resources or []:
        metadata = item.get("metadata") or extract_metadata(item.get("agent_notes", ""))
        source_file = metadata.get("source_file")
        if source_file:
            mapping[source_file] = item
    return mapping


def build_chapter_hubs(resources: List[Dict]) -> List[Dict]:
    by_source_file = _resources_by_source_file(resources)
    hubs = []
    for chapter in load_chapter_index():
        hub = {**chapter, "primary_resources": [], "optional_resources": []}
        for section_key in ["primary_resources", "optional_resources"]:
            for item in chapter.get(section_key) or []:
                source_file = f"courseware/{item.get('resource_key')}"
                resource = by_source_file.get(source_file)
                payload = {
                    **item,
                    "source_file": source_file,
                    "resource": resource,
                    "available": bool(resource),
                }
                hub[section_key].append(payload)
        hubs.append(hub)
    return hubs
