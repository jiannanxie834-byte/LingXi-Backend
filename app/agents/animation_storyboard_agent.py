from app.agents.agent_result_dto import AgentResultDTO


def run(topic: str = "深度学习知识点", unit_id: str = "") -> AgentResultDTO:
    output = {
        "type": "animation_storyboard",
        "title": f"{topic} 动画分镜",
        "scenes": [
            {
                "scene_id": 1,
                "visual": f"展示「{topic}」的核心结构或计算流程。",
                "narration": "先建立直观图像，再进入公式或代码。",
                "subtitle": "从图解到推导",
            },
            {
                "scene_id": 2,
                "visual": "高亮关键变量、张量形状或计算路径。",
                "narration": "观察每一步输入、输出和变化原因。",
                "subtitle": "关注 shape 与信息流",
            },
        ],
    }
    return AgentResultDTO(
        agent_name="AnimationStoryboardAgent",
        input_summary=topic,
        output=output,
        evidence_refs=[unit_id] if unit_id else [],
        quality_score=0.88,
    )
