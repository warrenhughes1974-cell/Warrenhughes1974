"""
LifePRO-native source file resolution for QLA_Migration batch conversion.

When changing TABLE_SOURCE_SPECS, update docs/LIFEPRO_SOURCE_FILES.txt to match.
"""
from __future__ import annotations

import os
import re
from typing import Iterable, List, Optional, Tuple

_EXCLUDE_SUBSTRINGS = ("copy", "old", "backup", "archive")

# table_id -> resolution spec
# lifepro_patterns: regex matched against filename (newest mtime wins)
# legacy_names: project/interim filenames (rollback-safe fallback)
TABLE_SOURCE_SPECS = {
    "quikmstr": {
        "lifepro_table": "PPOLC",
        "lifepro_label": "Policy Master",
        "lifepro_patterns": [r"^PPOLC[_ ]PolicyMaster[_ ]Extract.*\.csv$"],
        "legacy_names": ["quikmstr.csv"],
        "required": True,
        "converts_to": "quikmstr",
    },
    "quikridr": {
        "lifepro_table": "PPBEN",
        "lifepro_label": "Policy Benefit / Riders",
        "lifepro_patterns": [r"^PPBEN[_ ]PolicyBenefit[_ ]Extract.*\.csv$"],
        "legacy_names": ["PPBEN.csv"],
        "required": True,
        "converts_to": "quikridr",
    },
    "quikdvdp": {
        "lifepro_table": "PPBENTYP",
        "lifepro_label": "Benefit Type",
        "lifepro_patterns": [r"^PPBENTYP[_ ]BenefitType[_ ]Extract.*\.csv$"],
        "legacy_names": ["PPBENTYP.csv"],
        "required": True,
        "converts_to": "quikdvdp",
    },
    "quikclnt": {
        "lifepro_table": "PRELSA / RNA",
        "lifepro_label": "Relationship Name Address",
        "lifepro_patterns": [r"^RelationshipNameAddress[_ ]Extract.*\.csv$"],
        "legacy_names": ["quikclnt.csv", "RelationshipNameAddress_Extract.csv"],
        "required": True,
        "converts_to": "quikclnt",
    },
    "quikclid": {
        "lifepro_table": "PRELSA / RNA",
        "lifepro_label": "Relationship Name Address",
        "lifepro_patterns": [r"^RelationshipNameAddress[_ ]Extract.*\.csv$"],
        "legacy_names": ["quikclid.csv", "RelationshipNameAddress_Extract.csv"],
        "required": True,
        "converts_to": "quikclid",
    },
    "quikbenf": {
        "lifepro_table": "PRELSA / RNA",
        "lifepro_label": "Relationship Name Address",
        "lifepro_patterns": [r"^RelationshipNameAddress[_ ]Extract.*\.csv$"],
        "legacy_names": ["quikbenf.csv", "RelationshipNameAddress_Extract.csv"],
        "required": True,
        "converts_to": "quikbenf",
    },
    "quikplan": {
        "lifepro_table": "PCOVR",
        "lifepro_label": "Coverage / Plan Setup",
        "lifepro_patterns": [r"^PCOVR[_ ]Coverage[_ ]Extract.*\.csv$"],
        "legacy_names": ["quikplan_source.csv", "quikplan.csv"],
        "required": True,
        "converts_to": "quikplan",
    },
    "quikprmh": {
        "lifepro_table": "PACTG",
        "lifepro_label": "Accounting Transactions",
        "lifepro_patterns": [r"^PACTG[_ ]Accounting[_ ]Extract.*\.csv$"],
        "legacy_names": ["PACTG_Accounting_Extract20260427.csv"],
        "required": True,
        "converts_to": "quikprmh",
    },
    "quikdvpr": {
        "lifepro_table": "PACTG",
        "lifepro_label": "Accounting Transactions",
        "lifepro_patterns": [r"^PACTG[_ ]Accounting[_ ]Extract.*\.csv$"],
        "legacy_names": ["PACTG_Accounting_Extract20260427.csv"],
        "required": True,
        "converts_to": "quikdvpr",
    },
    "quikactg": {
        "lifepro_table": "PACTG",
        "lifepro_label": "Accounting Transactions",
        "lifepro_patterns": [r"^PACTG[_ ]Accounting[_ ]Extract.*\.csv$"],
        "legacy_names": ["PACTG_Accounting_Extract20260427.csv"],
        "required": True,
        "converts_to": "quikactg",
    },
    "quikloan": {
        "lifepro_table": "PLOAN",
        "lifepro_label": "Loan Information",
        "lifepro_patterns": [r"^PLOAN[_ ]LoanInformation[_ ]Extract.*\.csv$"],
        "legacy_names": ["PLOAN.csv"],
        "required": False,
        "converts_to": "quikloan",
    },
    "quikagts": {
        "lifepro_table": "PAGNT",
        "lifepro_label": "Agent Master",
        "lifepro_patterns": [
            r"^PAGNT[_ ]AgentMaster[_ ]Extract.*\.csv$",
            r"^PROD[_ ]PAGNT[_ ]AgentMaster[_ ]Extract.*\.csv$",
        ],
        "legacy_names": ["PAGNT.csv"],
        "required": True,
        "converts_to": "quikagts",
    },
    "quikmemo": {
        "lifepro_table": "PNOTE + PENSE",
        "lifepro_label": "Policy Notes + ENS Messages",
        "lifepro_patterns": [r"^PNOTE[_ ]PolicyNotes[_ ]Extract.*\.csv$"],
        "legacy_names": ["PNOTE.csv"],
        "required": False,
        "converts_to": "quikmemo",
    },
}

# Dual-source memo inputs (Issue 21M)
MEMO_SOURCE_SPECS = {
    "pnote": {
        "lifepro_table": "PNOTE",
        "lifepro_label": "Policy Notes",
        "lifepro_patterns": [
            r"^PNOTE[_ ]PolicyNotes[_ ]Extract.*\.csv$",
            r"^PNOTE\.csv$",
        ],
        "legacy_names": ["PNOTE.csv"],
    },
    "pense": {
        "lifepro_table": "PENSE",
        "lifepro_label": "ENS Data",
        "lifepro_patterns": [
            r"^PENSE[_ ]ENSData[_ ]Extract.*\.csv$",
            r"^PENSE\.csv$",
        ],
        "legacy_names": ["PENSE.csv"],
    },
}

# Enrichment files loaded during quikmstr (not standalone table conversions)
ENRICHMENT_SOURCE_SPECS = {
    "ppach_banking": {
        "lifepro_table": "PPACH",
        "lifepro_label": "PAC / Banking History",
        "lifepro_patterns": [r"^PPACH[_ ]PACHistory[_ ]Extract.*\.csv$"],
        "legacy_names": ["PPACH.csv"],
        "required": True,
        "used_for": "quikmstr banking (MBANKNO / MACCTNO)",
    },
    "ppbentyp_nfo_div": {
        "lifepro_table": "PPBENTYP",
        "lifepro_label": "Benefit Type",
        "lifepro_patterns": [r"^PPBENTYP[_ ]BenefitType[_ ]Extract.*\.csv$"],
        "legacy_names": ["PPBENTYP.csv"],
        "required": True,
        "used_for": "quikmstr NFO/dividend option enrichment",
    },
    "aba_routing_lookup": {
        "lifepro_table": "(derived)",
        "lifepro_label": "ABA routing lookup",
        "lifepro_patterns": [r"^aba[_ ]routing[_ ]lookup\.csv$"],
        "legacy_names": ["aba_routing_lookup.csv"],
        "required": True,
        "used_for": "quikmstr full 9-digit ABA (Issue 21H; built from PPCOM, not LifePRO direct)",
    },
}


def _is_excluded_filename(filename: str) -> bool:
    lower = filename.lower()
    return any(bad in lower for bad in _EXCLUDE_SUBSTRINGS)


def _list_csv_files(src_dir: str) -> List[str]:
    if not src_dir or not os.path.isdir(src_dir):
        return []
    return [
        f for f in os.listdir(src_dir)
        if f.lower().endswith(".csv") and os.path.isfile(os.path.join(src_dir, f))
    ]


def find_newest_matching(src_dir: str, patterns: Iterable[str]) -> str:
    """Return newest file in src_dir matching any regex pattern (filename only)."""
    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
    matches: List[str] = []
    for filename in _list_csv_files(src_dir):
        if _is_excluded_filename(filename):
            continue
        if any(p.search(filename) for p in compiled):
            matches.append(os.path.normpath(os.path.join(src_dir, filename)))
    if not matches:
        return ""
    return max(matches, key=os.path.getmtime)


def find_by_keyword(src_dir: str, keyword: str) -> str:
    """Legacy keyword scan (ppach, ppbentyp, aba_routing_lookup, pactg, ...)."""
    key = keyword.lower().replace(" ", "_")
    key_flat = key.replace("_", "")
    matches: List[str] = []
    for filename in _list_csv_files(src_dir):
        if _is_excluded_filename(filename):
            continue
        f_lower = filename.lower()
        if key in f_lower or key_flat in f_lower.replace("_", ""):
            matches.append(os.path.normpath(os.path.join(src_dir, filename)))
    if not matches:
        return ""
    return max(matches, key=os.path.getmtime)


def resolve_enrichment_source(src_dir: str, enrichment_key: str) -> Tuple[str, str]:
    """Return (path, resolution_label) for enrichment key."""
    spec = ENRICHMENT_SOURCE_SPECS.get(enrichment_key, {})
    if not spec:
        path = find_by_keyword(src_dir, enrichment_key)
        return path, f"keyword:{enrichment_key}" if path else ""

    path = find_newest_matching(src_dir, spec.get("lifepro_patterns", []))
    if path:
        return path, f"lifepro:{os.path.basename(path)}"
    for legacy in spec.get("legacy_names", []):
        candidate = os.path.normpath(os.path.join(src_dir, legacy))
        if os.path.isfile(candidate):
            return candidate, f"legacy:{legacy}"
    return "", ""


def resolve_memo_source(src_dir: str, memo_key: str) -> Tuple[str, str]:
    """Resolve PNOTE or PENSE source CSV for quikmemo conversion."""
    spec = MEMO_SOURCE_SPECS.get(str(memo_key or "").strip().lower(), {})
    if not spec:
        return "", ""
    path = find_newest_matching(src_dir, spec.get("lifepro_patterns", []))
    if path:
        return path, f"lifepro:{os.path.basename(path)}"
    for legacy in spec.get("legacy_names", []):
        candidate = os.path.normpath(os.path.join(src_dir, legacy))
        if os.path.isfile(candidate):
            return candidate, f"legacy:{legacy}"
    return "", ""


def resolve_quikmemo_sources(src_dir: str) -> Tuple[str, str, str, str]:
    """Return (pnote_path, pnote_label, pense_path, pense_label)."""
    pnote_path, pnote_label = resolve_memo_source(src_dir, "pnote")
    pense_path, pense_label = resolve_memo_source(src_dir, "pense")
    return pnote_path, pnote_label, pense_path, pense_label


def resolve_table_source(src_dir: str, table_id: str) -> Tuple[str, str]:
    """
    Resolve source CSV for a QLA table id.
    Returns (absolute_path, resolution_label). path empty if not found.
    Prefers LifePRO extract filenames; falls back to legacy/project names.
    """
    table = str(table_id or "").strip().lower()
    spec = TABLE_SOURCE_SPECS.get(table)
    if not spec:
        legacy = f"{table}.csv"
        candidate = os.path.normpath(os.path.join(src_dir, legacy))
        if os.path.isfile(candidate):
            return candidate, f"legacy:{legacy}"
        return "", ""

    path = find_newest_matching(src_dir, spec.get("lifepro_patterns", []))
    if path:
        return path, f"lifepro:{os.path.basename(path)}"

    for legacy in spec.get("legacy_names", []):
        candidate = os.path.normpath(os.path.join(src_dir, legacy))
        if os.path.isfile(candidate):
            return candidate, f"legacy:{legacy}"

    return "", ""


def expected_legacy_filename(table_id: str) -> str:
    """Human-readable primary legacy name (for UI hints only)."""
    table = str(table_id or "").strip().lower()
    spec = TABLE_SOURCE_SPECS.get(table)
    if spec and spec.get("legacy_names"):
        return spec["legacy_names"][0]
    return f"{table}.csv"
