import unittest

from app.services.data_services import resource_artifact_type_service as artifact_types
from app.services.data_services.resource_quality_gate import validate_teaching_quality


class TeachingQualityGateTest(unittest.TestCase):
    def test_short_course_note_is_rejected_as_fatal(self):
        item = {
            "title": "卷积神经网络中的卷积操作 · 课程讲解文档",
            "type": artifact_types.COURSE_NOTE,
            "summary": "简短摘要",
            "content": "## 学习目标\n了解 CNN。\n## 核心内容\nCNN 可以处理图像。\n## 常见误区\n不要混淆概念。",
            "source": "深度学习初始知识库",
            "unit_id": "dl_cnn_conv_basic",
        }
        result = validate_teaching_quality(
            item,
            {
                "topic": "卷积神经网络中的卷积操作",
                "unit_id": "dl_cnn_conv_basic",
                "resource_type": artifact_types.COURSE_NOTE,
                "evidence_chunks": [],
            },
        )

        self.assertFalse(result["passed"])
        self.assertTrue(result["fatal"])
        self.assertLess(result["teaching_quality_score"], 60)
        self.assertTrue(any("内容过短" in issue for issue in result["issues"]))
        self.assertTrue(any("核心主题词覆盖不足" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
