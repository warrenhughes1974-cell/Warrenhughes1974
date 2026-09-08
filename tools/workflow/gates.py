"""Evidence-driven workflow gates.

Agents may collect evidence. They may not write PASS into a result file
and have that treated as proof. Every decision reads inspected fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .coverage import (
    issue_row,
    load_coverage_map,
    load_smoke_job_labels,
    mapped_smoke_ids,
    protected_ids,
    smoke_ids_in_registry,
)

STATUSES = ("PASS", "FAIL", "NOT_RUN", "BLOCKED", "NOT_APPLICABLE", "UNVERIFIED")
GROK_TIERS = frozenset({"money", "engine", "status", "rates", "claims"})
STANDING_CHECKIN_REMOTE = "origin"
STANDING_CHECKIN_BRANCH = "main"
WARREN_TRIGGERS = frozenset(
    {"nogo", "class_c", "closed_conflict", "force_push", "protected_merge", "deploy", "opus"}
)


@dataclass
class Check:
    id: str
    status: str
    detail: str

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"invalid status {self.status!r}")


@dataclass
class GateReport:
    command: str
    issue_id: str
    overall: str
    checks: list[Check] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 0 if self.overall == "PASS" else 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "issue_id": self.issue_id,
            "overall": self.overall,
            "exit_code": self.exit_code,
            "checks": [c.__dict__ for c in self.checks],
        }


def _failing(checks: list[Check]) -> bool:
    return any(c.status == "FAIL" for c in checks)


def _report(command: str, issue_id: str, checks: list[Check]) -> GateReport:
    overall = "FAIL" if _failing(checks) else "PASS"
    if not checks:
        overall = "FAIL"
        checks = [Check("evidence", "FAIL", "no checks were evaluated")]
    return GateReport(command=command, issue_id=issue_id, overall=overall, checks=checks)


def _add(checks: list[Check], check_id: str, ok: bool, detail: str, *, fail_status: str = "FAIL") -> None:
    checks.append(Check(check_id, "PASS" if ok else fail_status, detail))


def evaluate_issue(evidence: dict[str, Any], coverage: dict[str, Any] | None = None) -> GateReport:
    """Issue-complete gates: mapped smoke, registration, execution, commit membership, approval."""
    coverage = coverage or load_coverage_map()
    issue_id = str(evidence.get("issue_id") or "")
    checks: list[Check] = []
    row = issue_row(issue_id, coverage)
    smokes = mapped_smoke_ids(issue_id, coverage)

    if not issue_id:
        checks.append(Check("issue_id", "FAIL", "issue_id missing"))
        return _report("issue", issue_id, checks)

    if row is None:
        checks.append(Check("coverage_map", "FAIL", f"issue {issue_id} has no mapped smoke"))
    elif not smokes:
        checks.append(Check("mapped_smoke", "FAIL", f"issue {issue_id} has an empty smoke list"))
    else:
        checks.append(Check("mapped_smoke", "PASS", ",".join(smokes)))

    registry = list(evidence.get("smoke_registry_labels") or [])
    if not registry:
        registry = load_smoke_job_labels()
    # Workflow-only issues may use the coverage map as the registry when SMOKE_JOBS is absent.
    if not registry:
        registry = list(smokes)

    for smoke_id in smokes:
        present = smoke_ids_in_registry(registry, smoke_id)
        _add(checks, f"registered:{smoke_id}", present, "in registry" if present else "absent from SMOKE_JOBS/coverage registry")

    executed = {str(x) for x in evidence.get("executed_smoke_ids") or []}
    skipped = {str(x) for x in evidence.get("skipped_smoke_ids") or []}
    failed = {str(x) for x in evidence.get("failed_smoke_ids") or []}
    for smoke_id in smokes:
        if smoke_id in failed:
            checks.append(Check(f"executed:{smoke_id}", "FAIL", "required smoke failed"))
        elif smoke_id in skipped:
            checks.append(Check(f"executed:{smoke_id}", "FAIL", "required smoke skipped; skip is not PASS"))
        elif smoke_id in executed:
            checks.append(Check(f"executed:{smoke_id}", "PASS", "executed"))
        else:
            checks.append(Check(f"executed:{smoke_id}", "FAIL", "registered smoke never executed"))

    matched = evidence.get("matched_count")
    expected_pop = evidence.get("expected_population")
    if evidence.get("validator_status") == "PASS" and expected_pop not in (None, 0) and matched == 0:
        checks.append(Check("empty_population", "FAIL", "validator PASS with unexpectedly empty population"))
    elif "validator_status" in evidence:
        checks.append(Check("empty_population", "PASS", f"matched={matched} expected_population={expected_pop}"))

    required_files = [str(p) for p in evidence.get("required_files") or []]
    committed = {str(p) for p in evidence.get("committed_files") or []}
    for path in required_files:
        _add(checks, f"committed:{path}", path in committed, "in commit tree" if path in committed else "uncommitted or omitted")

    used = [str(p) for p in evidence.get("local_test_used_files") or []]
    tree = {str(p) for p in evidence.get("commit_tree_files") or committed}
    missing_from_commit = [p for p in used if p not in tree]
    _add(
        checks,
        "clean_inputs",
        not missing_from_commit,
        "all local-test files in commit" if not missing_from_commit else f"local tests used files absent from commit: {missing_from_commit}",
    )

    validated_fp = evidence.get("validated_fingerprint")
    current_fp = evidence.get("current_fingerprint")
    if validated_fp or current_fp:
        _add(
            checks,
            "fingerprint",
            validated_fp is not None and validated_fp == current_fp,
            "unchanged" if validated_fp == current_fp else "code, source cut, or Output changed after validation",
        )

    trigger = str(evidence.get("warren_trigger") or "")
    if trigger in WARREN_TRIGGERS:
        _add(
            checks,
            "warren_approval",
            bool(evidence.get("recorded_approval")),
            "recorded" if evidence.get("recorded_approval") else f"advance blocked; {trigger} requires Warren approval",
        )
    else:
        checks.append(Check("warren_approval", "NOT_APPLICABLE", "standing auto-advance"))

    for pid in protected_ids(coverage):
        prow = issue_row(pid, coverage)
        _add(
            checks,
            f"protected:{pid}",
            prow is not None and bool(mapped_smoke_ids(pid, coverage)),
            "mapped" if prow else "protected baseline issue missing from coverage map",
        )

    return _report("issue", issue_id, checks)


def evaluate_smoke(evidence: dict[str, Any], coverage: dict[str, Any] | None = None) -> GateReport:
    coverage = coverage or load_coverage_map()
    issue_id = str(evidence.get("issue_id") or "all")
    checks: list[Check] = []
    if str(evidence.get("issue_id") or "").lower() in {"", "all"}:
        ids = list((coverage.get("issues") or {}).keys())
    else:
        ids = [str(evidence.get("issue_id"))]

    registry = list(evidence.get("smoke_registry_labels") or [])
    if not registry:
        registry = load_smoke_job_labels()
    executed = {str(x) for x in evidence.get("executed_smoke_ids") or []}
    skipped = {str(x) for x in evidence.get("skipped_smoke_ids") or []}
    failed = {str(x) for x in evidence.get("failed_smoke_ids") or []}

    for iid in ids:
        smokes = mapped_smoke_ids(iid, coverage)
        if not smokes:
            checks.append(Check(f"map:{iid}", "FAIL", "no mapped smoke"))
            continue
        if not registry:
            registry = list(smokes)
        for smoke_id in smokes:
            if not smoke_ids_in_registry(registry, smoke_id):
                checks.append(Check(f"registry:{smoke_id}", "FAIL", "absent from SMOKE_JOBS"))
            elif smoke_id in failed or smoke_id in skipped:
                checks.append(Check(f"run:{smoke_id}", "FAIL", "skipped or failed"))
            elif smoke_id not in executed:
                checks.append(Check(f"run:{smoke_id}", "FAIL", "registered smoke never executed"))
            else:
                checks.append(Check(f"run:{smoke_id}", "PASS", "executed"))

    return _report("smoke", issue_id, checks)


def evaluate_check_in(evidence: dict[str, Any], coverage: dict[str, Any] | None = None) -> GateReport:
    _ = coverage or load_coverage_map()
    issue_id = str(evidence.get("issue_id") or "")
    checks: list[Check] = []

    dest_remote = str(evidence.get("remote") or "")
    dest_branch = str(evidence.get("branch") or "")
    intended = dest_remote == STANDING_CHECKIN_REMOTE and dest_branch == STANDING_CHECKIN_BRANCH
    _add(checks, "destination", intended, f"{dest_remote}/{dest_branch}" if dest_remote else "destination missing")

    current_branch = str(evidence.get("current_branch") or "")
    if evidence.get("current_branch") is not None:
        _add(
            checks,
            "branch",
            current_branch == dest_branch or current_branch == STANDING_CHECKIN_BRANCH,
            f"current={current_branch} intended={dest_branch}",
        )

    if evidence.get("push_ok") is True:
        checks.append(Check("push", "PASS", "push command succeeded"))
    elif evidence.get("push_ok") is False:
        checks.append(Check("push", "FAIL", str(evidence.get("push_error") or "push failed")))
    else:
        checks.append(Check("push", "UNVERIFIED", "push result not recorded"))

    remote_verified = evidence.get("remote_verified") is True
    live_sha = str(evidence.get("ls_remote_sha") or "")
    candidate = str(evidence.get("candidate_sha") or "")
    if not remote_verified or not live_sha:
        checks.append(Check("live_remote", "FAIL", "live remote could not be verified"))
    elif candidate and live_sha != candidate and not evidence.get("delivery_contains_fix"):
        checks.append(
            Check(
                "live_remote",
                "FAIL",
                "remote SHA does not match candidate and delivery_contains_fix was not proven",
            )
        )
    else:
        checks.append(Check("live_remote", "PASS", f"sha={live_sha}"))

    if evidence.get("delivery_contains_fix") is False:
        checks.append(Check("delivery_fix", "FAIL", "delivery branch no longer contains the corrected behavior"))
    elif evidence.get("delivery_contains_fix") is True:
        checks.append(Check("delivery_fix", "PASS", "fix present on delivery candidate"))
    else:
        checks.append(Check("delivery_fix", "UNVERIFIED", "delivery fix content not inspected"))
        # UNVERIFIED is not PASS, but only FAIL blocks. Require explicit proof for check-in.
        checks.append(Check("delivery_fix_required", "FAIL", "check-in requires proven delivery_contains_fix"))

    if dest_branch and current_branch and dest_branch != current_branch and dest_branch != STANDING_CHECKIN_BRANCH:
        checks.append(Check("wrong_branch", "FAIL", f"candidate is on {current_branch}, not {dest_branch}"))

    if evidence.get("force_push") or evidence.get("warren_trigger") in {"force_push", "protected_merge", "deploy"}:
        _add(
            checks,
            "warren_approval",
            bool(evidence.get("recorded_approval")),
            "force-push/merge/deploy requires Warren approval",
        )

    if not issue_id:
        checks.append(Check("issue_id", "FAIL", "issue_id missing"))

    # UNVERIFIED push with no recorded result already added; treat UNVERIFIED as blocking for check-in.
    if any(c.id == "push" and c.status == "UNVERIFIED" for c in checks):
        checks.append(Check("push_required", "FAIL", "NOT VERIFIED AS CHECKED IN — push result missing"))

    return _report("check-in", issue_id, checks)


def evaluate_release_proof(evidence: dict[str, Any], coverage: dict[str, Any] | None = None) -> GateReport:
    coverage = coverage or load_coverage_map()
    issue_id = str(evidence.get("issue_id") or "")
    checks: list[Check] = []

    _add(checks, "candidate_sha", bool(evidence.get("candidate_sha")), "recorded" if evidence.get("candidate_sha") else "missing")
    _add(
        checks,
        "clean_checkout",
        evidence.get("clean_checkout_ok") is True,
        "clean-checkout proof present" if evidence.get("clean_checkout_ok") is True else "release candidate requires clean-checkout + full Output rebuild",
    )

    pkg_sha = str(evidence.get("package_candidate_sha") or "")
    cand = str(evidence.get("candidate_sha") or "")
    _add(checks, "package_candidate", bool(pkg_sha) and pkg_sha == cand, f"package={pkg_sha} candidate={cand}")

    pub = str(evidence.get("published_hash") or "")
    valid = str(evidence.get("validated_package_hash") or "")
    _add(checks, "package_hash", bool(pub) and pub == valid, f"published={pub} validated={valid}")

    dest = evidence.get("destination_verified")
    if dest is True:
        checks.append(Check("destination", "PASS", str(evidence.get("delivery_location") or "verified")))
    elif dest is False:
        checks.append(Check("destination", "FAIL", "published package differs or destination missing"))
    else:
        checks.append(Check("destination", "FAIL", "PUBLISHED — RECIPIENT ACCESS NOT VERIFIED"))

    row = issue_row(issue_id, coverage) if issue_id else None
    client_visible = bool((row or {}).get("client_visible")) if row is not None else bool(evidence.get("client_visible"))
    if evidence.get("client_visible") is not None:
        client_visible = bool(evidence.get("client_visible"))
    if client_visible:
        _add(checks, "uat", evidence.get("uat_confirmed") is True, "UAT confirmed" if evidence.get("uat_confirmed") else "required UAT missing")
    else:
        checks.append(Check("uat", "NOT_APPLICABLE", "internal / not client-visible"))

    if evidence.get("output_rebuilt") is not True:
        checks.append(Check("output_rebuild", "FAIL", "no matching rebuilt artifact"))
    else:
        checks.append(Check("output_rebuild", "PASS", str(evidence.get("output_batch_id") or "rebuilt")))

    # Reuse issue smoke completeness when provided
    if mapped_smoke_ids(issue_id, coverage) or evidence.get("executed_smoke_ids"):
        smoke_report = evaluate_issue(evidence, coverage)
        checks.extend(smoke_report.checks)

    return _report("release-proof", issue_id, checks)
