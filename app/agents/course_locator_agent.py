from app.agents.agent_result_dto import AgentResultDTO
from app.services.data_services import dsa_course_map_service, dsa_topic_resolver


def run(semantic_result: dict = None, generation_context: dict = None) -> AgentResultDTO:
    semantic_result = semantic_result or {}
    generation_context = generation_context or {}
    course_map = (
        semantic_result.get("dsa_course_map")
        or semantic_result.get("ai_course_map")
        or {}
    )
    topic = (
        semantic_result.get("display_topic")
        or course_map.get("display_topic")
        or course_map.get("normalized_topic")
        or semantic_result.get("topic")
        or generation_context.get("topic")
        or ""
    )
    unit_id = (
        semantic_result.get("primary_unit_id")
        or semantic_result.get("unit_id")
        or course_map.get("primary_unit_id")
        or course_map.get("unit_id")
        or ""
    )
    unit_ids = [item for item in [unit_id, *(semantic_result.get("unit_ids") or [])] if item]
    resolved = dsa_topic_resolver.resolve_topic(
        topic,
        chapter_id=semantic_result.get("chapter_id") or course_map.get("chapter_id") or "",
        section_id=semantic_result.get("section_id") or course_map.get("section_id") or "",
        unit_ids=list(dict.fromkeys(unit_ids)),
        fallback_topic=topic or "数据结构与算法学习主题",
    )
    if not resolved.get("chapter_id") and unit_id:
        unit = dsa_course_map_service.get_unit(unit_id) or {}
        resolved = dsa_topic_resolver.resolve_topic(
            topic,
            chapter_id=unit.get("chapter_id") or "",
            section_id=unit.get("section_id") or "",
            unit_ids=[unit_id],
            fallback_topic=topic or unit.get("title") or "数据结构与算法学习主题",
        )

    output = {
        "course": "数据结构与算法",
        "topic": resolved.get("topic") or topic or "数据结构与算法学习主题",
        "student_question": semantic_result.get("message") or generation_context.get("message") or "",
        "chapter_title": resolved.get("chapter_title") or "待定位",
        "section_title": resolved.get("section_title") or "待定位",
        "unit_titles": resolved.get("unit_titles") or [],
        "scope_level": semantic_result.get("scope_level") or course_map.get("scope_level") or "unit",
        "course_id": dsa_course_map_service.COURSE_ID,
        "chapter_id": resolved.get("chapter_id") or "",
        "section_id": resolved.get("section_id") or "",
        "unit_ids": resolved.get("unit_ids") or [],
        "evidence_refs": resolved.get("evidence_refs") or [],
    }
    return AgentResultDTO(
        agent_name="CourseLocatorAgent",
        input_summary=topic or "数据结构与算法学习主题",
        output=output,
        evidence_refs=output["evidence_refs"],
        quality_score=1.0 if output["chapter_id"] else 0.6,
        warnings=[] if output["chapter_id"] else ["未能精确定位章节，使用课程级兜底定位。"],
    )
