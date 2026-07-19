import re
from typing import Dict, List


QUESTION_HEADING_RE = re.compile(
    r"(?m)^\s*#{2,6}\s*(?:第\s*)?题目?\s*(\d+)\s*[|｜:：、.]\s*([^\n]+?)\s*$"
)
FIELD_RE = re.compile(
    r"^\s*(?:[-*+]\s*)?(?:\*\*|__)?"
    r"(题目|题干|知识点|答案|参考答案|解析|答案解析|常见错误|评分要点|难度)"
    r"(?:\*\*|__)?\s*[:：]\s*(.*)$"
)
OPTION_RE = re.compile(r"^\s*(?:[-*+]\s*)?(?:\(([A-Ha-h])\)|([A-Ha-h]))\s*[.、:：）)]\s*(.+?)\s*$")


def _clean(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^(?:\*\*|__)(.*?)(?:\*\*|__)$", r"\1", text)
    return text.strip()


def _question_type(label: str, options: List[Dict]) -> str:
    source = str(label or "")
    if "判断" in source:
        return "true_false"
    if "选择" in source and len(options) >= 2:
        return "single_choice"
    if any(marker in source for marker in ["代码", "编程"]):
        return "code"
    if any(marker in source for marker in ["计算", "过程", "实验", "项目", "分析"]):
        return "analysis"
    return "short_answer"


def _distribute_points(count: int) -> List[int]:
    if count <= 0:
        return []
    base, remainder = divmod(100, count)
    return [base + (1 if index < remainder else 0) for index in range(count)]


def _parse_block(number: int, label: str, block: str) -> Dict:
    # 最后一题之后常跟着“练习顺序 / 复盘清单 / 来源”等全局章节，
    # 这些内容不属于本题的解析或常见错误。
    block = re.split(r"(?m)^#{1,2}\s+", block, maxsplit=1)[0]
    values = {
        "stem": [],
        "knowledge_point": [],
        "reference_answer": [],
        "explanation": [],
        "common_errors": [],
        "rubric": [],
        "difficulty": [],
    }
    field_map = {
        "题目": "stem",
        "题干": "stem",
        "知识点": "knowledge_point",
        "答案": "reference_answer",
        "参考答案": "reference_answer",
        "解析": "explanation",
        "答案解析": "explanation",
        "常见错误": "common_errors",
        "评分要点": "rubric",
        "难度": "difficulty",
    }
    current = "stem"
    options = []

    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        field_match = FIELD_RE.match(line)
        if field_match:
            current = field_map[field_match.group(1)]
            value = _clean(field_match.group(2))
            if value:
                values[current].append(value)
            continue

        option_match = OPTION_RE.match(line)
        if current == "stem" and option_match:
            key = (option_match.group(1) or option_match.group(2) or "").upper()
            options.append({"key": key, "text": _clean(option_match.group(3))})
            continue

        if line.strip():
            values[current].append(line.strip())

    stem = _clean("\n".join(values["stem"]))
    question_label = _clean(label) or "练习题"
    return {
        "question_id": f"q{number}",
        "question_index": number,
        "label": question_label,
        "type": _question_type(question_label, options),
        "stem": stem,
        "options": options,
        "reference_answer": _clean("\n".join(values["reference_answer"])),
        "explanation": _clean("\n".join(values["explanation"])),
        "common_errors": _clean("\n".join(values["common_errors"])),
        "knowledge_point": _clean("\n".join(values["knowledge_point"])),
        "rubric": _clean("\n".join(values["rubric"])),
        "difficulty": _clean("\n".join(values["difficulty"])),
    }


def parse_exercise_content(content: str) -> List[Dict]:
    """将历史 Markdown 题集转成后端唯一的结构化题目模型。

    只识别明确的“题目 N｜题型”标题，因此不会再把题集简介、练习顺序或
    复盘清单误当成第一题。
    """
    source = str(content or "").replace("\r\n", "\n")
    matches = list(QUESTION_HEADING_RE.finditer(source))
    questions = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        number = int(match.group(1))
        parsed = _parse_block(number, match.group(2), source[start:end])
        if parsed["stem"]:
            questions.append(parsed)

    points = _distribute_points(len(questions))
    for index, question in enumerate(questions):
        question["question_index"] = index + 1
        question["question_id"] = f"q{index + 1}"
        question["points"] = points[index]
    return questions


def public_questions(questions: List[Dict]) -> List[Dict]:
    allowed = {
        "question_id",
        "question_index",
        "label",
        "type",
        "stem",
        "options",
        "knowledge_point",
        "difficulty",
        "points",
    }
    return [{key: value for key, value in question.items() if key in allowed} for question in questions]


def answer_sheet(questions: List[Dict]) -> List[Dict]:
    return [
        {
            "question_id": question["question_id"],
            "question_index": question["question_index"],
            "answer": question.get("reference_answer") or "",
            "explanation": question.get("explanation") or "",
            "common_errors": question.get("common_errors") or "",
        }
        for question in questions
    ]


def sanitized_markdown(questions: List[Dict]) -> str:
    lines = ["## 作答说明", "", "请按顺序完成以下题目，答案与解析将在提交后展示。"]
    for question in questions:
        lines.extend([
            "",
            f"### 第 {question['question_index']} 题｜{question.get('label') or '练习题'}",
            "",
        ])
        if question.get("knowledge_point"):
            lines.extend([f"**知识点**：{question['knowledge_point']}", ""])
        lines.append(question.get("stem") or "")
        for option in question.get("options") or []:
            lines.append(f"- {option.get('key')}. {option.get('text')}")
    return "\n".join(lines).strip()


def public_artifact(artifact: Dict) -> Dict:
    if not artifact:
        return {}
    result = dict(artifact)
    artifact_type = str(result.get("type") or "")
    if "练习题" not in artifact_type and artifact_type != "exercise_set":
        return result
    questions = parse_exercise_content(result.get("content") or "")
    result["questions"] = public_questions(questions)
    result["question_count"] = len(questions)
    result["content"] = sanitized_markdown(questions)
    return result
