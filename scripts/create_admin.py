from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import SessionLocal, init_db
from app.models.schemas import User


def main():
    init_db()
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(username="admin")
            db.add(admin)

        admin.nickname = "管理员"
        admin.password = "123456"
        admin.role = "admin"
        admin.avatar = admin.avatar or ""
        admin.bio = "系统管理员"
        admin.hours = admin.hours or 999
        admin.tags = "系统管理,资源审核"

        db.commit()
        print("管理员账号已就绪：admin / 123456")
    except Exception as exc:
        db.rollback()
        print(f"管理员账号创建失败：{exc}")
        raise SystemExit(1) from exc
    finally:
        db.close()


if __name__ == "__main__":
    main()
