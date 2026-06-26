from app.agents.agent_result_dto import AgentResultDTO


def run(topic: str, unit_id: str = "", references=None) -> AgentResultDTO:
    output = {
        "type": "reading_pack",
        "title": f"{topic} 拓展阅读包",
        "content_format": "markdown",
        "reading_order": ["教材章节", "公开课程", "官方文档", "教程/博客", "论文方向"],
        "references": references or [],
    }
    return AgentResultDTO("ReadingGenerationAgent", input_summary=topic, output=output, evidence_refs=[unit_id] if unit_id else [], quality_score=0.85)
