from app.agents.agent_result_dto import AgentResultDTO
from app.agents.evaluation_agent import run as evaluation_run
from app.services.data_services import semantic_analysis_service


def run(db, username: str, message: str) -> AgentResultDTO:
    intent_result = evaluation_run(message)
    semantic_result = semantic_analysis_service.analyze_learning_request(db, username, message, intent_result)
    return AgentResultDTO(
        agent_name="IntentSemanticAgent",
        input_summary=message[:120],
        output={"intent": intent_result, "semantic": semantic_result},
        evidence_refs=[semantic_result.get("unit_id", "")] if semantic_result.get("unit_id") else [],
        quality_score=semantic_result.get("confidence", 0) / 100,
        warnings=[] if semantic_result.get("is_supported_scope") else ["out_of_course"],
    )
