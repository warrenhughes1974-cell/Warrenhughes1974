"""Self-tests for the verified development/delivery gates.

Uses disposable evidence dicts and temporary coverage maps.
Does not touch the real remote, source extracts, or published Output.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("WORKFLOW_GATE_SKIP_SELFTEST", "1")

from tools.workflow.coverage import load_coverage_map  # noqa: E402
from tools.workflow.gates import (  # noqa: E402
    evaluate_check_in,
    evaluate_issue,
    evaluate_release_proof,
    evaluate_smoke,
)


def _map(**issues):
    return {
        "version": "test-1",
        "protected_baseline": ["25", "26", "143", "WF1"],
        "issues": issues,
    }


def _issue_row(smoke="smoke-143"):
    return {
        "title": "fixture",
        "tier": "money",
        "client_visible": True,
        "smoke_ids": [smoke],
        "scripts": ["tools/validators/fake_143.py"],
    }


def _passing_issue(issue_id="143", smoke="smoke-143"):
    return {
        "issue_id": issue_id,
        "smoke_registry_labels": [smoke],
        "executed_smoke_ids": [smoke],
        "skipped_smoke_ids": [],
        "failed_smoke_ids": [],
        "validator_status": "PASS",
        "matched_count": 3,
        "expected_population": 3,
        "required_files": ["tools/validators/fake_143.py"],
        "committed_files": ["tools/validators/fake_143.py"],
        "commit_tree_files": ["tools/validators/fake_143.py"],
        "local_test_used_files": ["tools/validators/fake_143.py"],
        "validated_fingerprint": "abc",
        "current_fingerprint": "abc",
    }


class IssueGateTests(unittest.TestCase):
    def test_fix_with_no_mapped_smoke_fails(self):
        coverage = _map(WF1=_issue_row("workflow-gate-self-tests"), **{"25": _issue_row("s25"), "26": _issue_row("s26"), "143": _issue_row()})
        ev = _passing_issue("999")
        report = evaluate_issue(ev, coverage)
        self.assertEqual(report.overall, "FAIL")
        self.assertTrue(any("no mapped smoke" in c.detail for c in report.checks))

    def test_smoke_absent_from_registry_fails(self):
        coverage = _map(WF1=_issue_row("workflow-gate-self-tests"), **{"25": _issue_row("s25"), "26": _issue_row("s26"), "143": _issue_row()})
        ev = _passing_issue()
        ev["smoke_registry_labels"] = ["some-other-smoke"]
        report = evaluate_issue(ev, coverage)
        self.assertEqual(report.overall, "FAIL")
        self.assertTrue(any(c.id.startswith("registered:") and c.status == "FAIL" for c in report.checks))

    def test_registered_smoke_never_executed_fails(self):
        coverage = _map(WF1=_issue_row("workflow-gate-self-tests"), **{"25": _issue_row("s25"), "26": _issue_row("s26"), "143": _issue_row()})
        ev = _passing_issue()
        ev["executed_smoke_ids"] = []
        report = evaluate_issue(ev, coverage)
        self.assertEqual(report.overall, "FAIL")
        self.assertTrue(any("never executed" in c.detail for c in report.checks))

    def test_skipped_or_failed_smoke_fails(self):
        coverage = _map(WF1=_issue_row("workflow-gate-self-tests"), **{"25": _issue_row("s25"), "26": _issue_row("s26"), "143": _issue_row()})
        ev = _passing_issue()
        ev["executed_smoke_ids"] = []
        ev["skipped_smoke_ids"] = ["smoke-143"]
        report = evaluate_issue(ev, coverage)
        self.assertEqual(report.overall, "FAIL")
        ev2 = _passing_issue()
        ev2["executed_smoke_ids"] = []
        ev2["failed_smoke_ids"] = ["smoke-143"]
        self.assertEqual(evaluate_issue(ev2, coverage).overall, "FAIL")

    def test_empty_population_pass_fails(self):
        coverage = _map(WF1=_issue_row("workflow-gate-self-tests"), **{"25": _issue_row("s25"), "26": _issue_row("s26"), "143": _issue_row()})
        ev = _passing_issue()
        ev["matched_count"] = 0
        ev["expected_population"] = 10
        report = evaluate_issue(ev, coverage)
        self.assertEqual(report.overall, "FAIL")
        self.assertTrue(any(c.id == "empty_population" and c.status == "FAIL" for c in report.checks))

    def test_uncommitted_required_file_fails(self):
        coverage = _map(WF1=_issue_row("workflow-gate-self-tests"), **{"25": _issue_row("s25"), "26": _issue_row("s26"), "143": _issue_row()})
        ev = _passing_issue()
        ev["committed_files"] = []
        ev["commit_tree_files"] = []
        report = evaluate_issue(ev, coverage)
        self.assertEqual(report.overall, "FAIL")
        self.assertTrue(any(c.id.startswith("committed:") and c.status == "FAIL" for c in report.checks))

    def test_local_test_file_absent_from_commit_fails(self):
        coverage = _map(WF1=_issue_row("workflow-gate-self-tests"), **{"25": _issue_row("s25"), "26": _issue_row("s26"), "143": _issue_row()})
        ev = _passing_issue()
        ev["local_test_used_files"] = ["hidden_fixture.py"]
        ev["commit_tree_files"] = ["tools/validators/fake_143.py"]
        report = evaluate_issue(ev, coverage)
        self.assertEqual(report.overall, "FAIL")
        self.assertTrue(any(c.id == "clean_inputs" and c.status == "FAIL" for c in report.checks))

    def test_fingerprint_change_after_validation_fails(self):
        coverage = _map(WF1=_issue_row("workflow-gate-self-tests"), **{"25": _issue_row("s25"), "26": _issue_row("s26"), "143": _issue_row()})
        ev = _passing_issue()
        ev["current_fingerprint"] = "changed"
        report = evaluate_issue(ev, coverage)
        self.assertEqual(report.overall, "FAIL")
        self.assertTrue(any(c.id == "fingerprint" and c.status == "FAIL" for c in report.checks))

    def test_advance_without_warren_approval_on_exception_fails(self):
        coverage = _map(WF1=_issue_row("workflow-gate-self-tests"), **{"25": _issue_row("s25"), "26": _issue_row("s26"), "143": _issue_row()})
        ev = _passing_issue()
        ev["warren_trigger"] = "class_c"
        ev["recorded_approval"] = False
        report = evaluate_issue(ev, coverage)
        self.assertEqual(report.overall, "FAIL")
        self.assertTrue(any(c.id == "warren_approval" and c.status == "FAIL" for c in report.checks))

    def test_deleting_protected_row_still_fails(self):
        coverage = {
            "version": "test-1",
            "protected_baseline": ["25", "26", "143", "WF1"],
            "issues": {
                "WF1": _issue_row("workflow-gate-self-tests"),
                "25": _issue_row("s25"),
                "26": _issue_row("s26"),
                # 143 deleted from issues
            },
        }
        ev = _passing_issue("25", "s25")
        ev["smoke_registry_labels"] = ["s25"]
        ev["executed_smoke_ids"] = ["s25"]
        ev["required_files"] = []
        ev["committed_files"] = []
        ev["commit_tree_files"] = []
        ev["local_test_used_files"] = []
        report = evaluate_issue(ev, coverage)
        self.assertEqual(report.overall, "FAIL")
        self.assertTrue(any(c.id == "protected:143" and c.status == "FAIL" for c in report.checks))

    def test_happy_path_pass(self):
        coverage = _map(
            WF1=_issue_row("workflow-gate-self-tests"),
            **{"25": _issue_row("s25"), "26": _issue_row("s26"), "143": _issue_row()},
        )
        ev = _passing_issue()
        report = evaluate_issue(ev, coverage)
        self.assertEqual(report.overall, "PASS", [c.__dict__ for c in report.checks if c.status == "FAIL"])


class CheckInGateTests(unittest.TestCase):
    def _base(self):
        return {
            "issue_id": "WF1",
            "remote": "origin",
            "branch": "main",
            "current_branch": "main",
            "push_ok": True,
            "remote_verified": True,
            "ls_remote_sha": "aaa",
            "candidate_sha": "aaa",
            "delivery_contains_fix": True,
        }

    def test_push_failure_or_unverified_remote_fails(self):
        ev = self._base()
        ev["push_ok"] = False
        ev["push_error"] = "authentication failed"
        self.assertEqual(evaluate_check_in(ev).overall, "FAIL")
        ev2 = self._base()
        ev2["remote_verified"] = False
        ev2["ls_remote_sha"] = ""
        self.assertEqual(evaluate_check_in(ev2).overall, "FAIL")

    def test_wrong_branch_fails(self):
        ev = self._base()
        ev["branch"] = "release"
        ev["current_branch"] = "feature-x"
        ev["remote"] = "origin"
        report = evaluate_check_in(ev)
        self.assertEqual(report.overall, "FAIL")

    def test_delivery_missing_fix_fails(self):
        ev = self._base()
        ev["delivery_contains_fix"] = False
        self.assertEqual(evaluate_check_in(ev).overall, "FAIL")

    def test_missing_push_record_fails(self):
        ev = self._base()
        del ev["push_ok"]
        self.assertEqual(evaluate_check_in(ev).overall, "FAIL")


class ReleaseProofTests(unittest.TestCase):
    def _base(self):
        return {
            "issue_id": "WF1",
            "candidate_sha": "sha1",
            "clean_checkout_ok": True,
            "package_candidate_sha": "sha1",
            "published_hash": "pkg1",
            "validated_package_hash": "pkg1",
            "destination_verified": True,
            "delivery_location": "\\\\test\\share",
            "client_visible": False,
            "output_rebuilt": True,
            "output_batch_id": "batch-1",
            "smoke_registry_labels": ["workflow-gate-self-tests"],
            "executed_smoke_ids": ["workflow-gate-self-tests"],
            "required_files": [],
            "committed_files": [],
            "commit_tree_files": [],
            "local_test_used_files": [],
        }

    def test_package_from_wrong_candidate_fails(self):
        ev = self._base()
        ev["package_candidate_sha"] = "other"
        self.assertEqual(evaluate_release_proof(ev).overall, "FAIL")

    def test_published_hash_mismatch_fails(self):
        ev = self._base()
        ev["published_hash"] = "different"
        self.assertEqual(evaluate_release_proof(ev).overall, "FAIL")

    def test_missing_uat_on_client_visible_fails(self):
        ev = self._base()
        ev["client_visible"] = True
        ev["uat_confirmed"] = False
        self.assertEqual(evaluate_release_proof(ev).overall, "FAIL")

    def test_internal_issue_uat_not_required(self):
        ev = self._base()
        ev["client_visible"] = False
        report = evaluate_release_proof(ev)
        self.assertTrue(any(c.id == "uat" and c.status == "NOT_APPLICABLE" for c in report.checks))
        self.assertEqual(report.overall, "PASS", [c.__dict__ for c in report.checks if c.status == "FAIL"])

    def test_no_rebuilt_output_fails(self):
        ev = self._base()
        ev["output_rebuilt"] = False
        self.assertEqual(evaluate_release_proof(ev).overall, "FAIL")


class SmokeAllAndMapTests(unittest.TestCase):
    def test_installed_coverage_map_loads(self):
        data = load_coverage_map()
        self.assertEqual(data["version"], "1.0.0")
        self.assertIn("143", data["issues"])
        self.assertIn("WF1", data["issues"])

    def test_smoke_all_fails_when_none_executed(self):
        coverage = load_coverage_map()
        report = evaluate_smoke({"issue_id": "all", "executed_smoke_ids": []}, coverage)
        self.assertEqual(report.overall, "FAIL")

    def test_cli_rejects_empty_evidence_checkin(self):
        import subprocess

        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "validators" / "run_workflow_gate.py"), "--check-in", "WF1"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            errors="replace",
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("OVERALL STATUS: FAIL", r.stdout)

    def test_cli_issue_wf1_with_evidence_file(self):
        import subprocess

        coverage = load_coverage_map()
        ev = {
            "issue_id": "WF1",
            "smoke_registry_labels": ["workflow-gate-self-tests"],
            "executed_smoke_ids": ["workflow-gate-self-tests"],
            "required_files": ["tools/workflow/gates.py"],
            "committed_files": ["tools/workflow/gates.py"],
            "commit_tree_files": ["tools/workflow/gates.py"],
            "local_test_used_files": ["tools/workflow/gates.py"],
            "validated_fingerprint": "x",
            "current_fingerprint": "x",
        }
        with tempfile.TemporaryDirectory() as td:
            ev_path = Path(td) / "ev.json"
            ev_path.write_text(json.dumps(ev), encoding="utf-8")
            r = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "validators" / "run_workflow_gate.py"),
                    "--issue",
                    "WF1",
                    "--evidence",
                    str(ev_path),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                errors="replace",
            )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OVERALL STATUS: PASS", r.stdout)
        self.assertTrue(coverage["issues"]["WF1"]["smoke_ids"])


if __name__ == "__main__":
    unittest.main()
