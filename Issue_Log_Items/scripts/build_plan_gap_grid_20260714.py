"""Build per-plan rate assumption gap grid (CSO crosswalk + 20260713 LifePRO zip grids)."""
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

grids = json.load(open(REPO / "_tmp_grids.json"))

# CSO crosswalk assumption codes per plan
cso = {}
with open(REPO / "plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv",
          newline="", encoding="utf-8", errors="replace") as f:
    for r in csv.DictReader(f):
        lp = (r.get("lifepro_coverage_id") or "").strip()
        if lp:
            cso[lp] = r

# PUA / synthetic plans from catalog crosswalk (not all in CSO)
catalog = {}
with open(REPO / "plan_governance/product_catalog_crosswalk.csv",
          newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.reader(f):
        if len(row) > 8:
            lp, qla = row[0].strip(), row[7].strip()
            if lp and qla:
                catalog[lp] = qla


# Crosswalk plan IDs that map to a different (umbrella) COVERAGE_ID in the rate extracts
GRID_ALIASES = {
    "L17 1": "L17",
    "L17 2+": "L17",
    "L17 BASE": "L17",
    "L17 1 JPO": "L17",
    "L17 2+ JPO": "L17",
}


def grid_status(cov, code):
    keys = [cov, GRID_ALIASES.get(cov, cov)]
    return "HAVE" if any(code in grids.get(k, []) for k in keys) else "MISSING"


out = []
all_covs = sorted(set(list(cso.keys()) + [c for c in grids if "PUA" in c]))
for cov in all_covs:
    r = cso.get(cov, {})
    qla = (r.get("qla_plan_code") or catalog.get(cov, "")).strip()
    desc = (r.get("qla_plan_description") or "").strip()
    nfo_src = (r.get("nfo_interest_source") or "").strip()
    nfo_code = (r.get("nfo_interest_code") or "").strip()
    mort = (r.get("mort_code_default") or "").strip()
    eti = (r.get("eti_code_default") or "").strip()
    intcv = (r.get("qla_intmethcv_code") or "").strip()
    notes = (r.get("conversion_notes") or "").strip()

    no_cv_plan = "No cash-value assumptions" in notes
    in_cso = cov in cso

    if no_cv_plan:
        f_mort = f_eti = f_nfo = f_int = "N/A (no CV product)"
    elif not in_cso:
        f_mort = f_eti = f_nfo = f_int = "MISSING (not in CSO crosswalk)"
    else:
        f_mort = mort if mort else "MISSING"
        f_eti = eti if eti else "BLANK (no ETI table in source)"
        if nfo_code:
            f_nfo = f"{nfo_code} ({nfo_src})"
        elif "Commission" in nfo_src:
            f_nfo = "MISSING - CRVM (need issue-year rate)"
        elif nfo_src:
            f_nfo = f"MISSING - graded ({nfo_src})"
        else:
            f_nfo = "MISSING"
        f_int = intcv if intcv else "MISSING"

    cv = grid_status(cov, "CV")
    rv = grid_status(cov, "RV")
    np_ = grid_status(cov, "NP")
    nf = grid_status(cov, "NF")
    if no_cv_plan:
        cv = "N/A"

    tv_needed = (rv == "HAVE" or np_ == "HAVE") and not no_cv_plan
    if no_cv_plan:
        tv = "N/A"
    elif tv_needed:
        tv = "MISSING (RSVINT/RSVMETH/INTMETHTV/STOREMEANS/CALCMIDS)"
    else:
        tv = "MISSING + no RV/NP grids delivered"

    needs = []
    if "MISSING - CRVM" in f_nfo:
        needs.append("NFOINT rate by issue year")
    if "graded" in f_nfo:
        needs.append("NFOINT graded-rate handling")
    if not in_cso and not no_cv_plan:
        needs.append("Full CV/TV assumption row (add to CSO crosswalk)")
    if tv_needed:
        needs.append("QuikPlTv 5 assumption codes")
    if cv == "MISSING" and not no_cv_plan:
        needs.append("CV grid")
    if rv == "MISSING" and not no_cv_plan:
        needs.append("RV (reserve) grid")
    if np_ == "MISSING" and not no_cv_plan:
        needs.append("NP grid")

    out.append({
        "LifePRO Plan": cov,
        "QLA Plan": qla,
        "Description": desc,
        "QuikPlCv MORT": f_mort,
        "QuikPlCv ETIMORT": f_eti,
        "QuikPlCv NFOINT": f_nfo,
        "QuikPlCv INTMETHCV": f_int,
        "QuikPlTv (all 5 fields)": tv,
        "QuikCvs CV grid": cv,
        "QuikTvs RV grid": rv,
        "QuikTvs NP grid": np_,
        "QuikNff NF grid": nf,
        "WHAT WE NEED FROM CSO": "; ".join(needs) if needs else "Nothing - complete",
    })

p = REPO / "Issue_Log_Items/Plan_By_Plan_Rate_Assumption_Gap_Grid_20260714.csv"
with p.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
print("rows:", len(out), "->", p)
