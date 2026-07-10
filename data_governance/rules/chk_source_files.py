"""Category 1 — Source file presence checks."""

from __future__ import annotations

import os

from data_governance.governance_config import CRITICAL, AuditFinding, make_finding
from data_governance.rules._helpers import get_df


def check_source_files(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    ctx = data.get("_context") or {}
    source_dir = ctx.get("source_dir") or ""
    required = ctx.get("required_source_files") or []

    # GOV-003
    for filename in required:
        path = os.path.join(source_dir, filename) if source_dir else filename
        exists = os.path.isfile(path)
        # Also allow pre-loaded flag
        if not exists and data.get(f"_source_exists:{filename}"):
            exists = True
        if not exists:
            findings.append(
                make_finding(
                    rule_id="GOV-003",
                    rule_category="Source Files",
                    severity=CRITICAL,
                    source_file=filename,
                    description="Required LifePRO source file must exist before conversion.",
                    reason=(
                        f"Required source file '{filename}' was not found in "
                        f"QLA_Migration/Source/. This file must exist before conversion "
                        f"can produce reliable output."
                    ),
                    field_name="",
                    expected="file present",
                    actual="missing",
                    affected_keys=[filename],
                    affected_count=1,
                )
            )

    # GOV-005
    output_dir = ctx.get("output_dir") or ""
    plan_path = os.path.join(output_dir, "quikplan.csv") if output_dir else "quikplan.csv"
    plan_df = get_df(data, "quikplan", "quikplan.csv")
    plan_exists = plan_df is not None or (output_dir and os.path.isfile(plan_path))
    if not plan_exists:
        findings.append(
            make_finding(
                rule_id="GOV-005",
                rule_category="Source Files",
                severity=CRITICAL,
                source_file="quikplan.csv",
                description="quikplan.csv must exist in the output directory.",
                reason=(
                    "quikplan.csv was not found in the output directory. "
                    "All other output files reference plan codes — quikplan.csv must "
                    "exist before batch processing."
                ),
                field_name="",
                expected="file present",
                actual="missing",
                affected_keys=["quikplan.csv"],
                affected_count=1,
            )
        )

    return findings
