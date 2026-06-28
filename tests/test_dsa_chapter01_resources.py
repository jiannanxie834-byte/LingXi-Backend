import json
import re
import unittest
from pathlib import Path


COURSE_DIR = Path(__file__).resolve().parents[1] / "data" / "knowledge_base" / "data_structures_algorithms"
CHAPTER_DIR = COURSE_DIR / "courseware" / "chapter_01_complexity"
CHAPTER_ID = "chapter_01_complexity"


def _jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _compact_len(path: Path) -> int:
    return len(re.sub(r"\s+", "", path.read_text(encoding="utf-8")))


class DsaChapter01ResourcesTest(unittest.TestCase):
    def test_chapter_01_has_required_six_sections(self):
        expected_files = [
            "01_algorithm_program_input_size.md",
            "02_time_complexity_big_o.md",
            "03_common_complexities_growth.md",
            "04_loop_analysis.md",
            "05_space_complexity_case_analysis.md",
            "06_search_and_recursion_cases.md",
        ]
        actual_files = sorted(path.name for path in (CHAPTER_DIR / "sections").glob("*.md"))
        self.assertEqual(actual_files, expected_files)
        for filename in expected_files:
            length = _compact_len(CHAPTER_DIR / "sections" / filename)
            self.assertGreaterEqual(length, 400)
            self.assertLessEqual(length, 750)

    def test_chapter_01_resource_counts_and_no_forbidden_references(self):
        self.assertTrue((CHAPTER_DIR / "resources" / "chapter_overview.md").exists())
        self.assertFalse((CHAPTER_DIR / "resources" / "main_note.md").exists())
        self.assertEqual(len(_jsonl(CHAPTER_DIR / "banks" / "exercises.jsonl")), 8)
        self.assertEqual(len(_jsonl(CHAPTER_DIR / "banks" / "code_tasks.jsonl")), 2)
        videos = _jsonl(CHAPTER_DIR / "banks" / "video_items.jsonl")
        self.assertTrue(all(item.get("status") == "ready" for item in videos))
        self.assertTrue(all(item.get("usage_policy") == "link_only" for item in videos))
        self.assertTrue(all(item.get("source_url") for item in videos))

        forbidden = [
            "TODO",
            "LeetCode",
            "main_note.md",
            "animations.jsonl",
            "visual_animation",
            "interactive_animation",
            "animation_refs",
        ]
        files = list(CHAPTER_DIR.rglob("*"))
        files.extend([COURSE_DIR / "chapter_resource_index.json", COURSE_DIR / "course_tree.json"])
        for path in files:
            if not path.is_file() or path.suffix not in {".json", ".jsonl", ".md", ".mmd"}:
                continue
            text = path.read_text(encoding="utf-8")
            for word in forbidden:
                self.assertNotIn(word, text, f"{path} should not contain {word}")

    def test_chapter_01_global_indexes_are_aligned(self):
        manifest = json.loads((CHAPTER_DIR / "chapter_manifest.json").read_text(encoding="utf-8"))
        section_map = json.loads((CHAPTER_DIR / "indexes" / "section_resource_map.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["sections"]), 6)
        self.assertEqual(set(section_map), {item["section_id"] for item in manifest["sections"]})

        tree = json.loads((COURSE_DIR / "course_tree.json").read_text(encoding="utf-8"))
        chapter = next(item for item in tree["chapters"] if item["chapter_id"] == CHAPTER_ID)
        self.assertEqual(len(chapter["sections"]), 6)

        chapter_index = json.loads((COURSE_DIR / "chapter_resource_index.json").read_text(encoding="utf-8"))
        entry = next(item for item in chapter_index if item["chapter_id"] == CHAPTER_ID)
        self.assertEqual(len(entry["section_resources"]), 6)
        self.assertEqual(entry["banks"], ["banks/exercises.jsonl", "banks/code_tasks.jsonl", "banks/video_items.jsonl"])

        evidence = [item for item in _jsonl(COURSE_DIR / "evidence" / "evidence_chunks.jsonl") if item.get("chapter_id") == CHAPTER_ID]
        self.assertGreaterEqual(len(evidence), 6)
        self.assertTrue(all(item.get("content_excerpt") for item in evidence))

        units = [item for item in _jsonl(COURSE_DIR / "knowledge_units.jsonl") if item.get("chapter_id") == CHAPTER_ID]
        unit_ids = [item["unit_id"] for item in units]
        self.assertEqual(len(unit_ids), len(set(unit_ids)))
        self.assertIn("dsa_case_analysis", unit_ids)
        self.assertIn("dsa_binary_search_complexity", unit_ids)


if __name__ == "__main__":
    unittest.main()
