from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"
ACTION_LOG = LOG_DIR / "agent_actions.log"
EXFIL_LOG = LOG_DIR / "simulated_exfiltration.log"

BLOCKED_FILES = {"fake_secrets.txt"}
INSECURE_COMMANDS = {"ls", "pwd", "whoami", "date"}
SECURE_COMMANDS = {"pwd", "date"}
SENSITIVE_MARKERS = (
    "api_key",
    "password",
    "token",
    "secret",
    "fake_api_key",
    "fake_db_password",
    "fake_cloud_token",
)


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str = ""


def ensure_log_files() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ACTION_LOG.touch(exist_ok=True)
    EXFIL_LOG.touch(exist_ok=True)


def log_action(action: str, details: str) -> None:
    """Append a timestamped agent/tool action to logs/agent_actions.log."""
    ensure_log_files()
    timestamp = datetime.now().isoformat(timespec="seconds")
    with ACTION_LOG.open("a", encoding="utf-8") as log:
        log.write(f"[{timestamp}] {action}: {details}\n")


def resolve_data_file(filename: str) -> Path:
    candidate = (DATA_DIR / filename).resolve()
    data_root = DATA_DIR.resolve()
    if data_root not in candidate.parents and candidate != data_root:
        raise ValueError("Path traversal outside data/ is not allowed.")
    return candidate


def is_sensitive_filename(filename: str) -> bool:
    return Path(filename).name in BLOCKED_FILES


def content_looks_sensitive(content: str) -> bool:
    lowered = content.lower()
    return any(marker in lowered for marker in SENSITIVE_MARKERS)


def check_file_read(filename: str, secure: bool) -> PolicyDecision:
    if secure and is_sensitive_filename(filename):
        return PolicyDecision(False, "secure policy blocks access to fake_secrets.txt")
    return PolicyDecision(True)


def check_command(command: str, secure: bool) -> PolicyDecision:
    command_name = command.strip().split()[0] if command.strip() else ""
    allowed = SECURE_COMMANDS if secure else INSECURE_COMMANDS
    if command.strip() != command_name:
        return PolicyDecision(False, "arguments, shell operators, and command chaining are not allowed")
    if command_name not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        return PolicyDecision(False, f"command blocked; allowed commands are: {allowed_text}")
    return PolicyDecision(True)


def check_exfiltration(content: str, secure: bool) -> PolicyDecision:
    if secure and content_looks_sensitive(content):
        return PolicyDecision(False, "secure policy blocks moving sensitive-looking data to another destination")
    return PolicyDecision(True)
