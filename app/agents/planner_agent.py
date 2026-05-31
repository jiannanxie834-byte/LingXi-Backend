def run(profile):
    topic = profile.get("topic") or profile.get("knowledge_topic") or "当前主题"
    intent = profile.get("intent") or profile.get("goal") or "综合学习"

    return {
        "title": f"{topic} · {intent}路线",
        "steps": [
            f"第 1 步：定位 {topic} 的核心概念和当前卡点",
            f"第 2 步：完成 {topic} 的专业课程讲解文档阅读",
            "第 3 步：用知识点思维导图整理关键关系",
            "第 4 步：完成分层练习题并记录错因",
            "第 5 步：完成学科实践应用任务并提交复盘"
        ]
    }
