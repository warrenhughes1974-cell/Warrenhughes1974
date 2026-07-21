# Issue A — Risk Review Report

**Issue:** A — QuikPlan / PVO / rate-key structural defects (internal)  
**Framework stage:** Risk Agent  
**Status:** Conditional Go (phased)  
**Fallback simulated:** Description-based single-prem starter list (A1)  
**Generated:** 2026-07-20  
**Agent/script:** Risk Agent + `QLA_Migration/_research_issueA_single_prem.py` + `_risk_review_issueA_fleet.py`

**Status note:** Risk analysis only — no production code changes. Internal track — not client-facing.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Proceed to Development only for **A1 (single-prem modal fix)** using the description-based starter list below; hold A2–A9 pending SME answers or separate Risk scopes. A1 is safe and surgical: existing DG-R-009 path already zeros modals, but **Issue #21J modal overlay runs afterward and restores non-zero S/Q/M**.

| Sub-item | Recommendation | Why |
|----------|----------------|-----|
| **A1** Single prem PAYYRS + S/Q/M=0 | **GO** (starter = DESCR list) | Root cause confirmed; 4 plans; existing function + order bug |
| **A2** Calc Dfcy | **NO-GO** | Awaiting CSO |
| **A3–A6** Default keys / blank Pl* / basis / category | **HOLD** | Needs TESTRD pattern design + high blast (#77 overlap) |
| **A7** VarGP vs rates | **HOLD** | Systemic 141/141 VARGP=4 — separate product decision |
| **A8** Annuity | **HOLD** | 2 plans; Eric int/schg + PAR/VarDB rules |
| **A9** Supp `9*` | **HOLD** | Supp-type field undefined; PAR=1 on 26/56 |

---

## 0. Single-premium starter list (from DESCR)

Scanned `QLA_Migration/Output/quikplan.csv` (141 plans).  
**Rule used:** `DESCR` contains `SINGLE PREM` (case-insensitive).

| PLAN | DESCR | PAYYRS | SEMI | QTRL | MTHD | MTHB | A1 today |
|------|-------|-------:|-----:|-----:|-----:|-----:|----------|
| **1668SP** | SINGLE PREMIUM WHOLE LIFE | 1 | 52.5017 | 27.0007 | 9.1997 | 8.7966 | **FAIL** (modals) |
| **10L171** | SINGLE PREMIUM WHOLE LIFE | 1 | 50.0000 | 25.0035 | 8.3298 | 8.3298 | **FAIL** (modals) |
| **10L172** | SINGLE PREMIUM WHOLE LIFE | 1 | 50.0000 | 25.0035 | 8.3298 | 8.3298 | **FAIL** (modals) |
| **1L17SP** | SINGLE PREMIUM WHOLE LIFE | 1 | 50.0000 | 25.0035 | 8.3298 | 8.3298 | **FAIL** (modals) |

**Starter list for Development (A1):** `1668SP`, `10L171`, `10L172`, `1L17SP`

### Not in DESCR (do not auto-add from description)

| PLAN | Current DESCR | Notes |
|------|---------------|-------|
| **117JPO** | L17 JUVENILE PURCHASE OPTION | In `single_premium_plans.csv` from DG-R-009; **not** “SINGLE PREMIUM” in current DESCR |
| **17MJPO** | L17 MULTI JUVENILE PURCHASE OPTION | Same — config-listed but description is JPO |
| **7647SP** | SPOUSE - FAMILY LIFE DECREASING TERM | Code ends in SP; **not** single premium |

`Configs/single_premium_plans.csv` currently lists 6 plans (includes 117JPO / 17MJPO). Risk recommends Development **align config to the 4 DESCR hits** unless Eric confirms JPO belong on the SP list.

---

## 1. Current vs Proposed Mapping (A1 only)

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `PAYYRS` | Already `1` on 4 DESCR SP plans | Keep `1` | No (already OK in Output) |
| `PAYAGE` | `0` | Keep `0` | No |
| `SEMI` / `QTRL` / `MTHD` / `MTHB` | Non-zero (client modal map / #21J) | **`0`** for SP plans | **Yes** |
| `ANNL` | 100.0000 | Leave (Robert did not require annual=0) | No |

**Root cause:** In `quikplan_converter.py` / `app.py`, `apply_single_premium_payment_settings` runs **before** `apply_modal_factors_to_quikplan` (#21J), which re-applies non-zero SEMI/QTRL/MTHD/MTHB from the modal mapping.

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikmstr.MMODPREM | PPOLC | **No** |
| quikridr.MPREM | #26 | **No** |
| MPOLICY padding | #25 | **No** |
| Non-SP plan modal factors | #21J mapping | **No** (must remain) |
| VARGP / VARDB / PAR / PVO | — | **No** in A1 scope |

**Downstream note:** After SP modals are zeroed on quikplan, Issue #36 copies plan factors to quikmstr — SP policies on those plans will get MSEMI/MQTRL/MMTHD/MMTHB=0. That is intentional for A1; Validation must confirm non-SP plans unchanged.

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/quikplan_converter.py` — `apply_single_premium_payment_settings` / `load_single_premium_plans` | DG-R-009 SP payment settings |
| `QLA_Migration/Configs/single_premium_plans.csv` | Confirmed SP plan list |
| `qla_core/modal_premium_factors.py` — `apply_modal_factors_to_quikplan` | #21J overlay (**overwrites** SP zeros today) |
| `QLA_Migration/app.py` / root `app.py` (~7295 then ~7358) | Call order: SP then modal |
| Go-Live Item 08 / DG-R-009 | Prior SP remediation |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Total quikplan rows | 141 |
| DESCR contains SINGLE PREM | **4** |
| Of those with PAYYRS≠1 | 0 (Output) |
| Of those with S/Q/M ≠ 0 | **4** (all) |
| A1 rows that would change (modals only) | **4** |
| Config SP list size today | 6 |
| VARGP=4 (A7 context) | 141 / 141 |
| Plans with no PlGd/Bd/Uw/St (A3) | 15 (incl. 10L171, 10L172, 117JPO) |
| Annuity-like (A8) | 2 (A60MIR, A96DAR) — both PAR=1 |
| Prefix-9 (A9) | 56; PAR=1 on 26 |

### A1 breakdown

| PLAN | would_change SEMI/QTRL/MTHD/MTHB | PAYYRS change? |
|------|----------------------------------|----------------|
| 1668SP | Yes → 0 | No |
| 10L171 | Yes → 0 | No |
| 10L172 | Yes → 0 | No |
| 1L17SP | Yes → 0 | No |

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| **F1** Re-apply SP zeros **after** #21J modal overlay; config = 4 DESCR plans | 4 | **Recommended** |
| F2 Description auto-detect every run (no CSV) | 4 today | Reject for prod — Robert asked for Eric list; DESCR can drift |
| F3 Keep 6-plan CSV including JPO | 6 | Reject until Eric confirms JPO are truly single-prem |
| F4 Zero ANNL as well | 4 | Reject — not in Robert rule |

**Recommended fallback:** F1 — surgical order/skip fix; starter config = four DESCR plans; Eric can expand later.

---

## 6. Trace Plans (A1)

| Plan | Before S/Q/M/B | Proposed | Pass? |
|------|----------------|----------|-------|
| 10L171 | 50 / 25.0035 / 8.3298 / 8.3298 | 0 / 0 / 0 / 0 | Target |
| 10L172 | 50 / 25.0035 / 8.3298 / 8.3298 | 0 / 0 / 0 / 0 | Target |
| 1668SP | 52.5017 / 27.0007 / 9.1997 / 8.7966 | 0 / 0 / 0 / 0 | Target |
| 1L17SP | 50 / 25.0035 / 8.3298 / 8.3298 | 0 / 0 / 0 / 0 | Target |
| 117JPO (control) | non-zero | **unchanged** if removed from CSV | Control |
| Non-SP e.g. 130JEB | existing #21J factors | **unchanged** | Control |

---

## 7. Top Changes

| Plan | Field | Before | After |
|------|-------|-------:|------:|
| 1668SP | SEMI | 52.5017 | 0 |
| 1668SP | QTRL | 27.0007 | 0 |
| 10L171 | SEMI | 50.0000 | 0 |
| 10L171 | QTRL | 25.0035 | 0 |
| (same pattern) | MTHD/MTHB | 8.3298… | 0 |

---

## 8. Material Calculation Impact

- **Intentional:** Single-prem plans cannot have modal (S/Q/M) factors; QLAdmin should show 0.00.
- **Side effect:** quikmstr Names-tab modal factors for policies on these 4 plans will also become 0 after #36 copy — correct for SP.
- **Not in scope:** Premium amounts, MPREM, policy fees.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | Preserved — A1 does not touch policy keys |
| Issue #26 MPREM / MMODPREM | Preserved |
| Issue #21J modal factors | Preserved for **non-SP** plans; SP plans must be excluded or re-zeroed after overlay |
| DG-R-009 | Reinforced — make its zeros stick |

---

## 10. Regression Testing Checklist (Validation Agent)

- [ ] Plans `10L171`, `10L172`, `1668SP`, `1L17SP`: PAYYRS=1; SEMI=QTRL=MTHD=MTHB=0
- [ ] `117JPO` / `17MJPO`: unchanged unless Eric adds them to SP list
- [ ] Spot-check ≥3 non-SP plans: SEMI/QTRL/MTHD/MTHB match pre-fix #21J values
- [ ] quikmstr modal copy for SP vs non-SP sample policies
- [ ] Row counts: quikplan still 141; no schema drift
- [ ] Run `Issue_A_Conversion_Checklist.md` A1 → PASS; other IDs still OPEN/BLOCKED as appropriate

---

## 11. Recommended Development Agent Task (A1 only)

**Model:** Composer 2.5 (locked) — requires user **Approved for Development**.

1. Trim `QLA_Migration/Configs/single_premium_plans.csv` to the **4 DESCR plans** (optionally comment that JPO await Eric).
2. Ensure SP modal zeros **win after** `apply_modal_factors_to_quikplan` — either:
   - call `apply_single_premium_payment_settings` again after #21J in both converter and `app.py`, **or**
   - skip #21J overlay when PLAN ∈ SP set.
3. Do **NOT** change: non-SP modals, VARGP/VARDB, PVO keys, PAR, policy tables, #25/#26.
4. Bump `APP_VERSION` in root `app.py` **and** `QLA_Migration/app.py`.
5. Add/extend a small unit or batch assertion that SP plans keep S/Q/M=0 after full quikplan post-process.
6. Out of scope this pass: A2–A9.

---

## Appendix

- Research: `QLA_Migration/_research_issueA_single_prem.py`
- Fleet risk: `QLA_Migration/_risk_review_issueA_fleet.py`
- Checklist: `Issue_A_Conversion_Checklist.md`
- Dependency Gate remains FAIL for full A package; **A1 Conditional Go** is an explicit scope carve-out
