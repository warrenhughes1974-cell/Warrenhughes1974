"""Governance engine orchestrator.

Pure audit/reporting — never blocks, never modifies data, never stops early.
"""

from __future__ import annotations

import glob
import os
import traceback
from collections import Counter
from datetime import datetime
from typing import Any

import pandas as pd

from data_governance.governance_config import (
    CRITICAL,
    ADVISORY,
    HIGH,
    INFO,
    AuditFinding,
    GovernanceReport,
    make_finding,
)
from data_governance.rules import CHECK_PIPELINE


def _load_csv(path: str) -> pd.DataFrame | None:
    try:
        return pd.read_csv(path, dtype=str, low_memory=False, keep_default_na=False)
    except Exception:
        try:
            return pd.read_csv(path, dtype=str, low_memory=False)
        except Exception:
            return None


def load_conversion_data(conversion_context: dict) -> dict[str, Any]:
    """Load output CSVs (and optional source/crosswalk) into a data dict."""
    data: dict[str, Any] = {"_context": dict(conversion_context)}

    # Pre-supplied dataframes
    for key, val in (conversion_context.get("dataframes") or {}).items():
        data[key] = val

    output_dir = conversion_context.get("output_dir") or ""
    if output_dir and os.path.isdir(output_dir):
        for path in glob.glob(os.path.join(output_dir, "quik*.csv")):
            name = os.path.basename(path)
            key = name.lower()
            if key not in data:
                df = _load_csv(path)
                if df is not None:
                    data[key] = df
                    data[name] = df
        # rates subfolder
        rates_dir = os.path.join(output_dir, "rates")
        if os.path.isdir(rates_dir):
            for path in glob.glob(os.path.join(rates_dir, "quik*.csv")):
                name = os.path.basename(path)
                key = name.lower()
                if key not in data:
                    df = _load_csv(path)
                    if df is not None:
                        data[key] = df

    # Crosswalk
    cw = conversion_context.get("crosswalk_path")
    if cw and os.path.isfile(cw) and "master_crosswalk.csv" not in {k.lower() for k in data}:
        df = _load_csv(cw)
        if df is not None:
            data["Master_Crosswalk.csv"] = df
            data["master_crosswalk.csv"] = df

    # Optional product/setup tables from a product dir
    product_dir = conversion_context.get("product_dir") or ""
    if product_dir and os.path.isdir(product_dir):
        for path in glob.glob(os.path.join(product_dir, "*.csv")):
            name = os.path.basename(path)
            key = name.lower()
            if key not in data:
                df = _load_csv(path)
                if df is not None:
                    data[key] = df

    return data


def _summarize(findings: list[AuditFinding]) -> tuple[dict, dict, dict]:
    by_sev = Counter(f.severity for f in findings)
    by_cat = Counter(f.rule_category for f in findings)
    by_file = Counter(f.source_file for f in findings)
    # Ensure all severity keys present
    for sev in (CRITICAL, HIGH, ADVISORY, INFO):
        by_sev.setdefault(sev, 0)
    return dict(by_sev), dict(by_cat), dict(by_file)


def run_governance(conversion_context: dict) -> GovernanceReport:
    """
    Entry point: run every governance check and return a GovernanceReport.

    conversion_context keys (all optional except paths when loading from disk):
      - conversion_id
      - output_dir
      - source_dir
      - required_source_files
      - crosswalk_path
      - product_dir
      - dataframes (pre-loaded dict)
      - transformation_notes
      - app_table_version / schema_version
      - write_reports (bool, default True)
      - report_dir (defaults to output_dir)
      - progress_callback (optional callable) — presentation only; never affects findings.
            Called as progress_callback(event, **kwargs) with events:
              "load"   — about to / finished loading CSVs
              "check"  — before each rule (index, total, name)
              "report" — about to write report files
              "done"   — audit finished
    """
    ctx = dict(conversion_context or {})
    run_ts = datetime.now().isoformat(timespec="seconds")
    conversion_id = str(ctx.get("conversion_id") or run_ts)
    progress_cb = ctx.get("progress_callback")

    def _progress(event: str, **kwargs: Any) -> None:
        if not callable(progress_cb):
            return
        try:
            progress_cb(event, **kwargs)
        except Exception:
            # Presentation-only — never interrupt the audit.
            pass

    _progress("load")
    data = load_conversion_data(ctx)
    all_findings: list[AuditFinding] = []

    total_steps = len(CHECK_PIPELINE)
    for idx, (step_name, check_fn) in enumerate(CHECK_PIPELINE):
        _progress("check", index=idx, total=total_steps, name=step_name)
        try:
            result = check_fn(data)
            if result is None:
                result = []
            if not isinstance(result, list):
                raise TypeError(f"{check_fn.__name__} returned {type(result)}, expected list")
            all_findings.extend(result)
        except Exception as exc:
            tb = traceback.format_exc()
            all_findings.append(
                make_finding(
                    rule_id="ENGINE-ERROR",
                    rule_category="Engine",
                    severity=CRITICAL,
                    source_file=step_name,
                    description="Governance rule module raised an unexpected exception.",
                    reason=(
                        f"Check '{step_name}' ({check_fn.__name__}) failed with "
                        f"{type(exc).__name__}: {exc}. Remaining checks continue."
                    ),
                    field_name="",
                    expected="check completes",
                    actual=str(exc),
                    affected_keys=[step_name],
                    sample_records=[{"traceback": tb[:2000]}],
                    affected_count=1,
                )
            )

    by_sev, by_cat, by_file = _summarize(all_findings)
    report = GovernanceReport(
        run_timestamp=run_ts,
        conversion_id=conversion_id,
        conversion_source=str(ctx.get("conversion_source") or "LifePRO"),
        conversion_target=str(ctx.get("conversion_target") or "QLA"),
        findings=all_findings,
        total_findings=len(all_findings),
        by_severity=by_sev,
        by_category=by_cat,
        by_file=by_file,
        clean=len(all_findings) == 0,
    )

    if ctx.get("write_reports", True):
        _progress("report")
        try:
            from data_governance.governance_report import write_governance_reports
            report_dir = ctx.get("report_dir") or ctx.get("output_dir") or "."
            write_governance_reports(report, report_dir)
        except Exception as exc:
            # Reporting failure becomes a finding but we still return the report
            report.findings.append(
                make_finding(
                    rule_id="ENGINE-ERROR",
                    rule_category="Engine",
                    severity=CRITICAL,
                    source_file="governance_report",
                    description="Failed to write governance report files.",
                    reason=f"Report writer failed: {type(exc).__name__}: {exc}",
                    field_name="",
                    expected="reports written",
                    actual=str(exc),
                    affected_keys=["governance_report"],
                    affected_count=1,
                )
            )
            report.total_findings = len(report.findings)
            report.by_severity, report.by_category, report.by_file = _summarize(report.findings)
            report.clean = False

    _progress("done", total_findings=report.total_findings, clean=report.clean)
    return report
