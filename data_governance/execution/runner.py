"""Rule execution orchestration for QLAdmin Data Governance."""

from __future__ import annotations

import os
import traceback
from collections.abc import Callable
from datetime import datetime
from typing import Any

from data_governance.catalog.registry import required_tables_for, select_rules
from data_governance.config.settings import GovernancePaths, resolve_output_base
from data_governance.data_access.region_path import (
    DataRegionPathError,
    validate_data_region_path,
)
from data_governance.data_access.table_loader import load_governance_tables
from data_governance.data_access.table_resolver import TableResolver
from data_governance.models.findings import (
    GovernanceRunResult,
    RuleExecutionResult,
    make_finding,
    new_run_id,
)
from data_governance.models.statuses import STATUS_ERROR, STATUS_NOT_RUN
from data_governance.reporting.report_writer import write_governance_outputs


ProgressCallback = Callable[..., None]


class _RunLog:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def write(self, message: str) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.lines.append(f"[{stamp}] {message}")

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(self.lines).rstrip() + "\n")


def run_data_governance(
    *,
    data_dir: str | None = None,
    input_path: str | None = None,
    output_dir: str | None = None,
    output_path: str | None = None,
    governance_item_id: str | None = None,
    rule_id: str | None = None,
    write_reports: bool = True,
    isolate_run_folder: bool = True,
    require_explicit_input: bool = False,
    preloaded_tables: dict[str, list[dict[str, Any]]] | None = None,
    progress_callback: ProgressCallback | None = None,
) -> GovernanceRunResult:
    """Run selected governance rules against a QLAdmin data region.

    Parameters
    ----------
    data_dir / input_path:
        Folder containing QLAdmin DBF files (the data region).
    output_dir / output_path:
        Base folder for reports. Each run writes to ``<base>/<run_id>/`` when
        ``isolate_run_folder`` is True.
    """
    region_arg = input_path if input_path is not None else data_dir
    output_arg = output_path if output_path is not None else output_dir

    run_id, run_timestamp = new_run_id()
    log = _RunLog()
    log.write("QLAdmin Data Governance run starting")
    log.write(f"Run ID: {run_id}")

    # Resolve / validate data region
    try:
        if preloaded_tables is not None and not region_arg:
            resolved_data = "(memory)"
        else:
            if region_arg is None or not str(region_arg).strip():
                # Optional env fallback for app wiring; CLI run requires --input
                env = os.environ.get("QLA_GOVERNANCE_DATA_DIR", "").strip()
                region_arg = env or None
            resolved_data = validate_data_region_path(
                region_arg,
                require_explicit=require_explicit_input and preloaded_tables is None,
            )
    except DataRegionPathError as exc:
        output_base = resolve_output_base(output_arg)
        run_folder = (
            os.path.join(output_base, run_id) if isolate_run_folder else output_base
        )
        result = GovernanceRunResult(
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_dir=str(region_arg or ""),
            output_dir=run_folder,
            output_base=output_base,
            source_opened_read_only=True,
            source_files_modified=False,
        )
        result.rule_results.append(
            RuleExecutionResult(
                governance_item_id=governance_item_id or "",
                rule_id=rule_id or "PATH",
                rule_name="Data region validation",
                business_name="Data region validation",
                severity="Critical",
                status=STATUS_ERROR,
                error_count=1,
                error_message=str(exc),
                findings=[
                    make_finding(
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        governance_item_id=governance_item_id or "",
                        rule_id=rule_id or "PATH",
                        rule_name="Data region validation",
                        business_name="Data region validation",
                        description="Validate the selected QLAdmin data region",
                        severity="Critical",
                        status=STATUS_ERROR,
                        source_table="",
                        source_field="",
                        message=str(exc),
                        data_region_path=str(region_arg or ""),
                    )
                ],
            )
        )
        result.finalize()
        log.write(f"ERROR: {exc}")
        if write_reports:
            os.makedirs(run_folder, exist_ok=True)
            paths = GovernancePaths(result.data_dir, run_folder)
            write_governance_outputs(result, paths)
            log.save(paths.run_log)
            result.run_log_path = paths.run_log
        return result

    output_base = resolve_output_base(output_arg)
    run_folder = os.path.join(output_base, run_id) if isolate_run_folder else output_base

    if rule_id:
        scope = "rule"
    elif governance_item_id:
        scope = "item"
    else:
        scope = "all"
    result = GovernanceRunResult(
        run_id=run_id,
        run_timestamp=run_timestamp,
        data_dir=resolved_data,
        output_dir=run_folder,
        output_base=output_base,
        source_opened_read_only=True,
        source_files_modified=False,
        review_scope=scope,
        selected_governance_item_id=(governance_item_id or "").strip().upper(),
        selected_rule_id=(rule_id or "").strip().upper(),
    )
    log.write(f"Data region: {resolved_data}")
    log.write(f"Output base: {output_base}")
    log.write(f"Run folder: {run_folder}")
    log.write(f"Review scope: {scope}")
    log.write("Source DBF files will be opened read-only; source files are never modified")

    def _progress(event: str, **kwargs: Any) -> None:
        if progress_callback is None:
            return
        try:
            progress_callback(event, **kwargs)
        except Exception:
            pass

    try:
        rules = select_rules(rule_id=rule_id, governance_item_id=governance_item_id)
    except KeyError as exc:
        result.rule_results.append(
            RuleExecutionResult(
                governance_item_id=governance_item_id or "",
                rule_id=rule_id or "",
                rule_name="Selection",
                business_name="Rule selection",
                severity="Critical",
                status=STATUS_ERROR,
                error_count=1,
                error_message=str(exc),
                findings=[
                    make_finding(
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        governance_item_id=governance_item_id or "",
                        rule_id=rule_id or "SELECTION",
                        rule_name="Selection",
                        business_name="Rule selection",
                        description="Select governance rules for execution",
                        severity="Critical",
                        status=STATUS_ERROR,
                        source_table="",
                        source_field="",
                        message=str(exc),
                        data_region_path=resolved_data,
                    )
                ],
            )
        )
        result.finalize()
        if write_reports:
            os.makedirs(run_folder, exist_ok=True)
            paths = GovernancePaths(resolved_data, run_folder)
            write_governance_outputs(result, paths)
            log.write(str(exc))
            log.save(paths.run_log)
            result.run_log_path = paths.run_log
        return result

    _progress("load", data_dir=resolved_data)
    table_names = required_tables_for(rules)
    resolver = (
        None
        if resolved_data == "(memory)"
        else TableResolver(resolved_data)
    )
    store = load_governance_tables(
        resolved_data if resolved_data != "(memory)" else "",
        logical_names=table_names,
        preloaded=preloaded_tables,
        resolver=resolver,
    )
    store.data_dir = resolved_data
    for name, err in store.load_errors.items():
        log.write(f"Table load note — {name}: {err}")

    total = len(rules)
    for index, registered in enumerate(rules):
        definition = registered.definition
        _progress(
            "check",
            index=index,
            total=total,
            name=definition.rule_id,
            business_name=definition.business_name,
        )
        log.write(f"Executing {definition.rule_id} — {definition.business_name}")

        # Validate required tables for this rule only; do not stop the run.
        # DG-PLANVALUES evaluates each source table independently — missing individual
        # plan-value sources (or a reference) are handled inside the rule.
        missing = [t for t in definition.source_tables if store.missing(t)]
        if (
            missing
            and preloaded_tables is None
            and definition.governance_item_id
            not in (
                "DG-PLANVALUES",
                "DG-QUIKPLAN",
                "DG-QUIKMSTR",
                "DG-QUIKCLNT",
                "DG-QUIKCLID",
            )
        ):
            msg = (
                f"Required table(s) not found in data region '{resolved_data}': "
                + ", ".join(missing)
            )
            log.write(f"ERROR (rule isolated): {msg}")
            rule_result = RuleExecutionResult(
                governance_item_id=definition.governance_item_id,
                rule_id=definition.rule_id,
                rule_name=definition.technical_name,
                business_name=definition.business_name,
                severity=definition.severity,
                status=STATUS_ERROR,
                error_count=1,
                error_message=msg,
                findings=[
                    make_finding(
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        governance_item_id=definition.governance_item_id,
                        rule_id=definition.rule_id,
                        rule_name=definition.technical_name,
                        business_name=definition.business_name,
                        description=definition.purpose,
                        severity=definition.severity,
                        status=STATUS_ERROR,
                        source_table=", ".join(definition.source_tables),
                        source_field=", ".join(definition.source_fields),
                        message=msg,
                        data_region_path=resolved_data,
                        expected_condition="Required DBF/CSV present in data region",
                        actual_condition="Missing: " + ", ".join(missing),
                    )
                ],
            )
            result.rule_results.append(rule_result)
            continue
        if missing and definition.governance_item_id in (
            "DG-PLANVALUES",
            "DG-QUIKPLAN",
            "DG-QUIKMSTR",
            "DG-QUIKCLNT",
            "DG-QUIKCLID",
        ):
            log.write(
                f"Note: {definition.rule_id} continuing with unavailable table(s): "
                + ", ".join(missing)
            )

        try:
            rule_result = registered.execute(
                store,
                run_id=run_id,
                run_timestamp=run_timestamp,
            )
        except Exception as exc:
            log.write(f"Processing error in {definition.rule_id}: {exc}")
            rule_result = RuleExecutionResult(
                governance_item_id=definition.governance_item_id,
                rule_id=definition.rule_id,
                rule_name=definition.technical_name,
                business_name=definition.business_name,
                severity=definition.severity,
                status=STATUS_ERROR,
                error_count=1,
                error_message=f"{exc}",
                findings=[
                    make_finding(
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        governance_item_id=definition.governance_item_id,
                        rule_id=definition.rule_id,
                        rule_name=definition.technical_name,
                        business_name=definition.business_name,
                        description=definition.purpose,
                        severity=definition.severity,
                        status=STATUS_ERROR,
                        source_table=", ".join(definition.source_tables),
                        source_field=", ".join(definition.source_fields),
                        message=f"Processing error while running {definition.rule_id}: {exc}",
                        data_region_path=resolved_data,
                        actual_condition=traceback.format_exc(limit=3),
                    )
                ],
            )

        for finding in rule_result.findings:
            if not finding.data_region_path:
                finding.data_region_path = resolved_data
        log.write(
            f"Finished {definition.rule_id}: status={rule_result.status} "
            f"passed={rule_result.passed_count} failed={rule_result.failed_count} "
            f"errors={rule_result.error_count}"
        )
        result.rule_results.append(rule_result)

    result.finalize()
    log.write(f"Overall status: {result.overall_status}")
    log.write("Source files modified: No")
    log.write(
        f"Evaluation totals: reviewed={result.records_evaluated} "
        f"looked_fine={result.passed_count} problems={result.failed_count}"
    )

    if write_reports:
        _progress("report", output_dir=run_folder)
        os.makedirs(run_folder, exist_ok=True)
        paths = GovernancePaths(resolved_data, run_folder)
        write_governance_outputs(result, paths)
        if result.what_was_checked_path:
            log.write(f"What Was Checked: {result.what_was_checked_path}")
        if result.items_needing_attention_path:
            log.write(f"Items Needing Attention: {result.items_needing_attention_path}")
        if result.business_overall_result:
            log.write(f"Business result: {result.business_overall_result}")
        if result.data_conformance_accuracy_display:
            log.write(
                f"Percentage passed (completed checks): "
                f"{result.data_conformance_accuracy_display}"
            )
        for warning in result.report_warnings:
            log.write(f"WARNING: {warning}")
        log.write(f"Internal technical folder: {paths.internal_dir}")
        log.save(paths.run_log)
        result.run_log_path = paths.run_log

    _progress(
        "done",
        overall_status=result.overall_status,
        failed_count=result.failed_count,
        error_count=result.error_count,
        total_findings=len(result.findings),
    )
    return result
