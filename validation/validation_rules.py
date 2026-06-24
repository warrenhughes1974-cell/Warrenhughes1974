"""Extensible validation rule registry for final output validation."""

from __future__ import annotations

import json
import os
import re
from typing import TYPE_CHECKING, Any

from .rule_audit import STATUS_SKIPPED_OPTIONAL, RuleAuditTracker
from .validation_config import (
    GOVERNANCE_LEAK_COLUMNS,
    LOAN_TRANSACTION_CODES,
    RULE_ALIASES,
    US_STATE_CODES,
    VALID_MSTATUS_CODES,
    resolve_rule_files,
    rule_meta,
)
from .validation_helpers import (
    field_lookup,
    is_blank,
    make_result,
    normalize,
    not_executed,
    parse_date_yyyymmdd,
    validate_reference,
    validate_unique_rows,
)

if TYPE_CHECKING:
    pass


def _tbl(tables: dict, name: str) -> tuple[list[str], list[dict], str, int]:
    t = tables.get(name, {})
    return t.get("fieldnames", []), t.get("rows", []), t.get("path", ""), t.get("row_count", 0)


def _rule_files(rule_id: str, output_dir: str, source_dir: str | None, repo_root: str):
    return resolve_rule_files(rule_id, output_dir, source_dir, repo_root)


def _optional_skip(audit: RuleAuditTracker | None, rule_id: str, output_dir: str, source_dir: str | None, repo_root: str) -> bool:
    """Return True if rule should be skipped (optional files missing)."""
    if audit is None:
        return False
    exp, found, missing, required = _rule_files(rule_id, output_dir, source_dir, repo_root)
    if missing and not required:
        audit.skip(
            rule_id,
            f"Optional file(s) missing: {', '.join(missing)}",
            status=STATUS_SKIPPED_OPTIONAL,
            files_expected=exp,
            files_found=found,
            files_missing=missing,
        )
        return True
    return False


def _guard(
    audit: RuleAuditTracker | None,
    rule_id: str,
    fn,
    output_dir: str,
    source_dir: str | None,
    repo_root: str,
    records_scanned: int = 0,
) -> list[dict]:
    if audit is None:
        try:
            return fn() or []
        except Exception:
            raise
    if _optional_skip(audit, rule_id, output_dir, source_dir, repo_root):
        return []
    exp, found, missing, _ = _rule_files(rule_id, output_dir, source_dir, repo_root)
    return audit.run_guarded(
        rule_id, fn,
        files_expected=exp,
        files_found=found,
        files_missing=missing,
        records_scanned=records_scanned,
    )


def run_extended_rules(
    tables: dict[str, dict],
    output_dir: str,
    repo_root: str,
    source_dir: str | None,
    app_table_schemas: dict[str, list[str]] | None,
    audit: RuleAuditTracker | None = None,
) -> list[dict]:
    """Run catalog rules beyond validate_output.py priority checks."""
    results: list[dict] = []

    def _gov005():
        out = []
        if not os.path.isfile(os.path.join(output_dir, "quikplan.csv")):
            out.append(make_result("GOV-005", "Required output file missing: quikplan.csv", "quikplan", output_dir))
        return out

    results.extend(_guard(audit, "GOV-005", _gov005, output_dir, source_dir, repo_root))

    def _gov003():
        out = []
        if source_dir and os.path.isdir(source_dir):
            for fname in ("quikmstr.csv", "PPBEN.csv", "PACTG_Accounting_Extract20260427.csv"):
                if not os.path.isfile(os.path.join(source_dir, fname)):
                    out.append(make_result("GOV-003", f"Expected source file missing: {fname}", "source", source_dir))
        else:
            out.append(not_executed("GOV-003", "Source folder not configured or not visible"))
        return out

    results.extend(_guard(audit, "GOV-003", _gov003, output_dir, source_dir, repo_root))

    def _gov012():
        out = []
        if not app_table_schemas:
            return out
        manifest_path = os.path.join(repo_root, "validation_config", "schema_manifest.json")
        if os.path.isfile(manifest_path):
            with open(manifest_path, encoding="utf-8") as fh:
                manifest = json.load(fh)
            for table, cols in app_table_schemas.items():
                if table not in manifest:
                    out.append(make_result("GOV-012", f"schema_manifest missing table: {table}", table, manifest_path))
                else:
                    m_cols = [c.upper() for c in manifest[table].get("columns", [])]
                    a_cols = [c.upper() for c in cols]
                    if m_cols != a_cols:
                        out.append(make_result(
                            "GOV-012",
                            f"schema_manifest column list differs from app TABLE_SCHEMAS for {table}",
                            table, manifest_path,
                        ))
        return out

    results.extend(_guard(audit, "GOV-012", _gov012, output_dir, source_dir, repo_root))

    fn, rows, path, mstr_n = _tbl(tables, "quikmstr")

    def _pol001():
        if not fn:
            return []
        return validate_unique_rows(
            "quikmstr", fn, rows, ["MPOLICY"], "POL-001",
            rule_meta("POL-001")["rule_name"], "Critical", "Block", path,
        )

    results.extend(_guard(audit, "POL-001", _pol001, output_dir, source_dir, repo_root, mstr_n))

    def _pol002():
        out = []
        if not fn:
            return out
        lookup = field_lookup(fn)
        mp = lookup.get("MPOLICY")
        if mp:
            for idx, row in enumerate(rows, start=2):
                if is_blank(row.get(mp, "")):
                    out.append(make_result("POL-002", "MPOLICY is blank", "quikmstr", path, key_fields="MPOLICY", row_number=idx))
                    break
        return out

    results.extend(_guard(audit, "POL-002", _pol002, output_dir, source_dir, repo_root, mstr_n))

    def _mstr001():
        out = []
        if not (fn and rows):
            return out
        lookup = field_lookup(fn)
        for fld, rid, msg in (
            ("MSTATUS", "MSTR-001", "MSTATUS blank or invalid"),
            ("MSTATDATE", "MSTR-002", "MSTATDATE blank or invalid date"),
            ("MBILLFRM", "MSTR-006", "MBILLFRM blank"),
            ("MMODE", "MSTR-009", "MMODE blank"),
            ("MISSUEST", "MSTR-010", "MISSUEST blank or invalid state"),
        ):
            col = lookup.get(fld)
            if not col:
                continue
            for idx, row in enumerate(rows[:5000], start=2):
                val = normalize(row.get(col, ""))
                if is_blank(val):
                    out.append(make_result(rid, f"{msg}: blank", "quikmstr", path, field_name=fld, row_number=idx))
                    break
                if fld == "MSTATUS" and val not in VALID_MSTATUS_CODES:
                    out.append(make_result(rid, f"Invalid MSTATUS code: {val}", "quikmstr", path, field_name=fld, actual_value=val, row_number=idx))
                    break
                if fld == "MSTATDATE" and not parse_date_yyyymmdd(val):
                    out.append(make_result(rid, f"Invalid MSTATDATE: {val}", "quikmstr", path, field_name=fld, row_number=idx))
                    break
                if fld == "MISSUEST" and val not in US_STATE_CODES:
                    out.append(make_result(rid, f"Invalid MISSUEST: {val}", "quikmstr", path, field_name=fld, actual_value=val, row_number=idx))
                    break
        return out

    if audit is None:
        results.extend(_mstr001())
    else:
        for rid in ("MSTR-001", "MSTR-002", "MSTR-006", "MSTR-009", "MSTR-010"):
            def _one(r=rid):
                return [x for x in _mstr001() if x.get("rule_id") == r]
            results.extend(_guard(audit, rid, _one, output_dir, source_dir, repo_root, mstr_n))

    def _mstr008():
        out = []
        if not (fn and rows):
            return out
        lookup = field_lookup(fn)
        bf, bank = lookup.get("MBILLFRM"), lookup.get("MBANKNO")
        if bf and bank:
            for idx, row in enumerate(rows, start=2):
                if normalize(row.get(bf, "")) == "2" and is_blank(row.get(bank, "")):
                    out.append(make_result("MSTR-008", "MBANKNO required when MBILLFRM=2 (bank billing)", "quikmstr", path, field_name="MBANKNO", row_number=idx))
                    break
        return out

    results.extend(_guard(audit, "MSTR-008", _mstr008, output_dir, source_dir, repo_root, mstr_n))

    def _mstr013():
        out = []
        if not (fn and rows):
            return out
        lookup = field_lookup(fn)
        for fld in ("MBENPID", "MBENCID"):
            col = lookup.get(fld)
            if col:
                for idx, row in enumerate(rows, start=2):
                    if not is_blank(row.get(col, "")):
                        out.append(make_result("MSTR-013", f"{fld} must be blank", "quikmstr", path, field_name=fld, row_number=idx))
                        break
        return out

    results.extend(_guard(audit, "MSTR-013", _mstr013, output_dir, source_dir, repo_root, mstr_n))

    def _mstr012():
        out = []
        if not (fn and rows):
            return out
        cfn, crows, _, _ = _tbl(tables, "quikclnt")
        if not cfn:
            return out
        lookup = field_lookup(fn)
        clookup = field_lookup(cfn)
        cid_col = clookup.get("MCLIENTID")
        if not cid_col:
            return out
        client_set = {normalize(r.get(cid_col, "")) for r in crows if not is_blank(r.get(cid_col, ""))}
        for ref_fld in ("MPRIMID", "MOWNRID", "MASGNID", "MPAYRID", "MOWNCID"):
            rc = lookup.get(ref_fld)
            if not rc:
                continue
            for idx, row in enumerate(rows, start=2):
                val = normalize(row.get(rc, ""))
                if not is_blank(val) and val not in client_set:
                    out.append(make_result("MSTR-012", f"{ref_fld}={val!r} not in quikclnt.MCLIENTID", "quikmstr", path, field_name=ref_fld, key_value=val, row_number=idx))
                    break
        return out

    results.extend(_guard(audit, "MSTR-012", _mstr012, output_dir, source_dir, repo_root, mstr_n))

    rfn, rrows, rpath, ridr_n = _tbl(tables, "quikridr")

    for rule_id, key_fields in (
        ("DUP-002", ["MPOLICY", "MPHASE"]),
        ("DUP-003", ["MRIDRID"]),
    ):
        def _dup(rid=rule_id, kf=key_fields):
            if not rfn:
                return []
            return validate_unique_rows("quikridr", rfn, rrows, kf, rid, rule_meta(rid)["rule_name"], "Critical", "Block", rpath)
        results.extend(_guard(audit, rule_id, _dup, output_dir, source_dir, repo_root, ridr_n))

    for rule_id, fld in (("REQ-002", "MRIDRID"), ("REQ-003", "MPHASE")):
        def _req(rid=rule_id, field=fld):
            out = []
            if not rfn:
                return out
            lookup = field_lookup(rfn)
            col = lookup.get(field)
            if col:
                for idx, row in enumerate(rrows, start=2):
                    val = normalize(row.get(col, ""))
                    if is_blank(val) or val in ("0",):
                        out.append(make_result(rid, f"{field} blank or zero", "quikridr", rpath, field_name=field, row_number=idx))
                        break
            return out
        results.extend(_guard(audit, rule_id, _req, output_dir, source_dir, repo_root, ridr_n))

    cfn, crows, cpath, clms_n = _tbl(tables, "quikclms")

    def _dup008():
        if not cfn:
            return []
        return validate_unique_rows("quikclms", cfn, crows, ["CLAIMNUM"], "DUP-008", rule_meta("DUP-008")["rule_name"], "Critical", "Block", cpath)

    results.extend(_guard(audit, "DUP-008", _dup008, output_dir, source_dir, repo_root, clms_n))

    clfn, clrows, clpath, clnt_n = _tbl(tables, "quikclnt")

    def _clnt001():
        if not clfn:
            return []
        return validate_unique_rows("quikclnt", clfn, clrows, ["MCLIENTID"], "CLNT-001", rule_meta("CLNT-001")["rule_name"], "Critical", "Block", clpath)

    results.extend(_guard(audit, "CLNT-001", _clnt001, output_dir, source_dir, repo_root, clnt_n))

    lfn, lrows, lpath, loan_n = _tbl(tables, "quikloan")

    def _loan002():
        if not lfn:
            return []
        return validate_unique_rows("quikloan", lfn, lrows, ["MPOLICY"], "LOAN-002", rule_meta("LOAN-002")["rule_name"], "Critical", "Block", lpath)

    results.extend(_guard(audit, "LOAN-002", _loan002, output_dir, source_dir, repo_root, loan_n))

    def _loan005():
        out = []
        if not lfn:
            return out
        lookup = field_lookup(lfn)
        ld = lookup.get("MLOANDATE")
        if ld:
            for idx, row in enumerate(lrows, start=2):
                if is_blank(row.get(ld, "")):
                    out.append(make_result("LOAN-005", "MLOANDATE blank", "quikloan", lpath, field_name="MLOANDATE", row_number=idx))
                    break
        return out

    results.extend(_guard(audit, "LOAN-005", _loan005, output_dir, source_dir, repo_root, loan_n))

    idfn, idrows, idpath, clid_n = _tbl(tables, "quikclid")
    mfn, mrows, mpath, _ = _tbl(tables, "quikmstr")

    def _clid002():
        if not (idfn and mfn):
            return []
        return validate_reference("quikclid", idfn, idrows, "quikmstr", mfn, mrows, "MPOLICY", "MPOLICY", "CLID-002", rule_meta("CLID-002")["rule_name"], "Critical", "Block", idpath)

    results.extend(_guard(audit, "CLID-002", _clid002, output_dir, source_dir, repo_root, clid_n))

    def _clid001():
        if not (idfn and clfn):
            return []
        return validate_reference("quikclid", idfn, idrows, "quikclnt", clfn, clrows, "MCLIENTID", "MCLIENTID", "CLID-001", rule_meta("CLID-001")["rule_name"], "Critical", "Block", idpath)

    results.extend(_guard(audit, "CLID-001", _clid001, output_dir, source_dir, repo_root, clid_n))

    def _clid003():
        out = []
        if not (idfn and rfn):
            return out
        lookup = field_lookup(idfn)
        pol_c, phase_c = lookup.get("MPOLICY"), lookup.get("MPHASE")
        rlookup = field_lookup(rfn)
        rp, rph = rlookup.get("MPOLICY"), rlookup.get("MPHASE")
        if pol_c and phase_c and rp and rph:
            rider_keys = {(normalize(r.get(rp, "")), normalize(r.get(rph, ""))) for r in rrows}
            for idx, row in enumerate(idrows, start=2):
                ph = normalize(row.get(phase_c, ""))
                if ph in ("", "0"):
                    continue
                key = (normalize(row.get(pol_c, "")), ph)
                if key not in rider_keys:
                    out.append(make_result("CLID-003", f"MPOLICY+MPHASE {key} not in quikridr", "quikclid", idpath, key_fields="MPOLICY,MPHASE", key_value=f"{key[0]}|{key[1]}", row_number=idx))
                    break
        return out

    results.extend(_guard(audit, "CLID-003", _clid003, output_dir, source_dir, repo_root, clid_n))

    def _clm011():
        out = []
        for tname in ("quikclms", "quikclmp"):
            tfn, _, tpath, _ = _tbl(tables, tname)
            if tfn:
                leaked = [f for f in tfn if f.lower() in GOVERNANCE_LEAK_COLUMNS]
                if leaked:
                    out.append(make_result("CLM-011", f"Governance metadata column(s) in output: {', '.join(leaked)}", tname, tpath, field_name=",".join(leaked)))
        return out

    results.extend(_guard(audit, "CLM-011", _clm011, output_dir, source_dir, repo_root))

    pfn, prows, ppath, prmh_n = _tbl(tables, "quikprmh")

    def _prm009():
        out = []
        if not pfn:
            return out
        lookup = field_lookup(pfn)
        for fld in ("MSOURCE", "RENEWAL", "MBATCH", "MPOLICY"):
            col = lookup.get(fld)
            if not col:
                continue
            for idx, row in enumerate(prows, start=2):
                val = normalize(row.get(col, ""))
                compact = re.sub(r"[^0-9A-Z]", "", val)
                if val in LOAN_TRANSACTION_CODES or compact in LOAN_TRANSACTION_CODES:
                    out.append(make_result("PRM-009", f"Loan/borrowed-money code in {fld}", "quikprmh", ppath, field_name=fld, actual_value=val, row_number=idx))
                    break
        return out

    results.extend(_guard(audit, "PRM-009", _prm009, output_dir, source_dir, repo_root, prmh_n))

    plfn, plrows, plpath, plan_n = _tbl(tables, "quikplan")

    def _plan001():
        out = []
        if not plfn:
            return out
        lookup = field_lookup(plfn)
        plan_col = lookup.get("PLAN")
        if plan_col:
            bad = re.compile(r"^[A-Z0-9]{6}$")
            for idx, row in enumerate(plrows, start=2):
                plan = normalize(row.get(plan_col, ""))
                if plan and not bad.match(plan):
                    out.append(make_result("PLAN-001", f"PLAN code format invalid: {plan!r}", "quikplan", plpath, field_name="PLAN", actual_value=plan, row_number=idx))
                    break
        return out

    results.extend(_guard(audit, "PLAN-001", _plan001, output_dir, source_dir, repo_root, plan_n))

    def _rdrplan001():
        return [make_result("RDR-PLAN-001", "Extensible rider MPLAN PUA/rate-up validation registered — config-driven completion pending", "quikridr", rpath or "")]

    results.extend(_guard(audit, "RDR-PLAN-001", _rdrplan001, output_dir, source_dir, repo_root, ridr_n))

    def _clm006():
        pactg_found = False
        if source_dir:
            for name in ("PACTG_Accounting_Extract20260427.csv", "PACTG.csv"):
                if os.path.isfile(os.path.join(source_dir, name)):
                    pactg_found = True
                    break
        if not pactg_found:
            return [not_executed("CLM-006", "PACTG source not available to validator")]
        return []

    results.extend(_guard(audit, "CLM-006", _clm006, output_dir, source_dir, repo_root))

    return results


def apply_findings_to_audit(audit: RuleAuditTracker, findings: list[dict], *, records_scanned: int = 0) -> None:
    """Update audit rows for legacy/priority findings keyed by rule_id."""
    from collections import defaultdict
    counts: dict[str, int] = defaultdict(int)
    for row in findings:
        rid = row.get("rule_id") or ""
        if rid:
            counts[rid] += 1
    for rid, count in counts.items():
        st = audit._rows.get(rid, {}).get("status")
        if st and st not in ("PENDING",):
            continue
        audit.complete(rid, count, records_scanned=records_scanned)


def convert_legacy_finding(finding: dict, source_path: str = "") -> dict:
    """Convert validate_output.py finding to enterprise result row."""
    ctx = finding.get("context") or {}
    rule_id = ctx.get("validation_id", "")
    category = finding.get("category", "")
    legacy_sev = finding.get("severity", "WARN")

    if rule_id:
        canonical = RULE_ALIASES.get(rule_id, rule_id)
        meta = rule_meta(canonical)
        rule_id = canonical
    elif category == "schema":
        msg = finding.get("message", "")
        if "order" in msg.lower():
            rule_id, meta = "FMT-007", rule_meta("FMT-007")
        else:
            rule_id, meta = "FMT-008", rule_meta("FMT-008")
    elif category == "dates":
        rule_id, meta = "DT-001", rule_meta("DT-001")
    elif category == "duplicates":
        table = finding.get("table", "")
        if table == "quikmstr":
            rule_id, meta = "POL-001", rule_meta("POL-001")
        elif table == "quikridr":
            rule_id, meta = "DUP-002", rule_meta("DUP-002")
        else:
            rule_id, meta = "DUP-002", {"rule_name": f"Duplicate key in {table}", "severity": "Critical", "disposition": "Block"}
    elif category == "critical":
        field = (finding.get("field") or "").upper()
        table = finding.get("table", "")
        if field == "MRIDRID":
            rule_id, meta = "REQ-002", rule_meta("REQ-002")
        elif field == "MPHASE":
            rule_id, meta = "REQ-003", rule_meta("REQ-003")
        elif field == "MPOLICY" and table == "quikmstr":
            rule_id, meta = "POL-002", rule_meta("POL-002")
        elif field == "DATEPAID":
            rule_id, meta = "PRM-010", rule_meta("PRM-010")
        else:
            rule_id, meta = "REQ-003", {"rule_name": f"Required field {field}", "severity": "Critical", "disposition": "Block"}
    else:
        rule_id, meta = "DT-001", {"rule_name": category, "severity": "Medium", "disposition": "Warning"}

    if legacy_sev == "ERROR" and meta.get("disposition") != "Block":
        meta = dict(meta)
        meta["severity"] = "Critical"
        meta["disposition"] = "Block"
    elif legacy_sev == "WARN":
        meta = dict(meta)
        if meta.get("disposition") == "Block":
            meta["severity"] = "High"
            meta["disposition"] = "Hold"

    return {
        "rule_id": rule_id,
        "rule_name": meta.get("rule_name", rule_id),
        "severity": meta.get("severity", "High"),
        "disposition": meta.get("disposition", "Hold"),
        "table_name": finding.get("table", ""),
        "file_name": os.path.basename(source_path) if source_path else "",
        "key_fields": "MPOLICY" if ctx.get("MPOLICY") else "",
        "key_value": str(ctx.get("MPOLICY", ctx.get("value", ""))),
        "field_name": finding.get("field", "") or "",
        "actual_value": str(ctx.get("value", "")),
        "expected_value": "",
        "message": finding.get("message", ""),
        "source_file": source_path,
        "row_number": finding.get("row", "") or "",
        "created_timestamp": "",
    }
