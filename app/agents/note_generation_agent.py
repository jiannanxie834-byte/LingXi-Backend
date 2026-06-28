from app.agents.agent_result_dto import AgentResultDTO


def run(topic: str, unit_id: str = "", evidence_refs=None) -> AgentResultDTO:
    evidence_refs = evidence_refs or ([unit_id] if unit_id else [])
    output = {
        "type": "course_note",
        "title": f"{topic} 课程讲解文档",
        "content_format": "markdown",
        "is_final_content": False,
        "handoff_to": "ResourceArtifactGeneration",
        "sections": [
            "学习定位与适用对象",
            "本知识点在《数据结构与算法》课程中的位置",
            "前置知识",
            "核心概念详细解释",
            "公式/流程/算法机制",
            "具体例子",
            "代码实现思路或伪代码",
            "常见误区",
            "自测题与答案",
            "下一步建议",
        ],
        "minimum_quality": {
            "min_chars": 1800,
            "min_headings": 8,
            "requires_examples": 2,
            "requires_exercises": 3,
            "requires_evidence_refs": True,
        },
        "note": "本 Agent 只规划讲义结构，不能作为最终课程讲义正文落库；最终正文必须由资源生成链路结合 evidence_chunks 和教学质量门禁生成。",
    }
    return AgentResultDTO("NoteGenerationAgent", input_summary=topic, output=output, evidence_refs=evidence_refs, quality_score=0.75)
