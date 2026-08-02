#!/usr/bin/env python3
"""Issue #135 — read-only CSO Total_Paid vs Output / PACTG reverse-engineering recon.

Hard-control rules (locked):
  - CSO has no claim number; control is policy-level Total_Paid only.
  - Do NOT sum death claims with PS/surrender/shell rows.
  - ~459 CSO policies absent from Output are Eric-supply gaps, not conversion failures.
  - Do not force-fit unexplained residuals.

Outputs land under Issue_Log_Items/Issue_135/evidence/ (not QLA_Migration/Output).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.normalize_utils import format_qladmin_mpolicy  # noqa: E402

DEFAULT_CSO = ROOT / "docs" / "Claims" / "CSO Life claims summary - 2017 - 2025.xlsx"
DEFAULT_CLMS = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
DEFAULT_CLMP = ROOT / "QLA_Migration" / "Output" / "quikclmp.csv"
DEFAULT_OUT = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
TOLERANCE = 0.01

TEACHER_DEATH = [
    "9011156098C",
    "9010914301C",
    "9010391359C",
    "9010150740C",
    "9010402010C",
    "9010429064C",
    "9010430296C",
]
SURRENDER_EXAMPLES = [
    "9010360289C",
    "9010753675C",
    "9010429711C",
    "9010746846C",
]

# Heuristic GL classifiers for proposed-rule labeling (evidence-backed, not force-fit).
CODE_CLASS = {
    "0094": "payout_death_claim_payment",
    "0090": "payout_related",
    "0560": "partial_surrender",
    "0561": "partial_surrender",
    "0567": "surrender_related",
    "0630": "interest_death_benefit",
    "0412": "loan_interest_capitalized",
    "0451": "loan_unearned_interest_income",
    "0310": "dividend_on_deposit",
    "0641": "dividend_interest",
}
ACCOUNT_CLASS = {
    "1058": "payout_cash_death_claim",
    "2032": "clearing_death",
    "2023": "div_on_deposit_interest_exclude",
    "1017": "loan_principal_interest",
    "7046": "loan_interest_income",
    "1015": "reinstatement_endow_loop",
    "2031": "reinstatement_clearing",
    "2019": "unapplied_intraco",
    "2039": "reinstatement_related",
}
CREDIT_CODE_CLASS = {
    "6001": "funding_death_benefit",
    "6037": "div_deposit_interest_exclude",
    "6038": "interest_on_death_benefit",
    "6044": "reinstatement_related",
}


def _strip(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _money(v) -> float:
    s = _strip(v).replace(",", "").replace("$", "")
    if not s or s.lower() in ("nan", "none"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _norm_code(v) -> str:
    digits = re.sub(r"[^0-9]", "", _strip(v))
    if not digits:
        return ""
    return str(int(digits)).zfill(4)


def _norm_account(v) -> str:
    s = _strip(v)
    digits = re.sub(r"[^0-9]", "", s)
    if not digits:
        return s.upper()
    # Keep leading account family (e.g. 1058 from 1058000256)
    return digits


def _account_family(v) -> str:
    digits = re.sub(r"[^0-9]", "", _strip(v))
    return digits[:4] if len(digits) >= 4 else digits


def _policy_digits(v) -> str:
    return re.sub(r"[^0-9]", "", _strip(v))


def resolve_pactg(explicit: str | None = None) -> Path:
    if explicit:
        p = Path(explicit)
        if p.is_file():
            return p
    env = __import__("os").environ.get("QLA_CLAIMS_PACTG_PATH", "").strip()
    if env and Path(env).is_file():
        return Path(env)
    candidates = [
        ROOT / "QLA_Migration" / "Source" / "PACTG_Accounting_Extract20260630.csv",
        ROOT / "QLA_Migration" / "Source" / "PACTG_Accounting_Extract20260427.csv",
        ROOT / "docs" / "claims_conversion_reference" / "PACTG_Accounting_Extract20260427.csv",
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError("PACTG extract not found")


def load_cso(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    need = {"Policy", "Total_Paid"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"CSO workbook missing columns: {sorted(missing)}")
    rows = []
    for _, r in df.iterrows():
        pol_raw = _strip(r.get("Policy", ""))
        if not pol_raw:
            continue
        mpolicy = format_qladmin_mpolicy(pol_raw)
        rows.append(
            {
                "cso_policy_raw": pol_raw,
                "mpolicy": mpolicy,
                "policy_digits": _policy_digits(pol_raw),
                "cso_total_paid": round(_money(r.get("Total_Paid")), 2),
                "cso_plan_code": _strip(r.get("Plan_code", "")),
                "cso_notice_date": _strip(r.get("Notice_date", "")),
                "cso_date_incurred": _strip(r.get("Date_Incurred", "")),
                "cso_last_pd_date": _strip(r.get("Last_Pd_Date", "")),
            }
        )
    out = pd.DataFrame(rows)
    # CSO is policy-level hard control — one control row per policy.
    out = out.drop_duplicates(subset=["mpolicy"], keep="first")
    return out


def classify_claim_row(row: pd.Series) -> str:
    """Distinguish death vs PS/surrender/shell at quikclms row grain."""
    memo = _strip(row.get("MEMOTEXT", "")).upper()
    claimstat = _strip(row.get("CLAIMSTAT", ""))
    claimnum = _strip(row.get("CLAIMNUM", ""))
    if "PARTIAL_SURRENDER" in memo or claimnum.upper().startswith("PS-"):
        return "PARTIAL_SURRENDER"
    if "SURRENDER_CLAIM" in memo or claimstat in ("99", "98"):
        if "DISBURSEMENT" in memo:
            return "DISBURSEMENT"
        if claimstat == "98" or "MATURITY" in memo:
            return "MATURITY_OR_98"
        return "SURRENDER"
    if "DISBURSEMENT_CLAIM" in memo:
        return "DISBURSEMENT"
    if "DEATH_CLAIM" in memo or claimstat in ("1", "2"):
        return "DEATH_CLAIM"
    if not claimstat and not memo:
        return "SHELL_OR_BLANK"
    return "OTHER"


def is_reversed_date(reversed_dt: str) -> bool:
    """PACTG DATE_REVERSED uses 0 / blank for not-reversed; real dates when reversed."""
    s = _strip(reversed_dt)
    if not s:
        return False
    if s in {"0", "0.0", "00", "00000000", "0/0/0", "00/00/0000"}:
        return False
    # Numeric zero variants
    try:
        if float(s.replace(",", "")) == 0.0:
            return False
    except ValueError:
        pass
    return True


def classify_pactg_row(dr_code: str, cr_code: str, dr_acct: str, cr_acct: str, reversed_dt: str) -> str:
    if is_reversed_date(reversed_dt):
        return "reversal"
    for code in (dr_code, cr_code):
        if code in CODE_CLASS:
            return CODE_CLASS[code]
    for code in (dr_code, cr_code):
        prefix3 = code[:3] if len(code) >= 3 else code
        # credit revenue style 6001 / 6037 / 6038 / 6044 often 4-digit with trailing nuance
        for key, label in CREDIT_CODE_CLASS.items():
            if code.startswith(key) or prefix3 == key[:3] and code.startswith(key[:3]):
                # more precise: startswith key
                if code.startswith(key):
                    return label
    for acct in (_account_family(dr_acct), _account_family(cr_acct)):
        if acct in ACCOUNT_CLASS:
            return ACCOUNT_CLASS[acct]
    # Intra-company / unapplied long account forms
    if "1058000256" in (_norm_account(dr_acct), _norm_account(cr_acct)):
        return "unapplied_intraco"
    if _account_family(dr_acct) == "2019" or _account_family(cr_acct) == "2019":
        return "unapplied_intraco"
    return "unclassified"


def load_output_claims(clms_path: Path, clmp_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    clms = pd.read_csv(clms_path, dtype=str, keep_default_na=False)
    clmp = (
        pd.read_csv(clmp_path, dtype=str, keep_default_na=False)
        if clmp_path.is_file()
        else pd.DataFrame()
    )
    clms["_family"] = clms.apply(classify_claim_row, axis=1)
    clms["_mpaid_n"] = clms["MPAID"].map(_money) if "MPAID" in clms.columns else 0.0
    clms["_mintamt_n"] = clms["MINTAMT"].map(_money) if "MINTAMT" in clms.columns else 0.0
    payee_sum: dict[str, float] = defaultdict(float)
    payee_n: dict[str, int] = defaultdict(int)
    if not clmp.empty and {"MPOLICY", "MAMOUNT"}.issubset(clmp.columns):
        for _, r in clmp.iterrows():
            pol = _strip(r.get("MPOLICY", ""))
            payee_sum[pol] += _money(r.get("MAMOUNT"))
            payee_n[pol] += 1
    return clms, clmp, {"payee_sum": payee_sum, "payee_n": payee_n}


def stream_pactg_for_policies(pactg_path: Path, policy_digits: set[str]) -> dict[str, list[dict]]:
    """Stream PACTG once; collect rows for requested policy digits."""
    buckets: dict[str, list[dict]] = defaultdict(list)
    if not policy_digits:
        return buckets
    csv.field_size_limit(10**7)
    with open(pactg_path, newline="", encoding="latin-1") as fh:
        reader = csv.reader(fh)
        header = [c.replace("\ufeff", "").strip().upper() for c in next(reader)]
        # Header may have trailing spaces in source — normalize keys already stripped.
        idx = {name: i for i, name in enumerate(header)}

        def col(*names: str) -> int | None:
            for n in names:
                if n in idx:
                    return idx[n]
            # fuzzy: strip spaces from header keys
            for n in names:
                for k, i in idx.items():
                    if k.replace(" ", "") == n.replace(" ", ""):
                        return i
            return None

        i_pol = col("POLICY_NUMBER")
        i_dr = col("DEBIT_CODE")
        i_cr = col("CREDIT_CODE")
        i_dra = col("DEBIT_ACCOUNT")
        i_cra = col("CREDIT_ACCOUNT")
        i_amt = col("TRANS_AMOUNT")
        i_eff = col("EFFECTIVE_DATE")
        i_rev = col("DATE_REVERSED")
        i_rcode = col("REVERSAL_CODE")
        if i_pol is None or i_amt is None:
            raise ValueError("PACTG missing POLICY_NUMBER / TRANS_AMOUNT")

        for raw in reader:
            if len(raw) <= i_pol:
                continue
            dig = _policy_digits(raw[i_pol])
            if dig not in policy_digits:
                continue
            dr = _norm_code(raw[i_dr] if i_dr is not None else "")
            cr = _norm_code(raw[i_cr] if i_cr is not None else "")
            dra = _strip(raw[i_dra] if i_dra is not None else "")
            cra = _strip(raw[i_cra] if i_cra is not None else "")
            rev = _strip(raw[i_rev] if i_rev is not None else "")
            amt = _money(raw[i_amt])
            layer = classify_pactg_row(dr, cr, dra, cra, rev)
            buckets[dig].append(
                {
                    "policy_digits": dig,
                    "effective_date": _strip(raw[i_eff] if i_eff is not None else ""),
                    "debit_code": dr,
                    "credit_code": cr,
                    "debit_account": dra,
                    "credit_account": cra,
                    "trans_amount": round(amt, 2),
                    "date_reversed": rev,
                    "reversal_code": _strip(raw[i_rcode] if i_rcode is not None else ""),
                    "layer_class": layer,
                }
            )
    return buckets


def propose_rule_from_residual(
    cso_paid: float,
    death_mpaid: float,
    payee_sum: float,
    layer_totals: dict[str, float],
) -> tuple[str, str]:
    """Propose a rule classification without inventing a forced match."""
    residual = round(cso_paid - death_mpaid, 2)
    if abs(residual) <= TOLERANCE:
        return "MATCH_CSO", "Death MPAID equals CSO Total_Paid within tolerance"
    # Multiple of CSO (reinstatement / duplicate)
    if cso_paid > 0 and death_mpaid > 0:
        ratio = death_mpaid / cso_paid
        if abs(ratio - 3.0) <= 0.02:
            return "REINSTATEMENT_TRIPLE_COUNT", "MPAID ≈ 3× CSO Total_Paid"
        if abs(ratio - 2.0) <= 0.02:
            return "DUPLICATE_PAYOUT", "MPAID ≈ 2× CSO Total_Paid"
    if abs(death_mpaid) <= TOLERANCE and cso_paid > 0:
        # Prefer economic payout evidence (often credit 0094 -> 1058) over loan-only label.
        if (
            layer_totals.get("payout_death_claim_payment", 0)
            or layer_totals.get("payout_cash_death_claim", 0)
            or layer_totals.get("payout_related", 0)
        ):
            return (
                "MISSING_DEATH_MPAID_BUT_PACTG_PAYOUT",
                "CSO paid > 0 but death MPAID=0; open PACTG 0094/1058 payout exists",
            )
        if layer_totals.get("loan_principal_interest", 0) or layer_totals.get("loan_interest_capitalized", 0):
            return "MISSING_LOAN_DEATH_PAYOUT", "CSO paid > 0 but death MPAID=0; loan layers present"
        return "MISSING_DEATH_MPAID", "CSO paid > 0 but death MPAID=0"
    if abs(payee_sum - death_mpaid) > TOLERANCE and abs(payee_sum - cso_paid) <= TOLERANCE:
        return "HEADER_PAYEE_MISALIGN", "Payee sum matches CSO but header MPAID does not"
    if abs(payee_sum - death_mpaid) > TOLERANCE:
        return "HEADER_PAYEE_MISALIGN", "Death MPAID and economic payee sum disagree"
    if layer_totals.get("div_deposit_interest_exclude", 0) or layer_totals.get("div_on_deposit_interest_exclude", 0):
        return "DIV_DEPOSIT_INTEREST_REVIEW", "Div-on-deposit interest layers present; residual unexplained"
    if layer_totals.get("interest_death_benefit", 0) or layer_totals.get("interest_on_death_benefit", 0):
        return "INTEREST_IN_CHECK_REVIEW", "Death-benefit interest layers present; keep out of MINTAMT"
    if layer_totals.get("unapplied_intraco", 0) or layer_totals.get("reinstatement_endow_loop", 0):
        return "INTRACO_OR_REINSTATE_REVIEW", "Intra-co / reinstatement layers present with residual"
    return "UNEXPLAINED_RESIDUAL", "Residual not force-fit; hold pending PACTG rule proof"


def build_policy_recon(
    cso: pd.DataFrame,
    clms: pd.DataFrame,
    payee_meta: dict,
    pactg_buckets: dict[str, list[dict]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    death = clms[clms["_family"] == "DEATH_CLAIM"].copy()
    non_death = clms[clms["_family"] != "DEATH_CLAIM"].copy()

    empty_death = pd.DataFrame(
        columns=["mpolicy", "death_rows", "death_mpaid", "death_mintamt", "death_claimstats", "death_claimnums"]
    )
    empty_non = pd.DataFrame(
        columns=["mpolicy", "non_death_rows", "non_death_families", "non_death_mpaid_sum"]
    )
    if death.empty:
        death_by_pol = empty_death
    else:
        death_by_pol = (
            death.groupby(death["MPOLICY"].map(_strip))
            .agg(
                death_rows=("MPOLICY", "count"),
                death_mpaid=("_mpaid_n", "sum"),
                death_mintamt=("_mintamt_n", "sum"),
                death_claimstats=(
                    "CLAIMSTAT",
                    lambda s: "|".join(sorted(set(_strip(x) for x in s if _strip(x)))),
                ),
                death_claimnums=(
                    "CLAIMNUM",
                    lambda s: "|".join(sorted(set(_strip(x) for x in s if _strip(x)))[:5]),
                ),
            )
            .reset_index()
            .rename(columns={"MPOLICY": "mpolicy"})
        )

    if non_death.empty:
        non_death_by_pol = empty_non
    else:
        non_death_by_pol = (
            non_death.groupby(non_death["MPOLICY"].map(_strip))
            .agg(
                non_death_rows=("MPOLICY", "count"),
                non_death_families=(
                    "_family",
                    lambda s: "|".join(sorted(set(_strip(x) for x in s if _strip(x)))),
                ),
                non_death_mpaid_sum=("_mpaid_n", "sum"),
            )
            .reset_index()
            .rename(columns={"MPOLICY": "mpolicy"})
        )

    payee_sum = payee_meta["payee_sum"]
    payee_n = payee_meta["payee_n"]

    recon_rows = []
    layer_rows = []
    for _, c in cso.iterrows():
        pol = c["mpolicy"]
        dig = c["policy_digits"]
        drow = death_by_pol[death_by_pol["mpolicy"] == pol]
        nrow = non_death_by_pol[non_death_by_pol["mpolicy"] == pol]
        in_output_any = bool(len(clms[clms["MPOLICY"].map(_strip) == pol]))
        in_death = not drow.empty
        death_mpaid = round(float(drow["death_mpaid"].iloc[0]), 2) if in_death else 0.0
        death_mintamt = round(float(drow["death_mintamt"].iloc[0]), 2) if in_death else 0.0
        death_rows = int(drow["death_rows"].iloc[0]) if in_death else 0
        psum = round(float(payee_sum.get(pol, 0.0)), 2)
        pn = int(payee_n.get(pol, 0))
        cso_paid = float(c["cso_total_paid"])
        residual = round(cso_paid - death_mpaid, 2)

        pactg_rows = pactg_buckets.get(dig, [])
        layer_totals: dict[str, float] = defaultdict(float)
        for pr in pactg_rows:
            layer_totals[pr["layer_class"]] += abs(float(pr["trans_amount"]))
            layer_rows.append(
                {
                    "mpolicy": pol,
                    "population": "",  # filled later
                    **pr,
                }
            )

        if not in_output_any:
            pop = "MISSING_ERIC_SUPPLY"
            rule, note = "ERIC_POLICY_GAP", "Absent from current Output; Eric has not supplied all policies yet — not a conversion failure"
        elif not in_death:
            pop = "IN_OUTPUT_NO_DEATH_HEADER"
            rule, note = "NO_DEATH_CLAIM_ROW", "Policy in Output but no DEATH_CLAIM/CLAIMSTAT 1|2 header; do not use PS/surrender amounts"
        elif abs(residual) <= TOLERANCE:
            pop = "AVAILABLE_MATCH"
            rule, note = propose_rule_from_residual(cso_paid, death_mpaid, psum, dict(layer_totals))
        else:
            pop = "AVAILABLE_MISMATCH"
            rule, note = propose_rule_from_residual(cso_paid, death_mpaid, psum, dict(layer_totals))

        is_teacher = pol in TEACHER_DEATH
        recon_rows.append(
            {
                "mpolicy": pol,
                "policy_digits": dig,
                "population": pop,
                "is_teacher_death": "Y" if is_teacher else "N",
                "cso_total_paid": cso_paid,
                "death_mpaid": death_mpaid,
                "death_mintamt": death_mintamt,
                "death_rows": death_rows,
                "death_claimstats": (drow["death_claimstats"].iloc[0] if in_death else ""),
                "payee_sum_mamount": psum,
                "payee_rows": pn,
                "residual_cso_minus_death_mpaid": residual,
                "payee_minus_death_mpaid": round(psum - death_mpaid, 2),
                "non_death_rows": int(nrow["non_death_rows"].iloc[0]) if not nrow.empty else 0,
                "non_death_families": (nrow["non_death_families"].iloc[0] if not nrow.empty else ""),
                "non_death_mpaid_sum_DO_NOT_ADD_TO_CSO": (
                    round(float(nrow["non_death_mpaid_sum"].iloc[0]), 2) if not nrow.empty else 0.0
                ),
                "pactg_row_count": len(pactg_rows),
                "pactg_layer_totals_json": json.dumps(dict(sorted((k, round(v, 2)) for k, v in layer_totals.items()))),
                "proposed_rule_class": rule,
                "proposed_rule_note": note,
                "cso_plan_code": c["cso_plan_code"],
                "cso_last_pd_date": c["cso_last_pd_date"],
            }
        )

    recon = pd.DataFrame(recon_rows)
    # Fill population on layer rows
    pop_map = dict(zip(recon["mpolicy"], recon["population"]))
    for lr in layer_rows:
        lr["population"] = pop_map.get(lr["mpolicy"], "")
    layers = pd.DataFrame(layer_rows)

    # Surrender examples (separate from CSO death hard control)
    surr_rows = []
    for pol in SURRENDER_EXAMPLES:
        sub = clms[clms["MPOLICY"].map(_strip) == pol]
        if sub.empty:
            surr_rows.append(
                {
                    "mpolicy": pol,
                    "in_output": "N",
                    "families": "",
                    "row_count": 0,
                    "mpaid_sum_all_families": 0.0,
                    "note": "Not in current Output",
                }
            )
            continue
        surr_rows.append(
            {
                "mpolicy": pol,
                "in_output": "Y",
                "families": "|".join(sorted(set(sub["_family"].tolist()))),
                "row_count": int(len(sub)),
                "mpaid_sum_all_families": round(float(sub["_mpaid_n"].sum()), 2),
                "claimstats": "|".join(sorted(set(sub["CLAIMSTAT"].map(_strip)))),
                "note": "Surrender workstream — not CSO Total_Paid hard control; do not sum with death",
            }
        )
    surrender = pd.DataFrame(surr_rows)
    return recon, layers, surrender


def write_markdown(
    path: Path,
    summary: dict,
    recon: pd.DataFrame,
    surrender: pd.DataFrame,
) -> None:
    teachers = recon[recon["is_teacher_death"] == "Y"].copy()
    lines = [
        "# Issue #135 — CSO × Output × PACTG Reconciliation",
        "",
        f"Generated: {summary.get('generated_at', '')}",
        "",
        "## Hard-control statements",
        "",
        "- CSO has **no claim number**; `Total_Paid` is a **policy-level** hard control.",
        "- Do **not** sum death-claim amounts with PS / surrender / shell rows.",
        "- Policies in `MISSING_ERIC_SUPPLY` are absent because Eric has not supplied all policies yet — **not** a current conversion failure.",
        "- Unexplained residuals are held as `UNEXPLAINED_RESIDUAL` — **not** force-fit to CSO.",
        "",
        "## Population summary (available ~1,100 vs Eric gaps)",
        "",
        f"| Bucket | Count |",
        f"|---|---:|",
        f"| CSO death policies (control) | {summary['cso_policies']} |",
        f"| AVAILABLE_MATCH | {summary['available_match']} |",
        f"| AVAILABLE_MISMATCH | {summary['available_mismatch']} |",
        f"| IN_OUTPUT_NO_DEATH_HEADER | {summary['in_output_no_death']} |",
        f"| MISSING_ERIC_SUPPLY | {summary['missing_eric_supply']} |",
        f"| Available represented (match+mismatch+no-death) | {summary['available_represented']} |",
        "",
        f"PACTG path: `{summary.get('pactg_path', '')}`",
        f"Output clms: `{summary.get('clms_path', '')}`",
        "",
        "## Teacher death cases",
        "",
        "| Policy | CSO Total_Paid | Death MPAID | Residual | Proposed rule |",
        "|---|---:|---:|---:|---|",
    ]
    for _, r in teachers.iterrows():
        lines.append(
            f"| {r['mpolicy']} | {r['cso_total_paid']:.2f} | {r['death_mpaid']:.2f} | "
            f"{r['residual_cso_minus_death_mpaid']:.2f} | {r['proposed_rule_class']} |"
        )
    lines.extend(
        [
            "",
            "## Surrender examples (separate workstream)",
            "",
            "| Policy | In Output | Families | MPAID sum (all families) | Note |",
            "|---|---|---|---:|---|",
        ]
    )
    for _, r in surrender.iterrows():
        lines.append(
            f"| {r['mpolicy']} | {r['in_output']} | {r.get('families', '')} | "
            f"{float(r['mpaid_sum_all_families']):.2f} | {r['note']} |"
        )
    lines.extend(
        [
            "",
            "## Proposed rule class counts (available mismatch only)",
            "",
        ]
    )
    mism = recon[recon["population"] == "AVAILABLE_MISMATCH"]
    if mism.empty:
        lines.append("_No available mismatches._")
    else:
        vc = mism["proposed_rule_class"].value_counts()
        lines.append("| Rule class | Count |")
        lines.append("|---|---:|")
        for k, v in vc.items():
            lines.append(f"| {k} | {int(v)} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #135 CSO/Output/PACTG recon (read-only)")
    ap.add_argument("--cso", default=str(DEFAULT_CSO))
    ap.add_argument("--clms", default=str(DEFAULT_CLMS))
    ap.add_argument("--clmp", default=str(DEFAULT_CLMP))
    ap.add_argument("--pactg", default="")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument(
        "--pactg-scope",
        choices=["teachers_plus_mismatch", "available", "all_cso"],
        default="available",
        help="Which CSO policies to pull PACTG detail for (default: all available in Output)",
    )
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    cso = load_cso(Path(args.cso))
    clms, _clmp, payee_meta = load_output_claims(Path(args.clms), Path(args.clmp))
    pactg_path = resolve_pactg(args.pactg or None)

    # First pass without PACTG to decide scope, then stream PACTG.
    recon_seed, _, surrender = build_policy_recon(cso, clms, payee_meta, {})
    if args.pactg_scope == "teachers_plus_mismatch":
        scope = set(
            recon_seed.loc[
                (recon_seed["is_teacher_death"] == "Y")
                | (recon_seed["population"] == "AVAILABLE_MISMATCH"),
                "policy_digits",
            ]
        )
        for pol in SURRENDER_EXAMPLES:
            scope.add(_policy_digits(pol))
    elif args.pactg_scope == "available":
        scope = set(
            recon_seed.loc[
                recon_seed["population"].isin(
                    ["AVAILABLE_MATCH", "AVAILABLE_MISMATCH", "IN_OUTPUT_NO_DEATH_HEADER"]
                ),
                "policy_digits",
            ]
        )
        for pol in TEACHER_DEATH + SURRENDER_EXAMPLES:
            scope.add(_policy_digits(pol))
    else:
        scope = set(recon_seed["policy_digits"])

    print(f"Streaming PACTG for {len(scope)} policies from {pactg_path} ...")
    pactg_buckets = stream_pactg_for_policies(pactg_path, scope)
    recon, layers, surrender = build_policy_recon(cso, clms, payee_meta, pactg_buckets)

    summary = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "issue": 135,
        "hard_control": "CSO Total_Paid is policy-level; no claim number; do not sum death+PS",
        "eric_gap_note": (
            "MISSING_ERIC_SUPPLY policies are absent because Eric has not supplied all "
            "policies yet; not treated as current conversion failure"
        ),
        "cso_path": str(Path(args.cso)),
        "clms_path": str(Path(args.clms)),
        "clmp_path": str(Path(args.clmp)),
        "pactg_path": str(pactg_path),
        "pactg_scope": args.pactg_scope,
        "pactg_policies_pulled": len(scope),
        "cso_policies": int(len(recon)),
        "available_match": int((recon["population"] == "AVAILABLE_MATCH").sum()),
        "available_mismatch": int((recon["population"] == "AVAILABLE_MISMATCH").sum()),
        "in_output_no_death": int((recon["population"] == "IN_OUTPUT_NO_DEATH_HEADER").sum()),
        "missing_eric_supply": int((recon["population"] == "MISSING_ERIC_SUPPLY").sum()),
        "available_represented": int(
            recon["population"]
            .isin(["AVAILABLE_MATCH", "AVAILABLE_MISMATCH", "IN_OUTPUT_NO_DEATH_HEADER"])
            .sum()
        ),
        "teacher_death": TEACHER_DEATH,
        "surrender_examples": SURRENDER_EXAMPLES,
        "proposed_rule_counts_mismatch": Counter(
            recon.loc[recon["population"] == "AVAILABLE_MISMATCH", "proposed_rule_class"]
        ),
        "mintamt_nonzero_death_rows": int(
            ((clms["_family"] == "DEATH_CLAIM") & (clms["_mintamt_n"].abs() > TOLERANCE)).sum()
        ),
    }
    # JSON-serialize Counter
    summary["proposed_rule_counts_mismatch"] = dict(summary["proposed_rule_counts_mismatch"])

    recon_path = out_dir / "issue135_cso_output_recon.csv"
    layers_path = out_dir / "issue135_pactg_layer_detail.csv"
    surr_path = out_dir / "issue135_surrender_examples.csv"
    teachers_path = out_dir / "issue135_teacher_cases.csv"
    summary_path = out_dir / "issue135_recon_summary.json"
    md_path = out_dir / "issue135_recon_report.md"

    recon.to_csv(recon_path, index=False, encoding="utf-8")
    # Limit layer file size: teachers + mismatches + surrender always; matches sample
    keep_pols = set(recon.loc[recon["is_teacher_death"] == "Y", "mpolicy"])
    keep_pols |= set(recon.loc[recon["population"] == "AVAILABLE_MISMATCH", "mpolicy"])
    keep_pols |= set(SURRENDER_EXAMPLES)
    match_sample = (
        recon.loc[recon["population"] == "AVAILABLE_MATCH", "mpolicy"].head(25).tolist()
    )
    keep_pols |= set(match_sample)
    if not layers.empty:
        layers_out = layers[layers["mpolicy"].isin(keep_pols)].copy()
    else:
        layers_out = layers
    layers_out.to_csv(layers_path, index=False, encoding="utf-8")
    surrender.to_csv(surr_path, index=False, encoding="utf-8")
    recon[recon["is_teacher_death"] == "Y"].to_csv(teachers_path, index=False, encoding="utf-8")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(md_path, summary, recon, surrender)

    print(json.dumps({k: summary[k] for k in (
        "cso_policies", "available_match", "available_mismatch",
        "in_output_no_death", "missing_eric_supply", "available_represented",
        "pactg_policies_pulled",
    )}, indent=2))
    print(f"Wrote {recon_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
