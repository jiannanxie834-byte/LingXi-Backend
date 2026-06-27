import unittest
from pathlib import Path

from app.services.data_services import deep_learning_course_map_service as course_map
from app.services.data_services import course_scope_service


COURSE_DIR = Path(__file__).resolve().parents[1] / "data" / "knowledge_base" / "deep_learning"


class DeepLearningCourseMapTest(unittest.TestCase):
    def test_course_map_has_fine_grained_units(self):
        units = course_map.list_units()
        unit_ids = {item["unit_id"] for item in units}

        self.assertGreaterEqual(len(units), 40)
        for unit_id in [
            "dl_lstm_cell",
            "dl_lstm_forget_gate",
            "dl_cnn_output_size",
            "dl_multihead_attention",
            "dl_project_image_classification",
        ]:
            self.assertIn(unit_id, unit_ids)

    def test_lstm_hits_dedicated_unit(self):
        result = course_map.match_deep_learning_topic("LSTM", "我想学习 LSTM")

        self.assertTrue(result["matched"])
        self.assertEqual(result["unit_id"], "dl_lstm_cell")

    def test_forget_gate_hits_micro_unit(self):
        result = course_map.match_deep_learning_topic("LSTM 遗忘门", "我不懂遗忘门")

        self.assertTrue(result["matched"])
        self.assertEqual(result["unit_id"], "dl_lstm_forget_gate")

    def test_cnn_output_size_hits_specific_unit(self):
        result = course_map.match_deep_learning_topic(
            "CNN 输出特征图尺寸计算",
            "我做 CNN 练习题时总是算错输出特征图尺寸。",
        )

        self.assertTrue(result["matched"])
        self.assertEqual(result["unit_id"], "dl_cnn_output_size")

    def test_multihead_attention_hits_specific_unit(self):
        result = course_map.match_deep_learning_topic("多头注意力", "多头注意力是什么")

        self.assertTrue(result["matched"])
        self.assertEqual(result["unit_id"], "dl_multihead_attention")

    def test_project_request_hits_project_unit(self):
        result = course_map.match_deep_learning_topic("CNN 图像分类项目", "我想做图像分类项目")

        self.assertTrue(result["matched"])
        self.assertEqual(result["unit_id"], "dl_project_image_classification")

    def test_out_of_course_reply_is_fixed(self):
        reply = course_scope_service.build_out_of_scope_reply("英语", "我想学习英语")

        self.assertEqual(reply, "本系统聚焦《深度学习》课程，「英语」暂未纳入课程图谱，请期待后续资源完善哦。")

    def test_core_chapters_are_rag_ready(self):
        rnn_content = (COURSE_DIR / "chapters" / "08_rnn_lstm.md").read_text(encoding="utf-8")

        self.assertGreater(len(rnn_content), 3000)
        for marker in [
            "BPTT",
            "梯度消失",
            "长期依赖",
            "细胞状态",
            "隐藏状态",
            "遗忘门",
            "输入门",
            "输出门",
            "nn.LSTM",
            "自测题与答案",
        ]:
            self.assertIn(marker, rnn_content)

    def test_labs_are_registered_and_sufficient(self):
        labs = list((COURSE_DIR / "labs").glob("*.py"))
        lab_names = {path.name for path in labs}

        self.assertGreaterEqual(len(labs), 8)
        for name in [
            "lstm_sequence_classification.py",
            "gru_sequence_classification.py",
            "optimizer_comparison.py",
            "regularization_dropout_bn_demo.py",
            "cnn_output_shape_debug.py",
        ]:
            self.assertIn(name, lab_names)


if __name__ == "__main__":
    unittest.main()
