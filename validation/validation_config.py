"""Configuration and constants for enterprise final output validation."""

from __future__ import annotations

import json
import os
from typing import Any

# Severity → disposition mapping (default; per-rule overrides in RULE_META)
SEVERITY_TO_DISPOSITION = {
    "Critical": "Block",
    "High": "Hold",
    "Medium": "Warning",
    "Low": "Report only",
    "Informational": "Report only",
}

# Map legacy validate_output severities to enterprise tiers
LEGACY_SEVERITY_MAP = {
    "ERROR": "Critical",
    "WARN": "High",
    "INFO": "Informational",
}

RULE_META: dict[str, dict[str, str]] = {
    "POL-001": {"rule_name": "Duplicate MPOLICY in quikmstr", "severity": "Critical", "disposition": "Block"},
    "POL-002": {"rule_name": "Missing MPOLICY", "severity": "Critical", "disposition": "Block"},
    "POL-008": {"rule_name": "MPAIDTO before issue date", "severity": "High", "disposition": "Hold"},
    "CW-001": {"rule_name": "One source policy maps to multiple MPOLICY", "severity": "Critical", "disposition": "Block"},
    "CW-002": {"rule_name": "Multiple source policies map to same MPOLICY", "severity": "Critical", "disposition": "Block"},
    "REF-001": {"rule_name": "quikridr without quikmstr", "severity": "Critical", "disposition": "Block"},
    "REF-002": {"rule_name": "quikprmh without quikmstr", "severity": "Critical", "disposition": "Block"},
    "REF-003": {"rule_name": "quikclms without quikmstr", "severity": "Critical", "disposition": "Block"},
    "REF-011": {"rule_name": "MPLAN on rider not found in quikplan", "severity": "High", "disposition": "Hold"},
    "REQ-002": {"rule_name": "quikridr MRIDRID blank", "severity": "Critical", "disposition": "Block"},
    "REQ-003": {"rule_name": "quikridr MPHASE blank or zero", "severity": "Critical", "disposition": "Block"},
    "RDR-002": {"rule_name": "MPHASE=1 base coverage missing", "severity": "High", "disposition": "Hold"},
    "RDR-003": {"rule_name": "Supplemental rider without base", "severity": "High", "disposition": "Hold"},
    "DUP-002": {"rule_name": "Duplicate quikridr MPOLICY+MPHASE", "severity": "Critical", "disposition": "Block"},
    "DUP-003": {"rule_name": "Duplicate MRIDRID", "severity": "Critical", "disposition": "Block"},
    "DUP-008": {"rule_name": "Duplicate CLAIMNUM in quikclms", "severity": "Critical", "disposition": "Block"},
    "CLM-006": {"rule_name": "Borrowed-money-only PACTG on quikclms policy", "severity": "Critical", "disposition": "Block"},
    "CLM-011": {"rule_name": "Governance metadata leaked to claim output", "severity": "Critical", "disposition": "Block"},
    "PRM-009": {"rule_name": "Loan/borrowed-money codes in quikprmh", "severity": "Critical", "disposition": "Block"},
    "PRM-010": {"rule_name": "Blank DATEPAID in quikprmh", "severity": "High", "disposition": "Hold"},
    "DT-001": {"rule_name": "Enterprise date range validation", "severity": "Medium", "disposition": "Warning"},
    "DT-003": {"rule_name": "Insured DOB after policy issue date", "severity": "Critical", "disposition": "Hold"},
    "FMT-007": {"rule_name": "Output column order mismatch", "severity": "Critical", "disposition": "Block"},
    "FMT-008": {"rule_name": "Extra or missing output columns", "severity": "Critical", "disposition": "Block"},
    "GOV-003": {"rule_name": "Required LifePRO source file missing", "severity": "Critical", "disposition": "Block"},
    "GOV-005": {"rule_name": "quikplan.csv missing in output", "severity": "Critical", "disposition": "Block"},
    "GOV-012": {"rule_name": "schema_manifest out of sync", "severity": "High", "disposition": "Report only"},
    "RCN-001": {"rule_name": "Source policy count vs quikmstr", "severity": "High", "disposition": "Report only"},
    "RCN-004": {"rule_name": "PLOAN vs quikloan staging count", "severity": "High", "disposition": "Report only"},
    "LOAN-002": {"rule_name": "Duplicate MPOLICY in quikloan", "severity": "Critical", "disposition": "Block"},
    "LOAN-005": {"rule_name": "Missing MLOANDATE on loan", "severity": "High", "disposition": "Hold"},
    "CLNT-001": {"rule_name": "Duplicate MCLIENTID in quikclnt", "severity": "Critical", "disposition": "Block"},
    "CLID-001": {"rule_name": "MCLIENTID must exist in quikclnt", "severity": "Critical", "disposition": "Block"},
    "CLID-002": {"rule_name": "MPOLICY must exist in quikmstr", "severity": "Critical", "disposition": "Block"},
    "CLID-003": {"rule_name": "MPHASE rider reference in quikridr", "severity": "Critical", "disposition": "Block"},
    "PLAN-001": {"rule_name": "PLAN code format", "severity": "Critical", "disposition": "Block"},
    "MSTR-001": {"rule_name": "MSTATUS required and valid", "severity": "High", "disposition": "Hold"},
    "MSTR-002": {"rule_name": "MSTATDATE required and valid", "severity": "High", "disposition": "Hold"},
    "MSTR-003": {"rule_name": "MBILLTO date ordering", "severity": "High", "disposition": "Hold"},
    "MSTR-006": {"rule_name": "MBILLFRM required", "severity": "High", "disposition": "Hold"},
    "MSTR-008": {"rule_name": "Bank number required for bank billing", "severity": "High", "disposition": "Hold"},
    "MSTR-009": {"rule_name": "MMODE required", "severity": "High", "disposition": "Hold"},
    "MSTR-010": {"rule_name": "MISSUEST required and valid", "severity": "High", "disposition": "Hold"},
    "MSTR-012": {"rule_name": "Client ID references must exist in quikclnt", "severity": "Critical", "disposition": "Block"},
    "MSTR-013": {"rule_name": "MBENPID and MBENCID must be empty", "severity": "High", "disposition": "Hold"},
    "RDR-PLAN-001": {"rule_name": "Rider MPLAN PUA/rate-up placeholder", "severity": "Medium", "disposition": "Warning"},
    "CLM-001": {"rule_name": "Claim without policy master (alias REF-003)", "severity": "Critical", "disposition": "Block"},
}

# output_files: list of filenames under output_dir; source_files: under source_dir
# required=False means rule skips gracefully when output file absent
RULE_FILE_DEPS: dict[str, dict[str, Any]] = {
    "GOV-005": {"output_files": ["quikplan.csv"], "required": True},
    "GOV-003": {"source_files": ["quikmstr.csv", "PPBEN.csv", "PACTG_Accounting_Extract20260427.csv"], "required": False},
    "GOV-012": {"config_files": ["validation_config/schema_manifest.json"], "required": False},
    "POL-001": {"output_files": ["quikmstr.csv"], "required": True},
    "POL-002": {"output_files": ["quikmstr.csv"], "required": True},
    "POL-008": {"output_files": ["quikmstr.csv"], "required": True},
    "MSTR-001": {"output_files": ["quikmstr.csv"], "required": True},
    "MSTR-002": {"output_files": ["quikmstr.csv"], "required": True},
    "MSTR-006": {"output_files": ["quikmstr.csv"], "required": True},
    "MSTR-008": {"output_files": ["quikmstr.csv"], "required": True},
    "MSTR-009": {"output_files": ["quikmstr.csv"], "required": True},
    "MSTR-010": {"output_files": ["quikmstr.csv"], "required": True},
    "MSTR-012": {"output_files": ["quikmstr.csv", "quikclnt.csv"], "required": True},
    "MSTR-013": {"output_files": ["quikmstr.csv"], "required": True},
    "REF-001": {"output_files": ["quikridr.csv", "quikmstr.csv"], "required": True},
    "REF-002": {"output_files": ["quikprmh.csv", "quikmstr.csv"], "required": False},
    "REF-003": {"output_files": ["quikclms.csv", "quikmstr.csv"], "required": False},
    "REF-011": {"output_files": ["quikridr.csv", "quikplan.csv"], "required": True},
    "REQ-002": {"output_files": ["quikridr.csv"], "required": True},
    "REQ-003": {"output_files": ["quikridr.csv"], "required": True},
    "RDR-002": {"output_files": ["quikridr.csv"], "required": True},
    "RDR-003": {"output_files": ["quikridr.csv"], "required": True},
    "DUP-002": {"output_files": ["quikridr.csv"], "required": True},
    "DUP-003": {"output_files": ["quikridr.csv"], "required": True},
    "DUP-008": {"output_files": ["quikclms.csv"], "required": False},
    "CLM-006": {"source_files": ["PACTG_Accounting_Extract20260427.csv", "PACTG.csv"], "output_files": ["quikclms.csv"], "required": False},
    "CLM-011": {"output_files": ["quikclms.csv", "quikclmp.csv"], "required": False},
    "PRM-009": {"output_files": ["quikprmh.csv"], "required": False},
    "PRM-010": {"output_files": ["quikprmh.csv"], "required": False},
    "DT-001": {"output_files": ["quikmstr.csv"], "required": False},
    "DT-003": {"output_files": ["quikridr.csv", "quikmstr.csv"], "required": True},
    "FMT-007": {"output_files": [], "required": False},
    "FMT-008": {"output_files": [], "required": False},
    "LOAN-002": {"output_files": ["quikloan.csv"], "required": False},
    "LOAN-005": {"output_files": ["quikloan.csv"], "required": False},
    "CLNT-001": {"output_files": ["quikclnt.csv"], "required": False},
    "CLID-001": {"output_files": ["quikclid.csv", "quikclnt.csv"], "required": False},
    "CLID-002": {"output_files": ["quikclid.csv", "quikmstr.csv"], "required": False},
    "CLID-003": {"output_files": ["quikclid.csv", "quikridr.csv"], "required": False},
    "PLAN-001": {"output_files": ["quikplan.csv"], "required": False},
    "CW-001": {"crosswalk": True, "required": False},
    "CW-002": {"crosswalk": True, "required": False},
    "RCN-001": {"source_files": ["quikmstr.csv"], "output_files": ["quikmstr.csv"], "required": False},
    "RCN-004": {"staging_files": ["plan_analysis/phase_l1_quikloan/quikloan_emit_candidates.csv"], "required": False},
    "RDR-PLAN-001": {"output_files": ["quikridr.csv"], "required": False},
}

# CLM-001 deprecated alias → REF-003
RULE_ALIASES = {"CLM-001": "REF-003"}

US_STATE_CODES = frozenset({
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
    "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT",
    "VA", "WA", "WV", "WI", "WY", "DC", "PR", "VI", "GU", "AS", "MP", "00",
})

VALID_MSTATUS_CODES = frozenset({
    "10", "11", "12", "22", "32", "41", "42", "44", "45", "50", "53", "54", "55", "56", "57", "90",
})

GOVERNANCE_LEAK_COLUMNS = frozenset({
    "governance_status", "business_review_required", "rollback_snapshot_id",
    "reconstructed_claim_id", "prototype_claimnum", "derivation_candidate_id",
    "blocker_category", "rulebook_lineage", "uat_segment", "replay_source",
    "audit_timestamp", "emit_timestamp", "governance_hold_reason",
})

LOAN_TRANSACTION_CODES = frozenset({
    "412", "413", "411", "0411", "0412", "0413", "0451", "414", "415", "416", "417", "451",
})

DEFAULT_CONFIG_DIR_NAME = "validation_config"
REPORT_SUBDIR = "validation_reports"


def default_config_dir(repo_root: str) -> str:
    return os.path.join(repo_root, DEFAULT_CONFIG_DIR_NAME)


def load_json_config(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_all_configs(config_dir: str) -> dict[str, Any]:
    cfg: dict[str, Any] = {}
    for name in ("schema_manifest.json", "critical_fields.json", "date_fields.json", "key_definitions.json"):
        path = os.path.join(config_dir, name)
        key = name.replace(".json", "").replace("schema_manifest", "schema")
        if os.path.isfile(path):
            cfg[key] = load_json_config(path)
    priority_path = os.path.join(config_dir, "priority_rules.json")
    if os.path.isfile(priority_path):
        cfg["priority"] = load_json_config(priority_path)
    return cfg


def rule_meta(rule_id: str) -> dict[str, str]:
    canonical = RULE_ALIASES.get(rule_id, rule_id)
    return RULE_META.get(canonical, {
        "rule_name": canonical,
        "severity": "High",
        "disposition": "Hold",
    })


def known_rule_ids() -> list[str]:
    return sorted(RULE_META.keys())


def resolve_rule_files(
    rule_id: str,
    output_dir: str,
    source_dir: str | None,
    repo_root: str,
) -> tuple[list[str], list[str], list[str], bool]:
    """Return (expected, found, missing, required)."""
    deps = RULE_FILE_DEPS.get(rule_id, {})
    expected: list[str] = []
    found: list[str] = []
    missing: list[str] = []
    required = deps.get("required", True)

    def _check(path: str, label: str) -> None:
        expected.append(label)
        if os.path.isfile(path):
            found.append(label)
        else:
            missing.append(label)

    for fname in deps.get("output_files", []):
        _check(os.path.join(output_dir, fname), fname)
    if source_dir:
        for fname in deps.get("source_files", []):
            _check(os.path.join(source_dir, fname), f"source/{fname}")
    for rel in deps.get("config_files", []):
        _check(os.path.join(repo_root, rel.replace("/", os.sep)), rel)
    for rel in deps.get("staging_files", []):
        _check(os.path.join(repo_root, rel.replace("/", os.sep)), rel)
    if deps.get("crosswalk"):
        cw_found = False
        for rel in ("QLA_Migration/Mapping/Master_Crosswalk.csv", "Master_Crosswalk.csv"):
            p = os.path.join(repo_root, rel.replace("/", os.sep))
            expected.append(rel)
            if os.path.isfile(p):
                found.append(rel)
                cw_found = True
            else:
                missing.append(rel)
        if not cw_found:
            required = False
    return expected, found, missing, required
