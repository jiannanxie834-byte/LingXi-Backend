from app.database import SessionLocal, init_db
from app.services.data_services.knowledge_seed_service import seed_initial_course_knowledge_base


def main():
    init_db()
    db = SessionLocal()
    try:
        result = seed_initial_course_knowledge_base(db)
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
