import json
from pathlib import Path
from typing import Dict, List


COURSE_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "knowledge_base"
    / "data_structures_algorithms"
)
COURSE_TREE_PATH = COURSE_DIR / "course_tree.json"
COURSE_MANIFEST_PATH = COURSE_DIR / "course_manifest.json"


def _json_load(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _jsonl_load(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
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


def load_course_manifest() -> Dict:
    return _json_load(COURSE_MANIFEST_PATH, {})


def load_course_tree() -> Dict:
    tree = _json_load(COURSE_TREE_PATH, {})
    manifest = load_course_manifest()
    if not tree:
        return {
            "course_id": manifest.get("course_id", "data_structures_algorithms"),
            "course_title": manifest.get("course_full_name", "数据结构与算法：可视化理解与代码实践"),
            "stage": manifest.get("stage", "framework_placeholder"),
            "chapters": [],
        }
    return tree


def load_chapter_manifest(chapter_id: str) -> Dict:
    path = COURSE_DIR / "courseware" / chapter_id / "chapter_manifest.json"
    return _json_load(path, {})


def load_section_resource_map(chapter_id: str) -> Dict:
    path = COURSE_DIR / "courseware" / chapter_id / "indexes" / "section_resource_map.json"
    data = _json_load(path, {})
    return data if isinstance(data, dict) else {}


def load_chapter_metadata(chapter_id: str) -> Dict:
    base = COURSE_DIR / "courseware" / chapter_id / "metadata"
    return {
        "objectives": _json_load(base / "chapter_objectives.json", {}),
        "misconceptions": _json_load(base / "chapter_misconceptions.json", {}),
        "assessment": _json_load(base / "chapter_assessment.json", {}),
    }


def _safe_courseware_text(chapter_id: str, relative_path: str) -> str:
    if not chapter_id or not relative_path:
        return ""
    chapter_dir = (COURSE_DIR / "courseware" / chapter_id).resolve()
    path = (chapter_dir / relative_path).resolve()
    try:
        path.relative_to(chapter_dir)
    except ValueError:
        return ""
    if not path.exists() or not path.is_file():
        return ""
    if path.suffix not in {".md", ".mmd", ".json", ".jsonl"}:
        return ""
    return path.read_text(encoding="utf-8")


def _load_chapter_sections(chapter: Dict) -> List[Dict]:
    chapter_id = chapter.get("chapter_id", "")
    sections = []
    for section in chapter.get("sections", []) or []:
        sections.append({
            **section,
            "content": _safe_courseware_text(chapter_id, section.get("path", "")),
        })
    return sections


def _load_chapter_resource_contents(chapter_id: str, manifest: Dict) -> Dict:
    resources = {}
    for item in manifest.get("chapter_level_resources", []) or []:
        path = item.get("path", "")
        if not path:
            continue
        resources[path] = {
            **item,
            "content": _safe_courseware_text(chapter_id, path),
        }
    return resources


def _load_chapter_banks(chapter_id: str) -> Dict:
    base = COURSE_DIR / "courseware" / chapter_id / "banks"
    return {
        "exercises": _jsonl_load(base / "exercises.jsonl"),
        "code_tasks": _jsonl_load(base / "code_tasks.jsonl"),
        "video_items": _jsonl_load(base / "video_items.jsonl"),
    }


def load_framework_payload() -> Dict:
    tree = load_course_tree()
    chapters = []
    for chapter in tree.get("chapters", []) or []:
        chapter_id = chapter.get("chapter_id", "")
        if not chapter_id:
            continue
        manifest = load_chapter_manifest(chapter_id)
        chapters.append({
            **chapter,
            "sections": _load_chapter_sections(chapter),
            "manifest": manifest,
            "section_resource_map": load_section_resource_map(chapter_id),
            "metadata": load_chapter_metadata(chapter_id),
            "resource_contents": _load_chapter_resource_contents(chapter_id, manifest),
            "banks": _load_chapter_banks(chapter_id),
        })
    return {
        **tree,
        "manifest": load_course_manifest(),
        "chapters": chapters,
    }


def validate_framework_structure() -> Dict:
    tree = load_course_tree()
    chapters = tree.get("chapters", []) or []
    issues = []
    unit_count = len(_jsonl_load(COURSE_DIR / "knowledge_units.jsonl"))

    required_root_files = [
        "course_manifest.json",
        "course_tree.json",
        "chapter_resource_index.json",
        "knowledge_units.jsonl",
        "misconceptions.jsonl",
        "learning_objectives.jsonl",
        "prerequisite_graph.json",
        "source_references.json",
        "video_catalog.json",
    ]
    for filename in required_root_files:
        if not (COURSE_DIR / filename).exists():
            issues.append(f"缺少根文件：{filename}")
    if (COURSE_DIR / "animations").exists():
        issues.append("DSA 主课程不应包含全局 animations/ 目录")
    for filename in ["visual_animation_blueprint.json", "animation_blueprint.json"]:
        if (COURSE_DIR / "blueprints" / filename).exists():
            issues.append(f"DSA 主课程不应包含动画蓝图：{filename}")

    for chapter in chapters:
        chapter_id = chapter.get("chapter_id", "")
        chapter_dir = COURSE_DIR / "courseware" / chapter_id
        for subdir in ["sections", "resources", "banks", "indexes", "metadata"]:
            if not (chapter_dir / subdir).is_dir():
                issues.append(f"{chapter_id} 缺少目录：{subdir}")
        if not (chapter_dir / "chapter_manifest.json").exists():
            issues.append(f"{chapter_id} 缺少 chapter_manifest.json")
        if not (chapter_dir / "resources" / "chapter_overview.md").exists():
            issues.append(f"{chapter_id} 缺少 resources/chapter_overview.md")
        if (chapter_dir / "resources" / "visual_animation.json").exists():
            issues.append(f"{chapter_id} 不应包含 resources/visual_animation.json")
        if (chapter_dir / "banks" / "animations.jsonl").exists():
            issues.append(f"{chapter_id} 不应包含 banks/animations.jsonl")
        map_path = chapter_dir / "indexes" / "section_resource_map.json"
        if not map_path.exists():
            issues.append(f"{chapter_id} 缺少 section_resource_map.json")
        else:
            section_map = _json_load(map_path, {})
            for section_id, item in (section_map if isinstance(section_map, dict) else {}).items():
                if any(key in item for key in ["animation_refs", "animation_filters", "visual_animation_refs"]):
                    issues.append(f"{chapter_id}/{section_id} 不应包含动画索引字段")

    return {
        "ok": not issues,
        "course_id": tree.get("course_id", "data_structures_algorithms"),
        "chapter_count": len(chapters),
        "unit_count": unit_count,
        "issues": issues,
    }
