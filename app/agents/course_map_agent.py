from app.agents.agent_result_dto import AgentResultDTO
from app.services.data_services import dsa_course_map_service


def run(topic: str = "", message: str = "") -> AgentResultDTO:
    match = dsa_course_map_service.match_dsa_topic(topic, message)
    return AgentResultDTO(
        agent_name="CourseMapAgent",
        input_summary=" / ".join([topic or "", message or ""])[:120],
        output=match,
        evidence_refs=[match.get("unit_id", "")] if match.get("unit_id") else [],
        quality_score=float(match.get("confidence") or 0),
        warnings=[] if match.get("matched") else ["未命中《数据结构与算法》课程图谱"],
    )
