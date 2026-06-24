def _validate_profile(profile):
    required = ["level", "tags", "topic", "knowledge_topic", "intent", "goal"]
    missing = [field for field in required if field not in profile]
    if missing:
        raise RuntimeError(f"画像建模结果缺少字段：{', '.join(missing)}")

    if not isinstance(profile["tags"], list):
        raise RuntimeError("画像建模结果 tags 必须是列表")

    return profile


def run(user, message, eval_result):
    intent = eval_result.get("intent", "综合学习")
    topic = eval_result.get("topic") or "当前主题"
    hours = user.hours if user else 0

    profile = {
        "level": "进阶" if hours >= 10 else "初学者",
        "tags": [topic],
        "topic": topic,
        "knowledge_topic": topic,
        "intent": intent,
        "goal": intent,
    }

    return _validate_profile(profile)
