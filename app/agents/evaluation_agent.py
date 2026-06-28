from app.services.llm_provider import chat_json
from app.services.data_services import course_scope_service, dsa_course_map_service


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
    ("数据结构与算法", ["数据结构与算法", "dsa", "算法课程", "数据结构", "算法"]),
    ("复杂度分析", ["复杂度", "时间复杂度", "空间复杂度", "大o", "big-o", "o(n)"]),
    ("数组、链表、栈与队列", ["数组", "链表", "栈", "队列", "双端队列", "单调栈", "双指针"]),
    ("递归、分治与回溯", ["递归", "调用栈", "分治", "回溯", "排列组合", "n皇后"]),
    ("排序与查找算法", ["排序", "冒泡", "选择排序", "插入排序", "归并排序", "快速排序", "二分查找"]),
    ("哈希表、堆与优先队列", ["哈希表", "哈希冲突", "堆", "优先队列", "top k"]),
    ("树、二叉树与搜索树", ["树", "二叉树", "遍历", "二叉搜索树", "层序遍历", "平衡树"]),
    ("图的表示、BFS 与 DFS", ["图", "bfs", "dfs", "广度优先", "深度优先", "邻接表", "拓扑排序", "迷宫"]),
    ("最短路径与最小生成树", ["dijkstra", "最短路径", "最小生成树", "kruskal", "prim", "并查集"]),
    ("贪心算法", ["贪心", "区间调度", "活动选择", "huffman", "反例"]),
    ("动态规划", ["动态规划", "dp", "状态定义", "状态转移", "背包", "最长公共子序列", "最长递增子序列"]),
    ("字符串算法与匹配", ["字符串", "kmp", "前缀函数", "trie", "字典树", "滚动哈希"]),
    ("算法项目实践", ["项目", "算法可视化", "刷题训练", "迷宫寻路", "在线判题"]),
]


def _compact(text: str):
    return "".join(str(text or "").lower().split())


def _infer_topic_by_rule(message: str):
    course_match = dsa_course_map_service.match_dsa_topic("", message)
    if course_match.get("matched"):
        return course_match.get("display_topic") or course_match.get("normalized_topic") or ""
    compact = _compact(message)
    for topic, aliases in TOPIC_KEYWORDS:
        if any(_compact(alias) in compact for alias in aliases):
            return course_scope_service.normalize_course_topic(topic)
    return ""


def _infer_intent_by_rule(message: str):
    compact = _compact(message)
    if any(word in compact for word in ["练习", "习题", "刷题", "题目", "题库", "做题", "出题", "测试", "错题", "推荐题"]):
        return "练习巩固"
    if any(word in compact for word in ["资源", "资料", "课件", "ppt", "导图", "学习包", "推荐"]):
        return "生成资源"
    if any(word in compact for word in ["代码", "项目", "实验", "实操", "实践", "模板", "怎么写"]):
        return "实操训练"
    if any(word in compact for word in ["是什么", "什么意思", "解释", "介绍", "原理", "不懂", "不会", "怎么做", "怎么用", "区别", "对比"]):
        return "概念讲解"
    if any(word in compact for word in ["学习规划", "路径规划", "规划路线", "学习路线", "路线", "计划", "学习一下", "想学习", "我要学习", "想学", "复习", "入门"]):
        return "路径规划"
    return ""


def _normalize_intent(intent: str):
    normalized = (intent or "").strip()
    normalized = INTENT_ALIASES.get(normalized, normalized)
    return normalized if normalized in INTENTS else ""


def _infer_by_llm(message: str):
    taxonomy = dsa_course_map_service.taxonomy_prompt()
    prompt = f"""
你是《数据结构与算法》课程学习平台内部的语义理解 Agent。请先理解学生自然语言，再判断学习意图、归一化学习主题和学习需求。

输出边界：
- 只输出 JSON 对象
- 不输出解释
- 不输出思考过程
- 不面向学生说话
- 不输出 Markdown 代码块

课程边界：
系统默认课程是《数据结构与算法》。学生表达模糊时，优先在本课程范围内理解，不要因为资源库没有精确词条就返回未确认。
下面是课程知识体系摘要，用于语义归一，不是关键词表：
{taxonomy}

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
- 如果能识别具体课程知识点，返回简短规范主题，例如“链表”“栈与队列”“二叉树遍历”“最短路径”“排序算法”“复杂度分析”。
- 当输入是“我要学习/我想学/想了解/准备学 + 数据结构与算法知识点”时，必须把后面的知识点作为 topic。
- 如果学生的表达是口语、同义说法或中英文混合，要归一到数据结构与算法课程主题。
- 如果属于数据结构与算法但本地课程库可能没有完全同名词条，也要返回合理主题，不要返回“未确认主题”。
- 如果完全无法判断，topic 返回“未确认主题”，confidence 不超过 50。
- 不得把未知主题默认成任何具体课程主题。

判断要求：
- 当学生表达想开始学习某个学科、课程或方向时，intent 优先选择“路径规划”。
- 当学生要求资料、课件、题库、学习包、PPT、导图时，intent 选择“生成资源”。
- 当学生询问概念、原理、区别、为什么时，intent 选择“概念讲解”。
- 当学生要求做题、刷题、错题、测试时，intent 选择“练习巩固”。
- 当学生要求项目、实验、代码、实践任务时，intent 选择“实操训练”。
- 只有在没有明确动作，只是泛泛聊天时，才选择“综合学习”。

JSON 字段：
{{
  "intent": "路径规划",
  "topic": "链表",
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
    try:
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
    except Exception:
        pass

    topic_by_rule = _infer_topic_by_rule(message)
    intent_by_rule = _infer_intent_by_rule(message)
    if topic_by_rule and intent_by_rule:
        return {
            "intent": intent_by_rule,
            "topic": topic_by_rule,
            "score": 78,
            "intent_source": "course_map_fallback",
            "topic_source": "course_map_fallback",
        }
    if topic_by_rule and not intent_by_rule:
        return {
            "intent": "综合学习",
            "topic": topic_by_rule,
            "score": 72,
            "intent_source": "course_map_fallback",
            "topic_source": "course_map_fallback",
        }
    return {
        "intent": intent_by_rule or "综合学习",
        "topic": topic_by_rule or "未确认主题",
        "score": 50 if not topic_by_rule else 70,
        "intent_source": "rule_fallback" if intent_by_rule else "fallback",
        "topic_source": "course_map_fallback" if topic_by_rule else "unknown",
    }
