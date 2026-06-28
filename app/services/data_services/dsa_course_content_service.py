import json
from pathlib import Path
from typing import Any, Dict, List


COURSE_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "knowledge_base"
    / "data_structures_algorithms"
)


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _read_courseware_text(chapter_id: str, relative_path: str) -> str:
    if not chapter_id or not relative_path:
        return ""
    chapter_dir = (COURSE_DIR / "courseware" / chapter_id).resolve()
    target = (chapter_dir / relative_path).resolve()
    try:
        target.relative_to(chapter_dir)
    except ValueError:
        return ""
    if not target.exists() or not target.is_file():
        return ""
    if target.suffix not in {".md", ".mmd"}:
        return ""
    return target.read_text(encoding="utf-8")


def _normalize_section(section: Dict[str, Any]) -> Dict[str, Any]:
    section_id = section.get("section_id") or section.get("id") or ""
    title = section.get("title") or section.get("name") or section_id
    return {
        **section,
        "id": section_id,
        "section_id": section_id,
        "name": title,
        "title": title,
    }


def _normalize_chapter(chapter: Dict[str, Any], include_sections: bool = True) -> Dict[str, Any]:
    chapter_id = chapter.get("chapter_id") or chapter.get("id") or ""
    title = chapter.get("title") or chapter.get("name") or chapter_id
    data = {
        **chapter,
        "id": chapter_id,
        "chapter_id": chapter_id,
        "name": title,
        "title": title,
    }
    if include_sections:
        data["sections"] = [_normalize_section(item) for item in chapter.get("sections", []) or []]
        data["children"] = data["sections"]
    return data


def _chapter_dir(chapter_id: str) -> Path:
    return COURSE_DIR / "courseware" / chapter_id


def _load_course_tree_raw() -> Dict[str, Any]:
    tree = _read_json(COURSE_DIR / "course_tree.json", {})
    manifest = _read_json(COURSE_DIR / "course_manifest.json", {})
    if not isinstance(tree, dict):
        tree = {}
    tree.setdefault("course_id", manifest.get("course_id", "data_structures_algorithms"))
    tree.setdefault("course_title", manifest.get("course_title") or manifest.get("course_full_name") or "数据结构与算法")
    tree.setdefault("chapters", [])
    return tree


def _load_manifest(chapter_id: str) -> Dict[str, Any]:
    manifest = _read_json(_chapter_dir(chapter_id) / "chapter_manifest.json", {})
    return manifest if isinstance(manifest, dict) else {}


def _load_section_map(chapter_id: str) -> Dict[str, Any]:
    section_map = _read_json(_chapter_dir(chapter_id) / "indexes" / "section_resource_map.json", {})
    return section_map if isinstance(section_map, dict) else {}


def _load_banks(chapter_id: str) -> Dict[str, List[Dict[str, Any]]]:
    bank_dir = _chapter_dir(chapter_id) / "banks"
    return {
        "exercises": _read_jsonl(bank_dir / "exercises.jsonl"),
        "code_tasks": _read_jsonl(bank_dir / "code_tasks.jsonl"),
        "video_items": _read_jsonl(bank_dir / "video_items.jsonl"),
    }


def _load_metadata(chapter_id: str) -> Dict[str, Any]:
    metadata_dir = _chapter_dir(chapter_id) / "metadata"
    return {
        "objectives": _read_json(metadata_dir / "chapter_objectives.json", {}),
        "assessment": _read_json(metadata_dir / "chapter_assessment.json", {}),
        "misconceptions": _read_json(metadata_dir / "chapter_misconceptions.json", {}),
    }


def _match_items(items: List[Dict[str, Any]], section_id: str, unit_ids: List[str]) -> List[Dict[str, Any]]:
    unit_set = set(unit_ids or [])
    matched = []
    for item in items:
        item_section_ids = set(item.get("section_ids") or [])
        item_unit_ids = set(item.get("unit_ids") or [])
        if section_id in item_section_ids or (unit_set and unit_set.intersection(item_unit_ids)):
            matched.append(item)
    return matched


def _find_chapter_in_tree(chapter_id: str) -> Dict[str, Any]:
    tree = _load_course_tree_raw()
    for chapter in tree.get("chapters", []) or []:
        normalized = _normalize_chapter(chapter)
        if normalized.get("chapter_id") == chapter_id:
            return normalized
    return {}


def _find_section_from_manifest(chapter_id: str, section_id: str) -> Dict[str, Any]:
    manifest = _load_manifest(chapter_id)
    for section in manifest.get("sections", []) or []:
        normalized = _normalize_section(section)
        if normalized.get("section_id") == section_id:
            return normalized
    chapter = _find_chapter_in_tree(chapter_id)
    for section in chapter.get("sections", []) or []:
        normalized = _normalize_section(section)
        if normalized.get("section_id") == section_id:
            return normalized
    return {}


def _section_path_from_map(chapter_id: str, section_id: str) -> str:
    section_map = _load_section_map(chapter_id)
    item = section_map.get(section_id) or {}
    for resource in item.get("base_resources", []) or []:
        if isinstance(resource, str):
            path = resource
            if path.startswith("sections/"):
                return path
            continue
        if not isinstance(resource, dict):
            continue
        path = resource.get("path") or resource.get("source_file") or resource.get("resource_key") or ""
        if path.startswith("sections/"):
            return path
    return ""


def get_course_tree() -> Dict[str, Any]:
    tree = _load_course_tree_raw()
    chapters = [_normalize_chapter(chapter) for chapter in tree.get("chapters", []) or []]
    return {
        "course_id": tree.get("course_id", "data_structures_algorithms"),
        "course_title": tree.get("course_title", "数据结构与算法"),
        "stage": tree.get("stage", ""),
        "chapters": chapters,
    }


def get_chapter_detail(chapter_id: str) -> Dict[str, Any]:
    chapter = _find_chapter_in_tree(chapter_id)
    manifest = _load_manifest(chapter_id)
    if not chapter and manifest:
        chapter = _normalize_chapter(manifest)
    if not chapter:
        return {"ok": False, "message": "章节内容不存在", "data": None}

    banks = _load_banks(chapter_id)
    section_map = _load_section_map(chapter_id)
    resources = {}
    for item in manifest.get("chapter_level_resources", []) or []:
        path = item.get("path") or ""
        resources[path] = {**item, "content": _read_courseware_text(chapter_id, path)}

    data = {
        **chapter,
        "manifest": manifest,
        "metadata": _load_metadata(chapter_id),
        "overview": resources.get("resources/chapter_overview.md", {}).get("content", ""),
        "mind_map": resources.get("resources/mind_map.mmd", {}).get("content", ""),
        "reading_video_guide": resources.get("resources/reading_video_guide.md", {}).get("content", ""),
        "project_brief": resources.get("resources/project_brief.md", {}).get("content", ""),
        "rubric": resources.get("resources/rubric.md", {}).get("content", ""),
        "report_template": resources.get("resources/report_template.md", {}).get("content", ""),
        "resource_contents": resources,
        "section_resource_map": section_map,
        "resources": banks,
        "banks": banks,
    }
    return {"ok": True, "message": "ok", "data": data}


def get_section_detail(chapter_id: str, section_id: str) -> Dict[str, Any]:
    chapter = _find_chapter_in_tree(chapter_id)
    if not chapter and not _load_manifest(chapter_id):
        return {"ok": False, "message": "章节内容不存在", "data": None}

    section = _find_section_from_manifest(chapter_id, section_id)
    if not section:
        return {"ok": False, "message": "小节内容不存在", "data": None}

    section_path = _section_path_from_map(chapter_id, section_id) or section.get("path") or ""
    content = _read_courseware_text(chapter_id, section_path)
    if not content:
        return {"ok": False, "message": "小节内容不存在", "data": None}

    unit_ids = section.get("unit_ids") or []
    banks = _load_banks(chapter_id)
    related = {
        "exercises": _match_items(banks["exercises"], section_id, unit_ids),
        "code_tasks": _match_items(banks["code_tasks"], section_id, unit_ids),
        "video_items": _match_items(banks["video_items"], section_id, unit_ids),
    }
    return {
        "ok": True,
        "message": "ok",
        "data": {
            "chapter_id": chapter_id,
            "section_id": section_id,
            "title": section.get("title") or section.get("name") or section_id,
            "path": section_path,
            "unit_ids": unit_ids,
            "content": content,
            "related": related,
        },
    }
