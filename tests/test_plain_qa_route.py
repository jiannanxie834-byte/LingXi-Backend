import unittest
from unittest.mock import patch

from app.models.schemas import TurnRoute
from app.services.data_services import conversation_router
from app.services.data_services import deterministic_complexity_service
from app.services.data_services import orchestrator_service


class PlainQaRouteTest(unittest.TestCase):
    def _route(self, text, last_topic=""):
        with patch.object(conversation_router, "get_last_topic", return_value=last_topic):
            return conversation_router.route_turn(object(), "student", "session", text)

    def test_explicit_answer_only_is_hard_plain_route(self):
        route = self._route("只回答这个问题，不要资源，不要路线：二分查找为什么快？")
        self.assertEqual(route.route_type, "plain_qa")
        self.assertFalse(route.should_run_full_agents)
        self.assertFalse(route.should_run_intent_agent)
        self.assertFalse(route.should_run_retrieval)
        self.assertFalse(route.should_run_planner)
        self.assertFalse(route.should_generate_resources)
        self.assertFalse(route.should_update_profile)

    def test_natural_question_does_not_create_learning_package(self):
        route = self._route("下面这段代码的时间复杂度是多少？")
        self.assertEqual(route.route_type, "concept_question")
        self.assertFalse(route.should_run_full_agents)
        self.assertFalse(route.should_generate_resources)

    def test_common_homework_question_is_plain_answer(self):
        route = self._route("这道题怎么做？我卡在边界条件了")
        self.assertEqual(route.route_type, "plain_qa")
        self.assertFalse(route.should_run_full_agents)
        self.assertFalse(route.should_generate_resources)

    def test_explicit_learning_request_keeps_full_mainline(self):
        route = self._route("我会数组，现在要学习二分查找，请生成学习路线")
        self.assertEqual(route.route_type, "learning_request")
        self.assertTrue(route.should_run_full_agents)
        self.assertTrue(route.should_run_planner)
        self.assertTrue(route.should_generate_resources)


class DeterministicComplexityTest(unittest.TestCase):
    def test_binary_search_distinguishes_halvings_and_comparisons(self):
        answer = deterministic_complexity_service.verified_answer(
            "二分查找长度为16时最多比较几次？"
        )
        self.assertIn("O(log n)", answer)
        self.assertIn("4 次减半", answer)
        self.assertIn("5 次", answer)

    def test_geometric_inner_loop_has_exact_boundary_counts(self):
        answer = deterministic_complexity_service.verified_answer(
            """这段代码复杂度是多少，n=1 时执行几次？
```python
for i in range(n):
    j = 1
    while j < n:
        j *= 2
```
"""
        )
        self.assertIn("O(n log n)", answer)
        self.assertIn("ceil(log_2(n))", answer)
        self.assertIn("n=1 时外层执行 1 次、内层执行 0 次", answer)


class PlainQaOrchestratorTest(unittest.TestCase):
    def test_plain_question_calls_only_one_answer_model(self):
        route = TurnRoute(route_type="concept_question", topic="栈")
        with (
            patch.object(orchestrator_service.conversation_router, "route_turn", return_value=route),
            patch.object(
                orchestrator_service,
                "chat",
                return_value={"ok": True, "content": "栈是后进先出，队列是先进先出。"},
            ) as answer_mock,
            patch.object(orchestrator_service, "eval_run") as intent_mock,
            patch.object(orchestrator_service, "profile_run") as profile_mock,
            patch.object(orchestrator_service, "planner_run") as planner_mock,
            patch.object(orchestrator_service, "resource_run") as resource_mock,
        ):
            result = orchestrator_service.handle_learning_chat(
                "student", "栈和队列有什么区别？", object(), session_id=""
            )

        answer_mock.assert_called_once()
        intent_mock.assert_not_called()
        profile_mock.assert_not_called()
        planner_mock.assert_not_called()
        resource_mock.assert_not_called()
        self.assertEqual(result["tutor_result"]["content"], "栈是后进先出，队列是先进先出。")
        self.assertEqual(result["profile"], {})
        self.assertIsNone(result["path"])
        self.assertEqual(result["resources"], [])
        self.assertEqual(result["pipeline_steps"], [])
        self.assertEqual(result["content_type"], "conversation_reply")

    def test_verified_code_answer_does_not_spend_model_call(self):
        route = TurnRoute(route_type="plain_qa", topic="复杂度分析")
        question = """只回答，不要资源，不要路线：
```python
for i in range(n):
    j = 1
    while j < n:
        j *= 2
```
复杂度是多少？
"""
        with (
            patch.object(orchestrator_service.conversation_router, "route_turn", return_value=route),
            patch.object(orchestrator_service, "chat") as answer_mock,
        ):
            result = orchestrator_service.handle_learning_chat(
                "student", question, object(), session_id=""
            )

        answer_mock.assert_not_called()
        self.assertIn("O(n log n)", result["tutor_result"]["content"])
        self.assertEqual(result["resources"], [])


if __name__ == "__main__":
    unittest.main()
