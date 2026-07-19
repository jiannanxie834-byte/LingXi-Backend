from app.services.data_services import resource_artifact_type_service as artifact_types


DSA_RESOURCE_TYPE_ALIASES = {
    "course_note": artifact_types.COURSE_NOTE,
    "mind_map": artifact_types.MIND_MAP,
    "exercise_set": artifact_types.EXERCISE_SET,
    "code_lab": artifact_types.CODE_LAB,
    "visual_explanation": artifact_types.MIND_MAP,
    "comparison_table": artifact_types.COURSE_NOTE,
    "project_brief": artifact_types.PROJECT_BRIEF,
    "learning_path": artifact_types.COURSE_NOTE,
    "remediation_report": artifact_types.DIAGNOSTIC_REPORT,
    "video_recommendation": artifact_types.VIDEO_RECOMMENDATION,
    "personalized_guide": artifact_types.PERSONALIZED_VIDEO_GUIDE,
    "ppt_outline": artifact_types.PPT_OUTLINE,
}


def is_dsa_context(subject_category: str, semantic_result: dict) -> bool:
    semantic_result = semantic_result or {}
    return (
        semantic_result.get("course_id") == "data_structures_algorithms"
        or bool(semantic_result.get("dsa_course_map"))
        or subject_category == "computer_science"
    )


def get_dsa_spec(resource_type: str) -> dict:
    resource_type = artifact_types.normalize_artifact_type(resource_type)
    base = {
        "quality_constraints": [
            "必须属于《数据结构与算法》课程范围，并绑定 chapter_id 与 unit_id",
            "本阶段只允许输出框架、结构和占位要求，不生成正式课程正文",
            "不得复制外部教材、题库或 LeetCode 题目原文",
            "主要生成内容不得偏离课程主题",
        ],
    }
    if resource_type == artifact_types.CODE_LAB:
        base["requirements"] = ["实验目标", "输入输出样例", "核心函数占位", "边界用例 TODO", "复杂度记录 TODO", "调试任务 TODO"]
    if resource_type == artifact_types.EXERCISE_SET:
        base["requirements"] = ["题型规划", "知识点覆盖表", "难度层级 TODO", "正式题目待后续导入"]
    return base
