"""学生画像的内部存储与公开展示适配。

内部十维字段继续保留，用于兼容既有事件和历史数据；学生端展示六项
有明确来源的核心信息。公开画像允许部分维度处于“待采集”状态，避免用
默认分数填补尚未产生的学习证据。
"""

from typing import Dict, Iterable, List, Optional


LEGACY_PROFILE_DIMENSION_KEYS = (
    "知识基础",
    "学习目标",
    "概念理解",
    "练习表现",
    "实践能力",
    "规划执行",
    "复盘能力",
    "易错修复",
    "媒介偏好",
    "兴趣方向",
)

PUBLIC_PROFILE_DIMENSION_KEYS = (
    "当前知识水平",
    "学习目标",
    "练习表现",
    "薄弱知识点",
    "路径执行",
    "资源偏好",
)

QUANTITATIVE_PUBLIC_DIMENSIONS = (
    "当前知识水平",
    "练习表现",
    "路径执行",
)


def clamp_score(value) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return None


def _clean_list(values: Iterable, limit: int = 5) -> List[str]:
    result = []
    for value in values or []:
        text = str(value or "").strip()
        if not text or text in result:
            continue
        result.append(text)
        if len(result) >= limit:
            break
    return result


def make_score_dimension(
    value,
    *,
    display: str,
    evidence: str,
    source: str,
    status: str = "observed",
) -> Dict:
    score = clamp_score(value)
    if score is None:
        status = "pending" if status == "observed" else status
    return {
        "kind": "score",
        "value": score,
        "display": str(display or "待采集"),
        "status": status,
        "evidence": str(evidence or "尚无可用学习证据"),
        "source": str(source or "none"),
    }


def make_text_dimension(
    value,
    *,
    evidence: str,
    source: str,
    status: str = "reported",
) -> Dict:
    text = str(value or "").strip()
    if not text:
        text = "待确认"
        status = "pending"
    return {
        "kind": "text",
        "value": text,
        "display": text,
        "status": status,
        "evidence": str(evidence or "尚无可用学习证据"),
        "source": str(source or "none"),
    }


def make_tags_dimension(
    values,
    *,
    pending_text: str,
    evidence: str,
    source: str,
    status: str = "observed",
) -> Dict:
    items = _clean_list(values)
    if not items:
        status = "pending"
    display = "、".join(items) if items else pending_text
    return {
        "kind": "tags",
        "value": items,
        "display": display,
        "status": status,
        "evidence": str(evidence or "尚无可用学习证据"),
        "source": str(source or "none"),
    }


def _split_legacy_items(value) -> List[str]:
    text = str(value or "").strip()
    if not text:
        return []
    for separator in ["；", ";", "、", "，", ","]:
        text = text.replace(separator, "\n")
    return _clean_list(text.splitlines())


def _normalize_entry(name: str, entry) -> Dict:
    if isinstance(entry, dict):
        normalized = dict(entry)
        kind = normalized.get("kind") or ("score" if name in QUANTITATIVE_PUBLIC_DIMENSIONS else "text")
        normalized["kind"] = kind
        if kind == "score":
            normalized["value"] = clamp_score(normalized.get("value"))
        elif kind == "tags":
            raw = normalized.get("value")
            normalized["value"] = _clean_list(raw if isinstance(raw, list) else _split_legacy_items(raw))
        else:
            normalized["value"] = str(normalized.get("value") or normalized.get("display") or "待确认")
        normalized["display"] = str(normalized.get("display") or (
            "、".join(normalized.get("value") or []) if kind == "tags" else normalized.get("value") or "待采集"
        ))
        normalized["status"] = str(normalized.get("status") or "pending")
        normalized["evidence"] = str(normalized.get("evidence") or "尚无可用学习证据")
        normalized["source"] = str(normalized.get("source") or "none")
        return normalized

    if name in QUANTITATIVE_PUBLIC_DIMENSIONS:
        score = clamp_score(entry)
        return make_score_dimension(
            score,
            display=f"{score} 分" if score is not None else "待采集",
            evidence="由历史画像兼容转换，后续学习行为将补充可追溯证据。",
            source="legacy_profile",
            status="provisional" if score is not None else "pending",
        )
    return make_text_dimension(
        entry,
        evidence="由历史画像兼容转换，后续学习行为将补充可追溯证据。",
        source="legacy_profile",
        status="provisional" if entry else "pending",
    )


def _pending_dimensions() -> Dict:
    return {
        "当前知识水平": make_score_dimension(None, display="待诊断", evidence="完成有效练习或评价后生成。", source="none"),
        "学习目标": make_text_dimension("", evidence="在学习对话中说明课程、知识点和预期成果后生成。", source="none"),
        "练习表现": make_score_dimension(None, display="暂无有效作答", evidence="完成可批改练习后生成。", source="none"),
        "薄弱知识点": make_tags_dimension([], pending_text="待练习诊断", evidence="根据错题和诊断记录生成。", source="none"),
        "路径执行": make_score_dimension(None, display="尚无执行记录", evidence="开始执行学习任务后生成。", source="none"),
        "资源偏好": make_tags_dimension([], pending_text="待确认", evidence="根据学生主动表达和资源使用反馈生成。", source="none", status="reported"),
    }


def derive_public_dimensions(profile: Dict) -> Dict:
    """把新画像或历史十维画像统一转换为六项公开信息。"""
    profile = profile if isinstance(profile, dict) else {}
    supplied = profile.get("public_dimensions")
    result = _pending_dimensions()
    if isinstance(supplied, dict):
        for name in PUBLIC_PROFILE_DIMENSION_KEYS:
            if name in supplied:
                result[name] = _normalize_entry(name, supplied.get(name))
        return result

    dimensions = profile.get("dimensions") if isinstance(profile.get("dimensions"), dict) else {}
    radar = profile.get("radar") if isinstance(profile.get("radar"), dict) else {}
    evidence = profile.get("evidence") if isinstance(profile.get("evidence"), dict) else {}

    evidence_count = int(evidence.get("evidence_count") or 0)
    knowledge_score = clamp_score(evidence.get("recent_avg_score"))
    if knowledge_score is None and evidence_count:
        knowledge_score = clamp_score(radar.get("知识基础"))
    knowledge_text = str(dimensions.get("知识基础") or "待诊断")
    result["当前知识水平"] = make_score_dimension(
        knowledge_score,
        display=(f"{knowledge_score} 分 · {knowledge_text.split('；')[0]}" if knowledge_score is not None else knowledge_text),
        evidence=str(evidence.get("level_evidence") or "当前记录尚未包含可核验的作答分数。"),
        source=str(evidence.get("level_source") or ("legacy_profile" if dimensions.get("知识基础") else "none")),
        status="observed" if knowledge_score is not None else ("reported" if dimensions.get("知识基础") else "pending"),
    )

    result["学习目标"] = make_text_dimension(
        dimensions.get("学习目标"),
        evidence="从学习对话中的主题和任务意图提取。",
        source="dialogue" if dimensions.get("学习目标") else "none",
    )

    exercise_score = clamp_score(evidence.get("exercise_avg_score"))
    result["练习表现"] = make_score_dimension(
        exercise_score,
        display=f"最近有效练习 {exercise_score} 分" if exercise_score is not None else "暂无有效作答",
        evidence=f"有效练习记录 {evidence_count} 条。" if exercise_score is not None else "完成可批改练习后生成。",
        source="exercise_attempts" if exercise_score is not None else "none",
    )

    weak_points = evidence.get("weak_points") or _split_legacy_items(dimensions.get("易错修复"))
    weak_points = [item for item in _clean_list(weak_points) if "继续定位" not in item and "尚无足够" not in item]
    result["薄弱知识点"] = make_tags_dimension(
        weak_points,
        pending_text="待练习诊断",
        evidence="来自错题知识点、作答反馈和学习评价。" if weak_points else "当前还没有足够的错题证据。",
        source="evaluation_records/exercise_attempts" if weak_points else "none",
    )

    execution_rate = clamp_score(evidence.get("execution_rate"))
    result["路径执行"] = make_score_dimension(
        execution_rate,
        display=f"已完成 {execution_rate}%" if execution_rate is not None else "尚无执行记录",
        evidence=f"按当前主题统计学习任务完成率 {execution_rate}%。" if execution_rate is not None else "开始执行学习路径或待办后生成。",
        source="learning_plans/todos" if execution_rate is not None else "none",
    )

    preference = _split_legacy_items(dimensions.get("媒介偏好"))
    result["资源偏好"] = make_tags_dimension(
        preference,
        pending_text="待确认",
        evidence="来自学生主动表达；有资源使用反馈后继续校正。" if preference else "在对话中说明希望使用的资源形式后生成。",
        source="dialogue" if preference else "none",
        status="reported",
    )
    return result


def flatten_public_dimensions(public_dimensions: Dict) -> Dict:
    normalized = derive_public_dimensions({"public_dimensions": public_dimensions})
    return {name: normalized[name]["display"] for name in PUBLIC_PROFILE_DIMENSION_KEYS}


def public_radar(public_dimensions: Dict) -> Dict:
    normalized = derive_public_dimensions({"public_dimensions": public_dimensions})
    result = {}
    for name in QUANTITATIVE_PUBLIC_DIMENSIONS:
        value = clamp_score(normalized[name].get("value"))
        if value is not None:
            result[name] = value
    return result


def build_public_profile_payload(profile: Dict) -> Dict:
    profile = profile if isinstance(profile, dict) else {}
    public_dimensions = derive_public_dimensions(profile)
    tags = profile.get("tags") if isinstance(profile.get("tags"), list) else []
    return {
        "tags": tags,
        "knowledge_tags": profile.get("knowledge_tags") if isinstance(profile.get("knowledge_tags"), list) else tags,
        "hours": profile.get("hours"),
        "updated_at": profile.get("updated_at"),
        "dimensions": flatten_public_dimensions(public_dimensions),
        "public_dimensions": public_dimensions,
        "radar": public_radar(public_dimensions),
        "evidence_summary": profile.get("evidence") if isinstance(profile.get("evidence"), dict) else {},
    }


def is_meaningful_dimension(entry: Dict) -> bool:
    return isinstance(entry, dict) and entry.get("status") not in {"", "pending", None}
