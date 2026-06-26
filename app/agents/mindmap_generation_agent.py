from app.agents.agent_result_dto import AgentResultDTO


def run(topic: str, unit_id: str = "", concepts=None) -> AgentResultDTO:
    concepts = concepts or ["前置知识", "核心概念", "公式流程", "练习任务"]
    output = {
        "type": "mind_map",
        "title": f"{topic} 知识点思维导图",
        "content_format": "mermaid",
        "mermaid": "mindmap\n  root((" + topic + "))\n" + "\n".join([f"    {item}" for item in concepts]),
    }
    return AgentResultDTO("MindMapGenerationAgent", input_summary=topic, output=output, evidence_refs=[unit_id] if unit_id else [], quality_score=0.9)
