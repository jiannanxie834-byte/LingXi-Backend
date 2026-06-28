import re
from typing import Dict, List

from app.agents.agent_result_dto import AgentResultDTO


FORBIDDEN_PATTERNS = [
    r"\bdsa_[a-z0-9_]+",
    r"\bsec_[a-z0-9_]+",
    r"\bunit_id\b",
    r"\bunit_ids\b",
    r"\blink_only\b",
    r"\bpending_curation\b",
    r"资源治理信息",
    r"内容安全与防幻觉自检",
    r"教学质量门控",
    r"artifact_id",
    r"resource_id",
    r"course_id",
    r"chapter_id",
    r"section_id",
]


def _sanitize_content(value: str) -> str:
    text = str(value or "")
    for pattern in FORBIDDEN_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.I)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() or "该类资源暂未完善"


def run(outputs: List[Dict]) -> dict:
    outputs = outputs or []
    cleaned = []
    warnings = []
    for item in outputs:
        content = str(item.get("content") or "")
        issues = []
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, content, flags=re.I):
                issues.append(pattern)
        if issues:
            warnings.append(f"{item.get('summary') or '学习资源'} 包含内部字段，已清洗")
        cleaned.append({
            **item,
            "content": _sanitize_content(content),
        })

    dto = AgentResultDTO(
        agent_name="QualityAgent",
        input_summary="学习包学生端展示质量检查",
        output={
            "checked_resources": len(cleaned),
            "cleaned_resources": len(warnings),
            "student_visible": True,
        },
        quality_score=1.0 if not warnings else 0.85,
        warnings=warnings,
    )
    return {"dto": dto, "outputs": cleaned}
