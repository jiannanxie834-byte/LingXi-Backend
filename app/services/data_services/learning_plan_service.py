import json
import uuid
import datetime
from sqlalchemy.orm import Session

from app.models.schemas import LearningPlan, TodoList


def _first_list_item(value, default=""):
    return value[0] if isinstance(value, list) and value else default


def _resource_type_matches(focus_type: str, resource_type: str) -> bool:
    focus = str(focus_type or "").strip()
    current = str(resource_type or "").strip()
    if not focus or not current:
        return False
    return focus == current or focus in current or current in focus


def normalize_plan_resource(item: dict, step: dict, step_index: int = 0, resource_index: int = 0):
    item = item or {}
    artifact = item.get("artifact") if isinstance(item.get("artifact"), dict) else {}
    artifact_id = item.get("artifact_id") or artifact.get("artifact_id") or ""
    resource_id = item.get("resource_id") or artifact.get("resource_id") or item.get("id") or ""
    unit_ids = item.get("unit_ids") or artifact.get("unit_ids") or []
    unit_id = item.get("unit_id") or _first_list_item(unit_ids) or step.get("unit_id") or ""
    resource_type = item.get("type") or artifact.get("type") or "学习资源"

    query = {
        "artifact_id": artifact_id,
        "resource_id": resource_id,
        "unit_id": unit_id,
        "type": resource_type,
    }
    return {
        "id": artifact_id or resource_id or f"res_{step_index + 1}_{resource_index + 1}",
        "artifact_id": artifact_id,
        "resource_id": resource_id,
        "title": item.get("title") or artifact.get("title") or f"{step.get('title') or '学习步骤'}配套资源",
        "type": resource_type,
        "unit_id": unit_id,
        "route": "/resource" if artifact_id else "",
        "query": query,
    }


def bind_resources_to_step(step: dict, resources: list, step_index: int = 0):
    def _has_resource_title(item):
        artifact = item.get("artifact") if isinstance(item.get("artifact"), dict) else {}
        return bool(item.get("title") or artifact.get("title"))

    resource_items = [
        item for item in (resources or [])
        if isinstance(item, dict) and _has_resource_title(item)
    ]
    step_unit_id = str(step.get("unit_id") or "").strip()
    focus_types = step.get("resource_focus") if isinstance(step.get("resource_focus"), list) else []
    matched = []

    for item in resource_items:
        artifact = item.get("artifact") if isinstance(item.get("artifact"), dict) else {}
        item_unit_ids = item.get("unit_ids") or artifact.get("unit_ids") or []
        item_unit_id = str(item.get("unit_id") or _first_list_item(item_unit_ids) or "").strip()
        item_type = str(item.get("type") or artifact.get("type") or "").strip()
        unit_ok = not step_unit_id or not item_unit_id or item_unit_id == step_unit_id
        focus_ok = not focus_types or any(_resource_type_matches(focus, item_type) for focus in focus_types)
        if unit_ok and focus_ok:
            matched.append(item)

    if not matched:
        matched = [
            item for item in resource_items
            if not step_unit_id
            or str(item.get("unit_id") or _first_list_item((item.get("artifact") or {}).get("unit_ids") or []) or "").strip() in {"", step_unit_id}
        ]
    if not matched:
        matched = resource_items

    return [
        normalize_plan_resource(item, step, step_index, r_index)
        for r_index, item in enumerate(matched[:3])
    ]


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
    stored = _load_user_plans_from_db(db, username)
    return stored if stored is not None else []


def save_user_plans(db: Session, username: str, plans_list: list):
    return _save_user_plans_to_db(db, username, plans_list or [])


def save_generated_plan(
    db: Session,
    username: str,
    title: str,
    path_steps: list,
    resources: list
):
    plans = get_plans_by_username(db, username)

    def _task_from_step(step, idx):
        if isinstance(step, dict):
            unit_id = step.get("unit_id") or ""
            return {
                "id": step.get("id") or f"node_{idx + 1:03d}",
                "title": step.get("title") or f"任务 {idx + 1}",
                "desc": step.get("objective") or "",
                "status": step.get("status") or ("active" if idx == 0 else "pending"),
                "isCustom": False,
                "unit_id": unit_id,
                "resources": bind_resources_to_step(step, resources, idx),
                "resource_focus": step.get("resource_focus") or [],
            }

        text = str(step or "")
        step_dict = {"title": text, "unit_id": "", "resource_focus": []}
        return {
            "id": f"node_{idx + 1:03d}",
            "title": text.split("：", 1)[0] if "：" in text else f"任务 {idx + 1}",
            "desc": text.split("：", 1)[1] if "：" in text else text,
            "status": "active" if idx == 0 else "pending",
            "isCustom": False,
            "unit_id": "",
            "resources": bind_resources_to_step(step_dict, resources, idx),
            "resource_focus": [],
        }

    new_plan = {
        "id": f"route_{uuid.uuid4().hex[:8]}",
        "title": title,
        "desc": f"围绕「{title}」生成的《深度学习》个性化学习路线。",
        "isCollapsed": False,
        "isAiGenerated": True,
        "tasks": [
            _task_from_step(step, idx)
            for idx, step in enumerate(path_steps)
        ],
    }

    filtered = [p for p in plans if p.get("title") != title]

    save_user_plans(db, username, [new_plan] + filtered)

    return new_plan


def attach_artifacts_to_plan(db: Session, username: str, plan_title: str, resources: list):
    plans = get_plans_by_username(db, username)
    if not plans:
        return None

    target = None
    for plan in plans:
        if plan_title and plan.get("title") == plan_title:
            target = plan
            break
    if not target:
        target = plans[0]

    for idx, task in enumerate(target.get("tasks", []) or []):
        task["resources"] = bind_resources_to_step(task, resources, idx)

    save_user_plans(db, username, plans)
    return target


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
    stored = _load_user_todos_from_db(db, username)
    if stored is not None:
        return stored

    default_todos = [
        {"id": 1, "content": "完成 CNN 卷积与池化基础练习", "done": True},
        {"id": 2, "content": "复习反向传播链式法则推导", "done": False},
    ]

    _save_user_todos_to_db(db, username, default_todos)
    return default_todos


def save_user_todos(db: Session, username: str, todos_list: list):
    return _save_user_todos_to_db(db, username, todos_list or [])
