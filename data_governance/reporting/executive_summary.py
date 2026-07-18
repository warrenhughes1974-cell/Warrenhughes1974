"""Executive Summary section for the human-readable governance report."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from data_governance.catalog.governance_items import ALL_GOVERNANCE_ITEMS, ALL_RULE_DEFINITIONS
from data_governance.models.findings import GovernanceRunResult
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_NOT_RUN, STATUS_PASS
from data_governance.reporting.accuracy import (
    ACCURACY_MEANING,
    ConformanceAccuracy,
    format_accuracy_short,
)


def format_business_datetime(run_timestamp: str) -> str:
    """Format 'YYYY-MM-DD HH:MM:SS' as 'July 18, 2026 at 10:25:28 AM'."""
    try:
        dt = datetime.strptime(run_timestamp.strip(), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return run_timestamp
    hour = dt.strftime("%I").lstrip("0") or "12"
    return f"{dt.strftime('%B')} {dt.day}, {dt.year} at {hour}:{dt.strftime('%M:%S %p')}"


def _plain_status_local(status: str) -> str:
    mapping = {
        "PASS": "PASSED — no problems found",
        "FAIL": "FAILED — problems were found that need attention",
        "ERROR": "ERROR — the check could not finish (usually a missing file)",
        "NOT_RUN": "NOT RUN — this check was not executed",
    }
    return mapping.get(status, status)


def count_rule_statuses(result: GovernanceRunResult) -> dict[str, int]:
    counts = {
        "executed": len(result.rule_results),
        "passed": 0,
        "failed": 0,
        "not_run": 0,
        "error": 0,
    }
    for rule in result.rule_results:
        if rule.status == STATUS_PASS:
            counts["passed"] += 1
        elif rule.status == STATUS_FAIL:
            counts["failed"] += 1
        elif rule.status == STATUS_ERROR:
            counts["error"] += 1
        elif rule.status == STATUS_NOT_RUN:
            counts["not_run"] += 1
    return counts


def governance_items_executed(result: GovernanceRunResult) -> list[str]:
    item_map = {item.item_id: item for item in ALL_GOVERNANCE_ITEMS}
    seen: list[str] = []
    for rule in result.rule_results:
        item_id = rule.governance_item_id
        if item_id and item_id not in seen:
            seen.append(item_id)
    labels = []
    for item_id in seen:
        item = item_map.get(item_id)
        if item:
            labels.append(f"{item.item_id} — {item.name}")
        else:
            labels.append(item_id)
    return labels


def build_top_issues(result: GovernanceRunResult, *, limit: int = 8) -> list[str]:
    """Concise business-language top issues from FAIL findings only."""
    fail_findings = [f for f in result.findings if f.status == STATUS_FAIL]
    if not fail_findings:
        return []

    by_rule: dict[str, list] = defaultdict(list)
    for finding in fail_findings:
        by_rule[finding.rule_id].append(finding)

    defn_by_id = {d.rule_id: d for d in ALL_RULE_DEFINITIONS}
    ranked = sorted(by_rule.items(), key=lambda kv: (-len(kv[1]), kv[0]))

    issues: list[str] = []
    for rule_id, findings in ranked[:limit]:
        count = len(findings)
        definition = defn_by_id.get(rule_id)
        business = definition.business_name if definition else findings[0].business_name
        noun = "record" if count == 1 else "records"
        # Prefer a short message derived from the first finding when it already
        # names the business issue clearly.
        sample = findings[0].message
        if count == 1:
            issues.append(sample)
        else:
            issues.append(
                f"{count} {noun} failed '{business}' "
                f"(example: {sample})"
            )
    return issues


def build_executive_summary_lines(
    result: GovernanceRunResult,
    accuracy: ConformanceAccuracy,
) -> list[str]:
    statuses = count_rule_statuses(result)
    items = governance_items_executed(result)
    top_issues = build_top_issues(result)

    lines: list[str] = []
    lines.append("# QLAdmin Data Governance Executive Summary")
    lines.append("")
    lines.append("## Overall Result")
    lines.append("")
    lines.append(_plain_status_local(result.overall_status))
    lines.append("")
    lines.append("## Run Snapshot")
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append(f"| Data Region | `{result.data_dir}` |")
    lines.append(f"| Run ID | `{result.run_id}` |")
    lines.append(f"| Run Date | {format_business_datetime(result.run_timestamp)} |")
    lines.append(
        "| Governance Items Executed | "
        + (", ".join(items) if items else "(none)")
        + " |"
    )
    lines.append(f"| Rules Executed | {statuses['executed']:,} |")
    lines.append(f"| Rules Passed | {statuses['passed']:,} |")
    lines.append(f"| Rules Failed | {statuses['failed']:,} |")
    lines.append(f"| Rules Not Run | {statuses['not_run']:,} |")
    lines.append(f"| Rules with Processing Errors | {statuses['error']:,} |")
    lines.append(f"| Total Records Reviewed | {accuracy.records_reviewed:,} |")
    lines.append(f"| Records That Looked Fine | {accuracy.looked_fine:,} |")
    lines.append(f"| Problems Found | {accuracy.problems_found:,} |")
    lines.append(f"| Data Conformance Accuracy | **{accuracy.percent_display}** |")
    lines.append("")
    lines.append("## Data Conformance Accuracy")
    lines.append("")
    lines.append(f"**{accuracy.percent_display}**")
    lines.append("")
    lines.append(format_accuracy_short(accuracy.percent_display))
    lines.append("")
    lines.append(ACCURACY_MEANING)
    lines.append("")
    if accuracy.warning:
        lines.append(f"**Warning:** {accuracy.warning}")
        lines.append("")

    lines.append("## Top Issues")
    lines.append("")
    if not top_issues:
        if result.overall_status == "PASS":
            lines.append("No significant issues were found in this run.")
        else:
            lines.append(
                "No detailed problem findings were recorded. "
                "See rule results below for processing errors or incomplete checks."
            )
    else:
        for i, issue in enumerate(top_issues, start=1):
            lines.append(f"{i}. {issue}")
    lines.append("")
    return lines
