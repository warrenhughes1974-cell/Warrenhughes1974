"""Shared paths and constants for ISWL Phase 1 QUIKCVS validators."""
from __future__ import annotations

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CONFIG = PROJECT_ROOT / "plan_analysis" / "phase_r5_rate_loader" / "rate_loader_config.json"
FALLBACK_CONFIG = PROJECT_ROOT / "plan_analysis" / "phase_r5_rate_loader" / "rate_loader_config.example.json"

ISWL_COVERAGE_IDS = frozenset({
    "658 CEN I", "658 CEN SD", "659 CEN II", "659 CEN SR", "659 CEN SD",
    "659 SR GD", "669 SR GD", "679 CEN SD",
})

ISSUE31_OUTPUT = PROJECT_ROOT / "Issue_Log_Items" / "Issue_31" / "output"
PHASE1_OUT = ISSUE31_OUTPUT / "Phase1_QUIKCVS"
PHASE2_OUT = ISSUE31_OUTPUT / "Phase2_QUIKGPS"
PHASE3_OUT = ISSUE31_OUTPUT / "Phase3_QUIKCOI"
PHASE4_OUT = ISSUE31_OUTPUT / "Phase4_QUIKGCOI"
BASELINES_OUT = ISSUE31_OUTPUT / "baselines"
PIPELINE_OUT = ISSUE31_OUTPUT / "pipeline"

ISSUE32_OUTPUT = PROJECT_ROOT / "Issue_Log_Items" / "Issue_32" / "output"
PHASE5_OUT = ISSUE32_OUTPUT / "Phase5_QUIKUINT"
UINT_BASELINE_PATH = ISSUE32_OUTPUT / "baselines" / "iswl_quikuint_regression_baseline.json"

ISSUE33_OUTPUT = PROJECT_ROOT / "Issue_Log_Items" / "Issue_33" / "output"
PHASE6_OUT = ISSUE33_OUTPUT / "Phase6_QUIKISSC"
ISSC_BASELINE_PATH = ISSUE33_OUTPUT / "baselines" / "iswl_quikissc_regression_baseline.json"

ISWL_UINT_MPLANS = frozenset({
    "1658C1", "1658CS", "1659C2", "1659CR", "1659CS", "1659SR", "1669SR", "1679CS",
})
ISWL_ISSC_MPLANS = ISWL_UINT_MPLANS
EXPECTED_UINT_ROWS = 32
EXPECTED_UINT_TIERS_PER_MPLAN = 4
EXPECTED_ISSC_ROWS = 8
BASELINE_PATH = BASELINES_OUT / "iswl_quikcvs_regression_baseline.json"
GPS_BASELINE_PATH = BASELINES_OUT / "iswl_quikgps_regression_baseline.json"
COI_BASELINE_PATH = BASELINES_OUT / "iswl_quikcoi_regression_baseline.json"
GCOI_BASELINE_PATH = BASELINES_OUT / "iswl_quikgcoi_regression_baseline.json"

ISWL_BP_MPLANS = frozenset({"1658CS", "1659CS", "1669SR", "1679CS"})
ISWL_COI_MPLANS = frozenset({"1658CS", "1679CS"})
ISWL_GCOI_MPLANS = frozenset({"1679CS"})


def load_config() -> dict:
    path = DEFAULT_CONFIG if DEFAULT_CONFIG.is_file() else FALLBACK_CONFIG
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["_config_path"] = str(path)
    return cfg


def resolve_path(cfg: dict, key: str) -> Path:
    rel = cfg.get(key, "")
    if not rel:
        return Path()
    p = Path(rel)
    return p if p.is_absolute() else PROJECT_ROOT / p


def ensure_phase1_out() -> Path:
    PHASE1_OUT.mkdir(parents=True, exist_ok=True)
    return PHASE1_OUT


def ensure_phase2_out() -> Path:
    PHASE2_OUT.mkdir(parents=True, exist_ok=True)
    return PHASE2_OUT


def ensure_phase3_out() -> Path:
    PHASE3_OUT.mkdir(parents=True, exist_ok=True)
    return PHASE3_OUT


def ensure_phase4_out() -> Path:
    PHASE4_OUT.mkdir(parents=True, exist_ok=True)
    return PHASE4_OUT


def ensure_baselines_out() -> Path:
    BASELINES_OUT.mkdir(parents=True, exist_ok=True)
    return BASELINES_OUT


def ensure_pipeline_out() -> Path:
    PIPELINE_OUT.mkdir(parents=True, exist_ok=True)
    return PIPELINE_OUT


def ensure_phase5_out() -> Path:
    PHASE5_OUT.mkdir(parents=True, exist_ok=True)
    return PHASE5_OUT


def ensure_phase6_out() -> Path:
    PHASE6_OUT.mkdir(parents=True, exist_ok=True)
    return PHASE6_OUT


def ensure_issue33_baselines_out() -> Path:
    (ISSUE33_OUTPUT / "baselines").mkdir(parents=True, exist_ok=True)
    return ISSUE33_OUTPUT / "baselines"


def ensure_issue32_baselines_out() -> Path:
    (ISSUE32_OUTPUT / "baselines").mkdir(parents=True, exist_ok=True)
    return ISSUE32_OUTPUT / "baselines"


RATE_OUTPUT_DIR = PROJECT_ROOT / "QLA_Migration" / "Output" / "rates"
FORBIDDEN_COI_GCOI_KEY_FILES = ("QuikPlCoi.csv", "QuikPlGcoi.csv")
REQUIRED_COI_GCOI_FACTOR_FILES = ("QuikCoi.csv", "QuikGcoi.csv")


def validate_coi_gcoi_output_filenames() -> tuple[bool, list[str]]:
    """Assert deliverable COI/GCOI factor filenames; forbid invalid QuikPl* companions."""
    notes: list[str] = []
    ok = True
    for name in REQUIRED_COI_GCOI_FACTOR_FILES:
        if not (RATE_OUTPUT_DIR / name).is_file():
            ok = False
            notes.append(f"missing required output: {name}")
    for name in FORBIDDEN_COI_GCOI_KEY_FILES:
        if (RATE_OUTPUT_DIR / name).is_file():
            ok = False
            notes.append(f"forbidden artifact present: {name}")
    manifest = RATE_OUTPUT_DIR / "rate_csv_manifest.csv"
    if manifest.is_file():
        text = manifest.read_text(encoding="utf-8")
        if "QuikPlCoi" in text or "QuikPlGcoi" in text:
            ok = False
            notes.append("rate_csv_manifest references QuikPlCoi or QuikPlGcoi")
    return ok, notes
