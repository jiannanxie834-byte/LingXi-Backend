import datetime
import json
import uuid
from typing import Dict, Iterable, List

from sqlalchemy.orm import Session

from app.agents.agent_result_dto import AgentResultDTO, from_pipeline_step
from app.models.schemas import AgentTrace


def _json_dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def save_agent_results(
    db: Session,
    *,
    trace_id: str,
    username: str = "",
    session_id: str = "",
    results: Iterable[AgentResultDTO],
) -> List[Dict]:
    saved = []
    now = datetime.datetime.now()
    for result in results:
        row = AgentTrace(
            id=f"atrace_{uuid.uuid4().hex[:16]}",
            trace_id=trace_id,
            username=username or "",
            session_id=session_id or "",
            agent_name=result.agent_name,
            status=result.status,
            input_summary=result.input_summary,
            output_json=_json_dump(result.output),
            evidence_refs_json=_json_dump(result.evidence_refs),
            quality_score=float(result.quality_score or 0),
            warnings_json=_json_dump(result.warnings),
            started_at=now,
            finished_at=now,
        )
        db.add(row)
        saved.append(to_dict(row))
    db.commit()
    return saved


def save_pipeline_trace(
    db: Session,
    *,
    trace_id: str,
    username: str = "",
    session_id: str = "",
    pipeline_steps: List[Dict] = None,
) -> List[Dict]:
    results = [from_pipeline_step(step) for step in (pipeline_steps or [])]
    if not results:
        return []
    return save_agent_results(
        db,
        trace_id=trace_id,
        username=username,
        session_id=session_id,
        results=results,
    )


def to_dict(row: AgentTrace) -> Dict:
    return {
        "id": row.id,
        "trace_id": row.trace_id,
        "username": row.username,
        "session_id": row.session_id,
        "agent_name": row.agent_name,
        "status": row.status,
        "input_summary": row.input_summary,
        "output": json.loads(row.output_json or "{}"),
        "evidence_refs": json.loads(row.evidence_refs_json or "[]"),
        "quality_score": row.quality_score or 0,
        "warnings": json.loads(row.warnings_json or "[]"),
        "started_at": row.started_at.isoformat(timespec="seconds") if row.started_at else "",
        "finished_at": row.finished_at.isoformat(timespec="seconds") if row.finished_at else "",
    }


def list_trace(db: Session, trace_id: str) -> List[Dict]:
    rows = (
        db.query(AgentTrace)
        .filter(AgentTrace.trace_id == trace_id)
        .order_by(AgentTrace.started_at.asc())
        .all()
    )
    return [to_dict(row) for row in rows]
