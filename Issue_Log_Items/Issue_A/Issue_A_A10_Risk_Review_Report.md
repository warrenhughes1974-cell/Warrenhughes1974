# Issue A / A10 — Risk Review Report

**Issue:** A10 — QuikUwpo missing underwriting class codes  
**Framework stage:** Risk Agent  
**Status:** **GO**  
**Generated:** 2026-07-20  
**Track:** Internal — not client-facing  
**Status note:** Risk analysis only — no production code changes in this stage.

---

## Go / No-Go Recommendation

**GO** — Safe to proceed to Development for A10 only.

| Factor | Assessment |
|--------|------------|
| Business rule | Locked by Robert — clear |
| Schema | Confirmed Help §7.230 + live DBF |
| Blast radius | **Low** — new emit table only; no QuikPlan / policy / QuikPlUw membership changes |
| SME dependency | None for implement |
| Rollback | Delete/omit `QuikUwpo.csv` / DBF; leave prior region default row |

---

## 1. Current vs Proposed

| Item | Current | Proposed |
|------|---------|----------|
| `QuikUwpo` emit | **None** (conversion never writes it) | Emit with rate package |
| CSO region table | 1 row: `00` / NOT APPLICABLE | 5 rows from fleet codes |
| Key | UWCODE | Same — enforce unique |
| Descriptions | N/A | From `UWCLASS_LABEL` |

### Expected rows (current QuikPlUw fleet)

| UWCODE | UWDESCR |
|--------|---------|
| 00 | NOT APPLICABLE |
| NS | NON-SMOKER |
| PR | PREFERRED |
| SM | SMOKER |
| ST | STANDARD |

---

## 2. Fields / tables untouched

| Target | Touched? |
|--------|----------|
| quikplan / policy tables | **No** |
| QuikPlUw plan membership rows | **No** (read only as source of codes) |
| QuikUwcd / QuikUwmm | **No** |
| Factor / key rate tables | **No** |
| #25 / #26 | **No** |

---

## 3. Population / impact

| Metric | Value |
|--------|------:|
| Distinct UWCODE on QuikPlUw | 5 |
| In CSO QuikUwpo today | 1 (`00`) |
| Missing codes | 4 (NS, PR, SM, ST) |
| Plans using NS | 16 |
| Plans using PR | 37 |
| Plans using SM | 63 |
| Plans using ST | 12 |

Inventory: `Issue_Log_Items/Issue_A/Reports/A10_quikuwpo_inventory.csv`

---

## 4. Risk register

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| R1 | Emit invents unused UW codes | Low | Derive only from QuikPlUw (+ always `00`) |
| R2 | Duplicate UWCODE (WPA sample has dupes) | Medium | Dedupe by UWCODE before write |
| R3 | PR vs WPA PF preferred code | Low | Match our fleet (`PR`); do not emit PF unless plans use it |
| R4 | Unknown UWCODE with no label | Low | Fallback UWDESCR = code itself |
| R5 | Rate emit skipped → QuikUwpo stale | Low | Document: regenerate with Rate Tables; checklist A10 on rate runs |
| R6 | Wrong output folder | Low | Emit under `Output/rates/` with other setup CSVs |

---

## 5. Development constraints (surgical)

1. Add schema + writer for QuikUwpo only.  
2. Hook emit in `rate_emit` after member tables are available.  
3. Bump `APP_VERSION` in **both** `app.py` files if any GUI path logs the emit. Prefer pure `qla_core` if no app.py touch needed — still bump if rate loader UI path changes behavior users see.  
4. Add A10 verifier / checklist run-log support.  
5. No changes to QuikPlUw content or QuikPlan.

---

## 6. Validation / regression (post-Dev)

| Check | Pass criteria |
|-------|---------------|
| A10 unique | No duplicate UWCODE in QuikUwpo |
| A10 coverage | Every QuikPlUw.UWCODE ∈ QuikUwpo |
| A10 default | `00` present |
| Regression | QuikPlUw / key / factor row counts unchanged vs pre-fix baseline |

Publish `QuikUwpo.csv` to `Output/Test_Validation/rates/` (or rates folder under Test_Validation) on PASS.

---

## Recommendation

**GO for Development (A10 only).**  

Next user prompt required: **Approved for Development (A10)** — assigned model **Composer 2.5** (or confirm one-time override in this session).
