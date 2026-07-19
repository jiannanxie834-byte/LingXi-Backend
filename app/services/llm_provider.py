import json
import logging
import os
import time
import urllib.error
import urllib.request

from app.config import load_env_file


load_env_file()

logger = logging.getLogger(__name__)

DEFAULT_SPARK_API_URL = "https://spark-api-open.xf-yun.com/x2/chat/completions"


def _get_provider():
    return os.getenv("LINGXI_LLM_PROVIDER", "spark").strip().lower()


def _debug_enabled():
    return os.getenv("LINGXI_DEBUG_LLM", "").strip().lower() in {"1", "true", "yes", "on"}


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


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
            "model": os.getenv("SPARK_MODEL", "spark-x").strip(),
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
    enabled = config["provider"] == "spark" and bool(config["api_key"])
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


def _parse_spark_sse_response(response):
    content_parts = []
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="ignore").strip()
        if not line:
            continue
        if line.startswith("data:"):
            line = line[5:].strip()
        if line == "[DONE]":
            break
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("code") not in {None, 0}:
            return {
                "ok": False,
                "error": event.get("message") or f"Spark SSE error {event.get('code')}",
                "content": "".join(content_parts),
            }
        for choice in event.get("choices") or []:
            delta = choice.get("delta") or choice.get("message") or {}
            content = delta.get("content") or ""
            if isinstance(content, list):
                content = "".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                )
            if content:
                content_parts.append(str(content))
    content = "".join(content_parts)
    if not content:
        return {"ok": False, "error": "empty SSE content", "content": ""}
    return {"ok": True, "content": content}


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

    json_text = text[start:end]
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as exc:
        # 长 Markdown 正文中常含有真实换行符。部分兼容式接口会
        # 把它们直接放入 JSON 字符串，导致返回内容可读但不能被 json.loads
        # 解析。这里只转义字符串内的控制字符，不修改模型语义内容。
        if "Invalid control character" not in str(exc):
            raise ValueError(f"LLM response is not valid JSON: {exc}") from exc
        repaired = []
        in_string = False
        escaped = False
        for char in json_text:
            if not in_string:
                repaired.append(char)
                if char == '"':
                    in_string = True
                continue
            if escaped:
                repaired.append(char)
                escaped = False
            elif char == "\\":
                repaired.append(char)
                escaped = True
            elif char == '"':
                repaired.append(char)
                in_string = False
            elif char == "\n":
                repaired.append("\\n")
            elif char == "\r":
                repaired.append("\\r")
            elif char == "\t":
                repaired.append("\\t")
            elif ord(char) < 0x20:
                repaired.append(f"\\u{ord(char):04x}")
            else:
                repaired.append(char)
        try:
            parsed = json.loads("".join(repaired))
        except json.JSONDecodeError as repaired_exc:
            raise ValueError(f"LLM response is not valid JSON: {repaired_exc}") from repaired_exc

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
            "LLM JSON response missing required fields",
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
            or data.get(field) is None
            or (isinstance(data.get(field), str) and not data.get(field).strip())
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
    required_fields_hint = "、".join(required_fields or [])
    retry_messages = [
        *strict_messages,
        {
            "role": "user",
            "content": (
                "上一次输出不是完整 JSON。请只重新输出一个完整 JSON 对象。\n"
                + (f"必须包含这些字段：{required_fields_hint}。\n" if required_fields_hint else "")
                + "不要输出 Markdown。\n"
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

    use_spark_stream = (
        config["provider"] == "spark"
        and config["model"] == "spark-x"
        and _env_bool("SPARK_STREAM", True)
    )
    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": use_spark_stream,
    }
    if config["provider"] == "spark" and config["model"] == "spark-x":
        # X2 默认开启深度思考。资源生成属于有明确结构的教学写作，
        # 关闭思考可避免推理消耗挤占正文 token 和触发网关空闲超时。
        payload["thinking"] = {
            "type": os.getenv("SPARK_THINKING", "disabled").strip().lower() or "disabled"
        }
        # 讯飞 X2 支持在非流式请求中定期发送空行保活。
        if not use_spark_stream:
            payload["keep_alive"] = _env_bool("SPARK_KEEP_ALIVE", True)
        payload["user"] = "lingxi-resource-agent"
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

    data = None
    stream_result = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if use_spark_stream:
                    stream_result = _parse_spark_sse_response(resp)
                else:
                    data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            logger.warning("LLM HTTP error: %s; body=%s", e, err_body[:500])
            if attempt == 0 and e.code in {408, 429, 500, 502, 503, 504}:
                time.sleep(0.4)
                continue
            return {"ok": False, "error": f"HTTP {e.code}: {err_body[:240] or e.reason}", "content": ""}
        except urllib.error.URLError as e:
            logger.warning("LLM URL error: %s", e)
            if attempt == 0:
                time.sleep(0.4)
                continue
            return {"ok": False, "error": str(e), "content": ""}
        except TimeoutError as e:
            logger.warning("LLM request timeout: %s", e)
            if attempt == 0:
                time.sleep(0.4)
                continue
            return {"ok": False, "error": "LLM request timeout", "content": ""}

    if stream_result is not None:
        return stream_result
    if data is None:
        return {"ok": False, "error": "LLM request failed", "content": ""}

    return _parse_llm_response(data, config["provider"])
