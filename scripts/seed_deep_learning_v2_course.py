#!/usr/bin/env python3
"""Seed the curated Deep Learning v2 course base into the database."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import SessionLocal, init_db
from app.services.data_services.knowledge_seed_service import seed_initial_course_knowledge_base


def _run_check(script_name: str) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / script_name)],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if result.returncode != 0:
        raise SystemExit(f"{script_name} failed; refuse to seed Deep Learning v2 course base.")


def main() -> None:
    _run_check("check_deep_learning_v2_completeness.py")
    _run_check("audit_deep_learning_v2_quality.py")
    init_db()
    db = SessionLocal()
    try:
        result = seed_initial_course_knowledge_base(db)
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
