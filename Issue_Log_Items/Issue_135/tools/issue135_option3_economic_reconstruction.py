#!/usr/bin/env python3
"""Issue #135 Option 3 — upstream economic payment reconstruction (controlled overlay).

Approved mechanism: correct economic payment events first, then derive both
quikclmp payee amounts and quikclms header MPAID from the corrected set.

Scope (this pass):
  - Apply only to Phase B CANDIDATE policies in AVAILABLE_MISMATCH (evidence-backed).
  - Do NOT invent settlements for the 459 Eric-supply gaps (absent from source).
  - Do NOT mutate production QLA_Migration/Output amounts (overlay staging only).
  - HOLD clearing/loan/interest residuals and any candidate that cannot match CSO.
  - Preserve Phase A MINTAMT=0; do not touch #134 MEMOTEXT or #78/#84/#85 logic.

Narrowest upstream location (analysis):
  Economic duplication enters via PACTG lifecycle/reinstatement/intraco legs that are
  treated as payout events before Phase 8–10a/10b derive quikclmp/quikclms. The safe
  correction point is a pre-derivation economic-event filter (claim/policy/date/payee/
  amount/account). Production app.py currently loads UAT candidate CSVs + post-emit
  hooks; wiring this filter into a full claims re-batch is a separate gate. This tool
  produces a controlled overlay proving the rule set on available candidates.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TOOLS))

from issue135_cso_pactg_recon import (  # noqa: E402
    TOLERANCE,
    _account_family,
    _money,
    _strip,
    is_reversed_date,
    load_cso,
    load_output_claims,
    resolve_pactg,
    stream_pactg_for_policies,
)

EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
DEFAULT_DEEP = EVIDENCE / "issue135_phase_b_mismatch_deep_dive.csv"
DEFAULT_CLMS = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
DEFAULT_CLMP = ROOT / "QLA_Migration" / "Output" / "quikclmp.csv"
DEFAULT_CSO = ROOT / "docs" / "Claims" / "CSO Life claims summary - 2017 - 2025.xlsx"
DEFAULT_RECON = EVIDENCE / "issue135_cso_output_recon.csv"

# Explicit rule reason codes (lineage)
RULE_EXCLUDE_REVERSAL = "EXCLUDE_REVERSAL_DATE_REVERSED"
RULE_EXCLUDE_REINSTATE_LOOP = "EXCLUDE_REINSTATEMENT_ENDOW_LOOP"
RULE_EXCLUDE_INTRACO_LOOP = "EXCLUDE_INTRACO_UNAPPLIED_LOOP"
RULE_KEEP_ECONOMIC_DEATH_PAYOUT = "KEEP_ECONOMIC_DEATH_PAYOUT_2032_TO_1058"
RULE_SUBSET_MATCH_CSO = "DEDUP_SUBSET_MATCH_CSO_TOTAL_PAID"
RULE_PROMOTE_MISSING_PACTG = "PROMOTE_MISSING_DEATH_PAYOUT_FROM_PACTG"
RULE_HOLD_NO_SUBSET = "HOLD_NO_CSO_MATCHING_SUBSET"
RULE_HOLD_MISSING_NO_MATCH = "HOLD_MISSING_NO_PACTG_CSO_MATCH"
RULE_HOLD_PRIOR_CLASS = "HOLD_PRIOR_EVIDENCE_CLASS"
RULE_SKIP_ERIC_GAP = "SKIP_ERIC_SUPPLY_GAP_NOT_IN_SOURCE"
RULE_SKIP_NON_CANDIDATE = "SKIP_NON_CANDIDATE_OR_MATCH"

TEACHERS = ["9011156098C", "9010914301C", "9010391359C"]


def _digits_acct(acct: str) -> str:
    return "".join(ch for ch in _strip(acct) if ch.isdigit())


def classify_pactg_economic_role(row: dict) -> tuple[str, str]:
    """Return (role, rule_reason) for one open PACTG row."""
    if is_reversed_date(row.get("date_reversed", "")):
        return "REVERSAL", RULE_EXCLUDE_REVERSAL

    dra = _account_family(row["debit_account"])
    cra = _account_family(row["credit_account"])
    dig_dr = _digits_acct(row["debit_account"])
    dig_cr = _digits_acct(row["credit_account"])
    dr = row.get("debit_code", "")
    cr = row.get("credit_code", "")

    # Reinstatement / endow loops (money recycled via 1015 / 6044)
    if (dra == "1058" and cra == "1015") or (dra == "1015" and cra == "1058"):
        return "LOOP_REINSTATE", RULE_EXCLUDE_REINSTATE_LOOP
    if dra == "1015" or cra == "1015":
        if dr in {"0094", "0090", "0020", "0530"} or cr in {"0094", "0090", "0020", "0530", "6044"}:
            return "LOOP_REINSTATE", RULE_EXCLUDE_REINSTATE_LOOP
    if cr.startswith("6044") or dr.startswith("6044"):
        return "LOOP_REINSTATE", RULE_EXCLUDE_REINSTATE_LOOP

    # Intra-co / unapplied re-payout
    if dra == "2019" or cra == "2019" or "1058000256" in (dig_dr, dig_cr):
        return "LOOP_INTRACO", RULE_EXCLUDE_INTRACO_LOOP

    # Valid economic death payout: clearing 2032 -> cash 1058 via 0094/0090
    if dra == "2032" and cra == "1058" and cr in {"0094", "0090"}:
        return "ECONOMIC_DEATH_PAYOUT", RULE_KEEP_ECONOMIC_DEATH_PAYOUT

    return "OTHER", "OTHER_NON_ECONOMIC"


def loop_reissue_dates(rows: list[dict]) -> set[str]:
    """Dates where cash claim payment is recycled out of 1058 (or re-issued via 2019).

    Important: do NOT exclude an entire date merely because reinstatement *funding*
    (1015→6001 / clearing) posts on the same day as a valid 2032→1058 economic payout.
    Only cash-recycling / re-issuance dates are removed from the payee pool.
    """
    dates: set[str] = set()
    for r in rows:
        if is_reversed_date(r.get("date_reversed", "")):
            continue
        dra = _account_family(r["debit_account"])
        cra = _account_family(r["credit_account"])
        dig_dr = _digits_acct(r["debit_account"])
        dig_cr = _digits_acct(r["credit_account"])
        d = _strip(r.get("effective_date", ""))
        if not d:
            continue
        # Cash leaving death-claim payment account into endow / unapplied
        if dra == "1058" and cra in {"1015", "2019", "2031", "2039"}:
            dates.add(d)
        # Intra-co re-payout back into 1058 (duplicate economic representation)
        if dra == "2019" and cra == "1058":
            dates.add(d)
        if "1058000256" in (dig_dr, dig_cr) and (dra == "1058" or cra == "1058"):
            dates.add(d)
    return dates


# Back-compat alias used by report text / callers
def loop_payment_dates(rows: list[dict]) -> set[str]:
    return loop_reissue_dates(rows)


def economic_payout_events(rows: list[dict]) -> list[dict]:
    events = []
    for r in rows:
        role, reason = classify_pactg_economic_role(r)
        if role != "ECONOMIC_DEATH_PAYOUT":
            continue
        events.append(
            {
                "effective_date": _strip(r.get("effective_date", "")),
                "amount": round(float(r["trans_amount"]), 2),
                "debit_code": r.get("debit_code", ""),
                "credit_code": r.get("credit_code", ""),
                "debit_account": r.get("debit_account", ""),
                "credit_account": r.get("credit_account", ""),
                "date_reversed": r.get("date_reversed", ""),
                "rule_reason": reason,
                "source_lineage": "PACTG_OPEN_2032_TO_1058",
            }
        )
    return events


def best_subset(items: list[tuple[Any, float]], target: float):
    """Fewest-rows subset summing to target; tie-break earliest date then key."""
    n = len(items)
    if n == 0:
        return None
    # Cap combinatorial blow-up
    if n > 16:
        # Greedy fallback: prefer exact amount matches, then earliest rows
        exact = [it for it in items if abs(it[1] - target) <= TOLERANCE]
        if exact:
            exact_sorted = sorted(exact, key=lambda x: x[0])
            return [exact_sorted[0]]
        return None
    best = None
    for r in range(1, n + 1):
        for comb in itertools.combinations(range(n), r):
            s = sum(items[i][1] for i in comb)
            if abs(s - target) <= TOLERANCE:
                chosen = [items[i] for i in comb]
                # Tie-break: earliest date element in key (key[1] when using row_id keys;
                # key[0] when using date-leading keys).
                def _date_part(key):
                    if isinstance(key, tuple) and len(key) >= 2:
                        return str(key[1])
                    return str(key)

                score = (
                    r,
                    min(_date_part(x[0]) for x in chosen),
                    tuple(str(x[0]) for x in chosen),
                )
                if best is None or score < best[0]:
                    best = (score, chosen)
        if best is not None:
            break
    return None if best is None else best[1]


def reconstruct_policy(
    mpolicy: str,
    policy_digits: str,
    cso_total_paid: float,
    evidence_class: str,
    hold_flag: str,
    pactg_rows: list[dict],
    clmp_rows: pd.DataFrame,
    death_header: dict | None,
) -> dict:
    """Apply Option-3 rules for one evidence-backed candidate policy."""
    base = {
        "mpolicy": mpolicy,
        "policy_digits": policy_digits,
        "evidence_class": evidence_class,
        "prior_hold_flag": hold_flag,
        "cso_total_paid": round(cso_total_paid, 2),
        "current_death_mpaid": _money((death_header or {}).get("MPAID", 0)),
        "current_payee_sum": round(
            float(pd.to_numeric(clmp_rows["MAMOUNT"], errors="coerce").fillna(0).sum())
            if len(clmp_rows) and "MAMOUNT" in clmp_rows.columns
            else 0.0,
            2,
        ),
        "option3_status": "HOLD",
        "rule_reasons": "",
        "corrected_mpaid": "",
        "corrected_payee_sum": "",
        "corrected_payee_n": 0,
        "loop_dates_excluded": "",
        "needs_payee_identity": "N",
        "overlay_note": "",
    }

    if hold_flag != "CANDIDATE":
        base["option3_status"] = "SKIP_HOLD_CLASS"
        base["rule_reasons"] = RULE_HOLD_PRIOR_CLASS
        base["overlay_note"] = "Prior Phase B HOLD — not force-fit"
        return base

    loop_dates = loop_reissue_dates(pactg_rows)
    eco = economic_payout_events(pactg_rows)
    reasons: list[str] = []
    if loop_dates:
        reasons.append(RULE_EXCLUDE_REINSTATE_LOOP)
        reasons.append(RULE_EXCLUDE_INTRACO_LOOP)
    if eco:
        reasons.append(RULE_KEEP_ECONOMIC_DEATH_PAYOUT)

    selected_payee_frames: list[pd.DataFrame] = []
    corrected_mpaid = None
    needs_identity = "N"
    note = ""

    if len(clmp_rows):
        work = clmp_rows.copy().reset_index(drop=True)
        work["_amt"] = pd.to_numeric(work["MAMOUNT"], errors="coerce").fillna(0.0)
        work["_date"] = work["MPMTDATE"].map(_strip) if "MPMTDATE" in work.columns else ""
        work["_row_id"] = work.index.astype(int)
        filtered = work[~work["_date"].isin(loop_dates)].copy()
        if filtered.empty:
            filtered = work.copy()
            note = "loop_reissue_filter_emptied_used_all_payees;"
        items = [
            ((int(r["_row_id"]), str(r["_date"]), str(r.get("MPAYNAME", ""))), float(r["_amt"]))
            for _, r in filtered.iterrows()
        ]
        subset = best_subset(items, cso_total_paid)
        if subset is None and abs(float(work["_amt"].sum()) - cso_total_paid) <= TOLERANCE:
            subset = [
                ((int(r["_row_id"]), str(r["_date"]), str(r.get("MPAYNAME", ""))), float(r["_amt"]))
                for _, r in work.iterrows()
            ]
            note += "full_payee_sum_already_matches_cso;"
        if subset is not None:
            row_ids = [s[0][0] for s in subset]
            chosen = work[work["_row_id"].isin(row_ids)].copy()
            # Preserve subset order deterministically
            chosen["_ord"] = chosen["_row_id"].map({rid: i for i, rid in enumerate(row_ids)})
            chosen = chosen.sort_values("_ord").drop(columns=["_ord"])
            selected_payee_frames.append(chosen)
            corrected_mpaid = round(float(chosen["_amt"].sum()), 2)
            reasons.append(RULE_SUBSET_MATCH_CSO)
            note += f"payee_subset_n={len(chosen)};"
        else:
            base["option3_status"] = "HOLD"
            base["rule_reasons"] = "|".join(reasons + [RULE_HOLD_NO_SUBSET])
            base["loop_dates_excluded"] = "|".join(sorted(loop_dates))
            base["overlay_note"] = (
                f"no_payee_subset_sums_to_cso remaining_sum="
                f"{float(filtered['_amt'].sum()):.2f}"
            )
            return base
    else:
        # Missing payees — promote only with PACTG economic evidence matching CSO
        keys = []
        for e in eco:
            if e["effective_date"] in loop_dates:
                continue
            keys.append((e["effective_date"], e["amount"], e))
        exact = [k for k in keys if abs(k[1] - cso_total_paid) <= TOLERANCE]
        promote_amt = None
        promote_date = ""
        promote_lineage = ""
        if exact:
            exact_sorted = sorted(exact, key=lambda x: x[0])
            promote_amt = cso_total_paid
            promote_date = exact_sorted[0][0]
            promote_lineage = exact_sorted[0][2]["source_lineage"]
        else:
            bydate: dict[str, list] = defaultdict(list)
            for d, a, e in keys:
                bydate[d].append((a, e))
            for d in sorted(bydate):
                amts = [x[0] for x in bydate[d]]
                if abs(sum(amts) - cso_total_paid) <= TOLERANCE:
                    promote_amt = cso_total_paid
                    promote_date = d
                    promote_lineage = "PACTG_DATE_SUM"
                    break
                unique = list(dict.fromkeys(amts))
                if abs(sum(unique) - cso_total_paid) <= TOLERANCE:
                    promote_amt = cso_total_paid
                    promote_date = d
                    promote_lineage = "PACTG_DATE_UNIQUE_SUM"
                    break
        if promote_amt is None:
            base["option3_status"] = "HOLD"
            base["rule_reasons"] = "|".join(reasons + [RULE_HOLD_MISSING_NO_MATCH])
            base["loop_dates_excluded"] = "|".join(sorted(loop_dates))
            base["overlay_note"] = f"no_pactg_economic_match keys={[(k[0], k[1]) for k in keys[:8]]}"
            return base
        reasons.append(RULE_PROMOTE_MISSING_PACTG)
        needs_identity = "Y"
        corrected_mpaid = round(promote_amt, 2)
        # Stub payee row — amount proven; identity must be supplied/linked later
        stub = {
            "MPOLICY": mpolicy,
            "MPHASE": (death_header or {}).get("MPHASE", "1") or "1",
            "MCHECKNO": "0",
            "MAMOUNT": f"{corrected_mpaid:.2f}",
            "MPAYNAME": "***NEEDS_PAYEE_IDENTITY***",
            "MPAYADDR1": "",
            "MPAYADDR2": "",
            "MPAYCITY": "",
            "MPAYST": "",
            "MPAYZIP": "",
            "MPAYZIP2": "",
            "MTIN": "",
            "MBANKNO": "",
            "MHDPMT": "",
            "MHDCODE": "C",
            "MCHKDATE": promote_date,
            "MPMTDATE": promote_date,
            "MSEQ": "1",
            "MHOLDINT": "0.00",
            "MFEDTAX": "0.00",
            "MSTTAX": "0.00",
            "MGROSS": f"{corrected_mpaid:.2f}",
            "MDOB": "",
            "MGENDER": "",
            "MCOUNTRY": "",
            "_amt": corrected_mpaid,
            "_date": promote_date,
            "_promote_lineage": promote_lineage,
        }
        selected_payee_frames.append(pd.DataFrame([stub]))
        note += f"pactg_promote date={promote_date} lineage={promote_lineage};"

    assert corrected_mpaid is not None
    payees = (
        pd.concat(selected_payee_frames, ignore_index=True)
        if selected_payee_frames
        else pd.DataFrame()
    )
    payee_sum = round(float(payees["_amt"].sum()) if len(payees) else 0.0, 2)
    if abs(payee_sum - cso_total_paid) > TOLERANCE or abs(corrected_mpaid - cso_total_paid) > TOLERANCE:
        base["option3_status"] = "HOLD"
        base["rule_reasons"] = "|".join(reasons + [RULE_HOLD_NO_SUBSET])
        base["overlay_note"] = "post_check_cso_mismatch"
        return base

    base.update(
        {
            "option3_status": "CORRECTED",
            "rule_reasons": "|".join(dict.fromkeys(reasons)),
            "corrected_mpaid": f"{corrected_mpaid:.2f}",
            "corrected_payee_sum": f"{payee_sum:.2f}",
            "corrected_payee_n": int(len(payees)),
            "loop_dates_excluded": "|".join(sorted(loop_dates)),
            "needs_payee_identity": needs_identity,
            "overlay_note": note.strip(";"),
            "_payees": payees,
            "_eco_events": eco,
        }
    )
    return base


def build_header_overlay_row(death_header: dict, corrected_mpaid: float, payees: pd.DataFrame) -> dict:
    out = dict(death_header)
    out["MPAID"] = f"{corrected_mpaid:.2f}"
    out["MINTAMT"] = "0.00"
    # Align related paid fields only when they were inflated with the old MPAID
    old_mpaid = _money(death_header.get("MPAID", 0))
    for fld in ("MFACE", "NETDB"):
        if fld in out and abs(_money(out.get(fld, 0)) - old_mpaid) <= TOLERANCE and old_mpaid > 0:
            out[fld] = f"{corrected_mpaid:.2f}"
    if len(payees) and "MPMTDATE" in payees.columns:
        dates = sorted({_strip(x) for x in payees["MPMTDATE"].tolist() if _strip(x)})
        if dates and (not _strip(out.get("PDDATE", "")) or _money(death_header.get("MPAID", 0)) == 0):
            out["PDDATE"] = dates[-1]
    out["MINTAMT"] = "0.00"
    return out


def run(args: argparse.Namespace) -> dict:
    deep = pd.read_csv(args.deep_dive, dtype=str, keep_default_na=False)
    clms, clmp, _payee_meta = load_output_claims(Path(args.clms), Path(args.clmp))
    cso = load_cso(Path(args.cso))
    recon = (
        pd.read_csv(args.recon, dtype=str, keep_default_na=False)
        if Path(args.recon).is_file()
        else pd.DataFrame()
    )

    candidates = deep[deep["hold_flag"] == "CANDIDATE"].copy()
    holds_prior = deep[deep["hold_flag"] != "CANDIDATE"].copy()

    digits = set(candidates["policy_digits"].map(_strip))
    pactg_path = resolve_pactg(args.pactg)
    print(f"Streaming PACTG for {len(digits)} candidate policies from {pactg_path} ...")
    buckets = stream_pactg_for_policies(pactg_path, digits)

    # Death headers by policy (CLAIMSTAT contains 2 preferred)
    death = clms[clms["_family"] == "DEATH_CLAIM"].copy()
    header_by_pol: dict[str, dict] = {}
    for pol, grp in death.groupby(death["MPOLICY"].map(_strip)):
        # Prefer CLAIMSTAT=2
        pref = grp[grp["CLAIMSTAT"].map(_strip) == "2"]
        use = pref if len(pref) else grp
        header_by_pol[pol] = use.iloc[0].to_dict()

    summary_rows = []
    event_rows = []
    clmp_overlay_rows = []
    clms_overlay_rows = []
    hold_rows = []

    for _, r in holds_prior.iterrows():
        hold_rows.append(
            {
                "mpolicy": _strip(r["mpolicy"]),
                "evidence_class": _strip(r["evidence_class"]),
                "hold_flag": _strip(r["hold_flag"]),
                "option3_status": "HOLD_PRIOR",
                "rule_reasons": RULE_HOLD_PRIOR_CLASS,
                "cso_total_paid": _money(r["cso_total_paid"]),
                "death_mpaid": _money(r["death_mpaid"]),
                "overlay_note": "Unresolved residual / clearing / loan / interest — not force-fit",
            }
        )

    for _, r in candidates.iterrows():
        pol = _strip(r["mpolicy"])
        dig = _strip(r["policy_digits"])
        clmp_pol = clmp[clmp["MPOLICY"].map(_strip) == pol].copy() if len(clmp) else pd.DataFrame()
        result = reconstruct_policy(
            mpolicy=pol,
            policy_digits=dig,
            cso_total_paid=_money(r["cso_total_paid"]),
            evidence_class=_strip(r["evidence_class"]),
            hold_flag=_strip(r["hold_flag"]),
            pactg_rows=buckets.get(dig, []),
            clmp_rows=clmp_pol,
            death_header=header_by_pol.get(pol),
        )
        payees = result.pop("_payees", pd.DataFrame())
        eco = result.pop("_eco_events", [])
        summary_rows.append(result)

        for e in eco:
            event_rows.append(
                {
                    "mpolicy": pol,
                    "policy_digits": dig,
                    "event_role": "ECONOMIC_DEATH_PAYOUT_SOURCE",
                    **e,
                    "option3_status": result["option3_status"],
                }
            )
        for d in _strip(result.get("loop_dates_excluded", "")).split("|"):
            if d:
                event_rows.append(
                    {
                        "mpolicy": pol,
                        "policy_digits": dig,
                        "event_role": "LOOP_DATE_EXCLUDED",
                        "effective_date": d,
                        "amount": "",
                        "rule_reason": RULE_EXCLUDE_REINSTATE_LOOP + "|" + RULE_EXCLUDE_INTRACO_LOOP,
                        "source_lineage": "PACTG_LOOP_DATE",
                        "option3_status": result["option3_status"],
                    }
                )

        if result["option3_status"] == "CORRECTED":
            hdr = header_by_pol.get(pol)
            if hdr is None:
                held = dict(result)
                held["option3_status"] = "HOLD"
                held["overlay_note"] = (held.get("overlay_note") or "") + ";missing_death_header"
                # Correct the already-appended summary row
                summary_rows[-1] = {k: v for k, v in held.items() if not str(k).startswith("_")}
                hold_rows.append({**held, "hold_flag": "HOLD"})
                continue
            corr = _money(result["corrected_mpaid"])
            overlay_hdr = build_header_overlay_row(hdr, corr, payees)
            overlay_hdr["_issue135_option3"] = "Y"
            overlay_hdr["_rule_reasons"] = result["rule_reasons"]
            overlay_hdr["_cso_total_paid"] = f"{result['cso_total_paid']:.2f}"
            clms_overlay_rows.append(overlay_hdr)
            for _, pr in payees.iterrows():
                prow = {k: pr.get(k, "") for k in clmp.columns} if len(clmp.columns) else {}
                for k in pr.index:
                    if str(k).startswith("_"):
                        continue
                    prow[k] = pr[k]
                prow["MAMOUNT"] = f"{_money(pr.get('MAMOUNT', pr.get('_amt', 0))):.2f}"
                if not _strip(prow.get("MGROSS", "")):
                    prow["MGROSS"] = prow["MAMOUNT"]
                prow["_issue135_option3"] = "Y"
                prow["_rule_reasons"] = result["rule_reasons"]
                prow["_cso_total_paid"] = f"{result['cso_total_paid']:.2f}"
                prow["_needs_payee_identity"] = result["needs_payee_identity"]
                clmp_overlay_rows.append(prow)
        else:
            hold_rows.append({**result, "hold_flag": "HOLD"})

    summary_df = pd.DataFrame(summary_rows)
    status_counts = Counter(summary_df["option3_status"]) if len(summary_df) else Counter()
    class_corr = (
        summary_df[summary_df["option3_status"] == "CORRECTED"]
        .groupby("evidence_class")
        .size()
        .to_dict()
        if len(summary_df)
        else {}
    )

    # Teacher check
    teacher_status = {}
    for t in TEACHERS:
        sub = summary_df[summary_df["mpolicy"] == t] if len(summary_df) else pd.DataFrame()
        if len(sub):
            teacher_status[t] = {
                "option3_status": sub.iloc[0]["option3_status"],
                "cso_total_paid": sub.iloc[0]["cso_total_paid"],
                "corrected_mpaid": sub.iloc[0]["corrected_mpaid"],
                "rule_reasons": sub.iloc[0]["rule_reasons"],
            }
        else:
            teacher_status[t] = {"option3_status": "NOT_IN_CANDIDATES"}

    # Eric gaps from recon
    eric_n = 0
    if len(recon):
        eric_n = int((recon["population"] == "MISSING_ERIC_SUPPLY").sum())

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_path = out_dir / "issue135_option3_candidate_summary.csv"
    summary_df.drop(columns=[c for c in summary_df.columns if c.startswith("_")], errors="ignore").to_csv(
        summary_path, index=False
    )
    events_df = pd.DataFrame(event_rows)
    events_df.to_csv(out_dir / "issue135_option3_corrected_events.csv", index=False)
    clmp_ov = pd.DataFrame(clmp_overlay_rows)
    clms_ov = pd.DataFrame(clms_overlay_rows)
    clmp_ov.to_csv(out_dir / "issue135_option3_quikclmp_overlay.csv", index=False)
    clms_ov.to_csv(out_dir / "issue135_option3_quikclms_overlay.csv", index=False)
    holds_df = pd.DataFrame(hold_rows)
    holds_df.to_csv(out_dir / "issue135_option3_hold_unresolved.csv", index=False)

    corrected_n = int(status_counts.get("CORRECTED", 0))
    candidate_hold_n = int(sum(1 for s, n in status_counts.items() if s != "CORRECTED" for _ in range(n)))
    # recount holds among candidates only
    candidate_hold_n = int(len(summary_df) - corrected_n) if len(summary_df) else 0
    prior_hold_n = int(len(holds_prior))

    machine = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "issue": 135,
        "phase": "OPTION3_ECONOMIC_RECONSTRUCTION_OVERLAY",
        "production_output_mutated": False,
        "app_py_wired": False,
        "mintamt_remains_zero": True,
        "pactg_path": str(pactg_path),
        "available_mismatch": int(len(deep)),
        "candidates_in": int(len(candidates)),
        "prior_holds_untouched": prior_hold_n,
        "corrected_candidates": corrected_n,
        "candidate_holds_unresolved": candidate_hold_n,
        "status_counts": dict(status_counts),
        "corrected_by_class": {k: int(v) for k, v in class_corr.items()},
        "overlay_quikclms_rows": int(len(clms_ov)),
        "overlay_quikclmp_rows": int(len(clmp_ov)),
        "needs_payee_identity_n": int(
            (summary_df["needs_payee_identity"] == "Y").sum() if len(summary_df) else 0
        ),
        "teacher_status": teacher_status,
        "eric_supply_gaps": eric_n,
        "eric_gaps_touched": False,
        "remaining_production_gate": (
            "Overlay proven on available CANDIDATE policies. Production quikclms/quikclmp "
            "amounts unchanged. Wire Option-3 filter upstream of Phase 10a/10b derivation "
            "(or controlled post-emit consume of overlay) only after user approval of "
            "production consume path + focused re-validation on full Output."
        ),
        "artifacts": {
            "candidate_summary": str(summary_path),
            "corrected_events": str(out_dir / "issue135_option3_corrected_events.csv"),
            "quikclmp_overlay": str(out_dir / "issue135_option3_quikclmp_overlay.csv"),
            "quikclms_overlay": str(out_dir / "issue135_option3_quikclms_overlay.csv"),
            "hold_unresolved": str(out_dir / "issue135_option3_hold_unresolved.csv"),
        },
    }
    with open(out_dir / "issue135_option3_summary.json", "w", encoding="utf-8") as fh:
        json.dump(machine, fh, indent=2)

    # Markdown report
    lines = [
        "# Issue #135 — Option 3 Economic Reconstruction (Overlay)",
        "",
        f"Generated: {machine['generated_at']}",
        "",
        "## Decision",
        "",
        "Warren approved **Option 3**: correct upstream accounting reconstruction, then derive "
        "both quikclmp payees and quikclms headers from corrected economic payments.",
        "",
        "## Production safety",
        "",
        f"- Production Output mutated: **{machine['production_output_mutated']}**",
        f"- app.py wired: **{machine['app_py_wired']}**",
        f"- MINTAMT remains 0: **{machine['mintamt_remains_zero']}**",
        f"- Eric 459 gaps touched: **{machine['eric_gaps_touched']}**",
        "",
        "## Narrowest upstream location",
        "",
        "Economic over-count enters when reinstatement/endow (1015/6044) and intra-co "
        "(2019 / 1058000256) PACTG legs are treated as payout events before Phase 8–10 "
        "derive quikclmp/quikclms. Correct **economic events** first (policy/date/payee/"
        "amount/account), then set `MPAID = sum(corrected MAMOUNT)`. Do not patch only final MPAID.",
        "",
        "## Counts",
        "",
        f"| Metric | Count |",
        f"|---|---:|",
        f"| AVAILABLE_MISMATCH deep-dive rows | {machine['available_mismatch']} |",
        f"| CANDIDATE in | {machine['candidates_in']} |",
        f"| CORRECTED (overlay) | {corrected_n} |",
        f"| Candidate still HOLD | {candidate_hold_n} |",
        f"| Prior Phase B HOLD (untouched) | {prior_hold_n} |",
        f"| Overlay quikclms rows | {machine['overlay_quikclms_rows']} |",
        f"| Overlay quikclmp rows | {machine['overlay_quikclmp_rows']} |",
        f"| Promote stubs needing payee identity | {machine['needs_payee_identity_n']} |",
        f"| Eric supply gaps (untouched) | {eric_n} |",
        "",
        "### Corrected by evidence class",
        "",
        "| Class | Corrected |",
        "|---|---:|",
    ]
    for cls, n in sorted(class_corr.items()):
        lines.append(f"| {cls} | {n} |")
    lines += [
        "",
        "## Teacher cases",
        "",
        "| Policy | Status | CSO | Corrected MPAID |",
        "|---|---|---:|---:|",
    ]
    for t, st in teacher_status.items():
        lines.append(
            f"| {t} | {st.get('option3_status')} | {st.get('cso_total_paid')} | {st.get('corrected_mpaid')} |"
        )
    lines += [
        "",
        "## Rules applied",
        "",
        "| Rule | Meaning |",
        "|---|---|",
        f"| `{RULE_EXCLUDE_REVERSAL}` | DATE_REVERSED blank/0 is NOT reversed |",
        f"| `{RULE_EXCLUDE_REINSTATE_LOOP}` | 1058↔1015 / 6044 lifecycle excluded from economic payout |",
        f"| `{RULE_EXCLUDE_INTRACO_LOOP}` | 2019 / 1058000256 re-payout excluded |",
        f"| `{RULE_KEEP_ECONOMIC_DEATH_PAYOUT}` | Keep 2032→1058 (0094/0090) death cash legs |",
        f"| `{RULE_SUBSET_MATCH_CSO}` | Dedup/select payee subset summing to CSO Total_Paid |",
        f"| `{RULE_PROMOTE_MISSING_PACTG}` | Promote missing death payout only with PACTG+CSO proof |",
        f"| `{RULE_HOLD_NO_SUBSET}` / `{RULE_HOLD_MISSING_NO_MATCH}` | Unresolved → HOLD |",
        "",
        "## Remaining gate",
        "",
        machine["remaining_production_gate"],
        "",
        "## Artifacts",
        "",
    ]
    for k, v in machine["artifacts"].items():
        lines.append(f"- `{k}`: `{Path(v).name}`")
    report_path = out_dir / "issue135_option3_report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    machine["report"] = str(report_path)

    print(json.dumps({k: machine[k] for k in (
        "corrected_candidates", "candidate_holds_unresolved", "prior_holds_untouched",
        "overlay_quikclms_rows", "overlay_quikclmp_rows", "production_output_mutated",
        "teacher_status",
    )}, indent=2))
    return machine


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--deep-dive", default=str(DEFAULT_DEEP))
    p.add_argument("--clms", default=str(DEFAULT_CLMS))
    p.add_argument("--clmp", default=str(DEFAULT_CLMP))
    p.add_argument("--cso", default=str(DEFAULT_CSO))
    p.add_argument("--recon", default=str(DEFAULT_RECON))
    p.add_argument("--pactg", default=None)
    p.add_argument("--out", default=str(EVIDENCE))
    return p


if __name__ == "__main__":
    run(build_argparser().parse_args())
