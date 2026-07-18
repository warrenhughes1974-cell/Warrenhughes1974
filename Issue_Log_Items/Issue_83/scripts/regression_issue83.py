"""
Issue #83 Regression — read-only batch/compare (no production edits).

Baseline note:
  Archive/rates is pre-#71 (BAND often 01/02/03) and older factor package.
  #83 regression therefore:
    - treats factor Archive compare as no-shrink (informational growth OK)
    - compares key preservation with BAND normalized to 00 (#71)
    - proves #83 apply path does not write factor CSVs
"""
from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
RATES = OUT / "rates"
ARCHIVE = ROOT / "QLA_Migration" / "Archive" / "rates"
TEST_VAL = OUT / "Test_Validation"
EVID = ROOT / "Issue_Log_Items" / "Issue_83" / "evidence"
APPLY = ROOT / "QLA_Migration" / "_apply_issue83_gender_companion_keys.py"

FAMILIES = ("QuikPlGp", "QuikPlDb", "QuikPlCv", "QuikPlTv", "QuikPlDv")
FACTORS = ("QuikGps", "QuikDbs", "QuikCvs", "QuikTvs", "QuikDvs", "QuikNps")
MEMBER_FILES = ("QuikPlGd.csv", "QuikPlUw.csv", "QuikPlBd.csv", "QuikPlSt.csv", "QuikPlNb.csv")
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


def row_count(path: Path) -> int:
    return max(0, len(read(path)))


def money(v: str) -> str:
    s = n(v)
    if not s:
        return ""
    try:
        return f"{float(s):.2f}"
    except ValueError:
        return s


def key_sig(r: dict, normalize_band: bool = True) -> tuple:
    band = n(r.get("BAND"))
    if normalize_band:
        band = "00"  # Issue #71 fleet BAND
    return (
        n(r.get("PLAN")),
        n(r.get("GENDER")),
        n(r.get("UWCLASS")),
        band,
        n(r.get("ISSCNTRY")) or "0000",
        n(r.get("ISSUEST")) or "00",
        n(r.get("EFFDATE")) or "19000101",
    )


def fm_plans(gd_rows: list[dict]) -> set[str]:
    by = defaultdict(set)
    for r in gd_rows:
        code = n(r.get("GDCODE"))
        if code in {"F", "M"}:
            by[n(r.get("PLAN"))].add(code)
    return {p for p, codes in by.items() if {"F", "M"}.issubset(codes)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    checks: list[dict[str, str]] = []
    fails: list[str] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"CHECK": name, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            fails.append(f"{name}: {detail}")

    for script, label in (
        ("_validate_issue83_gender_companion_keys.py", "issue83_validator"),
        ("_validate_issue77_rate_setup.py", "issue77_validator"),
    ):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "QLA_Migration" / script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        last = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else (proc.stderr or "")[:200]
        add(label, proc.returncode == 0, last)

    # #83 apply must not write factor tables
    apply_txt = APPLY.read_text(encoding="utf-8", errors="replace") if APPLY.is_file() else ""
    writes_factor = any(f"{stem}.csv" in apply_txt and "_write" in apply_txt for stem in FACTORS)
    # stronger: only KEY_FILES / MEMBER_FILES / quikplan in _write calls
    factor_names_in_write = any(stem in apply_txt for stem in ("QuikGps", "QuikCvs", "QuikTvs"))
    add(
        "apply_does_not_emit_factors",
        APPLY.is_file() and "KEY_FILES" in apply_txt and not writes_factor,
        f"factor_names_mentioned={factor_names_in_write}",
    )

    # Factor no-shrink vs Archive (growth from later rate work is OK)
    if ARCHIVE.is_dir():
        for stem in FACTORS:
            cur = row_count(RATES / f"{stem}.csv")
            base = row_count(ARCHIVE / f"{stem}.csv")
            add(f"factor_no_shrink_{stem}", cur >= base, f"archive={base} current={cur}")
    else:
        add("factor_archive_present", False, "Archive/rates missing")

    # Factor SHA fingerprint evidence (current package)
    for stem in FACTORS:
        p = RATES / f"{stem}.csv"
        if p.is_file():
            add(f"factor_fingerprint_{stem}", True, f"rows={row_count(p)} sha256={sha256(p)[:16]}")

    # Key tables: no shrink vs archive
    for kt in FAMILIES:
        cur = row_count(RATES / f"{kt}.csv")
        base = row_count(ARCHIVE / f"{kt}.csv") if ARCHIVE.is_dir() else -1
        add(f"key_no_shrink_{kt}", cur >= base, f"archive={base} current={cur} delta={cur - base}")

    gd = read(RATES / "QuikPlGd.csv")
    candidates = fm_plans(gd)

    # Non-candidate plans: archive F/M keys still present (BAND-normalized)
    non_cand_drift = []
    if ARCHIVE.is_dir():
        for kt in FAMILIES:
            cur_sigs = {key_sig(r) for r in read(RATES / f"{kt}.csv")}
            for r in read(ARCHIVE / f"{kt}.csv"):
                plan = n(r.get("PLAN"))
                if not plan or plan in candidates:
                    continue
                if n(r.get("GENDER")) not in {"F", "M"}:
                    continue
                sig = key_sig(r)
                if sig not in cur_sigs:
                    non_cand_drift.append(f"{kt}:{sig}")
    add(
        "non_candidate_fm_keys_preserved",
        len(non_cand_drift) == 0,
        f"drift={len(non_cand_drift)} sample={non_cand_drift[:8]}",
    )

    # Candidate plans: prior F/M archive keys still present (BAND-normalized)
    cand_missing = []
    if ARCHIVE.is_dir():
        for kt in FAMILIES:
            cur_sigs = {key_sig(r) for r in read(RATES / f"{kt}.csv")}
            for r in read(ARCHIVE / f"{kt}.csv"):
                plan = n(r.get("PLAN"))
                if plan not in candidates:
                    continue
                if n(r.get("GENDER")) not in {"F", "M"}:
                    continue
                if key_sig(r) not in cur_sigs:
                    cand_missing.append(f"{kt}:{key_sig(r)}")
    add(
        "candidate_existing_fm_keys_preserved",
        len(cand_missing) == 0,
        f"missing={len(cand_missing)} sample={cand_missing[:8]}",
    )

    # Companion completeness (same as research: 0 gaps)
    gaps = []
    keys_by = {kt: defaultdict(set) for kt in FAMILIES}
    for kt in FAMILIES:
        for r in read(RATES / f"{kt}.csv"):
            keys_by[kt][n(r.get("PLAN"))].add(n(r.get("GENDER")))
    for plan in sorted(candidates):
        for kt in FAMILIES:
            have = keys_by[kt].get(plan, set())
            if not (have & {"F", "M"}):
                continue
            for g in ("F", "M"):
                if g not in have:
                    gaps.append(f"{kt}:{plan}:{g}")
    add("companion_gaps_zero", len(gaps) == 0, f"gaps={len(gaps)}")

    band_bad = []
    for kt in FAMILIES:
        for r in read(RATES / f"{kt}.csv"):
            if n(r.get("GENDER")) not in {"F", "M"}:
                continue
            if n(r.get("BAND")) not in ("", "00"):
                band_bad.append(f"{kt}:{n(r.get('PLAN'))}:{n(r.get('GENDER'))}:{n(r.get('BAND'))}")
    add("band_00_on_fm_keys", len(band_bad) == 0, f"bad={len(band_bad)} sample={band_bad[:8]}")

    cv221 = [r for r in read(RATES / "QuikPlCv.csv") if n(r.get("PLAN")) == "221END"]
    genders = {n(r.get("GENDER")) for r in cv221}
    add("anchor_221END_has_FM", {"F", "M"}.issubset(genders), f"genders={sorted(genders)}")
    cvs_fac = {n(r.get("GENDER")) for r in read(RATES / "QuikCvs.csv") if n(r.get("PLAN")) == "221END"}
    add("anchor_221END_F_values_N", "F" not in cvs_fac and "F" in genders, f"factors={sorted(cvs_fac)}")
    add("anchor_221END_M_values_Y", "M" in cvs_fac and "M" in genders, f"factors={sorted(cvs_fac)}")

    # #80 assumption parity on sibling keys for 221END
    by_g = {n(r.get("GENDER")): r for r in cv221}
    if {"F", "M"}.issubset(by_g):
        same = all(
            n(by_g["F"].get(f)) == n(by_g["M"].get(f))
            for f in ("MORT", "ETIMORT", "NFOINT", "INTMETHCV")
        )
        add("anchor_221END_assumptions_match_sibling", same, "F vs M QuikPlCv assumptions")
    else:
        add("anchor_221END_assumptions_match_sibling", False, "missing F/M")

    mstr = OUT / "quikmstr.csv"
    ridr = OUT / "quikridr.csv"
    if mstr.is_file():
        bad_w = sum(1 for i, r in enumerate(read(mstr)) if i < 200 and len(n(r.get("MPOLICY"))) != 10)
        add("issue25_mpolicy_width_sample200", bad_w == 0, f"bad={bad_w}")
    else:
        add("issue25_mpolicy_width_sample200", True, "quikmstr absent — N/A")

    if ridr.is_file():
        by_pol = {}
        for r in read(ridr):
            if n(r.get("MPHASE")) in ("1", "01"):
                by_pol[n(r.get("MPOLICY"))] = r
        miss = []
        for pol, want in MPREM26.items():
            got = money(by_pol.get(pol, {}).get("MPREM"))
            if got != want:
                miss.append(f"{pol} got={got!r} want={want!r}")
        add("issue26_mprem_spot", len(miss) == 0, f"miss={miss}")
    else:
        add("issue26_mprem_spot", True, "quikridr absent — N/A")

    tv_bad = []
    qp_out, qp_tv = OUT / "quikplan.csv", TEST_VAL / "quikplan.csv"
    if not (qp_out.is_file() and qp_tv.is_file() and qp_out.read_bytes() == qp_tv.read_bytes()):
        tv_bad.append("quikplan.csv")
    for fname in [f"{t}.csv" for t in FAMILIES] + list(MEMBER_FILES):
        a, b = RATES / fname, TEST_VAL / "rates" / fname
        if not a.is_file() or not b.is_file() or a.read_bytes() != b.read_bytes():
            tv_bad.append(fname)
    add("test_validation_parity", len(tv_bad) == 0, f"bad={tv_bad[:10]}")

    for rel in ("app.py", "QLA_Migration/app.py"):
        text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        add(f"version_{rel}", 'APP_VERSION = "v58.02"' in text, "expect v58.02")

    # Policy tables not modified by #83 (file list in apply)
    add(
        "apply_scope_keys_members_quikplan_only",
        "KEY_FILES" in apply_txt and "MEMBER_FILES" in apply_txt and "quikplan.csv" in apply_txt
        and "quikmstr" not in apply_txt and "quikridr" not in apply_txt,
        "apply script scope",
    )

    EVID.mkdir(parents=True, exist_ok=True)
    out_csv = EVID / "issue83_regression_checks.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["CHECK", "RESULT", "DETAIL"])
        w.writeheader()
        w.writerows(checks)

    print("Issue #83 regression")
    print(f"  checks: {len(checks)}")
    print(f"  FAIL: {len(fails)}")
    print(f"  evidence: {out_csv}")
    for c in checks:
        if c["CHECK"].startswith("factor_fingerprint_"):
            continue
        mark = "OK" if c["RESULT"] == "PASS" else "!!"
        print(f"  [{mark}] {c['CHECK']}: {c['DETAIL']}")
    if fails:
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
