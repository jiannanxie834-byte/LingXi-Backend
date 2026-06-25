import re
from typing import Dict, List

from app.services.data_services import ai_course_map_service, resource_policy_service


CODE_TERMS = [
    "```python",
    "```java",
    "function",
    "def ",
    "class ",
    "代码注释",
    "PyTorch",
    "TensorFlow",
    "extract_core_concepts",
    "伪代码",
    "算法实现",
    "模型训练",
]

LANGUAGE_EXERCISE_TERMS = ["答案", "解析", "翻译", "填空题", "选择题", "阅读理解", "口语", "例句"]
PLANNING_AS_EXERCISE_TERMS = ["制定学习计划", "路径规划", "学习路线", "资源类型", "CEFR 自评设计", "评估学习路径"]
READING_MATERIAL_TERMS = ["阅读短文", "原文", "关键词", "理解题", "来源名称", "标题"]
EXERCISE_REQUIRED_TERMS = ["题目", "答案", "解析"]
READING_REQUIRED_TERMS = ["阅读主题", "关键词", "阅读问题", "外部来源", "来源条目", "MOOC", "教材", "公开视频", "链接"]
PRACTICE_REQUIRED_TERMS = ["任务目标", "操作步骤", "验收标准"]
UNSUPPORTED_LEVEL_TERMS = ["进阶学习者", "高阶学习者", "B1", "B2", "C1", "C2", "已掌握", "已经具备"]

TOPIC_MISMATCH_TERMS = {
    "foreign_language": ["RNN", "CNN", "深度学习", "模型训练", "路径规划算法", "PyTorch", "TensorFlow"],
    "mathematics": ["法语", "英语", "RNN", "CNN", "PyTorch"],
    "physics": ["法语", "英语", "RNN", "CNN", "PyTorch"],
    "general_course": ["RNN", "CNN", "PyTorch", "TensorFlow"],
}


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


def validate_resource_semantics(resource: Dict, semantic_result: Dict) -> Dict:
    subject_category = semantic_result.get("subject_category") or resource.get("subject_category") or "unknown"
    resource_type = semantic_result.get("resource_type") or resource.get("type") or ""
    topic = semantic_result.get("topic") or resource.get("topic") or resource.get("title") or ""
    level_source = semantic_result.get("level_source") or resource.get("level_source") or "none"
    allow_code = bool(semantic_result.get("should_generate_code_content") or resource.get("allow_code_content"))

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
    }

    generation_context = semantic_result.get("generation_context") or {}
    if resource_type == "多模态学习包":
        _append_issue(
            result,
            "资源类型已停用：多模态学习包应作为同主题资源聚合视图，不再作为独立资源正文生成。",
            "请改为生成讲解文档、思维导图、练习题、拓展阅读或实践任务，并由前端聚合成主题学习包。",
            fatal=True,
        )

    if (
        resource_type == resource_policy_service.FEEDBACK_RESOURCE_TYPE
        and not resource_policy_service.has_feedback_context(generation_context)
    ):
        _append_issue(
            result,
            "缺少真实错题、测验、评价或学习反馈记录，不能生成错题诊断与学习反馈报告。",
            "首次学习请求可生成入门自测题或基础练习，但不能伪装成错题诊断报告。",
            fatal=True,
        )

    code_hits = _contains_any(text, CODE_TERMS)
    if subject_category != "computer_science" and not allow_code and code_hits:
        _append_issue(
            result,
            f"学科错配：非编程学科出现代码/算法内容（{', '.join(code_hits[:4])}）",
            "请改为该学科本身的例题、图解、阅读或实践任务。",
            fatal=True,
        )

    if subject_category == "foreign_language" and resource_type == "不同类型练习题目":
        planning_hits = _contains_any(text, PLANNING_AS_EXERCISE_TERMS)
        exercise_hits = _contains_any(text, LANGUAGE_EXERCISE_TERMS)
        if planning_hits and not exercise_hits:
            _append_issue(
                result,
                "资源类型错配：外语练习题被生成成学习规划题",
                "外语练习必须包含选择、填空、翻译、阅读理解或口语情境题，并提供答案解析。",
                fatal=True,
            )

    if resource_type == "拓展阅读材料":
        reading_hits = _contains_any(text, READING_MATERIAL_TERMS)
        if not reading_hits:
            _append_issue(
                result,
                "阅读资源不完整：缺少阅读短文、关键词、理解题或明确外部来源",
                "请补充 AI 原创短文或可核验的外部来源条目。",
                fatal=subject_category == "foreign_language",
            )

    if resource_type == "不同类型练习题目":
        missing = [term for term in EXERCISE_REQUIRED_TERMS if term not in text]
        if missing:
            _append_issue(
                result,
                f"练习题结构不完整：缺少{'、'.join(missing)}",
                "练习题必须包含题目、答案和解析，且题目要考查课程知识点本身。",
                fatal=True,
            )

    if resource_type == "拓展阅读材料":
        reading_hits = _contains_any(text, READING_REQUIRED_TERMS)
        if not reading_hits:
            _append_issue(
                result,
                "拓展阅读材料缺少阅读主题、关键词、阅读问题或明确外部来源条目",
                "请补充可直接用于学习的阅读主题、关键词清单和阅读后问题，或给出可核验外部入口。",
                fatal=True,
            )

    if resource_type == "学科实践应用任务":
        missing = [term for term in PRACTICE_REQUIRED_TERMS if term not in text]
        if missing:
            _append_issue(
                result,
                f"实践任务结构不完整：缺少{'、'.join(missing)}",
                "实践任务必须写清任务目标、操作步骤和验收标准，避免只给泛泛建议。",
                fatal=True,
            )

    course_map = (
        semantic_result.get("ai_course_map")
        or resource.get("ai_course_map")
        or ai_course_map_service.match_ai_course_topic(topic, text)
    )
    if course_map.get("matched"):
        chapter = course_map.get("chapter") or ""
        core_topics = course_map.get("core_topics") or []
        has_chapter = bool(chapter and chapter in text)
        matched_core = [item for item in core_topics if item and item in text]
        if not has_chapter and len(matched_core) < 1:
            _append_issue(
                result,
                f"人工智能课程深度不足：资源未体现「{chapter}」章节或核心知识点",
                "请在正文中明确课程章节、前置知识和核心知识点，避免生成空泛学习建议。",
                fatal=False,
            )

    if level_source == "none":
        level_hits = _contains_any(text, UNSUPPORTED_LEVEL_TERMS)
        if level_hits:
            _append_issue(
                result,
                f"无证据水平推断：出现 {', '.join(level_hits[:4])}",
                "当前主题水平未确认时，只能写入门诊断、基础路线或待确认水平。",
                fatal=True,
            )

    mismatch_terms = TOPIC_MISMATCH_TERMS.get(subject_category, [])
    mismatch_hits = _contains_any(text, mismatch_terms)
    if mismatch_hits:
        # 允许计算机学科中的算法词，不允许外语等主题被 AI/编程术语污染。
        topic_compact = re.sub(r"\s+", "", topic.lower())
        if subject_category == "foreign_language" or "法语" in topic_compact or "英语" in topic_compact:
            _append_issue(
                result,
                f"主题错配：{topic} 资源中出现不相关技术术语（{', '.join(mismatch_hits[:4])}）",
                "请重新生成与主题一致的学科内容。",
                fatal=True,
            )

    if result["passed"]:
        result["issues"].append("语义门禁：未发现学科错配或资源类型错配")
        result["suggestions"].append("建议管理员继续核验事实、来源和课程适配度。")

    return result


def attach_quality_note(notes: str, quality: Dict) -> str:
    issues = quality.get("issues") or []
    suggestions = quality.get("suggestions") or []
    lines = [
        "[[LINGXI_RESOURCE_QUALITY_GATE]]",
        "## 资源语义质量门禁",
        f"- 通过状态：{'通过' if quality.get('passed') else '未通过'}",
        f"- 致命问题：{'是' if quality.get('fatal') else '否'}",
        "",
        "### 问题",
        *[f"- {item}" for item in issues],
        "",
        "### 建议",
        *[f"- {item}" for item in suggestions],
        "[[/LINGXI_RESOURCE_QUALITY_GATE]]",
    ]
    return "\n\n".join(part for part in [notes or "", "\n".join(lines)] if part)
