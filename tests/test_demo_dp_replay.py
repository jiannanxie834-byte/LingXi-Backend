import unittest
from unittest.mock import patch

from app.services.data_services import orchestrator_service, semantic_analysis_service


class DemoDynamicProgrammingReplayTests(unittest.TestCase):
    def test_exact_beginner_learning_request_enables_replay(self):
        self.assertTrue(
            orchestrator_service._is_demo_dp_replay_request(
                "我现在只是数据结构与算法的初学者，我现在想学习动态规划"
            )
        )

    def test_other_dynamic_programming_questions_do_not_enable_replay(self):
        self.assertFalse(
            orchestrator_service._is_demo_dp_replay_request(
                "动态规划的状态转移方程为什么这样写？"
            )
        )
        self.assertFalse(
            orchestrator_service._is_demo_dp_replay_request(
                "我是数据结构初学者，想学习动态规划，只回答，不要资源、不要路线"
            )
        )

    def test_demo_semantic_analysis_skips_llm(self):
        eval_result = orchestrator_service._demo_dp_eval_result()
        with patch.object(
            semantic_analysis_service,
            "_infer_by_llm",
            side_effect=AssertionError("demo route must not call the model"),
        ):
            result = semantic_analysis_service.analyze_learning_request(
                db=None,
                username="student",
                message="我是数据结构与算法初学者，想学习动态规划",
                eval_result=eval_result,
                allow_llm=False,
            )
        self.assertEqual(result["subject_category"], "computer_science")
        self.assertTrue(result["should_generate_resources"])
        self.assertIn("动态规划", result["display_topic"])


if __name__ == "__main__":
    unittest.main()
