import datetime
import json
import uuid
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.schemas import ProfileEvent
from app.services.data_services import profile_dimension_service


PROFILE_DIMENSION_KEYS = list(profile_dimension_service.LEGACY_PROFILE_DIMENSION_KEYS)
PUBLIC_DIMENSION_KEYS = list(profile_dimension_service.PUBLIC_PROFILE_DIMENSION_KEYS)

SOURCE_PUBLIC_DIMENSIONS = {
    "chat": {"当前知识水平", "学习目标", "资源偏好"},
    "evaluation": {"当前知识水平", "练习表现", "薄弱知识点"},
    "exercise_attempt": {"当前知识水平", "练习表现", "薄弱知识点"},
    "learning_plan": {"路径执行"},
    "todo": {"路径执行"},
    "resource_feedback": {"资源偏好"},
}


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


def _profile_event_public_dimensions(features: Dict) -> Dict:
    features = features if isinstance(features, dict) else {}
    payload = {
        "dimensions": features.get("dimensions") or features.get("legacy_dimensions") or {},
        "radar": features.get("radar") or features.get("legacy_radar") or {},
        "evidence": features.get("evidence") or {},
    }
    if isinstance(features.get("public_dimensions"), dict) and features.get("public_dimensions"):
        payload["public_dimensions"] = features.get("public_dimensions")
    return profile_dimension_service.derive_public_dimensions(payload)


def _merge_public_history(events: List[Dict]) -> Dict:
    merged = {}
    latest_full = {}
    for event in reversed(events):
        features = event.get("extracted_features") or {}
        event_public = _profile_event_public_dimensions(features)
        latest_full = event_public or latest_full
        updated = set(event.get("updated_dimensions") or [])
        public_updates = [name for name in PUBLIC_DIMENSION_KEYS if name in updated]

        if public_updates:
            for name in public_updates:
                if name in event_public:
                    merged[name] = event_public[name]
        elif not features.get("public_dimensions"):
            # 历史事件没有六维公开层，先完成兼容转换；新事件会按真实差分覆盖。
            merged.update(event_public)

    for name in PUBLIC_DIMENSION_KEYS:
        if name not in merged and name in latest_full:
            merged[name] = latest_full[name]
    return profile_dimension_service.derive_public_dimensions({"public_dimensions": merged})


def _changed_public_dimensions(
    *,
    source_type: str,
    current: Dict,
    previous: Dict,
) -> List[str]:
    allowed = SOURCE_PUBLIC_DIMENSIONS.get(source_type, set(PUBLIC_DIMENSION_KEYS))
    changed = []
    for name in PUBLIC_DIMENSION_KEYS:
        entry = current.get(name)
        if name not in allowed or not profile_dimension_service.is_meaningful_dimension(entry):
            continue
        if previous.get(name) != entry:
            changed.append(name)
    return changed


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
    previous_events = list_profile_events(db, username, limit=30)
    previous_public = _merge_public_history(previous_events) if previous_events else {}
    public_dimensions = profile_dimension_service.derive_public_dimensions(profile)
    updated_dimensions = _changed_public_dimensions(
        source_type=source_type,
        current=public_dimensions,
        previous=previous_public,
    )
    extracted_features = {
        "tags": profile.get("tags", []),
        "knowledge_tags": profile.get("knowledge_tags", []),
        # dimensions/radar 继续保存内部十维快照，避免破坏历史数据和既有任务。
        "dimensions": {key: dimensions.get(key) for key in PROFILE_DIMENSION_KEYS if key in dimensions},
        "radar": {
            key: radar.get(key, 0)
            for key in PROFILE_DIMENSION_KEYS
            if key in radar
        },
        "public_dimensions": public_dimensions,
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
        .filter(
            ProfileEvent.student_id == username,
            ~ProfileEvent.source_type.like("legacy_invalid%"),
        )
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
    latest_evidence = {}

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
        if isinstance(features.get("evidence"), dict) and features.get("evidence"):
            latest_evidence = features.get("evidence")
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

    public_dimensions = _merge_public_history(events) if events else {}

    if not merged_dimensions and not any(merged_radar.values()) and not tags and not public_dimensions:
        return {}

    public_profile = profile_dimension_service.build_public_profile_payload({
        "tags": tags,
        "knowledge_tags": knowledge_tags,
        "hours": getattr(user, "hours", None) if user else None,
        "updated_at": latest_time or datetime.datetime.now().isoformat(timespec="seconds"),
        "dimensions": merged_dimensions,
        "radar": merged_radar,
        "public_dimensions": public_dimensions,
        "evidence": latest_evidence,
    })
    return public_profile
