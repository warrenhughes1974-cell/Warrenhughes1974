"""Executable workflow gate runner.

Usage:
  python tools/validators/run_workflow_gate.py --issue <ID> [--evidence path.json]
  python tools/validators/run_workflow_gate.py --smoke <ID|all> [--evidence path.json]
  python tools/validators/run_workflow_gate.py --check-in <ID> [--evidence path.json]
  python tools/validators/run_workflow_gate.py --release-proof <ID> [--evidence path.json]

Exit 1 when a required gate is failed, missing, stale, or unverifiable.
Gate decisions come from inspected evidence fields, not from an agent writing PASS.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.workflow.coverage import issue_row, load_coverage_map, mapped_smoke_ids  # noqa: E402
from tools.workflow.gates import (  # noqa: E402
    evaluate_check_in,
    evaluate_issue,
    evaluate_release_proof,
    evaluate_smoke,
)


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        errors="replace",
    )


def _load_evidence(path: Path | None) -> dict:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _run_wf1_unittests() -> tuple[bool, str]:
    if os.environ.get("WORKFLOW_GATE_SKIP_SELFTEST") == "1":
        return False, "self-test skipped to avoid recursion"
    env = os.environ.copy()
    env["WORKFLOW_GATE_SKIP_SELFTEST"] = "1"
    test_path = ROOT / "tests" / "workflow" / "test_workflow_gates.py"
    r = subprocess.run(
        [sys.executable, str(test_path), "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        errors="replace",
        env=env,
    )
    tail = ((r.stdout or "") + (r.stderr or "")).strip()[-400:]
    return r.returncode == 0, tail


def _print_receipt(payload: dict) -> None:
    print("=" * 72)
    print(f"ISSUE: {payload.get('issue_id') or 'UNVERIFIED'}")
    print(f"CURRENT STAGE: {payload.get('current_stage') or 'UNVERIFIED'}")
    print(f"OVERALL STATUS: {payload.get('overall')}")
    print(f"COMMAND: {payload.get('command')}")
    print("CHECKS:")
    for row in payload.get("checks") or []:
        print(f"  [{row['status']}] {row['id']}: {row['detail']}")
    print(f"NEXT ACTION: {payload.get('next_action') or 'See remaining FAIL/UNVERIFIED checks.'}")
    print("=" * 72)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verified development/delivery gate runner")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--issue", dest="issue_id", help="Evaluate issue completeness gates")
    g.add_argument("--smoke", dest="smoke_id", help="Issue ID or 'all'")
    g.add_argument("--check-in", dest="checkin_id", help="Verified check-in gates")
    g.add_argument("--release-proof", dest="release_id", help="Release-candidate gates")
    p.add_argument("--evidence", type=Path, help="JSON evidence collected from inspected commands")
    p.add_argument("--json", type=Path, help="Write machine-readable report")
    args = p.parse_args(argv)

    evidence = _load_evidence(args.evidence)
    coverage = load_coverage_map()

    if args.issue_id:
        evidence.setdefault("issue_id", args.issue_id)
        command = "issue"
        if args.issue_id.upper() == "WF1" and "executed_smoke_ids" not in evidence:
            ok, tail = _run_wf1_unittests()
            evidence["executed_smoke_ids"] = ["workflow-gate-self-tests"] if ok else []
            evidence["failed_smoke_ids"] = [] if ok else ["workflow-gate-self-tests"]
            evidence.setdefault("smoke_registry_labels", ["workflow-gate-self-tests"])
            evidence.setdefault("required_files", [])
            evidence.setdefault("committed_files", [])
            evidence.setdefault("detail", tail)
        report = evaluate_issue(evidence, coverage)
    elif args.smoke_id:
        evidence.setdefault("issue_id", args.smoke_id)
        command = "smoke"
        if str(args.smoke_id).upper() == "WF1" and "executed_smoke_ids" not in evidence:
            ok, tail = _run_wf1_unittests()
            evidence["executed_smoke_ids"] = ["workflow-gate-self-tests"] if ok else []
            evidence["failed_smoke_ids"] = [] if ok else ["workflow-gate-self-tests"]
            evidence.setdefault("smoke_registry_labels", ["workflow-gate-self-tests"])
            evidence.setdefault("detail", tail)
        report = evaluate_smoke(evidence, coverage)
    elif args.checkin_id:
        evidence.setdefault("issue_id", args.checkin_id)
        evidence.setdefault("remote", "origin")
        evidence.setdefault("branch", "main")
        br = _git("rev-parse", "--abbrev-ref", "HEAD")
        evidence.setdefault("current_branch", (br.stdout or "").strip())
        command = "check-in"
        report = evaluate_check_in(evidence, coverage)
    else:
        evidence.setdefault("issue_id", args.release_id)
        command = "release-proof"
        report = evaluate_release_proof(evidence, coverage)

    payload = report.as_dict()
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    payload["current_stage"] = evidence.get("current_stage")
    payload["plain_english"] = evidence.get("plain_english")
    if report.overall != "PASS":
        payload["next_action"] = "Fix FAIL/UNVERIFIED checks. Do not tell Warren this is done."
    else:
        payload["next_action"] = evidence.get("next_action") or "Record receipt; continue only with remaining authorized work."

    _print_receipt(payload)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    row = issue_row(str(evidence.get("issue_id") or ""), coverage)
    if row:
        print(f"SPEC TIER: {row.get('tier')}")
        print(f"SMOKE IDS: {', '.join(mapped_smoke_ids(str(evidence.get('issue_id')), coverage))}")
    print(f"COMMAND: {command}")
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
