import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
_PLACEHOLDERS = {"your_key_here", "changeme", "xxx", ""}

DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
DEFAULT_MAX_JOBS_TO_SCORE = 15


def load_env() -> None:
    if not ENV_FILE.is_file():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(ENV_FILE, override=True)
    except ImportError:
        raw = ENV_FILE.read_text(encoding="utf-8-sig")
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ[key.strip()] = value.strip().strip('"').strip("'")


def get_groq_api_key() -> str:
    load_env()
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key.lower() in _PLACEHOLDERS:
        return ""
    return key


def get_groq_model() -> str:
    load_env()
    return os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL


def get_max_jobs_to_score() -> int:
    load_env()
    try:
        return max(1, int(os.environ.get("MAX_JOBS_TO_SCORE", DEFAULT_MAX_JOBS_TO_SCORE)))
    except ValueError:
        return DEFAULT_MAX_JOBS_TO_SCORE


def groq_key_status() -> tuple[bool, str]:
    if not ENV_FILE.is_file():
        return False, (
            f"No .env file at:\n{ENV_FILE}\n\n"
            "Create .env with:\nGROQ_API_KEY=your_key\n\n"
            "Free key: https://console.groq.com/keys"
        )
    if not get_groq_api_key():
        return False, (
            f"GROQ_API_KEY missing in .env\n\n"
            f"Edit: {ENV_FILE}\n\n"
            "Get a free key: https://console.groq.com/keys"
        )
    return True, ""
