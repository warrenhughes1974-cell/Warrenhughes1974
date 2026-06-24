#!/usr/bin/env python3
"""
Structure-preserving deterministic PII sanitizer for legacy insurance export CSV/DBF.

Isolated utility — does not import or modify app.py.

Design:
  - Default: PRESERVE all fields (especially join keys)
  - Sanitize ONLY PCI/PII fields matched by configurable patterns
  - Preserve file dialect, delimiters, line endings, field width (CSV) or DBF schema
  - Deterministic: same source value -> same sanitized value across files/runs

Configuration: config/field_masking_rules.json (v2)
"""

import argparse
import csv
import fnmatch
import hashlib
import io
import json
import logging
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RULES_PATH = os.path.join(SCRIPT_DIR, "config", "field_masking_rules.json")
SANITIZER_ENGINE_VERSION = "1.2.0"

# dBase/FoxPro DBF version bytes (first byte of file)
_DBF_SIGNATURES = frozenset({
    b"\x03", b"\x30", b"\x31", b"\x32", b"\x43", b"\x63", b"\x83", b"\x8b", b"\xf5",
})

BLANK_TOKENS = {"", "NAN", "NONE", "NULL", "NA", "N/A"}

FIRST_NAMES = (
    "ALEX", "BLAKE", "CASEY", "DREW", "ELLIS", "FINLEY", "GRAY", "HARPER",
    "INDIGO", "JORDAN", "KAI", "LOGAN", "MORGAN", "NOEL", "PARKER", "QUINN",
)
LAST_NAMES = (
    "ABBOTT", "BENNETT", "CARTER", "DALTON", "ELLIS", "FOSTER", "GARCIA", "HAYES",
    "IRVING", "JENKINS", "KELLER", "LAWSON", "MARTIN", "NELSON", "OWENS", "PRATT",
)
STREETS = ("OAK ST", "MAPLE AVE", "PINE RD", "CEDAR LN", "ELM DR", "BIRCH WAY")
CITIES = ("RIVERTON", "LAKEVIEW", "FAIRFIELD", "GREENVILLE", "CLAYTON", "MADISON")

logger = logging.getLogger("sanitize_test_data")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_rules(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def normalize_lookup(val):
    if val is None:
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def is_blank(val):
    return normalize_lookup(val).upper() in BLANK_TOKENS


def digest_index(seed, modulo):
    return int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16) % modulo


def fit_field_width(original, replacement):
    """Pad/truncate replacement to exactly match original field byte length."""
    if original == replacement:
        return original
    olen = len(original)
    if olen == 0:
        return replacement
    if len(replacement) == olen:
        return replacement
    if len(replacement) > olen:
        return replacement[:olen]
    pad = original[-1] if original and original[-1] in (" ", "\t") else " "
    return replacement + (pad * (olen - len(replacement)))


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------

def merge_replace_overrides(rules, runtime_overrides=None):
    """Merge replace values from rules JSON and runtime (GUI/CLI). Runtime wins on duplicate keys."""
    merged = {}
    file_vals = rules.get("replace_overrides") or {}
    if isinstance(file_vals, dict):
        for key, val in file_vals.items():
            if val is not None and str(val).strip() != "":
                merged[str(key)] = str(val)
    if runtime_overrides:
        for key, val in runtime_overrides.items():
            if val is not None and str(val).strip() != "":
                merged[str(key)] = str(val)
    return merged or None


def list_sanitize_patterns(rules):
    """Return sanitize_patterns entries (match + type) for replace UI."""
    return list(rules.get("sanitize_patterns", []))


class RuleEngine:
    """preserve_fields / preserve_patterns always win; then file overrides; then sanitize_patterns."""

    def __init__(self, rules, filename, replace_overrides=None):
        self.filename = filename
        self.defaults = rules.get("defaults", {}).get("unlisted", "PRESERVE")
        self.preserve_fields = [f.upper() for f in rules.get("preserve_fields", [])]
        self.preserve_patterns = [p.upper() for p in rules.get("preserve_patterns", [])]
        self.sanitize_patterns = rules.get("sanitize_patterns", [])
        self.replace_overrides = replace_overrides or {}

        file_cfg = self._get_file_config(rules, filename)
        self.file_fields = {k.upper(): v for k, v in file_cfg.get("fields", {}).items()}
        self.file_preserve_patterns = [
            p.upper() for p in file_cfg.get("preserve_field_patterns", [])
        ]

    def _get_file_config(self, rules, filename):
        exact = rules.get("files", {}).get(filename)
        if exact:
            return exact
        lower = filename.lower()
        for pattern, cfg in rules.get("file_patterns", {}).items():
            if fnmatch.fnmatch(lower, pattern.lower()):
                return cfg
        return {}

    def _matches_any(self, upper, patterns):
        return any(fnmatch.fnmatch(upper, pat) for pat in patterns)

    def resolve(self, field_name):
        upper = str(field_name).strip().upper()

        if upper in self.preserve_fields:
            return {"type": "PRESERVE"}

        if self._matches_any(upper, self.file_preserve_patterns):
            return {"type": "PRESERVE"}

        if upper in self.file_fields:
            return self.file_fields[upper]

        if self._matches_any(upper, self.preserve_patterns):
            return {"type": "PRESERVE"}

        repl = self._lookup_replace(upper)
        if repl is not None:
            return {"type": "REPLACE", "value": repl}

        for entry in self.sanitize_patterns:
            match = entry.get("match", "").upper()
            excludes = [e.upper() for e in entry.get("exclude", [])]
            if excludes and self._matches_any(upper, excludes):
                continue
            if match and fnmatch.fnmatch(upper, match):
                return entry

        return {"type": self.defaults}

    def _lookup_replace(self, upper):
        """Fixed literal for columns matching a replace_overrides pattern (honors sanitize excludes)."""
        if not self.replace_overrides:
            return None
        for pattern, value in self.replace_overrides.items():
            pat = str(pattern).strip().upper()
            if not pat or value is None or str(value).strip() == "":
                continue
            if not fnmatch.fnmatch(upper, pat):
                continue
            for entry in self.sanitize_patterns:
                excludes = [e.upper() for e in entry.get("exclude", [])]
                if not excludes or not self._matches_any(upper, excludes):
                    continue
                sanitize_match = entry.get("match", "").upper()
                if sanitize_match and fnmatch.fnmatch(upper, sanitize_match):
                    break
                if fnmatch.fnmatch(upper, pat):
                    break
            else:
                return str(value)
                continue
            # excluded field for a sanitize rule that also matches this column
            continue
        return None


# ---------------------------------------------------------------------------
# Deterministic PII registry (MASK / FAKE only)
# ---------------------------------------------------------------------------

class PiiRegistry:
    def __init__(self, salt):
        self.salt = salt
        self._cache = {}

    def _seed(self, category, value):
        return f"{self.salt}|{category}|{normalize_lookup(value)}"

    def fake_core(self, value, kind):
        if is_blank(value):
            return value
        key = (kind, normalize_lookup(value))
        if key in self._cache:
            return self._cache[key]

        seed = self._seed(kind, value)
        if kind == "first":
            token = FIRST_NAMES[digest_index(seed, len(FIRST_NAMES))]
        elif kind == "last":
            token = LAST_NAMES[digest_index(seed, len(LAST_NAMES))]
        elif kind == "street":
            num = digest_index(seed + ":n", 9000) + 100
            token = f"{num} {STREETS[digest_index(seed + ':s', len(STREETS))]}"
        elif kind == "city":
            token = CITIES[digest_index(seed, len(CITIES))]
        else:
            token = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12].upper()

        self._cache[key] = token
        return token

    def stats(self):
        return {"mapped_pii_values": len(self._cache)}


# ---------------------------------------------------------------------------
# Width-preserving transforms
# ---------------------------------------------------------------------------

def mask_preserving(value, style):
    if is_blank(value):
        return value

    chars = list(value)
    if style == "ssn":
        digit_idx = [i for i, c in enumerate(chars) if c.isdigit()]
        for i in digit_idx[:-4]:
            chars[i] = "X"
        return "".join(chars)

    if style == "phone":
        digit_idx = [i for i, c in enumerate(chars) if c.isdigit()]
        for i in digit_idx[:-4]:
            chars[i] = "X"
        return "".join(chars)

    if style == "email":
        at = value.find("@")
        if at > 0:
            local = list(value[:at])
            domain = value[at:]
            for i in range(len(local)):
                if local[i] not in (" ",):
                    local[i] = "x"
            return "".join(local) + domain
        for i, c in enumerate(chars):
            if c not in ("@", " ", ".", "-", "_") and not c.isdigit():
                chars[i] = "x"
        return "".join(chars)

    if style == "account":
        digit_idx = [i for i, c in enumerate(chars) if c.isdigit()]
        for i in digit_idx[:-4]:
            chars[i] = "X"
        return "".join(chars)

    return value


def apply_transform(original, rule, registry):
    mtype = rule.get("type", "PRESERVE").upper()
    if mtype == "PRESERVE" or is_blank(original):
        return original

    if mtype == "MASK":
        masked = mask_preserving(original, rule.get("style", "ssn"))
        return fit_field_width(original, masked)

    if mtype == "FAKE":
        fake = registry.fake_core(original, rule.get("kind", "first"))
        return fit_field_width(original, fake)

    if mtype == "REPLACE":
        return fit_field_width(original, str(rule.get("value", "")))

    return original


# ---------------------------------------------------------------------------
# Structure-preserving CSV I/O
# ---------------------------------------------------------------------------

def read_raw_lines(path):
    with open(path, "rb") as f:
        data = f.read()
    if not data:
        return [], "\n"
    if b"\r\n" in data:
        term = "\r\n"
        parts = data.split(b"\r\n")
    else:
        term = "\n"
        parts = data.split(b"\n")
    if parts and parts[-1] == b"":
        parts.pop()
    return [p.decode("latin1") for p in parts], term


def detect_delimiter(line):
    tabs = line.count("\t")
    commas = line.count(",")
    if tabs > commas:
        return "\t"
    return ","


def build_dialect(sample_line, delimiter):
    try:
        dialect = csv.Sniffer().sniff(sample_line, delimiters=",\t")
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = delimiter
    dialect.delimiter = delimiter
    dialect.skipinitialspace = False
    return dialect


def parse_csv_line(line, dialect):
    return next(csv.reader([line], dialect=dialect))


def serialize_csv_row(fields, dialect, lineterminator):
    buf = io.StringIO()
    writer = csv.writer(
        buf,
        delimiter=dialect.delimiter,
        quotechar=dialect.quotechar,
        quoting=dialect.quoting,
        doublequote=True,
        escapechar=dialect.escapechar,
        lineterminator="",
    )
    writer.writerow(fields)
    return buf.getvalue()


def copy_file_exact(input_path, output_path):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(input_path, "rb") as f_in, open(output_path, "wb") as f_out:
        f_out.write(f_in.read())


def _file_extension(path):
    return os.path.splitext(path)[1].lower()


def _is_dbf_binary(path):
    """True when file content looks like a DBF table (not CSV text)."""
    try:
        with open(path, "rb") as f:
            return f.read(1) in _DBF_SIGNATURES
    except OSError:
        return False


def _resolve_file_kind(path):
    """Return 'dbf', 'csv', or 'unknown' using extension and file signature."""
    ext = _file_extension(path)
    if ext == ".dbf" or _is_dbf_binary(path):
        return "dbf"
    if ext == ".csv":
        return "csv"
    if ext in (".txt", ".tsv"):
        return "csv"
    return "unknown"


def engine_capabilities():
    """Feature flags for GUI / deployment checks."""
    try:
        import dbf  # noqa: F401
        dbf_installed = True
    except ImportError:
        dbf_installed = False
    return {
        "engine_version": SANITIZER_ENGINE_VERSION,
        "dbf_support": dbf_installed,
        "script_path": os.path.abspath(__file__),
    }


def _skip_file_result(fname, action, extra=None):
    result = {
        "file": fname,
        "action": action,
        "rows_in": 0,
        "rows_out": 0,
        "columns": 0,
        "format": extra.get("format", "n/a") if extra else "n/a",
        "dialect": "n/a",
        "line_ending": "n/a",
        "sanitized_counts": Counter(),
        "preserved_counts": Counter(),
        "warnings": [],
    }
    if extra:
        result.update(extra)
    return result


def copy_dbf_sidecars(input_path, output_path):
    """Copy memo/index sidecars when present (binary copy)."""
    base_in = os.path.splitext(input_path)[0]
    base_out = os.path.splitext(output_path)[0]
    for suffix in (".fpt", ".FPT", ".cdx", ".CDX", ".ndx", ".NDX"):
        src = base_in + suffix
        if os.path.isfile(src):
            copy_file_exact(src, base_out + suffix)


def _parse_dbf_field_structure(structure):
    """Parse dbf.structure() lines like 'MFNAME C(20)' into metadata."""
    fields = []
    for line in structure:
        line = str(line).strip()
        parts = line.split(maxsplit=1)
        name = parts[0]
        type_part = parts[1] if len(parts) > 1 else "C"
        ftype = type_part[0].upper()
        width = 0
        match = re.search(r"C\((\d+)\)", type_part, re.IGNORECASE)
        if match:
            width = int(match.group(1))
        fields.append({"name": name, "ftype": ftype, "width": width})
    return fields


def _dbf_char_original(value, width):
    """Normalize character field to fixed width for transform + write-back."""
    text = "" if value is None else str(value)
    if width <= 0:
        return text
    if len(text) >= width:
        return text[:width]
    return text + (" " * (width - len(text)))


def sanitize_dbf_structure(input_path, output_path, rules, registry, replace_overrides=None):
    try:
        import dbf
    except ImportError as exc:
        raise RuntimeError(
            "DBF support requires the 'dbf' package. From the QLA_Data_Sanitizer folder run: "
            "pip install -r requirements.txt"
        ) from exc

    fname = os.path.basename(input_path)
    tmp_path = None
    skip_files = {s.lower() for s in rules.get("skip_files", [])}
    if fname.lower() in skip_files:
        copy_file_exact(input_path, output_path)
        copy_dbf_sidecars(input_path, output_path)
        return _skip_file_result(fname, "SKIPPED_COPY", {"format": "dbf"})

    src = dbf.Table(input_path)
    src.open(mode=dbf.READ_ONLY)
    try:
        structure = src.structure()
        if not structure:
            copy_file_exact(input_path, output_path)
            return _skip_file_result(fname, "EMPTY_COPY", {"format": "dbf"})

        field_meta = _parse_dbf_field_structure(structure)
        names = [f["name"] for f in field_meta]
        engine = RuleEngine(rules, fname, replace_overrides)
        column_rules = [engine.resolve(name) for name in names]

        sanitized_counts = Counter()
        preserved_counts = Counter()
        warnings = []

        out_dir = os.path.dirname(os.path.abspath(output_path)) or "."
        os.makedirs(out_dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(suffix=".dbf", dir=out_dir)
        os.close(fd)
        os.remove(tmp_path)

        dst = dbf.Table(tmp_path, structure)
        dst.open(mode=dbf.READ_WRITE)

        rows_in = 0
        try:
            for rec in src:
                rows_in += 1
                row = list(rec)
                for idx, meta in enumerate(field_meta):
                    if meta["ftype"] != "C":
                        continue

                    original = _dbf_char_original(row[idx], meta["width"])
                    rule = column_rules[idx]
                    mtype = rule.get("type", "PRESERVE").upper()
                    col = names[idx]

                    if mtype == "PRESERVE":
                        preserved_counts[col] += 1
                        continue

                    replacement = apply_transform(original, rule, registry)
                    if replacement != original:
                        row[idx] = replacement
                        sanitized_counts[col] += 1
                    else:
                        preserved_counts[col] += 1

                try:
                    dst.append(tuple(row))
                except Exception as exc:
                    warnings.append(f"row {rows_in}: append failed ({exc})")
                    raise

            rows_out = len(dst)
        finally:
            dst.close()

        if rows_in != rows_out:
            raise RuntimeError(f"Row count mismatch in {fname}: {rows_in} -> {rows_out}")

        if os.path.exists(output_path):
            os.remove(output_path)
        os.replace(tmp_path, output_path)
        copy_dbf_sidecars(input_path, output_path)

        codepage_label = str(getattr(src, "codepage", "default"))
        return {
            "file": fname,
            "action": "SANITIZED",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "columns": len(names),
            "format": "dbf",
            "dialect": f"dbf fields={len(names)} codepage={codepage_label}",
            "line_ending": "n/a",
            "sanitized_counts": sanitized_counts,
            "preserved_counts": preserved_counts,
            "warnings": warnings,
        }
    finally:
        src.close()
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def sanitize_csv_structure(input_path, output_path, rules, registry, replace_overrides=None):
    if _is_dbf_binary(input_path):
        raise RuntimeError(
            f"{os.path.basename(input_path)} is a DBF file, not CSV. "
            "Use sanitize_test_data.py v1.1+ (engine 1.1.0) with a .dbf extension, or run: "
            "pip install -r requirements.txt"
        )

    fname = os.path.basename(input_path)
    skip_files = {s.lower() for s in rules.get("skip_files", [])}
    if fname.lower() in skip_files:
        copy_file_exact(input_path, output_path)
        return _skip_file_result(fname, "SKIPPED_COPY", {"format": "csv"})

    lines, lineterminator = read_raw_lines(input_path)
    if not lines:
        copy_file_exact(input_path, output_path)
        return _skip_file_result(
            fname,
            "EMPTY_COPY",
            {"format": "csv", "dialect": "empty", "line_ending": repr(lineterminator)},
        )

    header_line = lines[0]
    delimiter = detect_delimiter(header_line)
    dialect = build_dialect(header_line, delimiter)
    header = parse_csv_line(header_line, dialect)
    engine = RuleEngine(rules, fname, replace_overrides)

    column_rules = [engine.resolve(col) for col in header]
    sanitized_counts = Counter()
    preserved_counts = Counter()
    warnings = []

    out_lines = [header_line]
    data_rows_in = 0

    for line in lines[1:]:
        if line == "":
            continue
        data_rows_in += 1
        try:
            fields = parse_csv_line(line, dialect)
        except Exception as exc:
            warnings.append(f"row {data_rows_in + 1}: parse failed ({exc}); copied raw")
            out_lines.append(line)
            continue

        changed = False
        new_fields = list(fields)
        while len(new_fields) < len(header):
            new_fields.append("")

        for idx, col in enumerate(header):
            if idx >= len(new_fields):
                break
            original = new_fields[idx]
            rule = column_rules[idx]
            mtype = rule.get("type", "PRESERVE").upper()
            if mtype == "PRESERVE":
                preserved_counts[col] += 1
                continue
            replacement = apply_transform(original, rule, registry)
            if replacement != original:
                new_fields[idx] = replacement
                sanitized_counts[col] += 1
                changed = True
            else:
                preserved_counts[col] += 1

        if changed:
            out_lines.append(serialize_csv_row(new_fields[: len(header)], dialect, lineterminator))
        else:
            out_lines.append(line)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        for i, line in enumerate(out_lines):
            f.write(line.encode("latin1"))
            if i < len(out_lines) - 1:
                f.write(lineterminator.encode("latin1"))

    return {
        "file": fname,
        "action": "SANITIZED",
        "rows_in": data_rows_in,
        "rows_out": data_rows_in,
        "columns": len(header),
        "format": "csv",
        "dialect": f"delim={repr(delimiter)} quote={repr(dialect.quotechar)}",
        "line_ending": repr(lineterminator),
        "sanitized_counts": sanitized_counts,
        "preserved_counts": preserved_counts,
        "warnings": warnings,
    }


def sanitize_file_structure(input_path, output_path, rules, registry, replace_overrides=None):
    """Route to CSV or DBF sanitizer by extension and file signature."""
    merged_replace = merge_replace_overrides(rules, replace_overrides)
    kind = _resolve_file_kind(input_path)
    if kind == "dbf":
        return sanitize_dbf_structure(input_path, output_path, rules, registry, merged_replace)
    if kind == "csv":
        return sanitize_csv_structure(input_path, output_path, rules, registry, merged_replace)
    ext = _file_extension(input_path)
    copy_file_exact(input_path, output_path)
    return _skip_file_result(
        os.path.basename(input_path),
        "SKIPPED_COPY",
        {"format": ext or "unknown"},
    )


# ---------------------------------------------------------------------------
# Batch + audit
# ---------------------------------------------------------------------------

def discover_files(input_dir, patterns):
    found = []
    for name in sorted(os.listdir(input_dir)):
        lower = name.lower()
        if not any(fnmatch.fnmatch(lower, pattern.lower()) for pattern in patterns):
            continue
        found.append(os.path.join(input_dir, name))
    return found


def resolve_output_path(input_path, input_root, output_root):
    return os.path.join(output_root, os.path.relpath(input_path, input_root))


def run_batch(input_dir, output_dir, rules_path, patterns, replace_overrides=None):
    rules = load_rules(rules_path)
    registry = PiiRegistry(rules.get("salt", "qla-enterprise-test-salt-v2"))
    merged_replace = merge_replace_overrides(rules, replace_overrides)
    files = discover_files(input_dir, patterns)
    if not files:
        raise FileNotFoundError(f"No files matched patterns {patterns!r} in: {input_dir}")

    results = []
    for path in files:
        out = resolve_output_path(path, input_dir, output_dir)
        logger.info("Processing: %s", os.path.basename(path))
        results.append(sanitize_file_structure(path, out, rules, registry, merged_replace))

    for r in results:
        if r["action"] == "SANITIZED" and r["rows_in"] != r["rows_out"]:
            raise RuntimeError(f"Row count mismatch in {r['file']}: {r['rows_in']} -> {r['rows_out']}")

    stats = registry.stats()
    if merged_replace:
        stats["replace_mode"] = True
        stats["replace_overrides"] = dict(merged_replace)
    return results, stats


def write_audit_log(output_dir, results, registry_stats, rules_path):
    log_path = os.path.join(output_dir, "Sanitization_Audit_Log.txt")
    total_sanitized = Counter()
    total_preserved = 0
    total_warnings = 0

    lines = [
        "=== QLAdmin Structure-Preserving Sanitization Audit ===",
        f"Rules: {os.path.abspath(rules_path)}",
        f"Mapped PII values: {registry_stats.get('mapped_pii_values', 0)}",
        "",
    ]
    if registry_stats.get("replace_mode"):
        lines.append("Replace mode: ENABLED (fixed literals instead of MASK/FAKE)")
        for pat, val in sorted(registry_stats.get("replace_overrides", {}).items()):
            lines.append(f"  {pat} -> {val!r}")
        lines.append("")

    for r in results:
        lines.append(f"File: {r['file']}")
        lines.append(f"  Action: {r['action']}")
        lines.append(f"  Rows: {r['rows_in']} (preserved count)")
        lines.append(f"  Columns: {r['columns']}")
        lines.append(f"  Format: {r.get('format', 'n/a')}")
        lines.append(f"  Dialect: {r.get('dialect', 'n/a')}")
        lines.append(f"  Line ending: {r.get('line_ending', 'n/a')}")

        if r.get("sanitized_counts"):
            lines.append("  Sanitized fields:")
            for field, count in sorted(r["sanitized_counts"].items()):
                lines.append(f"    {field}: {count}")
                total_sanitized[field] += count

        if r.get("preserved_counts"):
            preserved_sum = sum(r["preserved_counts"].values())
            total_preserved += preserved_sum
            lines.append(f"  Preserved field assignments: {preserved_sum}")

        if r.get("warnings"):
            total_warnings += len(r["warnings"])
            lines.append("  Warnings:")
            for w in r["warnings"][:10]:
                lines.append(f"    {w}")

        lines.append("")

    lines.extend([
        "=== Summary ===",
        f"Files processed: {len(results)}",
        f"Total sanitized field assignments: {sum(total_sanitized.values())}",
        f"Total preserved field assignments: {total_preserved}",
        f"Total warnings: {total_warnings}",
    ])

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return log_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Structure-preserving PII sanitizer for legacy insurance export CSV/DBF.",
    )
    parser.add_argument("--input", help="Single input CSV or DBF file")
    parser.add_argument("--output", help="Single output CSV or DBF file")
    parser.add_argument("--input-dir", help="Batch input directory")
    parser.add_argument("--output-dir", help="Batch output directory")
    parser.add_argument("--rules", default=DEFAULT_RULES_PATH, help="field_masking_rules.json path")
    parser.add_argument(
        "--patterns",
        default="*.csv,*.dbf",
        help="Comma-separated filename patterns for batch mode",
    )
    parser.add_argument(
        "--replace-config",
        help="JSON file with replace_overrides (pattern -> literal value)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    try:
        rules = load_rules(args.rules)
        cli_replace = None
        if args.replace_config:
            with open(args.replace_config, encoding="utf-8") as f:
                cfg = json.load(f)
            cli_replace = cfg.get("replace_overrides", cfg)

        if args.input and args.output:
            registry = PiiRegistry(rules.get("salt", "qla-enterprise-test-salt-v2"))
            result = sanitize_file_structure(args.input, args.output, rules, registry, cli_replace)
            print(f"{result['file']}: action={result['action']} rows={result['rows_in']}")
            if result.get("sanitized_counts"):
                print("Sanitized:", dict(result["sanitized_counts"]))
            merged = merge_replace_overrides(rules, cli_replace)
            if merged:
                print("Replace mode:", merged)
            print(f"Mapped PII values: {registry.stats()['mapped_pii_values']}")
            return 0

        if args.input_dir and args.output_dir:
            patterns = [p.strip() for p in args.patterns.split(",") if p.strip()]
            results, stats = run_batch(
                os.path.abspath(args.input_dir),
                os.path.abspath(args.output_dir),
                args.rules,
                patterns,
                cli_replace,
            )
            log_path = write_audit_log(args.output_dir, results, stats, args.rules)
            print(f"Processed {len(results)} file(s). Audit log: {log_path}")
            print(f"Mapped PII values: {stats['mapped_pii_values']}")
            return 0

        parser.error("Provide --input/--output or --input-dir/--output-dir")

    except (FileNotFoundError, RuntimeError, json.JSONDecodeError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
