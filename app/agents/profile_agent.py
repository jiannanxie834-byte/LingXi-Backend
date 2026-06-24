def _validate_profile(profile):
    required = ["level", "tags", "topic", "knowledge_topic", "intent", "goal"]
    missing = [field for field in required if field not in profile]
    if missing:
        raise RuntimeError(f"画像建模结果缺少字段：{', '.join(missing)}")

    if not isinstance(profile["tags"], list):
        raise RuntimeError("画像建模结果 tags 必须是列表")

    return profile


def run(user, message, eval_result, semantic_result=None, db=None):
    intent = eval_result.get("intent", "综合学习")
    semantic_result = semantic_result or {}
    topic = semantic_result.get("topic") or eval_result.get("topic") or "当前主题"

    profile = {
        "level": semantic_result.get("level", "未确认"),
        "level_source": semantic_result.get("level_source", "none"),
        "level_evidence": semantic_result.get("level_evidence", ""),
        "needs_level_diagnosis": semantic_result.get("needs_level_diagnosis", True),
        "tags": [topic],
        "topic": topic,
        "knowledge_topic": topic,
        "intent": intent,
        "goal": intent,
        "subject_category": semantic_result.get("subject_category", "unknown"),
        "is_programming_related": semantic_result.get("is_programming_related", False),
        "should_generate_code_content": semantic_result.get("should_generate_code_content", False),
    }

    return _validate_profile(profile)
