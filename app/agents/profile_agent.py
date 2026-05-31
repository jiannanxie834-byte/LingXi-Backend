def run(user, message, eval_result):
    intent = eval_result.get("intent", "综合学习")
    topic = eval_result.get("topic", "人工智能导论")
    hours = user.hours if user else 0

    return {
        "level": "进阶" if hours >= 10 else "初学者",
        "tags": [topic, intent],
        "topic": topic,
        "knowledge_topic": topic,
        "intent": intent,
        "goal": intent,
    }
