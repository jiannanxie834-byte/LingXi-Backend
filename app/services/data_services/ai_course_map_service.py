import re
from typing import Dict, List


AI_COURSE_MAP = [
    {
        "chapter": "人工智能基础",
        "topics": ["人工智能概念", "智能体", "搜索与问题求解"],
        "aliases": ["人工智能", "AI", "智能体", "搜索", "启发式搜索", "A*", "状态空间"],
        "prerequisites": [],
        "resource_focus": ["概念讲解", "思维导图", "基础练习"],
        "practice_tasks": ["解释一个生活场景中的智能体组成"],
    },
    {
        "chapter": "机器学习基础",
        "topics": ["监督学习", "无监督学习", "训练集", "测试集", "特征工程"],
        "aliases": ["机器学习", "监督学习", "无监督学习", "训练集", "测试集", "特征工程", "分类", "回归"],
        "prerequisites": ["人工智能基础"],
        "resource_focus": ["讲解文档", "练习题", "实践任务"],
        "practice_tasks": ["用表格数据完成一次分类任务并解释训练/测试划分"],
    },
    {
        "chapter": "模型评估",
        "topics": ["准确率", "召回率", "混淆矩阵", "过拟合", "欠拟合"],
        "aliases": ["模型评估", "准确率", "精确率", "召回率", "F1", "混淆矩阵", "过拟合", "欠拟合"],
        "prerequisites": ["机器学习基础"],
        "resource_focus": ["讲解文档", "练习题", "实验分析"],
        "practice_tasks": ["对一个分类结果画出混淆矩阵并解释错误类型"],
    },
    {
        "chapter": "神经网络基础",
        "topics": ["神经元", "激活函数", "前向传播", "反向传播"],
        "aliases": ["神经网络", "神经元", "激活函数", "前向传播", "反向传播", "梯度下降"],
        "prerequisites": ["机器学习基础"],
        "resource_focus": ["图解", "推导练习", "代码实践"],
        "practice_tasks": ["手算一个两层神经网络的前向传播过程"],
    },
    {
        "chapter": "序列模型",
        "topics": ["RNN", "LSTM", "长期依赖", "门控机制"],
        "aliases": ["RNN", "循环神经网络", "LSTM", "长短期记忆网络", "长期依赖", "门控机制", "遗忘门", "输入门", "输出门", "序列模型"],
        "prerequisites": ["神经网络基础"],
        "resource_focus": ["结构图", "对比表", "代码实践", "练习题"],
        "practice_tasks": ["用 RNN 或 LSTM 完成一个简单序列预测任务"],
    },
    {
        "chapter": "NLP 与大语言模型",
        "topics": ["词向量", "Transformer", "注意力机制", "大语言模型"],
        "aliases": ["NLP", "自然语言处理", "词向量", "Transformer", "注意力机制", "自注意力", "大语言模型", "LLM", "提示词"],
        "prerequisites": ["神经网络基础", "序列模型"],
        "resource_focus": ["讲解文档", "结构图", "拓展阅读", "实践任务"],
        "practice_tasks": ["对比 RNN、LSTM、Transformer 的序列建模方式"],
    },
    {
        "chapter": "AI 安全与防幻觉",
        "topics": ["幻觉", "RAG", "内容安全", "人工审核"],
        "aliases": ["AI安全", "人工智能安全", "幻觉", "RAG", "检索增强", "内容安全", "人工审核", "防幻觉", "信息安全", "网络安全"],
        "prerequisites": ["大语言模型"],
        "resource_focus": ["案例分析", "实践任务", "评价报告"],
        "practice_tasks": ["设计一个 RAG 回答的引用核验流程"],
    },
]

_CANONICAL_TOPIC_ALIASES = {
    "ai": "人工智能概念",
    "人工智能": "人工智能概念",
    "a*": "搜索与问题求解",
    "astar": "搜索与问题求解",
    "rnn": "RNN",
    "循环神经网络": "RNN",
    "lstm": "LSTM",
    "长短期记忆网络": "LSTM",
    "transformer": "Transformer",
    "llm": "大语言模型",
    "rag": "RAG",
}


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").lower())


def _canonical_topic(alias: str, chapter: Dict) -> str:
    compact = _compact(alias)
    if compact in _CANONICAL_TOPIC_ALIASES:
        return _CANONICAL_TOPIC_ALIASES[compact]
    for topic in chapter.get("topics", []):
        if _compact(topic) in compact or compact in _compact(topic):
            return topic
    return chapter.get("topics", ["人工智能"])[0]


def match_ai_course_topic(topic: str, message: str = "") -> Dict:
    text = "\n".join([str(topic or ""), str(message or "")])
    compact_text = _compact(text)
    if not compact_text:
        return {"matched": False}

    best_match = None
    best_score = 0

    for chapter in AI_COURSE_MAP:
        aliases = list(chapter.get("topics", [])) + list(chapter.get("aliases", []))
        for alias in aliases:
            compact_alias = _compact(alias)
            if not compact_alias:
                continue
            if compact_alias in compact_text:
                score = len(compact_alias)
                if score > best_score:
                    best_score = score
                    best_match = (chapter, alias)

    if not best_match:
        return {"matched": False}

    chapter, matched_alias = best_match
    return {
        "matched": True,
        "chapter": chapter["chapter"],
        "topic": _canonical_topic(matched_alias, chapter),
        "matched_alias": matched_alias,
        "core_topics": chapter.get("topics", []),
        "prerequisites": chapter.get("prerequisites", []),
        "resource_focus": chapter.get("resource_focus", []),
        "practice_tasks": chapter.get("practice_tasks", []),
    }


def format_course_map_for_prompt(course_match: Dict) -> str:
    if not course_match or not course_match.get("matched"):
        return "未匹配到人工智能课程地图章节。"
    return "\n".join([
        f"课程章节：{course_match.get('chapter')}",
        f"核心知识点：{'、'.join(course_match.get('core_topics') or [])}",
        f"前置知识：{'、'.join(course_match.get('prerequisites') or []) or '无'}",
        f"推荐资源重点：{'、'.join(course_match.get('resource_focus') or [])}",
        f"推荐实践任务：{'；'.join(course_match.get('practice_tasks') or [])}",
    ])
