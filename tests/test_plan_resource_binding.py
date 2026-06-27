import unittest

from app.services.data_services import learning_plan_service
from app.services.data_services import resource_artifact_type_service as artifact_types


class PlanResourceBindingTest(unittest.TestCase):
    def test_preview_resource_without_artifact_is_static_tag(self):
        step = {
            "id": "node_cnn_01",
            "title": "理解 CNN 输出尺寸",
            "unit_id": "dl_cnn_output_size",
            "resource_focus": [artifact_types.COURSE_NOTE],
        }
        resources = [
            {
                "title": "CNN 输出特征图尺寸计算 · 课程讲解文档",
                "type": artifact_types.COURSE_NOTE,
                "unit_id": "dl_cnn_output_size",
            }
        ]

        bound = learning_plan_service.bind_resources_to_step(step, resources, 0)

        self.assertEqual(len(bound), 1)
        self.assertEqual(bound[0]["title"], "CNN 输出特征图尺寸计算 · 课程讲解文档")
        self.assertEqual(bound[0]["route"], "")
        self.assertEqual(bound[0]["query"]["artifact_id"], "")

    def test_generated_artifact_becomes_clickable_resource_object(self):
        step = {
            "id": "node_attention_01",
            "title": "掌握多头注意力",
            "unit_id": "dl_multihead_attention",
            "resource_focus": [artifact_types.COURSE_NOTE],
        }
        resources = [
            {
                "id": "RES001",
                "title": "多头注意力 · 课程讲解文档",
                "type": artifact_types.COURSE_NOTE,
                "artifact": {
                    "artifact_id": "artifact_attention_note_001",
                    "resource_id": "RES001",
                    "type": artifact_types.COURSE_NOTE,
                    "unit_ids": ["dl_multihead_attention"],
                },
            },
            {
                "id": "RES002",
                "title": "卷积滑窗动画",
                "type": artifact_types.INTERACTIVE_ANIMATION,
                "artifact": {
                    "artifact_id": "artifact_cnn_animation_001",
                    "resource_id": "RES002",
                    "type": artifact_types.INTERACTIVE_ANIMATION,
                    "unit_ids": ["dl_cnn_conv_basic"],
                },
            },
        ]

        bound = learning_plan_service.bind_resources_to_step(step, resources, 0)

        self.assertEqual(len(bound), 1)
        self.assertEqual(bound[0]["artifact_id"], "artifact_attention_note_001")
        self.assertEqual(bound[0]["route"], "/resource")
        self.assertEqual(bound[0]["query"]["artifact_id"], "artifact_attention_note_001")
        self.assertEqual(bound[0]["query"]["unit_id"], "dl_multihead_attention")


if __name__ == "__main__":
    unittest.main()
