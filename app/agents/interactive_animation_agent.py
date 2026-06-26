from app.agents.agent_result_dto import AgentResultDTO


def _cnn_spec():
    return {
        "animation_type": "cnn_convolution",
        "input_matrix_size": [5, 5],
        "kernel_size": [3, 3],
        "stride": 1,
        "padding": 0,
        "steps": [
            {
                "step": 1,
                "highlight_input_region": [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]],
                "highlight_output_cell": [0, 0],
                "explanation": "卷积核覆盖左上角 3x3 区域，计算第一个输出值。",
            },
            {"step": 2, "action": "move_right", "explanation": "卷积核向右滑动一个步幅，输出特征图同步移动。"},
        ],
    }


def _backprop_spec():
    return {
        "animation_type": "backpropagation_flow",
        "layers": ["input", "hidden", "output", "loss"],
        "steps": [
            {"step": 1, "highlight": "loss", "explanation": "先计算预测值和真实标签之间的损失。"},
            {"step": 2, "highlight": "output_to_hidden", "explanation": "梯度从输出层向隐藏层传播。"},
            {"step": 3, "highlight": "chain_rule", "explanation": "链式法则把局部梯度逐段相乘。"},
        ],
    }


def _attention_spec():
    return {
        "animation_type": "attention_flow",
        "tokens": ["我", "喜欢", "深度学习"],
        "steps": [
            {"step": 1, "highlight": "qkv", "explanation": "每个 token 生成 Query、Key、Value。"},
            {"step": 2, "highlight": "score", "explanation": "Query 与 Key 点积得到注意力分数。"},
            {"step": 3, "highlight": "softmax", "explanation": "softmax 将分数归一化为权重。"},
            {"step": 4, "highlight": "weighted_sum", "explanation": "按权重对 Value 加权求和。"},
        ],
    }


def run(unit_id: str = "", topic: str = "") -> AgentResultDTO:
    text = f"{unit_id} {topic}".lower()
    if "cnn" in text or "卷积" in text:
        spec = _cnn_spec()
    elif "backprop" in text or "反向传播" in text or "bp" in text:
        spec = _backprop_spec()
    elif "transformer" in text or "attention" in text or "注意力" in text:
        spec = _attention_spec()
    else:
        spec = _cnn_spec()
    return AgentResultDTO(
        agent_name="InteractiveAnimationAgent",
        input_summary=topic or unit_id,
        output={"type": "interactive_animation", "format": "animation_spec", "spec": spec},
        evidence_refs=[unit_id] if unit_id else [],
        quality_score=0.9,
    )
