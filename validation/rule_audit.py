"""Rule execution audit tracker for final output validation."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Callable

from .validation_config import rule_meta

AUDIT_COLUMNS = [
    "rule_id", "rule_name", "severity", "disposition", "status",
    "files_expected", "files_found", "files_missing",
    "records_scanned", "findings_count", "skip_reason", "error_message",
    "started_at", "completed_at", "runtime_seconds",
]

STATUS_PENDING = "PENDING"
STATUS_EXECUTED_NO_FINDINGS = "EXECUTED_NO_FINDINGS"
STATUS_EXECUTED_WITH_FINDINGS = "EXECUTED_WITH_FINDINGS"
STATUS_SKIPPED_OPTIONAL = "SKIPPED_MISSING_OPTIONAL_FILE"
STATUS_SKIPPED_NA = "SKIPPED_NOT_APPLICABLE"
STATUS_SKIPPED_DISABLED = "SKIPPED_CONFIG_DISABLED"
STATUS_FAILED = "FAILED_INTERNAL_ERROR"


class RuleAuditTracker:
    """Tracks per-rule execution for UAT transparency."""

    def __init__(self, known_rule_ids: list[str] | None = None) -> None:
        self._rows: dict[str, dict[str, Any]] = {}
        self._timers: dict[str, float] = {}
        if known_rule_ids:
            for rid in known_rule_ids:
                self._ensure_row(rid)

    def known_rule_ids(self) -> list[str]:
        return sorted(self._rows.keys())

    def _ensure_row(self, rule_id: str) -> dict[str, Any]:
        if rule_id not in self._rows:
            meta = rule_meta(rule_id)
            self._rows[rule_id] = {
                "rule_id": rule_id,
                "rule_name": meta.get("rule_name", rule_id),
                "severity": meta.get("severity", "High"),
                "disposition": meta.get("disposition", "Hold"),
                "status": STATUS_PENDING,
                "files_expected": "",
                "files_found": "",
                "files_missing": "",
                "records_scanned": 0,
                "findings_count": 0,
                "skip_reason": "",
                "error_message": "",
                "started_at": "",
                "completed_at": "",
                "runtime_seconds": "",
            }
        return self._rows[rule_id]

    def begin(
        self,
        rule_id: str,
        *,
        files_expected: list[str] | None = None,
        files_found: list[str] | None = None,
        files_missing: list[str] | None = None,
        records_scanned: int = 0,
    ) -> None:
        row = self._ensure_row(rule_id)
        row["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._timers[rule_id] = time.perf_counter()
        if files_expected is not None:
            row["files_expected"] = "|".join(files_expected)
        if files_found is not None:
            row["files_found"] = "|".join(files_found)
        if files_missing is not None:
            row["files_missing"] = "|".join(files_missing)
        if records_scanned:
            row["records_scanned"] = records_scanned

    def skip(
        self,
        rule_id: str,
        reason: str,
        *,
        status: str = STATUS_SKIPPED_NA,
        files_expected: list[str] | None = None,
        files_found: list[str] | None = None,
        files_missing: list[str] | None = None,
    ) -> None:
        row = self._ensure_row(rule_id)
        if not row.get("started_at"):
            row["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row["status"] = status
        row["skip_reason"] = reason
        row["findings_count"] = 0
        if files_expected is not None:
            row["files_expected"] = "|".join(files_expected)
        if files_found is not None:
            row["files_found"] = "|".join(files_found)
        if files_missing is not None:
            row["files_missing"] = "|".join(files_missing)
        self._finish_timer(rule_id)

    def complete(
        self,
        rule_id: str,
        findings_count: int,
        *,
        records_scanned: int | None = None,
        files_expected: list[str] | None = None,
        files_found: list[str] | None = None,
        files_missing: list[str] | None = None,
    ) -> None:
        row = self._ensure_row(rule_id)
        row["findings_count"] = findings_count
        row["status"] = (
            STATUS_EXECUTED_WITH_FINDINGS if findings_count else STATUS_EXECUTED_NO_FINDINGS
        )
        if records_scanned is not None:
            row["records_scanned"] = records_scanned
        if files_expected is not None:
            row["files_expected"] = "|".join(files_expected)
        if files_found is not None:
            row["files_found"] = "|".join(files_found)
        if files_missing is not None:
            row["files_missing"] = "|".join(files_missing)
        self._finish_timer(rule_id)

    def fail(self, rule_id: str, error_message: str) -> None:
        row = self._ensure_row(rule_id)
        row["status"] = STATUS_FAILED
        row["error_message"] = str(error_message)[:500]
        if not row.get("started_at"):
            row["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._finish_timer(rule_id)

    def _finish_timer(self, rule_id: str) -> None:
        row = self._rows.get(rule_id)
        if not row:
            return
        row["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start = self._timers.get(rule_id)
        if start is not None:
            row["runtime_seconds"] = f"{time.perf_counter() - start:.4f}"

    def run_guarded(
        self,
        rule_id: str,
        fn: Callable[[], list[dict]],
        *,
        files_expected: list[str] | None = None,
        files_found: list[str] | None = None,
        files_missing: list[str] | None = None,
        records_scanned: int = 0,
        skip_if: str | None = None,
        skip_status: str = STATUS_SKIPPED_NA,
    ) -> list[dict]:
        """Execute a rule; capture failures without aborting the full validator."""
        if skip_if:
            self.skip(
                rule_id, skip_if,
                status=skip_status,
                files_expected=files_expected,
                files_found=files_found,
                files_missing=files_missing,
            )
            return []
        self.begin(
            rule_id,
            files_expected=files_expected,
            files_found=files_found,
            files_missing=files_missing,
            records_scanned=records_scanned,
        )
        try:
            findings = fn() or []
            self.complete(
                rule_id, len(findings),
                records_scanned=records_scanned,
                files_expected=files_expected,
                files_found=files_found,
                files_missing=files_missing,
            )
            return findings
        except Exception as exc:
            self.fail(rule_id, str(exc))
            return [{
                "rule_id": rule_id,
                "rule_name": rule_meta(rule_id).get("rule_name", rule_id),
                "severity": "High",
                "disposition": "Hold",
                "table_name": "",
                "file_name": "",
                "key_fields": "",
                "key_value": "",
                "field_name": "",
                "actual_value": "",
                "expected_value": "",
                "message": f"Rule internal error: {exc}",
                "source_file": "",
                "row_number": "",
                "created_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }]

    def finalize_unrun(self, default_reason: str = "Rule not executed in this validation pass") -> None:
        for row in self._rows.values():
            if row["status"] == STATUS_PENDING:
                row["status"] = STATUS_SKIPPED_NA
                row["skip_reason"] = default_reason
                if not row.get("started_at"):
                    row["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if not row.get("completed_at"):
                    row["completed_at"] = row["started_at"]
                    row["runtime_seconds"] = "0.0000"

    def summary_counts(self) -> dict[str, int]:
        rows = list(self._rows.values())
        return {
            "total_rules_known": len(rows),
            "rules_executed": sum(
                1 for r in rows
                if r["status"] in (STATUS_EXECUTED_NO_FINDINGS, STATUS_EXECUTED_WITH_FINDINGS)
            ),
            "rules_with_findings": sum(
                1 for r in rows if r["status"] == STATUS_EXECUTED_WITH_FINDINGS
            ),
            "rules_skipped": sum(
                1 for r in rows
                if r["status"].startswith("SKIPPED")
            ),
            "rules_failed_internally": sum(1 for r in rows if r["status"] == STATUS_FAILED),
        }

    def to_list(self) -> list[dict]:
        return [self._rows[k] for k in sorted(self._rows.keys())]
