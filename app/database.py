# app/database.py

from app.models.base import (
    Base,
    SessionLocal,
    engine,
    get_db,
    init_schema_migrations,
    init_seeding_data,
)


def init_db():
    from app.models import schemas  # noqa: F401
    from app.services.data_services.knowledge_seed_service import seed_initial_course_knowledge_base

    Base.metadata.create_all(bind=engine)
    init_schema_migrations()
    init_seeding_data()
    db = SessionLocal()
    try:
        result = seed_initial_course_knowledge_base(db)
        if result.get("success"):
            print(
                f"Initial course knowledge base synced: {result.get('course')}; "
                f"{result.get('knowledge_points')} knowledge points, "
                f"{result.get('resources')} resources."
            )
        else:
            print(f"Initial course knowledge base sync failed: {result.get('message')}")
    finally:
        db.close()
