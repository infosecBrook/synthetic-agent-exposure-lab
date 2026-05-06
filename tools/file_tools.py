from __future__ import annotations

from pathlib import Path

from tools.policy import DATA_DIR, BLOCKED_FILES, check_file_read, resolve_data_file


def list_files(secure: bool = False) -> list[str]:
    """List files available to the agent in data/."""
    names = sorted(path.name for path in DATA_DIR.iterdir() if path.is_file())
    if secure:
        return [name for name in names if name not in BLOCKED_FILES]
    return names


def read_file(filename: str, secure: bool = False) -> str:
    """Read a local demo file from data/ with optional secure policy checks."""
    clean_name = Path(filename).name
    decision = check_file_read(clean_name, secure=secure)
    if not decision.allowed:
        raise PermissionError(decision.reason)

    path = resolve_data_file(clean_name)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"{clean_name} does not exist in data/")
    return path.read_text(encoding="utf-8")
