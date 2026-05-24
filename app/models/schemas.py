# app/models/schemas.py
from sqlalchemy import Column, String, Integer, Text
from app.models.base import Base

# ================= 1. 用户表模型 =================
class User(Base):
    __tablename__ = "users"
    
    username = Column(String, primary_key=True, index=True, comment="学生账号/管理员账号")
    password = Column(String, nullable=False, comment="密码")
    role = Column(String, default="student", comment="角色: student 或 admin")
    avatar = Column(String, default="", comment="头像Base64或URL")
    bio = Column(String, default="这个人十分神秘什么都没留下哟", comment="个性签名")
    hours = Column(Integer, default=0, comment="累计在研/AI学时")
    tags = Column(String, default="", comment="学情画像标签，多标签用逗号隔开，如 Python,后端")


# ================= 2. 高校知识资源库模型 =================
class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(String, primary_key=True, index=True, comment="资源唯一编码")
    title = Column(String, nullable=False, comment="资源名称")
    type = Column(String, nullable=False, comment="知识模态: 知识点思维导图、代码类实操案例等")
    status = Column(String, default="待审核", comment="审核状态: 待审核、已通过")
    uploader = Column(String, default="system", comment="上传者或生成的智能体角色")
    time = Column(String, nullable=True, comment="提交时间")
    summary = Column(Text, default="", comment="资源摘要")
    content = Column(Text, default="", comment="资源正文，Markdown 格式")
    source = Column(String, default="", comment="知识来源或课程章节")
    agent_notes = Column(Text, default="", comment="智能体生成说明与审核提示")


# ================= 3. 动态分类标签表模型 =================
class ResourceType(Base):
    __tablename__ = "resource_types"
    
    name = Column(String, primary_key=True, index=True, comment="分类名称")
    status = Column(String, default="待审核", comment="状态: 待审核、已通过")


# ================= 4. 问题反馈表模型 =================
class Feedback(Base):
    __tablename__ = "feedbacks"
    
    id = Column(String, primary_key=True, index=True, comment="反馈编码")
    username = Column(String, nullable=False, comment="提交反馈的学生账号")
    content = Column(Text, nullable=False, comment="反馈具体内容")
    status = Column(String, default="待处理", comment="状态: 待处理、已处理")
    date = Column(String, nullable=False, comment="提交日期")


# ================= 5. 个性化学习规划表 =================
class LearningPlan(Base):
    __tablename__ = "learning_plans"

    username = Column(String, primary_key=True, index=True, comment="学生账号")
    plans_json = Column(Text, default="[]", comment="该学生的完整学习路线 JSON")
    updated_at = Column(String, nullable=True, comment="最后更新时间")


# ================= 6. 学习评价与错题诊断记录表 =================
class EvaluationRecord(Base):
    __tablename__ = "evaluation_records"

    id = Column(String, primary_key=True, index=True, comment="评价记录编码")
    username = Column(String, nullable=False, index=True, comment="学生账号")
    topic = Column(String, nullable=False, comment="评价主题")
    score = Column(Integer, default=0, comment="诊断得分")
    level = Column(String, default="", comment="掌握等级")
    weak_points = Column(Text, default="[]", comment="薄弱点 JSON")
    suggestions = Column(Text, default="[]", comment="补救建议 JSON")
    wrong_notes = Column(Text, default="", comment="学生提交的错题或自测描述")
    answers_json = Column(Text, default="{}", comment="原始作答数据 JSON")
    generated_resource_id = Column(String, default="", comment="生成的诊断资源编码")
    created_at = Column(String, nullable=True, comment="创建时间")
