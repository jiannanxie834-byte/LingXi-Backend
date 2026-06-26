from app.agents.agent_result_dto import AgentResultDTO
from app.agents.planner_agent import run as planner_run


def run(profile: dict, semantic_result: dict = None) -> AgentResultDTO:
    plan = planner_run(profile, semantic_result=semantic_result)
    steps = plan.get("steps", [])
    return AgentResultDTO(
        agent_name="LearningPathAgent",
        input_summary=plan.get("title", ""),
        output=plan,
        evidence_refs=[step.get("unit_id", "") for step in steps if step.get("unit_id")],
        quality_score=1.0 if steps else 0.0,
        warnings=[] if steps else ["未生成路径节点"],
    )
