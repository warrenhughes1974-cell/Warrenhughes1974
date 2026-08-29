"""Issue #142 — emit Active SL rows as 9SUBLF (zero VPU, keep units/premium).

Issue #27 still suppresses non-active SL rows. Warren override 2026-08-29
narrows that blanket so Active STATUS_CODE=A rows emit.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd

from qla_core.schema_constants import QUIKPLAN_SCHEMA
from qla_core.sl_benefit_governance import is_active_sl_status

ISSUE142_PLAN = "9SUBLF"
ISSUE142_DESCR = "SUBSTANDARD LIFE PREMIUM RIDER"
ISSUE142_PRODUCT = "70"

EMIT_AUDIT_COLUMNS = [
    "POLICY_NUMBER",
    "QLA_POLICY_NUMBER",
    "BENEFIT_SEQ",
    "SOURCE_PLAN",
    "NUMBER_OF_UNITS",
    "ANN_PREM_PER_UNIT",
    "MODE_PREMIUM",
    "EMIT_PLAN",
    "EMIT_VPU",
]


def default_emit_audit_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    return root / "Issue_Log_Items" / "Issue_142" / "evidence" / "issue142_sl_emit_audit.csv"


def sl_active_mask(source: pd.DataFrame, sl_mask: pd.Series) -> pd.Series:
    if "STATUS_CODE" not in source.columns:
        return pd.Series(False, index=source.index)
    status = source["STATUS_CODE"].astype(str).str.strip().str.upper()
    return sl_mask & status.map(is_active_sl_status)


def prepare_active_sl_for_emit(source: pd.DataFrame, active_mask: pd.Series) -> pd.DataFrame:
    """Route Active SL rows to 9SUBLF and zero VPU so insured amount is not duplicated."""
    if source is None or source.empty or not bool(active_mask.any()):
        return source
    out = source.copy()
    out.loc[active_mask, "PLAN_CODE"] = ISSUE142_PLAN
    if "VALUE_PER_UNIT" in out.columns:
        out.loc[active_mask, "VALUE_PER_UNIT"] = "0"
    return out


def build_emit_audit_rows(
    sl_source: pd.DataFrame,
    *,
    cw_map: dict[str, str] | None = None,
    normalize_fn: Callable[[str], str] | None = None,
) -> list[dict[str, str]]:
    if sl_source is None or sl_source.empty:
        return []
    norm = normalize_fn or (lambda x: str(x).strip())
    cw = cw_map or {}
    rows: list[dict[str, str]] = []
    for _, r in sl_source.iterrows():
        lp = norm(r.get("POLICY_NUMBER", ""))
        rows.append(
            {
                "POLICY_NUMBER": lp,
                "QLA_POLICY_NUMBER": cw.get(lp, lp),
                "BENEFIT_SEQ": str(r.get("BENEFIT_SEQ", "")).strip().replace(".0", ""),
                "SOURCE_PLAN": str(r.get("PLAN_CODE", "")).strip(),
                "NUMBER_OF_UNITS": str(r.get("NUMBER_OF_UNITS", "")).strip(),
                "ANN_PREM_PER_UNIT": str(r.get("ANN_PREM_PER_UNIT", "")).strip(),
                "MODE_PREMIUM": str(r.get("MODE_PREMIUM", "")).strip(),
                "EMIT_PLAN": ISSUE142_PLAN,
                "EMIT_VPU": "0",
            }
        )
    return rows


def write_emit_audit(
    audit_rows: list[dict[str, str]],
    audit_path: Path | str | None = None,
) -> str:
    path = Path(audit_path) if audit_path else default_emit_audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(audit_rows, columns=EMIT_AUDIT_COLUMNS)
    df.to_csv(path, index=False, encoding="latin1")
    return str(path.resolve())


def build_9sublf_plan_row(schema: list[str] | None = None) -> dict[str, str]:
    schema = schema or list(QUIKPLAN_SCHEMA)
    row = {h: "" for h in schema}
    values = {
        "PLAN": ISSUE142_PLAN,
        "DESCR": ISSUE142_DESCR,
        "PLANNAME": ISSUE142_DESCR,
        "PAR": "0",
        "VARDB": "0",
        # Issue A7: 4 = no rate table on file. 9SUBLF emits no QuikGps grid
        # (rider premium rides on quikridr MPREM), unlike 9SLADB/9FTRWP (code 3).
        "VARGP": "4",
        "LOAGE": "00",
        "HIAGE": "100",
        "RENEW": "N",
        "PAYYRS": "100",
        "PAYAGE": "00",
        "INSYRS": "100",
        "INSAGE": "00",
        "ANNL": "100.0000",
        "SEMI": "50.0000",
        "QTRL": "25.0000",
        "MTHD": "8.3333",
        "MTHB": "8.3333",
        "ANNLFEE": "0.0000",
        "SEMIFEE": "0.0000",
        "QTRLFEE": "0.0000",
        "MTHDFEE": "0.0000",
        "MTHBFEE": "0.0000",
        "INITVAL": "0.00",
        "PRODUCT": ISSUE142_PRODUCT,
        "CALCADV": "N",
        "MINUNIT": "0",
        "MAXUNIT": "99",
        "BACTIVE": "N",
        "RRULE": "B",
        "LOANINT": "0.00",
        "LOANINTX": "A",
        "DEPINT": "0.00",
        "AGTRSV": "0.00",
        "AUTONFO": "0",
        "INTMETHCV": "A",
        "DEFICIENCY": "N",
        "PLANVALOPT": "N",
        "HCOMMIP": "F",
        "HRIGPKEY": "F",
        "MNAICLOB": "NAPLAN",
        "MLAPSE": "0",
    }
    vary_dims = ("GDVARY", "UWVARY", "BDVARY", "STVARY")
    vary_fams = ("GP", "DB", "CV", "TV", "DV")
    for dim in vary_dims:
        for fam in vary_fams:
            values[f"{dim}{fam}"] = "N"
    for key, val in values.items():
        if key in row:
            row[key] = val
    return row


def seed_9sublf_plan(df: pd.DataFrame, log=None) -> pd.DataFrame:
    """Append 9SUBLF once when missing. Idempotent."""
    if df is None or df.empty or "PLAN" not in df.columns:
        return df
    plans = df["PLAN"].astype(str).str.strip().str.upper()
    if (plans == ISSUE142_PLAN).any():
        return df
    schema = list(df.columns) if len(df.columns) else list(QUIKPLAN_SCHEMA)
    row = build_9sublf_plan_row(schema)
    out = pd.concat([df, pd.DataFrame([row], columns=schema)], ignore_index=True)
    if log is not None:
        try:
            log(f"Issue #142: seeded quikplan {ISSUE142_PLAN}")
        except Exception:
            pass
    return out
