from typing import Dict, List


BASE_RESOURCE_TYPES = [
    "专业课程讲解文档",
    "知识点思维导图",
    "不同类型练习题目",
    "拓展阅读材料",
    "学科实践应用任务",
]

FEEDBACK_RESOURCE_TYPE = "错题诊断与学习反馈报告"
DEPRECATED_RESOURCE_TYPES = ["多模态学习包"]

PROGRAMMING_FORBIDDEN = [
    "代码注释案例",
    "伪代码",
    "函数",
    "Python",
    "PyTorch",
    "TensorFlow",
    "算法实现",
    "模型训练",
]

FOREIGN_LANGUAGE_SPECS = {
    "专业课程讲解文档": {
        "requirements": ["学习目标", "核心语法/词汇点", "例句", "中文解释", "常见错误", "小练习"],
        "quality_constraints": ["围绕词汇、语法、例句和语言使用场景", "不得生成代码或算法内容"],
    },
    "知识点思维导图": {
        "requirements": ["发音", "词汇", "语法", "阅读", "听力", "口语", "写作", "文化语境"],
        "quality_constraints": ["围绕语言能力结构展开", "不得用程序流程图替代语言学习导图"],
    },
    "不同类型练习题目": {
        "requirements": ["选择题", "填空题", "翻译题", "阅读理解题", "口语情境题", "参考答案", "解析"],
        "quality_constraints": ["练习题必须考查语言本身", "不得考查学习路线规划或资源适用性"],
    },
    "拓展阅读材料": {
        "requirements": ["标题", "阅读短文或外部来源条目", "关键词表", "理解题", "参考答案"],
        "quality_constraints": ["必须提供具体阅读内容或明确来源名称", "不得只泛泛建议阅读指南"],
    },
    "错题诊断与学习反馈报告": {
        "requirements": ["薄弱点", "错因类型", "纠正例句", "修复练习", "复盘建议"],
        "quality_constraints": ["诊断必须围绕语言错误，不得改写成学习计划评估题"],
    },
    "学科实践应用任务": {
        "requirements": ["情境任务", "表达模板", "提交物", "评价标准", "复盘问题"],
        "quality_constraints": ["任务可为自我介绍、点餐、问路、邮件写作或朗读复盘"],
    },
}

COMPUTER_SCIENCE_SPECS = {
    "专业课程讲解文档": ["学习目标", "核心概念", "例子", "常见误区", "复习提示"],
    "知识点思维导图": ["中心主题", "一级知识点", "关系说明", "易混点"],
    "不同类型练习题目": ["概念题", "应用题", "代码阅读题", "参考答案", "错因提示"],
    "拓展阅读材料": ["中文优先资料", "适合学生的入口", "推荐顺序", "阅读目标"],
    "错题诊断与学习反馈报告": ["薄弱点", "错因类型", "修复建议", "后续练习"],
    "学科实践应用任务": ["任务背景", "操作步骤", "提交物", "评价标准", "复盘问题"],
}

MATHEMATICS_SPECS = {
    "专业课程讲解文档": ["定义", "公式", "几何/直观解释", "例题", "常见误区"],
    "知识点思维导图": ["定义", "定理", "公式关系", "典型题型", "易错点"],
    "不同类型练习题目": ["基础计算题", "证明/推导题", "应用题", "参考答案", "解析"],
    "拓展阅读材料": ["章节导读", "例题阅读", "关键词", "理解题"],
    "错题诊断与学习反馈报告": ["薄弱公式", "错因类型", "修复题组", "复盘建议"],
    "学科实践应用任务": ["建模情境", "计算步骤", "提交物", "评价标准"],
}

PHYSICS_SPECS = {
    "专业课程讲解文档": ["物理图景", "核心概念", "公式含义", "典型例题", "常见误区"],
    "知识点思维导图": ["现象", "模型", "公式", "实验", "应用"],
    "不同类型练习题目": ["概念判断题", "计算题", "实验分析题", "参考答案", "解析"],
    "拓展阅读材料": ["现象短文", "实验材料", "关键词", "理解题"],
    "错题诊断与学习反馈报告": ["薄弱模型", "错因类型", "修复题组", "复盘建议"],
    "学科实践应用任务": ["实验背景", "操作步骤", "数据记录", "评价标准"],
}

GENERAL_SPECS = {
    "专业课程讲解文档": ["学习目标", "核心概念", "案例", "常见误区", "思考题"],
    "知识点思维导图": ["概念", "背景", "案例", "争议点", "应用"],
    "不同类型练习题目": ["概念题", "案例分析题", "开放讨论题", "参考答案"],
    "拓展阅读材料": ["短文", "关键词", "理解题", "延伸问题"],
    "错题诊断与学习反馈报告": ["薄弱点", "错因类型", "修复建议"],
    "学科实践应用任务": ["情境任务", "步骤", "提交物", "评价标准"],
}


def _generic_requirements(subject_category: str, resource_type: str) -> List[str]:
    catalog = {
        "computer_science": COMPUTER_SCIENCE_SPECS,
        "mathematics": MATHEMATICS_SPECS,
        "physics": PHYSICS_SPECS,
        "general_course": GENERAL_SPECS,
    }.get(subject_category, GENERAL_SPECS)
    return catalog.get(resource_type, ["学习目标", "核心内容", "示例", "练习", "复盘建议"])


def get_supported_resource_types(subject_category: str) -> List[str]:
    if subject_category == "unknown":
        return ["学习主题澄清与水平诊断"]
    return BASE_RESOURCE_TYPES


def get_resource_spec(subject_category: str, resource_type: str, topic: str, semantic_result: Dict) -> Dict:
    allow_code = bool(semantic_result.get("should_generate_code_content")) or subject_category == "computer_science"
    level = semantic_result.get("level") or "未确认"
    level_source = semantic_result.get("level_source") or "none"

    if subject_category == "foreign_language":
        spec = FOREIGN_LANGUAGE_SPECS.get(resource_type, {})
        requirements = spec.get("requirements") or ["语言学习目标", "例句", "练习", "复盘建议"]
        quality_constraints = spec.get("quality_constraints") or ["外语资源必须围绕语言能力"]
        forbidden_terms = PROGRAMMING_FORBIDDEN
    else:
        requirements = _generic_requirements(subject_category, resource_type)
        quality_constraints = ["练习题必须考查主题本身，不得改写成学习规划题"]
        forbidden_terms = [] if allow_code else PROGRAMMING_FORBIDDEN

    if level_source == "none":
        quality_constraints.append("学生水平未确认，不得写进阶、高阶、B1/B2/C1/C2 或已经具备")

    return {
        "topic": topic,
        "subject_category": subject_category,
        "resource_type": resource_type,
        "requirements": requirements,
        "quality_constraints": quality_constraints,
        "forbidden_terms": forbidden_terms,
        "allow_code_content": allow_code,
        "level": level,
        "level_source": level_source,
        "requires_human_review": True,
    }
