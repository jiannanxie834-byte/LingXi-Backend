from app.agents.agent_result_dto import AgentResultDTO
from app.services.data_services import video_catalog_service


def run(course_match: dict, profile: dict = None) -> AgentResultDTO:
    guide = video_catalog_service.build_personalized_video_guide(course_match, profile=profile)
    return AgentResultDTO(
        agent_name="PersonalizedVideoGuideAgent",
        input_summary=guide.get("topic", ""),
        output=guide,
        evidence_refs=[
            item.get("video_item_id") or item.get("video_id") or item.get("source_url", "")
            for item in guide.get("recommended_videos", [])
        ],
        quality_score=1.0 if guide.get("recommended_videos") else 0.75,
        warnings=[],
    )
