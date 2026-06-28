import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from app.services.course_registry.course_registry import DSA_CHAPTERS


COURSE_ID = "data_structures_algorithms"
COURSE_NAME = "数据结构与算法"
COURSE_DISPLAY_NAME = "《数据结构与算法》"
COURSE_FULL_NAME = "《数据结构与算法：可视化理解与代码实践》"
COURSE_POSITIONING = (
    "面向计算机科学与技术、软件工程、人工智能、电子信息等专业本科低年级至中年级学生的专业基础核心课程，"
    "覆盖数据结构、算法设计思想、复杂度分析、代码实现、题目训练和可视化理解。"
)

DSA_CHAPTERS = DSA_CHAPTERS

COURSE_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "knowledge_base"
    / "data_structures_algorithms"
)
KNOWLEDGE_UNITS_PATH = COURSE_DIR / "knowledge_units.jsonl"


def _load_units_from_jsonl() -> List[Dict]:
    if not KNOWLEDGE_UNITS_PATH.exists():
        return []
    units = []
    with KNOWLEDGE_UNITS_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("unit_id") and item.get("title") and item.get("chapter_id"):
                item.setdefault("course_id", COURSE_ID)
                item.setdefault("aliases", [])
                item.setdefault("prerequisites", [])
                item.setdefault("related_units", [])
                item.setdefault("compare_units", [])
                item.setdefault("core_concepts", [])
                item.setdefault("visualization_suggestions", [])
                item.setdefault("suitable_resource_types", [])
                item.setdefault("difficulty", "beginner")
                units.append(item)
    return units


EXTRA_UNIT_ALIASES = {
    "dsa_algorithm_intro": ["数据结构与算法", "算法导论", "算法课程"],
    "dsa_time_complexity": ["时间复杂度", "复杂度"],
    "dsa_space_complexity": ["空间复杂度"],
    "dsa_array_basic": ["数组", "数组基础", "随机访问", "下标访问", "数组怎么用"],
    "dsa_array_operations": ["数组操作", "数组插入", "数组删除", "数组扩容", "数组复杂度"],
    "dsa_linked_list_basic": ["链表", "单链表", "链表节点", "链表指针"],
    "dsa_linked_list_operations": ["单链表反转", "单链表怎么反转", "链表怎么反转", "反转链表", "链表反转", "链表插入", "链表删除", "重连指针"],
    "dsa_stack": ["栈", "括号匹配", "括号合法性", "有效括号", "栈匹配", "栈怎么用"],
    "dsa_queue": ["队列", "循环队列", "先进先出", "队列怎么用"],
    "dsa_deque": ["双端队列", "deque", "滑动窗口最大值", "窗口最大值"],
    "dsa_two_pointers_intro": ["双指针", "快慢指针", "左右指针", "滑动窗口", "窗口边界"],
    "dsa_monotonic_stack_intro": ["单调栈", "下一个更大元素"],
    "dsa_recursion_basic": ["递归", "递归终止条件", "递归边界", "递归出口"],
    "dsa_call_stack": ["递归调用栈", "函数调用栈", "栈帧"],
    "dsa_divide_and_conquer": ["分治"],
    "dsa_backtracking_basic": ["回溯"],
    "dsa_binary_search": ["二分查找", "二分", "折半查找", "二分模板"],
    "dsa_binary_search_boundary": ["二分边界", "边界条件", "左右边界", "lower_bound", "upper_bound"],
    "dsa_bubble_selection_insertion": ["排序", "排序算法", "排序复习", "冒泡排序", "选择排序", "插入排序", "基础排序"],
    "dsa_sorting_searching_intro": ["排序", "排序算法", "排序复习", "排序怎么复习", "查找排序", "排序与查找"],
    "dsa_merge_sort": ["归并排序", "merge sort"],
    "dsa_quick_sort": ["快速排序", "快排", "quick sort"],
    "dsa_sorting_complexity_comparison": ["排序比较", "排序复杂度", "排序稳定性"],
    "dsa_hash_table": ["哈希表", "散列表"],
    "dsa_hash_collision": ["哈希冲突", "散列冲突"],
    "dsa_set_usage": ["set", "集合", "去重"],
    "dsa_map_usage": ["map", "字典", "映射", "计数表"],
    "dsa_heap_basic": ["堆", "二叉堆", "堆排序", "heap sort"],
    "dsa_min_heap": ["小根堆", "最小堆", "min heap"],
    "dsa_max_heap": ["大根堆", "最大堆", "max heap"],
    "dsa_priority_queue": ["优先队列", "优先级队列", "priority queue", "优先队列怎么用"],
    "dsa_top_k_problem": ["top k", "topk", "前 k 个", "第 k 大", "第 k 小"],
    "dsa_tree_basic": ["树", "树结构"],
    "dsa_binary_tree_basic": ["二叉树", "binary tree"],
    "dsa_tree_traversal": ["树遍历", "二叉树遍历", "前中后序", "前中后序遍历", "前序遍历", "中序遍历", "后序遍历", "层序遍历"],
    "dsa_preorder_traversal": ["树遍历", "二叉树遍历", "前中后序", "前中后序遍历", "前序遍历", "先序遍历"],
    "dsa_inorder_traversal": ["中序遍历", "二叉树中序遍历", "左根右"],
    "dsa_postorder_traversal": ["后序遍历", "二叉树后序遍历", "左右根"],
    "dsa_level_order_traversal": ["层序遍历", "二叉树层序遍历", "按层遍历"],
    "dsa_bst": ["二叉搜索树", "bst", "搜索树"],
    "dsa_bfs": ["BFS", "广度优先搜索", "迷宫寻路", "最短步数"],
    "dsa_dfs": ["DFS", "深度优先搜索", "迷宫搜索", "回溯搜索"],
    "dsa_maze_search": ["迷宫寻路", "迷宫搜索", "网格搜索", "迷宫最短路"],
    "dsa_dijkstra": ["Dijkstra", "迪ijkstra", "迪杰斯特拉", "最短路径", "最短路", "最短路模板"],
    "dsa_mst_intro": ["最小生成树", "MST"],
    "dsa_kruskal": ["Kruskal", "克鲁斯卡尔"],
    "dsa_prim": ["Prim", "普里姆"],
    "dsa_union_find": ["并查集", "union find", "disjoint set"],
    "dsa_greedy_intro": ["贪心", "贪心算法"],
    "dsa_greedy_choice_property": ["贪心选择性质"],
    "dsa_greedy_counterexample": ["贪心反例", "反例"],
    "dsa_dp_intro": ["动态规划", "DP"],
    "dsa_dp_state_definition": ["状态定义", "dp 状态", "dp含义"],
    "dsa_dp_transition": ["动态规划状态转移", "dp状态转移", "状态转移", "状态转移方程", "转移方程"],
    "dsa_dp_table_order": ["dp 填表", "填表顺序", "遍历顺序"],
    "dsa_knapsack_01": ["01背包", "0/1背包", "背包问题"],
    "dsa_string_basic": ["字符串", "字符串基础"],
    "dsa_brute_force_matching": ["暴力匹配", "朴素匹配"],
    "dsa_kmp_intro": ["KMP", "字符串匹配", "kmp算法"],
    "dsa_prefix_function": ["前缀函数", "最长相等前后缀"],
    "dsa_kmp_next_array": ["next数组", "next 数组", "KMP next 数组", "回退数组"],
    "dsa_trie": ["Trie", "字典树", "前缀树"],
    "dsa_rolling_hash_intro": ["滚动哈希", "窗口哈希"],
    "dsa_algorithm_project_design": ["算法项目", "迷宫寻路项目", "刷题训练系统"],
    "dsa_project_maze_path_finder": ["迷宫寻路项目", "迷宫项目", "路径规划项目", "BFS项目"],
}


def _with_extra_aliases(units: List[Dict]) -> List[Dict]:
    result = []
    for unit in units:
        extra = EXTRA_UNIT_ALIASES.get(unit.get("unit_id"), [])
        result.append({
            **unit,
            "aliases": list(dict.fromkeys([*(unit.get("aliases") or []), *extra])),
        })
    return result


DSA_UNITS = _with_extra_aliases(_load_units_from_jsonl())
CHAPTER_BY_ID = {chapter["chapter_id"]: chapter for chapter in DSA_CHAPTERS}
UNIT_BY_ID = {unit["unit_id"]: unit for unit in DSA_UNITS}


def _compact(value: str) -> str:
    return re.sub(r"[\s_\-·：:，,。！？!?.、/\\（）()《》]+", "", str(value or "").lower())


def _tokenize(value: str) -> List[str]:
    text = str(value or "").lower()
    return re.findall(r"[a-z0-9+#.]+|[\u4e00-\u9fff]{2,}", text)


def _intent_from_message(message: str) -> str:
    compact = _compact(message)
    if any(word in compact for word in ["错题", "错因", "做错", "写错", "总是错", "补弱", "不会这类题"]):
        return "evaluation"
    if any(word in compact for word in ["对比", "比较", "区别", "差异", "vs"]):
        return "comparison"
    if any(word in compact for word in ["不懂", "不会", "看不懂", "是什么", "什么意思", "怎么做", "怎么用", "区别", "对比"]):
        return "concept_explanation"
    if any(word in compact for word in ["项目", "实战", "实验", "实践", "做一个", "实现一个"]):
        return "project"
    if any(word in compact for word in ["代码", "c++", "python", "调试", "debug", "实现", "模板", "怎么写"]):
        return "code_lab"
    if any(word in compact for word in ["练习", "刷题", "题", "测验"]):
        return "practice"
    if any(word in compact for word in ["规划", "路线", "计划", "怎么学", "复习", "学习路径", "系统学习", "入门"]):
        return "path_planning"
    return "concept_explanation"


def _score_unit(unit: Dict, message: str, topic: str = "") -> Dict:
    text = "\n".join([topic or "", message or ""])
    compact_text = _compact(text)
    if not compact_text:
        return {"score": 0.0, "aliases": []}

    matched_aliases = []
    exact_or_explicit_hit = False
    alias_score = 0.0
    alias_candidates = (
        [(unit.get("title", ""), 0.18)]
        + [(alias, 0.15) for alias in unit.get("aliases", [])]
        + [(concept, 0.05) for concept in unit.get("core_concepts", [])]
    )
    for alias, boost in alias_candidates:
        compact_alias = _compact(alias)
        if not compact_alias:
            continue
        if compact_alias == compact_text:
            alias_score = max(alias_score, 1.0 + boost)
            matched_aliases.append(alias)
            exact_or_explicit_hit = True
        elif compact_alias in compact_text:
            alias_len = len(compact_alias)
            alias_score = max(alias_score, min(0.98, 0.6 + alias_len / 80 + boost))
            matched_aliases.append(alias)
            if alias in unit.get("aliases", []) or alias in EXTRA_UNIT_ALIASES.get(unit.get("unit_id"), []):
                exact_or_explicit_hit = True

    score = alias_score
    text_tokens = set(_tokenize(text))
    unit_tokens = set(_tokenize(unit.get("title", "")))
    for field in ["core_concepts", "prerequisites", "related_units", "compare_units", "aliases"]:
        for item in unit.get(field, []):
            unit_tokens.update(_tokenize(item))
    hits = text_tokens & unit_tokens
    if hits:
        score += min(0.26, 0.06 * len(hits))

    compact_unit_id = _compact(unit.get("unit_id", ""))
    if any(word in compact_text for word in ["项目", "实战", "做一个"]):
        if "project" in compact_unit_id:
            score += 0.45
    if "迷宫" in compact_text and "maze" in compact_unit_id:
        score += 0.5
    if "dp" in compact_text and "dp" in compact_unit_id:
        score += 0.3
    return {
        "score": round(score, 3),
        "aliases": list(dict.fromkeys(matched_aliases)),
        "explicit_alias_hit": exact_or_explicit_hit,
    }


def get_unit(unit_id: str) -> Optional[Dict]:
    unit = UNIT_BY_ID.get(unit_id)
    return dict(unit) if unit else None


def get_intro_unit() -> Dict:
    for unit in DSA_UNITS:
        if unit.get("unit_id") == "dsa_algorithm_intro":
            return dict(unit)
    return dict(DSA_UNITS[0]) if DSA_UNITS else {}


def list_units() -> List[Dict]:
    return [dict(unit) for unit in DSA_UNITS]


def taxonomy_prompt(max_units: int = 90) -> str:
    """Compact course taxonomy for LLM semantic grounding, not keyword matching."""
    lines = [f"课程：{COURSE_DISPLAY_NAME}"]
    for chapter in DSA_CHAPTERS:
        units = [
            unit.get("title", "")
            for unit in DSA_UNITS
            if unit.get("chapter_id") == chapter.get("chapter_id")
        ]
        if not units:
            continue
        lines.append(f"- 第 {chapter.get('chapter_no')} 章 {chapter.get('title')}：{'、'.join(units[:max_units])}")
    return "\n".join(lines)


def is_dsa_scope(topic: str = "", message: str = "") -> bool:
    return bool(match_dsa_topic(topic, message).get("matched"))


def build_semantic_course_match(
    topic: str = "",
    message: str = "",
    learning_need_type: str = "",
    confidence: float = 0.62,
) -> Dict:
    """Build an in-course grounding result when LLM understands the DSA topic but exact local resources are thin."""
    matched = match_dsa_topic(topic, message)
    if matched.get("matched"):
        if learning_need_type:
            matched["learning_need_type"] = learning_need_type
        return matched

    unit = get_intro_unit()
    chapter = CHAPTER_BY_ID.get(unit.get("chapter_id"), {})
    display_topic = str(topic or message or COURSE_NAME).strip()[:80] or COURSE_NAME
    need_type = learning_need_type or _intent_from_message(message or topic)
    compact_need = _compact("\n".join([topic or "", message or ""]))
    return {
        "matched": True,
        "semantic_only": True,
        "resource_exact_match": False,
        "course_id": COURSE_ID,
        "course_name": COURSE_NAME,
        "course_display_name": COURSE_DISPLAY_NAME,
        "raw_topic": topic or message,
        "normalized_topic": display_topic,
        "display_topic": display_topic,
        "chapter_id": unit.get("chapter_id", ""),
        "chapter": chapter.get("title", ""),
        "chapter_title": chapter.get("title", ""),
        "section_id": unit.get("section_id", ""),
        "unit_ids": [unit.get("unit_id", "")] if unit.get("unit_id") else [],
        "unit_id": unit.get("unit_id", ""),
        "primary_unit_id": unit.get("unit_id", ""),
        "unit": dict(unit),
        "confidence": max(0.35, min(float(confidence or 0.62), 0.78)),
        "matched_aliases": [],
        "learning_need_type": need_type,
        "requires_code": need_type in {"code_lab", "project"} or any(word in compact_need for word in ["代码", "python", "c++", "实现", "调试"]),
        "requires_multimodal": any(word in compact_need for word in ["可视化", "图解", "动画", "导图", "流程"]),
        "prerequisites": unit.get("prerequisites", []),
        "related_units": unit.get("related_units", []),
        "compare_units": unit.get("compare_units", []),
        "core_topics": unit.get("core_concepts", []),
        "practice_tasks": [],
    }


def match_dsa_topic(topic: str = "", message: str = "") -> Dict:
    raw_topic = str(topic or "").strip()
    raw_message = str(message or "").strip()
    combined = "\n".join([raw_topic, raw_message])
    compact = _compact(combined)
    if not compact:
        return {"matched": False}

    best_unit = None
    best = {"score": 0.0, "aliases": []}
    scored_units = []
    for unit in DSA_UNITS:
        current = _score_unit(unit, raw_message, raw_topic)
        if current["score"] > 0:
            scored_units.append((unit, current))
        if current["score"] > best["score"]:
            best_unit = unit
            best = current

    general_scope = any(alias in compact for alias in ["数据结构", "算法", "datastructure", "algorithm", "dsa"])
    if not best_unit:
        return {"matched": False}
    if best["score"] < 0.58 and not general_scope and not best.get("explicit_alias_hit"):
        return {"matched": False}
    if best["score"] < 0.58 and general_scope:
        best_unit = get_intro_unit()
        best = {"score": 0.62, "aliases": ["数据结构与算法"]}

    need_type = _intent_from_message(combined)
    top_units = [
        (unit, score)
        for unit, score in sorted(scored_units, key=lambda item: item[1]["score"], reverse=True)
        if score["score"] >= max(0.5, best["score"] - 0.12)
    ]
    if need_type == "comparison":
        distinct = []
        seen = set()
        for unit, score in top_units:
            if unit.get("unit_id") in seen:
                continue
            distinct.append((unit, score))
            seen.add(unit.get("unit_id"))
            if len(distinct) >= 3:
                break
        if len(distinct) >= 2:
            best_unit, best = distinct[0]
            compare_units = [unit.get("unit_id") for unit, _ in distinct[1:] if unit.get("unit_id")]
            display_topic = " 与 ".join(unit.get("title", "") for unit, _ in distinct[:2] if unit.get("title")) + " 对比学习"
        else:
            compare_units = []
            display_topic = best_unit["title"]
    else:
        compare_units = best_unit.get("compare_units", [])
        display_topic = best_unit["title"]

    chapter = CHAPTER_BY_ID.get(best_unit["chapter_id"], {})
    compact_need = _compact(combined)
    requires_code = need_type in {"code_lab", "project"} or any(word in compact_need for word in ["代码", "python", "c++", "实现", "调试"])
    requires_multimodal = any(word in compact_need for word in ["可视化", "图解", "动画", "导图", "流程"])
    confidence = min(best["score"], 1.0)
    return {
        "matched": True,
        "course_id": COURSE_ID,
        "course_name": COURSE_NAME,
        "course_display_name": COURSE_DISPLAY_NAME,
        "raw_topic": raw_topic or raw_message,
        "normalized_topic": best_unit["title"],
        "display_topic": display_topic,
        "chapter_id": best_unit["chapter_id"],
        "chapter": chapter.get("title", ""),
        "chapter_title": chapter.get("title", ""),
        "section_id": best_unit.get("section_id", ""),
        "unit_ids": [unit.get("unit_id") for unit, _ in top_units[:3] if unit.get("unit_id")] if need_type == "comparison" else [best_unit["unit_id"]],
        "unit_id": best_unit["unit_id"],
        "primary_unit_id": best_unit["unit_id"],
        "unit": dict(best_unit),
        "confidence": round(confidence, 3),
        "matched_aliases": best["aliases"],
        "learning_need_type": need_type,
        "requires_code": requires_code,
        "requires_multimodal": requires_multimodal,
        "prerequisites": best_unit.get("prerequisites", []),
        "related_units": best_unit.get("related_units", []),
        "compare_units": compare_units,
        "core_topics": best_unit.get("core_concepts", []),
        "practice_tasks": [],
    }


def course_map_payload() -> Dict:
    return {
        "course_id": COURSE_ID,
        "course_name": COURSE_NAME,
        "course_display_name": COURSE_DISPLAY_NAME,
        "course_full_name": COURSE_FULL_NAME,
        "course_positioning": COURSE_POSITIONING,
        "chapters": [
            {
                **chapter,
                "chapter_title": f"第 {chapter.get('chapter_no')} 章 {chapter.get('title')}",
                "units": [
                    dict(unit)
                    for unit in DSA_UNITS
                    if unit.get("chapter_id") == chapter.get("chapter_id")
                ],
            }
            for chapter in DSA_CHAPTERS
        ],
    }
