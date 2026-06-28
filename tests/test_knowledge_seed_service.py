import unittest

from app.services.data_services import knowledge_seed_service


class KnowledgeSeedServiceTest(unittest.TestCase):
    def test_seed_loads_fine_grained_units(self):
        units = knowledge_seed_service._load_knowledge_units()
        unit_ids = {item["unit_id"] for item in units}

        self.assertGreaterEqual(len(units), 70)
        self.assertIn("dsa_binary_search_complexity", unit_ids)
        self.assertIn("dsa_hash_table", unit_ids)
        self.assertIn("dsa_dp_intro", unit_ids)

    def test_units_expand_course_knowledge_points(self):
        units = knowledge_seed_service._load_knowledge_units()
        points = knowledge_seed_service._knowledge_points_from_units(units)
        topics = {item["topic"] for item in points}

        self.assertGreaterEqual(len(points), 70)
        self.assertIn("二分查找复杂度", topics)
        self.assertIn("哈希表", topics)
        self.assertIn("动态规划基本思想", topics)

    def test_units_do_not_create_unit_level_placeholder_resources(self):
        units = knowledge_seed_service._load_knowledge_units()
        docs = knowledge_seed_service._unit_resource_documents(units)

        self.assertEqual(docs, [])


if __name__ == "__main__":
    unittest.main()
