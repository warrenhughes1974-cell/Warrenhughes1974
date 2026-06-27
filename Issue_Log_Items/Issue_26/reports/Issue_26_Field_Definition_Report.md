# Issue #26 — Field Definition Confirmation Report

**Status:** Field definition **confirmed from QLAdmin Help** — Development may proceed after business sign-off  
**Date:** 2026-06-26  
**Sources:** `docs/claims_conversion_reference/QLAdmin_Help.pdf` (pp. 46, 887–901), `Sync_Rulebook_quikridr.csv`, PPBEN/quikridr trace analysis  
**No code changes in this pass**

---

## 1. Executive Conclusion

QLAdmin Help **definitively defines** the Coverage Master (`QuikRidr`) fields:

| QLAdmin field | Official definition (QLAdmin Help) | Current LifePRO source | Correct? |
|---------------|-----------------------------------|------------------------|----------|
| **MVPU** | **Value per unit** | `VALUE_PER_UNIT` | **Yes — keep** |
| **MPREM** | **Annual premium per unit** | `MODE_PREMIUM` | **No — wrong source** |
| **MUNIT** | Number of units of coverage | `NUMBER_OF_UNITS` | **Yes — keep** |

LifePRO **`ANN_PREM_PER_UNIT`** matches both:

- LifePRO UI label “Premium Per Unit” (Issue #26 trace), and  
- QLAdmin **`MPREM`** field definition (“Annual premium per unit”).

The reported client QLAdmin values (`18.10`, `174.40`, `31.20`) match **`MODE_PREMIUM`** loaded into **`MPREM`**, which QLAdmin defines as **annual premium per unit**, not modal premium total.

**Modal premium** belongs on **`quikmstr.MMODPREM`** (“Modal premium”), which already maps from PPOLC `MODE_PREMIUM` — **keep unchanged**.

---

## 2. Confirmed Source Field

| Attribute | Value |
|-----------|-------|
| **Extract** | `PPBEN_PolicyBenefit_Extract_20260530.csv` |
| **Field** | **`ANN_PREM_PER_UNIT`** |
| **Grain** | One value per benefit row; Issue #26 compares **base coverage** (`BENEFIT_SEQ = 1`) |
| **LifePRO meaning** | Annual premium **rate** per unit of coverage |
| **Trace match** | Exactly matches client LifePRO values for all three policies |

---

## 3. Current Target Fields and Meanings

### quikridr (Coverage Master — `QuikRidr`)

| Field | QLAdmin definition | Current rulebook source | Emitted (trace pol 010310404C ph1) |
|-------|-------------------|-------------------------|-------------------------------------|
| **MUNIT** | Number of units of coverage | `NUMBER_OF_UNITS` | 15.00000 |
| **MVPU** | **Value per unit** (face) | `VALUE_PER_UNIT` | 1000.00 |
| **MPREM** | **Annual premium per unit** | `MODE_PREMIUM` ❌ | 18.10 (modal — wrong semantic) |
| MANNLFEE+ | Annual/semi/qtr/mth policy fees | Partially via engine (21C) | — |
| MSAVEAGE | Original issue age | unmapped | blank |
| MSAVEUNIT | Original number of units | unmapped | blank |
| **MSAVEVPU** | **Original value per unit** | unmapped | blank |
| **MSAVEPREM** | **Original premium per unit** | unmapped | blank |
| MCOMMPREM | Non-commissionable premium amount | unmapped | blank |

**QLAdmin Help citation (QuikRidr table, ~p. 887–901):**

```
MUNIT  … Number of units of coverage
MVPU   … Value per unit
MPREM  … Annual premium per unit
MSAVEVPU … Original value per unit
MSAVEPREM … Original premium per unit
```

**Policy Display — Coverage tab (p. 46):**

```
(26) Prem/Unit … Annual premium per unit for the phase coverage.
(27) Pol Fee   … Modal policy fee for the phase of coverage.
```

### quikmstr (Policy Master)

| Field | QLAdmin definition | Current source | Keep? |
|-------|-------------------|----------------|-------|
| **MMODEPREM** | **Modal premium** (p. 894) | PPOLC `MODE_PREMIUM` | **Yes** |
| **MMODE** | Premium mode | PPOLC `BILLING_MODE` | Yes |

Modal premium at **policy** level is correctly separated from coverage **rate** fields.

---

## 4. Candidate Target Fields — Evidence For / Against

### ✅ **MPREM** — **CONFIRMED TARGET** for `ANN_PREM_PER_UNIT`

| Evidence | Detail |
|----------|--------|
| QLAdmin Help | `MPREM` = “Annual premium per unit” |
| Policy Display UI | “Prem/Unit — Annual premium per unit for the phase coverage” |
| Trace data | LifePRO `ANN_PREM_PER_UNIT` = 13.20 / 10.96 / 9.12 (client expected) |
| Current mis-map | `MODE_PREMIUM` → `MPREM` produces 18.10 / 174.40 / 31.20 (client reported QLAdmin) |

**Recommendation:** Map **`ANN_PREM_PER_UNIT` → `MPREM`** (replace `MODE_PREMIUM` as source for `quikridr.MPREM` only).

---

### ❌ **MVPU** — **REJECT** for `ANN_PREM_PER_UNIT`

| Evidence | Detail |
|----------|--------|
| QLAdmin Help | `MVPU` = “Value per unit” (face amount) |
| Policy Display UI | “Val /U — Value per unit for the coverage” (p. 50) |
| LifePRO | `VALUE_PER_UNIT` = $1,000 face; distinct from premium rate |
| Fleet | 4,954 / 5,083 policies: `MVPU` == `VALUE_PER_UNIT`; **0** match `ANN_PREM_PER_UNIT` |

**Recommendation:** **Do not overwrite MVPU.** Keep `VALUE_PER_UNIT` → `MVPU`.

---

### ❌ **MSAVEVPU** — **REJECT** for `ANN_PREM_PER_UNIT`

| Evidence | Detail |
|----------|--------|
| QLAdmin Help | “**Original** value per unit” — snapshot/historical face, not current premium rate |
| Semantics | “MSAVE*” prefix = saved/original values at issue or prior status |
| Output | Blank fleet-wide (never populated by conversion) |

**Recommendation:** Do **not** map current `ANN_PREM_PER_UNIT` to `MSAVEVPU`.

---

### ❌ **MSAVEPREM** — **REJECT** for current `ANN_PREM_PER_UNIT` (unless business wants *original* rate)

| Evidence | Detail |
|----------|--------|
| QLAdmin Help | “**Original** premium per unit” |
| Use case | Likely for reinstatement / saved-coverage scenarios, not active rate display |
| Output | Blank fleet-wide |

**Recommendation:** Do **not** map unless business confirms a separate requirement for **original** (issue-date) premium per unit on conversions.

---

### ❌ **MCOMMPREM** — **REJECT**

| Evidence | Detail |
|----------|--------|
| QLAdmin Help | “Non-commissionable premium amount” |
| Semantics | Commission treatment, not premium rate |

---

### ❌ **quikmstr.MMODEPREM** — **REJECT** for `ANN_PREM_PER_UNIT`

| Evidence | Detail |
|----------|--------|
| QLAdmin Help | “Modal premium” — **policy-level total**, not per-unit rate |
| Current mapping | PPOLC `MODE_PREMIUM` — **correct for modal premium** |
| Trace | 174.40 on 010331768C is policy modal total (= `ANN_PPU × units + fee`), not per-unit rate |

**Recommendation:** **Keep** `quikmstr.MMODEPREM` ← `MODE_PREMIUM`. Do not conflate with coverage rate.

---

## 5. Where Does LifePRO `MODE_PREMIUM` (PPBEN) Belong?

| LifePRO field | Meaning | Correct QLAdmin home |
|---------------|---------|---------------------|
| PPOLC `MODE_PREMIUM` | Policy modal premium | **quikmstr.MMODPREM** ✅ already mapped |
| PPBEN `MODE_PREMIUM` | Benefit-phase modal premium | **Not `quikridr.MPREM`** per QLAdmin schema |
| PPBEN `ANN_PREM_PER_UNIT` | Annual premium rate / unit | **`quikridr.MPREM`** ✅ confirmed |

QLAdmin likely **derives** modal billing amounts from **`MPREM × MUNIT`**, plan modal factors (`quikplan`), and fee fields — not by storing modal total in `MPREM`.

Loading `MODE_PREMIUM` into `MPREM` **short-circuits** that model and produces the Issue #26 symptom.

---

## 6. Impact Analysis If `ANN_PREM_PER_UNIT` → `MPREM`

| Area | Impact |
|------|--------|
| **QLAdmin Coverage Display** | “Prem/Unit” should match LifePRO Premium Per Unit |
| **Premium calculation** | **High** — QLAdmin uses coverage rate × units for billing/valuation paths; correcting `MPREM` fixes downstream math, not just display |
| **quikmstr modal premium** | **None** if `MMODEPREM` mapping unchanged |
| **MVPU / face amount** | **None** if `VALUE_PER_UNIT` → `MVPU` unchanged |
| **PUA / rider phases** | Phase 2+ rows have own PPBEN records; map per benefit row |
| **Blank ANN_PREM_PER_UNIT** | 2,469 / 5,083 base benefits have blank/zero `ANN_PREM_PER_UNIT` — need fallback rule (see §8) |
| **Policies where ANN_PPU = MODE_PREM** | 630 policies — no numeric change after fix |
| **Fleet affected** | ~4,453 policies where `ANN_PPU ≠ MODE_PREM` (87.6%) |

**Not display-only** — this is a **semantic correction** to a core coverage master field.

---

## 7. ANN_PREM_PER_UNIT Population (Task 9)

| Metric | Count | % |
|--------|-------|---|
| Base benefits (BENEFIT_SEQ = 1) | 5,083 | 100% |
| `ANN_PREM_PER_UNIT` populated (non-zero) | 2,614 | 51.4% |
| Blank / zero | 2,469 | 48.6% |
| `ANN_PPU == MODE_PREMIUM` (exact) | 630 | 12.4% |

Population is **product/status dependent** — not all plan types carry annual premium per unit in LifePRO. Development must define **fallback** for blank `ANN_PREM_PER_UNIT` (e.g., leave `MPREM` blank, derive from `MODE_PREMIUM/units`, or hold for client review).

---

## 8. Trace Policy Validation (Post-Fix Expectation)

| Policy | ANN_PREM_PER_UNIT → MPREM | Current MPREM (wrong) | MVPU (unchanged) | MMODPREM (unchanged) |
|--------|---------------------------|----------------------|------------------|----------------------|
| 010310404C | **13.20** | 18.10 | 1000.00 | 18.10 |
| 010331768C | **10.96** | 174.40 | 1000.00 | 174.40 |
| 010367131C | **9.12** | 31.20 | 1000.00 | 31.20 |

---

## 9. Recommended Development Task (after business sign-off)

**Scope:** Surgical rulebook change only — `Sync_Rulebook_quikridr.csv`

1. Change **`MPREM`** source from `MODE_PREMIUM` to **`ANN_PREM_PER_UNIT`**.
2. **Do not** change `MVPU`, `MUNIT`, or `quikmstr` mappings.
3. **Do not** map `MSAVEVPU` / `MSAVEPREM` without separate business requirement.
4. Define fallback for blank `ANN_PREM_PER_UNIT` (governance decision).
5. Add validation script: phase-1 `quikridr.MPREM` vs PPBEN `ANN_PREM_PER_UNIT`.
6. Version bump + re-test trace policies + 20-policy regression sample.
7. Client UAT: confirm Coverage tab “Prem/Unit” and policy-level “Modal Premium” both correct.

---

## 10. Testing Checklist

- [ ] QLAdmin Coverage tab **Prem/Unit** = PPBEN `ANN_PREM_PER_UNIT` for trace policies
- [ ] QLAdmin Policy Master **Modal Premium** = PPOLC `MODE_PREMIUM` (unchanged)
- [ ] `MVPU` still = `VALUE_PER_UNIT` ($1,000 typical)
- [ ] `MUNIT` unchanged
- [ ] Phase 2 PUA riders: `MPREM` reflects rider row `ANN_PREM_PER_UNIT` (often zero/blank)
- [ ] Policies with blank `ANN_PREM_PER_UNIT`: documented fallback behavior
- [ ] No change to plan codes, crosswalk, units precision, or fee mapping (21C)
- [ ] Fleet validation: 0 rows where populated `ANN_PPU` ≠ emitted `MPREM` (within $0.01)

---

## 11. Client Clarification Needed

| # | Question | Why |
|---|----------|-----|
| 1 | Confirm UAT compares LifePRO **Premium Per Unit** to QLAdmin Coverage **Prem/Unit** (not Modal Premium) | Validates comparison basis |
| 2 | For **2,469 policies** with blank LifePRO `ANN_PREM_PER_UNIT`, what should QLAdmin `MPREM` show? | Fallback rule |
| 3 | Is **original** premium per unit (`MSAVEPREM`) required at conversion, or only current rate? | Avoid unnecessary MSAVE* mapping |
| 4 | After fix, re-test modal premium breakdown (Issue 21J) — modal totals should come from `MMODEPREM` + plan factors | Related regression |

---

## 12. Classification

| Category | Verdict |
|----------|---------|
| **Conversion logic error** | **Yes** — wrong LifePRO field mapped to `quikridr.MPREM` |
| **QLAdmin display behavior** | **No** — QLAdmin displays what we load; definitions are clear |
| **Source-data issue** | **Partial** — 48.6% blank `ANN_PREM_PER_UNIT` needs fallback policy |

---

## Appendix — QLAdmin Help References

| Page | Content |
|------|---------|
| **46** | Policy Display Coverage: **(26) Prem/Unit = Annual premium per unit**; (27) Pol Fee = Modal policy fee |
| **50** | **Val/U = Value per unit**; Units; Modal Premiums on Names tab (policy level) |
| **887–901** | QuikRidr field dictionary: **MVPU**, **MPREM**, **MSAVEVPU**, **MSAVEPREM** |
| **894** | QuikMstr: **MMODEPREM = Modal premium** |

Reproduce trace: `python QLA_Migration/_research_issue26_ppu.py`
