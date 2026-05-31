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

    Base.metadata.create_all(bind=engine)
    init_schema_migrations()
    init_seeding_data()
