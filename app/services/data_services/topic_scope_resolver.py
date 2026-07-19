import re
from typing import Dict, List

from app.services.data_services import (
    course_scope_service,
    dsa_course_map_service,
)


SCOPE_COURSE = "course"
SCOPE_CHAPTER = "chapter"
SCOPE_UNIT = "unit"
SCOPE_CONCEPT = "concept"
SCOPE_COMPARISON = "comparison"
SCOPE_PROJECT = "project"
SCOPE_DIAGNOSTIC = "diagnostic"
SCOPE_REMEDIATION = "remediation"
SCOPE_AMBIGUOUS = "ambiguous"
SCOPE_OUT_OF_COURSE = "out_of_course"

FULL_CHAPTER_MARKERS = [
    "系统学习",
    "完整学习",
    "完整掌握",
    "完整讲",
    "整章",
    "整个章节",
    "全章",
    "章节路线",
    "学习路线",
    "路线",
    "路径",
    "系统掌握",
    "从头学",
    "全面学",
    "都学",
    "全部学",
]

BROAD_CHAPTER_TOPICS = [
    "复杂度分析",
    "线性结构",
    "数组链表栈队列",
    "递归分治回溯",
    "排序查找",
    "哈希表堆优先队列",
    "树二叉树搜索树",
    "图算法",
    "图的表示",
    "bfsdfs",
    "最短路径",
    "最小生成树",
    "贪心算法",
    "动态规划",
    "字符串算法",
    "算法项目",
    "算法可视化",
    "刷题训练",
]

OUT_OF_COURSE_MARKERS = [
    "数据库",
    "操作系统",
    "计算机网络",
    "英语",
    "高数",
    "高等数学",
    "法语",
    "金融",
]

COURSE_ONLY_MARKERS = [
    "学习数据结构与算法",
    "学数据结构与算法",
    "数据结构与算法入门",
    "数据结构与算法课程",
    "数据结构与算法怎么学",
    "学习算法",
    "算法怎么学",
    "dsa",
]

CONCEPT_MARKERS = [
    "不懂",
    "不会",
    "是什么",
    "什么是",
    "概念",
    "定义",
    "原理",
    "公式",
    "解释",
    "讲讲",
    "讲一下",
    "为什么",
]

COMPARISON_MARKERS = [
    "比较",
    "对比",
    "区别",
    "差异",
    "不同",
    "vs",
    "VS",
    "优缺点",
]

PROJECT_MARKERS = [
    "项目",
    "实战",
    "做一个",
    "完成一个",
    "训练一个",
    "实现一个",
]

TARGET_CUE_MARKERS = [
    "不理解",
    "没理解",
    "不懂",
    "不会",
    "看不懂",
    "想学习",
    "想学",
    "请讲",
    "讲解",
    "重点学习",
]

BACKGROUND_CUE_MARKERS = [
    "学过",
    "已经学过",
    "掌握了",
    "已经掌握",
    "会用",
    "熟悉",
]

DIAGNOSTIC_MARKERS = [
    "诊断",
    "错题",
    "错因",
    "做错",
    "答错",
    "写错",
    "总是错",
    "总是写错",
    "不会做",
    "测评",
    "测试结果",
    "作答记录",
    "补弱",
]


def _compact(value: str) -> str:
    return re.sub(r"[\s_\-·：:，,。！？!?.、/\\（）()《》]+", "", str(value or "").lower())


def _contains_any(text: str, markers: List[str]) -> bool:
    compact = _compact(text)
    return any(_compact(marker) in compact for marker in markers if marker)


def _topic_label(label: str) -> str:
    return str(label or "").strip(" ，,。.;；:：、/\\|[]（）()《》")


def _canonical_short_label(label: str) -> str:
    compact = _compact(label)
    return {
        "bfs": "BFS",
        "dfs": "DFS",
        "dp": "动态规划",
        "kmp": "KMP",
        "dijkstra": "Dijkstra",
        "unionfind": "并查集",
    }.get(compact, label)


def _unit_payload(unit: Dict) -> Dict:
    return {
        "unit_id": unit.get("unit_id", ""),
        "title": unit.get("title", ""),
        "chapter_id": unit.get("chapter_id", ""),
    }


def _unit_payload_from_id(unit_id: str) -> Dict:
    unit = dsa_course_map_service.get_unit(unit_id or "") or {}
    return _unit_payload(unit) if unit else {"unit_id": unit_id or "", "title": unit_id or "", "chapter_id": ""}


def _units_from_ids(unit_ids: List[str]) -> List[Dict]:
    result = []
    seen = set()
    for unit_id in unit_ids or []:
        if not unit_id or unit_id in seen:
            continue
        result.append(_unit_payload_from_id(unit_id))
        seen.add(unit_id)
    return result


def _score_alias(alias: str) -> int:
    compact_alias = _compact(alias)
    if not compact_alias:
        return 0
    if re.fullmatch(r"[a-z0-9+#.]+", compact_alias):
        return max(6, len(compact_alias) * 2)
    return max(4, len(compact_alias))


def _learning_target_bonus(compact_message: str, alias_position: int) -> int:
    """Prefer the topic the student wants help with over stated prerequisites."""
    if alias_position < 0:
        return 0
    prefix = compact_message[max(0, alias_position - 18):alias_position]
    target_bonus = 22 if any(_compact(marker) in prefix for marker in TARGET_CUE_MARKERS) else 0
    background_penalty = 16 if any(_compact(marker) in prefix for marker in BACKGROUND_CUE_MARKERS) else 0
    return target_bonus - background_penalty


def _find_unit_matches(message: str) -> List[Dict]:
    compact_message = _compact(message)
    if not compact_message:
        return []

    matches_by_unit = {}
    for unit in dsa_course_map_service.list_units():
        alias_candidates = (
            [(unit.get("title", ""), 6)]
            + [(alias, 5) for alias in unit.get("aliases", [])]
            + [(concept, 0) for concept in unit.get("core_concepts", [])]
        )
        for alias, boost in alias_candidates:
            compact_alias = _compact(alias)
            if not compact_alias or compact_alias not in compact_message:
                continue
            current = matches_by_unit.get(unit["unit_id"])
            position = compact_message.find(compact_alias)
            score = _score_alias(alias) + boost + _learning_target_bonus(compact_message, position)
            if current is None or score > current["score"]:
                matches_by_unit[unit["unit_id"]] = {
                    "unit": unit,
                    "label": _topic_label(alias),
                    "score": score,
                    "position": position,
                }

    matches = list(matches_by_unit.values())
    matches.sort(key=lambda item: (-item["score"], item["position"], item["unit"].get("unit_id", "")))
    return matches


def _same_chapter_units(chapter_id: str, primary_unit_id: str = "") -> List[Dict]:
    return [
        _unit_payload(unit)
        for unit in dsa_course_map_service.list_units()
        if unit.get("chapter_id") == chapter_id and unit.get("unit_id") != primary_unit_id
    ]


def _related_units(unit: Dict, chapter_id: str, primary_unit_id: str = "") -> List[Dict]:
    explicit = _units_from_ids(unit.get("related_units", []))
    return explicit if explicit else _same_chapter_units(chapter_id, primary_unit_id)


def _resolve_prerequisite_units(unit: Dict) -> List[Dict]:
    result = []
    seen = set()
    for prerequisite in unit.get("prerequisites", []):
        match = dsa_course_map_service.match_dsa_topic(prerequisite, prerequisite)
        unit_id = match.get("unit_id")
        if unit_id and unit_id != unit.get("unit_id") and unit_id not in seen:
            result.append({
                "unit_id": unit_id,
                "title": match.get("normalized_topic") or match.get("topic") or prerequisite,
                "chapter_id": match.get("chapter_id", ""),
            })
            seen.add(unit_id)
        elif prerequisite and prerequisite not in seen:
            result.append({
                "unit_id": "",
                "title": prerequisite,
                "chapter_id": "",
            })
            seen.add(prerequisite)
    return result


def _explicit_display_label(message: str, match: Dict) -> str:
    label = _topic_label(match.get("label") or "")
    if label:
        return label
    unit = match.get("unit") or {}
    return unit.get("title", "")


def _comparison_labels(message: str, matches: List[Dict]) -> List[str]:
    compact_message = _compact(message)
    labels_with_position = []
    for unit in dsa_course_map_service.list_units():
        aliases = [unit.get("title", ""), *unit.get("aliases", []), *unit.get("core_concepts", [])]
        for alias in aliases:
            label = _canonical_short_label(_topic_label(alias))
            compact_label = _compact(label)
            if not compact_label or compact_label not in compact_message:
                continue
            labels_with_position.append((compact_message.find(compact_label), label))
    for match in sorted(matches, key=lambda item: item.get("position", 0)):
        label = _canonical_short_label(_explicit_display_label(message, match))
        compact_label = _compact(label)
        if compact_label and compact_label in compact_message:
            labels_with_position.append((compact_message.find(compact_label), label))

    labels = []
    for _, label in sorted(labels_with_position, key=lambda item: (item[0], -len(_compact(item[1])))):
        compact_label = _compact(label)
        if compact_label and compact_label not in {_compact(item) for item in labels}:
            labels.append(label)
    return labels


def _join_compare_labels(labels: List[str]) -> str:
    labels = [label for label in dict.fromkeys(labels) if label]
    if len(labels) <= 2:
        return " 与 ".join(labels)
    return "、".join(labels[:-1]) + f" 与 {labels[-1]}"


def _is_broad_chapter_request(message: str, matches: List[Dict]) -> bool:
    compact_message = _compact(message)
    if not any(marker in compact_message for marker in ["学习", "学", "了解", "复习", "掌握"]):
        return False
    if any(_compact(topic) in compact_message for topic in BROAD_CHAPTER_TOPICS):
        return True
    return any(_compact(match.get("label", "")) in {_compact(topic) for topic in BROAD_CHAPTER_TOPICS} for match in matches)


def _chapter_payload(unit: Dict) -> Dict:
    chapter = dsa_course_map_service.CHAPTER_BY_ID.get(unit.get("chapter_id", ""), {})
    return {
        "chapter_id": unit.get("chapter_id", ""),
        "chapter_title": chapter.get("title", ""),
    }


def _base_result(scope_level: str, display_topic: str = "", primary_unit: Dict = None, message: str = "") -> Dict:
    primary_unit = primary_unit or {}
    chapter_info = _chapter_payload(primary_unit) if primary_unit else {"chapter_id": "", "chapter_title": ""}
    course_match = (
        dsa_course_map_service.match_dsa_topic(primary_unit.get("title", ""), message)
        if primary_unit
        else {}
    )
    if course_match and display_topic:
        course_match = {
            **course_match,
            "display_topic": display_topic,
            "scope_level": scope_level,
            "should_generate_full_chapter": scope_level == SCOPE_CHAPTER,
        }
    return {
        "scope_level": scope_level,
        "primary_topic": primary_unit.get("title", "") if primary_unit else display_topic,
        "display_topic": display_topic,
        "primary_unit_id": primary_unit.get("unit_id", ""),
        "chapter_id": chapter_info.get("chapter_id", ""),
        "chapter_title": chapter_info.get("chapter_title", ""),
        "prerequisite_units": _resolve_prerequisite_units(primary_unit) if primary_unit else [],
        "related_units": _related_units(primary_unit, chapter_info.get("chapter_id", ""), primary_unit.get("unit_id", "")) if primary_unit else [],
        "compare_units": _units_from_ids(primary_unit.get("compare_units", [])) if primary_unit else [],
        "expansion_policy": "out_of_course_reply" if scope_level == SCOPE_OUT_OF_COURSE else "unit_focused",
        "should_generate_full_chapter": scope_level == SCOPE_CHAPTER,
        "course_match": course_match,
    }


def resolve_topic_scope(message: str, eval_topic: str = "") -> Dict:
    text = str(message or "").strip()
    fallback_topic = course_scope_service.extract_requested_topic(text, eval_topic)
    direct_course_match = dsa_course_map_service.match_dsa_topic(fallback_topic, text)
    if _contains_any(text, OUT_OF_COURSE_MARKERS) and not direct_course_match.get("matched"):
        return {
            "scope_level": SCOPE_OUT_OF_COURSE,
            "primary_topic": fallback_topic or "这个主题",
            "display_topic": fallback_topic or "这个主题",
            "primary_unit_id": "",
            "chapter_id": "",
            "chapter_title": "",
            "prerequisite_units": [],
            "related_units": [],
            "compare_units": [],
            "expansion_policy": "out_of_course_reply",
            "should_generate_full_chapter": False,
            "course_match": {"matched": False, "scope_type": "out_of_course"},
            "reply": course_scope_service.build_out_of_scope_reply(fallback_topic, text),
        }
    matches = _find_unit_matches(" ".join([text, eval_topic or ""]))
    has_full_chapter_marker = _contains_any(text, FULL_CHAPTER_MARKERS)
    has_comparison_marker = _contains_any(text, COMPARISON_MARKERS)
    has_project_marker = _contains_any(text, PROJECT_MARKERS)
    has_diagnostic_marker = _contains_any(text, DIAGNOSTIC_MARKERS)
    has_concept_marker = _contains_any(text, CONCEPT_MARKERS)
    has_broad_chapter_marker = _is_broad_chapter_request(text, matches)

    if has_comparison_marker and matches:
        labels = _comparison_labels(text, matches)
        if len(labels) < 2 and len(matches) >= 2:
            labels = [_explicit_display_label(text, match) for match in matches[:2]]
        if len(labels) < 2 and len(matches) == 1:
            labels = [_explicit_display_label(text, matches[0]), matches[0]["unit"].get("title", "")]
        labels = [label for label in labels if label]
        display_topic = _join_compare_labels(labels[:3]) + " 对比学习" if labels else f"{fallback_topic} 对比学习"
        primary_unit = matches[0]["unit"]
        result = _base_result(SCOPE_COMPARISON, display_topic, primary_unit, text)
        result["compare_units"] = [_unit_payload(match["unit"]) for match in matches[:4]]
        result["expansion_policy"] = "comparison"
        result["should_generate_full_chapter"] = False
        result["course_match"] = {**result["course_match"], "learning_need_type": "comparison"}
        return result

    if has_project_marker and matches:
        primary = next(
            (
                match for match in matches
                if "project" in _compact(match["unit"].get("unit_id", ""))
                or "项目" in match["unit"].get("title", "")
            ),
            matches[0],
        )
        primary_unit = primary["unit"]
        display_topic = primary_unit.get("title", "") or _explicit_display_label(text, primary)
        result = _base_result(SCOPE_PROJECT, display_topic, primary_unit, text)
        result["expansion_policy"] = "project_path_and_code_lab"
        result["course_match"] = {**result["course_match"], "learning_need_type": "project", "requires_code": True}
        return result

    if has_diagnostic_marker and matches:
        primary_unit = matches[0]["unit"]
        display_topic = primary_unit.get("title", "") or _explicit_display_label(text, matches[0])
        scope = SCOPE_DIAGNOSTIC if _contains_any(text, ["诊断", "测评", "测试结果", "作答记录"]) else SCOPE_REMEDIATION
        result = _base_result(scope, display_topic, primary_unit, text)
        result["expansion_policy"] = "diagnostic_feedback_only" if scope == SCOPE_DIAGNOSTIC else "remediation_path_patch"
        result["course_match"] = {**result["course_match"], "learning_need_type": "evaluation" if scope == SCOPE_DIAGNOSTIC else "remediation"}
        return result

    intro_unit_id = (dsa_course_map_service.get_intro_unit() or {}).get("unit_id", "")
    specific_matches = [
        match for match in matches
        if match["unit"].get("unit_id") != intro_unit_id or _compact(match.get("label")) not in {"数据结构与算法", "dsa", "算法", "datastructuresalgorithms"}
    ]
    if not specific_matches and _contains_any(text, COURSE_ONLY_MARKERS):
        intro_unit = dsa_course_map_service.get_intro_unit() or {}
        result = _base_result(SCOPE_COURSE, "《数据结构与算法》课程导学", intro_unit, text)
        result["expansion_policy"] = "course_diagnostic_and_path"
        result["should_generate_full_chapter"] = False
        result["related_units"] = []
        result["course_match"] = {**result["course_match"], "learning_need_type": "course_orientation"}
        return result

    if matches:
        primary = matches[0]
        primary_unit = primary["unit"]
        display_topic = primary_unit.get("title", "") or _explicit_display_label(text, primary)
        if has_full_chapter_marker or has_broad_chapter_marker:
            display_topic = _chapter_payload(primary_unit).get("chapter_title") or display_topic
            result = _base_result(SCOPE_CHAPTER, display_topic, primary_unit, text)
            result["expansion_policy"] = "chapter_learning_path"
            result["should_generate_full_chapter"] = True
            result["course_match"] = {**result["course_match"], "learning_need_type": "path_planning"}
            return result

        scope_level = SCOPE_CONCEPT if has_concept_marker else SCOPE_UNIT
        result = _base_result(scope_level, display_topic, primary_unit, text)
        result["expansion_policy"] = "micro_explanation" if scope_level == SCOPE_CONCEPT else "prerequisite_and_comparison_only"
        result["should_generate_full_chapter"] = False
        return result

    course_match = direct_course_match
    if course_match.get("matched"):
        unit = course_match.get("unit") or dsa_course_map_service.get_unit(course_match.get("unit_id", "")) or {}
        display_topic = unit.get("title") or (fallback_topic if fallback_topic not in {"未确认主题", "当前主题"} else course_match.get("normalized_topic", ""))
        result = _base_result(SCOPE_UNIT, display_topic, unit, text)
        result["course_match"] = {**course_match, "display_topic": display_topic, "scope_level": SCOPE_UNIT}
        return result

    return {
        "scope_level": SCOPE_OUT_OF_COURSE,
        "primary_topic": fallback_topic or "这个主题",
        "display_topic": fallback_topic or "这个主题",
        "primary_unit_id": "",
        "chapter_id": "",
        "chapter_title": "",
        "prerequisite_units": [],
        "related_units": [],
        "compare_units": [],
        "expansion_policy": "out_of_course_reply",
        "should_generate_full_chapter": False,
        "course_match": {"matched": False, "scope_type": "out_of_course"},
        "reply": course_scope_service.build_out_of_scope_reply(fallback_topic, text),
    }
