from typing import Dict, List

from app.services.data_services import (
    dsa_resource_blueprint,
    resource_artifact_type_service as artifact_types,
)


BASE_RESOURCE_TYPES = artifact_types.ACTIVE_ARTIFACT_TYPES
FEEDBACK_RESOURCE_TYPE = artifact_types.DIAGNOSTIC_REPORT
DEPRECATED_RESOURCE_TYPES = artifact_types.DEPRECATED_ARTIFACT_TYPES

PROGRAMMING_FORBIDDEN = [
    "Python",
    "TensorFlow",
    "代码",
    "函数",
    "类定义",
    "模型训练",
]


def _base_course_constraints(resource_type: str, semantic_result: Dict) -> List[str]:
    constraints = [
        "必须属于当前课程范围，并绑定 chapter_id 与 unit_id",
        "必须体现课程知识单元的核心概念、前置知识、常见误区或实践任务",
        "不得虚构教材、MOOC、论文或视频链接",
        "视频类资源只提供原始公开入口和观看建议，不下载、不搬运、不重新托管",
        "个性化原因必须来自学生画像、学习目标、本轮输入或评价记录，不得凭空推断",
    ]
    if resource_type == artifact_types.EXERCISE_SET:
        constraints.append("练习题必须包含题干、答案、解析、对应知识点、难度和常见错误")
    if resource_type == artifact_types.READING_PACK:
        constraints.append("阅读包必须给出阅读顺序、阅读目标和可核验的公开入口或教材章节建议")
    if resource_type == artifact_types.CODE_LAB:
        constraints.append("代码实验必须说明运行方式、依赖、输入输出样例、复杂度记录、调试任务和实验报告模板")
    if resource_type in {artifact_types.INTERACTIVE_ANIMATION, artifact_types.ANIMATION_STORYBOARD}:
        constraints.append("动画资源必须输出结构化规格或分镜，不要求生成 MP4")
    if resource_type == artifact_types.VIDEO_RECOMMENDATION:
        constraints.append("必须写明 copyright_note：仅提供原始链接和学习建议，不复制、不下载、不重新分发视频内容")
    if semantic_result.get("level_source") == "none":
        constraints.append("学生水平未确认时，不得写进阶、高阶或已经具备相关基础")
    return constraints


def get_supported_resource_types(subject_category: str) -> List[str]:
    return list(BASE_RESOURCE_TYPES)


def get_resource_spec(subject_category: str, resource_type: str, topic: str, semantic_result: Dict) -> Dict:
    normalized_type = artifact_types.normalize_artifact_type(resource_type)
    requirements = artifact_types.get_requirements(normalized_type)
    if not requirements:
        requirements = ["学习目标", "核心内容", "例子", "练习", "复盘建议"]

    subject_category = subject_category or semantic_result.get("subject_category") or "unknown"
    semantic_result = semantic_result or {}
    deep_spec = {}
    if dsa_resource_blueprint.is_dsa_context(subject_category, semantic_result):
        deep_spec = dsa_resource_blueprint.get_dsa_spec(normalized_type)
        if deep_spec.get("requirements"):
            requirements = deep_spec["requirements"]

    allow_code = normalized_type == artifact_types.CODE_LAB or bool(
        semantic_result.get("should_generate_code_content")
        or semantic_result.get("requires_code")
    )
    forbidden_terms = [] if allow_code else PROGRAMMING_FORBIDDEN
    quality_constraints = [
        *_base_course_constraints(normalized_type, semantic_result),
        *(deep_spec.get("quality_constraints") or []),
    ]

    return {
        "topic": topic,
        "subject_category": subject_category,
        "resource_type": normalized_type,
        "content_format": artifact_types.get_format(normalized_type),
        "requirements": requirements,
        "quality_constraints": list(dict.fromkeys(quality_constraints)),
        "forbidden_terms": forbidden_terms,
        "allow_code_content": allow_code,
        "level": semantic_result.get("level") or "未确认",
        "level_source": semantic_result.get("level_source") or "none",
        "requires_human_review": True,
    }
