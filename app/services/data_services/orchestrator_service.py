from app.services.llm_provider import chat

from app.services.data_services import (
    user_service,
    resource_service,
    learning_plan_service,
    profile_service
)

from app.agents.evaluation_agent import run as eval_run
from app.agents.profile_agent import run as profile_run
from app.agents.planner_agent import run as planner_run
from app.agents.resource_agent import run as resource_run


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

    # =========================
    # 3. 用户画像分析
    # =========================
    profile_result = profile_run(user, message, eval_result)

    profile_update = profile_service.build_profile(
        user=user,
        message=message,
        intent=intent,
        knowledge_topic=topic,
        score=eval_result.get("score", 0)
    )
    profile_update["tags"] = list(dict.fromkeys(profile_update.get("tags", []) + profile_result.get("tags", [])))

    # =========================
    # 4. 默认聊天回复
    # =========================
    chat_prompt = f"""
你是一个大学学习助手，请自然回答用户问题。

用户问题：{message}

当前用户状态：
- 意图：{intent}
- 知识水平：{profile_result.get("level")}

要求：
- 不要生成学习计划
- 不要生成资源
- 像正常AI对话一样回答
"""

    reply_res = chat([
        {"role": "user", "content": chat_prompt}
    ])
    print("LLM RESULT:", reply_res)
    ai_reply = reply_res.get("content") if reply_res.get("ok") else (
        f"我先按本地课程知识库给你处理：当前识别到的主题是「{topic}」，"
        f"学习意图是「{intent}」。如果你需要，我可以继续生成学习路线和配套资源。"
    )
    # =========================
    # 5. 是否生成学习路径和资源
    # =========================
    should_plan = intent in ["路径规划", "生成学习路径", "制定计划", "生成资源", "练习巩固", "实操训练"]

    path = None
    resources = []

    if should_plan:

        # 6.1 规划路径
        plan_result = planner_run(profile_result)

        # 6.2 资源规划
        resource_plan = resource_run(plan_result, profile_result)

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

输出：
- summary
- content
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
        ai_reply = f"""{ai_reply}

已同步生成 1 条学习路线和 {len(resources)} 份配套资源，资源会先进入管理员审核队列，通过后再展示给学生端。"""

    # =========================
    # 7. 更新用户状态
    # =========================
    updated_user = user_service.update_user_learning_profile(
        db,
        username,
        profile_update.get("tags", []),
        hours_delta=1
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
        "auto_generated": should_plan
    }
