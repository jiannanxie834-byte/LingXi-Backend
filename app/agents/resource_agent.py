RESOURCE_TYPES = [
    "专业课程讲解文档",
    "知识点思维导图",
    "不同类型练习题目",
    "拓展阅读材料",
    "多模态学习包",
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

    if resource_type == "多模态学习包":
        return f"""# {topic} 多模态学习包

## 文字讲解
围绕「{topic}」先用文字建立基本概念，再用图示、代码注释、题解和任务完成迁移应用。

## Mermaid 流程图
```mermaid
flowchart TD
    A[提出学习问题] --> B[识别核心概念]
    B --> C[建立知识关系]
    C --> D[查看例题题解]
    D --> E[完成实践任务]
    E --> F[复盘错因并更新画像]
```

## 代码注释案例
```python
# 用伪代码表示学习过程，不限定具体编程课程
question = "{topic}"
concepts = extract_core_concepts(question)  # 提取核心概念
examples = match_examples(concepts)         # 匹配课程案例
feedback = diagnose_mistakes(examples)      # 根据练习结果生成反馈
```

## 分步题解
1. 先判断题目考查的是定义、关系还是应用。
2. 再列出已知条件和需要推导的目标。
3. 用课程中的核心概念解释每一步。
4. 最后检查是否存在概念混淆或条件遗漏。

## PPT 页结构
1. 学习目标：用一句话说明本节要解决的问题。
2. 概念图解：用流程图或关系图呈现「{topic}」的关键组成。
3. 场景案例：给出一个高校课程或真实任务中的应用场景。
4. 误区提醒：列出 2-3 个学生容易混淆的点。
5. 互动练习：设计一道可现场回答的检查题。

## 图解元素
- 主体对象：{topic}
- 关系箭头：概念之间的因果、包含或执行顺序
- 强调颜色：用于标出易错点和关键步骤

## 动画分镜
| 镜头 | 画面 | 字幕/讲解 |
| --- | --- | --- |
| 1 | 标题和学习目标出现 | 今天用一个案例理解 {topic} |
| 2 | 概念节点逐个展开 | 先建立整体框架，再看细节 |
| 3 | 错误示例与正确示例对比 | 这个差异是考试和实践中的高频失分点 |
| 4 | 练习题出现 | 用一道题检查是否真正掌握 |

## 生成建议
- 可直接导出为 PPT，也可复制 Mermaid 流程图继续制作图解。
- 若课堂演示时间有限，优先保留文字讲解、流程图、题解和实践任务。
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
