from app.services import db_service, llm_provider


COURSE_KNOWLEDGE = [
    {
        "topic": "Vue3 组合式 API",
        "keywords": ["vue", "vue3", "组合式", "ref", "reactive", "生命周期", "pinia", "router"],
        "chapter": "前端工程化课程 / Vue3 组合式 API",
        "core": "响应式数据、组件状态拆分、生命周期、路由与状态管理",
        "pitfalls": ["在 script 中忘记 ref 的 .value", "watch 监听源写错", "把业务逻辑全部堆在单组件中"],
        "practice": "实现一个可筛选、可编辑、可持久化的学习任务面板",
        "practice_kind": "coding",
        "practice_output": "可运行的小功能、关键代码片段和功能复盘",
        "code_lang": "javascript",
        "code": """import { ref, computed } from 'vue'

const keyword = ref('')
const tasks = ref([
  { title: '理解 ref 和 reactive', done: false },
  { title: '完成组合式函数拆分', done: false }
])

const filteredTasks = computed(() =>
  tasks.value.filter(task => task.title.includes(keyword.value))
)""",
    },
    {
        "topic": "计算机网络",
        "keywords": ["计网", "网络", "tcp", "udp", "三次握手", "四次挥手", "http", "https"],
        "chapter": "计算机网络课程 / TCP-IP 与应用层协议",
        "core": "分层模型、可靠传输、拥塞控制、HTTP 请求响应与安全通信",
        "pitfalls": ["混淆 TCP 与 UDP 的适用场景", "只背三次握手流程而不理解状态变化", "忽略抓包验证"],
        "practice": "使用 Wireshark 抓取一次 HTTP 请求并标注每一层协议字段",
        "practice_kind": "experiment",
        "practice_output": "抓包截图、协议字段标注表和现象解释",
    },
    {
        "topic": "Python 数据分析",
        "keywords": ["python", "pandas", "数据分析", "numpy", "可视化", "matplotlib"],
        "chapter": "Python 数据分析课程 / 数据清洗与统计分析",
        "core": "数据读取、缺失值处理、分组统计、可视化表达",
        "pitfalls": ["没有检查缺失值就直接建模", "分组统计口径不一致", "图表只好看但没有表达结论"],
        "practice": "清洗一份学生学习行为数据并输出每周学习时长趋势",
        "practice_kind": "coding",
        "practice_output": "清洗后的数据表、统计结果和趋势图",
        "code_lang": "python",
        "code": """import pandas as pd

df = pd.read_csv('learning_logs.csv')
df['date'] = pd.to_datetime(df['date'])
weekly = df.groupby(pd.Grouper(key='date', freq='W'))['minutes'].sum()
print(weekly.tail())""",
    },
    {
        "topic": "人工智能导论",
        "keywords": ["人工智能", "机器学习", "深度学习", "模型", "神经网络", "分类", "训练"],
        "chapter": "人工智能导论课程 / 机器学习基础",
        "core": "监督学习、特征工程、训练验证划分、模型评估",
        "pitfalls": ["只看准确率不看混淆矩阵", "训练集和测试集泄漏", "没有记录实验参数"],
        "practice": "用鸢尾花数据集训练一个分类器并解释评估指标",
        "practice_kind": "modeling",
        "practice_output": "实验参数记录、评估结果和模型解释",
        "code_lang": "python",
        "code": """from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)
model = DecisionTreeClassifier(max_depth=3).fit(X_train, y_train)
print(model.score(X_test, y_test))""",
    },
    {
        "topic": "高等数学",
        "keywords": ["数学", "高数", "微积分", "导数", "积分", "极限", "函数", "建模"],
        "chapter": "高等数学课程 / 函数、极限、导数与积分",
        "core": "函数关系、极限思想、导数应用、积分累积与数学建模",
        "pitfalls": ["只套公式不解释变量含义", "忽略定义域和边界条件", "把计算结果和实际问题脱节"],
        "practice": "选择一个生活中的最优化问题，用函数建模并说明导数如何帮助决策",
        "practice_kind": "modeling",
        "practice_output": "问题描述、变量设定、函数模型、求解过程和结论解释",
    },
    {
        "topic": "大学物理",
        "keywords": ["物理", "力学", "电磁", "实验", "速度", "加速度", "牛顿", "能量"],
        "chapter": "大学物理课程 / 力学实验与能量分析",
        "core": "物理量测量、受力分析、能量守恒、实验误差与数据解释",
        "pitfalls": ["只背公式不画受力图", "忽略单位和量纲", "实验结论没有误差分析"],
        "practice": "设计一个小车斜面运动实验，记录数据并分析速度变化规律",
        "practice_kind": "experiment",
        "practice_output": "实验方案、数据记录表、图像分析和误差说明",
    },
    {
        "topic": "大学英语",
        "keywords": ["英语", "阅读", "写作", "作文", "口语", "听力", "翻译", "词汇"],
        "chapter": "大学英语课程 / 阅读理解与写作表达",
        "core": "主题句识别、段落结构、关键词推断、观点表达与语言修改",
        "pitfalls": ["逐词翻译导致句意割裂", "作文观点缺少论据", "忽略段落之间的逻辑衔接"],
        "practice": "围绕一个校园学习主题完成阅读批注，并改写一段 120 词短文",
        "practice_kind": "writing",
        "practice_output": "阅读批注、关键词表、改写短文和修改说明",
    },
    {
        "topic": "历史与思政",
        "keywords": ["历史", "思政", "政治", "材料分析", "近代史", "论述", "观点"],
        "chapter": "历史与思政课程 / 材料阅读与观点论证",
        "core": "史料提取、背景定位、观点判断、论据组织与价值分析",
        "pitfalls": ["只复述材料不提出观点", "史实时间线混乱", "论证缺少材料证据支撑"],
        "practice": "围绕一段历史材料提炼观点，并用两条史实论据完成短论证",
        "practice_kind": "analysis",
        "practice_output": "材料要点表、观点句、论据链和短论证文本",
    },
]


def _infer_knowledge(message: str):
    text = message.lower()
    for item in COURSE_KNOWLEDGE:
        if any(keyword in text for keyword in item["keywords"]):
            return item
    return COURSE_KNOWLEDGE[3]


def _infer_intent(message: str):
    if any(word in message for word in ["题", "练习", "考试", "测验", "刷题"]):
        return "练习巩固"
    if any(word in message for word in ["代码", "项目", "实操", "案例", "demo"]):
        return "实操训练"
    if any(word in message for word in ["不会", "不懂", "解释", "讲一下", "原理"]):
        return "概念讲解"
    if any(word in message for word in ["规划", "路线", "怎么学", "计划"]):
        return "路径规划"
    return "综合学习"


def _build_profile(user, message: str, knowledge: dict, intent: str):
    tags = [t for t in (user.tags or "").split(",") if t] if user else []
    base_score = min(88, 45 + (user.hours if user else 0) * 2)
    practice_score = 82 if intent == "实操训练" else 66
    focus_score = 76 if len(message) >= 12 else 58

    return {
        "tags": list(dict.fromkeys(tags + [knowledge["topic"], intent])),
        "dimensions": {
            "知识基础": base_score,
            "认知风格": "视觉-实践型" if intent in ["实操训练", "综合学习"] else "文字-理解型",
            "学习目标": intent,
            "知识短板": "、".join(knowledge["pitfalls"][:2]),
            "易错点偏好": knowledge["pitfalls"][0],
            "实践能力": practice_score,
            "学习专注度": focus_score,
        },
        "radar": {
            "知识基础": base_score,
            "自驱探索力": min(92, focus_score + 8),
            "实践动手能力": practice_score,
            "学习专注度": focus_score,
            "易错点修复": 68 if intent == "概念讲解" else 76,
            "认知匹配度": 86 if intent in ["实操训练", "综合学习"] else 78,
        },
    }


def _build_practice_summary(knowledge: dict):
    kind_labels = {
        "coding": "代码项目与功能实现",
        "experiment": "实验探究与数据记录",
        "modeling": "建模分析与结果解释",
        "writing": "语言表达与作品改写",
        "analysis": "材料分析与观点论证",
    }
    label = kind_labels.get(knowledge.get("practice_kind"), "综合应用任务")
    return f"{label}：{knowledge['practice']}。产出物包括{knowledge.get('practice_output', '过程记录和复盘说明')}。"


def _build_practice_preview(knowledge: dict):
    if knowledge.get("code"):
        return f"""实践任务：{knowledge['practice']}

```{knowledge.get('code_lang', '')}
{knowledge['code']}
```"""

    return f"""实践任务：{knowledge['practice']}

建议产出：{knowledge.get('practice_output', '过程记录、结论说明和复盘')}。"""


def _build_practice_resource_content(resource: dict, knowledge: dict, intent: str):
    kind = knowledge.get("practice_kind", "application")
    if kind == "coding":
        return f"""# {resource['title']}

## 任务目标
{knowledge['practice']}

## 参考实现
```{knowledge.get('code_lang', '')}
{knowledge.get('code', '')}
```

## 产出要求
- 提交可运行代码或关键截图。
- 说明代码验证了 {knowledge['topic']} 的哪个核心概念。
- 记录至少 2 条调试或错误排查过程。

## 复盘问题
1. 你把哪些知识点转化成了可运行功能？
2. 哪个步骤最容易出错？
3. 下次如何避免「{knowledge['pitfalls'][0]}」？
"""

    if kind == "experiment":
        return f"""# {resource['title']}

## 探究任务
{knowledge['practice']}

## 操作步骤
1. 明确观察对象和关键变量。
2. 设计记录表，采集至少 3 组有效数据或现象。
3. 对照「{knowledge['core']}」解释结果。
4. 写出误差来源或可能的干扰因素。

## 产出要求
- 实验或观察方案
- 数据记录表
- 现象解释
- 误差/局限分析
"""

    if kind == "modeling":
        return f"""# {resource['title']}

## 应用任务
{knowledge['practice']}

## 完成步骤
1. 把现实问题拆成变量、条件和目标。
2. 建立可解释的模型或分析框架。
3. 给出求解过程，说明每一步对应的知识点。
4. 将结果放回真实情境中解释。

## 产出要求
{knowledge.get('practice_output', '模型说明、求解过程和结论解释')}
"""

    if kind == "writing":
        return f"""# {resource['title']}

## 表达任务
{knowledge['practice']}

## 完成步骤
1. 先标注材料中的主题句和关键词。
2. 整理观点、论据和连接词。
3. 完成初稿后进行一次结构修改。
4. 标出至少 3 处语言表达改进。

## 产出要求
{knowledge.get('practice_output', '批注文本、改写作品和修改说明')}
"""

    return f"""# {resource['title']}

## 分析任务
{knowledge['practice']}

## 完成步骤
1. 提取材料中的关键信息。
2. 判断材料对应的背景、概念或观点。
3. 用至少两条证据支撑自己的结论。
4. 写出一段结构完整的分析文本。

## 产出要求
{knowledge.get('practice_output', '要点表、论证链和分析短文')}
"""


def _build_resources(knowledge: dict, intent: str):
    resources = [
        {
            "type": "专业课程讲解文档",
            "title": f"{knowledge['topic']} 个性化讲解文档",
            "summary": f"围绕 {knowledge['core']} 进行分层讲解，并补充关键概念、例子和复习提示。",
        },
        {
            "type": "知识点思维导图",
            "title": f"{knowledge['topic']} 知识结构图",
            "summary": f"中心节点为 {knowledge['topic']}，一级节点包括核心概念、常见误区、实践任务、评估指标。",
        },
        {
            "type": "不同类型练习题目",
            "title": f"{knowledge['topic']} 分层练习题",
            "summary": "包含 3 道概念判断题、2 道应用题、1 道开放实践题，并标注推荐完成顺序。",
        },
        {
            "type": "拓展阅读材料",
            "title": f"{knowledge['topic']} 拓展阅读清单",
            "summary": f"优先阅读课程章节「{knowledge['chapter']}」，再补充官方文档、案例文章和实验记录模板。",
        },
        {
            "type": "错题诊断与学习反馈报告",
            "title": f"{knowledge['topic']} 错题诊断报告",
            "summary": f"结合 {knowledge['topic']} 常见误区和当前学习意图，给出错因分析、补救建议和复习优先级。",
        },
        {
            "type": "学科实践应用任务",
            "title": f"{knowledge['topic']} 学科实践应用任务",
            "summary": _build_practice_summary(knowledge),
        },
    ]
    for item in resources:
        item["source"] = knowledge["chapter"]
        item["agent_notes"] = f"由资源生成 Agent 基于「{knowledge['chapter']}」和当前学习意图「{intent}」生成，建议管理员重点核对术语、例题和实践步骤。"
        item["content"] = _build_resource_content(item, knowledge, intent)
    return resources


def _build_resource_content(resource: dict, knowledge: dict, intent: str):
    resource_type = resource["type"]
    if resource_type == "专业课程讲解文档":
        return f"""# {resource['title']}

## 学习目标
- 理解 {knowledge['topic']} 中的核心概念：{knowledge['core']}。
- 能识别并修正常见误区：{knowledge['pitfalls'][0]}。
- 能完成一个和课程内容对应的小型实践任务。

## 核心讲解
{knowledge['topic']} 的学习重点不是孤立记忆概念，而是把「概念-例子-练习-反馈」连成一条闭环。本节建议先用 15 分钟建立知识框架，再用 30 分钟完成实践验证。

## 易错提醒
1. {knowledge['pitfalls'][0]}
2. {knowledge['pitfalls'][1]}
3. {knowledge['pitfalls'][2]}

## 推荐学习任务
{knowledge['practice']}
"""

    if resource_type == "知识点思维导图":
        return f"""# {resource['title']}

- {knowledge['topic']}
  - 核心概念
    - {knowledge['core']}
  - 常见误区
    - {knowledge['pitfalls'][0]}
    - {knowledge['pitfalls'][1]}
    - {knowledge['pitfalls'][2]}
  - 实践任务
    - {knowledge['practice']}
  - 自测反馈
    - 完成练习题
    - 记录错因
    - 回填学习画像
"""

    if resource_type == "不同类型练习题目":
        return f"""# {resource['title']}

## 概念判断题
1. 学习 {knowledge['topic']} 时，只要背下定义就能完成实践任务。  
   答案提示：错误。需要通过案例验证概念。
2. 常见误区「{knowledge['pitfalls'][0]}」可以通过实践记录及时发现。  
   答案提示：正确。
3. 学习路径应根据测试反馈动态调整。  
   答案提示：正确。

## 应用题
1. 请用自己的话解释：{knowledge['core']}。
2. 请列出你在学习 {knowledge['topic']} 时最可能出现的两个错误，并写出修正方法。

## 实践题
完成任务：{knowledge['practice']}。提交内容包括过程记录、关键证据或作品、遇到的问题和复盘。
"""

    if resource_type == "拓展阅读材料":
        return f"""# {resource['title']}

## 必读材料
- 课程章节：{knowledge['chapter']}
- 主题关键词：{knowledge['topic']}
- 核心内容：{knowledge['core']}

## 阅读顺序
1. 先阅读课程讲义中的基础定义。
2. 再阅读一个完整案例，观察知识点如何落地。
3. 最后对照常见误区进行查漏补缺。

## 阅读记录模板
- 我已经理解的内容：
- 我还不确定的问题：
- 我准备验证的小实验：
"""

    if resource_type == "错题诊断与学习反馈报告":
        return f"""# {resource['title']}

## 诊断结论
当前最需要优先修复的问题是：{knowledge['pitfalls'][0]}。

## 可能错因
1. 对 {knowledge['topic']} 的核心概念理解停留在记忆层面，缺少案例验证。
2. 学习时没有把「{knowledge['core']}」拆成可检查的小目标。
3. 做题或实操后没有记录错因，导致同类问题重复出现。

## 补救建议
1. 先复读课程讲解文档，标出 3 个仍不确定的概念。
2. 完成分层练习题中的概念判断题，再做应用题。
3. 最后完成实践任务：{knowledge['practice']}。

## 下次复盘模板
- 我本次犯错的知识点：
- 触发错误的题目或场景：
- 正确解法的关键步骤：
- 下次遇到同类问题时我要先检查：
"""

    if resource_type == "学科实践应用任务":
        return _build_practice_resource_content(resource, knowledge, intent)

    return f"""# {resource['title']}

暂无正文内容。
"""


def _build_learning_path(knowledge: dict, intent: str):
    return [
        f"第 1 步：快速定位你当前的问题属于「{intent}」，先阅读核心概念卡片。",
        f"第 2 步：对照「{knowledge['chapter']}」补齐 {knowledge['core']}。",
        f"第 3 步：完成学科实践应用任务：{knowledge['practice']}。",
        "第 4 步：用练习题自测，把错题回填到画像中的易错点。",
        "第 5 步：根据自测结果重新生成下一轮资源和路径。",
    ]


def _score_evaluation(text: str, confidence: int, knowledge: dict):
    content = text.strip().lower()
    length_score = min(25, len(content) // 8)
    keyword_hits = sum(1 for word in knowledge["keywords"] if word in content)
    keyword_score = min(20, keyword_hits * 5)
    confidence_score = max(0, min(25, int(confidence or 0) // 4))
    reflection_score = 0
    if any(word in text for word in ["因为", "原因", "错因", "理解", "步骤", "复盘"]):
        reflection_score += 15
    if any(word in text for word in ["不会", "不懂", "总是错", "混淆", "记不住"]):
        reflection_score -= 8

    score = max(35, min(96, 35 + length_score + keyword_score + confidence_score + reflection_score))
    if score >= 85:
        level = "掌握较好"
    elif score >= 70:
        level = "基本掌握"
    elif score >= 55:
        level = "需要巩固"
    else:
        level = "重点补救"
    return score, level


def _level_from_score(score: int):
    if score >= 85:
        return "掌握较好"
    if score >= 70:
        return "基本掌握"
    if score >= 55:
        return "需要巩固"
    return "重点补救"


def _build_diagnosis_content(knowledge: dict, wrong_notes: str, score: int, level: str, weak_points: list, suggestions: list):
    weak_lines = "\n".join([f"- {item}" for item in weak_points])
    suggestion_lines = "\n".join([f"{index}. {item}" for index, item in enumerate(suggestions, 1)])
    return f"""# {knowledge['topic']} 错题诊断与学习反馈报告

## 诊断得分
{score} 分，掌握等级：{level}

## 学生提交内容摘要
{wrong_notes or "学生暂未填写详细错题描述，系统根据主题和自信度给出基础诊断。"}

## 主要薄弱点
{weak_lines}

## 补救建议
{suggestion_lines}

## 下一轮学习任务
完成「{knowledge['practice']}」，并记录至少 2 条错因复盘。
"""


def _collect_learning_signal(username: str):
    user = db_service.get_user_by_username(username)
    plans = db_service.get_plans_by_username(username)
    history = db_service.get_evaluation_records(username)
    resources = db_service.get_all_resources()
    task_status = {"completed": 0, "active": 0, "pending": 0}
    plan_titles = []
    task_text = []

    for plan in plans:
        plan_titles.append(plan.get("title", ""))
        for task in plan.get("tasks", []):
            status = task.get("status", "pending")
            if status in task_status:
                task_status[status] += 1
            task_text.extend([task.get("title", ""), task.get("desc", "")])

    total_tasks = sum(task_status.values())
    completion_rate = round(task_status["completed"] / total_tasks * 100) if total_tasks else 0
    recent_history = history[:3]
    recent_avg_score = round(sum(item.get("score", 0) for item in recent_history) / len(recent_history)) if recent_history else None
    resource_titles = [
        item.get("title", "")
        for item in resources
        if item.get("uploader") in ["资源生成 Agent", "学习评价 Agent"]
    ][:12]

    source_text = " ".join(
        ([user.tags if user else ""] + plan_titles + task_text + resource_titles + [
            item.get("topic", "") + " " + item.get("level", "") + " " + " ".join(item.get("weak_points", []))
            for item in recent_history
        ])
    )
    return {
        "user": user,
        "plans": plans,
        "history": history,
        "task_status": task_status,
        "completion_rate": completion_rate,
        "recent_avg_score": recent_avg_score,
        "source_text": source_text,
    }


def handle_auto_evaluation(username: str):
    signal = _collect_learning_signal(username)
    user = signal["user"]
    knowledge = _infer_knowledge(signal["source_text"] or (user.tags if user else "人工智能导论"))
    hours = user.hours if user else 0
    task_status = signal["task_status"]
    completion_rate = signal["completion_rate"]
    recent_avg_score = signal["recent_avg_score"]
    active_fix_plan = any("错题修复" in plan.get("title", "") for plan in signal["plans"])

    score = 62 + min(12, hours // 4) + round(completion_rate * 0.18)
    if recent_avg_score is not None:
        score = round(score * 0.45 + recent_avg_score * 0.55)
    if active_fix_plan:
        score -= 8
    if task_status["pending"] > task_status["completed"]:
        score -= 6
    score = max(42, min(96, score))
    level = _level_from_score(score)

    history_weak_points = []
    for item in signal["history"]:
        if item.get("topic") == knowledge["topic"]:
            history_weak_points = [
                point for point in item.get("weak_points", [])
                if point in knowledge["pitfalls"] or any(keyword.lower() in point.lower() for keyword in knowledge["keywords"])
            ][:2]
            break
    weak_points = list(dict.fromkeys(history_weak_points + [
        knowledge["pitfalls"][0],
        "学习路线中仍有较多待完成任务" if task_status["pending"] else "需要持续复盘已完成任务",
        "平台记录显示需要继续补齐实践验证",
    ]))[:4]
    suggestions = [
        f"优先完成当前规划中的 active 任务，再处理 {task_status['pending']} 个待完成任务。",
        f"围绕「{knowledge['chapter']}」复习 {knowledge['core']}。",
        "对最近一次错题诊断报告做二次复盘，比较薄弱点是否减少。",
        f"完成实践任务：{knowledge['practice']}。",
    ]
    auto_notes = (
        f"系统基于平台数据自动诊断：累计学习 {hours} 小时，"
        f"任务完成率 {completion_rate}%，"
        f"待完成任务 {task_status['pending']} 个，"
        f"近三次评价均分 {recent_avg_score if recent_avg_score is not None else '暂无'}。"
    )
    diagnosis_resource = {
        "type": "错题诊断与学习反馈报告",
        "title": f"{knowledge['topic']} 平台自动诊断报告",
        "summary": f"{level}：由平台行为数据自动生成，任务完成率 {completion_rate}%。",
        "source": f"{knowledge['chapter']} / 平台学习行为数据",
        "agent_notes": "由学习评价 Agent 基于画像、规划、资源和历史评价自动生成，适合做阶段性学习反馈。",
        "content": _build_diagnosis_content(knowledge, auto_notes, score, level, weak_points, suggestions),
    }
    saved_resources = db_service.insert_generated_resources([diagnosis_resource], uploader="学习评价 Agent") if username else []
    generated_resource_id = saved_resources[0]["id"] if saved_resources else ""
    updated_user = db_service.update_user_learning_profile(
        username,
        [knowledge["topic"], "平台自动诊断", level],
        hours_delta=0,
    ) if username else None
    remedial_plan = None
    if username and score < 82:
        remedial_plan = db_service.save_generated_plan(
            username=username,
            title=f"{knowledge['topic']} · 自动补弱路线",
            path_steps=[
                f"第 1 步：查看平台自动诊断报告，确认当前等级「{level}」。",
                f"第 2 步：优先完成 {task_status['pending']} 个待完成任务。",
                f"第 3 步：复习「{knowledge['chapter']}」核心知识。",
                f"第 4 步：完成实践任务：{knowledge['practice']}。",
                "第 5 步：再次运行自动诊断，观察任务完成率和诊断分变化。",
            ],
            resources=[diagnosis_resource],
        )

    record = db_service.save_evaluation_record(
        username=username,
        topic=knowledge["topic"],
        score=score,
        level=level,
        weak_points=weak_points,
        suggestions=suggestions,
        wrong_notes=auto_notes,
        answers={
            "mode": "auto",
            "hours": hours,
            "task_status": task_status,
            "completion_rate": completion_rate,
            "recent_avg_score": recent_avg_score,
        },
        generated_resource_id=generated_resource_id,
    ) if username else None

    return {
        "record": record,
        "score": score,
        "level": level,
        "weak_points": weak_points,
        "suggestions": suggestions,
        "generated_resource": saved_resources[0] if saved_resources else diagnosis_resource,
        "remedial_plan": remedial_plan,
        "profile": {
            "tags": updated_user["tags"] if updated_user else [knowledge["topic"], "平台自动诊断", level],
            "hours": updated_user["hours"] if updated_user else 0,
        },
        "auto_summary": auto_notes,
        "data_sources": ["学习画像", "规划任务状态", "历史评价记录", "Agent 生成资源"],
    }


def handle_learning_evaluation(username: str, topic: str, wrong_notes: str, answer_summary: str, confidence: int = 60):
    merged_text = f"{topic}\n{wrong_notes}\n{answer_summary}"
    knowledge = _infer_knowledge(merged_text)
    score, level = _score_evaluation(merged_text, confidence, knowledge)
    weak_points = [
        knowledge["pitfalls"][0],
        knowledge["pitfalls"][1],
        "缺少实践验证和错因复盘" if score < 75 else "需要继续保持复盘记录",
    ]
    suggestions = [
        f"回看「{knowledge['chapter']}」中关于 {knowledge['core']} 的内容。",
        "先完成分层练习题中的概念判断题，再做应用题。",
        f"完成实践任务：{knowledge['practice']}。",
        "把本次错因写入学习画像，下一轮路径优先补弱。",
    ]
    diagnosis_resource = {
        "type": "错题诊断与学习反馈报告",
        "title": f"{knowledge['topic']} 错题诊断报告",
        "summary": f"{level}：识别出 {len(weak_points)} 个薄弱点，并生成补救路线。",
        "source": f"{knowledge['chapter']} / 学习评价 Agent",
        "agent_notes": "由学习评价 Agent 根据学生自测与错题描述生成，建议管理员核对诊断建议是否贴合课程要求。",
        "content": _build_diagnosis_content(knowledge, wrong_notes or answer_summary, score, level, weak_points, suggestions),
    }
    saved_resources = db_service.insert_generated_resources([diagnosis_resource], uploader="学习评价 Agent") if username else []
    generated_resource_id = saved_resources[0]["id"] if saved_resources else ""
    updated_user = db_service.update_user_learning_profile(
        username,
        [knowledge["topic"], "错题诊断", level],
        hours_delta=1 if score < 75 else 0,
    ) if username else None
    remedial_plan = None
    if username and score < 80:
        remedial_plan = db_service.save_generated_plan(
            username=username,
            title=f"{knowledge['topic']} · 错题修复路线",
            path_steps=[
                f"第 1 步：复盘本次错因，重点标记「{weak_points[0]}」。",
                f"第 2 步：重读「{knowledge['chapter']}」核心概念。",
                "第 3 步：完成错题诊断报告中的补救建议。",
                f"第 4 步：完成实践任务：{knowledge['practice']}。",
                "第 5 步：重新提交一次学习评价，比较得分变化。",
            ],
            resources=[diagnosis_resource],
        )

    record = db_service.save_evaluation_record(
        username=username,
        topic=knowledge["topic"],
        score=score,
        level=level,
        weak_points=weak_points,
        suggestions=suggestions,
        wrong_notes=wrong_notes,
        answers={
            "topic": topic,
            "wrong_notes": wrong_notes,
            "answer_summary": answer_summary,
            "confidence": confidence,
        },
        generated_resource_id=generated_resource_id,
    ) if username else None

    return {
        "record": record,
        "score": score,
        "level": level,
        "weak_points": weak_points,
        "suggestions": suggestions,
        "generated_resource": saved_resources[0] if saved_resources else diagnosis_resource,
        "remedial_plan": remedial_plan,
        "profile": {
            "tags": updated_user["tags"] if updated_user else [knowledge["topic"], "错题诊断", level],
            "hours": updated_user["hours"] if updated_user else 0,
        },
    }


def _build_llm_guidance(message: str, knowledge: dict, intent: str, profile: dict):
    messages = [
        {
            "role": "system",
            "content": (
                "你是高校个性化学习系统中的教学辅导 Agent。"
                "请基于给定画像和课程主题，输出简洁、可执行、适合学生阅读的学习建议。"
                "不要虚构资料来源，不要替代资源审核流程。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"学生原始问题：{message}\n"
                f"课程主题：{knowledge['topic']}\n"
                f"学习意图：{intent}\n"
                f"核心内容：{knowledge['core']}\n"
                f"画像维度：{profile['dimensions']}\n"
                "请给出 3 条学习建议和 1 个当天可完成的小任务。"
            ),
        },
    ]
    result = llm_provider.chat(messages, temperature=0.45, max_tokens=800)
    return result.get("content", "").strip() if result.get("ok") else ""


def _format_reply(knowledge: dict, intent: str, profile: dict, resources: list, path: list, llm_guidance: str = ""):
    pitfall_lines = "\n".join([f"- {item}" for item in knowledge["pitfalls"]])
    resource_lines = "\n".join(
        [f"{index}. **{item['type']}**：{item['title']}。{item['summary']}" for index, item in enumerate(resources, 1)]
    )
    path_lines = "\n".join([f"{index}. {step}" for index, step in enumerate(path, 1)])
    safety_source = (
        "本次回答由系统课程知识库和已配置的大模型共同生成，生成资源仍需管理员审核后开放。"
        if llm_guidance
        else "本次回答只基于系统内置课程知识库和你的提问生成，没有引用不明来源内容。"
    )

    return f"""### 多智能体协作结果

**画像分析 Agent**
- 当前主题：{knowledge['topic']}
- 学习意图：{intent}
- 认知风格：{profile['dimensions']['认知风格']}
- 重点短板：{profile['dimensions']['知识短板']}

**知识检索 Agent**
- 命中知识源：{knowledge['chapter']}
- 核心内容：{knowledge['core']}
- 常见误区：
{pitfall_lines}

**资源生成 Agent**
{resource_lines}

**实践应用 Agent**
{_build_practice_preview(knowledge)}

**路径规划 Agent**
{path_lines}

**大模型教学 Agent**
{llm_guidance or "当前未配置外部大模型，系统先使用本地课程知识库生成可演示结果；配置 API Key 后这里会自动替换为真实模型建议。"}

**安全校验 Agent**
- {safety_source}
- 建议把生成资源先进入资源库审核，再开放给学生端使用。

**系统联动**
- 6 类个性化资源已提交到管理后台的资源审核队列。
- 个性化学习路线已同步到【规划】页面，可继续手动调整任务顺序和完成状态。
"""


def handle_learning_chat(username: str, message: str, history=None):
    user = db_service.get_user_by_username(username) if username else None
    knowledge = _infer_knowledge(message)
    intent = _infer_intent(message)
    profile = _build_profile(user, message, knowledge, intent)
    resources = _build_resources(knowledge, intent)
    path = _build_learning_path(knowledge, intent)
    llm_guidance = _build_llm_guidance(message, knowledge, intent, profile)
    updated_user = db_service.update_user_learning_profile(username, profile["tags"], hours_delta=1) if username else None
    saved_resources = db_service.insert_generated_resources(resources) if username else []
    saved_plan = db_service.save_generated_plan(
        username=username,
        title=f"{knowledge['topic']} · {intent}路线",
        path_steps=path,
        resources=resources,
    ) if username else None

    return {
        "reply": _format_reply(knowledge, intent, profile, resources, path, llm_guidance),
        "agents": ["画像分析 Agent", "知识检索 Agent", "资源生成 Agent", "实践应用 Agent", "路径规划 Agent", "大模型教学 Agent", "安全校验 Agent"],
        "llm_enabled": llm_provider.is_enabled(),
        "profile": {
            "dimensions": profile["dimensions"],
            "radar": profile["radar"],
            "tags": updated_user["tags"] if updated_user else profile["tags"],
            "hours": updated_user["hours"] if updated_user else 0,
        },
        "resources": resources,
        "path": path,
        "saved_resources": saved_resources,
        "saved_plan": saved_plan,
    }
