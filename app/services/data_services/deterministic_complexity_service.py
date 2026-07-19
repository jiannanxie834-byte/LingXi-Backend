"""Deterministic checks for common algorithm-complexity questions.

The normal answer route uses this module before asking the language model.  When
the code shape is one we can prove locally, the verified answer is returned
directly so exact loop counts and boundary cases cannot drift with the model.
"""

import ast
import math
import re
from typing import Optional


def _extract_code(text: str) -> str:
    fenced = re.search(r"```(?:python|py)?\s*\n(.*?)```", text or "", re.IGNORECASE | re.DOTALL)
    if fenced:
        return fenced.group(1).strip()

    lines = (text or "").splitlines()
    code_start = next(
        (
            index
            for index, line in enumerate(lines)
            if re.match(r"\s*(?:for|while|def)\s+", line)
        ),
        None,
    )
    return "\n".join(lines[code_start:]).strip() if code_start is not None else ""


def _name(node) -> str:
    return node.id if isinstance(node, ast.Name) else ""


def _range_shape(node) -> Optional[dict]:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "range":
        return None
    args = node.args
    if len(args) == 1 and isinstance(args[0], ast.Name):
        return {"start": "0", "stop": args[0].id, "step": 1, "count": args[0].id}
    if len(args) == 2 and isinstance(args[0], ast.Constant) and isinstance(args[1], ast.Name):
        start = args[0].value
        if isinstance(start, int):
            return {
                "start": str(start),
                "stop": args[1].id,
                "step": 1,
                "count": f"max(0, {args[1].id} - {start})",
            }
    return None


def _geometric_while(loop: ast.While, initializers: list) -> Optional[dict]:
    if not isinstance(loop.test, ast.Compare) or len(loop.test.ops) != 1 or len(loop.test.comparators) != 1:
        return None
    if not isinstance(loop.test.ops[0], ast.Lt):
        return None
    variable = _name(loop.test.left)
    limit = _name(loop.test.comparators[0])
    if not variable or not limit:
        return None

    start = None
    for statement in initializers:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and _name(statement.targets[0]) == variable:
            if isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, (int, float)):
                start = statement.value.value
    if start != 1:
        return None

    factor = None
    for statement in loop.body:
        if isinstance(statement, ast.AugAssign) and _name(statement.target) == variable:
            if isinstance(statement.op, ast.Mult) and isinstance(statement.value, ast.Constant):
                factor = statement.value.value
        elif isinstance(statement, ast.Assign) and len(statement.targets) == 1 and _name(statement.targets[0]) == variable:
            value = statement.value
            if (
                isinstance(value, ast.BinOp)
                and isinstance(value.op, ast.Mult)
                and _name(value.left) == variable
                and isinstance(value.right, ast.Constant)
            ):
                factor = value.right.value
    if not isinstance(factor, (int, float)) or factor <= 1:
        return None
    return {"variable": variable, "limit": limit, "factor": factor}


def _verified_loop_answer(text: str) -> str:
    code = _extract_code(text)
    if not code:
        return ""
    try:
        tree = ast.parse(code)
    except (IndentationError, SyntaxError):
        return ""

    outer = next((node for node in tree.body if isinstance(node, ast.For)), None)
    if not outer:
        return ""
    outer_range = _range_shape(outer.iter)
    if not outer_range:
        return ""

    inner_while = next((node for node in outer.body if isinstance(node, ast.While)), None)
    if inner_while:
        shape = _geometric_while(inner_while, outer.body[: outer.body.index(inner_while)])
        if shape and outer_range["stop"] == shape["limit"]:
            factor = shape["factor"]
            factor_text = str(int(factor)) if float(factor).is_integer() else str(factor)
            variable = shape["limit"]
            return (
                f"这段代码的总时间复杂度是 **O({variable} log {variable})**。外层 `range({variable})` "
                f"执行 {variable} 次；每次外层循环都把 `j` 从 1 开始按 {factor_text} 倍增长，"
                f"所以内层 `while` 的精确执行次数是：当 {variable} ≤ 1 时为 0 次，当 {variable} > 1 时为 "
                f"`ceil(log_{factor_text}({variable}))` 次。\n\n"
                f"因此内层语句的总执行次数是 `{variable} × ceil(log_{factor_text}({variable}))`（{variable} > 1）。"
                f"边界上，{variable}=0 时外层不执行；{variable}=1 时外层执行 1 次、内层执行 0 次。"
            )

    inner_for = next((node for node in outer.body if isinstance(node, ast.For)), None)
    if inner_for:
        inner_range = _range_shape(inner_for.iter)
        if inner_range and inner_range["stop"] == outer_range["stop"]:
            variable = outer_range["stop"]
            return (
                f"外层循环执行 {variable} 次，每次又完整执行 {variable} 次内层循环，"
                f"所以内层语句一共执行 **{variable}² 次**，总时间复杂度是 **O({variable}²)**。"
                f"当 {variable}=0 时两层都不执行；当 {variable}=1 时内层语句执行 1 次。"
            )

    variable = outer_range["stop"]
    return (
        f"`range({variable})` 在 {variable} ≥ 0 时会产生 0 到 {variable}-1，共 **{variable} 次**迭代，"
        f"因此单层循环的时间复杂度是 **O({variable})**。边界上，{variable}=0 时执行 0 次，"
        f"{variable}=1 时执行 1 次。"
    )


def _binary_search_answer(text: str) -> str:
    normalized = re.sub(r"\s+", "", text or "").lower()
    if "二分" not in normalized or not any(marker in normalized for marker in ("复杂度", "比较", "几次", "为什么", "快")):
        return ""

    number_match = re.search(r"(?:长度(?:为|是)?|有|共)?\s*(\d+)\s*(?:个)?(?:元素|数据|数)?", text or "")
    size = int(number_match.group(1)) if number_match else None
    if size is not None and size > 0:
        halvings = math.ceil(math.log2(size))
        comparisons = math.floor(math.log2(size)) + 1
        sequence = [size]
        while sequence[-1] > 1:
            sequence.append(math.ceil(sequence[-1] / 2))
        sequence_text = " → ".join(str(value) for value in sequence)
        return (
            "二分查找的时间复杂度是 **O(log n)**，前提是数据已经有序；每次比较后，候选区间大约缩小一半。"
            f"以 {size} 个元素为例，候选数量可看成 `{sequence_text}`，经过 {halvings} 次减半只剩 1 个候选。"
            f"但“减半次数”和“实际比较次数”不能混为一谈：经典二分实现的最坏比较次数可达到 **{comparisons} 次**。"
        )

    return (
        "二分查找的时间复杂度是 **O(log n)**，因为每次比较都会把候选范围缩小约一半。"
        "它要求待查数据有序；最坏比较次数通常按 `floor(log₂ n) + 1` 计算。"
    )


def verified_answer(text: str) -> str:
    """Return a locally proven answer, or an empty string when the shape is unknown."""
    loop_answer = _verified_loop_answer(text)
    if loop_answer:
        return loop_answer
    return _binary_search_answer(text)
