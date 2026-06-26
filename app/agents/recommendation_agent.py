from app.agents.agent_result_dto import AgentResultDTO


def run(resources: list, profile: dict = None, plan: dict = None) -> AgentResultDTO:
    profile = profile or {}
    plan_text = str(plan or "")

    def score(item):
        value = 50
        text = " ".join([item.get("title", ""), item.get("type", ""), item.get("summary", "")])
        if "代码" in text or "PyTorch" in text:
            value += 15 if "实践" in str(profile) or "代码" in str(profile) else 5
        if "练习" in text:
            value += 10 if "薄弱" in str(profile) or "错" in plan_text else 3
        if "视频" in text or "动画" in text or "导图" in text:
            value += 10 if "图" in str(profile) or "可视化" in str(profile) else 5
        return value

    ranked = sorted([{**item, "recommendation_score": score(item)} for item in resources], key=lambda x: x["recommendation_score"], reverse=True)
    return AgentResultDTO(
        agent_name="RecommendationAgent",
        input_summary=f"{len(resources)} artifacts",
        output={"resources": ranked},
        evidence_refs=[item.get("unit_id", "") for item in resources if item.get("unit_id")],
        quality_score=1.0 if ranked else 0.0,
    )
