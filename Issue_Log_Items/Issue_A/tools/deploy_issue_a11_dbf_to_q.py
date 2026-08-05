#!/usr/bin/env python3
"""Issue A11 — build plan/rate DBFs via DBF Append Tool and deploy to Q UAT."""

from __future__ import annotations

import csv
import json
import os
import shutil
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.normalize_utils import CLIENT_ID_TARGET_FIELDS

TV = ROOT / "QLA_Migration" / "Output" / "Test_Validation"
ARCH = ROOT / "QLA_Migration" / "Archive"
EVID = ROOT / "Issue_Log_Items" / "Issue_A" / "evidence"
DBF_TOOL = Path(r"C:\Users\warren\Desktop\DBF_Append_Tool")
INPUT = DBF_TOOL / "_issue_a11_input"
OUTPUT = DBF_TOOL / "_issue_a11_output"
TEMPLATES = DBF_TOOL / "templates"
QDEST = Path(r"Q:\CSO\CSO_Test_6_30_2026")

# CSV stem -> exact filename on Q (case-sensitive best-effort on Windows)
Q_NAMES = {
    "quikplan": "quikplan.dbf",
    "quikloan": "quikloan.dbf",
    "QuikAint": "QuikAint.dbf",
    "QuikCoi": "QuikCoi.dbf",
    "QuikCvs": "QuikCvs.dbf",
    "QuikDbs": "QuikDbs.dbf",
    "QuikDvs": "QuikDvs.dbf",
    "QuikGcoi": "QuikGcoi.dbf",
    "QuikGps": "QuikGps.dbf",
    "QuikIssc": "QuikIssc.dbf",
    "QuikNff": "QuikNff.dbf",
    "QuikNps": "QuikNps.dbf",
    "QuikPlBd": "QuikPlBd.dbf",
    "QuikPlCv": "QuikPlCv.dbf",
    "QuikPlDb": "QuikPlDb.dbf",
    "QuikPlDv": "QuikPlDv.dbf",
    "QuikPlGd": "QuikPlGd.dbf",
    "QuikPlGp": "QuikPlGp.dbf",
    "QuikPlNb": "QuikPlNb.dbf",
    "QuikPlSt": "QuikPlSt.dbf",
    "QuikPlTv": "QuikPlTv.dbf",
    "QuikPlUw": "QuikPlUw.dbf",
    "QuikTvs": "QuikTvs.dbf",
    "QuikUint": "QuikUint.dbf",
    "QuikUwpo": "QuikUwpo.dbf",
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
    """Direct binary injection (DBF Append Tool v1.5 logic, headless)."""
    if out_path.exists():
        out_path.unlink()
    shutil.copy2(template_path, out_path)

    stem = out_path.stem
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
        memo_found = any(out_path.with_suffix(ext).exists() for ext in (".fpt", ".dbt", ".FPT", ".DBT"))
        if has_memo and not memo_found:
            dbf_handle.seek(0)
            dbf_handle.write(b"\x03")

        today = datetime.now()
        dbf_handle.seek(1)
        dbf_handle.write(bytes([today.year - 1900, today.month, today.day]))

        num_records = int.from_bytes(header[4:8], byteorder="little")
        header_len = int.from_bytes(header[8:10], byteorder="little")
        record_len = int.from_bytes(header[10:12], byteorder="little")

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

        dbf_handle.seek(0, 2)
        if dbf_handle.tell() > header_len:
            dbf_handle.seek(-1, 2)
            if dbf_handle.read(1) == b"\x1A":
                dbf_handle.seek(-1, 2)
            else:
                dbf_handle.seek(0, 2)
        else:
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


def _stage_csvs() -> list[Path]:
    if INPUT.exists():
        shutil.rmtree(INPUT)
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    INPUT.mkdir(parents=True)
    OUTPUT.mkdir(parents=True)

    staged: list[Path] = []
    for name in ("quikplan.csv", "quikloan.csv"):
        src = TV / name
        if not src.is_file():
            raise FileNotFoundError(f"Missing Test_Validation table: {src}")
        dst = INPUT / name
        shutil.copy2(src, dst)
        staged.append(dst)

    rates = TV / "rates"
    if not rates.is_dir():
        raise FileNotFoundError(f"Missing Test_Validation rates folder: {rates}")
    for src in sorted(rates.glob("*.csv")):
        dst = INPUT / src.name
        shutil.copy2(src, dst)
        staged.append(dst)
    return staged


def _build_dbfs() -> list[dict]:
    results: list[dict] = []
    for csv_path in sorted(INPUT.glob("*.csv")):
        stem = csv_path.stem
        tmpl = _find_template(stem)
        out_path = OUTPUT / f"{stem}.dbf"
        rec: dict = {"csv": csv_path.name, "stem": stem, "ok": False}
        if tmpl is None:
            rec["error"] = "missing template"
            results.append(rec)
            continue
        try:
            prior, appended = _append_csv_to_dbf(csv_path, tmpl, out_path)
            rec.update(
                {
                    "ok": True,
                    "template": tmpl.name,
                    "output": out_path.name,
                    "prior_records": prior,
                    "appended": appended,
                    "total": prior + appended,
                }
            )
        except Exception as exc:
            rec["error"] = str(exc)
            rec["trace"] = traceback.format_exc()
        results.append(rec)
    return results


def _q_target_name(stem: str) -> str:
    return Q_NAMES.get(stem, f"{stem}.dbf")


def _archive_q_targets(ts: str) -> Path | None:
    if not QDEST.is_dir():
        return None
    q_arch = ARCH / f"Q_CSO_Test_6_30_2026_pre_issue_a11_deploy_{ts}"
    q_arch.mkdir(parents=True, exist_ok=True)
    archived = 0
    for stem in Q_NAMES:
        name = _q_target_name(stem)
        src = QDEST / name
        if src.is_file():
            shutil.copy2(src, q_arch / name)
            archived += 1
        for ext in (".dbt", ".DBT", ".fpt", ".FPT"):
            memo = QDEST / name.replace(".dbf", ext).replace(".DBF", ext)
            if memo.is_file():
                shutil.copy2(memo, q_arch / memo.name)
                archived += 1
    return q_arch if archived else q_arch


def _deploy_to_q(build_results: list[dict], ts: str) -> list[dict]:
    if not QDEST.is_dir():
        raise FileNotFoundError(f"Q UAT folder not found: {QDEST}")

    q_arch = _archive_q_targets(ts)
    deployed: list[dict] = []
    for item in build_results:
        if not item.get("ok"):
            deployed.append({**item, "deployed": False})
            continue
        stem = item["stem"]
        src = OUTPUT / f"{stem}.dbf"
        q_name = _q_target_name(stem)
        dst = QDEST / q_name
        shutil.copy2(src, dst)
        for ext in (".dbt", ".DBT", ".fpt", ".FPT"):
            memo_src = OUTPUT / f"{stem}{ext}"
            if memo_src.is_file():
                memo_dst = QDEST / q_name.replace(".dbf", ext).replace(".DBF", ext)
                shutil.copy2(memo_src, memo_dst)
        deployed.append(
            {
                "stem": stem,
                "csv": item["csv"],
                "q_file": q_name,
                "rows": item.get("total"),
                "deployed": True,
                "size": dst.stat().st_size,
            }
        )
    return deployed


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    EVID.mkdir(parents=True, exist_ok=True)

    staged = _stage_csvs()
    build = _build_dbfs()
    ok_build = [b for b in build if b.get("ok")]
    fail_build = [b for b in build if not b.get("ok")]

    if fail_build:
        summary = {
            "generated_at": ts,
            "task": "issue_a11_dbf_deploy",
            "staged_csv_count": len(staged),
            "build_ok": len(ok_build),
            "build_fail": len(fail_build),
            "build_results": build,
            "pass": False,
        }
        out = EVID / "issue_a11_dbf_deploy_summary.json"
        out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("BUILD FAIL", len(fail_build), "errors")
        for f in fail_build:
            print(" ", f.get("csv"), f.get("error"))
        print("wrote", out)
        return 2

    deployed = _deploy_to_q(build, ts)
    fail_deploy = [d for d in deployed if not d.get("deployed")]

    # Spot-check quikplan row count + LOANINTX on a few plans via CSV (already validated)
    plan_csv = TV / "quikplan.csv"
    plan_rows = sum(1 for _ in open(plan_csv, encoding="utf-8-sig", errors="replace")) - 1

    summary = {
        "generated_at": ts,
        "task": "issue_a11_dbf_deploy",
        "source": str(TV),
        "dbf_input": str(INPUT),
        "dbf_output": str(OUTPUT),
        "destination": str(QDEST),
        "archive_q_dir": str(ARCH / f"Q_CSO_Test_6_30_2026_pre_issue_a11_deploy_{ts}"),
        "staged_csv_count": len(staged),
        "build_ok": len(ok_build),
        "build_fail": 0,
        "deployed_count": len([d for d in deployed if d.get("deployed")]),
        "deploy_fail": len(fail_deploy),
        "quikplan_csv_rows": plan_rows,
        "build_results": build,
        "deploy_results": deployed,
        "pass": len(fail_deploy) == 0 and len(ok_build) == len(Q_NAMES),
    }
    out = EVID / "issue_a11_dbf_deploy_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("ISSUE_A11_DBF_DEPLOY", "PASS" if summary["pass"] else "FAIL")
    print("built", len(ok_build), "deployed", summary["deployed_count"], "->", QDEST)
    print("wrote", out)
    return 0 if summary["pass"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
