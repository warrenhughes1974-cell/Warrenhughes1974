"""Product vs policy crosswalk authority separation (Phase P2E/P3C).

Authority order for PLAN (when overlay disabled):
  1. product_catalog_crosswalk.csv
  2. Legacy Master_Crosswalk product mappings (fallback)

Phase P3C closed catalog: authoritative emit PLAN set from product_catalog_crosswalk.csv
final column (crosswalk_ql_plan_code or explicit final/target column).

Policy-number mappings remain Master_Crosswalk-only.
Policy Form Crosswalk overlay (CROSSWALK_OVERLAY=1) remains highest when enabled.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

import pandas as pd

from qla_core.normalize_utils import normalize

POLICY_NUMBER_RE = re.compile(r"^90\d{8}$")
PLAN_CONTAINS_SPACE_RE = re.compile(r"\s")

FINAL_AUTHORITATIVE_PLAN_COLUMNS = (
    "final_ql_plan_code",
    "authoritative_ql_plan_code",
    "target_ql_plan_code",
    "final_plan_code",
    "crosswalk_ql_plan_code",
)

DEFAULT_PRODUCT_CATALOG = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "plan_governance", "product_catalog_crosswalk.csv"),
)


@dataclass
class CrosswalkAuthority:
    """Separated product PLAN authority vs policy-number crosswalk."""

    product_plan_map: dict[str, str] = field(default_factory=dict)
    policy_map: dict[str, str] = field(default_factory=dict)
    legacy_product_map: dict[str, str] = field(default_factory=dict)

    def as_legacy_combined_map(self) -> dict[str, str]:
        """Combined map mirroring pre-P2E behavior for non-quikplan tables."""
        combined = dict(self.policy_map)
        combined.update(self.legacy_product_map)
        combined.update(self.product_plan_map)
        return combined


@dataclass
class ClosedProductCatalog:
    """Closed authoritative product catalog for quikplan emission (Phase P3C)."""

    catalog_path: str
    authority_column: str
    authoritative_plan_set: set[str] = field(default_factory=set)
    coverage_to_plan: dict[str, str] = field(default_factory=dict)
    coverage_rows: dict[str, dict] = field(default_factory=dict)
    config_errors: list[dict] = field(default_factory=list)


def is_policy_number(value: str) -> bool:
    return bool(POLICY_NUMBER_RE.match(strip_val(value)))


def strip_val(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def split_master_crosswalk_rows(cw_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split Master_Crosswalk into policy-number vs product/entity mappings."""
    df = cw_df.copy()
    df["Old_Value"] = df.iloc[:, 0].map(strip_val)
    df["New_Value"] = df.iloc[:, 1].map(strip_val)
    df["mapping_class"] = df["Old_Value"].apply(
        lambda v: "POLICY_NUMBER" if is_policy_number(v) else "PRODUCT_OR_ENTITY",
    )
    policy_df = df[df["mapping_class"] == "POLICY_NUMBER"].copy()
    product_df = df[df["mapping_class"] == "PRODUCT_OR_ENTITY"].copy()
    return policy_df, product_df


def _dedupe_old_to_new(df: pd.DataFrame) -> dict[str, str]:
    """Last-wins dedupe for Old_Value -> New_Value (preserves current engine behavior)."""
    result: dict[str, str] = {}
    for _, row in df.iterrows():
        old = normalize(row["Old_Value"])
        new = normalize(row["New_Value"])
        if old:
            result[old] = new
    return result


def resolve_authoritative_plan_column(columns: list[str]) -> str:
    """Select final authoritative PLAN column from product catalog headers."""
    normalized = {strip_val(c).lower(): strip_val(c) for c in columns}
    for candidate in FINAL_AUTHORITATIVE_PLAN_COLUMNS:
        if candidate in normalized:
            return normalized[candidate]
    return ""


def plan_contains_space(plan: str) -> bool:
    return bool(PLAN_CONTAINS_SPACE_RE.search(strip_val(plan)))


def load_closed_product_catalog(path: str | None = None) -> ClosedProductCatalog:
    """Load closed authoritative PLAN catalog from product_catalog_crosswalk.csv."""
    catalog_path = path or DEFAULT_PRODUCT_CATALOG
    result = ClosedProductCatalog(catalog_path=catalog_path, authority_column="")

    if not catalog_path or not os.path.isfile(catalog_path):
        result.config_errors.append({
            "error_type": "CATALOG_NOT_FOUND",
            "severity": "ERROR",
            "lifepro_coverage_id": "",
            "field": "catalog_path",
            "value": catalog_path,
            "notes": "product_catalog_crosswalk.csv not found",
        })
        return result

    df = pd.read_csv(catalog_path, dtype=str, keep_default_na=False).fillna("")
    df.columns = [strip_val(c) for c in df.columns]

    authority_column = resolve_authoritative_plan_column(list(df.columns))
    if not authority_column:
        result.config_errors.append({
            "error_type": "MISSING_AUTHORITY_COLUMN",
            "severity": "ERROR",
            "lifepro_coverage_id": "",
            "field": "authority_column",
            "value": "",
            "notes": "No final authoritative PLAN column found in product catalog",
        })
        return result

    result.authority_column = authority_column
    id_col = "lifepro_coverage_id" if "lifepro_coverage_id" in df.columns else df.columns[0]
    stable_col = "ql_plan_code" if "ql_plan_code" in df.columns else ""

    for row_idx, row in df.iterrows():
        cid = normalize(row.get(id_col, ""))
        auth_plan = strip_val(row.get(authority_column, ""))
        stable_plan = strip_val(row.get(stable_col, "")) if stable_col else ""
        row_dict = {strip_val(k): strip_val(row.get(k, "")) for k in df.columns}

        if not cid:
            continue

        result.coverage_rows[cid] = row_dict

        if not auth_plan:
            result.config_errors.append({
                "error_type": "BLANK_AUTHORITATIVE_PLAN",
                "severity": "ERROR",
                "lifepro_coverage_id": cid,
                "field": authority_column,
                "value": auth_plan,
                "notes": "Authoritative PLAN is blank",
            })
            continue

        if plan_contains_space(auth_plan):
            result.config_errors.append({
                "error_type": "PLAN_CONTAINS_SPACE",
                "severity": "ERROR",
                "lifepro_coverage_id": cid,
                "field": authority_column,
                "value": auth_plan,
                "notes": "Authoritative PLAN contains spaces — QLAdmin PLAN codes must not contain spaces",
            })

        if stable_plan and plan_contains_space(stable_plan):
            result.config_errors.append({
                "error_type": "COMPAT_PLAN_CONTAINS_SPACE",
                "severity": "WARN",
                "lifepro_coverage_id": cid,
                "field": stable_col,
                "value": stable_plan,
                "notes": "Compatibility emit PLAN contains spaces — not valid for closed authority emission",
            })

        if stable_plan and auth_plan and stable_plan != auth_plan and stable_plan == cid:
            result.config_errors.append({
                "error_type": "PASSTHROUGH_COMPAT_PLAN",
                "severity": "INFO",
                "lifepro_coverage_id": cid,
                "field": stable_col,
                "value": stable_plan,
                "notes": f"Passthrough compatibility PLAN documented; authoritative target is {auth_plan}",
            })

        result.coverage_to_plan[cid] = auth_plan
        result.authoritative_plan_set.add(auth_plan)

    return result


@dataclass
class AuthoritativeMplanResolver:
    """Closed MPLAN resolution index (Phase P3E) — maps candidate PLAN_CODE values to authoritative PLAN."""

    catalog: ClosedProductCatalog
    candidate_to_authoritative: dict[str, str] = field(default_factory=dict)
    authoritative_plan_set: set[str] = field(default_factory=set)
    quikplan_plan_set: set[str] = field(default_factory=set)
    legacy_product_map: dict[str, str] = field(default_factory=dict)

    def authoritative_union(self) -> set[str]:
        """Final emit universe: catalog authoritative plans validated against quikplan when available."""
        if self.quikplan_plan_set:
            return self.authoritative_plan_set & self.quikplan_plan_set
        return self.authoritative_plan_set


@dataclass
class MplanResolution:
    """Result of authoritative MPLAN resolution."""

    resolved_mplan: str
    resolution_path: str
    fallback_value: str
    is_authoritative: bool
    source_plan_code: str
    candidate_mplan: str
    error_category: str = ""
    remediation_hint: str = ""


def build_authoritative_mplan_resolver(
    catalog: ClosedProductCatalog | None = None,
    legacy_product_map: dict[str, str] | None = None,
    quikplan_plan_set: set[str] | None = None,
    catalog_path: str | None = None,
) -> AuthoritativeMplanResolver:
    """Build candidate→authoritative MPLAN resolution index from P3C catalog + legacy maps."""
    if catalog is None:
        catalog = load_closed_product_catalog(catalog_path)

    resolver = AuthoritativeMplanResolver(
        catalog=catalog,
        authoritative_plan_set=set(catalog.authoritative_plan_set),
        quikplan_plan_set=set(quikplan_plan_set or set()),
        legacy_product_map=dict(legacy_product_map or {}),
    )

    def _register(candidate: str, authoritative: str) -> None:
        candidate = strip_val(candidate)
        authoritative = strip_val(authoritative)
        if not candidate or not authoritative:
            return
        if plan_contains_space(authoritative):
            return
        resolver.candidate_to_authoritative[candidate] = authoritative
        resolver.authoritative_plan_set.add(authoritative)

    cat_df = pd.read_csv(catalog.catalog_path, dtype=str, keep_default_na=False).fillna("") if os.path.isfile(catalog.catalog_path) else pd.DataFrame()
    if not cat_df.empty:
        cat_df.columns = [strip_val(c) for c in cat_df.columns]
        id_col = "lifepro_coverage_id" if "lifepro_coverage_id" in cat_df.columns else cat_df.columns[0]
        auth_col = catalog.authority_column or "crosswalk_ql_plan_code"
        compat_col = "ql_plan_code" if "ql_plan_code" in cat_df.columns else ""

        for _, row in cat_df.iterrows():
            cid = strip_val(row.get(id_col, ""))
            auth = strip_val(row.get(auth_col, ""))
            compat = strip_val(row.get(compat_col, "")) if compat_col else ""
            if auth:
                _register(auth, auth)
            if cid and auth:
                _register(cid, auth)
            if compat and auth:
                _register(compat, auth)

    for old, new in (legacy_product_map or {}).items():
        old, new = strip_val(old), strip_val(new)
        if not old:
            continue
        if old in resolver.candidate_to_authoritative:
            _register(old, resolver.candidate_to_authoritative[old])
        elif new in resolver.candidate_to_authoritative:
            _register(old, resolver.candidate_to_authoritative[new])
        elif new in catalog.authoritative_plan_set:
            _register(old, new)
            _register(new, new)

    return resolver


def resolve_authoritative_mplan(
    source_plan_code: str,
    candidate_mplan: str,
    resolver: AuthoritativeMplanResolver,
    allow_legacy: bool = False,
) -> MplanResolution:
    """Resolve PPBEN PLAN_CODE / crosswalk candidate to authoritative MPLAN."""
    source = strip_val(source_plan_code)
    candidate = strip_val(candidate_mplan)
    fallback = candidate if candidate else source
    emit_universe = resolver.authoritative_union()

    if not source and not candidate:
        return MplanResolution(
            resolved_mplan="",
            resolution_path="BLANK_INPUT",
            fallback_value="",
            is_authoritative=False,
            source_plan_code=source,
            candidate_mplan=candidate,
            error_category="",
            remediation_hint="Blank MPLAN — classify before governance action",
        )

    for probe, path in (
        (source, "SOURCE_PLAN_CODE"),
        (candidate, "LEGACY_CROSSWALK"),
    ):
        if not probe:
            continue
        if probe in emit_universe and not plan_contains_space(probe):
            return MplanResolution(
                resolved_mplan=probe,
                resolution_path=f"DIRECT_{path}",
                fallback_value=fallback,
                is_authoritative=True,
                source_plan_code=source,
                candidate_mplan=candidate,
            )
        if probe in resolver.candidate_to_authoritative:
            auth = resolver.candidate_to_authoritative[probe]
            if auth in emit_universe and not plan_contains_space(auth):
                return MplanResolution(
                    resolved_mplan=auth,
                    resolution_path=f"CATALOG_{path}",
                    fallback_value=fallback,
                    is_authoritative=True,
                    source_plan_code=source,
                    candidate_mplan=candidate,
                )

    if allow_legacy:
        emit_val = fallback
        return MplanResolution(
            resolved_mplan=emit_val,
            resolution_path="LEGACY_FALLBACK",
            fallback_value=fallback,
            is_authoritative=emit_val in emit_universe and not plan_contains_space(emit_val),
            source_plan_code=source,
            candidate_mplan=candidate,
            error_category="LEGACY_FALLBACK_REPORTED",
            remediation_hint="Legacy fallback enabled via QLA_ALLOW_LEGACY_MPLAN_FALLBACK",
        )

    error = "PLAN_NOT_IN_AUTHORITATIVE_CATALOG"
    hint = "Add PLAN mapping to product_catalog_crosswalk.csv or enable legacy fallback for rollback"
    if plan_contains_space(fallback):
        error = "PLAN_CONTAINS_SPACE"
        hint = f"Replace spaced passthrough '{fallback}' with authoritative catalog PLAN"

    return MplanResolution(
        resolved_mplan="",
        resolution_path="UNAUTHORIZED",
        fallback_value=fallback,
        is_authoritative=False,
        source_plan_code=source,
        candidate_mplan=candidate,
        error_category=error,
        remediation_hint=hint,
    )


def validate_authoritative_mplan(
    resolved_mplan: str,
    resolver: AuthoritativeMplanResolver,
    *,
    allow_blank: bool = True,
) -> tuple[bool, str]:
    """Validate resolved MPLAN against authoritative emit universe."""
    plan = strip_val(resolved_mplan)
    if not plan:
        return allow_blank, "" if allow_blank else "BLANK_MPLAN"
    if plan_contains_space(plan):
        return False, "PLAN_CONTAINS_SPACE"
    emit_universe = resolver.authoritative_union()
    if plan not in emit_universe:
        return False, "ORPHAN_MPLAN"
    return True, ""


def load_quikplan_plan_set(quikplan_path: str) -> set[str]:
    """Load authoritative quikplan.PLAN universe from emitted catalog file."""
    if not quikplan_path or not os.path.isfile(quikplan_path):
        return set()
    df = pd.read_csv(quikplan_path, dtype=str, keep_default_na=False)
    if "PLAN" not in df.columns:
        return set()
    return {strip_val(v) for v in df["PLAN"] if strip_val(v)}


def closed_mplan_authority_enabled() -> bool:
    return os.environ.get("QLA_CLOSED_MPLAN_AUTHORITY", "0").strip().lower() in ("1", "true", "yes")


def allow_legacy_mplan_fallback() -> bool:
    return os.environ.get("QLA_ALLOW_LEGACY_MPLAN_FALLBACK", "0").strip().lower() in ("1", "true", "yes")


def load_product_catalog_crosswalk(path: str | None = None) -> dict[str, str]:
    """Load dedicated product catalog PLAN map: lifepro_coverage_id -> ql_plan_code."""
    catalog_path = path or DEFAULT_PRODUCT_CATALOG
    if not catalog_path or not os.path.isfile(catalog_path):
        return {}

    df = pd.read_csv(catalog_path, dtype=str, keep_default_na=False).fillna("")
    df.columns = [strip_val(c) for c in df.columns]

    id_col = "lifepro_coverage_id" if "lifepro_coverage_id" in df.columns else df.columns[0]
    plan_col = "ql_plan_code" if "ql_plan_code" in df.columns else (
        "New_Value" if "New_Value" in df.columns else df.columns[1] if len(df.columns) > 1 else ""
    )
    if not plan_col:
        return {}

    result: dict[str, str] = {}
    for _, row in df.iterrows():
        cid = normalize(row.get(id_col, ""))
        plan = normalize(row.get(plan_col, ""))
        if cid and plan:
            result[cid] = plan
    return result


def load_crosswalk_authority(
    master_cw_path: str,
    product_catalog_path: str | None = None,
) -> CrosswalkAuthority:
    """Build layered crosswalk authority from Master_Crosswalk + product catalog."""
    policy_map: dict[str, str] = {}
    legacy_product_map: dict[str, str] = {}

    if master_cw_path and os.path.isfile(master_cw_path):
        cw_df = pd.read_csv(master_cw_path, dtype=str, keep_default_na=False)
        policy_df, product_df = split_master_crosswalk_rows(cw_df)
        policy_map = _dedupe_old_to_new(policy_df)
        legacy_product_map = _dedupe_old_to_new(product_df)

    catalog_map = load_product_catalog_crosswalk(product_catalog_path)

    # Layered product PLAN authority: catalog overrides legacy product fallback
    product_plan_map = dict(legacy_product_map)
    product_plan_map.update(catalog_map)

    return CrosswalkAuthority(
        product_plan_map=product_plan_map,
        policy_map=policy_map,
        legacy_product_map=legacy_product_map,
    )


def resolve_plan_code(coverage_id: str, authority: CrosswalkAuthority) -> str:
    """Resolve PLAN from COVERAGE_ID using layered product authority."""
    key = normalize(coverage_id)
    if key in authority.product_plan_map:
        return authority.product_plan_map[key]
    return key
