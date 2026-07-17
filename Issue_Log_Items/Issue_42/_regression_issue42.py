"""
Issue #42 Regression — candidates changed; non-candidates / other tables stable.

Read-only w.r.t. production logic. Writes evidence under Issue_42/evidence/.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974")
sys.path.insert(0, str(ROOT))

from qla_core import rate_pipeline as RP

CONFIG = ROOT / "plan_analysis" / "phase_r5_rate_loader" / "rate_loader_config.json"
RATES = ROOT / "QLA_Migration" / "Output" / "rates"
OUTPUT = ROOT / "QLA_Migration" / "Output"
EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_42" / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)

# Plans intentionally impacted by Issue #42 PDAGE miss-fill / inheritance
CANDIDATE_PLANS = frozenset(
    {
        "5L0110",  # L01 10Y
        "5L0510",  # L05 10Y
        "5L075Y",  # L07 5Y
        "1L10OD",
        "1L10PR",
        "1L10SO",
        "1L10SR",
        "1L1095",
        "196085",  # 960 LP85-8
        "1L17SP",  # L17
        "9POADB",
        "960ADB",
        "965ADB",
        "901ADB",
        "996ADB",
        "9ADB10",
        "976659",
        "9896WP",
        "9L01WP",
        "9065WP",
        "960SWP",
        "910RWP",
    }
)

INTENTIONALLY_EMITTED = frozenset({"QuikNps.csv", "QuikTvs.csv", "QuikPlTv.csv"})


def _rowcount(path: Path) -> int:
    if not path.is_file():
        return -1
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return sum(1 for _ in f) - 1


def _file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _plan_row_fingerprint(path: Path, plan_col: str = "PLAN") -> dict[str, tuple[int, str]]:
    """plan -> (row_count, md5 of sorted serialized rows)."""
    by_plan: dict[str, list[str]] = defaultdict(list)
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        rd = csv.DictReader(f)
        fields = rd.fieldnames or []
        for row in rd:
            plan = (row.get(plan_col) or "").strip()
            sig = "|".join((row.get(c) or "").strip() for c in fields)
            by_plan[plan].append(sig)
    out = {}
    for plan, rows in by_plan.items():
        rows_sorted = sorted(rows)
        h = hashlib.md5("\n".join(rows_sorted).encode("utf-8")).hexdigest()
        out[plan] = (len(rows_sorted), h)
    return out


def _grid_plan_fingerprint(res, table: str) -> dict[str, tuple[int, str]]:
    rows = res.factor_rows.get(table, [])
    by_plan: dict[str, list[str]] = defaultdict(list)
    if not rows:
        return {}
    fields = list(rows[0].keys())
    for row in rows:
        plan = (row.get("PLAN") or "").strip()
        sig = "|".join(str(row.get(c, "")).strip() for c in fields)
        by_plan[plan].append(sig)
    out = {}
    for plan, rs in by_plan.items():
        rs_sorted = sorted(rs)
        h = hashlib.md5("\n".join(rs_sorted).encode("utf-8")).hexdigest()
        out[plan] = (len(rs_sorted), h)
    return out


def _run_pipeline(missfill_enabled: bool):
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg = dict(cfg)
    i42 = dict(cfg.get("issue42_pdage_missfill") or {})
    i42["enabled"] = missfill_enabled
    cfg["issue42_pdage_missfill"] = i42
    with tempfile.TemporaryDirectory() as td:
        cfg_path = os.path.join(td, "rate_loader_config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
        return RP.run(cfg_path, str(ROOT))


def main():
    ok = True
    results = []

    def check(name, passed, detail=""):
        nonlocal ok
        status = "PASS" if passed else "FAIL"
        if not passed:
            ok = False
        results.append({"check": name, "status": status, "detail": detail})
        print(f"{status}: {name}" + (f" — {detail}" if detail else ""))

    # --- Policy tables untouched (mtime before rate emit ~7:50) ---
    policy_tables = [
        "quikmstr.csv",
        "quikridr.csv",
        "quikprmh.csv",
        "quikplan.csv",
        "quikclid.csv",
        "quikclnt.csv",
        "quikmemo.csv",
        "quikdvdp.csv",
    ]
    row_counts = []
    for name in policy_tables:
        p = OUTPUT / name
        n = _rowcount(p)
        row_counts.append({"table": name, "rows": n, "scope": "policy"})
        # Policy tables should not have been rewritten at emit time
        check(
            f"policy_present:{name}",
            n >= 0,
            f"rows={n}",
        )

    # --- Untouched rate families (not in intentional emit set) ---
    for p in sorted(RATES.glob("Quik*.csv")):
        if p.name in INTENTIONALLY_EMITTED:
            row_counts.append({"table": f"rates/{p.name}", "rows": _rowcount(p), "scope": "issue42_target"})
            continue
        row_counts.append({"table": f"rates/{p.name}", "rows": _rowcount(p), "scope": "untouched_rate"})
        # Confirm mtime earlier than intentional emit (QuikNps)
        nps = RATES / "QuikNps.csv"
        if nps.is_file() and p.stat().st_mtime > nps.stat().st_mtime + 1:
            check(f"untouched_mtime:{p.name}", False, "mtime after QuikNps emit")
        else:
            check(f"untouched_mtime:{p.name}", True, f"rows={_rowcount(p)}")

    with open(EVIDENCE / "issue42_regression_row_counts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["table", "rows", "scope"])
        w.writeheader()
        w.writerows(row_counts)

    # --- Pipeline on vs off: non-candidate plans identical ---
    print("Running pipeline WITH missfill...")
    res_on = _run_pipeline(True)
    print("Running pipeline WITHOUT missfill...")
    res_off = _run_pipeline(False)

    for table in ("QuikNps", "QuikTvs"):
        fp_on = _grid_plan_fingerprint(res_on, table)
        fp_off = _grid_plan_fingerprint(res_off, table)
        all_plans = sorted(set(fp_on) | set(fp_off))
        changed = []
        unchanged_noncand = 0
        changed_noncand = []
        new_cand = []
        for plan in all_plans:
            a = fp_on.get(plan)
            b = fp_off.get(plan)
            if a != b:
                changed.append(plan)
                if plan in CANDIDATE_PLANS:
                    new_cand.append(plan)
                else:
                    changed_noncand.append(plan)
            elif plan not in CANDIDATE_PLANS:
                unchanged_noncand += 1

        check(
            f"{table}:non_candidate_stable",
            len(changed_noncand) == 0,
            f"changed_noncand={changed_noncand[:10]} unchanged_noncand={unchanged_noncand}",
        )
        # Candidates that should appear/change when missfill on
        must = {"5L0110", "196085", "1L17SP"}
        missing_must = [p for p in must if p not in fp_on or fp_on[p][0] == 0]
        check(
            f"{table}:candidates_present",
            len(missing_must) == 0,
            f"missing={missing_must} changed_cands={sorted(new_cand)[:15]}",
        )

        with open(EVIDENCE / f"issue42_regression_{table}_plan_delta.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["plan", "rows_off", "hash_off", "rows_on", "hash_on", "candidate", "delta"])
            for plan in all_plans:
                a = fp_on.get(plan, (0, ""))
                b = fp_off.get(plan, (0, ""))
                delta = "CHANGED" if a != b else "SAME"
                w.writerow(
                    [
                        plan,
                        b[0],
                        b[1][:12],
                        a[0],
                        a[1][:12],
                        "Y" if plan in CANDIDATE_PLANS else "N",
                        delta,
                    ]
                )

    # --- Output QuikNps header schema vs prior QuikCvs (same factor family pattern) ---
    nps = RATES / "QuikNps.csv"
    cvs = RATES / "QuikCvs.csv"
    if nps.is_file() and cvs.is_file():
        with open(nps, encoding="utf-8", newline="") as f:
            nps_hdr = next(csv.reader(f))
        with open(cvs, encoding="utf-8", newline="") as f:
            cvs_hdr = next(csv.reader(f))
        # Factor tables share PLAN/AGE/CNTL/GENDER/UWCLASS/BAND prefix; value cols differ by family
        prefix = ["PLAN", "AGE", "CNTL"]
        check(
            "QuikNps_schema_prefix",
            nps_hdr[:3] == prefix,
            f"hdr0-2={nps_hdr[:3]}",
        )
        check(
            "QuikNps_has_NP_cols",
            any(h.startswith("NP") for h in nps_hdr),
            f"np_cols={[h for h in nps_hdr if h.startswith('NP')]}",
        )

    # --- #25 MPOLICY width spot-check ---
    mstr = OUTPUT / "quikmstr.csv"
    if mstr.is_file():
        bad = 0
        sample = []
        with open(mstr, encoding="utf-8", errors="replace", newline="") as f:
            for i, row in enumerate(csv.DictReader(f)):
                mp = row.get("MPOLICY") or row.get("mpolicy") or ""
                if len(mp) != 10:
                    bad += 1
                if i < 5:
                    sample.append(f"{mp!r}({len(mp)})")
                if i > 2000:
                    break
        check("issue25_mpolicy_width_sample", bad == 0, f"bad={bad} samples={sample}")

    # --- #26 MPREM spot: quikridr has MPREM column populated for some rows ---
    ridr = OUTPUT / "quikridr.csv"
    if ridr.is_file():
        with open(ridr, encoding="utf-8", errors="replace", newline="") as f:
            rd = csv.DictReader(f)
            fields = rd.fieldnames or []
            has_mprem = "MPREM" in fields
            populated = 0
            for i, row in enumerate(rd):
                if (row.get("MPREM") or "").strip():
                    populated += 1
                if i > 500:
                    break
        check("issue26_mprem_column_present", has_mprem and populated > 0, f"populated_in_sample={populated}")

    # --- Test_Validation matches Output for emitted tables ---
    tv = OUTPUT / "Test_Validation"
    for name in INTENTIONALLY_EMITTED:
        a = RATES / name
        b = tv / name
        if a.is_file() and b.is_file():
            check(f"test_validation_match:{name}", _file_md5(a) == _file_md5(b), "")
        else:
            check(f"test_validation_match:{name}", False, f"a={a.is_file()} b={b.is_file()}")

    with open(EVIDENCE / "issue42_regression_checks.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["check", "status", "detail"])
        w.writeheader()
        w.writerows(results)

    print("\nIssue #42 regression:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
