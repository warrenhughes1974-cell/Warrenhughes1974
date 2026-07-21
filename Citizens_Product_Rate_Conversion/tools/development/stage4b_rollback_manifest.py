"""Build Stage 4B rollback manifest with pre/post hashes."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRE = ROOT / "manifests" / "stage4b_prechange_file_hashes.csv"
OUT = ROOT / "reports" / "development" / "Stage4B_Rollback_Manifest.csv"

STAGE4B_ALL = [
    ".citizens-project-root",
    "pyproject.toml",
    "config/citizens.yaml",
    "config/engine_version.yaml",
    "config/source_locations.yaml",
    "config/output_locations.yaml",
    "config/runtime.yaml",
    "config/logging.yaml",
    "config/environments/local.yaml",
    "config/environments/validation.yaml",
    "config/environments/production.yaml",
    "config/schemas/citizens_config.schema.json",
    "config/schemas/engine_version.schema.json",
    "config/schemas/source_locations.schema.json",
    "config/schemas/output_locations.schema.json",
    "config/schemas/runtime.schema.json",
    "conversion/orchestration/configuration.py",
    "conversion/orchestration/citizens_paths.py",
    "conversion/orchestration/legacy_cfic_paths.py",
    "conversion/orchestration/engine_import.py",
    "conversion/orchestration/cfic_reserve_build.py",
    "conversion/orchestration/cfic_rate_publish.py",
    "conversion/orchestration/package_cfic_rates.py",
    "conversion/orchestration/build_cfic_assumption_template.py",
    "tools/engine/check_engine_compatibility.py",
    "tools/development/stage4b_prechange_baseline.py",
    "tools/development/stage4b_legacy_scan.py",
    "tools/development/stage4b_rollback_manifest.py",
    "tests/conftest.py",
    "tests/unit/configuration/test_configuration_loader.py",
    "tests/integration/configuration/test_real_project_load.py",
    "tests/unit/engine/test_engine_import.py",
    "tests/integration/engine/test_compatibility_checker.py",
    "docs/architecture/ENTERPRISE_ENGINE_API_CONTRACT.md",
    "reports/development/Stage4B_Prechange_Baseline.md",
    "reports/development/CIT-ARCH-001_Validation_Report.md",
    "reports/development/CIT-ENGINE-001_Package_Discovery_Report.md",
    "reports/development/Stage4B_Legacy_Reference_Comparison.csv",
    "reports/development/Stage4B_Regression_and_Integrity_Report.md",
    "reports/development/Stage4B_Rollback_Manifest.csv",
    "reports/engine/engine_compatibility_result.json",
    "issues/development/CIT-ARCH-001.md",
    "issues/development/CIT-ENGINE-001.md",
    "Stage4B_Runtime_Foundation_and_Engine_Pin_Report.md",
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


def main() -> None:
    pre_map = {}
    if PRE.exists():
        with PRE.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pre_map[row["relative_path"]] = row.get("sha256", "")

    rows = []
    for rel in STAGE4B_ALL:
        path = ROOT / rel
        if not path.exists():
            continue
        rows.append({
            "relative_path": rel,
            "prechange_sha256": pre_map.get(rel, "NEW_FILE"),
            "postchange_sha256": sha256_file(path),
            "backup_source": "manifests/stage4b_prechange_file_hashes.csv" if rel in pre_map else "N/A",
            "issue_id": "CIT-ARCH-001" if "engine" not in rel.lower() and "ENGINE" not in rel else "CIT-ARCH-001;CIT-ENGINE-001",
            "change_purpose": "Stage 4B runtime foundation",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            w.writeheader()
            w.writerows(rows)
    print(f"Wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
