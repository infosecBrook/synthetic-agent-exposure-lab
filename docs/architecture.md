# Architecture

## Request Flow

```text
User prompt
  -> Agent prompt and provider router
  -> Ollama local LLM, mock planner, or OpenAI API
  -> Tool selection
  -> Tool layer
  -> Policy checks
  -> Local data or command execution
  -> Logging
  -> Final response
```

## User Prompt

The user prompt is terminal input. In the insecure agent, the prompt can directly influence tool calls. In the secure agent, the prompt is interpreted through policy checks before sensitive actions are allowed.

## Model Providers

The project supports three execution modes through `AGENT_PROVIDER`:

- `ollama`: real local LLM mode. This is the default and uses the Ollama chat API at `OLLAMA_HOST`.
- `mock`: deterministic Python planner for repeatable recording and offline workshops.
- `openai`: optional API comparison mode when `OPENAI_API_KEY` is available.

Ollama mode keeps prompts and model inference local. Mock mode keeps the demo deterministic for recording, workshops, and offline review.

## Tool Layer

Tools are implemented in `tools/`:

- `file_tools.py` provides `list_files()` and `read_file(filename)`.
- `command_tools.py` provides `run_command(command)`.
- `network_tools.py` provides `simulate_exfiltration(content, destination)`.
- `llm_client.py` provides the Ollama JSON-planner client.
- `policy.py` provides shared policy decisions, path safety, sensitivity checks, and action logging.

The network tool does not send network traffic. It writes a clearly labeled local record to `logs/simulated_exfiltration.log`.

## Data Access

Demo data lives in `data/`:

- `public_notes.txt` is low-risk business context.
- `employee_directory.txt` contains fake employee records.
- `fake_secrets.txt` contains fake credentials.
- `poisoned_document.txt` contains normal text plus an indirect prompt injection.

The insecure agent can read any file in `data/`. The secure agent blocks `fake_secrets.txt`.

## Policy Layer

The secure agent uses allowlists and content checks:

- File policy blocks `fake_secrets.txt`.
- Command policy allows only `pwd` and `date`.
- Exfiltration policy blocks sensitive-looking content.
- Tool chaining that attempts to move sensitive data is refused.
- Instructions inside files are treated as untrusted content.

The insecure agent still has some safety constraints because this is a defensive local demo. It only runs harmless commands: `ls`, `pwd`, `whoami`, and `date`.

## Logging Layer

Every tool call, result, user prompt, and blocked action is written to `logs/agent_actions.log`.

Simulated exfiltration attempts are written to `logs/simulated_exfiltration.log` with:

- Timestamp
- Attempted destination
- Content
- Clear simulation labels

## Insecure vs Secure Architecture

The insecure architecture trusts the model's decision to call tools. It has weak instructions, broad file access, and permits a tool chain from file read to simulated exfiltration.

The secure architecture treats the model as an untrusted decision-maker. The model can request actions, but the policy layer decides whether those actions are allowed. This separation is the central lesson of the lab: model instructions are not a security boundary.

## Differentiation

Many public AI security projects are large frameworks: eval suites, middleware, MCP scanners, or production guardrail packages. This project is deliberately smaller: a local LLM, a narrow tool surface, fake business data, clear logs, and a side-by-side insecure/secure comparison designed for a short video demonstration.
