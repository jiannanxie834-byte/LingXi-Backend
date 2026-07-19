from app.services.data_services import resource_artifact_type_service as artifact_types
from app.services.data_services import video_catalog_service


DEFAULT_DSA_LEARNING_PACKAGE_TYPES = [
    artifact_types.COURSE_NOTE,
    artifact_types.MIND_MAP,
    artifact_types.EXERCISE_SET,
    artifact_types.CODE_LAB,
    artifact_types.INTERACTIVE_ANIMATION,
]

DSA_POST_EXERCISE_REMEDIATION_TYPES = [
    artifact_types.COURSE_NOTE,
    artifact_types.EXERCISE_SET,
    artifact_types.CODE_LAB,
    artifact_types.DIAGNOSTIC_REPORT,
]


DSA_RESOURCE_POLICY_BY_SCOPE = {
    "course": DEFAULT_DSA_LEARNING_PACKAGE_TYPES,
    "chapter": DEFAULT_DSA_LEARNING_PACKAGE_TYPES,
    "unit": DEFAULT_DSA_LEARNING_PACKAGE_TYPES,
    "concept": DEFAULT_DSA_LEARNING_PACKAGE_TYPES,
    "comparison": DEFAULT_DSA_LEARNING_PACKAGE_TYPES,
    "project": [
        artifact_types.COURSE_NOTE,
        artifact_types.MIND_MAP,
        artifact_types.EXERCISE_SET,
        artifact_types.CODE_LAB,
        artifact_types.PERSONALIZED_VIDEO_GUIDE,
        artifact_types.PROJECT_BRIEF,
    ],
    "remediation": DSA_POST_EXERCISE_REMEDIATION_TYPES,
    "diagnostic": DSA_POST_EXERCISE_REMEDIATION_TYPES,
}


def select_dsa_resource_types(context: dict) -> list[str]:
    context = context or {}
    scope_level = context.get("scope_level") or (context.get("dsa_course_map") or {}).get("scope_level") or "unit"
    resource_types = list(DSA_RESOURCE_POLICY_BY_SCOPE.get(scope_level) or DSA_RESOURCE_POLICY_BY_SCOPE["unit"])
    course_map = context.get("dsa_course_map") or context.get("ai_course_map") or {}
    topic_text = " ".join([
        str(context.get("topic") or ""),
        str(context.get("display_topic") or ""),
        str(course_map.get("normalized_topic") or ""),
        str(course_map.get("display_topic") or ""),
        str(course_map.get("unit_id") or ""),
    ]).lower()
    is_dynamic_programming = "动态规划" in topic_text or "dsa_dp" in topic_text

    videos = video_catalog_service.search_videos(
        unit_id=course_map.get("unit_id") or context.get("primary_unit_id") or "",
        topic=context.get("display_topic") or context.get("topic") or course_map.get("normalized_topic") or "",
        chapter_id=course_map.get("chapter_id") or "",
        section_id=course_map.get("section_id") or "",
        unit_ids=course_map.get("unit_ids") or [],
        limit=1,
    )
    has_real_video = any(
        str(item.get("source_url") or "").startswith(("http://", "https://"))
        for item in videos
    )

    replacement_type = (
        artifact_types.INTERACTIVE_ANIMATION
        if is_dynamic_programming
        else artifact_types.PERSONALIZED_VIDEO_GUIDE
        if has_real_video
        else artifact_types.READING_PACK
    )
    resource_types = [
        replacement_type if resource_type == artifact_types.INTERACTIVE_ANIMATION else resource_type
        for resource_type in resource_types
    ]
    if not has_real_video:
        resource_types = [
            artifact_types.READING_PACK
            if resource_type == artifact_types.PERSONALIZED_VIDEO_GUIDE
            else resource_type
            for resource_type in resource_types
        ]
    if context.get("requires_code") and artifact_types.CODE_LAB not in resource_types:
        resource_types.append(artifact_types.CODE_LAB)
    if context.get("requires_multimodal") and artifact_types.MIND_MAP not in resource_types:
        resource_types.append(artifact_types.MIND_MAP)
    return list(dict.fromkeys(resource_types))
