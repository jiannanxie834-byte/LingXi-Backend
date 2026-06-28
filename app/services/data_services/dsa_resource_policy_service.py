from app.services.data_services import resource_artifact_type_service as artifact_types


DEFAULT_DSA_LEARNING_PACKAGE_TYPES = [
    artifact_types.COURSE_NOTE,
    artifact_types.MIND_MAP,
    artifact_types.EXERCISE_SET,
    artifact_types.CODE_LAB,
    artifact_types.DIAGNOSTIC_REPORT,
    artifact_types.PERSONALIZED_VIDEO_GUIDE,
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
        artifact_types.DIAGNOSTIC_REPORT,
        artifact_types.PERSONALIZED_VIDEO_GUIDE,
        artifact_types.PROJECT_BRIEF,
    ],
    "remediation": DEFAULT_DSA_LEARNING_PACKAGE_TYPES,
    "diagnostic": DEFAULT_DSA_LEARNING_PACKAGE_TYPES,
}


def select_dsa_resource_types(context: dict) -> list[str]:
    context = context or {}
    scope_level = context.get("scope_level") or (context.get("dsa_course_map") or {}).get("scope_level") or "unit"
    resource_types = list(DSA_RESOURCE_POLICY_BY_SCOPE.get(scope_level) or DSA_RESOURCE_POLICY_BY_SCOPE["unit"])
    if context.get("requires_code") and artifact_types.CODE_LAB not in resource_types:
        resource_types.append(artifact_types.CODE_LAB)
    if context.get("requires_multimodal") and artifact_types.MIND_MAP not in resource_types:
        resource_types.append(artifact_types.MIND_MAP)
    return list(dict.fromkeys(resource_types))
