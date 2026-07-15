# Issue #76 — Planning Report

**Issue:** #76 — ETI/RPU phase-1 pay-up + duration for CV anniversary dates  
**Framework stage:** Planning Agent  
**Status:** Ready for Dependency Gate  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Scope decisions:** `Issue_76_Scope_Decisions.md`  
**Intake:** `Issue_76_Intake_Summary.md`

---

## 1. Executive Finding

Policy Display cash values on exercised ETI/RPU policies date far into the future because phase-1 **`MPAYUP`** remains the contractual LifePRO pay-up age (e.g. **20270201**) while **`MLASTANN`** is computed from **issue** year (`_compute_quikridr_mlastann` → e.g. **53**). QLAdmin then effectively dates CV lines from pay-up + duration (**2027+53=2080**).

**UAT proof on `010407670C`:** setting pay-up to **paid-to `20121001`** and duration to **14** (2026−2012) moved CV dates to **10/01/2026–2027**.

**Direction:** After final master status is known, for **MPHASE=1** when `MSTATUS` ∈ {44,45}: force `MPAYUP=MPAIDTO` and recompute `MLASTANN` = system year − pay-up year. Preserve #60 PUA rules and #72 NFO.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File | Role |
|--------------|------|------|
| PPBEN | `PPBEN_PolicyBenefit_Extract_*.csv` | `PAY_UP_DATE` → today’s phase-1 `MPAYUP` (e.g. 20270201) |
| PPOLC | `PPOLC_PolicyMaster_Extract_*.csv` | `PAID_TO_DATE` → `quikmstr.MPAIDTO` |
| — | Converted `quikmstr` | Authoritative paid-to for SD-76-1 |

Sample `9010407670` / `010407670C`: PPBEN seq1 `PAY_UP_DATE=20270201`; PPOLC `PAID_TO_DATE=20121001`.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Help / type | Role |
|-------|-------|-------------|------|
| quikridr | MPAYUP | DATE 8.0 §7.203 | Pay-up date (Coverage “Payup”) |
| quikridr | MLASTANN | NUMERIC 3.0 §7.203 | “Last anniversary processed (t)” |
| quikridr | MCV0/1/2 | NUMERIC | CV years around t — rebuilt in QLAdmin |
| quikmstr | MPAIDTO | DATE | Paid-to — source for new MPAYUP |
| quikmstr | MSTATUS | | Gate: 44/45 only |

**Repo references:**

| Location | Role |
|----------|------|
| `Sync_Rulebook_quikridr.csv` | `PAY_UP_DATE→MPAYUP` |
| `app.py` `_compute_quikridr_mlastann` / `_apply_quikridr_mlastann` | Today: duration from **MEFFDATE** |
| `app.py` `_apply_pua_rider_inheritance` | #60: PUA `MPAYUP=MEFFDATE` — do not break |
| Post-row quikridr emit | Hook site after mlastann apply + after quikmstr available for join |

---

## 4. Required Source-to-Target Field Mapping

| Driver | Condition | Target | Transformation | Change? |
|--------|-----------|--------|----------------|---------|
| `quikmstr.MPAIDTO` | Master status 44/45; ridr phase 1 | `MPAYUP` | Copy paid-to YYYYMMDD | **Yes** |
| New `MPAYUP` + system year | Same rows | `MLASTANN` | `str(sys_year - int(MPAYUP[:4]))` | **Yes** |
| PPBEN PAY_UP_DATE | Status ∉ {44,45} or phase ≠ 1 | `MPAYUP` | Unchanged rulebook path | **No** |
| MEFFDATE | Non-candidate rows | `MLASTANN` | Existing `_apply_quikridr_mlastann` | **No** |
| #60 PUA | `*PA` / PUA product | `MPAYUP` / `MLASTANN` | Existing inheritance | **No** |

### Fields that must remain unchanged

| Target | Touch? |
|--------|--------|
| MPOLICY (#25) | **No** |
| MPREM (#26) | **No** |
| MEFFDATE / MAGE / MEXPRY / MUNIT | **No** |
| MNFOPT (#72) | **No** |
| PUA phase fields (#60) | **No** |
| Rates / BAND / NFOINT | **No** |

---

## 5. Open Client Questions

1. **OBQ-76-1:** For YE batch with `QLA_VALUATION_DATE=20251231`, should duration use **2025** (→ 13 for sample) or **run-date year** (→ 14, matches screenshot)?  
   - **Planning default (SD-76-8):** run-date year unless Risk/UAT requires valuation-year freeze.

2. **OBQ-76-2:** If `MPAIDTO` blank/invalid on a 44/45 policy, fallback?  
   - **Assumption:** leave LifePRO `PAY_UP_DATE` and issue-based `MLASTANN`; log count.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| MPAYUP | 8-digit YYYYMMDD from `MPAIDTO` |
| MLASTANN | Non-negative integer string; blank if pay-up year unparsable |
| Timing | After quikmstr row exists for policy; after phase-1 mlastann first pass — **override** for 44/45 phase 1 |
| Logging | “Issue #76: adjusted phase-1 MPAYUP/MLASTANN on N ETI/RPU polic(ies)” |

---

## 7. Policy Key Handling

- Join: normalized `MPOLICY` between emitted/pending quikridr and `quikmstr` (or in-batch paid-to cache from PPOLC/`quikmstr` emit order).  
- Prefer cache `pol → MPAIDTO` + `pol → MSTATUS` when processing quikridr (quikmstr may emit before or after — Dev must use PPOLC/`_qm_status_cache` / paid-to map already built in batch).

---

## 8. Estimated Record Counts (current Output)

| Population | Count | Action |
|------------|------:|--------|
| Phase-1 on status 44/45 | 400 | Candidates |
| MPAYUP ← MPAIDTO (≠ today) | **223** | Change pay-up |
| MLASTANN recompute | **400** | Change duration |
| Non-44/45 / later phases | — | **0** from #76 |
| PUA rows (#60) | 494 | Untouched by #76 |

---

## 9. Sample Trace

| Policy | Status | MPAIDTO | MPAYUP before | After | MLASTANN before | After (sys 2026) |
|--------|--------|---------|---------------|-------|-----------------|------------------|
| **010407670C** | 45 | 20121001 | 20270201 | **20121001** | 53 | **14** |
| 010374099C | 44 | 20090921 | 20730921 | **20090921** | 55 | **17** |
| 010149295C | 44 | 19921201 | 19921201 | 19921201 | 64 | **34** |
| Active control (e.g. 010367131C) | 22 | — | unchanged | unchanged | issue-based | unchanged |

---

## 10. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Overwriting #60 PUA MPAYUP | High | Gate: phase=1 only; exclude PUA product / phase>1 |
| YE duration 13 vs UAT 14 | Med | SD-76-8 + OBQ-76-1 |
| Quikmstr not yet written when ridr emits | Med | Use PPOLC paid-to + status cache (same batch sources) |
| Blank MPAIDTO | Low | Fallback leave source; count |
| CV $ still need rebuild | Info | UAT checklist |

---

## 11. Recommended Risk Agent Prompt

```
Risk Agent — Issue #76 ETI/RPU phase-1 MPAYUP + MLASTANN

Read Issue_76_Intake_Summary.md, Issue_76_Planning_Report.md, Issue_76_Scope_Decisions.md.
Simulate before/after for status 44/45 phase-1; prove non-candidates and #60 PUA unchanged.
Go / Conditional Go / No-Go. No code.
```

---

## 12. Recommended Development Task (do not implement)

1. In `app.py` + `QLA_Migration/app.py`: after phase-1 `MPAYUP`/`MLASTANN` are set (and after status known from PPOLC/`PUT_`/`ST_`/`#49` path via cache), if master status ∈ {44,45} and `MPHASE==1`:  
   - `MPAYUP = MPAIDTO` (normalized YYYYMMDD)  
   - `MLASTANN = str(run_date.year - int(MPAYUP[:4]))`  
2. Do **not** apply to PUA later phases (#60).  
3. Bump `APP_VERSION` both copies.  
4. Rebatch `quikridr`; publish `Test_Validation/quikridr.csv`.  
5. Validator: `010407670C` phase1 MPAYUP=20121001, MLASTANN=14 (or valuation-year variant if locked); all 44/45 phase1 MLASTANN matches formula; #60 PUA controls unchanged; #25/#26 smoke.  

**Model for Development:** Composer 2.5 (locked).

---

## Gate Criteria (G1 — Planning Complete)

- [x] Planning report published  
- [x] Source and target documented  
- [x] Trace table included  
- [x] Open questions enumerated  
- [x] Development task outlined but **not** executed  
- [x] No code, rulebook, or output changes  
