# Issue #98 — Planning Report

**Issue:** #98 — CV Endpoint Off By One (`17085M` / `010398471C`)  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete — proceed to Dependency Gate  
**Generated:** 2026-07-22  
**Agent:** Planning Agent (Cursor Grok 4.5, read-only)

---

## 1. Executive finding

Issue #41 correctly fixed the **age-100 inclusive endpoint convention** for the `1960PO` proof family, but the **Issue #37 `cv_lifepro_first_duration` heuristic** (hardcoded from the 960 PO matrix) still over-shifts many issue ages on other products — including Eric’s `17085M` M/14 example.

For that slice, current Output places `.06` at year 4 and truncates terminal `1000`, leaving `975.61` as the last factor at year 86. Eric’s LifePRO convention for this case is: `.06` at year 3, `975.61` at year 85, `1000` at year 86.

**Recommended direction:** Surgical remap correction so LifePRO terminal `1000` lands at QL duration `100 - issue_age`, with first nonzero (`.06`) landing at Eric’s year 3 for this proof — then re-validate #37/#41 anchors before fleet re-emit of `QuikCvs`.

---

## 2. Confirmed LifePRO source

| Source | File | Notes |
|--------|------|-------|
| Rate table CV rows | `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` | `COVERAGE_ID=670 GL85-8`, `TYPE_CODE=CV` |
| Rate owner for `17085M` | `670 GL85-8` | Issue #40 inheritance (actuarial-approved) |
| Issuing plan | `17085M` | Policy base coverage `670 GL85-M` |

### Source slice — `670 GL85-8` / CV / M / 14 / band 1 / UW 0

| Source duration | Value | Role |
|----------------:|------:|------|
| 1 | 0.00 | leading zero |
| 2 | **0.06** | first nonzero |
| 53 | **674.69** | Eric neighbor low |
| 54 | **688.11** | Eric neighbor high |
| 84 | **975.61** | Eric year-85 value |
| 85 | **1000.00** | Eric year-86 terminal |

`684.76` is not a source cell; it sits between 674.69 and 688.11 (Eric’s stated band).

---

## 3. Confirmed QLAdmin target

| Table | Fields | Path |
|-------|--------|------|
| `QuikCvs` | `PLAN`, `AGE`, `CNTL`, `CV0`–`CV9`, `GENDER`, `UWCLASS`, `BAND`, … | `QLA_Migration/Output/rates/QuikCvs.csv` |
| `QuikPlCv` | plan CV keys (already present for `17085M`) | unchanged for this issue |

Duration index = `CNTL * 10 + column` (Issue #41 convention).

---

## 4. Current mapping (code)

| Step | Rule (today) |
|------|----------------|
| FNZ pre-scan | First nonzero source duration per `(COVERAGE_ID, SEX, AGE)` |
| LifePRO first column | `cv_lifepro_first_duration(sex, age)` — **960 PO matrix** |
| Remap | `lp_d = source_d + first - fnz` |
| Truncate | drop if `lp_d > 100 - age` or `lp_d < 1` |
| Emit | Issue #41: return `lp_d` as QL duration (not `lp_d - 1`) |

For M/14: `first=4`, `fnz=2` → **offset +2** → terminal 1000 maps to 87 → **truncated**.

Eric-aligned offset for this slice: **+1** (`first=3` with same `fnz=2`).

---

## 5. Proposed fix options (Development chooses after Risk)

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A — Adjust first-duration matrix** | Change `cv_lifepro_first_duration` for ages that currently over-shift (e.g. M 1–17 / parallel F) so first nonzero lands at LifePRO display year | Small code surface | Matrix still product-family heuristic; need fleet proof |
| **B — Endpoint-anchored offset** | Per slice: choose offset so max kept source duration with terminal/end value maps to `100 - age` | Directly enforces Eric/#41 endpoint | Must prove #37 leading placement still holds on 960 PO |
| **C — Product-specific override** | Special-case GL85 / `17085M` only | Minimal blast radius | Leaves same defect on other ages/products (research saw many truncated-1000 slices) |

**Planning preference:** Prefer **B** (or A proven equivalent to B on proof set) over C — Eric’s symptom is the general off-by-one class, not GL85-only.

---

## 6. Open questions

1. Should LifePRO screenshots be filed under `Issue_98/evidence/` before Development, or are Eric’s numeric anchors sufficient?  
2. For slices whose source terminal is **not** 1000 (e.g. some age-0 GL85 rows end at 975.61), confirm endpoint = last source value at `100 - age` (already #40/#41 behavior) vs forcing 1000.  
3. After remap fix, is a full guarded rate emit required, or QuikCvs-only re-emit (as #41 did)?

---

## 7. Must not change

- Non-CV families (`QuikNps`, `QuikGps`, `QuikDbs`, `QuikDvs`, `QuikTvs`, …)  
- Issue #40 inheritance owner selection (`670 GL85-8` → `17085M`)  
- Issue #25 MPOLICY padding / #26 MPREM  
- Policy conversion tables (`quikmstr`, `quikridr`, fees — #97)

---

## 8. Validation plan (for later G5)

| ID | Check |
|----|-------|
| V98-01 | `17085M` M/14: `.06` at duration 3 |
| V98-02 | `17085M` M/14: `975.61` at 85; `1000` at 86 |
| V98-03 | Neighbors 674.69 / 688.11 at 54 / 55 |
| V98-04 | Issue #41 endpoint examples still PASS (`_validate_issue41_quikcvs_endpoint.py`) |
| V98-05 | Issue #37 placement / G5 matrix still PASS |
| V98-06 | `17085M` vs `170858` value parity at same QL index (#40) |
| V98-07 | Fleet count of slices truncating source `1000` → 0 (or documented waiver) |

Evidence seed: `evidence/issue98_010398471C_cv_trace.csv` (current 5/5 FAIL).

---

## G1 gate

- [x] Source/target mapping documented  
- [x] Fix options listed  
- [x] Open questions listed  
- [x] Regression boundaries stated  

**Next:** Dependency Gate.
