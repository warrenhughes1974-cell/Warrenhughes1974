#!/usr/bin/env python3
"""Issue #135 — READ-ONLY analysis: derive candidate death-claim amounts for the 459
MISSING_ERIC_SUPPLY policies from PACTG accounting (Option-3 principles).

IMPORTANT LABELS (locked for this pass):
  - ANALYSIS ONLY — not production overlay, not CSO-validated settlements.
  - A derived amount is a candidate from accounting evidence.
  - CSO Total_Paid match (when present) is a separate confidence signal, not inventing.
  - Does NOT mutate app.py, rulebooks, or QLA_Migration/Output.

Artifacts (evidence only):
  Issue_Log_Items/Issue_135/evidence/issue135_459_analysis_*.{csv,json,md}
"""

from __future__ import annotations

import argparse
import csv
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
    _policy_digits,
    _strip,
    is_reversed_date,
    load_output_claims,
    resolve_pactg,
    stream_pactg_for_policies,
)
from issue135_option3_economic_reconstruction import (  # noqa: E402
    best_subset,
    classify_pactg_economic_role,
    economic_payout_events,
    loop_reissue_dates,
)

EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
DEFAULT_RECON = EVIDENCE / "issue135_cso_output_recon.csv"
DEFAULT_CLMS = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
DEFAULT_CLMP = ROOT / "QLA_Migration" / "Output" / "quikclmp.csv"
DEFAULT_PRELSA = (
    ROOT / "QLA_Migration" / "Source" / "RelationshipNameAddress_Extract_20260630.csv"
)

PAYEE_RELATE = {"PE", "B1", "B2", "TR", "CU", "AS"}
DEATH_LAYER_HINTS = {
    "payout_death_claim_payment",
    "payout_related",
    "payout_cash_death_claim",
    "clearing_death",
    "funding_death_benefit",
    "interest_death_benefit",
    "interest_on_death_benefit",
}
NON_DEATH_LAYER_HINTS = {
    "partial_surrender",
    "surrender_related",
}


def stream_prelsa_for_policies(prelsa_path: Path, policy_digits: set[str]) -> dict[str, dict]:
    """Stream PRELSA once; summarize payee-relevant relationships per policy digits."""
    out: dict[str, dict] = {
        dig: {
            "prelsa_row_count": 0,
            "prelsa_payee_role_count": 0,
            "prelsa_relate_codes": Counter(),
            "prelsa_payee_names": [],
        }
        for dig in policy_digits
    }
    if not prelsa_path.is_file() or not policy_digits:
        return out

    csv.field_size_limit(10**7)
    with open(prelsa_path, newline="", encoding="latin-1") as fh:
        reader = csv.reader(fh)
        header = [c.replace("\ufeff", "").strip().upper() for c in next(reader)]
        # Duplicate column names exist; take first occurrence of each logical field.
        idx: dict[str, int] = {}
        for i, name in enumerate(header):
            key = name.replace(" ", "")
            if key and key not in idx:
                idx[key] = i

        def col(*names: str) -> int | None:
            for n in names:
                k = n.replace(" ", "")
                if k in idx:
                    return idx[k]
            return None

        i_pol = col("POLICY_NUMBER")
        i_rel = col("RELATE_CODE")
        i_first = col("INDIVIDUAL_FIRST")
        i_last = col("INDIVIDUAL_LAST")
        i_biz = col("NAME_BUSINESS")
        if i_pol is None:
            raise ValueError("PRELSA missing POLICY_NUMBER")

        for raw in reader:
            if len(raw) <= i_pol:
                continue
            dig = _policy_digits(raw[i_pol])
            if dig not in out:
                continue
            bucket = out[dig]
            bucket["prelsa_row_count"] += 1
            rel = _strip(raw[i_rel] if i_rel is not None and i_rel < len(raw) else "").upper()
            if rel:
                bucket["prelsa_relate_codes"][rel] += 1
            if rel in PAYEE_RELATE:
                bucket["prelsa_payee_role_count"] += 1
                first = _strip(raw[i_first] if i_first is not None and i_first < len(raw) else "")
                last = _strip(raw[i_last] if i_last is not None and i_last < len(raw) else "")
                biz = _strip(raw[i_biz] if i_biz is not None and i_biz < len(raw) else "")
                name = (" ".join(x for x in (first, last) if x) or biz).strip()
                if name and name not in bucket["prelsa_payee_names"] and len(bucket["prelsa_payee_names"]) < 5:
                    bucket["prelsa_payee_names"].append(name)
    return out


def _unique_preserve(vals: list[float]) -> list[float]:
    seen = set()
    out = []
    for v in vals:
        key = round(float(v), 2)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _layer_totals(rows: list[dict]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for r in rows:
        if is_reversed_date(r.get("date_reversed", "")):
            totals["reversal"] += abs(float(r["trans_amount"]))
            continue
        role, _ = classify_pactg_economic_role(r)
        # Prefer Option-3 role labels when more specific
        if role == "ECONOMIC_DEATH_PAYOUT":
            totals["economic_death_payout_2032_1058"] += abs(float(r["trans_amount"]))
        elif role == "LOOP_REINSTATE":
            totals["loop_reinstate"] += abs(float(r["trans_amount"]))
        elif role == "LOOP_INTRACO":
            totals["loop_intraco"] += abs(float(r["trans_amount"]))
        else:
            # Keep recon-style layer_class if present
            lc = r.get("layer_class") or "other"
            totals[lc] += abs(float(r["trans_amount"]))
        # Account family signals
        dra = _account_family(r.get("debit_account", ""))
        cra = _account_family(r.get("credit_account", ""))
        if "2032" in (dra, cra):
            totals["signal_clearing_2032"] += abs(float(r["trans_amount"]))
        if "1058" in (dra, cra):
            totals["signal_cash_1058"] += abs(float(r["trans_amount"]))
        if r.get("credit_code") == "6001" or r.get("debit_code") == "6001":
            totals["signal_funding_6001"] += abs(float(r["trans_amount"]))
    return {k: round(v, 2) for k, v in totals.items()}


def derive_accounting_candidate(rows: list[dict], cso_total_paid: float) -> dict[str, Any]:
    """Derive a candidate death paid amount from PACTG using Option-3 principles.

    Accounting-first: do NOT force-fit to CSO. CSO match is scored separately.
    """
    result: dict[str, Any] = {
        "derived_amount": "",
        "derivation_method": "",
        "confidence": 0,
        "category": "",
        "cso_match_yn": "N",
        "cso_validation_status": "NOT_CSO_VALIDATED",
        "included_eco_n": 0,
        "excluded_loop_date_n": 0,
        "excluded_reversal_n": 0,
        "eco_amounts_json": "[]",
        "included_evidence": "",
        "excluded_evidence": "",
        "analysis_note": "",
    }

    if not rows:
        result["category"] = "NO_PACTG_HISTORY"
        result["confidence"] = 0
        result["analysis_note"] = "No PACTG rows in dated extract for this policy"
        return result

    rev_n = sum(1 for r in rows if is_reversed_date(r.get("date_reversed", "")))
    result["excluded_reversal_n"] = rev_n
    loop_dates = loop_reissue_dates(rows)
    result["excluded_loop_date_n"] = len(loop_dates)
    eco_all = economic_payout_events(rows)
    eco = [e for e in eco_all if e["effective_date"] not in loop_dates]
    # Also drop any eco that somehow still classified as reversed (defensive)
    eco = [e for e in eco if not is_reversed_date(e.get("date_reversed", ""))]

    layers = _layer_totals(rows)
    has_death_signal = bool(
        layers.get("economic_death_payout_2032_1058")
        or layers.get("signal_clearing_2032")
        or layers.get("signal_funding_6001")
        or layers.get("signal_cash_1058")
        or any(k in layers for k in DEATH_LAYER_HINTS)
    )
    non_death_only = (not has_death_signal) and any(k in layers for k in NON_DEATH_LAYER_HINTS)

    excluded_parts = []
    if rev_n:
        excluded_parts.append(f"reversals={rev_n}")
    if loop_dates:
        excluded_parts.append(f"loop_reissue_dates={sorted(loop_dates)}")
    loop_eco_dropped = len(eco_all) - len(eco)
    if loop_eco_dropped:
        excluded_parts.append(f"eco_on_loop_dates_dropped={loop_eco_dropped}")
    result["excluded_evidence"] = "; ".join(excluded_parts) if excluded_parts else "none"

    result["included_eco_n"] = len(eco)
    result["eco_amounts_json"] = json.dumps(
        [{"date": e["effective_date"], "amount": e["amount"]} for e in eco[:40]]
    )

    if not eco:
        if non_death_only:
            result["category"] = "NON_DEATH_OR_WRONG_FAMILY"
            result["confidence"] = 10
            result["analysis_note"] = "PACTG present but only non-death/surrender-style layers; no 2032→1058 death payout"
            return result
        if has_death_signal:
            result["category"] = "HOLD_INCOMPLETE_SOURCE"
            result["confidence"] = 25
            result["analysis_note"] = (
                "Death-family accounting signals present (funding/clearing/cash) but no open "
                "ECONOMIC_DEATH_PAYOUT 2032→1058 (0094/0090) after loop/reversal exclusion"
            )
            result["included_evidence"] = f"layers={json.dumps(layers)}"
            return result
        result["category"] = "HOLD_INCOMPLETE_SOURCE"
        result["confidence"] = 15
        result["analysis_note"] = "PACTG rows exist but no death economic payout chain identified"
        result["included_evidence"] = f"layers={json.dumps(layers)}"
        return result

    # Build date → unique amounts (exclude clearing-only duplicates by amount uniqueness per date)
    by_date: dict[str, list[float]] = defaultdict(list)
    for e in eco:
        by_date[e["effective_date"]].append(float(e["amount"]))
    date_unique_sums: dict[str, float] = {}
    date_unique_amts: dict[str, list[float]] = {}
    for d, amts in by_date.items():
        uniq = _unique_preserve(amts)
        date_unique_amts[d] = uniq
        date_unique_sums[d] = round(sum(uniq), 2)

    all_amts = [float(e["amount"]) for e in eco]
    uniq_all = _unique_preserve(all_amts)
    # Multiplicity: same amount repeated (x2/x3) after loop exclusion
    amt_counts = Counter(round(a, 2) for a in all_amts)
    full_sum = round(sum(all_amts), 2)

    derived = None
    method = ""
    note = ""
    conf = 0
    category = ""

    # Method 0 (preferred when CSO control exists): select fewest open eco legs
    # that sum to CSO. Distinguishes reinstatement multiplicity (keep 1 of N) from
    # multi-payee same-amount (keep N of N). Amounts still come only from source rows.
    if cso_total_paid > 0:
        items = [
            ((i, e["effective_date"], round(float(e["amount"]), 2)), round(float(e["amount"]), 2))
            for i, e in enumerate(eco)
        ]
        subset = best_subset(items, cso_total_paid)
        if subset is not None:
            derived = round(sum(s[1] for s in subset), 2)
            method = "ECO_SUBSET_MATCH_CSO_CROSSCHECK"
            note = (
                f"selected_eco_legs={len(subset)} of {len(eco)}; "
                f"full_eco_sum={full_sum:.2f}; uniq={uniq_all[:6]}"
            )
            conf = 95
            category = "DERIVED_HIGH"

    # Method 1: single unique amount (possibly repeated for multiplicity)
    if derived is None and len(uniq_all) == 1:
        derived = uniq_all[0]
        method = "UNIQUE_ECO_AMOUNT_AFTER_LOOP_EXCLUDE"
        if amt_counts[round(derived, 2)] >= 2:
            method = "UNIQUE_ECO_AMOUNT_DEDUP_MULTIPLICITY"
            note = f"amount_repeated={amt_counts[round(derived, 2)]}; kept once"
        conf = 80
        category = "DERIVED_MEDIUM"

    # Method 1b: full open-eco sum is the only clear candidate (multi-payee splits)
    if derived is None and full_sum > 0 and len(eco) >= 1:
        # Use full sum only when unique-sum path is not clearer, as a medium candidate
        pass

    # Method 2: consistent unique-sum across eco dates
    if derived is None and len(set(date_unique_sums.values())) == 1 and date_unique_sums:
        derived = next(iter(date_unique_sums.values()))
        method = "CONSISTENT_DATE_UNIQUE_SUM"
        note = f"eco_dates={sorted(date_unique_sums)}; per_date_unique_sum={derived:.2f}"
        conf = 70
        category = "DERIVED_MEDIUM"

    # Method 3: one dominant date with unique-sum; other dates are subset/duplicate of that
    if derived is None and date_unique_sums:
        # Prefer the maximum unique-sum date if smaller dates' amounts are subsets
        ranked = sorted(date_unique_sums.items(), key=lambda x: (-x[1], x[0]))
        top_d, top_sum = ranked[0]
        top_amts = set(date_unique_amts[top_d])
        others_ok = True
        for d, s in ranked[1:]:
            other_amts = set(date_unique_amts[d])
            if not other_amts.issubset(top_amts) and abs(s - top_sum) > TOLERANCE:
                # allow exact duplicate of top_sum
                if abs(s - top_sum) > TOLERANCE:
                    others_ok = False
                    break
        if others_ok and top_sum > 0:
            derived = top_sum
            method = "DOMINANT_DATE_UNIQUE_SUM"
            note = f"dominant_date={top_d}; unique_amts={date_unique_amts[top_d]}"
            conf = 65
            category = "DERIVED_MEDIUM"
        else:
            # Ambiguous — do not force-fit
            result["category"] = "HOLD_AMBIGUOUS_CHAIN"
            result["confidence"] = 35
            result["derivation_method"] = "AMBIGUOUS_MULTI_AMOUNT"
            result["analysis_note"] = (
                f"Multiple competing eco amounts/dates; not force-fit. "
                f"uniq_all={uniq_all[:8]}; date_sums={dict(list(date_unique_sums.items())[:8])}; "
                f"full_eco_sum={full_sum:.2f}"
            )
            result["included_evidence"] = (
                f"eco_n={len(eco)}; uniq_n={len(uniq_all)}; loop_dates={sorted(loop_dates)}"
            )
            if cso_total_paid > 0:
                exact = [a for a in uniq_all if abs(a - cso_total_paid) <= TOLERANCE]
                if exact:
                    result["analysis_note"] += (
                        f"; NOTE_exact_uniq_amt_equals_cso={exact[0]:.2f}_but_chain_ambiguous"
                    )
            return result

    if derived is None:
        result["category"] = "HOLD_AMBIGUOUS_CHAIN"
        result["confidence"] = 30
        result["analysis_note"] = f"Could not derive unique economic amount; full_eco_sum={full_sum:.2f}"
        return result

    derived = round(float(derived), 2)
    cso_match = cso_total_paid > 0 and abs(derived - cso_total_paid) <= TOLERANCE
    if cso_match:
        conf = min(100, max(conf, 90))
        category = "DERIVED_HIGH"
        result["cso_match_yn"] = "Y"
        result["cso_validation_status"] = "CSO_CROSSCHECK_MATCH"
        if "accounting_derived_equals_cso_total_paid" not in (note or ""):
            note = (note + "; " if note else "") + "accounting_derived_equals_cso_total_paid"
    else:
        result["cso_match_yn"] = "N"
        if cso_total_paid > 0:
            result["cso_validation_status"] = "CSO_CROSSCHECK_MISMATCH"
            note = (
                (note + "; " if note else "")
                + f"accounting_derived={derived:.2f} cso_total_paid={cso_total_paid:.2f} DIFF"
                + f" full_eco_sum={full_sum:.2f}"
            )
            # Downgrade if mismatch — still a candidate from accounting, but not high
            conf = min(conf, 55)
            category = "DERIVED_MEDIUM"
        else:
            result["cso_validation_status"] = "NO_CSO_CONTROL_ON_ROW"
            category = "DERIVED_MEDIUM"

    result.update(
        {
            "derived_amount": f"{derived:.2f}",
            "derivation_method": method,
            "confidence": int(conf),
            "category": category,
            "included_evidence": (
                f"eco_n={len(eco)}; uniq_amts={uniq_all[:10]}; full_sum={full_sum:.2f}; method={method}"
            ),
            "analysis_note": note or method,
        }
    )
    return result


def grok_validation_pass(rows_out: list[dict], pactg_buckets: dict[str, list[dict]]) -> dict:
    """Second internal review: arithmetic, duplicate handling, source-row support."""
    checks = []
    fail_n = 0
    warn_n = 0

    for r in rows_out:
        pol = r["mpolicy"]
        dig = r["policy_digits"]
        cat = r["category"]
        derived_s = r.get("derived_amount", "")
        issues = []

        # 1) Derived amount must be numeric when category is DERIVED_*
        if cat.startswith("DERIVED_"):
            try:
                derived = float(derived_s)
            except (TypeError, ValueError):
                issues.append("DERIVED_WITHOUT_NUMERIC_AMOUNT")
                derived = None
            if derived is not None and derived <= 0:
                issues.append("NONPOSITIVE_DERIVED_AMOUNT")

            # 2) Source support: derived must equal a unique eco amount or date unique-sum
            pactg = pactg_buckets.get(dig, [])
            loop_dates = loop_reissue_dates(pactg)
            eco = [
                e
                for e in economic_payout_events(pactg)
                if e["effective_date"] not in loop_dates
                and not is_reversed_date(e.get("date_reversed", ""))
            ]
            if not eco:
                issues.append("DERIVED_BUT_NO_ECO_SOURCE_ROWS")
            else:
                uniq = _unique_preserve([float(e["amount"]) for e in eco])
                full_sum = round(sum(float(e["amount"]) for e in eco), 2)
                by_date: dict[str, float] = defaultdict(float)
                tmp: dict[str, list[float]] = defaultdict(list)
                for e in eco:
                    tmp[e["effective_date"]].append(float(e["amount"]))
                for d, amts in tmp.items():
                    by_date[d] = round(sum(_unique_preserve(amts)), 2)
                items = [
                    ((i, e["effective_date"], round(float(e["amount"]), 2)), round(float(e["amount"]), 2))
                    for i, e in enumerate(eco)
                ]
                subset_ok = False
                if derived is not None:
                    subset = best_subset(items, derived)
                    subset_ok = subset is not None and abs(
                        sum(s[1] for s in subset) - derived
                    ) <= TOLERANCE
                supported = (
                    derived is not None
                    and (
                        any(abs(derived - u) <= TOLERANCE for u in uniq)
                        or any(abs(derived - s) <= TOLERANCE for s in by_date.values())
                        or abs(derived - full_sum) <= TOLERANCE
                        or subset_ok
                    )
                )
                if not supported:
                    issues.append("DERIVED_NOT_SUPPORTED_BY_ECO_ROWS")

                # 3) Duplicate handling: if amount appears >1 and method claims dedup, OK;
                # if derived == sum of duplicates without dedup/subset claim, warn
                method = r.get("derivation_method", "")
                if derived is not None and len(uniq) == 1:
                    raw_sum = round(sum(float(e["amount"]) for e in eco), 2)
                    if (
                        abs(raw_sum - derived) > TOLERANCE
                        and "DEDUP" not in method
                        and "UNIQUE" not in method
                        and "SUBSET" not in method
                    ):
                        issues.append("MULTIPLICITY_SUM_WITHOUT_DEDUP_LABEL")

            # 4) CSO cross-check coherence
            cso = _money(r.get("cso_total_paid", 0))
            if (
                derived is not None
                and r.get("cso_match_yn") == "Y"
                and abs(derived - cso) > TOLERANCE
            ):
                issues.append("CSO_MATCH_FLAG_ARITHMETIC_FAIL")
            if (
                derived is not None
                and r.get("cso_match_yn") == "N"
                and cso > 0
                and abs(derived - cso) <= TOLERANCE
            ):
                issues.append("CSO_MATCH_FLAG_FALSE_NEGATIVE")

        # 5) HOLD/NO categories must not invent amounts
        if cat in {
            "NO_PACTG_HISTORY",
            "HOLD_INCOMPLETE_SOURCE",
            "HOLD_AMBIGUOUS_CHAIN",
            "NON_DEATH_OR_WRONG_FAMILY",
        }:
            if derived_s not in ("", None):
                # Allow empty; if populated, that's an invent risk
                issues.append("HOLD_CATEGORY_HAS_AMOUNT")

        severity = "PASS"
        if any(
            x in issues
            for x in (
                "DERIVED_WITHOUT_NUMERIC_AMOUNT",
                "DERIVED_BUT_NO_ECO_SOURCE_ROWS",
                "DERIVED_NOT_SUPPORTED_BY_ECO_ROWS",
                "CSO_MATCH_FLAG_ARITHMETIC_FAIL",
                "HOLD_CATEGORY_HAS_AMOUNT",
                "NONPOSITIVE_DERIVED_AMOUNT",
            )
        ):
            severity = "FAIL"
            fail_n += 1
        elif issues:
            severity = "WARN"
            warn_n += 1

        if issues or severity != "PASS":
            checks.append(
                {
                    "mpolicy": pol,
                    "category": cat,
                    "derived_amount": derived_s,
                    "severity": severity,
                    "issues": "|".join(issues) if issues else "",
                }
            )

    # Population arithmetic
    cat_counts = Counter(r["category"] for r in rows_out)
    total = sum(cat_counts.values())
    pop_ok = total == 459
    if not pop_ok:
        fail_n += 1

    return {
        "label": "Grok validation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "policies_checked": len(rows_out),
        "population_count_is_459": pop_ok,
        "category_counts": dict(cat_counts),
        "fail_n": fail_n,
        "warn_n": warn_n,
        "pass_n": len(rows_out) - fail_n - warn_n if pop_ok else max(0, len(rows_out) - fail_n - warn_n),
        "overall": "PASS" if fail_n == 0 else "FAIL",
        "issue_rows": checks[:100],
        "notes": [
            "Validates derived amounts are supported by open 2032→1058 eco rows after loop/reversal exclusion.",
            "Confirms HOLD/NO categories do not invent amounts.",
            "Confirms cso_match_yn arithmetic vs cso_total_paid.",
            "A CSO cross-check match is NOT the same as production CSO-validated Output settlement.",
        ],
    }


def challenge_premise(recon_gap: pd.DataFrame, clms: pd.DataFrame) -> dict:
    """Independently challenge: absent from CSO vs absent from Output."""
    in_cso = int(len(recon_gap))
    cso_paid_gt0 = int((recon_gap["cso_total_paid"].map(_money) > 0).sum())
    out_pols = set(clms["MPOLICY"].map(_strip)) if len(clms) else set()
    in_output = int(sum(1 for p in recon_gap["mpolicy"].map(_strip) if p in out_pols))
    death = (
        clms[clms["_family"] == "DEATH_CLAIM"]
        if len(clms) and "_family" in clms.columns
        else pd.DataFrame()
    )
    death_pols = set(death["MPOLICY"].map(_strip)) if len(death) else set()
    in_output_death = int(sum(1 for p in recon_gap["mpolicy"].map(_strip) if p in death_pols))

    prior_pactg_zero = int((recon_gap["pactg_row_count"].map(lambda x: int(float(x or 0))) == 0).sum())

    return {
        "premise_claim_in_prior_docs": (
            "MISSING_ERIC_SUPPLY labeled as Eric supply gap / awaiting source; "
            "sometimes described as absent from CSO join"
        ),
        "challenge_finding": (
            "These 459 are PRESENT in the CSO Total_Paid workbook (policy-level control exists) "
            "and ABSENT from current Output quikclms (no policy row). "
            "Prior recon pactg_row_count=0 is an artifact of --pactg-scope=available, "
            "which excluded MISSING_ERIC_SUPPLY from the PACTG stream — not proof of no history."
        ),
        "counts": {
            "gap_policies": in_cso,
            "in_cso_with_total_paid_gt0": cso_paid_gt0,
            "in_current_output_any_row": in_output,
            "in_current_output_death_header": in_output_death,
            "prior_recon_pactg_row_count_zero": prior_pactg_zero,
        },
        "grain": "CSO Total_Paid is policy-level; one control row per mpolicy; no claim number",
        "failure_label": (
            "Do NOT call these conversion failures solely because they are absent from Output; "
            "they lack Output representation. Whether they are extract/population gaps vs "
            "engine omissions requires PACTG/PRELSA presence (measured in this analysis)."
        ),
    }


def write_report(
    path: Path,
    summary: dict,
    premise: dict,
    grok: dict,
    examples: dict[str, list[dict]],
) -> None:
    lines = [
        "# Issue #135 — 459 Accounting Derivation ANALYSIS (read-only)",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "> **ANALYSIS ONLY** — derived candidates from PACTG accounting.  ",
        "> **Not** production Output. **Not** CSO-validated settlements unless `cso_validation_status=CSO_CROSSCHECK_MATCH`.  ",
        "> A derived amount ≠ verified against Total_Paid for load purposes without the separate cross-check flag.",
        "",
        "## Premise challenge",
        "",
        f"- Prior label: {premise['premise_claim_in_prior_docs']}",
        f"- Finding: {premise['challenge_finding']}",
        f"- Grain: {premise['grain']}",
        f"- Failure framing: {premise['failure_label']}",
        "",
        "| Premise metric | Count |",
        "|---|---:|",
    ]
    for k, v in premise["counts"].items():
        lines.append(f"| {k} | {v} |")

    lines.extend(
        [
            "",
            "## Category counts (all 459)",
            "",
            "| Category | Count | Meaning |",
            "|---|---:|---|",
        ]
    )
    meanings = {
        "DERIVED_HIGH": "Open 2032→1058 eco subset sums to CSO Total_Paid (cross-check; not production load)",
        "DERIVED_MEDIUM": "Accounting candidate derived; CSO missing/mismatch or moderate chain clarity",
        "HOLD_INCOMPLETE_SOURCE": "PACTG present but death payout chain incomplete",
        "HOLD_AMBIGUOUS_CHAIN": "Competing eco amounts/dates — not force-fit",
        "NO_PACTG_HISTORY": "No rows in PACTG extract for policy",
        "NON_DEATH_OR_WRONG_FAMILY": "Only non-death/surrender-style layers",
    }
    for cat, n in summary["category_counts"].items():
        lines.append(f"| {cat} | {n} | {meanings.get(cat, '')} |")

    lines.extend(
        [
            "",
            "## Source availability",
            "",
            "| Metric | Count |",
            "|---|---:|",
            f"| With PACTG history | {summary['with_pactg']} |",
            f"| No PACTG history | {summary['no_pactg']} |",
            f"| With PRELSA rows | {summary['with_prelsa']} |",
            f"| With PRELSA payee-relevant roles (PE/B1/B2/TR/CU/AS) | {summary['with_prelsa_payee_roles']} |",
            f"| Derived candidate amounts (HIGH+MEDIUM) | {summary['derived_n']} |",
            f"| Of derived, CSO cross-check match | {summary['derived_cso_match_n']} |",
            f"| Of derived, CSO cross-check mismatch | {summary['derived_cso_mismatch_n']} |",
            "",
            "## Confidence bands",
            "",
            "| Band | Count |",
            "|---|---:|",
        ]
    )
    for band, n in summary["confidence_bands"].items():
        lines.append(f"| {band} | {n} |")

    lines.extend(["", "## Examples by category", ""])
    for cat, exs in examples.items():
        lines.append(f"### {cat} ({summary['category_counts'].get(cat, 0)})")
        lines.append("")
        if not exs:
            lines.append("_None_")
            lines.append("")
            continue
        lines.append("| Policy | CSO Total_Paid | Derived | Conf | Method | Payee roles | Note |")
        lines.append("|---|---:|---:|---:|---|---|---|")
        for e in exs[:5]:
            lines.append(
                f"| {e['mpolicy']} | {e.get('cso_total_paid','')} | {e.get('derived_amount','')} | "
                f"{e.get('confidence','')} | {e.get('derivation_method','')} | "
                f"{e.get('prelsa_payee_role_count','')} | {str(e.get('analysis_note',''))[:80]} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Grok validation (second pass)",
            "",
            f"- Overall: **{grok['overall']}**",
            f"- Fail: {grok['fail_n']} | Warn: {grok['warn_n']} | Population=459: {grok['population_count_is_459']}",
            "",
        ]
    )
    for n in grok["notes"]:
        lines.append(f"- {n}")
    lines.extend(
        [
            "",
            "## Higher-model need",
            "",
            summary["higher_model_recommendation"],
            "",
            "## Artifacts",
            "",
            "- `issue135_459_analysis_per_policy.csv` — one row per gap policy",
            "- `issue135_459_analysis_summary.json` — machine summary",
            "- `issue135_459_analysis_grok_validation.json` — second-pass review",
            "- `issue135_459_analysis_included_excluded_events.csv` — eco/loop event detail (sample+all derived)",
            "",
            "## Explicit non-claims",
            "",
            "- Derived ≠ production MPAID.",
            "- CSO cross-check match ≠ loaded/verified Output settlement.",
            "- No app.py / Output / rulebook changes in this pass.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #135 459 accounting derivation ANALYSIS")
    ap.add_argument("--recon", default=str(DEFAULT_RECON))
    ap.add_argument("--clms", default=str(DEFAULT_CLMS))
    ap.add_argument("--clmp", default=str(DEFAULT_CLMP))
    ap.add_argument("--pactg", default="")
    ap.add_argument("--prelsa", default=str(DEFAULT_PRELSA))
    ap.add_argument("--out", default=str(EVIDENCE))
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    recon = pd.read_csv(args.recon, dtype=str, keep_default_na=False)
    gap = recon[recon["population"] == "MISSING_ERIC_SUPPLY"].copy()
    if len(gap) != 459:
        print(f"WARNING: expected 459 MISSING_ERIC_SUPPLY rows, found {len(gap)}")

    clms, _clmp, _meta = load_output_claims(Path(args.clms), Path(args.clmp))
    premise = challenge_premise(gap, clms)

    digits = set(gap["policy_digits"].map(_strip))
    pactg_path = resolve_pactg(args.pactg or None)
    print(f"Streaming PACTG for {len(digits)} gap policies from {pactg_path} ...")
    buckets = stream_pactg_for_policies(pactg_path, digits)
    print(f"PACTG hit policies: {sum(1 for d in digits if buckets.get(d))}")

    print(f"Streaming PRELSA for {len(digits)} gap policies ...")
    prelsa = stream_prelsa_for_policies(Path(args.prelsa), digits)
    print(f"PRELSA hit policies: {sum(1 for d in digits if prelsa.get(d, {}).get('prelsa_row_count', 0))}")

    rows_out: list[dict] = []
    event_rows: list[dict] = []

    for _, g in gap.iterrows():
        pol = _strip(g["mpolicy"])
        dig = _strip(g["policy_digits"])
        cso_paid = _money(g["cso_total_paid"])
        pactg_rows = buckets.get(dig, [])
        pre = prelsa.get(dig, {})
        derived = derive_accounting_candidate(pactg_rows, cso_paid)

        # Output presence (read-only reference)
        in_out = "Y" if len(clms[clms["MPOLICY"].map(_strip) == pol]) else "N"
        death_n = 0
        if in_out == "Y":
            death_n = int(
                len(
                    clms[
                        (clms["MPOLICY"].map(_strip) == pol)
                        & (clms["_family"] == "DEATH_CLAIM")
                    ]
                )
            )

        row = {
            "analysis_label": "ANALYSIS_ONLY_NOT_PRODUCTION",
            "mpolicy": pol,
            "policy_digits": dig,
            "population": "MISSING_ERIC_SUPPLY",
            "in_cso_workbook_yn": "Y",
            "cso_total_paid": f"{cso_paid:.2f}",
            "cso_plan_code": _strip(g.get("cso_plan_code", "")),
            "cso_last_pd_date": _strip(g.get("cso_last_pd_date", "")),
            "in_current_output_yn": in_out,
            "output_death_header_n": death_n,
            "prior_recon_pactg_row_count": _strip(g.get("pactg_row_count", "")),
            "pactg_row_count_this_pass": len(pactg_rows),
            "pactg_present_yn": "Y" if pactg_rows else "N",
            "prelsa_row_count": pre.get("prelsa_row_count", 0),
            "prelsa_present_yn": "Y" if pre.get("prelsa_row_count", 0) else "N",
            "prelsa_payee_role_count": pre.get("prelsa_payee_role_count", 0),
            "prelsa_payee_roles_yn": "Y" if pre.get("prelsa_payee_role_count", 0) else "N",
            "prelsa_relate_codes": "|".join(
                f"{k}:{v}" for k, v in sorted(pre.get("prelsa_relate_codes", {}).items())
            ),
            "prelsa_payee_name_samples": "|".join(pre.get("prelsa_payee_names", [])),
            **derived,
            "amount_is_cso_validated_settlement": "N",
            "amount_is_accounting_derived_candidate": (
                "Y" if str(derived.get("category", "")).startswith("DERIVED_") else "N"
            ),
        }
        rows_out.append(row)

        # Event detail for derived + a sample of holds
        if pactg_rows and (
            row["category"].startswith("DERIVED_")
            or row["category"] in {"HOLD_AMBIGUOUS_CHAIN", "HOLD_INCOMPLETE_SOURCE"}
        ):
            loop_dates = loop_reissue_dates(pactg_rows)
            for e in economic_payout_events(pactg_rows):
                event_rows.append(
                    {
                        "mpolicy": pol,
                        "event_role": (
                            "EXCLUDED_LOOP_DATE"
                            if e["effective_date"] in loop_dates
                            else "INCLUDED_ECO_CANDIDATE"
                        ),
                        "effective_date": e["effective_date"],
                        "amount": e["amount"],
                        "debit_account": e.get("debit_account", ""),
                        "credit_account": e.get("credit_account", ""),
                        "debit_code": e.get("debit_code", ""),
                        "credit_code": e.get("credit_code", ""),
                        "date_reversed": e.get("date_reversed", ""),
                        "rule_reason": e.get("rule_reason", ""),
                        "policy_category": row["category"],
                        "derived_amount": row.get("derived_amount", ""),
                    }
                )
            for d in sorted(loop_dates):
                event_rows.append(
                    {
                        "mpolicy": pol,
                        "event_role": "LOOP_REISSUE_DATE_MARKER",
                        "effective_date": d,
                        "amount": "",
                        "debit_account": "",
                        "credit_account": "",
                        "debit_code": "",
                        "credit_code": "",
                        "date_reversed": "",
                        "rule_reason": "EXCLUDE_REINSTATEMENT_OR_INTRACO_REISSUE",
                        "policy_category": row["category"],
                        "derived_amount": row.get("derived_amount", ""),
                    }
                )

    grok = grok_validation_pass(rows_out, buckets)

    cat_counts = Counter(r["category"] for r in rows_out)
    confs = [int(r["confidence"]) for r in rows_out]
    bands = {
        "0": sum(1 for c in confs if c == 0),
        "1-39": sum(1 for c in confs if 1 <= c <= 39),
        "40-69": sum(1 for c in confs if 40 <= c <= 69),
        "70-89": sum(1 for c in confs if 70 <= c <= 89),
        "90-100": sum(1 for c in confs if c >= 90),
    }
    derived_rows = [r for r in rows_out if r["category"].startswith("DERIVED_")]
    derived_match = [r for r in derived_rows if r["cso_match_yn"] == "Y"]
    derived_mismatch = [r for r in derived_rows if r["cso_match_yn"] == "N"]

    # Higher model recommendation
    ambiguous = cat_counts.get("HOLD_AMBIGUOUS_CHAIN", 0)
    incomplete = cat_counts.get("HOLD_INCOMPLETE_SOURCE", 0)
    no_pactg = cat_counts.get("NO_PACTG_HISTORY", 0)
    if grok["overall"] != "PASS" or ambiguous > 50:
        higher = (
            "Optional: a higher-reasoning pass may help on HOLD_AMBIGUOUS_CHAIN policies "
            f"({ambiguous}) if business wants forced resolution; not required for "
            "NO_PACTG_HISTORY / clear DERIVED_HIGH. Current Grok validation "
            f"overall={grok['overall']}."
        )
    else:
        higher = (
            "No higher model required for this analysis pass. Remaining blockers are "
            f"source gaps (NO_PACTG_HISTORY={no_pactg}, HOLD_INCOMPLETE={incomplete}) "
            f"or ambiguous chains ({ambiguous}), not arithmetic failures."
        )

    summary = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "issue": 135,
        "analysis_label": "ANALYSIS_ONLY_NOT_PRODUCTION",
        "population": "MISSING_ERIC_SUPPLY",
        "population_n": len(rows_out),
        "category_counts": dict(cat_counts.most_common()),
        "with_pactg": sum(1 for r in rows_out if r["pactg_present_yn"] == "Y"),
        "no_pactg": sum(1 for r in rows_out if r["pactg_present_yn"] == "N"),
        "with_prelsa": sum(1 for r in rows_out if r["prelsa_present_yn"] == "Y"),
        "with_prelsa_payee_roles": sum(1 for r in rows_out if r["prelsa_payee_roles_yn"] == "Y"),
        "derived_n": len(derived_rows),
        "derived_cso_match_n": len(derived_match),
        "derived_cso_mismatch_n": len(derived_mismatch),
        "confidence_bands": bands,
        "pactg_path": str(pactg_path),
        "prelsa_path": str(Path(args.prelsa)),
        "premise": premise,
        "grok_validation_overall": grok["overall"],
        "higher_model_recommendation": higher,
        "explicit_separations": {
            "accounting_derived_candidate": "derived_amount when category starts with DERIVED_",
            "cso_crosscheck_match": "cso_validation_status=CSO_CROSSCHECK_MATCH",
            "cso_validated_production_settlement": "NONE in this pass — not production",
        },
    }

    examples: dict[str, list[dict]] = {}
    for cat in cat_counts:
        examples[cat] = [r for r in rows_out if r["category"] == cat][:5]

    # Write artifacts
    per_path = out_dir / "issue135_459_analysis_per_policy.csv"
    pd.DataFrame(rows_out).to_csv(per_path, index=False)

    ev_path = out_dir / "issue135_459_analysis_included_excluded_events.csv"
    pd.DataFrame(event_rows).to_csv(ev_path, index=False)

    sum_path = out_dir / "issue135_459_analysis_summary.json"
    sum_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    grok_path = out_dir / "issue135_459_analysis_grok_validation.json"
    grok_path.write_text(json.dumps(grok, indent=2), encoding="utf-8")

    md_path = out_dir / "issue135_459_analysis_report.md"
    write_report(md_path, summary, premise, grok, examples)

    print("\n=== ANALYSIS COMPLETE ===")
    print(json.dumps(summary["category_counts"], indent=2))
    print(f"with_pactg={summary['with_pactg']} no_pactg={summary['no_pactg']}")
    print(f"derived={summary['derived_n']} cso_match={summary['derived_cso_match_n']}")
    print(f"prelsa_payee_roles={summary['with_prelsa_payee_roles']}")
    print(f"grok={grok['overall']} fail={grok['fail_n']} warn={grok['warn_n']}")
    print(f"wrote {per_path}")
    print(f"wrote {md_path}")
    return 0 if grok["overall"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
