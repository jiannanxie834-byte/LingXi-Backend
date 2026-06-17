import os
from pathlib import Path


def load_env_file(verbose: bool = False):
    """Load project .env values without requiring python-dotenv."""
    project_root = Path(__file__).resolve().parents[1]
    candidates = [
        Path.cwd() / ".env",
        project_root / ".env",
    ]

    env_path = next((path for path in candidates if path.exists()), None)

    if not env_path:
        if verbose:
            print("[ENV] .env not found")
        return None

    if verbose:
        print("[ENV] loading:", env_path)

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")

    return env_path
