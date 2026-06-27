from app.services.data_services import (
    course_scope_service,
    deep_learning_course_map_service,
    resource_artifact_type_service as artifact_types,
    resource_policy_service,
    resource_spec_service,
)


ACTIVE_RESOURCE_TYPES = artifact_types.ACTIVE_ARTIFACT_TYPES
FEEDBACK_RESOURCE_TYPE = artifact_types.DIAGNOSTIC_REPORT
DEPRECATED_RESOURCE_TYPES = artifact_types.DEPRECATED_ARTIFACT_TYPES
SUPPORTED_RESOURCE_TYPES = (
    ACTIVE_RESOURCE_TYPES
    + artifact_types.EXPORTABLE_ARTIFACT_TYPES
    + artifact_types.EVENT_TRIGGERED_ARTIFACT_TYPES
)


def _validate_resource_plan(plan):
    resources = plan.get("resources")
    if not isinstance(resources, list) or not resources:
        raise RuntimeError("资源规划结果 resources 必须是非空列表")

    for index, resource in enumerate(resources, start=1):
        if not isinstance(resource, dict):
            raise RuntimeError(f"资源规划第 {index} 项必须是对象")
        for field in ["topic", "title", "type", "summary", "requirements"]:
            if field not in resource:
                raise RuntimeError(f"资源规划第 {index} 项缺少 {field}")

        resource["type"] = artifact_types.normalize_artifact_type(resource["type"])
        if resource["type"] in DEPRECATED_RESOURCE_TYPES:
            raise RuntimeError(f"资源规划第 {index} 项类型已停用，不应由 AI 新生成")
        if resource["type"] not in SUPPORTED_RESOURCE_TYPES:
            raise RuntimeError(f"资源规划第 {index} 项类型不受支持：{resource['type']}")
        if not isinstance(resource["requirements"], list) or not resource["requirements"]:
            raise RuntimeError(f"资源规划第 {index} 项 requirements 必须是非空列表")
        if not resource.get("unit_id"):
            raise RuntimeError(f"资源规划第 {index} 项必须绑定深度学习知识单元 unit_id")

    return plan


def _unknown_topic_plan(topic, plan_title, semantic_result):
    return _validate_resource_plan({
        "semantic_result": semantic_result,
        "generation_context": {},
        "resources": [
            {
                "topic": topic,
                "title": f"{topic} 学习主题澄清与深度学习基础诊断",
                "type": artifact_types.EXERCISE_SET,
                "summary": "用于先确认学习主题、目标和当前基础，避免生成错配资源。",
                "requirements": ["学习主题", "目标水平", "已有基础", "诊断问题", "下一步建议"],
                "plan_title": plan_title,
                "subject_category": "unknown",
                "level": "未确认",
                "level_source": "none",
                "requires_human_review": True,
                "quality_constraints": ["未知主题不得批量生成资源", "这是入门自测题，不是诊断与补弱报告"],
                "allow_code_content": False,
                "course_id": "",
                "chapter_id": "",
                "unit_id": "dl_intro_diagnosis",
                "content_format": artifact_types.get_format(artifact_types.EXERCISE_SET),
            }
        ],
    })


def run(plan, profile, semantic_result=None, generation_context=None):
    semantic_result = semantic_result or {}
    generation_context = generation_context or {}
    topic = course_scope_service.normalize_course_topic(
        semantic_result.get("display_topic")
        or profile.get("topic")
        or profile.get("knowledge_topic")
        or semantic_result.get("normalized_topic")
        or semantic_result.get("topic")
        or "当前主题"
    )
    intent = profile.get("intent") or profile.get("goal") or semantic_result.get("learning_need_type") or "综合学习"
    subject_category = profile.get("subject_category") or semantic_result.get("subject_category") or "unknown"
    course_match = (
        semantic_result.get("deep_learning_course_map")
        or semantic_result.get("ai_course_map")
        or deep_learning_course_map_service.match_deep_learning_topic(topic)
    )

    if subject_category == "unknown" or not course_match.get("matched"):
        return _unknown_topic_plan(topic, plan.get("title", ""), semantic_result)

    policy_context = {
        **generation_context,
        "intent": intent,
        "topic": topic,
        "subject_category": subject_category,
        "deep_learning_course_map": course_match,
        "display_topic": semantic_result.get("display_topic") or course_match.get("display_topic") or topic,
        "scope_level": semantic_result.get("scope_level") or course_match.get("scope_level") or "",
        "primary_unit_id": semantic_result.get("primary_unit_id") or course_match.get("primary_unit_id") or "",
        "chapter_title": semantic_result.get("chapter_title") or course_match.get("chapter_title") or course_match.get("chapter") or "",
        "prerequisite_units": semantic_result.get("prerequisite_units", []),
        "related_units": semantic_result.get("related_units", []),
        "compare_units": semantic_result.get("compare_units", []),
        "expansion_policy": semantic_result.get("expansion_policy") or course_match.get("expansion_policy") or "",
        "should_generate_full_chapter": bool(semantic_result.get("should_generate_full_chapter") or course_match.get("should_generate_full_chapter")),
        "learning_need_type": semantic_result.get("learning_need_type") or course_match.get("learning_need_type"),
        "requires_code": bool(semantic_result.get("requires_code") or course_match.get("requires_code")),
        "requires_multimodal": bool(semantic_result.get("requires_multimodal") or course_match.get("requires_multimodal")),
    }
    resource_types = resource_policy_service.select_resource_types(policy_context)

    resource_plan = {
        "semantic_result": {
            **semantic_result,
            "deep_learning_course_map": course_match,
            "ai_course_map": course_match,
        },
        "generation_context": policy_context,
        "deep_learning_course_map": course_match,
        "resources": [
            _build_resource_item(
                topic=topic,
                intent=intent,
                resource_type=resource_type,
                plan_title=plan.get("title", ""),
                profile=profile,
                semantic_result=semantic_result,
                subject_category=subject_category,
                generation_context=policy_context,
                course_match=course_match,
            )
            for resource_type in resource_types
        ],
    }

    return _validate_resource_plan(resource_plan)


def _title_for_resource(topic, resource_type, course_match):
    display_topic = course_match.get("display_topic") or topic or course_match.get("normalized_topic") or "深度学习主题"
    return f"{display_topic} · {resource_type}"


def _summary_for_resource(resource_type, course_match, intent):
    unit_title = course_match.get("display_topic") or course_match.get("normalized_topic") or course_match.get("topic") or "深度学习知识点"
    chapter = course_match.get("chapter") or "《深度学习》课程"
    summary_map = {
        artifact_types.COURSE_NOTE: f"围绕「{unit_title}」生成面向学生的课程讲解，覆盖前置知识、核心概念、公式流程和易错点。",
        artifact_types.MIND_MAP: f"把「{unit_title}」的前置关系、核心概念和常见误区组织成可视化知识结构。",
        artifact_types.EXERCISE_SET: f"为「{unit_title}」生成分层题组，包含答案、解析、知识点和常见错误。",
        artifact_types.READING_PACK: f"整理「{unit_title}」对应的教材章节、公开视频/公开课入口、官方文档和阅读顺序。",
        artifact_types.CODE_LAB: f"提供与「{unit_title}」匹配的 PyTorch 实验指导、代码骨架、运行方式和调参任务。",
        artifact_types.PPT_OUTLINE: f"生成可用于课堂展示或演示视频的「{unit_title}」PPT 大纲。",
        artifact_types.VIDEO_RECOMMENDATION: f"从公开视频目录中匹配「{unit_title}」学习入口，只保存原始链接和观看建议。",
        artifact_types.PERSONALIZED_VIDEO_GUIDE: f"依据学生画像生成「{unit_title}」观看前、中、后的个性化学习指南。",
        artifact_types.INTERACTIVE_ANIMATION: f"生成「{unit_title}」交互动画规格，用于前端渲染卷积、反传或注意力过程。",
        artifact_types.ANIMATION_STORYBOARD: f"生成「{unit_title}」动画分镜，便于 PPT、演示视频和可视化说明使用。",
        artifact_types.PROJECT_BRIEF: f"围绕「{unit_title}」设计深度学习课程项目任务书、验收标准和评分 Rubric。",
        artifact_types.DIAGNOSTIC_REPORT: f"基于真实评价或错题反馈生成「{unit_title}」诊断与补弱报告。",
    }
    return summary_map.get(resource_type, f"面向「{intent}」场景生成的 {resource_type}。")


def _build_resource_item(topic, intent, resource_type, plan_title, profile, semantic_result, subject_category, generation_context, course_match):
    resource_type = artifact_types.normalize_artifact_type(resource_type)
    spec = resource_spec_service.get_resource_spec(
        subject_category=subject_category,
        resource_type=resource_type,
        topic=topic,
        semantic_result=semantic_result,
    )
    unit = course_match.get("unit") or {}
    display_topic = semantic_result.get("display_topic") or course_match.get("display_topic") or topic
    scope_level = semantic_result.get("scope_level") or course_match.get("scope_level") or ""
    return {
        "topic": display_topic,
        "title": _title_for_resource(topic, resource_type, course_match),
        "type": resource_type,
        "summary": _summary_for_resource(resource_type, course_match, intent),
        "requirements": spec.get("requirements") or artifact_types.get_requirements(resource_type),
        "plan_title": plan_title,
        "subject_category": subject_category,
        "level": profile.get("level", "未确认"),
        "level_source": profile.get("level_source", "none"),
        "requires_human_review": True,
        "quality_constraints": spec.get("quality_constraints", []),
        "forbidden_terms": spec.get("forbidden_terms", []),
        "allow_code_content": spec.get("allow_code_content", False),
        "content_format": spec.get("content_format") or artifact_types.get_format(resource_type),
        "course_id": course_match.get("course_id") or deep_learning_course_map_service.COURSE_ID,
        "chapter_id": course_match.get("chapter_id") or unit.get("chapter_id") or "",
        "chapter": course_match.get("chapter") or "",
        "unit_id": course_match.get("unit_id") or unit.get("unit_id") or "",
        "unit_title": display_topic,
        "display_topic": display_topic,
        "scope_level": scope_level,
        "primary_unit_id": semantic_result.get("primary_unit_id") or course_match.get("primary_unit_id") or course_match.get("unit_id") or unit.get("unit_id") or "",
        "chapter_title": semantic_result.get("chapter_title") or course_match.get("chapter_title") or course_match.get("chapter") or "",
        "prerequisite_units": semantic_result.get("prerequisite_units", []),
        "related_units": semantic_result.get("related_units", []),
        "compare_units": semantic_result.get("compare_units", []),
        "expansion_policy": semantic_result.get("expansion_policy") or course_match.get("expansion_policy") or "",
        "should_generate_full_chapter": bool(semantic_result.get("should_generate_full_chapter") or course_match.get("should_generate_full_chapter")),
        "evidence_refs": [course_match.get("unit_id") or unit.get("unit_id") or ""],
        "personalization_reason": _build_personalization_reason(profile, semantic_result, course_match),
        "feedback_evidence_sources": generation_context.get("evidence_sources", []),
        "deep_learning_course_map": course_match,
        "ai_course_map": course_match,
    }


def _build_personalization_reason(profile, semantic_result, course_match):
    fragments = []
    level = semantic_result.get("level") or profile.get("level")
    if level and level != "未确认":
        fragments.append(f"当前水平：{level}")
    if semantic_result.get("requires_multimodal"):
        fragments.append("偏向图解/多模态表达")
    if semantic_result.get("requires_code") or semantic_result.get("should_generate_code_content"):
        fragments.append("本轮需求包含代码或实验目标")
    need_type = semantic_result.get("learning_need_type") or course_match.get("learning_need_type")
    if need_type:
        fragments.append(f"学习需求：{need_type}")
    return "；".join(fragments) or "依据本轮学习主题和课程知识单元生成。"
