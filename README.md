# claude-collab

An execution delegation skill for AI assistants. Enables your AI assistant (OpenClaw) to delegate coding tasks to [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI (the executor) programmatically.

**The workflow:** Your assistant understands the project, researches via subagents, formulates a detailed plan, then delegates execution to Claude Code. Results come back for review.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and on PATH

## Quick Start

**Recommended to use with [OpenContext](https://github.com/wowyuarm/opencontext)** — get project context, delegate to Claude Code.

The skill provides `claude-collab/scripts/claude_exec.py`, a subprocess wrapper around `claude -p`.

**Important:** Claude Code runs in the current working directory. Always `cd` to the target project first.

```bash
# Execute a plan with full permissions (recommended default)
cd /path/to/project && python3 scripts/claude_exec.py \
  --dangerously-skip-permissions \
  "## Task
Implement input validation for POST /users

## Steps
1. Add email format and non-empty name validation in src/api/users.ts
2. Add tests in tests/api/users.test.ts
3. Run npm test

## Acceptance Criteria
- [ ] Invalid email returns 400
- [ ] Empty name returns 400
- [ ] npm test passes"

# Long plans — read from file
cd /path/to/project && python3 scripts/claude_exec.py \
  --dangerously-skip-permissions \
  --plan-file /tmp/execution-plan.md

# File-based output for longer tasks
cd /path/to/project && python3 scripts/claude_exec.py \
  --dangerously-skip-permissions \
  --output /tmp/result.json \
  --plan-file /tmp/execution-plan.md

# Multi-turn session
SESSION_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
cd /path/to/project && python3 scripts/claude_exec.py \
  --dangerously-skip-permissions --session $SESSION_ID "Step 1 plan"
cd /path/to/project && python3 scripts/claude_exec.py \
  --dangerously-skip-permissions --resume $SESSION_ID "Step 2 plan"
```

See `SKILL.md` for the complete delegation protocol, execution plan template, result handling, and error recovery guidance.

## Notes

- When using a third-party model, configure via environment variables (`ANTHROPIC_BASE_URL`, `ANTHROPIC_API_KEY`). The `--model` parameter will be ignored to preserve your configuration.

## License

MIT
