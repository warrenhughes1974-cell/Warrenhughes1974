"""Issue #135 — MATCH_CSO_EXISTING_HEADER_ZERO_PAYEE quikclmp backfill.

Evidence-gated cohort path (not blind mass-apply):
  1) Inventory death-family CLAIMSTAT=2 headers with MPAID>0 and zero quikclmp.
  2) Classify each via Option-3 open 2032->1058 economic payouts + PRELSA PE/B1.
  3) Append payees only for SAFE_BACKFILL; hold incomplete/mismatch without fabricating.

Preserves quikclms money fields (MPAID/MFACE/NETDB/MINTAMT/PREMIUM/CLAIMSTAT).
Golden policy 9011156655C keeps explicit expected-payee checks.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from qla_core.issue78_quikclmp_recovery import QUIKCLMP_SCHEMA, _blank_payment_row, _build_display_name
from qla_core.normalize_utils import normalize

REASON = "MATCH_CSO_EXISTING_HEADER_ZERO_PAYEE"
TOLERANCE = 0.01

CLASS_SAFE = "SAFE_BACKFILL"
CLASS_HOLD_INCOMPLETE = "HOLD_INCOMPLETE"
CLASS_HOLD_MISMATCH = "HOLD_MISMATCH"
CLASS_NOT_IN_SCOPE = "NOT_IN_SCOPE"
CLASS_ALREADY = "ALREADY_BACKFILLED"

# Golden one-policy expected checks (preserve exact 9011156655C behavior).
GOLDEN_ALLOWLIST: dict[str, dict[str, Any]] = {
    "9011156655C": {
        "lifepro": "9011156655",
        "expected_mpaid": 5145.67,
        "expected_mface": 5000.00,
        "expected_mintamt": 0.00,
        "expected_premium": 0.00,
        "expected_payee_count": 4,
        "expected_payees": (
            {"mseq": 1, "name_id": "711250", "amount": 1286.42, "name": "LINVILLE L BRASWELL"},
            {"mseq": 2, "name_id": "711251", "amount": 1286.41, "name": "CHERI ROSE BRASWELL"},
            {"mseq": 3, "name_id": "711252", "amount": 1286.42, "name": "DANIEL L BRASWELL JR"},
            {"mseq": 4, "name_id": "711254", "amount": 1286.42, "name": "ROBERT C BRASWELL"},
        ),
    },
}

# Back-compat alias used by prior callers / validators.
ALLOWLIST = GOLDEN_ALLOWLIST

REVERSAL_CODES = frozenset({"Y", "R", "V"})


def _strip(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() in ("nan", "none"):
        return ""
    return text


def _money(value: Any) -> float:
    try:
        return float(str(value).replace(",", "").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


def _money_s(value: Any) -> str:
    return f"{_money(value):.2f}"


def _policy_digits(mpolicy: str) -> str:
    mp = normalize(mpolicy)
    if mp.endswith("C") and len(mp) >= 2:
        return mp[:-1]
    return "".join(ch for ch in mp if ch.isdigit())


def _norm_code(v: Any) -> str:
    digits = re.sub(r"[^0-9]", "", _strip(v))
    if not digits:
        return ""
    return str(int(digits)).zfill(4)


def _account_family(v: Any) -> str:
    digits = re.sub(r"[^0-9]", "", _strip(v))
    return digits[:4] if len(digits) >= 4 else digits


def _digits_acct(acct: Any) -> str:
    return "".join(ch for ch in _strip(acct) if ch.isdigit())


def _is_reversed_date(reversed_dt: Any) -> bool:
    s = _strip(reversed_dt)
    if not s or s in {"0", "0.0", "00", "00000000", "0/0/0", "00/00/0000"}:
        return False
    try:
        if float(s.replace(",", "")) == 0.0:
            return False
    except ValueError:
        pass
    return True


def _classify_pactg_economic_role(row: dict) -> str:
    """Narrow Option-3 role: ECONOMIC_DEATH_PAYOUT / LOOP_* / REVERSAL / OTHER."""
    if _is_reversed_date(row.get("date_reversed", "")):
        return "REVERSAL"
    dra = _account_family(row.get("debit_account", ""))
    cra = _account_family(row.get("credit_account", ""))
    dig_dr = _digits_acct(row.get("debit_account", ""))
    dig_cr = _digits_acct(row.get("credit_account", ""))
    dr = _strip(row.get("debit_code", ""))
    cr = _strip(row.get("credit_code", ""))
    if (dra == "1058" and cra == "1015") or (dra == "1015" and cra == "1058"):
        return "LOOP_REINSTATE"
    if dra == "1015" or cra == "1015":
        if dr in {"0094", "0090", "0020", "0530"} or cr in {
            "0094",
            "0090",
            "0020",
            "0530",
            "6044",
        }:
            return "LOOP_REINSTATE"
    if cr.startswith("6044") or dr.startswith("6044"):
        return "LOOP_REINSTATE"
    if dra == "2019" or cra == "2019" or "1058000256" in (dig_dr, dig_cr):
        return "LOOP_INTRACO"
    if dra == "2032" and cra == "1058" and cr in {"0094", "0090"}:
        return "ECONOMIC_DEATH_PAYOUT"
    return "OTHER"


def _loop_reissue_dates(rows: list[dict]) -> set[str]:
    dates: set[str] = set()
    for r in rows:
        if _is_reversed_date(r.get("date_reversed", "")):
            continue
        dra = _account_family(r.get("debit_account", ""))
        cra = _account_family(r.get("credit_account", ""))
        dig_dr = _digits_acct(r.get("debit_account", ""))
        dig_cr = _digits_acct(r.get("credit_account", ""))
        d = _strip(r.get("effective_date", ""))
        if not d:
            continue
        if dra == "1058" and cra in {"1015", "2019", "2031", "2039"}:
            dates.add(d)
        if dra == "2019" and cra == "1058":
            dates.add(d)
        if "1058000256" in (dig_dr, dig_cr) and (dra == "1058" or cra == "1058"):
            dates.add(d)
    return dates


def _payee_fields_from_rna(row: pd.Series) -> dict[str, str]:
    """Build payee identity fields; keep address lengths consistent with Output."""
    name = _build_display_name(row)
    suffix = _strip(row.get("INDIVIDUAL_SUFFIX", ""))
    if suffix and name and not name.upper().endswith(f" {suffix.upper()}"):
        name = f"{name} {suffix}"[:50]
    return {
        "MPAYNAME": name,
        "MPAYADDR1": _strip(row.get("ADDR_LINE_1", ""))[:40],
        "MPAYADDR2": _strip(row.get("ADDR_LINE_2", ""))[:40],
        "MPAYCITY": _strip(row.get("CITY", ""))[:50],
        "MPAYST": _strip(row.get("STATE", ""))[:2],
        "MPAYZIP": _strip(row.get("ZIP", ""))[:5],
        "MPAYZIP2": _strip(row.get("ZIP_EXTENSION", ""))[:4],
    }


def stream_pactg_with_payees(
    pactg_path: str | Path,
    policy_digits: set[str],
) -> dict[str, list[dict]]:
    """Stream PACTG once; include PAYEE_RELA_CODE / PAYEE_SEQUENCE for backfill."""
    buckets: dict[str, list[dict]] = defaultdict(list)
    if not policy_digits:
        return buckets
    csv.field_size_limit(10**7)
    with open(pactg_path, newline="", encoding="latin-1") as fh:
        reader = csv.reader(fh)
        header = [c.replace("\ufeff", "").strip().upper() for c in next(reader)]
        idx = {name: i for i, name in enumerate(header)}

        def col(*names: str) -> int | None:
            for n in names:
                if n in idx:
                    return idx[n]
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
        i_pr = col("PAYEE_RELA_CODE")
        i_ps = col("PAYEE_SEQUENCE")
        i_ctrl = col("CONTROL_NUMBER")
        if i_pol is None or i_amt is None:
            raise ValueError("PACTG missing POLICY_NUMBER / TRANS_AMOUNT")

        for raw in reader:
            if len(raw) <= i_pol:
                continue
            dig = _policy_digits(raw[i_pol])
            if dig not in policy_digits:
                continue
            buckets[dig].append(
                {
                    "policy_digits": dig,
                    "effective_date": _strip(raw[i_eff] if i_eff is not None else ""),
                    "debit_code": _norm_code(raw[i_dr] if i_dr is not None else ""),
                    "credit_code": _norm_code(raw[i_cr] if i_cr is not None else ""),
                    "debit_account": _strip(raw[i_dra] if i_dra is not None else ""),
                    "credit_account": _strip(raw[i_cra] if i_cra is not None else ""),
                    "trans_amount": round(_money(raw[i_amt]), 2),
                    "date_reversed": _strip(raw[i_rev] if i_rev is not None else ""),
                    "reversal_code": _strip(raw[i_rcode] if i_rcode is not None else ""),
                    "payee_rela_code": _strip(raw[i_pr] if i_pr is not None else ""),
                    "payee_sequence": _strip(raw[i_ps] if i_ps is not None else ""),
                    "control_number": _strip(raw[i_ctrl] if i_ctrl is not None else ""),
                }
            )
    return buckets


def _load_rna_payees_by_policy(
    rel_path: str | Path,
    policy_digits: set[str],
) -> dict[str, dict[str, dict[str, pd.Series]]]:
    """Map lifepro -> relate_code -> benefit_seq -> RNA row (PE preferred over B1)."""
    rel = pd.read_csv(
        rel_path,
        encoding="latin1",
        dtype=str,
        engine="python",
        on_bad_lines="skip",
    )
    rel.columns = [_strip(c) for c in rel.columns]
    out: dict[str, dict[str, dict[str, pd.Series]]] = {}
    if "POLICY_NUMBER" not in rel.columns or "RELATE_CODE" not in rel.columns:
        return out
    pol = rel[rel["POLICY_NUMBER"].astype(str).str.strip().isin(policy_digits)].copy()
    for _, row in pol.iterrows():
        dig = _strip(row.get("POLICY_NUMBER", ""))
        code = _strip(row.get("RELATE_CODE", ""))
        if code not in {"PE", "B1"}:
            continue
        seq = _strip(row.get("BENEFIT_SEQ_NUMBER", ""))
        if not seq or seq == "0":
            continue
        out.setdefault(dig, {}).setdefault(code, {})
        if seq not in out[dig][code]:
            out[dig][code][seq] = row
    return out


def _load_rna_pe(rel_path: str | Path, lifepro: str) -> dict[str, pd.Series]:
    """Map BENEFIT_SEQ_NUMBER -> PE RNA row for one LifePRO policy (back-compat)."""
    packed = _load_rna_payees_by_policy(rel_path, {lifepro})
    return packed.get(lifepro, {}).get("PE", {})


def _select_economic_payouts(rows: list[dict], target_mpaid: float) -> tuple[list[dict], str]:
    """Select open 2032->1058 PE payout legs summing to target; exclude loop dates."""
    loop = _loop_reissue_dates(rows)
    eco: list[dict] = []
    for row in rows:
        if _classify_pactg_economic_role(row) != "ECONOMIC_DEATH_PAYOUT":
            continue
        if _strip(row.get("reversal_code", "")) in REVERSAL_CODES:
            continue
        if _strip(row.get("effective_date", "")) in loop:
            continue
        eco.append(row)
    if not eco:
        return [], "no_open_2032_to_1058_economic_payout"
    eco_sum = round(sum(float(x["trans_amount"]) for x in eco), 2)
    if abs(eco_sum - target_mpaid) <= TOLERANCE:
        return eco, "eco_full_sum_match"
    bydate: dict[str, list[dict]] = defaultdict(list)
    for x in eco:
        bydate[_strip(x.get("effective_date", ""))].append(x)
    for d in sorted(bydate):
        xs = bydate[d]
        s = round(sum(float(x["trans_amount"]) for x in xs), 2)
        if abs(s - target_mpaid) <= TOLERANCE:
            return xs, f"eco_date_sum_match:{d}"
        seen: set[float] = set()
        uniq: list[dict] = []
        for x in xs:
            a = round(float(x["trans_amount"]), 2)
            if a in seen:
                continue
            seen.add(a)
            uniq.append(x)
        if abs(round(sum(float(x["trans_amount"]) for x in uniq), 2) - target_mpaid) <= TOLERANCE:
            return uniq, f"eco_date_unique_sum_match:{d}"
    return [], f"eco_sum={eco_sum}!=mpaid={target_mpaid:.2f}"


def inventory_match_cso_zero_payee_cohort(
    clms_df: pd.DataFrame,
    clmp_df: pd.DataFrame,
    *,
    recon_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Inventory MATCH_CSO death headers with MPAID>0 and zero live quikclmp rows.

    Prefer recon MATCH_CSO list when available; always re-check live Output payee count.
    """
    clms = clms_df.copy().fillna("")
    clmp = clmp_df.copy().fillna("")
    clmp_cnt = clmp.groupby(clmp["MPOLICY"].map(_strip)).size().to_dict()

    rows: list[dict[str, Any]] = []
    if recon_path and Path(recon_path).is_file():
        recon = pd.read_csv(recon_path, dtype=str).fillna("")
        m = recon[recon["proposed_rule_class"].map(_strip) == "MATCH_CSO"].copy()
        m["death_mpaid_n"] = m["death_mpaid"].map(_money)
        m["payee_rows_recon"] = m["payee_rows"].map(lambda x: int(float(x or 0)))
        seed = m[(m["death_mpaid_n"] > 0) & (m["payee_rows_recon"] == 0)]
        for _, r in seed.iterrows():
            pol = _strip(r["mpolicy"])
            dig = _strip(r.get("policy_digits", "")) or _policy_digits(pol)
            hdr = clms[
                (clms["MPOLICY"].map(_strip) == pol)
                & (clms["CLAIMSTAT"].map(_strip) == "2")
            ]
            if not len(hdr):
                continue
            h0 = hdr.iloc[0]
            mpaid = _money(h0.get("MPAID", 0))
            if mpaid <= 0:
                continue
            rows.append(
                {
                    "mpolicy": pol,
                    "policy_digits": dig,
                    "claimstat": _strip(h0.get("CLAIMSTAT", "")),
                    "mpaid": round(mpaid, 2),
                    "mface": round(_money(h0.get("MFACE", 0)), 2),
                    "mintamt": round(_money(h0.get("MINTAMT", 0)), 2),
                    "premium": round(_money(h0.get("PREMIUM", 0)), 2),
                    "cso_total_paid": round(_money(r.get("cso_total_paid", mpaid)), 2),
                    "live_payee_rows": int(clmp_cnt.get(pol, 0)),
                    "recon_payee_rows": int(r["payee_rows_recon"]),
                    "source": "recon_MATCH_CSO",
                }
            )
    else:
        # Fallback: live Output death headers with MPAID>0 and zero payees
        death = clms[clms["CLAIMSTAT"].map(_strip) == "2"].copy()
        for _, h0 in death.iterrows():
            pol = _strip(h0.get("MPOLICY", ""))
            mpaid = _money(h0.get("MPAID", 0))
            if mpaid <= 0 or int(clmp_cnt.get(pol, 0)) > 0:
                continue
            rows.append(
                {
                    "mpolicy": pol,
                    "policy_digits": _policy_digits(pol),
                    "claimstat": "2",
                    "mpaid": round(mpaid, 2),
                    "mface": round(_money(h0.get("MFACE", 0)), 2),
                    "mintamt": round(_money(h0.get("MINTAMT", 0)), 2),
                    "premium": round(_money(h0.get("PREMIUM", 0)), 2),
                    "cso_total_paid": round(mpaid, 2),
                    "live_payee_rows": 0,
                    "recon_payee_rows": "",
                    "source": "live_output_death_zero_payee",
                }
            )
    return pd.DataFrame(rows)


def classify_zero_payee_policy(
    *,
    mpolicy: str,
    policy_digits: str,
    mpaid: float,
    cso_total_paid: float,
    live_payee_rows: int,
    claimstat: str,
    pactg_rows: list[dict],
    rna_by_code: dict[str, dict[str, pd.Series]],
) -> dict[str, Any]:
    """Classify one cohort policy for safe payee backfill."""
    base = {
        "mpolicy": mpolicy,
        "policy_digits": policy_digits,
        "mpaid": round(mpaid, 2),
        "cso_total_paid": round(cso_total_paid, 2),
        "live_payee_rows": int(live_payee_rows),
        "claimstat": claimstat,
        "class": CLASS_NOT_IN_SCOPE,
        "reason": "",
        "eco_n": 0,
        "eco_sum": 0.0,
        "payee_n": 0,
        "selection_rule": "",
        "payee_evidence": "",
    }
    if claimstat != "2" or mpaid <= 0:
        base["reason"] = "non_death_or_no_positive_header"
        return base
    if live_payee_rows > 0:
        base["class"] = CLASS_ALREADY
        base["reason"] = f"already_has_payees={live_payee_rows}"
        base["payee_n"] = int(live_payee_rows)
        return base
    if abs(mpaid - cso_total_paid) > TOLERANCE:
        base["class"] = CLASS_HOLD_MISMATCH
        base["reason"] = f"mpaid={mpaid}!=cso={cso_total_paid}"
        return base

    selected, sel_rule = _select_economic_payouts(pactg_rows, mpaid)
    base["selection_rule"] = sel_rule
    if not selected:
        if sel_rule.startswith("eco_sum="):
            base["class"] = CLASS_HOLD_MISMATCH
            base["reason"] = sel_rule
            eco_all = [
                r
                for r in pactg_rows
                if _classify_pactg_economic_role(r) == "ECONOMIC_DEATH_PAYOUT"
            ]
            base["eco_n"] = len(eco_all)
            base["eco_sum"] = round(sum(float(x["trans_amount"]) for x in eco_all), 2)
        else:
            base["class"] = CLASS_HOLD_INCOMPLETE
            base["reason"] = sel_rule
        return base

    eco_sum = round(sum(float(x["trans_amount"]) for x in selected), 2)
    base["eco_n"] = len(selected)
    base["eco_sum"] = eco_sum

    pe_map = rna_by_code.get("PE", {})
    b1_map = rna_by_code.get("B1", {})
    built: list[dict[str, Any]] = []
    seen_seq: set[str] = set()
    for x in selected:
        rela = _strip(x.get("payee_rela_code", ""))
        seq = _strip(x.get("payee_sequence", ""))
        amt = round(float(x["trans_amount"]), 2)
        rna_row = None
        used_code = ""
        if rela in {"PE", "B1"} and seq:
            if rela == "PE" and seq in pe_map:
                rna_row = pe_map[seq]
                used_code = "PE"
            elif rela == "B1" and seq in b1_map:
                rna_row = b1_map[seq]
                used_code = "B1"
            elif rela == "PE" and seq in b1_map and seq not in pe_map:
                # Explicit PE payout but only B1 identity at same seq — still usable.
                rna_row = b1_map[seq]
                used_code = "B1_FOR_PE"
        if rna_row is None:
            base["class"] = CLASS_HOLD_INCOMPLETE
            base["reason"] = (
                f"missing_rna_for_payee rela={rela!r} seq={seq!r} "
                f"pe_keys={sorted(pe_map)[:8]} b1_keys={sorted(b1_map)[:8]}"
            )
            return base
        if seq in seen_seq:
            base["class"] = CLASS_HOLD_INCOMPLETE
            base["reason"] = f"duplicate_payee_sequence={seq}"
            return base
        seen_seq.add(seq)
        name_id = _strip(rna_row.get("NAME_ID", ""))
        fields = _payee_fields_from_rna(rna_row)
        if not _strip(fields.get("MPAYNAME", "")):
            base["class"] = CLASS_HOLD_INCOMPLETE
            base["reason"] = f"blank_payee_name seq={seq} name_id={name_id}"
            return base
        built.append(
            {
                "mseq": seq,
                "name_id": name_id,
                "amount": amt,
                "name": fields["MPAYNAME"],
                "relate_used": used_code,
                "effective_date": _strip(x.get("effective_date", "")),
                "rna_row": rna_row,
                "payee_fields": fields,
            }
        )

    payee_sum = round(sum(float(p["amount"]) for p in built), 2)
    if abs(payee_sum - mpaid) > TOLERANCE:
        base["class"] = CLASS_HOLD_MISMATCH
        base["reason"] = f"payee_sum={payee_sum}!=mpaid={mpaid}"
        return base

    base["class"] = CLASS_SAFE
    base["reason"] = "open_2032_to_1058_pe_match_mpaid"
    base["payee_n"] = len(built)
    base["payee_evidence"] = "|".join(
        f"{p['mseq']}:{p['name_id']}:{p['amount']:.2f}" for p in built
    )
    base["_payees"] = built
    return base


def classify_match_cso_zero_payee_cohort(
    cohort_df: pd.DataFrame,
    *,
    prelsa_path: str | Path,
    pactg_path: str | Path,
    pactg_buckets: dict[str, list[dict]] | None = None,
) -> pd.DataFrame:
    """Classify full inventory; returns one row per policy (no _payees column)."""
    if cohort_df is None or cohort_df.empty:
        return pd.DataFrame()
    digits = set(cohort_df["policy_digits"].map(_strip))
    buckets = pactg_buckets if pactg_buckets is not None else stream_pactg_with_payees(
        pactg_path, digits
    )
    rna = _load_rna_payees_by_policy(prelsa_path, digits)
    out_rows: list[dict[str, Any]] = []
    for _, r in cohort_df.iterrows():
        pol = _strip(r["mpolicy"])
        dig = _strip(r["policy_digits"])
        cls = classify_zero_payee_policy(
            mpolicy=pol,
            policy_digits=dig,
            mpaid=_money(r.get("mpaid", 0)),
            cso_total_paid=_money(r.get("cso_total_paid", r.get("mpaid", 0))),
            live_payee_rows=int(r.get("live_payee_rows", 0) or 0),
            claimstat=_strip(r.get("claimstat", "2")) or "2",
            pactg_rows=buckets.get(dig, []),
            rna_by_code=rna.get(dig, {}),
        )
        cls.pop("_payees", None)
        out_rows.append(cls)
    return pd.DataFrame(out_rows)


def build_allowlist_from_classification(
    class_df: pd.DataFrame,
    *,
    cohort_df: pd.DataFrame | None = None,
    prelsa_path: str | Path | None = None,
    pactg_path: str | Path | None = None,
    pactg_buckets: dict[str, list[dict]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build apply allowlist for SAFE_BACKFILL rows; merge golden expected checks."""
    allow: dict[str, dict[str, Any]] = {}
    if class_df is None or class_df.empty:
        return allow
    safe = class_df[class_df["class"].map(_strip) == CLASS_SAFE]
    if safe.empty:
        return allow

    # Re-classify with payee payloads for allowlist construction.
    digits = set(safe["policy_digits"].map(_strip))
    buckets = pactg_buckets
    if buckets is None and pactg_path is not None:
        buckets = stream_pactg_with_payees(pactg_path, digits)
    buckets = buckets or {}
    rna = (
        _load_rna_payees_by_policy(prelsa_path, digits)
        if prelsa_path is not None
        else {}
    )
    cohort_idx = {}
    if cohort_df is not None and not cohort_df.empty:
        cohort_idx = {
            _strip(r["mpolicy"]): r for _, r in cohort_df.iterrows()
        }

    for _, r in safe.iterrows():
        pol = _strip(r["mpolicy"])
        dig = _strip(r["policy_digits"])
        mpaid = _money(r.get("mpaid", 0))
        cso = _money(r.get("cso_total_paid", mpaid))
        live = int(r.get("live_payee_rows", 0) or 0)
        src = cohort_idx.get(pol)
        mface = _money(src.get("mface", 0)) if src is not None else 0.0
        mint = _money(src.get("mintamt", 0)) if src is not None else 0.0
        prem = _money(src.get("premium", 0)) if src is not None else 0.0
        cls = classify_zero_payee_policy(
            mpolicy=pol,
            policy_digits=dig,
            mpaid=mpaid,
            cso_total_paid=cso,
            live_payee_rows=live,
            claimstat=_strip(r.get("claimstat", "2")) or "2",
            pactg_rows=buckets.get(dig, []),
            rna_by_code=rna.get(dig, {}),
        )
        payees = cls.get("_payees") or []
        if cls.get("class") != CLASS_SAFE or not payees:
            continue
        cfg: dict[str, Any] = {
            "lifepro": dig,
            "expected_mpaid": mpaid,
            "expected_mface": mface if mface else mpaid,  # soft: apply uses live header
            "expected_mintamt": mint,
            "expected_premium": prem,
            "expected_payee_count": len(payees),
            "expected_payees": tuple(
                {
                    "mseq": int(p["mseq"]) if str(p["mseq"]).isdigit() else p["mseq"],
                    "name_id": p["name_id"],
                    "amount": float(p["amount"]),
                    "name": p["name"],
                }
                for p in payees
            ),
            "selection_rule": cls.get("selection_rule", ""),
        }
        # Soft-match mface: allow live header mface during apply (see apply gate).
        cfg["soft_mface"] = True
        if pol in GOLDEN_ALLOWLIST:
            cfg = dict(GOLDEN_ALLOWLIST[pol])
            cfg["soft_mface"] = False
        allow[pol] = cfg
    return allow


def discover_safe_allowlist(
    clms_df: pd.DataFrame,
    clmp_df: pd.DataFrame,
    *,
    prelsa_path: str | Path,
    pactg_path: str | Path,
    recon_path: str | Path | None = None,
) -> tuple[dict[str, dict[str, Any]], pd.DataFrame, pd.DataFrame, dict[str, list[dict]]]:
    """Inventory + classify + build SAFE allowlist. Returns allow, cohort, class_df, buckets."""
    cohort = inventory_match_cso_zero_payee_cohort(
        clms_df, clmp_df, recon_path=recon_path
    )
    digits = set(cohort["policy_digits"].map(_strip)) if len(cohort) else set()
    buckets = stream_pactg_with_payees(pactg_path, digits)
    class_df = classify_match_cso_zero_payee_cohort(
        cohort,
        prelsa_path=prelsa_path,
        pactg_path=pactg_path,
        pactg_buckets=buckets,
    )
    allow = build_allowlist_from_classification(
        class_df,
        cohort_df=cohort,
        prelsa_path=prelsa_path,
        pactg_path=pactg_path,
        pactg_buckets=buckets,
    )
    return allow, cohort, class_df, buckets


def _load_pactg_pe_payouts(pactg_path: str | Path, lifepro: str) -> pd.DataFrame:
    """Back-compat: economic PE payouts for one policy as DataFrame."""
    buckets = stream_pactg_with_payees(pactg_path, {lifepro})
    rows = buckets.get(lifepro, [])
    # Target unknown here — return all open economic PE legs (caller validates sum).
    loop = _loop_reissue_dates(rows)
    eco = []
    for row in rows:
        if _classify_pactg_economic_role(row) != "ECONOMIC_DEATH_PAYOUT":
            continue
        if _strip(row.get("reversal_code", "")) in REVERSAL_CODES:
            continue
        if _strip(row.get("effective_date", "")) in loop:
            continue
        if _strip(row.get("payee_rela_code", "")) not in {"PE", "B1"}:
            continue
        eco.append(row)
    if not eco:
        return pd.DataFrame()
    out = pd.DataFrame(eco)
    out["AMT"] = out["trans_amount"].astype(float)
    out["EFF"] = out["effective_date"].map(_strip)
    out["CHECK"] = out["control_number"].map(_strip)
    out["PE_SEQ"] = out["payee_sequence"].map(_strip)
    out["_seq_n"] = pd.to_numeric(out["PE_SEQ"], errors="coerce").fillna(9999)
    return out.sort_values(["_seq_n", "EFF", "AMT"]).reset_index(drop=True)


def apply_match_cso_zero_payee_backfill(
    clms_df: pd.DataFrame,
    clmp_df: pd.DataFrame,
    *,
    prelsa_path: str | Path,
    pactg_path: str | Path,
    allowlist: dict[str, dict[str, Any]] | None = None,
    auto_discover: bool = False,
    recon_path: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """
    Append quikclmp rows for SAFE / allowlisted MATCH_CSO zero-payee policies.

    Default allowlist remains golden-only for re-batch safety unless auto_discover=True
    or an explicit allowlist is provided (cohort apply script).
    """
    stats: dict[str, Any] = {
        "applied": False,
        "policies_backfilled": 0,
        "rows_added": 0,
        "skipped": [],
        "audit_rows": [],
        "reason_class": REASON,
        "allowlist_policies": [],
        "discovery": {},
    }
    clms = clms_df.copy().fillna("")
    clmp = clmp_df.copy().fillna("")
    for col in QUIKCLMP_SCHEMA:
        if col not in clmp.columns:
            clmp[col] = ""

    allow = allowlist
    if allow is None and auto_discover:
        allow, cohort, class_df, _buckets = discover_safe_allowlist(
            clms,
            clmp,
            prelsa_path=prelsa_path,
            pactg_path=pactg_path,
            recon_path=recon_path,
        )
        stats["discovery"] = {
            "cohort_n": int(len(cohort)),
            "class_counts": {
                str(k): int(v)
                for k, v in class_df["class"].value_counts().to_dict().items()
            }
            if len(class_df)
            else {},
            "safe_n": int(len(allow)),
        }
        stats["_cohort_df"] = cohort
        stats["_class_df"] = class_df
    elif allow is None:
        allow = dict(GOLDEN_ALLOWLIST)

    stats["allowlist_policies"] = sorted(allow.keys())
    if not allow:
        stats["skipped"].append({"mpolicy": "", "reason": "empty_allowlist"})
        return clms, clmp, stats

    # One PACTG stream + one RNA load for the whole allowlist (not per-policy).
    allow_digits = {
        _strip(cfg.get("lifepro", "")) or _policy_digits(pol)
        for pol, cfg in allow.items()
    }
    pactg_buckets = stream_pactg_with_payees(pactg_path, allow_digits)
    rna_all = _load_rna_payees_by_policy(prelsa_path, allow_digits)

    new_rows: list[dict[str, str]] = []

    for mpolicy, cfg in allow.items():
        pol = _strip(mpolicy)
        lifepro = _strip(cfg.get("lifepro", "")) or _policy_digits(pol)
        hdr = clms[clms["MPOLICY"].map(_strip) == pol]
        if hdr.empty:
            stats["skipped"].append({"mpolicy": pol, "reason": "missing_quikclms_header"})
            continue
        existing = clmp[clmp["MPOLICY"].map(_strip) == pol]
        if len(existing):
            stats["skipped"].append(
                {"mpolicy": pol, "reason": f"already_has_payees={len(existing)}"}
            )
            continue

        death = hdr[hdr["CLAIMSTAT"].map(_strip).isin(["1", "2"])]
        use = death if len(death) else hdr
        # Prefer CLAIMSTAT=2
        pref = use[use["CLAIMSTAT"].map(_strip) == "2"]
        use = pref if len(pref) else use
        h0 = use.iloc[0]
        if _strip(h0.get("CLAIMSTAT", "")) != "2":
            stats["skipped"].append({"mpolicy": pol, "reason": "not_claimstat_2"})
            continue
        mpaid = _money(h0.get("MPAID", 0))
        mface = _money(h0.get("MFACE", 0))
        mintamt = _money(h0.get("MINTAMT", 0))
        premium = _money(h0.get("PREMIUM", 0))
        if mpaid <= 0:
            stats["skipped"].append({"mpolicy": pol, "reason": "mpaid_not_positive"})
            continue

        exp_mpaid = float(cfg.get("expected_mpaid", mpaid))
        exp_mface = float(cfg.get("expected_mface", mface))
        exp_mint = float(cfg.get("expected_mintamt", 0.0))
        exp_prem = float(cfg.get("expected_premium", 0.0))
        soft_mface = bool(cfg.get("soft_mface", False))
        if abs(mpaid - exp_mpaid) > TOLERANCE:
            stats["skipped"].append(
                {"mpolicy": pol, "reason": f"mpaid_mismatch={mpaid}!={exp_mpaid}"}
            )
            continue
        if not soft_mface and abs(mface - exp_mface) > TOLERANCE:
            stats["skipped"].append(
                {"mpolicy": pol, "reason": f"mface_mismatch={mface}!={exp_mface}"}
            )
            continue
        if abs(mintamt - exp_mint) > TOLERANCE:
            stats["skipped"].append(
                {"mpolicy": pol, "reason": f"mintamt_nonzero={mintamt}"}
            )
            continue
        if abs(premium - exp_prem) > TOLERANCE:
            stats["skipped"].append(
                {"mpolicy": pol, "reason": f"premium_nonzero={premium}"}
            )
            continue

        rna_packed = rna_all.get(lifepro, {})
        pe_rna = rna_packed.get("PE", {})
        b1_rna = rna_packed.get("B1", {})
        if not pe_rna and not b1_rna:
            stats["skipped"].append({"mpolicy": pol, "reason": "no_rna_pe_or_b1_payees"})
            continue

        selected, sel_rule = _select_economic_payouts(
            pactg_buckets.get(lifepro, []), mpaid
        )
        if not selected:
            stats["skipped"].append({"mpolicy": pol, "reason": f"select_fail:{sel_rule}"})
            continue
        payouts = pd.DataFrame(selected)
        payouts["AMT"] = payouts["trans_amount"].astype(float)
        payouts["EFF"] = payouts["effective_date"].map(_strip)
        payouts["PE_SEQ"] = payouts["payee_sequence"].map(_strip)
        payouts["RELA"] = payouts["payee_rela_code"].map(_strip)
        payouts["_seq_n"] = pd.to_numeric(payouts["PE_SEQ"], errors="coerce").fillna(9999)
        payouts = payouts.sort_values(["_seq_n", "EFF", "AMT"]).reset_index(drop=True)

        exp_n = int(cfg.get("expected_payee_count", 0) or 0)
        if exp_n and len(payouts) != exp_n:
            stats["skipped"].append(
                {"mpolicy": pol, "reason": f"payout_count={len(payouts)}!={exp_n}"}
            )
            continue

        payout_sum = round(float(payouts["AMT"].sum()), 2)
        if abs(payout_sum - mpaid) > TOLERANCE:
            stats["skipped"].append(
                {
                    "mpolicy": pol,
                    "reason": f"payout_sum={payout_sum}!=mpaid={mpaid}",
                }
            )
            continue

        mphase = _strip(h0.get("MPHASE", "1")) or "1"
        # QLAdmin indexes QUIKCLMP on MPOLICY+STR(MPHASE)+STR(MSEQ) and relates
        # from the claim header key. Payee MSEQ must match header MSEQ (usually 0);
        # duplicate keys are OK for multiple payees under one claim.
        header_mseq = _strip(h0.get("MSEQ", "0")) or "0"
        expected_by_name_id = {
            str(e["name_id"]): e for e in cfg.get("expected_payees", ()) if e.get("name_id") is not None
        }
        built: list[dict[str, str]] = []
        audit_detail: list[dict[str, Any]] = []

        for _, prow in payouts.iterrows():
            pe_seq = _strip(prow.get("PE_SEQ", ""))
            rela = _strip(prow.get("RELA", ""))
            rna_row = None
            if pe_seq in pe_rna:
                rna_row = pe_rna[pe_seq]
            elif pe_seq in b1_rna:
                rna_row = b1_rna[pe_seq]
            if rna_row is None:
                stats["skipped"].append(
                    {"mpolicy": pol, "reason": f"missing_rna_for_pe_seq={pe_seq}"}
                )
                built = []
                break
            name_id = _strip(rna_row.get("NAME_ID", ""))
            amt = round(float(prow["AMT"]), 2)
            mseq = header_mseq
            exp = expected_by_name_id.get(str(name_id))
            if exp is not None:
                if abs(amt - float(exp["amount"])) > TOLERANCE:
                    stats["skipped"].append(
                        {
                            "mpolicy": pol,
                            "reason": f"amt_mismatch_name_id{name_id}={amt}!={exp['amount']}",
                        }
                    )
                    built = []
                    break

            payee = _payee_fields_from_rna(rna_row)
            if exp is not None and _strip(payee.get("MPAYNAME", "")).upper() != _strip(
                exp.get("name", "")
            ).upper():
                stats["skipped"].append(
                    {
                        "mpolicy": pol,
                        "reason": (
                            f"name_mismatch_name_id{name_id}="
                            f"{payee.get('MPAYNAME')!r}!={exp.get('name')!r}"
                        ),
                    }
                )
                built = []
                break
            if not _strip(payee.get("MPAYNAME", "")):
                stats["skipped"].append(
                    {"mpolicy": pol, "reason": f"blank_name_pe_seq={pe_seq}"}
                )
                built = []
                break

            row = _blank_payment_row(pol, mphase)
            row.update(payee)
            row["MAMOUNT"] = _money_s(amt)
            row["MGROSS"] = _money_s(amt)
            eff = _strip(prow.get("EFF", ""))
            row["MCHKDATE"] = eff
            row["MPMTDATE"] = eff
            # Do not invent QLAdmin check numbers from PACTG CONTROL_NUMBER.
            row["MCHECKNO"] = "0"
            row["MSEQ"] = str(mseq)
            row["MHDPMT"] = "C"
            built.append(row)
            audit_detail.append(
                {
                    "mpolicy": pol,
                    "mseq": str(mseq),
                    "name_id": name_id,
                    "mpayname": row["MPAYNAME"],
                    "mamount": row["MAMOUNT"],
                    "mpayaddr1": row["MPAYADDR1"],
                    "mpaycity": row["MPAYCITY"],
                    "mpayst": row["MPAYST"],
                    "mpayzip": row["MPAYZIP"],
                    "mcheckno": row["MCHECKNO"],
                    "mchkdate": row["MCHKDATE"],
                    "pactg_pe_seq": pe_seq,
                    "pactg_rela": rela,
                    "pactg_eff": eff,
                    "reason": REASON,
                }
            )

        if not built:
            continue
        if exp_n and len(built) != exp_n:
            stats["skipped"].append(
                {"mpolicy": pol, "reason": f"built_count={len(built)}!={exp_n}"}
            )
            continue

        new_rows.extend(built)
        stats["policies_backfilled"] += 1
        stats["rows_added"] += len(built)
        stats["audit_rows"].extend(audit_detail)
        stats["audit_rows"].append(
            {
                "mpolicy": pol,
                "mseq": "SUMMARY",
                "name_id": "",
                "mpayname": "",
                "mamount": _money_s(payout_sum),
                "mpayaddr1": "",
                "mpaycity": "",
                "mpayst": "",
                "mpayzip": "",
                "mcheckno": "",
                "mchkdate": "",
                "pactg_pe_seq": "",
                "pactg_rela": "",
                "pactg_eff": "",
                "reason": REASON,
                "detail": (
                    f"appended={len(built)};mpaid={_money_s(mpaid)};"
                    f"mface={_money_s(mface)};mintamt={_money_s(mintamt)};"
                    f"premium={_money_s(premium)};header_unchanged=Y;"
                    f"selection={sel_rule}"
                ),
            }
        )

    if new_rows:
        add_df = pd.DataFrame(new_rows, columns=QUIKCLMP_SCHEMA)
        clmp = pd.concat(
            [clmp.reindex(columns=QUIKCLMP_SCHEMA, fill_value=""), add_df],
            ignore_index=True,
        )
        stats["applied"] = True

    return clms, clmp, stats


def write_zero_payee_backfill_audit(
    stats: dict[str, Any],
    evidence_dir: str | Path,
    *,
    cohort_df: pd.DataFrame | None = None,
    class_df: pd.DataFrame | None = None,
) -> dict[str, str]:
    """Write audit artifacts under Issue_135/evidence (not Output root)."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    cohort = cohort_df if cohort_df is not None else stats.get("_cohort_df")
    classes = class_df if class_df is not None else stats.get("_class_df")

    if isinstance(cohort, pd.DataFrame):
        p = evidence_dir / "issue135_match_cso_zero_payee_cohort_inventory.csv"
        cohort.to_csv(p, index=False, encoding="utf-8")
        paths["inventory"] = str(p)

    if isinstance(classes, pd.DataFrame):
        p = evidence_dir / "issue135_match_cso_zero_payee_classification.csv"
        classes.to_csv(p, index=False, encoding="utf-8")
        paths["classification"] = str(p)
        holds = classes[
            classes["class"].map(_strip).isin([CLASS_HOLD_INCOMPLETE, CLASS_HOLD_MISMATCH])
        ]
        hp = evidence_dir / "issue135_match_cso_zero_payee_holds.csv"
        holds.to_csv(hp, index=False, encoding="utf-8")
        paths["holds"] = str(hp)

    audit = pd.DataFrame(stats.get("audit_rows") or [])
    audit_path = evidence_dir / "issue135_match_cso_zero_payee_backfill_audit.csv"
    audit.to_csv(audit_path, index=False, encoding="utf-8")
    paths["audit"] = str(audit_path)

    # Keep prior single-policy filename as a compatibility pointer when golden applied.
    if any(_strip(a.get("mpolicy")) == "9011156655C" for a in (stats.get("audit_rows") or [])):
        compat = evidence_dir / "issue135_9011156655C_zero_payee_backfill_audit.csv"
        audit.to_csv(compat, index=False, encoding="utf-8")
        paths["audit_compat_9011156655C"] = str(compat)

    class_counts = {}
    if isinstance(classes, pd.DataFrame) and len(classes):
        class_counts = {
            str(k): int(v) for k, v in classes["class"].value_counts().to_dict().items()
        }

    summary = {
        "reason_class": stats.get("reason_class", REASON),
        "applied": bool(stats.get("applied")),
        "policies_backfilled": int(stats.get("policies_backfilled", 0) or 0),
        "rows_added": int(stats.get("rows_added", 0) or 0),
        "skipped_n": len(stats.get("skipped") or []),
        "skipped_sample": (stats.get("skipped") or [])[:20],
        "allowlist_n": len(stats.get("allowlist_policies") or []),
        "allowlist_policies_sample": (stats.get("allowlist_policies") or [])[:20],
        "class_counts": class_counts or stats.get("discovery", {}).get("class_counts", {}),
        "discovery": stats.get("discovery") or {},
        "golden_policy": "9011156655C",
        "note": (
            "Evidence-gated MATCH_CSO_EXISTING_HEADER_ZERO_PAYEE cohort backfill. "
            "SAFE_BACKFILL only; HOLD cases not fabricated. "
            "Issue #135 remains open (prior 9 HOLDs + residual zero-payee holds)."
        ),
    }
    summary_path = evidence_dir / "issue135_match_cso_zero_payee_backfill_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    paths["summary"] = str(summary_path)
    return paths
