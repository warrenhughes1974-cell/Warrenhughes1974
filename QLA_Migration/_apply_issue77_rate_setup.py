"""
Issue #77 — apply default key stubs + PVO recompute + MLOANINT default to current Output.
Does not invent factor values. Safe to re-run.
"""
from __future__ import annotations

import csv
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qla_core import rate_dbf_schema as S
from qla_core import rate_key_setup as K
from qla_core import rate_member_setup as MB
from qla_core.quikplan_rate_variation_flags import (
    RateVariationEnrichmentConfig,
    enrich_quikplan_rows,
)
from qla_core.schema_constants import QUIKPLAN_SCHEMA

OUT = ROOT / "QLA_Migration" / "Output"
RATES = OUT / "rates"
TV = OUT / "Test_Validation"
FAMILY_FACTOR = {
    "QuikPlGp": "QuikGps.csv",
    "QuikPlDb": "QuikDbs.csv",
    "QuikPlCv": "QuikCvs.csv",
    "QuikPlTv": "QuikTvs.csv",
    "QuikPlDv": "QuikDvs.csv",
}
KEY_FILES = {kt: f"{kt}.csv" for kt in K.FAMILY_KEY_TABLES}
MEMBER_FILES = ("QuikPlGd.csv", "QuikPlUw.csv", "QuikPlBd.csv", "QuikPlSt.csv", "QuikPlNb.csv")


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        return list(csv.DictReader(f))


def _write(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def _key_fields(kt: str) -> list[str]:
    return [n for n, _t, _l, _d in S.key_table_fields(kt)]


def main() -> int:
    key_rows = {}
    for kt, fname in KEY_FILES.items():
        rows = _read(RATES / fname)
        key_rows[kt] = rows

    # Rated plans = any factor family rows (plus Nps)
    rated = set()
    for fname in list(FAMILY_FACTOR.values()) + ["QuikNps.csv", "QuikNff.csv", "QuikCoi.csv"]:
        for r in _read(RATES / fname):
            p = (r.get("PLAN") or "").strip()
            if p:
                rated.add(p)

    before_counts = {kt: len(key_rows[kt]) for kt in K.FAMILY_KEY_TABLES}
    repaired = K.repair_na_stubs_when_real_codes_exist(key_rows)
    added = K.ensure_default_key_stubs(key_rows, rated, effdate=S.STANDARD_EFFDATE)
    print(f"NA stubs repaired to real codes: {repaired}")
    print(f"default key stubs added: {len(added)}")
    for kt in K.FAMILY_KEY_TABLES:
        print(f"  {kt}: {before_counts[kt]} -> {len(key_rows[kt])}")

    member_rows = {}
    for fname in MEMBER_FILES:
        tname = fname.replace(".csv", "")
        member_rows[tname] = _read(RATES / fname)
    # MLOANINT default
    for r in member_rows.get("QuikPlSt", []):
        if not str(r.get("MLOANINT") or "").strip():
            r["MLOANINT"] = "0.00"
    pruned = MB.prune_default_members_when_real_exist(member_rows)
    mem_added = MB.ensure_members_for_keys(member_rows, key_rows, effdate=S.STANDARD_EFFDATE)
    print(f"NA members pruned (real codes exist): {pruned}")
    print(f"member rows added for stub keys: {mem_added}")

    for kt in K.FAMILY_KEY_TABLES:
        _write(RATES / KEY_FILES[kt], _key_fields(kt), key_rows[kt])
    for fname in MEMBER_FILES:
        tname = fname.replace(".csv", "")
        fields = [n for n, _t, _l, _d in S.member_table_fields(tname)]
        _write(RATES / fname, fields, member_rows[tname])

    # PVO recompute on quikplan
    qp_path = OUT / "quikplan.csv"
    qp = _read(qp_path)
    cfg = RateVariationEnrichmentConfig.from_env_and_defaults(str(ROOT))
    cfg.emitted_csv_dir = str(RATES)
    result = enrich_quikplan_rows(qp, cfg, str(ROOT))
    if result.validation_blockers:
        print("PVO enrichment blockers:", result.validation_blockers)
        for c in result.validation_checks:
            if c["STATUS"] == "FAIL":
                print(" FAIL", c)
        return 1
    _write(qp_path, list(QUIKPLAN_SCHEMA), result.enriched_rows)
    print(f"quikplan PVO plans updated (field diffs): {result.plans_updated}")
    print(f"PLANVALOPT=Y: {result.planvalopt_y}")

    # Publish to Test_Validation
    TV.mkdir(parents=True, exist_ok=True)
    (TV / "rates").mkdir(parents=True, exist_ok=True)
    shutil.copy2(qp_path, TV / "quikplan.csv")
    for kt in K.FAMILY_KEY_TABLES:
        shutil.copy2(RATES / KEY_FILES[kt], TV / "rates" / KEY_FILES[kt])
    for fname in MEMBER_FILES:
        shutil.copy2(RATES / fname, TV / "rates" / fname)
    print(f"published to {TV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
