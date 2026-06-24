def _validate_plan(plan):
    if not plan.get("title"):
        raise RuntimeError("路径规划结果缺少 title")
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        raise RuntimeError("路径规划结果 steps 必须是非空列表")

    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise RuntimeError(f"路径规划第 {index} 步必须是对象")
        for field in ["title", "objective", "resource_focus", "status"]:
            if field not in step:
                raise RuntimeError(f"路径规划第 {index} 步缺少 {field}")
        if not isinstance(step["resource_focus"], list):
            raise RuntimeError(f"路径规划第 {index} 步 resource_focus 必须是列表")

    return plan


def run(profile):
    topic = profile.get("topic") or profile.get("knowledge_topic") or "当前主题"
    intent = profile.get("intent") or profile.get("goal") or "综合学习"

    plan = {
        "title": f"{topic} · {intent}路线",
        "steps": [
            {
                "title": "第 1 步",
                "objective": f"定位 {topic} 的核心概念和当前卡点",
                "resource_focus": ["专业课程讲解文档", "拓展阅读材料"],
                "status": "active",
            },
            {
                "title": "第 2 步",
                "objective": f"阅读 {topic} 的课程讲解并整理基础术语",
                "resource_focus": ["专业课程讲解文档", "知识点思维导图"],
                "status": "pending",
            },
            {
                "title": "第 3 步",
                "objective": "用知识点思维导图整理概念关系和易混点",
                "resource_focus": ["知识点思维导图"],
                "status": "pending",
            },
            {
                "title": "第 4 步",
                "objective": "完成分层练习题并记录错因",
                "resource_focus": ["不同类型练习题目", "错题诊断与学习反馈报告"],
                "status": "pending",
            },
            {
                "title": "第 5 步",
                "objective": "完成学科实践应用任务并提交复盘",
                "resource_focus": ["学科实践应用任务", "多模态学习包"],
                "status": "pending",
            },
        ],
    }

    return _validate_plan(plan)
