"""CFIC Issue #01 Wave 1 — one-time green-sheet OCR extract (standalone)."""
from __future__ import annotations

import argparse
import csv
import re
import zipfile
from pathlib import Path

import cv2
import fitz
import numpy as np

from cfic_green_sheet_template import (
    BODY_BAND,
    COLUMN_BOXES_4X,
    HEADER_BAND,
    P7MN_RENEWAL_NET,
    RENDER_SCALE,
    PageGrid,
    default_grid,
    row_center,
)

ROOT = Path(__file__).resolve().parents[3]
STAGING_ROOT = ROOT / "extracted_green_sheets" / "staging"
ZIP_PATH = ROOT / "CFIC_Cash_Values" / "P7MN_CV.zip"

STAGING_FIELDS = [
    "source_plan",
    "ql_plan",
    "issue_age",
    "duration",
    "renewal_net",
    "terminal_reserve",
    "mean_reserve",
    "cash_value",
    "paid_up",
    "eti_years",
    "eti_days",
    "pure_end",
    "inforce_unit",
    "gender",
    "uwclass",
    "band",
    "source_file",
    "source_page",
    "extract_method",
    "extract_confidence",
]

_READER = None


def get_reader():
    global _READER
    if _READER is None:
        import easyocr

        _READER = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _READER


def preprocess_page(img: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    b, g, r = cv2.split(img)
    mask = (g.astype(int) > r.astype(int) + 15) & (g.astype(int) > b.astype(int) + 15)
    clean = img.copy()
    clean[mask] = (255, 255, 255)
    gray = cv2.cvtColor(clean, cv2.COLOR_BGR2GRAY)
    return clean, gray


def render_pdf_page(pdf_bytes: bytes, page_index: int) -> np.ndarray:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_index]
    mat = fitz.Matrix(RENDER_SCALE, RENDER_SCALE)
    pix = page.get_pixmap(matrix=mat)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    doc.close()
    return img


def ocr_text_region(gray: np.ndarray, ya: int, yb: int, xa: int, xb: int, allowlist: str) -> tuple[str, float]:
    cell = gray[ya:yb, xa:xb]
    if cell.size == 0:
        return "", 0.0
    cell = cv2.resize(cell, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    res = get_reader().readtext(cell, allowlist=allowlist, detail=1, paragraph=False)
    if not res:
        return "", 0.0
    best = max(res, key=lambda t: t[2])
    return best[1].strip(), float(best[2])


def normalize_decimal(text: str) -> str:
    cleaned = text.replace(",", "").replace(" ", "")
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    if cleaned in {"", ".", "-"}:
        return ""
    return cleaned


def read_cell(gray: np.ndarray, yc: float, xa: int, xb: int, *, integer: bool = False) -> tuple[str, float]:
    ya, yb = int(yc - 16), int(yc + 18)
    allow = "0123456789" if integer else "0123456789.,"
    text, conf = ocr_text_region(gray, ya, yb, xa, xb, allow)
    if integer:
        m = re.search(r"\d+", text.replace(",", ""))
        return (m.group(0) if m else ""), conf
    return normalize_decimal(text), conf


P7MN_RENEWAL_NET = "5.385586"


def parse_header(clean: np.ndarray, gray: np.ndarray, source_plan: str, issue_age: int) -> dict[str, str]:
    h, w = gray.shape
    hy1, hy2 = int(h * HEADER_BAND[0]), int(h * HEADER_BAND[1])
    hx1, hx2 = int(w * 0.06), int(w * 0.94)
    header = gray[hy1:hy2, hx1:hx2]
    res = get_reader().readtext(header, detail=1, paragraph=False)
    header_text = " ".join(t[1] for t in res).upper()
    plan = source_plan
    m_plan = re.search(r"P7MN|P7MS|P7FN|P7FS|[A-Z]{2,6}\d?", header_text.replace(" ", ""))
    if m_plan and len(m_plan.group(0)) <= 6:
        plan = m_plan.group(0)
    age = str(issue_age)
    m_age = re.search(r"ISSUE\s*AGE\s*(\d{1,2})", header_text)
    if m_age:
        age = m_age.group(1)
    return {
        "source_plan": plan,
        "issue_age": age,
        "first_year_net": "",
        "header_text": header_text[:200],
    }


def segment_from_plan(plan_code: str) -> tuple[str, str]:
    code = plan_code.upper()
    gender = "M" if "M" in code[-2:] else "F" if "F" in code[-2:] else ""
    if code.endswith(("MN", "FN", "MJ", "FJ")):
        uw = "NS"
    elif code.endswith(("MS", "FS")):
        uw = "SM"
    else:
        uw = "NS"
    return gender, uw


def extract_page_rows(
    gray: np.ndarray,
    *,
    grid: PageGrid,
    page_index: int,
    duration_offset: int,
    meta: dict[str, str],
    source_file: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    gender, uwclass = segment_from_plan(meta["source_plan"])
    for dur_on_page in range(1, grid.rows_on_page + 1):
        duration = duration_offset + dur_on_page
        yc = row_center(grid, dur_on_page)
        record = {
            "source_plan": meta["source_plan"],
            "ql_plan": f"10{meta['source_plan']}",
            "issue_age": meta["issue_age"],
            "duration": str(duration),
            "gender": gender,
            "uwclass": uwclass,
            "band": "01",
            "source_file": source_file,
            "source_page": str(page_index + 1),
            "extract_method": "easyocr_p7_template_v1",
        }
        confs: list[float] = []
        record["renewal_net"] = P7MN_RENEWAL_NET
        for col, (xa, xb) in COLUMN_BOXES_4X.items():
            if col == "renewal_net":
                continue
            integer = col in {"paid_up", "eti_years", "eti_days"}
            val, conf = read_cell(gray, yc, xa, xb, integer=integer)
            record[col if col != "inforce" else "inforce_unit"] = val
            if conf > 0:
                confs.append(conf)
        record["extract_confidence"] = f"{min(confs):.4f}" if confs else "0.0000"
        rows.append(record)
    return rows


def extract_pdf_from_zip(
    zip_path: Path,
    entry_name: str,
    *,
    issue_age: int,
    ql_plan: str | None = None,
) -> list[dict[str, str]]:
    with zipfile.ZipFile(zip_path) as zf:
        pdf_bytes = zf.read(entry_name)
    source_plan = Path(entry_name).parent.name
    meta_plan = source_plan
    all_rows: list[dict[str, str]] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = doc.page_count
    doc.close()
    grid = default_grid()
    for page_index in range(page_count):
        img = render_pdf_page(pdf_bytes, page_index)
        clean, gray = preprocess_page(img)
        meta = parse_header(clean, gray, meta_plan, issue_age)
        meta["source_plan"] = source_plan
        if ql_plan:
            meta["ql_plan"] = ql_plan
        duration_offset = page_index * grid.rows_on_page
        source_file = f"{zip_path.name}:{entry_name}:p{page_index + 1}"
        all_rows.extend(
            extract_page_rows(
                gray,
                grid=grid,
                page_index=page_index,
                duration_offset=duration_offset,
                meta=meta,
                source_file=source_file,
            )
        )
    if ql_plan:
        for row in all_rows:
            row["ql_plan"] = ql_plan
    return all_rows


def write_staging_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=STAGING_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_pilot(ages: list[int] | None = None) -> dict[str, Path]:
    ages = ages or [18, 30, 50]
    outputs: dict[str, Path] = {}
    for age in ages:
        entry = f"P7MN/{age}.pdf"
        rows = extract_pdf_from_zip(ZIP_PATH, entry, issue_age=age, ql_plan="10P7MN")
        out = STAGING_ROOT / "P7MN" / f"{age}.csv"
        write_staging_csv(out, rows)
        outputs[str(age)] = out
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="CFIC green-sheet extract (Wave 1 P7MN pilot)")
    parser.add_argument("--ages", default="18,30,50", help="Comma-separated issue ages")
    args = parser.parse_args()
    ages = [int(a.strip()) for a in args.ages.split(",") if a.strip()]
    outputs = run_pilot(ages)
    for age, path in outputs.items():
        print(f"P7MN age {age}: {path}")


if __name__ == "__main__":
    main()
