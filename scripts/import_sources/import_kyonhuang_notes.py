#!/usr/bin/env python3
"""Import lightweight source metadata from KyonHuang Andrew Ng notes.

The importer intentionally stores bounded excerpts and structural metadata.
Curated courseware is generated later from the chapter map and source coverage,
so student-facing resources do not become a dump of third-party text.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SOURCE_ID = "src_kyonhuang_andrew_ng"
DEFAULT_SOURCE = Path("/tmp/lingxi_kyonhuang_notes")
DEFAULT_OUT = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "knowledge_base"
    / "deep_learning_v2"
    / "imported_sources"
    / "kyonhuang_andrew_ng"
)


CHAPTER_KEYWORDS = [
    ("chapter_01_intro", ["概述", "深度学习", "what is"]),
    ("chapter_03_neural_network_basics", ["逻辑回归", "神经网络基础", "浅层神经网络", "向量化"]),
    ("chapter_04_deep_network_and_backprop", ["深层神经网络", "反向传播", "前向传播"]),
    ("chapter_05_regularization_and_generalization", ["正则化", "初始化", "Batch", "超参数", "实用层面"]),
    ("chapter_06_optimization", ["优化算法", "Momentum", "RMSProp", "Adam", "mini-batch"]),
    ("chapter_07_cnn_foundation", ["卷积神经网络", "卷积", "池化"]),
    ("chapter_08_cnn_architectures_and_cv_practice", ["深度卷积网络", "实例探究", "ResNet", "Inception"]),
    ("chapter_09_cv_advanced_tasks", ["目标检测", "人脸识别", "风格迁移"]),
    ("chapter_10_sequence_models", ["序列模型", "循环神经网络", "RNN", "LSTM", "GRU"]),
    ("chapter_11_attention_transformer", ["Attention", "注意力", "词嵌入", "Transformer"]),
]


def _clean(value: str) -> str:
    value = re.sub(r"!\[[^\]]*]\([^)]+\)", "", value)
    value = re.sub(r"\[[^\]]+]\([^)]+\)", lambda m: m.group(0).split("](")[0].lstrip("["), value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _headings(markdown: str) -> list[str]:
    result = []
    for line in markdown.splitlines():
        match = re.match(r"^(#{1,4})\s+(.+)$", line.strip())
        if match:
            title = match.group(2).strip()
            if title and title not in result:
                result.append(title)
    return result[:24]


def _formulas(markdown: str) -> list[str]:
    values = re.findall(r"\$\$(.*?)\$\$|\$(.*?)\$", markdown, flags=re.S)
    formulas = []
    for block, inline in values:
        item = _clean(block or inline)
        if item and len(item) <= 240 and item not in formulas:
            formulas.append(item)
    return formulas[:16]


def _images(markdown: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"!\[[^\]]*]\(([^)]+)\)", markdown)))[:24]


def _map_chapters(text: str) -> list[str]:
    haystack = text.lower()
    matched = []
    for chapter_id, keywords in CHAPTER_KEYWORDS:
        if any(keyword.lower() in haystack for keyword in keywords):
            matched.append(chapter_id)
    return matched or ["chapter_01_intro"]


def import_source(source_dir: Path, output_dir: Path) -> dict:
    docs_dir = source_dir / "docs"
    if not docs_dir.exists():
        raise FileNotFoundError(f"docs directory not found: {docs_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    chunks = []
    source_index = []

    sidebar = docs_dir / "_sidebar.md"
    sidebar_headings = _headings(sidebar.read_text(encoding="utf-8", errors="ignore")) if sidebar.exists() else []

    for idx, path in enumerate(sorted(docs_dir.rglob("*.md")), start=1):
        if path.name.startswith("_"):
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        headings = _headings(raw)
        title = headings[0] if headings else path.stem
        excerpt = _clean(raw)[:1600]
        mapped = _map_chapters(" ".join([str(path), title, " ".join(headings), excerpt]))
        chunk = {
            "source_id": SOURCE_ID,
            "chunk_id": f"kyon_{idx:04d}",
            "source_path": str(path.relative_to(source_dir)),
            "title": title,
            "heading_path": headings[:8],
            "content_excerpt": excerpt,
            "formulas": _formulas(raw),
            "images": _images(raw),
            "mapped_chapter_candidates": mapped,
            "mapped_unit_candidates": [],
        }
        chunks.append(chunk)
        source_index.append({
            "source_path": chunk["source_path"],
            "title": title,
            "mapped_chapter_candidates": mapped,
        })

    with (output_dir / "extracted_chunks.jsonl").open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    (output_dir / "source_index.json").write_text(
        json.dumps({
            "source_id": SOURCE_ID,
            "source_root": str(source_dir),
            "sidebar_headings": sidebar_headings,
            "items": source_index,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    by_chapter = {}
    for chunk in chunks:
        for chapter_id in chunk["mapped_chapter_candidates"]:
            by_chapter[chapter_id] = by_chapter.get(chapter_id, 0) + 1
    report = [
        "# KyonHuang Andrew Ng Notes 抽取报告",
        "",
        f"- 来源目录：`{source_dir}`",
        f"- Markdown 文件数：{len(chunks)}",
        "- 抽取策略：保留标题、公式、图片引用和有限摘录，学生端只使用后续重构讲义。",
        "",
        "## 章节覆盖",
        *[f"- {chapter_id}: {count} 个片段" for chapter_id, count in sorted(by_chapter.items())],
        "",
    ]
    (output_dir / "extraction_report.md").write_text("\n".join(report), encoding="utf-8")
    return {"chunks": len(chunks), "chapters": by_chapter}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    result = import_source(args.source_dir, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
