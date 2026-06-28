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
    "dsa_recursion_basic": ["递归", "递归终止条件", "递归边界", "递归出口"],
    "dsa_divide_and_conquer": ["分治"],
    "dsa_backtracking_basic": ["回溯"],
    "dsa_binary_search": ["二分查找", "二分"],
    "dsa_hash_table": ["哈希表", "散列表"],
    "dsa_heap_basic": ["堆"],
    "dsa_tree_basic": ["树", "树结构"],
    "dsa_bfs": ["BFS", "广度优先搜索", "迷宫寻路", "最短步数"],
    "dsa_dfs": ["DFS", "深度优先搜索", "迷宫搜索"],
    "dsa_dijkstra": ["Dijkstra", "迪ijkstra", "最短路径"],
    "dsa_mst_intro": ["最小生成树", "MST"],
    "dsa_greedy_intro": ["贪心", "贪心算法"],
    "dsa_dp_intro": ["动态规划", "DP"],
    "dsa_dp_state_definition": ["状态定义"],
    "dsa_dp_transition": ["状态转移", "状态转移方程"],
    "dsa_kmp_intro": ["KMP", "字符串匹配"],
    "dsa_algorithm_project_design": ["算法项目", "迷宫寻路项目", "刷题训练系统"],
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
    if any(word in compact for word in ["项目", "实战", "实验", "实践", "做一个", "实现一个"]):
        return "project"
    if any(word in compact for word in ["代码", "c++", "python", "调试", "debug", "实现"]):
        return "code_lab"
    if any(word in compact for word in ["练习", "刷题", "题", "测验"]):
        return "practice"
    if any(word in compact for word in ["规划", "路线", "计划", "怎么学", "学习路径", "系统学习", "入门"]):
        return "path_planning"
    if any(word in compact for word in ["对比", "比较", "区别", "差异", "vs"]):
        return "comparison"
    return "concept_explanation"


def _score_unit(unit: Dict, message: str, topic: str = "") -> Dict:
    text = "\n".join([topic or "", message or ""])
    compact_text = _compact(text)
    if not compact_text:
        return {"score": 0.0, "aliases": []}

    matched_aliases = []
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
        elif compact_alias in compact_text:
            alias_len = len(compact_alias)
            alias_score = max(alias_score, min(0.98, 0.6 + alias_len / 80 + boost))
            matched_aliases.append(alias)

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
    return {"score": round(score, 3), "aliases": list(dict.fromkeys(matched_aliases))}


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


def is_dsa_scope(topic: str = "", message: str = "") -> bool:
    return bool(match_dsa_topic(topic, message).get("matched"))


def match_dsa_topic(topic: str = "", message: str = "") -> Dict:
    raw_topic = str(topic or "").strip()
    raw_message = str(message or "").strip()
    combined = "\n".join([raw_topic, raw_message])
    compact = _compact(combined)
    if not compact:
        return {"matched": False}

    best_unit = None
    best = {"score": 0.0, "aliases": []}
    for unit in DSA_UNITS:
        current = _score_unit(unit, raw_message, raw_topic)
        if current["score"] > best["score"]:
            best_unit = unit
            best = current

    general_scope = any(alias in compact for alias in ["数据结构", "算法", "datastructure", "algorithm", "dsa"])
    if not best_unit:
        return {"matched": False}
    if best["score"] < 0.58 and not general_scope:
        return {"matched": False}
    if best["score"] < 0.58 and general_scope:
        best_unit = get_intro_unit()
        best = {"score": 0.62, "aliases": ["数据结构与算法"]}

    chapter = CHAPTER_BY_ID.get(best_unit["chapter_id"], {})
    need_type = _intent_from_message(combined)
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
        "display_topic": best_unit["title"],
        "chapter_id": best_unit["chapter_id"],
        "chapter": chapter.get("title", ""),
        "chapter_title": chapter.get("title", ""),
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
        "compare_units": best_unit.get("compare_units", []),
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
