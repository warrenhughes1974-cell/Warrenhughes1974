"""Rate source-identity validator — LifePRO native grids vs loaded Quik* tables.

Independence rule (the reason this exists): this script shares NO code with the
rate loader. No qla_core imports, no cv_remap, no duration_to_ql_for_type. The
LifePRO axis is derived from the physical file layout only:

  PDAGE     pages of ten factors: native year = (DURATION-1)*10 + column + 1
  PAAGERAT  1-based ordinal:      issue age  = SEQ - 1

Three legs:
  1. Grid identity  — every PDAGE/PAAGERAT cell vs every loaded factor cell,
     tested at offsets -1/0/+1 per slice. A family must land on ONE offset
     fleet-wide. Endpoint (last nonzero source year vs last loaded slot) is
     reported per plan and is automatically offset-aware.
  2. Policy dollars — ValxLife per-policy dollars ÷ units located on the loaded
     grid at the policy's own issue age / policy year (CV pair T-1/T, dividend,
     terminal reserve pair, gross premium via quikridr.MPREM at MAGE).
  3. Post-load parity — optional --qla-export dir compared cell-wise to the
     package (NOT RUN when absent; a correct CSV loaded wrong is still wrong).

Verdicts are per (family, plan): ALIGNED / MISALIGNED / MISMATCH / NO_SOURCE /
UNTESTABLE. Zero-value source cells missing from the loaded table are noted,
not failed. Nothing is forced through a formula it does not fit.

Usage:
  python tools/validators/validate_rate_source_identity.py
  python tools/validators/validate_rate_source_identity.py --qla-export C:/path/to/export
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "QLA_Migration" / "Source"
RATES = ROOT / "QLA_Migration" / "Output" / "rates"
RIDR = ROOT / "QLA_Migration" / "Output" / "quikridr.csv"
VALX_XLSX = ROOT / "docs" / "Valuation" / "QLReports" / "QLAdmin-ValxLife 6-2026 run at 6-2026.xlsx"
CROSSWALK = ROOT / "plan_analysis" / "source_data" / "crosswalk" / "Policy Form Crosswalk 5.22.26.xlsx"
EVIDENCE = ROOT / "QLA_Migration" / "Validation" / "rate_source_identity"

PDAGE_GLOB = "PDAGE_AgeDuration_Rates_Extract_*.csv"
PAAGERAT_GLOB = "PAAGERAT_AttainedAge_Rates_Extract_*.csv"

# family -> (loaded table file, factor prefix)
PDAGE_FAMILIES = {
    "CV": ("QuikCvs.csv", "CV"),
    "DV": ("QuikDvs.csv", "DV"),
    "NP": ("QuikNps.csv", "NP"),
    "RV": ("QuikTvs.csv", "TV"),
    "DB": ("QuikDbs.csv", "DB"),
}
GP_TABLE = ("QuikGps.csv", "GP")

OFFSETS = (-1, 0, 1)
CELL_TOL = 0.006          # loaded factors are CHAR(7) 2dp text
SLICE_MATCH_SHARE = 0.95  # nonzero-cell share for a slice to count as matched
MIN_POLICIES = 5


def _f(s):
    s = (s or "").strip()
    if s in ("", ".", "-", "-."):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _dash(s):
    s = (s or "").strip()
    return bool(s) and set(s) <= {"-"}


# ---------------------------------------------------------------- source read

def newest(glob_pat):
    files = sorted(SOURCE.glob(glob_pat))
    return files[-1] if files else None


def read_pdage():
    """(type, cov, sex, uwcls, band, age) -> {native_year: value} from raw pages."""
    path = newest(PDAGE_GLOB)
    if path is None:
        return None, {}
    slices = defaultdict(dict)
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        rd = csv.reader(f)
        header = [h.strip() for h in next(rd)]
        ix = {h: i for i, h in enumerate(header)}
        c_cov, c_typ = ix["COVERAGE_ID"], ix["TYPE_CODE"]
        c_age, c_sex = ix["AGE"], ix["SEX"]
        c_band, c_uw, c_dur = ix["BAND"], ix["UWCLS"], ix["DURATION"]
        c_vals = [ix[f"VALUE{i}"] for i in range(1, 11)]
        for r in rd:
            if len(r) <= c_vals[-1]:
                continue
            typ = r[c_typ].strip()
            if typ not in PDAGE_FAMILIES:
                continue
            cov = r[c_cov].strip()
            if not cov or _dash(cov):
                continue
            try:
                age = int(float(r[c_age]))
                page = int(float(r[c_dur]))
            except ValueError:
                continue
            key = (typ, cov, r[c_sex].strip(), r[c_uw].strip(), r[c_band].strip(), age)
            base = (page - 1) * 10
            d = slices[key]
            for i, ci in enumerate(c_vals):
                v = _f(r[ci])
                if v is not None:
                    d[base + i + 1] = v
    return path, slices


def read_paagerat():
    """('PR'|'CV', cov, sex, uwcls, band) -> {age: value}.

    PR: issue-age axis, SEQ is a 1-based ordinal (Issue 138) -> age = SEQ - 1.
    CV: PUA attained-age axis, SEQ IS the attained age (proven 2026-08-13:
        '670 PUA' M SEQ 60 = 667.90 = Eric's implied ~668 at attained 60).
    """
    path = newest(PAAGERAT_GLOB)
    if path is None:
        return None, {}
    slices = defaultdict(dict)
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        rd = csv.reader(f)
        header = [h.strip() for h in next(rd)]
        ix = {h: i for i, h in enumerate(header)}
        for r in rd:
            if len(r) <= ix["SEQ"]:
                continue
            typ = r[ix["TYPE_CODE"]].strip()
            if typ not in ("PR", "CV"):
                continue
            cov = r[ix["COVERAGE_ID"]].strip()
            if not cov or _dash(cov):
                continue
            try:
                seq = int(float(r[ix["SEQ"]]))
            except ValueError:
                continue
            v = _f(r[ix["VALUE_INFO"]])
            if v is None:
                continue
            key = (typ, cov, r[ix["SEX"]].strip(), r[ix["UWCLS"]].strip(),
                   r[ix["BAND"]].strip())
            slices[key][seq - 1 if typ == "PR" else seq] = v
    return path, slices


def load_crosswalk():
    """coverage -> plan and plan -> [coverages] from the Policy Form Crosswalk."""
    try:
        import openpyxl
    except ImportError:
        return {}, {}
    if not CROSSWALK.is_file():
        return {}, {}
    wb = openpyxl.load_workbook(CROSSWALK, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    cov2plan, plan2covs = {}, defaultdict(list)
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        cov = str(row[0]).strip() if row and row[0] else ""
        plan = str(row[2]).strip() if len(row) > 2 and row[2] else ""
        if cov and plan:
            cov2plan[cov] = plan
            plan2covs[plan].append(cov)
    wb.close()
    return cov2plan, dict(plan2covs)


# ---------------------------------------------------------------- loaded read

def read_factor_table(fname, pfx):
    """(plan, gender, uwclass, band, age) -> {slot: value}; also slot-axis plan set."""
    path = RATES / fname
    grids = defaultdict(dict)
    slot_axis = set()
    if not path.is_file():
        return grids, slot_axis
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for r in csv.DictReader(f):
            plan = (r.get("PLAN") or "").strip()
            if not plan:
                continue
            age = (r.get("AGE") or "").strip()
            try:
                cntl = int((r.get("CNTL") or "0").strip() or 0)
            except ValueError:
                continue
            if age == "00" and cntl > 0:
                slot_axis.add(plan)
            key = (plan, (r.get("GENDER") or "").strip(),
                   (r.get("UWCLASS") or "").strip(), (r.get("BAND") or "").strip(), age)
            g = grids[key]
            for i in range(10):
                v = _f(r.get(f"{pfx}{i}"))
                if v is not None:
                    g[cntl * 10 + i] = v
    return grids, slot_axis


# ------------------------------------------------------------- slice compare

def trim(src):
    """Drop trailing zero page-padding; keep interior zeros. None if all zero."""
    nz = [k for k, v in src.items() if v]
    if not nz:
        return None, 0
    last = max(nz)
    return {k: v for k, v in src.items() if k <= last}, last


def compare(src, loaded, offset):
    """(nonzero_tested, nonzero_matched, zero_omitted, mismatch_examples)."""
    tested = matched = zomit = 0
    ex = []
    for y, v in src.items():
        lv = loaded.get(y + offset)
        if v == 0.0:
            if lv is None:
                zomit += 1
            continue
        tested += 1
        if lv is not None and abs(lv - v) <= CELL_TOL:
            matched += 1
        elif len(ex) < 3:
            ex.append((y, v, lv))
    return tested, matched, zomit, ex


def best_offset(src, loaded):
    scores = {}
    for o in OFFSETS:
        t, m, _, _ = compare(src, loaded, o)
        scores[o] = (m, t)
    o = max(scores, key=lambda k: scores[k][0])
    return o, scores


# ------------------------------------------------------------------ leg 1

def leg1_grid_identity(pdage, paagerat, cov2plan, plan2covs):
    """Compare every loaded slice to its LifePRO source slice.

    Join order per loaded slice: crosswalk coverage first, then fingerprint
    search across all source slices with the same (type, sex, age).
    """
    # index source by (type, sex, age) -> [(cov, uwcls, band, vec)]
    src_ix = defaultdict(list)
    for (typ, cov, sex, uw, band, age), vec in pdage.items():
        v, _ = trim(vec)
        if v:
            src_ix[(typ, sex, age)].append((cov, uw, band, v))
    pr_ix = defaultdict(list)     # sex -> [(cov, uwcls, band, vec)] TYPE=PR
    cv_aa_ix = defaultdict(list)  # sex -> [(cov, uwcls, band, vec)] TYPE=CV attained-age
    for (typ, cov, sex, uw, band), vec in paagerat.items():
        v, _ = trim(vec)
        if v:
            (pr_ix if typ == "PR" else cv_aa_ix)[sex].append((cov, uw, band, v))

    plan_rows = {}           # (family, plan) -> stats dict
    mismatch_rows = []

    def slice_result(family, plan, gender, age_label, loaded_vec, candidates):
        """Best (offset, coverage) for one loaded slice among candidate source vecs."""
        best = None
        for cov, uw, band, svec in candidates:
            o, scores = best_offset(svec, loaded_vec)
            m, t = scores[o]
            share = m / t if t else 0.0
            if best is None or m > best[0]:
                best = (m, t, share, o, cov, svec)
        return best

    def account(family, plan, res, gender, age_label, loaded_vec, joined_via):
        st = plan_rows.setdefault((family, plan), {
            "slices": 0, "cells": 0, "matched": 0, "offsets": Counter(),
            "covs": Counter(), "no_source": 0, "endpoint_ok": 0,
            "endpoint_bad": 0, "join": Counter(), "examples": []})
        st["slices"] += 1
        if res is None:
            st["no_source"] += 1
            return
        m, t, share, o, cov, svec = res
        st["cells"] += t
        st["matched"] += m
        st["offsets"][o] += t
        st["covs"][cov] += 1
        st["join"][joined_via] += 1
        # endpoint: last nonzero source year must land at last nonzero loaded slot
        src_last = max(y for y, v in svec.items() if v)
        nz_loaded = [s for s, v in loaded_vec.items() if v]
        if nz_loaded and max(nz_loaded) == src_last + o and \
           abs(loaded_vec[max(nz_loaded)] - svec[src_last]) <= CELL_TOL:
            st["endpoint_ok"] += 1
        else:
            st["endpoint_bad"] += 1
        if share < SLICE_MATCH_SHARE and len(st["examples"]) < 3:
            _, _, _, ex = compare(svec, loaded_vec, o)
            st["examples"].append((gender, age_label, o, ex))
            for y, v, lv in ex:
                mismatch_rows.append([family, plan, gender, age_label, cov, o, y, v, lv])

    # PDAGE families
    for family, (fname, pfx) in PDAGE_FAMILIES.items():
        grids, _ = read_factor_table(fname, pfx)
        # PUA CV rides the Issue 140 attained-age slot axis; its source is
        # PAAGERAT TYPE=CV (attained age), not PDAGE. An attained-age plan is
        # one whose EVERY row sits at AGE=00 (a real issue-age plan always has
        # other ages too, even when its age-0 grid spans CNTL pages). Merge the
        # AGE=00 pages into one attained-age vector per (plan, gender, uw, band).
        aa_only = set()
        if family == "CV":
            plan_ages = defaultdict(set)
            for (plan, _g, _u, _b, age), _v in grids.items():
                plan_ages[plan].add(age)
            aa_only = {p for p, ages in plan_ages.items() if ages == {"00"}}
        aa_merged = defaultdict(dict)
        for (plan, gender, uw, band, age), lvec in grids.items():
            if family == "CV" and plan in aa_only:
                aa_merged[(plan, gender, uw, band)].update(lvec)
                continue
            if not any(lvec.values()):
                continue
            try:
                age_i = int(age)
            except ValueError:
                continue
            covs = plan2covs.get(plan, [])
            cands = [c for c in src_ix.get((family, gender, age_i), []) if c[0] in covs]
            joined = "crosswalk"
            res = slice_result(family, plan, gender, age, lvec, cands) if cands else None
            if res is None or res[2] < SLICE_MATCH_SHARE:
                allc = src_ix.get((family, gender, age_i), [])
                res2 = slice_result(family, plan, gender, age, lvec, allc) if allc else None
                if res2 is not None and (res is None or res2[0] > res[0]):
                    res, joined = res2, "fingerprint"
            account(family, plan, res, gender, age, lvec, joined)
        for (plan, gender, uw, band), lvec in aa_merged.items():
            if not any(lvec.values()):
                continue
            covs = plan2covs.get(plan, [])
            cands = [c for c in cv_aa_ix.get(gender, []) if c[0] in covs]
            joined = "crosswalk"
            res = slice_result(family, plan, gender, "AA", lvec, cands) if cands else None
            if res is None or res[2] < SLICE_MATCH_SHARE:
                allc = cv_aa_ix.get(gender, [])
                res2 = slice_result(family, plan, gender, "AA", lvec, allc) if allc else None
                if res2 is not None and (res is None or res2[0] > res[0]):
                    res, joined = res2, "fingerprint"
            account(family, plan, res, gender, "AA", lvec, joined)

    # PR / QuikGps
    gp_grids, slot_axis = read_factor_table(*GP_TABLE)
    # collapse slot-axis plan pages into one age-indexed vector per key
    merged = defaultdict(dict)
    for (plan, gender, uw, band, age), lvec in gp_grids.items():
        if plan in slot_axis:
            merged[(plan, gender, uw, band, "SLOT")].update(lvec)
        else:
            # issue-age axis: value at column 0 belongs to that AGE
            if 0 in lvec:
                try:
                    merged[(plan, gender, uw, band, "AGE")][int(age)] = lvec[0]
                except ValueError:
                    pass
    for (plan, gender, uw, band, axis), lvec in merged.items():
        if not any(lvec.values()):
            continue
        covs = plan2covs.get(plan, [])
        cands = [c for c in pr_ix.get(gender, []) if c[0] in covs]
        joined = "crosswalk"
        res = slice_result("PR", plan, gender, axis, lvec, cands) if cands else None
        if res is None or res[2] < SLICE_MATCH_SHARE:
            allc = pr_ix.get(gender, [])
            res2 = slice_result("PR", plan, gender, axis, lvec, allc) if allc else None
            if res2 is not None and (res is None or res2[0] > res[0]):
                res, joined = res2, "fingerprint"
        account("PR", plan, res, gender, axis, lvec, joined)

    return plan_rows, mismatch_rows


# ------------------------------------------------------------------ leg 2

VALX_COL = {  # 0-based indices in the ValxLife sheet (headers on row 2)
    "policy": 2, "seq": 3, "plan_id": 9, "ben_type": 11, "sex": 14,
    "issue_age": 16, "policy_year": 19, "policy_month": 20, "paid_up": 22,
    "units": 30, "prem_per_unit": 44, "rv_t1": 52, "rv_t": 53,
    "rv_val_prem": 54, "dividend": 99, "cv_t1": 103, "cv_t": 104,
}


def read_valx():
    try:
        import openpyxl
    except ImportError:
        return []
    if not VALX_XLSX.is_file():
        return []
    wb = openpyxl.load_workbook(VALX_XLSX, read_only=True, data_only=True)
    ws = wb["ValxLife"]
    out = []
    for row in ws.iter_rows(min_row=3, max_col=110, values_only=True):
        if row[VALX_COL["policy"]] is None:
            continue
        out.append({k: row[i] for k, i in VALX_COL.items()})
    wb.close()
    return out


def read_ridr():
    """(digits(MPOLICY), MPHASE) -> policy dict."""
    out = {}
    if not RIDR.is_file():
        return out
    with RIDR.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for r in csv.DictReader(f):
            pol = re.sub(r"\D", "", (r.get("MPOLICY") or ""))
            ph = (r.get("MPHASE") or "").strip()
            out[(pol, ph)] = {
                "plan": (r.get("MPLAN") or "").strip(),
                "sex": (r.get("MSEX") or "").strip(),
                "age": (r.get("MAGE") or "").strip(),
                "uw": (r.get("MUWCLASS") or "").strip(),
                "band": (r.get("MBAND") or "").strip(),
                "unit": _f(r.get("MUNIT")),
                "prem": _f(r.get("MPREM")),
            }
    return out


def grid_lookup(grids, plan, gender, uw, band):
    for b in (band, "00", "01"):
        g = grids.get((plan, gender, uw, b))
        if g:
            return g
    return None


def leg2_policy_dollars(ridr):
    """Score every testable Valx policy at duration offsets on the loaded grids."""
    fam_grids = {}
    for family, (fname, pfx) in PDAGE_FAMILIES.items():
        raw, _ = read_factor_table(fname, pfx)
        merged = defaultdict(dict)
        for (plan, gender, uw, band, age), vec in raw.items():
            merged[(plan, gender, uw, band, age)] = vec
        fam_grids[family] = merged
    gp_raw, gp_slots = read_factor_table(*GP_TABLE)
    gp = defaultdict(dict)
    for (plan, gender, uw, band, age), vec in gp_raw.items():
        if plan in gp_slots:
            gp[(plan, gender, uw, band, "SLOT")].update(vec)
        elif 0 in vec:
            try:
                gp[(plan, gender, uw, band, "AGE")][int(age)] = vec[0]
            except ValueError:
                pass

    def fam_slice(family, p, age=None):
        for b in (p["band"], "00", "01"):
            key = (p["plan"], p["sex"], p["uw"], b, (age or p["age"]).zfill(2))
            g = fam_grids[family].get(key)
            if g:
                return g
        return None

    stats = defaultdict(lambda: defaultdict(lambda: {
        "n": 0, "hits": Counter(), "untestable": Counter(), "examples": []}))
    exceptions = []

    for v in read_valx():
        pol = str(v["policy"]).strip()
        seq = str(v["seq"]).strip()
        p = ridr.get((re.sub(r"\D", "", pol), seq))
        bt = str(v["ben_type"] or "").strip()
        pu = str(v["paid_up"] or "").strip()
        units = float(v["units"] or 0)
        try:
            py = int(v["policy_year"])
        except (TypeError, ValueError):
            py = None
        if p is None or bt != "BA" or pu or units <= 0 or py is None or py < 2:
            continue
        tol_u = 0.005 / units + 0.006

        def score(family, pairs, single=None):
            st = stats[family][p["plan"]]
            g = fam_slice(family, p)
            if g is None:
                st["untestable"]["no_grid"] += 1
                return
            st["n"] += 1
            hit_any = False
            for o in OFFSETS:
                ok = True
                if pairs:
                    for (yy, val) in pairs:
                        lv = g.get(yy + o)
                        if lv is None or abs(lv - val) > tol_u:
                            ok = False
                            break
                elif single is not None:
                    yy, val = single
                    lv = g.get(yy + o)
                    ok = lv is not None and abs(lv - val) <= tol_u
                else:
                    ok = False
                if ok:
                    st["hits"][o] += 1
                    hit_any = True
            if not hit_any:
                st["hits"]["none"] += 1
                if len(st["examples"]) < 3:
                    st["examples"].append(pol)
                exceptions.append([family, p["plan"], pol, seq, p["age"], py,
                                   (pairs or [single])[0][1]])

        cv1, cv2 = float(v["cv_t1"] or 0), float(v["cv_t"] or 0)
        if cv1 > 0 and cv2 > 0:
            score("CV", [(py - 1, round(cv1 / units, 4)), (py, round(cv2 / units, 4))])
        rv1, rv2 = float(v["rv_t1"] or 0), float(v["rv_t"] or 0)
        if rv1 > 0 and rv2 > 0:
            score("RV", [(py - 1, round(rv1 / units, 4)), (py, round(rv2 / units, 4))])
        # DV convention proven 2026-08-13 (Eric workbook): the dividend paid at
        # the anniversary during the valuation year is the NATIVE year-py factor
        # (1960PO: 333.60 = 22.24x15u at native Dur 57), not py-1.
        dv = float(v["dividend"] or 0)
        if dv > 0:
            score("DV", None, single=(py, round(dv / units, 4)))
        npv = float(v["rv_val_prem"] or 0)
        if npv > 0:
            score("NP", None, single=(py - 1, round(npv / units, 4)))

        # GP: quikridr.MPREM at MAGE (independent policy field, Issue 88 lineage)
        prem = p["prem"]
        if prem and prem > 0 and p["age"].isdigit():
            st = stats["PR"][p["plan"]]
            age_i = int(p["age"])
            g = None
            for b in (p["band"], "00", "01"):
                g = gp.get((p["plan"], p["sex"], p["uw"], b, "SLOT")) or \
                    gp.get((p["plan"], p["sex"], p["uw"], b, "AGE"))
                if g:
                    break
            if g is None:
                st["untestable"]["no_grid"] += 1
            else:
                st["n"] += 1
                hit = False
                for o in OFFSETS:
                    lv = g.get(age_i + o)
                    if lv is not None and abs(lv - round(prem, 2)) <= 0.006:
                        st["hits"][o] += 1
                        hit = True
                if not hit:
                    st["hits"]["none"] += 1
                    if len(st["examples"]) < 3:
                        st["examples"].append(pol)
                    exceptions.append(["PR", p["plan"], pol, seq, p["age"], py, prem])

    return stats, exceptions


def classify_leg2(row):
    n = row["n"]
    at0, up, dn, none = row["hits"][0], row["hits"][1], row["hits"][-1], row["hits"]["none"]
    if n < MIN_POLICIES:
        return "TOO_FEW"
    best = max(OFFSETS, key=lambda o: row["hits"][o])
    if row["hits"][best] == 0:
        return "UNTESTABLE" if none == n else "MIXED"
    if none > n * 0.5:
        return "MOSTLY_NO_MATCH"
    return f"ALIGNED@{best:+d}" if row["hits"][best] >= n * 0.8 else "PARTIAL"


# ------------------------------------------------------------------ leg 3

def leg3_export_parity(export_dir):
    results = []
    for family, (fname, pfx) in {**PDAGE_FAMILIES, "PR": GP_TABLE}.items():
        pkg = RATES / fname
        exp = export_dir / fname
        if not exp.is_file():
            alt = [p for p in export_dir.glob("*") if p.stem.lower() == Path(fname).stem.lower()]
            exp = alt[0] if alt else exp
        if not pkg.is_file() or not exp.is_file():
            results.append((fname, "MISSING", 0, 0))
            continue

        def rows(path):
            with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
                out = {}
                for r in csv.DictReader(f):
                    key = tuple((r.get(k) or "").strip() for k in
                                ("PLAN", "AGE", "CNTL", "GENDER", "UWCLASS", "BAND"))
                    out[key] = tuple((r.get(f"{pfx}{i}") or "").strip() for i in range(10))
                return out

        a, b = rows(pkg), rows(exp)
        diff = sum(1 for k in a if k not in b or b[k] != a[k]) + sum(1 for k in b if k not in a)
        results.append((fname, "PASS" if diff == 0 else "FAIL", len(a), diff))
    return results


# -------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="LifePRO source-identity rate validator")
    ap.add_argument("--qla-export", type=Path, default=None)
    args = ap.parse_args()

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    print("Rate source-identity validator (independent of loader code)")

    cov2plan, plan2covs = load_crosswalk()
    print(f"  crosswalk: {len(cov2plan)} coverages -> {len(plan2covs)} plans")

    pd_path, pdage = read_pdage()
    pr_path, paagerat = read_paagerat()
    print(f"  PDAGE:    {pd_path.name if pd_path else 'MISSING'} ({len(pdage)} slices)")
    print(f"  PAAGERAT: {pr_path.name if pr_path else 'MISSING'} ({len(paagerat)} PR slices)")

    # ---- leg 1
    plan_rows, mismatch_rows = leg1_grid_identity(pdage, paagerat, cov2plan, plan2covs)

    fam_offset = {}
    for family in list(PDAGE_FAMILIES) + ["PR"]:
        votes = Counter()
        for (f, _), st in plan_rows.items():
            if f == family:
                votes.update(st["offsets"])
        fam_offset[family] = votes.most_common(1)[0][0] if votes else None

    leg1_csv = EVIDENCE / "grid_identity_by_plan.csv"
    fails1, endpoint_bad = [], []
    with leg1_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["FAMILY", "PLAN", "SLICES", "NONZERO_CELLS", "MATCHED",
                    "MATCH_SHARE", "BEST_OFFSET", "FAMILY_OFFSET", "SOURCE_COVS",
                    "JOIN", "NO_SOURCE_SLICES", "ENDPOINT_OK", "ENDPOINT_BAD", "VERDICT"])
        for (family, plan), st in sorted(plan_rows.items()):
            share = st["matched"] / st["cells"] if st["cells"] else 0.0
            off = st["offsets"].most_common(1)[0][0] if st["offsets"] else None
            verdict = "MATCH"
            if st["cells"] == 0:
                verdict = "NO_SOURCE"
            elif share < SLICE_MATCH_SHARE:
                verdict = "MISMATCH"
            elif off != fam_offset[family]:
                verdict = "OFFSET_DIVERGES"
            if verdict in ("MISMATCH", "OFFSET_DIVERGES"):
                fails1.append((family, plan, verdict, round(share, 4), off))
            if st["endpoint_bad"]:
                endpoint_bad.append((family, plan, st["endpoint_bad"], st["endpoint_ok"]))
            w.writerow([family, plan, st["slices"], st["cells"], st["matched"],
                        f"{share:.4f}", off, fam_offset[family],
                        ";".join(c for c, _ in st["covs"].most_common(3)),
                        ";".join(f"{k}:{v}" for k, v in st["join"].items()),
                        st["no_source"], st["endpoint_ok"], st["endpoint_bad"], verdict])

    with (EVIDENCE / "grid_mismatch_cells.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["FAMILY", "PLAN", "GENDER", "AGE", "SOURCE_COV", "OFFSET",
                    "NATIVE_YEAR", "SOURCE_VALUE", "LOADED_VALUE"])
        w.writerows(mismatch_rows[:5000])

    print("\nLeg 1 — grid identity (native LifePRO axis vs loaded tables)")
    for family in list(PDAGE_FAMILIES) + ["PR"]:
        plans = [(p, st) for (f, p), st in plan_rows.items() if f == family]
        cells = sum(st["cells"] for _, st in plans)
        matched = sum(st["matched"] for _, st in plans)
        print(f"  {family}: plans={len(plans)} cells={cells} matched={matched} "
              f"({matched / cells:.2%} at family offset {fam_offset[family]})"
              if cells else f"  {family}: no comparable cells")
    if fails1:
        print(f"  FAILING plans ({len(fails1)}):")
        for family, plan, verdict, share, off in fails1[:20]:
            print(f"    - {family} {plan}: {verdict} share={share} offset={off}")
    if endpoint_bad:
        print(f"  endpoint misalignments on {len(endpoint_bad)} plan/family pairs "
              f"(see grid_identity_by_plan.csv)")

    # ---- leg 2
    ridr = read_ridr()
    print(f"\nLeg 2 — policy dollars (Valx + quikridr, {len(ridr)} phases)")
    stats, exceptions = leg2_policy_dollars(ridr)

    leg2_csv = EVIDENCE / "policy_dollar_by_plan.csv"
    fails2 = []
    with leg2_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["FAMILY", "PLAN", "POLICIES", "AT_-1", "AT_0", "AT_+1",
                    "NO_MATCH", "NO_GRID", "VERDICT", "EXAMPLES"])
        for family in sorted(stats):
            for plan in sorted(stats[family]):
                row = stats[family][plan]
                verdict = classify_leg2(row)
                if verdict in ("MIXED", "MOSTLY_NO_MATCH"):
                    fails2.append((family, plan, verdict, row["n"]))
                w.writerow([family, plan, row["n"], row["hits"][-1], row["hits"][0],
                            row["hits"][1], row["hits"]["none"],
                            row["untestable"]["no_grid"], verdict,
                            ";".join(row["examples"])])
    with (EVIDENCE / "policy_dollar_exceptions.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["FAMILY", "PLAN", "POLICY", "SEQ", "ISSUE_AGE", "POLICY_YEAR", "IMPLIED"])
        w.writerows(exceptions[:20000])

    for family in sorted(stats):
        n = sum(r["n"] for r in stats[family].values())
        at = {o: sum(r["hits"][o] for r in stats[family].values()) for o in OFFSETS}
        none = sum(r["hits"]["none"] for r in stats[family].values())
        print(f"  {family}: policies={n} match -1={at[-1]} 0={at[0]} +1={at[1]} none={none}")
    if fails2:
        print(f"  plans with mixed/no dollar match ({len(fails2)}):")
        for family, plan, verdict, n in fails2[:20]:
            print(f"    - {family} {plan}: {verdict} over {n} policies")

    # ---- leg 3
    print("\nLeg 3 — post-load QLAdmin export parity")
    leg3 = None
    if args.qla_export and args.qla_export.is_dir():
        leg3 = leg3_export_parity(args.qla_export)
        for fname, status, rows_n, diff in leg3:
            print(f"  {fname}: {status} rows={rows_n} diffs={diff}")
    else:
        print("  NOT RUN — provide --qla-export after loading the package into QLAdmin")

    summary = {
        "family_offsets": fam_offset,
        "leg1_failing_plans": [list(x) for x in fails1],
        "leg1_endpoint_bad": [list(x) for x in endpoint_bad],
        "leg2_failing_plans": [list(x) for x in fails2],
        "leg3": ([list(x) for x in leg3] if leg3 else "NOT_RUN"),
        "result": "FAIL" if (fails1 or fails2) else "PASS_WITH_LEG3_PENDING" if leg3 is None else "PASS",
    }
    (EVIDENCE / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nEvidence: {EVIDENCE}")
    print(f"RESULT: {summary['result']}")
    return 1 if (fails1 or fails2) else 0


if __name__ == "__main__":
    sys.exit(main())
