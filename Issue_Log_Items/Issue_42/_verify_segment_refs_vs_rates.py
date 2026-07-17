"""Cross-check Segment References color assessments against delivered rate extracts."""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974")
PARSED = ROOT / "Issue_Log_Items" / "Issue_42" / "evidence_segment_references_parsed.csv"
RT = ROOT / "plan_analysis" / "source_data" / "rates" / "Rate_Table_Extract_20260427.csv"
PA = ROOT / "plan_analysis" / "source_data" / "rates" / "PAAGERAT_AttainedAge_Rates_Extract_20260428.csv"
OUT = ROOT / "Issue_Log_Items" / "Issue_42" / "evidence_segment_refs_vs_extracts.csv"

# Map spreadsheet column header -> TYPE_CODE(s)
COL_TO_TYPES = {
    "Premiums (PR)": ["PR"],
    "Cash Values (CV)": ["CV"],
    "Dividends (DV)": ["DV"],
    "Death Benefits (DB)": ["DB"],
    "Reserve Factors (RV)": ["RV"],
    "Net Valuation Premiums (NP)": ["NP"],
    "Non-Forfeiture Factors (NF)": ["NF"],
    "Guar COI Rates (U5)": ["U5"],
    "Curr COI Rates (U6)": ["U6"],
}


def load_rate_index(path):
    """Return dict coverage_id -> set of type_codes, and (cov, type) -> rowcount."""
    by_cov = defaultdict(set)
    counts = defaultdict(int)
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f)
        # normalize fieldnames
        for row in r:
            cov = (row.get("COVERAGE_ID") or "").strip()
            typ = (row.get("TYPE_CODE") or "").strip()
            if not cov or cov.startswith("-"):
                continue
            by_cov[cov].add(typ)
            counts[(cov, typ)] += 1
    return by_cov, counts


print("Loading Rate_Table...")
rt_by, rt_counts = load_rate_index(RT)
print(f"  unique coverages={len(rt_by)}")
print("Loading PAAGERAT...")
pa_by, pa_counts = load_rate_index(PA)
print(f"  unique coverages={len(pa_by)}")

focus = {"dark_green", "light_green", "purple", "red", "peach", "yellow"}
rows_out = []
agree = disagree = partial = 0

with open(PARSED, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["assessment"] not in focus:
            continue
        col = row["rate_type_col"]
        types = COL_TO_TYPES.get(col)
        if not types:
            # non-rate setup columns — skip for extract presence check
            continue
        seg = row["segment"].strip()
        assess = row["assessment"]

        rt_types = rt_by.get(seg, set())
        pa_types = pa_by.get(seg, set())
        rt_hits = {t: rt_counts.get((seg, t), 0) for t in types}
        pa_hits = {t: pa_counts.get((seg, t), 0) for t in types}
        rt_any = sum(rt_hits.values())
        pa_any = sum(pa_hits.values())
        any_cov = seg in rt_by or seg in pa_by

        # Expected presence by assessment
        # dark_green / light_green: we should have received the rates
        # purple: attained-age needed (expect missing from PA for that type, or missing entirely)
        # red: age/duration needed (expect missing from RT for that type)
        # peach: no rates in LifePRO (expect missing from both)
        # yellow: research

        in_rt = rt_any > 0
        in_pa = pa_any > 0
        present = in_rt or in_pa

        expected = None
        verdict = "CHECK"
        note = ""

        if assess in ("dark_green", "light_green"):
            expected = "present"
            if present:
                verdict = "AGREE"
                note = f"found RT={rt_any} PA={pa_any}"
                agree += 1
            else:
                # maybe segment exists under other types
                if any_cov:
                    verdict = "PARTIAL"
                    note = f"cov exists but type {types} missing; RT types={sorted(rt_types)[:8]} PA types={sorted(pa_types)[:8]}"
                    partial += 1
                else:
                    verdict = "DISAGREE"
                    note = "marked received but ZERO rows in both extracts"
                    disagree += 1
        elif assess == "purple":
            # Attained age needed — should be missing from PA (or both) for the type
            expected = "missing_pa"
            if in_pa:
                verdict = "DISAGREE"
                note = f"marked AA-needed but PA has {pa_any} rows for {types}"
                disagree += 1
            elif in_rt and types == ["PR"]:
                # PR sometimes wrongly in RT — unusual
                verdict = "PARTIAL"
                note = f"missing PA but present in RT={rt_any} (unusual for PR)"
                partial += 1
            else:
                verdict = "AGREE"
                note = f"missing from PA (and RT={rt_any}) as expected for New Era AA request"
                agree += 1
        elif assess == "red":
            expected = "missing_rt"
            if in_rt:
                verdict = "DISAGREE"
                note = f"marked duration-needed but RT has {rt_any} rows for {types}"
                disagree += 1
            else:
                verdict = "AGREE"
                note = f"missing from RT (PA={pa_any}) as expected for New Era duration request"
                agree += 1
        elif assess == "peach":
            expected = "missing_both"
            if present:
                verdict = "DISAGREE"
                note = f"marked no-LP-rates but found RT={rt_any} PA={pa_any}"
                disagree += 1
            else:
                verdict = "AGREE"
                note = "absent from both extracts"
                agree += 1
        elif assess == "yellow":
            expected = "research"
            verdict = "RESEARCH"
            note = f"RT={rt_any} PA={pa_any} any_cov={any_cov}"
            partial += 1

        rows_out.append(
            {
                "sheet": row["sheet"],
                "policy_form": row["policy_form"],
                "rate_type_col": col,
                "type_codes": "|".join(types),
                "segment": seg,
                "assessment": assess,
                "rt_rows": rt_any,
                "pa_rows": pa_any,
                "rt_types_present": "|".join(sorted(rt_types)),
                "pa_types_present": "|".join(sorted(pa_types)),
                "verdict": verdict,
                "note": note,
            }
        )

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
    w.writeheader()
    w.writerows(rows_out)

print(f"\nWrote {OUT}")
print(f"Checked {len(rows_out)} rate-relevant cells")
print(f"AGREE={agree} DISAGREE={disagree} PARTIAL/RESEARCH={partial}")

# Summary by assessment + verdict
print("\n=== By assessment x verdict ===")
summ = defaultdict(int)
for r in rows_out:
    summ[(r["assessment"], r["verdict"])] += 1
for k in sorted(summ):
    print(f"  {k[0]:12} {k[1]:10} {summ[k]}")

print("\n=== DISAGREE detail ===")
for r in rows_out:
    if r["verdict"] == "DISAGREE":
        print(
            f"  [{r['sheet']}] {r['policy_form']} | {r['rate_type_col']} | seg={r['segment']} | {r['note']}"
        )

print("\n=== PARTIAL detail ===")
for r in rows_out:
    if r["verdict"] == "PARTIAL":
        print(
            f"  [{r['sheet']}] {r['policy_form']} | {r['rate_type_col']} | seg={r['segment']} | {r['note']}"
        )

print("\n=== Issue 42 focus (L01/L10 LP9595) ===")
for r in rows_out:
    if "L01 10Y" in r["segment"] or "L10 LP9595" in r["segment"] or "L01 10Y" in r["policy_form"]:
        print(
            f"  {r['assessment']:12} {r['policy_form']} | {r['rate_type_col']} | {r['segment']} | RT={r['rt_rows']} PA={r['pa_rows']} | {r['verdict']}"
        )

# Unique New Era request list (purple + red unique segment+type)
print("\n=== Unique New Era requests (purple AA / red duration) ===")
seen = set()
for r in rows_out:
    if r["assessment"] in ("purple", "red") and r["verdict"] in ("AGREE", "PARTIAL"):
        key = (r["assessment"], r["segment"], r["type_codes"])
        if key in seen:
            continue
        seen.add(key)
        kind = "AttainedAge(PAAGERAT)" if r["assessment"] == "purple" else "AgeDuration(Rate_Table)"
        print(f"  {kind}: segment={r['segment']!r} types={r['type_codes']} (example form {r['policy_form']})")
print(f"Unique request keys: {len(seen)}")
