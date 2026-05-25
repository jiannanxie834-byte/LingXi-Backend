# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./lingxi.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# =========================
# FastAPI依赖注入
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# 初始化数据库
# =========================
def init_db():
    from app.models.schemas import (
        User,
        Resource,
        ResourceType,
        LearningPlan,
        EvaluationRecord,
        TodoList,
        Feedback
    )

    Base.metadata.create_all(bind=engine)