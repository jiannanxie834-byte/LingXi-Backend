RESOURCE_TYPES = [
    "专业课程讲解文档",
    "知识点思维导图",
    "不同类型练习题目",
    "拓展阅读材料",
    "多模态学习包",
    "错题诊断与学习反馈报告",
    "学科实践应用任务",
]


RESOURCE_REQUIREMENTS = {
    "专业课程讲解文档": ["学习目标", "核心概念", "例子", "常见误区", "复习提示"],
    "知识点思维导图": ["中心主题", "一级知识点", "关系说明", "易混点"],
    "不同类型练习题目": ["概念题", "应用题", "开放题", "参考答案", "错因提示"],
    "拓展阅读材料": ["中文优先资料", "适合学生的入口", "推荐顺序", "阅读目标"],
    "多模态学习包": ["文字讲解", "Mermaid 流程图", "代码注释案例", "分步题解", "PPT 页纲", "实践任务"],
    "错题诊断与学习反馈报告": ["薄弱点", "错因类型", "修复建议", "后续练习"],
    "学科实践应用任务": ["任务背景", "操作步骤", "提交物", "评价标准", "复盘问题"],
}


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
        if resource["type"] not in RESOURCE_TYPES:
            raise RuntimeError(f"资源规划第 {index} 项类型不受支持")
        if not isinstance(resource["requirements"], list) or not resource["requirements"]:
            raise RuntimeError(f"资源规划第 {index} 项 requirements 必须是非空列表")

    return plan


def run(plan, profile):
    topic = profile.get("topic") or profile.get("knowledge_topic") or "当前主题"
    intent = profile.get("intent") or profile.get("goal") or "综合学习"

    resource_plan = {
        "resources": [
            {
                "topic": topic,
                "title": f"{topic} {resource_type}",
                "type": resource_type,
                "summary": f"面向「{intent}」场景生成的 {resource_type}。",
                "requirements": RESOURCE_REQUIREMENTS[resource_type],
                "plan_title": plan.get("title", ""),
            }
            for resource_type in RESOURCE_TYPES
        ]
    }

    return _validate_resource_plan(resource_plan)
