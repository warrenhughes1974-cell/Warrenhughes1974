"""Report generation for QLAdmin Data Governance."""

from data_governance.reporting.report_writer import write_governance_outputs
from data_governance.reporting.simplified_reports import write_simplified_user_reports

__all__ = ["write_governance_outputs", "write_simplified_user_reports"]
