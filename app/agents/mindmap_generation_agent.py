from app.agents.agent_result_dto import AgentResultDTO


GROUPS = [
    ("前置知识", ("前置", "基础", "定义", "概念", "复杂度", "数组", "链表", "栈", "队列", "递归")),
    ("核心概念", ("核心", "结构", "性质", "关系", "状态", "指针", "节点", "存储")),
    ("操作流程", ("流程", "步骤", "操作", "插入", "删除", "查找", "遍历", "访问", "转移", "排序", "匹配")),
    ("典型应用", ("应用", "场景", "任务", "项目", "括号", "路径", "编码", "调度", "窗口")),
    ("易错点", ("误区", "错误", "混淆", "忽略", "边界", "反例", "陷阱", "开销")),
    ("练习方向", ("练习", "题", "证明", "验证", "对比", "复盘", "实验", "代码")),
]


def _group_concepts(concepts):
    grouped = [(name, []) for name, _ in GROUPS]
    fallback = ("关联概念", [])
    for concept in concepts:
        item = str(concept or "").strip()
        if not item:
            continue
        matched = False
        for index, (_, keywords) in enumerate(GROUPS):
            if any(keyword.lower() in item.lower() for keyword in keywords):
                grouped[index][1].append(item)
                matched = True
                break
        if not matched:
            fallback[1].append(item)
    return [(name, items[:5]) for name, items in [*grouped, fallback] if items]


def _render_mermaid(topic: str, concepts) -> str:
    lines = ["mindmap", f"  root(({topic}))"]
    for group_name, items in _group_concepts(concepts):
        lines.append(f"    {group_name}")
        for item in items:
            lines.append(f"      {item}")
    return "\n".join(lines)


def run(topic: str, unit_id: str = "", concepts=None) -> AgentResultDTO:
    concepts = concepts or ["前置知识", "核心概念", "公式流程", "练习任务"]
    output = {
        "type": "mind_map",
        "title": f"{topic} 知识点思维导图",
        "content_format": "mermaid",
        "mermaid": _render_mermaid(topic, concepts),
    }
    return AgentResultDTO("MindMapGenerationAgent", input_summary=topic, output=output, evidence_refs=[unit_id] if unit_id else [], quality_score=0.9)
