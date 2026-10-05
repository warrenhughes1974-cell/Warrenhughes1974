"""Issue 186 acceptance compare. Read-only. Python 3 standard library only.

Finds every Active + PAID_UP_TYPE=LP policy on the 9/30 LifePRO policy extract,
maps each to the QLAdmin MPOLICY key the converter emits, and compares v59.26
(before) to v59.27 (after) for:

  quikmstr.MSTATUS          policy header
  quikridr.MPHSTAT          coverage phase 1 (MPHASE = 1)
  quikridr.MSAVESTAT        save status on that same phase-1 row

Each results folder may be converter CSV output, DBF_Append_Tool\\input (CSV),
or DBF_Append_Tool\\output (DBF). When a folder has both, the CSV is used.

No client files are written except the report path given with --out.

Exit 0 = PASS, 1 = FAIL, 2 = the inputs could not be read.
"""

from __future__ import annotations

import argparse
import csv
import io
import struct
import sys
import tempfile
from pathlib import Path

PPOLC_NAME = "PPOLC_PolicyMaster_Extract_20260930.csv"
TRACE_POLICY = "9015FG8217"
TRACE_MPOLICY = "9015FG8217C"
MPOLICY_WIDTH = 11

REPORT_FIELDS = [
    "ROW_TYPE",
    "POLICY_NUMBER",
    "MPOLICY",
    "CONTRACT_CODE",
    "CONTRACT_REASON",
    "PAID_UP_TYPE",
    "BEFORE_MSTATUS",
    "AFTER_MSTATUS",
    "BEFORE_MPHSTAT",
    "AFTER_MPHSTAT",
    "BEFORE_MSAVESTAT",
    "AFTER_MSAVESTAT",
    "PHASE1_ROWS_BEFORE",
    "PHASE1_ROWS_AFTER",
    "ROW_RESULT",
    "NOTE",
]


def norm(value) -> str:
    s = "" if value is None else str(value).strip().upper()
    if s.endswith(".0") and s[:-2].replace("-", "").isdigit():
        s = s[:-2]
    if s.lower() in {"NAN", "NONE", "NULL"}:
        return ""
    return s


def norm_status(value) -> str:
    s = norm(value)
    if s.endswith(".00") and s[:-3].isdigit():
        s = s[:-3]
    return s


def qla_mpolicy(policy_number: str) -> str:
    """Issue #2: source POLICY_NUMBER + C, right-justified to 11 characters."""
    core = norm(policy_number)
    if not core or core.startswith("----") or set(core) <= {"-"}:
        return ""
    if len(core) == MPOLICY_WIDTH and core.endswith("C"):
        return core
    core = core + "C"
    if len(core) > MPOLICY_WIDTH:
        return ""
    return core.rjust(MPOLICY_WIDTH)


def policy_key(value: str) -> str:
    """Compare keys with the padding spaces removed."""
    return norm(value)


def _decode_text(raw: bytes) -> str:
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    text = _decode_text(path.read_bytes())
    first = text.splitlines()[0] if text else ""
    delim = ";" if first.count(";") > first.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    rows = []
    for row in reader:
        cleaned = {(k or "").strip().upper(): (v if v is not None else "") for k, v in row.items()}
        probe = next(iter(cleaned.values()), "")
        if "---" in str(probe):
            continue
        rows.append(cleaned)
    return rows


def read_dbf_rows(path: Path) -> list[dict[str, str]]:
    """Minimal dBase III / Visual FoxPro reader. Character and numeric fields only."""
    data = path.read_bytes()
    if len(data) < 32:
        raise ValueError(f"DBF too small: {path}")
    nrec = struct.unpack_from("<I", data, 4)[0]
    header_len = struct.unpack_from("<H", data, 8)[0]
    rec_len = struct.unpack_from("<H", data, 10)[0]
    if header_len < 33 or rec_len < 2 or header_len > len(data):
        raise ValueError(f"DBF header not readable: {path}")
    fields: list[tuple[str, str, int]] = []
    pos = 32
    while pos < header_len and data[pos] != 0x0D:
        if pos + 32 > len(data):
            break
        name = data[pos:pos + 11].split(b"\x00", 1)[0].decode("ascii", "replace").strip().upper()
        ftype = chr(data[pos + 11]).upper()
        flen = data[pos + 16]
        if name and flen:
            fields.append((name, ftype, flen))
        pos += 32
    if not fields:
        raise ValueError(f"DBF has no fields: {path}")
    rows = []
    for i in range(nrec):
        start = header_len + i * rec_len
        rec = data[start:start + rec_len]
        if len(rec) < rec_len or rec[:1] == b"*":
            continue
        offset = 1
        row: dict[str, str] = {}
        for name, _ftype, flen in fields:
            raw = rec[offset:offset + flen]
            offset += flen
            row[name] = raw.decode("latin-1", "replace")
        rows.append(row)
    return rows


def find_table(folder: Path, stem: str) -> tuple[Path, str]:
    if not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")
    csvs = []
    dbfs = []
    for path in folder.iterdir():
        if not path.is_file():
            continue
        if path.stem.lower() != stem:
            continue
        if path.suffix.lower() == ".csv":
            csvs.append(path)
        elif path.suffix.lower() == ".dbf":
            dbfs.append(path)
    if csvs:
        return sorted(csvs)[0], "csv"
    if dbfs:
        return sorted(dbfs)[0], "dbf"
    raise FileNotFoundError(
        f"{stem}.csv or {stem}.dbf not found in {folder} "
        "(quikmstr = header MSTATUS, quikridr = phase-1 MPHSTAT and MSAVESTAT)"
    )


def read_table(path: Path, kind: str) -> list[dict[str, str]]:
    if kind == "csv":
        return read_csv_rows(path)
    return read_dbf_rows(path)


def find_ppolc(source_dir: Path) -> Path:
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source folder not found: {source_dir}")
    matches: list[Path] = []
    for path in source_dir.iterdir():
        if path.is_file() and path.name.lower() == PPOLC_NAME.lower():
            matches.append(path)
        elif path.is_dir():
            for child in path.iterdir():
                if child.is_file() and child.name.lower() == PPOLC_NAME.lower():
                    matches.append(child)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise FileNotFoundError(
            f"{PPOLC_NAME} not found in {source_dir} or one folder under it"
        )
    raise FileNotFoundError(f"More than one {PPOLC_NAME}: {matches}")


def load_active_lp(ppolc: Path) -> list[dict[str, str]]:
    rows = read_csv_rows(ppolc)
    if not rows:
        raise ValueError(f"No rows in {ppolc}")
    needed = {"POLICY_NUMBER", "CONTRACT_CODE", "PAID_UP_TYPE"}
    missing = needed - set(rows[0])
    if missing:
        raise ValueError(f"{ppolc.name} is missing columns {sorted(missing)}")
    found = []
    for row in rows:
        policy = norm(row.get("POLICY_NUMBER", ""))
        code = norm(row.get("CONTRACT_CODE", ""))
        reason = norm(row.get("CONTRACT_REASON", ""))
        put = norm(row.get("PAID_UP_TYPE", ""))
        if not policy or code != "A" or put != "LP":
            continue
        mpolicy = qla_mpolicy(policy)
        if not mpolicy:
            continue
        found.append(
            {
                "POLICY_NUMBER": policy,
                "MPOLICY": policy_key(mpolicy),
                "MPOLICY_PADDED": mpolicy,
                "CONTRACT_CODE": code,
                "CONTRACT_REASON": reason,
                "PAID_UP_TYPE": put,
            }
        )
    found.sort(key=lambda r: r["MPOLICY"])
    return found


def load_header(folder: Path) -> tuple[dict[str, str], str]:
    path, kind = find_table(folder, "quikmstr")
    out: dict[str, str] = {}
    for row in read_table(path, kind):
        key = policy_key(row.get("MPOLICY", ""))
        if not key:
            continue
        out[key] = norm_status(row.get("MSTATUS", ""))
    return out, f"{kind}:{path.name}"


def _phase_is_one(value: str) -> bool:
    s = norm_status(value)
    if not s:
        return False
    try:
        return int(float(s)) == 1
    except ValueError:
        return False


def load_phase1(folder: Path) -> tuple[dict[str, list[tuple[str, str]]], str]:
    path, kind = find_table(folder, "quikridr")
    out: dict[str, list[tuple[str, str]]] = {}
    for row in read_table(path, kind):
        if not _phase_is_one(row.get("MPHASE", "")):
            continue
        key = policy_key(row.get("MPOLICY", ""))
        if not key:
            continue
        out.setdefault(key, []).append(
            (norm_status(row.get("MPHSTAT", "")), norm_status(row.get("MSAVESTAT", "")))
        )
    return out, f"{kind}:{path.name}"


def collapse(values: list[str]) -> str:
    uniq: list[str] = []
    for value in values:
        if value not in uniq:
            uniq.append(value)
    if not uniq:
        return ""
    if len(uniq) == 1:
        return uniq[0]
    return "|".join(uniq)


def phase_pair(rows: list[tuple[str, str]]) -> tuple[str, str, int]:
    if not rows:
        return "", "", 0
    return collapse([a for a, _ in rows]), collapse([b for _, b in rows]), len(rows)


def all_equal(rows: list[tuple[str, str]], status: str, index: int) -> bool:
    return bool(rows) and all(pair[index] == status for pair in rows)


def run_compare(source_dir: Path, before_dir: Path, after_dir: Path, out_path: Path) -> int:
    ppolc = find_ppolc(source_dir)
    cohort = load_active_lp(ppolc)
    before_header, before_header_src = load_header(before_dir)
    after_header, after_header_src = load_header(after_dir)
    before_phase, before_phase_src = load_phase1(before_dir)
    after_phase, after_phase_src = load_phase1(after_dir)

    cohort_keys = {row["MPOLICY"] for row in cohort}
    failures: list[str] = []
    report_rows: list[dict[str, str]] = []
    trace_seen = False

    for row in cohort:
        key = row["MPOLICY"]
        b_phase, b_save, b_n = phase_pair(before_phase.get(key, []))
        a_phase, a_save, a_n = phase_pair(after_phase.get(key, []))
        b_header = before_header.get(key, "")
        a_header = after_header.get(key, "")
        after_ok = (
            a_header == "22"
            and all_equal(after_phase.get(key, []), "22", 0)
            and all_equal(after_phase.get(key, []), "22", 1)
        )
        note = ""
        row_result = "PASS" if after_ok else "FAIL"
        if key == TRACE_MPOLICY:
            trace_seen = True
            moved = (
                b_header == "54"
                and all_equal(before_phase.get(key, []), "54", 0)
                and all_equal(before_phase.get(key, []), "54", 1)
                and after_ok
            )
            if not moved:
                row_result = "FAIL"
                note = "9015FG8217C must move 54 to 22 on header, phase 1, and save status"
            else:
                note = "54 to 22 on header, phase 1, and save status"
        if row_result != "PASS":
            failures.append(f"{key}: after header={a_header or '(blank)'} phase1={a_phase or '(blank)'} save={a_save or '(blank)'}")
        report_rows.append(
            {
                "ROW_TYPE": "ACTIVE_LP",
                "POLICY_NUMBER": row["POLICY_NUMBER"],
                "MPOLICY": key,
                "CONTRACT_CODE": row["CONTRACT_CODE"],
                "CONTRACT_REASON": row["CONTRACT_REASON"],
                "PAID_UP_TYPE": row["PAID_UP_TYPE"],
                "BEFORE_MSTATUS": b_header,
                "AFTER_MSTATUS": a_header,
                "BEFORE_MPHSTAT": b_phase,
                "AFTER_MPHSTAT": a_phase,
                "BEFORE_MSAVESTAT": b_save,
                "AFTER_MSAVESTAT": a_save,
                "PHASE1_ROWS_BEFORE": str(b_n),
                "PHASE1_ROWS_AFTER": str(a_n),
                "ROW_RESULT": row_result,
                "NOTE": note,
            }
        )

    if not trace_seen:
        failures.append(
            f"{TRACE_MPOLICY} is not an Active + LP policy on {ppolc.name}"
        )

    outside_changes = []
    shared = set(before_header) & set(after_header)
    for key in sorted(shared - cohort_keys):
        before = before_header[key]
        after = after_header[key]
        if before == after:
            continue
        outside_changes.append((key, before, after))
        report_rows.append(
            {
                "ROW_TYPE": "HEADER_CHANGE",
                "POLICY_NUMBER": "",
                "MPOLICY": key,
                "CONTRACT_CODE": "",
                "CONTRACT_REASON": "",
                "PAID_UP_TYPE": "",
                "BEFORE_MSTATUS": before,
                "AFTER_MSTATUS": after,
                "BEFORE_MPHSTAT": "",
                "AFTER_MPHSTAT": "",
                "BEFORE_MSAVESTAT": "",
                "AFTER_MSAVESTAT": "",
                "PHASE1_ROWS_BEFORE": "",
                "PHASE1_ROWS_AFTER": "",
                "ROW_RESULT": "FAIL",
                "NOTE": "Header MSTATUS changed and this policy is not Active+LP",
            }
        )
    if outside_changes:
        failures.append(
            f"{len(outside_changes)} policy header(s) outside Active+LP changed MSTATUS"
        )

    only_before = sorted(set(before_header) - set(after_header) - cohort_keys)
    only_after = sorted(set(after_header) - set(before_header) - cohort_keys)
    for key in only_before:
        report_rows.append(
            {
                "ROW_TYPE": "HEADER_ONLY_BEFORE",
                "POLICY_NUMBER": "",
                "MPOLICY": key,
                "CONTRACT_CODE": "",
                "CONTRACT_REASON": "",
                "PAID_UP_TYPE": "",
                "BEFORE_MSTATUS": before_header.get(key, ""),
                "AFTER_MSTATUS": "",
                "BEFORE_MPHSTAT": "",
                "AFTER_MPHSTAT": "",
                "BEFORE_MSAVESTAT": "",
                "AFTER_MSAVESTAT": "",
                "PHASE1_ROWS_BEFORE": "",
                "PHASE1_ROWS_AFTER": "",
                "ROW_RESULT": "INFO",
                "NOTE": "In the before header file only; not scored as a status change",
            }
        )
    for key in only_after:
        report_rows.append(
            {
                "ROW_TYPE": "HEADER_ONLY_AFTER",
                "POLICY_NUMBER": "",
                "MPOLICY": key,
                "CONTRACT_CODE": "",
                "CONTRACT_REASON": "",
                "PAID_UP_TYPE": "",
                "BEFORE_MSTATUS": "",
                "AFTER_MSTATUS": after_header.get(key, ""),
                "BEFORE_MPHSTAT": "",
                "AFTER_MPHSTAT": "",
                "BEFORE_MSAVESTAT": "",
                "AFTER_MSAVESTAT": "",
                "PHASE1_ROWS_BEFORE": "",
                "PHASE1_ROWS_AFTER": "",
                "ROW_RESULT": "INFO",
                "NOTE": "In the after header file only; not scored as a status change",
            }
        )

    passed = not failures
    result = "PASS" if passed else "FAIL"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerow(
            {
                "ROW_TYPE": "SUMMARY",
                "POLICY_NUMBER": "",
                "MPOLICY": "",
                "CONTRACT_CODE": "",
                "CONTRACT_REASON": "",
                "PAID_UP_TYPE": "",
                "BEFORE_MSTATUS": "",
                "AFTER_MSTATUS": "",
                "BEFORE_MPHSTAT": "",
                "AFTER_MPHSTAT": "",
                "BEFORE_MSAVESTAT": "",
                "AFTER_MSAVESTAT": "",
                "PHASE1_ROWS_BEFORE": "",
                "PHASE1_ROWS_AFTER": "",
                "ROW_RESULT": result,
                "NOTE": f"Active+LP count={len(cohort)}; outside header changes={len(outside_changes)}",
            }
        )
        for row in report_rows:
            writer.writerow(row)

    print(f"PPOLC: {ppolc}")
    print(f"Before: header {before_header_src}; phase {before_phase_src}")
    print(f"After:  header {after_header_src}; phase {after_phase_src}")
    print(f"Active+LP policies found: {len(cohort)}")
    print(f"Outside Active+LP header changes: {len(outside_changes)}")
    for key, before, after in outside_changes[:20]:
        print(f"  {key}: {before or '(blank)'} -> {after or '(blank)'}")
    if len(outside_changes) > 20:
        print(f"  ... +{len(outside_changes) - 20} more (see the report)")
    if only_before or only_after:
        print(
            f"Header policies on one side only (not scored): "
            f"before-only {len(only_before)}, after-only {len(only_after)}"
        )
    if not trace_seen:
        print(f"{TRACE_POLICY} / {TRACE_MPOLICY}: not in the Active+LP set")
    else:
        trace = next(r for r in report_rows if r["MPOLICY"] == TRACE_MPOLICY)
        print(
            f"{TRACE_MPOLICY}: header {trace['BEFORE_MSTATUS'] or '(blank)'} -> {trace['AFTER_MSTATUS'] or '(blank)'}; "
            f"phase1 {trace['BEFORE_MPHSTAT'] or '(blank)'} -> {trace['AFTER_MPHSTAT'] or '(blank)'}; "
            f"save {trace['BEFORE_MSAVESTAT'] or '(blank)'} -> {trace['AFTER_MSAVESTAT'] or '(blank)'}"
        )
    if failures:
        print("FAIL")
        for item in failures[:20]:
            print(f"  {item}")
        if len(failures) > 20:
            print(f"  ... +{len(failures) - 20} more")
    else:
        print("PASS")
    print(f"Report: {out_path}")
    return 0 if passed else 1


def _write_dbf(path: Path, fields: list[tuple[str, str, int]], rows: list[dict[str, str]]) -> None:
    desc = bytearray()
    for name, ftype, length in fields:
        slot = bytearray(32)
        raw = name.encode("ascii")[:11]
        slot[0:len(raw)] = raw
        slot[11] = ord(ftype)
        slot[16] = length
        desc += slot
    desc += b"\x0D"
    header_len = 32 + len(desc)
    rec_len = 1 + sum(length for _name, _ftype, length in fields)
    header = bytearray(32)
    header[0] = 0x03
    struct.pack_into("<I", header, 4, len(rows))
    struct.pack_into("<H", header, 8, header_len)
    struct.pack_into("<H", header, 10, rec_len)
    body = bytearray()
    for row in rows:
        rec = bytearray(b" " * rec_len)
        offset = 1
        for name, ftype, length in fields:
            val = str(row.get(name, ""))
            packed = val.rjust(length) if ftype == "N" else val.ljust(length)
            rec[offset:offset + length] = packed.encode("latin-1", "replace")[:length]
            offset += length
        body += rec
    path.write_bytes(bytes(header) + bytes(desc) + bytes(body) + b"\x1A")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def self_check() -> int:
    """Synthetic folders only. No LifePRO extract is read or written."""
    print("issue186_before_after.py --self-check")
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="issue186_") as tmp:
        root = Path(tmp)
        source = root / "source"
        before = root / "before"
        after_csv = root / "after_csv"
        after_dbf = root / "after_dbf"
        bad_after = root / "bad_after"
        for folder in (source, before, after_csv, after_dbf, bad_after):
            folder.mkdir()
        _write_csv(
            source / PPOLC_NAME,
            ["POLICY_NUMBER", "CONTRACT_CODE", "CONTRACT_REASON", "PAID_UP_TYPE", "COMPANY_CODE"],
            [
                {"POLICY_NUMBER": "9015FG8217", "CONTRACT_CODE": "A", "CONTRACT_REASON": "RS", "PAID_UP_TYPE": "LP", "COMPANY_CODE": "03"},
                {"POLICY_NUMBER": "901ML4054", "CONTRACT_CODE": "A", "CONTRACT_REASON": "RS", "PAID_UP_TYPE": "LP", "COMPANY_CODE": "03"},
                {"POLICY_NUMBER": "9010000001", "CONTRACT_CODE": "T", "CONTRACT_REASON": "LP", "PAID_UP_TYPE": "LP", "COMPANY_CODE": "03"},
                {"POLICY_NUMBER": "9010000002", "CONTRACT_CODE": "A", "CONTRACT_REASON": "", "PAID_UP_TYPE": "PU", "COMPANY_CODE": "03"},
                {"POLICY_NUMBER": "-------------", "CONTRACT_CODE": "A", "CONTRACT_REASON": "", "PAID_UP_TYPE": "LP", "COMPANY_CODE": "03"},
            ],
        )
        master_fields = ["MPOLICY", "MSTATUS"]
        rider_fields = ["MPOLICY", "MPHASE", "MPHSTAT", "MSAVESTAT"]
        _write_csv(
            before / "quikmstr.csv",
            master_fields,
            [
                {"MPOLICY": "9015FG8217C", "MSTATUS": "54"},
                {"MPOLICY": " 901ML4054C", "MSTATUS": "22"},
                {"MPOLICY": "9010000001C", "MSTATUS": "54"},
                {"MPOLICY": "9010000002C", "MSTATUS": "41"},
            ],
        )
        _write_csv(
            before / "quikridr.csv",
            rider_fields,
            [
                {"MPOLICY": "9015FG8217C", "MPHASE": "1", "MPHSTAT": "54", "MSAVESTAT": "54"},
                {"MPOLICY": "9015FG8217C", "MPHASE": "2", "MPHSTAT": "99", "MSAVESTAT": "99"},
                {"MPOLICY": " 901ML4054C", "MPHASE": "1", "MPHSTAT": "54", "MSAVESTAT": "54"},
                {"MPOLICY": "9010000001C", "MPHASE": "1", "MPHSTAT": "54", "MSAVESTAT": "54"},
                {"MPOLICY": "9010000002C", "MPHASE": "1", "MPHSTAT": "41", "MSAVESTAT": "41"},
            ],
        )
        _write_csv(
            after_csv / "QUIKMSTR.CSV",
            master_fields,
            [
                {"MPOLICY": "9015FG8217C", "MSTATUS": "22"},
                {"MPOLICY": " 901ML4054C", "MSTATUS": "22"},
                {"MPOLICY": "9010000001C", "MSTATUS": "54"},
                {"MPOLICY": "9010000002C", "MSTATUS": "41"},
            ],
        )
        _write_csv(
            after_csv / "quikridr.csv",
            rider_fields,
            [
                {"MPOLICY": "9015FG8217C", "MPHASE": "1", "MPHSTAT": "22", "MSAVESTAT": "22"},
                {"MPOLICY": "9015FG8217C", "MPHASE": "2", "MPHSTAT": "99", "MSAVESTAT": "99"},
                {"MPOLICY": " 901ML4054C", "MPHASE": "01", "MPHSTAT": "22", "MSAVESTAT": "22"},
                {"MPOLICY": "9010000001C", "MPHASE": "1", "MPHSTAT": "54", "MSAVESTAT": "54"},
                {"MPOLICY": "9010000002C", "MPHASE": "1", "MPHSTAT": "41", "MSAVESTAT": "41"},
            ],
        )
        # DBF copy of the passing after-state, plus a CSV that must lose to the DBF
        # when both exist... the rule is CSV wins. A second folder holds DBF only.
        dbf_fields_m = [("MPOLICY", "C", 11), ("MSTATUS", "C", 2)]
        dbf_fields_r = [
            ("MPOLICY", "C", 11),
            ("MPHASE", "N", 2),
            ("MPHSTAT", "C", 2),
            ("MSAVESTAT", "C", 2),
        ]
        _write_dbf(
            after_dbf / "QUIKMSTR.DBF",
            dbf_fields_m,
            [
                {"MPOLICY": "9015FG8217C", "MSTATUS": "22"},
                {"MPOLICY": " 901ML4054C", "MSTATUS": "22"},
                {"MPOLICY": "9010000001C", "MSTATUS": "54"},
                {"MPOLICY": "9010000002C", "MSTATUS": "41"},
            ],
        )
        _write_dbf(
            after_dbf / "QUIKRIDR.DBF",
            dbf_fields_r,
            [
                {"MPOLICY": "9015FG8217C", "MPHASE": "1", "MPHSTAT": "22", "MSAVESTAT": "22"},
                {"MPOLICY": " 901ML4054C", "MPHASE": "1", "MPHSTAT": "22", "MSAVESTAT": "22"},
                {"MPOLICY": "9010000001C", "MPHASE": "1", "MPHSTAT": "54", "MSAVESTAT": "54"},
                {"MPOLICY": "9010000002C", "MPHASE": "1", "MPHSTAT": "41", "MSAVESTAT": "41"},
            ],
        )
        # Decoy CSV in the DBF folder would be preferred; do not put one here.
        _write_csv(
            bad_after / "quikmstr.csv",
            master_fields,
            [
                {"MPOLICY": "9015FG8217C", "MSTATUS": "54"},
                {"MPOLICY": " 901ML4054C", "MSTATUS": "22"},
                {"MPOLICY": "9010000001C", "MSTATUS": "54"},
                {"MPOLICY": "9010000002C", "MSTATUS": "45"},
            ],
        )
        _write_csv(
            bad_after / "quikridr.csv",
            rider_fields,
            [
                {"MPOLICY": "9015FG8217C", "MPHASE": "1", "MPHSTAT": "54", "MSAVESTAT": "54"},
                {"MPOLICY": " 901ML4054C", "MPHASE": "1", "MPHSTAT": "22", "MSAVESTAT": "22"},
                {"MPOLICY": "9010000001C", "MPHASE": "1", "MPHSTAT": "54", "MSAVESTAT": "54"},
                {"MPOLICY": "9010000002C", "MPHASE": "1", "MPHSTAT": "41", "MSAVESTAT": "41"},
            ],
        )

        good_out = root / "good.csv"
        bad_out = root / "bad.csv"
        dbf_out = root / "dbf.csv"
        code_good = run_compare(source, before, after_csv, good_out)
        code_dbf = run_compare(source, before, after_dbf, dbf_out)
        code_bad = run_compare(source, before, bad_after, bad_out)
        if code_good != 0:
            errors.append(f"passing CSV case returned {code_good}")
        if code_dbf != 0:
            errors.append(f"passing DBF case returned {code_dbf}")
        if code_bad != 1:
            errors.append(f"failing case returned {code_bad}, expected 1")
        good_text = good_out.read_text(encoding="utf-8")
        if "9015FG8217C" not in good_text or "901ML4054C" not in good_text:
            errors.append("report missed a padded or exact MPOLICY")
        if "HEADER_CHANGE" in good_text:
            errors.append("passing case recorded an outside header change")
        bad_text = bad_out.read_text(encoding="utf-8")
        if "9010000002C" not in bad_text or "HEADER_CHANGE" not in bad_text:
            errors.append("failing case did not record the outside header change")
        if "9015FG8217C must move 54 to 22" not in bad_text:
            errors.append("failing case did not flag 9015FG8217C")
        # Deleted DBF row must be ignored.
        deleted = after_dbf / "with_deleted.dbf"
        _write_dbf(
            deleted,
            dbf_fields_m,
            [{"MPOLICY": "9015FG8217C", "MSTATUS": "54"}],
        )
        blob = bytearray(deleted.read_bytes())
        # Flip the single record's delete flag (first byte of the record).
        header_len = struct.unpack_from("<H", blob, 8)[0]
        blob[header_len] = ord("*")
        # Add is not needed; a deleted-only file should yield no rows.
        deleted.write_bytes(blob)
        if read_dbf_rows(deleted):
            errors.append("deleted DBF row was not skipped")

    if errors:
        print("SELF-CHECK FAIL")
        for item in errors:
            print(f"  {item}")
        return 1
    print("SELF-CHECK PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Issue 186 Active+LP before/after compare")
    parser.add_argument("--source-dir", type=Path, help="Folder containing PPOLC_PolicyMaster_Extract_20260930.csv")
    parser.add_argument("--before-dir", type=Path, help="v59.26 quikmstr/quikridr CSV or DBF folder")
    parser.add_argument("--after-dir", type=Path, help="v59.27 quikmstr/quikridr CSV or DBF folder")
    parser.add_argument("--out", type=Path, help="CSV report path to write")
    parser.add_argument("--self-check", action="store_true", help="Run synthetic checks and write nothing permanent")
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    missing = [
        name
        for name, value in (
            ("--source-dir", args.source_dir),
            ("--before-dir", args.before_dir),
            ("--after-dir", args.after_dir),
            ("--out", args.out),
        )
        if value is None
    ]
    if missing:
        parser.error("required: " + ", ".join(missing))
    try:
        return run_compare(args.source_dir, args.before_dir, args.after_dir, args.out)
    except (OSError, ValueError, csv.Error) as exc:
        print(f"FAIL - {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
