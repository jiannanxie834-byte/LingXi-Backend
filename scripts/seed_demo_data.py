from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.models import schemas  # noqa: F401
from app.models.base import Base, engine, SessionLocal
from app.services.data_services.knowledge_seed_service import seed_initial_course_knowledge_base


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = seed_initial_course_knowledge_base(db)
        print(result)
        if not result.get("success"):
            raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
