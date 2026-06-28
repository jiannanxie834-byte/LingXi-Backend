import unittest

from app.agents.interactive_animation_agent import run as run_interactive_animation_agent


class ResourceArtifactGenerationTest(unittest.TestCase):
    def test_binary_search_topic_generates_binary_search_animation_spec(self):
        result = run_interactive_animation_agent(
            unit_id="dsa_binary_search_complexity",
            topic="二分查找复杂度",
        )
        spec = result.output["spec"]

        self.assertEqual(spec["animation_type"], "binary_search_animation")
        self.assertGreaterEqual(len(spec["steps"]), 3)

    def test_dynamic_programming_topic_generates_dp_table_animation_spec(self):
        result = run_interactive_animation_agent(
            unit_id="dsa_dp_intro",
            topic="动态规划入门",
        )
        spec = result.output["spec"]

        self.assertEqual(spec["animation_type"], "dp_table_animation")
        self.assertGreaterEqual(len(spec["steps"]), 3)


if __name__ == "__main__":
    unittest.main()
