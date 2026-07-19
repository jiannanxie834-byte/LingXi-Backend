from app.agents import package_agent
from app.services.data_services import (
    dsa_resource_policy_service,
    resource_artifact_type_service as artifact_types,
    resource_quality_gate,
    resource_service,
)


BASE_CONTEXT = {
    "course_id": "data_structures_algorithms",
    "chapter_id": "chapter_10_dynamic_programming",
    "unit_id": "dsa_dp_basic",
    "evidence_refs": ["evidence_dp_basic"],
    "topic": "动态规划",
}


def _review(resource_type, content, **extra):
    item = {
        "title": f"动态规划 · {resource_type}",
        "topic": "动态规划",
        "unit_title": "动态规划",
        "type": resource_type,
        "summary": "面向当前学习需求的资源。",
        "content": content,
        **BASE_CONTEXT,
        **extra,
    }
    return resource_quality_gate.validate_teaching_quality(item, {**BASE_CONTEXT, **extra})


def test_generation_failure_never_returns_local_fallback(monkeypatch):
    monkeypatch.setattr(package_agent, "chat_json", lambda *args, **kwargs: {"ok": False, "error": "timeout"})
    result = package_agent._generate_one(
        {"type": artifact_types.COURSE_NOTE, "topic": "动态规划"},
        {"topic": "动态规划", "student_question": "学习动态规划"},
        {},
        {},
    )

    assert result["missing"] is True
    assert result["content"] == ""
    assert result["assembly_policy"] == "generation_failed_no_fallback"


def test_generation_accepts_complete_content_without_optional_metadata(monkeypatch):
    mindmap = """mindmap
  root((时间复杂度))
    前置知识
      基本运算
    核心概念
      渐进增长
    操作流程
      统计执行次数
    典型应用
      算法比较
    易错点
      忽略输入规模
    练习方向
      分析循环
"""

    def fake_chat_json(*args, **kwargs):
        assert kwargs["required_fields"] == ["content"]
        return {"ok": True, "data": {"content": mindmap}}

    monkeypatch.setattr(package_agent, "chat_json", fake_chat_json)

    result = package_agent._generate_one(
        {"type": artifact_types.MIND_MAP, "topic": "时间复杂度"},
        {"topic": "时间复杂度", "student_question": "我想学习时间复杂度"},
        {},
        {},
    )

    assert result["missing"] is False
    assert result["content"].startswith("mindmap")
    assert result["summary"] == ""
    assert result["personalization_reason"] == ""


def test_video_guide_keeps_only_catalog_links():
    catalog_url = "https://www.bilibili.com/video/BV-catalog"
    content = package_agent._enforce_catalog_video_links(
        "## 推荐视频\n[未知来源](https://example.com/fake)",
        {
            "video_items": [
                {
                    "title": "知识库视频",
                    "source_url": catalog_url,
                    "watch_focus": ["核心流程", "易错点"],
                }
            ]
        },
    )

    assert "example.com" not in content
    assert catalog_url in content
    assert "知识库公开视频链接" in content


def test_generic_fallback_and_placeholder_code_are_fatal():
    fallback_note = """# 为你定制的动态规划讲解
## 学习定位
这份讲解不是直接复制课程小节。
## 核心概念
处理的是序列、集合、树、图，还是一个可以拆分成子问题的过程。
"""
    note_review = _review(artifact_types.COURSE_NOTE, fallback_note)
    assert note_review["fatal"] is True
    assert any("降级模板" in issue for issue in note_review["issues"])

    code_lab = """# 动态规划代码实验
## 实验目标
理解状态转移。
## 环境依赖
Python 3.10
## 完整代码
```python
def solve(data):
    # TODO: 补全核心逻辑
    pass
```
## 运行命令
python main.py
## 学生任务
补全代码。
## 常见报错
下标越界。
"""
    code_review = _review(artifact_types.CODE_LAB, code_lab)
    assert code_review["fatal"] is True
    assert any("TODO/pass" in issue for issue in code_review["issues"])
    assert code_review["score"] < 88


def test_duplicate_mindmap_and_linkless_video_cannot_pass():
    mindmap = """mindmap
  root((动态规划))
    前置知识
      状态
      状态
    核心概念
      转移
      转移
    操作流程
      初始化
      遍历
    易错点
      边界
      顺序
"""
    mindmap_review = _review(artifact_types.MIND_MAP, mindmap)
    assert mindmap_review["fatal"] is True
    assert any("重复节点" in issue for issue in mindmap_review["issues"])

    video = """# 动态规划视频指南
## 观看/阅读前准备
记录问题。
## 观看/阅读中关注点
关注转移。
## 观看/阅读后任务
手推表格。
## 版权说明
只保留原始入口。
"""
    video_review = _review(artifact_types.PERSONALIZED_VIDEO_GUIDE, video)
    assert video_review["fatal"] is True
    assert any("原始 HTTP(S)" in issue for issue in video_review["issues"])


def test_todo_in_non_code_resource_is_still_a_placeholder():
    review = _review(
        artifact_types.INTERACTIVE_ANIMATION,
        "## 动画目标\n## 步骤与高亮\nTODO: 补齐练习",
        assets=[{"url": "/media/a.html", "mime_type": "text/html"}],
    )

    assert review["fatal"] is True
    assert review["score"] <= 30


def test_mindmap_normalization_removes_exact_duplicate_nodes():
    content = """mindmap
  root((动态规划))
    前置知识
      前置知识
      递归
    核心概念
      状态
      状态
"""

    normalized = package_agent._normalize_mindmap_content(content, "动态规划")

    assert normalized.count("前置知识") == 1
    assert normalized.count("状态") == 1


def test_code_lab_normalization_restores_fence_only_for_valid_python():
    valid = """## 完整代码（保存为 main.py）
python
def solve(n):
    return n + 1

assert solve(0) == 1
assert solve(1) == 2
assert solve(9) == 10

## 运行命令
python main.py
"""
    invalid = valid.replace("return n + 1", "return (")

    normalized = package_agent._normalize_code_lab_content(valid)

    assert "```python\ndef solve" in normalized
    assert "assert solve(9) == 10\n```" in normalized
    assert package_agent._normalize_code_lab_content(invalid) == invalid.strip()


def test_markdown_normalization_repairs_bare_code_blocks_between_headings():
    content = """## 动画后练习
python
def climb(n):
    return n + 1

print(climb(2))

#### 下一项练习
python
for value in range(3):
    print(value)
"""

    normalized = package_agent._normalize_markdown_code_blocks(content)

    assert "```python\ndef climb" in normalized
    assert "print(climb(2))\n```\n\n#### 下一项练习" in normalized
    assert "```python\nfor value in range(3):" in normalized
    assert normalized.endswith("```")


def test_template_exercise_without_real_options_is_rejected():
    content = """### 题目 1｜选择题
**知识点**：动态规划
**题目**：下列哪一项正确？
**答案**：选择能说明条件的选项。
**解析**：不要只给结论，要说明每一步为什么成立。
**常见错误**：忽略边界条件。
### 题目 2｜判断题
**知识点**：状态
**题目**：DP 就是递归。
**答案**：错
**解析**：不要只给结论，要说明每一步为什么成立。
**常见错误**：忽略边界条件。
### 题目 3｜简答题
**知识点**：转移
**题目**：解释转移。
**答案**：描述状态依赖。
**解析**：不要只给结论，要说明每一步为什么成立。
**常见错误**：忽略边界条件。
### 题目 4｜过程题
**知识点**：初始化
**题目**：写出初始化。
**答案**：dp[0]=0。
**解析**：不要只给结论，要说明每一步为什么成立。
**常见错误**：忽略边界条件。
"""

    review = _review(artifact_types.EXERCISE_SET, content)

    assert review["fatal"] is True
    assert any("A-D" in issue for issue in review["issues"])
    assert any("模板答案" in issue for issue in review["issues"])


def test_default_dsa_package_uses_verifiable_video_guide_mainline():
    assert artifact_types.PERSONALIZED_VIDEO_GUIDE in dsa_resource_policy_service.DEFAULT_DSA_LEARNING_PACKAGE_TYPES
    assert artifact_types.INTERACTIVE_ANIMATION not in dsa_resource_policy_service.DEFAULT_DSA_LEARNING_PACKAGE_TYPES


def test_dsa_multimodal_type_follows_topic_and_catalog(monkeypatch):
    monkeypatch.setattr(
        dsa_resource_policy_service.video_catalog_service,
        "search_videos",
        lambda **kwargs: [{"source_url": "https://www.bilibili.com/video/example"}],
    )
    dp_types = dsa_resource_policy_service.select_dsa_resource_types({
        "topic": "动态规划",
        "dsa_course_map": {"unit_id": "dsa_dp_intro", "scope_level": "concept"},
    })
    tree_types = dsa_resource_policy_service.select_dsa_resource_types({
        "topic": "后序遍历",
        "dsa_course_map": {"unit_id": "dsa_postorder_traversal", "scope_level": "concept"},
    })

    assert artifact_types.PERSONALIZED_VIDEO_GUIDE in dp_types
    assert artifact_types.INTERACTIVE_ANIMATION not in dp_types
    assert artifact_types.PERSONALIZED_VIDEO_GUIDE in tree_types
    assert artifact_types.INTERACTIVE_ANIMATION not in tree_types


def test_dsa_multimodal_type_falls_back_to_reading_without_video(monkeypatch):
    monkeypatch.setattr(
        dsa_resource_policy_service.video_catalog_service,
        "search_videos",
        lambda **kwargs: [],
    )
    resource_types = dsa_resource_policy_service.select_dsa_resource_types({
        "topic": "综合项目",
        "dsa_course_map": {"unit_id": "dsa_project_overview", "scope_level": "concept"},
    })

    assert artifact_types.READING_PACK in resource_types
    assert artifact_types.PERSONALIZED_VIDEO_GUIDE not in resource_types
    assert artifact_types.INTERACTIVE_ANIMATION not in resource_types


def test_failed_resources_are_skipped_without_clearing_the_whole_package(monkeypatch):
    plan = {
        "semantic_result": {"course_id": "data_structures_algorithms"},
        "resources": [
            {"title": f"动态规划资源 {index}", "type": resource_type}
            for index, resource_type in enumerate(
                dsa_resource_policy_service.DEFAULT_DSA_LEARNING_PACKAGE_TYPES,
                start=1,
            )
        ],
    }
    outputs = [
        {"missing": True, "error": "spark timeout"}
        for _ in plan["resources"]
    ]
    monkeypatch.setattr(
        resource_service,
        "insert_generated_resources",
        lambda _db, resources, **kwargs: resources,
    )

    result = resource_service.save_ai_generated_resources(
        db=object(),
        resource_plan=plan,
        llm_outputs=outputs,
        applicant_username="student",
    )

    assert result["resources"] == []
    assert len(result["skipped_resources"]) == len(plan["resources"])
    assert not any(item["type"] == "package" for item in result["skipped_resources"])
