"""Governance report generator — HTML, CSV, and plain-text log."""

from __future__ import annotations

import csv
import html
import json
import os
from collections import defaultdict

from data_governance.governance_config import (
    ADVISORY,
    CRITICAL,
    HIGH,
    INFO,
    GovernanceReport,
)

SEVERITY_COLORS = {
    CRITICAL: ("#b91c1c", "#fee2e2"),
    HIGH: ("#c2410c", "#ffedd5"),
    ADVISORY: ("#a16207", "#fef9c3"),
    INFO: ("#1d4ed8", "#dbeafe"),
}

SEVERITY_RANK = {CRITICAL: 0, HIGH: 1, ADVISORY: 2, INFO: 3}


def write_governance_reports(report: GovernanceReport, output_dir: str) -> dict[str, str]:
    """Write governance_audit.html / .csv / .log into output_dir. Returns paths."""
    os.makedirs(output_dir, exist_ok=True)
    paths = {
        "html": os.path.join(output_dir, "governance_audit.html"),
        "csv": os.path.join(output_dir, "governance_audit.csv"),
        "log": os.path.join(output_dir, "governance_audit.log"),
    }
    _write_html(report, paths["html"])
    _write_csv(report, paths["csv"])
    _write_log(report, paths["log"])
    return paths


def _badge(severity: str) -> str:
    fg, bg = SEVERITY_COLORS.get(severity, ("#333", "#eee"))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:4px;font-weight:600;font-size:12px;">{html.escape(severity)}</span>'
    )


def _write_html(report: GovernanceReport, path: str) -> None:
    by_cat: dict[str, list] = defaultdict(list)
    for f in report.findings:
        by_cat[f.rule_category].append(f)

    files_checked = len({f.source_file for f in report.findings if f.source_file})
    n_crit = report.by_severity.get(CRITICAL, 0)
    n_high = report.by_severity.get(HIGH, 0)
    n_adv = report.by_severity.get(ADVISORY, 0)
    n_info = report.by_severity.get(INFO, 0)
    clean_label = "YES" if report.clean else "NO"

    parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        "<title>Data Governance Audit Report</title>",
        "<style>",
        "body{font-family:Segoe UI,Arial,sans-serif;margin:24px;color:#1e293b;background:#f8fafc;}",
        "h1{margin-bottom:4px;} .meta{color:#64748b;margin-bottom:16px;}",
        "table{border-collapse:collapse;width:100%;background:#fff;margin:8px 0 16px;}",
        "th,td{border:1px solid #e2e8f0;padding:6px 8px;text-align:left;vertical-align:top;font-size:13px;}",
        "th{background:#f1f5f9;} details{background:#fff;border:1px solid #e2e8f0;",
        "border-radius:6px;margin:10px 0;padding:8px 12px;}",
        "summary{cursor:pointer;font-weight:600;font-size:15px;}",
        ".reason{color:#334155;} .count{font-weight:600;}",
        ".dash{border:2px solid #334155;background:#fff;padding:0;margin:0 0 20px;max-width:720px;}",
        ".dash-h{background:#1e293b;color:#fff;padding:10px 14px;font-weight:700;}",
        ".dash-row{display:flex;border-top:1px solid #cbd5e1;}",
        ".dash-cell{flex:1;padding:12px;text-align:center;border-right:1px solid #cbd5e1;}",
        ".dash-cell:last-child{border-right:none;}",
        ".dash-n{font-size:28px;font-weight:700;}",
        ".dash-l{font-size:11px;letter-spacing:.04em;color:#64748b;}",
        ".card{border:1px solid #e2e8f0;border-radius:6px;margin:10px 0;padding:10px 12px;background:#fff;}",
        ".card-h{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:6px;}",
        ".card-meta{color:#64748b;font-size:12px;}",
        "</style></head><body>",
        # SUMMARY DASHBOARD
        "<div class='dash'>",
        "<div class='dash-h'>CONVERSION GOVERNANCE AUDIT<br>",
        f"<span style='font-weight:400;font-size:13px'>Conversion ID: {html.escape(report.conversion_id)}"
        f" &nbsp;&nbsp; Run: {html.escape(report.run_timestamp)}</span></div>",
        "<div class='dash-row'>",
        f"<div class='dash-cell'><div class='dash-l'>CRITICAL</div><div class='dash-n' style='color:#b91c1c'>{n_crit}</div></div>",
        f"<div class='dash-cell'><div class='dash-l'>HIGH</div><div class='dash-n' style='color:#c2410c'>{n_high}</div></div>",
        f"<div class='dash-cell'><div class='dash-l'>ADVISORY</div><div class='dash-n' style='color:#a16207'>{n_adv}</div></div>",
        f"<div class='dash-cell'><div class='dash-l'>INFO</div><div class='dash-n' style='color:#1d4ed8'>{n_info}</div></div>",
        "</div>",
        "<div class='dash-row'>",
        f"<div class='dash-cell' style='flex:2;text-align:left'>Files Checked: <b>{files_checked}</b>"
        f" &nbsp;|&nbsp; Total Findings: <b>{report.total_findings}</b></div>",
        f"<div class='dash-cell'>Clean Run: <b>{clean_label}</b></div>",
        "</div></div>",
        f"<div class='meta'>{html.escape(report.conversion_source)} → {html.escape(report.conversion_target)}</div>",
        "<h2>Summary by Category</h2><table><tr><th>Category</th><th>Count</th><th>Jump</th></tr>",
    ]
    for cat, items in sorted(by_cat.items(), key=lambda x: (-len(x[1]), x[0])):
        anchor = html.escape(cat.replace(" ", "_"))
        parts.append(
            f"<tr><td>{html.escape(cat)}</td><td>{len(items)}</td>"
            f"<td><a href='#{anchor}'>View</a></td></tr>"
        )
    parts.append("</table>")

    for cat, items in sorted(by_cat.items(), key=lambda x: x[0]):
        anchor = html.escape(cat.replace(" ", "_"))
        items_sorted = sorted(items, key=lambda f: (SEVERITY_RANK.get(f.severity, 9), f.rule_id))
        parts.append(f"<details open id='{anchor}'><summary>{html.escape(cat)} ({len(items)})</summary>")
        for f in items_sorted:
            sample_html = ""
            if f.sample_records:
                sample_html = "<table><tr>"
                cols = list(f.sample_records[0].keys())
                sample_html += "".join(f"<th>{html.escape(str(c))}</th>" for c in cols) + "</tr>"
                for rec in f.sample_records[:10]:
                    sample_html += "<tr>" + "".join(
                        f"<td>{html.escape(str(rec.get(c, '')))}</td>" for c in cols
                    ) + "</tr>"
                sample_html += "</table>"
            parts.append(
                "<div class='card'>"
                f"<div class='card-h'><b>{html.escape(f.rule_id)}</b> {_badge(f.severity)} "
                f"<span class='card-meta'>{html.escape(f.source_file)} │ {html.escape(f.field_name)}</span></div>"
                f"<div><b>Description:</b> {html.escape(f.description)}</div>"
                f"<div class='reason'><b>Reason:</b> {html.escape(f.reason)}</div>"
                f"<div><b>Expected:</b> {html.escape(f.expected)} &nbsp;|&nbsp; "
                f"<b>Actual:</b> {html.escape(f.actual)}</div>"
                f"<div>Records affected: <span class='count'>{f.affected_count}</span></div>"
                f"<div><b>Sample records:</b> {sample_html or '(none)'}</div>"
                "</div>"
            )
        parts.append("</details>")

    parts.append("</body></html>")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts))


def _write_csv(report: GovernanceReport, path: str) -> None:
    fields = [
        "rule_id", "rule_category", "severity", "source_file", "description",
        "reason", "field_name", "expected", "actual", "affected_keys",
        "affected_count", "sample_records",
    ]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for f in report.findings:
            row = f.to_dict()
            row["affected_keys"] = json.dumps(row.get("affected_keys") or [])
            row["sample_records"] = json.dumps(row.get("sample_records") or [])
            writer.writerow({k: row.get(k, "") for k in fields})


def _write_log(report: GovernanceReport, path: str) -> None:
    lines = [
        f"Data Governance Audit Log | {report.conversion_id} | {report.run_timestamp}",
        f"Total findings: {report.total_findings} | Clean: {report.clean}",
        "-" * 80,
    ]
    for f in report.findings:
        lines.append(
            f"[{f.severity.upper()}] {f.rule_id} | {f.source_file} | {f.field_name} | "
            f"{f.affected_count} affected | {f.reason}"
        )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
