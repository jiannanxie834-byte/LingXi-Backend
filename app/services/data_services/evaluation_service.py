import json
import datetime
import uuid

from sqlalchemy.orm import Session
from app.models.schemas import EvaluationRecord


def _safe_json_load(data, default):
    try:
        return json.loads(data) if data else default
    except Exception:
        return default


def _evaluation_to_dict(record: EvaluationRecord):
    return {
        "id": record.id,
        "username": record.username,
        "topic": record.topic,
        "score": record.score,
        "level": record.level,
        "weak_points": _safe_json_load(record.weak_points, []),
        "suggestions": _safe_json_load(record.suggestions, []),
        "wrong_notes": record.wrong_notes or "",
        "answers": _safe_json_load(record.answers_json, {}),
        "generated_resource_id": record.generated_resource_id or "",
        "created_at": record.created_at.isoformat() if record.created_at else ""
    }


# =========================
# 保存评价记录（DB由外部传入）
# =========================
def save_evaluation_record(
    db: Session,
    username: str,
    topic: str,
    score: int,
    level: str,
    weak_points: list,
    suggestions: list,
    wrong_notes: str,
    answers: dict,
    generated_resource_id: str = ""
):
    try:
        record = EvaluationRecord(
            id=str(uuid.uuid4()),
            username=username,
            topic=topic,
            score=score,
            level=level,
            weak_points=json.dumps(weak_points or [], ensure_ascii=False),
            suggestions=json.dumps(suggestions or [], ensure_ascii=False),
            wrong_notes=wrong_notes or "",
            answers_json=json.dumps(answers or {}, ensure_ascii=False),
            generated_resource_id=generated_resource_id,
            created_at=datetime.datetime.now()
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return _evaluation_to_dict(record)

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"保存评价记录失败: {str(e)}"
        }


# =========================
# 查询评价记录
# =========================
def get_evaluation_records(db: Session, username: str):
    try:
        records = (
            db.query(EvaluationRecord)
            .filter(EvaluationRecord.username == username)
            .order_by(EvaluationRecord.created_at.desc())
            .all()
        )

        return [_evaluation_to_dict(r) for r in records]

    except Exception as e:
        return {
            "success": False,
            "message": f"获取评价记录失败: {str(e)}"
        }