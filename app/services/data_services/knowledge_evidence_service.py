import json
import re
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.schemas import CourseKnowledge, Resource
from app.services.data_services import resource_service


MAX_FIELD_LEN = 1800


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

    stop_terms = {"什么", "怎么", "如何", "一下", "这个", "那个", "相关", "知识", "学习", "请问", "根据", "解释", "课程", "知识库"}
    return [term for term in terms if term and term not in stop_terms]


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


def _score_text(query, terms, fields, keywords=None):
    query = _normalize(query)
    haystack = _normalize("\n".join(fields))[:MAX_FIELD_LEN]
    score = 0

    for keyword in keywords or []:
        keyword_text = _normalize(str(keyword))
        if not keyword_text:
            continue
        if keyword_text in query:
            score += 14
        for term in terms:
            if len(term) >= 3 and term in keyword_text:
                score += 6

    for term in terms:
        if term in haystack:
            score += 3 if len(term) >= 3 else 1

    return score


def search_course_evidence(db: Session, query: str, limit: int = 4):
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
            fields = [
                row.topic or "",
                row.chapter or "",
                row.core or "",
                " ".join(str(item) for item in pitfalls),
                row.practice or "",
                row.practice_output or "",
                row.code_lang or "",
                row.code or "",
            ]
            score = _score_text(query, terms, fields, keywords=keywords + [row.topic or "", row.chapter or ""])
            if score <= 0:
                continue
            candidates.append({
                "kind": "course_knowledge",
                "title": row.topic or "课程知识点",
                "source": row.chapter or "人工智能导论初始知识库",
                "excerpt": _first_matching_excerpt(fields, terms),
                "score": score,
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
            fields = [
                row.title or "",
                row.type or "",
                row.summary or "",
                row.content or "",
                row.source or "",
            ]
            score = _score_text(query, terms, fields, keywords=[row.title or "", row.type or "", row.source or ""])
            if score <= 0:
                continue
            candidates.append({
                "kind": "resource",
                "resource_id": row.id,
                "title": row.title or "学习资源",
                "resource_type": row.type or "",
                "source": row.source or row.uploader or "已审核资源库",
                "excerpt": _first_matching_excerpt(fields, terms),
                "score": score,
                "keywords": [],
            })
    except Exception:
        return []

    candidates.sort(key=lambda item: item.get("score", 0), reverse=True)
    return candidates[:max(limit, 1)]


def format_evidence_for_prompt(evidence):
    if not evidence:
        return "未检索到高置信课程依据。回答时请明确说明需要进一步核验，不要编造来源。"

    lines = []
    for index, item in enumerate(evidence, start=1):
        title = item.get("title") or "未命名依据"
        source = item.get("source") or "课程知识库"
        excerpt = item.get("excerpt") or ""
        lines.append(f"{index}. {title}｜{source}：{excerpt}")
    return "\n".join(lines)
