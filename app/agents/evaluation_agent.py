import json
import re

from app.services.llm_provider import chat


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
    ("计算机网络", ["计网", "网络", "tcp", "udp", "三次握手", "四次挥手", "http", "https"]),
    ("Python 数据分析", ["python", "pandas", "数据分析", "numpy", "可视化", "matplotlib"]),
    ("人工智能导论", ["人工智能", "机器学习", "深度学习", "模型", "神经网络", "分类", "训练"]),
    ("高等数学", ["数学", "高数", "微积分", "导数", "积分", "极限", "函数", "建模"]),
    ("大学物理", ["物理", "力学", "电磁", "实验", "速度", "加速度", "牛顿", "能量"]),
    ("大学英语", ["英语", "阅读", "写作", "作文", "口语", "听力", "翻译", "词汇"]),
]


def _normalize_intent(intent: str):
    normalized = (intent or "").strip()
    normalized = INTENT_ALIASES.get(normalized, normalized)
    return normalized if normalized in INTENTS else "综合学习"


def _infer_topic_by_rules(message: str):
    lowered = (message or "").lower()
    for topic, keywords in TOPIC_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return topic, True
    return "人工智能导论", False


def _infer_intent_by_rules(message: str):
    text = message or ""

    intent_keywords = [
        ("路径规划", ["规划", "路线", "怎么学", "计划", "安排", "方案", "节奏", "顺序", "步骤", "阶段", "复习路径"]),
        ("生成资源", ["资源", "资料", "生成", "文档", "导图", "材料", "讲义", "整理一份"]),
        ("练习巩固", ["题", "练习", "考试", "测验", "刷题", "错题", "巩固", "检测", "自测"]),
        ("实操训练", ["项目", "实践", "实操", "案例", "实验", "应用", "任务", "动手"]),
        ("概念讲解", ["不会", "不懂", "解释", "讲一下", "原理", "为什么", "是什么", "区别", "含义"]),
    ]

    for intent, keywords in intent_keywords:
        if any(word in text for word in keywords):
            return intent, True

    return "综合学习", False


def _extract_json(content: str):
    text = (content or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    match = re.search(r"\{.*\}", text, re.S)
    if match:
        text = match.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _infer_by_llm(message: str):
    prompt = f"""
你是学习平台的意图识别 Agent。请根据学生输入判断学习意图和学科主题。

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
- 如果完全无法判断，返回“人工智能导论”。

只返回 JSON，不要解释：
{{
  "intent": "路径规划",
  "topic": "计算机网络",
  "confidence": 80
}}
"""

    result = chat(
        [{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=800
    )

    if not result.get("ok"):
        return {}

    data = _extract_json(result.get("content", ""))
    if not isinstance(data, dict):
        return {}

    intent = _normalize_intent(data.get("intent", ""))
    topic = (data.get("topic") or "").strip()[:40] or "人工智能导论"

    try:
        confidence = int(data.get("confidence", 80))
    except (TypeError, ValueError):
        confidence = 80

    return {
        "intent": intent,
        "topic": topic,
        "score": max(0, min(100, confidence)),
    }


def run(message: str):
    rule_intent, intent_matched = _infer_intent_by_rules(message)
    rule_topic, topic_matched = _infer_topic_by_rules(message)

    llm_result = {}
    if not intent_matched or not topic_matched:
        llm_result = _infer_by_llm(message)

    intent = rule_intent if intent_matched else llm_result.get("intent", rule_intent)
    topic = rule_topic if topic_matched else llm_result.get("topic", rule_topic)

    return {
        "intent": _normalize_intent(intent),
        "topic": topic,
        "score": llm_result.get("score", 80),
        "intent_source": "rule" if intent_matched else ("llm" if llm_result else "fallback"),
        "topic_source": "rule" if topic_matched else ("llm" if llm_result else "fallback"),
    }
