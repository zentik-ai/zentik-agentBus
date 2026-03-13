#!/usr/bin/env python3
"""
Read plans from .agentbus-plans in the current repository.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PLAN_FILE_RE = re.compile(r"^(\d{3})-.*\.md$")
STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(.+?)\s*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", help="Plan number (e.g. 002)")
    parser.add_argument("--list", action="store_true", dest="list_mode")
    parser.add_argument(
        "--path",
        action="store_true",
        dest="path_only",
        help="Print only the selected plan path",
    )
    return parser.parse_args()


def get_plan_files(plans_dir: Path) -> list[Path]:
    files: list[tuple[int, Path]] = []
    for path in plans_dir.glob("*.md"):
        match = PLAN_FILE_RE.match(path.name)
        if not match:
            continue
        files.append((int(match.group(1)), path))
    files.sort(key=lambda item: item[0])
    return [item[1] for item in files]


def extract_status(plan_path: Path) -> str:
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        match = STATUS_RE.match(line.strip())
        if match:
            return match.group(1)
    return "unknown"


def select_plan(plan_files: list[Path], plan_arg: str | None) -> Path:
    if plan_arg is None:
        return plan_files[-1]

    normalized = plan_arg.strip()
    if normalized.isdigit() and len(normalized) <= 3:
        normalized = f"{int(normalized):03d}"

    for path in plan_files:
        if path.name.startswith(f"{normalized}-"):
            return path

    print(f"Error: plan '{plan_arg}' not found", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    args = parse_args()

    repo_path = Path.cwd()
    plans_dir = repo_path / ".agentbus-plans"
    if not plans_dir.exists() or not plans_dir.is_dir():
        print("No plans found in this repo.")
        return

    plan_files = get_plan_files(plans_dir)
    if not plan_files:
        print("No plans found in this repo.")
        return

    if args.list_mode:
        print("Plans in .agentbus-plans/:")
        for plan in plan_files:
            print(f"  {plan.name} ({extract_status(plan)})")
        return

    selected = select_plan(plan_files, args.plan)
    if args.path_only:
        print(selected)
        return

    print(selected.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
