"""Layout template for Citizens PermaLife 7 rate sheets (2x PDF render)."""
from __future__ import annotations

from dataclasses import dataclass

RENDER_SCALE = 2

# Column x bounds at 2x render (1224px wide pages) — tuned on CNB p4 P7MN adult.
COLUMN_BOXES = {
    "rate_under_100k": (468, 545),
    "rate_over_100k": (545, 625),
    "cash_value_10": (625, 710),
    "cash_value_20": (710, 800),
    "cash_value_65": (790, 900),
    "paid_up_10": (900, 990),
    "paid_up_20": (990, 1080),
    "paid_up_65": (1080, 1180),
}

AGE_COL_SINGLE = (395, 435)


@dataclass(frozen=True)
class SheetSpec:
    pdf: str
    page_index: int  # 0-based
    cfic_plan: str
    ql_plan: str
    gender: str  # F / M
    uwclass: str  # NS / SM
    age_min: int
    age_max: int
    layout: str  # single | dual_juvenile
    side: str  # left / right / na


# CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf (0-based page index)
PERMALIFE7_SHEETS: list[SheetSpec] = [
    SheetSpec("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 0, "P7FN", "10P7FN", "F", "NS", 0, 17, "dual_juvenile", "left"),
    SheetSpec("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 0, "P7MN", "10P7MN", "M", "NS", 0, 17, "dual_juvenile", "right"),
    SheetSpec("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 1, "P7FS", "10P7FS", "F", "SM", 0, 17, "dual_juvenile", "left"),
    SheetSpec("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 1, "P7MS", "10P7MS", "M", "SM", 0, 17, "dual_juvenile", "right"),
    SheetSpec("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 2, "P7FN", "10P7FN", "F", "NS", 18, 70, "single", "na"),
    SheetSpec("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 3, "P7MN", "10P7MN", "M", "NS", 18, 70, "single", "na"),
    SheetSpec("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 4, "P7FS", "10P7FS", "F", "SM", 18, 70, "single", "na"),
    SheetSpec("CurrentNewBusiness_PlanCodes_Rates SheetsHold.pdf", 4, "P7MS", "10P7MS", "M", "SM", 18, 70, "single", "na"),
]

STAGING_FIELDS = [
    "cfic_plan",
    "ql_plan",
    "gender",
    "uwclass",
    "age",
    "rate_under_100k",
    "rate_over_100k",
    "cash_value_10",
    "cash_value_20",
    "cash_value_65",
    "paid_up_10",
    "paid_up_20",
    "paid_up_65",
    "source_pdf",
    "source_page",
    "extract_method",
    "extract_confidence",
]
