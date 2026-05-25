import json
from sqlalchemy.orm import Session
from app.models.schemas import CourseKnowledge


def get_course_knowledge(db: Session):
    """获取课程知识库"""

    try:
        rows = db.query(CourseKnowledge).all()

        return [
            {
                "topic": r.topic,
                "keywords": json.loads(r.keywords or "[]"),
                "chapter": r.chapter,
                "core": r.core,
                "pitfalls": json.loads(r.pitfalls or "[]"),
                "practice": r.practice,
                "practice_kind": r.practice_kind,
                "practice_output": r.practice_output,
                "code_lang": r.code_lang,
                "code": r.code,
            }
            for r in rows
        ]

    except Exception:
        return []

# =========================
# 新增知识点
# =========================
def insert_course_knowledge(db: Session, data: dict):
    try:
        item = CourseKnowledge(
            topic=data["topic"],
            keywords=json.dumps(data.get("keywords", []), ensure_ascii=False),
            chapter=data.get("chapter", ""),
            core=data.get("core", ""),
            pitfalls=json.dumps(data.get("pitfalls", []), ensure_ascii=False),
            practice=data.get("practice", ""),
            practice_kind=data.get("practice_kind", "coding"),
            practice_output=data.get("practice_output", ""),
            code_lang=data.get("code_lang"),
            code=data.get("code"),
        )

        db.add(item)
        db.commit()
        db.refresh(item)

        return {
            "success": True,
            "topic": item.topic
        }

    except Exception:
        db.rollback()
        return False