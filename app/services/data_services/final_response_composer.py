INTERNAL_KEYS = {
    "debug",
    "raw_output",
    "agent_notes",
    "knowledge_chunks",
    "recommend_score",
    "matched_tags",
    "_recommend_rank",
    "pipeline_steps",
    "evidence",
    "teaching_sources",
    "external_evidence",
    "safety_summary",
}

INTERNAL_TEXT_MARKERS = [
    "多智能体处理链路",
    "知识库依据",
    "推理过程",
    "raw_output",
    "agent_notes",
    "knowledge_chunks",
    "recommend_score",
    "matched_tags",
    "_recommend_rank",
    "Agent",
    "-->",
    "当前课程库资料不足",
    "资料局限",
    "需要人工复核",
    "本回答基于当前课程库状态",
    "基于当前课程资料，",
    "基于当前课程资料",
    "基于课程资料，",
    "基于课程资料",
    "未编造内容",
]

STUDENT_PROGRESS = {
    "intent": ("understand", "理解学习需求"),
    "evidence": ("collect", "整理课程资料"),
    "profile": ("profile", "更新学习画像"),
    "answer": ("answer", "生成学习建议"),
    "teaching-source": ("match", "匹配学习资料"),
    "plan": ("plan", "生成学习路线"),
    "resource-plan": ("resources", "准备配套资源"),
    "safety": ("check", "完成内容检查"),
}


def _clean_text(value):
    text = str(value or "").strip()
    for marker in INTERNAL_TEXT_MARKERS:
        text = text.replace(marker, "")
    return text.strip(" ，,。；;：:")


def _strip_internal_fields(value):
    if isinstance(value, dict):
        return {
            key: _strip_internal_fields(item)
            for key, item in value.items()
            if key not in INTERNAL_KEYS
        }
    if isinstance(value, list):
        return [_strip_internal_fields(item) for item in value]
    if isinstance(value, str):
        return _clean_text(value)
    return value


def _format_structured_items(title, items):
    if not isinstance(items, list) or not items:
        return []

    lines = [f"**{title}**"]
    for item in items:
        if isinstance(item, dict):
            item_title = _clean_text(item.get("title") or "")
            detail = _clean_text(item.get("detail") or item.get("description") or "")
            if item_title and detail and item_title != detail:
                lines.append(f"- {item_title}：{detail}")
            elif item_title:
                lines.append(f"- {item_title}")
            elif detail:
                lines.append(f"- {detail}")
        else:
            text = _clean_text(item)
            if text:
                lines.append(f"- {text}")

    return lines if len(lines) > 1 else []


def _compose_content_from_tutor(tutor_result):
    content = _clean_text(tutor_result.get("content") or tutor_result.get("reply") or "")
    if content:
        return content

    summary = _clean_text(tutor_result.get("summary") or "")
    sections = []
    if summary:
        sections.append(summary)

    key_points = _format_structured_items("可以先抓住这几个重点", tutor_result.get("key_points"))
    if key_points:
        sections.append("\n".join(key_points))

    next_actions = _format_structured_items("建议下一步这样做", tutor_result.get("next_actions"))
    if next_actions:
        sections.append("\n".join(next_actions))

    caveats = [
        _clean_text(item)
        for item in tutor_result.get("caveats", [])
        if _clean_text(item)
    ] if isinstance(tutor_result.get("caveats"), list) else []
    if caveats:
        sections.append("\n".join(["**需要注意**", *[f"- {item}" for item in caveats]]))

    return "\n\n".join(section for section in sections if section).strip()


def _build_progress(pipeline_steps):
    progress = []
    for step in pipeline_steps or []:
        if not isinstance(step, dict) or step.get("status") == "skipped":
            continue
        public_step = STUDENT_PROGRESS.get(step.get("key") or "")
        if not public_step:
            continue
        public_key, label = public_step
        progress.append({
            "key": public_key,
            "label": label,
            "status": step.get("status") or "completed",
        })
    return progress


def _build_cards(path_result=None, resource_result=None, resource_status=None):
    cards = []
    path = path_result if isinstance(path_result, dict) else None
    resources = resource_result if isinstance(resource_result, list) else []
    resource_state = resource_status if isinstance(resource_status, dict) else {}

    if path:
        task_count = len(path.get("tasks") or [])
        cards.append({
            "type": "learning_path",
            "title": path.get("title") or "学习路线已生成",
            "status": "ready",
            "summary": f"已生成 {task_count} 个学习步骤，可在“规划”页查看和继续调整。",
            "action_text": "查看规划",
            "action_route": "/plan",
        })

    if resource_state.get("status") == "queued":
        resource_items = [
            {
                "title": item.get("title") or "配套学习资料",
                "type": item.get("type") or "学习资源",
                "status": item.get("status") or "整理中",
            }
            for item in (resource_state.get("items") or resources)[:6]
            if isinstance(item, dict)
        ]
        cards.append({
            "type": "resource_review",
            "title": "配套资料正在整理",
            "status": "pending",
            "summary": resource_state.get("message") or "配套资料正在整理，完成后会进入资源库。",
            "items": resource_items,
            "action_text": "查看资源库",
            "action_route": "/resource",
        })
        return _strip_internal_fields(cards)

    if resources:
        resource_items = [
            {
                "title": item.get("title") or "学习资源",
                "type": item.get("type") or "学习资源",
                "status": item.get("status") or "待审核",
            }
            for item in resources[:6]
            if isinstance(item, dict)
        ]
        cards.append({
            "type": "resource_review",
            "title": "配套学习资源已准备",
            "status": "pending_review",
            "summary": f"{len(resources)} 份配套资源已进入审核队列，通过后会出现在资源库。",
            "items": resource_items,
            "action_text": "查看资源库",
            "action_route": "/resource",
        })

    return _strip_internal_fields(cards)


def compose_student_answer(
    *,
    intent_result=None,
    knowledge_result=None,
    profile_result=None,
    tutor_result=None,
    plan_result=None,
    resource_result=None,
    resource_status=None,
    safety_result=None,
    pipeline_steps=None,
    trace_id="",
):
    tutor_result = tutor_result or {}
    content = _compose_content_from_tutor(tutor_result)

    if not content:
        content = "我已经整理好本轮学习建议。你可以继续补充学习目标、当前基础或具体卡点，我会据此调整学习路线和资源。"

    return {
        "message": {
            "content": content,
            "content_type": "student_answer",
        },
        "progress": _build_progress(pipeline_steps or []),
        "cards": _build_cards(plan_result, resource_result, resource_status),
        "trace_id": trace_id,
    }
