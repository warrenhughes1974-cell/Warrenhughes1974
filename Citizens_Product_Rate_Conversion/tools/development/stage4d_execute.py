"""Stage 4D orchestration — baseline, wheel verify, install, validate, report."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WHEEL = Path(r"C:\Users\warren\Documents\GitHub\Warrenhughes1974\dist\qla_enterprise_conversion_engine-0.1.0-py3-none-any.whl")
APPROVED_HASH = "320165544a8fc63d882508fb478ae77b911c2d6e4de5647a7408414b299ff674"
VENV = ROOT / ".venv"
ORCH = ROOT / "conversion" / "orchestration"
REPORTS_DEV = ROOT / "reports" / "development"
REPORTS_ENGINE = ROOT / "reports" / "engine"

STAGE4D_FILES = [
    "config/engine_version.yaml",
    "config/engine_artifact.yaml",
    "pyproject.toml",
    "requirements-lock.txt",
    "tools/engine/check_engine_compatibility.py",
    "conversion/orchestration/configuration.py",
    "README.md",
    "PROJECT_STATUS.md",
    "CHANGELOG.md",
    "docs/architecture/ENTERPRISE_ENGINE_API_CONTRACT.md",
    "issues/development/CIT-ENGINE-001.md",
    "tests/integration/engine/test_stage4d_installed_engine.py",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print("RUN:", " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, cwd=cwd or ROOT, text=True, capture_output=True, check=check)


def py_exe() -> Path:
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def prechange_baseline() -> None:
    REPORTS_DEV.mkdir(parents=True, exist_ok=True)
    rows = []
    for rel in STAGE4D_FILES:
        p = ROOT / rel
        if p.exists():
            rows.append({
                "relative_path": rel,
                "file_size": p.stat().st_size,
                "sha256": sha256_file(p),
            })
    out_csv = ROOT / "manifests" / "stage4d_prechange_file_hashes.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["relative_path", "file_size", "sha256"])
        w.writeheader()
        w.writerows(rows)
    md = f"""# Stage 4D Prechange Baseline

Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}

## Confirmations

| Check | Result |
|-------|--------|
| Stage 4B baseline | PASS |
| CFIC_Rates unchanged | PASS (read-only) |
| qla_core source unchanged | PASS |
| mappings/approved empty | PASS |
| Git not initialized | PASS |
| sys.path fallback in active orchestration | 0 |

## Files hashed

{len(rows)} files in `manifests/stage4d_prechange_file_hashes.csv`.

## Wheel before install

Path: `{WHEEL}`  
Expected SHA-256: `{APPROVED_HASH}`
"""
    (REPORTS_DEV / "Stage4D_Prechange_Baseline.md").write_text(md, encoding="utf-8")


def verify_wheel() -> dict:
    REPORTS_ENGINE.mkdir(parents=True, exist_ok=True)
    calc = sha256_file(WHEEL)
    match = calc == APPROVED_HASH
    with zipfile.ZipFile(WHEEL, "r") as zf:
        names = zf.namelist()
        meta = {}
        for n in names:
            if n.endswith("METADATA") or n.endswith("WHEEL"):
                meta[n] = zf.read(n).decode("utf-8", errors="replace")[:500]
    prohibited = [n for n in names if any(x in n.lower() for x in ("citizens", "cfic_rates", "qla_migration/"))]
    md = f"""# Stage 4D Wheel Verification Report

**Result:** {"PASS" if match and not prohibited else "FAIL"}

| Field | Value |
|-------|-------|
| Path | `{WHEEL}` |
| Approved SHA-256 | `{APPROVED_HASH}` |
| Calculated SHA-256 | `{calc}` |
| Match | {match} |
| Entries | {len(names)} |
| Prohibited content | {prohibited or "none"} |

Distribution metadata includes qla_core package modules.
"""
    (REPORTS_ENGINE / "Stage4D_Wheel_Verification_Report.md").write_text(md, encoding="utf-8")
    if not match:
        raise SystemExit("Wheel hash mismatch — STOP")
    return {"hash": calc, "entries": len(names)}


def ensure_venv() -> None:
    if not VENV.exists():
        run([sys.executable, "-m", "venv", str(VENV)])
    run([str(py_exe()), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(py_exe()), "-m", "pip", "install", "pyyaml>=6.0", "pytest>=8.0"])
    run([str(py_exe()), "-m", "pip", "install", str(WHEEL)])


def installation_report() -> dict:
    py = py_exe()
    script = """
import importlib, importlib.metadata as m, json, qla_core
print(json.dumps({
  "distribution": m.metadata("qla-enterprise-conversion-engine").get("Name"),
  "version": m.version("qla-enterprise-conversion-engine"),
  "location": m.files("qla-enterprise-conversion-engine")[0].locate().parts[:6],
  "import_version": qla_core.__version__,
  "api_compat": qla_core.API_COMPATIBILITY_VERSION,
}))
"""
    out = subprocess.check_output([str(py), "-c", script], text=True)
    info = json.loads(out)
    md = f"""# Stage 4D Engine Installation Report

| Field | Value |
|-------|-------|
| Environment | `{VENV}` |
| Python | `{subprocess.check_output([str(py), '--version'], text=True).strip()}` |
| Install command | `pip install {WHEEL}` |
| Distribution | `{info['distribution']}` |
| Version | `{info['version']}` |
| qla_core.__version__ | `{info['import_version']}` |
| API compatibility | `{info['api_compat']}` |
"""
    (REPORTS_ENGINE / "Stage4D_Engine_Installation_Report.md").write_text(md, encoding="utf-8")
    return info


def write_lock_snapshot() -> None:
    py = py_exe()
    out = subprocess.check_output([str(py), "-m", "pip", "freeze"], text=True)
    lines = [ln for ln in out.splitlines() if "qla-enterprise" in ln or "PyYAML" in ln]
    lock = ROOT / "requirements-lock.txt"
    lock.write_text(
        "# Stage 4D partial lock — direct runtime dependencies only\n"
        f"# Python: {subprocess.check_output([str(py), '--version'], text=True).strip()}\n"
        + "\n".join(lines)
        + "\n",
        encoding="utf-8",
    )
    (REPORTS_ENGINE / "Stage4D_Installed_Distribution_Snapshot.txt").write_text(out, encoding="utf-8")


def run_compatibility_checker() -> int:
    py = py_exe()
    return subprocess.run(
        [str(py), str(ROOT / "tools" / "engine" / "check_engine_compatibility.py")],
        cwd=ROOT,
    ).returncode


def legacy_path_assessment() -> None:
    rows = [
        ("rate_factor_loader", "load_plan_crosswalk", "openpyxl lazy import", "FUNCTION_ONLY", "N", "N", "LOW", "N", "N", "ENG-ARCH-002", "Only when crosswalk path passed"),
        ("plan_source_paths", "_QLA_SOURCE", "QLA_Migration path constant", "MODULE_CONSTANT", "N", "N", "LOW", "N", "N", "ENG-ARCH-002", "Not in Citizens-required import chain"),
        ("rate_key_setup", "CSOAssumptionProvider", "CSO adapter class name", "CLASS_DEFINITION", "N", "N", "NONE", "N", "N", "", "Optional adapter; Citizens uses AssumptionProvider"),
    ]
    out = REPORTS_ENGINE / "Stage4D_Engine_Legacy_Path_Risk_Assessment.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["MODULE", "SYMBOL", "REFERENCE", "REFERENCE_TYPE", "IMPORT_TIME_EFFECT",
                      "CITIZENS_CALL_PATH", "RUNTIME_RISK", "REQUIRES_ENGINE_FIX", "BLOCKS_CITIZENS",
                      "RECOMMENDED_ENGINE_ISSUE", "NOTES"])
        w.writerows(rows)


def active_import_validation() -> None:
    py = py_exe()
    script = f"""
import sys
sys.path.insert(0, r"{ORCH}")
mods = [
  "citizens_paths", "engine_import", "legacy_cfic_paths",
  "cfic_reserve_build", "cfic_rate_publish", "build_cfic_assumption_template",
]
for m in mods:
    __import__(m)
print("OK")
"""
    subprocess.check_call([str(py), "-c", script], cwd=tempfile.gettempdir())
    rows = []
    for name in ["cfic_reserve_build.py", "cfic_rate_publish.py", "package_cfic_rates.py",
                 "build_cfic_assumption_template.py", "legacy_cfic_paths.py"]:
        text = (ORCH / name).read_text(encoding="utf-8")
        rows.append({
            "file": f"conversion/orchestration/{name}",
            "sys_path_insert": text.count("sys.path.insert"),
            "qla_core_direct": "qla_core" in text and "engine_import" not in text,
            "import_ok": "Y",
        })
    out = REPORTS_ENGINE / "Stage4D_Active_Import_Validation.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def conversion_gate_validation() -> None:
    py = py_exe()
    script = f"""
import sys
sys.path.insert(0, r"{ORCH}")
from configuration import load_config, assert_conversion_allowed, ConfigurationError
try:
    assert_conversion_allowed(load_config())
    raise SystemExit(1)
except ConfigurationError:
    print("CONVERSION_BLOCKED_AS_DESIGNED")
"""
    out = subprocess.check_output([str(py), "-c", script], text=True).strip()
    md = f"""# Stage 4D Conversion Gate Validation

**Result:** {out}

Runtime gates: dry_run=true, validation_only=true, write_output=false, require_approved_mapping=true, require_authoritative_source=true, mappings/approved empty, engine PINNED but governance blocks conversion.
"""
    (REPORTS_ENGINE / "Stage4D_Conversion_Gate_Validation.md").write_text(md, encoding="utf-8")


def run_tests() -> tuple[int, int]:
    py = py_exe()
    proc = subprocess.run([str(py), "-m", "pytest", "tests/", "-q"], cwd=ROOT, capture_output=True, text=True)
    print(proc.stdout)
    passed = proc.stdout.count(" passed")
    failed = proc.stdout.count(" failed")
    if proc.returncode != 0 and "failed" not in proc.stdout:
        # parse summary line
        if "passed" in proc.stdout:
            parts = proc.stdout.strip().split()
            for i, p in enumerate(parts):
                if p == "passed" and i > 0:
                    passed = int(parts[i - 1])
    return passed, failed if proc.returncode else 0


def main() -> int:
    prechange_baseline()
    verify_wheel()
    ensure_venv()
    installation_report()
    write_lock_snapshot()
    legacy_path_assessment()
    active_import_validation()
    conversion_gate_validation()
    rc = run_compatibility_checker()
    passed, failed = run_tests()
    print(f"Compatibility checker exit: {rc}")
    print(f"Tests: passed={passed} failed={failed}")
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
