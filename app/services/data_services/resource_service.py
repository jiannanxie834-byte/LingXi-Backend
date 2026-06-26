import datetime
import json
import logging
import re
from collections import Counter

from sqlalchemy.orm import Session

from app.models.schemas import (
    EvaluationRecord,
    LearningPlan,
    Resource,
    ResourceType,
    User,
)
from app.services.data_services import (
    content_guard_service,
    resource_artifact_type_service as artifact_types,
    resource_artifact_service,
    resource_policy_service,
    resource_quality_gate,
    system_message_service,
)
from app.services.data_services.knowledge_tag_service import (
    extract_knowledge_tags_from_text,
    summarize_knowledge_tags,
)

logger = logging.getLogger(__name__)

DEFAULT_RESOURCE_TYPES = [
    *artifact_types.ACTIVE_ARTIFACT_TYPES,
    *artifact_types.EXPORTABLE_ARTIFACT_TYPES,
    *artifact_types.EVENT_TRIGGERED_ARTIFACT_TYPES,
]

DEPRECATED_AI_RESOURCE_TYPES = set(artifact_types.DEPRECATED_ARTIFACT_TYPES)

DEPRECATED_RESOURCE_TYPES = set(artifact_types.DEPRECATED_ARTIFACT_TYPES)

SYSTEM_UPLOADERS = {
    "system",
    "课程知识库种子",
    "资源生成 Agent",
    "学习评价 Agent",
    "AI-Agent",
}


# =========================
# tools
# =========================

def _is_deprecated_resource_type(type_name: str):
    normalized_type = (type_name or "").strip()
    return artifact_types.is_deprecated(normalized_type)


def _new_resource_id():
    return f"RES{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"


def _now_text():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_json_load(value, default):
    try:
        return json.loads(value) if value else default
    except Exception:
        return default


def _compact_text(value):
    return re.sub(r"\s+", "", str(value or "").lower())


def _split_tags(value):
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _canonical_term(value):
    term = str(value or "").strip(" ，,。.;；:：、/\\|[]（）()")
    if term.endswith(("和", "与", "及", "或")) and len(term) > 2:
        term = term[:-1]
    upper_aliases = {
        "ppt": "PPT",
        "rag": "RAG",
        "llm": "LLM",
        "nlp": "NLP",
        "tp": "TP",
        "fp": "FP",
        "tn": "TN",
        "fn": "FN",
    }
    return upper_aliases.get(term.lower(), term)


def _text_terms(values):
    text = "\n".join(str(item or "") for item in values if item)
    terms = set(extract_knowledge_tags_from_text(text))
    raw_terms = re.findall(r"[a-z0-9_+#.]+|[\u4e00-\u9fff]{2,}", _compact_text(text))

    stop_terms = {
        "学习", "资源", "课程", "知识", "需要", "建议", "当前", "完成", "进行", "暂无",
        "任务", "路线", "计划", "薄弱点", "诊断", "报告", "内容", "学生",
        "学习资源", "课程资源", "资源生成", "多模态学习", "知识点", "系统",
    }
    for term in raw_terms:
        term = _canonical_term(term)
        if term in stop_terms:
            continue
        if 2 <= len(term) <= 18:
            terms.add(term)

    return list(terms)


def _count_matches(resource_text, terms):
    compact = _compact_text(resource_text)
    matched = []
    for term in terms:
        term = _canonical_term(term)
        compact_term = _compact_text(term)
        if compact_term and compact_term in compact:
            matched.append(term)
    return list(dict.fromkeys(matched))


def _resource_text(resource):
    return "\n".join([
        resource.title or "",
        resource.type or "",
        resource.summary or "",
        resource.content or "",
        resource.source or "",
    ])


def _load_recommendation_context(db: Session, username: str):
    user = None
    if username:
        user = db.query(User).filter(User.username == username).first()

    profile_tags = _split_tags(user.tags if user else "")
    recent_records = []
    weak_points = []
    evaluated_topics = []
    recent_scores = []
    generated_resource_ids = []

    if username:
        recent_records = (
            db.query(EvaluationRecord)
            .filter(EvaluationRecord.username == username)
            .order_by(EvaluationRecord.created_at.desc())
            .limit(6)
            .all()
        )

    for record in recent_records:
        evaluated_topics.append(record.topic or "")
        recent_scores.append(record.score or 0)
        generated_resource_ids.append(record.generated_resource_id or "")
        weak_points.extend(_safe_json_load(record.weak_points, []))
        weak_points.append(record.wrong_notes or "")

    plans = []
    if username:
        plan_record = (
            db.query(LearningPlan)
            .filter(LearningPlan.username == username)
            .first()
        )
        plans = _safe_json_load(plan_record.plans_json if plan_record else "", [])

    plan_fragments = []
    active_fragments = []
    completed_count = 0
    total_count = 0

    for plan in plans if isinstance(plans, list) else []:
        plan_fragments.append(plan.get("title", ""))
        for task in plan.get("tasks", []):
            total_count += 1
            status = str(task.get("status", "")).lower()
            fragment = " ".join([
                task.get("title", ""),
                task.get("desc", ""),
                " ".join(str(item) for item in task.get("resources", [])),
            ])
            plan_fragments.append(fragment)
            if status in {"active", "pending", "进行中", "待开始"}:
                active_fragments.append(fragment)
            if status in {"completed", "done", "已完成"} or task.get("done"):
                completed_count += 1

    recent_avg_score = round(sum(recent_scores) / len(recent_scores)) if recent_scores else None
    plan_completion_rate = round(completed_count / total_count * 100) if total_count else None
    topic_candidates = summarize_knowledge_tags(profile_tags + evaluated_topics + _text_terms(active_fragments))

    return {
        "user": user,
        "profile_tags": summarize_knowledge_tags(profile_tags),
        "weak_points": weak_points,
        "evaluated_topics": summarize_knowledge_tags(evaluated_topics),
        "recent_avg_score": recent_avg_score,
        "generated_resource_ids": [item for item in generated_resource_ids if item],
        "plan_fragments": plan_fragments,
        "active_fragments": active_fragments,
        "plan_completion_rate": plan_completion_rate,
        "topic_candidates": topic_candidates,
    }


def _preferred_resource_types(context):
    preferred = Counter()
    avg_score = context.get("recent_avg_score")
    active_text = _compact_text(" ".join(context.get("active_fragments") or []))
    weak_text = _compact_text(" ".join(context.get("weak_points") or []))

    if avg_score is not None and avg_score < 75:
        preferred[artifact_types.EXERCISE_SET] += 3
        preferred[artifact_types.DIAGNOSTIC_REPORT] += 3
        preferred[artifact_types.MIND_MAP] += 1

    if any(word in active_text or word in weak_text for word in ["实践", "项目", "实验", "应用", "代码", "动手"]):
        preferred[artifact_types.CODE_LAB] += 3
        preferred[artifact_types.PROJECT_BRIEF] += 2

    if any(word in active_text or word in weak_text for word in ["概念", "原理", "框架", "理解", "关系"]):
        preferred[artifact_types.COURSE_NOTE] += 2
        preferred[artifact_types.MIND_MAP] += 2

    if any(word in active_text or word in weak_text for word in ["拓展", "阅读", "论文", "资料"]):
        preferred[artifact_types.READING_PACK] += 3

    return preferred


def _recommendation_source_text(context):
    fragments = []
    fragments.extend(context.get("evaluated_topics") or [])
    fragments.extend(context.get("profile_tags") or [])
    fragments.extend(context.get("topic_candidates") or [])
    fragments.extend(context.get("active_fragments") or [])
    fragments.extend(context.get("weak_points") or [])
    return "\n".join(str(item or "") for item in fragments if item)


def _resource_to_dict(resource: Resource):
    raw_notes = resource.agent_notes or ""
    safety_review = content_guard_service.extract_review(raw_notes)

    return {
        "id": resource.id,
        "title": resource.title,
        "type": resource.type,
        "status": resource.status,
        "uploader": resource.uploader,
        "applicant_username": resource.applicant_username or "",
        "time": resource.time,
        "summary": resource.summary or "",
        "content": resource.content or "",
        "source": resource.source or "",
        "agent_notes": content_guard_service.strip_review_block(raw_notes),
        "safety_review": safety_review,
        "review_comment": resource.review_comment or "",
        "reviewed_at": resource.reviewed_at or "",
    }


def _with_content_review(item: dict, reviewer: str, semantic_result: dict = None):
    review = content_guard_service.review_resource_content(
        title=item.get("title", ""),
        resource_type=item.get("type", ""),
        summary=item.get("summary", ""),
        content=item.get("content", ""),
        source=item.get("source", ""),
        reviewer=reviewer,
        semantic_result=semantic_result,
    )

    return {
        **item,
        "agent_notes": content_guard_service.attach_review_note(
            item.get("agent_notes", ""),
            review
        )
    }


def _resource_recipient(db: Session, resource: Resource):
    applicant = (resource.applicant_username or "").strip()
    if applicant and system_message_service.user_exists(db, applicant):
        return applicant

    uploader = (resource.uploader or "").strip()
    if uploader and uploader not in SYSTEM_UPLOADERS and system_message_service.user_exists(db, uploader):
        return uploader

    if system_message_service.user_exists(db, "student"):
        return "student"

    first_student = db.query(User).filter(User.role == "student").first()
    return first_student.username if first_student else ""


def _notify_resource_review(
    db: Session,
    resource: Resource,
    action_label: str,
    content: str,
):
    recipient = _resource_recipient(db, resource)
    if not recipient:
        return None

    return system_message_service.create_message(
        db=db,
        username=recipient,
        title=f"资源审核{action_label}",
        content=content,
        category="资源审核",
        related_resource_id=resource.id,
        commit=False,
    )


def _resource_type_recipient(db: Session, resource_type: ResourceType):
    applicant = (resource_type.applicant_username or "").strip()
    if applicant and system_message_service.user_exists(db, applicant):
        return applicant

    if system_message_service.user_exists(db, "student"):
        return "student"

    first_student = db.query(User).filter(User.role == "student").first()
    return first_student.username if first_student else ""


def _notify_type_review(
    db: Session,
    resource_type: ResourceType,
    action_label: str,
    content: str,
):
    recipient = _resource_type_recipient(db, resource_type)
    if not recipient:
        return None

    return system_message_service.create_message(
        db=db,
        username=recipient,
        title=f"资源分类审核{action_label}",
        content=content,
        category="分类审核",
        related_resource_id="",
        commit=False,
    )


# =========================
# query layer
# =========================

def get_all_resources(db: Session):

    try:

        return [
            _resource_to_dict(r)
            for r in db.query(Resource).all()
            if not _is_deprecated_resource_type(r.type)
        ]

    except Exception:
        return []


def get_passed_resources(db: Session):

    try:

        return [
            _resource_to_dict(r)
            for r in db.query(Resource)
            .filter(Resource.status == "已通过")
            .all()
            if not _is_deprecated_resource_type(r.type)
        ]

    except Exception:
        return []


def get_passed_resource_bundles(db: Session):
    from app.services.data_services import resource_bundle_service

    return resource_bundle_service.build_topic_bundles(get_passed_resources(db))


def get_recommended_resources(db: Session, username: str = "", limit: int = 12):
    """画像、错题、学习路线和内容质量共同参与的可解释混合推荐。"""

    try:
        resources = [
            r
            for r in db.query(Resource)
            .filter(Resource.status == "已通过")
            .all()
            if not _is_deprecated_resource_type(r.type)
        ]
        if not resources:
            return []

        context = _load_recommendation_context(db, username)
        preferred_types = _preferred_resource_types(context)

        weak_terms = _text_terms(
            context.get("weak_points", [])
            + context.get("evaluated_topics", [])
        )
        profile_terms = summarize_knowledge_tags(
            context.get("profile_tags", [])
            + context.get("topic_candidates", [])
        )
        plan_terms = _text_terms(
            context.get("active_fragments", [])
            or context.get("plan_fragments", [])
        )
        topic_terms = summarize_knowledge_tags(profile_terms + context.get("evaluated_topics", []))
        recent_avg_score = context.get("recent_avg_score")
        generated_resource_ids = set(context.get("generated_resource_ids", []))

        scored = []
        for resource in resources:
            resource_text = _resource_text(resource)
            resource_type = artifact_types.normalize_artifact_type(resource.type or "")
            if resource_type in DEPRECATED_AI_RESOURCE_TYPES:
                continue
            weak_matches = _count_matches(resource_text, weak_terms)
            profile_matches = _count_matches(resource_text, profile_terms)
            plan_matches = _count_matches(resource_text, plan_terms)
            topic_matches = _count_matches(resource_text, topic_terms)
            safety_review = content_guard_service.extract_review(resource.agent_notes or "")

            preferred_type_weight = 0
            for type_name, weight in preferred_types.items():
                if type_name == resource_type or type_name in resource_type or resource_type in type_name:
                    preferred_type_weight = max(preferred_type_weight, weight)

            weak_score = min(30, len(weak_matches) * 7 + len(topic_matches) * 3)
            profile_score = min(18, len(profile_matches) * 6)
            plan_score = min(12, len(plan_matches) * 4)
            type_score = min(10, preferred_type_weight * 4)

            evaluation_score = 0
            if resource.id in generated_resource_ids:
                evaluation_score += 8
            if recent_avg_score is not None and recent_avg_score < 75:
                if any(key in resource_type for key in ["练习", "题", "诊断", "反馈", "导图"]):
                    evaluation_score += 7
            elif recent_avg_score is not None and recent_avg_score >= 85:
                if any(key in resource_type for key in ["拓展", "实践", "代码", "项目", "视频", "动画", "PPT"]):
                    evaluation_score += 6
            evaluation_score = min(10, evaluation_score)

            quality_score = min(5, max(0, round(safety_review.get("score", 0) / 20))) if safety_review else 0
            freshness_score = 3 if resource.uploader in SYSTEM_UPLOADERS else 2
            if len((resource.content or "").strip()) >= 500:
                freshness_score += 2
            diversity_score = min(5, freshness_score)

            score = min(
                100,
                20
                + weak_score
                + profile_score
                + plan_score
                + type_score
                + evaluation_score
                + quality_score
                + diversity_score
            )

            item = _resource_to_dict(resource)
            item["_recommend_rank"] = int(score)
            scored.append(item)

        limit_value = max(1, min(int(limit or 12), 30))

        from app.services.data_services import teaching_source_service
        teaching_context = _recommendation_source_text(context)
        pushed_cards = teaching_source_service.build_pushed_teaching_resource_cards(
            teaching_context,
            limit=4,
        )
        scored.extend(pushed_cards)

        scored.sort(
            key=lambda item: (
                item.get("_recommend_rank", 0),
                item.get("auto_pushed", False),
                item.get("title", ""),
            ),
            reverse=True,
        )
        result = scored[:limit_value]
        for item in result:
            item.pop("_recommend_rank", None)

        return result

    except Exception as exc:
        raise RuntimeError("推荐资源计算失败") from exc


def get_resource_by_id(db: Session, resource_id: str):
    try:
        resource = (
            db.query(Resource)
            .filter(Resource.id == resource_id)
            .first()
        )
        return _resource_to_dict(resource) if resource else None
    except Exception:
        return None


# =========================
# 分类
# =========================

def get_all_resource_types(db: Session):

    try:

        types = [
            t for t in db.query(ResourceType).all()
            if not _is_deprecated_resource_type(t.name)
        ]

        return [
            {
                "name": t.name,
                "status": t.status,
                "applicant_username": t.applicant_username or "",
                "reason": t.reason or "",
                "review_comment": t.review_comment or "",
                "reviewed_at": t.reviewed_at or "",
            }
            for t in types
        ]

    except Exception:
        return []


def get_passed_resource_types(db: Session):

    try:

        types = (
            db.query(ResourceType)
            .filter(ResourceType.status == "已通过")
            .all()
        )

        names = DEFAULT_RESOURCE_TYPES + [
            t.name
            for t in types
            if t.name not in DEFAULT_RESOURCE_TYPES
            and t.name not in DEPRECATED_AI_RESOURCE_TYPES
            and not _is_deprecated_resource_type(t.name)
        ]

        return list(dict.fromkeys(names))

    except Exception:
        return []


def propose_new_type(
    db: Session,
    name: str,
    username: str = "",
    reason: str = "",
):

    try:

        exists = (
            db.query(ResourceType)
            .filter(ResourceType.name == name)
            .first()
        )

        if exists:
            return False

        item = ResourceType(
            name=name,
            status="待审核",
            applicant_username=(username or "").strip(),
            reason=(reason or "").strip(),
        )

        db.add(item)
        db.commit()

        return True

    except Exception:
        db.rollback()
        return False


def approve_resource_type(
    db: Session,
    name: str
):

    try:

        item = (
            db.query(ResourceType)
            .filter(ResourceType.name == name)
            .first()
        )

        if not item:
            return False

        item.status = "已通过"
        item.reviewed_at = _now_text()

        item.review_comment = "分类申请已通过，可在学生端资源工厂中使用。"

        _notify_type_review(
            db,
            item,
            "通过",
            f"你申请的新资源分类「{item.name}」已通过审核，现在可以在资源工厂中使用。",
        )

        db.commit()

        return True

    except Exception:
        db.rollback()
        return False


def reject_resource_type(
    db: Session,
    name: str,
    comment: str = "",
):
    try:
        item = (
            db.query(ResourceType)
            .filter(ResourceType.name == name)
            .first()
        )

        if not item:
            return False

        item.status = "未通过"
        item.review_comment = (comment or "该分类暂未通过审核，请根据管理员意见调整后重新申请。").strip()
        item.reviewed_at = _now_text()

        _notify_type_review(
            db,
            item,
            "未通过",
            f"你申请的新资源分类「{item.name}」暂未通过审核。\n\n修改意见：{item.review_comment}",
        )

        db.commit()

        return True

    except Exception:
        db.rollback()
        return False


def update_resource_type_comment(
    db: Session,
    name: str,
    comment: str,
):
    try:
        item = (
            db.query(ResourceType)
            .filter(ResourceType.name == name)
            .first()
        )

        if not item:
            return False

        item.status = "未通过"
        item.review_comment = (comment or "请根据管理员意见修改后重新申请。").strip()
        item.reviewed_at = _now_text()

        _notify_type_review(
            db,
            item,
            "意见更新",
            f"资源分类「{item.name}」收到新的修改意见。\n\n修改意见：{item.review_comment}",
        )

        db.commit()

        return True

    except Exception:
        db.rollback()
        return False


# =========================
# core: AI结果落库入口
# =========================

def save_ai_generated_resources(
    db: Session,
    resource_plan: dict,
    llm_outputs: list,
    uploader: str = "AI-Agent",
    applicant_username: str = "",
):
    resources = []
    skipped = []
    semantic_result = resource_plan.get("semantic_result") or {}
    generation_context = resource_plan.get("generation_context") or {}

    for index, plan_item in enumerate(resource_plan.get("resources", [])):
        llm_item = llm_outputs[index] if index < len(llm_outputs) else {}
        title = plan_item.get("title") or plan_item.get("topic") or "未命名资源"
        item = {
            "title": title,
            "type": artifact_types.normalize_artifact_type(plan_item.get("type", artifact_types.COURSE_NOTE)),
            "summary": llm_item.get("summary") or plan_item.get("summary", ""),
            "content": llm_item.get("content") or plan_item.get("content", ""),
            "source": llm_item.get("source") or plan_item.get("source", ""),
            "agent_notes": plan_item.get("agent_notes", ""),
            "subject_category": plan_item.get("subject_category") or semantic_result.get("subject_category", "unknown"),
            "level": plan_item.get("level") or semantic_result.get("level", "未确认"),
            "level_source": plan_item.get("level_source") or semantic_result.get("level_source", "none"),
            "allow_code_content": plan_item.get("allow_code_content", False),
            "unit_id": plan_item.get("unit_id") or semantic_result.get("unit_id", ""),
            "chapter_id": plan_item.get("chapter_id") or semantic_result.get("chapter_id", ""),
            "course_id": plan_item.get("course_id") or semantic_result.get("course_id", ""),
            "deep_learning_course_map": plan_item.get("deep_learning_course_map") or semantic_result.get("deep_learning_course_map") or {},
            "ai_course_map": plan_item.get("ai_course_map") or semantic_result.get("ai_course_map") or {},
        }
        if item.get("type") in DEPRECATED_AI_RESOURCE_TYPES:
            skipped.append({
                "title": item.get("title"),
                "type": item.get("type"),
                "issues": ["该资源类型已停用，新系统只生成《深度学习》Artifact 类型。"],
            })
            continue
        if (
            item.get("type") == resource_policy_service.FEEDBACK_RESOURCE_TYPE
            and not resource_policy_service.has_feedback_context(generation_context)
        ):
            skipped.append({
                "title": item.get("title"),
                "type": item.get("type"),
                "issues": ["缺少真实错题、测验、评价或学习反馈记录，不能生成诊断与补弱报告。"],
            })
            continue
        quality_context = {
            **semantic_result,
            "generation_context": generation_context,
            "resource_type": item.get("type"),
            "subject_category": item.get("subject_category"),
            "level": item.get("level"),
            "level_source": item.get("level_source"),
            "should_generate_code_content": item.get("allow_code_content", False),
            "unit_id": item.get("unit_id", ""),
            "chapter_id": item.get("chapter_id", ""),
            "course_id": item.get("course_id", ""),
            "deep_learning_course_map": item.get("deep_learning_course_map") or semantic_result.get("deep_learning_course_map") or {},
            "ai_course_map": item.get("ai_course_map") or semantic_result.get("ai_course_map") or {},
        }
        quality = resource_quality_gate.validate_resource_semantics(item, quality_context)
        item["agent_notes"] = resource_quality_gate.attach_quality_note(item.get("agent_notes", ""), quality)
        if quality.get("fatal"):
            skipped.append({
                "title": item.get("title"),
                "type": item.get("type"),
                "issues": quality.get("issues", []),
            })
            continue
        item["_semantic_context"] = quality_context
        resources.append(item)

    reviewed_resources = []
    for item in resources:
        semantic_context = item.pop("_semantic_context", None)
        reviewed_resources.append(_with_content_review(item, "内容安全 Agent", semantic_context))

    inserted = insert_generated_resources(
        db,
        reviewed_resources,
        uploader=uploader,
        applicant_username=applicant_username,
    )
    return {
        "resources": inserted,
        "skipped_resources": skipped,
    }


def insert_generated_resources(
    db: Session,
    resources: list,
    uploader: str = "资源生成 Agent",
    applicant_username: str = "",
):
    inserted = []

    try:
        for item in resources:
            title = (item.get("title") or "").strip()
            r_type = (item.get("type") or "").strip()
            if not title or not r_type or _is_deprecated_resource_type(r_type):
                continue

            existing = (
                db.query(Resource)
                .filter(Resource.title == title, Resource.type == r_type)
                .first()
            )

            if existing:
                existing.summary = item.get("summary", existing.summary or "")
                existing.content = item.get("content", existing.content or "")
                existing.source = item.get("source", existing.source or "")
                existing.agent_notes = item.get("agent_notes", existing.agent_notes or "")
                existing.uploader = uploader
                existing.applicant_username = applicant_username or existing.applicant_username or ""
                existing.status = "待审核"
                existing.review_comment = ""
                existing.reviewed_at = ""
                existing.time = _now_text()
                artifact = resource_artifact_service.upsert_from_resource(
                    db,
                    resource=existing,
                    plan_item=item,
                    semantic_result=item.get("deep_learning_course_map") or {},
                )
                resource_dict = _resource_to_dict(existing)
                resource_dict["artifact"] = artifact
                inserted.append(resource_dict)
                continue

            resource = Resource(
                id=_new_resource_id(),
                title=title,
                type=r_type,
                status="待审核",
                uploader=uploader,
                applicant_username=applicant_username or "",
                time=_now_text(),
                summary=item.get("summary", ""),
                content=item.get("content", ""),
                source=item.get("source", ""),
                agent_notes=item.get("agent_notes", "")
            )

            db.add(resource)
            db.flush()
            artifact = resource_artifact_service.upsert_from_resource(
                db,
                resource=resource,
                plan_item=item,
                semantic_result=item.get("deep_learning_course_map") or {},
            )
            resource_dict = _resource_to_dict(resource)
            resource_dict["artifact"] = artifact
            inserted.append(resource_dict)

        db.commit()
        return inserted

    except Exception as exc:
        logger.exception("Insert generated resources failed")
        db.rollback()
        raise RuntimeError(f"AI 资源落库失败：{str(exc)[:120]}") from exc


# =========================
# CRUD
# =========================

def insert_new_resource(
    db: Session,
    title: str,
    r_type: str,
    summary: str = "",
    content: str = "",
    source: str = "",
    agent_notes: str = "",
    uploader: str = "student",
    applicant_username: str = "",
):

    try:
        reviewed_item = _with_content_review(
            {
                "title": title,
                "type": r_type,
                "summary": summary,
                "content": content,
                "source": source,
                "agent_notes": agent_notes,
            },
            "学生资源预审 Agent"
        )

        resource = Resource(
            id=_new_resource_id(),

            title=title,

            type=r_type,

            status="待审核",

            uploader=uploader,
            applicant_username=(applicant_username or uploader or "").strip(),

            time=_now_text(),

            summary=reviewed_item.get("summary", ""),

            content=reviewed_item.get("content", ""),

            source=reviewed_item.get("source", ""),

            agent_notes=reviewed_item.get("agent_notes", "")
        )

        db.add(resource)
        db.flush()
        resource_artifact_service.upsert_from_resource(
            db,
            resource=resource,
            plan_item={
                "content_format": artifact_types.get_format(artifact_types.normalize_artifact_type(r_type)),
                "personalization_reason": "学生主动上传或补充的深度学习课程资源。",
            },
            semantic_result={},
        )

        db.commit()

        db.refresh(resource)

        return _resource_to_dict(resource)

    except Exception:

        db.rollback()

        return None


def approve_resource(
    db: Session,
    resource_id: str,
    comment: str = "",
):

    try:

        r = (
            db.query(Resource)
            .filter(Resource.id == resource_id)
            .first()
        )

        if not r:
            return False

        r.status = "已通过"
        r.review_comment = (comment or "资源内容已通过管理员审核，可在学生端资源工厂正常查看。").strip()
        r.reviewed_at = _now_text()
        resource_artifact_service.sync_resource_status(db, r.id, r.status)

        _notify_resource_review(
            db,
            r,
            "通过",
            f"你提交或生成的资源「{r.title}」已通过审核，现已在学生端资源工厂开放。\n\n审核意见：{r.review_comment}",
        )

        db.commit()

        return True

    except Exception:

        db.rollback()

        return False


def approve_pending_resources_by_applicant(
    db: Session,
    applicant_username: str,
    limit: int = 10,
):
    username = (applicant_username or "").strip()
    if not username:
        return []

    safe_limit = max(1, min(int(limit or 10), 20))

    try:
        pending = (
            db.query(Resource)
            .filter(
                Resource.applicant_username == username,
                Resource.status == "待审核",
            )
            .order_by(Resource.time.desc())
            .limit(safe_limit)
            .all()
        )

        approved = []
        for item in pending:
            item.status = "已通过"
            item.review_comment = "教师审核通过，已进入学生资源工厂。"
            item.reviewed_at = _now_text()
            resource_artifact_service.sync_resource_status(db, item.id, item.status)
            approved.append(_resource_to_dict(item))

        if approved:
            system_message_service.create_message(
                db=db,
                username=username,
                title="本轮配套资源已通过教师审核",
                content=f"你本轮学习生成的 {len(approved)} 份配套 Artifact 已通过教师审核，已进入资源工厂。",
                category="资源审核",
                commit=False,
            )

        db.commit()
        return approved
    except Exception:
        db.rollback()
        return []


def reject_resource(
    db: Session,
    resource_id: str,
    comment: str = "",
):

    try:

        r = (
            db.query(Resource)
            .filter(Resource.id == resource_id)
            .first()
        )

        if not r:
            return False

        r.status = "未通过"
        r.review_comment = (comment or "资源暂未通过审核，请根据管理员意见修改后重新提交。").strip()
        r.reviewed_at = _now_text()
        resource_artifact_service.sync_resource_status(db, r.id, r.status)

        _notify_resource_review(
            db,
            r,
            "未通过",
            f"你提交或生成的资源「{r.title}」暂未通过审核。\n\n修改意见：{r.review_comment}",
        )

        db.commit()

        return True

    except Exception:

        db.rollback()

        return False


def update_resource_review_comment(
    db: Session,
    resource_id: str,
    comment: str,
):
    try:
        r = (
            db.query(Resource)
            .filter(Resource.id == resource_id)
            .first()
        )

        if not r:
            return False

        r.status = "未通过"
        r.review_comment = (comment or "请根据管理员意见修改后重新提交。").strip()
        r.reviewed_at = _now_text()
        resource_artifact_service.sync_resource_status(db, r.id, r.status)

        _notify_resource_review(
            db,
            r,
            "意见更新",
            f"资源「{r.title}」收到新的修改意见。\n\n修改意见：{r.review_comment}",
        )

        db.commit()

        return True

    except Exception:

        db.rollback()

        return False
