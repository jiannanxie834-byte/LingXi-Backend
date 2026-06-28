"""Seed the Data Structures and Algorithms course framework placeholders."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models import schemas  # noqa: F401
from app.models.base import Base, engine, SessionLocal
from app.services.data_services.knowledge_seed_service import seed_initial_course_knowledge_base


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = seed_initial_course_knowledge_base(db)
        if not result.get("success"):
            raise SystemExit(result.get("message") or "DSA course framework seed failed.")
        print(
            "DSA course framework synced: "
            f"{result.get('course')}; "
            f"{result.get('knowledge_points')} knowledge units, "
            f"{result.get('resources')} placeholder resources."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
