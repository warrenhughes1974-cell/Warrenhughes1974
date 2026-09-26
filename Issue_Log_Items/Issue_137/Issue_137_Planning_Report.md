# Issue #137 — Planning Report

**Issue:** #137 — Names-tab Modalized Annual Premium  
**Framework stage:** Planning Agent  
**Status:** Planning Complete  
**Generated:** 2026-08-05  
**Agent/script:** Cursor Grok 4.5 (read-only research)

---

## 1. Executive Finding

Names-tab Annl is wrong because blank-ANN `quikridr.MPREM` uses Issue #88 **calendar** annualization (`MODE × 12/4/2 ÷ units`). LifePRO modalized annual is `MODE_PREMIUM ÷ (mode_factor/100)`. Gold `9010722550C`: current MPREM 9.6264 → base 481.32 (+25 fee = 506.32); proposed MPREM ≈ 8.7197 → base ≈ **436** (+25 fee ≈ **461** on Names if UI adds fee).

**Recommended direction:** Surgical change only inside the #88 blank-ANN interceptor — replace `ann_factor` payments-per-year with modal-factor reverse-engineer. Do **not** touch populated ANN (#26) or `MMODEPREM`.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Notes |
|--------------|--------------|---------------------|-------|
| PPBEN | `PPBEN_PolicyBenefit_Extract_20260731.csv` | Yes | `ANN_PREM_PER_UNIT`, `MODE_PREMIUM`, `NUMBER_OF_UNITS` |
| PPOLC | `PPOLC_PolicyMaster_Extract_20260731.csv` | Yes | `BILLING_MODE`, `BILLING_FORM`, `MODE_PREMIUM` |
| Modal factors | `Mapping/Modal_Premium_Factors_By_Plan.csv` | Yes | SEMI/QTRL/MTHD/MTHB % |

### Available source fields

| Field | Source | Notes |
|-------|--------|-------|
| Mode premium | PPBEN/PPOLC `MODE_PREMIUM` | Already → `MMODEPREM` |
| Annual PPU | PPBEN `ANN_PREM_PER_UNIT` | Blank → #88 path (this issue) |
| Units | `NUMBER_OF_UNITS` | Divisor |
| Billing mode | PPOLC `BILLING_MODE` | 1/3/6/12 (already cached for #88) |
| Bill form | PPOLC `BILLING_FORM` / `MBILLFRM` | DIR vs PAC → MTHD vs MTHB |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Role |
|-------|-------|------|
| `quikridr` | `MPREM` | Annual premium **per unit** (Coverage Prem/Unit); Names Annl base = MPREM×MUNIT |
| `quikmstr` | `MMODEPREM` | Billed mode premium — **unchanged** |
| `quikmstr` | MSEMI/MQTRL/MMTHD/MMTHB | Factors for UI + divisor source |
| `quikridr` | MANNLFEE / M*FEE | Fee — **unchanged** |

**UI:** Policy Display → Names → Modal Premiums  
**Formula (#58):** `(MPREM × MUNIT × factor/100) + modal_fee`

**Repo references:**

| Location | Role |
|----------|------|
| `app.py` / `QLA_Migration/app.py` ~8815–8844 | #26/#88 MPREM interceptor (`ann_factor` dict) |
| `qla_core/modal_premium_factors.py` | Factor load / #36 copy |
| `Sync_Rulebook_quikridr.csv` | ANN→MPREM |

---

## 4. Required Source-to-Target Field Mapping

| Condition | Current | Proposed | Change? |
|-----------|---------|----------|---------|
| ANN_PREM_PER_UNIT > 0 | ANN → MPREM (#26) | unchanged | **No** |
| ANN blank/zero, units > 0 | `(MODE × {12,4,2,1}) / units` | `(MODE ÷ (factor%/100)) / units` | **Yes** |
| units ≤ 0 | blank/skip | unchanged | **No** |
| MMODEPREM | MODE_PREMIUM | unchanged | **No** |

### Mode → factor (this book)

| BILLING_MODE / MMODE | Meaning | Factor field |
|---------------------:|---------|--------------|
| 12 | Annual | 100% (no divide) |
| 6 | Semiannual | SEMI / MSEMI |
| 3 | Quarterly | QTRL / MQTRL |
| 1 | Monthly Direct (BF≠PAC) | MTHD / MMTHD |
| 1 | Monthly PAC (BF=PAC/2) | MTHB / MMTHB |

Factor lookup at emit: plan modal mapping (same CSV as #21J) by phase-1 plan code; PAC GL85 overrides only affect quikmstr post-emit — for MPREM emit use mapping + bill form (document if PAC GL85 blank-ANN policies need override parity).

### Fields that must remain unchanged

| Target | Touch? |
|--------|--------|
| `quikmstr.MMODEPREM` | **No** |
| Populated ANN→MPREM (#26) | **No** |
| MSEMI/MQTRL/MMTHD/MMTHB population (#36) | **No** (read only) |
| M*FEE (#58) | **No** |
| MPOLICY (#2/#25) | **No** |

---

## 5. Open Client Questions

| ID | Question | Planning default |
|----|----------|------------------|
| OQ-1 | Names Annl shows 436 or 436+25 fee? | Accept Names ≈ **461** if UI adds MANNLFEE; premium base must be **436** |
| OQ-2 | Scope blank-ANN only vs all MPREM? | **Blank-ANN only** (preserve #26) |
| OQ-3 | QuikVal Prem/Unit moves with MPREM — OK? | **Yes with UAT**; modalized truth preferred over calendar ×12 |

---

## 6. Formatting / Fallback Rules

- Round MPREM like current #88 emit (`:.6f` strip trailing zeros).
- Missing factor for plan: **fallback to current crude ann_factor** (do not invent); audit count.
- Annual mode: factor 100% → same as today’s ×1.
- Zero MODE_PREMIUM: leave blank/zero as today.

---

## 7. Policy Key Handling

No change — `format_qladmin_mpolicy` / Issue #2 width 11.

---

## 8. Estimated Record Counts

| Population (phase-1 join, 20260731 Output) | Count |
|--------------------------------------------|------:|
| Phase-1 quikridr | 5,083 |
| Populated ANN (out of scope) | ~2,613 |
| Blank ANN in scope | ~2,077 |
| Blank ANN where modal formula ≠ current MPREM | ~**1,257** |
| Of those, monthly (`01`) | ~824 |

Gold Nancy is blank ANN and in the change set.

---

## 9. Sample Trace

| Policy | Plan | Mode | Current MPREM | Proposed MPREM | Annual base now → proposed |
|--------|------|-----:|-------------:|---------------:|----------------------------|
| `9010722550C` | 1659C2 | 01 Dir | 9.6264 | ~8.7197 | 481.32 → **435.98** |
| `9010732078C` | 1659C2 | 06 | (blank-ANN path) | MODE/0.525/units | calendar → modalized |
| `9010367131C` | 17085M | 06 | 9.12 (ANN) | **unchanged** | already modalized |
| `9010779727C` | 1658C1 | (#88) | 5.8615 | recompute if blank+non-annual | UAT QuikVal |

---

## 10. Risks and Unknowns

- Same field drives Coverage Prem/Unit and LifePRO valuation compares — blast radius intentional.
- Applying modal factors only when factor CSV has plan; missing plans keep crude.
- PAC GL85 special 25/50 on quikmstr may diverge from plan CSV at MPREM emit time (small plan set).

---

## 11. Recommended Risk Agent Focus

1. Quantify blank-ANN rows that change (done in Risk).  
2. Confirm #26 populated rows untouched.  
3. Conditional Go on QuikVal UAT + gold Names check.  

---

## 12. Recommended Development Task (do not implement)

1. Bump `APP_VERSION` twin `app.py` + `QLA_Migration/app.py`.  
2. In #88 blank-ANN block only: replace `{12:1,6:2,3:4,1:12}` with modal-factor divisor from plan mapping + bill form; annual = ÷1.00.  
3. Cache bill form alongside billing mode if needed for MTHD/MTHB.  
4. Validator: Nancy `MPREM×MUNIT ≈ 436` (±0.05); Eric ANN unchanged; #88 annual blank unchanged vs ×1; factor-missing audit.  
5. Publish `Test_Validation/quikridr.csv` on PASS; full Output re-batch before Closure.
