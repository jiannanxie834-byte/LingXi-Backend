import datetime
import json
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.schemas import (
    ChatMessage,
    ChatSession,
    EvaluationRecord,
    Feedback,
    LearningPlan,
    Resource,
    ResourceType,
    TodoList,
    User,
)
from app.services.data_services import content_guard_service
from app.services.data_services.knowledge_seed_service import seed_initial_course_knowledge_base


DEMO_USERNAMES = ["student", "demo_basic"]
DEMO_SESSION_IDS = ["CHAT_DEMO_SUPERVISED", "CHAT_DEMO_MULTIMODAL"]
DEMO_RESOURCE_IDS = [
    "DEMO_RES_APPROVED_DOC",
    "DEMO_RES_APPROVED_MINDMAP",
    "DEMO_RES_APPROVED_QUIZ",
    "DEMO_RES_PENDING_MULTIMODAL",
    "DEMO_RES_PENDING_PRACTICE",
    "DEMO_RES_DIAG_SUPERVISED",
]
DEMO_FEEDBACK_IDS = ["DEMO_FB_001", "DEMO_FB_002", "DEMO_FB_003"]
DEMO_RESOURCE_TYPES = ["课程案例数据集", "实验报告模板", "可解释性案例卡"]


def _now(offset_minutes: int = 0) -> datetime.datetime:
    return datetime.datetime.now() + datetime.timedelta(minutes=offset_minutes)


def _now_str(offset_minutes: int = 0) -> str:
    return _now(offset_minutes).strftime("%Y-%m-%d %H:%M:%S")


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _reviewed_notes(title: str, resource_type: str, summary: str, content: str, source: str, base_note: str) -> str:
    review = content_guard_service.review_resource_content(
        title=title,
        resource_type=resource_type,
        summary=summary,
        content=content,
        source=source,
        reviewer="演示数据内容安全 Agent",
    )
    return content_guard_service.attach_review_note(base_note, review)


def _upsert_user(db: Session, data: Dict):
    row = db.query(User).filter(User.username == data["username"]).first()
    if not row:
        row = User(username=data["username"])
        db.add(row)

    for key, value in data.items():
        setattr(row, key, value)


def _upsert_resource(db: Session, data: Dict):
    row = db.query(Resource).filter(Resource.id == data["id"]).first()
    if not row:
        row = Resource(id=data["id"])
        db.add(row)

    for key, value in data.items():
        setattr(row, key, value)


def _upsert_resource_type(db: Session, name: str, status: str):
    row = db.query(ResourceType).filter(ResourceType.name == name).first()
    if not row:
        row = ResourceType(name=name)
        db.add(row)
    row.status = status


def _upsert_feedback(db: Session, data: Dict):
    row = db.query(Feedback).filter(Feedback.id == data["id"]).first()
    if not row:
        row = Feedback(id=data["id"])
        db.add(row)

    for key, value in data.items():
        setattr(row, key, value)


def _upsert_learning_plan(db: Session, username: str, plans: List[Dict]):
    row = db.query(LearningPlan).filter(LearningPlan.username == username).first()
    if not row:
        row = LearningPlan(username=username)
        db.add(row)
    row.plans_json = _json(plans)
    row.updated_at = _now_str()


def _upsert_todos(db: Session, username: str, todos: List[Dict]):
    row = db.query(TodoList).filter(TodoList.username == username).first()
    if not row:
        row = TodoList(username=username)
        db.add(row)
    row.todos_json = _json(todos)
    row.updated_at = _now_str()


def _add_chat_message(db: Session, message_id: str, session_id: str, username: str, role: str, content: str, offset_minutes: int):
    row = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    if not row:
        row = ChatMessage(id=message_id)
        db.add(row)
    row.session_id = session_id
    row.username = username
    row.role = role
    row.content = content
    row.created_at = _now(offset_minutes)


def _upsert_chat_session(db: Session, session_id: str, title: str, username: str, offset_minutes: int):
    row = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not row:
        row = ChatSession(id=session_id)
        db.add(row)
    row.username = username
    row.title = title
    row.created_at = _now(offset_minutes)
    row.updated_at = _now(offset_minutes + 5)


def _upsert_evaluation_record(db: Session, data: Dict):
    row = db.query(EvaluationRecord).filter(EvaluationRecord.id == data["id"]).first()
    if not row:
        row = EvaluationRecord(id=data["id"])
        db.add(row)

    for key, value in data.items():
        if key in {"weak_points", "suggestions", "answers_json"} and not isinstance(value, str):
            value = _json(value)
        setattr(row, key, value)


def _reset_demo_scope(db: Session):
    db.query(ChatMessage).filter(ChatMessage.username.in_(DEMO_USERNAMES)).delete(synchronize_session=False)
    db.query(ChatSession).filter(ChatSession.username.in_(DEMO_USERNAMES)).delete(synchronize_session=False)
    db.query(EvaluationRecord).filter(EvaluationRecord.username.in_(DEMO_USERNAMES)).delete(synchronize_session=False)
    db.query(LearningPlan).filter(LearningPlan.username.in_(DEMO_USERNAMES)).delete(synchronize_session=False)
    db.query(TodoList).filter(TodoList.username.in_(DEMO_USERNAMES)).delete(synchronize_session=False)
    db.query(ChatMessage).filter(ChatMessage.username.like("test_%")).delete(synchronize_session=False)
    db.query(ChatSession).filter(ChatSession.username.like("test_%")).delete(synchronize_session=False)
    db.query(EvaluationRecord).filter(EvaluationRecord.username.like("test_%")).delete(synchronize_session=False)
    db.query(LearningPlan).filter(LearningPlan.username.like("test_%")).delete(synchronize_session=False)
    db.query(TodoList).filter(TodoList.username.like("test_%")).delete(synchronize_session=False)
    db.query(User).filter(User.username.like("test_%")).delete(synchronize_session=False)

    # Seed 脚本用于恢复稳定演示底库：保留课程知识库资源，重建 DEMO_* 资源，清除临时生成资源。
    db.query(Resource).filter(
        ~Resource.id.like("KB-AI-INTRO-%"),
        ~Resource.id.in_(DEMO_RESOURCE_IDS),
    ).delete(synchronize_session=False)
    db.query(Resource).filter(Resource.id.in_(DEMO_RESOURCE_IDS)).delete(synchronize_session=False)
    db.query(Feedback).filter(~Feedback.id.in_(DEMO_FEEDBACK_IDS)).delete(synchronize_session=False)
    db.query(Feedback).filter(Feedback.id.in_(DEMO_FEEDBACK_IDS)).delete(synchronize_session=False)
    db.query(ResourceType).filter(~ResourceType.name.in_(DEMO_RESOURCE_TYPES)).delete(synchronize_session=False)
    db.query(ResourceType).filter(ResourceType.name.in_(DEMO_RESOURCE_TYPES)).delete(synchronize_session=False)


def _seed_users(db: Session):
    _upsert_user(db, {
        "username": "admin",
        "nickname": "管理员",
        "password": "123456",
        "role": "admin",
        "avatar": "",
        "bio": "负责课程知识库、资源审核、反馈处理与系统治理。",
        "hours": 999,
        "tags": "系统管理,内容审核,资源治理,防幻觉",
    })
    _upsert_user(db, {
        "username": "student",
        "nickname": "林溪同学",
        "password": "123456",
        "role": "student",
        "avatar": "",
        "bio": "人工智能导论课程学习者，当前重点补强监督学习、模型评估和主题资源包表达。",
        "hours": 42,
        "tags": "人工智能导论,监督学习与模型评估,混淆矩阵,大语言模型,RAG,主题学习包,实践驱动",
    })
    _upsert_user(db, {
        "username": "demo_basic",
        "nickname": "基础薄弱学生",
        "password": "123456",
        "role": "student",
        "avatar": "",
        "bio": "刚开始学习人工智能导论，适合演示新手画像和基础路径推荐。",
        "hours": 6,
        "tags": "人工智能概述,基础薄弱,概念入门",
    })


def _seed_resources(db: Session):
    resources = [
        {
            "id": "DEMO_RES_APPROVED_DOC",
            "title": "监督学习与模型评估重点讲解",
            "type": "专业课程讲解文档",
            "status": "已通过",
            "uploader": "资源生成 Agent",
            "summary": "面向监督学习薄弱学生，解释分类、回归、混淆矩阵和指标取舍。",
            "source": "人工智能导论初始知识库 / 第 4 章 监督学习与模型评估",
            "content": """# 监督学习与模型评估重点讲解

## 学习目标
- 区分分类任务和回归任务。
- 理解混淆矩阵中 TP、FP、FN、TN 的含义。
- 能结合学习预警场景解释准确率、精确率、召回率和 F1。

## 核心解释
监督学习使用带标签样本训练模型。分类任务输出离散类别，回归任务输出连续数值。模型评估不能只看准确率，尤其在类别不均衡时，应结合召回率和业务代价判断模型是否可用。

## 例子
学习预警系统更害怕漏掉真正有风险的学生，所以通常更关注召回率。""",
        },
        {
            "id": "DEMO_RES_APPROVED_MINDMAP",
            "title": "人工智能导论知识结构图",
            "type": "知识点思维导图",
            "status": "已通过",
            "uploader": "课程知识库种子",
            "summary": "用 Mermaid 图展示人工智能导论 8 个章节之间的关系。",
            "source": "人工智能导论初始知识库 / 课程大纲",
            "content": """# 人工智能导论知识结构图

```mermaid
flowchart TD
    A[人工智能导论] --> B[搜索与问题求解]
    A --> C[机器学习基础]
    C --> D[监督学习与评估]
    C --> E[神经网络与深度学习]
    A --> F[NLP 与大语言模型]
    F --> G[RAG 与智能体]
    A --> H[AI 安全与防幻觉]
```

## 使用方式
先看整体结构，再根据个人画像进入对应章节。""",
        },
        {
            "id": "DEMO_RES_APPROVED_QUIZ",
            "title": "混淆矩阵分层练习与题解",
            "type": "不同类型练习题目",
            "status": "已通过",
            "uploader": "资源生成 Agent",
            "summary": "包含概念判断、指标计算和场景解释题。",
            "source": "人工智能导论初始知识库 / 第 4 章 监督学习与模型评估",
            "content": """# 混淆矩阵分层练习与题解

## 概念题
类别不均衡时只看准确率可能会误判模型效果。判断：正确。

## 计算题
TP=36，FP=12，FN=9，TN=143。

1. 准确率 = (36 + 143) / 200 = 0.895
2. 精确率 = 36 / (36 + 12) = 0.75
3. 召回率 = 36 / (36 + 9) = 0.80

## 场景解释
如果任务是学习风险预警，漏掉风险学生的代价较高，应优先关注召回率。""",
        },
        {
            "id": "DEMO_RES_PENDING_MULTIMODAL",
            "title": "监督学习展示讲解文档",
            "type": "专业课程讲解文档",
            "status": "待审核",
            "uploader": "资源生成 Agent",
            "summary": "包含文字讲解、流程图、代码注释和分步题解，用于演示计算机课程资源审核。",
            "source": "人工智能导论初始知识库 / 第 4 章 监督学习与模型评估",
            "content": """# 监督学习展示讲解文档

## 文字讲解
监督学习的核心是从带标签样本中学习输入到输出的映射。分类任务关注类别，回归任务关注连续数值。

## Mermaid 流程图
```mermaid
flowchart TD
    A[带标签数据] --> B[训练模型]
    B --> C[验证集调参]
    C --> D[测试集评估]
    D --> E[混淆矩阵]
    E --> F[解释指标取舍]
```

## 代码注释案例
```python
# y_true 是真实标签，y_pred 是模型预测结果
matrix = confusion_matrix(y_true, y_pred)
precision = tp / (tp + fp)  # 预测为正的样本中有多少是真的正类
recall = tp / (tp + fn)     # 真实正类中有多少被找出来
```

## 分步题解
1. 先画混淆矩阵。
2. 再定位 TP、FP、FN、TN。
3. 根据场景判断更重视精确率还是召回率。

## 课堂展示页纲
1. 监督学习任务定义。
2. 分类与回归区别。
3. 混淆矩阵。
4. 指标计算。
5. 学习预警场景讨论。
""",
        },
        {
            "id": "DEMO_RES_PENDING_PRACTICE",
            "title": "学习风险预警模型实践任务",
            "type": "学科实践应用任务",
            "status": "待审核",
            "uploader": "资源生成 Agent",
            "summary": "要求学生设计一个监督学习任务，用指标解释模型是否适合学习预警。",
            "source": "人工智能导论初始知识库 / 实践项目任务书",
            "content": """# 学习风险预警模型实践任务

## 任务目标
设计一个二分类学习风险预警任务，解释数据、标签、特征和评价指标。

## 产出要求
- 标签定义说明。
- 至少 5 个候选特征。
- 混淆矩阵和指标解释。
- 模型上线前的风险和伦理说明。

## 评分标准
重点考查问题建模、指标解释、隐私意识和复盘能力。""",
        },
        {
            "id": "DEMO_RES_DIAG_SUPERVISED",
            "title": "监督学习与模型评估错题诊断报告",
            "type": "错题诊断与学习反馈报告",
            "status": "待审核",
            "uploader": "学习评价 Agent",
            "summary": "识别学生在混淆矩阵、精确率、召回率上的薄弱点，并生成补救建议。",
            "source": "人工智能导论初始知识库 / 学习评价 Agent",
            "content": """# 监督学习与模型评估错题诊断报告

## 诊断结论
当前学生能够理解分类任务，但在混淆矩阵四个格子的含义、精确率与召回率的场景取舍上仍不稳定。

## 薄弱点
- 混淆 TP、FP、FN、TN。
- 类别不均衡时仍优先看准确率。
- 没有结合学习预警场景解释指标。

## 补救建议
1. 重新画混淆矩阵。
2. 完成分层练习中的计算题。
3. 用学习风险预警场景解释为什么召回率重要。
4. 完成实践任务并提交一次复盘。""",
        },
    ]

    for item in resources:
        item["time"] = _now_str()
        item["agent_notes"] = _reviewed_notes(
            title=item["title"],
            resource_type=item["type"],
            summary=item["summary"],
            content=item["content"],
            source=item["source"],
            base_note="演示基准数据：用于展示资源生成、内容安全自检、管理员审核和学生资源库发布链路。",
        )
        _upsert_resource(db, item)


def _seed_resource_types(db: Session):
    _upsert_resource_type(db, "课程案例数据集", "待审核")
    _upsert_resource_type(db, "实验报告模板", "已通过")
    _upsert_resource_type(db, "可解释性案例卡", "待审核")


def _seed_feedbacks(db: Session):
    feedbacks = [
        {
            "id": "DEMO_FB_001",
            "username": "student",
            "content": "资源详情页里的 PPT 导出很好用，希望流程图导出后也能保留为可编辑形态。",
            "status": "待处理",
            "date": _now_str(-80),
        },
        {
            "id": "DEMO_FB_002",
            "username": "demo_basic",
            "content": "我刚开始学 AI，希望首页能提示先看哪一章。",
            "status": "待处理",
            "date": _now_str(-50),
        },
        {
            "id": "DEMO_FB_003",
            "username": "student",
            "content": "错题诊断报告能自动同步到规划页，这个功能已经满足复习需要。",
            "status": "已处理",
            "date": _now_str(-20),
        },
    ]
    for item in feedbacks:
        _upsert_feedback(db, item)


def _student_plans() -> List[Dict]:
    return [
        {
            "id": "route_demo_supervised",
            "title": "监督学习与模型评估 · 个性化补弱路线",
            "isCollapsed": False,
            "isAiGenerated": True,
            "tasks": [
                {
                    "id": "task_supervised_1",
                    "title": "复盘混淆矩阵四格含义",
                    "desc": "重新画出 TP、FP、FN、TN，并用自己的话解释每一格。",
                    "status": "completed",
                    "isCustom": False,
                    "resources": ["监督学习与模型评估重点讲解", "混淆矩阵分层练习与题解"],
                },
                {
                    "id": "task_supervised_2",
                    "title": "完成指标计算练习",
                    "desc": "完成准确率、精确率、召回率和 F1 的计算题。",
                    "status": "active",
                    "isCustom": False,
                    "resources": ["混淆矩阵分层练习与题解"],
                },
                {
                    "id": "task_supervised_3",
                    "title": "解释学习预警场景指标取舍",
                    "desc": "说明为什么风险预警更关注召回率，并写出可能的误报代价。",
                    "status": "pending",
                    "isCustom": False,
                    "resources": ["学习风险预警模型实践任务"],
                },
                {
                    "id": "task_supervised_4",
                    "title": "提交一次错题复盘",
                    "desc": "把仍然混淆的指标写入评价页，触发诊断报告。",
                    "status": "pending",
                    "isCustom": True,
                    "resources": ["监督学习与模型评估错题诊断报告"],
                },
            ],
        },
        {
            "id": "route_demo_multimodal",
            "title": "主题学习包 · 项目展示路线",
            "isCollapsed": False,
            "isAiGenerated": True,
            "tasks": [
                {
                    "id": "task_multi_1",
                    "title": "阅读多智能体协同章节",
                    "desc": "理解意图识别、画像建模、资源生成、内容安全、管理员审核之间的协作关系。",
                    "status": "completed",
                    "isCustom": False,
                    "resources": ["第 7 章 多模态资源生成与智能体协同"],
                },
                {
                    "id": "task_multi_2",
                    "title": "查看监督学习主题学习包",
                    "desc": "观察讲解文档、思维导图、练习题、阅读材料和实践任务是否形成完整资源组合。",
                    "status": "active",
                    "isCustom": False,
                    "resources": ["监督学习展示讲解文档"],
                },
                {
                    "id": "task_multi_3",
                    "title": "导出 PPT 用于课堂展示",
                    "desc": "在资源详情页点击导出 PPT，检查文件是否能正常打开。",
                    "status": "pending",
                    "isCustom": False,
                    "resources": ["监督学习展示讲解文档"],
                },
            ],
        },
    ]


def _basic_plans() -> List[Dict]:
    return [
        {
            "id": "route_demo_basic_intro",
            "title": "人工智能导论 · 入门学习路线",
            "isCollapsed": False,
            "isAiGenerated": True,
            "tasks": [
                {
                    "id": "task_basic_1",
                    "title": "建立 AI 基本概念",
                    "desc": "阅读第 1 章，区分人工智能、机器学习、深度学习和智能体。",
                    "status": "active",
                    "isCustom": False,
                    "resources": ["第 1 章 人工智能概述"],
                },
                {
                    "id": "task_basic_2",
                    "title": "查看课程知识结构图",
                    "desc": "先看课程整体结构，再选择下一章学习。",
                    "status": "pending",
                    "isCustom": False,
                    "resources": ["人工智能导论知识结构图"],
                },
            ],
        }
    ]


def _seed_plans_and_todos(db: Session):
    _upsert_learning_plan(db, "student", _student_plans())
    _upsert_learning_plan(db, "demo_basic", _basic_plans())
    _upsert_todos(db, "student", [
        {"id": "todo_demo_1", "content": "完成混淆矩阵分层练习第 2 题", "done": False},
        {"id": "todo_demo_2", "content": "把错题原因写入学习评价", "done": False},
        {"id": "todo_demo_3", "content": "审核通过后回到资源库查看主题学习包", "done": True},
        {"id": "todo_demo_4", "content": "导出一份监督学习 PPT 作为演示素材", "done": False},
    ])
    _upsert_todos(db, "demo_basic", [
        {"id": "todo_basic_1", "content": "阅读第 1 章人工智能概述", "done": False},
        {"id": "todo_basic_2", "content": "完成概念判断题 1-3", "done": False},
    ])


def _seed_chats(db: Session):
    _upsert_chat_session(db, "CHAT_DEMO_SUPERVISED", "监督学习复习路线", "student", -120)
    _add_chat_message(
        db,
        "CHAT_DEMO_SUPERVISED_M1",
        "CHAT_DEMO_SUPERVISED",
        "student",
        "user",
        "我监督学习里的混淆矩阵总是分不清，能不能帮我安排复习路线？",
        -119,
    )
    _add_chat_message(
        db,
        "CHAT_DEMO_SUPERVISED_M2",
        "CHAT_DEMO_SUPERVISED",
        "student",
        "ai",
        """可以。系统已经识别到你的薄弱点集中在“监督学习与模型评估”。

建议路线：

1. 先画出 TP、FP、FN、TN 四格。
2. 完成准确率、精确率、召回率计算题。
3. 用学习风险预警场景解释指标取舍。
4. 提交一次错题复盘，生成诊断报告。

我已经为你准备了配套资源：监督学习重点讲解、混淆矩阵练习题和学习风险预警实践任务。""",
        -118,
    )
    _add_chat_message(
        db,
        "CHAT_DEMO_SUPERVISED_M3",
        "CHAT_DEMO_SUPERVISED",
        "student",
        "user",
        "为什么学习预警更看重召回率？",
        -117,
    )
    _add_chat_message(
        db,
        "CHAT_DEMO_SUPERVISED_M4",
        "CHAT_DEMO_SUPERVISED",
        "student",
        "ai",
        "因为召回率衡量真实风险学生中有多少被系统找出来。学习预警场景中，漏掉真正需要帮助的学生代价更高，所以召回率通常比单纯准确率更关键。",
        -116,
    )

    _upsert_chat_session(db, "CHAT_DEMO_MULTIMODAL", "主题学习包生成", "student", -60)
    _add_chat_message(
        db,
        "CHAT_DEMO_MULTIMODAL_M1",
        "CHAT_DEMO_MULTIMODAL",
        "student",
        "user",
        "给监督学习整理一组适合演示的主题学习资源。",
        -59,
    )
    _add_chat_message(
        db,
        "CHAT_DEMO_MULTIMODAL_M2",
        "CHAT_DEMO_MULTIMODAL",
        "student",
        "ai",
        """已整理“监督学习主题学习包”，包含：

- 文字讲解
- Mermaid 流程图
- 代码注释案例
- 分步题解
- 实践任务

这些内容会以讲解文档、导图、练习题、阅读材料和实践任务组合展示，通过审核后会在学生端资源库形成主题学习包。""",
        -58,
    )


def _seed_evaluations(db: Session):
    records = [
        {
            "id": "DEMO_EVAL_001",
            "username": "student",
            "topic": "监督学习与模型评估",
            "score": 68,
            "level": "需要巩固",
            "weak_points": ["混淆 TP、FP、FN、TN", "类别不均衡时仍只看准确率", "缺少场景化指标解释"],
            "suggestions": ["重画混淆矩阵", "完成指标计算题", "用学习预警场景解释召回率"],
            "wrong_notes": "我知道准确率怎么算，但总分不清精确率和召回率。",
            "answers_json": {"confidence": 54, "mode": "manual"},
            "generated_resource_id": "DEMO_RES_DIAG_SUPERVISED",
            "created_at": _now(-720),
        },
        {
            "id": "DEMO_EVAL_002",
            "username": "student",
            "topic": "自然语言处理与大语言模型",
            "score": 78,
            "level": "基本掌握",
            "weak_points": ["RAG 各环节作用解释还不够完整", "提示词约束写得偏笼统"],
            "suggestions": ["画出 RAG 流程图", "补充检索来源和审核规则"],
            "wrong_notes": "能理解大模型问答，但对 RAG 的检索和生成边界还不够清楚。",
            "answers_json": {"confidence": 72, "mode": "manual"},
            "generated_resource_id": "",
            "created_at": _now(-360),
        },
        {
            "id": "DEMO_EVAL_003",
            "username": "student",
            "topic": "多模态学习资源生成",
            "score": 86,
            "level": "掌握较好",
            "weak_points": ["需要继续强化资源审核意识"],
            "suggestions": ["在每份学习包中标注来源", "保留管理员审核链路"],
            "wrong_notes": "已经能说明多模态不只是视频，还包括流程图、题解和 PPT。",
            "answers_json": {"confidence": 88, "mode": "auto"},
            "generated_resource_id": "DEMO_RES_PENDING_MULTIMODAL",
            "created_at": _now(-90),
        },
    ]
    for item in records:
        _upsert_evaluation_record(db, item)


def seed_demo_base_data(db: Session, reset_demo_scope: bool = True) -> Dict:
    try:
        if reset_demo_scope:
            _reset_demo_scope(db)

        seed_initial_course_knowledge_base(db)
        _seed_users(db)
        _seed_resources(db)
        _seed_resource_types(db)
        _seed_feedbacks(db)
        _seed_plans_and_todos(db)
        _seed_chats(db)
        _seed_evaluations(db)

        db.commit()
        return {
            "success": True,
            "users": len(DEMO_USERNAMES) + 1,
            "resources": len(DEMO_RESOURCE_IDS),
            "resource_types": len(DEMO_RESOURCE_TYPES),
            "feedbacks": len(DEMO_FEEDBACK_IDS),
            "chat_sessions": len(DEMO_SESSION_IDS),
            "evaluation_records": 3,
            "message": "演示基准数据已写入 MySQL。",
        }
    except Exception as exc:
        db.rollback()
        return {
            "success": False,
            "message": str(exc),
        }
