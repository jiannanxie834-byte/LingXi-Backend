from app.services.data_services import exercise_question_service


CONTENT = """# 动态规划练习

这是题集简介，不能被当成第一题。

### 题目 1｜选择题
**知识点**：状态定义
**题目**：设计动态规划时，以下哪项应先明确？
- A. 状态的含义
- B. 随机测试数量
- C. 输出格式的颜色
**答案**：A
**解析**：状态含义是转移和初始化的前提。
**常见错误**：直接写转移方程。

### 题目 2：判断题
题干：只要存在最优子结构，所有问题都必须用动态规划。
答案：错。
解析：还要结合重叠子问题和具体目标。
常见错误：把必要条件当成充分条件。

### 题目 3｜简答题
知识点：转移顺序
题目：为什么遍历顺序必须保证依赖状态已经计算？
答案：当前状态的值来自已完成的依赖状态。
解析：否则会使用未定义或旧值。
常见错误：只背循环模板。

## 复盘清单
这里的文字不应进入第三题。
"""


def test_parse_exercise_content_builds_stable_structured_questions():
    questions = exercise_question_service.parse_exercise_content(CONTENT)

    assert len(questions) == 3
    assert [item["question_id"] for item in questions] == ["q1", "q2", "q3"]
    assert [item["type"] for item in questions] == ["single_choice", "true_false", "short_answer"]
    assert sum(item["points"] for item in questions) == 100
    assert questions[0]["options"][0] == {"key": "A", "text": "状态的含义"}
    assert questions[1]["reference_answer"] == "错。"
    assert "复盘清单" not in questions[2]["common_errors"]


def test_public_artifact_never_exposes_answers_or_explanations():
    artifact = exercise_question_service.public_artifact({
        "artifact_id": "artifact_demo",
        "type": "练习题集",
        "content": CONTENT,
    })

    assert artifact["question_count"] == 3
    assert "reference_answer" not in artifact["questions"][0]
    assert "explanation" not in artifact["questions"][0]
    assert "答案：A" not in artifact["content"]
    assert "状态含义是转移" not in artifact["content"]


def test_answer_sheet_is_only_built_from_canonical_backend_questions():
    questions = exercise_question_service.parse_exercise_content(CONTENT)
    answers = exercise_question_service.answer_sheet(questions)

    assert answers[0]["question_id"] == "q1"
    assert answers[0]["answer"] == "A"
    assert answers[0]["explanation"] == "状态含义是转移和初始化的前提。"
