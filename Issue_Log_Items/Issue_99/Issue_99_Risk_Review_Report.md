# Issue #99 — Risk Review Report

**Issue:** #99 — ISWL QuikPlan MKTG / PRODUCT / HLOB = ISWLFE  
**Framework stage:** Risk Agent (G3)  
**Status:** **GO** — awaiting Development approval  
**Generated:** 2026-07-23  
**Agent:** Risk Agent (Cursor Grok 4.5, read-only)

**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**GO** — Client-confirmed plan-setup gap; scope is 8 ISWL plans × 3 fields; blast radius is small and well-bounded by the existing ISWL allowlist. Safe for surgical Development after approval.

---

## 1. Is this actually an issue?

**Yes.** Current Output has no `ISWLFE` on any ISWL plan. Sujitha states QL needs that tag to recognize ISWL. Warren directed MKTG + PRODUCT + HLOB all become `ISWLFE`.

---

## 2. Current vs proposed mapping

| Field | Current (ISWL) | Proposed | Non-ISWL |
|-------|----------------|----------|----------|
| MKTG | blank | `ISWLFE` | unchanged |
| PRODUCT | `05`/`06`/`16` (PRODUCT_TYPE) | `ISWLFE` | unchanged |
| HLOB | blank | `ISWLFE` | unchanged |

---

## 3. Blast radius

| Item | Assessment |
|------|------------|
| Tables | `quikplan` only |
| Rows | 8 of 141 |
| Columns | MKTG, PRODUCT, HLOB only |
| Policy tables | None |
| Rates | None |
| #25 / #26 | Unaffected |

---

## 4. Regression risks

| Risk | Level | Mitigation |
|------|-------|------------|
| Accidental fleet PRODUCT wipe | Medium if coded wrong | Strict `is_iswl_mplan()` gate; validator asserts 133 non-ISWL PRODUCT unchanged |
| Product-setup isolated emit skips override | Medium | Wire enrichment on every path that writes quikplan |
| QLAdmin rejects `ISWLFE` | Low | PFSA already used it; UAT reload |
| Downstream reports expecting PRODUCT_TYPE | Low | Document override; client requested PRODUCT=`ISWLFE` |

---

## 5. Validation plan (for post-Dev)

1. All 8 ISWL plans: MKTG=PRODUCT=HLOB=`ISWLFE`
2. Non-ISWL: zero unintended deltas on those three fields
3. Schema / field order unchanged
4. Publish `Output/Test_Validation/quikplan.csv` on PASS
5. Accountability IN_DATA before Closure (G7)

---

## 6. Development constraints

- Surgical only; bump `APP_VERSION` in root + `QLA_Migration/app.py` if `app.py` changes
- Prefer shared helper using existing ISWL allowlist
- No architecture redesign
- Do not start until: **“Approved for Development”**

---

## Gate G3

**GO** — Ask for Development approval.
