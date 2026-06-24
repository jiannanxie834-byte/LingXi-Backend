from typing import Optional


def reply_acknowledgement(last_topic: Optional[str]) -> str:
    if last_topic:
        return f"好的，我会继续围绕「{last_topic}」为你提供学习帮助。你可以继续问概念解释、代码实现、练习题或学习路线。"
    return "好的。你可以直接告诉我想学习的课程、知识点或具体问题。"


def reply_topic_rejection(topic: Optional[str]) -> str:
    if topic:
        return f"好的，那我们先不聊「{topic}」。你想换成哪个方向？可以选机器学习、深度学习、信息安全、编程实践，或者直接输入一个知识点。"
    return "好的，那我们先换个方向。你想聊课程学习、考试复习、项目实践，还是学习方法？"


def reply_topic_switch() -> str:
    return "可以。你想换成课程学习、考试复习、项目实践，还是学习方法？选一个方向我再继续。"


def reply_casual_chat() -> str:
    return "可以。我主要负责学习辅导。你想聊学习方法、课程选择，还是最近哪个知识点不太懂？"


def reply_meta_question() -> str:
    return "我还不能确定你接下来想说什么。你可以告诉我想学习的主题、遇到的问题，或者让我根据最近的学习记录推荐下一步。"


def reply_capability_intro() -> str:
    return "我可以帮你解释知识点、规划学习路线、推荐学习资源、生成练习题，并根据学习评价调整后续路线。"


def reply_clarification_needed() -> str:
    return "这句话还不够明确。你可以补充课程主题、学习目标或具体问题，我再帮你拆解。"


def reply_continue_without_topic() -> str:
    return "可以继续，不过我需要先知道你想学习哪个主题。你可以输入一个课程名或知识点。"


def reply_out_of_scope() -> str:
    return "这个问题不太属于学习辅导范围。你可以告诉我想学习的课程、知识点或具体卡点，我会帮你继续拆解。"
