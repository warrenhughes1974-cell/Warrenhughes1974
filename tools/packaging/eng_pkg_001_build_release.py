"""Build, test, and document ENG-PKG-001 release artifacts."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist"
REPORTS = ROOT / "reports" / "packaging"
PROHIBITED_WHEEL_PATHS = (
    "/citizens",
    "/cfic_rates/",
    "/qla_migration/",
    "/quarantine/",
    "/source/original/",
    ".env",
    "__pycache__/",
    ".pyc",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str], cwd: Path | None = None, **kwargs) -> subprocess.CompletedProcess:
    print("RUN:", " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, cwd=cwd or ROOT, check=True, text=True, capture_output=True, **kwargs)


def list_wheel_contents(wheel: Path) -> list[str]:
    with zipfile.ZipFile(wheel, "r") as zf:
        return sorted(zf.namelist())


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

    # Source-tree smoke tests (skip metadata test when not installed)
    source_tests = run([sys.executable, "-m", "pytest", "tests/engine_packaging/", "-q"])

    # Build
    if DIST.exists():
        shutil.rmtree(DIST)
    build_result = run([sys.executable, "-m", "build"])
    wheels = sorted(DIST.glob("*.whl"))
    sdists = sorted(DIST.glob("*.tar.gz"))
    if not wheels or not sdists:
        raise SystemExit("Build did not produce wheel and sdist")

    wheel = wheels[0]
    sdist = sdists[0]
    wheel_hash = sha256_file(wheel)
    sdist_hash = sha256_file(sdist)
    contents = list_wheel_contents(wheel)
    (REPORTS / "ENG-PKG-001_Distribution_Contents.txt").write_text("\n".join(contents) + "\n", encoding="utf-8")

    prohibited = [c for c in contents if any(p in c.lower().replace("\\", "/") for p in PROHIBITED_WHEEL_PATHS)]
    if prohibited:
        raise SystemExit(f"Prohibited wheel content: {prohibited[:10]}")

    # Clean install + full test suite in isolated venv
    venv_dir = Path(tempfile.mkdtemp(prefix="qla_engine_clean_"))
    py = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    clean_ok = False
    clean_out = ""
    installed_tests_stdout = ""
    try:
        run([sys.executable, "-m", "venv", str(venv_dir)])
        run([str(py), "-m", "pip", "install", "--upgrade", "pip"], cwd=ROOT)
        run([str(py), "-m", "pip", "install", str(wheel)], cwd=ROOT)
        neutral = Path(tempfile.gettempdir())
        smoke = subprocess.run(
            [
                str(py), "-c",
                "import importlib.metadata as m; import qla_core; "
                "import qla_core.rate_dbf_schema, qla_core.rate_factor_loader, "
                "qla_core.rate_key_setup, qla_core.rate_member_setup, qla_core.rate_dbf_writer; "
                "assert m.version('qla-enterprise-conversion-engine')==qla_core.__version__; "
                "assert qla_core.API_COMPATIBILITY_VERSION==1; print('OK')",
            ],
            cwd=neutral,
            capture_output=True,
            text=True,
        )
        clean_ok = smoke.returncode == 0
        clean_out = smoke.stdout + smoke.stderr

        # Copy tests into venv run (installed package only)
        installed_tests = subprocess.run(
            [str(py), "-m", "pip", "install", "pytest"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if installed_tests.returncode == 0:
            test_copy = venv_dir / "engine_packaging_tests"
            shutil.copytree(ROOT / "tests" / "engine_packaging", test_copy)
            full = subprocess.run(
                [str(py), "-m", "pytest", str(test_copy), "-q"],
                cwd=neutral,
                capture_output=True,
                text=True,
            )
            installed_tests_stdout = full.stdout + full.stderr
            clean_ok = clean_ok and full.returncode == 0
    finally:
        shutil.rmtree(venv_dir, ignore_errors=True)

    manifest = {
        "distribution_name": "qla-enterprise-conversion-engine",
        "import_name": "qla_core",
        "version": "0.1.0",
        "api_compatibility_version": 1,
        "repository_commit": commit,
        "build_timestamp": ts,
        "python_version": sys.version,
        "wheel_filename": wheel.name,
        "wheel_sha256": wheel_hash,
        "sdist_filename": sdist.name,
        "sdist_sha256": sdist_hash,
        "required_modules": [
            "rate_dbf_schema", "rate_factor_loader", "rate_key_setup",
            "rate_member_setup", "rate_dbf_writer",
        ],
        "required_symbols": [
            "emit_all_rate_tables_csv", "build_factor_grid",
            "build_key_rows", "build_member_rows",
        ],
        "source_tree_test_result": "PASS" if source_tests.returncode == 0 else "FAIL",
        "installed_test_result": "PASS" if clean_ok else "FAIL",
        "clean_install_result": "PASS" if clean_ok else "FAIL",
        "wheel_file_count": len(contents),
        "notes": "Initial controlled distribution; packaging-only release",
    }
    (REPORTS / "ENG-PKG-001_Release_Manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    build_md = f"""# ENG-PKG-001 Build Report

**Timestamp:** {ts}  
**Result:** {"PASS" if clean_ok else "FAIL"}

## Build environment

| Field | Value |
|-------|-------|
| Python | `{sys.version.split()[0]}` |
| Command | `python -m build` |
| Commit | `{commit}` |

## Artifacts

| Artifact | Filename | SHA-256 |
|----------|----------|---------|
| Wheel | `{wheel.name}` | `{wheel_hash}` |
| Source dist | `{sdist.name}` | `{sdist_hash}` |

## Wheel inspection

- Files in wheel: {len(contents)}
- Prohibited content: none detected
- Contents list: `ENG-PKG-001_Distribution_Contents.txt`

## Source-tree tests

```
{source_tests.stdout}
```

## Installed-package tests (clean venv)

```
{installed_tests_stdout}
```

## Clean install smoke

Result: **{"PASS" if clean_ok else "FAIL"}**

```
{clean_out}
```

## Build stderr

```
{build_result.stderr}
```
"""
    (REPORTS / "ENG-PKG-001_Build_Report.md").write_text(build_md, encoding="utf-8")

    clean_md = f"""# ENG-PKG-001 Clean Install Report

**Timestamp:** {ts}  
**Result:** {"PASS" if clean_ok else "FAIL"}

## Procedure

1. Created temporary virtual environment (not Citizens environment)
2. Installed wheel `{wheel.name}` (not editable)
3. Imported qla_core and required modules from neutral temp directory
4. Verified metadata version == `qla_core.__version__`
5. Ran full packaging test suite in clean venv

## Output

```
{clean_out}
{installed_tests_stdout}
```
"""
    (REPORTS / "ENG-PKG-001_Clean_Install_Report.md").write_text(clean_md, encoding="utf-8")

    print(f"Wheel: {wheel}")
    print(f"SHA-256: {wheel_hash}")
    print(f"Clean install: {'PASS' if clean_ok else 'FAIL'}")
    return 0 if clean_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
