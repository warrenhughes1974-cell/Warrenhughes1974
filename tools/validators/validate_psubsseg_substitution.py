"""
PSUBSSEG substitution validator — fail-closed full-grid proof (exit 1 on FAIL).

Independently recomputes every expected era-banded cell from the reviewed scope
manifest + merged PDAGE extract (same loader transform the pipeline uses) and
proves QLA_Migration/Output/rates carries them:

  1. Scope manifest loads clean (no drift vs crosswalk).
  2. Every scoped (PLAN, EFFDATE) generation exists: >=1 factor row in the data
     table AND >=1 key row in the key table (QuikPlTv/QuikPlNp/QuikPlCv).
  3. EXTRACT entries: every expected nonzero cell present with the formatted
     value (UW-collapse aware: the cell may live on its UW class or on the
     collapsed '00' key of the same generation).
  4. PLAN_COPY entries: the banded generation's factor rows are value-identical
     to the copy plan's standard 19000101 generation (same key population).

Registered as an always-on release smoke (SMOKE_JOBS) so no future rebatch can
drop these generations silently. See Issue_Log_Items/PSUBSSEG_Rate_Substitution.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from qla_core import rate_dbf_schema as S  # noqa: E402
from qla_core import psubsseg_substitution_loader as PSUB  # noqa: E402
from qla_core import plan_source_paths as PSP  # noqa: E402
from qla_core.rate_factor_loader import LoaderConfig, load_plan_crosswalk  # noqa: E402
from qla_core.plan_source_paths import policy_form_crosswalk  # noqa: E402

RATES_DIR = os.path.join(ROOT, "QLA_Migration", "Output", "rates")
SCOPE_CSV = os.path.join(ROOT, "Issue_Log_Items", "PSUBSSEG_Rate_Substitution",
                         "psubsseg_substitution_scope.csv")
CONFIG_JSON = os.path.join(ROOT, "plan_analysis", "phase_r5_rate_loader",
                           "rate_loader_config.json")

KEY_TABLE = S.KEY_TABLE  # QuikNps shares QuikPlTv (valuation key) per schema


def _fail(msgs, msg):
    msgs.append("FAIL: " + msg)


def _load_output_table(table):
    """rows keyed by (PLAN, AGE, CNTL, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, EFFDATE)."""
    path = os.path.join(RATES_DIR, f"{table}.csv")
    rows = {}
    if not os.path.isfile(path):
        return rows, None
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        rd = csv.DictReader(f)
        fields = rd.fieldnames or []
        for r in rd:
            key = tuple((r.get(k) or "").strip()
                        for k in ("PLAN", "AGE", "CNTL", "GENDER", "UWCLASS",
                                  "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE"))
            rows[key] = r
    return rows, fields


def _load_key_table(kt):
    path = os.path.join(RATES_DIR, f"{kt}.csv")
    gens = set()
    if not os.path.isfile(path):
        return gens
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        for r in csv.DictReader(f):
            gens.add(((r.get("PLAN") or "").strip(), (r.get("EFFDATE") or "").strip()))
    return gens


def main():
    msgs = []
    cov2plan, _ = load_plan_crosswalk(policy_form_crosswalk())
    manifest, scope_issues = PSUB.load_scope_manifest(SCOPE_CSV, cov2plan)
    for issue in scope_issues:
        _fail(msgs, f"scope manifest: {issue['detail']}")
    if not manifest:
        _fail(msgs, f"scope manifest empty or missing: {SCOPE_CSV}")
        print("\n".join(msgs))
        return 1

    with open(CONFIG_JSON, encoding="utf-8") as f:
        cfg = json.load(f)
    config = LoaderConfig.from_dict(cfg.get("segmentation_defaults"))
    decimals = config.source_decimals

    pdage_path = PSP.pdage_extract()

    # -------- recompute expected EXTRACT cells --------
    expected = defaultdict(dict)  # (table, plan..., effdate) -> {col: value}
    status = Counter()
    for t in PSUB.transform_psubsseg_pdage(pdage_path, manifest, config):
        status[t["status"]] += 1
        if t["status"] != "IN_SCOPE":
            continue
        key = (t["table"], t["plan"], t["age"], t["cntl"], t["gender"],
               t["uwclass"], t["band"], t["isscntry"], t["issuest"], t["effdate"])
        expected[key][t["col"]] = t["value"]
    if status.get("SOURCE_SEGMENT_ABSENT"):
        _fail(msgs, f"{status['SOURCE_SEGMENT_ABSENT']} scoped source segment(s) "
                    f"absent from merged PDAGE ({pdage_path})")

    # -------- load emitted output --------
    tables = sorted({e["target_table"] for e in manifest})
    out_rows = {}
    out_fields = {}
    for table in tables:
        out_rows[table], out_fields[table] = _load_output_table(table)
        if out_fields[table] is None:
            _fail(msgs, f"Output table missing: {table}.csv")
    key_gens = {kt: _load_key_table(kt) for kt in {KEY_TABLE[t] for t in tables}}

    # -------- gate 2: every scoped generation exists (factor + key rows) --------
    for e in manifest:
        table, plan, eff = e["target_table"], e["issuing_plan"], e["effdate"]
        n_rows = sum(1 for k in out_rows.get(table, {}) if k[0] == plan and k[8] == eff)
        if n_rows == 0:
            _fail(msgs, f"{table}: no factor rows for generation {plan}@{eff} "
                        f"({e['issuing_coverage']}/{e['rate_type']})")
        kt = KEY_TABLE[table]
        if (plan, eff) not in key_gens.get(kt, set()):
            _fail(msgs, f"{kt}: no key row for generation {plan}@{eff}")

    # -------- gate 3: EXTRACT cell-level value proof (UW-collapse aware) --------
    pfx_for = {"QuikTvs": "TV", "QuikNps": "NP", "QuikCvs": "CV",
               "QuikDvs": "DV", "QuikDbs": "DB"}
    checked = matched = 0
    mismatches = []
    for key, cells in expected.items():
        table = key[0]
        pfx = pfx_for[table]
        row_key = key[1:6] + key[6:]  # (plan, age, cntl, gender, uwclass, band, cntry, st, eff)
        row = out_rows.get(table, {}).get(row_key)
        if row is None:
            # UW collapse: same generation may store the grid under UWCLASS '00'
            collapsed = row_key[:4] + ("00",) + row_key[5:]
            row = out_rows.get(table, {}).get(collapsed)
        if row is None:
            checked += len(cells)
            mismatches.append((key, "ROW_MISSING", None, None))
            continue
        for col, value in cells.items():
            checked += 1
            text, _fits, _red = S.format_factor(
                value, max_len=S.factor_field_len(table), source_decimals=decimals)
            got = (row.get(f"{pfx}{col}") or "").strip()
            if got == text:
                matched += 1
            else:
                mismatches.append((key, f"{pfx}{col}", text, got))
    if mismatches:
        _fail(msgs, f"{len(mismatches)} expected cell(s) missing or mismatched "
                    f"(of {checked} checked); first 5:")
        for m in mismatches[:5]:
            msgs.append(f"      {m}")

    # -------- gate 4: PLAN_COPY generations value-identical to base --------
    for e in manifest:
        if e["mode"] != "PLAN_COPY":
            continue
        table, plan, eff = e["target_table"], e["issuing_plan"], e["effdate"]
        pfx = pfx_for[table]
        rows = out_rows.get(table, {})
        base = {k[1:8]: r for k, r in rows.items()
                if k[0] == e["copy_plan"] and k[8] == S.STANDARD_EFFDATE}
        band = {k[1:8]: r for k, r in rows.items() if k[0] == plan and k[8] == eff}
        if not base:
            _fail(msgs, f"{table}: PLAN_COPY base {e['copy_plan']}@{S.STANDARD_EFFDATE} empty")
            continue
        if set(base) != set(band):
            _fail(msgs, f"{table}: PLAN_COPY {plan}@{eff} key population differs from "
                        f"{e['copy_plan']} base ({len(band)} vs {len(base)})")
            continue
        diff = 0
        for seg, brow in base.items():
            crow = band[seg]
            for i in range(S.N_DURATION_COLS):
                if (brow.get(f"{pfx}{i}") or "") != (crow.get(f"{pfx}{i}") or ""):
                    diff += 1
        if diff:
            _fail(msgs, f"{table}: PLAN_COPY {plan}@{eff} has {diff} factor cell(s) "
                        f"differing from {e['copy_plan']} base")

    verdict = "PASS" if not msgs else "FAIL"
    print(f"PSUBSSEG substitution validator: {verdict}")
    print(f"  scope entries: {len(manifest)} "
          f"({sum(1 for e in manifest if e['mode'] == 'EXTRACT')} EXTRACT / "
          f"{sum(1 for e in manifest if e['mode'] == 'PLAN_COPY')} PLAN_COPY)")
    print(f"  expected cells checked: {checked}; matched: {matched}")
    print(f"  loader row status: {dict(status)}")
    for m in msgs:
        print("  " + m)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
