#!/usr/bin/env python3
"""
List registered services from ~/.agentbus/services.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REGISTRY_PATH = Path.home() / ".agentbus" / "services.json"


def load_registry() -> dict[str, str]:
    if not REGISTRY_PATH.exists():
        return {}

    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in registry file: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print("Error: registry file must contain a JSON object", file=sys.stderr)
        sys.exit(1)

    out: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, str):
            out[key] = value
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    services = load_registry()
    if not services:
        print("No services registered yet. Use register_service.py to add one.")
        return

    if args.as_json:
        print(json.dumps(dict(sorted(services.items())), indent=2, ensure_ascii=True))
        return

    print("Registered services:")
    for name, path in sorted(services.items()):
        print(f"  {name} -> {path}")


if __name__ == "__main__":
    main()
