"""Policy Form Crosswalk enrichment scaffold — disabled by default (CROSSWALK_OVERLAY=0)."""

from __future__ import annotations

import os
from dataclasses import dataclass

import pandas as pd

from qla_core.normalize_utils import normalize


@dataclass
class CrosswalkOverlayConfig:
    enabled: bool = False
    crosswalk_path: str = ""
    crosswalk_map: dict | None = None


def crosswalk_overlay_enabled() -> bool:
    return os.environ.get("CROSSWALK_OVERLAY", "0").strip().lower() in ("1", "true", "yes")


def product_uat_overlay_enabled() -> bool:
    """Isolated product-setup UAT overlay — does not affect batch conversion by default."""
    return os.environ.get("QLA_PRODUCT_UAT_OVERLAY", "0").strip().lower() in ("1", "true", "yes")


def load_policy_form_crosswalk(path: str) -> dict:
    """LifePRO Coverage_ID -> {ql_plan_code, ql_form_number, ql_plan_description, ql_friendly_name}."""
    if not path or not os.path.isfile(path):
        return {}

    xwalk = pd.read_excel(path)
    xwalk.columns = [
        "lifepro_coverage_id",
        "unused",
        "ql_plan_code",
        "ql_form_number",
        "ql_plan_description",
        "ql_friendly_name",
    ]
    result = {}
    for _, row in xwalk.iterrows():
        cid = normalize(row.get("lifepro_coverage_id", ""))
        if not cid or cid == "NAN":
            continue
        result[cid] = {
            "ql_plan_code": normalize(row.get("ql_plan_code", "")),
            "ql_form_number": normalize(row.get("ql_form_number", "")),
            "ql_plan_description": str(row.get("ql_plan_description", "")).strip(),
            "ql_friendly_name": str(row.get("ql_friendly_name", "")).strip(),
        }
    return result


def resolve_crosswalk_overlay_config(crosswalk_path: str | None = None) -> CrosswalkOverlayConfig:
    """Batch/global overlay config — reads CROSSWALK_OVERLAY only (default off)."""
    enabled = crosswalk_overlay_enabled()
    path = crosswalk_path or os.environ.get("POLICY_FORM_CROSSWALK_PATH", "").strip()
    if not path:
        root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        try:
            from qla_core import plan_source_paths as PSP
            path = PSP.policy_form_crosswalk()
        except ImportError:
            path = ""
        if not path:
            default = os.path.join(
                root, "plan_analysis", "source_data", "crosswalk", "Policy Form Crosswalk 5.22.26.xlsx",
            )
            path = default if os.path.isfile(default) else os.path.join(
                root, "docs", "plan_conversion_reference", "Policy Form Crosswalk 5.22.26.xlsx",
            )

    crosswalk_map = load_policy_form_crosswalk(path) if enabled and path else None
    return CrosswalkOverlayConfig(enabled=enabled, crosswalk_path=path, crosswalk_map=crosswalk_map)


def resolve_product_setup_overlay_config(
    crosswalk_path: str | None = None,
    uat_overlay: bool = False,
) -> CrosswalkOverlayConfig:
    """Product setup subprocess overlay — QLA_PRODUCT_UAT_OVERLAY or --uat-overlay only."""
    enabled = uat_overlay or product_uat_overlay_enabled()
    path = crosswalk_path or os.environ.get("POLICY_FORM_CROSSWALK_PATH", "").strip()
    if not path:
        root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        try:
            from qla_core import plan_source_paths as PSP
            path = PSP.policy_form_crosswalk()
        except ImportError:
            path = ""
        if not path:
            default = os.path.join(
                root, "plan_analysis", "source_data", "crosswalk", "Policy Form Crosswalk 5.22.26.xlsx",
            )
            path = default if os.path.isfile(default) else os.path.join(
                root, "docs", "plan_conversion_reference", "Policy Form Crosswalk 5.22.26.xlsx",
            )

    crosswalk_map = load_policy_form_crosswalk(path) if enabled and path else None
    return CrosswalkOverlayConfig(enabled=enabled, crosswalk_path=path, crosswalk_map=crosswalk_map)


def apply_crosswalk_overlay(row_data: dict, coverage_id: str, config: CrosswalkOverlayConfig) -> dict:
    """Optional overlay for PLAN/FORM/DESCR/PLANNAME — no-op when disabled."""
    if not config.enabled or not config.crosswalk_map:
        return row_data

    entry = config.crosswalk_map.get(normalize(coverage_id))
    if not entry:
        return row_data

    out = dict(row_data)
    if entry.get("ql_plan_code"):
        out["PLAN"] = entry["ql_plan_code"]
    if entry.get("ql_form_number"):
        out["FORM"] = entry["ql_form_number"]
    if entry.get("ql_plan_description"):
        out["DESCR"] = entry["ql_plan_description"].upper()
    if entry.get("ql_friendly_name"):
        out["PLANNAME"] = entry["ql_friendly_name"].upper()
    return out
