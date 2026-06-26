from app.agents.agent_result_dto import AgentResultDTO


def run(topic: str, unit_id: str = "") -> AgentResultDTO:
    output = {
        "type": "project_brief",
        "title": f"{topic} 课程实践项目任务书",
        "content_format": "markdown",
        "sections": ["项目背景", "项目目标", "数据集建议", "技术路线", "任务拆解", "验收标准", "提交物", "评分 Rubric", "扩展方向"],
    }
    return AgentResultDTO("ProjectBriefAgent", input_summary=topic, output=output, evidence_refs=[unit_id] if unit_id else [], quality_score=0.9)
