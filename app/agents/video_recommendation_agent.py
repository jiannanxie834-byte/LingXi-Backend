from app.agents.agent_result_dto import AgentResultDTO
from app.services.data_services import video_catalog_service


def run(unit_id: str = "", topic: str = "", profile: dict = None, limit: int = 6) -> AgentResultDTO:
    videos = video_catalog_service.search_videos(unit_id=unit_id, topic=topic, profile=profile, limit=limit)
    return AgentResultDTO(
        agent_name="VideoRecommendationAgent",
        input_summary=topic or unit_id,
        output={"videos": videos},
        evidence_refs=[item.get("video_id", "") for item in videos],
        quality_score=1.0 if videos else 0.0,
        warnings=[] if videos else ["未匹配到公开视频目录"],
    )
