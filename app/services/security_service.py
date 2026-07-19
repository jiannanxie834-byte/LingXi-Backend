import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Dict, Tuple

from app.config import load_env_file


load_env_file()

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 240_000
_PROCESS_TOKEN_SECRET = secrets.token_bytes(32)


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode((value + "=" * (-len(value) % 4)).encode("ascii"))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        str(password or "").encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def is_password_hash(value: str) -> bool:
    return str(value or "").startswith(f"{PASSWORD_SCHEME}$")


def verify_password(password: str, stored_value: str) -> Tuple[bool, str]:
    stored = str(stored_value or "")
    if not is_password_hash(stored):
        valid = hmac.compare_digest(stored, str(password or ""))
        return valid, hash_password(password) if valid else ""

    try:
        _, iteration_text, salt_text, digest_text = stored.split("$", 3)
        iterations = int(iteration_text)
        salt = _b64decode(salt_text)
        expected = _b64decode(digest_text)
    except (TypeError, ValueError):
        return False, ""

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        str(password or "").encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual, expected), ""


def _token_secret() -> bytes:
    configured = os.getenv("LINGXI_TOKEN_SECRET", "").strip()
    return configured.encode("utf-8") if configured else _PROCESS_TOKEN_SECRET


def create_access_token(username: str, role: str) -> str:
    now = int(time.time())
    lifetime = max(300, int(os.getenv("LINGXI_TOKEN_EXPIRE_SECONDS", "28800")))
    header = _b64encode(json.dumps({"alg": "HS256", "typ": "LXI"}, separators=(",", ":")).encode("utf-8"))
    payload = _b64encode(json.dumps({
        "sub": str(username or ""),
        "role": str(role or "student"),
        "iat": now,
        "exp": now + lifetime,
    }, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = _b64encode(hmac.new(_token_secret(), signing_input, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


def verify_access_token(token: str) -> Dict:
    try:
        header, payload, signature = str(token or "").split(".", 2)
        signing_input = f"{header}.{payload}".encode("ascii")
        expected = _b64encode(hmac.new(_token_secret(), signing_input, hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return {}
        data = json.loads(_b64decode(payload).decode("utf-8"))
        if not data.get("sub") or int(data.get("exp") or 0) <= int(time.time()):
            return {}
        return data
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
