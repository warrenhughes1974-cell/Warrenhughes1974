"""
Issue #124 — QuikIswl month-0 seed rows (superseded 2026-09-24 by Issue #155 history).
Issue #155 — full LifePRO PFNDRDET monthiversary history + MISWL on quikprmh / QuikIsrr.

Builds QuikIswl rows per ISWL base coverage (MPHASE=1, ISWL MPLAN allowlist) from
PFNDRDET detail through QLA_VALUATION_DATE; no month-0 row at issue date.

Policy keys/units/dates: quikridr + quikmstr Output.
PFNDR summary: QLA_Migration/Source/PFNDR_FundHistory_Extract_<QLA_VALUATION_DATE>.csv
PFNDRDET history: QLA_Migration/Source/PFNDRDET_FundHistoryDET_ISWL_Extract_20260831.csv
"""
from __future__ import annotations

import calendar
import csv
import datetime as dt
import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST

QUIKISWL_FIELDS = [
    "MPOLICY",
    "MLOB",
    "MLASTANNV",
    "MMONTH",
    "MACCTBAL",
    "MSURRCHG",
    "MCASHVAL",
    "MGTDCSV",
    "MLOANBAL",
    "MPREMIUMS",
    "MINT",
    "MEXP",
    "MDB",
    "MNAR",
    "MCOI",
    "MSPRCOI",
    "MCTRCOI",
    "MWPRCOI",
    "MADBCOI",
    "MGIOCOI",
    "MSURR",
    "MSUMPREM",
    "MSUSPENSE",
    "MUNALLOC",
    "MPROCDATE",
    "MPRNTSTMT",
]

ZERO_MONEY_FIELDS = [
    "MACCTBAL",
    "MSURRCHG",
    "MCASHVAL",
    "MGTDCSV",
    "MLOANBAL",
    "MPREMIUMS",
    "MINT",
    "MEXP",
    "MNAR",
    "MCOI",
    "MSPRCOI",
    "MCTRCOI",
    "MWPRCOI",
    "MADBCOI",
    "MGIOCOI",
    "MSURR",
    "MSUMPREM",
    "MSUSPENSE",
    "MUNALLOC",
]

OUTPUT_FILENAME = "QuikIswl.csv"
EXCEPTION_COLUMNS = [
    "MPOLICY",
    "REASON",
    "PFNDR_VALUATION_DATE",
    "PFNDR_FUND_BALANCE",
    "REBUILT_BALANCE",
    "SEED_MLASTANNV",
]
MISWL_COLUMN = "MISWL"

PFNDRDET_FILENAME = "PFNDRDET_FundHistoryDET_ISWL_Extract_20260831.csv"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _s(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _parse_unit(v: object) -> float | None:
    t = _s(v)
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _fmt_money(v: float) -> str:
    return f"{v:.2f}"


def _norm_date(v: object) -> str:
    d = "".join(ch for ch in _s(v) if ch.isdigit())
    return d[:8] if len(d) >= 8 else ""


def _parse_date8(s: str) -> dt.date | None:
    s = _norm_date(s)
    if len(s) != 8 or s == "00000000":
        return None
    try:
        return dt.date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    except ValueError:
        return None


def _parse_money(v: object) -> float:
    t = _s(v)
    if not t:
        return 0.0
    try:
        return float(t)
    except ValueError:
        return 0.0


def _require_valuation_date() -> str:
    raw = os.environ.get("QLA_VALUATION_DATE", "").strip()
    if len(raw) != 8 or not raw.isdigit():
        raise ValueError(
            "QLA_VALUATION_DATE must be set to YYYYMMDD before QuikIswl seed emit"
        )
    return raw


def _add_months(d: dt.date, n: int) -> dt.date:
    y, m = divmod(d.month - 1 + n, 12)
    y += d.year
    m += 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def _months_between(issue: dt.date, d: dt.date) -> int:
    n = (d.year - issue.year) * 12 + (d.month - issue.month)
    if _add_months(issue, n) > d:
        n -= 1
    return n


def next_monthiversary_on_or_after(issue: dt.date, paid: dt.date) -> dt.date:
    """First QL monthiversary on or after paid date."""
    n = max(_months_between(issue, paid), 0)
    m = _add_months(issue, n)
    return m if m >= paid else _add_months(issue, n + 1)


@dataclass
class _DateFlow:
    dep: float = 0.0
    load: float = 0.0
    inte: float = 0.0
    ded_all: float = 0.0
    ded_pf: float = 0.0
    ded_mt: float = 0.0
    wd: float = 0.0
    ln: float = 0.0


@dataclass
class PolicyMeta:
    mpolicy: str
    issue: str
    mdb: str
    mplan: str = ""


@dataclass
class QuikIswlEmitResult:
    rows: list[dict] = field(default_factory=list)
    skipped_missing_issue: list[dict] = field(default_factory=list)
    skipped_bad_unit: list[dict] = field(default_factory=list)
    skipped_orphan_mstr: list[dict] = field(default_factory=list)
    by_plan: dict[str, int] = field(default_factory=dict)


def load_iswl_policy_meta(
    mstr_path: Path,
    ridr_path: Path,
    *,
    allowlist: frozenset[str] | set[str] = ISWL_MPLAN_ALLOWLIST,
) -> tuple[dict[str, PolicyMeta], QuikIswlEmitResult]:
    """Policy metadata for ISWL base coverages (same population as legacy month-0 seeds)."""
    result = QuikIswlEmitResult()
    meta: dict[str, PolicyMeta] = {}
    mstr: dict[str, dict[str, str]] = {}
    with mstr_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = _s(row.get("MPOLICY"))
            if pol:
                mstr[pol] = {
                    "MISSDT": _norm_date(row.get("MISSDT")),
                    "MSTATUS": _s(row.get("MSTATUS")),
                }

    by_plan: dict[str, int] = {}
    with ridr_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            plan = _s(row.get("MPLAN"))
            phase = _s(row.get("MPHASE"))
            if plan not in allowlist or phase != "1":
                continue
            pol = _s(row.get("MPOLICY"))
            if not pol:
                continue
            ms = mstr.get(pol)
            if ms is None:
                result.skipped_orphan_mstr.append(
                    {"MPOLICY": pol, "MPLAN": plan, "reason": "no_quikmstr"}
                )
                continue
            issue = ms.get("MISSDT", "")
            if not issue:
                result.skipped_missing_issue.append(
                    {"MPOLICY": pol, "MPLAN": plan, "reason": "blank_MISSDT"}
                )
                continue
            unit = _parse_unit(row.get("MUNIT"))
            if unit is None:
                result.skipped_bad_unit.append(
                    {
                        "MPOLICY": pol,
                        "MPLAN": plan,
                        "MUNIT": _s(row.get("MUNIT")),
                        "reason": "bad_MUNIT",
                    }
                )
                continue
            meta[pol] = PolicyMeta(
                mpolicy=pol,
                issue=issue,
                mdb=_fmt_money(unit * 1000.0),
                mplan=plan,
            )
            by_plan[plan] = by_plan.get(plan, 0) + 1

    result.by_plan = dict(sorted(by_plan.items()))
    return meta, result


def build_quikiswl_seed_rows(
    mstr_path: Path,
    ridr_path: Path,
    *,
    allowlist: frozenset[str] | set[str] = ISWL_MPLAN_ALLOWLIST,
) -> QuikIswlEmitResult:
    """Legacy month-0 row builder (Issue #124); retained for reference/tests."""
    meta, result = load_iswl_policy_meta(mstr_path, ridr_path, allowlist=allowlist)
    for pm in meta.values():
        out = {f: "" for f in QUIKISWL_FIELDS}
        out["MPOLICY"] = pm.mpolicy
        out["MLOB"] = "I"
        out["MLASTANNV"] = pm.issue
        out["MMONTH"] = "0"
        out["MDB"] = pm.mdb
        for fld in ZERO_MONEY_FIELDS:
            out[fld] = "0.00"
        result.rows.append(out)
    result.rows.sort(key=lambda r: (r["MPOLICY"], r["MLASTANNV"]))
    return result


def _pfndrdet_path() -> Path:
    return _project_root() / "QLA_Migration" / "Source" / PFNDRDET_FILENAME


def _load_pfndrdet_history(
    max_valuation_date: str,
) -> tuple[
    dict[str, tuple[str, float]],
    dict[str, dict[str, _DateFlow]],
]:
    """
    Stream PFNDRDET; return cv[pol_no] -> (cv_date, cv_gross_deposits),
    flows[pol_no][valdate] -> aggregated amounts (pol_no without C suffix).
    """
    path = _pfndrdet_path()
    if not path.is_file():
        raise FileNotFoundError(f"PFNDRDET extract required: {path}")

    cv: dict[str, tuple[str, float]] = {}
    flows: dict[str, dict[str, _DateFlow]] = defaultdict(lambda: defaultdict(_DateFlow))

    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = _s(row.get("POLICY_NUMBER"))
            if not pol:
                continue
            vd = _norm_date(row.get("VALUATION_DATE"))
            if not vd or vd > max_valuation_date:
                continue
            t = _s(row.get("DETAIL_TYPE"))
            bucket = flows[pol][vd]
            if t == "CV":
                cv[pol] = (vd, _parse_money(row.get("CV_GROSS_DEPOSITS")))
            elif t == "IN":
                bucket.inte += _parse_money(row.get("CURR_INT_AMOUNT"))
            elif t == "DP":
                bucket.dep += _parse_money(row.get("GROSS_DEPOSIT"))
                bucket.load += _parse_money(row.get("DEPOSIT_LOAD"))
                bucket.inte += _parse_money(row.get("DEP_CURR_INT_AMT"))
            elif t == "DD":
                amt = _parse_money(row.get("DEDUCTION_AMOUNT"))
                bucket.ded_all += amt
                ded_type = _s(row.get("DEDUCTION_TYPE"))
                if ded_type == "PF":
                    bucket.ded_pf += amt
                elif ded_type == "MT":
                    bucket.ded_mt += amt
            elif t == "WD":
                bucket.wd += _parse_money(row.get("GROSS_WITHDRAWAL"))
            elif t == "LN":
                bucket.ln += _parse_money(row.get("LOAN_AMOUNT"))
            # EI, LS, ** — intentionally ignored (EI mirrors IN)

    return cv, flows


def _cum_net_through(
    flow_dates: dict[str, _DateFlow], thru: str
) -> tuple[float, float, float, float, float, float]:
    dep = load = inte = ded = wd = ln = 0.0
    for d, b in flow_dates.items():
        if d <= thru:
            dep += b.dep
            load += b.load
            inte += b.inte
            ded += b.ded_all
            wd += b.wd
            ln += b.ln
    return dep, load, inte, ded, wd, ln


def _blank_money_row(mpolicy: str, mdb: str) -> dict:
    row = {f: "" for f in QUIKISWL_FIELDS}
    row["MPOLICY"] = mpolicy
    row["MLOB"] = "I"
    row["MDB"] = mdb
    row["MSURRCHG"] = "0.00"
    row["MGTDCSV"] = "0.00"
    row["MNAR"] = "0.00"
    row["MSPRCOI"] = "0.00"
    row["MCTRCOI"] = "0.00"
    row["MWPRCOI"] = "0.00"
    row["MADBCOI"] = "0.00"
    row["MGIOCOI"] = "0.00"
    row["MSUSPENSE"] = "0.00"
    row["MUNALLOC"] = "0.00"
    return row


def _make_history_row(
    pm: PolicyMeta,
    val_date: str,
    *,
    macctbal: float,
    msumprem: float,
    mloanbal: float,
    mpremiums: float,
    mint: float,
    mexp: float,
    mcoi: float,
    msurr: float,
) -> dict:
    issue_d = _parse_date8(pm.issue)
    val_d = _parse_date8(val_date)
    mmonth = str(_months_between(issue_d, val_d)) if issue_d and val_d else "0"
    row = _blank_money_row(pm.mpolicy, pm.mdb)
    row["MLASTANNV"] = val_date
    row["MMONTH"] = mmonth
    row["MACCTBAL"] = _fmt_money(macctbal)
    row["MCASHVAL"] = _fmt_money(macctbal)
    row["MLOANBAL"] = _fmt_money(mloanbal)
    row["MPREMIUMS"] = _fmt_money(mpremiums)
    row["MINT"] = _fmt_money(mint)
    row["MEXP"] = _fmt_money(mexp)
    row["MCOI"] = _fmt_money(mcoi)
    row["MSURR"] = _fmt_money(msurr)
    row["MSUMPREM"] = _fmt_money(msumprem)
    return row


def _flow_components(flow: _DateFlow) -> tuple[float, float, float, float, float]:
    """MPREMIUMS, MINT, MEXP, MCOI, MSURR — all DD amounts must exit via MEXP or MCOI."""
    mprem = flow.dep
    mint = flow.inte
    mcoi = flow.ded_mt
    mexp = flow.ded_pf + flow.load + max(flow.ded_all - flow.ded_pf - flow.ded_mt, 0.0)
    msurr = flow.wd
    return mprem, mint, mexp, mcoi, msurr


def _apply_flows(
    bal: float,
    sumprem: float,
    loan: float,
    flow: _DateFlow,
    *,
    record_floor: list[tuple[str, str]],
    mpolicy: str,
    val_date: str,
) -> tuple[float, float, float]:
    mprem, mint, mexp, mcoi, msurr = _flow_components(flow)
    loan += flow.ln
    raw_bal = bal + mprem - mexp - mcoi + mint - msurr
    if raw_bal < 0:
        record_floor.append((mpolicy, val_date))
        raw_bal = 0.0
    sumprem += mprem
    return raw_bal, sumprem, loan


def build_quikiswl_history_rows(
    policy_meta: dict[str, PolicyMeta],
    pfndr: dict[str, dict[str, str]],
    cv_by_pol: dict[str, tuple[str, float]],
    flows_by_pol: dict[str, dict[str, _DateFlow]],
    valuation_date: str,
) -> tuple[list[dict], list[dict], dict[str, int]]:
    """Build full PFNDRDET roll-forward QuikIswl rows (Issue #155 amendment)."""
    rows: list[dict] = []
    exceptions: list[dict] = []
    exc_counts: dict[str, int] = defaultdict(int)

    def _exc(
        mpolicy: str,
        reason: str,
        pfndr_row: dict[str, str] | None,
        *,
        rebuilt: str = "",
        seed_mlastannv: str = "",
    ) -> None:
        exc_counts[reason] += 1
        exceptions.append(
            {
                "MPOLICY": mpolicy,
                "REASON": reason,
                "PFNDR_VALUATION_DATE": _norm_date(pfndr_row.get("VALUATION_DATE"))
                if pfndr_row
                else "",
                "PFNDR_FUND_BALANCE": _s(pfndr_row.get("FUND_BALANCE")) if pfndr_row else "",
                "REBUILT_BALANCE": rebuilt,
                "SEED_MLASTANNV": seed_mlastannv,
            }
        )

    for mpolicy, pm in sorted(policy_meta.items()):
        pol_no = mpolicy[:-1] if mpolicy.endswith("C") else mpolicy
        pf = pfndr.get(mpolicy)
        if pf is None:
            _exc(mpolicy, "NO_PFNDR", None)
            continue

        pf_val_s = _norm_date(pf.get("VALUATION_DATE"))
        if not pf_val_s or pf_val_s > valuation_date:
            _exc(mpolicy, "NO_PFNDR", pf)
            continue

        pol_flows = flows_by_pol.get(pol_no)
        if not pol_flows:
            _exc(mpolicy, "NO_HISTORY", pf)
            continue

        cv_info = cv_by_pol.get(pol_no)
        if not cv_info:
            _exc(mpolicy, "NO_HISTORY", pf)
            continue
        cv_date, cv_gross = cv_info

        dep, load, inte, ded, wd, _ln = _cum_net_through(pol_flows, pf_val_s)
        net = dep - load + inte - ded - wd
        fund_bal = _parse_money(pf.get("FUND_BALANCE"))
        raw_open = fund_bal - net
        if raw_open < 0:
            _exc(mpolicy, "NEGATIVE_FLOORED_ZERO", pf, seed_mlastannv=cv_date)
        implied_open = max(raw_open, 0.0)

        floor_events: list[tuple[str, str]] = []
        running_bal = implied_open
        running_sumprem = cv_gross
        running_loan = 0.0

        end_date = pf_val_s if pf_val_s <= valuation_date else valuation_date
        dates = sorted(d for d in pol_flows if cv_date <= d <= end_date)
        if not dates or dates[0] != cv_date:
            if cv_date not in pol_flows:
                dates = sorted({cv_date, *dates})
            else:
                dates = sorted(d for d in dates if d >= cv_date)
                if cv_date not in dates:
                    dates = [cv_date] + dates

        pol_rows: list[dict] = []
        for i, d in enumerate(dates):
            flow = pol_flows.get(d, _DateFlow())
            if i == 0 and d == cv_date:
                mprem = mint = mexp = mcoi = msurr = 0.0
                end_bal = running_bal
                end_sumprem = running_sumprem
                end_loan = running_loan
                if (
                    flow.dep
                    or flow.load
                    or flow.inte
                    or flow.ded_all
                    or flow.wd
                    or flow.ln
                ):
                    end_bal, end_sumprem, end_loan = _apply_flows(
                        running_bal,
                        running_sumprem,
                        running_loan,
                        flow,
                        record_floor=floor_events,
                        mpolicy=mpolicy,
                        val_date=d,
                    )
                    mprem, mint, mexp, mcoi, msurr = _flow_components(flow)
                pol_rows.append(
                    _make_history_row(
                        pm,
                        d,
                        macctbal=end_bal,
                        msumprem=end_sumprem,
                        mloanbal=end_loan,
                        mpremiums=mprem,
                        mint=mint,
                        mexp=mexp,
                        mcoi=mcoi,
                        msurr=msurr,
                    )
                )
                running_bal, running_sumprem, running_loan = (
                    end_bal,
                    end_sumprem,
                    end_loan,
                )
            else:
                mprem, mint, mexp, mcoi, msurr = _flow_components(flow)
                running_loan += flow.ln
                raw_bal = (
                    running_bal + mprem - mexp - mcoi + mint - msurr
                )
                if raw_bal < 0:
                    floor_events.append((mpolicy, d))
                    raw_bal = 0.0
                running_bal = raw_bal
                running_sumprem += mprem
                pol_rows.append(
                    _make_history_row(
                        pm,
                        d,
                        macctbal=running_bal,
                        msumprem=running_sumprem,
                        mloanbal=running_loan,
                        mpremiums=mprem,
                        mint=mint,
                        mexp=mexp,
                        mcoi=mcoi,
                        msurr=msurr,
                    )
                )

        seen_floor: set[str] = set()
        for _pol, fd in floor_events:
            if fd in seen_floor:
                continue
            seen_floor.add(fd)
            _exc(mpolicy, "NEGATIVE_FLOORED_ZERO", pf, seed_mlastannv=fd)

        exp_final = fund_bal
        if pol_rows:
            last = pol_rows[-1]
            rebuilt = _parse_money(last.get("MACCTBAL"))
            if fund_bal < -0.005:
                if abs(rebuilt - fund_bal) > 0.011:
                    _exc(
                        mpolicy,
                        "NEGATIVE_SIGNED",
                        pf,
                        rebuilt=_fmt_money(rebuilt),
                        seed_mlastannv=_norm_date(last.get("MLASTANNV")),
                    )
                last["MACCTBAL"] = _fmt_money(fund_bal)
                last["MCASHVAL"] = _fmt_money(fund_bal)
            elif abs(rebuilt - exp_final) > 0.011:
                _exc(
                    mpolicy,
                    "OPEN_BALANCE_UNTIED",
                    pf,
                    rebuilt=_fmt_money(rebuilt),
                    seed_mlastannv=_norm_date(last.get("MLASTANNV")),
                )
                if exp_final <= 0.011 and rebuilt > 0.011:
                    last["MACCTBAL"] = "0.00"
                    last["MCASHVAL"] = "0.00"

        rows.extend(pol_rows)

    rows.sort(key=lambda r: (r["MPOLICY"], r["MLASTANNV"]))
    return rows, exceptions, dict(exc_counts)


def _load_pfndr_by_mpolicy(valuation_date: str) -> dict[str, dict[str, str]]:
    path = (
        _project_root()
        / "QLA_Migration"
        / "Source"
        / f"PFNDR_FundHistory_Extract_{valuation_date}.csv"
    )
    if not path.is_file():
        raise FileNotFoundError(
            f"PFNDR extract required for valuation date {valuation_date}: {path}"
        )
    out: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="latin1", errors="replace") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [_s(h) for h in (reader.fieldnames or [])]
        for row in reader:
            cleaned = {_s(k): _s(v) if isinstance(v, str) else "" for k, v in row.items() if k}
            pol_num = _s(cleaned.get("POLICY_NUMBER"))
            if not pol_num:
                continue
            mpolicy = pol_num + "C"
            out[mpolicy] = cleaned
    return out


def write_quikiswl_csv(rows: list[dict], out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=QUIKISWL_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def write_issue155_exceptions(
    exceptions: list[dict], valuation_date: str, reports_dir: Path | None = None
) -> Path:
    rep = reports_dir or (_project_root() / "QLA_Migration" / "Reports")
    rep.mkdir(parents=True, exist_ok=True)
    path = rep / f"issue155_iswl_seed_exceptions_{valuation_date}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=EXCEPTION_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(exceptions)
    return path


def _load_issue_dates(mstr_path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not mstr_path.is_file():
        return out
    with mstr_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = _s(row.get("MPOLICY"))
            if pol:
                out[pol] = _norm_date(row.get("MISSDT"))
    return out


def _read_iswl_seed_context(iswl_path: Path) -> dict[str, dict[str, str]]:
    """Per MPOLICY: seed_mlastannv = max MLASTANNV (latest history row)."""
    ctx: dict[str, dict[str, str]] = {}
    if not iswl_path.is_file():
        return ctx
    with iswl_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = _s(row.get("MPOLICY"))
            annv = _norm_date(row.get("MLASTANNV"))
            if not pol or not annv:
                continue
            prev = ctx.get(pol, {}).get("seed_mlastannv", "")
            if not prev or annv > prev:
                ctx.setdefault(pol, {})["seed_mlastannv"] = annv
    return ctx


def _stamp_miswl_on_csv(
    csv_path: Path,
    date_field: str,
    seed_ctx: dict[str, dict[str, str]],
) -> dict[str, int]:
    if not csv_path.is_file():
        return {"status": "SKIPPED", "reason": "missing_file", "stamped": 0, "blank": 0}

    with csv_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        raw_fields = list(reader.fieldnames or [])
        rows = list(reader)

    base_fields = [c for c in raw_fields if c != MISWL_COLUMN]
    out_fields = base_fields + [MISWL_COLUMN]

    stamped = 0
    blank = 0
    for row in rows:
        pol = _s(row.get("MPOLICY"))
        info = seed_ctx.get(pol)
        miswl = ""
        if info and info.get("seed_mlastannv") and info.get("issue_date"):
            issue_d = _parse_date8(info["issue_date"])
            seed_d = _parse_date8(info["seed_mlastannv"])
            paid_d = _parse_date8(row.get(date_field, ""))
            if issue_d and seed_d and paid_d:
                mv = next_monthiversary_on_or_after(issue_d, paid_d)
                if mv <= seed_d:
                    miswl = mv.strftime("%Y%m%d")
        row[MISWL_COLUMN] = miswl
        if miswl:
            stamped += 1
        else:
            blank += 1
        for k in list(row.keys()):
            if k not in out_fields:
                del row[k]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    return {"stamped": stamped, "blank": blank, "rows": len(rows)}


def stamp_iswl_miswl(output_dir: Path | str) -> dict:
    """
    Stamp trailing MISWL on quikprmh.csv and QuikIsrr.csv from QuikIswl history rows.
    Idempotent when MISWL column already exists.
    """
    out = Path(output_dir)
    iswl_path = out / OUTPUT_FILENAME
    if not iswl_path.is_file():
        alt = out / "quikiswl.csv"
        iswl_path = alt if alt.is_file() else iswl_path

    seed_ctx = _read_iswl_seed_context(iswl_path)
    issue_dates = _load_issue_dates(out / "quikmstr.csv")
    for pol, info in seed_ctx.items():
        info["issue_date"] = issue_dates.get(pol, "")

    prmh = _stamp_miswl_on_csv(out / "quikprmh.csv", "DATEPAID", seed_ctx)
    isrr = _stamp_miswl_on_csv(out / "QuikIsrr.csv", "MSURRDATE", seed_ctx)
    return {
        "status": "SUCCESS",
        "issue": 155,
        "seed_policies": len(
            [p for p, c in seed_ctx.items() if c.get("seed_mlastannv")]
        ),
        "quikprmh": prmh,
        "QuikIsrr": isrr,
    }


def emit_quikiswl_seeds(output_dir: Path | str) -> dict:
    """
    Build and write QuikIswl.csv under output_dir (full PFNDRDET history through cut).
    Stamps quikprmh MISWL when quikprmh.csv exists. Returns a JSON-serializable summary.
    """
    try:
        valuation_date = _require_valuation_date()
    except ValueError as exc:
        return {
            "status": "FAILED",
            "error": str(exc),
            "output_dir": str(output_dir),
        }

    out = Path(output_dir)
    mstr_path = out / "quikmstr.csv"
    ridr_path = out / "quikridr.csv"
    if not mstr_path.is_file() or not ridr_path.is_file():
        return {
            "status": "FAILED",
            "error": "missing quikmstr.csv or quikridr.csv",
            "output_dir": str(out),
        }

    try:
        policy_meta, meta_result = load_iswl_policy_meta(mstr_path, ridr_path)
        pfndr = _load_pfndr_by_mpolicy(valuation_date)
        cv_by_pol, flows_by_pol = _load_pfndrdet_history(valuation_date)
        history_rows, exceptions, exc_counts = build_quikiswl_history_rows(
            policy_meta, pfndr, cv_by_pol, flows_by_pol, valuation_date
        )
        path = out / OUTPUT_FILENAME
        n = write_quikiswl_csv(history_rows, path)
        exc_path = write_issue155_exceptions(exceptions, valuation_date)
        miswl_summary = stamp_iswl_miswl(out)
    except FileNotFoundError as exc:
        return {
            "status": "FAILED",
            "error": str(exc),
            "output_dir": str(out),
            "valuation_date": valuation_date,
        }
    except Exception as exc:
        return {
            "status": "FAILED",
            "error": str(exc),
            "output_dir": str(out),
            "valuation_date": valuation_date,
        }

    policies_with_rows = len({r["MPOLICY"] for r in history_rows})
    return {
        "status": "SUCCESS",
        "issue": 155,
        "issue124_month0": "removed",
        "valuation_date": valuation_date,
        "output": str(path),
        "rows": n,
        "policies_with_history": policies_with_rows,
        "exceptions_path": str(exc_path),
        "exceptions": exc_counts,
        "by_plan": meta_result.by_plan,
        "skipped_missing_issue": len(meta_result.skipped_missing_issue),
        "skipped_bad_unit": len(meta_result.skipped_bad_unit),
        "skipped_orphan_mstr": len(meta_result.skipped_orphan_mstr),
        "miswl_stamp": miswl_summary,
    }
