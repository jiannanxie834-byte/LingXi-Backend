import json
import os
from pathlib import Path
import urllib.error
import urllib.request


# =========================
# 1. 加载 .env
# =========================
def _load_env_file():
    project_root = Path(__file__).resolve().parents[2]
    candidates = [
        Path.cwd() / ".env",
        project_root / ".env",
    ]

    env_path = next((path for path in candidates if path.exists()), None)

    if not env_path:
        print("[ENV] .env not found")
        return

    print("[ENV] loading:", env_path)

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        k, v = line.split("=", 1)

        os.environ[k.strip()] = v.strip().strip('"').strip("'")

    print("[ENV CHECK]")
    print("LINGXI_LLM_PROVIDER =", os.getenv("LINGXI_LLM_PROVIDER"))
    print("SPARK_API_PASSWORD =", "SET" if os.getenv("SPARK_API_PASSWORD") else "EMPTY")
    print("DEEPSEEK_API_KEY =", "SET" if os.getenv("DEEPSEEK_API_KEY") else "EMPTY")

_load_env_file()

DEFAULT_SPARK_API_URL = "https://spark-api-open.xf-yun.com/v1/chat/completions"
DEFAULT_DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


def _get_provider():
    return os.getenv("LINGXI_LLM_PROVIDER", "local").strip().lower()


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

    print("[LLM ENABLE CHECK]", enabled)

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
    print("[LLM RESPONSE]", {
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


# =========================
# 3. 调用LLM
# =========================
def chat(messages, temperature=0.5, max_tokens=1200):
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

    print("[LLM REQUEST]", payload)
    print("[LLM PROVIDER]", config["provider"])
    print("[LLM URL]", config["api_url"])
    print("[LLM MODEL]", config["model"])

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
        print("[LLM HTTP ERROR BODY]", err_body)
        return {"ok": False, "error": str(e), "content": ""}
    except urllib.error.URLError as e:
        print("[LLM URL ERROR]", e)
        return {"ok": False, "error": str(e), "content": ""}
    except TimeoutError as e:
        print("[LLM TIMEOUT]", e)
        return {"ok": False, "error": "LLM request timeout", "content": ""}

    return _parse_llm_response(data, config["provider"])
