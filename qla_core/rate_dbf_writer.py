"""
QLAdmin V5 rate DBF writer (framework) — rollback-safe emit of factor / rate-key tables.

NOT invoked during R5 dry-run. Provided so R5+ emit is a single, audited code path.

Safety model:
  * write to a temp file in the target directory, then atomically replace the target;
  * never mutate an existing DBF in place;
  * caller is responsible for running rate_validation and gating on zero BLOCKERs first.
"""
import os
import tempfile

from qla_core import rate_dbf_schema as S


def _emit(path, fields, rows, overwrite):
    import dbf
    spec = S.dbf_spec(fields)
    order = [f[0] for f in fields]
    date_fields = {f[0] for f in fields if f[1] == "D"}
    logical_fields = {f[0] for f in fields if f[1] == "L"}
    numeric_fields = {f[0] for f in fields if f[1] == "N"}

    target_dir = os.path.dirname(os.path.abspath(path))
    os.makedirs(target_dir, exist_ok=True)
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(f"{path} exists and overwrite=False")

    fd, tmp = tempfile.mkstemp(suffix=".dbf", dir=target_dir)
    os.close(fd)
    os.remove(tmp)  # let dbf create it
    table = dbf.Table(tmp, spec)
    table.open(mode=dbf.READ_WRITE)
    try:
        for row in rows:
            vals = []
            for name in order:
                v = row.get(name, "")
                if name in date_fields:
                    vals.append(_to_date(v))
                elif name in logical_fields:
                    vals.append(_to_logical(v))
                elif name in numeric_fields:
                    vals.append(_to_number(v))
                else:
                    vals.append("" if v is None else str(v))
            table.append(tuple(vals))
    finally:
        table.close()
    os.replace(tmp, path)  # atomic publish
    return len(rows)


def _to_date(v):
    import dbf
    s = (str(v) if v is not None else "").strip()
    if len(s) == 8 and s.isdigit() and s != "00000000":
        return dbf.Date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    return None


def _to_number(v):
    s = (str(v) if v is not None else "").strip()
    if s == "":
        return None  # blank numeric placeholder
    try:
        return float(s)
    except ValueError:
        return None


def _to_logical(v):
    s = (str(v) if v is not None else "").strip().upper()
    if s in ("Y", "T", "TRUE", "1"):
        return True
    if s in ("N", "F", "FALSE", "0"):
        return False
    return None


def write_factor_table(path, table, rows, overwrite=False):
    return _emit(path, S.factor_table_fields(table), rows, overwrite)


def write_key_table(path, key_table, rows, overwrite=False):
    return _emit(path, S.key_table_fields(key_table), rows, overwrite)


def write_member_table(path, member_table, rows, overwrite=False):
    return _emit(path, S.member_table_fields(member_table), rows, overwrite)


def _csv_cell(name, v, field_type):
    if v is None:
        return ""
    if field_type == "L":
        s = str(v).strip().upper()
        if s in ("Y", "T", "TRUE", "1"):
            return "Y"
        if s in ("N", "F", "FALSE", "0"):
            return "N"
        return ""
    return "" if v is None else str(v).strip()


def write_table_csv(path, fields, rows, overwrite=False):
    """Write rate rows to CSV with DBF-matching column order (append-ready for QLAdmin)."""
    import csv

    order = [f[0] for f in fields]
    types = {f[0]: f[1] for f in fields}
    target_dir = os.path.dirname(os.path.abspath(path))
    os.makedirs(target_dir, exist_ok=True)
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(f"{path} exists and overwrite=False")

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=order, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({n: _csv_cell(n, row.get(n, ""), types[n]) for n in order})
    return len(rows)


def write_factor_table_csv(path, table, rows, overwrite=False):
    return write_table_csv(path, S.factor_table_fields(table), rows, overwrite)


def write_key_table_csv(path, key_table, rows, overwrite=False):
    return write_table_csv(path, S.key_table_fields(key_table), rows, overwrite)


def write_member_table_csv(path, member_table, rows, overwrite=False):
    return write_table_csv(path, S.member_table_fields(member_table), rows, overwrite)


def emit_all_rate_tables_csv(
    factor_rows,
    key_rows,
    member_rows,
    output_dir,
    overwrite=True,
):
    """Emit all rate factor/key/member tables as CSV under output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    manifest = []
    for table, rows in factor_rows.items():
        path = os.path.join(output_dir, f"{table}.csv")
        n = write_factor_table_csv(path, table, rows, overwrite=overwrite)
        manifest.append({"kind": "factor", "table": table, "path": path, "rows": n})
    for key_table, rows in key_rows.items():
        path = os.path.join(output_dir, f"{key_table}.csv")
        n = write_key_table_csv(path, key_table, rows, overwrite=overwrite)
        manifest.append({"kind": "key", "table": key_table, "path": path, "rows": n})
    for member_table, rows in member_rows.items():
        path = os.path.join(output_dir, f"{member_table}.csv")
        n = write_member_table_csv(path, member_table, rows, overwrite=overwrite)
        manifest.append({"kind": "member", "table": member_table, "path": path, "rows": n})
    return manifest
