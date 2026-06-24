"""Verify LifePRO-native source resolution against May 2026 extract zip."""
import os
import sys
import zipfile
import tempfile
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from qla_core.lifepro_source_resolver import (  # noqa: E402
    resolve_table_source,
    resolve_enrichment_source,
    TABLE_SOURCE_SPECS,
)

ZIP_PATH = os.path.join(
    BASE, "QLA_Migration", "Source", "Incoming", "LifePRO_Extracts_20260530.zip"
)
ABA_SRC = os.path.join(BASE, "QLA_Migration", "Source", "aba_routing_lookup.csv")

EXTRACT_NAMES = [
    "PPOLC_PolicyMaster_Extract_20260530.csv",
    "PPBEN_PolicyBenefit_Extract_20260530.csv",
    "PPBENTYP_BenefitType_Extract_20260530.csv",
    "RelationshipNameAddress_Extract_20260530.csv",
    "PCOVR_Coverage_Extract_20260530.csv",
    "PACTG_Accounting_Extract20260530.csv",
    "PLOAN_LoanInformation_Extract_20260530.csv",
    "PAGNT_AgentMaster_Extract_20260530.csv",
    "PPACH_PACHistory_Extract_20260530.csv",
]


def main():
    if not os.path.isfile(ZIP_PATH):
        print(f"SKIP: zip not found: {ZIP_PATH}")
        return 1

    tmp = tempfile.mkdtemp(prefix="qla_lifepro_src_test_")
    try:
        with zipfile.ZipFile(ZIP_PATH) as zf:
            for name in EXTRACT_NAMES:
                zf.extract(name, tmp)
        if os.path.isfile(ABA_SRC):
            shutil.copy2(ABA_SRC, os.path.join(tmp, "aba_routing_lookup.csv"))

        failures = []
        for table in TABLE_SOURCE_SPECS:
            path, label = resolve_table_source(tmp, table)
            if not path:
                failures.append(f"MISSING table source: {table}")
            else:
                print(f"OK  {table:10} -> {os.path.basename(path)} ({label})")

        for key in ("ppach_banking", "ppbentyp_nfo_div", "aba_routing_lookup"):
            path, label = resolve_enrichment_source(tmp, key)
            if not path:
                failures.append(f"MISSING enrichment: {key}")
            else:
                print(f"OK  {key:18} -> {os.path.basename(path)} ({label})")

        if failures:
            for f in failures:
                print(f"FAIL {f}")
            return 1
        print("ALL RESOLUTION CHECKS PASSED")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
