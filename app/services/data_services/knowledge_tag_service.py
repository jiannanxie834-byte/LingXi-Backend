import re
from collections import OrderedDict
from typing import Iterable, List, Optional


MAX_KNOWLEDGE_TAGS = 8

_NON_KNOWLEDGE_TAGS = {
    "概念讲解",
    "实操训练",
    "路径规划",
    "练习巩固",
    "综合学习",
    "生成学习路径",
    "制定计划",
    "生成资源",
    "错题诊断",
    "平台自动诊断",
    "初学者",
    "进阶",
    "熟练",
    "高级",
    "低",
    "中",
    "高",
}

_DROP_PATTERNS = [
    "需要",
    "适合",
    "建议",
    "进一步",
    "强化",
    "提升",
    "修复",
    "复盘",
    "学习目标",
    "学习路线",
    "学习计划",
    "暂无",
    "当前主题",
]

_ALIASES = [
    (("promise", "async", "await", "异步", "axios"), "JavaScript 异步编程"),
    (("javascript", "js基础", "js 基础", "js"), "JavaScript 基础"),
    (("vue3组合式api", "组合式api", "composition api"), "Vue3 组合式 API"),
    (("vue组件", "组件通信", "父子组件"), "Vue 组件通信"),
    (("vue", "vue3"), "Vue 基础"),
    (("element plus", "elementplus"), "Element Plus"),
    (("前端路由", "router", "vue router"), "前端路由"),
    (("表单校验", "表单验证"), "表单校验"),
    (("html",), "HTML 基础"),
    (("css",), "CSS 样式基础"),
    (("python",), "Python 基础"),
    (("fastapi",), "FastAPI"),
    (("sqlite",), "SQLite 数据库"),
    (("mysql",), "MySQL 数据库"),
    (("人工智能导论", "人工智能相关知识", "人工智能", "ai基础", "ai 基础"), "人工智能基础"),
    (("机器学习",), "机器学习基础"),
    (("深度学习",), "深度学习基础"),
    (("大模型", "llm"), "大模型基础"),
    (("神经网络",), "神经网络"),
    (("自然语言处理", "nlp"), "自然语言处理"),
    (("计算机网络", "网络协议"), "计算机网络"),
    (("数据库",), "数据库基础"),
]

_SUPPRESS_WHEN_PRESENT = {
    "JavaScript 基础": {"JavaScript 异步编程"},
    "Vue 基础": {"Vue 组件通信", "Vue3 组合式 API"},
}


def _compact_text(value: str) -> str:
    return re.sub(r"\s+", "", value.lower())


def normalize_knowledge_tag(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    tag = str(value).strip()
    tag = tag.strip("「」『』“”\"'` ，,。.;；:/\\|[]（）()")
    if not tag or tag in _NON_KNOWLEDGE_TAGS:
        return None

    compact = _compact_text(tag)
    if compact in {_compact_text(item) for item in _NON_KNOWLEDGE_TAGS}:
        return None

    if any(pattern in tag for pattern in _DROP_PATTERNS):
        return None

    for keys, normalized in _ALIASES:
        if any(key in compact for key in keys):
            return normalized

    if len(tag) < 2 or len(tag) > 18:
        return None

    return tag


def extract_knowledge_tags_from_text(text: Optional[str]) -> List[str]:
    if not text:
        return []

    compact = _compact_text(str(text))
    tags = []

    for keys, normalized in _ALIASES:
        if any(key in compact for key in keys):
            tags.append(normalized)

    return summarize_knowledge_tags(tags)


def summarize_knowledge_tags(
    candidates: Iterable[Optional[str]],
    max_count: int = MAX_KNOWLEDGE_TAGS
) -> List[str]:
    result = OrderedDict()

    for item in candidates:
        normalized = normalize_knowledge_tag(item)
        if normalized:
            result.setdefault(normalized, None)

    tags = list(result.keys())
    tag_set = set(tags)
    collapsed = [
        tag
        for tag in tags
        if not (
            tag in _SUPPRESS_WHEN_PRESENT
            and _SUPPRESS_WHEN_PRESENT[tag].intersection(tag_set)
        )
    ]

    return collapsed[:max_count]
