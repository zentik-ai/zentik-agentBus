#!/usr/bin/env python3
"""
Write a numbered plan file into <service-repo>/.agentbus-plans/.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


PLAN_FILE_RE = re.compile(r"^(\d{3})-.*\.md$")
NON_SLUG_RE = re.compile(r"[^a-z0-9]+")


def print_usage() -> None:
    print(
        "Usage: uv run scripts/write_plan.py "
        "<service-path> <feature-slug> <plan-content-file>"
    )


def normalize_slug(raw: str) -> str:
    normalized = NON_SLUG_RE.sub("-", raw.strip().lower()).strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized


def next_number(plans_dir: Path) -> str:
    max_seen = 0
    for candidate in plans_dir.glob("*.md"):
        match = PLAN_FILE_RE.match(candidate.name)
        if not match:
            continue
        max_seen = max(max_seen, int(match.group(1)))
    return f"{max_seen + 1:03d}"


def main() -> None:
    if len(sys.argv) != 4:
        print_usage()
        sys.exit(1)

    service_path = Path(sys.argv[1]).expanduser()
    raw_slug = sys.argv[2]
    content_path = Path(sys.argv[3]).expanduser()

    if not service_path.is_absolute():
        print("Error: service path must be absolute", file=sys.stderr)
        sys.exit(1)
    if not service_path.exists() or not service_path.is_dir():
        print(f"Error: invalid service path '{service_path}'", file=sys.stderr)
        sys.exit(1)
    if not content_path.exists() or not content_path.is_file():
        print(f"Error: invalid plan content file '{content_path}'", file=sys.stderr)
        sys.exit(1)

    slug = normalize_slug(raw_slug)
    if not slug:
        print("Error: invalid feature slug after normalization", file=sys.stderr)
        sys.exit(1)

    plan_content = content_path.read_text(encoding="utf-8")

    plans_dir = service_path / ".agentbus-plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    number = next_number(plans_dir)
    target_path = plans_dir / f"{number}-{slug}.md"
    target_path.write_text(plan_content, encoding="utf-8")

    print(f"Written: {target_path}")


if __name__ == "__main__":
    main()
