"""Citizens plan crosswalk + segmentation helpers (standalone CFIC pipeline)."""
from __future__ import annotations

import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[3]  # CFIC_Rates
CROSSWALK = ROOT / "Citizens_Plan_Crosswak.xlsx"

# PermaLife / PermaLife8 style: P7MN, P8FS, etc.
_P_GENDER_SMOKER = re.compile(r"^P\d([MF])([NS])$", re.I)
# Term / other 4-char codes with trailing gender+smoker: Q1MN, RW8G is different
_GENDER_SMOKER_SUFFIX = re.compile(r"^.{2}([MF])([NS])$", re.I)


def load_crosswalk() -> dict[str, dict]:
    wb = openpyxl.load_workbook(CROSSWALK, data_only=True)
    ws = wb.active
    lookup: dict[str, dict] = {}
    for lob, plan, suffix, ql in ws.iter_rows(min_row=2, values_only=True):
        if plan is None:
            continue
        group = str(plan).strip()
        ql_raw = "" if ql is None else str(ql).strip()
        lob_s = "" if lob is None else str(lob).strip()
        suffix_s = "" if suffix is None else str(suffix)
        for token in re.split(r",\s*", group):
            token = token.strip().upper()
            if token:
                lookup[token] = {
                    "cfic_plan_group": group,
                    "ql_plan_all": ql_raw,
                    "lob": lob_s,
                    "suffix": suffix_s,
                }
    return lookup


def resolve_ql_plan(code: str, lookup: dict[str, dict] | None = None) -> tuple[str, bool]:
    """
    Return (ql_plan C6 token, in_crosswalk).

    Prefer exact token 10{CFIC} when listed in crosswalk (e.g. 10P7MN).
    When crosswalk lists multiple CFIC codes under one QL plan (e.g. CP05/10/20 -> 10CP05),
    only the code that suffix-matches the single QL token uses it; others get 10{CFIC}.
    """
    lookup = lookup or load_crosswalk()
    code_u = code.strip().upper()
    default = f"10{code_u}"[:6].ljust(6)
    hit = lookup.get(code_u)
    if not hit:
        return default, False
    ql_all = hit["ql_plan_all"]
    if not ql_all:
        return default, True
    parts = [p.strip() for p in ql_all.split(",") if p.strip()]
    exact = f"10{code_u}"
    for part in parts:
        if part.upper() == exact:
            return part[:6].ljust(6), True
    if len(parts) == 1:
        only = parts[0].upper()
        if only.endswith(code_u):
            return parts[0][:6].ljust(6), True
    return default, True


def decode_segmentation(cfic_plan: str, plan_desc: str = "") -> tuple[str, str, str]:
    """
    Derive (GENDER, UWCLASS, BAND) from CFIC plan code / Plans description.
    Reserve file encodes sex/smoker in plan code; no face-amount band -> BAND 00.
    """
    code = cfic_plan.strip().upper()
    m = _P_GENDER_SMOKER.match(code) or _GENDER_SMOKER_SUFFIX.match(code)
    if m:
        gender = m.group(1).upper()
        uw = "NS" if m.group(2).upper() == "N" else "SM"
        return gender, uw, "00"

    desc = (plan_desc or "").upper()
    gender = "0"
    if " MALE" in desc or desc.endswith("MALE"):
        gender = "M"
    elif " FEMALE" in desc or desc.endswith("FEMALE"):
        gender = "F"
    uw = "00"
    if re.search(r"\b7S\b|\b8S\b|SMOKER", desc):
        uw = "SM"
    elif re.search(r"\b7N\b|\b8N\b|NON", desc):
        uw = "NS"
    return gender, uw, "00"
