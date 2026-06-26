from datetime import datetime
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


AgentStatus = Literal["queued", "running", "completed", "failed", "skipped", "needs_review"]


class AgentResultDTO(BaseModel):
    agent_name: str
    status: AgentStatus = "completed"
    input_summary: str = ""
    output: Dict[str, Any] = Field(default_factory=dict)
    evidence_refs: List[str] = Field(default_factory=list)
    quality_score: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    started_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    finished_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


def from_pipeline_step(step: Dict[str, Any]) -> AgentResultDTO:
    status = str(step.get("status") or "completed")
    if status not in {"queued", "running", "completed", "failed", "skipped", "needs_review"}:
        status = "completed" if status == "pending" else "needs_review"
    return AgentResultDTO(
        agent_name=str(step.get("agent") or step.get("key") or "Agent"),
        status=status,
        input_summary=str(step.get("label") or ""),
        output={
            "key": step.get("key"),
            "label": step.get("label"),
            "detail": step.get("detail"),
        },
        warnings=[str(step.get("detail"))] if status in {"failed", "needs_review"} and step.get("detail") else [],
        quality_score=1.0 if status == "completed" else 0.0,
    )
