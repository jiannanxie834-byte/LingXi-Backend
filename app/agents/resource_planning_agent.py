from app.agents.agent_result_dto import AgentResultDTO
from app.agents.resource_agent import run as resource_plan_run


def run(plan: dict, profile: dict, semantic_result: dict = None, generation_context: dict = None) -> AgentResultDTO:
    result = resource_plan_run(plan, profile, semantic_result=semantic_result, generation_context=generation_context)
    resources = result.get("resources", [])
    return AgentResultDTO(
        agent_name="ResourcePlanningAgent",
        input_summary=(result.get("dsa_course_map") or result.get("ai_course_map") or {}).get("normalized_topic", ""),
        output=result,
        evidence_refs=[item.get("unit_id", "") for item in resources if item.get("unit_id")],
        quality_score=1.0 if resources else 0.0,
        warnings=[] if resources else ["未规划出 Artifact"],
    )
