from app.agents.agent_result_dto import AgentResultDTO


QUESTION_TYPES = ["选择题", "判断题", "简答题", "计算题", "代码补全题", "实验分析题", "项目任务题"]


def run(topic: str, unit_id: str = "") -> AgentResultDTO:
    output = {
        "type": "exercise_set",
        "title": f"{topic} 练习题集",
        "question_types": QUESTION_TYPES,
        "required_fields": ["题干", "选项/输入", "标准答案", "解析", "对应知识点", "难度", "常见错误"],
    }
    return AgentResultDTO("ExerciseGenerationAgent", input_summary=topic, output=output, evidence_refs=[unit_id] if unit_id else [], quality_score=0.9)
