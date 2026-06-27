import json
import re
from pathlib import Path
from typing import Dict, List, Optional


COURSE_ID = "deep_learning_v2"
COURSE_NAME = "深度学习"
COURSE_DISPLAY_NAME = "《深度学习》"
COURSE_POSITIONING = "面向人工智能、计算机科学与技术、软件工程、电子信息等专业本科高年级或研究生低年级学生的专业核心课程"


DEEP_LEARNING_CHAPTERS = [
    {"chapter_id": "chapter_01_intro", "title": "第 1 章 深度学习导论与课程学习诊断"},
    {"chapter_id": "chapter_02_pytorch_foundation", "title": "第 2 章 Python、NumPy 与 PyTorch 基础"},
    {"chapter_id": "chapter_03_neural_network_basics", "title": "第 3 章 神经网络基础与向量化计算"},
    {"chapter_id": "chapter_04_deep_network_and_backprop", "title": "第 4 章 深层神经网络与反向传播"},
    {"chapter_id": "chapter_05_regularization_and_generalization", "title": "第 5 章 正则化、初始化与泛化"},
    {"chapter_id": "chapter_06_optimization", "title": "第 6 章 优化算法与超参数调试"},
    {"chapter_id": "chapter_07_cnn_foundation", "title": "第 7 章 CNN 基础：卷积、池化与图像张量"},
    {"chapter_id": "chapter_08_cnn_architectures_and_cv_practice", "title": "第 8 章 经典 CNN 架构与图像分类实践"},
    {"chapter_id": "chapter_09_cv_advanced_tasks", "title": "第 9 章 计算机视觉进阶任务"},
    {"chapter_id": "chapter_10_sequence_models", "title": "第 10 章 序列模型：RNN、GRU 与 LSTM"},
    {"chapter_id": "chapter_11_attention_transformer", "title": "第 11 章 Attention、Transformer 与 NLP 基础"},
    {"chapter_id": "chapter_12_final_project", "title": "第 12 章 综合项目与课程成果输出"},
]


DEEP_LEARNING_UNITS = []


COURSE_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "knowledge_base"
    / "deep_learning_v2"
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
                item.setdefault("learning_outcomes", [])
                item.setdefault("common_misconceptions", [])
                item.setdefault("resource_focus", [])
                item.setdefault("formulas", [])
                item.setdefault("evidence_refs", [])
                units.append(item)
    return units


_JSONL_UNITS = _load_units_from_jsonl()
if _JSONL_UNITS:
    DEEP_LEARNING_UNITS = _JSONL_UNITS

CHAPTER_BY_ID = {chapter["chapter_id"]: chapter for chapter in DEEP_LEARNING_CHAPTERS}
UNIT_BY_ID = {unit["unit_id"]: unit for unit in DEEP_LEARNING_UNITS}
DEEP_LEARNING_COURSE_MAP = [
    {
        "chapter_id": chapter["chapter_id"],
        "chapter": chapter["title"],
        "topics": [unit["title"] for unit in DEEP_LEARNING_UNITS if unit["chapter_id"] == chapter["chapter_id"]],
        "aliases": [
            alias
            for unit in DEEP_LEARNING_UNITS
            if unit["chapter_id"] == chapter["chapter_id"]
            for alias in unit.get("aliases", [])
        ],
    }
    for chapter in DEEP_LEARNING_CHAPTERS
]


def _compact(value: str) -> str:
    return re.sub(r"[\s_\-·：:，,。！？!?.、/\\（）()《》]+", "", str(value or "").lower())


def _tokenize(value: str) -> List[str]:
    text = str(value or "").lower()
    return re.findall(r"[a-z0-9+#.]+|[\u4e00-\u9fff]{2,}", text)


def _intent_from_message(message: str) -> str:
    compact = _compact(message)
    if any(word in compact for word in ["错题", "错因", "做错", "算错", "不会这类题", "总是错"]):
        return "evaluation"
    if any(word in compact for word in ["项目", "实战", "两周", "完成一个", "做一个"]):
        return "project"
    if any(word in compact for word in ["代码", "pytorch", "实验", "实现", "训练", "调参"]):
        return "code_lab"
    if any(word in compact for word in ["练习", "题", "刷题", "测验"]):
        return "practice"
    if any(word in compact for word in ["规划", "路线", "计划", "安排", "怎么学", "学习路径", "我要学", "想学", "帮我学", "系统学习", "入门", "怎么入门"]):
        return "path_planning"
    if any(word in compact for word in ["生成", "资源", "资料", "课件", "ppt", "导图", "视频", "动画", "多模态"]):
        return "resource_generation"
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
        + [(concept, 0.04) for concept in unit.get("core_concepts", [])]
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
            if alias_len <= 2:
                alias_score = max(alias_score, 0.62 + boost)
            elif alias_len <= 4:
                alias_score = max(alias_score, 0.72 + boost)
            else:
                alias_score = max(alias_score, min(0.96, 0.72 + alias_len / 100 + boost))
            matched_aliases.append(alias)
    score = alias_score

    text_tokens = set(_tokenize(text))
    concept_tokens = set()
    for field in ["core_concepts", "prerequisites", "related_units", "compare_units", "learning_outcomes", "resource_focus"]:
        for item in unit.get(field, []):
            concept_tokens.update(_tokenize(item))
    token_hits = text_tokens & concept_tokens
    if token_hits:
        score += min(0.25, 0.05 * len(token_hits))

    title_tokens = set(_tokenize(unit.get("title", "")))
    title_hits = text_tokens & title_tokens
    if title_hits:
        score += min(0.18, 0.06 * len(title_hits))

    # Project-like requests should prefer project units unless the user explicitly
    # asks for a narrow concept explanation.
    compact_unit_title = _compact(unit.get("title", ""))
    compact_unit_id = _compact(unit.get("unit_id", ""))
    if any(word in compact_text for word in ["项目", "实战", "两周"]):
        if "project" in compact_unit_id:
            score += 0.45
        if "项目" in compact_unit_title:
            score += 0.25
    if "图像分类" in compact_text and "projectimageclassification" in compact_unit_id:
        score += 0.5
    if "图像分类" in compact_text and "pytorch" in compact_text and "pytorch" in compact_unit_title:
        score += 0.25

    return {
        "score": round(score, 3),
        "aliases": list(dict.fromkeys(matched_aliases)),
    }


def get_unit(unit_id: str) -> Optional[Dict]:
    unit = UNIT_BY_ID.get(unit_id)
    return dict(unit) if unit else None


def get_intro_unit() -> Dict:
    for unit in DEEP_LEARNING_UNITS:
        title = _compact(unit.get("title", ""))
        aliases = {_compact(alias) for alias in unit.get("aliases", [])}
        if unit.get("chapter_id") == "chapter_01_intro" and (
            "深度学习课程" in title
            or "课程地图" in title
            or {"深度学习", "deeplearning", "dl"} & aliases
        ):
            return dict(unit)
    return dict(DEEP_LEARNING_UNITS[0]) if DEEP_LEARNING_UNITS else {}


def list_units() -> List[Dict]:
    return [dict(unit) for unit in DEEP_LEARNING_UNITS]


def is_deep_learning_scope(topic: str = "", message: str = "") -> bool:
    return bool(match_deep_learning_topic(topic, message).get("matched"))


def match_deep_learning_topic(topic: str = "", message: str = "") -> Dict:
    raw_topic = str(topic or "").strip()
    raw_message = str(message or "").strip()
    combined = "\n".join([raw_topic, raw_message])
    compact = _compact(combined)
    if not compact:
        return {"matched": False}

    best_unit = None
    best = {"score": 0.0, "aliases": []}
    for unit in DEEP_LEARNING_UNITS:
        current = _score_unit(unit, raw_message, raw_topic)
        if current["score"] > best["score"]:
            best_unit = unit
            best = current

    if not best_unit:
        return {"matched": False}

    # A general deep-learning request is still in scope even if it does not name a
    # detailed knowledge unit yet.
    general_scope = any(alias in compact for alias in ["深度学习", "deeplearning", "神经网络"])
    if best["score"] < 0.58 and not general_scope:
        return {"matched": False}

    if best["score"] < 0.58 and general_scope:
        best_unit = get_intro_unit()
        best = {"score": 0.62, "aliases": ["深度学习"]}

    chapter = CHAPTER_BY_ID.get(best_unit["chapter_id"], {})
    need_type = _intent_from_message(combined)
    requires_code = (
        need_type in {"code_lab", "project"}
        or any(word in compact for word in ["代码", "pytorch", "torch", "实验", "实现", "训练", "项目"])
        or "代码实验" in " ".join(best_unit.get("resource_focus", []))
    )
    requires_multimodal = (
        any(word in compact for word in ["图解", "动画", "导图", "视频", "多模态", "可视化"])
        or any(item in best_unit.get("resource_focus", []) for item in ["图解", "交互动画", "视频推荐"])
    )

    confidence = min(best["score"], 1.0)
    return {
        "matched": True,
        "course_id": COURSE_ID,
        "course_name": COURSE_NAME,
        "course_display_name": COURSE_DISPLAY_NAME,
        "raw_topic": raw_topic or raw_message,
        "normalized_topic": best_unit["title"],
        "chapter_id": best_unit["chapter_id"],
        "chapter": chapter.get("title", ""),
        "unit_id": best_unit["unit_id"],
        "unit": dict(best_unit),
        "topic": best_unit["title"],
        "intent": need_type,
        "learning_need_type": need_type,
        "scope_type": "in_course",
        "difficulty": best_unit.get("difficulty", "beginner"),
        "requires_code": requires_code,
        "requires_multimodal": requires_multimodal,
        "confidence": round(confidence, 2),
        "matched_aliases": best["aliases"],
        "matched_alias": best["aliases"][0] if best["aliases"] else "",
        "core_topics": best_unit.get("core_concepts", []),
        "prerequisites": best_unit.get("prerequisites", []),
        "resource_focus": best_unit.get("resource_focus", []),
        "practice_tasks": [item for item in [best_unit.get("code_lab", "")] + best_unit.get("exercise_blueprints", []) if item],
        "learning_outcomes": best_unit.get("learning_outcomes", []),
        "common_misconceptions": best_unit.get("common_misconceptions", []),
        "related_units": best_unit.get("related_units", []),
        "compare_units": best_unit.get("compare_units", []),
        "evidence_refs": best_unit.get("evidence_refs", []),
        "visual_suggestions": best_unit.get("visual_suggestions", []),
        "formulas": best_unit.get("formulas", []),
    }


def format_course_map_for_prompt(course_match: Dict) -> str:
    if not course_match or not course_match.get("matched"):
        return f"未匹配到{COURSE_DISPLAY_NAME}课程图谱章节。"

    unit = course_match.get("unit") or {}
    return "\n".join([
        f"课程：{COURSE_DISPLAY_NAME}",
        f"章节：{course_match.get('chapter') or unit.get('chapter_id') or ''}",
        f"知识单元：{course_match.get('normalized_topic') or course_match.get('topic') or unit.get('title') or ''}",
        f"知识单元 ID：{course_match.get('unit_id') or unit.get('unit_id') or ''}",
        f"核心概念：{'、'.join(course_match.get('core_topics') or unit.get('core_concepts') or [])}",
        f"前置知识：{'、'.join(course_match.get('prerequisites') or unit.get('prerequisites') or []) or '无'}",
        f"相关知识：{'、'.join(course_match.get('related_units') or unit.get('related_units') or []) or '无'}",
        f"对比知识：{'、'.join(course_match.get('compare_units') or unit.get('compare_units') or []) or '无'}",
        f"学习产出：{'；'.join(course_match.get('learning_outcomes') or unit.get('learning_outcomes') or [])}",
        f"常见误区：{'；'.join(course_match.get('common_misconceptions') or unit.get('common_misconceptions') or [])}",
        f"推荐资源重点：{'、'.join(course_match.get('resource_focus') or unit.get('resource_focus') or [])}",
        f"推荐实践任务：{'；'.join(course_match.get('practice_tasks') or [])}",
    ])


def course_map_payload() -> Dict:
    chapters = []
    for chapter in DEEP_LEARNING_CHAPTERS:
        units = [
            dict(unit)
            for unit in DEEP_LEARNING_UNITS
            if unit.get("chapter_id") == chapter["chapter_id"]
        ]
        chapters.append({**chapter, "units": units})
    return {
        "course_id": COURSE_ID,
        "course_name": COURSE_NAME,
        "course_display_name": COURSE_DISPLAY_NAME,
        "course_positioning": COURSE_POSITIONING,
        "chapters": chapters,
        "units": list_units(),
        "unit_count": len(DEEP_LEARNING_UNITS),
    }
