"""审计并可恢复地归档旧版低质量资源、伪评价和被污染的画像快照。

默认只做干跑；显式传入 --apply 才会更新数据库。所有数据都保留原行，
通过 archived / legacy_invalid 标记排除，不做物理删除。
"""

import argparse
import datetime
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal
from app.models.schemas import EvaluationRecord, ProfileEvent, Resource, ResourceArtifact
from app.services.data_services import (
    dsa_resource_policy_service,
    resource_artifact_service,
    resource_artifact_type_service as artifact_types,
    resource_quality_gate,
)


ACTIVE_STATUSES = {"published", "needs_review"}
COURSE_ID = "data_structures_algorithms"
CORE_RESOURCE_TYPES = set(dsa_resource_policy_service.DEFAULT_DSA_LEARNING_PACKAGE_TYPES)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


def _content_hash(value: str) -> str:
    return hashlib.sha256(_normalize(value).encode("utf-8")).hexdigest()


def _parse_cutoff(value: str) -> datetime.datetime:
    try:
        return datetime.datetime.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit("--legacy-before 必须是 ISO 日期，例如 2026-07-18") from exc


def _artifact_review(artifact: ResourceArtifact, resource: Optional[Resource]) -> dict:
    item = resource_artifact_service.to_dict(artifact)
    agent_notes = resource.agent_notes if resource else ""
    if "personalized_generation_fallback" in str(agent_notes or ""):
        item["assembly_policy"] = "personalized_generation_fallback"
    unit_ids = item.get("unit_ids") or []
    context = {
        "course_id": artifact.course_id or COURSE_ID,
        "chapter_id": artifact.chapter_id or "",
        "section_id": artifact.section_id or "",
        "unit_id": unit_ids[0] if unit_ids else "",
        "topic": artifact.title or "",
        "normalized_topic": artifact.title or "",
        "evidence_refs": item.get("evidence_refs") or [],
        "assets": item.get("assets") or [],
    }
    return resource_quality_gate.validate_teaching_quality(item, context)


def _legacy_evaluation(record: EvaluationRecord, cutoff: datetime.datetime) -> bool:
    if (record.created_at or datetime.datetime.min) >= cutoff:
        return False
    diagnosis_type = str(record.diagnosis_type or "")
    if diagnosis_type.startswith("legacy_invalid"):
        return False
    return diagnosis_type in {"topic_matched", "auto_multi_factor", "exercise_ai_grading"}


def build_audit(db, username: str, cutoff: datetime.datetime) -> dict:
    pairs = (
        db.query(ResourceArtifact, Resource)
        .outerjoin(Resource, ResourceArtifact.resource_id == Resource.id)
        .filter(
            ResourceArtifact.student_id == username,
            ResourceArtifact.status.in_(ACTIVE_STATUSES),
        )
        .order_by(ResourceArtifact.updated_at.desc())
        .all()
    )

    audits = []
    for artifact, resource in pairs:
        review = _artifact_review(artifact, resource)
        reasons = []
        updated_at = artifact.updated_at or artifact.created_at or datetime.datetime.min
        if artifact.course_id != COURSE_ID:
            reasons.append("非《数据结构与算法》比赛主线")
        if updated_at < cutoff and artifact.type not in CORE_RESOURCE_TYPES:
            reasons.append("旧版非五类主线资源")
        if updated_at < cutoff and artifact.type == artifact_types.DIAGNOSTIC_REPORT:
            reasons.append("旧版评价数据生成的诊断报告")
        if not review.get("passed"):
            issues = review.get("issues") or ["未通过教学质量门控"]
            reasons.append(f"实际质量 {review.get('score', 0)}/100：{'；'.join(issues[:3])}")
        audits.append({
            "artifact": artifact,
            "resource": resource,
            "review": review,
            "reasons": reasons,
        })

    # 只在已通过内容门控的候选中选一份；低质量项本身已会被归档。
    for key_name, key_fn in [
        ("标题", lambda row: (row["artifact"].type, _normalize(row["artifact"].title))),
        ("正文", lambda row: (row["artifact"].type, _content_hash(row["artifact"].content))),
    ]:
        groups = defaultdict(list)
        for audit in audits:
            groups[key_fn(audit)].append(audit)
        for group in groups.values():
            if len(group) < 2:
                continue
            keep = max(
                group,
                key=lambda row: (
                    int(row["review"].get("score") or 0),
                    row["artifact"].updated_at or datetime.datetime.min,
                ),
            )
            for audit in group:
                if audit is not keep:
                    audit["reasons"].append(f"与 {keep['artifact'].artifact_id} {key_name}重复")

    evaluations = (
        db.query(EvaluationRecord)
        .filter(EvaluationRecord.username == username)
        .order_by(EvaluationRecord.created_at.desc())
        .all()
    )
    invalid_evaluations = [row for row in evaluations if _legacy_evaluation(row, cutoff)]
    invalid_evaluation_ids = {row.id for row in invalid_evaluations}

    profile_events = (
        db.query(ProfileEvent)
        .filter(ProfileEvent.student_id == username)
        .order_by(ProfileEvent.created_at.desc())
        .all()
    )
    invalid_profile_events = [
        row for row in profile_events
        if (row.created_at or datetime.datetime.min) < cutoff
        and not str(row.source_type or "").startswith("legacy_invalid")
    ] if invalid_evaluation_ids else []

    return {
        "audits": audits,
        "invalid_evaluations": invalid_evaluations,
        "invalid_profile_events": invalid_profile_events,
    }


def print_report(audit_result: dict, username: str) -> None:
    audits = audit_result["audits"]
    archived = [row for row in audits if row["reasons"]]
    kept = [row for row in audits if not row["reasons"]]
    reason_counts = Counter(
        reason.split("：", 1)[0]
        for row in archived
        for reason in row["reasons"]
    )
    print(f"用户: {username}")
    print(f"当前活动资源: {len(audits)}")
    print(f"建议归档: {len(archived)}")
    print(f"通过严格审计且保留: {len(kept)}")
    print(f"需标记失效的旧评价: {len(audit_result['invalid_evaluations'])}")
    print(f"需标记失效的旧画像快照: {len(audit_result['invalid_profile_events'])}")
    print("归档原因统计:")
    for reason, count in reason_counts.most_common():
        print(f"- {reason}: {count}")
    print("保留资源:")
    for row in kept:
        artifact = row["artifact"]
        print(f"- {artifact.artifact_id} | {artifact.type} | {row['review'].get('score', 0)} | {artifact.title}")
    print("归档样例:")
    for row in archived[:20]:
        artifact = row["artifact"]
        print(f"- {artifact.artifact_id} | {artifact.type} | {artifact.title} | {'；'.join(row['reasons'])}")


def apply_audit(db, audit_result: dict) -> None:
    now = datetime.datetime.now()
    reviewed_at = now.isoformat(timespec="seconds")
    for audit in audit_result["audits"]:
        artifact = audit["artifact"]
        artifact.quality_score = float(audit["review"].get("score") or 0)
        artifact.updated_at = now
        if not audit["reasons"]:
            continue
        artifact.status = "archived"
        resource = audit["resource"]
        if resource:
            resource.status = "未通过"
            resource.review_comment = "历史质量审计归档：" + "；".join(audit["reasons"])
            resource.reviewed_at = reviewed_at

    for record in audit_result["invalid_evaluations"]:
        original = str(record.diagnosis_type or "unknown")
        record.diagnosis_type = f"legacy_invalid:{original}"[:64]

    for event in audit_result["invalid_profile_events"]:
        original = str(event.source_type or "unknown")
        event.source_type = f"legacy_invalid:{original}"[:64]
        if not str(event.reason or "").startswith("历史画像快照已失效"):
            event.reason = f"历史画像快照已失效（原因：旧评价数据污染）；{event.reason or ''}"

    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="student")
    parser.add_argument("--legacy-before", default="2026-07-18")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    cutoff = _parse_cutoff(args.legacy_before)
    db = SessionLocal()
    try:
        audit_result = build_audit(db, args.username, cutoff)
        print_report(audit_result, args.username)
        if not args.apply:
            print("干跑完成，数据库未修改。如需执行，加 --apply。")
            return
        apply_audit(db, audit_result)
        print("已应用：仅更新归档/失效标记，没有物理删除任何行。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
