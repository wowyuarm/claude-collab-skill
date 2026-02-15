#!/usr/bin/env python3
"""
Execute Claude Code CLI in non-interactive (--print) mode.

Supports single-shot queries and multi-turn conversations via --session/--resume.
Provides sensible safety defaults while exposing key CLI capabilities.
"""

import argparse
import os
import subprocess
import sys


def is_third_party_configured() -> bool:
    """Check if third-party model is configured via environment variables."""
    return bool(
        os.environ.get("ANTHROPIC_BASE_URL") or os.environ.get("ANTHROPIC_API_KEY")
    )


def build_command(args: argparse.Namespace) -> list[str]:
    """Build the claude CLI command from parsed arguments."""
    cmd = ["claude", "-p"]

    # Session management: explicit create vs resume
    if args.resume:
        cmd += ["--resume", args.resume]
    elif args.session:
        cmd += ["--session-id", args.session]

    if args.continue_session:
        cmd.append("--continue")

    # Permission control (mutually exclusive group handled by argparse)
    if args.dangerously_skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    elif args.permission_mode:
        cmd += ["--permission-mode", args.permission_mode]

    if args.allowed_tools:
        cmd.append("--allowedTools")
        cmd.extend(t.strip() for t in args.allowed_tools.split(","))

    if args.disallowed_tools:
        cmd.append("--disallowedTools")
        cmd.extend(t.strip() for t in args.disallowed_tools.split(","))

    # Model selection (skip if third-party model is configured via env vars)
    if args.model and not is_third_party_configured():
        cmd += ["--model", args.model]

    # Execution limits
    if args.max_turns:
        cmd += ["--max-turns", str(args.max_turns)]
    if args.max_budget:
        cmd += ["--max-budget-usd", str(args.max_budget)]

    # Output format
    if args.output_format:
        cmd += ["--output-format", args.output_format]

    # System prompt injection
    if args.append_system_prompt:
        cmd += ["--append-system-prompt", args.append_system_prompt]

    # Additional working directories
    if args.add_dir:
        for d in args.add_dir.split(","):
            cmd += ["--add-dir", d.strip()]

    # MCP configuration
    if args.mcp_config:
        cmd += ["--mcp-config", args.mcp_config]

    # The prompt itself
    cmd.append(args.prompt)
    return cmd


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Claude Code in non-interactive print mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  # Single analysis query (read-only, safe)
  %(prog)s "Analyze the architecture of src/"

  # Start a new multi-turn session
  %(prog)s --session <uuid> "Read src/main.py and suggest improvements"

  # Resume an existing session
  %(prog)s --resume <uuid> "Apply the changes you suggested"

  # Read-only analysis with JSON output
  %(prog)s --permission-mode plan --output-format json "List all API endpoints"

  # Editing with explicit tool allowlist
  %(prog)s --allowed-tools "Read,Edit(src/**),Bash(npm test)" "Explain the auth module and fix the token bug"

  # Use a specific model with budget limit
  %(prog)s --model sonnet --max-budget 2.0 "Refactor the database layer"
""",
    )

    parser.add_argument("prompt", help="The prompt to send to Claude Code")

    # Session management
    session_group = parser.add_mutually_exclusive_group()
    session_group.add_argument(
        "--session",
        metavar="UUID",
        help="Create a new session with this UUID",
    )
    session_group.add_argument(
        "--resume",
        metavar="ID",
        help="Resume an existing session by ID or name",
    )
    session_group.add_argument(
        "--continue-session",
        action="store_true",
        help="Continue the most recent session in the working directory",
    )

    # Permission control
    perm_group = parser.add_mutually_exclusive_group()
    perm_group.add_argument(
        "--permission-mode",
        choices=["default", "plan", "acceptEdits", "dontAsk", "bypassPermissions"],
        help="Set permission mode (default: relies on Claude Code defaults)",
    )
    perm_group.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help="Skip ALL permission checks (use only in isolated environments)",
    )
    parser.add_argument(
        "--allowed-tools",
        metavar="RULES",
        help='Comma-separated tool allow rules, e.g. "Read,Edit(src/**),Bash(npm test)"',
    )
    parser.add_argument(
        "--disallowed-tools",
        metavar="RULES",
        help='Comma-separated tool deny rules, e.g. "Bash,Write"',
    )

    # Model selection
    parser.add_argument(
        "--model",
        help="Model alias (sonnet, opus, haiku) or full model ID",
    )

    # Execution limits
    parser.add_argument(
        "--max-turns",
        type=int,
        help="Max agentic turns before stopping",
    )
    parser.add_argument(
        "--max-budget",
        type=float,
        help="Max budget in USD before stopping",
    )

    # Output
    parser.add_argument(
        "--output-format",
        choices=["text", "json", "stream-json"],
        help="Output format (default: text)",
    )

    # System prompt
    parser.add_argument(
        "--append-system-prompt",
        metavar="TEXT",
        help="Append additional instructions to Claude Code's system prompt",
    )

    # Working directory / MCP
    parser.add_argument(
        "--add-dir",
        metavar="PATHS",
        help='Comma-separated additional directories, e.g. "../other-project,/shared/libs"',
    )
    parser.add_argument(
        "--mcp-config",
        metavar="PATH",
        help="Path to MCP server configuration JSON file",
    )

    # Process control
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Subprocess timeout in seconds (default: 300)",
    )

    args = parser.parse_args()
    cmd = build_command(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=args.timeout,
        )
    except subprocess.TimeoutExpired:
        print(
            f"ERROR: Claude Code did not respond within {args.timeout}s. "
            "Consider increasing --timeout for complex tasks.",
            file=sys.stderr,
        )
        sys.exit(124)  # Standard timeout exit code
    except FileNotFoundError:
        print(
            "ERROR: 'claude' command not found. "
            "Install Claude Code CLI: npm install -g @anthropic-ai/claude-code",
            file=sys.stderr,
        )
        sys.exit(127)  # Standard command-not-found exit code

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
