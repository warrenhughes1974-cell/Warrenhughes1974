"""Data Conformance Accuracy calculation for governance runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ACCURACY_UNAVAILABLE_ZERO = "Not Available — No records were evaluated"
ACCURACY_UNAVAILABLE_RECONCILE = "Unavailable"
RECONCILE_WARNING = (
    "Data Conformance Accuracy could not be calculated because the reviewed, "
    "conforming, and problem counts did not reconcile."
)
ACCURACY_MEANING = (
    "Data Conformance Accuracy represents the percentage of evaluated records "
    "that matched the active governance rules during this run. It does not "
    "independently confirm that every value is factually or actuarially correct."
)
ACCURACY_SHORT = "{display} of the record checks completed without a governance exception."


@dataclass(frozen=True)
class ConformanceAccuracy:
    records_reviewed: int
    looked_fine: int
    problems_found: int
    percent_raw: float | None
    percent_display: str
    reconciles: bool
    warning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "Records_Reviewed": self.records_reviewed,
            "Looked_Fine": self.looked_fine,
            "Problems_Found": self.problems_found,
            "Data_Conformance_Accuracy_Percent": self.percent_raw,
            "Data_Conformance_Accuracy_Display": self.percent_display,
            "counts_reconcile": self.reconciles,
            "warning": self.warning,
            "interpretation": ACCURACY_MEANING,
        }


def calculate_conformance_accuracy(
    *,
    records_reviewed: int,
    looked_fine: int,
    problems_found: int,
) -> ConformanceAccuracy:
    """Compute Data Conformance Accuracy from existing evaluation totals.

    Formula: Looked_Fine / Records_Reviewed * 100 when counts reconcile and
    Records_Reviewed > 0. Does not change the meaning of the input counts.
    """
    reviewed = int(records_reviewed)
    fine = int(looked_fine)
    problems = int(problems_found)
    reconciles = reviewed == fine + problems

    if reviewed == 0:
        return ConformanceAccuracy(
            records_reviewed=reviewed,
            looked_fine=fine,
            problems_found=problems,
            percent_raw=None,
            percent_display=ACCURACY_UNAVAILABLE_ZERO,
            reconciles=reconciles,
            warning="" if reconciles else RECONCILE_WARNING,
        )

    if not reconciles:
        return ConformanceAccuracy(
            records_reviewed=reviewed,
            looked_fine=fine,
            problems_found=problems,
            percent_raw=None,
            percent_display=ACCURACY_UNAVAILABLE_RECONCILE,
            reconciles=False,
            warning=RECONCILE_WARNING,
        )

    raw = (fine / reviewed) * 100.0
    display = f"{raw:.2f}%"
    return ConformanceAccuracy(
        records_reviewed=reviewed,
        looked_fine=fine,
        problems_found=problems,
        percent_raw=raw,
        percent_display=display,
        reconciles=True,
        warning="",
    )


def format_accuracy_short(display: str) -> str:
    if display in (ACCURACY_UNAVAILABLE_ZERO, ACCURACY_UNAVAILABLE_RECONCILE):
        return display
    return ACCURACY_SHORT.format(display=display)
