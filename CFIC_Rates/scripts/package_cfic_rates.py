"""
CFIC rate load package publisher — CSV-only output (CSO-style).

Orchestrates: extract (optional) → validate (optional) → build → publish → manifest.

Output policy:
  CFIC_Rates/Output/rates/  — Quik*.csv ONLY (PascalCase table names)
  CFIC_Rates/Reports/       — rate_csv_manifest.csv, emit_summary.json
  CFIC_Rates/Validation/    — parity check CSVs
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

CFIC_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CFIC_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(CFIC_ROOT))
sys.path.insert(0, str(CFIC_ROOT / "scripts"))

from cfic_paths import (  # noqa: E402
    LEGACY_OUTPUT_RATES,
    OUTPUT_RATES,
    REPORTS,
    VALIDATION,
)
from cfic_rate_publish import (  # noqa: E402
    audit_output_folder,
    clean_legacy_output,
    publish_rate_csvs,
    write_emit_summary,
    write_manifest,
)
from cfic_reserve_build import build_reserve_package  # noqa: E402

ISSUE03_SCRIPTS = CFIC_ROOT / "Issue_Log" / "CFIC_Issue_03" / "scripts"
EXTRACT_SCRIPT = ISSUE03_SCRIPTS / "extract_cfic_reserve_dbf.py"
EXTRACT_PLANS_SCRIPT = ISSUE03_SCRIPTS / "extract_cfic_plans_dbf.py"
VALIDATE_SCRIPT = ISSUE03_SCRIPTS / "validate_cfic_reserve_rates.py"
BUILD_ASSUMPTIONS_SCRIPT = CFIC_ROOT / "scripts" / "build_cfic_assumption_template.py"


def _run_script(script: Path, args: list[str]) -> None:
    cmd = [sys.executable, str(script), *args]
    print(f"RUN: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def parse_plans_arg(raw: str) -> list[str] | None:
    if raw.strip().upper() == "ALL":
        return None
    return [p.strip().upper() for p in raw.split(",") if p.strip()]


def run_validation(plans: list[str], validation_dir: Path) -> bool:
    """Run P7MN checkpoint validation; extend later per plan."""
    validation_dir.mkdir(parents=True, exist_ok=True)
    all_pass = True
    for plan in plans:
        if plan != "P7MN":
            continue
        _run_script(VALIDATE_SCRIPT, ["--plan", plan])
        src = ISSUE03_SCRIPTS.parent / "evidence" / f"cfic_issue03_{plan.lower()}_validation.csv"
        if src.exists():
            dest = validation_dir / src.name
            dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            lines = dest.read_text(encoding="utf-8").strip().splitlines()
            passes = sum(1 for line in lines[1:] if line.endswith(",Y"))
            total = max(len(lines) - 1, 0)
            if passes < total:
                all_pass = False
    return all_pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish CFIC rate CSV load package")
    parser.add_argument("--wave", default="reserve", choices=["reserve"], help="Rate wave to publish")
    parser.add_argument("--plans", default="P7MN,P7FN,P7FS,P7MS", help="CFIC plans or ALL")
    parser.add_argument("--extract", action="store_true", help="Run DBF extract before publish")
    parser.add_argument("--extract-plans", action="store_true", help="Also extract cifi0004.dbf plans master")
    parser.add_argument("--validate", action="store_true", help="Run Access parity validation")
    parser.add_argument("--clean-legacy", action="store_true", help="Remove deprecated output/rates/ drafts")
    parser.add_argument("--skip-audit", action="store_true", help="Skip post-publish output folder audit")
    args = parser.parse_args()

    plans = parse_plans_arg(args.plans)
    plan_list = plans if plans else ["ALL"]

    if args.extract:
        plan_arg = args.plans if args.plans.strip().upper() != "ALL" else "ALL"
        _run_script(EXTRACT_SCRIPT, ["--plans", plan_arg])
    if args.extract_plans:
        _run_script(EXTRACT_PLANS_SCRIPT, [])

    validation_pass: bool | None = None
    if args.validate:
        if plans:
            validation_pass = run_validation(plans, VALIDATION)
        else:
            validation_pass = run_validation(["P7MN"], VALIDATION)

    if args.wave == "reserve":
        pkg = build_reserve_package(plans)
        manifest = publish_rate_csvs(
            pkg["factor_rows"],
            pkg["key_rows"],
            pkg["member_rows"],
            output_dir=OUTPUT_RATES,
            overwrite=True,
        )
        meta = pkg["meta"]
    else:
        raise SystemExit(f"Unsupported wave: {args.wave}")

    manifest_path = write_manifest(
        manifest,
        wave=args.wave,
        plans=meta["cfic_plans"],
        notes="CFIC reserve DBF; OBQ-2 assumptions may be blank",
    )

    audit_issues = [] if args.skip_audit else audit_output_folder(OUTPUT_RATES)
    summary_path = write_emit_summary(
        wave=args.wave,
        plans=meta["cfic_plans"],
        manifest=manifest,
        validation_pass=validation_pass,
        audit_issues=audit_issues,
        extra={
            "collisions": meta["collisions"],
            "format_issues": meta["fmt_issues"],
            "assumption_gaps": len({d["plan"] for d in meta["dep_notes"]}),
            "member_placeholders": meta["member_placeholders"],
        },
    )

    legacy_removed = 0
    if args.clean_legacy:
        legacy_removed = clean_legacy_output(LEGACY_OUTPUT_RATES)

    print(f"\nPublished {len(manifest)} tables -> {OUTPUT_RATES}")
    print(f"Manifest -> {manifest_path}")
    print(f"Summary  -> {summary_path}")
    if meta["collisions"]:
        print(f"WARNING: {meta['collisions']} cell collision(s) in grid build")
        collision_path = REPORTS / "reserve_grid_collisions.txt"
        collision_path.write_text(
            f"collisions={meta['collisions']}\n"
            "Re-extract staging after crosswalk fix; collisions mean duplicate "
            "PLAN/AGE/CNTL/segment cells.\n",
            encoding="utf-8",
        )
        if meta["collisions"] > 0:
            raise SystemExit(
                f"Publish blocked: {meta['collisions']} grid collision(s). "
                f"See {collision_path}"
            )
    if audit_issues:
        print("OUTPUT AUDIT FAILED:")
        for issue in audit_issues:
            print(f"  - {issue}")
        raise SystemExit(1)
    if legacy_removed:
        print(f"Removed {legacy_removed} legacy draft CSV(s) from {LEGACY_OUTPUT_RATES}")

    if BUILD_ASSUMPTIONS_SCRIPT.exists():
        _run_script(BUILD_ASSUMPTIONS_SCRIPT, [])

    if validation_pass is False:
        print("NOTE: Validation reported failures — review Validation/ before client handoff")


if __name__ == "__main__":
    main()
