import re
from typing import Dict, List

from app.services.data_services import resource_quality_gate


REVIEW_START = "[[LINGXI_CONTENT_REVIEW]]"
REVIEW_END = "[[/LINGXI_CONTENT_REVIEW]]"

SENSITIVE_TERMS = [
    "违法",
    "暴力",
    "赌博",
    "毒品",
    "色情",
    "歧视",
    "仇恨",
]

FACT_RISK_TERMS = [
    "一定正确",
    "绝对正确",
    "唯一答案",
    "百分之百",
    "最新研究证明",
    "权威数据显示",
]


def _contains_any(text: str, words: List[str]) -> List[str]:
    lowered = (text or "").lower()
    return [word for word in words if word.lower() in lowered]


def _has_structure(content: str) -> bool:
    text = content or ""
    return bool(re.search(r"(^|\n)#{1,3}\s+", text)) or bool(re.search(r"(^|\n)[-0-9]+[.、)]\s+", text))


def review_resource_content(
    *,
    title: str,
    resource_type: str,
    summary: str,
    content: str,
    source: str = "",
    reviewer: str = "内容安全 Agent",
    semantic_result: Dict = None,
) -> Dict:
    text = "\n".join([title or "", resource_type or "", summary or "", content or "", source or ""])
    score = 100
    checks = []
    suggestions = []

    sensitive_hits = _contains_any(text, SENSITIVE_TERMS)
    if sensitive_hits:
        score -= 45
        checks.append(f"敏感内容风险：命中 {', '.join(sensitive_hits[:3])}")
        suggestions.append("请管理员复核是否存在违规、攻击性或不适合教学场景的表达。")
    else:
        checks.append("敏感内容：未发现明显风险词")

    fact_hits = _contains_any(text, FACT_RISK_TERMS)
    if fact_hits:
        score -= 12
        checks.append(f"事实表达风险：存在绝对化表述 {', '.join(fact_hits[:3])}")
        suggestions.append("将绝对化结论改为可验证、可追溯的教学表达，并补充依据。")
    else:
        checks.append("事实表达：未发现明显绝对化结论")

    if len((content or "").strip()) < 120:
        score -= 12
        checks.append("完整性：正文偏短")
        suggestions.append("建议补充学习目标、关键概念、示例、练习或产出要求。")
    else:
        checks.append("完整性：正文长度满足基本教学说明")

    if not (source or "").strip():
        score -= 8
        checks.append("来源标注：缺少明确知识来源")
        suggestions.append("建议标注课程章节、教材、课堂讲义、官方文档或知识库条目。")
    else:
        checks.append("来源标注：已提供知识来源")

    if not _has_structure(content):
        score -= 6
        checks.append("结构化：缺少标题或列表结构")
        suggestions.append("建议使用 Markdown 标题、列表、步骤或表格增强可读性。")
    else:
        checks.append("结构化：具备可读结构")

    resource_type_text = resource_type or ""
    if "视频" in resource_type_text:
        video_markers = ["原始链接", "公开视频", "观看重点", "观看任务", "copyright"]
        if not any(marker in (content or "") + (source or "") for marker in video_markers):
            score -= 10
            checks.append("视频资源：缺少原始链接、观看重点或版权边界说明")
            suggestions.append("视频类 Artifact 只允许提供公开原始入口、观看重点和学习任务，不得复制或重新托管视频内容。")
        else:
            checks.append("视频资源：包含公开入口或观看任务说明")

    if "动画" in resource_type_text:
        animation_markers = ["animation_type", "分镜", "步骤", "参数", "交互", "高亮"]
        if not any(marker in (content or "") for marker in animation_markers):
            score -= 10
            checks.append("动画资源：缺少可渲染规格或分镜信息")
            suggestions.append("动画类 Artifact 应写清可视化对象、关键步骤、交互参数和同步解释。")
        else:
            checks.append("动画资源：包含可渲染规格或分镜信息")

    if semantic_result:
        semantic_review = resource_quality_gate.validate_resource_semantics(
            {
                "title": title,
                "type": resource_type,
                "summary": summary,
                "content": content,
                "source": source,
            },
            {
                **semantic_result,
                "resource_type": resource_type,
            },
        )
        checks.extend([f"语义一致性：{item}" for item in semantic_review.get("issues", [])])
        suggestions.extend(semantic_review.get("suggestions", []))
        if semantic_review.get("fatal"):
            score -= 40

    score = max(0, min(100, score))
    if sensitive_hits or score < 70:
        risk_level = "高风险"
    elif score < 85:
        risk_level = "中风险"
    else:
        risk_level = "低风险"

    return {
        "reviewer": reviewer,
        "score": score,
        "risk_level": risk_level,
        "checks": checks,
        "suggestions": suggestions or ["建议管理员按课程标准进行最终术语与事实复核。"],
        "requires_human_review": True,
    }


def _format_review_block(review: Dict) -> str:
    checks = review.get("checks") or []
    suggestions = review.get("suggestions") or []
    lines = [
        REVIEW_START,
        "## 内容安全与防幻觉自检",
        f"- 审核 Agent：{review.get('reviewer', '内容安全 Agent')}",
        f"- 风险等级：{review.get('risk_level', '待复核')}",
        f"- 自检分数：{review.get('score', 0)}/100",
        f"- 人工复核：{'需要' if review.get('requires_human_review', True) else '可选'}",
        "",
        "### 自检项",
    ]
    lines.extend([f"- {item}" for item in checks])
    lines.extend(["", "### 审核建议"])
    lines.extend([f"- {item}" for item in suggestions])
    lines.append(REVIEW_END)
    return "\n".join(lines)


def strip_review_block(notes: str) -> str:
    text = notes or ""
    pattern = re.compile(
        rf"\n?{re.escape(REVIEW_START)}.*?{re.escape(REVIEW_END)}\n?",
        re.S,
    )
    return pattern.sub("\n", text).strip()


def attach_review_note(notes: str, review: Dict) -> str:
    base_notes = strip_review_block(notes)
    block = _format_review_block(review)
    return "\n\n".join(part for part in [base_notes, block] if part)


def extract_review(notes: str) -> Dict:
    text = notes or ""
    match = re.search(
        rf"{re.escape(REVIEW_START)}(?P<body>.*?){re.escape(REVIEW_END)}",
        text,
        re.S,
    )
    if not match:
        return {}

    body = match.group("body")
    risk_match = re.search(r"风险等级：([^\n]+)", body)
    score_match = re.search(r"自检分数：(\d+)", body)
    reviewer_match = re.search(r"审核 Agent：([^\n]+)", body)
    human_review_match = re.search(r"人工复核：([^\n]+)", body)

    checks_section = re.search(r"### 自检项(?P<checks>.*?)(### 审核建议|$)", body, re.S)
    suggestions_section = re.search(r"### 审核建议(?P<suggestions>.*)$", body, re.S)

    def parse_list(section):
        if not section:
            return []
        return [
            line.strip()[2:].strip()
            for line in section.splitlines()
            if line.strip().startswith("- ")
        ]

    return {
        "reviewer": reviewer_match.group(1).strip() if reviewer_match else "内容安全 Agent",
        "risk_level": risk_match.group(1).strip() if risk_match else "待复核",
        "score": int(score_match.group(1)) if score_match else 0,
        "requires_human_review": human_review_match.group(1).strip() == "需要" if human_review_match else True,
        "checks": parse_list(checks_section.group("checks") if checks_section else ""),
        "suggestions": parse_list(suggestions_section.group("suggestions") if suggestions_section else ""),
    }
