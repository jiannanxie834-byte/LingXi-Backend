import json
import re
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.schemas import CourseKnowledge, Resource
from app.services.data_services import (
    deep_learning_course_map_service,
    resource_service,
)


MAX_FIELD_LEN = 1800
MIN_RELEVANCE_SCORE = 0.65

GENERIC_QUERY_TERMS = {
    "什么",
    "怎么",
    "如何",
    "一下",
    "这个",
    "那个",
    "相关",
    "知识",
    "学习",
    "请问",
    "根据",
    "解释",
    "课程",
    "资料",
    "资源",
    "知识库",
    "规划",
    "路径规划",
    "学习路径",
    "路线",
    "计划",
    "安排",
    "生成",
    "我要",
    "我想",
    "想学",
    "想学习",
    "准备",
    "了解",
    "入门",
}

TOPIC_ALIAS_GROUPS = {
    "dl_intro": ["深度学习", "deep learning", "神经网络", "表示学习", "端到端学习"],
    "prerequisites": ["矩阵", "梯度", "链式法则", "概率", "训练集", "验证集", "测试集", "损失函数"],
    "mlp": ["感知机", "神经元", "mlp", "多层感知机", "激活函数", "全连接网络"],
    "backprop": ["反向传播", "bp", "backprop", "backpropagation", "前向传播", "链式法则", "梯度传播"],
    "optimization": ["sgd", "momentum", "adam", "优化器", "学习率", "学习率调度", "训练曲线"],
    "regularization": ["正则化", "dropout", "batchnorm", "batch normalization", "数据增强", "早停", "过拟合", "泛化"],
    "cnn": ["cnn", "卷积神经网络", "卷积", "卷积层", "卷积核", "步幅", "填充", "池化", "特征图", "图像分类"],
    "rnn_lstm": ["rnn", "循环神经网络", "lstm", "gru", "长短期记忆", "门控机制", "序列模型", "时间序列"],
    "transformer": ["transformer", "attention", "注意力机制", "自注意力", "多头注意力", "qkv", "位置编码", "encoder", "decoder"],
    "generative": ["自编码器", "autoencoder", "vae", "gan", "生成对抗网络", "扩散模型", "diffusion", "生成模型"],
    "pytorch": ["pytorch", "torch", "dataset", "dataloader", "训练循环", "模型训练", "代码实验", "图像分类实验"],
    "project": ["课程项目", "综合项目", "项目任务", "图像分类项目", "文本分类项目", "时间序列预测项目", "rubric"],
}


def _safe_json_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return [
            item.strip()
            for item in str(value).split(",")
            if item.strip()
        ]


def _normalize(text):
    return (text or "").lower().strip()


def _compact(text):
    return re.sub(r"\s+", "", _normalize(text))


def _query_terms(text):
    normalized = _normalize(text)
    raw_terms = re.findall(r"[a-z0-9_+#.]+|[\u4e00-\u9fff]{2,}", normalized)
    terms = set()

    for term in raw_terms:
        if len(term) <= 24:
            terms.add(term)
        if re.fullmatch(r"[\u4e00-\u9fff]+", term):
            for size in (2, 3, 4):
                if len(term) >= size:
                    terms.update(term[i:i + size] for i in range(0, len(term) - size + 1))

    return [
        term
        for term in terms
        if term and term not in GENERIC_QUERY_TERMS and not re.fullmatch(r"[a-z]", term)
    ]


def _clip(text, limit=180):
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "..."


def _content_excerpt(text, limit=1200):
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "..."


def _evidence_from_knowledge(row: CourseKnowledge, evidence_id: str = ""):
    return {
        "evidence_id": evidence_id or f"course_knowledge:{row.id}",
        "title": row.topic or "课程知识点",
        "source_path": row.chapter or "深度学习初始知识库",
        "content_excerpt": _content_excerpt("\n".join([
            row.core or "",
            "常见误区：" + "；".join(_safe_json_list(row.pitfalls)),
            "实践任务：" + (row.practice or ""),
            "实践产出：" + (row.practice_output or ""),
            "代码：" + (row.code or ""),
        ])),
    }


def _evidence_from_resource(row: Resource, evidence_id: str = ""):
    return {
        "evidence_id": evidence_id or row.id,
        "title": row.title or "课程资源",
        "source_path": row.source or row.uploader or "深度学习初始知识库",
        "content_excerpt": _content_excerpt("\n".join([
            row.summary or "",
            row.content or "",
        ])),
    }


def _matches_any(value, terms):
    compact = _compact(value)
    return any(_compact(term) and _compact(term) in compact for term in terms)


def _unit_evidence_score(value, unit, chapter, terms):
    compact = _compact(value)
    score = 0
    if _compact(unit.get("title", "")) and _compact(unit.get("title", "")) in compact:
        score += 10
    if _compact(unit.get("unit_id", "")) and _compact(unit.get("unit_id", "")) in compact:
        score += 8
    if _compact(chapter.get("title", "")) and _compact(chapter.get("title", "")) in compact:
        score += 6
    for alias in unit.get("aliases", []):
        if _compact(alias) and _compact(alias) in compact:
            score += 2
    for concept in unit.get("core_concepts", []):
        if _compact(concept) and _compact(concept) in compact:
            score += 1
    if not score and _matches_any(value, terms):
        score = 1
    return score


def get_evidence_for_unit(db: Session, course_id: str, unit_id: str, limit: int = 6):
    """按《深度学习》课程知识单元收集可注入生成 prompt 的证据片段。"""
    if course_id and course_id != deep_learning_course_map_service.COURSE_ID:
        return []

    unit = deep_learning_course_map_service.get_unit(unit_id or "")
    if not unit:
        return []

    chapter = deep_learning_course_map_service.CHAPTER_BY_ID.get(unit.get("chapter_id", ""), {})
    search_terms = [
        unit.get("title", ""),
        chapter.get("title", ""),
        unit.get("unit_id", ""),
        *unit.get("aliases", []),
        *unit.get("core_concepts", []),
    ]
    scored_evidence = []
    seen = set()

    try:
        for row in db.query(CourseKnowledge).all():
            haystack = "\n".join([
                row.topic or "",
                row.chapter or "",
                row.core or "",
                row.keywords or "",
            ])
            score = _unit_evidence_score(haystack, unit, chapter, search_terms)
            if score <= 0:
                continue
            item = _evidence_from_knowledge(row)
            if item["evidence_id"] not in seen:
                scored_evidence.append((score, item))
                seen.add(item["evidence_id"])

        resources = db.query(Resource).filter(Resource.status == "已通过").all()
        for row in resources:
            if resource_service._is_deprecated_resource_type(row.type):
                continue
            haystack = "\n".join([
                row.id or "",
                row.title or "",
                row.source or "",
                row.summary or "",
                row.content or "",
            ])
            score = _unit_evidence_score(haystack, unit, chapter, search_terms)
            if (row.id or "").startswith("KB-DL") or row.uploader == "课程知识库种子":
                score += 20
            if score <= 0:
                continue
            item = _evidence_from_resource(row)
            if item["evidence_id"] not in seen:
                scored_evidence.append((score, item))
                seen.add(item["evidence_id"])
    except Exception:
        return []

    scored_evidence.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored_evidence[:max(1, int(limit or 6))]]


def search_evidence(db: Session, course_id: str, query: str, limit: int = 6):
    """按主题检索详细证据，返回统一 evidence_chunks 结构。"""
    if course_id and course_id != deep_learning_course_map_service.COURSE_ID:
        return []

    course_match = deep_learning_course_map_service.match_deep_learning_topic(query, query)
    if course_match.get("unit_id"):
        unit_evidence = get_evidence_for_unit(db, course_id, course_match["unit_id"], limit=limit)
        if unit_evidence:
            return unit_evidence[:max(1, int(limit or 6))]

    evidence = []
    seen = set()
    for item in search_course_evidence(db, query, limit=limit, include_irrelevant=False):
        evidence_id = item.get("resource_id") or f"{item.get('kind', 'evidence')}:{item.get('title', '')}"
        converted = {
            "evidence_id": evidence_id,
            "title": item.get("title", ""),
            "source_path": item.get("source", ""),
            "content_excerpt": item.get("excerpt", ""),
        }
        if converted["evidence_id"] not in seen:
            evidence.append(converted)
            seen.add(converted["evidence_id"])

    return evidence[:max(1, int(limit or 6))]


def format_evidence_chunks_for_prompt(evidence_chunks):
    if not evidence_chunks:
        return "当前知识库中该知识点证据不足，已生成知识库补充任务。"
    lines = []
    for index, item in enumerate(evidence_chunks, start=1):
        lines.append(
            f"{index}. {item.get('title', '课程依据')}｜{item.get('source_path', '课程知识库')}｜"
            f"evidence_id={item.get('evidence_id', '')}\n"
            f"   {item.get('content_excerpt', '')}"
        )
    return "\n".join(lines)


def _first_matching_excerpt(fields: Iterable[str], terms):
    for field in fields:
        text = " ".join((field or "").split())
        if not text:
            continue
        lowered = text.lower()
        for term in terms:
            pos = lowered.find(term)
            if pos >= 0:
                start = max(pos - 45, 0)
                end = min(pos + 135, len(text))
                prefix = "..." if start > 0 else ""
                suffix = "..." if end < len(text) else ""
                return f"{prefix}{text[start:end]}{suffix}"
    return _clip(next((field for field in fields if field), ""), 180)


def _concept_groups_for_text(text):
    compact = _compact(text)
    matched = set()
    for group, aliases in TOPIC_ALIAS_GROUPS.items():
        for alias in aliases:
            alias_text = _compact(alias)
            if alias_text and alias_text in compact:
                matched.add(group)
                break
    return matched


def _score_candidate(query, terms, topic_fields, body_fields, keywords=None):
    query_groups = _concept_groups_for_text(query)
    candidate_topic_text = "\n".join(topic_fields + [str(item) for item in keywords or []])
    candidate_body_text = "\n".join(body_fields)[:MAX_FIELD_LEN]
    topic_groups = _concept_groups_for_text(candidate_topic_text)
    body_groups = _concept_groups_for_text(candidate_body_text)
    matched_topic_groups = query_groups & topic_groups
    matched_body_groups = query_groups & body_groups

    normalized_topic = _normalize(candidate_topic_text)
    normalized_body = _normalize(candidate_body_text)

    topic_hits = [
        term
        for term in terms
        if term and term in normalized_topic
    ]
    body_hits = [
        term
        for term in terms
        if term and term not in topic_hits and term in normalized_body
    ]
    strong_topic_hit = any(
        term in normalized_topic
        for term in terms
        if len(term) >= 3 or re.fullmatch(r"[a-z0-9_+#.]+", term or "")
    )

    score = 0.0
    if matched_topic_groups:
        score += 0.52 + min(0.18, 0.06 * len(matched_topic_groups))
    elif matched_body_groups and (topic_hits or strong_topic_hit):
        score += min(0.18, 0.06 * len(matched_body_groups))
    score += min(0.32, 0.11 * len(topic_hits))
    score += min(0.16, 0.04 * len(body_hits))
    if strong_topic_hit:
        score += 0.08

    score = round(min(score, 1.0), 2)
    topic_match = bool(matched_topic_groups or strong_topic_hit or len(topic_hits) >= 2)

    return {
        "score": score,
        "topic_match": topic_match,
        "is_relevant": score >= MIN_RELEVANCE_SCORE and topic_match,
        "matched_terms": topic_hits + body_hits[:5],
        "matched_concepts": sorted(matched_topic_groups or matched_body_groups),
    }


def search_course_evidence(db: Session, query: str, limit: int = 4, min_score: float = MIN_RELEVANCE_SCORE, include_irrelevant: bool = False):
    """从课程知识点和已通过资源中检索回答依据，用于防幻觉和演示证据链。"""
    terms = _query_terms(query)
    if not terms:
        return []

    candidates = []

    try:
        knowledge_rows = db.query(CourseKnowledge).all()
        for row in knowledge_rows:
            keywords = _safe_json_list(row.keywords)
            pitfalls = _safe_json_list(row.pitfalls)
            topic_fields = [
                row.topic or "",
                row.chapter or "",
                " ".join(str(item) for item in keywords),
            ]
            body_fields = [
                row.core or "",
                " ".join(str(item) for item in pitfalls),
                row.practice or "",
                row.practice_output or "",
                row.code_lang or "",
                row.code or "",
            ]
            relevance = _score_candidate(
                query,
                terms,
                topic_fields,
                body_fields,
                keywords=keywords + [row.topic or "", row.chapter or ""],
            )
            if relevance["score"] < min_score and not include_irrelevant:
                continue
            candidates.append({
                "kind": "course_knowledge",
                "title": row.topic or "课程知识点",
                "source": row.chapter or "深度学习初始知识库",
                "excerpt": _first_matching_excerpt(topic_fields + body_fields, terms),
                "score": relevance["score"],
                "topic_match": relevance["topic_match"],
                "is_relevant": relevance["is_relevant"],
                "matched_terms": relevance["matched_terms"][:8],
                "matched_concepts": relevance["matched_concepts"],
                "keywords": keywords[:6],
            })

        resource_rows = (
            db.query(Resource)
            .filter(Resource.status == "已通过")
            .all()
        )
        for row in resource_rows:
            if resource_service._is_deprecated_resource_type(row.type):
                continue
            topic_fields = [
                row.title or "",
                row.source or "",
            ]
            body_fields = [
                row.type or "",
                row.summary or "",
                row.content or "",
            ]
            relevance = _score_candidate(
                query,
                terms,
                topic_fields,
                body_fields,
                keywords=[row.title or "", row.source or ""],
            )
            if relevance["score"] < min_score and not include_irrelevant:
                continue
            candidates.append({
                "kind": "resource",
                "resource_id": row.id,
                "title": row.title or "学习资源",
                "resource_type": row.type or "",
                "source": row.source or row.uploader or "已审核资源工厂",
                "excerpt": _first_matching_excerpt(topic_fields + body_fields, terms),
                "score": relevance["score"],
                "topic_match": relevance["topic_match"],
                "is_relevant": relevance["is_relevant"],
                "matched_terms": relevance["matched_terms"][:8],
                "matched_concepts": relevance["matched_concepts"],
                "keywords": [],
            })
    except Exception:
        return []

    candidates.sort(key=lambda item: item.get("score", 0), reverse=True)
    return candidates[:max(limit, 1)]


def format_evidence_for_prompt(evidence):
    if not evidence:
        return "当前课程库资料不足，需补充资料或人工复核。回答时不要编造课程来源。"

    lines = []
    for index, item in enumerate(evidence, start=1):
        if not item.get("is_relevant"):
            continue
        title = item.get("title") or "未命名依据"
        source = item.get("source") or "课程资料"
        excerpt = item.get("excerpt") or ""
        lines.append(f"{index}. {title}｜{source}：{excerpt}")
    return "\n".join(lines) if lines else "当前课程库资料不足，需补充资料或人工复核。回答时不要编造课程来源。"
