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


def _step(title, objective, resource_focus, status="pending"):
    return {
        "title": title,
        "objective": objective,
        "resource_focus": resource_focus,
        "status": status,
    }


def run(profile, semantic_result=None):
    semantic_result = semantic_result or {}
    topic = profile.get("topic") or profile.get("knowledge_topic") or "当前主题"
    intent = profile.get("intent") or profile.get("goal") or "综合学习"
    subject_category = profile.get("subject_category") or semantic_result.get("subject_category") or "unknown"
    level = profile.get("level") or semantic_result.get("level") or "未确认"

    if subject_category == "unknown":
        return _validate_plan({
            "title": f"{topic} · 主题澄清路线",
            "steps": [
                _step("第 1 步：明确学习主题", "先确认具体课程、知识点或考试目标，避免生成错配资源。", ["学习主题澄清与水平诊断"], "active"),
                _step("第 2 步：完成基础水平诊断", "补充已学内容、目标水平和可投入时间。", ["错题诊断与学习反馈报告"]),
            ],
        })

    if subject_category == "foreign_language":
        title_prefix = f"{topic}基础学习路线" if level == "未确认" else f"{topic}{level}学习路线"
        return _validate_plan({
            "title": title_prefix,
            "steps": [
                _step("第 1 步：完成水平诊断", "确认发音、词汇、语法、阅读和听说基础。", ["错题诊断与学习反馈报告"], "active"),
                _step("第 2 步：建立发音和高频词汇基础", "学习基础发音、常用问候语和生活场景词汇。", ["专业课程讲解文档", "多模态学习包"]),
                _step("第 3 步：掌握基础语法结构", "学习名词阴阳性、冠词、基础动词变位和常用句型。", ["专业课程讲解文档", "知识点思维导图"]),
                _step("第 4 步：完成语言练习", "完成短文阅读、填空、翻译和口语情境题，记录错因。", ["不同类型练习题目", "错题诊断与学习反馈报告"]),
                _step("第 5 步：完成输出任务", "用一段自我介绍、点餐对话或校园问路完成听说读写输出训练。", ["学科实践应用任务", "多模态学习包"]),
            ],
        })

    if subject_category == "mathematics":
        return _validate_plan({
            "title": f"{topic}学习路线",
            "steps": [
                _step("第 1 步：确认前置知识", f"梳理学习 {topic} 所需的定义、公式和基础运算。", ["专业课程讲解文档"], "active"),
                _step("第 2 步：理解定义与公式", "把核心定义、公式含义和适用条件整理成结构图。", ["知识点思维导图"]),
                _step("第 3 步：完成例题拆解", "按步骤完成基础例题、推导题和应用题。", ["不同类型练习题目"]),
                _step("第 4 步：复盘错因", "记录公式误用、计算错误和审题偏差。", ["错题诊断与学习反馈报告"]),
            ],
        })

    if subject_category == "physics":
        return _validate_plan({
            "title": f"{topic}学习路线",
            "steps": [
                _step("第 1 步：建立物理图景", f"理解 {topic} 的现象、模型和基本变量。", ["专业课程讲解文档"], "active"),
                _step("第 2 步：掌握公式与实验", "梳理公式含义、适用条件和典型实验。", ["知识点思维导图", "多模态学习包"]),
                _step("第 3 步：完成计算和实验分析题", "通过分层练习定位概念混淆和公式误用。", ["不同类型练习题目"]),
                _step("第 4 步：完成应用任务", "结合真实现象或实验数据完成一次解释和复盘。", ["学科实践应用任务"]),
            ],
        })

    if subject_category == "computer_science":
        return _validate_plan({
            "title": f"{topic}学习路线",
            "steps": [
                _step("第 1 步：建立概念框架", f"明确 {topic} 的核心概念、适用场景和常见误区。", ["专业课程讲解文档", "知识点思维导图"], "active"),
                _step("第 2 步：拆解关键机制", "结合流程图、伪代码或代码注释理解关键过程。", ["多模态学习包", "专业课程讲解文档"]),
                _step("第 3 步：完成分层练习", "通过概念题、应用题和代码阅读题定位薄弱点。", ["不同类型练习题目", "错题诊断与学习反馈报告"]),
                _step("第 4 步：完成实践任务", "完成一个小实验、配置任务或代码案例，并记录复盘。", ["学科实践应用任务", "拓展阅读材料"]),
            ],
        })

    if subject_category == "general_course":
        return _validate_plan({
            "title": f"{topic}学习路线",
            "steps": [
                _step("第 1 步：明确核心概念", f"梳理 {topic} 的基本概念、背景和学习目标。", ["专业课程讲解文档"], "active"),
                _step("第 2 步：阅读案例材料", "通过案例、短文和关键词理解概念使用场景。", ["拓展阅读材料", "知识点思维导图"]),
                _step("第 3 步：完成讨论练习", "用概念题、案例分析题或开放题检查理解深度。", ["不同类型练习题目"]),
                _step("第 4 步：完成应用表达", "完成一份观点说明、案例分析或课堂展示提纲。", ["学科实践应用任务", "多模态学习包"]),
            ],
        })

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
