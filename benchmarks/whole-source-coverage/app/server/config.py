"""Settings for the notes server, read once from config.json beside the package."""
import json
import os
from dataclasses import dataclass
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
MIN_SECRET_CHARS = 32


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    token_secret: bytes
    token_ttl_seconds: int
    max_note_bytes: int
    allowed_origins: tuple[str, ...]


def load_settings(path: Path = CONFIG_PATH, environ=os.environ) -> Settings:
    raw = json.loads(path.read_text(encoding="utf-8"))
    secret = environ.get(raw["token_secret_env"], "")
    if len(secret) < MIN_SECRET_CHARS:
        raise RuntimeError(f"{raw['token_secret_env']} must hold at least {MIN_SECRET_CHARS} characters")
    ttl = int(raw["token_ttl_seconds"])
    if not 60 <= ttl <= 86400:
        raise RuntimeError("token_ttl_seconds must lie between one minute and one day")
    return Settings(
        data_dir=(path.parent / raw["data_dir"]).resolve(),
        token_secret=secret.encode("utf-8"),
        token_ttl_seconds=ttl,
        max_note_bytes=int(raw["max_note_bytes"]),
        allowed_origins=tuple(raw["allowed_origins"]),
    )
