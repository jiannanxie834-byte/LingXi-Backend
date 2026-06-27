import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.data_services import chapter_resource_service


COURSE_DIR = ROOT / "data" / "knowledge_base" / "deep_learning_v2"
OUTPUT = ROOT / "docs" / "chapter_resource_completeness.md"

CORE_CHAPTERS = {
    "chapter_03_neural_network_basics",
    "chapter_04_deep_network_and_backprop",
    "chapter_05_regularization_and_generalization",
    "chapter_06_optimization",
    "chapter_07_cnn_foundation",
    "chapter_08_cnn_architectures_and_cv_practice",
    "chapter_10_sequence_models",
    "chapter_11_attention_transformer",
}

REQUIRED_TYPES = ["课程讲解文档", "知识点思维导图", "练习题集", "拓展阅读包"]
CORE_EXTRA_TYPES = ["PyTorch 实操案例", "交互动画规格", "课程实践项目任务书"]


def compact_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def count_exercises(text: str) -> int:
    return len(re.findall(r"(^|\n)##\s*\d+\.", text or ""))


def read_file(resource_key: str) -> str:
    path = COURSE_DIR / "courseware" / resource_key
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 章节资源完整度检查",
        "",
        "| 章节 | 必备类型 | 核心额外资源 | 主讲义字数 | 题目数 | 结论 |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    failed = []
    for chapter in chapter_resource_service.load_chapter_index():
        chapter_id = chapter.get("chapter_id", "")
        resources = [*(chapter.get("primary_resources") or []), *(chapter.get("optional_resources") or [])]
        types = {item.get("type") for item in resources}
        missing = [item for item in REQUIRED_TYPES if item not in types]
        core_extra_ok = chapter_id not in CORE_CHAPTERS or any(item in types for item in CORE_EXTRA_TYPES)

        main_item = next((item for item in resources if item.get("type") == "课程讲解文档"), {})
        exercise_item = next((item for item in resources if item.get("type") == "练习题集"), {})
        main_text = read_file(main_item.get("resource_key", ""))
        exercise_text = read_file(exercise_item.get("resource_key", ""))
        main_len = compact_len(main_text)
        exercise_count = count_exercises(exercise_text)
        main_threshold = 4500 if chapter_id in CORE_CHAPTERS else 3000
        exercise_threshold = 12 if chapter_id in CORE_CHAPTERS else 8

        issues = []
        if missing:
            issues.append(f"缺少：{'、'.join(missing)}")
        if not core_extra_ok:
            issues.append("核心章节缺少代码实验/动画/项目任务书")
        if main_len < main_threshold:
            issues.append(f"主讲义不足 {main_threshold} 字")
        if exercise_count < exercise_threshold:
            issues.append(f"练习题不足 {exercise_threshold} 题")

        conclusion = "通过" if not issues else "未通过：" + "；".join(issues)
        if issues:
            failed.append(chapter.get("chapter_title", chapter_id))
        lines.append(
            f"| {chapter.get('chapter_title')} | {'通过' if not missing else '缺失'} | "
            f"{'通过' if core_extra_ok else '缺失'} | {main_len} | {exercise_count} | {conclusion} |"
        )

    lines += ["", f"检查结果：{'全部通过' if not failed else '未通过章节：' + '、'.join(failed)}"]
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"success": not failed, "failed": failed, "output": str(OUTPUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
