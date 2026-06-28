import json
import logging
import os
import urllib.error
import urllib.request

from app.config import load_env_file


load_env_file()

logger = logging.getLogger(__name__)

DEFAULT_SPARK_API_URL = "https://spark-api-open.xf-yun.com/v1/chat/completions"
DEFAULT_DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


def _get_provider():
    return os.getenv("LINGXI_LLM_PROVIDER", "local").strip().lower()


def _debug_enabled():
    return os.getenv("LINGXI_DEBUG_LLM", "").strip().lower() in {"1", "true", "yes", "on"}


def _debug(message, *args):
    if _debug_enabled():
        logger.info(message, *args)


def _get_provider_config():
    provider = _get_provider()

    if provider == "spark":
        return {
            "provider": "spark",
            "api_key": os.getenv("SPARK_API_PASSWORD", "").strip(),
            "api_url": os.getenv("SPARK_API_URL", DEFAULT_SPARK_API_URL).strip(),
            "model": os.getenv("SPARK_MODEL", "generalv3").strip(),
        }

    if provider == "deepseek":
        return {
            "provider": "deepseek",
            "api_key": os.getenv("DEEPSEEK_API_KEY", "").strip(),
            "api_url": os.getenv("DEEPSEEK_API_URL", DEFAULT_DEEPSEEK_API_URL).strip(),
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro").strip(),
        }

    return {
        "provider": provider,
        "api_key": "",
        "api_url": "",
        "model": "",
    }


# =========================
# 2. 是否启用LLM
# =========================
def is_enabled():
    config = _get_provider_config()
    enabled = config["provider"] in {"spark", "deepseek"} and bool(config["api_key"])
    return enabled


def _parse_llm_response(data, provider):
    if provider == "spark" and "code" in data and data.get("code") != 0:
        return {"ok": False, "error": data.get("message", "fail"), "content": ""}

    if "error" in data:
        error = data.get("error") or {}
        message = error.get("message") if isinstance(error, dict) else str(error)
        return {"ok": False, "error": message or "LLM error", "content": ""}

    choices = data.get("choices") or []
    if not choices:
        return {"ok": False, "error": "no response", "content": ""}

    first_choice = choices[0] or {}
    _debug("LLM response metadata: %s", {
        "provider": provider,
        "choices": len(choices),
        "finish_reason": first_choice.get("finish_reason"),
    })

    msg = first_choice.get("message") or {}

    content = (
        msg.get("content")
        or msg.get("text")
        or first_choice.get("text")
        or ""
    )

    if isinstance(content, list):
        content = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        )

    if not content:
        if msg.get("reasoning_content") and first_choice.get("finish_reason") == "length":
            return {
                "ok": False,
                "error": "empty content; increase max_tokens for thinking model",
                "content": ""
            }
        return {"ok": False, "error": "empty content", "content": ""}

    return {
        "ok": True,
        "content": content
    }


def extract_json_object(content: str):
    text = (content or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, dict):
        return parsed
    if parsed is not None:
        raise ValueError("LLM JSON response must be an object")

    start = text.find("{")
    if start < 0:
        raise ValueError("LLM response does not contain a JSON object")

    depth = 0
    in_string = False
    escaped = False
    end = -1

    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                break

    if end < 0:
        raise ValueError("LLM response contains incomplete JSON object")

    try:
        parsed = json.loads(text[start:end])
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM response is not valid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("LLM JSON response must be an object")

    return parsed


def _json_max_tokens(default_value: int) -> int:
    try:
        return int(os.getenv("LLM_JSON_MAX_TOKENS", str(default_value)))
    except ValueError:
        return default_value


def _should_retry_json_error(error: str) -> bool:
    return any(
        marker in str(error or "")
        for marker in [
            "LLM response contains incomplete JSON object",
            "LLM response is not valid JSON",
        ]
    )


def chat_json(messages, required_fields=None, temperature=0.2, max_tokens=3000):
    max_tokens = _json_max_tokens(max_tokens)
    strict_messages = [
        {
            "role": "system",
            "content": (
                "你是内部结构化工具。只输出一个 JSON 对象；"
                "不要输出解释、思考过程、Markdown 代码块或面向学生的话；"
                "所有字符串必须是合法 JSON 字符串，字符串内部不要使用未转义的英文双引号。"
            ),
        },
        *messages,
    ]

    def _parse_result(result):
        if not result.get("ok"):
            return {
                "ok": False,
                "error": result.get("error", "LLM call failed"),
                "content": result.get("content", ""),
                "data": {},
            }

        content = result.get("content", "")
        try:
            data = extract_json_object(content)
        except ValueError as exc:
            return {
                "ok": False,
                "error": str(exc),
                "content": content,
                "data": {},
            }

        missing = [
            field
            for field in (required_fields or [])
            if field not in data
        ]
        if missing:
            return {
                "ok": False,
                "error": f"LLM JSON response missing required fields: {', '.join(missing)}",
                "content": content,
                "data": data,
            }

        return {
            "ok": True,
            "content": content,
            "data": data,
        }

    result = chat(strict_messages, temperature=temperature, max_tokens=max_tokens, json_mode=True)
    parsed = _parse_result(result)
    if parsed.get("ok") or not _should_retry_json_error(parsed.get("error", "")):
        return parsed

    logger.warning("LLM JSON parse failed, retrying once: %s", parsed.get("error"))
    retry_messages = [
        *strict_messages,
        {
            "role": "user",
            "content": (
                "上一次输出不是完整 JSON。请只重新输出一个完整 JSON 对象。\n"
                "不要输出 Markdown。\n"
                "不要输出解释。\n"
                "不要输出代码块。\n"
                "不要输出多余文本。\n"
                "JSON 必须能被 json.loads 直接解析。"
            ),
        },
    ]
    retry_result = chat(retry_messages, temperature=0.1, max_tokens=max_tokens, json_mode=True)
    retry_parsed = _parse_result(retry_result)
    if not retry_parsed.get("ok"):
        retry_parsed["retried"] = True
    return retry_parsed


# =========================
# 3. 调用LLM
# =========================
def chat(messages, temperature=0.5, max_tokens=1200, json_mode=False):
    if not is_enabled():
        return {"ok": False, "error": "LLM disabled", "content": ""}

    config = _get_provider_config()
    timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", "20"))

    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if json_mode and config["provider"] == "deepseek":
        payload["response_format"] = {"type": "json_object"}

    _debug(
        "LLM request provider=%s model=%s url=%s messages=%s max_tokens=%s",
        config["provider"],
        config["model"],
        config["api_url"],
        len(messages),
        max_tokens,
    )

    req = urllib.request.Request(
        config["api_url"],
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        logger.warning("LLM HTTP error: %s; body=%s", e, err_body[:500])
        return {"ok": False, "error": str(e), "content": ""}
    except urllib.error.URLError as e:
        logger.warning("LLM URL error: %s", e)
        return {"ok": False, "error": str(e), "content": ""}
    except TimeoutError as e:
        logger.warning("LLM request timeout: %s", e)
        return {"ok": False, "error": "LLM request timeout", "content": ""}

    return _parse_llm_response(data, config["provider"])
