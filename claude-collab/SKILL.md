---
name: claude-collab
description: Delegate coding tasks to Claude Code CLI for programmatic collaboration. Use when: (1) users ask to "use Claude Code", "delegate to Claude", or "collaborate with Claude", (2) deep codebase exploration or multi-file refactoring is needed, (3) architecture review or code analysis across a large project, (4) iterative multi-step coding tasks that benefit from Claude Code's agentic capabilities, (5) scaffolding or code generation following existing project patterns. Requires the `claude` CLI binary on PATH.
---


# Claude Collab

Invoke Claude Code CLI in non-interactive (`-p`) mode for programmatic collaboration on coding tasks.

## Tool

`claude_exec.py` — subprocess wrapper around `claude -p` with safety defaults and full CLI feature exposure.

```bash
python scripts/claude_exec.py [OPTIONS] "prompt"
```

### Quick Reference

```bash
# Read-only analysis (safest — no file writes or commands)
python scripts/claude_exec.py --permission-mode plan "Analyze the architecture of src/"

# Analysis with JSON output for structured parsing
python scripts/claude_exec.py --permission-mode plan --output-format json "List all API endpoints"

# Editing with explicit tool allowlist (recommended for modifications)
python scripts/claude_exec.py \
  --allowed-tools "Read" "Edit(src/**)" "Bash(npm test)" \
  "Fix the null pointer bug in src/auth.py"

# Multi-turn session: create
python scripts/claude_exec.py --session <uuid> "Read src/main.py and plan refactoring"

# Multi-turn session: resume
python scripts/claude_exec.py --resume <uuid> "Apply the refactoring you proposed"

# Continue the most recent session in this directory
python scripts/claude_exec.py --continue-session "What were we working on?"

# Full autonomy (ONLY in isolated/sandboxed environments)
python scripts/claude_exec.py --dangerously-skip-permissions "Refactor the auth module"

# Model and budget control
python scripts/claude_exec.py --model haiku --max-turns 5 --max-budget 1.0 "Explain this function"

# Inject context via system prompt
python scripts/claude_exec.py --append-system-prompt "Always use TypeScript strict mode" "Add input validation"

# Extended timeout for large tasks
python scripts/claude_exec.py --timeout 600 "Migrate all tests from Jest to Vitest"
```

### All Options

| Option | Description |
|---|---|
| `--session UUID` | Create a new session with this UUID |
| `--resume ID` | Resume an existing session by ID |
| `--continue-session` | Continue the most recent session in cwd |
| `--permission-mode MODE` | `plan` (read-only), `acceptEdits`, `dontAsk`, `default` |
| `--dangerously-skip-permissions` | Skip all permission checks (isolated envs only) |
| `--allowed-tools RULE...` | Tool allow rules, e.g. `"Read" "Edit(src/**)"` |
| `--disallowed-tools RULE...` | Tool deny rules |
| `--model NAME` | `sonnet`, `opus`, `haiku`, or full model ID |
| `--max-turns N` | Limit agentic turns |
| `--max-budget N` | Limit spend in USD |
| `--output-format FMT` | `text` (default), `json`, `stream-json` |
| `--append-system-prompt TEXT` | Append instructions to Claude's system prompt |
| `--add-dir PATH...` | Additional directories Claude Code can access |
| `--mcp-config PATH` | MCP server configuration JSON file |
| `--timeout SECS` | Subprocess timeout (default: 300) |


## Permission Modes — Choose the Right Level

Always use the **minimum permission level** needed for the task.

| Mode | Can Read | Can Edit | Can Run Commands | Use When |
|---|---|---|---|---|
| `plan` | Yes | No | No | Analysis, review, Q&A |
| `acceptEdits` | Yes | Yes | No | Safe file editing without shell access |
| `dontAsk` + `--allowed-tools` | Yes | Controlled | Controlled | Precise control over what's allowed |
| `default` | Yes | Prompted | Prompted | Interactive (not useful in `-p` mode) |
| `--dangerously-skip-permissions` | Yes | Yes | Yes | Sandboxed/isolated environments only |

**Recommended approach for modifications**: Use `--allowed-tools` to grant exactly the permissions needed:

```bash
# Allow reading anything, editing only in src/, running only tests
python scripts/claude_exec.py \
  --allowed-tools "Read" "Glob" "Grep" "Edit(src/**)" "Bash(npm test)" \
  "Fix the rendering bug in src/components/Header.tsx"
```


## Workflow: When and How to Collaborate

### When to delegate to Claude Code

- **Deep codebase exploration**: "Find all usages of X across the project"
- **Multi-file refactoring**: Changes spanning many files that need consistency
- **Architecture analysis**: Understanding complex dependency graphs
- **Code generation**: Scaffolding new modules following existing patterns
- **Iterative debugging**: When the problem requires reading, hypothesizing, and testing

### When NOT to delegate

- **Simple single-file edits**: Faster to do yourself with your own tools
- **Tasks requiring external context the agent can't access**: API keys, credentials, external services
- **Tasks you can't verify**: If you can't check Claude Code's output, don't delegate

### Step-by-Step Process

#### 1. Classify the task and choose permission level

| Task Type | Permission Level | Example |
|---|---|---|
| Read-only analysis | `--permission-mode plan` | "What design patterns does this codebase use?" |
| File editing | `--allowed-tools "Read" "Edit(...)"` | "Fix the bug in auth.py" |
| Edit + test | `--allowed-tools "Read" "Edit(...)" "Bash(npm test)"` | "Fix the bug and verify tests pass" |
| Full autonomy | `--dangerously-skip-permissions` | Complex multi-step refactor in sandbox |

#### 2. Write a focused, specific prompt

**Bad prompts** (vague, unbounded):
- "Fix everything"
- "Make the code better"
- "Refactor this"

**Good prompts** (specific, verifiable):
- "Read src/auth/token.py and identify why refresh tokens expire prematurely. Check the TTL calculation in the `refresh()` method."
- "Rename all instances of `UserManager` to `UserService` across the project. Update imports accordingly."
- "Add input validation to the `POST /users` endpoint in src/api/users.ts. Validate that email is a valid format and name is non-empty."

#### 3. For multi-step tasks, use sessions

```bash
# Step 1: Analyze (read-only is safe for analysis)
python scripts/claude_exec.py --session $SESSION_ID --permission-mode plan \
  "Read the authentication module and identify security issues"

# Step 2: Review the analysis, then apply fixes with appropriate permissions
python scripts/claude_exec.py --resume $SESSION_ID \
  --allowed-tools "Read" "Edit(src/auth/**)" \
  "Fix the token expiry issue you identified. Do not change the public API."

# Step 3: Verify
python scripts/claude_exec.py --resume $SESSION_ID \
  --allowed-tools "Read" "Bash(npm test)" \
  "Run the auth test suite and report results"
```

#### 4. Verify results independently

After Claude Code reports completion, **always verify with your own tools**:
- Read modified files to confirm changes are correct
- Run tests / linters / type checkers
- Check that no unintended files were modified

Do not blindly trust the response. Claude Code is capable but not infallible.

#### 5. Handle errors

| Situation | Action |
|---|---|
| Timeout | Increase `--timeout`, or break the task into smaller steps |
| Wrong output | Send a correction in the same session with `--resume` |
| Exit code != 0 | Check stderr for details; may indicate a CLI or permission error |
| Claude not found | Ensure `claude` CLI is installed and on PATH |


## Notes

- Claude Code runs in the current working directory. Ensure you invoke the script from the correct project root, or use `--add-dir` for cross-project access.
- The calling tool's own execution timeout must be >= the `--timeout` value passed to this script.
- Session state is managed by Claude Code itself in `~/.claude/sessions/`. This script does not maintain separate state.
- When using `--output-format json`, the output includes structured metadata (tool calls, token usage, etc.) useful for programmatic processing.
- `--max-turns` and `--max-budget` are safety guardrails — use them in automated pipelines to prevent runaway execution.
