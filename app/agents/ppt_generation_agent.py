from app.agents.agent_result_dto import AgentResultDTO


def run(topic: str, unit_id: str = "") -> AgentResultDTO:
    output = {
        "type": "ppt_outline",
        "title": f"{topic} PPT 大纲",
        "content_format": "ppt_outline",
        "slides": ["封面", "学习目标", "知识背景", "核心概念", "图解过程", "代码示例", "练习题", "项目任务", "总结"],
    }
    return AgentResultDTO("PptGenerationAgent", input_summary=topic, output=output, evidence_refs=[unit_id] if unit_id else [], quality_score=0.88)
