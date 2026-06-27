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


def _lstm_gate_spec():
    return {
        "animation_type": "lstm_gate_flow",
        "nodes": ["x_t", "h_{t-1}", "c_{t-1}", "f_t", "i_t", "g_t", "c_t", "o_t", "h_t"],
        "steps": [
            {
                "step": 1,
                "highlight": ["x_t", "h_{t-1}"],
                "formula": "[x_t, h_{t-1}]",
                "explanation": "当前输入 x_t 与上一时刻隐藏状态 h_{t-1} 拼接，作为三个门和候选记忆的共同输入。",
            },
            {
                "step": 2,
                "highlight": ["f_t", "c_{t-1}"],
                "formula": "f_t = sigmoid(W_f [h_{t-1}, x_t] + b_f)",
                "explanation": "遗忘门 f_t 决定上一时刻细胞状态 c_{t-1} 中哪些信息保留、哪些信息衰减。",
            },
            {
                "step": 3,
                "highlight": ["i_t", "g_t"],
                "formula": "i_t = sigmoid(...),  g_t = tanh(...)",
                "explanation": "输入门 i_t 控制新信息写入比例，候选记忆 g_t 提供本时刻可能写入的内容。",
            },
            {
                "step": 4,
                "highlight": ["c_t", "f_t", "i_t", "g_t"],
                "formula": "c_t = f_t * c_{t-1} + i_t * g_t",
                "explanation": "新的细胞状态 c_t 同时融合被保留的旧记忆和被允许写入的新记忆。",
            },
            {
                "step": 5,
                "highlight": ["o_t", "h_t", "c_t"],
                "formula": "h_t = o_t * tanh(c_t)",
                "explanation": "输出门 o_t 决定细胞状态中哪些信息暴露为当前隐藏状态 h_t，并传递给下一时刻或上层网络。",
            },
        ],
    }


def run(unit_id: str = "", topic: str = "") -> AgentResultDTO:
    text = f"{unit_id} {topic}".lower()
    if "cnn" in text or "卷积" in text:
        spec = _cnn_spec()
    elif "lstm" in text or "长短期记忆" in text or "遗忘门" in text or "输入门" in text or "输出门" in text:
        spec = _lstm_gate_spec()
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
