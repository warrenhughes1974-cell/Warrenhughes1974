#!/usr/bin/env python3
"""
Enterprise post-conversion validator for QLAdmin migration output CSVs.

Isolated read-only utility — does not import or modify app.py.

Validation categories:
  1. Schema validation (column presence, order, extras)
  2. Blank critical field detection (config-driven)
  3. Invalid date detection
  4. Duplicate key detection
  5. Regression comparison (optional baseline)
  6. Priority go-live checks (priority_rules.json — 25-check set)

Configuration: validation_config/*.json (override with --config-dir)
Priority checklist: validation_config/priority_validation_checks.txt
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_DATE = "19000101"
BLANK_TOKENS = {"", "NAN", "NONE", "NULL", "NA", "N/A"}
DEFAULT_SAMPLE_LIMIT = 10
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_DIR = os.path.join(SCRIPT_DIR, "validation_config")

CATEGORIES = ("schema", "critical", "dates", "duplicates", "regression", "priority")

logger = logging.getLogger("validate_output")


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_json_config(path, label):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {label} config: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_all_config(config_dir):
    cfg = {
        "schema": load_json_config(os.path.join(config_dir, "schema_manifest.json"), "schema"),
        "critical": load_json_config(os.path.join(config_dir, "critical_fields.json"), "critical fields"),
        "dates": load_json_config(os.path.join(config_dir, "date_fields.json"), "date fields"),
        "keys": load_json_config(os.path.join(config_dir, "key_definitions.json"), "key definitions"),
    }
    priority_path = os.path.join(config_dir, "priority_rules.json")
    if os.path.isfile(priority_path):
        with open(priority_path, encoding="utf-8") as fh:
            cfg["priority"] = json.load(fh)
    else:
        cfg["priority"] = {}
    return cfg


# ---------------------------------------------------------------------------
# Core I/O helpers
# ---------------------------------------------------------------------------

def normalize(val):
    if val is None:
        return ""
    s = str(val).strip().upper()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def is_blank(val, extra_blank=None):
    tokens = BLANK_TOKENS if not extra_blank else BLANK_TOKENS | {normalize(v) for v in extra_blank}
    return normalize(val) in tokens


def read_csv_table(path):
    with open(path, newline="", encoding="latin1") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return [], []
        fieldnames = [str(c).strip() for c in reader.fieldnames]
        reader.fieldnames = fieldnames
        rows = list(reader)
    return fieldnames, rows


def discover_output_files(output_dir):
    if not os.path.isdir(output_dir):
        raise FileNotFoundError(f"Output directory not found: {output_dir}")
    return sorted(
        os.path.join(output_dir, name)
        for name in os.listdir(output_dir)
        if name.lower().endswith(".csv") and name.lower().startswith("quik")
    )


def table_name_from_path(path):
    return os.path.splitext(os.path.basename(path))[0].lower()


def field_lookup(fieldnames):
    return {f.upper(): f for f in fieldnames}


def make_finding(category, severity, table, message, row=None, field=None, context=None):
    return {
        "category": category,
        "severity": severity,
        "table": table,
        "message": message,
        "row": row,
        "field": field,
        "context": context or {},
    }


def make_priority_finding(validation_id, severity, table, message, row=None, field=None, context=None):
    ctx = dict(context or {})
    ctx["validation_id"] = validation_id
    return make_finding("priority", severity, table, f"[{validation_id}] {message}", row=row, field=field, context=ctx)


def apply_sample_limit(findings, sample_limit):
    counts = Counter(f["category"] for f in findings)
    shown = Counter()
    limited = []
    for f in findings:
        cat = f["category"]
        if shown[cat] < sample_limit:
            limited.append(f)
            shown[cat] += 1
    truncated = {cat: counts[cat] > sample_limit for cat in counts}
    return limited, counts, truncated


# ---------------------------------------------------------------------------
# Category 1: Schema validation
# ---------------------------------------------------------------------------

def check_schema(table, fieldnames, schema_cfg):
    findings = []
    if table not in schema_cfg:
        return findings

    expected = schema_cfg[table]["columns"]
    strict_order = schema_cfg[table].get("strict_order", True)
    actual_upper = [f.upper() for f in fieldnames]
    expected_upper = [c.upper() for c in expected]

    for col in expected_upper:
        if col not in actual_upper:
            findings.append(make_finding(
                "schema", "ERROR", table,
                f"Missing required column: {col}",
                field=col,
            ))

    for col in actual_upper:
        if col not in expected_upper:
            findings.append(make_finding(
                "schema", "WARN", table,
                f"Unexpected extra column: {col}",
                field=col,
            ))

    if strict_order and actual_upper[: len(expected_upper)] != expected_upper:
        findings.append(make_finding(
            "schema", "ERROR", table,
            "Column order mismatch vs schema manifest",
            context={"expected_head": expected[:5], "actual_head": fieldnames[:5]},
        ))

    return findings


# ---------------------------------------------------------------------------
# Category 2: Critical field validation
# ---------------------------------------------------------------------------

def check_critical_fields(table, fieldnames, rows, critical_cfg):
    findings = []
    rules = critical_cfg.get(table, [])
    if not rules:
        return findings

    lookup = field_lookup(fieldnames)
    for rule in rules:
        field = rule["field"].upper()
        if field not in lookup:
            continue
        col = lookup[field]
        blank_if = rule.get("blank_if")
        severity = rule.get("severity", "ERROR")
        for idx, row in enumerate(rows, start=2):
            val = row.get(col, "")
            if is_blank(val, extra_blank=blank_if):
                ctx = {}
                if "MPOLICY" in lookup:
                    ctx["MPOLICY"] = row.get(lookup["MPOLICY"], "")
                if table == "quikclid" and "MRELATION" in lookup:
                    ctx["MRELATION"] = row.get(lookup["MRELATION"], "")
                findings.append(make_finding(
                    "critical", severity, table,
                    f"Blank critical field: {field}",
                    row=idx, field=field, context=ctx,
                ))
    return findings


# ---------------------------------------------------------------------------
# Category 3: Date validation
# ---------------------------------------------------------------------------

def validate_date_value(val):
    if is_blank(val):
        return None
    raw = str(val).strip()
    digits = re.sub(r"[^0-9]", "", raw)
    if len(digits) == 8:
        if digits < MIN_DATE:
            return f"before {MIN_DATE}"
        try:
            datetime.strptime(digits, "%Y%m%d")
            return True
        except ValueError:
            return "invalid YYYYMMDD calendar date"
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            parsed = datetime.strptime(raw, fmt)
            if parsed.strftime("%Y%m%d") < MIN_DATE:
                return f"before {MIN_DATE}"
            return True
        except ValueError:
            continue
    return f"unrecognized date format ({raw!r})"


def resolve_date_columns(table, fieldnames, date_cfg):
    exclusions = {c.upper() for c in date_cfg.get("global_exclusions", [])}
    configured = [c.upper() for c in date_cfg.get("by_table", {}).get(table, [])]
    if configured:
        return [f for f in fieldnames if f.upper() in configured]
    cols = []
    for f in fieldnames:
        n = f.upper()
        if n in exclusions:
            continue
        if "DATE" in n or "DOB" in n or n.endswith("DT") or n in ("MPAIDTO", "MBILLTO"):
            cols.append(f)
    return cols


def check_dates(table, fieldnames, rows, date_cfg):
    findings = []
    for col in resolve_date_columns(table, fieldnames, date_cfg):
        for idx, row in enumerate(rows, start=2):
            val = row.get(col, "")
            result = validate_date_value(val)
            if result is not True and result is not None:
                findings.append(make_finding(
                    "dates", "ERROR", table,
                    f"Invalid date in {col}: {result}",
                    row=idx, field=col,
                    context={"value": val},
                ))
    return findings


# ---------------------------------------------------------------------------
# Category 4: Duplicate key validation
# ---------------------------------------------------------------------------

def check_duplicate_keys(table, fieldnames, rows, key_cfg):
    findings = []
    definitions = key_cfg.get(table, [])
    if not definitions:
        return findings

    lookup = field_lookup(fieldnames)
    for definition in definitions:
        key_name = definition["name"]
        fields = definition["fields"]
        severity = definition.get("severity", "ERROR")
        cols = []
        for f in fields:
            fu = f.upper()
            if fu not in lookup:
                cols = None
                break
            cols.append(lookup[fu])
        if not cols:
            continue

        seen = defaultdict(list)
        for idx, row in enumerate(rows, start=2):
            key = tuple(normalize(row.get(c, "")) for c in cols)
            if all(not part for part in key):
                continue
            seen[key].append(idx)

        for key, row_nums in seen.items():
            if len(row_nums) > 1:
                findings.append(make_finding(
                    "duplicates", severity, table,
                    f"Duplicate key '{key_name}': {dict(zip(fields, key))}",
                    context={"rows": row_nums, "count": len(row_nums), "key_name": key_name},
                ))
    return findings


# ---------------------------------------------------------------------------
# Category 5: Regression comparison
# ---------------------------------------------------------------------------

def build_table_metrics(table, fieldnames, findings):
    metrics = {
        "row_count": 0,
        "schema_errors": 0,
        "critical_errors": 0,
        "invalid_dates": 0,
        "duplicate_keys": 0,
        "blank_mridrid": 0,
        "missing_mphase": 0,
    }
    for f in findings:
        if f["category"] == "schema" and f["severity"] == "ERROR":
            metrics["schema_errors"] += 1
        elif f["category"] == "critical" and f["severity"] == "ERROR":
            metrics["critical_errors"] += 1
            if f.get("field") == "MRIDRID":
                metrics["blank_mridrid"] += 1
            if f.get("field") == "MPHASE":
                metrics["missing_mphase"] += 1
        elif f["category"] == "dates":
            metrics["invalid_dates"] += 1
        elif f["category"] == "duplicates":
            metrics["duplicate_keys"] += 1
    metrics["column_signature"] = "|".join(f.upper() for f in fieldnames)
    return metrics


def write_baseline(path, label, table_results):
    payload = {
        "label": label,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tables": {},
    }
    for result in table_results:
        payload["tables"][result["table"]] = {
            "row_count": result["row_count"],
            "metrics": result["metrics"],
        }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    logger.info("Baseline written: %s", path)


def load_baseline(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_regression(table, metrics, row_count, baseline_data, strict=False):
    findings = []
    base_tables = baseline_data.get("tables", {})
    if table not in base_tables:
        findings.append(make_finding(
            "regression", "WARN", table,
            f"No baseline entry for table '{table}'",
        ))
        return findings

    base = base_tables[table]
    base_metrics = base.get("metrics", {})
    base_count = base.get("row_count", 0)

    if row_count != base_count:
        severity = "ERROR" if strict else "WARN"
        findings.append(make_finding(
            "regression", severity, table,
            f"Row count changed: baseline={base_count} current={row_count}",
            context={"delta": row_count - base_count},
        ))

    for metric in ("blank_mridrid", "missing_mphase", "invalid_dates", "duplicate_keys", "critical_errors"):
        current = metrics.get(metric, 0)
        previous = base_metrics.get(metric, 0)
        if current > previous:
            findings.append(make_finding(
                "regression", "ERROR", table,
                f"Metric regression '{metric}': baseline={previous} current={current}",
                context={"delta": current - previous},
            ))

    base_sig = base_metrics.get("column_signature", "")
    current_sig = metrics.get("column_signature", "")
    if base_sig and current_sig and base_sig != current_sig:
        findings.append(make_finding(
            "regression", "ERROR", table,
            "Column signature changed vs baseline",
        ))

    return findings


# ---------------------------------------------------------------------------
# Category 6: Priority go-live checks (priority_rules.json)
# ---------------------------------------------------------------------------

def date_to_yyyymmdd(val):
    """Return YYYYMMDD string or None if unparseable/blank."""
    if is_blank(val):
        return None
    raw = str(val).strip()
    digits = re.sub(r"[^0-9]", "", raw)
    if len(digits) == 8:
        try:
            datetime.strptime(digits, "%Y%m%d")
            return digits
        except ValueError:
            return None
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw[:10], fmt).strftime("%Y%m%d")
        except ValueError:
            continue
    return None


def _table_data(tables, name):
    if name not in tables:
        return None, []
    return tables[name]["fieldnames"], tables[name]["rows"]


def _key_set(rows, lookup, field):
    fu = field.upper()
    if fu not in lookup:
        return set()
    col = lookup[fu]
    return {normalize(row.get(col, "")) for row in rows if not is_blank(row.get(col, ""))}


def _norm_txn_code(val):
    s = re.sub(r"[^0-9]", "", str(val).strip())
    if not s:
        return ""
    return s.lstrip("0") or "0"


def check_priority_dob_vs_issue(tables, rules):
    """DT-003: quikridr MPHDOB must not be after quikmstr MISSDT for same MPOLICY."""
    findings = []
    spec = rules.get("dob_vs_issue")
    if not spec:
        return findings
    vid = spec["id"]
    child_fn, child_rows = _table_data(tables, spec["child"])
    parent_fn, parent_rows = _table_data(tables, spec["parent"])
    if not child_rows or not parent_rows:
        return findings
    child_lookup = field_lookup(child_fn)
    parent_lookup = field_lookup(parent_fn)
    key = spec.get("key", "MPOLICY").upper()
    dob_f = spec.get("dob_field", "MPHDOB").upper()
    issue_f = spec.get("issue_field", "MISSDT").upper()
    if key not in child_lookup or dob_f not in child_lookup:
        return findings
    if key not in parent_lookup or issue_f not in parent_lookup:
        return findings
    issue_by_pol = {}
    for row in parent_rows:
        pol = normalize(row.get(parent_lookup[key], ""))
        iss = date_to_yyyymmdd(row.get(parent_lookup[issue_f], ""))
        if pol and iss:
            issue_by_pol[pol] = iss
    key_col = child_lookup[key]
    dob_col = child_lookup[dob_f]
    cap = int(spec.get("max_samples", 50))
    hits = 0
    for idx, row in enumerate(child_rows, start=2):
        pol = normalize(row.get(key_col, ""))
        dob = date_to_yyyymmdd(row.get(dob_col, ""))
        iss = issue_by_pol.get(pol)
        if not pol or not dob or not iss:
            continue
        if dob > iss:
            hits += 1
            if hits <= cap:
                findings.append(make_priority_finding(
                    vid, spec.get("severity", "ERROR"), spec["child"],
                    spec.get("message", "Insured DOB after policy issue date"),
                    row=idx,
                    field=dob_f,
                    context={"MPOLICY": pol, dob_f: dob, issue_f: iss},
                ))
    if hits > cap:
        findings.append(make_priority_finding(
            vid, spec.get("severity", "ERROR"), spec["child"],
            f"{hits} total DOB-after-issue rows (showing first {cap})",
            field=dob_f,
            context={"total": hits},
        ))
    return findings


def _resolve_pactg_path(source_dir, repo_root, rules_spec):
    if rules_spec.get("pactg_path") and os.path.isfile(rules_spec["pactg_path"]):
        return rules_spec["pactg_path"]
    for rel in rules_spec.get("pactg_files", []):
        for base in (source_dir, repo_root):
            if not base:
                continue
            candidate = os.path.join(base, rel.replace("/", os.sep))
            if os.path.isfile(candidate):
                return candidate
    return None


def _load_crosswalk_maps(repo_root, rules):
    src_to_tgt = {}
    tgt_to_srcs = defaultdict(set)
    for rel in rules.get("crosswalk_paths", []):
        path = os.path.join(repo_root, rel.replace("/", os.sep))
        if not os.path.isfile(path):
            continue
        with open(path, newline="", encoding="latin1") as fh:
            for row in csv.reader(fh):
                if len(row) < 2:
                    continue
                src, tgt = normalize(row[0]), normalize(row[1])
                if src:
                    src_to_tgt[src] = tgt
                    if tgt:
                        tgt_to_srcs[tgt].add(src)
        break
    return src_to_tgt, tgt_to_srcs


def check_priority_pactg_claim_domain(tables, rules, source_dir, repo_root, pactg_path=None):
    """CLM-006: quikclms policy backed only by borrowed-money PACTG codes (no claim semantics)."""
    findings = []
    spec = rules.get("pactg_claim_domain")
    if not spec:
        return findings
    vid = spec["id"]
    _, clms_rows = _table_data(tables, "quikclms")
    if not clms_rows:
        return findings
    path = pactg_path or _resolve_pactg_path(source_dir, repo_root, spec)
    if not path:
        findings.append(make_priority_finding(
            vid, "WARN", "quikclms",
            "PACTG source not found — CLM-006 skipped (use --pactg or --source-dir)",
        ))
        return findings
    claim_codes = {_norm_txn_code(c) for c in spec.get("claim_domain_codes", [])}
    borrow_codes = {_norm_txn_code(c) for c in spec.get("borrowed_money_codes", [])}
    code_fields = [c.upper() for c in spec.get("code_fields", [])]
    pol_fields = [c.upper() for c in spec.get("policy_fields", [])]
    src_to_tgt, tgt_to_srcs = _load_crosswalk_maps(repo_root, rules)
    policy_codes = defaultdict(set)
    fieldnames, pactg_rows = read_csv_table(path)
    lookup = field_lookup(fieldnames)
    code_cols = [lookup[f] for f in code_fields if f in lookup]
    pol_cols = [lookup[f] for f in pol_fields if f in lookup]
    if not code_cols or not pol_cols:
        findings.append(make_priority_finding(
            vid, "WARN", "quikclms",
            "PACTG missing expected code/policy columns — CLM-006 skipped",
            context={"path": path},
        ))
        return findings
    for row in pactg_rows:
        pols = {normalize(row.get(c, "")) for c in pol_cols if not is_blank(row.get(c, ""))}
        codes = set()
        for c in code_cols:
            nc = _norm_txn_code(row.get(c, ""))
            if nc:
                codes.add(nc)
        if not codes:
            continue
        for pol in pols:
            if not pol:
                continue
            policy_codes[pol].update(codes)
            mapped = src_to_tgt.get(pol)
            if mapped:
                policy_codes[mapped].update(codes)
    clms_lookup = field_lookup(_table_data(tables, "quikclms")[0])
    if "MPOLICY" not in clms_lookup:
        return findings
    mp_col = clms_lookup["MPOLICY"]
    flagged = 0
    cap = int(spec.get("max_samples", 40))
    seen = set()
    for row in clms_rows:
        mp = normalize(row.get(mp_col, ""))
        if not mp or mp in seen:
            continue
        seen.add(mp)
        keys = {mp} | tgt_to_srcs.get(mp, set())
        codes = set()
        for k in keys:
            codes |= policy_codes.get(k, set())
        if not codes:
            continue
        has_claim = bool(codes & claim_codes)
        has_borrow = bool(codes & borrow_codes)
        if has_borrow and not has_claim:
            flagged += 1
            if flagged <= cap:
                findings.append(make_priority_finding(
                    vid, spec.get("severity", "ERROR"), "quikclms",
                    "Claim row policy has PACTG borrowed-money-only activity (no claim-domain codes)",
                    context={
                        "MPOLICY": mp,
                        "pactg_codes": sorted(codes)[:12],
                        "pactg_path": path,
                    },
                ))
    if flagged > cap:
        findings.append(make_priority_finding(
            vid, spec.get("severity", "ERROR"), "quikclms",
            f"{flagged} policies with borrowed-money-only PACTG chains (showing first {cap})",
            context={"total": flagged},
        ))
    elif path:
        findings.append(make_priority_finding(
            vid, "INFO", "quikclms",
            f"CLM-006 PACTG scan complete: {len(seen)} claim policies reviewed, 0 borrowed-money-only flags",
            context={"pactg_path": path, "policies_scanned": len(seen)},
        ))
    return findings


def check_priority_date_order(tables, rules):
    findings = []
    for spec in rules.get("date_order_checks", []):
        vid = spec["id"]
        table = spec["table"]
        fieldnames, rows = _table_data(tables, table)
        if not rows:
            continue
        lookup = field_lookup(fieldnames)
        left_f = spec["left_field"].upper()
        right_f = spec["right_field"].upper()
        if left_f not in lookup or right_f not in lookup:
            continue
        left_col, right_col = lookup[left_f], lookup[right_f]
        for idx, row in enumerate(rows, start=2):
            left_d = date_to_yyyymmdd(row.get(left_col, ""))
            right_d = date_to_yyyymmdd(row.get(right_col, ""))
            if not left_d or not right_d:
                continue
            bad = False
            if spec.get("rule") == "left_before_right_invalid" and left_d < right_d:
                bad = True
            if spec.get("rule") == "left_after_right_invalid" and left_d > right_d:
                bad = True
            if bad:
                findings.append(make_priority_finding(
                    vid, spec.get("severity", "ERROR"), table,
                    spec.get("message", f"{left_f} vs {right_f} date order violation"),
                    row=idx,
                    field=left_f,
                    context={left_f: left_d, right_f: right_d, "MPOLICY": row.get(lookup.get("MPOLICY", ""), "")},
                ))
    return findings


def check_priority_cross_table(tables, rules):
    findings = []
    for spec in rules.get("cross_table_referential", []):
        vid = spec["id"]
        child_name = spec["child"]
        parent_name = spec["parent"]
        key = spec["key"].upper()
        child_fn, child_rows = _table_data(tables, child_name)
        parent_fn, parent_rows = _table_data(tables, parent_name)
        if not child_rows or not parent_rows:
            continue
        child_lookup = field_lookup(child_fn)
        parent_lookup = field_lookup(parent_fn)
        if key not in child_lookup or key not in parent_lookup:
            continue
        parent_keys = _key_set(parent_rows, parent_lookup, key)
        child_col = child_lookup[key]
        orphans = defaultdict(int)
        for idx, row in enumerate(child_rows, start=2):
            k = normalize(row.get(child_col, ""))
            if not k or k in parent_keys:
                continue
            orphans[k] += 1
        for orphan_key, count in sorted(orphans.items(), key=lambda x: -x[1])[:20]:
            findings.append(make_priority_finding(
                vid, spec.get("severity", "ERROR"), child_name,
                f"{count} row(s) with {key}={orphan_key!r} not found in {parent_name}",
                field=key,
                context={"orphan_key": orphan_key, "orphan_rows": count, "parent": parent_name},
            ))
        if len(orphans) > 20:
            findings.append(make_priority_finding(
                vid, spec.get("severity", "ERROR"), child_name,
                f"{len(orphans)} distinct orphan {key} values (showing first 20)",
                field=key,
            ))
    return findings


def check_priority_plan_referential(tables, rules):
    findings = []
    spec = rules.get("plan_referential")
    if not spec:
        return findings
    vid = spec["id"]
    child_fn, child_rows = _table_data(tables, spec["child"])
    parent_fn, parent_rows = _table_data(tables, spec["parent"])
    if not child_rows or not parent_rows:
        return findings
    child_lookup = field_lookup(child_fn)
    parent_lookup = field_lookup(parent_fn)
    parent_field = spec["parent_field"].upper()
    if parent_field not in parent_lookup:
        return findings
    plan_col = parent_lookup[parent_field]
    valid_plans = _key_set(parent_rows, parent_lookup, parent_field)
    child_col = None
    for cand in spec.get("child_fields", ["MPLAN", "PLAN"]):
        if cand.upper() in child_lookup:
            child_col = child_lookup[cand.upper()]
            break
    if not child_col:
        return findings
    orphans = defaultdict(int)
    for idx, row in enumerate(child_rows, start=2):
        plan = normalize(row.get(child_col, ""))
        if not plan or (spec.get("skip_blank") and is_blank(plan)):
            continue
        if plan not in valid_plans:
            orphans[plan] += 1
    for plan, count in sorted(orphans.items(), key=lambda x: -x[1])[:25]:
        findings.append(make_priority_finding(
            vid, spec.get("severity", "ERROR"), spec["child"],
            f"{count} row(s) with plan {plan!r} not found in {spec['parent']}.{parent_field}",
            field=child_col,
            context={"orphan_plan": plan, "count": count},
        ))
    return findings


def check_priority_rider_phase(tables, rules):
    findings = []
    for spec in rules.get("rider_phase_checks", []):
        vid = spec["id"]
        table = spec["table"]
        fieldnames, rows = _table_data(tables, table)
        if not rows:
            continue
        lookup = field_lookup(fieldnames)
        phase_f = spec.get("phase_field", "MPHASE").upper()
        pol_f = "MPOLICY"
        if phase_f not in lookup or pol_f not in lookup:
            continue
        phase_col = lookup[phase_f]
        pol_col = lookup[pol_f]
        base = normalize(spec.get("base_phase", "1"))
        by_policy = defaultdict(set)
        for row in rows:
            pol = normalize(row.get(pol_col, ""))
            if not pol:
                continue
            ph = normalize(row.get(phase_col, ""))
            by_policy[pol].add(ph)
        for pol, phases in by_policy.items():
            has_base = base in phases
            has_supplemental = any(p for p in phases if p and p != base)
            if spec["type"] == "missing_base_phase" and phases and not has_base:
                findings.append(make_priority_finding(
                    vid, spec.get("severity", "ERROR"), table,
                    f"Policy {pol!r} has coverage rows but no MPHASE={base} base row",
                    field=phase_f,
                    context={"MPOLICY": pol, "phases": sorted(phases)},
                ))
            if spec["type"] == "supplemental_without_base" and has_supplemental and not has_base:
                findings.append(make_priority_finding(
                    vid, spec.get("severity", "ERROR"), table,
                    f"Policy {pol!r} has supplemental MPHASE but no MPHASE={base}",
                    field=phase_f,
                    context={"MPOLICY": pol, "phases": sorted(phases)},
                ))
    return findings


def check_priority_table_values(tables, rules):
    findings = []
    for spec in rules.get("table_value_checks", []):
        vid = spec["id"]
        table = spec["table"]
        fieldnames, rows = _table_data(tables, table)
        if not rows:
            continue
        lookup = field_lookup(fieldnames)
        field = spec["field"].upper()
        if field not in lookup:
            continue
        col = lookup[field]
        patterns = {normalize(p) for p in spec.get("match_any_normalized", [])}
        for idx, row in enumerate(rows, start=2):
            val = normalize(row.get(col, ""))
            if not val:
                continue
            compact = re.sub(r"[^0-9A-Z]", "", val)
            if val in patterns or compact in patterns:
                findings.append(make_priority_finding(
                    vid, spec.get("severity", "ERROR"), table,
                    spec.get("message", f"Forbidden value in {field}"),
                    row=idx,
                    field=field,
                    context={"value": row.get(col, ""), "MPOLICY": row.get(lookup.get("MPOLICY", ""), "")},
                ))
    return findings


def check_priority_governance_columns(tables, rules):
    findings = []
    forbidden = {c.lower() for c in rules.get("governance_columns", [])}
    for table_name in ("quikclms", "quikclmp"):
        fieldnames, rows = _table_data(tables, table_name)
        if not fieldnames:
            continue
        leaked = [f for f in fieldnames if f.lower() in forbidden]
        if leaked:
            findings.append(make_priority_finding(
                "CLM-011", "ERROR", table_name,
                f"Governance metadata column(s) in output: {', '.join(leaked)}",
                context={"columns": leaked},
            ))
    return findings


def check_priority_crosswalk(repo_root, rules):
    findings = []
    path = None
    for rel in rules.get("crosswalk_paths", []):
        candidate = os.path.join(repo_root, rel.replace("/", os.sep))
        if os.path.isfile(candidate):
            path = candidate
            break
    if not path:
        findings.append(make_priority_finding(
            "CW-001", "WARN", "crosswalk",
            "Master_Crosswalk.csv not found — skipping crosswalk checks",
        ))
        return findings
    src_to_targets = defaultdict(set)
    target_to_sources = defaultdict(set)
    with open(path, newline="", encoding="latin1") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if len(row) < 2:
                continue
            src = normalize(row[0])
            tgt = normalize(row[1])
            if not src:
                continue
            src_to_targets[src].add(tgt)
            if tgt:
                target_to_sources[tgt].add(src)
    for src, targets in src_to_targets.items():
        if len(targets) > 1:
            findings.append(make_priority_finding(
                "CW-001", "ERROR", "crosswalk",
                f"Source {src!r} maps to multiple targets: {sorted(targets)}",
                context={"source": src, "targets": sorted(targets)},
            ))
    for tgt, sources in target_to_sources.items():
        if len(sources) > 1:
            findings.append(make_priority_finding(
                "CW-002", "ERROR", "crosswalk",
                f"Target {tgt!r} receives multiple sources ({len(sources)}); sample: {sorted(sources)[:5]}",
                context={"target": tgt, "source_count": len(sources)},
            ))
    return findings


def check_priority_required_files(output_dir, source_dir, repo_root, rules):
    findings = []
    for spec in rules.get("required_output_files", []):
        fpath = os.path.join(output_dir, spec["file"])
        if not os.path.isfile(fpath):
            findings.append(make_priority_finding(
                spec["id"], spec.get("severity", "ERROR"), "governance",
                f"Required output file missing: {spec['file']}",
                context={"path": fpath},
            ))
    if source_dir:
        for spec in rules.get("required_source_files", []):
            fpath = os.path.join(source_dir, spec["file"])
            if not os.path.isfile(fpath):
                findings.append(make_priority_finding(
                    spec["id"], spec.get("severity", "WARN"), "governance",
                    f"Expected source file missing: {spec['file']}",
                    context={"path": fpath},
                ))
    return findings


def check_priority_schema_manifest(config, rules):
    findings = []
    required = rules.get("schema_manifest_required_tables", [])
    manifest = config.get("schema", {})
    for table in required:
        if table not in manifest:
            findings.append(make_priority_finding(
                "GOV-012", "ERROR", "governance",
                f"schema_manifest.json missing table definition: {table}",
            ))
    return findings


def check_priority_reconciliation(tables, output_dir, repo_root, source_dir, rules):
    findings = []
    for spec in rules.get("reconciliation", []):
        vid = spec["id"]
        if spec["type"] == "policy_count" and source_dir:
            src_path = os.path.join(source_dir, spec["source_file"])
            out_table = spec["output_table"]
            _, out_rows = _table_data(tables, out_table)
            if not os.path.isfile(src_path) or not out_rows:
                continue
            src_fn, src_rows = read_csv_table(src_path)
            src_lookup = field_lookup(src_fn)
            sf = spec["source_field"].upper()
            of = spec["output_field"].upper()
            out_fn, _ = _table_data(tables, out_table)
            out_lookup = field_lookup(out_fn)
            if sf not in src_lookup or of not in out_lookup:
                continue
            src_count = len({normalize(r.get(src_lookup[sf], "")) for r in src_rows if not is_blank(r.get(src_lookup[sf], ""))})
            out_count = len({normalize(r.get(out_lookup[of], "")) for r in out_rows if not is_blank(r.get(out_lookup[of], ""))})
            if src_count != out_count:
                findings.append(make_priority_finding(
                    vid, spec.get("severity", "WARN"), out_table,
                    f"Policy count mismatch: source={src_count} output={out_count} (delta={out_count - src_count})",
                    context={"source_count": src_count, "output_count": out_count},
                ))
        if spec["type"] == "loan_candidate_count":
            staging = os.path.join(repo_root, spec.get("staging_file", "").replace("/", os.sep))
            if os.path.isfile(staging):
                _, staging_rows = read_csv_table(staging)
                staging_count = len(staging_rows)
                findings.append(make_priority_finding(
                    vid, "INFO", "quikloan",
                    f"Phase L1 staging emit candidates: {staging_count} rows",
                    context={"staging_path": staging, "count": staging_count},
                ))
            out_fn, out_rows = _table_data(tables, "quikloan")
            if out_rows and os.path.isfile(staging):
                if len(out_rows) != len(read_csv_table(staging)[1]):
                    findings.append(make_priority_finding(
                        vid, spec.get("severity", "WARN"), "quikloan",
                        f"Output quikloan.csv rows ({len(out_rows)}) differ from staging candidates",
                        context={"output_rows": len(out_rows)},
                    ))
    return findings


def run_priority_checks(tables, config, output_dir, repo_root=None, source_dir=None, pactg_path=None):
    rules = config.get("priority") or {}
    if not rules:
        return []
    repo_root = repo_root or SCRIPT_DIR
    findings = []
    findings.extend(check_priority_schema_manifest(config, rules))
    findings.extend(check_priority_required_files(output_dir, source_dir, repo_root, rules))
    findings.extend(check_priority_crosswalk(repo_root, rules))
    findings.extend(check_priority_dob_vs_issue(tables, rules))
    findings.extend(check_priority_date_order(tables, rules))
    findings.extend(check_priority_pactg_claim_domain(
        tables, rules, source_dir, repo_root, pactg_path=pactg_path,
    ))
    findings.extend(check_priority_cross_table(tables, rules))
    findings.extend(check_priority_plan_referential(tables, rules))
    findings.extend(check_priority_rider_phase(tables, rules))
    findings.extend(check_priority_table_values(tables, rules))
    findings.extend(check_priority_governance_columns(tables, rules))
    findings.extend(check_priority_reconciliation(tables, output_dir, repo_root, source_dir, rules))
    return findings


def load_all_tables(file_paths):
    tables = {}
    for path in file_paths:
        table = table_name_from_path(path)
        fieldnames, rows = read_csv_table(path)
        tables[table] = {"path": path, "fieldnames": fieldnames, "rows": rows}
    return tables


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def validate_table(path, config, enabled_categories, baseline_data=None, strict_regression=False):
    table = table_name_from_path(path)
    fieldnames, rows = read_csv_table(path)
    all_findings = []

    if "schema" in enabled_categories:
        all_findings.extend(check_schema(table, fieldnames, config["schema"]))

    if "critical" in enabled_categories:
        all_findings.extend(check_critical_fields(table, fieldnames, rows, config["critical"]))

    if "dates" in enabled_categories:
        all_findings.extend(check_dates(table, fieldnames, rows, config["dates"]))

    if "duplicates" in enabled_categories:
        all_findings.extend(check_duplicate_keys(table, fieldnames, rows, config["keys"]))

    metrics = build_table_metrics(table, fieldnames, all_findings)
    metrics["row_count"] = len(rows)

    if "regression" in enabled_categories and baseline_data:
        all_findings.extend(check_regression(table, metrics, len(rows), baseline_data, strict_regression))

    return {
        "table": table,
        "file": os.path.basename(path),
        "path": path,
        "row_count": len(rows),
        "metrics": metrics,
        "findings": all_findings,
    }


def run_validation(output_dir, config_dir, enabled_categories, sample_limit,
                   baseline_path=None, strict_regression=False,
                   repo_root=None, source_dir=None):
    config = load_all_config(config_dir)
    baseline_data = load_baseline(baseline_path) if baseline_path else None
    files = discover_output_files(output_dir)
    tables = load_all_tables(files)
    results = []
    for path in files:
        logger.info("Validating %s", os.path.basename(path))
        results.append(validate_table(
            path, config, enabled_categories, baseline_data, strict_regression,
        ))
    if "priority" in enabled_categories:
        logger.info("Running priority go-live checks (25-check set)")
        priority_findings = run_priority_checks(
            tables, config, output_dir, repo_root=repo_root, source_dir=source_dir,
        )
        results.append({
            "table": "priority_checks",
            "file": "priority_rules.json",
            "path": os.path.join(config_dir, "priority_rules.json"),
            "row_count": 0,
            "metrics": {"priority_findings": len(priority_findings)},
            "findings": priority_findings,
        })
    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def count_by_severity(findings):
    errors = sum(1 for f in findings if f["severity"] == "ERROR")
    warns = sum(1 for f in findings if f["severity"] == "WARN")
    return errors, warns


def format_text_report(results, output_dir, enabled_categories, sample_limit, baseline_path=None):
    lines = [
        "=== QLAdmin Output Validation Report ===",
        f"Directory: {os.path.abspath(output_dir)}",
        f"Categories: {', '.join(enabled_categories)}",
    ]
    if baseline_path:
        lines.append(f"Baseline: {os.path.abspath(baseline_path)}")
    lines.append("")

    total_errors = 0
    total_warns = 0
    category_totals = Counter()

    for result in results:
        findings = result["findings"]
        if not findings:
            continue
        limited, counts, truncated = apply_sample_limit(findings, sample_limit)
        errors, warns = count_by_severity(findings)
        total_errors += errors
        total_warns += warns

        lines.append(f"--- {result['file']} ({result['row_count']} rows) ---")
        by_category = defaultdict(list)
        for f in limited:
            by_category[f["category"]].append(f)

        for cat in CATEGORIES:
            if cat not in by_category:
                continue
            lines.append(f"  [{cat.upper()}] {counts[cat]} finding(s)")
            for f in by_category[cat]:
                loc = f"row {f['row']}" if f.get("row") else "file"
                field = f" {f['field']}" if f.get("field") else ""
                lines.append(f"    [{f['severity']}] {loc}{field}: {f['message']}")
                if f.get("context"):
                    ctx = ", ".join(f"{k}={v!r}" for k, v in f["context"].items() if k != "rows")
                    if ctx:
                        lines.append(f"      context: {ctx}")
                    if "rows" in f["context"]:
                        lines.append(f"      rows: {f['context']['rows'][:5]}")
            if truncated.get(cat):
                lines.append(f"    ... showing first {sample_limit} of {counts[cat]}")
            category_totals[cat] += counts[cat]
        lines.append("")

    lines.extend([
        "=== Summary ===",
        f"Files scanned: {len(results)}",
        f"Files with findings: {sum(1 for r in results if r['findings'])}",
        f"Total ERROR: {total_errors}",
        f"Total WARN: {total_warns}",
    ])
    for cat in CATEGORIES:
        if category_totals[cat]:
            lines.append(f"  {cat}: {category_totals[cat]}")
    priority_ids = Counter(
        f["context"].get("validation_id")
        for r in results for f in r["findings"]
        if f.get("category") == "priority" and f.get("context", {}).get("validation_id")
    )
    if priority_ids:
        lines.append("Priority check IDs triggered:")
        for vid, cnt in sorted(priority_ids.items()):
            lines.append(f"  {vid}: {cnt}")

    lines.append("Status: PASS" if total_errors == 0 else "Status: FAIL")
    return "\n".join(lines)


def write_csv_report(results, csv_path, sample_limit):
    all_findings = []
    for result in results:
        all_findings.extend(result["findings"])
    limited, _, _ = apply_sample_limit(all_findings, sample_limit)
    fieldnames = ["category", "severity", "table", "row", "field", "message", "context"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for finding in limited:
            row = dict(finding)
            row["context"] = json.dumps(row.get("context", {}), ensure_ascii=True)
            writer.writerow(row)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_categories(raw):
    if not raw:
        return set(CATEGORIES) - {"regression"}
    selected = {c.strip().lower() for c in raw.split(",")}
    unknown = selected - set(CATEGORIES)
    if unknown:
        raise ValueError(f"Unknown categories: {', '.join(sorted(unknown))}")
    return selected


def setup_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main():
    parser = argparse.ArgumentParser(
        description="Enterprise validator for QLAdmin quik*.csv migration outputs.",
    )
    parser.add_argument("output_dir", nargs="?", default=".", help="Directory with quik*.csv files")
    parser.add_argument("--config-dir", default=DEFAULT_CONFIG_DIR, help="Path to validation_config/")
    parser.add_argument("--rules", help="Comma-separated categories: schema,critical,dates,duplicates,regression")
    parser.add_argument("--baseline", help="Baseline JSON for regression comparison")
    parser.add_argument("--write-baseline", help="Write baseline JSON from current output")
    parser.add_argument("--baseline-label", default="manual_baseline", help="Label stored in baseline file")
    parser.add_argument("--strict-regression", action="store_true", help="Treat row-count drift as ERROR")
    parser.add_argument("-o", "--report", help="Write text report to file")
    parser.add_argument("--csv-report", help="Write findings CSV report to file")
    parser.add_argument("--sample-limit", type=int, default=DEFAULT_SAMPLE_LIMIT)
    parser.add_argument(
        "--repo-root",
        default=SCRIPT_DIR,
        help="Repository root for crosswalk and Phase L1 paths (default: script dir)",
    )
    parser.add_argument(
        "--source-dir",
        help="QLA_Migration/Source for GOV-003, RCN-001, and CLM-006 PACTG scan",
    )
    parser.add_argument(
        "--pactg",
        help="Explicit PACTG extract path for CLM-006 (default: auto from --source-dir)",
    )
    parser.add_argument(
        "--priority-only",
        action="store_true",
        help="Run only priority category (skip per-table schema/critical unless --rules overrides)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    setup_logging(args.verbose)
    output_dir = os.path.abspath(args.output_dir)

    try:
        if args.priority_only:
            enabled = {"priority"}
        else:
            enabled = parse_categories(args.rules)
            if args.rules is None:
                enabled.add("priority")
        if args.baseline:
            enabled.add("regression")

        config = load_all_config(args.config_dir)
        files = discover_output_files(output_dir)
        if not files and "priority" not in enabled:
            print(f"No quik*.csv files found in: {output_dir}")
            return 0

        source_dir = os.path.abspath(args.source_dir) if args.source_dir else None
        if not source_dir:
            default_src = os.path.join(args.repo_root, "QLA_Migration", "Source")
            if os.path.isdir(default_src):
                source_dir = default_src

        baseline_data = load_baseline(args.baseline) if args.baseline else None
        per_table = enabled - {"priority"}
        results = []
        if per_table and files:
            for path in files:
                logger.info("Validating %s", os.path.basename(path))
                results.append(validate_table(
                    path, config, per_table, baseline_data, args.strict_regression,
                ))
        if "priority" in enabled:
            tables = load_all_tables(files) if files else {}
            logger.info("Running priority go-live checks (25-check set)")
            pactg_path = os.path.abspath(args.pactg) if args.pactg else None
            priority_findings = run_priority_checks(
                tables, config, output_dir,
                repo_root=os.path.abspath(args.repo_root),
                source_dir=source_dir,
                pactg_path=pactg_path,
            )
            results.append({
                "table": "priority_checks",
                "file": "priority_rules.json",
                "path": os.path.join(args.config_dir, "priority_rules.json"),
                "row_count": 0,
                "metrics": {"priority_findings": len(priority_findings)},
                "findings": priority_findings,
            })
        if not results:
            print(f"No quik*.csv files found in: {output_dir}")
            return 0

        if args.write_baseline:
            write_baseline(args.write_baseline, args.baseline_label, results)
            print(f"Baseline written: {args.write_baseline}")

        report = format_text_report(
            results, output_dir, sorted(enabled), args.sample_limit, args.baseline,
        )
        print(report)

        if args.report:
            with open(args.report, "w", encoding="utf-8") as f:
                f.write(report + "\n")
            print(f"Text report saved: {args.report}")

        if args.csv_report:
            write_csv_report(results, args.csv_report, args.sample_limit)
            print(f"CSV report saved: {args.csv_report}")

        has_errors = any(
            f["severity"] == "ERROR"
            for r in results for f in r["findings"]
        )
        return 1 if has_errors else 0

    except (FileNotFoundError, ValueError) as exc:
        logger.error("%s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
