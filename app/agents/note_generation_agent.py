from app.agents.agent_result_dto import AgentResultDTO


def run(topic: str, unit_id: str = "", evidence_refs=None) -> AgentResultDTO:
    evidence_refs = evidence_refs or ([unit_id] if unit_id else [])
    output = {
        "type": "course_note",
        "title": f"{topic} 课程讲解文档",
        "content_format": "markdown",
        "sections": ["学习目标", "前置知识", "核心概念", "公式/流程", "例子", "易错点", "下一步建议"],
    }
    return AgentResultDTO("NoteGenerationAgent", input_summary=topic, output=output, evidence_refs=evidence_refs, quality_score=0.9)
