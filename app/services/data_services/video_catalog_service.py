import json
from pathlib import Path
from typing import Dict, List

from app.services.data_services import deep_learning_course_map_service


VIDEO_CATALOG_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "knowledge_base"
    / "deep_learning"
    / "video_catalog.json"
)


def _load_catalog() -> List[Dict]:
    if not VIDEO_CATALOG_PATH.exists():
        return []
    with VIDEO_CATALOG_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data if isinstance(data, list) else []


def _score_video(video: Dict, unit_id: str, topic: str, profile: Dict = None) -> int:
    profile = profile or {}
    score = 0
    if unit_id and unit_id in (video.get("unit_ids") or []):
        score += 60
    topic_text = " ".join([topic or "", " ".join(video.get("tags") or []), video.get("title", "")]).lower()
    for alias in [topic, *(video.get("tags") or [])]:
        if alias and str(alias).lower() in topic_text:
            score += 4
    preferences = " ".join(str(item) for item in [
        profile.get("cognitive_style", ""),
        profile.get("media_preference", ""),
        profile.get("learning_goal", ""),
    ])
    if "图" in preferences or "视频" in preferences or "可视化" in preferences:
        if "video" in (video.get("platform") or "").lower() or "图" in (video.get("title") or ""):
            score += 8
    if "代码" in preferences or "项目" in preferences:
        if any(tag.lower() in {"pytorch", "代码", "项目", "图像分类"} for tag in video.get("tags") or []):
            score += 8
    return score


def list_video_catalog() -> List[Dict]:
    return _load_catalog()


def search_videos(unit_id: str = "", topic: str = "", profile: Dict = None, limit: int = 6) -> List[Dict]:
    catalog = _load_catalog()
    if not unit_id and topic:
        match = deep_learning_course_map_service.match_deep_learning_topic(topic, topic)
        unit_id = match.get("unit_id", "")
    scored = []
    for video in catalog:
        score = _score_video(video, unit_id, topic, profile=profile)
        if score <= 0:
            continue
        scored.append({**video, "recommend_score": score})
    scored.sort(key=lambda item: (item.get("recommend_score", 0), item.get("title", "")), reverse=True)
    return scored[:max(1, min(int(limit or 6), 20))]


def build_personalized_video_guide(course_match: Dict, profile: Dict = None) -> Dict:
    profile = profile or {}
    topic = course_match.get("normalized_topic") or course_match.get("topic") or "深度学习主题"
    unit_id = course_match.get("unit_id", "")
    videos = search_videos(unit_id=unit_id, topic=topic, profile=profile, limit=3)
    return {
        "type": "personalized_video_guide",
        "topic": topic,
        "unit_id": unit_id,
        "before_watch": [
            "先回忆该知识点的前置概念和关键公式。",
            "打开视频前准备一张草稿纸，记录不理解的符号、shape 或流程。",
        ],
        "watch_focus": course_match.get("core_topics") or ["核心概念", "公式/流程", "常见误区"],
        "pause_and_think": [
            "这个步骤解决了什么问题？",
            "如果换一组输入 shape，输出会发生什么变化？",
            "这个概念在 PyTorch 代码里对应哪一行？",
        ],
        "after_watch_tasks": [
            "完成 2 道概念题和 1 道应用题。",
            "如果涉及代码，运行一个最小 demo 并记录输出 shape。",
        ],
        "linked_resources": ["练习题集", "PyTorch 实操案例", "交互动画规格"],
        "recommended_videos": videos,
        "copyright_note": "仅提供原始链接和学习建议，不复制、不下载、不重新分发视频内容。",
    }
