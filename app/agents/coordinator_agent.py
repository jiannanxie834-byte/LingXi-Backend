from app.agents.agent_result_dto import AgentResultDTO


PIPELINE = [
    "IntentSemanticAgent",
    "ProfileAgent",
    "CourseMapAgent",
    "EvidenceRetrievalAgent",
    "LearningPathAgent",
    "ResourcePlanningAgent",
    "ArtifactGenerationAgents",
    "QualityGuardAgent",
    "RecommendationAgent",
    "FinalResponseComposer",
]


def run(message: str) -> AgentResultDTO:
    return AgentResultDTO(
        agent_name="CoordinatorAgent",
        input_summary=message[:120],
        output={"pipeline": PIPELINE},
        quality_score=1.0,
    )
