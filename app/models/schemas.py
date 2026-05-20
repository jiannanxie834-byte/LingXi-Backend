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