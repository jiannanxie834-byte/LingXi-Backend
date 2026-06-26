import re
from typing import Dict, List

from app.services.data_services import (
    deep_learning_course_map_service,
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
