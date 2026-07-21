"""CFIC Issue #02 — extract gross premium / illustration values from docs PDF rate sheets."""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import cv2
import fitz
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cfic_permalife7_template import (
    AGE_COL_SINGLE,
    COLUMN_BOXES,
    PERMALIFE7_SHEETS,
    RENDER_SCALE,
    STAGING_FIELDS,
    SheetSpec,
)

ROOT = Path(__file__).resolve().parents[3]  # CFIC_Rates
DOCS = ROOT / "docs"
STAGING_ROOT = ROOT / "extracted_pdf_rates" / "staging"

_READER = None


def get_reader():
    global _READER
    if _READER is None:
        import easyocr

        _READER = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _READER


def render_page(pdf_path: Path, page_index: int) -> np.ndarray:
    doc = fitz.open(pdf_path)
    page = doc[page_index]
    pix = page.get_pixmap(matrix=fitz.Matrix(RENDER_SCALE, RENDER_SCALE))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    doc.close()
    return img


def ocr_cell(img: np.ndarray, yc: int, x0: int, x1: int, *, integer: bool = False) -> tuple[str, float]:
    ya, yb = yc - 14, yc + 16
    cell = img[ya:yb, x0:x1]
    if cell.size == 0:
        return "", 0.0
    cell = cv2.resize(cell, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    allow = "0123456789" if integer else "0123456789."
    res = get_reader().readtext(cell, allowlist=allow, detail=1, paragraph=False)
    if not res:
        return "", 0.0
    best = max(res, key=lambda t: t[2])
    text = best[1].strip()
    if integer:
        m = re.search(r"\d+", text.replace(",", ""))
        return (m.group(0) if m else ""), float(best[2])
    cleaned = re.sub(r"[^0-9.]", "", text.replace(",", ""))
    if cleaned in {"", "."}:
        return "", float(best[2])
    return cleaned, float(best[2])


def detect_age_rows(img: np.ndarray, spec: SheetSpec) -> dict[int, int]:
    if spec.layout == "dual_juvenile":
        # TODO: dual-table juvenile layout — Phase 2
        return {}
    x0, x1 = AGE_COL_SINGLE
    crop = img[250:1500, x0:x1]
    res = get_reader().readtext(crop, allowlist="0123456789", detail=1, paragraph=False)
    found: dict[int, int] = {}
    for box, text, conf in res:
        t = text.strip()
        if not re.fullmatch(r"\d{1,2}", t):
            continue
        age = int(t)
        if age < spec.age_min or age > spec.age_max:
            continue
        yc = int((box[0][1] + box[3][1]) / 2) + 250
        if age not in found or conf > 0.9:
            found[age] = yc
    if not found:
        return {}
    # Interpolate missing ages between detected anchors.
    ages_sorted = sorted(found)
    y_sorted = [found[a] for a in ages_sorted]
    if len(ages_sorted) >= 2:
        step = (y_sorted[-1] - y_sorted[0]) / (ages_sorted[-1] - ages_sorted[0])
        for age in range(spec.age_min, spec.age_max + 1):
            if age not in found:
                found[age] = int(y_sorted[0] + (age - ages_sorted[0]) * step)
    return found


def extract_sheet(spec: SheetSpec) -> list[dict[str, str]]:
    pdf_path = DOCS / spec.pdf
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    if spec.layout == "dual_juvenile":
        print(f"SKIP dual juvenile (Phase 2): {spec.cfic_plan} p{spec.page_index + 1}")
        return []

    img = render_page(pdf_path, spec.page_index)
    age_rows = detect_age_rows(img, spec)
    if not age_rows:
        print(f"WARN no ages: {spec.cfic_plan} p{spec.page_index + 1}")
        return []

    rows: list[dict[str, str]] = []
    for age in range(spec.age_min, spec.age_max + 1):
        yc = age_rows.get(age)
        if yc is None:
            continue
        vals: dict[str, str] = {}
        confs: list[float] = []
        for field, (xa, xb) in COLUMN_BOXES.items():
            integer = field.startswith("cash_value") or field.startswith("paid_up")
            text, conf = ocr_cell(img, yc, xa, xb, integer=integer)
            vals[field] = text
            if text:
                confs.append(conf)
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        rows.append(
            {
                "cfic_plan": spec.cfic_plan,
                "ql_plan": spec.ql_plan,
                "gender": spec.gender,
                "uwclass": spec.uwclass,
                "age": str(age),
                **vals,
                "source_pdf": spec.pdf,
                "source_page": str(spec.page_index + 1),
                "extract_method": "easyocr_permalife7_v1",
                "extract_confidence": f"{avg_conf:.3f}",
            }
        )
    return rows


def write_staging(spec: SheetSpec, rows: list[dict[str, str]]) -> Path:
    out_dir = STAGING_ROOT / spec.cfic_plan
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{spec.cfic_plan}_p{spec.page_index + 1}_{spec.gender}_{spec.uwclass}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=STAGING_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract CFIC docs PDF rate sheets")
    parser.add_argument(
        "--plans",
        default="P7MN",
        help="Comma-separated CFIC plan codes (default P7MN pilot)",
    )
    parser.add_argument("--all-permalife7", action="store_true", help="Extract all PermaLife 7 single-table sheets")
    args = parser.parse_args()

    if args.all_permalife7:
        targets = {s.cfic_plan for s in PERMALIFE7_SHEETS if s.layout == "single"}
    else:
        targets = {p.strip().upper() for p in args.plans.split(",") if p.strip()}

    selected = [s for s in PERMALIFE7_SHEETS if s.cfic_plan in targets]
    if not selected:
        raise SystemExit(f"No sheet specs for plans: {targets}")

    total = 0
    for spec in selected:
        rows = extract_sheet(spec)
        if not rows:
            continue
        path = write_staging(spec, rows)
        print(f"Wrote {len(rows)} rows -> {path}")
        total += len(rows)
    print(f"Done. {total} staging rows.")


if __name__ == "__main__":
    main()
