import unittest

from app.services.data_services import knowledge_seed_service


class KnowledgeSeedServiceTest(unittest.TestCase):
    def test_seed_loads_fine_grained_units(self):
        units = knowledge_seed_service._load_knowledge_units()
        unit_ids = {item["unit_id"] for item in units}

        self.assertGreaterEqual(len(units), 70)
        self.assertIn("dl_lstm_cell", unit_ids)
        self.assertIn("dl_cnn_output_size", unit_ids)
        self.assertIn("dl_multihead_attention", unit_ids)

    def test_units_expand_course_knowledge_points(self):
        units = knowledge_seed_service._load_knowledge_units()
        points = knowledge_seed_service._knowledge_points_from_units(units)
        topics = {item["topic"] for item in points}

        self.assertGreaterEqual(len(points), 70)
        self.assertIn("LSTM 长短期记忆网络", topics)
        self.assertIn("CNN 输出特征图尺寸计算", topics)
        self.assertIn("多头注意力", topics)

    def test_units_expand_initial_resource_documents(self):
        units = knowledge_seed_service._load_knowledge_units()
        docs = knowledge_seed_service._unit_resource_documents(units)
        ids = {item["id"] for item in docs}
        titles = {item["title"] for item in docs}
        lstm_doc = next(item for item in docs if item["unit_id"] == "dl_lstm_cell")

        self.assertGreaterEqual(len(docs), 70)
        self.assertEqual(len(ids), len(docs))
        self.assertIn("LSTM 长短期记忆网络 · 初始知识点资源卡", titles)
        self.assertIn("evidence_id: dl_lstm_cell", lstm_doc["content"])


if __name__ == "__main__":
    unittest.main()
