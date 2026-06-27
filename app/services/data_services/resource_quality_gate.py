import re
from typing import Dict, List

from app.services.data_services import (
    deep_learning_course_map_service,
    deep_learning_resource_blueprint,
    resource_artifact_type_service as artifact_types,
    resource_policy_service,
)


CODE_REQUIRED_TERMS = ["实验目标", "环境依赖", "运行方式", "训练流程", "代码", "实验报告"]
EXERCISE_REQUIRED_TERMS = ["题", "答案", "解析", "知识点"]
READING_REQUIRED_TERMS = ["阅读", "教材", "公开", "顺序", "目标"]
PROJECT_REQUIRED_TERMS = ["项目", "目标", "任务", "验收", "提交", "Rubric"]
VIDEO_REQUIRED_TERMS = ["原始链接", "公开视频", "推荐片段", "版权"]
ANIMATION_REQUIRED_TERMS = ["animation", "动画", "步骤", "高亮", "规格"]
UNSUPPORTED_LEVEL_TERMS = ["进阶学习者", "高阶学习者", "已掌握", "已经具备"]
TEACHING_REVIEW_START = "[[LINGXI_TEACHING_QUALITY_REVIEW]]"
TEACHING_REVIEW_END = "[[/LINGXI_TEACHING_QUALITY_REVIEW]]"
FAKE_SOURCE_PATTERNS = [
    r"https?://example\.com",
    r"某高校",
    r"某教材",
    r"待补充链接",
    r"虚构",
]


def _contains_any(text: str, terms: List[str]) -> List[str]:
    lowered = text.lower()
    return [term for term in terms if term.lower() in lowered]


def _append_issue(result: Dict, issue: str, suggestion: str = "", fatal: bool = False):
    result["issues"].append(issue)
    if suggestion:
        result["suggestions"].append(suggestion)
    result["passed"] = False
    if fatal:
        result["fatal"] = True


def _missing_terms(text: str, terms: List[str]) -> List[str]:
    return [term for term in terms if term not in text]


def _content_length(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def _heading_count(text: str) -> int:
    return len(re.findall(r"(^|\n)#{2,3}\s+", text or ""))


def _count_markers(text: str, markers: List[str]) -> int:
    return sum(1 for marker in markers if marker and marker in (text or ""))


def _coverage_categories(content: str) -> Dict[str, bool]:
    text = content or ""
    categories = {
        "定义": ["定义", "是什么", "概念", "含义"],
        "原理": ["原理", "机制", "为什么", "作用", "流程", "推导"],
        "例子": ["例子", "示例", "例题", "案例", "情境"],
        "练习": ["自测题", "练习", "参考答案", "答案", "解析"],
        "公式或代码": ["公式", "符号", "计算过程", "代码", "伪代码", "PyTorch", "torch", "算法流程"],
        "误区": ["误区", "易错", "常见错误", "混淆"],
        "学习建议": ["下一步", "建议", "检查清单", "复习"],
    }
    return {
        name: any(marker in text for marker in markers)
        for name, markers in categories.items()
    }


def _normalize_topic_for_check(topic: str) -> str:
    return re.sub(r"\s+", "", str(topic or "")).lower()


def _has_fake_source(text: str) -> bool:
    return any(re.search(pattern, text, re.I) for pattern in FAKE_SOURCE_PATTERNS)


def validate_resource_semantics(resource: Dict, semantic_result: Dict) -> Dict:
    semantic_result = semantic_result or {}
    resource_type = artifact_types.normalize_artifact_type(
        semantic_result.get("resource_type") or resource.get("type") or ""
    )
    topic = semantic_result.get("topic") or resource.get("topic") or resource.get("title") or ""
    level_source = semantic_result.get("level_source") or resource.get("level_source") or "none"
    course_map = (
        semantic_result.get("deep_learning_course_map")
        or resource.get("deep_learning_course_map")
        or semantic_result.get("ai_course_map")
        or resource.get("ai_course_map")
        or deep_learning_course_map_service.match_deep_learning_topic(topic)
    )

    text = "\n".join([
        resource.get("title", ""),
        resource.get("type", ""),
        resource.get("summary", ""),
        resource.get("content", ""),
        resource.get("source", ""),
    ])
    result = {
        "passed": True,
        "fatal": False,
        "issues": [],
        "suggestions": [],
        "quality_score": 92,
        "risk_level": "low",
    }

    generation_context = semantic_result.get("generation_context") or {}
    if artifact_types.is_deprecated(resource.get("type")):
        _append_issue(
            result,
            f"资源类型已停用：{resource.get('type')}",
            "请改用深度学习 Artifact 类型，如课程讲解文档、练习题集、PyTorch 实操案例、视频推荐卡或交互动画规格。",
            fatal=True,
        )

    if resource_type == resource_policy_service.FEEDBACK_RESOURCE_TYPE and not resource_policy_service.has_feedback_context(generation_context):
        _append_issue(
            result,
            "缺少真实错题、测验、评价或学习反馈记录，不能生成诊断与补弱报告。",
            "首次学习请求可生成练习题集或基础诊断题，但不能伪装成诊断报告。",
            fatal=True,
        )

    if not course_map.get("matched"):
        _append_issue(
            result,
            "课程范围不明确：资源未归一到《深度学习》课程图谱。",
            "请先完成语义归一，绑定 chapter_id 和 unit_id。",
            fatal=True,
        )

    unit_id = (
        semantic_result.get("unit_id")
        or resource.get("unit_id")
        or course_map.get("unit_id")
    )
    if not unit_id:
        _append_issue(
            result,
            "缺少知识单元绑定：资源必须包含 unit_id。",
            "每份资源都应绑定《深度学习》课程的具体知识单元。",
            fatal=True,
        )

    if resource_type == artifact_types.EXERCISE_SET:
        missing = _missing_terms(text, EXERCISE_REQUIRED_TERMS)
        if missing:
            _append_issue(result, f"练习题集结构不完整：缺少{'、'.join(missing)}", "补充题干、答案、解析、知识点和常见错误。", fatal=True)

    if resource_type == artifact_types.READING_PACK:
        missing = _missing_terms(text, READING_REQUIRED_TERMS)
        if missing:
            _append_issue(result, f"拓展阅读包结构不完整：缺少{'、'.join(missing)}", "补充教材章节建议、公开课入口、官方文档和阅读顺序。", fatal=True)

    if resource_type == artifact_types.CODE_LAB:
        missing = _missing_terms(text, CODE_REQUIRED_TERMS)
        if missing:
            _append_issue(result, f"PyTorch 实操案例结构不完整：缺少{'、'.join(missing)}", "补充可运行实验目标、依赖、训练流程、代码、运行方式和实验报告模板。", fatal=True)

    if resource_type == artifact_types.PROJECT_BRIEF:
        missing = _missing_terms(text, PROJECT_REQUIRED_TERMS)
        if missing:
            _append_issue(result, f"课程实践项目任务书结构不完整：缺少{'、'.join(missing)}", "补充项目目标、任务拆解、验收标准、提交物和评分 Rubric。", fatal=True)

    if resource_type == artifact_types.VIDEO_RECOMMENDATION:
        missing = _missing_terms(text, VIDEO_REQUIRED_TERMS)
        if missing:
            _append_issue(result, f"视频推荐卡结构不完整：缺少{'、'.join(missing)}", "补充原始链接、推荐片段、平台来源和版权说明。", fatal=True)
        if any(word in text for word in ["下载视频", "搬运", "重新托管", "网盘"]):
            _append_issue(result, "视频资源版权边界错误：不得下载、搬运或重新托管第三方视频。", "只保留原始链接和观看指南。", fatal=True)

    if resource_type in {artifact_types.INTERACTIVE_ANIMATION, artifact_types.ANIMATION_STORYBOARD}:
        missing = _missing_terms(text, ANIMATION_REQUIRED_TERMS)
        if missing:
            _append_issue(result, f"动画资源结构不完整：缺少{'、'.join(missing)}", "补充可渲染规格、步骤高亮、画面描述或分镜旁白。", fatal=False)

    if _has_fake_source(text):
        _append_issue(result, "疑似虚构外部来源或占位链接。", "外部资料必须来自可核验公开入口；没有来源时应说明需补充授权资料。", fatal=True)

    if level_source == "none":
        level_hits = _contains_any(text, UNSUPPORTED_LEVEL_TERMS)
        if level_hits:
            _append_issue(
                result,
                f"无证据水平推断：出现 {', '.join(level_hits[:4])}",
                "当前主题水平未确认时，只能写入门诊断、基础路线或待确认水平。",
                fatal=True,
            )

    if result["passed"]:
        result["issues"].append("深度学习 Artifact 门禁：课程范围、资源结构和版权边界通过初检")
        result["suggestions"].append("建议管理员继续核验公式、代码可运行性和外部链接有效性。")
    else:
        result["quality_score"] = 40 if result.get("fatal") else 72
        result["risk_level"] = "high" if result.get("fatal") else "medium"

    return result


def validate_teaching_quality(item: Dict, context: Dict) -> Dict:
    """Evaluate whether a generated Artifact is useful as a teaching resource."""
    context = context or {}
    resource_type = artifact_types.normalize_artifact_type(
        item.get("type") or context.get("resource_type") or ""
    )
    title = item.get("title", "")
    summary = item.get("summary", "")
    content = item.get("content", "")
    source = item.get("source", "")
    course_map = (
        item.get("deep_learning_course_map")
        or context.get("deep_learning_course_map")
        or item.get("ai_course_map")
        or context.get("ai_course_map")
        or {}
    )
    unit_id = item.get("unit_id") or context.get("unit_id") or course_map.get("unit_id") or ""
    topic = (
        item.get("unit_title")
        or course_map.get("normalized_topic")
        or context.get("normalized_topic")
        or context.get("topic")
        or item.get("topic")
        or title
    )
    full_text = "\n".join([title, summary, content, source])
    content_len = _content_length(content)
    headings = _heading_count(content)
    required_terms = deep_learning_resource_blueprint.get_topic_specific_terms(unit_id, topic)
    covered_terms = [term for term in required_terms if term in full_text]
    evidence_chunks = context.get("evidence_chunks") or item.get("evidence_chunks") or []
    evidence_refs = re.findall(r"evidence_id\s*[:：=]\s*[\w:\-]+", full_text, re.I)
    examples = _count_markers(content, ["例子", "示例", "例题", "案例", "情境", "Conv2d", "torch", "PyTorch"])
    exercises = _count_markers(content, ["自测题", "练习", "参考答案", "答案", "解析"])
    formula_or_code = _count_markers(content, ["公式", "算法流程", "计算过程", "代码", "伪代码", "PyTorch", "torch", "梯度", "softmax", "Conv2d"])
    personalization = _count_markers(full_text, ["基础", "目标", "偏好", "短板", "实践", "适用对象", "学习定位"])
    coverage = _coverage_categories(content)
    covered_category_names = [name for name, ok in coverage.items() if ok]

    issues = []
    repair_suggestions = []
    fatal = False

    if content_len < 1200:
        fatal = True
        issues.append("内容过短，少于 1200 个中文字符")
        repair_suggestions.append("扩展为完整讲义，补齐概念解释、公式流程、例子、练习和学习建议")
    elif content_len < deep_learning_resource_blueprint.COURSE_NOTE_QUALITY_RULES["min_chars"] and resource_type == artifact_types.COURSE_NOTE:
        issues.append("课程讲解文档少于 1800 个中文字符")
        repair_suggestions.append("继续扩展核心概念、例题和代码/伪代码说明")

    normalized_topic = _normalize_topic_for_check(topic)
    normalized_full_text = _normalize_topic_for_check(full_text)
    if normalized_topic and normalized_topic not in normalized_full_text:
        fatal = True
        issues.append(f"正文未明确出现当前主题：{topic}")
        repair_suggestions.append("在标题、课程位置和核心概念讲解中明确写出当前知识点")

    if resource_type == artifact_types.COURSE_NOTE and headings < 6:
        fatal = True
        issues.append("课程讲解文档二级标题少于 6 个")
        repair_suggestions.append("按 12 个讲义章节重写，至少包含 8 个二级标题")

    if resource_type == artifact_types.COURSE_NOTE and len(covered_category_names) < 3:
        fatal = True
        issues.append("课程讲义教学要素严重不足：定义、原理、例子、练习、公式/代码、误区、学习建议覆盖少于 3 类")
        repair_suggestions.append("按完整课程讲义重写，至少补齐定义、原理、例子、练习、公式/代码、误区和下一步建议")
    elif resource_type == artifact_types.COURSE_NOTE and len(covered_category_names) < 5:
        issues.append("课程讲义教学要素不够完整")
        repair_suggestions.append("继续补充定义、原理、例子、练习、公式/代码、误区和学习建议中的缺失部分")

    if "核心内容" in content and content_len < 1500:
        issues.append("内容停留在摘要层面，没有展开讲解")
        repair_suggestions.append("不要只列学习目标和核心内容，要逐项展开讲解")

    if required_terms and len(covered_terms) < min(4, len(required_terms)):
        fatal = True
        missing = [term for term in required_terms if term not in covered_terms]
        issues.append(f"核心主题词覆盖不足：缺少{'、'.join(missing[:5])}")
        repair_suggestions.append("围绕课程图谱补齐主题关键词，并解释它们之间的关系")

    if examples < 2 and resource_type == artifact_types.COURSE_NOTE:
        issues.append("具体例子不足，少于 2 个")
        repair_suggestions.append("加入至少 2 个深度学习模型或计算例子")

    if exercises < 3 and resource_type == artifact_types.COURSE_NOTE:
        issues.append("课堂小练习不足，未体现 3 道自测题与答案")
        repair_suggestions.append("补充 3 道自测题，并附参考答案和解析")

    if formula_or_code < 2 and resource_type == artifact_types.COURSE_NOTE:
        issues.append("公式、代码或算法流程说明不足")
        repair_suggestions.append("补充公式符号解释、算法流程或 Python/PyTorch 示例")

    if not evidence_chunks and not evidence_refs:
        issues.append("缺少课程知识库证据引用")
        repair_suggestions.append("补充 evidence_id，并依据课程知识库片段展开")

    score = 0
    score += 20 if normalized_topic and normalized_topic in normalized_full_text else 6
    score += min(15, headings * 2)
    score += 20 if content_len >= 1800 else (12 if content_len >= 1200 else 4)
    if required_terms:
        score += round(min(15, 15 * len(covered_terms) / max(1, len(required_terms))))
    else:
        score += 12
    score += min(10, examples * 3 + exercises)
    score += min(10, formula_or_code * 3)
    score += min(5, personalization)
    score += 5 if evidence_chunks or evidence_refs else 0
    if resource_type == artifact_types.COURSE_NOTE:
        score = min(100, score + min(5, len(covered_category_names)))
    score = max(0, min(100, int(score)))

    passed = not fatal and score >= 80
    if not issues and passed:
        issues.append("教学质量门控通过：结构、主题、深度、例子和证据引用均达到要求")
    if not repair_suggestions and not passed:
        repair_suggestions.append("按深度学习讲义蓝图重写，不要只做摘要式小修")

    return {
        "teaching_quality_score": score,
        "score": score,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "fatal": fatal,
        "issues": issues,
        "repair_suggestions": list(dict.fromkeys(repair_suggestions)),
        "covered_terms": covered_terms,
        "required_terms": required_terms,
        "metrics": {
            "content_chars": content_len,
            "heading_count": headings,
            "example_markers": examples,
            "exercise_markers": exercises,
            "formula_or_code_markers": formula_or_code,
            "evidence_count": len(evidence_chunks) + len(evidence_refs),
            "teaching_element_coverage": covered_category_names,
        },
    }


def attach_quality_note(notes: str, quality: Dict) -> str:
    issues = quality.get("issues") or []
    suggestions = quality.get("suggestions") or []
    lines = [
        "[[LINGXI_RESOURCE_QUALITY_GATE]]",
        "## 深度学习 Artifact 语义质量门禁",
        f"- 通过状态：{'通过' if quality.get('passed') else '未通过'}",
        f"- 致命问题：{'是' if quality.get('fatal') else '否'}",
        f"- 质量分：{quality.get('quality_score', 0)}",
        f"- 风险等级：{quality.get('risk_level', 'unknown')}",
        "",
        "### 问题",
        *[f"- {item}" for item in issues],
        "",
        "### 建议",
        *[f"- {item}" for item in suggestions],
        "[[/LINGXI_RESOURCE_QUALITY_GATE]]",
    ]
    return "\n\n".join(part for part in [notes or "", "\n".join(lines)] if part)


def _format_teaching_review_block(review: Dict) -> str:
    issues = review.get("issues") or []
    suggestions = review.get("repair_suggestions") or review.get("suggestions") or []
    lines = [
        TEACHING_REVIEW_START,
        "## 教学质量门控",
        f"score: {review.get('teaching_quality_score', review.get('score', 0))}",
        f"status: {'passed' if review.get('passed') else 'failed'}",
        f"fatal: {'true' if review.get('fatal') else 'false'}",
        "",
        "issues:",
        *[f"- {item}" for item in issues],
        "",
        "repair_suggestions:",
        *[f"- {item}" for item in suggestions],
        TEACHING_REVIEW_END,
    ]
    return "\n".join(lines)


def strip_teaching_quality_note(notes: str) -> str:
    text = notes or ""
    pattern = re.compile(
        rf"\n?{re.escape(TEACHING_REVIEW_START)}.*?{re.escape(TEACHING_REVIEW_END)}\n?",
        re.S,
    )
    return pattern.sub("\n", text).strip()


def attach_teaching_quality_note(notes: str, review: Dict) -> str:
    base_notes = strip_teaching_quality_note(notes)
    return "\n\n".join(part for part in [base_notes, _format_teaching_review_block(review)] if part)


def extract_teaching_quality_review(notes: str) -> Dict:
    text = notes or ""
    match = re.search(
        rf"{re.escape(TEACHING_REVIEW_START)}(?P<body>.*?){re.escape(TEACHING_REVIEW_END)}",
        text,
        re.S,
    )
    if not match:
        return {}

    body = match.group("body")
    score_match = re.search(r"score:\s*(\d+)", body)
    status_match = re.search(r"status:\s*([^\n]+)", body)
    fatal_match = re.search(r"fatal:\s*([^\n]+)", body)
    issues_section = re.search(r"issues:(?P<issues>.*?)(repair_suggestions:|$)", body, re.S)
    suggestions_section = re.search(r"repair_suggestions:(?P<suggestions>.*)$", body, re.S)

    def parse_list(section):
        if not section:
            return []
        return [
            line.strip()[2:].strip()
            for line in section.splitlines()
            if line.strip().startswith("- ")
        ]

    score = int(score_match.group(1)) if score_match else 0
    status = status_match.group(1).strip() if status_match else "unreviewed"
    return {
        "teaching_quality_score": score,
        "score": score,
        "status": status,
        "passed": status == "passed",
        "fatal": fatal_match.group(1).strip().lower() == "true" if fatal_match else False,
        "issues": parse_list(issues_section.group("issues") if issues_section else ""),
        "repair_suggestions": parse_list(suggestions_section.group("suggestions") if suggestions_section else ""),
    }


def strip_quality_blocks(notes: str) -> str:
    return strip_teaching_quality_note(notes or "")
