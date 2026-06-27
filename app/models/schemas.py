from dataclasses import dataclass
from typing import Optional

# app/models/schemas.py
from sqlalchemy import Column, Float, String, Integer, Text, DateTime
from app.models.base import Base

# ================= 1. 用户表模型 =================
class User(Base):
    __tablename__ = "users"
    
    username = Column(String(64), primary_key=True, index=True, comment="学生账号/管理员账号")
    nickname = Column(String(64), default="", comment="展示昵称，可重复")
    password = Column(String(255), nullable=False, comment="密码")
    role = Column(String(32), default="student", comment="角色: student 或 admin")
    avatar = Column(Text, default="", comment="头像Base64或URL")
    bio = Column(Text, default="这个人十分神秘什么都没留下哟", comment="个性签名")
    hours = Column(Integer, default=0, comment="累计在研/AI学时")
    tags = Column(Text, default="", comment="学情画像标签，多标签用逗号隔开，如 Python,后端")


# ================= 2. 深度学习资源 Artifact 模型 =================
class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(String(64), primary_key=True, index=True, comment="资源唯一编码")
    title = Column(String(255), nullable=False, comment="资源名称")
    type = Column(String(128), nullable=False, comment="资源 Artifact 类型: 课程讲解文档、练习题集、PyTorch 实操案例等")
    status = Column(String(32), default="待审核", comment="审核状态: 待审核、已通过、未通过")
    uploader = Column(String(64), default="system", comment="上传者或生成的智能体角色")
    applicant_username = Column(String(64), default="", comment="资源提交学生账号，系统生成资源可为空")
    time = Column(String(32), nullable=True, comment="提交时间")
    summary = Column(Text, default="", comment="资源摘要")
    content = Column(Text, default="", comment="资源正文，Markdown 格式")
    source = Column(String(255), default="", comment="知识来源或课程章节")
    agent_notes = Column(Text, default="", comment="智能体生成说明与审核提示")
    review_comment = Column(Text, default="", comment="管理员审核意见或修改建议")
    reviewed_at = Column(String(32), default="", comment="最近一次审核时间")


# ================= 3. 动态分类标签表模型 =================
class ResourceType(Base):
    __tablename__ = "resource_types"
    
    name = Column(String(128), primary_key=True, index=True, comment="分类名称")
    status = Column(String(32), default="待审核", comment="状态: 待审核、已通过、未通过")
    applicant_username = Column(String(64), default="", comment="分类申请学生账号")
    reason = Column(Text, default="", comment="分类申请说明")
    review_comment = Column(Text, default="", comment="管理员审核意见或修改建议")
    reviewed_at = Column(String(32), default="", comment="最近一次审核时间")


# ================= 4. 问题反馈表模型 =================
class Feedback(Base):
    __tablename__ = "feedbacks"
    
    id = Column(String(64), primary_key=True, index=True, comment="反馈编码")
    username = Column(String(64), nullable=False, comment="提交反馈的学生账号")
    content = Column(Text, nullable=False, comment="反馈具体内容")
    status = Column(String(32), default="待处理", comment="状态: 待处理、已处理")
    date = Column(String(32), nullable=False, comment="提交日期")


# ================= 4.1 系统消息表模型 =================
class SystemMessage(Base):
    __tablename__ = "system_messages"

    id = Column(String(64), primary_key=True, index=True, comment="消息编码")
    username = Column(String(64), nullable=False, index=True, comment="接收学生账号")
    title = Column(String(255), nullable=False, comment="消息标题")
    content = Column(Text, nullable=False, comment="消息正文")
    category = Column(String(64), default="资源审核", comment="消息类型")
    related_resource_id = Column(String(64), default="", comment="关联资源编码")
    status = Column(String(16), default="未读", comment="未读或已读")
    created_at = Column(DateTime, nullable=True, comment="创建时间")


# ================= 5. 个性化学习规划表 =================
class LearningPlan(Base):
    __tablename__ = "learning_plans"

    username = Column(String(64), primary_key=True, index=True, comment="学生账号")
    plans_json = Column(Text, default="[]", comment="该学生的完整学习路线 JSON")
    updated_at = Column(String(32), nullable=True, comment="最后更新时间")

# ================= 6. 独立学习计划 =================
class TodoList(Base):
    __tablename__ = "todo_lists"

    username = Column(String(64), primary_key=True)
    todos_json = Column(Text)
    updated_at = Column(String(32))


# ================= 7. 学习评价与错题诊断记录表 =================
class EvaluationRecord(Base):
    __tablename__ = "evaluation_records"

    id = Column(String(64), primary_key=True, index=True, comment="评价记录编码")
    username = Column(String(64), nullable=False, index=True, comment="学生账号")
    topic = Column(String(255), nullable=False, comment="评价主题")
    score = Column(Integer, default=0, comment="诊断得分")
    level = Column(String(64), default="", comment="掌握等级")
    weak_points = Column(Text, default="[]", comment="薄弱点 JSON")
    suggestions = Column(Text, default="[]", comment="补救建议 JSON")
    wrong_notes = Column(Text, default="", comment="学生提交的错题或自测描述")
    answers_json = Column(Text, default="{}", comment="原始作答数据 JSON")
    generated_resource_id = Column(String(64), default="", comment="生成的诊断资源编码")
    created_at = Column(DateTime, nullable=True, comment="创建时间")

# ================= 8. 课程知识 =================
class CourseKnowledge(Base):
    __tablename__ = "course_knowledge"

    id = Column(Integer, primary_key=True, autoincrement=True)

    topic = Column(String(100))
    keywords = Column(Text)  # JSON字符串 or 逗号分隔
    chapter = Column(String(200))
    core = Column(Text)

    pitfalls = Column(Text)
    practice = Column(Text)
    practice_kind = Column(String(50))
    practice_output = Column(Text)

    code_lang = Column(String(50), nullable=True)
    code = Column(Text, nullable=True)


# ================= 9. AI 对话会话 =================
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(64), primary_key=True, index=True, comment="对话会话编码")
    username = Column(String(64), nullable=False, index=True, comment="所属学生账号")
    title = Column(String(255), default="新对话", comment="会话标题")
    last_topic = Column(String(255), default="", comment="最近一次明确学习主题")
    state_json = Column(Text, default="{}", comment="会话状态，如上一轮意图、动作和待确认事项")
    created_at = Column(DateTime, nullable=True, comment="创建时间")
    updated_at = Column(DateTime, nullable=True, comment="最后更新时间")


# ================= 10. AI 对话消息 =================
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(64), primary_key=True, index=True, comment="消息编码")
    session_id = Column(String(64), nullable=False, index=True, comment="所属会话编码")
    username = Column(String(64), nullable=False, index=True, comment="所属学生账号")
    role = Column(String(16), nullable=False, comment="消息角色: user 或 ai")
    content = Column(Text, nullable=False, comment="消息内容")
    metadata_json = Column(Text, default="{}", comment="消息附加展示数据，如链路、依据与安全摘要")
    created_at = Column(DateTime, nullable=True, comment="创建时间")


# ================= 11. Agent Trace =================
class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id = Column(String(64), primary_key=True, index=True, comment="Trace 行编码")
    trace_id = Column(String(64), nullable=False, index=True, comment="一次对话或生成任务的 Trace 编码")
    username = Column(String(64), default="", index=True, comment="学生账号")
    session_id = Column(String(64), default="", index=True, comment="对话会话编码")
    agent_name = Column(String(128), nullable=False, comment="Agent 名称")
    status = Column(String(32), default="completed", comment="执行状态")
    input_summary = Column(Text, default="", comment="输入摘要")
    output_json = Column(Text, default="{}", comment="结构化输出 JSON")
    evidence_refs_json = Column(Text, default="[]", comment="证据引用 JSON")
    quality_score = Column(Float, default=0.0, comment="质量分")
    warnings_json = Column(Text, default="[]", comment="警告 JSON")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    finished_at = Column(DateTime, nullable=True, comment="结束时间")


# ================= 12. 学习画像事件 =================
class ProfileEvent(Base):
    __tablename__ = "profile_events"

    event_id = Column(String(64), primary_key=True, index=True, comment="画像事件编码")
    student_id = Column(String(64), nullable=False, index=True, comment="学生账号")
    course_id = Column(String(64), default="deep_learning_v2", index=True, comment="课程编码")
    source_type = Column(String(64), default="chat", comment="来源类型")
    source_id = Column(String(64), default="", comment="来源编码")
    extracted_features_json = Column(Text, default="{}", comment="抽取特征 JSON")
    updated_dimensions_json = Column(Text, default="[]", comment="更新画像维度 JSON")
    reason = Column(Text, default="", comment="画像变化原因")
    created_at = Column(DateTime, nullable=True, comment="创建时间")


# ================= 13. 资源 Artifact 终版表 =================
class ResourceArtifact(Base):
    __tablename__ = "resource_artifacts"

    artifact_id = Column(String(64), primary_key=True, index=True, comment="Artifact 编码")
    resource_id = Column(String(64), default="", index=True, comment="兼容旧 resources 表编码")
    course_id = Column(String(64), default="deep_learning_v2", index=True, comment="课程编码")
    unit_ids_json = Column(Text, default="[]", comment="知识单元 ID JSON")
    student_id = Column(String(64), default="", index=True, comment="学生账号")
    type = Column(String(64), nullable=False, index=True, comment="Artifact 类型编码或名称")
    title = Column(String(255), nullable=False, comment="标题")
    summary = Column(Text, default="", comment="摘要")
    content_format = Column(String(64), default="markdown", comment="内容格式")
    content = Column(Text, default="", comment="正文或结构化内容")
    assets_json = Column(Text, default="[]", comment="资源附件 JSON")
    personalization_reason = Column(Text, default="", comment="个性化原因")
    evidence_refs_json = Column(Text, default="[]", comment="证据引用 JSON")
    quality_score = Column(Float, default=0.0, comment="质量分")
    risk_level = Column(String(32), default="待复核", comment="风险等级")
    status = Column(String(32), default="needs_review", index=True, comment="generated/quality_checked/published/needs_review")
    agent_name = Column(String(128), default="ResourcePlanningAgent", comment="生成 Agent")
    agent_trace_id = Column(String(64), default="", index=True, comment="Trace 编码")
    source = Column(Text, default="", comment="来源说明或外部原始链接")
    created_at = Column(DateTime, nullable=True, comment="创建时间")
    updated_at = Column(DateTime, nullable=True, comment="更新时间")


# ================= 14. 生成任务与事件 =================
class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    job_id = Column(String(64), primary_key=True, index=True, comment="生成任务编码")
    username = Column(String(64), nullable=False, index=True, comment="学生账号")
    course_id = Column(String(64), default="deep_learning_v2", index=True, comment="课程编码")
    topic = Column(String(255), default="", comment="主题")
    unit_id = Column(String(64), default="", index=True, comment="知识单元")
    status = Column(String(32), default="queued", index=True, comment="queued/running/completed/failed")
    progress = Column(Integer, default=0, comment="进度百分比")
    message = Column(Text, default="", comment="当前状态消息")
    artifacts_json = Column(Text, default="[]", comment="生成 Artifact ID JSON")
    created_at = Column(DateTime, nullable=True, comment="创建时间")
    updated_at = Column(DateTime, nullable=True, comment="更新时间")


class GenerationJobEvent(Base):
    __tablename__ = "generation_job_events"

    id = Column(String(64), primary_key=True, index=True, comment="事件编码")
    job_id = Column(String(64), nullable=False, index=True, comment="生成任务编码")
    event = Column(String(64), default="agent_started", comment="事件类型")
    agent = Column(String(128), default="", comment="Agent 名称")
    message = Column(Text, default="", comment="事件说明")
    progress = Column(Integer, default=0, comment="进度百分比")
    created_at = Column(DateTime, nullable=True, comment="创建时间")


# ================= 15. 视频、练习与资源反馈 =================
class VideoResource(Base):
    __tablename__ = "video_resources"

    video_id = Column(String(64), primary_key=True, index=True, comment="视频编码")
    course_id = Column(String(64), default="deep_learning_v2", index=True)
    unit_ids_json = Column(Text, default="[]")
    title = Column(String(255), nullable=False)
    platform = Column(String(128), default="")
    source = Column(String(255), default="")
    source_url = Column(Text, default="")
    tags_json = Column(Text, default="[]")
    difficulty = Column(String(32), default="beginner")
    duration = Column(String(32), default="")
    recommended_segments_json = Column(Text, default="[]")
    copyright_policy = Column(String(64), default="link_only")
    created_at = Column(DateTime, nullable=True)


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"

    attempt_id = Column(String(64), primary_key=True, index=True)
    username = Column(String(64), nullable=False, index=True)
    course_id = Column(String(64), default="deep_learning_v2", index=True)
    unit_id = Column(String(64), default="", index=True)
    artifact_id = Column(String(64), default="", index=True)
    answers_json = Column(Text, default="{}")
    score = Column(Integer, default=0)
    error_pattern_json = Column(Text, default="[]")
    created_at = Column(DateTime, nullable=True)


class ResourceFeedback(Base):
    __tablename__ = "resource_feedback"

    feedback_id = Column(String(64), primary_key=True, index=True)
    username = Column(String(64), nullable=False, index=True)
    artifact_id = Column(String(64), nullable=False, index=True)
    rating = Column(Integer, default=0)
    comment = Column(Text, default="")
    created_at = Column(DateTime, nullable=True)


@dataclass
class TurnRoute:
    route_type: str
    should_run_full_agents: bool = False
    should_run_intent_agent: bool = False
    should_run_retrieval: bool = False
    should_run_planner: bool = False
    should_generate_resources: bool = False
    should_update_profile: bool = False
    should_clear_topic: bool = False
    topic: Optional[str] = None
    student_reply: Optional[str] = None
