import unittest

from app.services.data_services import dsa_course_map_service as course_map


class DsaCourseMapTest(unittest.TestCase):
    def test_course_has_12_chapters_and_units(self):
        payload = course_map.course_map_payload()
        self.assertEqual(payload["course_id"], "data_structures_algorithms")
        self.assertEqual(len(payload["chapters"]), 12)
        self.assertGreaterEqual(len(course_map.list_units()), 60)

    def test_match_core_topics(self):
        result = course_map.match_dsa_topic("动态规划", "我想学习动态规划")
        self.assertTrue(result["matched"])
        self.assertEqual(result["course_id"], "data_structures_algorithms")
        self.assertIn("动态规划", result["chapter"])


if __name__ == "__main__":
    unittest.main()
