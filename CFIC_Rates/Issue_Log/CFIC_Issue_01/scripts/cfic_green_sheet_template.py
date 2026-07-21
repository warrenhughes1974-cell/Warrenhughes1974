"""P7-style green-sheet layout template (4x render scale)."""

from __future__ import annotations

from dataclasses import dataclass

RENDER_SCALE = 4.0

# Body row grid — calibrated from P7MN/18.pdf (cash_value=21 at duration 10, y≈828).
ROW_Y0 = 460.6
ROW_HEIGHT = 38.67
ROWS_PER_PAGE = 49

P7MN_RENEWAL_NET = "5.385586"

# Column x-bounds on 4x render (4281px width).
COLUMN_BOXES_4X: dict[str, tuple[int, int]] = {
    "renewal_net": (520, 800),
    "terminal_reserve": (910, 1095),
    "mean_reserve": (1280, 1465),
    "cash_value": (1675, 1815),
    "paid_up": (1920, 2030),
    "eti_years": (2040, 2145),
    "eti_days": (2145, 2260),
    "pure_end": (2260, 2380),
    "inforce": (2380, 2580),
}

HEADER_BAND = (0.055, 0.165)  # fraction of page height
BODY_BAND = (0.17, 0.945)


@dataclass(frozen=True)
class PageGrid:
    y0: float
    row_height: float
    rows_on_page: int


def row_center(grid: PageGrid, duration_on_page: int) -> float:
    return grid.y0 + (duration_on_page - 1) * grid.row_height + grid.row_height / 2


def default_grid() -> PageGrid:
    return PageGrid(ROW_Y0, ROW_HEIGHT, ROWS_PER_PAGE)
