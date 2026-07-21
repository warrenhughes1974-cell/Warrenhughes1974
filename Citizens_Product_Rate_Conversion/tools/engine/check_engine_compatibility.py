"""Read-only Enterprise Engine compatibility checker (CIT-ENGINE-001)."""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

_ORCH = Path(__file__).resolve().parents[2] / "conversion" / "orchestration"
if str(_ORCH) not in sys.path:
    sys.path.insert(0, str(_ORCH))

from configuration import CitizensConfig, load_config  # noqa: E402


def _check_distribution(cfg: CitizensConfig) -> dict[str, Any]:
    result: dict[str, Any] = {
        "distribution_name": cfg.engine.distribution_name,
        "import_name": cfg.engine.import_name,
        "expected_version": cfg.engine.exact_version,
        "installed_version": None,
        "distribution_found": False,
        "version_match": None,
        "import_version": None,
        "metadata_version_match": None,
        "api_compatibility_expected": cfg.engine.api_compatibility_version,
        "api_compatibility_installed": None,
        "api_compatibility_match": None,
        "errors": [],
    }
    if not cfg.engine.distribution_name:
        result["errors"].append(
            "distribution_name unresolved — engine package metadata incomplete"
        )
        return result
    try:
        installed = metadata.version(cfg.engine.distribution_name)
        result["installed_version"] = installed
        result["distribution_found"] = True
        if cfg.engine.exact_version:
            result["version_match"] = installed == cfg.engine.exact_version
            if cfg.engine.strict_version_check and not result["version_match"]:
                result["errors"].append(
                    f"Version mismatch: expected {cfg.engine.exact_version}, installed {installed}"
                )
        else:
            result["errors"].append("exact_version unresolved — cannot pin or verify")
    except metadata.PackageNotFoundError:
        result["errors"].append(
            f"Distribution '{cfg.engine.distribution_name}' not installed"
        )
        return result

    try:
        qla = importlib.import_module(cfg.engine.import_name)
        result["import_version"] = getattr(qla, "__version__", None)
        result["api_compatibility_installed"] = getattr(qla, "API_COMPATIBILITY_VERSION", None)
        result["metadata_version_match"] = result["import_version"] == result["installed_version"]
        if not result["metadata_version_match"]:
            result["errors"].append(
                f"qla_core.__version__ ({result['import_version']}) != "
                f"installed metadata ({result['installed_version']})"
            )
        if cfg.engine.api_compatibility_version is not None:
            expected = str(cfg.engine.api_compatibility_version)
            actual = str(result["api_compatibility_installed"])
            result["api_compatibility_match"] = expected == actual
            if not result["api_compatibility_match"]:
                result["errors"].append(
                    f"API compatibility mismatch: expected {expected}, got {actual}"
                )
    except ImportError as exc:
        result["errors"].append(f"Cannot import {cfg.engine.import_name}: {exc}")
    return result


def _check_modules(cfg: CitizensConfig) -> dict[str, Any]:
    modules_result: dict[str, Any] = {"modules": {}, "errors": []}
    for mod_suffix in cfg.engine.required_modules:
        full = f"{cfg.engine.import_name}.{mod_suffix}"
        entry: dict[str, Any] = {"importable": False, "symbols": {}}
        try:
            module = importlib.import_module(full)
            entry["importable"] = True
            symbols = cfg.engine.required_symbols.get(mod_suffix, ())
            for symbol in symbols:
                entry["symbols"][symbol] = hasattr(module, symbol)
                if not entry["symbols"][symbol]:
                    modules_result["errors"].append(f"Missing symbol {full}.{symbol}")
        except ImportError as exc:
            entry["error"] = str(exc)
            modules_result["errors"].append(f"Cannot import {full}: {exc}")
        modules_result["modules"][mod_suffix] = entry
    return modules_result


def run_check(config: CitizensConfig | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    dist = _check_distribution(cfg)
    mods = _check_modules(cfg)
    status = cfg.engine.status
    symbol_errors = mods["errors"]
    compatible = (
        status in ("PINNED", "INSTALLED_PACKAGE_CONFIRMED")
        and not dist["errors"]
        and not symbol_errors
        and all(m.get("importable") for m in mods["modules"].values())
    )
    blocked = (
        status in ("PACKAGING_REQUIRED", "BLOCKED", "UNKNOWN")
        or bool(dist["errors"])
        or bool(symbol_errors)
        or not compatible
    )

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": cfg.project_name,
        "environment": cfg.environment,
        "engine_status": status,
        "compatible": compatible,
        "blocked": blocked,
        "distribution": dist,
        "modules": mods,
        "corrective_action": (
            None
            if compatible
            else "Install pinned qla-enterprise-conversion-engine==0.1.0 from verified wheel"
        ),
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Enterprise Engine compatibility")
    parser.add_argument("--output", help="JSON output path")
    args = parser.parse_args()
    cfg = load_config()
    result = run_check(cfg)
    out_path = Path(args.output) if args.output else (
        cfg.project_root / "reports/engine/engine_compatibility_result.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["blocked"] or not result["compatible"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
