import json
import re
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.schemas import EvaluationRecord
from app.services.data_services import (
    dsa_resource_policy_service,
    resource_artifact_type_service as artifact_types,
)


FEEDBACK_RESOURCE_TYPE = artifact_types.DIAGNOSTIC_REPORT

BASE_LEARNING_RESOURCE_TYPES = [
    artifact_types.COURSE_NOTE,
    artifact_types.MIND_MAP,
    artifact_types.EXERCISE_SET,
    artifact_types.READING_PACK,
    artifact_types.CODE_LAB,
    artifact_types.PPT_OUTLINE,
    artifact_types.VIDEO_RECOMMENDATION,
    artifact_types.PERSONALIZED_VIDEO_GUIDE,
    artifact_types.INTERACTIVE_ANIMATION,
    artifact_types.ANIMATION_STORYBOARD,
    artifact_types.PROJECT_BRIEF,
]

DEPRECATED_RESOURCE_TYPES = artifact_types.DEPRECATED_ARTIFACT_TYPES

FEEDBACK_INTENTS = {"学习评价", "错题诊断", "反馈分析", "补弱路线", "evaluation"}

WRONG_QUESTION_MARKERS = {
    "错题",
    "错因",
    "做错",
    "答错",
    "写错",
    "错了",
    "不会这类题",
    "不会做",
    "不懂",
    "看不懂",
    "没理解",
    "理解不了",
    "学不会",
    "分析错因",
    "哪里错",
    "为什么错",
}

QUIZ_RESULT_MARKERS = {
    "测验结果",
    "测试结果",
    "作答记录",
    "答题记录",
    "评价结果",
    "诊断得分",
}


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").lower())


def _safe_json_load(value, default):
    try:
        return json.loads(value) if value else default
    except Exception:
        return default


def _topic_matches(topic: str, text: str) -> bool:
    topic_compact = _compact(topic)
    text_compact = _compact(text)
    if not topic_compact or topic_compact == "未确认主题":
        return False
    if topic_compact in text_compact:
        return True

    topic_chars = {char for char in topic_compact if "\u4e00" <= char <= "\u9fff"}
    if len(topic_chars) <= 2:
        return False
    text_chars = {char for char in text_compact if "\u4e00" <= char <= "\u9fff"}
    return len(topic_chars & text_chars) >= 2


def _record_matches(record: EvaluationRecord, topic: str, subject_category: str) -> bool:
    text = "\n".join([
        record.topic or "",
        record.level or "",
        record.weak_points or "",
        record.suggestions or "",
        record.wrong_notes or "",
    ])
    if _topic_matches(topic, text):
        return True

    subject_aliases = {
        "computer_science": [
            "数据结构",
            "算法",
            "复杂度",
            "数组",
            "链表",
            "栈",
            "队列",
            "递归",
            "回溯",
            "排序",
            "二分查找",
            "哈希表",
            "堆",
            "二叉树",
            "图",
            "BFS",
            "DFS",
            "Dijkstra",
            "动态规划",
            "KMP",
        ],
    }.get(subject_category, [])
    text_compact = _compact(text)
    return any(_compact(alias) in text_compact for alias in subject_aliases)


def _has_meaningful_answers(record: EvaluationRecord) -> bool:
    answers = _safe_json_load(record.answers_json, {})
    if isinstance(answers, dict):
        return any(str(value or "").strip() for value in answers.values())
    if isinstance(answers, list):
        return bool(answers)
    return bool(answers)


def has_feedback_context(context: dict) -> bool:
    return any([
        context.get("has_evaluation_record") is True,
        context.get("has_wrong_question") is True,
        context.get("has_quiz_result") is True,
        context.get("user_submitted_feedback") is True,
        context.get("intent") in FEEDBACK_INTENTS,
    ])


def should_generate_feedback_report(context: dict) -> bool:
    return any([
        context.get("explicit_wrong_context") is True,
        context.get("explicit_quiz_context") is True,
        context.get("user_submitted_feedback") is True,
        context.get("intent") in FEEDBACK_INTENTS,
    ])


def select_resource_types(context: dict) -> List[str]:
    if (
        context.get("course_id") == "data_structures_algorithms"
        or context.get("dsa_course_map")
        or (context.get("ai_course_map") or {}).get("course_id") == "data_structures_algorithms"
    ):
        return dsa_resource_policy_service.select_dsa_resource_types(context)

    semantic_map = context.get("dsa_course_map") or context.get("ai_course_map") or {}
    learning_need_type = context.get("learning_need_type") or semantic_map.get("learning_need_type")
    scope_level = context.get("scope_level") or semantic_map.get("scope_level")
    requires_code = bool(context.get("requires_code") or semantic_map.get("requires_code"))
    requires_multimodal = bool(context.get("requires_multimodal") or semantic_map.get("requires_multimodal"))

    if scope_level == "course":
        resource_types = [
            artifact_types.COURSE_NOTE,
            artifact_types.MIND_MAP,
            artifact_types.EXERCISE_SET,
            artifact_types.READING_PACK,
        ]
        if should_generate_feedback_report(context):
            resource_types.append(FEEDBACK_RESOURCE_TYPE)
        return list(dict.fromkeys(resource_types))

    if scope_level == "comparison":
        return [
            artifact_types.COURSE_NOTE,
            artifact_types.MIND_MAP,
            artifact_types.EXERCISE_SET,
            artifact_types.READING_PACK,
            artifact_types.VIDEO_RECOMMENDATION,
        ]

    if scope_level == "project":
        return [
            artifact_types.PROJECT_BRIEF,
            artifact_types.CODE_LAB,
            artifact_types.COURSE_NOTE,
            artifact_types.EXERCISE_SET,
            artifact_types.PPT_OUTLINE,
            artifact_types.VIDEO_RECOMMENDATION,
        ]

    if scope_level == "diagnostic":
        resource_types = [artifact_types.EXERCISE_SET]
        if should_generate_feedback_report(context):
            resource_types.append(FEEDBACK_RESOURCE_TYPE)
        return list(dict.fromkeys(resource_types))

    if scope_level in {"unit", "concept"} and learning_need_type == "practice":
        return [artifact_types.EXERCISE_SET]

    if scope_level in {"unit", "concept"} and learning_need_type == "code_lab":
        return [artifact_types.CODE_LAB, artifact_types.EXERCISE_SET, artifact_types.COURSE_NOTE]

    resource_types = [
        artifact_types.COURSE_NOTE,
        artifact_types.MIND_MAP,
        artifact_types.EXERCISE_SET,
        artifact_types.READING_PACK,
        artifact_types.PPT_OUTLINE,
        artifact_types.VIDEO_RECOMMENDATION,
        artifact_types.PERSONALIZED_VIDEO_GUIDE,
    ]

    if requires_code or learning_need_type in {"code_lab", "project", "practice"}:
        resource_types.append(artifact_types.CODE_LAB)

    if requires_multimodal or learning_need_type in {"resource_generation", "project", "path_planning"}:
        resource_types.extend([
            artifact_types.INTERACTIVE_ANIMATION,
            artifact_types.ANIMATION_STORYBOARD,
        ])

    if learning_need_type in {"project", "code_lab"} or "项目" in _compact(context.get("topic", "")):
        resource_types.append(artifact_types.PROJECT_BRIEF)

    if should_generate_feedback_report(context):
        resource_types.append(FEEDBACK_RESOURCE_TYPE)
    return list(dict.fromkeys(resource_types))


def build_generation_context(
    db: Session,
    username: str,
    topic: str,
    subject_category: str,
    intent: str,
    message: str = "",
) -> Dict:
    compact_message = _compact(message)
    explicit_wrong_context = any(_compact(marker) in compact_message for marker in WRONG_QUESTION_MARKERS)
    explicit_quiz_context = any(_compact(marker) in compact_message for marker in QUIZ_RESULT_MARKERS)

    context = {
        "topic": topic,
        "subject_category": subject_category,
        "intent": intent,
        "has_evaluation_record": False,
        "has_wrong_question": explicit_wrong_context,
        "has_quiz_result": explicit_quiz_context,
        "explicit_wrong_context": explicit_wrong_context,
        "explicit_quiz_context": explicit_quiz_context,
        "user_submitted_feedback": explicit_wrong_context or explicit_quiz_context or intent in FEEDBACK_INTENTS,
        "evidence_sources": [],
    }
    if explicit_wrong_context:
        context["evidence_sources"].append("本轮输入包含错题/错因描述")
    if explicit_quiz_context:
        context["evidence_sources"].append("本轮输入包含测验或评价结果")

    if not db or not username:
        return context

    try:
        records = (
            db.query(EvaluationRecord)
            .filter(
                EvaluationRecord.username == username,
                ~EvaluationRecord.diagnosis_type.like("legacy_invalid%"),
            )
            .order_by(EvaluationRecord.created_at.desc())
            .limit(20)
            .all()
        )
    except Exception:
        return context

    matched_records = [
        record
        for record in records
        if _record_matches(record, topic, subject_category)
    ]
    if matched_records:
        context["has_evaluation_record"] = True
        context["evidence_sources"].append(f"同主题学习评价记录 {len(matched_records)} 条")

    wrong_records = [record for record in matched_records if (record.wrong_notes or "").strip()]
    if wrong_records:
        context["has_wrong_question"] = True
        context["evidence_sources"].append(f"同主题错题/自测描述 {len(wrong_records)} 条")

    quiz_records = [record for record in matched_records if _has_meaningful_answers(record)]
    if quiz_records:
        context["has_quiz_result"] = True
        context["evidence_sources"].append(f"同主题作答记录 {len(quiz_records)} 条")

    context["evidence_sources"] = list(dict.fromkeys(context["evidence_sources"]))
    return context
