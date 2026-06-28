"""Seed the DSA framework placeholders without importing formal resources."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models import schemas  # noqa: F401
from app.models.base import Base, engine, SessionLocal
from app.services.data_services.dsa_framework_service import validate_framework_structure
from app.services.data_services.knowledge_seed_service import seed_initial_course_knowledge_base


def main() -> None:
    validation = validate_framework_structure()
    if not validation.get("ok"):
        issues = "\n".join(f"- {item}" for item in validation.get("issues", []))
        raise SystemExit(f"DSA framework structure is incomplete:\n{issues}")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = seed_initial_course_knowledge_base(db)
        if not result.get("success"):
            raise SystemExit(result.get("message") or "DSA framework seed failed.")
        print(
            "DSA framework placeholders synced: "
            f"{result.get('course')}; "
            f"{result.get('knowledge_points')} knowledge units, "
            f"{result.get('resources')} framework resources, "
            f"{result.get('video_resources')} video rows."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
