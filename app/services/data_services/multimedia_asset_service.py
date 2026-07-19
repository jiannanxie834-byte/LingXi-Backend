import json

from sqlalchemy.orm import Session

from app.models.schemas import ResourceArtifact
from app.services.data_services import resource_artifact_type_service as artifact_types


DP_ANIMATION_ASSET = {
    "kind": "interactive_animation",
    "title": "动态规划状态转移交互动画",
    "url": "/media/animations/dp_state_transition.html",
    "mime_type": "text/html",
    "duration_seconds": 42,
    "controls": ["play", "pause", "next", "reset"],
}


def _is_dynamic_programming_item(item: dict) -> bool:
    course_map = item.get("dsa_course_map") or item.get("ai_course_map") or {}
    text = " ".join([
        str(item.get("title") or ""),
        str(item.get("topic") or ""),
        str(item.get("unit_title") or ""),
        str(item.get("unit_id") or ""),
        str(course_map.get("normalized_topic") or ""),
        str(course_map.get("unit_id") or ""),
    ]).lower()
    return "动态规划" in text or "dsa_dp" in text


def attach_playable_assets(resource_plan: dict) -> dict:
    for item in resource_plan.get("resources", []) or []:
        resource_type = artifact_types.normalize_artifact_type(item.get("type", ""))
        if resource_type not in {
            artifact_types.INTERACTIVE_ANIMATION,
            artifact_types.PERSONALIZED_VIDEO_GUIDE,
        } or not _is_dynamic_programming_item(item):
            continue
        assets = [asset for asset in (item.get("assets") or []) if isinstance(asset, dict)]
        if not any(asset.get("url") == DP_ANIMATION_ASSET["url"] for asset in assets):
            assets.append(dict(DP_ANIMATION_ASSET))
        item["assets"] = assets
    return resource_plan


def attach_to_existing_demo_artifacts(db: Session) -> int:
    rows = (
        db.query(ResourceArtifact)
        .filter(ResourceArtifact.type == artifact_types.PERSONALIZED_VIDEO_GUIDE)
        .filter(ResourceArtifact.title.like("%动态规划%"))
        .all()
    )
    changed = 0
    for row in rows:
        try:
            assets = json.loads(row.assets_json or "[]")
        except json.JSONDecodeError:
            assets = []
        if any(isinstance(asset, dict) and asset.get("url") == DP_ANIMATION_ASSET["url"] for asset in assets):
            continue
        assets.append(dict(DP_ANIMATION_ASSET))
        row.assets_json = json.dumps(assets, ensure_ascii=False)
        changed += 1
    if changed:
        db.commit()
    return changed
