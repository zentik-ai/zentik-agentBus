#!/usr/bin/env python3
"""
Register or update a service in ~/.agentbus/services.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REGISTRY_DIR = Path.home() / ".agentbus"
REGISTRY_PATH = REGISTRY_DIR / "services.json"


def print_usage() -> None:
    print("Usage: uv run scripts/register_service.py <name> <absolute-path>")


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

    normalized: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, str):
            normalized[key] = value
    return normalized


def main() -> None:
    if len(sys.argv) != 3:
        print_usage()
        sys.exit(1)

    name = sys.argv[1].strip()
    path_arg = sys.argv[2].strip()

    if not name:
        print("Error: service name cannot be empty", file=sys.stderr)
        sys.exit(1)

    service_path = Path(path_arg).expanduser()
    if not service_path.is_absolute():
        print("Error: path must be absolute", file=sys.stderr)
        sys.exit(1)
    if not service_path.exists():
        print(f"Error: path '{service_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    if not service_path.is_dir():
        print(f"Error: path '{service_path}' is not a directory", file=sys.stderr)
        sys.exit(1)

    registry = load_registry()
    registry[name] = str(service_path)

    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    print(f"Registered '{name}' -> {service_path}")


if __name__ == "__main__":
    main()
