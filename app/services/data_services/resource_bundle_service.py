import re
from collections import defaultdict
from typing import Dict, List, Optional


BUNDLE_RESOURCE_TYPES = [
    "专业课程讲解文档",
    "知识点思维导图",
    "不同类型练习题目",
    "拓展阅读材料",
    "学科实践应用任务",
]

DEPRECATED_STANDALONE_TYPES = {"多模态学习包"}


def _clean_topic(value: str) -> str:
    topic = str(value or "").strip()
    topic = re.sub(r"\s+", " ", topic)
    for resource_type in BUNDLE_RESOURCE_TYPES:
        topic = topic.replace(resource_type, "")
    topic = topic.strip(" -_·|｜:：/\\")
    return topic or "主题学习"


def infer_topic_from_resource(item: dict) -> str:
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
        if item.get("type") in DEPRECATED_STANDALONE_TYPES:
            continue
        items.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "type": item.get("type"),
            "summary": item.get("summary"),
            "status": item.get("status"),
        })

    return {
        "id": f"bundle::{_clean_topic(topic)}",
        "title": f"{_clean_topic(topic)}学习包",
        "topic": _clean_topic(topic),
        "subject_category": semantic_result.get("subject_category", "unknown"),
        "bundle_type": "topic_resource_bundle",
        "summary": "由讲解、导图、练习、阅读和实践任务组成的主题学习资源包。",
        "items": items,
        "resource_count": len(items),
        "type": "主题学习包",
        "auto_bundle": True,
    }


def build_topic_bundles(resources: List[dict], semantic_result: Optional[Dict] = None) -> List[dict]:
    grouped = defaultdict(list)
    for item in resources or []:
        if item.get("type") not in BUNDLE_RESOURCE_TYPES:
            continue
        grouped[infer_topic_from_resource(item)].append(item)

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
