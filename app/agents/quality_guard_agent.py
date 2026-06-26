from app.agents.agent_result_dto import AgentResultDTO
from app.services.data_services import resource_quality_gate


def run(resource: dict, semantic_result: dict = None) -> AgentResultDTO:
    review = resource_quality_gate.validate_resource_semantics(resource, semantic_result or {})
    return AgentResultDTO(
        agent_name="QualityGuardAgent",
        status="needs_review" if review.get("fatal") else "completed",
        input_summary=resource.get("title", ""),
        output=review,
        evidence_refs=[semantic_result.get("unit_id", "")] if semantic_result and semantic_result.get("unit_id") else [],
        quality_score=0.4 if review.get("fatal") else 0.88,
        warnings=review.get("issues", []),
    )
