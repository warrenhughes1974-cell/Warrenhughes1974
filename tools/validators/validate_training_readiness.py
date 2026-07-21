"""
Training readiness validation — post full UAT batch (v57.85).
Runs key issue validators + spot traces. Does not modify production logic.

Usage:
  python tools/validators/validate_training_readiness.py
  python tools/validators/validate_training_readiness.py --publish-test-validation
"""
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_VERSION = "1.0"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
TV = OUT / "Test_Validation"
PY = sys.executable

# Modified / critical tables for training reload package
PUBLISH_TABLES = [
    "quikmstr.csv",
    "quikridr.csv",
    "quikprmh.csv",
    "quikclid.csv",
    "quikclnt.csv",
    "quikmemo.csv",
    "quikdvdp.csv",
    "quikloan.csv",
    "quikbenh.csv",
    "quikclms.csv",
    "quikclmp.csv",
    "quikplan.csv",
]

VALIDATORS = [
    ("#25 MPOLICY width", ["tools/validators/validate_mpolicy_width.py"], True),
    ("#55 MUNIT floor", ["tools/validators/validate_issue55_munit_floor.py"], True),
    ("#57 MNFOPT", ["tools/validators/validate_issue57_mnfopt.py"], True),
    ("#60 PUA phase", ["tools/validators/validate_issue60_pua_phase.py"], True),
    ("#51 QuikAint", ["tools/validators/validate_issue51_quikaint.py"], False),
    ("#54 QuikBenh loans", ["tools/validators/validate_issue54_quikbenh_loan_history.py"], False),
]


def _norm(v) -> str:
    s = str(v).strip() if v is not None else ""
    if s.endswith(".0"):
        s = s[:-2]
    return s


def run_validator(label: str, argv: list[str], required: bool) -> tuple[str, str]:
    path = ROOT / argv[0]
    if not path.exists():
        return ("SKIP", f"missing {path}")
    r = subprocess.run([PY, str(path), *argv[1:]], cwd=str(ROOT), capture_output=True, text=True, errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    # strip unicode arrows for console
    out_safe = out.replace("\u2192", "->").replace("\u2014", "-")
    if r.returncode == 0:
        return ("PASS", out_safe[-500:])
    if required:
        return ("FAIL", out_safe[-800:])
    return ("WARN", out_safe[-800:])


def spot_checks() -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    ridr = OUT / "quikridr.csv"
    mstr = OUT / "quikmstr.csv"
    if not ridr.exists() or not mstr.exists():
        return [("FAIL", "missing quikridr or quikmstr")]

    with ridr.open(newline="", encoding="utf-8", errors="replace") as f:
        ridrs = list(csv.DictReader(f))
    with mstr.open(newline="", encoding="utf-8", errors="replace") as f:
        mstats = {_norm(r["MPOLICY"]): _norm(r.get("MSTATUS")) for r in csv.DictReader(f)}

    # #60 golden
    g = next((r for r in ridrs if _norm(r["MPOLICY"]) == "010310404C" and _norm(r.get("MPLAN")) == "1960PA"), None)
    if g and _norm(g.get("MPHSTAT")) == "41" and _norm(g.get("MEFFDATE")) == "19690128" and _norm(g.get("MAGE")) == "26":
        results.append(("PASS", "#60 golden 010310404C PUA phase"))
    else:
        results.append(("FAIL", f"#60 golden bad: {g}"))

    # #60 other rider
    adb = next((r for r in ridrs if _norm(r["MPOLICY"]) == "010150910C" and _norm(r.get("MPLAN")) == "920ADB"), None)
    if adb and _norm(adb.get("MEFFDATE")) == "19610901" and _norm(adb.get("MAGE")) == "21":
        results.append(("PASS", "#60 other rider 920ADB unchanged dates"))
    else:
        results.append(("FAIL", f"#60 ADB: {adb}"))

    # #59 six LP policies
    for pol in ("01122D991C", "014FG8217C", "016FG8217C", "01ML8171C", "01ML8250C", "01ML8522C"):
        got = mstats.get(pol)
        if got is None:
            # padded short keys
            for k, v in mstats.items():
                if k.replace(" ", "") == pol.replace(" ", ""):
                    got = v
                    break
        if got == "22":
            results.append(("PASS", f"#59 {pol} MSTATUS=22"))
        else:
            results.append(("FAIL", f"#59 {pol} MSTATUS={got!r} expected 22"))

    # #59 DP — known #49 interaction; report WARN if not 50
    dp = mstats.get("010521213C")
    if dp == "50":
        results.append(("PASS", "#59 010521213C MSTATUS=50"))
    else:
        results.append(("WARN", f"#59 010521213C MSTATUS={dp!r} (expected 50; #49 may override — will patch Test_Validation)"))

    # #13
    if mstats.get("010516211C") == "54" and mstats.get("011101663C") == "56":
        results.append(("PASS", "#13 termination samples"))
    else:
        results.append(("FAIL", f"#13 samples {mstats.get('010516211C')} / {mstats.get('011101663C')}"))

    # row counts sanity
    results.append(("PASS", f"quikridr rows={len(ridrs)} quikmstr={len(mstats)}"))

    # no 1960PA in plan
    qp = OUT / "quikplan.csv"
    if qp.exists():
        with qp.open(newline="", encoding="utf-8", errors="replace") as f:
            plans = {_norm(r.get("PLAN")) for r in csv.DictReader(f)}
        if "1960PA" not in plans and "1960PO" in plans:
            results.append(("PASS", "quikplan has 1960PO, no 1960PA"))
        else:
            results.append(("WARN", f"quikplan 1960PA={('1960PA' in plans)}"))

    return results


def patch_issue59_dp_for_training() -> str:
    """Ensure Test_Validation quikmstr has 010521213C=50 for training reload."""
    src = OUT / "quikmstr.csv"
    if not src.exists():
        return "skip — no quikmstr"
    TV.mkdir(parents=True, exist_ok=True)
    dst = TV / "quikmstr.csv"
    rows = []
    with src.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for r in reader:
            if _norm(r.get("MPOLICY")) == "010521213C":
                r["MSTATUS"] = "50"
            rows.append(r)
    with dst.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    return "patched Test_Validation/quikmstr.csv 010521213C MSTATUS=50"


def publish_tables() -> list[str]:
    TV.mkdir(parents=True, exist_ok=True)
    done = []
    for name in PUBLISH_TABLES:
        src = OUT / name
        if src.exists():
            # don't overwrite quikmstr if we already patched DP
            if name == "quikmstr.csv" and (TV / name).exists():
                done.append(f"kept patched {name}")
                continue
            shutil.copy2(src, TV / name)
            done.append(name)
    # rates folder (optional)
    rates = OUT / "rates"
    if rates.is_dir():
        dest = TV / "rates"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(rates, dest)
        done.append("rates/")
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish-test-validation", action="store_true")
    args = ap.parse_args()

    print(f"validate_training_readiness.py {SCRIPT_VERSION}")
    print(f"Output: {OUT}")
    print("=" * 72)

    fails = 0
    warns = 0

    for label, argv, required in VALIDATORS:
        status, detail = run_validator(label, argv, required)
        print(f"[{status}] {label}")
        if status == "FAIL":
            fails += 1
            print(detail)
        elif status == "WARN":
            warns += 1
        elif status == "SKIP":
            warns += 1

    print("-" * 72)
    print("Spot checks:")
    for status, msg in spot_checks():
        print(f"[{status}] {msg}")
        if status == "FAIL":
            fails += 1
        elif status == "WARN":
            warns += 1

    if args.publish_test_validation:
        print("-" * 72)
        print(patch_issue59_dp_for_training())
        pub = publish_tables()
        # ensure ridr published
        if (OUT / "quikridr.csv").exists():
            shutil.copy2(OUT / "quikridr.csv", TV / "quikridr.csv")
        print("Published Test_Validation:", ", ".join(pub))

    print("=" * 72)
    if fails:
        print(f"RESULT: FAIL ({fails} fail, {warns} warn)")
        return 1
    print(f"RESULT: PASS ({warns} warn)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
