import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List


COURSE_ID = "data_structures_algorithms"
COURSE_TITLE = "数据结构与算法"
COURSE_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "knowledge_base"
    / COURSE_ID
)


_TOPIC_ALIASES = [
    ("复杂度分析", ["复杂度", "大o", "大 o", "时间复杂度", "空间复杂度", "循环复杂度", "增长趋势"], "sec_01_time_complexity_big_o"),
    ("数组与链表", ["数组", "链表", "连续存储", "指针", "节点", "插入删除"], "sec_02_array"),
    ("栈与队列", ["栈", "队列", "lifo", "fifo", "单调栈", "双端队列"], "sec_02_stack"),
    ("递归", ["递归", "调用栈", "递归出口", "终止条件", "分治", "回溯"], "sec_03_recursion_basic"),
    ("排序算法", ["排序", "冒泡", "选择排序", "插入排序", "归并", "快速排序", "快排"], "sec_04_simple_sorting"),
    ("二分查找边界条件", ["二分", "二分查找", "边界", "left", "right", "mid", "有序数组"], "sec_04_binary_search"),
    ("哈希表", ["哈希", "hash", "散列", "map", "set", "冲突"], "sec_05_hash_table_intro"),
    ("堆与优先队列", ["堆", "优先队列", "priority queue", "top-k", "topk", "最大堆", "最小堆"], "sec_05_priority_queue"),
    ("树与二叉树", ["树", "二叉树", "二叉搜索树", "bst", "前序", "中序", "后序", "层序"], "sec_06_binary_tree_basic"),
    ("BFS 与 DFS", ["bfs", "dfs", "广度优先", "深度优先", "图搜索", "遍历", "迷宫"], "sec_07_bfs"),
    ("最短路径", ["最短路径", "dijkstra", "迪ijkstra", "bellman", "floyd", "带权图", "松弛"], "sec_08_dijkstra"),
    ("贪心算法", ["贪心", "局部最优", "活动选择", "区间调度", "huffman", "哈夫曼"], "sec_09_greedy_intro"),
    ("动态规划", ["动态规划", "dp", "状态转移", "转移方程", "状态定义", "背包", "初始化", "填表"], "sec_10_transition_equation"),
    ("字符串匹配", ["字符串", "kmp", "next数组", "next 数组", "前缀函数", "模式串", "trie", "字典树"], "sec_11_kmp_intro"),
    ("综合项目", ["综合项目", "课程设计", "算法可视化", "刷题系统", "迷宫寻路", "项目报告"], "sec_12_project_overview"),
]


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _read_jsonl(path: Path) -> List[Dict]:
    rows = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return rows
    for line in lines:
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").lower())


@lru_cache(maxsize=1)
def _course_index() -> Dict:
    tree = _read_json(COURSE_DIR / "course_tree.json", {})
    chapters = tree.get("chapters") or []
    units = _read_jsonl(COURSE_DIR / "knowledge_units.jsonl")

    chapter_by_id = {}
    section_by_id = {}
    unit_by_id = {}
    unit_aliases = []

    for chapter in chapters:
        chapter_id = chapter.get("chapter_id") or ""
        chapter_by_id[chapter_id] = chapter
        for section in chapter.get("sections") or []:
            section_id = section.get("section_id") or ""
            section_by_id[section_id] = {**section, "chapter_id": chapter_id, "chapter_title": chapter.get("title") or ""}

    for unit in units:
        unit_id = unit.get("unit_id") or ""
        if not unit_id:
            continue
        if unit.get("section_id") in section_by_id:
            unit.setdefault("chapter_id", section_by_id[unit["section_id"]]["chapter_id"])
        unit_by_id[unit_id] = unit
        alias_texts = [unit.get("title") or "", unit_id] + list(unit.get("aliases") or []) + list(unit.get("core_concepts") or [])
        for alias in alias_texts:
            if alias:
                unit_aliases.append((_compact(alias), unit_id))

    return {
        "chapters": chapters,
        "chapter_by_id": chapter_by_id,
        "section_by_id": section_by_id,
        "unit_by_id": unit_by_id,
        "unit_aliases": unit_aliases,
    }


def get_chapter_title(chapter_id: str) -> str:
    if not chapter_id:
        return "待定位"
    return (_course_index()["chapter_by_id"].get(chapter_id) or {}).get("title") or "待定位"


def get_section_title(section_id: str) -> str:
    if not section_id:
        return "待定位"
    return (_course_index()["section_by_id"].get(section_id) or {}).get("title") or "待定位"


def get_unit_titles(unit_ids: List[str]) -> List[str]:
    unit_by_id = _course_index()["unit_by_id"]
    return [
        (unit_by_id.get(unit_id) or {}).get("title") or unit_id
        for unit_id in (unit_ids or [])
        if unit_id
    ]


def _find_section(section_id: str) -> Dict:
    return _course_index()["section_by_id"].get(section_id) or {}


def _units_for_section(section: Dict, text: str) -> List[Dict]:
    unit_by_id = _course_index()["unit_by_id"]
    section_unit_ids = section.get("unit_ids") or []
    compact = _compact(text)
    matched = []
    for unit_id in section_unit_ids:
        unit = unit_by_id.get(unit_id) or {}
        aliases = [unit.get("title") or ""] + list(unit.get("aliases") or []) + list(unit.get("core_concepts") or [])
        if any(_compact(alias) and _compact(alias) in compact for alias in aliases):
            matched.append(unit)
    if matched:
        return matched[:3]
    return [unit_by_id.get(unit_id) for unit_id in section_unit_ids[:3] if unit_by_id.get(unit_id)]


def resolve_topic(
    text: str,
    *,
    course_id: str = COURSE_ID,
    chapter_id: str = "",
    section_id: str = "",
    unit_ids: List[str] = None,
    fallback_topic: str = "数据结构与算法学习诊断",
) -> Dict:
    text = text or ""
    unit_ids = [item for item in (unit_ids or []) if item]
    index = _course_index()

    if course_id and course_id != COURSE_ID:
        course_id = COURSE_ID

    if section_id and section_id in index["section_by_id"]:
        section = _find_section(section_id)
        chapter_id = chapter_id or section.get("chapter_id") or ""
        units = [index["unit_by_id"].get(item) for item in unit_ids if index["unit_by_id"].get(item)] or _units_for_section(section, text)
        return _build_result(fallback_topic, chapter_id, section, units, text, matched=bool(text.strip()))

    compact = _compact(text)
    best = None
    best_score = 0

    for topic_title, aliases, candidate_section_id in _TOPIC_ALIASES:
        score = sum(3 if _compact(alias) in compact else 0 for alias in aliases)
        if score > best_score:
            best = (topic_title, candidate_section_id)
            best_score = score

    if best and best_score > 0:
        topic_title, candidate_section_id = best
        section = _find_section(candidate_section_id)
        units = _units_for_section(section, text)
        return _build_result(topic_title, section.get("chapter_id") or "", section, units, text, matched=True)

    for alias, unit_id in index["unit_aliases"]:
        if alias and alias in compact:
            unit = index["unit_by_id"].get(unit_id) or {}
            title = unit.get("title") or fallback_topic
            section = _find_section(unit.get("section_id") or "")
            return _build_result(title, unit.get("chapter_id") or section.get("chapter_id") or "", section, [unit], text, matched=True)

    if chapter_id and chapter_id in index["chapter_by_id"]:
        chapter = index["chapter_by_id"][chapter_id]
        sections = chapter.get("sections") or []
        section = _find_section((sections[0] or {}).get("section_id") or "") if sections else {}
        units = _units_for_section(section, text) if section else []
        return _build_result(chapter.get("title") or fallback_topic, chapter_id, section, units, text, matched=bool(text.strip()))

    return _build_result(fallback_topic, "", {}, [], text, matched=False)


def _build_result(topic: str, chapter_id: str, section: Dict, units: List[Dict], text: str, matched: bool) -> Dict:
    unit_ids = [unit.get("unit_id") for unit in units if unit and unit.get("unit_id")]
    unit_titles = [unit.get("title") for unit in units if unit and unit.get("title")]
    misconceptions = []
    evidence_refs = []
    prerequisites = []
    for unit in units:
        misconceptions.extend(unit.get("common_misconceptions") or [])
        evidence_refs.extend(unit.get("evidence_refs") or [])
        prerequisites.extend(unit.get("prerequisites") or [])

    if not misconceptions:
        misconceptions = ["主题定位仍不够具体，需要通过练习确认真实薄弱点"]
    if not unit_titles:
        unit_titles = ["待定位"]

    section_id = section.get("section_id") or ""
    section_title = section.get("title") or "待定位"
    chapter_title = get_chapter_title(chapter_id)
    topic_title = topic or (unit_titles[0] if unit_titles else "数据结构与算法学习诊断")

    return {
        "course_id": COURSE_ID,
        "course_title": COURSE_TITLE,
        "matched": matched,
        "topic": topic_title,
        "chapter_id": chapter_id or "",
        "chapter_title": chapter_title,
        "section_id": section_id,
        "section_title": section_title,
        "unit_ids": unit_ids,
        "unit_titles": unit_titles,
        "evidence_refs": list(dict.fromkeys(evidence_refs or unit_ids)),
        "weak_points": list(dict.fromkeys(misconceptions))[:3],
        "suggestions": [
            f"先回到「{section_title}」复习定义、适用条件和边界情况。" if section_id else "先补充一个具体知识点或错题描述，系统再定位章节。",
            f"围绕「{unit_titles[0]}」完成 3 道基础题和 1 道边界题。" if unit_titles and unit_titles[0] != "待定位" else "从复杂度、线性结构、递归、图、动态规划中选择一个方向做诊断。",
            "用代码跑一组正常样例和边界样例，把错误原因写成一句话复盘。",
        ],
        "practice": f"完成「{topic_title}」补弱练习：概念判断、边界用例、代码实现各 1 题。",
        "diagnosis_type": "topic_matched" if matched else "course_general",
        "prerequisite_units": list(dict.fromkeys(prerequisites))[:5],
    }
