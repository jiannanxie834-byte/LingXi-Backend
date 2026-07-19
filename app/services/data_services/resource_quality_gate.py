import ast
import re
from collections import Counter
from typing import Dict, List

from app.services.data_services import (
    dsa_course_map_service,
    resource_artifact_type_service as artifact_types,
    resource_policy_service,
)


CODE_REQUIRED_TERMS = ["实验目标", "环境依赖", "运行方式", "训练流程", "代码", "实验报告"]
DSA_CODE_REQUIRED_TERMS = ["实验目标", "环境依赖", "运行命令", "完整代码", "学生任务", "复杂度"]
EXERCISE_REQUIRED_TERMS = ["题", "答案", "解析", "知识点"]
READING_REQUIRED_TERMS = ["阅读", "教材", "公开", "顺序", "目标"]
PROJECT_REQUIRED_TERMS = ["项目", "目标", "任务", "验收", "提交", "Rubric"]
VIDEO_REQUIRED_TERMS = ["原始链接", "公开视频", "推荐片段", "版权"]
ANIMATION_REQUIRED_TERMS = ["animation", "动画", "步骤", "高亮", "规格"]
TEACHING_PUBLISH_SCORE = 70
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
STRONG_PLACEHOLDER_PATTERNS = [
    r"该类资源暂未完善",
    r"参考答案需要根据.*补全",
    r"当前匹配小节暂未配置",
    r"本阶段只输出.*占位",
    r"\bplaceholder\b",
    r"\bTODO\b",
    r"待实现",
    r"待补充",
    r"补全(?:此处|核心逻辑)",
]
GENERIC_FALLBACK_PATTERNS = [
    r"很多错误来自还没确认问题边界",
    r"能用自然语言讲清楚，通常比直接背模板更稳",
    r"套模板但不解释条件",
    r"问题如何被表示、状态如何变化、结果如何验证",
    r"这份讲解不是直接复制课程小节",
    r"处理的是序列、集合、树、图，还是一个可以拆分成子问题的过程",
    r"先写下你对.*的当前理解，以及最不确定的一个问题",
    r"用 5 句话复述核心流程，并完成 2 道基础题",
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


def _exercise_question_count(text: str) -> int:
    return len(re.findall(r"(^|\n)###\s*题目\s*\d+", text or ""))


def _exercise_type_count(text: str) -> int:
    types = ["选择题", "判断题", "简答题", "计算题", "推导题", "过程题", "代码题", "代码理解题", "实验分析题"]
    return sum(1 for item in types if item in (text or ""))


def _count_markers(text: str, markers: List[str]) -> int:
    return sum(1 for marker in markers if marker and marker in (text or ""))


def _coverage_categories(content: str) -> Dict[str, bool]:
    text = content or ""
    categories = {
        "定义": ["定义", "是什么", "概念", "含义"],
        "原理": ["原理", "机制", "为什么", "作用", "流程", "推导"],
        "例子": ["例子", "示例", "例题", "案例", "情境"],
        "理解检查": ["小结", "检查清单", "理解", "复述", "边界", "下一步"],
        "公式或代码": ["公式", "符号", "计算过程", "代码", "伪代码", "算法流程"],
        "误区": ["误区", "易错", "常见错误", "混淆"],
        "学习建议": ["下一步", "建议", "检查清单", "复习"],
    }
    return {
        name: any(marker in text for marker in markers)
        for name, markers in categories.items()
    }


def _normalize_topic_for_check(topic: str) -> str:
    return re.sub(r"\s+", "", str(topic or "")).lower()


def _term_covered(term: str, text: str) -> bool:
    normalized_text = _normalize_topic_for_check(text)
    normalized_term = _normalize_topic_for_check(term)
    if not normalized_term:
        return False
    if normalized_term in normalized_text:
        return True

    parts = [
        part
        for part in re.split(r"[、,，/\\s]+|与|和|及|或", str(term or ""))
        if len(_normalize_topic_for_check(part)) >= 2
    ]
    if not parts:
        return False
    hits = sum(1 for part in parts if _normalize_topic_for_check(part) in normalized_text)
    return hits >= max(1, round(len(parts) * 0.6))


def _has_fake_source(text: str) -> bool:
    return any(re.search(pattern, text, re.I) for pattern in FAKE_SOURCE_PATTERNS)


def _pattern_hits(text: str, patterns: List[str]) -> List[str]:
    return [pattern for pattern in patterns if re.search(pattern, text or "", re.I)]


def _python_code_blocks(text: str) -> List[str]:
    return [block.strip() for block in re.findall(r"```python\s*(.*?)```", text or "", re.S | re.I) if block.strip()]


def _python_code_is_valid(text: str) -> bool:
    blocks = _python_code_blocks(text)
    if not blocks:
        return False
    try:
        for block in blocks:
            ast.parse(block)
        return True
    except SyntaxError:
        return False


def _real_urls(text: str) -> List[str]:
    return [url.rstrip(".,)）]》") for url in re.findall(r"https?://[^\s<>。，]+", text or "", re.I)]


def validate_resource_semantics(resource: Dict, semantic_result: Dict) -> Dict:
    semantic_result = semantic_result or {}
    resource_type = artifact_types.normalize_artifact_type(
        semantic_result.get("resource_type") or resource.get("type") or ""
    )
    topic = semantic_result.get("topic") or resource.get("topic") or resource.get("title") or ""
    level_source = semantic_result.get("level_source") or resource.get("level_source") or "none"
    course_map = (
        semantic_result.get("dsa_course_map")
        or resource.get("dsa_course_map")
        or semantic_result.get("ai_course_map")
        or resource.get("ai_course_map")
        or {}
    )
    is_dsa = (
        semantic_result.get("course_id") == dsa_course_map_service.COURSE_ID
        or resource.get("course_id") == dsa_course_map_service.COURSE_ID
        or course_map.get("course_id") == dsa_course_map_service.COURSE_ID
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
        course_label = "数据结构与算法" if is_dsa else "当前课程"
        _append_issue(
            result,
            f"资源类型已停用：{resource.get('type')}",
            f"请改用{course_label} Artifact 类型，如课程讲解文档、练习题集、代码实验、视频指南或诊断报告。",
            fatal=True,
        )

    if (
        resource_type == resource_policy_service.FEEDBACK_RESOURCE_TYPE
        and not is_dsa
        and not resource_policy_service.has_feedback_context(generation_context)
    ):
        _append_issue(
            result,
            "缺少真实错题、测验、评价或学习反馈记录，不能生成诊断与补弱报告。",
            "首次学习请求可生成练习题集或基础诊断题，但不能伪装成诊断报告。",
            fatal=True,
        )

    unit_id = (
        semantic_result.get("unit_id")
        or resource.get("unit_id")
        or course_map.get("unit_id")
    )
    has_location_binding = bool(
        unit_id
        or semantic_result.get("unit_ids")
        or resource.get("unit_ids")
        or semantic_result.get("chapter_id")
        or resource.get("chapter_id")
        or semantic_result.get("section_id")
        or resource.get("section_id")
    )
    if not course_map.get("matched") and not (is_dsa and has_location_binding):
        _append_issue(
            result,
            "课程范围不明确：资源未归一到当前课程图谱。",
            "请先完成语义归一，绑定 chapter_id 和 unit_id。",
            fatal=True,
        )

    if not unit_id and not (semantic_result.get("unit_ids") or resource.get("unit_ids")):
        _append_issue(
            result,
            "缺少知识单元绑定：资源必须包含 unit_id。",
            "每份资源都应绑定当前课程的具体知识单元。",
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
        missing = _missing_terms(text, DSA_CODE_REQUIRED_TERMS if is_dsa else CODE_REQUIRED_TERMS)
        if missing:
            _append_issue(result, f"代码实验结构不完整：缺少{'、'.join(missing)}", "补充可运行实验目标、依赖、完整代码、运行方式、学生任务和复杂度记录。", fatal=True)

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
        gate_label = "数据结构与算法" if is_dsa else "当前课程"
        result["issues"].append(f"{gate_label} Artifact 门禁：课程范围、资源结构和版权边界通过初检")
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
        item.get("dsa_course_map")
        or context.get("dsa_course_map")
        or item.get("ai_course_map")
        or context.get("ai_course_map")
        or {}
    )
    is_dsa = (
        item.get("course_id") == dsa_course_map_service.COURSE_ID
        or context.get("course_id") == dsa_course_map_service.COURSE_ID
        or course_map.get("course_id") == dsa_course_map_service.COURSE_ID
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
    chapter_id = (
        item.get("chapter_id")
        or context.get("chapter_id")
        or course_map.get("chapter_id")
        or ""
    )
    core_chapters = {
        "chapter_03_neural_network_basics",
        "chapter_04_deep_network_and_backprop",
        "chapter_05_regularization_and_generalization",
        "chapter_06_optimization",
        "chapter_07_cnn_foundation",
        "chapter_08_cnn_architectures_and_cv_practice",
        "chapter_10_sequence_models",
        "chapter_11_attention_transformer",
        "chapter_12_final_project",
    }
    is_core_chapter = chapter_id in core_chapters
    compact_artifact_types = {
        artifact_types.MIND_MAP,
        artifact_types.INTERACTIVE_ANIMATION,
        artifact_types.ANIMATION_STORYBOARD,
    }
    structured_non_long_types = {
        artifact_types.MIND_MAP,
        artifact_types.INTERACTIVE_ANIMATION,
        artifact_types.ANIMATION_STORYBOARD,
        artifact_types.READING_PACK,
        artifact_types.PERSONALIZED_VIDEO_GUIDE,
        artifact_types.VIDEO_RECOMMENDATION,
        artifact_types.DIAGNOSTIC_REPORT,
    }
    required_terms = []
    covered_terms = [term for term in required_terms if _term_covered(term, full_text)]
    evidence_chunks = context.get("evidence_chunks") or item.get("evidence_chunks") or []
    context_evidence_refs = context.get("evidence_refs") or item.get("evidence_refs") or []
    evidence_refs = context_evidence_refs or re.findall(r"evidence_id\s*[:：=]\s*[\w:\-]+", full_text, re.I)
    examples = _count_markers(content, ["例子", "示例", "例题", "案例", "情境"])
    exercises = _count_markers(content, ["练习", "答案", "解析"])
    formula_or_code = _count_markers(content, ["公式", "算法流程", "计算过程", "代码", "伪代码"])
    personalization = _count_markers(full_text, ["基础", "目标", "偏好", "短板", "实践", "适用对象", "学习定位"])
    coverage = _coverage_categories(content)
    covered_category_names = [name for name, ok in coverage.items() if ok]

    issues = []
    repair_suggestions = []
    fatal = False
    duplicate_nodes = 0
    code_placeholders = []
    excessive_repetition = False

    if not str(content or "").strip():
        fatal = True
        issues.append("资源正文为空")
        repair_suggestions.append("必须生成真实可用的学习内容后才能发布")

    if item.get("assembly_policy") == "personalized_generation_fallback":
        fatal = True
        issues.append("检测到降级模板产物，禁止作为真实资源发布")
        repair_suggestions.append("重新调用讯飞星火生成；失败时保留失败状态，不使用本地模板替代")

    placeholder_hits = _pattern_hits(content, STRONG_PLACEHOLDER_PATTERNS)
    if placeholder_hits:
        fatal = True
        issues.append("内容包含占位符或未完成说明")
        repair_suggestions.append("删除占位内容，提供可直接学习、作答或运行的完整产物")

    fallback_hits = _pattern_hits(content, GENERIC_FALLBACK_PATTERNS)
    if fallback_hits:
        fatal = True
        issues.append("内容命中通用降级模板，与具体知识点绑定不足")
        repair_suggestions.append("使用当前知识点的定义、输入输出、算法步骤和边界案例重写")

    if resource_type == artifact_types.COURSE_NOTE:
        min_chars = 700 if is_dsa else (4500 if is_core_chapter else 3000)
        if content_len < min_chars:
            fatal = True
            issues.append(f"章节主讲义过短，少于 {min_chars} 个中文字符")
            repair_suggestions.append("补齐学习定位、核心机制、关键流程、例子、误区、小结和下一步建议")
        min_headings = 5 if is_dsa else 8
        if headings < min_headings:
            fatal = True
            issues.append(f"章节主讲义二级标题少于 {min_headings} 个")
            repair_suggestions.append("按学习定位、核心概念、流程讲解、例子、误区和下一步建议扩展")
        if not is_dsa and "参考来源说明" not in content:
            fatal = True
            issues.append("章节主讲义缺少参考来源说明")
            repair_suggestions.append("在末尾说明公开资料仅作结构参考，不复制原文")
        if examples < 1:
            fatal = True
            issues.append("章节主讲义缺少具体例子")
            repair_suggestions.append("补充至少 1 个用于解释概念的具体例子")
        elif examples < 2:
            issues.append("具体例子偏少，建议继续补充")
            repair_suggestions.append("可补充算法输入输出、边界条件或计算例子")
    elif resource_type not in structured_non_long_types and content_len < (700 if is_dsa else 1200):
        fatal = True
        issues.append(f"内容过短，少于 {700 if is_dsa else 1200} 个中文字符")
        repair_suggestions.append("扩展为完整讲义，补齐概念解释、公式流程、例子、误区和学习建议")

    if resource_type == artifact_types.MIND_MAP:
        non_empty_lines = [line for line in (content or "").splitlines() if line.strip()]
        indentation_levels = {
            len(line) - len(line.lstrip(" "))
            for line in non_empty_lines
            if line.strip() and not line.strip().startswith("%%")
        }
        if "mindmap" not in content.lower() and "graph" not in content.lower():
            fatal = True
            issues.append("思维导图缺少 Mermaid mindmap 或 graph 结构")
            repair_suggestions.append("使用 Mermaid mindmap/graph 表达章节层级、前置关系和易混点")
        if len(non_empty_lines) < 10 or len(indentation_levels) < 3:
            fatal = True
            issues.append("思维导图层级过浅，不足以表达章节知识结构")
            repair_suggestions.append("至少展开中心主题、一级知识点、二级细节、前置关系和易混点")
        normalized_nodes = [re.sub(r"\s+", "", line) for line in non_empty_lines[1:]]
        duplicate_nodes = len(normalized_nodes) - len(set(normalized_nodes))
        if duplicate_nodes >= 2:
            fatal = True
            issues.append(f"思维导图存在 {duplicate_nodes} 个重复节点")
            repair_suggestions.append("合并同义节点，每个分支只保留一个清晰知识层级")

    if resource_type == artifact_types.EXERCISE_SET:
        question_count = _exercise_question_count(content)
        type_count = _exercise_type_count(content)
        min_questions = 4 if is_dsa else 8
        if question_count < min_questions:
            fatal = True
            issues.append(f"练习题集题量不足，少于 {min_questions} 题")
            repair_suggestions.append("补充覆盖概念、边界条件、复杂度和代码理解的题目")
        if "答案" not in content or "解析" not in content:
            fatal = True
            issues.append("练习题集缺少答案或解析")
            repair_suggestions.append("每题必须有答案、解析和常见错误")
        if type_count < (3 if is_dsa else 4):
            fatal = True
            issues.append("练习题集题型覆盖不足")
            repair_suggestions.append("补充选择、判断、简答、计算/推导、代码理解、实验分析等题型")
        answer_count = len(re.findall(r"(^|\n)\s*(?:[-*]\s*)?(?:\*\*)?(?:答案|参考答案)(?:\*\*)?\s*[:：]", content, re.M))
        explanation_count = len(re.findall(r"(^|\n)\s*(?:[-*]\s*)?(?:\*\*)?(?:解析|答案解析)(?:\*\*)?\s*[:：]", content, re.M))
        if answer_count < question_count or explanation_count < question_count:
            fatal = True
            issues.append("练习题集并非每题都有独立答案和解析")
            repair_suggestions.append("为每道题逐题补齐参考答案、解析、知识点和常见错误")
        question_sections = re.split(r"(?=^###\s*题目\s*\d+)", content, flags=re.M)
        choice_sections = [
            section for section in question_sections
            if section.strip() and "选择题" in section.splitlines()[0]
        ]
        for section in choice_sections:
            options = re.findall(r"(^|\n)\s*[A-D][.\u3001]、?\s*\S+", section)
            answer_is_letter = re.search(r"(?:\*\*)?答案(?:\*\*)?\s*[:：]\s*[A-D](?:\s|$)", section)
            if len(options) < 4 or not answer_is_letter:
                fatal = True
                issues.append("选择题缺少 A-D 四个独立选项，或答案不是可核验的选项字母")
                repair_suggestions.append("选择题必须给出 A-D 四个选项，参考答案只写一个选项字母")
                break

        repeated_lines = Counter(
            _normalize_topic_for_check(line)
            for line in content.splitlines()
            if len(_normalize_topic_for_check(line)) >= 20
            and not line.lstrip().startswith(("#", "---", "|"))
        )
        if any(count >= 3 for count in repeated_lines.values()):
            fatal = True
            excessive_repetition = True
            issues.append("多道题重复使用同一段模板答案/解析，未绑定具体题目")
            repair_suggestions.append("每题根据题干和知识点单独编写答案、解析和常见错误")

    if resource_type == artifact_types.CODE_LAB:
        required = ["完整代码", "运行命令", "学生任务", "常见报错"]
        missing = _missing_terms(content, required)
        if missing:
            fatal = True
            issues.append(f"代码实验结构不完整：缺少{'、'.join(missing)}")
            repair_suggestions.append("代码实验必须包含完整可运行代码、运行方式、学生任务、调参建议和常见报错")
        code_placeholders = _pattern_hits(content, [r"\bTODO\b", r"\bpass\b", r"补全此处", r"补全核心逻辑"])
        if code_placeholders:
            fatal = True
            issues.append("代码实验仍包含 TODO/pass/补全逻辑等占位代码")
            repair_suggestions.append("提供可直接运行的参考实现，学生任务可单独给出骨架")
        if not _python_code_is_valid(content):
            fatal = True
            issues.append("代码实验缺少语法可通过的 Python 完整代码块")
            repair_suggestions.append("对所有 Python 代码块进行 ast.parse 语法校验")
        test_count = len(re.findall(r"\bassert\b|\btest_[a-zA-Z0-9_]+\b|测试用例\s*[1-9]", content))
        if test_count < 3:
            fatal = True
            issues.append("代码实验少于 3 个可核验测试")
            repair_suggestions.append("补充普通、边界和异常输入的 assert 测试")

    if resource_type in {artifact_types.READING_PACK, artifact_types.PERSONALIZED_VIDEO_GUIDE, artifact_types.VIDEO_RECOMMENDATION}:
        required = ["观看/阅读前准备", "观看/阅读中关注点", "观看/阅读后任务", "版权说明"]
        missing = _missing_terms(content, required)
        if missing:
            fatal = True
            issues.append(f"阅读/视频指南结构不完整：缺少{'、'.join(missing)}")
            repair_suggestions.append("阅读/视频指南不能只是链接列表，必须提供前中后任务和版权说明")
        if resource_type in {artifact_types.PERSONALIZED_VIDEO_GUIDE, artifact_types.VIDEO_RECOMMENDATION} and not _real_urls(content):
            fatal = True
            issues.append("视频资源没有任何可核验的原始 HTTP(S) 入口")
            repair_suggestions.append("只发布具有真实原始链接、平台来源和观看任务的视频指南")

    if resource_type == artifact_types.INTERACTIVE_ANIMATION:
        assets = item.get("assets") or context.get("assets") or []
        playable_assets = [asset for asset in assets if isinstance(asset, dict) and asset.get("url") and asset.get("mime_type") in {"text/html", "video/mp4", "video/webm"}]
        if not playable_assets:
            fatal = True
            issues.append("交互动画只有文字规格，没有可播放产物")
            repair_suggestions.append("绑定可打开的 HTML 动画或视频文件后再发布")

    normalized_topic = _normalize_topic_for_check(topic)
    normalized_full_text = _normalize_topic_for_check(full_text)
    if normalized_topic and normalized_topic not in normalized_full_text:
        fatal = True
        issues.append(f"正文未明确出现当前主题：{topic}")
        repair_suggestions.append("在标题、课程位置和核心概念讲解中明确写出当前知识点")

    if resource_type == artifact_types.COURSE_NOTE and len(covered_category_names) < 3:
        fatal = True
        issues.append("课程讲义教学要素严重不足：定义、原理、例子、流程/公式、误区、学习建议覆盖少于 3 类")
        repair_suggestions.append("按完整课程讲义重写，至少补齐定义、原理、例子、流程/公式、误区和下一步建议")
    elif resource_type == artifact_types.COURSE_NOTE and len(covered_category_names) < 5:
        issues.append("课程讲义教学要素不够完整")
        repair_suggestions.append("继续补充定义、原理、例子、流程/公式、误区和学习建议中的缺失部分")

    if "核心内容" in content and content_len < 1500:
        issues.append("内容停留在摘要层面，没有展开讲解")
        repair_suggestions.append("不要只列学习目标和核心内容，要逐项展开讲解")

    term_strict_resource_types = {
        artifact_types.COURSE_NOTE,
        artifact_types.EXERCISE_SET,
        artifact_types.CODE_LAB,
        artifact_types.PROJECT_BRIEF,
    }
    if (
        required_terms
        and resource_type in term_strict_resource_types
        and len(covered_terms) < min(4, len(required_terms))
    ):
        fatal = True
        missing = [term for term in required_terms if not _term_covered(term, full_text)]
        issues.append(f"核心主题词覆盖不足：缺少{'、'.join(missing[:5])}")
        repair_suggestions.append("围绕课程图谱补齐主题关键词，并解释它们之间的关系")

    if examples < 2 and resource_type == artifact_types.COURSE_NOTE:
        issues.append("具体例子不足，少于 2 个")
        repair_suggestions.append("加入至少 2 个算法输入输出、边界条件或计算例子")

    if formula_or_code < 2 and resource_type == artifact_types.COURSE_NOTE:
        issues.append("公式、代码或算法流程说明不足")
        repair_suggestions.append("补充公式符号解释、算法流程或 Python 示例")

    if not evidence_chunks and not evidence_refs:
        issues.append("缺少课程知识库证据引用")
        repair_suggestions.append("补充 evidence_id，并依据课程知识库片段展开")

    score = 0
    score += 20 if normalized_topic and normalized_topic in normalized_full_text else 6
    structure_score = min(20, headings * 3)
    if resource_type == artifact_types.MIND_MAP:
        structure_score = min(20, max(0, len([line for line in content.splitlines() if line.strip()]) - 2))
    elif resource_type == artifact_types.EXERCISE_SET:
        structure_score = min(20, _exercise_question_count(content) * 3 + _exercise_type_count(content) * 2)
    elif resource_type == artifact_types.CODE_LAB:
        structure_score = 20 if _python_code_is_valid(content) else 0
    elif resource_type in {artifact_types.PERSONALIZED_VIDEO_GUIDE, artifact_types.VIDEO_RECOMMENDATION}:
        structure_score = min(20, len(_real_urls(content)) * 5 + headings * 2)
    elif resource_type == artifact_types.INTERACTIVE_ANIMATION:
        assets = item.get("assets") or context.get("assets") or []
        structure_score = 20 if any(isinstance(asset, dict) and asset.get("url") for asset in assets) else 0
    score += structure_score
    if resource_type in compact_artifact_types:
        score += 20 if not fatal else 5
    elif resource_type in structured_non_long_types:
        score += 18 if content_len >= 600 else 12
    else:
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
    if fatal:
        score = min(score, 69)
    if not str(content or "").strip():
        score = 0
    elif placeholder_hits or code_placeholders:
        score = min(score, 30)
    elif fallback_hits or item.get("assembly_policy") == "personalized_generation_fallback":
        score = min(score, 40)
    elif duplicate_nodes >= 2:
        score = min(score, 40)
    elif excessive_repetition:
        score = min(score, 40)

    passed = not fatal and score >= TEACHING_PUBLISH_SCORE
    if not passed and not issues:
        issues.append(
            f"综合教学质量分 {score}，未达到 {TEACHING_PUBLISH_SCORE} 分发布线"
        )
    if not issues and passed:
        issues.append("教学质量门控通过：结构、主题、深度、例子和证据引用均达到要求")
    if not repair_suggestions and not passed:
        repair_suggestions.append("按当前课程讲义结构重写，不要只做摘要式小修")

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
        "## 课程 Artifact 语义质量门禁",
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
