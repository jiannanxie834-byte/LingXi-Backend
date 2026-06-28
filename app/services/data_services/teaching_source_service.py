import hashlib
import re
from typing import Dict, List

from app.services.data_services import resource_artifact_type_service as artifact_types


DEFAULT_LIMIT = 10

CONCEPT_CATALOG = [
    {"id": "complexity", "label": "复杂度分析", "aliases": ["复杂度", "时间复杂度", "空间复杂度", "大O"]},
    {"id": "linear", "label": "线性结构", "aliases": ["数组", "链表", "栈", "队列", "双指针", "单调栈"]},
    {"id": "recursion", "label": "递归、分治与回溯", "aliases": ["递归", "分治", "回溯", "调用栈", "n皇后"]},
    {"id": "sort_search", "label": "排序与查找", "aliases": ["排序", "二分查找", "快速排序", "归并排序"]},
    {"id": "hash_heap", "label": "哈希表、堆与优先队列", "aliases": ["哈希表", "堆", "优先队列", "top k"]},
    {"id": "tree", "label": "树与二叉树", "aliases": ["树", "二叉树", "遍历", "二叉搜索树"]},
    {"id": "graph", "label": "图算法", "aliases": ["图", "BFS", "DFS", "拓扑排序", "迷宫"]},
    {"id": "shortest_mst", "label": "最短路径与最小生成树", "aliases": ["Dijkstra", "最短路径", "最小生成树", "Kruskal", "Prim", "并查集"]},
    {"id": "greedy", "label": "贪心算法", "aliases": ["贪心", "区间调度", "活动选择", "Huffman"]},
    {"id": "dp", "label": "动态规划", "aliases": ["动态规划", "DP", "状态转移", "背包", "LCS", "LIS"]},
    {"id": "string", "label": "字符串算法", "aliases": ["字符串", "KMP", "Trie", "滚动哈希"]},
]


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").lower())


def _clip(value: str, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[:limit].rstrip() + "..."


def extract_catalog_concepts(query: str) -> List[str]:
    compact = _compact(query)
    concept_ids = []
    for item in CONCEPT_CATALOG:
        aliases = [item["label"], *item.get("aliases", [])]
        if any(_compact(alias) in compact for alias in aliases):
            concept_ids.append(item["id"])
    return list(dict.fromkeys(concept_ids))


def _concept_labels(concept_ids: List[str]) -> List[str]:
    mapping = {item["id"]: item["label"] for item in CONCEPT_CATALOG}
    return [mapping.get(item, item) for item in concept_ids]


def select_teaching_sources(query: str, limit: int = DEFAULT_LIMIT) -> Dict:
    concept_ids = extract_catalog_concepts(query)
    return {
        "items": [],
        "meta": {
            "query": query or "",
            "matched_concepts": _concept_labels(concept_ids),
            "strategy": "数据结构与算法课程框架阶段：外部资料目录待后续导入",
            "copyright_policy": "本阶段不抓取、不复制外部教材或题库正文。",
            "total_count": 0,
            "sources": [],
            "material_types": [],
        },
    }


def format_teaching_sources_for_prompt(result: Dict, max_items: int = 6) -> str:
    concepts = "、".join((result or {}).get("meta", {}).get("matched_concepts", []))
    if concepts:
        return f"当前仅完成《数据结构与算法》课程框架搭建，已识别主题方向：{concepts}。正式外部教学资料目录将在后续知识库阶段导入。"
    return "当前仅完成《数据结构与算法》课程框架搭建，正式外部教学资料目录将在后续知识库阶段导入。"


def _card_id(prefix: str, title: str, concepts: List[str]) -> str:
    digest = hashlib.md5(f"{prefix}|{title}|{'|'.join(concepts)}".encode("utf-8")).hexdigest()[:10].upper()
    return f"AUTO-{prefix}-{digest}"


def build_pushed_teaching_resource_cards(query: str, limit: int = 4) -> List[Dict]:
    concept_ids = extract_catalog_concepts(query)
    if not concept_ids:
        return []
    topic = "、".join(_concept_labels(concept_ids)[:2])
    return [
        {
            "id": _card_id("FRAMEWORK", topic, concept_ids),
            "title": f"{topic}课程资源框架占位",
            "type": artifact_types.COURSE_NOTE,
            "status": "framework_placeholder",
            "uploader": "课程框架 Agent",
            "applicant_username": "",
            "time": "",
            "summary": "当前仅完成《数据结构与算法》课程框架搭建，正式课程资源将在后续知识库构建阶段导入。",
            "content": "资源内容建设中",
            "source": "《数据结构与算法》课程框架",
            "agent_notes": "",
            "safety_review": {},
            "review_comment": "",
            "reviewed_at": "",
            "auto_pushed": True,
            "_recommend_rank": 1,
        }
    ][:max(1, min(limit, 4))]
