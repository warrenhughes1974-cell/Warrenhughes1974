import csv

from qla_core.rate_emit import _write_csv_manifest
from qla_core.quikplan_rate_variation_flags import scan_emitted_key_csvs


def test_rate_manifest_is_written_outside_table_csv_directory(tmp_path):
    rates_dir = tmp_path / "QLA_Migration" / "Output" / "rates"
    reports_dir = tmp_path / "QLA_Migration" / "Reports" / "rates"
    path = _write_csv_manifest(
        str(rates_dir),
        [{"kind": "factor", "table": "QuikCvs", "path": str(rates_dir / "QuikCvs.csv"), "rows": 1}],
        str(reports_dir),
    )

    assert path == str(reports_dir / "rate_csv_manifest.csv")
    assert not (rates_dir / "rate_csv_manifest.csv").exists()
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["TABLE"] == "QuikCvs"


def test_emitted_key_scan_counts_every_key_row(tmp_path):
    rates_dir = tmp_path / "rates"
    rates_dir.mkdir()
    with open(rates_dir / "QuikPlCv.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["PLAN", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE"],
        )
        writer.writeheader()
        for uw in ("00", "NS"):
            writer.writerow({
                "PLAN": "P001", "GENDER": "F", "UWCLASS": uw, "BAND": "00",
                "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101",
            })

    stats = scan_emitted_key_csvs(str(rates_dir))
    assert stats[("P001", "CV")].row_count == 2
    assert stats[("P001", "CV")].uwclasses == {"00", "NS"}
