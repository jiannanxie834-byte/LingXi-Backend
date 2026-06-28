import unittest

from app.services.data_services.topic_scope_resolver import resolve_topic_scope


class DsaScopeResolverTest(unittest.TestCase):
    def test_required_scope_examples(self):
        cases = {
            "我想学习数据结构与算法": "course",
            "我不懂状态转移方程": "concept",
            "比较 BFS 和 DFS": "comparison",
            "我想做一个迷宫寻路项目": "project",
            "我总是写错递归终止条件": "remediation",
            "我想学习数据库索引": "out_of_course",
        }
        for text, expected_scope in cases.items():
            with self.subTest(text=text):
                self.assertEqual(resolve_topic_scope(text)["scope_level"], expected_scope)

    def test_dynamic_programming_hits_dsa(self):
        result = resolve_topic_scope("我想学习动态规划")
        self.assertIn(result["scope_level"], {"chapter", "unit"})
        self.assertEqual(result["chapter_id"], "chapter_10_dynamic_programming")


if __name__ == "__main__":
    unittest.main()
