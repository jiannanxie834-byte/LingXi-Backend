import unittest

from app.services.data_services import learning_plan_service
from app.services.data_services import resource_artifact_type_service as artifact_types


class PlanResourceBindingTest(unittest.TestCase):
    def test_preview_resource_without_artifact_is_static_tag(self):
        step = {
            "id": "node_binary_search_01",
            "title": "理解二分查找复杂度",
            "unit_id": "dsa_binary_search_complexity",
            "resource_focus": [artifact_types.COURSE_NOTE],
        }
        resources = [
            {
                "title": "二分查找复杂度 · 课程讲解文档",
                "type": artifact_types.COURSE_NOTE,
                "unit_id": "dsa_binary_search_complexity",
            }
        ]

        bound = learning_plan_service.bind_resources_to_step(step, resources, 0)

        self.assertEqual(len(bound), 1)
        self.assertEqual(bound[0]["title"], "二分查找复杂度 · 课程讲解文档")
        self.assertEqual(bound[0]["route"], "")
        self.assertEqual(bound[0]["query"]["artifact_id"], "")

    def test_generated_artifact_becomes_clickable_resource_object(self):
        step = {
            "id": "node_dp_01",
            "title": "掌握动态规划入门",
            "unit_id": "dsa_dp_intro",
            "resource_focus": [artifact_types.COURSE_NOTE],
        }
        resources = [
            {
                "id": "RES001",
                "title": "动态规划入门 · 课程讲解文档",
                "type": artifact_types.COURSE_NOTE,
                "artifact": {
                    "artifact_id": "artifact_dp_note_001",
                    "resource_id": "RES001",
                    "type": artifact_types.COURSE_NOTE,
                    "unit_ids": ["dsa_dp_intro"],
                },
            },
            {
                "id": "RES002",
                "title": "二分查找动画",
                "type": artifact_types.INTERACTIVE_ANIMATION,
                "artifact": {
                    "artifact_id": "artifact_binary_search_animation_001",
                    "resource_id": "RES002",
                    "type": artifact_types.INTERACTIVE_ANIMATION,
                    "unit_ids": ["dsa_binary_search_complexity"],
                },
            },
        ]

        bound = learning_plan_service.bind_resources_to_step(step, resources, 0)

        self.assertEqual(len(bound), 1)
        self.assertEqual(bound[0]["artifact_id"], "artifact_dp_note_001")
        self.assertEqual(bound[0]["route"], "/resource")
        self.assertEqual(bound[0]["query"]["artifact_id"], "artifact_dp_note_001")
        self.assertEqual(bound[0]["query"]["unit_id"], "dsa_dp_intro")


if __name__ == "__main__":
    unittest.main()
