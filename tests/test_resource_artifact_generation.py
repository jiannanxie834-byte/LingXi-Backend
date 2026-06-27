import unittest

from app.agents.interactive_animation_agent import run as run_interactive_animation_agent


class ResourceArtifactGenerationTest(unittest.TestCase):
    def test_lstm_topic_generates_lstm_gate_animation_spec(self):
        result = run_interactive_animation_agent(
            unit_id="dl_lstm_cell",
            topic="LSTM 长短期记忆网络",
        )
        spec = result.output["spec"]

        self.assertEqual(spec["animation_type"], "lstm_gate_flow")
        self.assertIn("f_t", spec["nodes"])
        self.assertIn("i_t", spec["nodes"])
        self.assertIn("o_t", spec["nodes"])
        self.assertGreaterEqual(len(spec["steps"]), 5)

    def test_attention_topic_generates_attention_animation_spec(self):
        result = run_interactive_animation_agent(
            unit_id="dl_multihead_attention",
            topic="多头注意力",
        )
        spec = result.output["spec"]

        self.assertEqual(spec["animation_type"], "attention_flow")
        self.assertGreaterEqual(len(spec["steps"]), 4)


if __name__ == "__main__":
    unittest.main()
