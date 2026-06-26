from app.agents.agent_result_dto import AgentResultDTO


def run(topic: str, unit_id: str = "") -> AgentResultDTO:
    output = {
        "type": "code_lab",
        "title": f"{topic} PyTorch 实操案例",
        "content_format": "python+markdown",
        "sections": ["实验目标", "环境依赖", "数据集说明", "模型结构", "训练流程", "完整代码", "运行方式", "调参任务", "实验报告模板", "常见报错"],
    }
    return AgentResultDTO("CodeLabGenerationAgent", input_summary=topic, output=output, evidence_refs=[unit_id] if unit_id else [], quality_score=0.9)
