import json
import uuid
import datetime
from copy import deepcopy
from sqlalchemy.orm import Session

from app.models.schemas import LearningPlan, TodoList


# =========================
# 内存缓存（保留）
# =========================
TEMP_PLANS_STORAGE = {}
TEMP_TODOS_STORAGE = {}


# =========================
# Learning Plan
# =========================

def _load_user_plans_from_db(db: Session, username: str):
    try:
        record = (
            db.query(LearningPlan)
            .filter(LearningPlan.username == username)
            .first()
        )

        if not record:
            return None

        return json.loads(record.plans_json or "[]")

    except Exception:
        return []
    

def _save_user_plans_to_db(db: Session, username: str, plans_list: list):
    try:
        record = (
            db.query(LearningPlan)
            .filter(LearningPlan.username == username)
            .first()
        )

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


def get_plans_by_username(db: Session, username: str):
    """获取学习路线（缓存 + DB）"""

    if username in TEMP_PLANS_STORAGE:
        return deepcopy(TEMP_PLANS_STORAGE[username])

    stored = _load_user_plans_from_db(db, username)

    if stored is not None:
        TEMP_PLANS_STORAGE[username] = stored
        return deepcopy(stored)

    return []


def save_user_plans(db: Session, username: str, plans_list: list):
    TEMP_PLANS_STORAGE[username] = deepcopy(plans_list or [])
    return _save_user_plans_to_db(db, username, plans_list or [])


def save_generated_plan(
    db: Session,
    username: str,
    title: str,
    path_steps: list,
    resources: list
):
    plans = get_plans_by_username(db, username)

    resource_titles = [
        item.get("title")
        for item in resources
        if item.get("title")
    ]

    new_plan = {
        "id": f"route_{uuid.uuid4().hex[:8]}",
        "title": title,
        "isCollapsed": False,
        "isAiGenerated": True,
        "tasks": [
            {
                "id": idx + 1,
                "title": step.split("：", 1)[0] if "：" in step else f"任务 {idx + 1}",
                "desc": step.split("：", 1)[1] if "：" in step else step,
                "status": "active" if idx == 0 else "pending",
                "isCustom": False,
                "resources": resource_titles[:3],
            }
            for idx, step in enumerate(path_steps)
        ],
    }

    filtered = [p for p in plans if p.get("title") != title]

    save_user_plans(db, username, [new_plan] + filtered)

    return new_plan


def delete_plan_route(db: Session, username: str, route_id: str):
    plans = get_plans_by_username(db, username)

    new_plans = [
        p for p in plans
        if str(p.get("id")) != str(route_id)
    ]

    save_user_plans(db, username, new_plans)
    return True


def delete_plan_task(db: Session, username: str, route_id: str, task_id: str):
    plans = get_plans_by_username(db, username)

    for plan in plans:
        if str(plan.get("id")) == str(route_id):
            plan["tasks"] = [
                t for t in plan.get("tasks", [])
                if str(t.get("id")) != str(task_id)
            ]
            break

    save_user_plans(db, username, plans)
    return True


# =========================
# Todo List
# =========================

def _load_user_todos_from_db(db: Session, username: str):
    try:
        record = (
            db.query(TodoList)
            .filter(TodoList.username == username)
            .first()
        )

        if not record:
            return None

        return json.loads(record.todos_json or "[]")

    except Exception:
        return []


def _save_user_todos_to_db(db: Session, username: str, todos_list: list):
    try:
        record = (
            db.query(TodoList)
            .filter(TodoList.username == username)
            .first()
        )

        if not record:
            record = TodoList(username=username)
            db.add(record)

        record.todos_json = json.dumps(todos_list or [], ensure_ascii=False)
        record.updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        db.commit()
        return True

    except Exception:
        db.rollback()
        return False


def get_todos_by_username(db: Session, username: str):
    if username in TEMP_TODOS_STORAGE:
        return deepcopy(TEMP_TODOS_STORAGE[username])

    stored = _load_user_todos_from_db(db, username)

    if stored is not None:
        TEMP_TODOS_STORAGE[username] = stored
        return deepcopy(stored)

    default_todos = [
        {"id": 1, "content": "完成计网第三章课后习题", "done": True},
        {"id": 2, "content": "复习 JavaScript 异步编程", "done": False},
    ]

    _save_user_todos_to_db(db, username, default_todos)
    TEMP_TODOS_STORAGE[username] = default_todos

    return deepcopy(default_todos)


def save_user_todos(db: Session, username: str, todos_list: list):
    TEMP_TODOS_STORAGE[username] = deepcopy(todos_list or [])
    return _save_user_todos_to_db(db, username, todos_list or [])