import json
import re
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.schemas import CourseKnowledge, Resource
from app.services.data_services import resource_service


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
    "ai_intro": ["人工智能", "人工智能导论", "ai", "智能体"],
    "search": ["搜索", "启发式", "a*", "astar", "状态空间", "问题求解"],
    "machine_learning": ["机器学习", "ml", "特征工程", "过拟合", "泛化"],
    "supervised_learning": ["监督学习", "分类", "回归", "混淆矩阵", "f1", "召回率", "准确率"],
    "deep_learning": ["深度学习", "神经网络", "反向传播", "梯度下降", "cnn"],
    "lstm": ["lstm", "rnn", "循环神经网络", "长短期记忆", "长短期记忆网络", "序列模型", "门控"],
    "transformer": ["transformer", "attention", "注意力", "注意力机制", "自注意力", "多头注意力", "bert", "gpt"],
    "nlp": ["自然语言处理", "nlp", "大语言模型", "llm", "提示词", "rag", "语义理解"],
    "multimodal": ["多模态", "流程图", "mermaid", "ppt", "图文", "题解", "代码注释"],
    "ai_safety": ["ai安全", "人工智能安全", "防幻觉", "内容安全", "伦理", "偏见", "可解释性"],
    "information_security": ["信息安全", "网络安全", "密码学", "加密", "认证", "访问控制", "系统安全", "安全协议"],
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
    if len(matched) > 1 and "ai_intro" in matched:
        matched.remove("ai_intro")
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
                "source": row.chapter or "人工智能初始知识库",
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
                "source": row.source or row.uploader or "已审核资源库",
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
