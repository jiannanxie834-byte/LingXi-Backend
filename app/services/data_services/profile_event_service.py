import datetime
import json
import uuid
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.schemas import ProfileEvent


PROFILE_DIMENSION_KEYS = [
    "知识基础",
    "学习目标",
    "学习阶段",
    "知识短板",
    "认知风格",
    "媒介偏好",
    "实践能力",
    "学习节奏",
    "易错模式",
    "兴趣方向",
]


def _json_dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_load(value, default):
    try:
        return json.loads(value) if value else default
    except Exception:
        return default


def _clamp(value, low: int = 0, high: int = 100) -> int:
    try:
        return max(low, min(high, int(round(float(value)))))
    except Exception:
        return low


def _fallback_radar(dimensions: Dict) -> Dict:
    radar = {}
    for key in PROFILE_DIMENSION_KEYS:
        value = dimensions.get(key)
        if isinstance(value, (int, float)):
            radar[key] = _clamp(value)
        elif value:
            radar[key] = 65
        else:
            radar[key] = 0
    return radar


def record_profile_event(
    db: Session,
    *,
    username: str,
    source_type: str,
    source_id: str = "",
    profile: Dict = None,
    reason: str = "",
    course_id: str = "data_structures_algorithms",
) -> Dict:
    profile = profile or {}
    dimensions = profile.get("dimensions") if isinstance(profile.get("dimensions"), dict) else {}
    radar = profile.get("radar") if isinstance(profile.get("radar"), dict) else {}
    updated_dimensions = [key for key in PROFILE_DIMENSION_KEYS if key in dimensions]
    extracted_features = {
        "tags": profile.get("tags", []),
        "knowledge_tags": profile.get("knowledge_tags", []),
        "dimensions": {key: dimensions.get(key) for key in updated_dimensions},
        "radar": {
            key: radar.get(key, 0)
            for key in PROFILE_DIMENSION_KEYS
            if key in radar
        },
        "hours": profile.get("hours"),
        "updated_at": profile.get("updated_at"),
        "evidence": profile.get("evidence", {}),
    }
    row = ProfileEvent(
        event_id=f"pevt_{uuid.uuid4().hex[:16]}",
        student_id=username,
        course_id=course_id,
        source_type=source_type,
        source_id=source_id or "",
        extracted_features_json=_json_dump(extracted_features),
        updated_dimensions_json=_json_dump(updated_dimensions),
        reason=reason or "本轮交互触发动态学习画像更新。",
        created_at=datetime.datetime.now(),
    )
    db.add(row)
    db.commit()
    return to_dict(row)


def to_dict(row: ProfileEvent) -> Dict:
    return {
        "event_id": row.event_id,
        "student_id": row.student_id,
        "course_id": row.course_id,
        "source_type": row.source_type,
        "source_id": row.source_id,
        "extracted_features": _json_load(row.extracted_features_json, {}),
        "updated_dimensions": _json_load(row.updated_dimensions_json, []),
        "reason": row.reason,
        "created_at": row.created_at.isoformat(timespec="seconds") if row.created_at else "",
    }


def list_profile_events(db: Session, username: str, limit: int = 30) -> List[Dict]:
    rows = (
        db.query(ProfileEvent)
        .filter(ProfileEvent.student_id == username)
        .order_by(ProfileEvent.created_at.desc())
        .limit(max(1, min(int(limit or 30), 100)))
        .all()
    )
    return [to_dict(row) for row in rows]


def get_current_profile_snapshot(db: Session, username: str, user: Optional[object] = None) -> Dict:
    events = list_profile_events(db, username, limit=20)
    merged_dimensions = {}
    merged_radar = {}
    tags = []
    knowledge_tags = []
    latest_time = ""

    for event in reversed(events):
        features = event.get("extracted_features") or {}
        dimensions = features.get("dimensions") if isinstance(features.get("dimensions"), dict) else {}
        radar = features.get("radar") if isinstance(features.get("radar"), dict) else {}
        merged_dimensions.update({key: value for key, value in dimensions.items() if key in PROFILE_DIMENSION_KEYS})
        merged_radar.update({key: _clamp(value) for key, value in radar.items() if key in PROFILE_DIMENSION_KEYS})
        if features.get("tags"):
            tags = features.get("tags") or tags
        if features.get("knowledge_tags"):
            knowledge_tags = features.get("knowledge_tags") or knowledge_tags
        latest_time = features.get("updated_at") or event.get("created_at") or latest_time

    if not merged_radar:
        merged_radar = _fallback_radar(merged_dimensions)
    else:
        for key, value in _fallback_radar(merged_dimensions).items():
            merged_radar.setdefault(key, value)

    if user and not tags:
        raw_tags = getattr(user, "tags", "") or ""
        tags = [item.strip() for item in raw_tags.split(",") if item.strip()]
    if not knowledge_tags:
        knowledge_tags = tags

    if not merged_dimensions and not any(merged_radar.values()) and not tags:
        return {}

    return {
        "tags": tags,
        "knowledge_tags": knowledge_tags,
        "hours": getattr(user, "hours", None) if user else None,
        "updated_at": latest_time or datetime.datetime.now().isoformat(timespec="seconds"),
        "dimensions": {
            key: merged_dimensions.get(key, "")
            for key in PROFILE_DIMENSION_KEYS
            if key in merged_dimensions
        },
        "radar": {
            key: _clamp(merged_radar.get(key, 0))
            for key in PROFILE_DIMENSION_KEYS
        },
    }
