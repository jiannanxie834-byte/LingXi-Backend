from typing import Optional


def reply_acknowledgement(last_topic: Optional[str]) -> str:
    if last_topic:
        return f"好的，我会继续围绕「{last_topic}」为你提供《深度学习》课程学习帮助。你可以继续问概念解释、推导过程、PyTorch 实现、练习题或学习路线。"
    return "好的。你可以直接告诉我想学习的《深度学习》知识点，例如 CNN、反向传播、Transformer 或 PyTorch 实验。"


def reply_topic_rejection(topic: Optional[str]) -> str:
    if topic:
        return f"好的，那我们先不聊「{topic}」。你想换成《深度学习》里的哪个方向？可以选 CNN、反向传播、Transformer、PyTorch 实验或课程项目。"
    return "好的，那我们先换个方向。你想聊 CNN、反向传播、Transformer、PyTorch 实验，还是深度学习课程项目？"


def reply_topic_switch() -> str:
    return "可以。你想换成《深度学习》课程里的概念理解、公式推导、代码实验、练习巩固，还是课程项目？选一个方向我再继续。"


def reply_casual_chat() -> str:
    return "可以。我主要负责《深度学习》课程学习辅导。你想聊学习方法，还是最近哪个知识点不太懂？"


def reply_meta_question() -> str:
    return "我还不能确定你接下来想说什么。你可以告诉我想学习的深度学习主题、遇到的公式或代码问题，或者让我根据最近的学习记录推荐下一步。"


def reply_capability_intro() -> str:
    return "我可以围绕《深度学习》帮你解释知识点、规划学习路线、生成练习题、整理 PyTorch 实验、推荐公开视频，并根据学习评价调整后续路线。"


def reply_clarification_needed() -> str:
    return "这句话还不够明确。你可以补充一个《深度学习》知识点、学习目标或具体卡点，我再帮你拆解。"


def reply_continue_without_topic() -> str:
    return "可以继续，不过我需要先知道你想学习《深度学习》里的哪个主题。你可以输入 CNN、反向传播、Transformer 或 PyTorch 实验。"


def reply_out_of_scope() -> str:
    return "这个问题暂不属于本系统的《深度学习》课程主线。你可以换成 CNN、反向传播、Transformer、PyTorch 实验或课程项目相关问题。"
