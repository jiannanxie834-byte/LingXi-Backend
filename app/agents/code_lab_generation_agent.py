from app.agents.agent_result_dto import AgentResultDTO


def run(topic: str, unit_id: str = "") -> AgentResultDTO:
    output = {
        "type": "code_lab",
        "title": f"{topic} 代码实验",
        "content_format": "python+markdown",
        "sections": ["实验目标", "环境依赖", "输入输出样例", "核心函数", "边界用例", "完整代码", "运行方式", "复杂度记录", "调试任务", "实验报告模板"],
    }
    return AgentResultDTO("CodeLabGenerationAgent", input_summary=topic, output=output, evidence_refs=[unit_id] if unit_id else [], quality_score=0.9)
