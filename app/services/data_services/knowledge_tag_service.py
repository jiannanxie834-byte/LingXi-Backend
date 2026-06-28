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
    (("数据结构", "算法", "algorithm"), "数据结构与算法"),
    (("复杂度", "大o", "大 o", "时间复杂度", "空间复杂度", "增长趋势"), "复杂度分析"),
    (("数组", "链表", "线性表", "连续存储", "指针", "节点"), "数组与链表"),
    (("栈", "队列", "lifo", "fifo", "单调栈", "双端队列"), "栈与队列"),
    (("递归", "调用栈", "终止条件", "回溯", "分治"), "递归与回溯"),
    (("排序", "冒泡", "选择排序", "插入排序", "归并", "快速排序", "快排"), "排序算法"),
    (("二分", "二分查找", "边界条件", "left", "right", "mid"), "二分查找"),
    (("哈希", "hash", "散列", "map", "set", "哈希冲突"), "哈希表"),
    (("堆", "优先队列", "priorityqueue", "top-k", "topk"), "堆与优先队列"),
    (("树", "二叉树", "二叉搜索树", "bst", "前序", "中序", "后序", "层序"), "树与二叉树"),
    (("图", "bfs", "dfs", "广度优先", "深度优先", "连通分量", "拓扑排序"), "图搜索"),
    (("最短路径", "dijkstra", "bellman", "floyd", "最小生成树", "kruskal", "prim"), "图算法"),
    (("贪心", "局部最优", "活动选择", "区间调度", "huffman", "哈夫曼"), "贪心算法"),
    (("动态规划", "dp", "状态定义", "状态转移", "转移方程", "背包", "填表"), "动态规划"),
    (("字符串", "kmp", "next数组", "前缀函数", "trie", "字典树", "滚动哈希"), "字符串匹配"),
    (("综合项目", "课程设计", "算法可视化", "刷题系统", "迷宫寻路"), "综合项目"),
]

_SUPPRESS_WHEN_PRESENT = {
    "数据结构与算法": {"数组与链表", "栈与队列"},
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
