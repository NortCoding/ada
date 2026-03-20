"""
ADA CLI entrypoint.

Requirements:
- Accept a command from terminal
- Example usage:
  python -m ada.cli.main "analyze project"
- Print the input received
- Keep it simple (no AI yet)
"""

from __future__ import annotations

import sys

from ada.cli.command_router import route_command


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    command = " ".join(argv).strip() if argv else ""

    try:
        print(f"Command received: {command}")
    except BrokenPipeError:
        # Allows `python ... | head` to terminate cleanly.
        return 0

    if command:
        try:
            route_command(command)
        except BrokenPipeError:
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

