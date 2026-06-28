import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import load_env_file


load_env_file()

# 数据库连接配置：默认使用 SQLite；部署时可在 .env 中切换为 MySQL/PostgreSQL 等 SQLAlchemy URL。
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lingxi.db").strip() or "sqlite:///./lingxi.db"


def _is_sqlite_url(database_url: str):
    return database_url.startswith("sqlite")


def _build_engine_kwargs(database_url: str):
    kwargs = {
        "pool_pre_ping": True,
    }

    if _is_sqlite_url(database_url):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_recycle"] = 3600

    return kwargs

engine = create_engine(DATABASE_URL, **_build_engine_kwargs(DATABASE_URL))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

RESOURCE_EXTRA_COLUMNS = {
    "applicant_username": {
        "default": "VARCHAR(64) DEFAULT ''",
    },
    "summary": {
        "default": "TEXT",
        "sqlite": "TEXT DEFAULT ''",
    },
    "content": {
        "default": "TEXT",
        "sqlite": "TEXT DEFAULT ''",
    },
    "source": {
        "default": "VARCHAR(255) DEFAULT ''",
    },
    "agent_notes": {
        "default": "TEXT",
        "sqlite": "TEXT DEFAULT ''",
    },
    "review_comment": {
        "default": "TEXT",
        "sqlite": "TEXT DEFAULT ''",
    },
    "reviewed_at": {
        "default": "VARCHAR(32) DEFAULT ''",
    },
}

RESOURCE_TYPE_EXTRA_COLUMNS = {
    "applicant_username": {
        "default": "VARCHAR(64) DEFAULT ''",
    },
    "reason": {
        "default": "TEXT",
        "sqlite": "TEXT DEFAULT ''",
    },
    "review_comment": {
        "default": "TEXT",
        "sqlite": "TEXT DEFAULT ''",
    },
    "reviewed_at": {
        "default": "VARCHAR(32) DEFAULT ''",
    },
}

EVALUATION_RECORD_EXTRA_COLUMNS = {
    "course_id": {
        "default": "VARCHAR(64) DEFAULT 'data_structures_algorithms'",
    },
    "chapter_id": {
        "default": "VARCHAR(64) DEFAULT ''",
    },
    "section_id": {
        "default": "VARCHAR(64) DEFAULT ''",
    },
    "unit_ids_json": {
        "default": "TEXT",
        "sqlite": "TEXT DEFAULT '[]'",
    },
    "evidence_refs_json": {
        "default": "TEXT",
        "sqlite": "TEXT DEFAULT '[]'",
    },
    "diagnosis_type": {
        "default": "VARCHAR(64) DEFAULT 'manual'",
    },
}

RESOURCE_ARTIFACT_EXTRA_COLUMNS = {
    "chapter_id": {
        "default": "VARCHAR(64) DEFAULT ''",
    },
    "section_id": {
        "default": "VARCHAR(64) DEFAULT ''",
    },
}


def _existing_columns(conn, table_name: str):
    inspector = inspect(conn)
    if not inspector.has_table(table_name):
        return set()

    return {column["name"] for column in inspector.get_columns(table_name)}


def _dialect_column_sql(column_sql: dict):
    return column_sql.get(engine.dialect.name) or column_sql["default"]


def init_schema_migrations():
    """补齐已有表的新字段。create_all 只会建新表，不会自动修改旧表结构。"""
    with engine.begin() as conn:
        resource_columns = _existing_columns(conn, "resources")
        for column_name, column_sql in RESOURCE_EXTRA_COLUMNS.items():
            if column_name not in resource_columns:
                conn.execute(text(
                    f"ALTER TABLE resources ADD COLUMN {column_name} {_dialect_column_sql(column_sql)}"
                ))

        for column_name in RESOURCE_EXTRA_COLUMNS:
            conn.execute(text(
                f"UPDATE resources SET {column_name} = '' WHERE {column_name} IS NULL"
            ))

        if resource_columns and "applicant_username" in _existing_columns(conn, "resources"):
            conn.execute(text(
                "UPDATE resources SET applicant_username = uploader "
                "WHERE (applicant_username IS NULL OR applicant_username = '') "
                "AND uploader NOT IN ('system', '课程知识库种子', '资源生成 Agent', '学习评价 Agent')"
            ))

        user_columns = _existing_columns(conn, "users")
        if "nickname" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN nickname VARCHAR(64) DEFAULT ''"))
        conn.execute(text("UPDATE users SET nickname = username WHERE nickname IS NULL OR nickname = ''"))
        if {"bio", "tags"}.issubset(_existing_columns(conn, "users")):
            conn.execute(text(
                "UPDATE users SET "
                "bio = '正在学习《数据结构与算法》课程，重点关注复杂度分析、二分边界与动态规划', "
                "tags = '数据结构与算法,复杂度分析,二分查找,动态规划' "
                "WHERE username IN ('student', 'demo_basic') "
                "AND 1 = 0"
            ))

        chat_message_columns = _existing_columns(conn, "chat_messages")
        if chat_message_columns and "metadata_json" not in chat_message_columns:
            conn.execute(text("ALTER TABLE chat_messages ADD COLUMN metadata_json TEXT"))
        if chat_message_columns:
            conn.execute(text("UPDATE chat_messages SET metadata_json = '{}' WHERE metadata_json IS NULL OR metadata_json = ''"))

        chat_session_columns = _existing_columns(conn, "chat_sessions")
        if chat_session_columns and "last_topic" not in chat_session_columns:
            conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN last_topic VARCHAR(255) DEFAULT ''"))
        if chat_session_columns and "state_json" not in chat_session_columns:
            state_column_sql = "TEXT DEFAULT '{}'" if engine.dialect.name == "sqlite" else "TEXT"
            conn.execute(text(f"ALTER TABLE chat_sessions ADD COLUMN state_json {state_column_sql}"))
        if chat_session_columns:
            conn.execute(text("UPDATE chat_sessions SET last_topic = '' WHERE last_topic IS NULL"))
            if "state_json" in _existing_columns(conn, "chat_sessions"):
                conn.execute(text("UPDATE chat_sessions SET state_json = '{}' WHERE state_json IS NULL OR state_json = ''"))

        resource_type_columns = _existing_columns(conn, "resource_types")
        for column_name, column_sql in RESOURCE_TYPE_EXTRA_COLUMNS.items():
            if resource_type_columns and column_name not in resource_type_columns:
                conn.execute(text(
                    f"ALTER TABLE resource_types ADD COLUMN {column_name} {_dialect_column_sql(column_sql)}"
                ))

        for column_name in RESOURCE_TYPE_EXTRA_COLUMNS:
            if column_name in _existing_columns(conn, "resource_types"):
                conn.execute(text(
                    f"UPDATE resource_types SET {column_name} = '' WHERE {column_name} IS NULL"
                ))

        evaluation_columns = _existing_columns(conn, "evaluation_records")
        for column_name, column_sql in EVALUATION_RECORD_EXTRA_COLUMNS.items():
            if evaluation_columns and column_name not in evaluation_columns:
                conn.execute(text(
                    f"ALTER TABLE evaluation_records ADD COLUMN {column_name} {_dialect_column_sql(column_sql)}"
                ))
        if evaluation_columns:
            if "course_id" in _existing_columns(conn, "evaluation_records"):
                conn.execute(text(
                    "UPDATE evaluation_records SET course_id = 'data_structures_algorithms' "
                    "WHERE course_id IS NULL OR course_id = ''"
                ))
            for column_name in ["chapter_id", "section_id"]:
                if column_name in _existing_columns(conn, "evaluation_records"):
                    conn.execute(text(f"UPDATE evaluation_records SET {column_name} = '' WHERE {column_name} IS NULL"))
            for column_name in ["unit_ids_json", "evidence_refs_json"]:
                if column_name in _existing_columns(conn, "evaluation_records"):
                    conn.execute(text(f"UPDATE evaluation_records SET {column_name} = '[]' WHERE {column_name} IS NULL OR {column_name} = ''"))
            if "diagnosis_type" in _existing_columns(conn, "evaluation_records"):
                conn.execute(text("UPDATE evaluation_records SET diagnosis_type = 'manual' WHERE diagnosis_type IS NULL OR diagnosis_type = ''"))

        artifact_columns = _existing_columns(conn, "resource_artifacts")
        for column_name, column_sql in RESOURCE_ARTIFACT_EXTRA_COLUMNS.items():
            if artifact_columns and column_name not in artifact_columns:
                conn.execute(text(
                    f"ALTER TABLE resource_artifacts ADD COLUMN {column_name} {_dialect_column_sql(column_sql)}"
                ))
        if artifact_columns:
            if "course_id" in _existing_columns(conn, "resource_artifacts"):
                conn.execute(text(
                    "UPDATE resource_artifacts SET course_id = 'data_structures_algorithms' "
                    "WHERE course_id IS NULL OR course_id = ''"
                ))
            for column_name in ["chapter_id", "section_id"]:
                if column_name in _existing_columns(conn, "resource_artifacts"):
                    conn.execute(text(f"UPDATE resource_artifacts SET {column_name} = '' WHERE {column_name} IS NULL"))

def get_db():
    """FastAPI 专属依赖项：每次请求自动创建数据库连接，用完自动关闭防止死锁"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_seeding_data():
    """Initialize default demo accounts when the user table is empty."""
    db = SessionLocal()
    from app.models.schemas import User
    
    try:
        exist_user = db.query(User).first()
        if not exist_user:
            print("Empty database detected; creating default admin and student accounts.")
            
            admin_user = User(
                username="admin",
                nickname="管理员",
                password="123456",  # 比赛演示用简易明文，后期可加加密
                role="admin",
                avatar="",
                bio="全站最高权限智能系统控制枢纽",
                hours=999,
                tags="系统管理,架构师"
            )
            
            student_user = User(
                username="student",
                nickname="学生用户",
                password="123456",
                role="student",
                avatar="",
                bio="正在学习《数据结构与算法》课程，重点关注复杂度分析、二分边界与动态规划",
                hours=15,
                tags="数据结构与算法,复杂度分析,二分查找,动态规划"
            )
            
            db.add(admin_user)
            db.add(student_user)
            db.commit()
            print("Default accounts created: admin / student.")
        else:
            print("Existing database detected; skipping default account initialization.")
    except Exception as e:
        print(f"Default account initialization failed: {e}")
        db.rollback()
    finally:
        db.close()
