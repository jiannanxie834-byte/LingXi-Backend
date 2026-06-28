import json
import unittest
from pathlib import Path


COURSE_DIR = Path(__file__).resolve().parents[1] / "data" / "knowledge_base" / "data_structures_algorithms"


class DsaSeedFrameworkTest(unittest.TestCase):
    def test_skeleton_files_exist(self):
        self.assertTrue((COURSE_DIR / "course_manifest.json").exists())
        self.assertTrue((COURSE_DIR / "course_tree.json").exists())
        self.assertTrue((COURSE_DIR / "chapter_resource_index.json").exists())
        self.assertTrue((COURSE_DIR / "knowledge_units.jsonl").exists())
        self.assertTrue((COURSE_DIR / "blueprints" / "course_note_blueprint.json").exists())
        self.assertTrue((COURSE_DIR / "policies" / "resource_generation_policy.json").exists())

    def test_chapter_index_and_units_are_aligned(self):
        chapter_index = json.loads((COURSE_DIR / "chapter_resource_index.json").read_text(encoding="utf-8"))
        self.assertEqual(len(chapter_index), 12)
        course_tree = json.loads((COURSE_DIR / "course_tree.json").read_text(encoding="utf-8"))
        self.assertEqual(len(course_tree["chapters"]), 12)
        self.assertTrue(all(len(chapter.get("sections", [])) >= 5 for chapter in course_tree["chapters"]))
        units = [
            json.loads(line)
            for line in (COURSE_DIR / "knowledge_units.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertGreaterEqual(len(units), 60)
        self.assertTrue(all(unit.get("chapter_id") and unit.get("section_id") for unit in units))
        chapter_dir = COURSE_DIR / "courseware" / "chapter_01_complexity"
        for subdir in ["sections", "resources", "banks", "indexes", "metadata"]:
            self.assertTrue((chapter_dir / subdir).is_dir())
        self.assertTrue((chapter_dir / "indexes" / "section_resource_map.json").exists())
        self.assertFalse((COURSE_DIR / "animations").exists())
        self.assertFalse((COURSE_DIR / "blueprints" / "visual_animation_blueprint.json").exists())
        self.assertFalse((chapter_dir / "banks" / "animations.jsonl").exists())
        self.assertFalse((chapter_dir / "resources" / "visual_animation.json").exists())

    def test_dsa_framework_does_not_reference_animation_modules(self):
        forbidden = [
            "visual_animation",
            "interactive_animation",
            "animations.jsonl",
            "visual_animation.json",
            "animation_refs",
            "animation_filters",
            "visual_animation_refs",
        ]
        files = [
            COURSE_DIR / "chapter_resource_index.json",
            COURSE_DIR / "policies" / "resource_generation_policy.json",
        ]
        files.extend((COURSE_DIR / "courseware").glob("chapter_*/chapter_manifest.json"))
        files.extend((COURSE_DIR / "courseware").glob("chapter_*/indexes/section_resource_map.json"))
        files.append(COURSE_DIR / "knowledge_units.jsonl")
        for path in files:
            text = path.read_text(encoding="utf-8")
            for word in forbidden:
                self.assertNotIn(word, text, f"{path} should not contain {word}")


if __name__ == "__main__":
    unittest.main()
