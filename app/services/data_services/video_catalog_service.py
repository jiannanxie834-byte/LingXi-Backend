import json
from pathlib import Path
from typing import Dict, List

from app.services.data_services import dsa_course_map_service


VIDEO_CATALOG_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "knowledge_base"
    / "data_structures_algorithms"
    / "video_catalog.json"
)
COURSEWARE_DIR = VIDEO_CATALOG_PATH.parent / "courseware"


def _read_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    rows: List[Dict] = []
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


def _normalize_video_item(item: Dict, source_kind: str = "courseware") -> Dict:
    video = dict(item or {})
    video_id = video.get("video_item_id") or video.get("video_id") or video.get("id") or ""
    video["video_item_id"] = video_id
    video["video_id"] = video_id
    video.setdefault("platform", video.get("source") or "Bilibili")
    video.setdefault("source", video.get("platform") or "公开视频")
    video.setdefault("usage_policy", "link_only")
    video.setdefault("source_kind", source_kind)
    if video.get("watch_focus") and not video.get("tags"):
        video["tags"] = video.get("watch_focus")
    return video


def _load_catalog() -> List[Dict]:
    catalog: List[Dict] = []
    if not VIDEO_CATALOG_PATH.exists():
        data = []
    else:
        with VIDEO_CATALOG_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    if isinstance(data, list):
        catalog.extend(_normalize_video_item(item, source_kind="legacy_catalog") for item in data if isinstance(item, dict))

    for path in sorted(COURSEWARE_DIR.glob("*/banks/video_items.jsonl")):
        catalog.extend(_normalize_video_item(item, source_kind="courseware_bank") for item in _read_jsonl(path))

    seen = set()
    unique = []
    for item in catalog:
        key = item.get("video_item_id") or item.get("source_url") or item.get("title")
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _score_video(
    video: Dict,
    unit_id: str,
    topic: str,
    profile: Dict = None,
    chapter_id: str = "",
    section_id: str = "",
    unit_ids: List[str] = None,
) -> int:
    profile = profile or {}
    unit_set = set([unit_id, *(unit_ids or [])]) - {""}
    score = 0
    video_unit_ids = set(video.get("unit_ids") or [])
    video_section_ids = set(video.get("section_ids") or [])
    if unit_set and unit_set.intersection(video_unit_ids):
        score += 90
    if section_id and section_id in video_section_ids:
        score += 70
    if chapter_id and chapter_id == video.get("chapter_id"):
        score += 28

    topic_text = " ".join([
        " ".join(video.get("tags") or []),
        " ".join(video.get("watch_focus") or []),
        video.get("title", ""),
    ]).lower()
    if topic and str(topic).lower() in topic_text:
        score += 14
    preferences = " ".join(str(item) for item in [
        profile.get("cognitive_style", ""),
        profile.get("media_preference", ""),
        profile.get("learning_goal", ""),
    ])
    if score > 0 and ("图" in preferences or "视频" in preferences or "可视化" in preferences):
        if "video" in (video.get("platform") or "").lower() or "图" in (video.get("title") or ""):
            score += 8
    if score > 0 and ("代码" in preferences or "项目" in preferences):
        if any(tag.lower() in {"代码", "项目", "算法", "可视化", "刷题"} for tag in video.get("tags") or []):
            score += 8
    return score


def list_video_catalog() -> List[Dict]:
    return _load_catalog()


def search_videos(
    unit_id: str = "",
    topic: str = "",
    profile: Dict = None,
    limit: int = 6,
    chapter_id: str = "",
    section_id: str = "",
    unit_ids: List[str] = None,
) -> List[Dict]:
    catalog = _load_catalog()
    if not unit_id and topic:
        match = dsa_course_map_service.match_dsa_topic(topic, topic)
        unit_id = match.get("unit_id", "")
        chapter_id = chapter_id or match.get("chapter_id", "")
        section_id = section_id or match.get("section_id", "")
        unit_ids = unit_ids or match.get("unit_ids", [])
    scored = []
    for video in catalog:
        if video.get("status") not in {None, "", "ready", "published", "正常开放"}:
            continue
        score = _score_video(
            video,
            unit_id,
            topic,
            profile=profile,
            chapter_id=chapter_id,
            section_id=section_id,
            unit_ids=unit_ids,
        )
        if score <= 0:
            continue
        scored.append({**video, "recommend_score": score})
    if any(item.get("recommend_score", 0) >= 70 for item in scored):
        scored = [item for item in scored if item.get("recommend_score", 0) >= 70]
    scored.sort(key=lambda item: (item.get("recommend_score", 0), item.get("title", "")), reverse=True)
    return scored[:max(1, min(int(limit or 6), 20))]


def build_personalized_video_guide(course_match: Dict, profile: Dict = None) -> Dict:
    profile = profile or {}
    topic = course_match.get("normalized_topic") or course_match.get("topic") or "算法学习主题"
    unit_id = course_match.get("unit_id") or course_match.get("primary_unit_id") or ""
    chapter_id = course_match.get("chapter_id", "")
    section_id = course_match.get("section_id", "")
    unit_ids = course_match.get("unit_ids") or ([unit_id] if unit_id else [])
    videos = search_videos(
        unit_id=unit_id,
        topic=topic,
        profile=profile,
        limit=3,
        chapter_id=chapter_id,
        section_id=section_id,
        unit_ids=unit_ids,
    )
    video_lines = [
        f"- [{video.get('title', '公开视频')}]({video.get('source_url', '')})：重点看{ '、'.join(video.get('watch_focus') or []) or topic }。"
        for video in videos
        if video.get("source_url")
    ]
    return {
        "type": "personalized_video_guide",
        "topic": topic,
        "unit_id": unit_id,
        "chapter_id": chapter_id,
        "section_id": section_id,
        "before_watch": [
            "先回忆该知识点的前置概念和关键公式。",
            "打开视频前准备一张草稿纸，记录不理解的符号、shape 或流程。",
        ],
        "watch_focus": course_match.get("core_topics") or ["核心概念", "公式/流程", "常见误区"],
        "pause_and_think": [
            "这个步骤解决了什么问题？",
            "如果换一组输入 shape，输出会发生什么变化？",
            "这个概念在代码实现里对应哪一段逻辑？",
        ],
        "after_watch_tasks": [
            "完成 2 道概念题和 1 道应用题。",
            "如果涉及代码，运行一个最小 demo 并记录输入输出和边界样例。",
        ],
        "linked_resources": ["练习题集", "代码实验", "图解说明"],
        "recommended_videos": videos,
        "content": "\n".join([
            f"# {topic} 个性化视频观看指南",
            "",
            "## 推荐视频链接",
            *(video_lines or ["- 当前匹配小节暂未配置公开视频链接。"]),
            "",
            "## 观看方法",
            "- 先带着一个具体问题观看，不要从头到尾被动听。",
            "- 看到关键步骤时暂停，手推一个最小例子。",
            "- 看完后回到练习题或代码实验验证是否真的掌握。",
        ]),
        "copyright_note": "仅提供原始链接和学习建议，不复制、不下载、不重新分发视频内容。",
    }
