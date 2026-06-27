import unittest

from app.agents.resource_agent import run as run_resource_agent
from app.services.data_services import resource_artifact_type_service as artifact_types
from app.services.data_services.topic_scope_resolver import resolve_topic_scope


class TopicScopeResolverTest(unittest.TestCase):
    def test_specific_lstm_question_stays_concept(self):
        result = resolve_topic_scope("LSTM 是什么")

        self.assertEqual(result["scope_level"], "concept")
        self.assertEqual(result["display_topic"], "LSTM 长短期记忆网络")
        self.assertEqual(result["primary_unit_id"], "dl_lstm_cell")
        self.assertFalse(result["should_generate_full_chapter"])

    def test_specific_lstm_learning_does_not_expand_to_chapter(self):
        result = resolve_topic_scope("我想学习 LSTM")

        self.assertEqual(result["scope_level"], "unit")
        self.assertEqual(result["display_topic"], "LSTM 长短期记忆网络")
        self.assertEqual(result["primary_unit_id"], "dl_lstm_cell")
        self.assertEqual(result["chapter_id"], "chapter_08_rnn_lstm")
        self.assertFalse(result["should_generate_full_chapter"])

    def test_full_chapter_marker_allows_chapter(self):
        result = resolve_topic_scope("我想系统学习 RNN LSTM GRU 整个章节")

        self.assertEqual(result["scope_level"], "chapter")
        self.assertEqual(result["display_topic"], "RNN、LSTM 与 GRU 序列建模")
        self.assertTrue(result["should_generate_full_chapter"])
        self.assertEqual(result["chapter_id"], "chapter_08_rnn_lstm")

    def test_course_level_request_does_not_expand_all_chapters(self):
        result = resolve_topic_scope("我想学习深度学习")

        self.assertEqual(result["scope_level"], "course")
        self.assertEqual(result["display_topic"], "《深度学习》课程导学")
        self.assertFalse(result["should_generate_full_chapter"])
        self.assertEqual(result["expansion_policy"], "course_diagnostic_and_path")

    def test_broad_sequence_model_request_is_chapter_scope(self):
        result = resolve_topic_scope("我想学习序列模型")

        self.assertEqual(result["scope_level"], "chapter")
        self.assertEqual(result["display_topic"], "RNN、LSTM 与 GRU 序列建模")
        self.assertEqual(result["expansion_policy"], "chapter_learning_path")
        self.assertTrue(result["should_generate_full_chapter"])

    def test_forget_gate_is_micro_concept(self):
        result = resolve_topic_scope("我不懂遗忘门")

        self.assertEqual(result["scope_level"], "concept")
        self.assertEqual(result["primary_unit_id"], "dl_lstm_forget_gate")
        self.assertEqual(result["display_topic"], "LSTM 遗忘门")
        self.assertEqual(result["expansion_policy"], "micro_explanation")

    def test_comparison_uses_explicit_topics(self):
        result = resolve_topic_scope("比较 CNN 和 Transformer 的区别")

        self.assertEqual(result["scope_level"], "comparison")
        self.assertEqual(result["display_topic"], "CNN 与 Transformer 对比学习")
        self.assertGreaterEqual(len(result["compare_units"]), 2)
        self.assertFalse(result["should_generate_full_chapter"])

    def test_same_unit_comparison_uses_explicit_aliases(self):
        result = resolve_topic_scope("LSTM 和 GRU 有什么区别")

        self.assertEqual(result["scope_level"], "comparison")
        self.assertEqual(result["display_topic"], "LSTM 与 GRU 对比学习")

    def test_project_request_is_project_scope(self):
        result = resolve_topic_scope("我想做一个 CNN 图像分类实验项目")

        self.assertEqual(result["scope_level"], "project")
        self.assertEqual(result["display_topic"], "CNN 图像分类项目")
        self.assertEqual(result["primary_unit_id"], "dl_project_image_classification")

    def test_cnn_output_size_hits_specific_unit(self):
        result = resolve_topic_scope("我做 CNN 练习题时总是算错输出特征图尺寸。")

        self.assertEqual(result["scope_level"], "unit")
        self.assertEqual(result["primary_unit_id"], "dl_cnn_output_size")
        self.assertEqual(result["display_topic"], "CNN 输出特征图尺寸计算")

    def test_multihead_attention_hits_specific_unit(self):
        result = resolve_topic_scope("多头注意力是什么")

        self.assertEqual(result["scope_level"], "concept")
        self.assertEqual(result["primary_unit_id"], "dl_multihead_attention")
        self.assertEqual(result["display_topic"], "多头注意力")

    def test_out_of_course_topic(self):
        result = resolve_topic_scope("我想学习法语")

        self.assertEqual(result["scope_level"], "out_of_course")
        self.assertEqual(result["display_topic"], "法语")
        self.assertFalse(result["should_generate_full_chapter"])


class ResourceAgentScopeTitleTest(unittest.TestCase):
    def test_resource_title_prefers_display_topic(self):
        scope = resolve_topic_scope("给我 LSTM 练习题")
        semantic_result = {
            **scope,
            "topic": scope["display_topic"],
            "normalized_topic": scope["display_topic"],
            "display_topic": scope["display_topic"],
            "subject_category": "computer_science",
            "learning_need_type": "practice",
            "course_id": "deep_learning",
            "unit_id": scope["primary_unit_id"],
            "deep_learning_course_map": scope["course_match"],
            "ai_course_map": scope["course_match"],
        }

        plan = run_resource_agent(
            {"title": "LSTM 练习"},
            {"topic": "LSTM", "level": "未确认"},
            semantic_result=semantic_result,
        )

        self.assertEqual([item["type"] for item in plan["resources"]], [artifact_types.EXERCISE_SET])
        self.assertTrue(all(item["title"].startswith("LSTM 长短期记忆网络 ·") for item in plan["resources"]))
        self.assertTrue(all(item["unit_title"] == "LSTM 长短期记忆网络" for item in plan["resources"]))


if __name__ == "__main__":
    unittest.main()
