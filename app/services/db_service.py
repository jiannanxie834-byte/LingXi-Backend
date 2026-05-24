from copy import deepcopy
import datetime
import json
import uuid
from sqlalchemy.orm import Session
from app.models.base import SessionLocal
from app.models.schemas import User, Resource, ResourceType, Feedback, LearningPlan, EvaluationRecord
from app.database import PLANS_DB

DEFAULT_RESOURCE_TYPES = [
    "专业课程讲解文档",
    "知识点思维导图",
    "不同类型练习题目",
    "拓展阅读材料",
    "错题诊断与学习反馈报告",
    "代码类实操案例",
]

DEPRECATED_RESOURCE_TYPES = {
    "多模态教学视频/动画",
    "多模态视频",
    "教学视频",
    "视频",
    "动画",
}


def _is_deprecated_resource_type(type_name: str):
    normalized_type = (type_name or "").strip()
    if normalized_type.isdigit():
        return True
    return any(item == normalized_type or item in normalized_type for item in DEPRECATED_RESOURCE_TYPES)


def _user_to_dict(user: User):
    return {
        "username": user.username,
        "role": user.role,
        "avatar": user.avatar,
        "bio": user.bio,
        "hours": user.hours,
        "tags": [t for t in user.tags.split(",") if t] if user.tags else [],
    }


def _resource_to_dict(resource: Resource):
    return {
        "id": resource.id,
        "title": resource.title,
        "type": resource.type,
        "status": resource.status,
        "uploader": resource.uploader,
        "time": resource.time,
        "summary": resource.summary or "",
        "content": resource.content or "",
        "source": resource.source or "",
        "agent_notes": resource.agent_notes or "",
    }


def _resource_type_to_dict(resource_type: ResourceType):
    return {
        "name": resource_type.name,
        "status": resource_type.status,
    }


def _feedback_to_dict(feedback: Feedback):
    return {
        "id": feedback.id,
        "username": feedback.username,
        "content": feedback.content,
        "status": feedback.status,
        "date": feedback.date,
    }


def _evaluation_to_dict(record: EvaluationRecord):
    try:
        weak_points = json.loads(record.weak_points or "[]")
    except (TypeError, json.JSONDecodeError):
        weak_points = []
    try:
        suggestions = json.loads(record.suggestions or "[]")
    except (TypeError, json.JSONDecodeError):
        suggestions = []
    try:
        answers = json.loads(record.answers_json or "{}")
    except (TypeError, json.JSONDecodeError):
        answers = {}

    return {
        "id": record.id,
        "username": record.username,
        "topic": record.topic,
        "score": record.score,
        "level": record.level,
        "weak_points": weak_points,
        "suggestions": suggestions,
        "wrong_notes": record.wrong_notes or "",
        "answers": answers,
        "generated_resource_id": record.generated_resource_id or "",
        "created_at": record.created_at,
    }


def _new_id(prefix: str):
    return f"{prefix}{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

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

def update_user_profile(username: str, bio: str, avatar: str = "", password: str = ""):
    """修改用户/管理员个性签名或头像并物理保存"""
    db = get_db_context()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            if bio is not None:
                user.bio = bio
            if avatar:
                user.avatar = avatar
            if password:
                user.password = password
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
            "data": _user_to_dict(user)
        }
    except Exception as e:
        return {"success": False, "message": f"服务器数据库异常: {str(e)}"}
    finally:
        db.close()


def create_user(username: str, password: str):
    """注册普通学生账号。"""
    db = get_db_context()
    try:
        exists = db.query(User).filter(User.username == username).first()
        if exists:
            return {"success": False, "message": "账号已存在，请直接登录"}

        user = User(
            username=username,
            password=password,
            role="student",
            avatar="",
            bio="这个人十分神秘什么都没留下哟",
            hours=0,
            tags=""
        )
        db.add(user)
        db.commit()
        return {"success": True, "data": _user_to_dict(user)}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"注册失败: {str(e)}"}
    finally:
        db.close()


def update_user_learning_profile(username: str, tags: list, hours_delta: int = 0):
    """根据对话结果轻量更新学生画像标签和学习时长。"""
    db = get_db_context()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None

        current_tags = [tag for tag in user.tags.split(",") if tag] if user.tags else []
        merged_tags = list(dict.fromkeys(current_tags + [tag for tag in tags if tag]))
        user.tags = ",".join(merged_tags)
        user.hours = max(0, (user.hours or 0) + hours_delta)
        db.commit()
        db.refresh(user)
        return _user_to_dict(user)
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()


# ================= 2. 管理员大盘模块（Dashboard Service） =================

def get_dashboard_stats():
    """轰鸣 SQL 统计全站实时运营指标，完美对齐前端卡片"""
    db = get_db_context()
    try:
        total_users = db.query(User).filter(User.role == "student").count()
        active_resources = [
            resource for resource in db.query(Resource).all()
            if not _is_deprecated_resource_type(resource.type)
        ]
        total_resources = len(active_resources)
        pending_resources = len([resource for resource in active_resources if resource.status == "待审核"])
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


def get_all_students():
    """管理端获取所有学生用户画像。"""
    db = get_db_context()
    try:
        students = db.query(User).filter(User.role == "student").all()
        return [_user_to_dict(user) for user in students]
    finally:
        db.close()


# ================= 3. 资源审核与管理模块（Resource Service） =================

def get_all_resources():
    """获取全量资源列表（学生端/管理端通用）"""
    db = get_db_context()
    try:
        resources = [
            resource for resource in db.query(Resource).all()
            if not _is_deprecated_resource_type(resource.type)
        ]
        return [_resource_to_dict(resource) for resource in resources]
    finally:
        db.close()

def approve_resource(resource_id: str):
    """批准某项高校知识资源放行入库"""
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


def reject_resource(resource_id: str):
    """下架或删除某项资源。"""
    db = get_db_context()
    try:
        res = db.query(Resource).filter(Resource.id == resource_id).first()
        if res:
            db.delete(res)
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
        resource_types = [
            resource_type for resource_type in db.query(ResourceType).all()
            if not _is_deprecated_resource_type(resource_type.name)
        ]
        return [_resource_type_to_dict(resource_type) for resource_type in resource_types]
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
        return [_feedback_to_dict(feedback) for feedback in db.query(Feedback).all()]
    finally:
        db.close()


def get_all_feedback():
    """兼容管理路由里正在使用的函数名。"""
    return get_all_feedbacks()

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


def mark_feedback_processed(feedback_id: str):
    """兼容管理路由里正在使用的函数名。"""
    return handle_feedback_status(feedback_id)


def delete_feedback_by_id(feedback_id: str):
    """物理删除反馈记录。"""
    db = get_db_context()
    try:
        fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if fb:
            db.delete(fb)
            db.commit()
            return True
        return False
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()


# ================= 5. 智能学习规划路线模块（持久化到 SQLite） =================

# 运行期缓存只用于减少重复查库，最终数据以 learning_plans 表为准。
TEMP_PLANS_STORAGE = {}


def _load_user_plans_from_db(username: str):
    db = get_db_context()
    try:
        record = db.query(LearningPlan).filter(LearningPlan.username == username).first()
        if not record:
            return None
        return json.loads(record.plans_json or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    finally:
        db.close()


def _save_user_plans_to_db(username: str, plans_list: list):
    db = get_db_context()
    try:
        record = db.query(LearningPlan).filter(LearningPlan.username == username).first()
        if not record:
            record = LearningPlan(username=username)
            db.add(record)
        record.plans_json = json.dumps(plans_list or [], ensure_ascii=False)
        record.updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

def get_plans_by_username(username: str):
    """获取路线：优先读 SQLite，首访时把演示默认路线迁入真实表。"""
    if username in TEMP_PLANS_STORAGE:
        return deepcopy(TEMP_PLANS_STORAGE[username])

    stored_plans = _load_user_plans_from_db(username)
    if stored_plans is not None:
        TEMP_PLANS_STORAGE[username] = stored_plans
        return deepcopy(stored_plans)

    default_plans = deepcopy(PLANS_DB.get(username, []))
    if default_plans:
        _save_user_plans_to_db(username, default_plans)
        TEMP_PLANS_STORAGE[username] = default_plans
    return deepcopy(default_plans)

def save_user_plans(username: str, plans_list: list):
    """当学生添加、删除、勾选任务时，保存完整路线快照。"""
    TEMP_PLANS_STORAGE[username] = deepcopy(plans_list or [])
    return _save_user_plans_to_db(username, plans_list or [])


def save_generated_plan(username: str, title: str, path_steps: list, resources: list):
    """把多智能体生成的学习路径同步到学生规划页。"""
    plans = get_plans_by_username(username)
    resource_titles = [item.get("title") for item in resources if item.get("title")]
    new_plan = {
        "id": _new_id("route_agent_"),
        "title": title,
        "isCollapsed": False,
        "isAiGenerated": True,
        "tasks": [
            {
                "id": index + 1,
                "title": step.split("：", 1)[0] if "：" in step else f"学习任务 {index + 1}",
                "desc": step.split("：", 1)[1] if "：" in step else step,
                "status": "active" if index == 0 else "pending",
                "isCustom": False,
                "resources": resource_titles[:3],
            }
            for index, step in enumerate(path_steps)
        ],
    }
    filtered_plans = [plan for plan in plans if plan.get("title") != title]
    save_user_plans(username, [new_plan] + filtered_plans)
    return new_plan

def delete_plan_route(username: str, route_id: str):
    """废弃整条学习路线"""
    plans = get_plans_by_username(username)
    save_user_plans(username, [plan for plan in plans if str(plan.get("id")) != str(route_id)])
    return True

def delete_plan_task(username: str, route_id: str, task_id: int):
    """从某条路线中精准剥离某个任务节点"""
    plans = get_plans_by_username(username)
    for plan in plans:
        if str(plan.get("id")) == str(route_id):
            plan["tasks"] = [task for task in plan.get("tasks", []) if str(task.get("id")) != str(task_id)]
            break
    save_user_plans(username, plans)
    return True


# ================= 6. 学习评价与错题诊断模块 =================

def save_evaluation_record(
    username: str,
    topic: str,
    score: int,
    level: str,
    weak_points: list,
    suggestions: list,
    wrong_notes: str,
    answers: dict,
    generated_resource_id: str = ""
):
    """保存学生自测/错题诊断记录。"""
    db = get_db_context()
    try:
        record = EvaluationRecord(
            id=_new_id("EVL"),
            username=username,
            topic=topic,
            score=score,
            level=level,
            weak_points=json.dumps(weak_points or [], ensure_ascii=False),
            suggestions=json.dumps(suggestions or [], ensure_ascii=False),
            wrong_notes=wrong_notes or "",
            answers_json=json.dumps(answers or {}, ensure_ascii=False),
            generated_resource_id=generated_resource_id,
            created_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return _evaluation_to_dict(record)
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()


def get_evaluation_records(username: str):
    """获取某个学生的学习评价历史。"""
    db = get_db_context()
    try:
        records = (
            db.query(EvaluationRecord)
            .filter(EvaluationRecord.username == username)
            .order_by(EvaluationRecord.created_at.desc())
            .all()
        )
        return [_evaluation_to_dict(record) for record in records]
    finally:
        db.close()


# ================= 6. 学生前台初始知识库与写入核心（消灭全站 500 报错） =================

def get_passed_resource_types():
    """【全真 SQL 版】学生前台：只拉取审核通过的分类，用于渲染 Tab 栏"""
    db = get_db_context()
    try:
        types = db.query(ResourceType).filter(ResourceType.status == "已通过").all()
        names = DEFAULT_RESOURCE_TYPES + [
            t.name
            for t in types
            if t.name not in DEFAULT_RESOURCE_TYPES and not _is_deprecated_resource_type(t.name)
        ]
        return names
    finally:
        db.close()

def get_passed_resources():
    """【全真 SQL 版】学生前台：只看审核通过的初始课程资源"""
    db = get_db_context()
    try:
        resources = [
            resource for resource in db.query(Resource).filter(Resource.status == "已通过").all()
            if not _is_deprecated_resource_type(resource.type)
        ]
        return [_resource_to_dict(resource) for resource in resources]
    finally:
        db.close()

def insert_new_resource(title: str, r_type: str, summary: str = "", content: str = "", source: str = "", agent_notes: str = ""):
    """【全真 SQL 版】前台学生：点击提交、上传初始资源库（物理插入真数据库）"""
    db = get_db_context()
    try:
        new_id = _new_id("RES")
        new_item = Resource(
            id=new_id,
            title=title,
            type=r_type,
            status="待审核",
            uploader="student",
            time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            summary=summary,
            content=content,
            source=source,
            agent_notes=agent_notes
        )
        db.add(new_item)
        db.commit()
        return {
            "id": new_id,
            "title": title,
            "type": r_type,
            "status": "待审核",
            "summary": summary,
            "content": content,
            "source": source,
            "agent_notes": agent_notes
        }
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()


def insert_generated_resources(resources: list, uploader: str = "资源生成 Agent"):
    """把 Agent 生成的学习资源送入后台审核队列。"""
    db = get_db_context()
    inserted_items = []
    try:
        for item in resources:
            title = item.get("title", "").strip()
            r_type = item.get("type", "").strip()
            if not title or not r_type:
                continue

            existing = db.query(Resource).filter(Resource.title == title, Resource.type == r_type).first()
            if existing:
                existing.summary = item.get("summary", existing.summary or "")
                existing.content = item.get("content", existing.content or "")
                existing.source = item.get("source", existing.source or "")
                existing.agent_notes = item.get("agent_notes", existing.agent_notes or "")
                existing.uploader = uploader
                existing.time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                inserted_items.append(_resource_to_dict(existing))
                continue

            resource = Resource(
                id=_new_id("RES"),
                title=title,
                type=r_type,
                status="待审核",
                uploader=uploader,
                time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                summary=item.get("summary", ""),
                content=item.get("content", ""),
                source=item.get("source", ""),
                agent_notes=item.get("agent_notes", "")
            )
            db.add(resource)
            db.flush()
            inserted_items.append(_resource_to_dict(resource))
        db.commit()
        return inserted_items
    except Exception:
        db.rollback()
        return []
    finally:
        db.close()

def insert_feedback(username: str, content: str):
    """【全真 SQL 版】消灭反馈提交报错：向反馈表物理新增一条记录"""
    db = get_db_context()
    try:
        new_id = _new_id("FB")
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
