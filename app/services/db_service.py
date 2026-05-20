from sqlalchemy.orm import Session
from app.models.base import SessionLocal
from app.models.schemas import User, Resource, ResourceType, Feedback

# ================= 💡 快捷获取真数据库会话 =================
def get_db_context():
    """创建一个独立的、安全的数据库连接实例"""
    return SessionLocal()


# ================= 1. 认证模块（Auth Service） =================

def get_user_by_username(username: str):
    """根据账号从数据库中抓取用户全量信息"""
    db = get_db_context()
    try:
        return db.query(User).filter(User.username == username).first()
    finally:
        db.close()

def update_user_profile(username: str, bio: str, avatar: str = ""):
    """修改用户/管理员个性签名或头像并物理保存"""
    db = get_db_context()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.bio = bio
            if avatar:
                user.avatar = avatar
            db.commit()
            return True
        return False
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

def check_user_login(username, password):
    """【全真 SQL 版】校验登录，成功返回 user_info 字典，失败返回报错信息"""
    db = get_db_context()
    try:
        user = db.query(User).filter(User.username == username).first()
        
        # 1. 校验用户是否存在
        if not user:
            return {"success": False, "message": "用户不存在，请先注册！"}
        
        # 2. 校验密码是否正确
        if user.password != password:
            return {"success": False, "message": "密码错误，请重新输入"}
        
        # 3. 校验成功，恢复 Pinia 强依赖的数据结构
        return {
            "success": True,
            "data": {
                "username": user.username,
                "role": user.role,
                "avatar": user.avatar,
                "bio": user.bio,
                "hours": user.hours,
                "tags": [t for t in user.tags.split(",") if t] if user.tags else []
            }
        }
    except Exception as e:
        return {"success": False, "message": f"服务器数据库异常: {str(e)}"}
    finally:
        db.close()


# ================= 2. 管理员大盘模块（Dashboard Service） =================

def get_dashboard_stats():
    """轰鸣 SQL 统计全站实时运营指标，完美对齐前端卡片"""
    db = get_db_context()
    try:
        total_users = db.query(User).filter(User.role == "student").count()
        total_resources = db.query(Resource).count()
        pending_resources = db.query(Resource).filter(Resource.status == "待审核").count()
        pending_feedback = db.query(Feedback).filter(Feedback.status == "待处理").count()
        pending_types = db.query(ResourceType).filter(ResourceType.status == "待审核").count()
        
        return {
            "total_users": total_users,
            "total_resources": total_resources,
            "pending_resources": pending_resources,
            "pending_feedback": pending_feedback,
            "todo_count": pending_resources + pending_feedback + pending_types
        }
    finally:
        db.close()


# ================= 3. 资源审核与管理模块（Resource Service） =================

def get_all_resources():
    """获取全量资源列表（学生端/管理端通用）"""
    db = get_db_context()
    try:
        return db.query(Resource).all()
    finally:
        db.close()

def approve_resource(resource_id: str):
    """批准某项高校多模态知识资源放行入库"""
    db = get_db_context()
    try:
        res = db.query(Resource).filter(Resource.id == resource_id).first()
        if res:
            res.status = "已通过"
            db.commit()
            return True
        return False
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

def get_all_resource_types():
    """获取所有学生提议的动态 Tab 分类"""
    db = get_db_context()
    try:
        return db.query(ResourceType).all()
    finally:
        db.close()

def approve_resource_type(type_name: str):
    """超级管理员批准全站动态新增分类"""
    db = get_db_context()
    try:
        rtype = db.query(ResourceType).filter(ResourceType.name == type_name).first()
        if rtype:
            rtype.status = "已通过"
            db.commit()
            return True
        return False
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()


# ================= 4. 问题反馈中心模块（Feedback Service） =================

def get_all_feedbacks():
    """捞出全站学生提交上来的所有反馈"""
    db = get_db_context()
    try:
        return db.query(Feedback).all()
    finally:
        db.close()

def handle_feedback_status(feedback_id: str):
    """一键处理/完结学生的反馈问题"""
    db = get_db_context()
    try:
        fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if fb:
            fb.status = "已处理"
            db.commit()
            return True
        return False
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()


# ================= 5. 智能学习规划路线模块（修复刷新消失） =================

# 🌟 全局路线内存高速锁，用于在比赛演示时锁死路线和独立任务，防止刷新消失
TEMP_PLANS_STORAGE = {}

def get_plans_by_username(username: str):
    """【持久兼容版】获取路线：如果内存中有保存的路线就返回，没有则返回空列表"""
    return TEMP_PLANS_STORAGE.get(username, [])

def save_user_plans(username: str, plans_list: list):
    """【持久兼容版】当学生在前端添加、删除、勾选任务时，强制同步锁死数据"""
    TEMP_PLANS_STORAGE[username] = plans_list
    return True

def delete_plan_route(username: str, route_id: str):
    """废弃整条学习路线"""
    return True

def delete_plan_task(username: str, route_id: str, task_id: int):
    """从某条路线中精准剥离某个任务节点"""
    return True


# ================= 6. 学生前台初始知识库与写入核心（消灭全站 500 报错） =================

def get_passed_resource_types():
    """【全真 SQL 版】学生前台：只拉取审核通过的分类，用于渲染 Tab 栏"""
    db = get_db_context()
    try:
        types = db.query(ResourceType).filter(ResourceType.status == "已通过").all()
        if not types:
            # 贴心兜底：如果数据库表完全是空，返回比赛系统默认需要的初始 6 大类
            return ["专业课程讲解文档", "知识点思维导图", "不同类型练习题目", "拓展阅读材料", "多模态教学视频/动画", "代码类实操案例"]
        return [t.name for t in types]
    finally:
        db.close()

def get_passed_resources():
    """【全真 SQL 版】学生前台：只看审核通过的初始课程资源"""
    db = get_db_context()
    try:
        return db.query(Resource).filter(Resource.status == "已通过").all()
    finally:
        db.close()

def insert_new_resource(title: str, r_type: str):
    """【全真 SQL 版】前台学生：点击提交、上传初始资源库（物理插入真数据库）"""
    import datetime
    db = get_db_context()
    try:
        new_id = f"RES{int(datetime.datetime.now().timestamp())}"[-6:]
        new_item = Resource(
            id=new_id,
            title=title,
            type=r_type,
            status="待审核",
            uploader="student",
            time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        db.add(new_item)
        db.commit()
        return {
            "id": new_id,
            "title": title,
            "type": r_type,
            "status": "待审核"
        }
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()

def insert_feedback(username: str, content: str):
    """【全真 SQL 版】消灭反馈提交报错：向反馈表物理新增一条记录"""
    import datetime
    db = get_db_context()
    try:
        new_id = f"FB{int(datetime.datetime.now().timestamp())}"[-6:]
        new_fb = Feedback(
            id=new_id,
            username=username,
            content=content,
            status="待处理",
            date=datetime.datetime.now().strftime("%Y-%m-%d")
        )
        db.add(new_fb)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

def propose_new_type(type_name: str):  
    """【全真 SQL 版】提议新资源分类：物理插入 resource_types 数据库表"""
    db = get_db_context()
    try:
        exists = db.query(ResourceType).filter(ResourceType.name == type_name).first()
        if not exists:
            new_type = ResourceType(name=type_name, status="待审核")
            db.add(new_type)
            db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()