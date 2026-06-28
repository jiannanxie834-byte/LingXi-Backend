import re
from typing import Dict, List

from app.agents.agent_result_dto import AgentResultDTO
from app.services.data_services import resource_artifact_type_service as artifact_types
from app.services.llm_provider import chat_json


EMPTY_TEXT = "该类资源暂未完善"
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
    fields = [
        ("知识基础", dimensions.get("知识基础") or profile.get("level") or "未确认"),
        ("学习目标", dimensions.get("学习目标") or profile.get("goal") or profile.get("intent") or "完成当前主题学习"),
        ("知识短板", dimensions.get("知识短板") or profile.get("weakness") or "需要通过本轮任务继续诊断"),
        ("认知风格", dimensions.get("认知风格") or profile.get("cognitive_style") or "文字讲解配合例题"),
        ("媒介偏好", dimensions.get("媒介偏好") or profile.get("media_preference") or "图解/代码示例/练习巩固"),
        ("实践能力", dimensions.get("实践能力") or profile.get("practice_ability") or "未确认"),
        ("易错模式", dimensions.get("易错模式") or profile.get("mistake_pattern") or "边界条件、概念迁移和模板套用需重点观察"),
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
每题必须包含：知识点、题目、答案、解析、常见错误。
"""
    if resource_type == artifact_types.CODE_LAB:
        return f"""
生成新的个性化代码实验。
必须包含：实验目标、环境依赖、完整代码、运行命令、学生任务、提示、参考答案、复杂度记录、常见报错。
代码任务可参考资源库模板，但需要根据学生当前问题改写。
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
    return f"生成一份新的个性化「{resource_type}」，必须结合学生画像和课程依据重写，不能复制资源库原文。"


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

    bare_match = re.match(r"mindmap\s+root(?:\(\((.*?)\)\)|\((.*?)\)|\[(.*?)\]|\{(.*?)\}|([^\s]+))\s*(.*)$", diagram, re.S | re.I)
    if bare_match:
        root = next((value for value in bare_match.groups()[:5] if value), None) or topic
        nodes = [item for item in re.split(r"\s+", bare_match.group(6) or "") if item]
        if len(nodes) >= 6:
            return _rebuild_grouped_mindmap(root, nodes)

    lines = [line.rstrip() for line in diagram.splitlines() if line.strip()]
    root_line = next((line.strip() for line in lines if line.strip().lower().startswith("root")), "")
    child_lines = [line for line in lines if not line.strip().lower().startswith(("mindmap", "root"))]
    is_flat = len(child_lines) >= 8 and all((len(line) - len(line.lstrip(" "))) <= 4 for line in child_lines)
    if not is_flat:
        return diagram

    root_match = re.match(r"root(?:\(\((.*?)\)\)|\((.*?)\)|\[(.*?)\]|\{(.*?)\}|(.*))", root_line, re.I)
    root = topic
    if root_match:
        root = next((value for value in root_match.groups() if _clean_text(value)), None) or topic
    nodes = [line.strip() for line in child_lines]
    return _rebuild_grouped_mindmap(root, nodes)


def _fallback_content(resource_type: str, topic: str, student_question: str, profile: Dict, retrieval: Dict) -> Dict:
    profile_text = _profile_summary(profile)
    topic = topic or "当前主题"
    if resource_type == artifact_types.MIND_MAP:
        content = f"""mindmap
  root(({topic}))
    学习定位
      当前问题：{student_question or topic}
      基础状态：先按入门诊断处理
    前置知识
      先复习定义
      再看适用条件
      最后处理边界情况
    核心理解
      概念含义
      操作流程
      复杂度影响
    易错点
      套模板但不解释条件
      忽略边界输入
      无法手推一个小例子
    练习方向
      概念辨析
      手推过程
      代码补全
    下一步
      完成 3 道基础题
      复盘错误原因
"""
    elif resource_type == artifact_types.EXERCISE_SET:
        content = f"""# {topic} 个性化练习题集

### 题目 1｜选择题
知识点：{topic} 的适用条件。
题目：学习「{topic}」时，第一步最应该确认什么？
答案：先确认定义、适用条件和输入输出约束。
解析：很多错误来自还没确认问题边界就套模板。
常见错误：只记结论，不说明为什么适用。

### 题目 2｜判断题
知识点：{topic} 的掌握标准。
题目：只要代码能跑通样例，就说明已经掌握「{topic}」。对还是错？
答案：错。
解析：还需要能解释边界条件、复杂度和失败场景。
常见错误：忽略空输入、重复元素或极端规模。

### 题目 3｜简答题
知识点：{topic} 的核心思想。
题目：用自己的话解释「{topic}」的核心思想。
答案：应围绕问题如何被表示、状态如何变化、结果如何验证来说明。
解析：能用自然语言讲清楚，通常比直接背模板更稳。
常见错误：只写关键词，不描述过程。

### 题目 4｜过程题
知识点：{topic} 的手推过程。
题目：构造一个最小例子，手推「{topic}」的关键步骤。
答案：选择 3-5 个元素或一个小规模输入，逐步写出每一步变化。
解析：手推能暴露对边界和更新顺序的理解漏洞。
常见错误：跳过中间状态。

## 练习顺序
先完成选择题和判断题，确认你能说清楚「{topic}」的适用条件；再做简答题，检查自己是否能不用模板解释核心思想；最后做过程题，把每一步变化写出来。不要只看答案是否一致，要看你的推理是否能覆盖边界情况。

## 复盘清单
1. 我是否能说明「{topic}」解决的问题类型？
2. 我是否写出了输入、输出和关键约束？
3. 我是否能解释为什么这一步更新合法？
4. 我是否检查了空输入、单元素、重复元素或极端规模？
5. 我是否能给出时间复杂度和空间复杂度？
"""
    elif resource_type == artifact_types.CODE_LAB:
        content = f"""# {topic} 个性化代码实验

## 实验目标
围绕「{topic}」完成一个最小可运行实现，并能解释输入、输出、复杂度和边界情况。

## 环境依赖
- Python 3.10+
- 终端运行：`python main.py`

## 完整代码
```python
def solve(data):
    \"\"\"根据当前主题补全核心逻辑。\"\"\"
    result = []
    for item in data:
        # TODO: 根据 {topic} 的规则更新 result
        result.append(item)
    return result

if __name__ == "__main__":
    sample = [1, 2, 3]
    print(solve(sample))
```

## 运行命令
```bash
python main.py
```

## 学生任务
1. 写出输入输出含义。
2. 补全核心更新逻辑。
3. 增加一个边界用例。
4. 记录时间复杂度和空间复杂度。

## 提示
先用最小样例手推，再写代码；不要直接套模板。

## 参考答案
参考答案需要根据你选择的具体题目补全，重点是解释为什么每一步更新合法。

## 复杂度记录
写出循环次数、辅助空间和输入规模之间的关系。

## 常见报错
- 空输入没有处理。
- 下标越界。
- 更新顺序导致旧状态被覆盖。

## 实验复盘
完成代码后，请不要只看输出是否等于样例。你需要补充至少 3 个测试：最小输入、普通输入和边界输入。每个测试都写清楚预期输出，并说明为什么这个输出符合「{topic}」的规则。最后把代码中的核心变量变化画成表格，这能帮助你发现循环条件、更新顺序和返回值位置的问题。

## 实验报告
实验报告建议包含：题目目标、输入输出定义、核心算法流程、完整代码、运行截图或运行结果、复杂度分析、遇到的错误和修复方式。对当前基础阶段来说，能写清楚“为什么这么更新”比写出更短的代码更重要。
"""
    elif resource_type == artifact_types.PERSONALIZED_VIDEO_GUIDE:
        videos = retrieval.get("video_items") or []
        video_lines = []
        for video in videos[:4]:
            if not isinstance(video, dict):
                continue
            title = video.get("title") or "公开视频"
            url = video.get("source_url") or ""
            focus = "、".join(video.get("watch_focus") or [])
            before = "；".join(video.get("before_watch") or [])
            after = "；".join(video.get("after_watch_tasks") or [])
            if url:
                video_lines.append(f"- [{title}]({url})：观看重点：{focus or topic}；观看前：{before or '先写下当前疑问'}；观看后：{after or '完成一次复述和一道练习'}。")
        content = f"""# {topic} 个性化视频与阅读学习指南

## 观看/阅读前准备
先写下你对「{topic}」的当前理解，以及最不确定的一个问题。

## 观看/阅读中关注点
- 关注定义和适用条件。
- 暂停手推一个小例子。
- 记录和你当前问题直接相关的步骤。

## 暂停思考问题
为什么这个方法适用于当前输入？如果输入为空、重复或规模很大会怎样？

## 观看/阅读后任务
用 5 句话复述核心流程，并完成 2 道基础题。

## 推荐视频链接
{chr(10).join(video_lines) if video_lines else "- 当前匹配小节暂未配置公开视频链接，先使用课程讲解、导图、练习题和代码实验完成学习。"}

## 关联练习
优先做概念辨析题和过程手推题，再进入代码补全。

## 关联代码实验
把核心过程写成函数，并补充边界用例。

## 版权说明
公开视频和阅读材料仅保留原始入口与学习任务，不下载、不搬运、不重新托管。
"""
    elif resource_type == artifact_types.DIAGNOSTIC_REPORT:
        content = f"""# {topic} 诊断与补弱报告

## 当前卡点
你当前的问题是：{student_question or topic}。系统暂未看到完整作答记录，因此先按学习表达和画像做轻量诊断。

## 可能错因
- 定义和适用条件没有分清。
- 只记模板，没有手推过程。
- 边界输入和复杂度分析容易被跳过。

## 薄弱知识
{profile_text}

## 补弱步骤
1. 回到定义，用一句话说明主题解决什么问题。
2. 用最小样例手推一次。
3. 写出边界情况。
4. 完成 3 道基础题并复盘错误。

## 当天任务
完成一份概念解释、一张手绘流程图和两道基础题。

## 三天复盘任务
第一天补概念，第二天补代码，第三天做混合题。

## 后续练习建议
先做基础题，再做变式题，最后做综合题。
"""
    else:
        content = f"""# 为你定制的 {topic} 讲解

## 学习定位
当前问题：{student_question or topic}。这份讲解不是直接复制课程小节，而是把课程资源库中的定义、例题方向和常见误区重新组织成适合你当前卡点的学习材料。先按“能说清楚概念、能手推过程、能写出边界条件”的目标来学，不急着背模板。

## 核心概念
「{topic}」的核心不是某个孤立结论，而是理解它解决什么问题、输入输出是什么、为什么这个方法或结构适用。学习时要先说清楚对象：处理的是序列、集合、树、图，还是一个可以拆分成子问题的过程；再说明操作：是查找、插入、删除、遍历、转移，还是维护某种约束；最后说明代价：时间复杂度和空间复杂度分别由什么决定。

## 一步步理解
1. 找到问题对象。
2. 明确状态或数据结构。
3. 手推最小例子。
4. 检查边界条件。
5. 再把手推过程翻译成代码或伪代码。
6. 用复杂度分析验证这个方法是否适合输入规模。

## 例子
示例一：如果题目给出 3-5 个元素，先不要写代码，先在纸上标出每一步变量、指针、队列、栈或状态数组的变化。你需要能解释“这一步为什么合法”，而不是只得到最后答案。

示例二：把同一个输入改成空输入、只有一个元素、存在重复元素或规模很大的情况，再检查原来的思路是否仍然成立。很多算法错误不是概念不会，而是边界条件没有被纳入同一套流程。

例题：请用一句话说明「{topic}」适合解决哪类问题，再写出一个最小输入并手推完整过程。答案不要求长，但必须包含输入、关键步骤、输出和复杂度。

## 常见误区
- 只记结论。
- 不说明适用条件。
- 忽略边界输入。
- 把相似概念混在一起，例如把“能访问”误认为“复杂度一定低”，或者把“模板能套”误认为“状态定义已经正确”。
- 写代码时先写循环，再回头猜变量含义，导致调试时不知道错误发生在哪一步。

## 小结
学习「{topic}」时，最重要的是把定义、适用条件、关键流程和复杂度来源连成一条线。你应该能说清楚它适合解决什么问题、每一步为什么成立、哪些输入会触发边界情况，以及它和相近知识点有什么区别。

## 下一步建议
如果你已经能复述本讲解的核心流程，可以进入配套“练习题集”模块做题；如果你还不能解释边界条件，先回到“例子”和“常见误区”两节，把最小样例和边界样例重新手推一遍。
"""
    return {
        "summary": f"根据你的问题「{student_question or topic}」生成的个性化{resource_type}。",
        "content": content,
        "personalization_reason": f"结合当前问题、学生画像和课程资源库依据生成，不直接复制原始资源。",
    }


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
    try:
        result = chat_json(
            [{"role": "user", "content": prompt}],
            required_fields=["summary", "content", "personalization_reason"],
            temperature=0.35,
            max_tokens=2600,
        )
        if result.get("ok"):
            data = result.get("data") or {}
            content = _clean_text(data.get("content"))
            if content:
                if resource_type == artifact_types.MIND_MAP:
                    content = _normalize_mindmap_content(content, topic)
                return {
                    "summary": _clean_text(data.get("summary")) or item.get("summary") or "",
                    "content": content,
                    "source": "数据结构与算法课程资源库依据生成",
                    "personalization_reason": _clean_text(data.get("personalization_reason")) or item.get("personalization_reason") or "",
                    "assembly_policy": "personalized_generation_from_grounded_context",
                    "missing": False,
                }
    except Exception:
        pass

    fallback = _fallback_content(resource_type, topic, student_question, profile, retrieval)
    if resource_type == artifact_types.MIND_MAP:
        fallback["content"] = _normalize_mindmap_content(fallback.get("content") or "", topic)
    return {
        **fallback,
        "source": "数据结构与算法课程资源库依据生成",
        "assembly_policy": "personalized_generation_fallback",
        "missing": False,
    }


def run(resources: List[Dict], location: Dict, profile: Dict, retrieval: Dict) -> dict:
    resources = resources or []
    location = location or {}
    profile = profile or {}
    retrieval = retrieval or {}
    packaged = [_generate_one(item, location, profile, retrieval) for item in resources]

    dto = AgentResultDTO(
        agent_name="PersonalizedGenerationAgent",
        input_summary=location.get("topic") or "数据结构与算法个性化学习包",
        output={
            "resource_count": len(packaged),
            "types": [item.get("type") for item in resources],
            "assembly_policy": "personalized_generation_from_grounded_context",
            "grounding_used": True,
            "profile_used": bool(profile),
            "minimum_resource_count_met": len(packaged) >= 5,
            "missing_count": sum(1 for item in packaged if item.get("missing")),
        },
        evidence_refs=location.get("evidence_refs") or [],
        quality_score=1.0 if len(packaged) >= 5 else 0.75,
        warnings=[] if len(packaged) >= 5 else ["个性化学习包资源类型少于 5 类"],
    )
    return {"dto": dto, "outputs": packaged}
