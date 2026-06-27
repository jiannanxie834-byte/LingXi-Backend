#!/usr/bin/env python3
"""Import lightweight metadata from AccumulateMore/CV notebooks."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SOURCE_ID = "src_accumulate_more_cv"
DEFAULT_SOURCE = Path("/tmp/lingxi_accumulate_cv")
DEFAULT_OUT = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "knowledge_base"
    / "deep_learning_v2"
    / "imported_sources"
    / "accumulate_more_cv"
)

FILTER_WORDS = [
    "微信",
    "交流群",
    "网盘",
    "内推",
    "广告",
    "关注公众号",
    "扫码",
    "领取资料",
]


def _notebook_index(path: Path) -> int:
    match = re.match(r"(\d+)_", path.name)
    return int(match.group(1)) if match else 0


def _series(index: int) -> str:
    if 100 <= index <= 122:
        return "pytorch_foundation"
    if 200 <= index <= 268:
        return "d2l_deep_learning"
    if 300 <= index <= 354:
        return "andrew_ng_deep_learning"
    return "filtered_or_out_of_scope"


def _chapter_candidates(index: int, title: str) -> list[str]:
    text = f"{index} {title}".lower()
    rules = [
        ("chapter_02_pytorch_foundation", ["tensor", "pytorch", "dataloader", "dataset", "transforms", "gpu", "module", "训练套路", "模型保存", "100", "101", "102", "103", "104", "105", "106", "107", "108", "118", "119", "120", "121"]),
        ("chapter_03_neural_network_basics", ["逻辑回归", "向量化", "浅层", "多层感知机", "softmax", "线性回归", "损失函数", "302", "303", "304", "206", "207", "208"]),
        ("chapter_04_deep_network_and_backprop", ["深层神经网络", "反向传播", "自动求导", "autograd", "305", "115", "205"]),
        ("chapter_05_regularization_and_generalization", ["过拟合", "欠拟合", "权重衰退", "丢弃法", "batch", "初始化", "正则", "209", "210", "211", "212", "314", "316"]),
        ("chapter_06_optimization", ["优化", "优化器", "adam", "sgd", "momentum", "116", "267", "315"]),
        ("chapter_07_cnn_foundation", ["卷积原理", "卷积层", "池化", "多输入多输出", "109", "110", "111", "216", "217", "218", "219", "329"]),
        ("chapter_08_cnn_architectures_and_cv_practice", ["lenet", "alexnet", "vgg", "nin", "googlenet", "resnet", "cifar", "微调", "220", "221", "222", "223", "224", "225", "226", "232", "233", "234", "330"]),
        ("chapter_09_cv_advanced_tasks", ["目标检测", "锚框", "ssd", "yolo", "语义分割", "转置卷积", "fcn", "样式迁移", "人脸识别", "236", "237", "239", "240", "241", "242", "244", "245", "331", "332"]),
        ("chapter_10_sequence_models", ["序列模型", "rnn", "gru", "lstm", "循环神经网络", "双向", "246", "249", "250", "251", "252", "253", "254", "342"]),
        ("chapter_11_attention_transformer", ["注意力", "attention", "transformer", "bert", "seq2seq", "编码器", "解码器", "词向量", "259", "260", "261", "262", "263", "264", "265", "343", "344"]),
        ("chapter_12_final_project", ["项目", "kaggle", "竞赛", "总结", "课程总结", "报告", "213", "235", "238", "266", "268", "323", "324"]),
    ]
    matched = [chapter_id for chapter_id, keys in rules if any(key.lower() in text for key in keys)]
    return matched or ["chapter_01_intro"]


def _clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _cell_source(cell: dict) -> str:
    source = cell.get("source") or []
    return "".join(source) if isinstance(source, list) else str(source)


def _is_noise(text: str) -> bool:
    return any(word in text for word in FILTER_WORDS)


def _code_purpose(code: str) -> str:
    lowered = code.lower()
    if "dataloader" in lowered:
        return "Dataset/DataLoader example"
    if "nn.module" in lowered or "class " in code:
        return "PyTorch model definition"
    if "optimizer" in lowered or ".step()" in lowered:
        return "training loop and optimizer"
    if "lstm" in lowered:
        return "PyTorch LSTM example"
    if "conv" in lowered:
        return "CNN convolution example"
    if "attention" in lowered or "transformer" in lowered:
        return "attention or transformer example"
    return "course code example"


def import_source(source_dir: Path, output_dir: Path) -> dict:
    if not source_dir.exists():
        raise FileNotFoundError(f"source directory not found: {source_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    chunks = []
    source_index = []
    filtered = []

    for path in sorted(source_dir.glob("*.ipynb")):
        index = _notebook_index(path)
        if index >= 400:
            filtered.append({"source_path": path.name, "reason": "400+ Agent/RAG notebook not in course spine"})
            continue
        title = re.sub(r"^\d+_", "", path.stem).replace("_", " ")
        try:
            notebook = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except json.JSONDecodeError:
            filtered.append({"source_path": path.name, "reason": "invalid notebook json"})
            continue

        markdown_parts = []
        code_cells = []
        for cell_index, cell in enumerate(notebook.get("cells") or []):
            text = _clean_text(_cell_source(cell))
            if not text or _is_noise(text):
                continue
            if cell.get("cell_type") == "markdown":
                markdown_parts.append(text)
            elif cell.get("cell_type") == "code" and len(code_cells) < 4:
                code = text.strip()
                if code and not _is_noise(code):
                    code_cells.append({
                        "cell_index": cell_index,
                        "code_excerpt": code[:1200],
                        "purpose": _code_purpose(code),
                    })

        if not markdown_parts and not code_cells:
            filtered.append({"source_path": path.name, "reason": "no usable course cell"})
            continue

        mapped = _chapter_candidates(index, title)
        chunk = {
            "source_id": SOURCE_ID,
            "chunk_id": f"acc_{index:03d}_001",
            "source_path": path.name,
            "notebook_index": index,
            "series": _series(index),
            "title": title,
            "cell_type": "notebook_summary",
            "content_excerpt": "\n\n".join(markdown_parts)[:1800],
            "code_cells": code_cells,
            "mapped_chapter_candidates": mapped,
            "mapped_unit_candidates": [],
        }
        chunks.append(chunk)
        source_index.append({
            "source_path": path.name,
            "notebook_index": index,
            "series": _series(index),
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
            "items": source_index,
            "filtered": filtered,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    by_chapter = {}
    for chunk in chunks:
        for chapter_id in chunk["mapped_chapter_candidates"]:
            by_chapter[chapter_id] = by_chapter.get(chapter_id, 0) + 1
    report = [
        "# AccumulateMore/CV Notebook 抽取报告",
        "",
        f"- 来源目录：`{source_dir}`",
        f"- 纳入 notebook：{len(chunks)}",
        f"- 过滤 notebook：{len(filtered)}",
        "- 抽取策略：保留 notebook 标题、有限 markdown 摘录和必要代码片段，最终课程实验由本项目重构。",
        "",
        "## 章节覆盖",
        *[f"- {chapter_id}: {count} 个 notebook" for chapter_id, count in sorted(by_chapter.items())],
        "",
        "## 过滤记录",
        *[f"- {item['source_path']}: {item['reason']}" for item in filtered[:80]],
    ]
    (output_dir / "extraction_report.md").write_text("\n".join(report), encoding="utf-8")
    return {"chunks": len(chunks), "filtered": len(filtered), "chapters": by_chapter}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    result = import_source(args.source_dir, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
