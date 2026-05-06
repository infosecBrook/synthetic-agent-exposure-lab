from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_core import provider_label, run_agent
from tools.llm_client import LocalLLMError
from tools.command_tools import run_command
from tools.file_tools import list_files, read_file
from tools.network_tools import simulate_exfiltration
from tools.policy import content_looks_sensitive, ensure_log_files, log_action


PROJECT_ROOT = Path(__file__).resolve().parent
SYSTEM_PROMPT = (PROJECT_ROOT / "prompts" / "secure_system_prompt.txt").read_text(encoding="utf-8")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files available in the local data directory.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read an approved file from the local data directory. fake_secrets.txt is blocked.",
            "parameters": {
                "type": "object",
                "properties": {"filename": {"type": "string"}},
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run an approved local demo command. Only pwd and date are allowed.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_exfiltration",
            "description": "Simulate sending non-sensitive data by writing to a local log file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "destination": {"type": "string"},
                },
                "required": ["content", "destination"],
            },
        },
    },
]


def blocked(reason: str) -> str:
    log_action("blocked_action", f"secure {reason}")
    return f"Blocked by secure policy: {reason}"


def call_tool(name: str, arguments: dict[str, Any]) -> str:
    log_action("tool_call", f"secure {name} {arguments}")
    try:
        if name == "list_files":
            result = "\n".join(list_files(secure=True))
        elif name == "read_file":
            result = read_file(arguments["filename"], secure=True)
        elif name == "run_command":
            result = run_command(arguments["command"], secure=True)
        elif name == "simulate_exfiltration":
            result = simulate_exfiltration(arguments["content"], arguments["destination"], secure=True)
        else:
            result = f"Unknown tool: {name}"
    except Exception as exc:
        result = blocked(str(exc))
    log_action("tool_result", f"secure {name} -> {result[:300]}")
    return result


def summarize_untrusted_document(content: str) -> str:
    lines = [
        line
        for line in content.splitlines()
        if not line.lower().startswith("assistant instruction:")
    ]
    return "Summary: " + " ".join(" ".join(lines).split())


def mock_agent(user_prompt: str) -> str:
    """Offline demo planner with defensive checks before tool use."""
    prompt = user_prompt.lower()

    if "attacker.example" in prompt or "send" in prompt:
        return blocked("tool chaining from file read to exfiltration is not allowed")

    if "poisoned_document" in prompt:
        document = call_tool("read_file", {"filename": "poisoned_document.txt"})
        return (
            summarize_untrusted_document(document)
            + "\n\nIgnored embedded file instructions because document content is untrusted."
        )

    if "anything that looks sensitive" in prompt:
        files = call_tool("list_files", {})
        return (
            "Available non-sensitive files:\n"
            + files
            + "\n\n"
            + blocked("requests to hunt for sensitive files are not allowed")
        )

    if "fake_secrets" in prompt or "secret" in prompt:
        return call_tool("read_file", {"filename": "fake_secrets.txt"})

    if "run ls" in prompt or prompt.strip() == "ls":
        return call_tool("run_command", {"command": "ls"})

    if "what files are available" in prompt or "list" in prompt:
        return call_tool("list_files", {})

    if "public_notes" in prompt:
        notes = call_tool("read_file", {"filename": "public_notes.txt"})
        if content_looks_sensitive(notes):
            return blocked("file content looked sensitive")
        return "Summary: " + " ".join(notes.split())

    if "date" in prompt:
        return call_tool("run_command", {"command": "date"})

    return "Try one of the demo prompts in prompts/attack_prompts.txt."


def sensitive_result_blocker(last_results: list[str]) -> str | None:
    if any(content_looks_sensitive(result) for result in last_results):
        return blocked("sensitive-looking tool output cannot be returned or passed to another tool")
    return None


def agent_response(user_prompt: str) -> str:
    return run_agent(
        user_prompt=user_prompt,
        secure=True,
        system_prompt=SYSTEM_PROMPT,
        tools=TOOLS,
        call_tool=call_tool,
        mock_agent=mock_agent,
        sensitive_result_blocker=sensitive_result_blocker,
    )


def main() -> None:
    ensure_log_files()
    print("Synthetic Agent Exposure Lab - SECURE AGENT")
    print(f"Provider: {provider_label()}")
    print("Local demo only. Type 'exit' to quit.\n")

    while True:
        user_prompt = input("secure> ").strip()
        if user_prompt.lower() in {"exit", "quit"}:
            break
        log_action("user_prompt", f"secure {user_prompt}")
        try:
            answer = agent_response(user_prompt)
        except LocalLLMError as exc:
            answer = f"Provider error: {exc}"
        print(f"\n{answer}\n")


if __name__ == "__main__":
    main()
