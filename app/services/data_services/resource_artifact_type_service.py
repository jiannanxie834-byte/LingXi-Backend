COURSE_NOTE = "课程讲解文档"
MIND_MAP = "知识点思维导图"
EXERCISE_SET = "练习题集"
READING_PACK = "拓展阅读包"
CODE_LAB = "代码实验"
PPT_OUTLINE = "PPT 大纲"
PPTX = "可导出 PPTX"
VIDEO_RECOMMENDATION = "外部公开视频推荐卡"
PERSONALIZED_VIDEO_GUIDE = "个性化视频观看指南"
INTERACTIVE_ANIMATION = "算法可视化动画规格"
ANIMATION_STORYBOARD = "动画分镜"
PROJECT_BRIEF = "算法项目任务书"
DIAGNOSTIC_REPORT = "诊断与补弱报告"

ACTIVE_ARTIFACT_TYPES = [
    COURSE_NOTE,
    MIND_MAP,
    EXERCISE_SET,
    READING_PACK,
    CODE_LAB,
    PPT_OUTLINE,
    VIDEO_RECOMMENDATION,
    PERSONALIZED_VIDEO_GUIDE,
    INTERACTIVE_ANIMATION,
    ANIMATION_STORYBOARD,
    PROJECT_BRIEF,
]

EXPORTABLE_ARTIFACT_TYPES = [
    PPTX,
]

EVENT_TRIGGERED_ARTIFACT_TYPES = [
    DIAGNOSTIC_REPORT,
]

DEPRECATED_ARTIFACT_TYPES = [
]

LEGACY_TYPE_MAPPING = {
    "PyTorch 实操案例": CODE_LAB,
    "交互动画规格": INTERACTIVE_ANIMATION,
    "课程实践项目任务书": PROJECT_BRIEF,
}

ARTIFACT_REQUIREMENTS = {
    COURSE_NOTE: ["学习目标", "前置知识", "核心概念", "直观解释", "公式/流程", "例子", "易错点", "小结", "下一步建议"],
    MIND_MAP: ["中心主题", "一级知识点", "前置关系", "易混点", "Mermaid mindmap 或 JSON 图结构"],
    EXERCISE_SET: ["选择题", "判断题", "简答题", "计算题", "代码补全题", "实验分析题", "项目任务题", "答案", "解析", "常见错误"],
    READING_PACK: ["教材章节建议", "公开课程建议", "官方文档建议", "论文方向建议", "博客/教程建议", "阅读顺序", "阅读目标"],
    CODE_LAB: ["实验目标", "环境依赖", "输入输出样例", "核心函数", "边界用例", "完整代码", "运行方式", "复杂度记录", "调试任务", "实验报告模板"],
    PPT_OUTLINE: ["封面", "学习目标", "知识背景", "核心概念", "图解过程", "代码示例", "练习题", "项目任务", "总结"],
    VIDEO_RECOMMENDATION: ["公开视频标题", "来源平台", "原始链接", "知识点标签", "建议观看片段", "观看优先级", "版权说明"],
    PERSONALIZED_VIDEO_GUIDE: ["观看前准备", "观看中关注点", "暂停思考问题", "观看后任务", "关联练习题", "关联代码实验", "关联交互动画"],
    INTERACTIVE_ANIMATION: ["animation_type", "可交互参数", "分步高亮", "同步解释", "前端渲染规格"],
    ANIMATION_STORYBOARD: ["分镜编号", "画面描述", "旁白", "字幕", "对应知识点"],
    PROJECT_BRIEF: ["项目背景", "项目目标", "输入输出约束", "算法路线", "任务拆解", "验收标准", "提交物", "评分 Rubric", "扩展方向"],
    DIAGNOSTIC_REPORT: ["薄弱点", "错因类型", "修复建议", "后续练习", "诊断依据"],
}

ARTIFACT_FORMATS = {
    COURSE_NOTE: "markdown",
    MIND_MAP: "mermaid",
    EXERCISE_SET: "markdown",
    READING_PACK: "markdown",
    CODE_LAB: "python_markdown",
    PPT_OUTLINE: "markdown",
    PPTX: "pptx",
    VIDEO_RECOMMENDATION: "json",
    PERSONALIZED_VIDEO_GUIDE: "json",
    INTERACTIVE_ANIMATION: "animation_spec",
    ANIMATION_STORYBOARD: "json",
    PROJECT_BRIEF: "markdown",
    DIAGNOSTIC_REPORT: "markdown",
}


def normalize_artifact_type(type_name: str) -> str:
    name = str(type_name or "").strip()
    return LEGACY_TYPE_MAPPING.get(name, name)


def is_deprecated(type_name: str) -> bool:
    name = str(type_name or "").strip()
    return name in DEPRECATED_ARTIFACT_TYPES or name.isdigit()


def is_supported(type_name: str, allow_event_triggered: bool = True) -> bool:
    normalized = normalize_artifact_type(type_name)
    supported = list(ACTIVE_ARTIFACT_TYPES) + list(EXPORTABLE_ARTIFACT_TYPES)
    if allow_event_triggered:
        supported += EVENT_TRIGGERED_ARTIFACT_TYPES
    return normalized in supported


def get_requirements(type_name: str):
    return ARTIFACT_REQUIREMENTS.get(normalize_artifact_type(type_name), [])


def get_format(type_name: str) -> str:
    return ARTIFACT_FORMATS.get(normalize_artifact_type(type_name), "markdown")


def all_public_types():
    return list(ACTIVE_ARTIFACT_TYPES) + list(EXPORTABLE_ARTIFACT_TYPES) + list(EVENT_TRIGGERED_ARTIFACT_TYPES)
