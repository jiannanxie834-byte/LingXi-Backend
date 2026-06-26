import datetime
import json
import uuid
from typing import Dict, List

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


def record_profile_event(
    db: Session,
    *,
    username: str,
    source_type: str,
    source_id: str = "",
    profile: Dict = None,
    reason: str = "",
    course_id: str = "deep_learning",
) -> Dict:
    profile = profile or {}
    dimensions = profile.get("dimensions") if isinstance(profile.get("dimensions"), dict) else {}
    updated_dimensions = [key for key in PROFILE_DIMENSION_KEYS if key in dimensions]
    extracted_features = {
        "tags": profile.get("tags", []),
        "knowledge_tags": profile.get("knowledge_tags", []),
        "dimensions": {key: dimensions.get(key) for key in updated_dimensions},
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
        "extracted_features": json.loads(row.extracted_features_json or "{}"),
        "updated_dimensions": json.loads(row.updated_dimensions_json or "[]"),
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
