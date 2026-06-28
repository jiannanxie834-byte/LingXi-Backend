from app.services.data_services import (
    course_scope_service,
    dsa_course_map_service,
    resource_artifact_type_service as artifact_types,
)


def _validate_plan(plan):
    if not plan.get("title"):
        raise RuntimeError("路径规划结果缺少 title")
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        raise RuntimeError("路径规划结果 steps 必须是非空列表")

    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise RuntimeError(f"路径规划第 {index} 步必须是对象")
        for field in ["title", "objective", "resource_focus", "status"]:
            if field not in step:
                raise RuntimeError(f"路径规划第 {index} 步缺少 {field}")
        if not isinstance(step["resource_focus"], list):
            raise RuntimeError(f"路径规划第 {index} 步 resource_focus 必须是列表")

    return plan


def _step(title, objective, resource_focus, status="pending", unit_id=""):
    return {
        "title": title,
        "objective": objective,
        "resource_focus": resource_focus,
        "status": status,
        "unit_id": unit_id,
    }


def _unit_text(items, fallback="暂无"):
    titles = []
    for item in items or []:
        if isinstance(item, dict):
            text = item.get("title") or item.get("name") or item.get("unit_title") or item.get("unit_id") or ""
        else:
            text = str(item or "")
        unit = dsa_course_map_service.get_unit(text)
        if unit:
            text = unit.get("title") or text
        if text and not text.startswith(("dsa_", "sec_", "chapter_")):
            titles.append(text)
    return "、".join(list(dict.fromkeys(titles))) or fallback


def _project_steps(course_match, topic):
    unit_id = course_match.get("unit_id") or ""
    return [
        _step(
            "第 1 步：锁定项目目标与验收标准",
            f"围绕「{topic}」明确数据集、模型、评估指标、提交物和两周节奏。",
            [artifact_types.PROJECT_BRIEF, artifact_types.PPT_OUTLINE],
            "active",
            unit_id,
        ),
        _step(
            "第 2 步：补齐关键前置知识",
            f"先检查前置知识：{_unit_text(course_match.get('prerequisites'))}。",
            [artifact_types.COURSE_NOTE, artifact_types.MIND_MAP, artifact_types.EXERCISE_SET],
            "pending",
            unit_id,
        ),
        _step(
            "第 3 步：完成算法最小实验",
            "用可运行代码跑通输入样例、核心函数、边界用例、复杂度记录和调试输出。",
            [artifact_types.CODE_LAB, artifact_types.VIDEO_RECOMMENDATION, artifact_types.PERSONALIZED_VIDEO_GUIDE],
            "pending",
            unit_id,
        ),
        _step(
            "第 4 步：解释模型结构与训练现象",
            "结合曲线、输出 shape、错误样本和可视化结果复盘模型表现。",
            [artifact_types.INTERACTIVE_ANIMATION, artifact_types.ANIMATION_STORYBOARD, artifact_types.EXERCISE_SET],
            "pending",
            unit_id,
        ),
        _step(
            "第 5 步：整理项目报告与演示",
            "输出实验报告、PPT 大纲、复现实验说明和下一步改进方向。",
            [artifact_types.PPT_OUTLINE, artifact_types.PROJECT_BRIEF],
            "pending",
            unit_id,
        ),
    ]


def run(profile, semantic_result=None):
    semantic_result = semantic_result or {}
    topic = course_scope_service.normalize_course_topic(
        semantic_result.get("display_topic")
        or profile.get("topic")
        or profile.get("knowledge_topic")
        or semantic_result.get("normalized_topic")
        or semantic_result.get("topic")
        or "当前主题"
    )
    course_match = (
        semantic_result.get("dsa_course_map")
        or semantic_result.get("ai_course_map")
        or dsa_course_map_service.match_dsa_topic(topic)
    )

    if not course_match.get("matched"):
        intro_unit_id = (dsa_course_map_service.get_intro_unit() or {}).get("unit_id", "")
        return _validate_plan({
            "title": f"{topic} · 主题澄清路线",
            "steps": [
                _step("第 1 步：确认是否属于《数据结构与算法》课程", "请补充复杂度分析、线性结构、排序查找、树图、动态规划或算法项目等具体知识点。", [artifact_types.EXERCISE_SET], "active", intro_unit_id),
                _step("第 2 步：完成基础水平诊断", "补充已学内容、目标水平和可投入时间，再生成正式路线。", [artifact_types.EXERCISE_SET], "pending", intro_unit_id),
            ],
        })

    unit = course_match.get("unit") or {}
    unit_id = course_match.get("unit_id") or unit.get("unit_id") or ""
    chapter = course_match.get("chapter") or "《数据结构与算法》课程"
    normalized_topic = course_match.get("display_topic") or semantic_result.get("display_topic") or topic or course_match.get("normalized_topic")
    core_topics = course_match.get("core_topics") or unit.get("core_concepts") or [normalized_topic]
    prerequisites = course_match.get("prerequisites") or unit.get("prerequisites") or []
    misconceptions = course_match.get("common_misconceptions") or unit.get("common_misconceptions") or []
    practice_tasks = course_match.get("practice_tasks") or []
    need_type = semantic_result.get("learning_need_type") or course_match.get("learning_need_type")
    scope_level = semantic_result.get("scope_level") or course_match.get("scope_level") or ""

    if scope_level == "course":
        return _validate_plan({
            "title": f"{normalized_topic} · 课程导学、诊断与学习路径",
            "steps": [
                _step("第 1 步：完成入门诊断", "先确认循环、函数、数组/列表、基础数学表达和代码调试能力。", [artifact_types.EXERCISE_SET], "active", unit_id),
                _step("第 2 步：建立课程全局地图", "了解数据结构、复杂度分析、算法设计思想、代码实现和题目训练之间的关系。", [artifact_types.COURSE_NOTE, artifact_types.MIND_MAP], "pending", unit_id),
                _step("第 3 步：选择第一阶段切入点", "根据诊断结果在复杂度、线性结构、递归回溯、排序查找或树图基础中选择起点。", [artifact_types.READING_PACK, artifact_types.VIDEO_RECOMMENDATION], "pending", unit_id),
                _step("第 4 步：按阶段推进学习", "后续只在确定具体章节或知识点后生成配套资源，避免一次性铺开全部章节。", [artifact_types.COURSE_NOTE, artifact_types.EXERCISE_SET], "pending", unit_id),
            ],
        })

    if scope_level == "comparison":
        compare_units = semantic_result.get("compare_units") or []
        compare_titles = [item.get("title") for item in compare_units if item.get("title")]
        return _validate_plan({
            "title": f"{normalized_topic} · 对比学习路线",
            "steps": [
                _step("第 1 步：分别确认两个对象的定义", f"先独立说明：{_unit_text(compare_titles, normalized_topic)}。", [artifact_types.COURSE_NOTE], "active", unit_id),
                _step("第 2 步：建立差异表", "从结构、输入输出、适用场景、优势局限和常见误区五个维度对比。", [artifact_types.MIND_MAP, artifact_types.READING_PACK], "pending", unit_id),
                _step("第 3 步：用题目检验理解", "完成对比辨析题和场景选择题，避免只背结论。", [artifact_types.EXERCISE_SET], "pending", unit_id),
            ],
        })

    if need_type == "project" or "项目" in normalized_topic:
        return _validate_plan({
            "title": f"{normalized_topic} · 个性化项目学习路线",
            "steps": _project_steps(course_match, normalized_topic),
        })

    steps = [
        _step(
            "第 1 步：确认前置基础",
            f"先用自然语言复述「{_unit_text(prerequisites, '循环、函数、数组和基本调试能力')}」这些前置基础的作用，再进入「{chapter}」的当前主题学习。",
            [artifact_types.COURSE_NOTE, artifact_types.EXERCISE_SET],
            "active",
            unit_id,
        ),
        _step(
            "第 2 步：建立知识结构",
            f"围绕 {normalized_topic} 梳理核心概念：{_unit_text(core_topics)}。",
            [artifact_types.MIND_MAP, artifact_types.INTERACTIVE_ANIMATION],
            "pending",
            unit_id,
        ),
        _step(
            "第 3 步：攻克核心机制",
            f"重点理解「{normalized_topic}」的公式/流程、适用场景和常见误区：{_unit_text(misconceptions)}。",
            [artifact_types.COURSE_NOTE, artifact_types.VIDEO_RECOMMENDATION, artifact_types.PERSONALIZED_VIDEO_GUIDE],
            "pending",
            unit_id,
        ),
        _step(
            "第 4 步：完成分层练习",
            "完成选择题、判断题、计算题、代码补全题和实验分析题，并记录答案依据与错因。",
            [artifact_types.EXERCISE_SET],
            "pending",
            unit_id,
        ),
    ]

    if course_match.get("requires_code") or semantic_result.get("requires_code"):
        steps.append(_step(
            "第 5 步：完成代码实验",
            practice_tasks[0] if practice_tasks else f"完成一个围绕 {normalized_topic} 的代码实验，并记录输入输出、边界样例、时间复杂度和调试过程。",
            [artifact_types.CODE_LAB, artifact_types.PROJECT_BRIEF],
            "pending",
            unit_id,
        ))
    else:
        steps.append(_step(
            "第 5 步：形成复盘材料",
            "把概念解释、易错点、练习错因和下一步问题整理成课堂展示或复习材料。",
            [artifact_types.PPT_OUTLINE, artifact_types.READING_PACK],
            "pending",
            unit_id,
        ))

    return _validate_plan({
        "title": f"{normalized_topic} · {chapter}学习路线",
        "steps": steps,
    })
