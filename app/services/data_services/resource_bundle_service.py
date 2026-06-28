import re
from collections import defaultdict
from typing import Dict, List, Optional

from app.services.data_services import resource_artifact_type_service as artifact_types


BUNDLE_RESOURCE_TYPES = set(artifact_types.ACTIVE_ARTIFACT_TYPES)
DEPRECATED_STANDALONE_TYPES = set(artifact_types.DEPRECATED_ARTIFACT_TYPES)


def _clean_topic(value: str) -> str:
    topic = str(value or "").strip()
    topic = re.sub(r"\s+", " ", topic)
    for resource_type in BUNDLE_RESOURCE_TYPES:
        topic = topic.replace(resource_type, "")
    topic = topic.strip(" -_·|｜:：/\\")
    return topic or "数据结构与算法主题"


def infer_topic_from_resource(item: dict) -> str:
    if item.get("unit_title"):
        return _clean_topic(item.get("unit_title"))
    if item.get("topic"):
        return _clean_topic(item.get("topic"))

    title = item.get("title") or ""
    for resource_type in BUNDLE_RESOURCE_TYPES:
        if resource_type in title:
            return _clean_topic(title.replace(resource_type, ""))

    summary = item.get("summary") or ""
    match = re.search(r"围绕[「『]?([^」』，。,.]{2,40})[」』]?", summary)
    if match:
        return _clean_topic(match.group(1))

    return _clean_topic(title)


def build_topic_bundle(topic: str, resources: List[dict], semantic_result: Optional[Dict] = None) -> dict:
    semantic_result = semantic_result or {}
    items = []

    for item in resources:
        normalized_type = artifact_types.normalize_artifact_type(item.get("type"))
        if normalized_type in DEPRECATED_STANDALONE_TYPES:
            continue
        items.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "type": normalized_type,
            "summary": item.get("summary"),
            "status": item.get("status"),
        })

    return {
        "id": f"bundle::{_clean_topic(topic)}",
        "title": f"{_clean_topic(topic)}主题学习包",
        "topic": _clean_topic(topic),
        "subject_category": semantic_result.get("subject_category", "computer_science"),
        "bundle_type": "topic_resource_bundle",
        "summary": "由讲解、导图、题集、阅读、代码实验、PPT、视频推荐、观看指南、交互动画和项目任务组成的主题学习资源包。",
        "items": items,
        "resource_count": len(items),
        "type": "主题学习包",
        "auto_bundle": True,
    }


def build_topic_bundles(resources: List[dict], semantic_result: Optional[Dict] = None) -> List[dict]:
    grouped = defaultdict(list)
    for item in resources or []:
        normalized_type = artifact_types.normalize_artifact_type(item.get("type"))
        if normalized_type not in BUNDLE_RESOURCE_TYPES:
            continue
        grouped[infer_topic_from_resource(item)].append({**item, "type": normalized_type})

    bundles = []
    for topic, items in grouped.items():
        item_types = {item.get("type") for item in items}
        if len(item_types) < 2:
            continue
        bundle = build_topic_bundle(topic, items, semantic_result=semantic_result)
        if bundle["resource_count"]:
            bundles.append(bundle)

    bundles.sort(key=lambda item: (item.get("resource_count", 0), item.get("title", "")), reverse=True)
    return bundles
