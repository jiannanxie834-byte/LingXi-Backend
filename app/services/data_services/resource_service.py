import datetime

from sqlalchemy.orm import Session

from app.models.schemas import (
    Resource,
    ResourceType
)

DEFAULT_RESOURCE_TYPES = [
    "专业课程讲解文档",
    "知识点思维导图",
    "不同类型练习题目",
    "拓展阅读材料",
    "错题诊断与学习反馈报告",
    "学科实践应用任务",
]

DEPRECATED_RESOURCE_TYPES = {
    "多模态教学视频/动画",
    "多模态视频",
    "教学视频",
    "视频",
    "动画",
    "代码类实操案例",
}


# =========================
# tools
# =========================

def _is_deprecated_resource_type(type_name: str):
    normalized_type = (type_name or "").strip()
    if normalized_type.isdigit():
        return True
    return any(item == normalized_type or item in normalized_type for item in DEPRECATED_RESOURCE_TYPES)


def _new_resource_id():
    return f"RES{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"


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


# =========================
# query layer
# =========================

def get_all_resources(db: Session):

    try:

        return [
            _resource_to_dict(r)
            for r in db.query(Resource).all()
            if not _is_deprecated_resource_type(r.type)
        ]

    except Exception:
        return []


def get_passed_resources(db: Session):

    try:

        return [
            _resource_to_dict(r)
            for r in db.query(Resource)
            .filter(Resource.status == "已通过")
            .all()
            if not _is_deprecated_resource_type(r.type)
        ]

    except Exception:
        return []


# =========================
# 分类
# =========================

def get_all_resource_types(db: Session):

    try:

        types = [
            t for t in db.query(ResourceType).all()
            if not _is_deprecated_resource_type(t.name)
        ]

        return [
            {
                "name": t.name,
                "status": t.status
            }
            for t in types
        ]

    except Exception:
        return []


def get_passed_resource_types(db: Session):

    try:

        types = (
            db.query(ResourceType)
            .filter(ResourceType.status == "已通过")
            .all()
        )

        names = DEFAULT_RESOURCE_TYPES + [
            t.name
            for t in types
            if t.name not in DEFAULT_RESOURCE_TYPES and not _is_deprecated_resource_type(t.name)
        ]

        return list(dict.fromkeys(names))

    except Exception:
        return []


def propose_new_type(
    db: Session,
    name: str
):

    try:

        exists = (
            db.query(ResourceType)
            .filter(ResourceType.name == name)
            .first()
        )

        if exists:
            return False

        item = ResourceType(name=name, status="待审核")

        db.add(item)
        db.commit()

        return True

    except Exception:
        db.rollback()
        return False


def approve_resource_type(
    db: Session,
    name: str
):

    try:

        item = (
            db.query(ResourceType)
            .filter(ResourceType.name == name)
            .first()
        )

        if not item:
            return False

        item.status = "已通过"

        db.commit()

        return True

    except Exception:
        db.rollback()
        return False


# =========================
# core: AI结果落库入口
# =========================

def save_ai_generated_resources(
    db: Session,
    resource_plan: dict,
    llm_outputs: list,
    uploader: str = "AI-Agent"
):
    resources = []

    for index, plan_item in enumerate(resource_plan.get("resources", [])):
        llm_item = llm_outputs[index] if index < len(llm_outputs) else {}
        title = plan_item.get("title") or plan_item.get("topic") or "未命名资源"
        resources.append({
            "title": title,
            "type": plan_item.get("type", "专业课程讲解文档"),
            "summary": llm_item.get("summary") or plan_item.get("summary", ""),
            "content": llm_item.get("content") or plan_item.get("content", ""),
            "source": llm_item.get("source") or plan_item.get("source", ""),
            "agent_notes": plan_item.get("agent_notes", str(plan_item)),
        })

    return insert_generated_resources(db, resources, uploader=uploader)


def insert_generated_resources(
    db: Session,
    resources: list,
    uploader: str = "资源生成 Agent"
):
    inserted = []

    try:
        for item in resources:
            title = (item.get("title") or "").strip()
            r_type = (item.get("type") or "").strip()
            if not title or not r_type or _is_deprecated_resource_type(r_type):
                continue

            existing = (
                db.query(Resource)
                .filter(Resource.title == title, Resource.type == r_type)
                .first()
            )

            if existing:
                existing.summary = item.get("summary", existing.summary or "")
                existing.content = item.get("content", existing.content or "")
                existing.source = item.get("source", existing.source or "")
                existing.agent_notes = item.get("agent_notes", existing.agent_notes or "")
                existing.uploader = uploader
                existing.status = "待审核"
                existing.time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                inserted.append(_resource_to_dict(existing))
                continue

            resource = Resource(
                id=_new_resource_id(),
                title=title,
                type=r_type,
                status="待审核",
                uploader=uploader,
                time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                summary=item.get("summary", ""),
                content=item.get("content", ""),
                source=item.get("source", ""),
                agent_notes=item.get("agent_notes", "")
            )

            db.add(resource)
            db.flush()
            inserted.append(_resource_to_dict(resource))

        db.commit()
        return inserted

    except Exception:
        db.rollback()
        return []


# =========================
# CRUD
# =========================

def insert_new_resource(
    db: Session,
    title: str,
    r_type: str,
    summary: str = "",
    content: str = "",
    source: str = "",
    agent_notes: str = "",
    uploader: str = "student"
):

    try:

        resource = Resource(
            id=_new_resource_id(),

            title=title,

            type=r_type,

            status="待审核",

            uploader=uploader,

            time=datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            summary=summary,

            content=content,

            source=source,

            agent_notes=agent_notes
        )

        db.add(resource)

        db.commit()

        db.refresh(resource)

        return {
    "success": True,
    "data": _resource_to_dict(resource)
}

    except Exception:

        db.rollback()

        return None


def approve_resource(
    db: Session,
    resource_id: str
):

    try:

        r = (
            db.query(Resource)
            .filter(Resource.id == resource_id)
            .first()
        )

        if not r:
            return False

        r.status = "已通过"

        db.commit()

        return True

    except Exception:

        db.rollback()

        return False


def reject_resource(
    db: Session,
    resource_id: str
):

    try:

        r = (
            db.query(Resource)
            .filter(Resource.id == resource_id)
            .first()
        )

        if not r:
            return False

        db.delete(r)

        db.commit()

        return True

    except Exception:

        db.rollback()

        return False
