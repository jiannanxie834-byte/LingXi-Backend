from app.services.llm_provider import chat_json
from app.services.data_services import course_scope_service


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


TOPIC_KEYWORDS = [
    ("深度学习", ["深度学习", "deep learning", "神经网络"]),
    ("卷积神经网络", ["cnn", "卷积神经网络", "卷积", "卷积层", "卷积核", "池化", "图像分类"]),
    ("反向传播", ["反向传播", "bp", "backprop", "backpropagation", "链式法则", "梯度"]),
    ("优化算法", ["sgd", "momentum", "adam", "优化器", "学习率", "训练曲线"]),
    ("正则化", ["正则化", "dropout", "batchnorm", "数据增强", "过拟合", "泛化"]),
    ("RNN/LSTM/GRU", ["rnn", "lstm", "gru", "循环神经网络", "序列模型", "门控机制"]),
    ("Transformer", ["transformer", "attention", "注意力机制", "自注意力", "多头注意力", "qkv", "位置编码"]),
    ("生成模型", ["自编码器", "vae", "gan", "扩散模型", "diffusion", "生成模型"]),
    ("PyTorch 深度学习工程实践", ["pytorch", "torch", "dataset", "dataloader", "训练循环", "代码实验"]),
    ("深度学习课程综合项目", ["课程项目", "综合项目", "图像分类项目", "文本分类项目", "时间序列预测项目"]),
]


def _compact(text: str):
    return "".join(str(text or "").lower().split())


def _infer_topic_by_rule(message: str):
    compact = _compact(message)
    for topic, aliases in TOPIC_KEYWORDS:
        if any(_compact(alias) in compact for alias in aliases):
            return course_scope_service.normalize_course_topic(topic)
    return ""


def _infer_intent_by_rule(message: str):
    compact = _compact(message)
    if any(word in compact for word in ["练习", "刷题", "题目", "测试", "错题"]):
        return "练习巩固"
    if any(word in compact for word in ["资源", "资料", "课件", "ppt", "导图"]):
        return "生成资源"
    if any(word in compact for word in ["代码", "项目", "实验", "实操", "实践"]):
        return "实操训练"
    if any(word in compact for word in ["规划", "路线", "计划", "学习一下", "想学习", "我要学习", "想学", "入门"]):
        return "路径规划"
    if any(word in compact for word in ["是什么", "什么意思", "解释", "介绍", "原理"]):
        return "概念讲解"
    return ""


def _normalize_intent(intent: str):
    normalized = (intent or "").strip()
    normalized = INTENT_ALIASES.get(normalized, normalized)
    return normalized if normalized in INTENTS else ""


def _infer_by_llm(message: str):
    prompt = f"""
你是《深度学习》课程学习平台内部的意图识别工具。请根据学生输入判断学习意图和深度学习课程主题。

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
- 如果能识别具体课程知识点，返回简短主题，例如“CNN”“反向传播”“Transformer”“PyTorch 图像分类实验”。
- 当输入是“我要学习/我想学/想了解/准备学 + 深度学习知识点”时，必须把后面的知识点作为 topic。
- 如果完全无法判断，topic 返回“未确认主题”，confidence 不超过 50。
- 不得把未知主题默认成“深度学习”。

判断要求：
- 当学生表达想开始学习某个学科、课程或方向时，intent 优先选择“路径规划”。
- 当学生要求资料、课件、题库、学习包、PPT、导图时，intent 选择“生成资源”。
- 当学生询问概念、原理、区别、为什么时，intent 选择“概念讲解”。
- 当学生要求做题、刷题、错题、测试时，intent 选择“练习巩固”。
- 当学生要求项目、实验、代码、实践任务时，intent 选择“实操训练”。
- 只有在没有明确动作，只是泛泛聊天时，才选择“综合学习”。

示例：
- 输入“我要学习 CNN”，返回 {{"intent":"路径规划","topic":"CNN","confidence":90}}
- 输入“我不懂反向传播”，返回 {{"intent":"概念讲解","topic":"反向传播","confidence":90}}
- 输入“帮我生成 Transformer 的练习题”，返回 {{"intent":"生成资源","topic":"Transformer","confidence":90}}

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

    topic = course_scope_service.normalize_course_topic((data.get("topic") or "").strip()[:40])

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
    topic_by_rule = _infer_topic_by_rule(message)
    intent_by_rule = _infer_intent_by_rule(message)
    if topic_by_rule and intent_by_rule:
        return {
            "intent": intent_by_rule,
            "topic": topic_by_rule,
            "score": 90,
            "intent_source": "rule",
            "topic_source": "rule",
        }

    llm_result = _infer_by_llm(message)
    topic = course_scope_service.normalize_course_topic(llm_result["topic"] or "未确认主题")
    if topic == course_scope_service.PRIMARY_COURSE_DISPLAY_NAME and not _infer_topic_by_rule(message):
        topic = "未确认主题"

    return {
        "intent": llm_result["intent"],
        "topic": topic,
        "score": llm_result["score"] if topic != "未确认主题" else min(llm_result["score"], 50),
        "intent_source": "llm",
        "topic_source": "llm" if topic != "未确认主题" else "unknown",
    }
