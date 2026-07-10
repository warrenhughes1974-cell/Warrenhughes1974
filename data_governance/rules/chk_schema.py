"""Category 2 — Schema integrity (column order and structure)."""

from __future__ import annotations

from data_governance.constants.schema_manifests import (
    SCHEMA_MANIFESTS,
    SCHEMA_MANIFEST_VERSION,
)
from data_governance.governance_config import CRITICAL, INFO, AuditFinding, make_finding
from data_governance.rules._helpers import get_df


def check_schema(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    ctx = data.get("_context") or {}

    for table_key, expected in SCHEMA_MANIFESTS.items():
        fname = f"{table_key}.csv"
        df = get_df(data, table_key, fname)
        if df is None:
            continue
        actual_cols = [str(c) for c in df.columns]

        # FMT-007 — column order
        min_len = min(len(actual_cols), len(expected))
        for i in range(min_len):
            if actual_cols[i] != expected[i]:
                findings.append(
                    make_finding(
                        rule_id="FMT-007",
                        rule_category="Schema Integrity",
                        severity=CRITICAL,
                        source_file=fname,
                        description="Output column order must match the QLA schema exactly.",
                        reason=(
                            f"In '{fname}', column at position {i} is "
                            f"'{actual_cols[i]}' but expected '{expected[i]}'. "
                            f"Column order must match the QLA schema exactly."
                        ),
                        field_name=actual_cols[i],
                        expected=expected[i],
                        actual=actual_cols[i],
                        affected_keys=[fname],
                        sample_records=[{"position": i, "actual": actual_cols[i], "expected": expected[i]}],
                        affected_count=1,
                    )
                )
                break  # first divergence is enough for order

        # FMT-008 — extra / missing columns
        expected_set = set(expected)
        actual_set = set(actual_cols)
        extra = sorted(actual_set - expected_set)
        missing = sorted(expected_set - actual_set)

        if extra:
            findings.append(
                make_finding(
                    rule_id="FMT-008",
                    rule_category="Schema Integrity",
                    severity=CRITICAL,
                    source_file=fname,
                    description="Output must not contain columns outside the QLA schema.",
                    reason=(
                        f"'{fname}' has {len(extra)} column(s) not in the schema: "
                        f"{extra}. These will cause import failure."
                    ),
                    field_name=",".join(extra[:5]),
                    expected="no extra columns",
                    actual=str(extra),
                    affected_keys=extra,
                    affected_count=len(extra),
                )
            )
        if missing:
            findings.append(
                make_finding(
                    rule_id="FMT-008",
                    rule_category="Schema Integrity",
                    severity=CRITICAL,
                    source_file=fname,
                    description="Output must include all required QLA schema columns.",
                    reason=(
                        f"'{fname}' is missing {len(missing)} required column(s): {missing}."
                    ),
                    field_name=",".join(missing[:5]),
                    expected=str(missing),
                    actual="missing",
                    affected_keys=missing,
                    affected_count=len(missing),
                )
            )

    # GOV-012 — schema manifest version vs app table version
    app_version = str(ctx.get("app_table_version") or ctx.get("schema_version") or "")
    if app_version and app_version != SCHEMA_MANIFEST_VERSION:
        findings.append(
            make_finding(
                rule_id="GOV-012",
                rule_category="Schema Integrity",
                severity=INFO,
                source_file="schema_manifests",
                description="Schema manifest version should align with app table version.",
                reason=(
                    f"schema_manifest version '{SCHEMA_MANIFEST_VERSION}' does not match "
                    f"app table version '{app_version}'. Review to confirm schemas are aligned."
                ),
                field_name="SCHEMA_MANIFEST_VERSION",
                expected=app_version,
                actual=SCHEMA_MANIFEST_VERSION,
                affected_keys=[SCHEMA_MANIFEST_VERSION, app_version],
                affected_count=1,
            )
        )

    return findings
