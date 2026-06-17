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

        user_columns = _existing_columns(conn, "users")
        if "nickname" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN nickname VARCHAR(64) DEFAULT ''"))
        conn.execute(text("UPDATE users SET nickname = username WHERE nickname IS NULL OR nickname = ''"))

        chat_message_columns = _existing_columns(conn, "chat_messages")
        if chat_message_columns and "metadata_json" not in chat_message_columns:
            conn.execute(text("ALTER TABLE chat_messages ADD COLUMN metadata_json TEXT"))
        if chat_message_columns:
            conn.execute(text("UPDATE chat_messages SET metadata_json = '{}' WHERE metadata_json IS NULL OR metadata_json = ''"))

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
                bio="正在跟随黑马程序员攻克 IHRM 人力资源管理系统的前端架构师",
                hours=15,
                tags="Vue3,Element Plus,后端,Python"
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
