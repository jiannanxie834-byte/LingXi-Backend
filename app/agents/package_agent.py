import ast
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from app.agents.agent_result_dto import AgentResultDTO
from app.services.data_services import resource_artifact_type_service as artifact_types
from app.services.llm_provider import chat_json


MAX_EVIDENCE_CHARS = 1600


def _clean_text(value: str) -> str:
    return str(value or "").strip()


def _shorten(value: str, limit: int = MAX_EVIDENCE_CHARS) -> str:
    text = _clean_text(value)
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n（以上为课程资源库依据摘要，已截断）"


def _list_value(value, limit: int = 6) -> str:
    if isinstance(value, list):
        return "；".join(str(item) for item in value[:limit] if str(item or "").strip())
    return str(value or "").strip()


def _profile_summary(profile: Dict) -> str:
    profile = profile or {}
    dimensions = profile.get("dimensions") if isinstance(profile.get("dimensions"), dict) else {}
    public_dimensions = profile.get("public_dimensions") if isinstance(profile.get("public_dimensions"), dict) else {}

    def public_value(name: str, fallback=""):
        entry = public_dimensions.get(name)
        if isinstance(entry, dict):
            return entry.get("display") or entry.get("value") or fallback
        return entry or fallback

    fields = [
        ("当前知识水平", public_value("当前知识水平", dimensions.get("知识基础") or profile.get("level") or "待诊断")),
        ("学习目标", public_value("学习目标", dimensions.get("学习目标") or profile.get("goal") or profile.get("intent") or "完成当前主题学习")),
        ("练习表现", public_value("练习表现", dimensions.get("练习表现") or "暂无有效作答")),
        ("薄弱知识点", public_value("薄弱知识点", dimensions.get("易错修复") or profile.get("weakness") or "待练习诊断")),
        ("路径执行", public_value("路径执行", dimensions.get("规划执行") or "尚无执行记录")),
        ("资源偏好", public_value("资源偏好", dimensions.get("媒介偏好") or profile.get("media_preference") or "待确认")),
    ]
    return "\n".join(f"- {key}：{value}" for key, value in fields)


def _grounding_summary(retrieval: Dict) -> str:
    retrieval = retrieval or {}
    exercises = retrieval.get("exercises") or []
    code_tasks = retrieval.get("code_tasks") or []
    videos = retrieval.get("video_items") or []
    metadata = retrieval.get("metadata") or {}
    objectives = metadata.get("objectives", {}).get("objectives") if isinstance(metadata.get("objectives"), dict) else []
    assessment = metadata.get("assessment", {}).get("assessment_points") if isinstance(metadata.get("assessment"), dict) else []
    misconceptions = metadata.get("misconceptions", {}).get("misconceptions") if isinstance(metadata.get("misconceptions"), dict) else []
    exercise_titles = [item.get("title") for item in exercises if isinstance(item, dict)]
    code_titles = [item.get("title") for item in code_tasks if isinstance(item, dict)]
    video_titles = []
    for item in videos:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or "公开视频"
        url = item.get("source_url") or ""
        focus = "、".join(item.get("watch_focus") or [])
        video_titles.append("｜".join(part for part in [title, url, focus] if part))
    misconception_text = []
    for item in misconceptions or []:
        if isinstance(item, dict):
            misconception_text.append(item.get("title") or item.get("description") or "")
        else:
            misconception_text.append(str(item))
    sections = [
        "【小节讲义摘要】",
        _shorten(retrieval.get("section_content") or "", 900) or "暂无小节讲义摘要。",
        "【章节思维导图摘要】",
        _shorten(retrieval.get("mind_map") or "", 500) or "暂无章节思维导图。",
        "【章节目标】",
        _list_value(objectives) or "暂无章节目标。",
        "【测评点】",
        _list_value(assessment) or "暂无测评点。",
        "【常见误区】",
        _list_value(misconception_text) or "暂无误区记录。",
        "【可参考题目标题】",
        _list_value(exercise_titles) or "暂无题目模板。",
        "【可参考代码任务】",
        _list_value(code_titles) or "暂无代码任务模板。",
        "【公开视频/阅读方向】",
        _list_value(video_titles) or _shorten(retrieval.get("reading_video_guide") or "", 500) or "暂无视频方向。",
    ]
    return "\n".join(sections)


def _artifact_instruction(resource_type: str, topic: str) -> str:
    if resource_type == artifact_types.COURSE_NOTE:
        return f"""
生成一份新的个性化课程讲解文档，不能复制小节正文。
必须包含二级标题：学习定位、核心概念、一步步理解、关键流程、例子、常见误区、小结、下一步建议。
课程讲解文档只负责把概念讲清楚，不要生成成套练习题，不要设置“自测题/参考答案”章节；练习题由“练习题集”模块单独负责。
正文不少于 900 个中文字符，围绕「{topic}」和学生当前问题重写讲解。
至少完整展开 2 个不同例子：一个用来推导基本状态转移，一个用来解释边界或选择分支，不得只提例子名称。
"""
    if resource_type == artifact_types.MIND_MAP:
        return f"""
生成新的 Mermaid mindmap，不要返回原始导图。
必须以 mindmap 开头，围绕「{topic}」生成“有层级、有逻辑”的知识结构，不要把所有词平铺在 root 下。
一级分支固定使用这些类别中的 5-6 个：学习定位、前置知识、核心概念、操作流程、典型应用、易错点、练习方向、下一步。
每个一级分支下面必须有 2-4 个二级节点；必要时再加第三级节点说明关系。
禁止输出只有 root + 一堆同级关键词的扁平导图。
示例格式：
mindmap
  root(({topic}))
    前置知识
      需要先理解的概念
      相关数据结构
    核心概念
      概念 A
        为什么重要
      概念 B
    操作流程
      第一步
      第二步
    易错点
      容易混淆的概念
      常见边界情况
"""
    if resource_type == artifact_types.EXERCISE_SET:
        return f"""
生成新的个性化练习题集，不要原样复制题库。
必须包含 4-6 道题，覆盖选择题、判断题、简答题、代码/过程题等至少 3 类。
每题标题必须使用 `### 题目 1｜选择题` 这种格式。
每题必须包含：知识点、题目、答案、解析、常见错误；主观题还必须包含评分要点。
选择题必须给出 A-D 四个独立选项，答案只写选项字母；判断题答案只写“对”或“错”。
不要在题目标题之外使用“题目 N”格式，避免结构解析歧义。
"""
    if resource_type == artifact_types.CODE_LAB:
        return f"""
生成新的个性化代码实验。
必须包含：实验目标、环境依赖、完整代码、运行命令、学生任务、参考实现、至少 3 个可运行测试、复杂度记录、常见报错。
代码任务可参考资源库模板，但需要根据学生当前问题改写。
完整代码必须可直接保存为 Python 文件运行，不得包含 TODO、pass、“补全此处”或伪代码占位。
至少 3 个测试必须直接写在同一个 Python 代码块中，使用 assert 覆盖普通、边界和长输入；仅写 print、注释或测试表格不算可运行测试。
整份资源只允许出现 1 个 `python` 代码块：函数实现、3 个以上 assert 和可直接运行的主入口全部放在该代码块中，必须通过 Python `ast.parse`。
"""
    if resource_type == artifact_types.INTERACTIVE_ANIMATION:
        return f"""
生成一份面向学生的「{topic}」交互动画学习说明。
必须包含：动画目标、可交互参数、播放/暂停/单步/重置操作、每个状态的高亮规则、观看任务、动画后练习。
正文要对已附加的可播放 HTML 动画进行真实操作指引，不得写“占位”、“待实现”或虚构视频链接。
动画后练习不得包含 TODO、pass 或需要补全的代码骨架；如果给出代码，必须是完整可运行示例。
所有代码必须放在标准 Markdown 围栏中，例如以 ```python 开始、以 ``` 结束；禁止只输出单独一行 `python` 后直接跟代码。
"""
    if resource_type == artifact_types.DIAGNOSTIC_REPORT:
        return f"""
生成新的错因诊断与补弱报告。
必须包含：当前卡点、可能错因、薄弱知识、补弱步骤、当天任务、三天复盘任务、后续练习建议。
不要声称已有真实得分，除非画像或评价里明确给出。
"""
    if resource_type == artifact_types.PERSONALIZED_VIDEO_GUIDE:
        return f"""
生成新的个性化视频/阅读学习指南。
必须包含：观看/阅读前准备、观看/阅读中关注点、暂停思考问题、观看/阅读后任务、关联练习、关联代码实验、版权说明。
如依据中有公开视频链接，必须保留原始 source_url 并为每个链接设计观看任务；不得下载、搬运或重新托管。
"""
    if resource_type == artifact_types.READING_PACK:
        return f"""
生成新的个性化拓展阅读包，作为当前主题没有可核验视频时的第五类资源。
必须包含：观看/阅读前准备、观看/阅读中关注点、暂停思考问题、观看/阅读后任务、推荐阅读顺序、关联练习、关联代码实验、版权说明。
优先使用课程资源库中的小节讲义、章节阅读指南和 evidence 依据，不得虚构教材、论文、博客、公开课或 URL。
没有真实链接时直接给出课程章节和知识点阅读顺序，不要写“待补充链接”“暂无资源”或其他占位内容。
"""
    return f"生成一份新的个性化「{resource_type}」，必须结合学生画像和课程依据重写，不能复制资源库原文。"


def _enforce_catalog_video_links(content: str, retrieval: Dict) -> str:
    videos = [item for item in (retrieval or {}).get("video_items") or [] if isinstance(item, dict)]
    allowed = [
        item for item in videos
        if str(item.get("source_url") or "").startswith(("http://", "https://"))
    ][:3]
    if not allowed:
        return content

    allowed_urls = {str(item.get("source_url")) for item in allowed}

    def clean_markdown_link(match):
        label, url = match.group(1), match.group(2)
        return match.group(0) if url in allowed_urls else label

    cleaned = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", clean_markdown_link, content or "")
    for match in list(re.finditer(r"https?://[^\s<>]+", cleaned)):
        raw_url = match.group(0).rstrip(".,，。；;)）]")
        if raw_url not in allowed_urls:
            cleaned = cleaned.replace(match.group(0), "")

    missing = [item for item in allowed if item.get("source_url") not in cleaned]
    if missing:
        lines = ["", "## 知识库公开视频链接", ""]
        for item in missing:
            focus = "、".join(item.get("watch_focus") or []) or "当前主题的核心流程与常见误区"
            lines.append(f"- [{item.get('title') or '公开视频'}]({item.get('source_url')})：观看时重点记录{focus}。")
        cleaned = cleaned.rstrip() + "\n" + "\n".join(lines)
    return cleaned.strip()


MINDMAP_GROUPS = [
    ("前置知识", ("前置", "基础", "定义", "概念", "条件", "复杂度", "数组", "链表", "栈", "队列", "树", "图", "递归")),
    ("核心概念", ("核心", "结构", "性质", "关系", "状态", "指针", "节点", "存储", "顺序", "链式", "最优子结构", "贪心选择")),
    ("操作流程", ("流程", "步骤", "操作", "插入", "删除", "查找", "遍历", "访问", "push", "pop", "peek", "入队", "出队", "递归调用", "转移", "排序", "匹配")),
    ("典型应用", ("应用", "场景", "任务", "项目", "括号", "表达式", "调度", "路径", "Huffman", "编码", "Top", "窗口", "播放", "缓存")),
    ("易错点", ("误区", "错误", "混淆", "忽略", "边界", "反例", "陷阱", "开销", "成本", "不一定", "快慢", "指针")),
    ("练习方向", ("练习", "题", "证明", "验证", "对比", "复盘", "实验", "代码", "实现", "下一步")),
]


def _group_mindmap_nodes(nodes: List[str]) -> List[tuple]:
    grouped = [(name, []) for name, _ in MINDMAP_GROUPS]
    fallback = ("关联概念", [])
    seen = set()
    for raw in nodes:
        item = _clean_text(raw)
        if not item or item in seen:
            continue
        seen.add(item)
        matched = False
        for index, (_, keywords) in enumerate(MINDMAP_GROUPS):
            if any(keyword.lower() in item.lower() for keyword in keywords):
                grouped[index][1].append(item)
                matched = True
                break
        if not matched:
            fallback[1].append(item)
    return [(name, items[:6]) for name, items in [*grouped, fallback] if items]


def _rebuild_grouped_mindmap(root: str, nodes: List[str]) -> str:
    lines = ["mindmap", f"  root(({root}))"]
    for group_name, items in _group_mindmap_nodes(nodes):
        lines.append(f"    {group_name}")
        for item in items:
            lines.append(f"      {item}")
    return "\n".join(lines)


def _normalize_mindmap_content(content: str, topic: str) -> str:
    text = _clean_text(content)
    if not text:
        return text

    fenced_match = re.search(r"```mermaid\s*(.*?)```", text, re.S | re.I)
    diagram = fenced_match.group(1).strip() if fenced_match else text
    if not diagram.lower().startswith("mindmap"):
        return text

    bare_match = None
    if "\n" not in diagram:
        bare_match = re.match(r"mindmap\s+root(?:\(\((.*?)\)\)|\((.*?)\)|\[(.*?)\]|\{(.*?)\}|([^\s]+))\s*(.*)$", diagram, re.S | re.I)
    if bare_match:
        root = next((value for value in bare_match.groups()[:5] if value), None) or topic
        nodes = [item for item in re.split(r"\s+", bare_match.group(6) or "") if item]
        if len(nodes) >= 6:
            return _dedupe_mindmap_nodes(_rebuild_grouped_mindmap(root, nodes))

    lines = [line.rstrip() for line in diagram.splitlines() if line.strip()]
    root_line = next((line.strip() for line in lines if line.strip().lower().startswith("root")), "")
    child_lines = [line for line in lines if not line.strip().lower().startswith(("mindmap", "root"))]
    is_flat = len(child_lines) >= 8 and all((len(line) - len(line.lstrip(" "))) <= 4 for line in child_lines)
    if not is_flat:
        return _dedupe_mindmap_nodes(diagram)

    root_match = re.match(r"root(?:\(\((.*?)\)\)|\((.*?)\)|\[(.*?)\]|\{(.*?)\}|(.*))", root_line, re.I)
    root = topic
    if root_match:
        root = next((value for value in root_match.groups() if _clean_text(value)), None) or topic
    nodes = [line.strip() for line in child_lines]
    return _dedupe_mindmap_nodes(_rebuild_grouped_mindmap(root, nodes))


def _normalize_code_lab_content(content: str) -> str:
    """Restore a Markdown fence only when the model's raw code is valid Python.

    Spark's JSON mode may omit triple backticks while preserving the `python`
    language marker. The quality gate still performs the authoritative AST
    validation; this normalization only makes an already complete program
    machine-extractable.
    """
    text = _clean_text(content)
    if not text or re.search(r"```python\s*.*?```", text, re.S | re.I):
        return text

    match = re.search(
        r"(?P<heading>^##\s*完整代码[^\n]*\n)(?P<code>.*?)(?=^##\s+|\Z)",
        text,
        re.S | re.M,
    )
    if not match:
        return text

    code = match.group("code").strip()
    code = re.sub(r"^python\s*\n", "", code, count=1, flags=re.I)
    try:
        ast.parse(code)
    except SyntaxError:
        return text

    replacement = f'{match.group("heading")}```python\n{code}\n```\n\n'
    return (text[:match.start()] + replacement + text[match.end():]).strip()


CODE_LANGUAGE_RE = re.compile(
    r"^(python|py|javascript|js|typescript|ts|java|cpp|c\+\+|c|go|rust|bash|shell|sql)$",
    re.I,
)
CODE_START_RE = re.compile(
    r"^(def\s+|class\s+|from\s+\S+\s+import\s+|import\s+|if\s+.+:|for\s+.+:|while\s+.+:|"
    r"try:|with\s+.+:|return\s+|raise\s+|print\s*\(|assert\s+|[A-Za-z_]\w*\s*=|#)"
)


def _normalize_markdown_code_blocks(content: str) -> str:
    """Repair a bare language marker without changing ordinary prose."""
    lines = str(content or "").splitlines()
    output = []
    inside_fence = False
    repairing = False

    for index, line in enumerate(lines):
        stripped = line.strip()
        if repairing and re.match(r"^#{2,6}\s+", stripped):
            while output and not output[-1].strip():
                output.pop()
            output.extend(["```", ""])
            repairing = False

        if not repairing and stripped.startswith("```"):
            inside_fence = not inside_fence
            output.append(line)
            continue

        next_line = next(
            (candidate.strip() for candidate in lines[index + 1:] if candidate.strip()),
            "",
        )
        if (
            not inside_fence
            and not repairing
            and CODE_LANGUAGE_RE.match(stripped)
            and CODE_START_RE.match(next_line)
        ):
            language = "python" if stripped.lower() in {"py", "python"} else stripped.lower()
            output.append(f"```{language}")
            repairing = True
            continue

        output.append(line)

    if repairing:
        while output and not output[-1].strip():
            output.pop()
        output.append("```")
    return "\n".join(output).strip()


def _dedupe_mindmap_nodes(diagram: str) -> str:
    """只删除 Mermaid 中完全相同的重复节点，不改写模型生成的教学内容。"""
    result = []
    seen = set()
    for line in (diagram or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower() == "mindmap" or stripped.lower().startswith("root"):
            result.append(line)
            continue
        normalized = re.sub(r"\s+", "", stripped)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(line)
    return "\n".join(result).strip()


def _generate_one(item: Dict, location: Dict, profile: Dict, retrieval: Dict) -> Dict:
    resource_type = artifact_types.normalize_artifact_type(item.get("type") or "")
    topic = item.get("display_topic") or item.get("topic") or location.get("topic") or "当前学习主题"
    student_question = item.get("student_question") or location.get("student_question") or topic
    prompt = f"""
你是《数据结构与算法》个性化资源生成系统中的 PersonalizedGenerationAgent。
请只生成一种 ResourceArtifact，不要生成整包 JSON。

学生当前问题：
{student_question}

当前知识点：
{topic}

学生画像摘要：
{_profile_summary(profile)}

课程资源库依据摘要（只能作为 grounding context，不能原样复制为最终正文）：
{_grounding_summary(retrieval)}

Artifact 类型：
{resource_type}

生成要求：
{_artifact_instruction(resource_type, topic)}

严格禁止：
- 不要输出资源库路径、内部 ID、匹配日志、质量分、风险等级。
- 不要出现 dsa_、sec_、unit_id、chapter_id、section_id、artifact_id、resource_id、link_only、pending_curation。
- 不要把课程资源库原文原样复制成正文。
- 不要说“资源库匹配内容”“raw evidence”“matched_resources”。

只返回 JSON 对象：
{{
  "summary": "学生可读的简短说明",
  "content": "学生真正看到的个性化正文",
  "personalization_reason": "一句话说明如何结合了学生问题、画像和课程依据"
}}
"""
    error_message = "讯飞星火未返回有效内容"
    try:
        token_budget = {
            artifact_types.COURSE_NOTE: 3600,
            artifact_types.CODE_LAB: 5200,
            artifact_types.EXERCISE_SET: 3600,
            artifact_types.PERSONALIZED_VIDEO_GUIDE: 2400,
            artifact_types.INTERACTIVE_ANIMATION: 2400,
            artifact_types.MIND_MAP: 1800,
        }.get(resource_type, 2600)
        result = chat_json(
            [{"role": "user", "content": prompt}],
            # 正文才是资源的必需字段；摘要和个性化说明属于展示元数据，
            # 模型偶尔漏掉时使用下方已有的系统默认值，不能让整包五类资源回滚。
            required_fields=["content"],
            temperature=0.25,
            max_tokens=token_budget,
        )
        if result.get("ok"):
            data = result.get("data") or {}
            content = _clean_text(data.get("content"))
            if content:
                if resource_type == artifact_types.MIND_MAP:
                    content = _normalize_mindmap_content(content, topic)
                elif resource_type == artifact_types.CODE_LAB:
                    content = _normalize_code_lab_content(content)
                    content = _normalize_markdown_code_blocks(content)
                elif resource_type == artifact_types.PERSONALIZED_VIDEO_GUIDE:
                    content = _normalize_markdown_code_blocks(content)
                    content = _enforce_catalog_video_links(content, retrieval)
                else:
                    content = _normalize_markdown_code_blocks(content)
                return {
                    "summary": _clean_text(data.get("summary")) or item.get("summary") or "",
                    "content": content,
                    "source": "数据结构与算法课程资源库依据生成",
                    "personalization_reason": _clean_text(data.get("personalization_reason")) or item.get("personalization_reason") or "",
                    "assembly_policy": "personalized_generation_from_grounded_context",
                    "missing": False,
                }
        error_message = _clean_text(result.get("error")) or error_message
    except Exception as exc:
        error_message = _clean_text(exc) or error_message

    return {
        "summary": "",
        "content": "",
        "source": "",
        "personalization_reason": "",
        "assembly_policy": "generation_failed_no_fallback",
        "missing": True,
        "error": error_message[:240],
    }


def run(resources: List[Dict], location: Dict, profile: Dict, retrieval: Dict) -> dict:
    resources = resources or []
    location = location or {}
    profile = profile or {}
    retrieval = retrieval or {}
    packaged = [None] * len(resources)
    # 资源生成优先保证单次输出完整；串行调用避免并发触发 QPS 限制后返回降级模板。
    max_workers = 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_generate_one, item, location, profile, retrieval): index
            for index, item in enumerate(resources)
        }
        for future in as_completed(future_map):
            packaged[future_map[future]] = future.result()

    dto = AgentResultDTO(
        agent_name="PersonalizedGenerationAgent",
        input_summary=location.get("topic") or "数据结构与算法个性化学习包",
        output={
            "resource_count": sum(1 for item in packaged if not item.get("missing")),
            "types": [item.get("type") for item in resources],
            "assembly_policy": "personalized_generation_from_grounded_context",
            "grounding_used": True,
            "profile_used": bool(profile),
            "minimum_resource_count_met": sum(1 for item in packaged if not item.get("missing")) >= 5,
            "missing_count": sum(1 for item in packaged if item.get("missing")),
        },
        evidence_refs=location.get("evidence_refs") or [],
        quality_score=sum(1 for item in packaged if not item.get("missing")) / max(1, len(packaged)),
        warnings=[
            f"{resources[index].get('type')}生成失败：{item.get('error') or '未知原因'}"
            for index, item in enumerate(packaged)
            if item.get("missing")
        ],
    )
    return {"dto": dto, "outputs": packaged}
