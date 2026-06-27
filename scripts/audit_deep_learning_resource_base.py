import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal
from app.models.schemas import Resource, ResourceArtifact
from app.services.data_services import chapter_resource_service, resource_quality_gate


COURSE_DIR = ROOT / "data" / "knowledge_base" / "deep_learning"
DOCS_DIR = ROOT / "docs"
OUTPUT = DOCS_DIR / "deep_learning_resource_audit.md"


def compact_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def heading_count(text: str) -> int:
    return len(re.findall(r"(^|\n)##\s+", text or ""))


def has_any(text: str, words):
    return any(word in (text or "") for word in words)


def count_exercises(text: str) -> int:
    return len(re.findall(r"(^|\n)###\s*题目\s*\d+", text or ""))


def json_load(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            count += 1
    return count


def quality_label(resource_type: str, content: str, chapter_core: bool = False) -> str:
    length = compact_len(content)
    exercise_count = count_exercises(content)
    if resource_type == "课程讲解文档":
        threshold = 4500 if chapter_core else 3000
        if length < threshold:
            return "low"
        if heading_count(content) < 8:
            return "low"
    if resource_type == "练习题集":
        if exercise_count < 8 or "答案" not in content or "解析" not in content:
            return "low"
    if resource_type == "PyTorch 实操案例":
        required = ["完整代码", "运行命令", "学生任务", "常见报错"]
        if any(item not in content for item in required):
            return "low"
    if resource_type in {"拓展阅读包", "个性化视频观看指南", "外部公开视频推荐卡"}:
        if "版权说明" not in content or "观看/阅读后任务" not in content:
            return "low"
    return "curated"


def file_metrics(path: Path):
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return {
        "path": str(path.relative_to(ROOT)),
        "chars": compact_len(text),
        "headings": heading_count(text),
        "has_formula_or_flow": has_any(text, ["=", "公式", "流程", "算法", "softmax", "梯度"]),
        "has_examples": has_any(text, ["例子", "示例", "案例", "例题"]),
        "exercise_count": count_exercises(text),
        "has_answers": "答案" in text and "解析" in text,
        "has_code": "```python" in text or "伪代码" in text or "```text" in text,
        "has_reference": "参考来源说明" in text or "版权说明" in text,
    }


def load_db_resources():
    db = SessionLocal()
    try:
        resources = db.query(Resource).all()
        artifacts = db.query(ResourceArtifact).all()
        return resources, artifacts
    finally:
        db.close()


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    chapter_index = chapter_resource_service.load_chapter_index()
    core_chapters = {
        "chapter_04_backpropagation",
        "chapter_05_optimization",
        "chapter_06_regularization",
        "chapter_07_cnn",
        "chapter_08_rnn_lstm",
        "chapter_08_rnn_lstm_gru",
        "chapter_09_transformer",
        "chapter_11_pytorch_practice",
        "chapter_12_final_project",
    }

    resources, artifacts = load_db_resources()
    resource_rows = []
    shallow = []
    duplicates = []
    seen = defaultdict(list)
    by_chapter = defaultdict(list)

    for row in resources:
        metadata = chapter_resource_service.extract_metadata(row.agent_notes or "")
        chapter_id = metadata.get("chapter_id", "")
        quality = resource_quality_gate.extract_teaching_quality_review(row.agent_notes or "")
        label = quality.get("status") or quality_label(row.type, row.content or "", chapter_id in core_chapters)
        item = {
            "id": row.id,
            "title": row.title,
            "type": row.type,
            "status": row.status,
            "chapter_id": chapter_id or "未标注",
            "chars": compact_len(row.content or ""),
            "quality": label,
        }
        resource_rows.append(item)
        by_chapter[item["chapter_id"]].append(item)
        seen[(row.title, row.type)].append(row.id)
        if label in {"low", "failed"} or item["chars"] < 1200 or row.id.startswith("KB-DL-UNIT"):
            shallow.append(item)

    for key, ids in seen.items():
        if len(ids) > 1:
            duplicates.append({"title": key[0], "type": key[1], "ids": ids})

    legacy_chapter_files = sorted((COURSE_DIR / "chapters").glob("*.md"))
    lab_files = sorted((COURSE_DIR / "labs").glob("*.py"))
    video_items = json_load(COURSE_DIR / "video_catalog.json", [])
    knowledge_unit_count = jsonl_count(COURSE_DIR / "knowledge_units.jsonl")

    lines = [
        "# 深度学习资源库审计报告",
        "",
        "## 0. 原始数据源扫描",
        "",
        f"- 原始章节讲义：{len(legacy_chapter_files)} 个文件",
        f"- 细粒度知识单元：{knowledge_unit_count} 条",
        f"- 外部公开视频目录：{len(video_items) if isinstance(video_items, list) else 0} 条",
        f"- 本地实验脚本：{len(lab_files)} 个",
        "",
        "| 类型 | 文件/目录 | 数量 | 治理建议 |",
        "| --- | --- | ---: | --- |",
        f"| 原始章节讲义 | data/knowledge_base/deep_learning/chapters | {len(legacy_chapter_files)} | 保留为内部知识底稿，学生端优先展示 courseware 章节资源 |",
        f"| 课程图谱单元 | knowledge_units.jsonl | {knowledge_unit_count} | 用于语义接地和章节索引，不再直接生成平铺小卡片 |",
        f"| 视频目录 | video_catalog.json | {len(video_items) if isinstance(video_items, list) else 0} | 仅作 link_only 推荐，不下载、不搬运、不重托管 |",
        f"| 实验脚本 | labs/*.py | {len(lab_files)} | 合并进章节 code_lab 或作为可运行实验附件依据 |",
        "",
        "## 1. 章节文件质量",
        "",
        "| 章节 | 文件 | 字数 | 二级标题 | 公式/流程 | 例子 | 题目数 | 答案解析 | 代码/伪代码 | 参考说明 |",
        "| --- | --- | ---: | ---: | --- | --- | ---: | --- | --- | --- |",
    ]

    for chapter in chapter_index:
        resources_in_index = [
            *((chapter.get("primary_resources") or [])),
            *((chapter.get("optional_resources") or [])),
        ]
        for item in resources_in_index:
            metrics = file_metrics(COURSE_DIR / "courseware" / item.get("resource_key", ""))
            lines.append(
                f"| {chapter.get('chapter_title')} | {item.get('resource_key')} | {metrics['chars']} | {metrics['headings']} | "
                f"{'是' if metrics['has_formula_or_flow'] else '否'} | {'是' if metrics['has_examples'] else '否'} | "
                f"{metrics['exercise_count']} | {'是' if metrics['has_answers'] else '否'} | "
                f"{'是' if metrics['has_code'] else '否'} | {'是' if metrics['has_reference'] else '否'} |"
            )

    lines += [
        "",
        "## 2. 数据库资源概览",
        "",
        f"- Resource 总数：{len(resources)}",
        f"- ResourceArtifact 总数：{len(artifacts)}",
        "",
        "| 章节 | 资源数 |",
        "| --- | ---: |",
    ]
    for chapter_id, items in sorted(by_chapter.items()):
        lines.append(f"| {chapter_id} | {len(items)} |")

    lines += [
        "",
        "## 3. 每个资源正文长度与质量等级",
        "",
        "| ID | 标题 | 类型 | 状态 | 章节 | 正文字数 | 教学质量 |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for item in resource_rows:
        lines.append(
            f"| {item['id']} | {item['title']} | {item['type']} | {item['status']} | {item['chapter_id']} | {item['chars']} | {item['quality']} |"
        )

    lines += [
        "",
        "## 4. 浅资源列表",
        "",
        "| ID | 标题 | 类型 | 章节 | 字数 | 建议 |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for item in shallow:
        lines.append(f"| {item['id']} | {item['title']} | {item['type']} | {item['chapter_id']} | {item['chars']} | 合并进章节 courseware 或归档 |")

    lines += [
        "",
        "## 5. 重复资源列表",
        "",
    ]
    if duplicates:
        for item in duplicates:
            lines.append(f"- {item['title']} / {item['type']}：{', '.join(item['ids'])}")
    else:
        lines.append("- 未发现完全同名同类型重复资源。")

    lines += [
        "",
        "## 6. 建议合并的资源列表",
        "",
        "- `KB-DL-UNIT-*` 初始知识点资源卡：合并为章节主讲义、章节练习题集或阅读指南。",
        "- 少于 1200 字的讲义、只有链接的阅读材料、只有几行说明的动画分镜：归档为 `archived_shallow` 或 `merged_into_chapter_pack`。",
        "",
        "## 7. 每章缺失资源类型",
        "",
    ]
    for chapter in chapter_index:
        types = {item.get("type") for item in [*(chapter.get("primary_resources") or []), *(chapter.get("optional_resources") or [])]}
        missing = [item for item in ["课程讲解文档", "知识点思维导图", "练习题集", "个性化视频观看指南"] if item not in types]
        lines.append(f"- {chapter.get('chapter_title')}：{'无' if not missing else '、'.join(missing)}")

    lines += [
        "",
        "## 8. 学生端不应展示的内部字段",
        "",
        "- 资源编码 / resource_id / artifact_id",
        "- 数据库 ID、审核状态、status",
        "- 生成 Agent 内部名、agent_trace_id、agent_notes",
        "- 推荐分数、命中标签、内部质量原始 JSON",
    ]

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written: {OUTPUT}")


if __name__ == "__main__":
    main()
