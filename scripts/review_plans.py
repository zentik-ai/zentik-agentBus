#!/usr/bin/env python3
"""
Review cross-service plan consistency for a feature slug.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path.home() / ".agentbus" / "services.json"
PLAN_FILE_RE = re.compile(r"^(\d{3})-(.+)\.md$")
BULLET_DECISION_RE = re.compile(r"^\s*-\s*([a-zA-Z0-9._-]+)\s*:\s*(.+?)\s*$")
OPEN_QUESTION_RE = re.compile(r"^\s*-\s*\[\s*\]\s*(.+?)\s*$")
HEADING_RE = re.compile(r"^##\s+(.+)$")

POSITIVE_WORDS = {"enable", "allow", "use", "adopt", "migrate", "send", "publish"}
NEGATIVE_WORDS = {"disable", "block", "avoid", "deprecate", "remove", "stop", "not"}


@dataclass
class PlanData:
    service: str
    path: Path
    decisions: dict[str, str]
    open_questions: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-slug", required=True, help="Feature slug to review")
    parser.add_argument(
        "--services",
        nargs="+",
        help="Optional explicit services to review. If omitted, use all registered services.",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def load_registry() -> dict[str, str]:
    if not REGISTRY_PATH.exists():
        print("Error: services registry not found. Register services first.", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in registry file: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print("Error: services registry must be a JSON object", file=sys.stderr)
        sys.exit(1)

    out: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, str):
            out[key] = value
    return out


def build_alias_map(services: list[str]) -> dict[str, str]:
    alias_map: dict[str, str] = {}
    for service in services:
        alias_map[service] = service
        if service.endswith("-service"):
            alias_map[service[: -len("-service")]] = service
    return alias_map


def find_plan_for_slug(service_path: Path, slug: str) -> Path | None:
    plans_dir = service_path / ".agentbus-plans"
    if not plans_dir.exists() or not plans_dir.is_dir():
        return None

    candidates: list[tuple[int, Path]] = []
    for plan in plans_dir.glob("*.md"):
        match = PLAN_FILE_RE.match(plan.name)
        if not match:
            continue
        number, file_slug = int(match.group(1)), match.group(2)
        if file_slug == slug:
            candidates.append((number, plan))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[-1][1]


def section_bounds(lines: list[str], section_name: str) -> tuple[int, int] | None:
    start = -1
    end = len(lines)
    for idx, line in enumerate(lines):
        heading_match = HEADING_RE.match(line.strip())
        if not heading_match:
            continue
        heading = heading_match.group(1).strip().lower()
        if start == -1 and heading == section_name.lower():
            start = idx + 1
            continue
        if start != -1 and idx > start:
            end = idx
            break

    if start == -1:
        return None
    return (start, end)


def parse_plan(service: str, plan_path: Path, alias_map: dict[str, str]) -> PlanData:
    content = plan_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    decisions: dict[str, str] = {}
    decisions_bounds = section_bounds(lines, "Decisions from other services")
    if decisions_bounds:
        start, end = decisions_bounds
        for line in lines[start:end]:
            match = BULLET_DECISION_RE.match(line)
            if not match:
                continue
            raw_service = match.group(1).strip()
            normalized_service = alias_map.get(raw_service, raw_service)
            decisions[normalized_service] = match.group(2).strip()

    open_questions: list[str] = []
    open_bounds = section_bounds(lines, "Open questions")
    if open_bounds:
        start, end = open_bounds
        for line in lines[start:end]:
            match = OPEN_QUESTION_RE.match(line)
            if match:
                open_questions.append(match.group(1).strip())

    return PlanData(
        service=service,
        path=plan_path,
        decisions=decisions,
        open_questions=open_questions,
    )


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text.lower())).strip()


def detect_question_conflicts(questions_by_service: dict[str, list[str]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    entries: list[tuple[str, str, set[str]]] = []
    for service, questions in questions_by_service.items():
        for question in questions:
            norm = normalize_text(question)
            tokens = set(norm.split())
            entries.append((service, question, tokens))

    for i in range(len(entries)):
        svc_a, q_a, tok_a = entries[i]
        for j in range(i + 1, len(entries)):
            svc_b, q_b, tok_b = entries[j]
            overlap = tok_a.intersection(tok_b)
            if len(overlap) < 4:
                continue
            a_pos = bool(tok_a.intersection(POSITIVE_WORDS))
            a_neg = bool(tok_a.intersection(NEGATIVE_WORDS))
            b_pos = bool(tok_b.intersection(POSITIVE_WORDS))
            b_neg = bool(tok_b.intersection(NEGATIVE_WORDS))
            if (a_pos and b_neg) or (a_neg and b_pos):
                findings.append(
                    {
                        "service_a": svc_a,
                        "question_a": q_a,
                        "service_b": svc_b,
                        "question_b": q_b,
                        "reason": "potential-opposite-intent",
                    }
                )
    return findings


def main() -> None:
    args = parse_args()
    slug = args.feature_slug.strip()
    if not slug:
        print("Error: --feature-slug cannot be empty", file=sys.stderr)
        sys.exit(1)

    registry = load_registry()
    all_services = sorted(registry.keys())
    alias_map = build_alias_map(all_services)

    if args.services:
        requested: list[str] = []
        unknown: list[str] = []
        for raw in args.services:
            normalized = alias_map.get(raw, raw)
            if normalized not in registry:
                unknown.append(raw)
                continue
            requested.append(normalized)
        requested = sorted(set(requested))
        if unknown:
            print(f"Error: unknown services: {', '.join(unknown)}", file=sys.stderr)
            sys.exit(1)
    else:
        requested = all_services

    plans: dict[str, PlanData] = {}
    missing_services: list[str] = []
    for service in requested:
        plan_path = find_plan_for_slug(Path(registry[service]), slug)
        if plan_path is None:
            missing_services.append(service)
            continue
        plans[service] = parse_plan(service, plan_path, alias_map)

    warnings: list[str] = []
    issues: list[str] = []

    if plans and missing_services:
        warnings.append(
            "Missing plan files for requested services: " + ", ".join(sorted(missing_services))
        )

    inconsistent_pairs: set[tuple[str, str]] = set()
    for service, plan in plans.items():
        for ref_service, ref_decision in plan.decisions.items():
            if ref_service not in requested:
                warnings.append(
                    f"{service}: references non-target service '{ref_service}' in decisions"
                )
                continue
            if ref_service not in plans:
                issues.append(
                    f"{service}: references '{ref_service}' in decisions, but no plan exists for feature '{slug}'"
                )
                continue
            back_decision = plans[ref_service].decisions.get(service)
            if back_decision is None:
                warnings.append(
                    f"{service}<->{ref_service}: unilateral decision reference (no reverse decision found)"
                )
            elif normalize_text(back_decision) != normalize_text(ref_decision):
                pair = tuple(sorted((service, ref_service)))
                if pair not in inconsistent_pairs:
                    inconsistent_pairs.add(pair)
                    issues.append(
                        f"{pair[0]}<->{pair[1]}: inconsistent cross-service decision text"
                    )

    questions_by_service = {svc: plan.open_questions for svc, plan in plans.items()}
    question_conflicts = detect_question_conflicts(questions_by_service)
    for conflict in question_conflicts:
        warnings.append(
            f"Potential question conflict: {conflict['service_a']} vs {conflict['service_b']}"
        )

    result: dict[str, Any] = {
        "feature_slug": slug,
        "requested_services": requested,
        "plans_found": sorted(plans.keys()),
        "missing_services": sorted(missing_services),
        "plan_paths": {svc: str(plan.path) for svc, plan in plans.items()},
        "issues": issues,
        "warnings": warnings,
        "question_conflicts": question_conflicts,
        "summary": {
            "status": "ok" if not issues else "needs-attention",
            "issues_count": len(issues),
            "warnings_count": len(warnings),
        },
    }

    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return

    print(f"Feature slug: {slug}")
    print(f"Requested services: {', '.join(requested) if requested else '(none)'}")
    print(f"Plans found: {', '.join(sorted(plans.keys())) if plans else '(none)'}")
    if missing_services:
        print(f"Missing plans: {', '.join(sorted(missing_services))}")

    print("\nPlan files:")
    if plans:
        for service in sorted(plans.keys()):
            print(f"  - {service}: {plans[service].path}")
    else:
        print("  (none)")

    print("\nIssues:")
    if issues:
        for item in issues:
            print(f"  - {item}")
    else:
        print("  - none")

    print("\nWarnings:")
    if warnings:
        for item in warnings:
            print(f"  - {item}")
    else:
        print("  - none")

    print(f"\nStatus: {result['summary']['status']}")


if __name__ == "__main__":
    main()
