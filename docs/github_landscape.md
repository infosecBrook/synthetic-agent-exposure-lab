# GitHub Landscape

This project should stay focused on being a small, video-friendly local LLM agent exposure lab.

## Similar Public Projects

- ShellWard: AI agent security middleware with DLP-style controls, prompt injection detection, and command protection.
  https://github.com/jnMetaCode/shellward
- AgentDojo: research benchmark for evaluating prompt injection attacks and defenses in agent environments.
  https://github.com/ethz-spylab/agentdojo
- promptfoo: prompt, agent, and RAG testing/red-teaming framework with model comparison support.
  https://github.com/promptfoo/promptfoo
- Giskard: open-source evaluation and testing library for LLM applications and agents.
  https://github.com/Giskard-AI/giskard
- Snyk Agent Scan: scanner for AI agents, MCP servers, and skills.
  https://github.com/snyk/agent-scan
- DeepTeam: framework for red-teaming LLM systems.
  https://github.com/confident-ai/deepteam
- OWASP AI Testing Guide: testing methodology for AI application risks such as prompt injection.
  https://github.com/OWASP/www-project-ai-testing-guide

## Differentiation

Most existing projects are broad frameworks, scanners, middleware, or formal eval suites. This lab is different if it remains:

- Local-first: Ollama is the default provider.
- Small enough to understand in one sitting.
- Side-by-side: insecure and secure agents use the same tool concepts.
- Visual: every risky action has a local log artifact.
- Safe: fake secrets only, no outbound network traffic, no malware behavior.
- Repeatable: mock mode gives deterministic output for a clean video take.

