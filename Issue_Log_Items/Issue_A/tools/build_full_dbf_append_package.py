#!/usr/bin/env python3
"""Build Append Tool package from Output: generic DBFs + correct memo/claims placement.

Does NOT write to Q:\\CSO\\CSO_Test_6_30_2026.
"""

from __future__ import annotations

import csv
import json
import shutil
import traceback
from datetime import datetime, timezone
from pathlib import Path

from qla_core.dbf_append_tool_package import (
    APPEND_INPUT_SKIP_CSVS,
    DEFAULT_APPEND_INPUT,
    DEFAULT_APPEND_OUTPUT,
    finalize_dbf_append_tool_package,
)
from qla_core.normalize_utils import CLIENT_ID_TARGET_FIELDS

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
INPUT = Path(DEFAULT_APPEND_INPUT)
OUTPUT = Path(DEFAULT_APPEND_OUTPUT)
TEMPLATES = Path(r"C:\Users\warren\Desktop\DBF_Append_Tool\templates")
EVID = ROOT / "Issue_Log_Items" / "Issue_A" / "evidence"

SKIP_CSV = {
    "rate_csv_manifest.csv",
    "claims_review_hold_manifest.csv",
    "claims_cross_table_validation_report.csv",
    "claims_emit_enhancement_validation.csv",
    "cso_mortality_crosswalk_qa.csv",
    "variation_code_audit.csv",
}


def _find_template(stem: str) -> Path | None:
    direct = TEMPLATES / f"{stem}.dbf"
    if direct.is_file():
        return direct
    lower = stem.lower()
    for p in TEMPLATES.glob("*.dbf"):
        if p.stem.lower() == lower:
            return p
    return None


def _append_csv_to_dbf(csv_path: Path, template_path: Path, out_path: Path) -> tuple[int, int]:
    if out_path.exists():
        out_path.unlink()
    shutil.copy2(template_path, out_path)

    for ext in (".fpt", ".dbt", ".FPT", ".DBT"):
        memo_tmpl = template_path.with_suffix(ext)
        if memo_tmpl.is_file():
            memo_tgt = out_path.with_suffix(ext)
            if memo_tgt.exists():
                memo_tgt.unlink()
            shutil.copy2(memo_tmpl, memo_tgt)

    dbf_handle = open(out_path, "r+b")
    try:
        header = dbf_handle.read(32)
        has_memo = header[0] in (0x83, 0x8B, 0xCB, 0xF5, 0xE5)
        memo_found = any(
            out_path.with_suffix(ext).exists() for ext in (".fpt", ".dbt", ".FPT", ".DBT")
        )
        if has_memo and not memo_found:
            dbf_handle.seek(0)
            dbf_handle.write(b"\x03")

        today = datetime.now()
        dbf_handle.seek(1)
        dbf_handle.write(bytes([today.year - 1900, today.month, today.day]))

        # Template may contain seed/demo rows — start fresh (structure only).
        num_records = 0
        header_len = int.from_bytes(header[8:10], byteorder="little")
        record_len = int.from_bytes(header[10:12], byteorder="little")
        dbf_handle.seek(4)
        dbf_handle.write((0).to_bytes(4, byteorder="little"))

        dbf_handle.seek(32)
        fields = []
        while True:
            field_data = dbf_handle.read(32)
            if not field_data or field_data[0] == 0x0D:
                break
            f_name = field_data[0:11].split(b"\x00", 1)[0].decode("latin-1").strip()
            f_type = chr(field_data[11])
            f_length = field_data[16]
            f_decimals = field_data[17]
            fields.append(
                {"name": f_name, "type": f_type, "length": f_length, "decimals": f_decimals}
            )

        # Truncate any pre-copied template data; write conversion rows only.
        dbf_handle.seek(header_len)
        dbf_handle.truncate()
        dbf_handle.seek(header_len)

        new_recs = 0
        with csv_path.open(mode="r", encoding="utf-8-sig", errors="replace", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if not reader.fieldnames:
                return num_records, 0
            csv_headers = {h.strip().upper(): h for h in reader.fieldnames if h}
            if "ORIGSTTUS" in csv_headers and "ORIGSTATUS" not in csv_headers:
                csv_headers["ORIGSTATUS"] = csv_headers["ORIGSTTUS"]

            for row in reader:
                record_bytes = bytearray(b" ")
                for field in fields:
                    f_name_upper = field["name"].upper()
                    csv_col = csv_headers.get(f_name_upper)
                    raw_val = str(row[csv_col]) if csv_col and csv_col in row else ""
                    val = raw_val.strip()

                    # Fixed-width SEEK keys: strip then right-justify to DBF length.
                    # (Default character packing below is left-justify / trailing spaces.)
                    if f_name_upper == "MPOLICY" or f_name_upper in CLIENT_ID_TARGET_FIELDS:
                        val = val.rjust(field["length"], " ")
                    if f_name_upper == "MBANKNO" and len(val) >= 2 and val[-2] == "/":
                        val = val[:-2]

                    if field["type"] == "D":
                        val_clean = "".join(filter(str.isalnum, val))
                        if not val_clean:
                            packed_val = b" " * field["length"]
                        elif len(val_clean) == 8:
                            if val_clean.startswith("20") or val_clean.startswith("19"):
                                packed_val = val_clean.encode("ascii")
                            else:
                                packed_val = (val_clean[4:8] + val_clean[0:4]).encode("ascii")
                        else:
                            packed_val = b" " * field["length"]
                    elif field["type"] == "M":
                        packed_val = b" " * field["length"]
                    elif field["type"] == "L":
                        if val.upper() in ("T", "TRUE", "1", "Y", "YES"):
                            packed_val = b"T"
                        elif val.upper() in ("F", "FALSE", "0", "N", "NO"):
                            packed_val = b"F"
                        else:
                            packed_val = b"?"
                    elif field["type"] in ("N", "F"):
                        if not val or val.lower() in ("nan", "none"):
                            packed_val = b" " * field["length"]
                        else:
                            try:
                                num = float(val.replace(",", ""))
                                dec = int(field.get("decimals") or 0)
                                if dec > 0:
                                    val = f"{num:.{dec}f}"
                                elif num == int(num):
                                    val = str(int(num))
                                else:
                                    val = str(num)
                                if val.startswith("."):
                                    val = "0" + val
                                elif val.startswith("-."):
                                    val = "-0" + val[1:]
                            except ValueError:
                                if val.startswith("."):
                                    val = "0" + val
                                elif val.startswith("-."):
                                    val = "-0" + val[1:]
                            if len(val) > field["length"]:
                                val = val[-field["length"] :]
                            packed_val = val.rjust(field["length"], " ").encode("ascii", "ignore")
                    else:
                        packed_val = val[: field["length"]].ljust(field["length"], " ").encode(
                            "ascii", "replace"
                        )
                    record_bytes.extend(packed_val)

                if len(record_bytes) < record_len:
                    record_bytes.extend(b" " * (record_len - len(record_bytes)))
                elif len(record_bytes) > record_len:
                    record_bytes = record_bytes[:record_len]
                dbf_handle.write(record_bytes)
                new_recs += 1

        dbf_handle.write(b"\x1A")
        dbf_handle.seek(4)
        total_recs = num_records + new_recs
        dbf_handle.write(total_recs.to_bytes(4, byteorder="little"))
        return num_records, new_recs
    finally:
        dbf_handle.close()


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    EVID.mkdir(parents=True, exist_ok=True)
    if not OUT.is_dir():
        print("FAIL: missing Output", OUT)
        return 2

    # 1) Publish safe CSVs + place memo/claims correctly
    pkg = finalize_dbf_append_tool_package(
        OUT,
        ROOT,
        append_input=INPUT,
        append_output=OUTPUT,
        publish_csvs=True,
    )
    print("memo", pkg.get("quikmemo"))
    print("claims", {k: pkg.get("claims", {}).get(k) for k in ("ok", "missing", "staging")})

    # 2) Build remaining non-memo/non-claims tables via Append Tool logic
    results = []
    ok = 0
    fail = 0
    csv_files = []
    for src in sorted(OUT.glob("*.csv")):
        if not src.name.lower().startswith("quik"):
            continue
        if src.name.lower() in APPEND_INPUT_SKIP_CSVS or src.name.lower() in SKIP_CSV:
            continue
        csv_files.append(src)
    rates = OUT / "rates"
    if rates.is_dir():
        for src in sorted(rates.glob("*.csv")):
            if src.name.lower() in SKIP_CSV:
                continue
            csv_files.append(src)

    for csv_path in csv_files:
        stem = csv_path.stem
        tmpl = _find_template(stem)
        out_path = OUTPUT / f"{stem}.dbf"
        rec = {"csv": csv_path.name, "stem": stem, "ok": False}
        if tmpl is None:
            rec["error"] = "missing template"
            fail += 1
            results.append(rec)
            print("MISSING TEMPLATE", csv_path.name)
            continue
        try:
            prior, appended = _append_csv_to_dbf(csv_path, tmpl, out_path)
            rec.update(
                {
                    "ok": True,
                    "template": tmpl.name,
                    "appended": appended,
                    "total": prior + appended,
                }
            )
            ok += 1
            print(f"OK {csv_path.name} -> {out_path.name} rows={prior + appended}")
        except Exception as exc:
            rec["error"] = str(exc)
            rec["trace"] = traceback.format_exc()
            fail += 1
            print("FAIL", csv_path.name, exc)
        results.append(rec)

    # Re-place memo/claims AFTER generic append so they are never overwritten
    pkg2 = finalize_dbf_append_tool_package(
        OUT,
        ROOT,
        append_input=INPUT,
        append_output=OUTPUT,
        publish_csvs=False,
    )

    summary = {
        "generated_at": ts,
        "task": "full_dbf_append_package",
        "source_csv": str(OUT),
        "dbf_input": str(INPUT),
        "dbf_output": str(OUTPUT),
        "q_deploy": False,
        "generic_ok": ok,
        "generic_fail": fail,
        "memo_ok": bool(pkg2.get("quikmemo", {}).get("ok")),
        "claims_ok": bool(pkg2.get("claims", {}).get("ok")),
        "memo": pkg2.get("quikmemo"),
        "claims": pkg2.get("claims"),
        "results": results,
        "pass": fail == 0 and ok > 0 and bool(pkg2.get("quikmemo", {}).get("ok")),
    }
    out_json = EVID / "full_dbf_append_package_summary.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        "FULL_DBF_APPEND",
        "PASS" if summary["pass"] else "FAIL",
        f"generic={ok}/{ok+fail}",
        f"memo_ok={summary['memo_ok']}",
        f"claims_ok={summary['claims_ok']}",
    )
    print("wrote", out_json)
    return 0 if summary["pass"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
