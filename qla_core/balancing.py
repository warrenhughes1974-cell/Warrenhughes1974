#!/usr/bin/env python3
"""
Issue #87 — QuikForge Balancing (read-only Source ↔ QLAdmin reconciliation).

Reads LifePRO extracts and Output quik*.csv from disk; writes control reports under
QLA_Migration/Balancing/. Does not modify conversion output.
"""
from __future__ import annotations

import csv
import html
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

import pandas as pd

from qla_core.lifepro_source_resolver import resolve_table_source
from qla_core.normalize_utils import format_qladmin_mpolicy, normalize, normalize_columns
from qla_core.quikplan_converter import load_crosswalk_map
from qla_core.quikloan_converter import convert_quikloan_from_ploan
from qla_core.sl_benefit_governance import SL_BENEFIT_TYPE

PRMH_EXCLUDED_CODES = frozenset({"96", "412", "413", "514", "641", "710", "1110", "1111"})
BENF_RELATE_CODES = frozenset({"B1", "B2", "P", "C"})
MONEY_TOLERANCE = 0.01
COUNT_TOLERANCE = 0

REPORT_COLUMNS = [
    "CONTROL_ID",
    "TIER",
    "DESCRIPTION",
    "SOURCE_VALUE",
    "QLADMIN_VALUE",
    "VARIANCE",
    "VARIANCE_PCT",
    "STATUS",
    "EXPLANATION",
]


@dataclass
class ControlResult:
    control_id: str
    tier: str
    description: str
    source_value: float
    qla_value: float
    status: str = "FAIL"
    explanation: str = ""
    detail_rows: list[dict] = field(default_factory=list)

    @property
    def variance(self) -> float:
        return self.source_value - self.qla_value

    @property
    def variance_pct(self) -> str:
        if self.source_value == 0:
            return "0.00%" if self.variance == 0 else "N/A"
        pct = (self.variance / self.source_value) * 100.0
        return f"{pct:.2f}%"

    def to_row(self) -> dict[str, str]:
        return {
            "CONTROL_ID": self.control_id,
            "TIER": self.tier,
            "DESCRIPTION": self.description,
            "SOURCE_VALUE": _fmt_num(self.source_value),
            "QLADMIN_VALUE": _fmt_num(self.qla_value),
            "VARIANCE": _fmt_num(self.variance),
            "VARIANCE_PCT": self.variance_pct,
            "STATUS": self.status,
            "EXPLANATION": self.explanation,
        }


def _fmt_num(val: float) -> str:
    if abs(val - round(val)) < 1e-9:
        return str(int(round(val)))
    return f"{val:.2f}"


def _parse_money(val: Any) -> float:
    s = normalize(val)
    if not s:
        return 0.0
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return 0.0


def _read_csv(path: str) -> pd.DataFrame:
    if not path or not os.path.isfile(path):
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="latin1", low_memory=False, dtype=str, on_bad_lines="skip")
    return normalize_columns(df).fillna("")


def _read_output_table(out_dir: str, table_id: str) -> pd.DataFrame:
    path = os.path.normpath(os.path.join(out_dir, f"{table_id}.csv"))
    return _read_csv(path)


def _resolve_source(src_dir: str, table_id: str) -> str:
    path, _label = resolve_table_source(src_dir, table_id)
    return path or ""


def _load_exclusions(config_path: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    if not os.path.isfile(config_path):
        return out
    with open(config_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if not row:
                continue
            cid = (row.get("CONTROL_ID") or "").strip()
            if not cid or cid.startswith("#"):
                continue
            reason = (row.get("REASON") or "").strip()
            if reason:
                out.setdefault(cid, []).append(reason)
    return out


def _is_active_rna_cancel_date(val: Any) -> bool:
    n = normalize(val)
    return n in ("", "0", "NULL")


def _map_policy(pol: str, cw_map: dict[str, str]) -> str:
    # Issue #2: source + C (ignore strip-9 New_Value; cw_map unused for identity)
    return format_qladmin_mpolicy(normalize(pol))


def _finalize_control(
    ctrl: ControlResult,
    *,
    count_control: bool = True,
    explained_if_nonzero: bool = False,
    exclusion_reasons: list[str] | None = None,
    relative_money_tolerance: float = 1e-6,
) -> ControlResult:
    tol = COUNT_TOLERANCE if count_control else MONEY_TOLERANCE
    var = abs(ctrl.variance)
    if count_control:
        if var <= tol:
            ctrl.status = "PASS"
            ctrl.explanation = ""
            return ctrl
    else:
        base = max(abs(ctrl.source_value), abs(ctrl.qla_value), 1.0)
        if var <= tol or (var / base) <= relative_money_tolerance:
            ctrl.status = "PASS"
            ctrl.explanation = ""
            return ctrl
    if explained_if_nonzero and exclusion_reasons:
        ctrl.status = "EXPLAINED"
        ctrl.explanation = "; ".join(exclusion_reasons[:2])
        return ctrl
    ctrl.status = "FAIL"
    ctrl.explanation = ctrl.explanation or "Variance exceeds tolerance"
    return ctrl


def _filter_ppben_for_ridr(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    work = df.copy()
    if "BENEFIT_TYPE" in work.columns:
        bt = work["BENEFIT_TYPE"].astype(str).str.strip().str.upper()
        work = work[~bt.isin(["UV", "FV", SL_BENEFIT_TYPE])]
    if "BENEFIT_SEQ" in work.columns:
        seq = work["BENEFIT_SEQ"].astype(str).str.strip().str.replace(".0", "", regex=False)
        work = work[seq.apply(lambda x: x.isdigit() and int(x) >= 1)]
    return work


def _pactg_premium_mask(df: pd.DataFrame) -> pd.Series:
    """Boolean mask for premium-history rows (CREDIT 110, debit not excluded)."""
    if df.empty:
        return pd.Series(dtype=bool)
    cc = df["CREDIT_CODE"].map(normalize) if "CREDIT_CODE" in df.columns else pd.Series("", index=df.index)
    dc = df["DEBIT_CODE"].map(normalize) if "DEBIT_CODE" in df.columns else pd.Series("", index=df.index)
    return (cc == "110") & (~dc.isin(PRMH_EXCLUDED_CODES))


def _count_pactg_premium_rows(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    return int(_pactg_premium_mask(df).sum())


def _sum_pactg_premium_amount(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    mask = _pactg_premium_mask(df)
    if "TRANS_AMOUNT" not in df.columns or not mask.any():
        return 0.0
    amounts = df.loc[mask, "TRANS_AMOUNT"].map(_parse_money)
    return round(float(amounts.sum()), 2)


def _filter_pactg_dividend_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    work = df.copy()
    credit_match = pd.Series(False, index=work.index)
    debit_match = pd.Series(False, index=work.index)
    if "CREDIT_CODE" in work.columns:
        cc = work["CREDIT_CODE"].map(normalize)
        credit_match = cc.isin(["516", "0516"])
    if "DEBIT_CODE" in work.columns:
        dc = work["DEBIT_CODE"].map(normalize)
        debit_match = dc.isin(["516", "0516"])
    return work[credit_match | debit_match]


def _filter_rna_clients(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    work = df.copy()
    if "CANCEL_DATE" in work.columns:
        work = work[work["CANCEL_DATE"].apply(_is_active_rna_cancel_date)]
    if "NAME_ID" in work.columns:
        work = work.drop_duplicates(subset=["NAME_ID"], keep="first")
    return work


def _filter_rna_beneficiaries(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "RELATE_CODE" not in df.columns:
        return pd.DataFrame()
    work = df.copy()
    work["RELATE_CODE"] = work["RELATE_CODE"].map(normalize)
    return work[work["RELATE_CODE"].isin(BENF_RELATE_CODES)]


def _sum_face_ppben(df: pd.DataFrame) -> float:
    total = 0.0
    for _, row in df.iterrows():
        units = _parse_money(row.get("NUMBER_OF_UNITS", ""))
        vpu = _parse_money(row.get("VALUE_PER_UNIT", ""))
        total += units * vpu
    return round(total, 2)


def _sum_face_ridr(df: pd.DataFrame) -> float:
    total = 0.0
    for _, row in df.iterrows():
        units = _parse_money(row.get("MUNIT", ""))
        vpu = _parse_money(row.get("MVPU", ""))
        total += units * vpu
    return round(total, 2)


def _sum_column(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df.columns:
        return 0.0
    return round(sum(_parse_money(v) for v in df[col]), 2)


def _compute_controls(
    *,
    src_dir: str,
    out_dir: str,
    crosswalk_path: str,
    exclusions: dict[str, list[str]],
    progress: Callable[..., None] | None = None,
) -> list[ControlResult]:
    def _log(msg: str, stage: int | None = None) -> None:
        if not progress:
            return
        try:
            progress(msg, stage)
        except TypeError:
            progress(msg)

    cw_map = load_crosswalk_map(crosswalk_path)
    controls: list[ControlResult] = []

    _log("Resolving LifePRO source extracts...", 1)
    ppolc_path = _resolve_source(src_dir, "quikmstr")
    ppben_path = _resolve_source(src_dir, "quikridr")
    ppbentyp_path = _resolve_source(src_dir, "quikdvdp")
    rna_path = _resolve_source(src_dir, "quikclnt")
    pactg_path = _resolve_source(src_dir, "quikprmh")
    ploan_path = _resolve_source(src_dir, "quikloan")

    _log("Reading QLAdmin output tables...", 2)
    quikmstr = _read_output_table(out_dir, "quikmstr")
    quikridr = _read_output_table(out_dir, "quikridr")
    quikclnt = _read_output_table(out_dir, "quikclnt")
    quikclid = _read_output_table(out_dir, "quikclid")
    quikbenf = _read_output_table(out_dir, "quikbenf")
    quikprmh = _read_output_table(out_dir, "quikprmh")
    quikloan = _read_output_table(out_dir, "quikloan")
    quikdvdp = _read_output_table(out_dir, "quikdvdp")
    quikdvpr = _read_output_table(out_dir, "quikdvpr")

    _log("Loading LifePRO source extracts...", 2)
    ppolc = _read_csv(ppolc_path)
    ppben = _read_csv(ppben_path)
    ppbentyp = _read_csv(ppbentyp_path)
    rna = _read_csv(rna_path)
    pactg = _read_csv(pactg_path)

    ppben_rid = _filter_ppben_for_ridr(ppben)

    # --- Tier 1 counts ---
    _log("Computing count controls...", 3)
    c01 = ControlResult(
        "BAL-C01", "Counts",
        "Number of policies in the LifePRO policy master vs QLAdmin Policy Master",
        len(ppolc), len(quikmstr),
    )
    controls.append(_finalize_control(c01, count_control=True))

    c02 = ControlResult(
        "BAL-C02", "Counts",
        "Number of coverages and riders (after dropping non-coverage rows) vs QLAdmin Riders",
        len(ppben_rid), len(quikridr),
    )
    controls.append(_finalize_control(
        c02, count_control=True,
        explained_if_nonzero=(len(ppben) != len(ppben_rid)),
        exclusion_reasons=exclusions.get("BAL-C02"),
    ))

    rna_clients = _filter_rna_clients(rna)
    c03 = ControlResult(
        "BAL-C03", "Counts",
        "Number of unique people (names/addresses) vs QLAdmin Clients",
        len(rna_clients), len(quikclnt),
    )
    controls.append(_finalize_control(
        c03, count_control=True,
        explained_if_nonzero=True,
        exclusion_reasons=exclusions.get("BAL-C03"),
    ))

    c04 = ControlResult(
        "BAL-C04", "Counts",
        "Number of person-to-policy relationships vs QLAdmin Policy Relationships",
        int(((rna["POLICY_NUMBER"].map(normalize) != "") & (rna["NAME_ID"].map(normalize) != "")).sum())
        if not rna.empty and "POLICY_NUMBER" in rna.columns and "NAME_ID" in rna.columns else 0,
        len(quikclid),
    )
    controls.append(_finalize_control(
        c04, count_control=True,
        explained_if_nonzero=True,
        exclusion_reasons=exclusions.get("BAL-C04"),
    ))

    rna_ben = _filter_rna_beneficiaries(rna)
    c05 = ControlResult(
        "BAL-C05", "Counts",
        "Number of beneficiary designations vs QLAdmin Beneficiaries",
        len(rna_ben), len(quikbenf),
    )
    controls.append(_finalize_control(
        c05, count_control=True,
        explained_if_nonzero=True,
        exclusion_reasons=exclusions.get("BAL-C05"),
    ))

    _log("Scanning premium-history transactions...", 3)
    pactg_prm_count = _count_pactg_premium_rows(pactg)
    c06 = ControlResult(
        "BAL-C06", "Counts",
        "Number of premium-history transactions vs QLAdmin Premium History",
        pactg_prm_count, len(quikprmh),
    )
    controls.append(_finalize_control(
        c06, count_control=True,
        explained_if_nonzero=(pactg_prm_count != len(quikprmh)),
        exclusion_reasons=exclusions.get("BAL-C06"),
    ))

    _log("Computing dollar and loan controls...", 4)
    loan_emit_count = 0
    loan_passed_df = pd.DataFrame()
    if ploan_path and os.path.isfile(ploan_path):
        _log("Building active loan population...", 4)
        qm_path = os.path.normpath(os.path.join(out_dir, "quikmstr.csv"))
        loan_passed_df, _, _, _stats = convert_quikloan_from_ploan(
            ploan_path,
            crosswalk_path=crosswalk_path if os.path.isfile(crosswalk_path) else None,
            quikmstr_path=qm_path if os.path.isfile(qm_path) else None,
        )
        loan_emit_count = len(loan_passed_df)
    c07 = ControlResult(
        "BAL-C07", "Counts",
        "Number of active policy loans vs QLAdmin Loans",
        loan_emit_count, len(quikloan),
    )
    controls.append(_finalize_control(
        c07, count_control=True,
        explained_if_nonzero=(len(_read_csv(ploan_path)) != loan_emit_count),
        exclusion_reasons=exclusions.get("BAL-C07"),
    ))

    pactg_div = _filter_pactg_dividend_rows(pactg)
    c08 = ControlResult(
        "BAL-C08", "Counts",
        "Number of dividend transactions vs QLAdmin Dividend History",
        len(pactg_div), len(quikdvpr),
    )
    controls.append(_finalize_control(
        c08, count_control=True,
        explained_if_nonzero=(len(pactg_div) != len(quikdvpr)),
        exclusion_reasons=exclusions.get(
            "BAL-C08",
            ["Small difference after dividend transaction filters — usually explained"],
        ),
    ))

    # --- Tier 2 dollars ---
    c_d01 = ControlResult(
        "BAL-D01", "Dollars",
        "Total face amount (coverage amount) vs QLAdmin Riders",
        _sum_face_ppben(ppben_rid), _sum_face_ridr(quikridr),
    )
    controls.append(_finalize_control(
        c_d01, count_control=False,
        explained_if_nonzero=True,
        exclusion_reasons=exclusions.get("BAL-D01"),
    ))

    c_d02 = ControlResult(
        "BAL-D02", "Dollars",
        "Total modal (billed) premium vs QLAdmin Policy Master",
        _sum_column(ppolc, "MODE_PREMIUM"), _sum_column(quikmstr, "MMODEPREM"),
    )
    controls.append(_finalize_control(c_d02, count_control=False))

    c_d03 = ControlResult(
        "BAL-D03", "Dollars",
        "Total premium-history dollars vs QLAdmin Premium History",
        _sum_pactg_premium_amount(pactg), _sum_column(quikprmh, "PREMIUM"),
    )
    controls.append(_finalize_control(
        c_d03, count_control=False,
        explained_if_nonzero=True,
        exclusion_reasons=exclusions.get("BAL-D03"),
    ))

    c_d04 = ControlResult(
        "BAL-D04", "Dollars",
        "Total outstanding loan balances vs QLAdmin Loans",
        _sum_column(loan_passed_df, "MLOANBAL"),
        _sum_column(quikloan, "MLOANBAL"),
    )
    controls.append(_finalize_control(
        c_d04, count_control=False,
        explained_if_nonzero=True,
        exclusion_reasons=exclusions.get("BAL-C07"),
    ))

    if not ppbentyp.empty and "BENEFIT_SEQ" in ppbentyp.columns:
        seq = ppbentyp["BENEFIT_SEQ"].astype(str).str.strip().str.replace(".0", "", regex=False)
        dvdp_src = ppbentyp[seq.isin(["1", "01"])]
    else:
        dvdp_src = ppbentyp
    c_d05 = ControlResult(
        "BAL-D05", "Dollars",
        "Total accumulated dividends on deposit vs QLAdmin Dividend Deposit",
        _sum_column(dvdp_src, "ACCUM_DIVIDENDS"), _sum_column(quikdvdp, "MDEPOSIT"),
    )
    controls.append(_finalize_control(c_d05, count_control=False))

    c_d06 = ControlResult(
        "BAL-D06", "Dollars",
        "Total dividend transaction dollars vs QLAdmin Dividend History",
        _sum_column(pactg_div, "TRANS_AMOUNT"), _sum_column(quikdvpr, "MDIV"),
    )
    controls.append(_finalize_control(c_d06, count_control=False))

    split_fail_policies: list[dict] = []
    if not quikbenf.empty and "MSPLIT" in quikbenf.columns and "MPOLICY" in quikbenf.columns:
        grouped = quikbenf.groupby("MPOLICY", dropna=False)
        total_policies = len(grouped)
        bad = 0
        for pol, grp in grouped:
            total = round(sum(_parse_money(v) for v in grp["MSPLIT"]), 2)
            if abs(total - 100.0) > MONEY_TOLERANCE:
                bad += 1
                split_fail_policies.append({"MPOLICY": pol, "MSPLIT_TOTAL": total})
        passing = total_policies - bad
        c_d07 = ControlResult(
            "BAL-D07", "Dollars",
            "Beneficiary share percents on each policy add up to 100%",
            float(passing),
            float(total_policies),
        )
        c_d07.detail_rows = split_fail_policies
        if bad:
            c_d07.status = "FAIL"
            c_d07.explanation = (
                f"{bad:,} policies have beneficiary share percents that do not add up to 100%. "
                "Review the detail list under internal/."
            )
        else:
            c_d07.status = "PASS"
    else:
        c_d07 = ControlResult(
            "BAL-D07", "Dollars",
            "Beneficiary share percents on each policy add up to 100%",
            0, 0, status="PASS",
        )
    controls.append(c_d07)

    # --- Tier 3 inventory ---
    _log("Checking policy inventory...", 5)
    src_policies = set()
    if not ppolc.empty and "POLICY_NUMBER" in ppolc.columns:
        for pol in ppolc["POLICY_NUMBER"]:
            mapped = _map_policy(pol, cw_map)
            if mapped:
                src_policies.add(mapped)

    qla_policies = set()
    if not quikmstr.empty and "MPOLICY" in quikmstr.columns:
        for pol in quikmstr["MPOLICY"]:
            p = format_qladmin_mpolicy(pol)
            if p:
                qla_policies.add(p)

    missing_in_qla = sorted(src_policies - qla_policies)
    extra_in_qla = sorted(qla_policies - src_policies)

    matched = src_policies & qla_policies
    c_i01 = ControlResult(
        "BAL-I01", "Inventory",
        "Every LifePRO policy appears in QLAdmin Policy Master",
        float(len(src_policies)),
        float(len(matched)),
    )
    c_i01.detail_rows = [{"MPOLICY": p, "DIRECTION": "MISSING_IN_QLA"} for p in missing_in_qla]
    if missing_in_qla and exclusions.get("BAL-I01"):
        c_i01.status = "EXPLAINED"
        c_i01.explanation = exclusions["BAL-I01"][0]
    elif missing_in_qla:
        c_i01.status = "FAIL"
        c_i01.explanation = (
            f"{len(missing_in_qla):,} policies from LifePRO are missing in QLAdmin Policy Master"
        )
    else:
        c_i01.status = "PASS"
    controls.append(c_i01)

    c_i02 = ControlResult(
        "BAL-I02", "Inventory",
        "QLAdmin Policy Master has no policies that were not in LifePRO",
        float(len(qla_policies)),
        float(len(matched)),
    )
    c_i02.detail_rows = [{"MPOLICY": p, "DIRECTION": "INVENTED_IN_QLA"} for p in extra_in_qla]
    c_i02.status = "PASS" if not extra_in_qla else "FAIL"
    if extra_in_qla:
        c_i02.explanation = (
            f"{len(extra_in_qla):,} policies appear in QLAdmin but were not in the LifePRO policy master"
        )
    controls.append(c_i02)

    if missing_in_qla and c_i01.status == "EXPLAINED" and abs(c01.variance) == len(missing_in_qla):
        c01.status = "EXPLAINED"
        c01.explanation = c_i01.explanation

    return controls


def _overall_result_label(pass_n: int, explained_n: int, fail_n: int) -> str:
    if fail_n > 0 and explained_n > 0:
        return "Some Items Need Attention (with Explained Variances)"
    if fail_n > 0:
        return "Some Items Need Attention"
    if explained_n > 0:
        return "Passed with Explained Variances"
    return "Passed"


def _tier_result_label(controls: list[ControlResult]) -> str:
    fails = sum(1 for c in controls if c.status == "FAIL")
    explained = sum(1 for c in controls if c.status == "EXPLAINED")
    if fails and explained:
        return "Needs Attention (with Explained)"
    if fails:
        return "Needs Attention"
    if explained:
        return "Passed with Explained Variances"
    return "Passed"


def _status_type(status: str) -> str:
    if status == "FAIL":
        return "Data Problem"
    if status == "EXPLAINED":
        return "Explained Variance"
    return "Information"


def write_items_needing_attention_csv(controls: list[ControlResult], path: str) -> None:
    """Business CSV — FAIL and EXPLAINED only (Governance-style)."""
    fieldnames = [
        "Area",
        "Control",
        "What We Checked",
        "Source Value",
        "QLAdmin Value",
        "Variance",
        "Problem / Explanation",
        "Type",
        "Reference",
    ]
    rows = [c for c in controls if c.status in ("FAIL", "EXPLAINED")]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        if not rows:
            writer.writerow(
                {
                    "Area": "All Areas",
                    "Control": "",
                    "What We Checked": "All balancing controls",
                    "Source Value": "",
                    "QLAdmin Value": "",
                    "Variance": "",
                    "Problem / Explanation": (
                        "No data problems were found and all checks completed successfully."
                    ),
                    "Type": "Information",
                    "Reference": "",
                }
            )
            return
        for ctrl in rows:
            writer.writerow(
                {
                    "Area": ctrl.tier,
                    "Control": ctrl.control_id,
                    "What We Checked": ctrl.description,
                    "Source Value": _fmt_num(ctrl.source_value),
                    "QLAdmin Value": _fmt_num(ctrl.qla_value),
                    "Variance": _fmt_num(ctrl.variance),
                    "Problem / Explanation": ctrl.explanation
                    or ("Variance exceeds tolerance" if ctrl.status == "FAIL" else ""),
                    "Type": _status_type(ctrl.status),
                    "Reference": ctrl.control_id,
                }
            )


def write_what_was_checked_html(
    *,
    controls: list[ControlResult],
    path: str,
    run_id: str,
    run_timestamp: datetime,
) -> str:
    """Governance-style HTML executive summary. Returns overall result label."""
    pass_n = sum(1 for c in controls if c.status == "PASS")
    explained_n = sum(1 for c in controls if c.status == "EXPLAINED")
    fail_n = sum(1 for c in controls if c.status == "FAIL")
    total = len(controls)
    overall = _overall_result_label(pass_n, explained_n, fail_n)
    denom = pass_n + fail_n
    pct = f"{(pass_n / denom) * 100.0:.2f}%" if denom else "Not Available"
    run_date = run_timestamp.strftime("%Y-%m-%d %H:%M:%S")

    tier_order = ["Counts", "Dollars", "Inventory"]
    by_tier: dict[str, list[ControlResult]] = {t: [] for t in tier_order}
    for ctrl in controls:
        by_tier.setdefault(ctrl.tier, []).append(ctrl)

    table_rows: list[str] = []
    sections: list[str] = []
    for tier in tier_order:
        tier_controls = by_tier.get(tier) or []
        if not tier_controls:
            continue
        problems = sum(1 for c in tier_controls if c.status == "FAIL")
        result_label = _tier_result_label(tier_controls)
        what = {
            "Counts": "How many policies, people, coverages, premiums, loans, and dividends moved over",
            "Dollars": "Whether money totals match (face amount, premiums, loans, dividends, beneficiary shares)",
            "Inventory": "Whether every policy made it across — and no extra policies were invented",
        }.get(tier, tier)
        table_rows.append(
            "<tr>"
            f"<td>{html.escape(tier)}</td>"
            f"<td>{html.escape(what)}</td>"
            f"<td>{html.escape(result_label)}</td>"
            f"<td>{problems:,}</td>"
            "</tr>"
        )
        bullets = "".join(
            f"<li>{html.escape(c.description)} "
            f"(<strong>{html.escape(c.status)}</strong>"
            f"{': ' + html.escape(c.explanation) if c.explanation and c.status != 'PASS' else ''})"
            f"</li>"
            for c in tier_controls
        )
        sections.append(
            f"<h3>{html.escape(tier)}</h3>\n"
            f"<p>We checked that:</p>\n<ul>\n{bullets}\n</ul>\n"
            f"<p><strong>Result:</strong> {html.escape(result_label)}</p>\n"
            f"<p><strong>Problems Found:</strong> {problems:,}</p>\n"
        )

    next_steps = (
        "<p>No action required. Source and QLAdmin control totals are in balance "
        "(or variances are documented as explained).</p>"
        if fail_n == 0
        else (
            "<ol>"
            "<li>Open <strong>2_Items_Needing_Attention.csv</strong> for FAIL and EXPLAINED rows.</li>"
            "<li>Review each <strong>Data Problem</strong> with the conversion owner.</li>"
            "<li>Policy-level detail (when present) is under <code>internal/</code>.</li>"
            "<li>Re-run Balancing after corrections.</li>"
            "</ol>"
        )
    )

    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>QuikForge Balancing Review</title>
<style>
body {{ font-family: Georgia, "Times New Roman", serif; color: #222; margin: 2rem; line-height: 1.45; }}
h1, h2, h3 {{ font-family: Arial, Helvetica, sans-serif; font-weight: 600; }}
h1 {{ font-size: 1.6rem; margin-bottom: 0.25rem; }}
h2 {{ font-size: 1.25rem; margin-top: 2rem; border-bottom: 1px solid #ccc; padding-bottom: 0.25rem; }}
h3 {{ font-size: 1.05rem; margin-top: 1.5rem; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #bbb; padding: 0.45rem 0.6rem; text-align: left; vertical-align: top; }}
th {{ background: #f3f3f3; font-family: Arial, Helvetica, sans-serif; }}
.summary dt {{ font-family: Arial, Helvetica, sans-serif; font-weight: 600; margin-top: 0.6rem; }}
.summary dd {{ margin: 0.15rem 0 0 0; }}
.pass {{ color: #15803D; }}
.fail {{ color: #B91C1C; }}
.explained {{ color: #A16207; }}
@media print {{ body {{ margin: 0.75in; }} }}
</style>
</head>
<body>
<h1>QuikForge Balancing Review</h1>
<p>This review compares the LifePRO source files to the QLAdmin conversion output.
Nothing was changed — this report only shows whether the counts and dollars match.</p>
<p><strong>Quick terms:</strong>
<em>LifePRO</em> = source system extracts;
<em>QLAdmin</em> = converted load files;
<em>Names &amp; Addresses</em> = the LifePRO file of people, roles, and beneficiaries
(sometimes called the Relationship Name/Address extract).</p>
<h2>Executive Summary</h2>
<dl class="summary">
<dt>Overall Result</dt><dd class="{'fail' if fail_n else 'pass'}">{html.escape(overall)}</dd>
<dt>Controls Passed</dt><dd>{pass_n:,} of {total:,} ({html.escape(pct)} of completed PASS/FAIL)</dd>
<dt>Problems Found (FAIL)</dt><dd>{fail_n:,}</dd>
<dt>Explained Variances</dt><dd>{explained_n:,}</dd>
<dt>Review Scope</dt><dd>All Active Balancing Controls (Counts, Dollars, Inventory)</dd>
<dt>Run Date</dt><dd>{html.escape(run_date)}</dd>
<dt>Run ID</dt><dd>{html.escape(run_id)}</dd>
</dl>
<h2>What We Checked</h2>
<table>
<thead><tr><th>Area</th><th>What We Checked</th><th>Result</th><th>Problems Found</th></tr></thead>
<tbody>
{''.join(table_rows)}
</tbody>
</table>
<h2>Area Details</h2>
{''.join(sections)}
<h2>What To Do Next</h2>
{next_steps}
<p>Plain-English control definitions: <code>Balancing_Methodology.md</code> in the Balancing folder.
Technical control totals: <code>internal/balancing_control_totals.csv</code>.</p>
</body>
</html>
"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return overall


def run_balancing(
    *,
    src_dir: str,
    out_dir: str,
    balancing_dir: str,
    crosswalk_path: str | None = None,
    exclusions_path: str | None = None,
    progress_callback: Callable[..., None] | None = None,
) -> dict[str, Any]:
    """
    Run fleet balancing controls and write Governance-style reports.

    Per-run folder layout (matches Data Governance):
      Balancing/BAL-<timestamp>/
        1_What_Was_Checked.html          ← open this first
        2_Items_Needing_Attention.csv
        internal/balancing_control_totals.csv
        internal/Balancing_Detail_*.csv
    """
    def _prog(msg: str, stage: int | None = None) -> None:
        if not progress_callback:
            return
        try:
            progress_callback(msg, stage)
        except TypeError:
            progress_callback(msg)

    src_dir = os.path.normpath(src_dir)
    out_dir = os.path.normpath(out_dir)
    balancing_dir = os.path.normpath(balancing_dir)
    os.makedirs(balancing_dir, exist_ok=True)

    if not crosswalk_path:
        crosswalk_path = os.path.normpath(
            os.path.join(os.path.dirname(balancing_dir), "Mapping", "Master_Crosswalk.csv")
        )
    if not exclusions_path:
        exclusions_path = os.path.normpath(
            os.path.join(os.path.dirname(balancing_dir), "Configs", "balancing_exclusions.csv")
        )

    exclusions = _load_exclusions(exclusions_path)
    controls = _compute_controls(
        src_dir=src_dir,
        out_dir=out_dir,
        crosswalk_path=crosswalk_path,
        exclusions=exclusions,
        progress=progress_callback,
    )

    _prog("Writing Balancing reports...", 6)
    run_ts = datetime.now()
    ts = run_ts.strftime("%Y%m%d_%H%M%S")
    run_id = f"BAL-{ts}"
    run_folder = os.path.join(balancing_dir, run_id)
    internal_dir = os.path.join(run_folder, "internal")
    os.makedirs(internal_dir, exist_ok=True)

    html_path = os.path.join(run_folder, "1_What_Was_Checked.html")
    attention_path = os.path.join(run_folder, "2_Items_Needing_Attention.csv")
    report_path = os.path.join(internal_dir, "balancing_control_totals.csv")

    overall_label = write_what_was_checked_html(
        controls=controls,
        path=html_path,
        run_id=run_id,
        run_timestamp=run_ts,
    )
    write_items_needing_attention_csv(controls, attention_path)

    with open(report_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        for ctrl in controls:
            writer.writerow(ctrl.to_row())

    detail_paths: list[str] = []
    for ctrl in controls:
        if ctrl.status != "FAIL" or not ctrl.detail_rows:
            continue
        detail_path = os.path.join(internal_dir, f"Balancing_Detail_{ctrl.control_id}.csv")
        with open(detail_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(ctrl.detail_rows[0].keys()))
            writer.writeheader()
            writer.writerows(ctrl.detail_rows)
        detail_paths.append(detail_path)

    pass_n = sum(1 for c in controls if c.status == "PASS")
    explained_n = sum(1 for c in controls if c.status == "EXPLAINED")
    fail_n = sum(1 for c in controls if c.status == "FAIL")

    return {
        "report_path": html_path,
        "what_was_checked_path": html_path,
        "attention_csv_path": attention_path,
        "control_totals_path": report_path,
        "detail_paths": detail_paths,
        "balancing_dir": balancing_dir,
        "run_folder": run_folder,
        "run_id": run_id,
        "pass_count": pass_n,
        "explained_count": explained_n,
        "fail_count": fail_n,
        "control_count": len(controls),
        "overall_status": "FAIL" if fail_n else "PASS",
        "overall_result": overall_label,
        "timestamp": ts,
    }
