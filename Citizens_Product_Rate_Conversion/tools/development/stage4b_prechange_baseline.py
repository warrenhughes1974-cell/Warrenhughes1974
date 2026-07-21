"""Generate Stage 4B prechange baseline hashes and report."""
from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "manifests" / "technical_asset_manifest.csv"
OUT_CSV = ROOT / "manifests" / "stage4b_prechange_file_hashes.csv"
OUT_MD = ROOT / "reports" / "development" / "Stage4B_Prechange_Baseline.md"

STAGE4B_TARGETS = [
    "conversion/orchestration/configuration.py",
    "conversion/orchestration/citizens_paths.py",
    "conversion/orchestration/legacy_cfic_paths.py",
    "conversion/orchestration/engine_import.py",
    "conversion/orchestration/cfic_reserve_build.py",
    "conversion/orchestration/cfic_rate_publish.py",
    "conversion/orchestration/package_cfic_rates.py",
    "conversion/orchestration/build_cfic_assumption_template.py",
    "config/citizens.yaml",
    "config/engine_version.yaml",
    "config/source_locations.yaml",
    "config/output_locations.yaml",
    "config/runtime.yaml",
    "config/logging.yaml",
    "README.md",
    "PROJECT_STATUS.md",
    "CHANGELOG.md",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest_rows() -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    if not MANIFEST.exists():
        return rows
    with MANIFEST.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rel = row.get("relative_path") or row.get("path") or ""
            if rel:
                rows[rel.replace("\\", "/")] = row
    return rows


def scan_reference(path: Path, patterns: list[str]) -> dict[str, int]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {p: 0 for p in patterns}
    return {p: text.count(p) for p in patterns}


def main() -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest_rows()
    patterns = [
        "sys.path.insert",
        "sys.path.append",
        "CFIC_Rates",
        "QLA_Migration",
        "qla_core",
        "C:\\Users",
        "Warrenhughes1974",
    ]
    rows_out = []
    for rel in STAGE4B_TARGETS:
        path = ROOT / rel
        if not path.exists():
            continue
        meta = manifest.get(rel, {})
        refs = scan_reference(path, patterns)
        rows_out.append({
            "relative_path": rel,
            "file_size": path.stat().st_size,
            "sha256": sha256_file(path),
            "lifecycle_classification": meta.get("lifecycle", meta.get("classification", "ACTIVE")),
            "active_or_historical": meta.get("status", "ACTIVE"),
            "qla_core_import": "Y" if refs["qla_core"] > 0 else "N",
            "sys_path_manipulation": "Y" if refs["sys.path.insert"] + refs["sys.path.append"] > 0 else "N",
            "cfic_rates_reference": "Y" if refs["CFIC_Rates"] > 0 else "N",
            "absolute_path_reference": "Y" if refs["C:\\Users"] + refs["Warrenhughes1974"] > 0 else "N",
            "proposed_issue": "CIT-ARCH-001" if "config" in rel or "paths" in rel else "CIT-ARCH-001,CIT-ENGINE-001",
            "proposed_change_reason": "Stage 4B centralized configuration and engine boundary",
        })

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()) if rows_out else [])
        if rows_out:
            w.writeheader()
            w.writerows(rows_out)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    md = f"""# Stage 4B Prechange Baseline

Generated: {ts}

## Baseline confirmations

| Check | Result |
|-------|--------|
| Stage 3 report exists | {"PASS" if (ROOT / "Stage3_Architecture_and_Execution_Readiness_Report.md").exists() else "FAIL"} |
| Stage 4A report exists | {"PASS" if (ROOT / "Stage4A_Source_Authority_and_Plan_Universe_Report.md").exists() else "FAIL"} |
| source_manifest rows | {sum(1 for _ in open(ROOT / "manifests/source_manifest.csv", encoding="utf-8")) - 1} |
| mappings/approved empty | {"PASS" if not any((ROOT / "mappings/approved").rglob("*")) else "FAIL"} |
| qla_core source in Citizens | {"PASS" if not (ROOT / "qla_core").exists() else "FAIL"} |
| Git initialized in Citizens | {"PASS" if not (ROOT / ".git").exists() else "FAIL"} |

## Files hashed for Stage 4B

{len(rows_out)} files captured in `manifests/stage4b_prechange_file_hashes.csv`.

## CFIC_Rates integrity

CFIC_Rates is read-only audit source — not modified during Stage 4B.

"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"Wrote {OUT_CSV} ({len(rows_out)} rows)")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
