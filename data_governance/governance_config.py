"""Data models and severity constants for the Data Governance Audit Module.

This module is audit/reporting only — findings never block or modify data.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


CRITICAL = "Critical"
HIGH = "High"
ADVISORY = "Advisory"
INFO = "Info"

SEVERITY_ORDER = (CRITICAL, HIGH, ADVISORY, INFO)

SCHEMA_MANIFEST_VERSION = "1.0.0"


@dataclass
class AuditFinding:
    rule_id: str
    rule_category: str
    severity: str
    source_file: str
    description: str
    reason: str
    field_name: str
    expected: str
    actual: str
    affected_keys: list = field(default_factory=list)
    affected_count: int = 0
    sample_records: list = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GovernanceReport:
    run_timestamp: str
    conversion_id: str
    conversion_source: str
    conversion_target: str
    findings: list[AuditFinding] = field(default_factory=list)
    total_findings: int = 0
    by_severity: dict = field(default_factory=dict)
    by_category: dict = field(default_factory=dict)
    by_file: dict = field(default_factory=dict)
    clean: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_timestamp": self.run_timestamp,
            "conversion_id": self.conversion_id,
            "conversion_source": self.conversion_source,
            "conversion_target": self.conversion_target,
            "findings": [f.to_dict() for f in self.findings],
            "total_findings": self.total_findings,
            "by_severity": self.by_severity,
            "by_category": self.by_category,
            "by_file": self.by_file,
            "clean": self.clean,
        }


def make_finding(
    rule_id: str,
    rule_category: str,
    severity: str,
    source_file: str,
    description: str,
    reason: str,
    field_name: str = "",
    expected: str = "",
    actual: str = "",
    affected_keys: list | None = None,
    sample_records: list | None = None,
    affected_count: int | None = None,
) -> AuditFinding:
    """Build an AuditFinding with sensible defaults for count/samples."""
    keys = list(affected_keys or [])
    samples = list(sample_records or [])
    count = affected_count if affected_count is not None else len(keys)
    if count == 0 and keys:
        count = len(keys)
    return AuditFinding(
        rule_id=rule_id,
        rule_category=rule_category,
        severity=severity,
        source_file=source_file,
        description=description,
        reason=reason,
        field_name=field_name,
        expected=str(expected) if expected is not None else "",
        actual=str(actual) if actual is not None else "",
        affected_keys=keys[:500],
        affected_count=count,
        sample_records=samples[:10],
    )
