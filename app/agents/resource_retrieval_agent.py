from app.agents.agent_result_dto import AgentResultDTO
from app.services.data_services import dsa_course_content_service


def _fallback_section_from_chapter(chapter_detail: dict, unit_ids: list[str]) -> dict:
    unit_set = set(unit_ids or [])
    for section in chapter_detail.get("manifest", {}).get("sections", []) or []:
        if unit_set.intersection(section.get("unit_ids") or []):
            return section
    for section in chapter_detail.get("sections", []) or []:
        if unit_set.intersection(section.get("unit_ids") or []):
            return section
    return (chapter_detail.get("sections") or [{}])[0] if chapter_detail.get("sections") else {}


def run(location: dict) -> dict:
    location = location or {}
    chapter_id = location.get("chapter_id") or ""
    section_id = location.get("section_id") or ""
    unit_ids = location.get("unit_ids") or []
    chapter_result = dsa_course_content_service.get_chapter_detail(chapter_id) if chapter_id else {"ok": False, "data": {}}
    chapter_detail = chapter_result.get("data") or {}
    if not section_id and chapter_detail:
        section_id = (_fallback_section_from_chapter(chapter_detail, unit_ids) or {}).get("section_id") or ""

    section_result = (
        dsa_course_content_service.get_section_detail(chapter_id, section_id)
        if chapter_id and section_id
        else {"ok": False, "data": {}}
    )
    section_detail = section_result.get("data") or {}
    related = section_detail.get("related") or {}
    retrieval = {
        "topic": location.get("topic") or "",
        "chapter_title": chapter_detail.get("title") or location.get("chapter_title") or "",
        "section_title": section_detail.get("title") or location.get("section_title") or "",
        "section_content": section_detail.get("content") or "",
        "section_path": section_detail.get("path") or "",
        "mind_map": chapter_detail.get("mind_map") or "",
        "mind_map_path": "resources/mind_map.mmd" if chapter_detail.get("mind_map") else "",
        "reading_video_guide": chapter_detail.get("reading_video_guide") or "",
        "reading_video_guide_path": "resources/reading_video_guide.md" if chapter_detail.get("reading_video_guide") else "",
        "exercises": related.get("exercises") or [],
        "code_tasks": related.get("code_tasks") or [],
        "video_items": related.get("video_items") or [],
        "metadata": chapter_detail.get("metadata") or {},
    }
    missing = [
        label for label, value in [
            ("小节正文", retrieval["section_content"]),
            ("思维导图", retrieval["mind_map"]),
            ("练习题", retrieval["exercises"]),
            ("代码任务", retrieval["code_tasks"]),
            ("视频指南", retrieval["reading_video_guide"] or retrieval["video_items"]),
        ] if not value
    ]
    dto = AgentResultDTO(
        agent_name="ResourceGroundingAgent",
        input_summary=location.get("topic") or "数据结构与算法学习主题",
        output={
            "grounding": {
                "course_note": bool(retrieval["section_content"]),
                "mind_map": bool(retrieval["mind_map"]),
                "exercise_set": len(retrieval["exercises"]),
                "code_lab": len(retrieval["code_tasks"]),
                "video_guide": bool(retrieval["reading_video_guide"] or retrieval["video_items"]),
                "remediation_metadata": bool(retrieval["metadata"]),
            },
            "grounding_policy": "仅作为个性化生成依据，不直接作为学生端最终内容",
            "source_paths": [
                item for item in [
                    retrieval.get("section_path"),
                    retrieval.get("mind_map_path"),
                    retrieval.get("reading_video_guide_path"),
                    "banks/exercises.jsonl" if retrieval["exercises"] else "",
                    "banks/code_tasks.jsonl" if retrieval["code_tasks"] else "",
                    "banks/video_items.jsonl" if retrieval["video_items"] else "",
                    "metadata/*.json" if retrieval["metadata"] else "",
                ] if item
            ],
            "missing": missing,
        },
        evidence_refs=location.get("evidence_refs") or [],
        quality_score=1.0 if not missing else 0.75,
        warnings=[f"未匹配到：{'、'.join(missing)}"] if missing else [],
    )
    return {"dto": dto, "retrieval": retrieval}
