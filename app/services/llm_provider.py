import json
import os
from pathlib import Path
import urllib.error
import urllib.request


def _load_env_file():
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_env_file()


DEFAULT_SPARK_API_URL = "https://spark-api-open.xf-yun.com/v1/chat/completions"


def is_enabled():
    """只有明确配置为 spark 且填入 APIPassword 时才调用外部大模型。"""
    provider = os.getenv("LINGXI_LLM_PROVIDER", "local").lower()
    return provider == "spark" and bool(os.getenv("SPARK_API_PASSWORD"))


def chat(messages, temperature=0.5, max_tokens=1200):
    """调用讯飞星火 HTTP 接口。失败时返回错误，不影响本地 Agent 主流程。"""
    if not is_enabled():
        return {"ok": False, "error": "LLM provider is not configured"}

    api_password = os.getenv("SPARK_API_PASSWORD", "")
    api_url = os.getenv("SPARK_API_URL", DEFAULT_SPARK_API_URL)
    model = os.getenv("SPARK_MODEL", "lite")
    timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    request = urllib.request.Request(
        api_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_password}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc)}

    if data.get("code") not in (None, 0):
        return {"ok": False, "error": data.get("message", "LLM request failed"), "raw": data}

    choices = data.get("choices") or []
    if not choices:
        return {"ok": False, "error": "LLM response has no choices", "raw": data}

    content = choices[0].get("message", {}).get("content", "")
    return {
        "ok": True,
        "content": content,
        "usage": data.get("usage", {}),
        "sid": data.get("sid", ""),
    }
