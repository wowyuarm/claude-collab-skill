---
name: claude-collab
description: "Delegate coding tasks to Claude Code CLI for programmatic collaboration. Use when: (1) users ask to \"use Claude Code\", \"delegate to Claude\", or \"collaborate with Claude\", (2) deep codebase exploration or multi-file refactoring is needed, (3) architecture review or code analysis across a large project, (4) iterative multi-step coding tasks that benefit from Claude Code's agentic capabilities, (5) scaffolding or code generation following existing project patterns. Requires the `claude` CLI binary on PATH."
---


# Claude Collab

## Mental Model

**You are the manager. Claude Code is your implementer.**

You delegate tasks by writing clear, self-contained briefs. Claude Code executes them autonomously — it can read files, search code, edit files, and run shell commands. Each invocation starts with **zero context** about your conversation or prior work, so your prompt is the *only* input it receives.

Results come back through one of two channels:
- **Direct (stdout)** — for quick tasks where you read the output immediately
- **Task file (JSON)** — for longer tasks or when output may exceed pipe limits

## Three Usage Patterns

**Note:** These are usage patterns, not command-line `--mode` options. Agents should choose the pattern that matches their needs and use the corresponding command-line arguments shown below.

### 1. Instant Pattern (Synchronous)

Run a task and get the result directly on stdout. Best for quick queries and short outputs.

```bash
python3 scripts/claude_exec.py --permission-mode plan "Analyze the architecture of src/"
# → stdout contains the full response
```

### 2. Task Pattern (File-Based)

Run a task and write the result to a JSON file. Best for longer tasks or when output may be large. The script writes a `"running"` status immediately, then updates the file when done.

```bash
python3 scripts/claude_exec.py \
  --output /tmp/analysis.json \
  --permission-mode plan \
  "Analyze the architecture of src/"
# → stdout prints only the file path
# → read /tmp/analysis.json for the result
# Note: /tmp/ is just an example; replace with any writable path
```

**Task file lifecycle:**

```
┌─ immediately ──────────────────────────┐
│ {"status": "running", "pid": 12345,    │
│  "started_at": "2025-01-15T10:30:00Z"} │
└────────────────────────────────────────┘
          ↓ (Claude Code runs)
┌─ on completion ────────────────────────┐
│ {"status": "completed",               │
│  "output": "...",                      │
│  "exit_code": 0,                      │
│  "completed_at": "2025-01-15T10:31:00Z"}│
└────────────────────────────────────────┘
```

**Task file statuses:**

| Status | Meaning |
|---|---|
| `running` | Claude Code is still working |
| `completed` | Finished successfully (`exit_code: 0`) |
| `error` | Finished with non-zero exit code |
| `timeout` | Exceeded `--timeout` |

### 3. Session Pattern (Multi-Step)

Use sessions when a task requires multiple steps and Claude Code should retain context between them. Combine with `--output` for file-based results.

```bash
SESSION_ID=$(python3 -c "import uuid; print(uuid.uuid4())")

# Step 1: Analyze (read-only)
python3 scripts/claude_exec.py \
  --output /tmp/step1.json \
  --session $SESSION_ID \
  --permission-mode plan \
  "Read the auth module and identify security issues"

# Step 2: Fix (Claude Code remembers step 1)
python3 scripts/claude_exec.py \
  --output /tmp/step2.json \
  --resume $SESSION_ID \
  --allowed-tools "Read,Edit(src/auth/**),Bash(npm test)" \
  "Fix the token expiry issue you identified. Run tests to confirm."
```
**Important notes for agents:**
- **Working directory:** Claude Code uses the **current working directory** where the script is invoked. Agents should `cd` to the target project before calling this script.
- **Session storage:** Session state is automatically managed by Claude Code in `~/.claude/projects/` (or `~/.claude/sessions/` depending on version).
- **Timeout:** Complex tasks may require longer timeouts; consider increasing `--timeout` beyond the default 300 seconds if needed.
- **Paths:** `/tmp/` in examples is just a placeholder; use any writable path for `--output`.

**Session ID rules:**
- `--session UUID` **creates** a new session (UUID required, e.g. from `uuidgen`)
- `--resume UUID` **continues** an existing session
- `--continue-session` resumes the most recent session in cwd (no UUID needed)
- Do not pass the same UUID to `--session` twice — use `--resume` after the first call


## Writing Effective Prompts

Claude Code starts each invocation with **zero context** — no conversation history, no prior knowledge. Your prompt is its only input.

**Include:**
- Concrete anchors: file paths, function names, error messages, line numbers
- Explicit goal: "analyze and report" vs. "edit the code" vs. "edit and run tests"
- Context only you have: user intent, constraints, domain requirements

**Bad** (vague, assumes shared context):
- "Fix everything"
- "Apply the changes we discussed"

**Good** (self-contained, specific, verifiable):
- "Read src/auth/token.py and identify why refresh tokens expire prematurely. Check the TTL calculation in the `refresh()` method."
- "Add input validation to `POST /users` in src/api/users.ts. Validate email format and non-empty name."


## Permission Model

Claude Code runs non-interactively — **it cannot prompt for permission at runtime**. Grant all needed permissions upfront.

| Mode | Can Read | Can Edit | Can Run Commands | Use When |
|---|---|---|---|---|
| `plan` | Yes | No | No | Analysis, review, Q&A |
| `acceptEdits` | Yes | Yes | No | Safe file editing |
| `--allowed-tools` | Yes | Controlled | Controlled | Precise control |
| `--dangerously-skip-permissions` | Yes | Yes | Yes | Sandboxed envs only |

`--permission-mode` sets the baseline. `--allowed-tools` adds specific tools on top. Example:

```bash
# plan baseline + allow only running tests
python3 scripts/claude_exec.py \
  --permission-mode plan \
  --allowed-tools "Bash(npm test)" \
  "Run the test suite and report failures"
```

### Tool Names for `--allowed-tools`

| Tool | What it does | Scoping syntax |
|---|---|---|
| `Read` | Read file contents | — |
| `Edit` | Apply targeted edits | `Edit(src/**)` |
| `Write` | Create or overwrite files | `Write(src/**)` |
| `Glob` | Find files by pattern | — |
| `Grep` | Search file contents (regex) | — |
| `Bash` | Run shell commands | `Bash(npm test)` |
| `WebFetch` | Fetch URL content | — |
| `WebSearch` | Web search | — |

`WebFetch` and `WebSearch` always require explicit allowlisting regardless of permission mode.


## CLI Reference

```
python3 scripts/claude_exec.py [OPTIONS] "prompt"
```

| Option | Description |
|---|---|
| `--output FILE` | Write results to JSON task file instead of stdout |
| `--session UUID` | Create a new session with this UUID |
| `--resume ID` | Resume an existing session |
| `--continue-session` | Continue the most recent session in cwd |
| `--permission-mode MODE` | `plan`, `acceptEdits`, `dontAsk`, `default`, `bypassPermissions` |
| `--dangerously-skip-permissions` | Skip all permission checks (isolated envs only) |
| `--allowed-tools RULES` | Comma-separated tool allow rules |
| `--disallowed-tools RULES` | Comma-separated tool deny rules |
| `--model NAME` | `sonnet`, `opus`, `haiku`, or full model ID |
| `--max-turns N` | Limit agentic turns |
| `--max-budget N` | Limit spend in USD |
| `--output-format FMT` | `text` (default), `json`, `stream-json` |
| `--append-system-prompt TEXT` | Append instructions to Claude's system prompt |
| `--add-dir PATHS` | Comma-separated additional directories |
| `--mcp-config PATH` | MCP server configuration JSON file |
| `--timeout SECS` | Subprocess timeout (default: 300) |

Exit codes: `0` success, `124` timeout, `127` claude CLI not found.


## Troubleshooting

### "error: the following arguments are required: prompt"

`--allowed-tools` or `--disallowed-tools` consumed the prompt. Pass tools as a **single comma-separated string**:

```bash
# WRONG — prompt gets consumed as a tool name
--allowed-tools "Read" "Edit(src/**)" "Fix the bug"

# CORRECT — single string, comma-separated
--allowed-tools "Read,Edit(src/**)" "Fix the bug"
```

### "Invalid session ID. Must be a valid UUID"

Generate a UUID with `uuidgen` or `python3 -c "import uuid; print(uuid.uuid4())"`.

### "Session ID is already in use"

Use `--resume` instead of `--session` to continue an existing session.

### Tools are blocked despite permission mode

Specific tools like `WebFetch` and `WebSearch` require explicit `--allowed-tools`:

```bash
python3 scripts/claude_exec.py \
  --permission-mode acceptEdits \
  --allowed-tools "WebFetch,WebSearch" \
  "Fetch the API docs from https://example.com/docs"
```

### Calling agent's exec tool blocks the command

Some agents' execution tools block commands containing tool names like `Bash` in arguments. Workarounds:
1. Store the command in a shell script and execute the script instead
2. Use `--dangerously-skip-permissions` in sandboxed environments
3. Check your calling agent's execution tool documentation for allowlisting options


## Notes

- **Working directory:** Claude Code runs in the current working directory where the script is invoked. Agents should `cd` to the target project before calling. Use `--add-dir` for cross-project access.
- **Session storage:** Session state is managed by Claude Code in `~/.claude/projects/` (or `~/.claude/sessions/` in older versions).
- **Timeout coordination:** The calling tool's execution timeout must be >= the script's `--timeout` value.
- **Safety limits:** `--max-turns` and `--max-budget` are safety guardrails for automated pipelines.
- **Atomic writes:** Task files are written atomically (tmp + rename) — safe to poll for status changes.
