#!/usr/bin/env python3
"""Check Deep Learning v2 course base completeness."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COURSE_DIR = ROOT / "data" / "knowledge_base" / "deep_learning_v2"
REQUIRED = ["main_note.md", "mind_map.mmd", "exercises.md", "reading_video_guide.md"]
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


def main() -> int:
    errors = []
    manifest_path = COURSE_DIR / "course_manifest.json"
    index_path = COURSE_DIR / "chapter_resource_index.json"
    units_path = COURSE_DIR / "knowledge_units.jsonl"
    evidence_path = COURSE_DIR / "evidence" / "evidence_chunks.jsonl"
    for path in [manifest_path, index_path, units_path, evidence_path]:
        if not path.exists():
            errors.append(f"missing {path}")

    chapters = []
    if index_path.exists():
        chapters = json.loads(index_path.read_text(encoding="utf-8"))
    if len(chapters) != 12:
        errors.append(f"expected 12 chapters, got {len(chapters)}")

    for chapter in chapters:
        chapter_id = chapter.get("chapter_id")
        chapter_dir = COURSE_DIR / "courseware" / chapter_id
        for filename in REQUIRED:
            if not (chapter_dir / filename).exists():
                errors.append(f"{chapter_id} missing {filename}")
        if chapter_id in CORE_CHAPTERS and not (chapter_dir / "code_lab.md").exists():
            errors.append(f"{chapter_id} missing core code_lab.md")

    unit_count = 0
    if units_path.exists():
        unit_count = sum(1 for line in units_path.read_text(encoding="utf-8").splitlines() if line.strip())
    if not 60 <= unit_count <= 100:
        errors.append(f"expected 60-100 knowledge units, got {unit_count}")

    if errors:
        print("Deep Learning v2 completeness check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Deep Learning v2 completeness check passed: {len(chapters)} chapters, {unit_count} units.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
