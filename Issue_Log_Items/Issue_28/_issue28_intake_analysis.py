"""Read-only Issue #28 intake comparison script. Do not modify converter artifacts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from qla_core.product_catalog_authority import (  # noqa: E402
    load_crosswalk_authority,
    split_master_crosswalk_rows,
)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    xlsx_paths = [
        ROOT / "plan_analysis/source_data/crosswalk/Policy Form Crosswalk 5.22.26.xlsx",
        Path(r"c:\Users\warren\AppData\Local\Temp\Policy Form Crosswalk 5.22.26 (2).xlsx"),
    ]
    xlsx_path = next((p for p in xlsx_paths if p.exists()), None)
    if xlsx_path is None:
        raise FileNotFoundError("Policy Form Crosswalk xlsx not found")

    auth = pd.read_excel(xlsx_path)
    auth.columns = [
        "lifepro_coverage_id",
        "unused",
        "ql_plan_code",
        "ql_form_number",
        "ql_plan_description",
        "ql_friendly_name",
    ]
    for col in auth.columns:
        auth[col] = auth[col].astype(str).str.strip()
    auth = auth[
        auth["lifepro_coverage_id"].notna()
        & (auth["lifepro_coverage_id"] != "nan")
        & (auth["lifepro_coverage_id"] != "")
    ]
    auth["lifepro_coverage_id_norm"] = auth["lifepro_coverage_id"].str.upper()

    cat_path = ROOT / "plan_governance/product_catalog_crosswalk.csv"
    cat_mig_path = ROOT / "QLA_Migration/Mapping/product_catalog_crosswalk.csv"
    cat = pd.read_csv(cat_path, dtype=str).fillna("")
    cat_mig = pd.read_csv(cat_mig_path, dtype=str).fillna("")
    cat_same = cat.equals(cat_mig)
    cat["lifepro_coverage_id_norm"] = cat["lifepro_coverage_id"].str.strip().str.upper()

    mcw = pd.read_csv(ROOT / "QLA_Migration/Mapping/Master_Crosswalk.csv", dtype=str).fillna("")
    mcw.columns = ["Old_Value", "New_Value"]
    mcw["Old_Value"] = mcw["Old_Value"].str.strip()
    mcw["New_Value"] = mcw["New_Value"].str.strip()
    pol_re = re.compile(r"^90\d{8}$")
    mcw_prod = mcw[~mcw["Old_Value"].str.match(pol_re, na=False)].copy()
    mcw_prod["Old_norm"] = mcw_prod["Old_Value"].str.upper()
    mcw_map = dict(zip(mcw_prod["Old_norm"], mcw_prod["New_Value"]))

    mcw_path = str(ROOT / "QLA_Migration/Mapping/Master_Crosswalk.csv")
    runtime_authority = load_crosswalk_authority(mcw_path, str(cat_path))

    qp = pd.read_csv(ROOT / "QLA_Migration/Output/quikplan.csv", dtype=str).fillna("")
    qp["PLAN_norm"] = qp["PLAN"].str.strip().str.upper()
    qp_plan_set = set(qp["PLAN_norm"]) - {""}

    qps_path = ROOT / "plan_analysis/quikplan_source.csv"
    qp_by_cov: dict[str, str] = {}
    if qps_path.exists():
        try:
            qps = pd.read_csv(
                qps_path, dtype=str, keep_default_na=False, on_bad_lines="skip", engine="python",
            )
        except TypeError:
            qps = pd.read_csv(
                qps_path, dtype=str, keep_default_na=False, error_bad_lines=False, engine="python",
            )
        qps = qps.fillna("")
        if not qps.empty:
            id_col = "COVERAGE_ID" if "COVERAGE_ID" in qps.columns else qps.columns[0]
            qps["COVERAGE_ID_norm"] = qps[id_col].astype(str).str.strip().str.upper()
            qps = qps[~qps["COVERAGE_ID_norm"].str.contains("---", na=False)]
            qps = qps.drop_duplicates(subset=["COVERAGE_ID_norm"], keep="first")
            for _, src_row in qps.iterrows():
                cid = src_row["COVERAGE_ID_norm"]
                runtime_plan = runtime_authority.product_plan_map.get(
                    src_row[id_col].strip(),
                    src_row[id_col].strip(),
                ).upper()
                qp_by_cov[cid] = runtime_plan if runtime_plan in qp_plan_set else ""
                if not qp_by_cov[cid]:
                    for plan in (runtime_plan, cid):
                        if plan in qp_plan_set:
                            qp_by_cov[cid] = plan
                            break

    ridr = pd.read_csv(ROOT / "QLA_Migration/Output/quikridr.csv", dtype=str).fillna("")
    ridr["MPLAN_norm"] = ridr["MPLAN"].str.strip().str.upper()

    inv = auth[
        [
            "lifepro_coverage_id",
            "ql_plan_code",
            "ql_form_number",
            "ql_plan_description",
            "ql_friendly_name",
        ]
    ].copy()
    inv["source_file"] = str(xlsx_path)
    inv.to_csv(OUT / "Issue_28_Crosswalk_Inventory.csv", index=False)

    auth_map = dict(zip(auth["lifepro_coverage_id_norm"], auth["ql_plan_code"]))
    cat_map_auth: dict[str, str] = {}
    cat_map_compat: dict[str, str] = {}
    cat_status: dict[str, str] = {}
    for _, row in cat.iterrows():
        key = row["lifepro_coverage_id_norm"]
        cat_map_auth[key] = row.get("crosswalk_ql_plan_code", "").strip()
        cat_map_compat[key] = row.get("ql_plan_code", "").strip()
        cat_status[key] = row.get("mapping_status", "").strip()

    rows_diff = []
    auth_ids = set(auth_map.keys())
    cat_ids = set(cat["lifepro_coverage_id_norm"])
    qp_ids = set(qp_by_cov.keys())

    for cid_norm, auth_plan in sorted(auth_map.items()):
        lifepro_id = next(
            (
                row["lifepro_coverage_id"]
                for _, row in auth.iterrows()
                if row["lifepro_coverage_id_norm"] == cid_norm
            ),
            cid_norm,
        )
        cat_auth = cat_map_auth.get(cid_norm, "")
        cat_compat = cat_map_compat.get(cid_norm, "")
        mcw_new = mcw_map.get(cid_norm, "")
        runtime_plan = runtime_authority.product_plan_map.get(lifepro_id, lifepro_id).strip().upper()
        qp_plan = qp_by_cov.get(cid_norm, "")
        if not qp_plan and runtime_plan in qp_plan_set:
            qp_plan = runtime_plan
        status = cat_status.get(cid_norm, "NOT_IN_CATALOG")

        effective_plan = runtime_plan
        effective_source = "runtime_product_plan_map"

        match = effective_plan == auth_plan.upper()
        discrepancy_type = ""
        if not match:
            if status == "CROSSWALK_DIVERGENT":
                discrepancy_type = "COMPAT_EMIT_VS_CROSSWALK_AUTHORITY"
            elif cat_auth and cat_auth.upper() != auth_plan.upper():
                discrepancy_type = "CATALOG_DIVERGENT"
            elif not cat_auth and not mcw_new:
                discrepancy_type = "MISSING_FROM_CATALOG"
            else:
                discrepancy_type = "OTHER"

        rows_diff.append(
            {
                "lifepro_coverage_id": lifepro_id,
                "authoritative_ql_plan_code": auth_plan,
                "catalog_crosswalk_ql_plan_code": cat_auth,
                "catalog_ql_plan_code_compat": cat_compat,
                "catalog_mapping_status": status,
                "master_crosswalk_new_value": mcw_new,
                "quikplan_output_plan": qp_plan,
                "effective_converter_plan": effective_plan,
                "effective_source": effective_source,
                "matches_authoritative": "Y" if match else "N",
                "discrepancy_type": discrepancy_type,
            }
        )

    rows_missing = [
        {
            "lifepro_coverage_id": next(
                row["lifepro_coverage_id"]
                for _, row in auth.iterrows()
                if row["lifepro_coverage_id_norm"] == cid_norm
            ),
            "authoritative_ql_plan_code": auth_map[cid_norm],
            "note": "In crosswalk xlsx but absent from product_catalog_crosswalk.csv",
        }
        for cid_norm in sorted(auth_ids - cat_ids)
    ]

    rows_extra = []
    for cid_norm in sorted(cat_ids - auth_ids):
        rows_extra.append(
            {
                "lifepro_coverage_id": next(
                    row["lifepro_coverage_id"]
                    for _, row in cat.iterrows()
                    if row["lifepro_coverage_id_norm"] == cid_norm
                ),
                "catalog_ql_plan_code": cat_map_compat.get(cid_norm, ""),
                "catalog_crosswalk_ql_plan_code": cat_map_auth.get(cid_norm, ""),
                "note": "In product catalog but absent from crosswalk xlsx",
            }
        )
    for cid_norm in sorted(qp_ids - auth_ids):
        rows_extra.append(
            {
                "lifepro_coverage_id": cid_norm,
                "quikplan_output_plan": qp_by_cov.get(cid_norm, ""),
                "note": "In quikplan output but absent from crosswalk xlsx",
            }
        )

    df_diff = pd.DataFrame(rows_diff)
    df_diff.to_csv(OUT / "Issue_28_Mapping_Differences.csv", index=False)
    pd.DataFrame(rows_missing).to_csv(OUT / "Issue_28_Missing_From_Converter.csv", index=False)
    pd.DataFrame(rows_extra).to_csv(OUT / "Issue_28_Extra_In_Converter.csv", index=False)

    divergent = cat[cat["mapping_status"] == "CROSSWALK_DIVERGENT"]
    matches = int((df_diff["matches_authoritative"] == "Y").sum())
    summary = {
        "crosswalk_rows": len(auth_map),
        "catalog_rows": len(cat),
        "catalog_migration_rows": len(cat_mig),
        "catalog_files_identical": cat_same,
        "quikplan_rows": len(qp),
        "quikplan_unique_plan": int(qp["PLAN"].nunique()),
        "quikridr_unique_mplan": int(ridr["MPLAN_norm"].nunique()),
        "exact_matches": matches,
        "mismatches": len(auth_map) - matches,
        "crosswalk_divergent_catalog_rows": int(len(divergent)),
        "missing_from_catalog": len(rows_missing),
        "extra_in_converter": len(rows_extra),
        "catalog_files_identical": cat_same,
        "xlsx_source": str(xlsx_path),
    }
    (OUT / "_population_stats.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
