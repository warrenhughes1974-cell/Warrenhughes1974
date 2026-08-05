"""Issue #120 — QuikList group bill master emit (active six groups only).

Populates quiklist.csv from PPOLC active LST groups + RNA GP name/address rows
joined via IDENTIFYING_ALPHA = COMPANY_CODE + POLICY_NUMBER.
"""
from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import Any

import pandas as pd

from qla_core.lifepro_source_resolver import resolve_table_source
from qla_core.schema_constants import QUIKLIST_SCHEMA

# Approved active-six scope (Issue #120).
ACTIVE_QUIKLIST_GROUPS = frozenset({"03494L", "05624L", "07132", "07777L", "T8342L", "Z2583L"})

# Terminated-only LST groups excluded from emit — DG-QUIKMSTR-015 waiver scope.
TERMINATED_ORPHAN_GROUPS = frozenset({"02698", "04403", "04498", "04965", "05947L", "09447"})

QUIKLIST_MCOMP = "C"
QUIKLIST_DEFAULT_MSORT = "N"
QUIKLIST_DEFAULT_MLAPSEL = 0
QUIKLIST_DEFAULT_MLAPSEH = 0
QUIKLIST_DEFAULT_MSTATUS = "A"
QUIKLIST_DEFAULT_MBILLDAY = 0
QUIKLIST_DEFAULT_MBILLMODE = 0

# Help §7.149 length caps.
_LEN_MGROUP = 8
_LEN_MCOMP = 1
_LEN_MBILLNAME = 30
_LEN_ADDR = 25
_LEN_STATE = 2
_LEN_ZIP5 = 5
_LEN_ZIP4 = 4
_LEN_MPHONE = 15


def _norm(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _field(row: dict[str, Any], name: str) -> str:
    if name in row:
        return _norm(row[name])
    target = name.strip()
    for key, val in row.items():
        if str(key).strip() == target:
            return _norm(val)
    return ""


def _left(value: str, limit: int) -> str:
    text = _norm(value)
    return text[:limit] if limit > 0 else text


def _real_policy_number(row: dict[str, Any]) -> bool:
    pol = _field(row, "POLICY_NUMBER")
    return bool(pol) and not set(pol) <= {"-", " "}


def _repair_shifted_address(city: str, state: str, zip5: str) -> tuple[str, str, str]:
    """07132-style repair: STATE holds city token, ZIP holds state abbr."""
    city = _norm(city)
    state = _norm(state)
    zip5 = _norm(zip5)
    if len(state) != 2 and len(zip5) == 2 and zip5.isalpha():
        city = state
        state = zip5.upper()
        zip5 = ""
    return city, state, zip5


def _split_zip(zip_raw: str, zip_ext_raw: str) -> tuple[str, str]:
    zip_raw = _norm(zip_raw)
    zip_ext = _norm(zip_ext_raw)
    if not zip_ext and len(zip_raw) > 5 and zip_raw.isdigit():
        return zip_raw[:5], zip_raw[5:9]
    return _left(zip_raw, _LEN_ZIP5), _left(zip_ext, _LEN_ZIP4)


def _address_score(
    addr1: str,
    addr2: str,
    city: str,
    state: str,
    zip5: str,
    address_code: str,
    status_code: str,
) -> tuple[int, tuple[str, str, str, str, str]]:
    city, state, zip5 = _repair_shifted_address(city, state, zip5)
    score = 0
    addr_code = _norm(address_code).upper()
    status = _norm(status_code).upper()
    if addr_code != "OTH":
        score += 4
    if addr1 and "@" not in addr1:
        score += 4
    elif addr1 and "@" in addr1:
        score -= 10
    if not addr1:
        score -= 5
    if len(state) == 2:
        score += 3
    if zip5 and zip5.isdigit():
        score += 3
    if city:
        score += 2
    if status == "A":
        score += 1
    tie = (addr1, addr2, city, state, zip5)
    return score, tie


def _pick_gp_name(rows: list[dict[str, Any]]) -> str:
    names: set[str] = set()
    for row in rows:
        name = _field(row, "NAME_BUSINESS") or _field(row, "KEY_NAME")
        if name:
            names.add(name)
    if len(names) == 1:
        return next(iter(names))
    if names:
        return sorted(names)[0]
    return ""


def _pick_gp_address(rows: list[dict[str, Any]]) -> dict[str, str]:
    best_score = None
    best_fields: dict[str, str] | None = None
    for row in rows:
        addr1 = _field(row, "ADDR_LINE_1")
        addr2 = _field(row, "ADDR_LINE_2")
        city = _field(row, "CITY")
        state = _field(row, "STATE")
        zip5 = _field(row, "ZIP")
        zip_ext = _field(row, "ZIP_EXTENSION")
        score, tie = _address_score(
            addr1,
            addr2,
            city,
            state,
            zip5,
            _field(row, "ADDRESS_CODE"),
            _field(row, "STATUS_CODE"),
        )
        city, state, zip5 = _repair_shifted_address(city, state, zip5)
        zip5, zip4 = _split_zip(zip5, zip_ext)
        candidate = {
            "MBILLADDR1": _left(addr1, _LEN_ADDR),
            "MBILLADDR2": _left(addr2, _LEN_ADDR),
            "MBILLCITY": _left(city, _LEN_ADDR),
            "MBILLST": _left(state, _LEN_STATE),
            "MBILLZIP": zip5,
            "MBILLZIP2": zip4,
        }
        sort_key = (score, tie)
        if best_score is None or sort_key > best_score:
            best_score = sort_key
            best_fields = candidate
    return best_fields or {
        "MBILLADDR1": "",
        "MBILLADDR2": "",
        "MBILLCITY": "",
        "MBILLST": "",
        "MBILLZIP": "",
        "MBILLZIP2": "",
    }


def _blank_quiklist_row(mgroup: str) -> dict[str, Any]:
    row: dict[str, Any] = {field: "" for field in QUIKLIST_SCHEMA}
    row["MGROUP"] = _left(mgroup, _LEN_MGROUP)
    row["MCOMP"] = QUIKLIST_MCOMP
    row["MSORT"] = QUIKLIST_DEFAULT_MSORT
    row["MLAPSEL"] = QUIKLIST_DEFAULT_MLAPSEL
    row["MLAPSEH"] = QUIKLIST_DEFAULT_MLAPSEH
    row["MSTATUS"] = QUIKLIST_DEFAULT_MSTATUS
    row["MBILLDAY"] = QUIKLIST_DEFAULT_MBILLDAY
    row["MBILLMODE"] = QUIKLIST_DEFAULT_MBILLMODE
    return row


def _build_quiklist_row(mgroup: str, gp_rows: list[dict[str, Any]]) -> dict[str, Any]:
    row = _blank_quiklist_row(mgroup)
    name = _pick_gp_name(gp_rows)
    row["MBILLNAME"] = _left(name, _LEN_MBILLNAME)
    row.update(_pick_gp_address(gp_rows))
    phone = ""
    for gp in gp_rows:
        tele = _field(gp, "TELE_NUM")
        if tele and tele not in ("0000000000", "0"):
            phone = tele
            break
    row["MPHONE"] = _left(phone, _LEN_MPHONE)
    return row


def _load_csv_rows(path: str) -> list[dict[str, Any]]:
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def build_quiklist_rows(source_dir: str) -> list[dict[str, Any]]:
    """Build ordered QuikList rows for the approved active-six groups."""
    ppolc_path, _ = resolve_table_source(source_dir, "quikmstr")
    rna_path, _ = resolve_table_source(source_dir, "quikclnt")
    if not ppolc_path or not os.path.isfile(ppolc_path):
        raise FileNotFoundError(f"PPOLC extract not found under {source_dir}")
    if not rna_path or not os.path.isfile(rna_path):
        raise FileNotFoundError(f"RelationshipNameAddress extract not found under {source_dir}")

    ppolc_rows = [r for r in _load_csv_rows(ppolc_path) if _real_policy_number(r)]
    active_lst = [
        r
        for r in ppolc_rows
        if _field(r, "BILLING_FORM").upper() == "LST"
        and _field(r, "CONTRACT_CODE").upper() == "A"
    ]

    group_policies: dict[str, list[str]] = {g: [] for g in sorted(ACTIVE_QUIKLIST_GROUPS)}
    pol_meta: dict[str, tuple[str, str]] = {}
    for row in active_lst:
        group = _field(row, "GROUP_NUMBER")
        if group not in ACTIVE_QUIKLIST_GROUPS:
            continue
        pol = _field(row, "POLICY_NUMBER")
        if not pol:
            continue
        pol_meta[pol] = (_field(row, "COMPANY_CODE") or "03", group)
        if pol not in group_policies[group]:
            group_policies[group].append(pol)

    gp_rows = [r for r in _load_csv_rows(rna_path) if _field(r, "RELATE_CODE").upper() == "GP"]
    gp_by_alpha: dict[str, list[dict[str, Any]]] = {}
    for row in gp_rows:
        alpha = _field(row, "IDENTIFYING_ALPHA")
        if alpha:
            gp_by_alpha.setdefault(alpha, []).append(row)

    rows: list[dict[str, Any]] = []
    for group in sorted(ACTIVE_QUIKLIST_GROUPS):
        hits: list[dict[str, Any]] = []
        for pol in group_policies.get(group, []):
            co, _ = pol_meta.get(pol, ("03", group))
            alpha = f"{co}{pol}"
            hits.extend(gp_by_alpha.get(alpha, []))
        rows.append(_build_quiklist_row(group, hits))
    return rows


def emit_quiklist_csv(source_dir: str, output_dir: str) -> dict[str, Any]:
    """Write quiklist.csv to output_dir. Returns path/stats dict."""
    rows = build_quiklist_rows(source_dir)
    df = pd.DataFrame(rows, columns=QUIKLIST_SCHEMA)
    out_path = os.path.normpath(os.path.join(output_dir, "quiklist.csv"))
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(out_path, index=False)
    return {
        "path": out_path,
        "row_count": len(rows),
        "groups": [r["MGROUP"] for r in rows],
        "terminated_orphan_waiver_groups": sorted(TERMINATED_ORPHAN_GROUPS),
        "emitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
