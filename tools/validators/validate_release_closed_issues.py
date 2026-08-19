"""
Release gate — prove Closed issue fixes are present in the Output about to be handed off.

Usage:
  python tools/validators/validate_release_closed_issues.py
  python tools/validators/validate_release_closed_issues.py --smoke-only
  python tools/validators/validate_release_closed_issues.py --json QLA_Migration/Reports/release_gate.json

Exit codes:
  0 = RELEASE_OK
  1 = RELEASE_BLOCKED (identity, package, smoke, or accountability GAP)

This is the automated counterpart to:
  Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
RATES = OUT / "rates"
SOURCE = ROOT / "QLA_Migration" / "Source"
REPORTS = ROOT / "QLA_Migration" / "Reports"
PY = sys.executable
SCRIPT_VERSION = "1.8"  # v1.8: #139 ISWL fee withhold always-on smoke (Warren 2026-08-19)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# High-risk smokes from Completed_Issues_Release_Validation_Guide.md
# (label, argv relative to ROOT, required)
SMOKE_JOBS: list[tuple[str, list[str], bool]] = [
    ("#106 QuikTvs duration", ["Issue_Log_Items/Issue_106/validate_issue106_quiktvs_duration.py"], True),
    (
        "L14 QuikCvs duration",
        ["Issue_Log_Items/Issue_L14/validate_issue_l14_quikcvs_duration.py"],
        True,
    ),
    ("#2 MPOLICY width-11", ["QLA_Migration/_validate_issue2_mpolicy.py"], True),
    ("#59 MSTATUS allowlist", ["tools/validators/validate_issue59_mstatus.py"], True),
    ("#135 Claims CSO", ["Issue_Log_Items/Issue_135/tools/_validate_issue135_production.py"], True),
    ("#136 PVO flags", ["tools/validators/validate_issue136_pvo_flags.py"], True),
    (
        "#21F CONV_ADJ (incl ISWL)",
        ["tools/validators/validate_issue21f_premium_adjustment.py"],
        True,
    ),
    (
        "quikclnt high-water EOF",
        ["tools/validators/validate_quikclnt_highwater.py"],
        True,
    ),
    (
        "CLNT-RJ client-ID width-12",
        ["tools/validators/validate_client_id_width12.py"],
        True,
    ),
    (
        "A7 VARGP/VARDB vs rate grids",
        ["tools/validators/validate_issueA7_variation_codes.py"],
        True,
    ),
    (
        "#138 QuikGps age vs LifePRO premium",
        ["tools/validators/validate_issue138_rate_age_alignment.py"],
        True,
    ),
    (
        "#140 attained-age storage axis",
        ["tools/validators/validate_issue140_attained_age_axis.py"],
        True,
    ),
    (
        "#95 QuikUint / PDINTTBL",
        ["tools/validators/validate_issue95_quikuint_pdinttbl.py"],
        True,
    ),
    (
        "#143 BF RPU MUNIT",
        ["tools/validators/validate_issue143_smoke.py"],
        True,
    ),
    (
        "#141 quikspec RESRVCAT",
        ["QLA_Migration/_validate_issue141_resrvcat.py"],
        True,
    ),
    (
        "#75/#45 PAC Bank Acct",
        ["tools/validators/validate_issue75_mbankno.py"],
        True,
    ),
    (
        "#139 ISWL policy fees withheld",
        ["tools/validators/validate_issue139_policy_fee_suppression.py"],
        True,
    ),
]


def _run(label: str, argv: list[str], required: bool = True) -> dict:
    path = ROOT / argv[0]
    if not path.exists():
        return {
            "id": label,
            "status": "SKIP" if not required else "FAIL",
            "detail": f"missing script {argv[0]}",
            "exit": 127,
        }
    r = subprocess.run(
        [PY, str(path), *argv[1:]],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        errors="replace",
    )
    out = ((r.stdout or "") + (r.stderr or "")).replace("\u2192", "->").replace("\u2014", "-")
    tail = out[-800:].strip().replace("\n", " | ")
    if r.returncode == 0:
        return {"id": label, "status": "PASS", "detail": "validator PASS", "exit": 0}
    status = "FAIL" if required else "WARN"
    return {"id": label, "status": status, "detail": tail or f"exit {r.returncode}", "exit": r.returncode}


def check_identity() -> list[dict]:
    rows: list[dict] = []

    # git commit
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            errors="replace",
        )
        commit = (r.stdout or "").strip() if r.returncode == 0 else ""
    except Exception as exc:  # noqa: BLE001
        commit = ""
        rows.append({"id": "git", "status": "WARN", "detail": f"git unavailable: {exc}"})
    if commit:
        rows.append({"id": "git", "status": "PASS", "detail": f"HEAD={commit}"})
    else:
        rows.append({"id": "git", "status": "WARN", "detail": "could not resolve HEAD"})

    # dirty tree (informational — Output is gitignored so dirty may be normal)
    try:
        r = subprocess.run(
            ["git", "status", "-sb"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            errors="replace",
        )
        branch_line = (r.stdout or "").splitlines()[0] if r.stdout else ""
        rows.append({"id": "git-status", "status": "PASS", "detail": branch_line[:200]})
    except Exception:
        pass

    # APP_VERSION
    app_version = "?"
    try:
        import app as app_mod  # type: ignore

        app_version = str(getattr(app_mod, "APP_VERSION", "?"))
        rows.append({"id": "APP_VERSION", "status": "PASS", "detail": app_version})
    except Exception as exc:  # noqa: BLE001
        rows.append({"id": "APP_VERSION", "status": "FAIL", "detail": f"cannot import app.py: {exc}"})

    # valuation date
    try:
        from qla_core.valuation_date import apply_valuation_date_env

        vdate, vsrc = apply_valuation_date_env(SOURCE)
        env_date = os.environ.get("QLA_VALUATION_DATE", "")
        detail = f"resolved={vdate} src={vsrc} env={env_date or '(unset)'}"
        rows.append({"id": "QLA_VALUATION_DATE", "status": "PASS", "detail": detail})
    except Exception as exc:  # noqa: BLE001
        rows.append(
            {
                "id": "QLA_VALUATION_DATE",
                "status": "FAIL",
                "detail": f"unresolved: {exc}",
            }
        )

    return rows


def check_package() -> list[dict]:
    rows: list[dict] = []
    if not OUT.is_dir():
        return [{"id": "Output/", "status": "FAIL", "detail": f"missing {OUT}"}]

    quik = sorted(OUT.glob("quik*.csv"))
    if len(quik) < 5:
        rows.append(
            {
                "id": "Output/quik*.csv",
                "status": "FAIL",
                "detail": f"only {len(quik)} quik*.csv files — full batch required",
            }
        )
    else:
        rows.append(
            {
                "id": "Output/quik*.csv",
                "status": "PASS",
                "detail": f"{len(quik)} table CSVs present",
            }
        )

    if not RATES.is_dir():
        rows.append(
            {
                "id": "Output/rates/",
                "status": "FAIL",
                "detail": "rates/ missing — rate regenerate required for release",
            }
        )
    else:
        rate_csvs = list(RATES.glob("Quik*.csv")) + list(RATES.glob("quik*.csv"))
        must = ["QuikTvs.csv", "QuikCvs.csv", "QuikUwpo.csv"]
        missing = [m for m in must if not (RATES / m).is_file()]
        if missing:
            rows.append(
                {
                    "id": "Output/rates/",
                    "status": "FAIL",
                    "detail": f"missing required rate files: {', '.join(missing)}",
                }
            )
        elif len(rate_csvs) < 10:
            rows.append(
                {
                    "id": "Output/rates/",
                    "status": "FAIL",
                    "detail": f"only {len(rate_csvs)} rate CSVs — looks incomplete",
                }
            )
        else:
            # mtime freshness hint (warn only)
            tvs = RATES / "QuikTvs.csv"
            mtime = datetime.fromtimestamp(tvs.stat().st_mtime).isoformat(timespec="seconds")
            rows.append(
                {
                    "id": "Output/rates/",
                    "status": "PASS",
                    "detail": f"{len(rate_csvs)} rate CSVs; QuikTvs mtime={mtime}",
                }
            )

    tv = OUT / "Test_Validation"
    if tv.is_dir():
        rows.append(
            {
                "id": "handoff-reminder",
                "status": "PASS",
                "detail": "Test_Validation/ exists - do NOT hand off TV alone; release = full Output",
            }
        )
    return rows


def smoke_issue71_band() -> dict:
    """#71 — rate BAND / BDCODE should be 00."""
    samples = [
        RATES / "QuikCvs.csv",
        RATES / "QuikTvs.csv",
        RATES / "QuikGps.csv",
        RATES / "QuikPlBd.csv",
    ]
    bad = 0
    checked = 0
    examples: list[str] = []
    for path in samples:
        if not path.is_file():
            continue
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames or []
            band_cols = [c for c in fields if c.upper() in ("BAND", "BDCODE", "MBAND")]
            if not band_cols:
                continue
            for i, row in enumerate(reader):
                if i >= 5000:  # sample head for speed
                    break
                for col in band_cols:
                    checked += 1
                    val = (row.get(col) or "").strip()
                    if val and val not in ("00", "0"):
                        bad += 1
                        if len(examples) < 5:
                            plan = (row.get("PLAN") or row.get("MPLAN") or "").strip()
                            examples.append(f"{path.name}:{plan}:{col}={val}")
    if checked == 0:
        return {
            "id": "#71 BAND=00",
            "status": "FAIL",
            "detail": "no BAND/BDCODE columns found in rate samples",
        }
    if bad:
        return {
            "id": "#71 BAND=00",
            "status": "FAIL",
            "detail": f"{bad} non-00 band values in sample; e.g. {'; '.join(examples)}",
        }
    return {
        "id": "#71 BAND=00",
        "status": "PASS",
        "detail": f"sampled {checked} band cells — all 00",
    }


def smoke_issue98_cvs() -> dict:
    """#98 — 17085M M/14: dur3=.06, terminal 1000."""
    path = RATES / "QuikCvs.csv"
    if not path.is_file():
        return {"id": "#98 QuikCvs endpoint", "status": "FAIL", "detail": "missing QuikCvs.csv"}

    vals: dict[int, str] = {}
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            if (r.get("PLAN") or "").strip() != "17085M":
                continue
            if (r.get("GENDER") or "").strip() != "M":
                continue
            if (r.get("AGE") or "").strip().lstrip("0") != "14" and (r.get("AGE") or "").strip() != "14":
                continue
            try:
                cntl = int((r.get("CNTL") or "0").strip() or "0")
            except ValueError:
                continue
            for i in range(10):
                v = (r.get(f"CV{i}") or "").strip()
                if v:
                    vals[cntl * 10 + i] = v

    if not vals:
        return {
            "id": "#98 QuikCvs endpoint",
            "status": "FAIL",
            "detail": "no 17085M M/14 QuikCvs rows",
        }

    fails = []
    d3 = vals.get(3)
    if d3 is None or abs(float(d3) - 0.06) > 0.001:
        fails.append(f"Dur3 got {d3!r} expected 0.06")
    # age-100 terminal around dur 86 for issue age 14
    terminal_ok = any(abs(float(v) - 1000.0) < 0.01 for v in vals.values())
    if not terminal_ok:
        fails.append("no 1000 terminal found on 17085M M/14 slice")
    if fails:
        return {"id": "#98 QuikCvs endpoint", "status": "FAIL", "detail": "; ".join(fails)}
    return {
        "id": "#98 QuikCvs endpoint",
        "status": "PASS",
        "detail": f"Dur3={d3}; terminal 1000 present ({len(vals)} duration cells)",
    }


def run_accountability() -> list[dict]:
    script = ROOT / "tools" / "validators" / "validate_issue_log_accountability.py"
    if not script.is_file():
        return [{"id": "accountability", "status": "FAIL", "detail": "missing accountability script"}]

    json_out = REPORTS / "release_gate_accountability.json"
    REPORTS.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [PY, str(script), "--json", str(json_out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        errors="replace",
    )
    out = ((r.stdout or "") + (r.stderr or "")).replace("\n", " | ")
    gaps = 0
    if json_out.is_file():
        try:
            data = json.loads(json_out.read_text(encoding="utf-8"))
            gaps = int(data.get("counts", {}).get("GAP", 0) or 0)
        except Exception:
            gaps = -1

    if r.returncode == 0 and gaps == 0:
        return [
            {
                "id": "accountability",
                "status": "PASS",
                "detail": f"no GAPs; report {json_out.name}",
            }
        ]
    if gaps > 0:
        return [
            {
                "id": "accountability",
                "status": "FAIL",
                "detail": f"{gaps} GAP(s) — see {json_out}; release blocked",
            }
        ]
    return [
        {
            "id": "accountability",
            "status": "FAIL",
            "detail": f"accountability exit={r.returncode}; {out[-400:]}",
        }
    ]


def write_reports(results: list[dict], identity: list[dict], overall: str) -> tuple[Path, Path]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = REPORTS / f"release_closed_issues_gate_{stamp}.json"
    md_path = REPORTS / f"release_closed_issues_gate_{stamp}.md"
    latest_json = REPORTS / "release_closed_issues_gate_latest.json"
    latest_md = REPORTS / "release_closed_issues_gate_latest.md"

    commit = next((r["detail"] for r in identity if r["id"] == "git"), "")
    version = next((r["detail"] for r in identity if r["id"] == "APP_VERSION"), "")
    vdate = next((r["detail"] for r in identity if r["id"] == "QLA_VALUATION_DATE"), "")

    payload = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "script_version": SCRIPT_VERSION,
        "overall": overall,
        "output": str(OUT),
        "identity": identity,
        "results": results,
        "guide": "Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md",
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Release Closed-Issues Gate",
        "",
        f"**Generated:** {payload['generated']}  ",
        f"**Script:** `tools/validators/validate_release_closed_issues.py` v{SCRIPT_VERSION}  ",
        f"**Overall:** **{overall}**  ",
        f"**Git:** {commit}  ",
        f"**APP_VERSION:** {version}  ",
        f"**Valuation:** {vdate}  ",
        f"**Output:** `{OUT}`  ",
        "",
        "Guide: `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md`",
        "",
        "## Results",
        "",
        "| Check | Status | Detail |",
        "|-------|--------|--------|",
    ]
    for r in identity + results:
        detail = str(r.get("detail", "")).replace("|", "/").replace("\n", " ")[:220]
        lines.append(f"| {r['id']} | **{r['status']}** | {detail} |")
    lines += [
        "",
        "## Sign-off",
        "",
        "```text",
        f"Release / engine APP_VERSION: {version}",
        f"Git commit: {commit}",
        f"Source package / QLA_VALUATION_DATE: {vdate}",
        f"Gate overall: {overall}",
        "Signed off by: ____________  Date: ____________",
        "```",
        "",
    ]
    text = "\n".join(lines) + "\n"
    md_path.write_text(text, encoding="utf-8")
    latest_md.write_text(text, encoding="utf-8")
    return latest_md, latest_json


def main() -> int:
    ap = argparse.ArgumentParser(description="Release gate for Closed issue fixes in Output")
    ap.add_argument(
        "--smoke-only",
        action="store_true",
        help="Skip full accountability (faster; still runs high-risk smokes)",
    )
    ap.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Optional extra JSON copy path",
    )
    args = ap.parse_args()

    print(f"validate_release_closed_issues.py v{SCRIPT_VERSION}")
    print(f"Output: {OUT}")
    print("=" * 72)

    identity = check_identity()
    results: list[dict] = []

    print("Identity...")
    for r in identity:
        print(f"  [{r['status']}] {r['id']}: {r['detail'][:160]}")

    print("Package...")
    pkg = check_package()
    results.extend(pkg)
    for r in pkg:
        print(f"  [{r['status']}] {r['id']}: {r['detail'][:160]}")

    print("High-risk smokes...")
    for label, argv, req in SMOKE_JOBS:
        print(f"  Running {label}...")
        row = _run(label, argv, req)
        results.append(row)
        print(f"  [{row['status']}] {row['id']}")

    print("  Running #71 BAND=00...")
    row71 = smoke_issue71_band()
    results.append(row71)
    print(f"  [{row71['status']}] {row71['id']}: {row71['detail'][:160]}")

    print("  Running #98 QuikCvs endpoint...")
    row98 = smoke_issue98_cvs()
    results.append(row98)
    print(f"  [{row98['status']}] {row98['id']}: {row98['detail'][:160]}")

    if not args.smoke_only:
        print("Accountability (full Closed catalog)...")
        acc = run_accountability()
        results.extend(acc)
        for r in acc:
            print(f"  [{r['status']}] {r['id']}: {r['detail'][:160]}")
    else:
        results.append(
            {
                "id": "accountability",
                "status": "SKIP",
                "detail": "--smoke-only: full catalog not run",
            }
        )

    blocked = [r for r in identity + results if r["status"] == "FAIL"]
    overall = "RELEASE_BLOCKED" if blocked else "RELEASE_OK"

    print("=" * 72)
    print(f"OVERALL: {overall}")
    if blocked:
        print("FAILURES:")
        for r in blocked:
            print(f"  [{r['id']}] {r['detail'][:240]}")
        print("\nDo not hand off this package. Rebuild Output/rates on the release commit, then re-run.")
    else:
        print("Safe to proceed with full Output handoff (not Test_Validation alone).")

    md_path, json_path = write_reports(results, identity, overall)
    print(f"\nWrote {md_path}")
    print(f"Wrote {json_path}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Wrote {args.json}")

    return 1 if overall == "RELEASE_BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
