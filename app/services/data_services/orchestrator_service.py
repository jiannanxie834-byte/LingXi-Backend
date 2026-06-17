from app.services.llm_provider import chat

from app.services.data_services import (
    user_service,
    resource_service,
    learning_plan_service,
    profile_service,
    knowledge_evidence_service
)

from app.agents.evaluation_agent import run as eval_run
from app.agents.profile_agent import run as profile_run
from app.agents.planner_agent import run as planner_run
from app.agents.resource_agent import run as resource_run


def _pipeline_step(key: str, label: str, agent: str, status: str = "completed", detail: str = ""):
    return {
        "key": key,
        "label": label,
        "agent": agent,
        "status": status,
        "detail": detail,
    }


def _summarize_safety(resources):
    reviews = [item.get("safety_review") or {} for item in resources or []]
    reviews = [item for item in reviews if item]
    if not reviews:
        return {
            "risk_level": "待复核",
            "avg_score": 0,
            "total": 0,
            "high_risk": 0,
        }

    scores = [item.get("score", 0) for item in reviews]
    high_risk = len([item for item in reviews if item.get("risk_level") == "高风险"])
    medium_risk = len([item for item in reviews if item.get("risk_level") == "中风险"])
    risk_level = "高风险" if high_risk else ("中风险" if medium_risk else "低风险")

    return {
        "risk_level": risk_level,
        "avg_score": round(sum(scores) / len(scores)),
        "total": len(reviews),
        "high_risk": high_risk,
    }


def handle_learning_chat(username: str, message: str, db):
    """
    🎯 多智能体学习系统主入口
    """

    # =========================
    # 1. 获取用户信息
    # =========================
    user = user_service.get_user_by_username(db, username)

    # =========================
    # 2. 意图识别
    # =========================
    eval_result = eval_run(message)
    intent = eval_result.get("intent", "")
    topic = eval_result.get("topic", "")
    pipeline_steps = [
        _pipeline_step(
            "intent",
            "识别学习意图与课程主题",
            "意图识别 Agent",
            detail=f"{intent} / {topic}"
        )
    ]

    # =========================
    # 3. 课程知识库依据检索
    # =========================
    evidence_query = " ".join([message, topic or "", intent or ""]).strip()
    evidence = knowledge_evidence_service.search_course_evidence(
        db,
        evidence_query,
        limit=4
    )
    evidence_prompt = knowledge_evidence_service.format_evidence_for_prompt(evidence)
    pipeline_steps.append(_pipeline_step(
        "evidence",
        "检索课程知识库依据",
        "知识检索 Agent",
        status="completed" if evidence else "fallback",
        detail=f"命中 {len(evidence)} 条课程依据" if evidence else "未命中高置信依据，回答将提示核验"
    ))

    # =========================
    # 4. 用户画像分析
    # =========================
    profile_result = profile_run(user, message, eval_result)

    profile_update = profile_service.build_profile(
        user=user,
        message=message,
        intent=intent,
        knowledge_topic=topic,
        score=eval_result.get("score", 0),
        db=db
    )
    pipeline_steps.append(_pipeline_step(
        "profile",
        "更新动态学习画像",
        "画像建模 Agent",
        detail="已融合本轮对话、历史评价、规划和待办数据"
    ))

    # =========================
    # 5. 默认聊天回复
    # =========================
    chat_prompt = f"""
你是一个大学学习助手，请自然回答用户问题。

用户问题：{message}

课程知识库依据：
{evidence_prompt}

当前用户状态：
- 意图：{intent}
- 知识水平：{profile_result.get("level")}

要求：
- 优先依据“课程知识库依据”回答，并把无法确定的内容标记为需要核验
- 如果有合适依据，回答里可以简短说明“根据课程知识库”
- 不要生成学习计划
- 不要生成资源
- 像正常AI对话一样回答
"""

    reply_res = chat([
        {"role": "user", "content": chat_prompt}
    ])
    ai_reply = reply_res.get("content") if reply_res.get("ok") else (
        f"我先按本地课程知识库给你处理：当前识别到的主题是「{topic}」，"
        f"学习意图是「{intent}」。如果你需要，我可以继续生成学习路线和配套资源。"
    )
    pipeline_steps.append(_pipeline_step(
        "answer",
        "生成个性化辅导回复",
        "学习辅导 Agent",
        status="completed" if reply_res.get("ok") else "fallback",
        detail="大模型回复已生成" if reply_res.get("ok") else "已启用本地兜底回复"
    ))
    # =========================
    # 6. 是否生成学习路径和资源
    # =========================
    should_plan = intent in ["路径规划", "生成学习路径", "制定计划", "生成资源", "练习巩固", "实操训练"]

    path = None
    resources = []

    if should_plan:

        # 6.1 规划路径
        plan_result = planner_run(profile_result)
        pipeline_steps.append(_pipeline_step(
            "plan",
            "规划学习路径",
            "路径规划 Agent",
            detail=f"生成 {len(plan_result.get('steps', []))} 个学习步骤"
        ))

        # 6.2 资源规划
        resource_plan = resource_run(plan_result, profile_result)
        pipeline_steps.append(_pipeline_step(
            "resource-plan",
            "规划配套资源类型",
            "资源设计 Agent",
            detail=f"规划 {len(resource_plan.get('resources', []))} 类个性化资源"
        ))

        # 6.3 保存路径
        path = learning_plan_service.save_generated_plan(
            db=db,
            username=username,
            title=plan_result.get("title", "学习路径"),
            path_steps=plan_result.get("steps", []),
            resources=resource_plan.get("resources", [])
        )

        # 6.4 生成资源内容
        llm_outputs = []

        for item in resource_plan.get("resources", []):
            prompt = f"""
你是大学学习资源生成助手。

类型：{item.get('type')}
主题：{item.get('topic')}
学生水平：{profile_result.get('level')}
学习目标：{intent}

课程知识库依据：
{evidence_prompt}

要求：
- 内容必须适合高校课程学习场景
- 优先使用课程知识库依据，不确定的事实必须标注“需人工复核”
- 避免绝对化和不可验证结论
- 尽量补充课程章节、资料来源或需要人工复核的位置
- 如果类型是多模态学习包，请输出文字讲解、Mermaid 流程图、代码注释案例、分步题解、PPT 页纲和实践任务

输出：
- summary
- content，使用 Markdown
"""

            res = chat([{"role": "user", "content": prompt}])

            content = res.get("content", "") if res.get("ok") else ""

            llm_outputs.append({
                "summary": content[:200] if content else item.get("summary", ""),
                "content": content or item.get("content", ""),
                "source": item.get("source", "")
            })

        # 6.5 保存资源
        resources = resource_service.save_ai_generated_resources(
            db=db,
            resource_plan=resource_plan,
            llm_outputs=llm_outputs,
            uploader="资源生成 Agent"
        )
        safety_summary = _summarize_safety(resources)
        pipeline_steps.append(_pipeline_step(
            "safety",
            "完成内容安全与防幻觉自检",
            "内容安全 Agent",
            detail=f"{safety_summary['total']} 份资源，平均 {safety_summary['avg_score']} 分，{safety_summary['risk_level']}"
        ))
        ai_reply = f"""{ai_reply}

已同步生成 1 条学习路线和 {len(resources)} 份配套资源，资源会先进入管理员审核队列，通过后再展示给学生端。"""
    else:
        pipeline_steps.extend([
            _pipeline_step("plan", "规划学习路径", "路径规划 Agent", "skipped", "本轮意图不需要生成新路径"),
            _pipeline_step("resource-plan", "规划配套资源类型", "资源设计 Agent", "skipped", "本轮意图不需要生成新资源"),
            _pipeline_step("safety", "完成内容安全与防幻觉自检", "内容安全 Agent", "skipped", "无新增资源需要自检"),
        ])

    # =========================
    # 7. 更新用户状态
    # =========================
    updated_user = user_service.update_user_learning_profile(
        db,
        username,
        profile_update.get("tags", []),
        hours_delta=1,
        replace_tags=True
    )

    if updated_user:
        profile_update["tags"] = updated_user["tags"]
        profile_update["hours"] = updated_user["hours"]

    # =========================
    # 8. 返回
    # =========================
    return {
        "reply": ai_reply,
        "profile": profile_update,
        "path": path,
        "resources": resources,
        "intent": intent,
        "auto_generated": should_plan,
        "pipeline_steps": pipeline_steps,
        "safety_summary": _summarize_safety(resources),
        "evidence": evidence,
    }
