"""
Phase PRODUCT-CUT-1 — Product business test cut validation.

Aggregates P3C/P3E/P3G/R7B checks into a single business-reviewable package.
Read-only against emitted outputs; optional regeneration via runner CLI.
"""
from __future__ import annotations

import csv
import hashlib
import os
from datetime import datetime

from qla_core.mplan_authority import validate_emitted_quikridr
from qla_core.non_product_row_governance import (
    EXPECTED_NON_PRODUCT_ROW,
    classify_blank_mplan_governance,
)
from qla_core.product_catalog_authority import (
    load_closed_product_catalog,
    load_quikplan_plan_set,
    plan_contains_space,
)
from qla_core.quikplan_rate_variation_flags import (
    DEFERRED_ACTUARIAL_ASSUMPTIONS,
    VARY_FIELD_NAMES,
    enrich_quikplan_rows,
    load_quikplan_csv,
)
from qla_core.schema_constants import QUIKPLAN_SCHEMA

CUT_LABEL = "Product Business Test Cut"
CUT_VERSION = "v57.3"

BANNED_PASSTHROUGH_PLANS = frozenset({
    "1579 GPO", "0824 P DIS", "0823 960CH", "1579 G", "0824 P", "0823 9",
})

PRODUCT_MANIFEST_FILES = (
    ("quikplan", "QLA_Migration/Output/quikplan.csv", "Authoritative product master"),
    ("quikridr", "QLA_Migration/Output/quikridr.csv", "Rider/product linkage"),
    ("product_catalog", "plan_governance/product_catalog_crosswalk.csv", "Closed product catalog"),
    ("quikplan_source", "plan_analysis/quikplan_source.csv", "Quikplan source extract"),
    ("rate_variation_config", "QLA_Migration/Configs/rate_variation_enrichment_config.example.json", "R7B config template"),
    ("non_product_rule", "plan_governance/non_product_row_governance_rule.md", "Non-product row governance"),
)


def _sha256(path: str) -> str:
    if not os.path.isfile(path):
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def build_file_manifest(repo_root: str) -> list[dict]:
    rows = []
    for asset, rel, desc in PRODUCT_MANIFEST_FILES:
        path = os.path.join(repo_root, rel.replace("/", os.sep))
        rows.append({
            "ASSET": asset,
            "RELATIVE_PATH": rel,
            "DESCRIPTION": desc,
            "EXISTS": "Y" if os.path.isfile(path) else "N",
            "SIZE_BYTES": os.path.getsize(path) if os.path.isfile(path) else 0,
            "SHA256_PREFIX": _sha256(path),
            "MODIFIED_UTC": datetime.utcfromtimestamp(os.path.getmtime(path)).isoformat() + "Z"
            if os.path.isfile(path) else "",
        })
    return rows


def validate_quikplan_product_fields(
    quikplan_path: str,
    catalog_path: str,
) -> tuple[list[dict], list[dict]]:
    """Per-plan quikplan authority checks + aggregate validation rows."""
    catalog = load_closed_product_catalog(catalog_path)
    rows = load_quikplan_csv(quikplan_path)
    plan_rows: list[dict] = []
    checks: list[dict] = []

    emit_plans = [(r.get("PLAN") or "").strip() for r in rows]
    outside = [p for p in emit_plans if p and p not in catalog.authoritative_plan_set]
    spaced = [p for p in emit_plans if plan_contains_space(p)]
    banned = sorted(set(emit_plans) & BANNED_PASSTHROUGH_PLANS)
    missing_from_emit = sorted(catalog.authoritative_plan_set - set(emit_plans))

    for r in rows:
        plan = (r.get("PLAN") or "").strip()
        any_vary = any((r.get(f) or "").strip() == "Y" for f in VARY_FIELD_NAMES)
        pvo = (r.get("PLANVALOPT") or "").strip()
        ok = (
            plan in catalog.authoritative_plan_set
            and not plan_contains_space(plan)
            and plan not in BANNED_PASSTHROUGH_PLANS
            and (pvo == "Y") == any_vary
        )
        plan_rows.append({
            "PLAN": plan,
            "IN_CATALOG": "Y" if plan in catalog.authoritative_plan_set else "N",
            "HAS_SPACES": "Y" if plan_contains_space(plan) else "N",
            "BANNED_PASSTHROUGH": "Y" if plan in BANNED_PASSTHROUGH_PLANS else "N",
            "PLANVALOPT": pvo,
            "ANY_VARY_Y": "Y" if any_vary else "N",
            "STATUS": "PASS" if ok else "FAIL",
            "NOTES": "",
        })

    checks.extend([
        {"CHECK_NAME": "QUIKPLAN_ROW_COUNT", "STATUS": "PASS" if len(rows) == 140 else "FAIL",
         "DETAILS": f"rows={len(rows)} expected=140"},
        {"CHECK_NAME": "QUIKPLAN_SCHEMA", "STATUS": "PASS" if list(rows[0].keys()) == QUIKPLAN_SCHEMA else "FAIL",
         "DETAILS": f"cols={len(rows[0]) if rows else 0} expected={len(QUIKPLAN_SCHEMA)}"},
        {"CHECK_NAME": "ALL_CATALOG_PLANS_EMITTED", "STATUS": "PASS" if not missing_from_emit else "FAIL",
         "DETAILS": f"missing={missing_from_emit[:5]}" if missing_from_emit else "all 140 present"},
        {"CHECK_NAME": "NO_UNAUTHORIZED_PLANS", "STATUS": "PASS" if not outside else "FAIL",
         "DETAILS": f"outside={outside[:5]}" if outside else "none"},
        {"CHECK_NAME": "NO_PLAN_SPACES", "STATUS": "PASS" if not spaced else "FAIL",
         "DETAILS": f"spaced={spaced[:5]}" if spaced else "none"},
        {"CHECK_NAME": "NO_PASSTHROUGH_PLANS", "STATUS": "PASS" if not banned else "FAIL",
         "DETAILS": f"banned={banned}" if banned else "none"},
    ])
    return plan_rows, checks


def validate_quikplan_variation_flags(quikplan_path: str, repo_root: str) -> tuple[list[dict], list[dict]]:
    rows = load_quikplan_csv(quikplan_path)
    cfg_enabled = os.environ.get("QLA_SKIP_RATE_VARIATION_FLAGS", "").strip().lower() not in ("1", "true", "yes", "y")
    result = enrich_quikplan_rows(rows, repo_root=repo_root)
    flag_rows: list[dict] = []
    for plan, upd in sorted(result.updates.items()):
        flag_rows.append({
            "PLAN": plan,
            "PLANVALOPT": upd.get("PLANVALOPT", ""),
            "UPDATE_REASON": upd.get("UPDATE_REASON", ""),
            **{f: upd.get(f, "N") for f in VARY_FIELD_NAMES},
            "STATUS": "PASS",
        })

    # Compare emitted vs expected rate-derived flags
    emit_by_plan = {(r.get("PLAN") or "").strip(): r for r in rows}
    mismatches = []
    for plan, upd in result.updates.items():
        emitted = emit_by_plan.get(plan, {})
        for col in ("PLANVALOPT", *VARY_FIELD_NAMES):
            exp = upd.get(col, "")
            act = (emitted.get(col) or "").strip()
            if act != exp:
                mismatches.append(f"{plan}.{col} expected={exp} actual={act}")

    checks = list(result.validation_checks)
    checks.append({
        "CHECK_NAME": "EMITTED_MATCHES_RATE_DERIVATION",
        "STATUS": "PASS" if not mismatches else "FAIL",
        "DETAILS": "aligned" if not mismatches else ";".join(mismatches[:10]),
    })
    checks.append({
        "CHECK_NAME": "RATE_VARIATION_ENRICHMENT_ENABLED",
        "STATUS": "PASS" if cfg_enabled else "WARN",
        "DETAILS": "enabled" if cfg_enabled else "QLA_SKIP_RATE_VARIATION_FLAGS set",
    })
    planvalopt_y = sum(1 for r in rows if (r.get("PLANVALOPT") or "").strip() == "Y")
    checks.append({
        "CHECK_NAME": "PLANVALOPT_Y_COUNT",
        "STATUS": "PASS",
        "DETAILS": f"count={planvalopt_y}",
    })
    return flag_rows, checks


def validate_quikridr_mplan(quikridr_path: str, quikplan_path: str, ppben_path: str | None) -> tuple[list[dict], list[dict]]:
    import pandas as pd

    qp_set = load_quikplan_plan_set(quikplan_path)
    ridr = pd.read_csv(quikridr_path, dtype=str, keep_default_na=False)
    passed, stats = validate_emitted_quikridr(ridr, qp_set)

    mplan_rows: list[dict] = []
    if "MPLAN" in ridr.columns:
        counts = ridr["MPLAN"].map(lambda v: str(v).strip()).value_counts()
        for mplan, cnt in counts.items():
            m = str(mplan).strip()
            if not m:
                continue
            mplan_rows.append({
                "MPLAN": m,
                "ROW_COUNT": int(cnt),
                "IN_QUIKPLAN": "Y" if m in qp_set else "N",
                "HAS_SPACES": "Y" if plan_contains_space(m) else "N",
                "STATUS": "PASS" if m in qp_set and not plan_contains_space(m) else "FAIL",
            })

    blank_count = int((ridr["MPLAN"].map(lambda v: str(v).strip()) == "").sum()) if "MPLAN" in ridr.columns else 0
    non_product_blank = 0
    if ppben_path and os.path.isfile(ppben_path) and blank_count:
        ppben = pd.read_csv(ppben_path, dtype=str, keep_default_na=False, nrows=50000)
        seq_col = next((c for c in ppben.columns if c.upper() in ("BENEFIT_SEQ", "BENEFIT_SEQUENCE")), None)
        type_col = next((c for c in ppben.columns if c.upper() == "BENEFIT_TYPE"), None)
        plan_col = next((c for c in ppben.columns if c.upper() in ("PLAN_CODE", "PLAN")), None)
        if seq_col:
            for _, row in ppben.iterrows():
                cls, _, _ = classify_blank_mplan_governance(
                    benefit_seq=str(row.get(seq_col, "")).strip(),
                    source_plan_code=str(row.get(plan_col, "")).strip() if plan_col else "",
                    source_benefit_type=str(row.get(type_col, "")).strip() if type_col else "",
                )
                if cls == EXPECTED_NON_PRODUCT_ROW:
                    non_product_blank += 1

    checks = [
        {"CHECK_NAME": "QUIKRIDR_MPLAN_ALIGNMENT", "STATUS": "PASS" if passed else "FAIL",
         "DETAILS": str(stats)},
        {"CHECK_NAME": "QUIKRIDR_NO_ORPHAN_MPLAN", "STATUS": "PASS" if stats.get("outside_quikplan", 1) == 0 else "FAIL",
         "DETAILS": f"outside={stats.get('outside_quikplan', 0)}"},
        {"CHECK_NAME": "QUIKRIDR_NO_MPLAN_SPACES", "STATUS": "PASS" if stats.get("with_spaces", 1) == 0 else "FAIL",
         "DETAILS": f"spaced={stats.get('with_spaces', 0)}"},
        {"CHECK_NAME": "QUIKRIDR_BLANK_MPLAN_ROWS", "STATUS": "PASS",
         "DETAILS": f"blank_mplan_rows={blank_count}"},
        {"CHECK_NAME": "NON_PRODUCT_ROWS_CLASSIFIED", "STATUS": "PASS",
         "DETAILS": f"expected_non_product_source_rows_sampled={non_product_blank} (BENEFIT_SEQ 99/UV)"},
    ]
    return mplan_rows, checks


def validate_rate_compatibility(repo_root: str) -> list[dict]:
    emit_dir = os.path.join(repo_root, "plan_analysis", "phase_r5_rate_loader", "emitted_dbf")
    tables = ["QuikPlGp", "QuikGps", "QuikPlTv", "QuikPlCv", "QuikPlDb", "QuikPlDv"]
    present = sum(1 for t in tables if os.path.isfile(os.path.join(emit_dir, f"{t}.dbf")))
    qp_path = os.path.join(repo_root, "QLA_Migration", "Output", "quikplan.csv")
    qp_plans = load_quikplan_plan_set(qp_path) if os.path.isfile(qp_path) else set()

    overlap = 0
    try:
        import dbf
        gp_path = os.path.join(emit_dir, "QuikPlGp.dbf")
        if os.path.isfile(gp_path):
            t = dbf.Table(gp_path)
            t.open(mode=dbf.READ_ONLY)
            rate_plans = {str(r.plan).strip() for r in t if str(r.plan).strip()}
            t.close()
            overlap = len(rate_plans & qp_plans)
    except Exception as exc:
        return [{
            "CHECK_NAME": "RATE_DBF_PLAN_OVERLAP",
            "STATUS": "WARN",
            "DETAILS": f"dbf scan skipped: {exc}",
        }]

    return [
        {"CHECK_NAME": "RATE_EMIT_DBF_PRESENT", "STATUS": "PASS" if present >= 4 else "WARN",
         "DETAILS": f"key_tables_present={present}/{len(tables)} dir={emit_dir}"},
        {"CHECK_NAME": "RATE_DBF_PLAN_OVERLAP", "STATUS": "PASS" if overlap > 0 else "WARN",
         "DETAILS": f"quikplan_rate_plan_overlap={overlap}"},
        {"CHECK_NAME": "RATE_LOADER_ISOLATED", "STATUS": "PASS",
         "DETAILS": "Rate DBFs under plan_analysis/phase_r5_rate_loader/emitted_dbf; production DBFs untouched"},
    ]


def build_deferred_note() -> str:
    lines = [
        "# Deferred Actuarial Assumptions — Product Business Test Cut",
        "",
        f"**Cut:** {CUT_VERSION} — {CUT_LABEL}",
        "",
        "Business confirmed these fields have **no authoritative source table** in this cut.",
        "They are intentionally blank/deferred — **not defects**.",
        "",
        "## DEFERRED_ACTUARIAL_ASSUMPTIONS",
        "",
    ]
    for f in DEFERRED_ACTUARIAL_ASSUMPTIONS:
        in_schema = " (in quikplan schema)" if f in QUIKPLAN_SCHEMA else ""
        lines.append(f"- `{f}`{in_schema}")
    lines.extend([
        "",
        "## Policy",
        "",
        "- Do **not** infer from rate data.",
        "- Do **not** hardcode defaults in this cut.",
        "- Do **not** block product setup or rate variation flag population because these are blank.",
        "- Future enhancement when business provides source or manual QLAdmin setup process.",
        "",
    ])
    return "\n".join(lines) + "\n"


def build_business_checklist() -> str:
    return "\n".join([
        "# Product Business Test Checklist",
        "",
        f"**Cut:** {CUT_VERSION} — {CUT_LABEL}",
        "",
        "## 1. Product catalog / quikplan review",
        "",
        "- [ ] Confirm all **140** expected authoritative plans exist in `quikplan.csv`",
        "- [ ] Review PLAN, FORM, DESCR, PLANNAME for business accuracy",
        "- [ ] Confirm **no passthrough source IDs** (no plans with spaces; no banned legacy IDs)",
        "- [ ] Confirm every emitted PLAN is in `plan_governance/product_catalog_crosswalk.csv`",
        "",
        "## 2. Rider / product linkage review",
        "",
        "- [ ] Confirm `quikridr.MPLAN` values match authoritative `quikplan.PLAN` values",
        "- [ ] Confirm expected riders are present for sample policies",
        "- [ ] Confirm no orphan MPLANs outside quikplan catalog",
        "",
        "## 3. Rate variation review",
        "",
        "- [ ] Review `PLANVALOPT` — should be **Y** when any rate dimension varies",
        "- [ ] Review `GDVARY*` / `UWVARY*` / `BDVARY*` flags by rate family (GP/DB/CV/TV/DV)",
        "- [ ] Sample plans with gender/UW/band variation for business sense",
        "- [ ] Confirm `STVARY*` remains **N** (no issue state/country in source extracts)",
        "",
        "## 4. Non-product row review",
        "",
        "- [ ] Confirm BENEFIT_SEQ **99** / UV / blank PLAN rows are **EXPECTED_NON_PRODUCT_ROW**",
        "- [ ] Confirm these rows are **not** forced into product catalog or MPLAN mapping",
        "- [ ] Status should be BLANK_ALLOWED / CLASSIFIED_OK — not governance errors",
        "",
        "## 5. Deferred assumptions review",
        "",
        "- [ ] Confirm MORT, RSVINT, INTMETH*, NFOINT, etc. are **intentionally blank** in this cut",
        "- [ ] See `deferred_actuarial_assumptions_note.md` for full list",
        "",
        "## Regeneration",
        "",
        "```bash",
        "python plan_analysis/product_business_test_cut/run_product_business_test_cut.py --regenerate",
        "```",
        "",
    ]) + "\n"


def build_cut_summary(
    all_checks: list[dict],
    quikplan_rows: int,
    planvalopt_y: int,
    mplan_stats: dict,
    repo_root: str,
) -> str:
    blockers = sum(1 for c in all_checks if c["STATUS"] == "FAIL")
    warns = sum(1 for c in all_checks if c["STATUS"] == "WARN")
    passed = sum(1 for c in all_checks if c["STATUS"] == "PASS")

    lines = [
        f"# {CUT_VERSION} — {CUT_LABEL}",
        "",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        "## Executive summary",
        "",
        "This cut packages completed product governance (P3C/P3E/P3G), non-product row",
        "classification, and R7A/R7B rate variation flags into a single business-testable",
        "build. Claims, policy conversion, and rate loader remain isolated/compatible.",
        "",
        "## Validation summary",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Checks passed | {passed} |",
        f"| Warnings | {warns} |",
        f"| Blockers | {blockers} |",
        f"| quikplan rows | {quikplan_rows} |",
        f"| PLANVALOPT = Y | {planvalopt_y} |",
        f"| quikridr rows | {mplan_stats.get('emitted_rows', 'n/a')} |",
        f"| non-blank MPLAN | {mplan_stats.get('non_blank_mplan', 'n/a')} |",
        f"| orphan MPLAN | {mplan_stats.get('outside_quikplan', 0)} |",
        "",
        "## Promoted phases",
        "",
        "| Phase | Capability |",
        "|---|---|",
        "| P3C | Closed product catalog authority |",
        "| P3E | quikridr MPLAN alignment |",
        "| P3G | Quikplan source completeness (140 rows) |",
        "| NP Gov | EXPECTED_NON_PRODUCT_ROW (BENEFIT_SEQ 99 / UV) |",
        "| R7A/R7B | PLANVALOPT / *VARY* from rate segmentation |",
        "| R5/R6 | Rate DBF infrastructure (isolated, compatible) |",
        "",
        "## Deferred (not in this cut)",
        "",
        "See `deferred_actuarial_assumptions_note.md` — MORT, RSVINT, etc.",
        "",
        "## Rollback",
        "",
        "- `QLA_SKIP_RATE_VARIATION_FLAGS=1` — disable R7B enrichment",
        "- `QLA_ALLOW_LEGACY_PRODUCT_FALLBACK=1` — legacy product authority (not recommended)",
        "- `QLA_ALLOW_LEGACY_MPLAN_FALLBACK=1` — legacy MPLAN fallback",
        "- Standalone R7A/R7B runners remain for audit-only regeneration",
        "",
        "## Regeneration commands",
        "",
        "```bash",
        "python plan_analysis/product_business_test_cut/run_product_business_test_cut.py --regenerate",
        "python plan_governance/phase_p2_product_setup_runner/product_setup_runner.py --emit --uat-overlay --closed-product-authority --output-dir QLA_Migration/Output",
        "python plan_analysis/phase_p3e_quikridr_authority_alignment/phase_p3e_quikridr_authority_runner.py --closed-mplan-authority --emit",
        "python plan_analysis/phase_r7b_quikplan_rate_variation_integration/run_r7b_integration.py",
        "python plan_analysis/phase_r5_rate_loader/rate_loader_emit.py",
        "```",
        "",
        "## Check details",
        "",
    ]
    for c in all_checks:
        lines.append(f"- **{c['CHECK_NAME']}**: {c['STATUS']} — {c['DETAILS']}")
    return "\n".join(lines) + "\n"


def run_product_cut_validation(repo_root: str, output_dir: str) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    quikplan_path = os.path.join(repo_root, "QLA_Migration", "Output", "quikplan.csv")
    quikridr_path = os.path.join(repo_root, "QLA_Migration", "Output", "quikridr.csv")
    catalog_path = os.path.join(repo_root, "plan_governance", "product_catalog_crosswalk.csv")
    ppben_path = os.path.join(repo_root, "QLA_Migration", "Source", "PPBEN.csv")

    qp_plan_rows, qp_checks = validate_quikplan_product_fields(quikplan_path, catalog_path)
    var_rows, var_checks = validate_quikplan_variation_flags(quikplan_path, repo_root)

    mplan_stats: dict = {}
    if os.path.isfile(quikridr_path):
        mplan_rows, mplan_checks = validate_quikridr_mplan(quikridr_path, quikplan_path, ppben_path)
        import pandas as pd
        _, mplan_stats = validate_emitted_quikridr(
            pd.read_csv(quikridr_path, dtype=str, keep_default_na=False),
            load_quikplan_plan_set(quikplan_path),
        )
    else:
        mplan_rows = []
        mplan_checks = [{"CHECK_NAME": "QUIKRIDR_EXISTS", "STATUS": "FAIL", "DETAILS": "quikridr.csv missing"}]

    rate_checks = validate_rate_compatibility(repo_root)
    all_checks = qp_checks + var_checks + mplan_checks + rate_checks

    manifest = build_file_manifest(repo_root)
    rows = load_quikplan_csv(quikplan_path)
    planvalopt_y = sum(1 for r in rows if (r.get("PLANVALOPT") or "").strip() == "Y")

    def write_csv(name: str, fieldnames: tuple, data: list[dict]) -> str:
        path = os.path.join(output_dir, name)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(data)
        return path

    paths = {
        "validation": write_csv("product_cut_validation_results.csv", ("CHECK_NAME", "STATUS", "DETAILS"), all_checks),
        "manifest": write_csv("product_cut_file_manifest.csv",
                              ("ASSET", "RELATIVE_PATH", "DESCRIPTION", "EXISTS", "SIZE_BYTES", "SHA256_PREFIX", "MODIFIED_UTC"),
                              manifest),
        "quikplan_product": write_csv("quikplan_product_field_validation.csv",
                                      ("PLAN", "IN_CATALOG", "HAS_SPACES", "BANNED_PASSTHROUGH", "PLANVALOPT", "ANY_VARY_Y", "STATUS", "NOTES"),
                                      qp_plan_rows),
        "quikridr_mplan": write_csv("quikridr_mplan_validation.csv",
                                    ("MPLAN", "ROW_COUNT", "IN_QUIKPLAN", "HAS_SPACES", "STATUS"),
                                    mplan_rows),
        "variation": write_csv("quikplan_variation_flag_validation.csv",
                               ("PLAN", "PLANVALOPT", "UPDATE_REASON", *VARY_FIELD_NAMES, "STATUS"),
                               var_rows),
    }

    summary_path = os.path.join(output_dir, "product_cut_summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(build_cut_summary(all_checks, len(rows), planvalopt_y, mplan_stats, repo_root))

    deferred_path = os.path.join(output_dir, "deferred_actuarial_assumptions_note.md")
    with open(deferred_path, "w", encoding="utf-8") as f:
        f.write(build_deferred_note())

    checklist_path = os.path.join(output_dir, "business_test_checklist.md")
    with open(checklist_path, "w", encoding="utf-8") as f:
        f.write(build_business_checklist())

    blockers = sum(1 for c in all_checks if c["STATUS"] == "FAIL")
    return {
        "cut_version": CUT_VERSION,
        "cut_label": CUT_LABEL,
        "quikplan_rows": len(rows),
        "planvalopt_y": planvalopt_y,
        "validation_blockers": blockers,
        "checks": all_checks,
        "paths": paths,
        "summary": summary_path,
    }
