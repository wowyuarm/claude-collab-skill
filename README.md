# claude-collab

A skill that enables AI agents to programmatically delegate coding tasks to [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI.

Agents use this skill to invoke Claude Code in non-interactive (`-p`) mode for codebase exploration, multi-file refactoring, architecture analysis, and iterative development — with granular permission control, session management, and execution guardrails.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and on PATH

## Usage

The skill provides `claude-collab/scripts/claude_exec.py`, a subprocess wrapper around `claude -p` that exposes session management, permission control, model selection, and execution limits through a unified interface.

```bash
# Read-only analysis
python3 scripts/claude_exec.py --permission-mode plan "Analyze the architecture of src/"

# Edit with explicit tool allowlist
python3 scripts/claude_exec.py \
  --allowed-tools "Read" "Edit(src/**)" "Bash(npm test)" \
  "Fix the null pointer bug in src/auth.py"

# Multi-turn session
python3 scripts/claude_exec.py --session <uuid> "Plan refactoring for src/main.py"
python3 scripts/claude_exec.py --resume <uuid> "Apply the changes you proposed"

# Model and budget control
python3 scripts/claude_exec.py --model haiku --max-turns 5 --max-budget 1.0 "Explain this function"
```

See `SKILL.md` for the complete option reference and workflow guidance.

## Permission Model

The skill encourages **minimum-privilege** usage. Instead of blanket `--dangerously-skip-permissions`, use targeted permission controls:

| Approach | When to Use |
|---|---|
| `--permission-mode plan` | Read-only analysis, no file writes or commands |
| `--allowed-tools "Read" "Edit(src/**)"` | Controlled editing scoped to specific paths |
| `--dangerously-skip-permissions` | Only in fully sandboxed/isolated environments |

## Notes

- When using a third-party model, configure via environment variables (`ANTHROPIC_BASE_URL`, `ANTHROPIC_API_KEY`). In this case, the `--model` parameter will be ignored to preserve your configuration.

## License

MIT
