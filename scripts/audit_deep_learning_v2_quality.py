#!/usr/bin/env python3
"""Audit Deep Learning v2 courseware quality before seeding."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COURSE_DIR = ROOT / "data" / "knowledge_base" / "deep_learning_v2"
CORE_CHAPTERS = {
    "chapter_03_neural_network_basics",
    "chapter_04_deep_network_and_backprop",
    "chapter_05_regularization_and_generalization",
    "chapter_06_optimization",
    "chapter_07_cnn_foundation",
    "chapter_08_cnn_architectures_and_cv_practice",
    "chapter_10_sequence_models",
    "chapter_11_attention_transformer",
}


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _count_questions(markdown: str) -> int:
    return len(re.findall(r"^##\s+\d+\.", markdown, flags=re.M))


def main() -> int:
    errors = []
    warnings = []
    index_path = COURSE_DIR / "chapter_resource_index.json"
    chapters = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    evidence = {item.get("evidence_id") for item in _read_jsonl(COURSE_DIR / "evidence" / "evidence_chunks.jsonl")}
    units = _read_jsonl(COURSE_DIR / "knowledge_units.jsonl")

    for chapter in chapters:
        chapter_id = chapter.get("chapter_id")
        chapter_dir = COURSE_DIR / "courseware" / chapter_id
        note_path = chapter_dir / "main_note.md"
        exercises_path = chapter_dir / "exercises.md"
        note = note_path.read_text(encoding="utf-8") if note_path.exists() else ""
        exercises = exercises_path.read_text(encoding="utf-8") if exercises_path.exists() else ""
        min_chars = 6000 if chapter_id in CORE_CHAPTERS else 4000
        min_questions = 12 if chapter_id in CORE_CHAPTERS else 8
        if len(note) < min_chars:
            errors.append(f"{chapter_id} main_note too short: {len(note)} < {min_chars}")
        if note.count("## ") < 10:
            errors.append(f"{chapter_id} main_note has fewer than 10 h2 sections")
        if _count_questions(exercises) < min_questions:
            errors.append(f"{chapter_id} exercises too few: {_count_questions(exercises)} < {min_questions}")
        if "初始知识点资源卡" in note:
            errors.append(f"{chapter_id} still contains shallow resource-card wording")

    for unit in units:
        refs = unit.get("evidence_refs") or []
        if not refs:
            errors.append(f"{unit.get('unit_id')} has no evidence_refs")
        for ref in refs:
            if ref not in evidence:
                errors.append(f"{unit.get('unit_id')} references missing evidence {ref}")
        if not unit.get("chapter_id") or not unit.get("title"):
            errors.append(f"invalid unit: {unit}")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    if errors:
        print("Deep Learning v2 quality audit failed:")
        for error in errors[:120]:
            print(f"- {error}")
        if len(errors) > 120:
            print(f"... {len(errors) - 120} more")
        return 1
    print(f"Deep Learning v2 quality audit passed: {len(chapters)} chapters, {len(units)} units, {len(evidence)} evidence chunks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
