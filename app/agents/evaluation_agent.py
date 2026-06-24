from app.services.llm_provider import chat_json


INTENTS = {
    "概念讲解",
    "路径规划",
    "生成资源",
    "练习巩固",
    "实操训练",
    "综合学习",
}

INTENT_ALIASES = {
    "制定计划": "路径规划",
    "学习路径": "路径规划",
    "学习规划": "路径规划",
    "复习规划": "路径规划",
    "资源生成": "生成资源",
    "资料生成": "生成资源",
    "刷题训练": "练习巩固",
    "错题诊断": "练习巩固",
    "实践应用": "实操训练",
    "项目实践": "实操训练",
}

def _normalize_intent(intent: str):
    normalized = (intent or "").strip()
    normalized = INTENT_ALIASES.get(normalized, normalized)
    return normalized if normalized in INTENTS else ""


def _infer_by_llm(message: str):
    prompt = f"""
你是学习平台内部的意图识别工具。请根据学生输入判断学习意图和学科主题。

输出边界：
- 只输出 JSON 对象
- 不输出解释
- 不输出思考过程
- 不面向学生说话
- 不输出 Markdown 代码块

学生输入：
{message}

意图只能从以下选项选择一个：
- 概念讲解
- 路径规划
- 生成资源
- 练习巩固
- 实操训练
- 综合学习

主题要求：
- 如果能识别具体课程或知识点，返回简短主题，例如“计算机网络”“数据库索引”“三次握手”。
- 当输入是“我要学习/我想学/想了解/准备学 + 学科、课程或方向”时，必须把后面的学科、课程或方向作为 topic，例如“我要学习信息安全”的 topic 是“信息安全”。
- 如果完全无法判断，topic 返回空字符串，confidence 不超过 30。

判断要求：
- 当学生表达想开始学习某个学科、课程或方向时，intent 优先选择“路径规划”。
- 当学生要求资料、课件、题库、学习包、PPT、导图时，intent 选择“生成资源”。
- 当学生询问概念、原理、区别、为什么时，intent 选择“概念讲解”。
- 当学生要求做题、刷题、错题、测试时，intent 选择“练习巩固”。
- 当学生要求项目、实验、代码、实践任务时，intent 选择“实操训练”。
- 只有在没有明确动作，只是泛泛聊天时，才选择“综合学习”。

示例：
- 输入“我要学习信息安全”，返回 {{"intent":"路径规划","topic":"信息安全","confidence":90}}
- 输入“我想学习数据库索引”，返回 {{"intent":"路径规划","topic":"数据库索引","confidence":90}}
- 输入“帮我生成机器学习的练习题”，返回 {{"intent":"生成资源","topic":"机器学习","confidence":90}}

JSON 字段：
{{
  "intent": "路径规划",
  "topic": "计算机网络",
  "confidence": 80
}}
"""

    result = chat_json(
        [{"role": "user", "content": prompt}],
        required_fields=["intent", "topic", "confidence"],
        temperature=0.1,
        max_tokens=800
    )

    if not result.get("ok"):
        raise RuntimeError(f"意图识别结构化输出失败：{result.get('error', '未知错误')}")

    data = result.get("data") or {}
    intent = _normalize_intent(data.get("intent", ""))
    if not intent:
        raise RuntimeError("意图识别结果不在允许范围内")

    topic = (data.get("topic") or "").strip()[:40]

    try:
        confidence = int(data.get("confidence"))
    except (TypeError, ValueError):
        raise RuntimeError("意图识别结果缺少可信度分数")

    return {
        "intent": intent,
        "topic": topic,
        "score": max(0, min(100, confidence)),
    }


def run(message: str):
    llm_result = _infer_by_llm(message)

    return {
        "intent": llm_result["intent"],
        "topic": llm_result["topic"],
        "score": llm_result["score"],
        "intent_source": "llm",
        "topic_source": "llm",
    }
