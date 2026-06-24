import json
import re
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.schemas import EvaluationRecord


FEEDBACK_RESOURCE_TYPE = "错题诊断与学习反馈报告"

BASE_LEARNING_RESOURCE_TYPES = [
    "专业课程讲解文档",
    "知识点思维导图",
    "不同类型练习题目",
    "拓展阅读材料",
    "学科实践应用任务",
]

DEPRECATED_RESOURCE_TYPES = ["多模态学习包"]

FEEDBACK_INTENTS = {"学习评价", "错题诊断", "反馈分析", "补弱路线"}

WRONG_QUESTION_MARKERS = {
    "错题",
    "错因",
    "做错",
    "答错",
    "写错",
    "错了",
    "不会这类题",
    "不会做",
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
        "foreign_language": ["法语", "英语", "日语", "德语", "西班牙语", "韩语", "俄语", "意大利语"],
        "computer_science": ["人工智能", "机器学习", "深度学习", "信息安全", "编程", "算法", "数据库"],
        "mathematics": ["数学", "高等数学", "线性代数", "概率论", "微积分"],
        "physics": ["物理", "大学物理", "力学", "电磁学", "光学"],
        "general_course": ["心理学", "管理学", "经济学", "历史", "文学", "哲学"],
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


def select_resource_types(context: dict) -> List[str]:
    resource_types = list(BASE_LEARNING_RESOURCE_TYPES)
    if has_feedback_context(context):
        resource_types.append(FEEDBACK_RESOURCE_TYPE)
    return resource_types


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
            .filter(EvaluationRecord.username == username)
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
