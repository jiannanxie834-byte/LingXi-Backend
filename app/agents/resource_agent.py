RESOURCE_TYPES = [
    "专业课程讲解文档",
    "知识点思维导图",
    "不同类型练习题目",
    "拓展阅读材料",
    "错题诊断与学习反馈报告",
    "学科实践应用任务",
]


def _resource_content(resource_type: str, topic: str, intent: str):
    if resource_type == "知识点思维导图":
        return f"""# {topic} 知识点思维导图

- 核心概念
- 常见误区
- 典型题型
- 实践应用
- 复盘反馈
"""

    if resource_type == "不同类型练习题目":
        return f"""# {topic} 分层练习题

1. 概念判断题：解释 {topic} 的核心定义。
2. 应用分析题：结合真实场景说明 {topic} 的使用条件。
3. 开放实践题：完成一个小任务，并写出错因复盘。
"""

    if resource_type == "学科实践应用任务":
        return f"""# {topic} 学科实践应用任务

## 任务目标
围绕「{topic}」完成一次可提交、可复盘的学科应用任务。

## 产出要求
- 过程记录
- 关键结论
- 遇到的问题
- 下一轮改进计划
"""

    if resource_type == "错题诊断与学习反馈报告":
        return f"""# {topic} 学习反馈报告

当前学习意图：{intent}

## 可能薄弱点
- 核心概念掌握不够稳定
- 做题后缺少错因归纳
- 实践应用和知识点之间的对应关系还需要强化
"""

    if resource_type == "拓展阅读材料":
        return f"""# {topic} 拓展阅读材料

建议先阅读课程讲义中的基础定义，再阅读一个完整案例，最后对照练习题进行查漏补缺。
"""

    return f"""# {topic} 个性化讲解文档

围绕「{topic}」建立概念、例子、练习和反馈的学习闭环。建议先理解核心概念，再通过练习和实践任务验证。
"""


def run(plan, profile):
    topic = profile.get("topic") or profile.get("knowledge_topic") or "当前主题"
    intent = profile.get("intent") or profile.get("goal") or "综合学习"

    return {
        "resources": [
            {
                "topic": topic,
                "title": f"{topic} {resource_type}",
                "type": resource_type,
                "summary": f"面向「{intent}」场景生成的 {resource_type}。",
                "content": _resource_content(resource_type, topic, intent),
                "source": "资源生成 Agent",
                "agent_notes": f"由资源生成 Agent 基于主题「{topic}」和意图「{intent}」生成，建议管理员审核术语、题目和实践要求。",
            }
            for resource_type in RESOURCE_TYPES
        ]
    }
