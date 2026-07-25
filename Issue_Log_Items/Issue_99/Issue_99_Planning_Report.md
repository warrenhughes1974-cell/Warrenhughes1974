# Issue #99 — Planning Report

**Issue:** #99 — ISWL QuikPlan MKTG / PRODUCT / HLOB = ISWLFE  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning Complete → Dependency Gate  
**Generated:** 2026-07-23  
**Model:** Cursor Grok 4.5  
**Depends on:** `Issue_99_Intake_Summary.md`

---

## 1. Executive finding

ISWL plans are missing the QLAdmin product tag `ISWLFE`. Sujitha confirmed QL needs this so plans are picked up as ISWL. Warren directed that **MKTG, PRODUCT, and HLOB** all become `ISWLFE` for the 8 ISWL MPLANs.

This is a surgical `quikplan` tagging fix — not a rates or policy-data change.

---

## 2. Confirmed LifePRO sources

| Source | Field | Role for #99 |
|--------|-------|--------------|
| PCOVR / plan emit | `COVERAGE_ID` → PLAN via crosswalk | Identifies ISWL plans |
| PCOVR | `PRODUCT_TYPE` | Today maps to `PRODUCT` (`05`/`06`/`16`) — **will be overridden** for ISWL only |
| — | (none) | MKTG / HLOB have no LifePRO source today |

ISWL membership: reuse `ISWL_MPLAN_ALLOWLIST` in `qla_core/cso_mortality_crosswalk.py` (not invent a second list).

---

## 3. Confirmed QLAdmin targets

| UI (Sujitha) | QuikPlan field | Target value |
|--------------|----------------|--------------|
| Plan Information → MKTG | `MKTG` | `ISWLFE` |
| QUIKPLAN:PRODUCT | `PRODUCT` | `ISWLFE` |
| LOB | `HLOB` | `ISWLFE` |

Schema: `qla_core/schema_constants.py` QUIKPLAN_SCHEMA includes `MKTG`, `PRODUCT`, `HLOB`.

---

## 4. Proposed mapping / implementation approach

**Preferred (surgical, durable):**

After normal quikplan row build (rulebook + enrichments), for each plan where `is_iswl_mplan(PLAN)`:

```text
MKTG    = ISWLFE
PRODUCT = ISWLFE
HLOB    = ISWLFE
```

Reuse `is_iswl_mplan()` / `ISWL_MPLAN_ALLOWLIST` — do not hardcode a parallel list in app.py.

**Avoid:**

- Changing LifePRO source extracts
- Blanking or changing PRODUCT for non-ISWL plans
- Broad rulebook rewrite of PRODUCT_TYPE mapping for all plans

**Rulebook note:** Optional later cleanup to document ISWL override in `Sync_Rulebook_quikplan.csv` Transformation_Note; primary fix should be code enrichment so emit is authoritative.

---

## 5. Open client questions

1. Confirm UI “LOB” is QuikPlan `HLOB` (assumed Yes).
2. Confirm `ISWLFE` remains a valid QuikList / plan-setup code in their QLAdmin (PFSA precedent suggests Yes).
3. Any plans beyond the 8-code allowlist that should also get `ISWLFE`? (Default: no.)

None of these block Development given Warren’s “change everything” direction and PFSA precedent.

---

## 6. Formatting / fallback rules

- Value exactly `ISWLFE` (case as client wrote).
- Apply only when PLAN ∈ ISWL allowlist.
- Preserve all other quikplan columns for ISWL and non-ISWL.
- Preserve #25 MPOLICY padding and #26 MPREM (unaffected tables).

---

## 7. Policy key handling

N/A — plan-level only. No MPOLICY / crosswalk policy keys.

---

## 8. Estimated record counts

| Population | Count |
|------------|------:|
| quikplan rows total | 141 |
| ISWL rows to change | **8** |
| Non-ISWL rows (must be unchanged) | 133 |
| Fields changed per ISWL row | 3 (`MKTG`, `PRODUCT`, `HLOB`) |

---

## 9. Sample before-state (current Output)

| PLAN | MKTG | PRODUCT | HLOB |
|------|------|---------|------|
| 1658CS | | 06 | |
| 1659C2 | | 05 | |
| 1659SR | | 16 | |
| 1679CS | | 06 | |

After: all three = `ISWLFE`.

---

## 10. Risks and unknowns

| Risk | Mitigation |
|------|------------|
| Overwriting PRODUCT loses PRODUCT_TYPE codes | Document intentional override; only ISWL |
| `ISWLFE` rejected on load | Client already used on PFSA; UAT reload quikplan |
| Allowlist drift vs future ISWL plans | Single allowlist module; Issue A checklist optional |
| Product-setup isolated path skips enrichment | Ensure enrichment runs on both batch and product-setup emit paths that write `quikplan.csv` |

---

## 11. Recommended Risk Agent focus

- Confirm blast radius = 8 plans × 3 fields
- Confirm no dependency on #23/#43 expense work
- Go/No-Go for Development

---

## Gate G1

- [x] Sources / targets confirmed
- [x] Proposed mapping documented
- [x] Counts and sample before-state
- [x] No code or rulebook changes in Planning
