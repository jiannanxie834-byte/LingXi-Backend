from typing import Dict, List

from app.agents.agent_result_dto import AgentResultDTO
from app.services.data_services import resource_artifact_type_service as artifact_types


EMPTY_TEXT = "该类资源暂未完善"


def _clean_text(value: str) -> str:
    return str(value or "").strip() or EMPTY_TEXT


INTERNAL_KEYS = {
    "id",
    "exercise_id",
    "task_id",
    "video_id",
    "chapter_id",
    "section_ids",
    "unit_ids",
}


def _public_record(item: Dict) -> Dict:
    return {
        key: value
        for key, value in (item or {}).items()
        if key not in INTERNAL_KEYS and value not in ("", None, [], {})
    }


def _list_value(value) -> str:
    if isinstance(value, list):
        return "；".join(str(item) for item in value if str(item or "").strip())
    return str(value or "").strip()


def _records_markdown(title: str, items: List[Dict], labels: Dict[str, str]) -> str:
    if not items:
        return EMPTY_TEXT
    lines = [f"# {title}", ""]
    for index, item in enumerate(items, start=1):
        public_item = _public_record(item)
        item_title = public_item.get("title") or public_item.get("task_type") or public_item.get("type") or f"条目 {index}"
        lines.extend([f"## {index}. {item_title}", ""])
        for field, label in labels.items():
            if field not in public_item:
                continue
            value = _list_value(public_item.get(field))
            if not value:
                continue
            lines.extend([f"### {label}", "", value, ""])
    return "\n".join(lines).strip()


def _exercise_markdown(items: List[Dict]) -> str:
    return _records_markdown(
        "练习题集",
        items,
        {
            "type": "题型",
            "difficulty": "难度",
            "tags": "标签",
            "stem": "题目",
            "answer": "答案",
            "explanation": "解析",
            "common_mistakes": "常见错误",
        },
    )


def _code_lab_markdown(items: List[Dict]) -> str:
    return _records_markdown(
        "代码任务",
        items,
        {
            "language": "语言",
            "task_type": "任务类型",
            "difficulty": "难度",
            "starter_code": "起始代码",
            "student_tasks": "学生任务",
            "solution": "参考答案",
        },
    )


def _video_guide_markdown(retrieval: Dict) -> str:
    guide = _clean_text(retrieval.get("reading_video_guide") or "")
    videos = retrieval.get("video_items") or []
    if guide == EMPTY_TEXT and not videos:
        return EMPTY_TEXT
    lines = [guide] if guide != EMPTY_TEXT else ["# 视频与阅读指南", ""]
    if videos:
        lines.extend(["", "## 匹配视频入口", ""])
        for item in videos:
            public_item = _public_record(item)
            lines.extend([
                f"- [{public_item.get('title') or '公开视频'}]({public_item.get('source_url') or '#'})",
                f"  - 平台：{public_item.get('platform') or '公开视频'}",
                f"  - 观看重点：{_list_value(public_item.get('watch_focus')) or '按本节主题观看'}",
            ])
    return "\n".join(lines).strip()


def _remediation_markdown(retrieval: Dict) -> str:
    metadata = retrieval.get("metadata") or {}
    objectives = metadata.get("objectives") or {}
    assessment = metadata.get("assessment") or {}
    misconceptions = metadata.get("misconceptions") or {}
    lines = ["# 诊断与补弱报告", ""]

    objective_items = objectives.get("objectives") or []
    if objective_items:
        lines.extend(["## 课程目标", ""])
        lines.extend([f"- {item}" for item in objective_items])
        lines.append("")

    assessment_items = assessment.get("assessment_points") or []
    if assessment_items:
        lines.extend(["## 测评点", ""])
        lines.extend([f"- {item}" for item in assessment_items])
        lines.append("")

    misconception_items = misconceptions.get("misconceptions") or []
    if misconception_items:
        lines.extend(["## 常见误区与纠正", ""])
        for item in misconception_items:
            public_item = _public_record(item)
            title = public_item.get("title")
            correction = public_item.get("correction")
            if title:
                lines.append(f"- {title}")
            if correction:
                lines.append(f"  - 纠正：{correction}")
        lines.append("")

    content = "\n".join(lines).strip()
    return content if content != "# 诊断与补弱报告" else EMPTY_TEXT


def _summary_for(resource_type: str, location: Dict) -> str:
    topic = location.get("topic") or "当前学习主题"
    mapping = {
        artifact_types.COURSE_NOTE: f"从课程资源库匹配「{topic}」对应小节正文。",
        artifact_types.MIND_MAP: f"从课程资源库匹配「{topic}」所在章节思维导图。",
        artifact_types.EXERCISE_SET: f"从课程资源库匹配「{topic}」相关练习题。",
        artifact_types.CODE_LAB: f"从课程资源库匹配「{topic}」相关代码任务。",
        artifact_types.DIAGNOSTIC_REPORT: f"从课程资源库匹配「{topic}」章节目标、测评点与常见误区。",
        artifact_types.PERSONALIZED_VIDEO_GUIDE: f"从课程资源库匹配「{topic}」阅读与视频指南。",
    }
    return mapping.get(resource_type, f"从课程资源库匹配「{topic}」学习资源。")


def run(resources: List[Dict], location: Dict, profile: Dict, retrieval: Dict) -> dict:
    resources = resources or []
    location = location or {}
    profile = profile or {}
    retrieval = retrieval or {}
    packaged = []
    for item in resources:
        resource_type = artifact_types.normalize_artifact_type(item.get("type") or "")
        if resource_type == artifact_types.COURSE_NOTE:
            content = _clean_text(retrieval.get("section_content"))
        elif resource_type == artifact_types.MIND_MAP:
            content = _clean_text(retrieval.get("mind_map"))
        elif resource_type == artifact_types.EXERCISE_SET:
            content = _exercise_markdown(retrieval.get("exercises") or [])
        elif resource_type == artifact_types.CODE_LAB:
            content = _code_lab_markdown(retrieval.get("code_tasks") or [])
        elif resource_type == artifact_types.DIAGNOSTIC_REPORT:
            content = _remediation_markdown(retrieval)
        elif resource_type == artifact_types.PERSONALIZED_VIDEO_GUIDE:
            content = _video_guide_markdown(retrieval)
        else:
            content = EMPTY_TEXT
        packaged.append({
            "summary": item.get("summary") or _summary_for(resource_type, location),
            "content": content,
            "source": "数据结构与算法课程资源库",
            "assembly_policy": "library_verbatim_selection",
            "missing": content == EMPTY_TEXT,
        })

    dto = AgentResultDTO(
        agent_name="PackageAgent",
        input_summary=location.get("topic") or "数据结构与算法学习包",
        output={
            "resource_count": len(packaged),
            "types": [item.get("type") for item in resources],
            "assembly_policy": "library_verbatim_selection",
            "personalization_scope": {
                "topic": location.get("topic") or "",
                "chapter_title": location.get("chapter_title") or "",
                "section_title": location.get("section_title") or "",
                "profile_used": bool(profile),
            },
            "missing_count": sum(1 for item in packaged if item.get("missing")),
        },
        evidence_refs=location.get("evidence_refs") or [],
        quality_score=1.0 if all(not item.get("missing") for item in packaged) else 0.8,
        warnings=["部分资源类型暂未完善"] if any(item.get("missing") for item in packaged) else [],
    )
    return {"dto": dto, "outputs": packaged}
