"""Generate ENG-PKG-001 rollback manifest."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRE = ROOT / "reports" / "packaging" / "ENG-PKG-001_Prechange_File_Hashes.csv"
OUT = ROOT / "reports" / "packaging" / "ENG-PKG-001_Rollback_Manifest.csv"

STAGE4C_FILES = [
    "pyproject.toml",
    "qla_core/__init__.py",
    "qla_core/README.md",
    "qla_core/CHANGELOG.md",
    "docs/packaging/VERSIONING_STANDARD.md",
    "docs/packaging/PUBLIC_API_CONTRACT.md",
    "docs/packaging/RELEASE_NOTES_0.1.0.md",
    "docs/packaging/DISTRIBUTION_AND_RELEASE_PROCESS.md",
    "tests/engine_packaging/test_eng_pkg_001_contract.py",
    "tools/packaging/eng_pkg_001_prechange_baseline.py",
    "tools/packaging/eng_pkg_001_legacy_scan.py",
    "tools/packaging/eng_pkg_001_build_release.py",
    "tools/packaging/eng_pkg_001_rollback_manifest.py",
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
    for rel in STAGE4C_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        rows.append({
            "relative_path": rel,
            "prechange_sha256": pre_map.get(rel, "NEW_FILE"),
            "postchange_sha256": sha256_file(path),
            "change_purpose": "ENG-PKG-001 packaging",
            "restoration_method": "Restore from prechange hash or delete if NEW_FILE",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
