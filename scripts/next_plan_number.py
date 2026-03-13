#!/usr/bin/env python3
"""
Return the next available 3-digit plan number for a service repo.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


PLAN_FILE_RE = re.compile(r"^(\d{3})-.*\.md$")


def print_usage() -> None:
    print("Usage: uv run scripts/next_plan_number.py <service-path>")


def next_number(service_path: Path) -> str:
    plans_dir = service_path / ".agentbus-plans"
    if not plans_dir.exists() or not plans_dir.is_dir():
        return "001"

    max_seen = 0
    for candidate in plans_dir.glob("*.md"):
        match = PLAN_FILE_RE.match(candidate.name)
        if not match:
            continue
        max_seen = max(max_seen, int(match.group(1)))
    return f"{max_seen + 1:03d}"


def main() -> None:
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)

    service_path = Path(sys.argv[1]).expanduser()
    if not service_path.is_absolute():
        print("Error: service path must be absolute", file=sys.stderr)
        sys.exit(1)
    if not service_path.exists() or not service_path.is_dir():
        print(f"Error: invalid service path '{service_path}'", file=sys.stderr)
        sys.exit(1)

    print(next_number(service_path))


if __name__ == "__main__":
    main()
