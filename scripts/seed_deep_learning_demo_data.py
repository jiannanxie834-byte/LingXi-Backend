from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import SessionLocal, init_db
from app.services.data_services.demo_seed_service import seed_demo_base_data


def main():
    init_db()
    db = SessionLocal()
    try:
        result = seed_demo_base_data(db, reset_demo_scope=True)
        print(result)
        if not result.get("success"):
            raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
