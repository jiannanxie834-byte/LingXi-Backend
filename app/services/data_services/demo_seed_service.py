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
from app.services.data_services import resource_artifact_type_service as artifact_types
from app.services.data_services.knowledge_seed_service import seed_initial_course_knowledge_base


DEMO_USERNAMES = ["student", "demo_basic"]
DEMO_SESSION_IDS = ["CHAT_DEMO_CNN_PROJECT", "CHAT_DEMO_TRANSFORMER"]
DEMO_RESOURCE_IDS = [
    "DEMO_DL_CNN_NOTE",
    "DEMO_DL_CNN_EXERCISE",
    "DEMO_DL_CNN_CODE_LAB",
    "DEMO_DL_CNN_VIDEO",
    "DEMO_DL_CNN_ANIMATION",
    "DEMO_DL_CNN_PROJECT",
    "DEMO_DL_DIAG_CNN_SIZE",
]
DEMO_FEEDBACK_IDS = ["DEMO_FB_DL_001", "DEMO_FB_DL_002"]
DEMO_RESOURCE_TYPES = artifact_types.all_public_types()


def _now(offset_minutes: int = 0) -> datetime.datetime:
    return datetime.datetime.now() + datetime.timedelta(minutes=offset_minutes)


def _now_str(offset_minutes: int = 0) -> str:
    return _now(offset_minutes).strftime("%Y-%m-%d %H:%M:%S")


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


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


def _upsert_feedback(db: Session, data: Dict):
    row = db.query(Feedback).filter(Feedback.id == data["id"]).first()
    if not row:
        row = Feedback(id=data["id"])
        db.add(row)
    for key, value in data.items():
        setattr(row, key, value)


def _upsert_evaluation_record(db: Session, data: Dict):
    row = db.query(EvaluationRecord).filter(EvaluationRecord.id == data["id"]).first()
    if not row:
        row = EvaluationRecord(id=data["id"])
        db.add(row)
    for key, value in data.items():
        setattr(row, key, value)


def _upsert_chat_session(db: Session, session_id: str, title: str, username: str, offset_minutes: int):
    row = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not row:
        row = ChatSession(id=session_id)
        db.add(row)
    row.username = username
    row.title = title
    row.last_topic = "卷积神经网络中的卷积操作" if "CNN" in title else "自注意力机制与 Transformer"
    row.state_json = _json({"last_topic": row.last_topic, "pending_action": "continue_learning_help"})
    row.created_at = _now(offset_minutes)
    row.updated_at = _now(offset_minutes + 4)


def _add_chat_message(db: Session, message_id: str, session_id: str, username: str, role: str, content: str, offset_minutes: int):
    row = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    if not row:
        row = ChatMessage(id=message_id)
        db.add(row)
    row.session_id = session_id
    row.username = username
    row.role = role
    row.content = content
    row.metadata_json = "{}"
    row.created_at = _now(offset_minutes)


def _reset_demo_scope(db: Session):
    db.query(ChatMessage).filter(ChatMessage.username.in_(DEMO_USERNAMES)).delete(synchronize_session=False)
    db.query(ChatSession).filter(ChatSession.username.in_(DEMO_USERNAMES)).delete(synchronize_session=False)
    db.query(EvaluationRecord).filter(EvaluationRecord.username.in_(DEMO_USERNAMES)).delete(synchronize_session=False)
    db.query(LearningPlan).filter(LearningPlan.username.in_(DEMO_USERNAMES)).delete(synchronize_session=False)
    db.query(TodoList).filter(TodoList.username.in_(DEMO_USERNAMES)).delete(synchronize_session=False)
    db.query(Resource).filter(Resource.id.in_(DEMO_RESOURCE_IDS)).delete(synchronize_session=False)
    db.query(Feedback).filter(Feedback.id.in_(DEMO_FEEDBACK_IDS)).delete(synchronize_session=False)
    db.query(ResourceType).filter(ResourceType.name.in_(DEMO_RESOURCE_TYPES)).delete(synchronize_session=False)


def _seed_users(db: Session):
    _upsert_user(db, {
        "username": "student",
        "nickname": "林溪同学",
        "password": "123456",
        "role": "student",
        "avatar": "",
        "bio": "目标两周完成 CNN 图像分类项目，偏好图解和代码。",
        "hours": 18,
        "tags": "CNN 卷积神经网络,反向传播,PyTorch 实战,深度学习课程项目",
    })
    _upsert_user(db, {
        "username": "demo_basic",
        "nickname": "演示学生",
        "password": "123456",
        "role": "student",
        "avatar": "",
        "bio": "深度学习入门阶段，正在补齐反向传播和卷积尺寸计算。",
        "hours": 6,
        "tags": "深度学习基础,反向传播,CNN 卷积神经网络",
    })


def _seed_resources(db: Session):
    resources = [
        {
            "id": "DEMO_DL_CNN_NOTE",
            "title": "卷积神经网络中的卷积操作 · 课程讲解文档",
            "type": artifact_types.COURSE_NOTE,
            "status": "已通过",
            "uploader": "资源生成 Agent",
            "summary": "解释 CNN 卷积核、stride、padding、通道数和特征图尺寸计算。",
            "source": "深度学习初始知识库 / 第 7 章 CNN",
            "content": "# CNN 卷积操作讲解\n\n## 学习目标\n理解卷积核滑动、参数共享、局部连接和输出尺寸公式。\n\n## 核心公式\n输出尺寸 = floor((输入尺寸 + 2*padding - kernel_size) / stride) + 1。\n\n## 易错点\n- 混淆 padding 和 stride。\n- 忽略输入通道数与输出通道数。\n- 只看卷积核大小，不检查 tensor shape。",
        },
        {
            "id": "DEMO_DL_CNN_EXERCISE",
            "title": "CNN 输出尺寸计算 · 练习题集",
            "type": artifact_types.EXERCISE_SET,
            "status": "待审核",
            "uploader": "资源生成 Agent",
            "summary": "包含选择题、判断题、计算题、代码补全题和实验分析题。",
            "source": "深度学习初始知识库 / 第 7 章 CNN",
            "content": "# CNN 输出尺寸计算练习题集\n\n## 计算题\n题：输入 32x32，kernel=3，stride=1，padding=1，输出尺寸是多少？\n\n答案：32x32。\n\n解析：floor((32 + 2*1 - 3)/1)+1 = 32。\n\n对应知识点：卷积输出尺寸。\n\n常见错误：忘记 padding 贡献了两侧像素。",
        },
        {
            "id": "DEMO_DL_CNN_CODE_LAB",
            "title": "CNN 图像分类 · PyTorch 实操案例",
            "type": artifact_types.CODE_LAB,
            "status": "待审核",
            "uploader": "资源生成 Agent",
            "summary": "给出 CNN 图像分类实验目标、环境依赖、训练流程、完整代码骨架和报告模板。",
            "source": "深度学习初始知识库 / 第 11 章 PyTorch 工程实践",
            "content": "# CNN 图像分类 PyTorch 实验\n\n## 实验目标\n完成一个最小 CNN 分类流程。\n\n## 环境依赖\nPython、PyTorch、torchvision。\n\n## 训练流程\nDataset -> DataLoader -> Model -> Loss -> Optimizer -> Train -> Validate。\n\n## 代码\n```python\nimport torch\nimport torch.nn as nn\nmodel = nn.Sequential(nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(16, 10))\n```\n\n## 运行方式\n记录输入 shape、loss 曲线和验证准确率。\n\n## 实验报告\n填写数据集、模型结构、训练参数、结果和错因分析。",
        },
        {
            "id": "DEMO_DL_CNN_VIDEO",
            "title": "CNN 公开课观看入口 · 外部公开视频推荐卡",
            "type": artifact_types.VIDEO_RECOMMENDATION,
            "status": "已通过",
            "uploader": "视频推荐 Agent",
            "summary": "推荐公开课程入口，并给出建议观看片段和版权说明。",
            "source": "深度学习教学资料目录",
            "content": "# CNN 公开视频推荐卡\n\n## 原始链接\n- CS231n: https://cs231n.github.io/\n- Dive into Deep Learning: https://zh.d2l.ai/\n\n## 推荐片段\n优先观看卷积层、池化层、图像分类实验相关章节。\n\n## 版权说明\n仅提供原始链接和学习建议，不复制、不下载、不重新分发视频内容。",
        },
        {
            "id": "DEMO_DL_CNN_ANIMATION",
            "title": "CNN 卷积滑窗 · 交互动画规格",
            "type": artifact_types.INTERACTIVE_ANIMATION,
            "status": "待审核",
            "uploader": "交互动画 Agent",
            "summary": "用 animation_spec 描述卷积核在输入矩阵上的滑动和输出特征图同步高亮。",
            "source": "深度学习初始知识库 / 第 7 章 CNN",
            "content": "# CNN 卷积滑窗动画规格\n\n## animation_type\ncnn_convolution\n\n## 参数\ninput_matrix_size: [5,5]\nkernel_size: [3,3]\nstride: 1\npadding: 0\n\n## 步骤\n1. 高亮左上角 3x3 区域，计算输出 [0,0]。\n2. 卷积核向右移动一个步幅，同步高亮输出 [0,1]。\n\n## 规格说明\n前端根据步骤高亮输入区域、卷积核和输出单元。",
        },
        {
            "id": "DEMO_DL_CNN_PROJECT",
            "title": "两周完成 CNN 图像分类项目 · 课程实践项目任务书",
            "type": artifact_types.PROJECT_BRIEF,
            "status": "待审核",
            "uploader": "项目任务 Agent",
            "summary": "拆解图像分类项目目标、数据集建议、技术路线、验收标准和评分 Rubric。",
            "source": "深度学习初始知识库 / 第 12 章 综合项目",
            "content": "# CNN 图像分类项目任务书\n\n## 项目背景\n用 CNN 完成一个小型图像分类任务。\n\n## 项目目标\n跑通训练、验证、误差分析和报告展示。\n\n## 数据集建议\nCIFAR-10、Fashion-MNIST 或教师提供的小数据集。\n\n## 技术路线\n数据加载 -> CNN 模型 -> 训练验证 -> 指标分析 -> 错误样本复盘。\n\n## 验收标准\n提交代码、实验报告、训练曲线、错误样本分析和 PPT 大纲。\n\n## Rubric\n模型可运行 30%，分析完整 30%，代码规范 20%，展示清晰 20%。",
        },
        {
            "id": "DEMO_DL_DIAG_CNN_SIZE",
            "title": "CNN 输出尺寸计算 · 诊断与补弱报告",
            "type": artifact_types.DIAGNOSTIC_REPORT,
            "status": "待审核",
            "uploader": "学习评价 Agent",
            "summary": "根据学生错题记录定位 padding、stride 和 kernel_size 的计算错误。",
            "source": "学习评价 Agent / CNN 输出尺寸",
            "content": "# CNN 输出尺寸计算诊断与补弱报告\n\n## 薄弱点\n- padding 没有乘以 2。\n- stride 对输出尺寸的缩小作用理解不稳。\n\n## 错因类型\n公式代入错误、tensor shape 检查不足。\n\n## 修复建议\n完成 5 道尺寸计算题，并在 PyTorch 中打印 Conv2d 输出 shape。\n\n## 诊断依据\n来自学生在学习评价中提交的错题描述。",
        },
    ]
    for item in resources:
        item["time"] = _now_str(-20)
        item["applicant_username"] = "student"
        item["agent_notes"] = "深度学习演示数据，建议管理员核验后发布。"
        _upsert_resource(db, item)


def _seed_resource_types(db: Session):
    for name in DEMO_RESOURCE_TYPES:
        _upsert_resource_type(db, name, "已通过")


def _seed_plans_and_todos(db: Session):
    plans = [{
        "id": "route_demo_cnn_project",
        "title": "两周完成 CNN 图像分类项目的个性化学习路径",
        "tasks": [
            {"title": "补齐反向传播基础", "desc": "理解链式法则和梯度如何传回参数。", "status": "active", "resources": [artifact_types.COURSE_NOTE, artifact_types.INTERACTIVE_ANIMATION]},
            {"title": "掌握 CNN 卷积操作", "desc": "完成卷积输出尺寸计算和卷积滑窗动画学习。", "status": "pending", "resources": [artifact_types.EXERCISE_SET, artifact_types.VIDEO_RECOMMENDATION]},
            {"title": "完成 PyTorch 图像分类实验", "desc": "跑通数据加载、模型训练和验证记录。", "status": "pending", "resources": [artifact_types.CODE_LAB, artifact_types.PROJECT_BRIEF]},
        ],
    }]
    _upsert_learning_plan(db, "student", plans)
    _upsert_todos(db, "student", [
        {"id": "todo_dl_1", "content": "完成 CNN 输出尺寸计算练习第 1-3 题", "done": False},
        {"id": "todo_dl_2", "content": "运行 PyTorch Conv2d shape 检查代码", "done": False},
        {"id": "todo_dl_3", "content": "审核通过后查看 CNN 主题学习包", "done": True},
    ])


def _seed_chats(db: Session):
    _upsert_chat_session(db, "CHAT_DEMO_CNN_PROJECT", "CNN 项目学习路线", "student", -120)
    _add_chat_message(db, "CHAT_DEMO_CNN_PROJECT_M1", "CHAT_DEMO_CNN_PROJECT", "student", "user", "我是大二学生，反向传播和 CNN 不太懂，想两周内做一个图像分类项目，比较喜欢图解和代码。", -119)
    _add_chat_message(db, "CHAT_DEMO_CNN_PROJECT_M2", "CHAT_DEMO_CNN_PROJECT", "student", "ai", "我会围绕「反向传播」「CNN 卷积操作」「PyTorch 图像分类实验」为你组织两周学习路线，并生成讲解、题集、代码实验、视频推荐、交互动画和项目任务书。", -118)

    _upsert_chat_session(db, "CHAT_DEMO_TRANSFORMER", "Transformer 自注意力", "student", -60)
    _add_chat_message(db, "CHAT_DEMO_TRANSFORMER_M1", "CHAT_DEMO_TRANSFORMER", "student", "user", "帮我生成 Transformer 自注意力机制的多模态学习资源，我公式基础一般，但想通过图解和代码理解。", -59)
    _add_chat_message(db, "CHAT_DEMO_TRANSFORMER_M2", "CHAT_DEMO_TRANSFORMER", "student", "ai", "已识别到「自注意力机制与 Transformer」。我会降低公式密度，优先提供 Q/K/V 图解、代码 demo、视频观看指南和 attention 交互动画规格。", -58)


def _seed_evaluations(db: Session):
    records = [{
        "id": "DEMO_EVAL_CNN_SIZE",
        "username": "student",
        "topic": "CNN 输出尺寸计算",
        "score": 66,
        "level": "需要巩固",
        "weak_points": _json(["padding 没有乘以 2", "stride 和 kernel_size 代入不稳定"]),
        "suggestions": _json(["重做尺寸公式练习", "使用 PyTorch 打印输出 shape", "观看卷积滑窗动画"]),
        "wrong_notes": "我做 CNN 练习题时总是算错输出特征图尺寸。",
        "answers_json": _json({"confidence": 58, "mode": "manual"}),
        "generated_resource_id": "DEMO_DL_DIAG_CNN_SIZE",
        "created_at": _now(-90),
    }]
    for item in records:
        _upsert_evaluation_record(db, item)


def _seed_feedbacks(db: Session):
    _upsert_feedback(db, {
        "id": "DEMO_FB_DL_001",
        "username": "student",
        "content": "希望 CNN 动画可以一步一步看卷积核滑动。",
        "status": "待处理",
        "date": _now_str(-60),
    })
    _upsert_feedback(db, {
        "id": "DEMO_FB_DL_002",
        "username": "demo_basic",
        "content": "想要更多反向传播的图解和小题。",
        "status": "已处理",
        "date": _now_str(-40),
    })


def seed_demo_base_data(db: Session, reset_demo_scope: bool = True) -> Dict:
    try:
        if reset_demo_scope:
            _reset_demo_scope(db)

        seed_initial_course_knowledge_base(db)
        _seed_users(db)
        _seed_resource_types(db)
        _seed_resources(db)
        _seed_feedbacks(db)
        _seed_plans_and_todos(db)
        _seed_chats(db)
        _seed_evaluations(db)

        db.commit()
        return {
            "success": True,
            "users": len(DEMO_USERNAMES),
            "resources": len(DEMO_RESOURCE_IDS),
            "resource_types": len(DEMO_RESOURCE_TYPES),
            "feedbacks": len(DEMO_FEEDBACK_IDS),
            "chat_sessions": len(DEMO_SESSION_IDS),
            "evaluation_records": 1,
            "message": "深度学习演示基准数据已写入 MySQL。",
        }
    except Exception as exc:
        db.rollback()
        return {
            "success": False,
            "message": str(exc),
        }
