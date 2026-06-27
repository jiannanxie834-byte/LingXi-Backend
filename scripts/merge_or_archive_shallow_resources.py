import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal
from app.models.schemas import Resource, ResourceArtifact
from app.services.data_services import chapter_resource_service, resource_quality_gate


ARCHIVE_STATUSES = {"archived_shallow", "merged_into_chapter_pack", "legacy_demo_only"}
LEGACY_SEED_UPLOADERS = {"课程知识库种子"}
LEGACY_SOURCE_MARKERS = {
    "《深度学习》课程知识库",
    "人工智能课程知识库",
    "课程知识库 /",
}


def compact_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def should_archive(row: Resource):
    metadata = chapter_resource_service.extract_metadata(row.agent_notes or "")
    if metadata.get("quality_level") == "curated":
        return "", ""
    teaching_review = resource_quality_gate.extract_teaching_quality_review(row.agent_notes or "")
    if row.status == "已通过" and teaching_review.get("status") == "failed":
        return "archived_shallow", "教学质量门控未通过，不应继续作为学生端开放资源展示。"
    source_text = "\n".join([row.source or "", row.agent_notes or ""])
    if (
        not metadata
        and (
            row.id.startswith("KB-DL-CH")
            or row.uploader in LEGACY_SEED_UPLOADERS
            or any(marker in source_text for marker in LEGACY_SOURCE_MARKERS)
        )
    ):
        return "legacy_demo_only", "旧版课程种子资源已由章节化 courseware 替代，仅保留管理员治理追溯。"
    if row.id.startswith("KB-DL-UNIT"):
        return "merged_into_chapter_pack", "细粒度知识点卡已合并进章节 courseware，不再作为学生端平铺资源展示。"
    if row.type == "课程讲解文档" and compact_len(row.content or "") < 1200:
        return "archived_shallow", "讲义正文过短，应合并进章节主讲义。"
    if row.type == "练习题集" and len(re.findall(r"(^|\n)###\s*题目\s*\d+", row.content or "")) < 8:
        return "merged_into_chapter_pack", "练习题数量不足，应合并进章节题集。"
    if row.type in {"拓展阅读包", "个性化视频观看指南", "外部公开视频推荐卡"}:
        if compact_len(row.content or "") < 1200 or "版权说明" not in (row.content or ""):
            return "merged_into_chapter_pack", "阅读/视频资源过浅，应合并进章节阅读与视频指南。"
    if row.type in {"交互动画规格", "动画分镜"} and compact_len(row.content or "") < 800:
        return "merged_into_chapter_pack", "动画说明过短，应合并为章节交互动画规格。"
    return "", ""


def main():
    db = SessionLocal()
    changed = []
    synced_artifacts = 0
    try:
        for row in db.query(Resource).all():
            if row.status in ARCHIVE_STATUSES:
                continue
            status, reason = should_archive(row)
            if not status:
                continue
            row.status = status
            row.review_comment = reason
            row.reviewed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            changed.append({"id": row.id, "title": row.title, "status": status})
        archived_resource_ids = {
            row.id
            for row in db.query(Resource.id)
            .filter(Resource.status.in_(ARCHIVE_STATUSES))
            .all()
        }
        for artifact in db.query(ResourceArtifact).all():
            if artifact.resource_id in archived_resource_ids and artifact.status != "archived":
                artifact.status = "archived"
                artifact.updated_at = datetime.datetime.now()
                synced_artifacts += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print({
        "archived_count": len(changed),
        "synced_artifacts": synced_artifacts,
        "items": changed[:20],
    })


if __name__ == "__main__":
    main()
