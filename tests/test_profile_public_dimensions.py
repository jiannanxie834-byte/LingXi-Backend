import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.schemas import ProfileEvent
from app.services.data_services import profile_dimension_service, profile_event_service
from app.services.data_services.orchestrator_service import _build_public_profile


class PublicProfileDimensionsTest(unittest.TestCase):
    def test_legacy_ten_dimensions_are_exposed_as_six_core_items(self):
        profile = {
            "dimensions": {
                "知识基础": "基本掌握；依据：有效练习",
                "学习目标": "路径规划 · 动态规划",
                "概念理解": "78 分",
                "练习表现": "78 分",
                "实践能力": "96 分",
                "规划执行": "40 分",
                "复盘能力": "73 分",
                "易错修复": "状态定义不清；边界初始化遗漏",
                "媒介偏好": "图解与代码",
                "兴趣方向": "动态规划",
            },
            "radar": {
                "知识基础": 78,
                "练习表现": 78,
                "规划执行": 40,
                "实践能力": 96,
            },
            "evidence": {
                "evidence_count": 2,
                "recent_avg_score": 78,
                "exercise_avg_score": 78,
                "execution_rate": 40,
                "weak_points": ["状态定义不清", "边界初始化遗漏"],
                "level_source": "exercise_attempts",
                "level_evidence": "2 条有效练习作答。",
            },
        }

        public = _build_public_profile(profile)

        self.assertEqual(
            list(public["public_dimensions"]),
            ["当前知识水平", "学习目标", "练习表现", "薄弱知识点", "路径执行", "资源偏好"],
        )
        self.assertEqual(len(public["dimensions"]), 6)
        self.assertNotIn("实践能力", public["dimensions"])
        self.assertNotIn("兴趣方向", public["dimensions"])
        self.assertEqual(public["public_dimensions"]["当前知识水平"]["value"], 78)
        self.assertEqual(public["public_dimensions"]["薄弱知识点"]["value"], ["状态定义不清", "边界初始化遗漏"])

    def test_legacy_radar_does_not_create_mastery_without_evidence(self):
        public = _build_public_profile({
            "dimensions": {"知识基础": "入门（学生自述）", "学习目标": "学习动态规划"},
            "radar": {"知识基础": 88, "实践能力": 96},
            "evidence": {"evidence_count": 0},
        })

        knowledge = public["public_dimensions"]["当前知识水平"]
        self.assertIsNone(knowledge["value"])
        self.assertNotIn("当前知识水平", public["radar"])
        self.assertIn(knowledge["status"], {"reported", "pending"})


class ProfileEventDiffTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        ProfileEvent.__table__.create(bind=engine)
        self.db = sessionmaker(bind=engine)()

    def tearDown(self):
        self.db.close()

    @staticmethod
    def _pending_profile(goal: str, preference=None):
        return {
            "dimensions": {"学习目标": goal, "媒介偏好": "、".join(preference or [])},
            "radar": {},
            "public_dimensions": {
                "当前知识水平": profile_dimension_service.make_score_dimension(
                    None, display="待有效作答诊断", evidence="暂无有效作答", source="none"
                ),
                "学习目标": profile_dimension_service.make_text_dimension(
                    goal, evidence="本轮对话提取", source="dialogue"
                ),
                "练习表现": profile_dimension_service.make_score_dimension(
                    None, display="暂无有效作答", evidence="暂无有效作答", source="none"
                ),
                "薄弱知识点": profile_dimension_service.make_tags_dimension(
                    [], pending_text="待练习诊断", evidence="暂无错题", source="none"
                ),
                "路径执行": profile_dimension_service.make_score_dimension(
                    None, display="尚无执行记录", evidence="暂无任务记录", source="none"
                ),
                "资源偏好": profile_dimension_service.make_tags_dimension(
                    preference or [], pending_text="待确认", evidence="本轮对话提取", source="dialogue", status="reported"
                ),
            },
        }

    def test_event_only_marks_dimensions_supported_by_its_source(self):
        first = profile_event_service.record_profile_event(
            self.db,
            username="student",
            source_type="chat",
            profile=self._pending_profile("路径规划 · 动态规划", ["代码案例"]),
        )
        self.assertEqual(first["updated_dimensions"], ["学习目标", "资源偏好"])

        evaluation = self._pending_profile("练习批改与补弱 · 动态规划", [])
        evaluation["public_dimensions"].update({
            "当前知识水平": profile_dimension_service.make_score_dimension(
                78, display="78 分 · 基本掌握", evidence="本次有效作答 78 分", source="current_assessment"
            ),
            "练习表现": profile_dimension_service.make_score_dimension(
                78, display="最近有效作答 78 分", evidence="本次有效作答 78 分", source="current_assessment"
            ),
            "薄弱知识点": profile_dimension_service.make_tags_dimension(
                ["边界初始化"], pending_text="待练习诊断", evidence="错题反馈", source="exercise_attempts"
            ),
        })
        second = profile_event_service.record_profile_event(
            self.db,
            username="student",
            source_type="evaluation",
            profile=evaluation,
        )

        self.assertEqual(second["updated_dimensions"], ["当前知识水平", "练习表现", "薄弱知识点"])
        snapshot = profile_event_service.get_current_profile_snapshot(self.db, "student")
        self.assertEqual(snapshot["dimensions"]["学习目标"], "路径规划 · 动态规划")
        self.assertEqual(snapshot["public_dimensions"]["当前知识水平"]["value"], 78)


if __name__ == "__main__":
    unittest.main()
