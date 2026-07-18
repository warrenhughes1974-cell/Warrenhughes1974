"""
Issue #83 — apply gender companion rate keys to current Output/rates + PVO recompute.
Does not invent factor values. Safe to re-run.
"""
from __future__ import annotations

import csv
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
    key_rows = {kt: _read(RATES / fname) for kt, fname in KEY_FILES.items()}
    before_counts = {kt: len(key_rows[kt]) for kt in K.FAMILY_KEY_TABLES}

    member_rows = {}
    for fname in MEMBER_FILES:
        tname = fname.replace(".csv", "")
        member_rows[tname] = _read(RATES / fname)

    companions = K.ensure_gender_companion_keys(key_rows, member_rows)
    print(f"gender companion keys added: {len(companions)}")
    for kt in K.FAMILY_KEY_TABLES:
        print(f"  {kt}: {before_counts[kt]} -> {len(key_rows[kt])}")

    mem_added = MB.ensure_members_for_keys(member_rows, key_rows, effdate=S.STANDARD_EFFDATE)
    print(f"member rows added for companion keys: {mem_added}")

    for kt in K.FAMILY_KEY_TABLES:
        _write(RATES / KEY_FILES[kt], _key_fields(kt), key_rows[kt])
    for fname in MEMBER_FILES:
        tname = fname.replace(".csv", "")
        fields = [n for n, _t, _l, _d in S.member_table_fields(tname)]
        _write(RATES / fname, fields, member_rows[tname])

    qp_path = OUT / "quikplan.csv"
    qp = _read(qp_path)
    cfg = RateVariationEnrichmentConfig.from_env_and_defaults(str(ROOT))
    cfg.emitted_csv_dir = str(RATES)
    result = enrich_quikplan_rows(qp, cfg, str(ROOT))
    if result.validation_blockers:
        print("PVO enrichment blockers:", result.validation_blockers)
        return 1
    _write(qp_path, list(QUIKPLAN_SCHEMA), result.enriched_rows)
    print(f"quikplan PVO plans updated: {result.plans_updated}")

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
