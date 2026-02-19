# dev-workflow

A development collaboration protocol for AI assistants. Provides a dual-path workflow for coding tasks: **spawn subagents** for lightweight changes, or delegate to **[Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI** for complex refactors.

**The workflow:** Your assistant understands the project (OpenContext), researches the codebase (subagents), formulates a plan, executes via the appropriate path, reviews, and creates a PR.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and on PATH (only needed for Path B)

## Quick Start

**Recommended to use with [OpenContext](https://github.com/wowyuarm/opencontext)** — get project context before executing.

### Path A: Spawn Subagent (lightweight)

For small–medium changes (<200 lines, 1–3 files). Your assistant spawns a subagent with a detailed task prompt directly — no external CLI needed.

### Path B: Claude Code CLI (heavyweight)

For large refactors, multi-step sessions, or when CLAUDE.md project rules should apply.

The skill provides `dev-workflow/scripts/claude_exec.py`, a subprocess wrapper around `claude -p`.

**Important:** Claude Code runs in the current working directory. Always `cd` to the target project first.

```bash
# Execute a plan with full permissions
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
```

See `SKILL.md` for the complete workflow protocol, execution plan template, review protocol, git branch workflow, and error recovery guidance.

## Notes

- When using a third-party model, configure via environment variables (`ANTHROPIC_BASE_URL`, `ANTHROPIC_API_KEY`). The `--model` parameter will be ignored.

## License

MIT
