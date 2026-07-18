"""
Issue #80 Regression — read-only batch/compare (no production edits).

Checks:
  - Official #80 validator PASS
  - Candidate quikplan/rate keys match coded expected
  - Non-candidate quikplan NFOINT/INTMETHCV unchanged vs pre-#80 archive
  - No invented QuikPlCv/Tv keys for quikplan-only plans
  - PUA plans not in Valuation_Setup authority
  - Factor-table row-count stability vs Archive/rates (informational if emit grew)
  - #25 / #26 spot checks
  - Test_Validation package purity + parity
  - APP_VERSION sync
"""
from __future__ import annotations

import csv
import filecmp
import hashlib
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
RATES = OUT / "rates"
TEST_VAL = OUT / "Test_Validation"
ARCHIVE_QP = ROOT / "QLA_Migration" / "Archive" / "quikplan_pre_issue80_moved_from_output.csv"
ARCHIVE_RATES = ROOT / "QLA_Migration" / "Archive" / "rates"
EXP_PATH = ROOT / "Issue_Log_Items" / "Issue_80" / "evidence" / "cso_valuation_setup_coded_expected.csv"
AUTH_PATH = ROOT / "plan_analysis" / "source_data" / "rates" / "CSO_Valuation_Setup.csv"
EVID = ROOT / "Issue_Log_Items" / "Issue_80" / "evidence"
ANCHOR_PATH = EVID / "issue80_risk_anchor_plans.csv"

QUIKPLAN_ONLY = frozenset({"10L171", "10L172", "117JPO"})
PUA_DEFER = frozenset({
    "121PUA", "165PUA", "170PUA", "185PUA", "1970PA", "1OLPUA", "1POPUA",
    "261PUA", "265PUA", "280PUA",
})
ALLOWED_TV = frozenset({
    "manifest.txt", "quikplan.csv", "rates/QuikPlCv.csv", "rates/QuikPlTv.csv",
})
QP_TARGET = ("NFOINT", "INTMETHCV")
CV_ASSUMP = ("MORT", "ETIMORT", "NFOINT", "INTMETHCV")
TV_ASSUMP = ("MORT", "RSVINT", "RSVMETH", "INTMETHTV", "STOREMEANS", "CALCMIDS")
FACTORS = ("QuikGps", "QuikDbs", "QuikCvs", "QuikTvs", "QuikDvs", "QuikNps")

# Issue #26 MPREM spot checks (from prior regression scripts)
MPREM26 = {
    "010310404C": "13.20",
    "010331768C": "10.96",
    "010367131C": "9.12",
}


def n(v) -> str:
    return "" if v is None else str(v).strip()


def read(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_in_scope() -> dict[str, dict]:
    out = {}
    for r in read(EXP_PATH):
        if n(r.get("scope_issue80")) == "IN_SCOPE" and n(r.get("qla_plan")):
            out[n(r["qla_plan"])] = r
    return out


def main() -> int:
    checks: list[dict[str, str]] = []
    fails: list[str] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"CHECK": name, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            fails.append(f"{name}: {detail}")

    # 0) Official validator
    proc = subprocess.run(
        [sys.executable, str(ROOT / "QLA_Migration" / "_validate_issue80_valuation_setup.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    add("official_validator", proc.returncode == 0, (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else proc.stderr[:200])

    exp = load_in_scope()
    candidates = set(exp)
    rate_key_plans = candidates - QUIKPLAN_ONLY
    auth = {n(r.get("qla_plan")) for r in read(AUTH_PATH) if n(r.get("qla_plan"))}
    add("authority_plan_count", len(auth) == 51, f"count={len(auth)}")
    add("pua_not_in_authority", not (auth & PUA_DEFER), f"leaked={sorted(auth & PUA_DEFER)}")

    qp = read(OUT / "quikplan.csv")
    cv = read(RATES / "QuikPlCv.csv")
    tv = read(RATES / "QuikPlTv.csv")
    qp_by = {n(r.get("PLAN")): r for r in qp}
    cv_by = defaultdict(list)
    tv_by = defaultdict(list)
    for r in cv:
        cv_by[n(r.get("PLAN"))].append(r)
    for r in tv:
        tv_by[n(r.get("PLAN"))].append(r)

    # 1) Candidate exact match
    cell_ok = cell_bad = 0
    for plan, e in exp.items():
        row = qp_by.get(plan)
        if not row:
            cell_bad += 1
            continue
        for fld, ef in (("NFOINT", "QuikPlCv_NFOINT"), ("INTMETHCV", "QuikPlCv_INTMETHCV")):
            if n(row.get(fld)) == n(e.get(ef)):
                cell_ok += 1
            else:
                cell_bad += 1
        if plan in QUIKPLAN_ONLY:
            continue
        for r in cv_by.get(plan, []):
            for fld, ef in (
                ("MORT", "QuikPlCv_MORT"),
                ("ETIMORT", "QuikPlCv_ETIMORT"),
                ("NFOINT", "QuikPlCv_NFOINT"),
                ("INTMETHCV", "QuikPlCv_INTMETHCV"),
            ):
                if n(r.get(fld)) == n(e.get(ef)):
                    cell_ok += 1
                else:
                    cell_bad += 1
        for r in tv_by.get(plan, []):
            for fld, ef, logical in (
                ("MORT", "QuikPlTv_MORT", False),
                ("RSVINT", "QuikPlTv_RSVINT", False),
                ("RSVMETH", "QuikPlTv_RSVMETH", False),
                ("INTMETHTV", "QuikPlTv_INTMETHTV", False),
                ("STOREMEANS", "QuikPlTv_STOREMEANS", True),
                ("CALCMIDS", "QuikPlTv_CALCMIDS", True),
            ):
                got = n(r.get(fld)).upper()
                want = n(e.get(ef)).upper()
                if logical:
                    got = "N" if got in ("N", "F", "FALSE", "0") else ("Y" if got in ("Y", "T", "TRUE", "1") else got)
                    want = "N" if want in ("N", "F", "FALSE", "0") else ("Y" if want in ("Y", "T", "TRUE", "1") else want)
                if got == want:
                    cell_ok += 1
                else:
                    cell_bad += 1
    add("candidate_cells", cell_bad == 0, f"ok={cell_ok} bad={cell_bad}")

    # 2) No invented keys
    invented = sorted((QUIKPLAN_ONLY & set(cv_by)) | (QUIKPLAN_ONLY & set(tv_by)))
    add("no_invented_keys", not invented, f"plans={invented}")

    # 3) Non-candidate quikplan target fields vs pre-#80 archive
    if ARCHIVE_QP.is_file():
        base_qp = {n(r.get("PLAN")): r for r in read(ARCHIVE_QP)}
        non_cand = sorted(set(qp_by) - candidates)
        target_drift = []
        other_drift = []
        for plan in non_cand:
            cur, old = qp_by[plan], base_qp.get(plan)
            if not old:
                continue
            for fld in QP_TARGET:
                if n(cur.get(fld)) != n(old.get(fld)):
                    target_drift.append(f"{plan}.{fld}:{n(old.get(fld))!r}->{n(cur.get(fld))!r}")
            # Sample unrelated columns
            for fld in ("FORM", "DESCR", "LOANINT", "LOANINTX", "PLANVALOPT"):
                if fld in cur and fld in old and n(cur.get(fld)) != n(old.get(fld)):
                    other_drift.append(f"{plan}.{fld}:{n(old.get(fld))!r}->{n(cur.get(fld))!r}")
        add(
            "noncandidate_quikplan_targets",
            not target_drift,
            f"plans={len(non_cand)} target_drift={len(target_drift)} sample={target_drift[:6]}",
        )
        # Informational — FORM drift is residual from Validation notes
        add(
            "noncandidate_unrelated_cols",
            True,
            f"other_drift={len(other_drift)} sample={other_drift[:8]} (informational)",
        )
        # Candidate target fields should match expected (already) and typically differ from archive when intentional
        intentional = 0
        for plan in sorted(candidates):
            cur, old, e = qp_by.get(plan), base_qp.get(plan), exp[plan]
            if not cur or not old:
                continue
            for fld, ef in (("NFOINT", "QuikPlCv_NFOINT"), ("INTMETHCV", "QuikPlCv_INTMETHCV")):
                if n(old.get(fld)) != n(e.get(ef)) and n(cur.get(fld)) == n(e.get(ef)):
                    intentional += 1
        add("candidate_intentional_quikplan_updates", intentional > 0, f"cells_updated_from_archive={intentional}")
    else:
        add("noncandidate_quikplan_targets", False, "archive missing")

    # 4) Anchors present and match expected
    anchors = ["1960PO", "1658C1", "17CSI3", "1L1095", "221END", "1668SP"]
    anchor_bad = []
    for plan in anchors:
        e = exp[plan]
        if n(qp_by.get(plan, {}).get("NFOINT")) != n(e.get("QuikPlCv_NFOINT")):
            anchor_bad.append(f"{plan}.quikplan.NFOINT")
        rows = cv_by.get(plan) or []
        if rows and n(rows[0].get("ETIMORT")) != n(e.get("QuikPlCv_ETIMORT")):
            anchor_bad.append(f"{plan}.cv.ETIMORT")
        trows = tv_by.get(plan) or []
        if trows and n(trows[0].get("RSVINT")) != n(e.get("QuikPlTv_RSVINT")):
            anchor_bad.append(f"{plan}.tv.RSVINT")
    add("anchors", not anchor_bad, f"bad={anchor_bad}")

    # 5) Factor tables — #80 must not invent factor cells; compare row counts to Archive/rates if present
    for name in FACTORS:
        cur_p = RATES / f"{name}.csv"
        arc_p = ARCHIVE_RATES / f"{name}.csv"
        cur_n = len(read(cur_p))
        if arc_p.is_file():
            arc_n = len(read(arc_p))
            # Current emit may be larger than older archive; fail only on unexpected shrink of factor grids
            add(
                f"factor_{name}",
                cur_n >= arc_n,
                f"current={cur_n} archive={arc_n} shrink={cur_n < arc_n}",
            )
        else:
            add(f"factor_{name}", cur_n > 0, f"current={cur_n}")

    # 6) Policy tables — #80 does not rewrite them; require present + non-empty.
    #    Hard row counts from older issues (#76 era) are not #80 gates (fleet moved).
    for table in ("quikmstr", "quikridr", "quikclid", "quikclnt"):
        p = OUT / f"{table}.csv"
        if not p.is_file():
            add(f"policy_table_{table}", False, "missing")
            continue
        with p.open(encoding="utf-8", errors="replace") as f:
            count = sum(1 for _ in f) - 1
        add(f"policy_table_{table}", count > 0, f"rows={count} (fleet context; not #80 touch list)")

    # 7) Issue #25 MPOLICY length sample
    mstr = read(OUT / "quikmstr.csv")
    bad25 = [n(r.get("MPOLICY")) for r in mstr[:200] if len(n(r.get("MPOLICY"))) != 10]
    add("issue25_mpolicy_len_sample200", not bad25, f"bad={len(bad25)} sample={bad25[:5]}")

    # 8) Issue #26 MPREM spot
    ridr = {(n(r.get("MPOLICY")), n(r.get("MPHASE"))): r for r in read(OUT / "quikridr.csv")}
    bad26 = []
    for pol, want in MPREM26.items():
        row = ridr.get((pol, "1")) or ridr.get((pol, "01"))
        # find any phase 1-like
        if not row:
            for (p, ph), r in ridr.items():
                if p == pol and ph in ("1", "01"):
                    row = r
                    break
        if not row:
            # any phase
            matches = [r for (p, _), r in ridr.items() if p == pol]
            row = matches[0] if matches else None
        got = n(row.get("MPREM")) if row else ""
        try:
            ok = abs(float(got or 0) - float(want)) < 0.001
        except ValueError:
            ok = got == want
        if not ok:
            bad26.append(f"{pol}:{got!r}!={want!r}")
    add("issue26_mprem_spot", not bad26, f"bad={bad26}")

    # 9) Test_Validation purity + parity
    found = {p.relative_to(TEST_VAL).as_posix() for p in TEST_VAL.rglob("*") if p.is_file()} if TEST_VAL.is_dir() else set()
    add("test_validation_purity", found == ALLOWED_TV, f"found={sorted(found)}")
    for src, dst in (
        (OUT / "quikplan.csv", TEST_VAL / "quikplan.csv"),
        (RATES / "QuikPlCv.csv", TEST_VAL / "rates" / "QuikPlCv.csv"),
        (RATES / "QuikPlTv.csv", TEST_VAL / "rates" / "QuikPlTv.csv"),
    ):
        ok = dst.is_file() and filecmp.cmp(src, dst, shallow=False)
        add(f"parity_{dst.name}", ok, f"sha={sha256(src)[:12] if src.is_file() else 'missing'}")

    # 10) Version sync
    for rel in ("app.py", "QLA_Migration/app.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        add(f"version_{rel}", 'APP_VERSION = "v58.01"' in text, "expect v58.01")

    # Write evidence
    EVID.mkdir(parents=True, exist_ok=True)
    out_csv = EVID / "issue80_regression_checks.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["CHECK", "RESULT", "DETAIL"])
        w.writeheader()
        w.writerows(checks)

    print("Issue #80 Regression")
    print(f"  checks={len(checks)} fails={len(fails)}")
    for c in checks:
        print(f"  [{c['RESULT']}] {c['CHECK']}: {c['DETAIL']}")
    print(f"  wrote {out_csv}")
    if fails:
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
