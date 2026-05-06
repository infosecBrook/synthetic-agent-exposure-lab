from __future__ import annotations

from datetime import datetime

from tools.policy import EXFIL_LOG, check_exfiltration, ensure_log_files


def simulate_exfiltration(content: str, destination: str, secure: bool = False) -> str:
    """
    Simulate data exfiltration without network traffic.

    This writes the attempted destination and content to a local log file only.
    """
    decision = check_exfiltration(content, secure=secure)
    if not decision.allowed:
        raise PermissionError(decision.reason)

    ensure_log_files()
    timestamp = datetime.now().isoformat(timespec="seconds")
    with EXFIL_LOG.open("a", encoding="utf-8") as log:
        log.write("\n=== SIMULATED EXFILTRATION ATTEMPT ===\n")
        log.write(f"time: {timestamp}\n")
        log.write(f"destination: {destination}\n")
        log.write("content:\n")
        log.write(content)
        log.write("\n=== END SIMULATION ===\n")
    return f"Simulated exfiltration logged locally for destination: {destination}"
