from __future__ import annotations

import subprocess

from tools.policy import check_command


def run_command(command: str, secure: bool = False) -> str:
    """Run a tightly limited local command for demo purposes."""
    decision = check_command(command, secure=secure)
    if not decision.allowed:
        raise PermissionError(decision.reason)

    result = subprocess.run(
        [command.strip()],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    output = result.stdout.strip() or result.stderr.strip()
    return output or f"{command.strip()} completed with no output"
