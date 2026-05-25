import datetime
import uuid

from sqlalchemy.orm import Session

from app.models.schemas import (
    Resource,
    ResourceType
)


# =========================
# tools
# =========================

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
        ]

    except Exception:
        return []


# =========================
# 分类
# =========================

def get_all_resource_types(db: Session):

    try:

        types = db.query(ResourceType).all()

        return [
            {
                "id": t.id,
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

        return [
            {
                "id": t.id,
                "name": t.name
            }
            for t in types
        ]

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

        item = ResourceType(
            id=str(uuid.uuid4()),
            name=name,
            status="待审核"
        )

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

    inserted = []

    try:

        for plan_item, llm_item in zip(
            resource_plan["resources"],
            llm_outputs
        ):

            res = Resource(
                id=f"RES{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}",

                title=plan_item.get(
                    "topic",
                    "未命名资源"
                ),

                type=plan_item.get(
                    "type",
                    "文档"
                ),

                status="已生成",

                summary=llm_item.get(
                    "summary",
                    ""
                ),

                content=llm_item.get(
                    "content",
                    ""
                ),

                source=llm_item.get(
                    "source",
                    ""
                ),

                uploader=uploader,

                time=datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                agent_notes=str(plan_item)
            )

            db.add(res)

            db.flush()

            inserted.append(
                _resource_to_dict(res)
            )

        db.commit()

        return {
    "success": True,
    "data": inserted
}

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
            id=f"RES{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}",

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