from app.agents.agent_result_dto import AgentResultDTO
from app.services.data_services import knowledge_evidence_service


def run(db, query: str, limit: int = 6) -> AgentResultDTO:
    items = knowledge_evidence_service.search_course_evidence(db, query or "", limit=limit)
    return AgentResultDTO(
        agent_name="EvidenceRetrievalAgent",
        input_summary=query[:120],
        output={"items": items},
        evidence_refs=[item.get("id") or item.get("evidence_id") or item.get("unit_id", "") for item in items],
        quality_score=1.0 if items else 0.0,
        warnings=[] if items else ["未检索到高置信课程证据"],
    )
