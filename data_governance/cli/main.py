"""Command-line entry for QLAdmin Data Governance."""

from __future__ import annotations

import argparse
import sys

from data_governance.execution.runner import run_data_governance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m data_governance",
        description=(
            "QLAdmin Data Governance — evaluate any QLAdmin data region "
            "(folder of DBF files) and write isolated run reports."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser(
        "run",
        help="Run governance checks against a QLAdmin data region",
    )
    run_p.add_argument(
        "--input",
        "--data-dir",
        dest="input_path",
        required=True,
        help="QLAdmin data-region path (folder containing Quik*.dbf files).",
    )
    run_p.add_argument(
        "--output",
        "--output-dir",
        dest="output_path",
        default=None,
        help=(
            "Output base folder for reports. Each run writes to "
            "<output>/<run_id>/ unless --no-run-subfolder is set."
        ),
    )
    group = run_p.add_mutually_exclusive_group()
    group.add_argument(
        "--all",
        action="store_true",
        help="Run all registered governance rules (default when no filter is given).",
    )
    group.add_argument(
        "--item",
        dest="governance_item_id",
        default=None,
        help="Run one governance item (e.g. DG-QUIKCOMP or DG-QUIKMSTR).",
    )
    group.add_argument(
        "--rule",
        dest="rule_id",
        default=None,
        help="Run one rule by ID (e.g. DG-QUIKCOMP-001 or DG-QUIKMSTR-001).",
    )
    run_p.add_argument(
        "--no-reports",
        action="store_true",
        help="Execute checks without writing report files.",
    )
    run_p.add_argument(
        "--no-run-subfolder",
        action="store_true",
        help="Write reports directly into --output instead of <output>/<run_id>/.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Allow `python -m data_governance --input ...` by implying the `run` command
    if argv and argv[0] not in ("run", "-h", "--help"):
        argv = ["run", *argv]

    parser = build_parser()
    args = parser.parse_args(argv)

    result = run_data_governance(
        input_path=args.input_path,
        output_path=args.output_path,
        governance_item_id=args.governance_item_id,
        rule_id=args.rule_id,
        write_reports=not args.no_reports,
        isolate_run_folder=not args.no_run_subfolder,
        require_explicit_input=True,
    )

    print("QLAdmin Data Governance")
    print(f"  Run ID:            {result.run_id}")
    print(f"  Timestamp:         {result.run_timestamp}")
    print(f"  Data region:       {result.data_dir}")
    print(f"  Output base:       {result.output_base}")
    print(f"  Run folder:        {result.output_dir}")
    print(f"  Rules executed:    {', '.join(result.rules_executed) or '(none)'}")
    print(f"  Records evaluated: {result.records_evaluated}")
    print(f"  Passed:            {result.passed_count}")
    print(f"  Failed:            {result.failed_count}")
    print(f"  Errors:            {result.error_count}")
    if result.data_conformance_accuracy_display:
        print(f"  Conformance:       {result.data_conformance_accuracy_display}")
    print(f"  Overall status:    {result.overall_status}")
    print(f"  Source read-only:  {result.source_opened_read_only}")
    print(f"  Source modified:   {result.source_files_modified}")
    if result.results_csv_path:
        print(f"  Results CSV:       {result.results_csv_path}")
    if result.findings_csv_path:
        print(f"  Findings CSV:      {result.findings_csv_path}")
    if result.summary_csv_path:
        print(f"  Summary CSV:       {result.summary_csv_path}")
    if result.report_md_path:
        print(f"  Report:            {result.report_md_path}")
    if result.validation_guide_path:
        print(f"  Validation guide:  {result.validation_guide_path}")
    if result.validation_manifest_path:
        print(f"  Validation JSON:   {result.validation_manifest_path}")
    if result.run_log_path:
        print(f"  Log:               {result.run_log_path}")

    if result.overall_status == "ERROR":
        return 2
    if result.overall_status == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
