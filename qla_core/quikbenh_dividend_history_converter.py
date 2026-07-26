"""
LifePRO dividend history → QuikBenh converter (Issue #114).

Two layers, mirroring the Issue #21F premium-history pattern:

  Layer A  PACTG dividend election codes (0514/0515/0516/0517/0518) → MBENTYP 1-5.
           Real dated transactions, limited to the PACTG extract window (2018+).
  Layer B  One conversion adjustment row per policy, dated 20171231, for
           PPBENTYP.DIVIDENDS_CREDITED minus the Layer A sum, so each policy's
           dividend history ties to the LifePRO lifetime total.

  Layer C  Issue #117 — the dividend accumulation ledger. QLAdmin's Dividend
           History window is not a credits list; it is a running account, and
           sum(3) + sum(6) - sum(7) must equal the QuikDvdp balance shown in its
           own footer (QLAdmin Help 6.5 p.649; verified on 425 of 464 accumulate
           policies in the client's production QUIKBENH.DBF).

             MBENTYP 6  Interest on policy funds / dividend accumulation
                        PACTG debit 0641 / credit 0310
             MBENTYP 7  Surrendered dividend accumulations
                        PACTG debit 0310 against any counterparty

           Layer B's 20171231 row is also split: the type 3 half keeps the
           Issue #114 amount exactly, and a type 6 half carries the pre-2018
           interest so the opening is a real balance rather than a credits
           remainder.

Rows whose benefit type cannot be derived (dividend option 6 = Reduce Loan, blank
option) and non-positive gaps are withheld to the exception report rather than
guessed. Appends to existing quikbenh.csv and replaces only MBENTYP 1-7, so
Issue #34 (type 8) and Issue #54 (types 10/11/12) rows are preserved untouched.

Production emit is gated by QLA_ENABLE_QUIKBENH_DIVIDEND_EMIT /
QLA_QUIKBENH_DIVIDEND_WRITE_OUTPUT.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from typing import Any

import pandas as pd

from qla_core.normalize_utils import format_qladmin_mpolicy, normalize_columns
from qla_core.schema_constants import QUIKBENH_SCHEMA

_DEFAULT_RULES_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "plan_governance",
        "config",
        "quikbenh_dividend_history_rules.json",
    )
)

_DEFAULT_ELECTION_CODES = {"0515": "1", "0516": "2", "0514": "3", "0517": "4", "0518": "5"}
_DEFAULT_OPTION_MAP = {"1": "1", "2": "2", "3": "3", "4": "4", "5": "5"}
_DEFAULT_PLUG_DATE = "20171231"
_DEFAULT_REPLACE_TYPES = frozenset({"1", "2", "3", "4", "5", "6", "7"})
_MONEY_TOLERANCE = 0.005

# Issue #117 — dividend accumulation ledger.
_DEFAULT_ACCUM_ACCOUNT = "0310"
_DEFAULT_INTEREST_CODE = "0641"
_DEFAULT_INTEREST_MBENTYP = "6"
_DEFAULT_OUTFLOW_MBENTYP = "7"
_DEFAULT_ACCUM_OPENING_MBENTYP = "3"

VALIDATION_FIELDS = [
    "SOURCE_POLICY",
    "MPOLICY",
    "DIVIDEND_OPTION",
    "MBENTYP",
    "LIFEPRO_LIFETIME",
    "LAYER_A_TXN_COUNT",
    "LAYER_A_TOTAL",
    "PLUG_AMOUNT",
    "FINAL_TOTAL",
    "REMAINING_VARIANCE",
    "STATUS",
]

EXCEPTION_FIELDS = [
    "SOURCE_POLICY",
    "MPOLICY",
    "DIVIDEND_OPTION",
    "LIFEPRO_LIFETIME",
    "LAYER_A_TOTAL",
    "GAP",
    "REASON",
    "NOTE",
]

# Issue #117 — per-policy proof that the emitted ledger equals the QuikDvdp balance.
LEDGER_FIELDS = [
    "SOURCE_POLICY",
    "MPOLICY",
    "DIVIDEND_OPTION",
    "ACCUM_DIVIDENDS",
    "OPENING_TYPE3",
    "OPENING_TYPE6",
    "WINDOW_TYPE3",
    "WINDOW_TYPE6",
    "WINDOW_TYPE7",
    "LEDGER_TOTAL",
    "VARIANCE",
    "STATUS",
]


def default_derivation_rules_path() -> str:
    return _DEFAULT_RULES_PATH


def load_dividend_rules(path: str | None = None) -> dict:
    rules_path = path or _DEFAULT_RULES_PATH
    if not os.path.isfile(rules_path):
        return {}
    with open(rules_path, encoding="utf-8") as fh:
        return json.load(fh)


def _norm_pactg_code(val: Any) -> str:
    """PACTG codes appear 3- or 4-digit; normalize to zero-padded 4."""
    s = "".join(ch for ch in str(val).strip() if ch.isdigit())
    if not s:
        return ""
    return s.zfill(4)[-4:]


def _money_float(val: Any) -> float:
    s = str(val or "").strip().replace(",", "")
    if not s or s.lower() in ("nan", "none", "null"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _money_str(amount: float) -> str:
    return f"{amount:.2f}"


def _fmt_date_yyyymmdd(val: Any) -> str:
    digits = "".join(ch for ch in str(val or "").strip() if ch.isdigit())
    return digits[:8] if len(digits) >= 8 else ""


def _rules_election_codes(rules: dict) -> dict[str, str]:
    raw = rules.get("pactg_election_codes") or _DEFAULT_ELECTION_CODES
    return {_norm_pactg_code(k): str(v).strip() for k, v in raw.items() if _norm_pactg_code(k)}


def _rules_option_map(rules: dict) -> dict[str, str]:
    raw = rules.get("dividend_option_mbentyp") or _DEFAULT_OPTION_MAP
    return {str(k).strip(): str(v).strip() for k, v in raw.items()}


def _rules_replace_types(rules: dict) -> frozenset[str]:
    raw = rules.get("mbentyp_replace_on_rerun") or sorted(_DEFAULT_REPLACE_TYPES)
    return frozenset(str(t).strip() for t in raw)


def _rules_accumulation(rules: dict) -> dict[str, str]:
    """Issue #117 accumulation-ledger codes (Help 6.5 p.649)."""
    types = rules.get("accumulation_mbentyp") or {}
    return {
        "account": _norm_pactg_code(rules.get("accumulation_account") or _DEFAULT_ACCUM_ACCOUNT),
        "interest_code": _norm_pactg_code(
            rules.get("pactg_interest_code") or _DEFAULT_INTEREST_CODE
        ),
        "interest_mbentyp": str(types.get("interest") or _DEFAULT_INTEREST_MBENTYP).strip(),
        "outflow_mbentyp": str(types.get("outflow") or _DEFAULT_OUTFLOW_MBENTYP).strip(),
        "opening_mbentyp": str(
            rules.get("accumulation_opening_mbentyp") or _DEFAULT_ACCUM_OPENING_MBENTYP
        ).strip(),
    }


def _in_crosswalk(pol: str, cw_map: dict[str, str] | None) -> bool:
    """Membership test mirroring the Issue #54 loan converter; empty map = no filter."""
    if not cw_map:
        return True
    key = pol.strip().upper()
    return key in cw_map or pol.strip() in cw_map


def build_layer_a_transactions(
    pactg_path: str,
    *,
    election_codes: dict[str, str],
    cw_map: dict[str, str] | None = None,
    exclude_reversed: bool = True,
    accumulation: dict[str, str] | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """
    Stream PACTG and emit one QuikBenh row per dividend election transaction.

    PACTG is ~800 MB; streamed with csv rather than loaded to a DataFrame.
    Only the election-code side is emitted — the premium, clearing and loan
    counterparties of the same transaction are deliberately skipped, otherwise
    each dividend would be counted twice.

    When `accumulation` is supplied (Issue #117) the same pass also collects the
    dividend-accumulation ledger legs, returned through stats so the Layer A
    contract used by Issue #114's reconciliation stays unchanged:

      interest_rows  debit 0641 / credit 0310  -> MBENTYP 6
      outflow_rows   debit 0310 / any credit   -> MBENTYP 7
      accum_back     credit 0310 under a non-dividend debit — reversal candidates
    """
    rows: list[dict[str, str]] = []
    contra: list[dict[str, str]] = []
    interest_rows: list[dict[str, str]] = []
    outflow_rows: list[dict[str, str]] = []
    accum_back: list[dict[str, str]] = []
    stats: dict[str, Any] = {
        "pactg_rows_read": 0,
        "election_rows": 0,
        "contra_side_excluded": 0,
        "reversed_excluded": 0,
        "orphan_no_crosswalk": 0,
        "bad_amount": 0,
        "bad_date": 0,
        "emit_passed": 0,
        "by_pactg_code": {},
        "by_mbentyp": {},
        "contra_rows": contra,
        "interest_rows": interest_rows,
        "outflow_rows": outflow_rows,
        "accum_back_rows": accum_back,
    }
    if not pactg_path or not os.path.isfile(pactg_path):
        return rows, stats

    csv.field_size_limit(10 ** 7)
    with open(pactg_path, newline="", encoding="latin-1") as fh:
        reader = csv.reader(fh)
        header = [str(c).replace("\ufeff", "").strip().upper() for c in next(reader)]
        try:
            ix = {
                name: header.index(name)
                for name in (
                    "CREDIT_CODE",
                    "DEBIT_CODE",
                    "POLICY_NUMBER",
                    "TRANS_AMOUNT",
                    "EFFECTIVE_DATE",
                    "DATE_REVERSED",
                )
            }
        except ValueError:
            return rows, stats

        width = len(header)
        for raw in reader:
            if len(raw) < width:
                continue
            pol = raw[ix["POLICY_NUMBER"]].strip()
            if not pol or pol.startswith("---"):
                continue
            stats["pactg_rows_read"] += 1

            credit = _norm_pactg_code(raw[ix["CREDIT_CODE"]])
            debit = _norm_pactg_code(raw[ix["DEBIT_CODE"]])

            # --- Issue #117: dividend accumulation ledger legs -------------------
            # Account 0310 holds the accumulation balance. Interest and dividends
            # are credited into it; withdrawals, death and surrender payouts debit
            # it. Issue #114 emitted only the dividend credits, so the QLAdmin
            # Dividend History window could not foot to its own balance footer.
            if accumulation:
                is_reversed = bool(raw[ix["DATE_REVERSED"]].strip().lstrip("0"))
                if not (exclude_reversed and is_reversed):
                    acct = accumulation["account"]
                    bucket = None
                    counterparty = ""
                    if debit == accumulation["interest_code"] and credit == acct:
                        bucket = interest_rows
                    elif debit == acct:
                        bucket = outflow_rows
                        counterparty = credit
                    elif (
                        credit == acct
                        and debit not in election_codes
                        and debit != accumulation["interest_code"]
                    ):
                        bucket = accum_back
                        counterparty = debit
                    if bucket is not None:
                        accum_amt = abs(_money_float(raw[ix["TRANS_AMOUNT"]]))
                        accum_date = _fmt_date_yyyymmdd(raw[ix["EFFECTIVE_DATE"]])
                        accum_mpol = (
                            format_qladmin_mpolicy(pol) if _in_crosswalk(pol, cw_map) else ""
                        )
                        if accum_mpol and accum_amt > 0 and accum_date:
                            bucket.append(
                                {
                                    "SOURCE_POLICY": pol,
                                    "MPOLICY": accum_mpol,
                                    "MDATE": accum_date,
                                    "MBEN": _money_str(accum_amt),
                                    "COUNTERPARTY_CODE": counterparty,
                                }
                            )
            # ---------------------------------------------------------------------

            # The dividend is credited to the policy on the DEBIT leg (e.g. debit 0517 /
            # credit 0112 buys paid-up additions). The same code on the CREDIT leg is the
            # contra side — either the clearing half of a posting already captured on its
            # debit leg, or a reversal that DATE_REVERSED did not flag. Emitting both legs
            # would count the dividend twice.
            if debit not in election_codes:
                if credit in election_codes:
                    stats["election_rows"] += 1
                    stats["contra_side_excluded"] += 1
                    contra.append(
                        {
                            "SOURCE_POLICY": pol,
                            "PACTG_CODE": credit,
                            "COUNTERPARTY_CODE": debit,
                            "EFFECTIVE_DATE": raw[ix["EFFECTIVE_DATE"]].strip(),
                            "AMOUNT": _money_str(abs(_money_float(raw[ix["TRANS_AMOUNT"]]))),
                        }
                    )
                continue
            hit = debit
            stats["election_rows"] += 1

            if exclude_reversed:
                rev = raw[ix["DATE_REVERSED"]].strip().lstrip("0")
                if rev:
                    stats["reversed_excluded"] += 1
                    continue

            if not _in_crosswalk(pol, cw_map):
                stats["orphan_no_crosswalk"] += 1
                continue
            mpolicy = format_qladmin_mpolicy(pol)
            if not mpolicy:
                stats["orphan_no_crosswalk"] += 1
                continue

            amount = abs(_money_float(raw[ix["TRANS_AMOUNT"]]))
            if amount <= 0:
                stats["bad_amount"] += 1
                continue
            mdate = _fmt_date_yyyymmdd(raw[ix["EFFECTIVE_DATE"]])
            if not mdate:
                stats["bad_date"] += 1
                continue

            mbentyp = election_codes[hit]
            rows.append(
                {
                    "MPOLICY": mpolicy,
                    "MBENTYP": mbentyp,
                    "MDATE": mdate,
                    "MBEN": _money_str(amount),
                }
            )
            stats["emit_passed"] += 1
            stats["by_pactg_code"][hit] = stats["by_pactg_code"].get(hit, 0) + 1
            stats["by_mbentyp"][mbentyp] = stats["by_mbentyp"].get(mbentyp, 0) + 1

    rows.sort(key=lambda r: (r["MPOLICY"], r["MDATE"], r["MBENTYP"]))
    return rows, stats


def build_lifetime_dividend_totals(
    ppbentyp_path: str,
    *,
    type_codes: list[str] | None = None,
    cw_map: dict[str, str] | None = None,
    balance_field: str = "ACCUM_DIVIDENDS",
) -> tuple[dict[str, dict], dict[str, float]]:
    """
    Per-policy lifetime dividends from PPBENTYP.

    DIVIDENDS_CREDITED is carried on BA rows only in this book; SU/PU/SL dividend
    columns are all zero, so unlike Issue #21F this is a single-component figure.
    Each target also carries BALANCE (ACCUM_DIVIDENDS), the accumulation figure the
    Issue #117 ledger has to foot to.
    Returns (targets_by_mpolicy, excluded_or_row_dollars_by_mpolicy).
    """
    targets: dict[str, dict] = {}
    or_excluded: dict[str, float] = {}
    if not ppbentyp_path or not os.path.isfile(ppbentyp_path):
        return targets, or_excluded

    keep = [str(t).strip().upper() for t in (type_codes or ["BA"])]
    df = pd.read_csv(
        ppbentyp_path, encoding="latin1", low_memory=False, dtype=str, on_bad_lines="skip"
    ).fillna("")
    df = normalize_columns(df)
    if "POLICY_NUMBER" not in df.columns or "DIVIDENDS_CREDITED" not in df.columns:
        return targets, or_excluded

    df = df[~df["POLICY_NUMBER"].str.contains("---", na=False)]
    df["_POL"] = df["POLICY_NUMBER"].str.strip()
    if "TYPE_CODE" in df.columns:
        df["_TC"] = df["TYPE_CODE"].astype(str).str.strip().str.upper()
    else:
        df["_TC"] = ""
    df["_AMT"] = df["DIVIDENDS_CREDITED"].map(_money_float)

    for pol, grp in df.groupby("_POL"):
        if not pol or not _in_crosswalk(pol, cw_map):
            continue
        mpolicy = format_qladmin_mpolicy(pol)
        if not mpolicy:
            continue
        kept = grp[grp["_TC"].isin(keep)]
        lifetime = float(kept["_AMT"].sum())
        other = float(grp.loc[~grp["_TC"].isin(keep), "_AMT"].sum())
        if other > 0:
            or_excluded[mpolicy] = other
        balance = 0.0
        if balance_field and balance_field in kept.columns and len(kept):
            balance = float(kept[balance_field].map(_money_float).sum())
        # Target set stays keyed on lifetime credits so Issue #114's reconciliation and
        # exception report are unchanged. No policy in this book carries a balance
        # without credits; one that did would be a source anomaly, not a conversion case.
        if lifetime > 0:
            option = ""
            if "DIVIDEND" in kept.columns and len(kept):
                option = str(kept["DIVIDEND"].iloc[0]).strip()
            targets[mpolicy] = {
                "SOURCE_POLICY": pol,
                "MPOLICY": mpolicy,
                "LIFETIME": lifetime,
                "OPTION": option,
                "BALANCE": balance,
            }
    return targets, or_excluded


def build_conversion_adjustment_rows(
    targets: dict[str, dict],
    layer_a_rows: list[dict[str, str]],
    *,
    option_map: dict[str, str],
    plug_date: str = _DEFAULT_PLUG_DATE,
    tolerance: float = _MONEY_TOLERANCE,
    or_excluded: dict[str, float] | None = None,
) -> tuple[list[dict[str, str]], list[dict], list[dict], dict[str, Any]]:
    """
    Layer B: one plug row per policy for the pre-extract dividend remainder.

    Positive gaps only. Non-positive gaps and undecidable benefit types are
    withheld to the exception report — never guessed into a benefit type.
    """
    or_excluded = or_excluded or {}
    layer_a_total: dict[str, float] = {}
    layer_a_count: dict[str, int] = {}
    for row in layer_a_rows:
        mp = row["MPOLICY"]
        layer_a_total[mp] = layer_a_total.get(mp, 0.0) + _money_float(row["MBEN"])
        layer_a_count[mp] = layer_a_count.get(mp, 0) + 1

    plug_rows: list[dict[str, str]] = []
    validation: list[dict] = []
    exceptions: list[dict] = []
    stats: dict[str, Any] = {
        "targets": len(targets),
        "plug_emitted": 0,
        "plug_dollars": 0.0,
        "exception_negative_or_zero_gap": 0,
        "exception_unmapped_option": 0,
        "exception_or_rows": len(or_excluded),
        "by_mbentyp": {},
    }

    for mpolicy in sorted(targets):
        rec = targets[mpolicy]
        a_total = round(layer_a_total.get(mpolicy, 0.0), 2)
        gap = round(rec["LIFETIME"] - a_total, 2)
        option = rec["OPTION"]
        mbentyp = option_map.get(option, "")

        if gap <= tolerance:
            status = "NEGATIVE_OR_ZERO_GAP"
            stats["exception_negative_or_zero_gap"] += 1
            exceptions.append(
                {
                    "SOURCE_POLICY": rec["SOURCE_POLICY"],
                    "MPOLICY": mpolicy,
                    "DIVIDEND_OPTION": option,
                    "LIFEPRO_LIFETIME": _money_str(rec["LIFETIME"]),
                    "LAYER_A_TOTAL": _money_str(a_total),
                    "GAP": _money_str(gap),
                    "REASON": status,
                    "NOTE": "Converted transactions meet or exceed the LifePRO lifetime total; "
                            "no adjustment row emitted",
                }
            )
        elif not mbentyp:
            status = f"UNMAPPED_OPTION_{option or 'BLANK'}"
            stats["exception_unmapped_option"] += 1
            note = (
                "LifePRO dividend option 6 = Reduce Loan; QLAdmin has no dividend-to-loan "
                "benefit type (OQ-1)"
                if option == "6"
                else "No dividend option recorded; benefit type not derivable (OQ-3)"
            )
            exceptions.append(
                {
                    "SOURCE_POLICY": rec["SOURCE_POLICY"],
                    "MPOLICY": mpolicy,
                    "DIVIDEND_OPTION": option,
                    "LIFEPRO_LIFETIME": _money_str(rec["LIFETIME"]),
                    "LAYER_A_TOTAL": _money_str(a_total),
                    "GAP": _money_str(gap),
                    "REASON": status,
                    "NOTE": note,
                }
            )
        else:
            status = "PLUG_EMITTED" if a_total > 0 else "OPENING_BALANCE"
            plug_rows.append(
                {
                    "MPOLICY": mpolicy,
                    "MBENTYP": mbentyp,
                    "MDATE": plug_date,
                    "MBEN": _money_str(gap),
                }
            )
            stats["plug_emitted"] += 1
            stats["plug_dollars"] = round(stats["plug_dollars"] + gap, 2)
            stats["by_mbentyp"][mbentyp] = stats["by_mbentyp"].get(mbentyp, 0) + 1

        emitted_plug = gap if status in ("PLUG_EMITTED", "OPENING_BALANCE") else 0.0
        final_total = round(a_total + emitted_plug, 2)
        validation.append(
            {
                "SOURCE_POLICY": rec["SOURCE_POLICY"],
                "MPOLICY": mpolicy,
                "DIVIDEND_OPTION": option,
                "MBENTYP": mbentyp,
                "LIFEPRO_LIFETIME": _money_str(rec["LIFETIME"]),
                "LAYER_A_TXN_COUNT": layer_a_count.get(mpolicy, 0),
                "LAYER_A_TOTAL": _money_str(a_total),
                "PLUG_AMOUNT": _money_str(emitted_plug) if emitted_plug else "",
                "FINAL_TOTAL": _money_str(final_total),
                "REMAINING_VARIANCE": _money_str(round(rec["LIFETIME"] - final_total, 2)),
                "STATUS": status,
            }
        )

    for mpolicy, amount in sorted(or_excluded.items()):
        exceptions.append(
            {
                "SOURCE_POLICY": targets.get(mpolicy, {}).get("SOURCE_POLICY", ""),
                "MPOLICY": mpolicy,
                "DIVIDEND_OPTION": targets.get(mpolicy, {}).get("OPTION", ""),
                "LIFEPRO_LIFETIME": "",
                "LAYER_A_TOTAL": "",
                "GAP": _money_str(amount),
                "REASON": "OR_ROW_DOLLARS_EXCLUDED",
                "NOTE": "Dividends on non-BA rider rows; excluded from the lifetime target to "
                        "match the Issue #21F premium treatment (OQ-2)",
            }
        )

    return plug_rows, validation, exceptions, stats


def net_accumulation_contras(
    outflow_rows: list[dict[str, str]],
    accum_back_rows: list[dict[str, str]],
    *,
    tolerance: float = _MONEY_TOLERANCE,
) -> tuple[list[dict[str, str]], list[dict]]:
    """
    Drop debit-310 postings that a later credit-310 entry put straight back.

    Policy 9010382426 debits $2,594.56 out of the accumulation on 2026-04-10 and
    credits the identical amount back on 2026-04-13 under a non-dividend code.
    DATE_REVERSED does not flag it. Emitting the debit leg as a type 7 would
    understate the balance by the full amount.
    """
    pending: dict[tuple[str, str], list[dict]] = {}
    for row in accum_back_rows:
        pending.setdefault((row["MPOLICY"], row["MBEN"]), []).append(row)

    kept: list[dict[str, str]] = []
    netted: list[dict] = []
    for row in outflow_rows:
        key = (row["MPOLICY"], row["MBEN"])
        match = pending.get(key)
        if match:
            back = match.pop(0)
            if not match:
                pending.pop(key, None)
            netted.append(
                {
                    "SOURCE_POLICY": row["SOURCE_POLICY"],
                    "MPOLICY": row["MPOLICY"],
                    "DIVIDEND_OPTION": "",
                    "LIFEPRO_LIFETIME": "",
                    "LAYER_A_TOTAL": "",
                    "GAP": row["MBEN"],
                    "REASON": "ACCUM_CONTRA_NETTED",
                    "NOTE": f"PACTG {row['MDATE']}: debit 0310 against "
                            f"{row['COUNTERPARTY_CODE']} reversed by a matching credit 0310 on "
                            f"{back['MDATE']} — nets to zero, not a surrendered accumulation",
                }
            )
            continue
        kept.append(row)
    return kept, netted


def build_accumulation_opening_rows(
    targets: dict[str, dict],
    layer_a_rows: list[dict[str, str]],
    plug_rows: list[dict[str, str]],
    interest_rows: list[dict[str, str]],
    outflow_rows: list[dict[str, str]],
    *,
    accumulation: dict[str, str],
    option_map: dict[str, str],
    plug_date: str = _DEFAULT_PLUG_DATE,
    tolerance: float = _MONEY_TOLERANCE,
) -> tuple[list[dict[str, str]], list[dict], list[dict], dict[str, Any]]:
    """
    Issue #117 Layer C: the pre-2018 interest half of the opening row.

    Issue #114 dates one row at 20171231 for the dividends credited before the PACTG
    window. That is the right type 3 amount but it is not the balance at that date —
    the account had also been earning interest. This adds the missing type 6 half so

        opening(3) + opening(6) + window(3) + window(6) - window(7) = ACCUM_DIVIDENDS

    A negative residual means value left the account before the window, which PACTG
    cannot see. Those policies are withheld to exceptions rather than plugged.
    """
    opening_mbentyp = accumulation["opening_mbentyp"]
    interest_mbentyp = accumulation["interest_mbentyp"]

    def _sum(rows: list[dict[str, str]], mpolicy: str, mbentyp: str | None = None) -> float:
        return round(
            sum(
                _money_float(r["MBEN"])
                for r in rows
                if r["MPOLICY"] == mpolicy and (mbentyp is None or r.get("MBENTYP") == mbentyp)
            ),
            2,
        )

    plug_by_policy: dict[str, float] = {}
    for row in plug_rows:
        if row["MBENTYP"] == opening_mbentyp:
            plug_by_policy[row["MPOLICY"]] = plug_by_policy.get(row["MPOLICY"], 0.0) + _money_float(
                row["MBEN"]
            )

    opening_rows: list[dict[str, str]] = []
    ledger: list[dict] = []
    exceptions: list[dict] = []
    stats: dict[str, Any] = {
        "balance_policies": 0,
        "opening_interest_emitted": 0,
        "opening_interest_dollars": 0.0,
        "ledger_balanced": 0,
        "ledger_shortfall": 0,
        "ledger_skipped_option": 0,
    }

    for mpolicy in sorted(targets):
        rec = targets[mpolicy]
        balance = round(float(rec.get("BALANCE") or 0.0), 2)
        if balance <= tolerance:
            continue
        stats["balance_policies"] += 1

        w3 = _sum(layer_a_rows, mpolicy, opening_mbentyp)
        w6 = _sum(interest_rows, mpolicy)
        w7 = _sum(outflow_rows, mpolicy)
        o3 = round(plug_by_policy.get(mpolicy, 0.0), 2)
        option = rec["OPTION"]

        if option_map.get(option, "") != opening_mbentyp:
            # Not an accumulate election (e.g. option 6 Reduce Loan, withheld by #114).
            # Report the balance so it stays visible; do not invent an opening.
            stats["ledger_skipped_option"] += 1
            ledger.append(
                {
                    "SOURCE_POLICY": rec["SOURCE_POLICY"],
                    "MPOLICY": mpolicy,
                    "DIVIDEND_OPTION": option,
                    "ACCUM_DIVIDENDS": _money_str(balance),
                    "OPENING_TYPE3": "",
                    "OPENING_TYPE6": "",
                    "WINDOW_TYPE3": _money_str(w3),
                    "WINDOW_TYPE6": _money_str(w6),
                    "WINDOW_TYPE7": _money_str(w7),
                    "LEDGER_TOTAL": _money_str(round(w3 + w6 - w7, 2)),
                    "VARIANCE": _money_str(round(balance - (w3 + w6 - w7), 2)),
                    "STATUS": "SKIPPED_UNMAPPED_OPTION",
                }
            )
            continue

        opening_total = round(balance - w3 - w6 + w7, 2)
        o6 = round(opening_total - o3, 2)

        if o6 > tolerance:
            opening_rows.append(
                {
                    "MPOLICY": mpolicy,
                    "MBENTYP": interest_mbentyp,
                    "MDATE": plug_date,
                    "MBEN": _money_str(o6),
                }
            )
            stats["opening_interest_emitted"] += 1
            stats["opening_interest_dollars"] = round(
                stats["opening_interest_dollars"] + o6, 2
            )
            status = "LEDGER_BALANCED"
            stats["ledger_balanced"] += 1
        elif o6 >= -tolerance:
            o6 = 0.0
            status = "LEDGER_BALANCED"
            stats["ledger_balanced"] += 1
        else:
            shortfall = o6
            o6 = 0.0
            status = "ACCUM_OPENING_SHORTFALL"
            stats["ledger_shortfall"] += 1
            exceptions.append(
                {
                    "SOURCE_POLICY": rec["SOURCE_POLICY"],
                    "MPOLICY": mpolicy,
                    "DIVIDEND_OPTION": option,
                    "LIFEPRO_LIFETIME": _money_str(rec["LIFETIME"]),
                    "LAYER_A_TOTAL": _money_str(w3),
                    "GAP": _money_str(round(-shortfall, 2)),
                    "REASON": status,
                    "NOTE": "Dividends credited exceed the accumulation balance, so value left "
                            "the account before the PACTG window. Either a pre-2018 withdrawal "
                            "or a dividend option change; no opening interest emitted and no "
                            "type 7 guessed (OQ-1)",
                }
            )

        ledger_total = round(o3 + o6 + w3 + w6 - w7, 2)
        ledger.append(
            {
                "SOURCE_POLICY": rec["SOURCE_POLICY"],
                "MPOLICY": mpolicy,
                "DIVIDEND_OPTION": option,
                "ACCUM_DIVIDENDS": _money_str(balance),
                "OPENING_TYPE3": _money_str(o3),
                "OPENING_TYPE6": _money_str(o6),
                "WINDOW_TYPE3": _money_str(w3),
                "WINDOW_TYPE6": _money_str(w6),
                "WINDOW_TYPE7": _money_str(w7),
                "LEDGER_TOTAL": _money_str(ledger_total),
                "VARIANCE": _money_str(round(balance - ledger_total, 2)),
                "STATUS": status,
            }
        )

    return opening_rows, ledger, exceptions, stats


def _load_existing_benh(path: str | None) -> pd.DataFrame:
    if not path or not os.path.isfile(path):
        return pd.DataFrame(columns=QUIKBENH_SCHEMA)
    df = pd.read_csv(path, encoding="utf-8", dtype=str, on_bad_lines="skip").fillna("")
    df = normalize_columns(df)
    for col in QUIKBENH_SCHEMA:
        if col not in df.columns:
            df[col] = ""
    return df[QUIKBENH_SCHEMA].copy()


def convert_quikbenh_dividend_history(
    pactg_path: str,
    ppbentyp_path: str,
    *,
    cw_map: dict[str, str] | None = None,
    rules: dict | None = None,
    output_dir: str | None = None,
    existing_benh_path: str | None = None,
    reports_dir: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """
    Build dividend-history QuikBenh rows and merge with existing QuikBenh output.

    Returns:
        merged_df, dividend_df, plug_df, exceptions_df, stats
    """
    rules = rules or load_dividend_rules()
    election_codes = _rules_election_codes(rules)
    option_map = _rules_option_map(rules)
    replace_types = _rules_replace_types(rules)
    plug_date = str(rules.get("conversion_adjustment_date") or _DEFAULT_PLUG_DATE).strip()
    tolerance = float(rules.get("money_tolerance") or _MONEY_TOLERANCE)
    exclude_reversed = bool(rules.get("exclude_reversed_rows", True))
    lifetime_types = rules.get("lifetime_type_codes") or ["BA"]
    balance_field = str(rules.get("balance_field") or "ACCUM_DIVIDENDS").strip()
    accum_enabled = bool(rules.get("accumulation_opening_enabled", True))
    accumulation = _rules_accumulation(rules) if accum_enabled else None

    layer_a_rows, stats = build_layer_a_transactions(
        pactg_path,
        election_codes=election_codes,
        cw_map=cw_map,
        exclude_reversed=exclude_reversed,
        accumulation=accumulation,
    )
    stats["layer_a_dollars"] = round(sum(_money_float(r["MBEN"]) for r in layer_a_rows), 2)
    stats["layer_a_policies"] = len({r["MPOLICY"] for r in layer_a_rows})

    plug_rows: list[dict[str, str]] = []
    validation_rows: list[dict] = []
    exception_rows: list[dict] = []
    ledger_rows: list[dict] = []
    opening_rows: list[dict[str, str]] = []
    interest_rows: list[dict[str, str]] = []
    outflow_rows: list[dict[str, str]] = []
    targets: dict[str, dict] = {}
    if rules.get("conversion_adjustment_enabled", True):
        targets, or_excluded = build_lifetime_dividend_totals(
            ppbentyp_path,
            type_codes=lifetime_types,
            cw_map=cw_map,
            balance_field=balance_field,
        )
        plug_rows, validation_rows, exception_rows, plug_stats = build_conversion_adjustment_rows(
            targets,
            layer_a_rows,
            option_map=option_map,
            plug_date=plug_date,
            tolerance=tolerance,
            or_excluded=or_excluded,
        )
        for key, value in plug_stats.items():
            stats[key if key.startswith("plug") else f"plug_{key}"] = value
        stats["lifetime_target_dollars"] = round(sum(t["LIFETIME"] for t in targets.values()), 2)
        stats["lifetime_target_policies"] = len(targets)

    # --- Issue #117: dividend accumulation ledger (MBENTYP 6 / 7 + opening split) ---
    if accumulation:
        interest_rows = list(stats.get("interest_rows") or [])
        raw_outflow = list(stats.get("outflow_rows") or [])
        outflow_rows, netted = net_accumulation_contras(
            raw_outflow, list(stats.get("accum_back_rows") or []), tolerance=tolerance
        )
        exception_rows.extend(netted)

        for row in interest_rows:
            row["MBENTYP"] = accumulation["interest_mbentyp"]
        for row in outflow_rows:
            row["MBENTYP"] = accumulation["outflow_mbentyp"]

        if targets:
            opening_rows, ledger_rows, ledger_exceptions, ledger_stats = (
                build_accumulation_opening_rows(
                    targets,
                    layer_a_rows,
                    plug_rows,
                    interest_rows,
                    outflow_rows,
                    accumulation=accumulation,
                    option_map=option_map,
                    plug_date=plug_date,
                    tolerance=tolerance,
                )
            )
            exception_rows.extend(ledger_exceptions)
            for key, value in ledger_stats.items():
                stats[f"accum_{key}"] = value

        stats["accum_interest_rows"] = len(interest_rows)
        stats["accum_interest_dollars"] = round(
            sum(_money_float(r["MBEN"]) for r in interest_rows), 2
        )
        stats["accum_outflow_rows"] = len(outflow_rows)
        stats["accum_outflow_dollars"] = round(
            sum(_money_float(r["MBEN"]) for r in outflow_rows), 2
        )
        stats["accum_contra_netted"] = len(netted)

    for c in stats.get("contra_rows") or []:
        exception_rows.append(
            {
                "SOURCE_POLICY": c["SOURCE_POLICY"],
                "MPOLICY": format_qladmin_mpolicy(c["SOURCE_POLICY"]),
                "DIVIDEND_OPTION": "",
                "LIFEPRO_LIFETIME": "",
                "LAYER_A_TOTAL": "",
                "GAP": c["AMOUNT"],
                "REASON": "CONTRA_SIDE_NOT_EMITTED",
                "NOTE": f"PACTG {c['EFFECTIVE_DATE']}: election code {c['PACTG_CODE']} on the "
                        f"credit leg against {c['COUNTERPARTY_CODE']} — clearing half or "
                        "unflagged reversal, not a dividend credited",
            }
        )

    dividend_df = pd.DataFrame(layer_a_rows, columns=QUIKBENH_SCHEMA)
    plug_df = pd.DataFrame(plug_rows, columns=QUIKBENH_SCHEMA)
    accum_df = pd.DataFrame(
        sorted(
            interest_rows + outflow_rows + opening_rows,
            key=lambda r: (r["MPOLICY"], r["MDATE"], r["MBENTYP"]),
        ),
        columns=QUIKBENH_SCHEMA,
    )

    existing_df = _load_existing_benh(existing_benh_path)
    existing_types = existing_df["MBENTYP"].astype(str).str.strip()
    preserved_df = existing_df[~existing_types.isin(replace_types)].copy()

    stats["existing_rows"] = len(existing_df)
    stats["existing_preserved_rows"] = len(preserved_df)
    stats["existing_dividend_rows_removed"] = len(existing_df) - len(preserved_df)
    for t in rules.get("preserve_mbentyp") or ("8", "10", "11", "12"):
        stats[f"existing_type{t}_rows"] = int((existing_types == str(t)).sum())

    # Append rather than re-sort: existing rows keep their positions so regression
    # can prove byte-identical preservation of MBENTYP 8/10/11/12.
    frames = [f for f in (preserved_df, dividend_df, plug_df, accum_df) if len(f)]
    merged_df = (
        pd.concat(frames, ignore_index=True) if frames
        else pd.DataFrame(columns=QUIKBENH_SCHEMA)
    )
    merged_df = merged_df.reindex(columns=QUIKBENH_SCHEMA).fillna("")

    exceptions_df = pd.DataFrame(exception_rows, columns=EXCEPTION_FIELDS)
    stats["rows_added"] = len(dividend_df) + len(plug_df) + len(accum_df)
    stats["merged_rows"] = len(merged_df)
    stats["emit_exceptions"] = len(exceptions_df)
    stats["reconciled_dollars"] = round(
        stats.get("layer_a_dollars", 0.0) + stats.get("plug_dollars", 0.0), 2
    )

    if reports_dir:
        write_issue114_reports(validation_rows, exception_rows, reports_dir)
        if accumulation:
            write_issue117_reports(ledger_rows, reports_dir)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stage_dir = os.path.join(output_dir, str(rules.get("staging_subdir") or "staged"))
        os.makedirs(stage_dir, exist_ok=True)
        dividend_df.to_csv(
            os.path.join(stage_dir, f"quikbenh_dividend_emit_{stamp}.csv"), index=False
        )
        plug_df.to_csv(
            os.path.join(stage_dir, f"quikbenh_dividend_plug_{stamp}.csv"), index=False
        )
        if len(accum_df):
            accum_df.to_csv(
                os.path.join(stage_dir, f"quikbenh_dividend_accum_{stamp}.csv"), index=False
            )
        exceptions_df.to_csv(
            os.path.join(stage_dir, f"quikbenh_dividend_exceptions_{stamp}.csv"), index=False
        )
        with open(
            os.path.join(output_dir, "quikbenh_dividend_emit_summary.txt"), "w", encoding="utf-8"
        ) as fh:
            fh.write(f"Issue #114 QuikBenh dividend history emit @ {stamp}\n")
            for key in (
                "pactg_rows_read",
                "election_rows",
                "reversed_excluded",
                "orphan_no_crosswalk",
                "emit_passed",
                "layer_a_dollars",
                "layer_a_policies",
                "lifetime_target_policies",
                "lifetime_target_dollars",
                "plug_emitted",
                "plug_dollars",
                "plug_exception_negative_or_zero_gap",
                "plug_exception_unmapped_option",
                "plug_exception_or_rows",
                "accum_interest_rows",
                "accum_interest_dollars",
                "accum_outflow_rows",
                "accum_outflow_dollars",
                "accum_contra_netted",
                "accum_balance_policies",
                "accum_opening_interest_emitted",
                "accum_opening_interest_dollars",
                "accum_ledger_balanced",
                "accum_ledger_shortfall",
                "accum_ledger_skipped_option",
                "rows_added",
                "existing_rows",
                "existing_type8_rows",
                "existing_type10_rows",
                "existing_type11_rows",
                "existing_type12_rows",
                "existing_dividend_rows_removed",
                "merged_rows",
                "reconciled_dollars",
            ):
                fh.write(f"{key}: {stats.get(key)}\n")
            fh.write(f"by_pactg_code: {stats.get('by_pactg_code')}\n")
            fh.write(f"layer_a_by_mbentyp: {stats.get('by_mbentyp')}\n")
            fh.write(f"plug_by_mbentyp: {stats.get('plug_by_mbentyp')}\n")

    return merged_df, dividend_df, plug_df, exceptions_df, stats


def write_issue114_reports(
    validation_rows: list[dict],
    exception_rows: list[dict],
    reports_dir: str,
) -> tuple[str, str]:
    """Write validation + exception CSVs under QLA_Migration/Reports/."""
    os.makedirs(reports_dir, exist_ok=True)
    val_path = os.path.join(reports_dir, "issue114_dividend_history_validation.csv")
    exc_path = os.path.join(reports_dir, "issue114_dividend_history_exceptions.csv")

    with open(val_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=VALIDATION_FIELDS)
        writer.writeheader()
        for row in validation_rows:
            writer.writerow({k: row.get(k, "") for k in VALIDATION_FIELDS})

    with open(exc_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=EXCEPTION_FIELDS)
        writer.writeheader()
        for row in exception_rows:
            writer.writerow({k: row.get(k, "") for k in EXCEPTION_FIELDS})

    return val_path, exc_path


def write_issue117_reports(ledger_rows: list[dict], reports_dir: str) -> str:
    """Per-policy proof that the emitted dividend ledger equals the QuikDvdp balance."""
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, "issue117_dividend_ledger_reconciliation.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LEDGER_FIELDS)
        writer.writeheader()
        for row in ledger_rows:
            writer.writerow({k: row.get(k, "") for k in LEDGER_FIELDS})
    return path


def detect_line_terminator(path: str, default: str = "\r\n") -> str:
    """Line ending already in use by an emitted table, so a rerun stays additive."""
    if not path or not os.path.isfile(path):
        return default
    with open(path, "rb") as fh:
        head = fh.read(65536)
    if b"\r\n" in head:
        return "\r\n"
    if b"\n" in head:
        return "\n"
    return default


def write_quikbenh_csv(df: pd.DataFrame, out_path: str, line_terminator: str | None = None) -> None:
    out = df.reindex(columns=QUIKBENH_SCHEMA).fillna("")
    term = line_terminator or detect_line_terminator(out_path)
    out.to_csv(out_path, index=False, lineterminator=term)
