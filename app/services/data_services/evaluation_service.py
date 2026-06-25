import json
import datetime
import uuid

from sqlalchemy.orm import Session
from app.models.schemas import EvaluationRecord
from app.services.data_services import (
    ai_course_map_service,
    knowledge_service,
    learning_plan_service,
    profile_service,
    resource_service,
    user_service,
)


COURSE_KNOWLEDGE = [
    {
        "topic": "计算机网络",
        "keywords": ["计网", "网络", "tcp", "udp", "三次握手", "四次挥手", "http", "https"],
        "chapter": "计算机网络 / TCP-IP 与应用层协议",
        "core": "分层模型、可靠传输、HTTP 请求响应与安全通信",
        "pitfalls": ["混淆 TCP 与 UDP 的适用场景", "只背三次握手流程而不理解状态变化", "忽略抓包验证"],
        "practice": "使用 Wireshark 抓取一次 HTTP 请求并标注每一层协议字段",
    },
    {
        "topic": "Python 数据分析",
        "keywords": ["python", "pandas", "数据分析", "numpy", "可视化", "matplotlib"],
        "chapter": "Python 数据分析 / 数据清洗与统计分析",
        "core": "数据读取、缺失值处理、分组统计、可视化表达",
        "pitfalls": ["没有检查缺失值就直接建模", "分组统计口径不一致", "图表只好看但没有表达结论"],
        "practice": "清洗一份学生学习行为数据并输出每周学习时长趋势",
    },
    {
        "topic": "人工智能",
        "keywords": ["人工智能", "机器学习", "深度学习", "模型", "神经网络", "分类", "训练"],
        "chapter": "人工智能 / 机器学习基础",
        "core": "监督学习、特征工程、训练验证划分、模型评估",
        "pitfalls": ["只看准确率不看混淆矩阵", "训练集和测试集泄漏", "没有记录实验参数"],
        "practice": "用公开数据集训练一个分类器并解释评估指标",
    },
    {
        "topic": "高等数学",
        "keywords": ["数学", "高数", "微积分", "导数", "积分", "极限", "函数", "建模"],
        "chapter": "高等数学 / 函数、极限、导数与积分",
        "core": "函数关系、极限思想、导数应用、积分累积与数学建模",
        "pitfalls": ["只套公式不解释变量含义", "忽略定义域和边界条件", "把计算结果和实际问题脱节"],
        "practice": "选择一个生活中的最优化问题，用函数建模并说明导数如何帮助决策",
    },
    {
        "topic": "大学物理",
        "keywords": ["物理", "力学", "电磁", "实验", "速度", "加速度", "牛顿", "能量"],
        "chapter": "大学物理 / 力学实验与能量分析",
        "core": "物理量测量、受力分析、能量守恒、实验误差与数据解释",
        "pitfalls": ["只背公式不画受力图", "忽略单位和量纲", "实验结论没有误差分析"],
        "practice": "设计一个小车斜面运动实验，记录数据并分析速度变化规律",
    },
    {
        "topic": "大学英语",
        "keywords": ["英语", "阅读", "写作", "作文", "口语", "听力", "翻译", "词汇"],
        "chapter": "大学英语 / 阅读理解与写作表达",
        "core": "主题句识别、段落结构、关键词推断、观点表达与语言修改",
        "pitfalls": ["逐词翻译导致句意割裂", "作文观点缺少论据", "忽略段落之间的逻辑衔接"],
        "practice": "围绕一个校园学习主题完成阅读批注，并改写一段 120 词短文",
    },
]


def _safe_json_load(data, default):
    try:
        return json.loads(data) if data else default
    except Exception:
        return default


def _safe_created_at(value):
    if not value:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat(sep=" ", timespec="seconds")
    return str(value)


def _evaluation_to_dict(record: EvaluationRecord):
    return {
        "id": record.id,
        "username": record.username,
        "topic": record.topic,
        "score": record.score,
        "level": record.level,
        "weak_points": _safe_json_load(record.weak_points, []),
        "suggestions": _safe_json_load(record.suggestions, []),
        "wrong_notes": record.wrong_notes or "",
        "answers": _safe_json_load(record.answers_json, {}),
        "generated_resource_id": record.generated_resource_id or "",
        "created_at": _safe_created_at(record.created_at)
    }


def _load_course_knowledge(db: Session):
    knowledge_rows = knowledge_service.get_course_knowledge(db)
    return knowledge_rows or COURSE_KNOWLEDGE


def _infer_knowledge(text: str, knowledge_base: list = None):
    lowered = (text or "").lower()
    items = knowledge_base or COURSE_KNOWLEDGE
    for item in items:
        if any(keyword in lowered for keyword in item["keywords"]):
            return item
    course_match = ai_course_map_service.match_ai_course_topic("", text)
    if course_match.get("matched"):
        core = "、".join(course_match.get("core_topics") or [])
        practice = (course_match.get("practice_tasks") or ["完成一次同主题练习并记录错因"])[0]
        pitfalls = {
            "模型评估": ["混淆准确率、精确率和召回率的适用场景", "只看单一指标而忽略业务代价"],
            "序列模型": ["混淆 RNN 与 LSTM 的记忆机制", "不理解遗忘门、输入门和输出门的作用"],
        }.get(course_match.get("chapter"), ["核心概念理解不稳定", "缺少同主题练习和错因复盘"])
        return {
            "topic": course_match.get("topic") or course_match.get("chapter"),
            "keywords": course_match.get("core_topics") or [course_match.get("topic")],
            "chapter": f"人工智能 / {course_match.get('chapter')}",
            "core": core or course_match.get("topic") or "人工智能课程核心知识点",
            "pitfalls": pitfalls,
            "practice": practice,
        }
    return items[2] if len(items) > 2 else COURSE_KNOWLEDGE[2]


def _level_from_score(score: int):
    if score >= 85:
        return "掌握较好"
    if score >= 70:
        return "基本掌握"
    if score >= 55:
        return "需要巩固"
    return "重点补救"


def _score_evaluation(text: str, confidence: int, knowledge: dict):
    content = (text or "").strip().lower()
    length_score = min(25, len(content) // 8)
    keyword_hits = sum(1 for keyword in knowledge["keywords"] if keyword in content)
    keyword_score = min(20, keyword_hits * 5)
    confidence_score = max(0, min(25, int(confidence or 0) // 4))
    reflection_score = 0

    if any(word in text for word in ["因为", "原因", "错因", "理解", "步骤", "复盘"]):
        reflection_score += 15
    if any(word in text for word in ["不会", "不懂", "总是错", "混淆", "记不住"]):
        reflection_score -= 8

    score = max(35, min(96, 35 + length_score + keyword_score + confidence_score + reflection_score))
    return score, _level_from_score(score)


def _build_diagnosis_content(knowledge: dict, notes: str, score: int, level: str, weak_points: list, suggestions: list):
    weak_lines = "\n".join([f"- {item}" for item in weak_points])
    suggestion_lines = "\n".join([f"{index}. {item}" for index, item in enumerate(suggestions, 1)])

    return f"""# {knowledge['topic']} 错题诊断与学习反馈报告

## 诊断得分
{score} 分，掌握等级：{level}

## 学习内容摘要
{notes or "学生暂未填写详细错题描述，系统仅根据本次评价入口生成基础诊断。"}

## 诊断依据
- 本报告依据学生在评价页提交的错题说明、作答摘要和自评置信度生成。
- 当前反馈文本：{notes or "暂无详细错题说明"}
- 未使用平台总学习时长推断本主题掌握水平。

## 主要薄弱点
{weak_lines}

## 补救建议
{suggestion_lines}

## 下一轮学习任务
完成「{knowledge['practice']}」，并记录至少 2 条错因复盘。
"""


def _build_diagnosis_resource(knowledge: dict, title: str, notes: str, score: int, level: str, weak_points: list, suggestions: list):
    return {
        "type": "错题诊断与学习反馈报告",
        "title": title,
        "summary": f"{level}：识别出 {len(weak_points)} 个薄弱点，并生成补救路线。",
        "source": f"{knowledge['chapter']} / 学习评价 Agent",
        "agent_notes": "由学习评价 Agent 根据学生作答、错题描述或本次评价反馈生成；未使用总学习时长推断本主题水平，建议管理员核对诊断建议是否贴合课程要求。",
        "content": _build_diagnosis_content(knowledge, notes, score, level, weak_points, suggestions),
    }


def _build_fix_steps(knowledge: dict, level: str, first_weak_point: str):
    return [
        f"第 1 步：复盘诊断报告，重点标记「{first_weak_point}」。",
        f"第 2 步：重读「{knowledge['chapter']}」中的核心内容：{knowledge['core']}。",
        "第 3 步：完成诊断报告中的补救建议，并记录仍不确定的问题。",
        f"第 4 步：完成学科实践应用任务：{knowledge['practice']}。",
        f"第 5 步：重新提交一次学习评价，比较当前等级「{level}」是否提升。",
    ]


# =========================
# 保存评价记录（DB由外部传入）
# =========================
def save_evaluation_record(
    db: Session,
    username: str,
    topic: str,
    score: int,
    level: str,
    weak_points: list,
    suggestions: list,
    wrong_notes: str,
    answers: dict,
    generated_resource_id: str = ""
):
    try:
        record = EvaluationRecord(
            id=str(uuid.uuid4()),
            username=username,
            topic=topic,
            score=score,
            level=level,
            weak_points=json.dumps(weak_points or [], ensure_ascii=False),
            suggestions=json.dumps(suggestions or [], ensure_ascii=False),
            wrong_notes=wrong_notes or "",
            answers_json=json.dumps(answers or {}, ensure_ascii=False),
            generated_resource_id=generated_resource_id,
            created_at=datetime.datetime.now()
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return _evaluation_to_dict(record)

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"保存评价记录失败: {str(e)}"
        }


# =========================
# 查询评价记录
# =========================
def get_evaluation_records(db: Session, username: str):
    try:
        records = (
            db.query(EvaluationRecord)
            .filter(EvaluationRecord.username == username)
            .order_by(EvaluationRecord.created_at.desc())
            .all()
        )

        return [_evaluation_to_dict(r) for r in records]

    except Exception as e:
        return {
            "success": False,
            "message": f"获取评价记录失败: {str(e)}"
        }


def handle_learning_evaluation(
    db: Session,
    username: str,
    topic: str,
    wrong_notes: str,
    answer_summary: str,
    confidence: int = 60
):
    merged_text = f"{topic}\n{wrong_notes}\n{answer_summary}"
    knowledge = _infer_knowledge(merged_text, _load_course_knowledge(db))
    score, level = _score_evaluation(merged_text, confidence, knowledge)

    weak_points = [
        knowledge["pitfalls"][0],
        knowledge["pitfalls"][1],
        "缺少实践验证和错因复盘" if score < 75 else "需要继续保持复盘记录",
    ]
    suggestions = [
        f"回看「{knowledge['chapter']}」中关于 {knowledge['core']} 的内容。",
        "先完成分层练习题中的概念判断题，再做应用题。",
        f"完成实践任务：{knowledge['practice']}。",
        "把本次错因写入学习画像，下一轮路径优先补弱。",
    ]

    diagnosis_resource = _build_diagnosis_resource(
        knowledge=knowledge,
        title=f"{knowledge['topic']} 错题诊断报告",
        notes=wrong_notes or answer_summary,
        score=score,
        level=level,
        weak_points=weak_points,
        suggestions=suggestions,
    )
    saved_resources = resource_service.insert_generated_resources(
        db,
        [diagnosis_resource],
        uploader="学习评价 Agent",
        applicant_username=username,
    )
    generated_resource_id = saved_resources[0]["id"] if saved_resources else ""

    updated_user = user_service.update_user_learning_profile(
        db,
        username,
        [knowledge["topic"]],
        hours_delta=1 if score < 75 else 0,
        replace_tags=True,
    )

    remedial_plan = None
    if score < 80:
        remedial_plan = learning_plan_service.save_generated_plan(
            db=db,
            username=username,
            title=f"{knowledge['topic']} · 错题修复路线",
            path_steps=_build_fix_steps(knowledge, level, weak_points[0]),
            resources=[diagnosis_resource],
        )

    record = save_evaluation_record(
        db=db,
        username=username,
        topic=knowledge["topic"],
        score=score,
        level=level,
        weak_points=weak_points,
        suggestions=suggestions,
        wrong_notes=wrong_notes,
        answers={
            "topic": topic,
            "wrong_notes": wrong_notes,
            "answer_summary": answer_summary,
            "confidence": confidence,
        },
        generated_resource_id=generated_resource_id,
    )

    profile_user = user_service.get_user_by_username(db, username)
    profile = profile_service.build_profile(
        user=profile_user,
        message=merged_text,
        intent="练习巩固",
        knowledge_topic=knowledge["topic"],
        score=score,
        db=db,
        semantic_result={
            "topic": knowledge["topic"],
            "subject_category": "computer_science",
            "level": level,
            "level_source": "current_evaluation",
            "level_evidence": f"本次学习评价得分 {score}，反馈主题：{knowledge['topic']}",
            "needs_level_diagnosis": False,
        },
    )
    if updated_user:
        profile["tags"] = profile_service.merge_tags(updated_user["tags"], profile.get("tags", []))
        profile["knowledge_tags"] = profile["tags"]
        profile["hours"] = updated_user["hours"]

    return {
        "record": record,
        "score": score,
        "level": level,
        "weak_points": weak_points,
        "suggestions": suggestions,
        "generated_resource": saved_resources[0] if saved_resources else diagnosis_resource,
        "remedial_plan": remedial_plan,
        "profile": profile,
    }


def handle_auto_evaluation(db: Session, username: str):
    user = user_service.get_user_by_username(db, username)
    plans = learning_plan_service.get_plans_by_username(db, username)
    history = get_evaluation_records(db, username)
    resources = resource_service.get_all_resources(db)

    task_status = {"completed": 0, "active": 0, "pending": 0}
    plan_text = []

    for plan in plans:
        plan_text.append(plan.get("title", ""))
        for task in plan.get("tasks", []):
            status = task.get("status", "pending")
            if status in task_status:
                task_status[status] += 1
            plan_text.extend([task.get("title", ""), task.get("desc", "")])

    total_tasks = sum(task_status.values())
    completion_rate = round(task_status["completed"] / total_tasks * 100) if total_tasks else 0
    recent_history = history[:3] if isinstance(history, list) else []
    recent_avg_score = round(sum(item.get("score", 0) for item in recent_history) / len(recent_history)) if recent_history else None
    source_text = " ".join([
        user.tags if user else "",
        " ".join(plan_text),
        " ".join([item.get("title", "") for item in resources[:12]]),
        " ".join([item.get("topic", "") for item in recent_history]),
    ])

    knowledge = _infer_knowledge(source_text, _load_course_knowledge(db))
    hours = user.hours if user else 0
    score = 62 + min(12, hours // 4) + round(completion_rate * 0.18)
    if recent_avg_score is not None:
        score = round(score * 0.45 + recent_avg_score * 0.55)
    if task_status["pending"] > task_status["completed"]:
        score -= 6
    score = max(42, min(96, score))
    level = _level_from_score(score)

    weak_points = list(dict.fromkeys([
        knowledge["pitfalls"][0],
        "学习路线中仍有较多待完成任务" if task_status["pending"] else "需要持续复盘已完成任务",
        "平台记录显示需要继续补齐实践验证",
    ]))[:4]
    suggestions = [
        f"优先完成当前规划中的 active 任务，再处理 {task_status['pending']} 个待完成任务。",
        f"围绕「{knowledge['chapter']}」复习 {knowledge['core']}。",
        "对最近一次错题诊断报告做二次复盘，比较薄弱点是否减少。",
        f"完成实践任务：{knowledge['practice']}。",
    ]
    auto_notes = (
        f"系统基于平台数据自动诊断：累计学习 {hours} 小时，"
        f"任务完成率 {completion_rate}%，"
        f"待完成任务 {task_status['pending']} 个，"
        f"近三次评价均分 {recent_avg_score if recent_avg_score is not None else '暂无'}。"
    )

    diagnosis_resource = _build_diagnosis_resource(
        knowledge=knowledge,
        title=f"{knowledge['topic']} 平台自动诊断报告",
        notes=auto_notes,
        score=score,
        level=level,
        weak_points=weak_points,
        suggestions=suggestions,
    )
    saved_resources = resource_service.insert_generated_resources(
        db,
        [diagnosis_resource],
        uploader="学习评价 Agent",
        applicant_username=username,
    )
    generated_resource_id = saved_resources[0]["id"] if saved_resources else ""

    updated_user = user_service.update_user_learning_profile(
        db,
        username,
        [knowledge["topic"]],
        hours_delta=0,
        replace_tags=True,
    )

    remedial_plan = None
    if score < 82:
        remedial_plan = learning_plan_service.save_generated_plan(
            db=db,
            username=username,
            title=f"{knowledge['topic']} · 自动补弱路线",
            path_steps=_build_fix_steps(knowledge, level, weak_points[0]),
            resources=[diagnosis_resource],
        )

    record = save_evaluation_record(
        db=db,
        username=username,
        topic=knowledge["topic"],
        score=score,
        level=level,
        weak_points=weak_points,
        suggestions=suggestions,
        wrong_notes=auto_notes,
        answers={
            "mode": "auto",
            "hours": hours,
            "task_status": task_status,
            "completion_rate": completion_rate,
            "recent_avg_score": recent_avg_score,
        },
        generated_resource_id=generated_resource_id,
    )

    profile_user = user_service.get_user_by_username(db, username)
    profile = profile_service.build_profile(
        user=profile_user,
        message=auto_notes,
        intent="练习巩固",
        knowledge_topic=knowledge["topic"],
        score=score,
        db=db,
    )
    if updated_user:
        profile["tags"] = profile_service.merge_tags(updated_user["tags"], profile.get("tags", []))
        profile["knowledge_tags"] = profile["tags"]
        profile["hours"] = updated_user["hours"]

    return {
        "record": record,
        "score": score,
        "level": level,
        "weak_points": weak_points,
        "suggestions": suggestions,
        "generated_resource": saved_resources[0] if saved_resources else diagnosis_resource,
        "remedial_plan": remedial_plan,
        "profile": profile,
        "auto_summary": auto_notes,
        "data_sources": ["学习画像", "规划任务状态", "历史评价记录", "Agent 生成资源"],
    }
