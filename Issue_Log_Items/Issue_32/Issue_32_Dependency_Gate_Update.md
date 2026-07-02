# Issue #32 — Dependency Gate Update (Post-Screenshot)

**Issue:** #32 — Policy Loan Conversion  
**Gate stage:** Dependency Gate — **Partial PASS on mapping evidence**  
**Evidence:** LifePRO screenshots — policy `9010331768`  
**Generated:** 2026-06-29  
**Engine:** v57.39 (unchanged)

---

## 1. Gate Status

| Gate area | Prior status (2026-06-29 planning) | Post-screenshot status |
|-----------|-------------------------------------|-------------------------|
| Source authority (PLOAN) | PASS | **PASS** — confirmed on trace policy |
| MPOLICY / crosswalk | PASS | **PASS** |
| MLOANINT scale | **BLOCKED** | **PASS** — evidence: 5.00 percent |
| MLOANPRIN definition | **BLOCKED** | **PASS** — evidence: LOAN_BALANCE |
| MLOANDATE source | **BLOCKED** | **PASS** — evidence: ACCRUAL_DATE |
| MLOANIDT source | **BLOCKED** | **PARTIAL PASS** — ACCRUAL_DATE on trace; fleet fallback TBD |
| MLOANINTX source | **BLOCKED** | **PARTIAL PASS** — value A inferred; PLOAN column rejected |
| MLOANACCR source | **BLOCKED** | **STILL BLOCKED** — not in PLOAN |
| MLOANBAL derivation | **BLOCKED** | **STILL BLOCKED** — depends on MLOANACCR |
| MLOANBILL source | **BLOCKED** | **PASS (default)** — no evidence; 0.00 acceptable |
| Zero-balance scope | **BLOCKED** | **STILL BLOCKED** — no screenshot evidence |
| STATUS filter | **BLOCKED** | **STILL BLOCKED** |
| Development authorization | **NO-GO** | **NO-GO** — accrual gap remains |

**Overall gate:** **HOLD** — proceed to **Ownership Decision** on narrowed question set only.

---

## 2. Dependencies Cleared by Screenshot

### D-1 — Interest rate scale ✅

| Item | Resolution |
|------|------------|
| Question | `.0500` → 0.05 or 5.00? |
| Evidence | Screen `5.00000%` = PLOAN `.0500` |
| Decision | **`MLOANINT = INTEREST_RATE × 100`** |
| Config | `mloanint_scale: AS_PERCENT` |

### D-2 — Principal field ✅

| Item | Resolution |
|------|------------|
| Question | Which PLOAN field is LifePRO Principal? |
| Evidence | Screen 3,707.11 = `LOAN_BALANCE`; ≠ `ORIG_LOAN_AMOUNT` 3,522.25 |
| Decision | **`MLOANPRIN ← LOAN_BALANCE`** |

### D-3 — Loan balance date ✅

| Item | Resolution |
|------|------------|
| Question | MLOANDATE source? |
| Evidence | Last Accrued Date 07/25/2025 = `ACCRUAL_DATE` 20250725 |
| Decision | **`MLOANDATE ← ACCRUAL_DATE`** |

### D-4 — INT_METHOD as MLOANINTX source ❌ REJECTED

| Item | Resolution |
|------|------------|
| Hypothesis | Map `INT_METHOD` → MLOANINTX |
| Fleet profile | 100% `INT_METHOD = D` |
| Screenshot | Interest Method = Advance |
| Decision | **Do not map INT_METHOD** — column does not encode A/R |

### D-5 — INTEREST_TYPE as MLOANINTX source ❌ REJECTED

| Item | Resolution |
|------|------------|
| Fleet profile | 100% `INTEREST_TYPE = F` |
| Screenshot | Interest Type = Fixed (separate from Method) |
| Decision | **Do not map INTEREST_TYPE to MLOANINTX** |

### D-6 — MLOANBILL default ✅

| Item | Resolution |
|------|------------|
| Evidence | Not shown on screenshot |
| Decision | **Default 0.00** unless SME overrides |

---

## 3. Dependencies Still Open

### O-1 — MLOANACCR source 🔴 CRITICAL

| Attribute | Detail |
|-----------|--------|
| Blocker | PLOAN `ACCRUED_INT_AMT = 0.00` fleet-wide; screen shows 18.19 |
| Impact | Cannot populate QuikLoan accrued interest from extract |
| Required input | SME: Does QLAdmin calculate interest on load? If yes, emit 0. If no, provide formula or secondary source |
| Gate | **FAIL until resolved** |

### O-2 — MLOANBAL derivation 🔴 CRITICAL

| Attribute | Detail |
|-----------|--------|
| Blocker | Net balance = Principal − Interest; not raw LOAN_BALANCE |
| Dependency | O-1 |
| Gate | **FAIL until O-1 resolved** |

### O-3 — MLOANINTX authoritative source 🟡 MEDIUM

| Attribute | Detail |
|-----------|--------|
| Evidence | Screenshot shows Advance; PLOAN has no A/R code |
| Working default | `MLOANINTX = A` via config |
| Required input | SME written confirm: fleet-wide advance method |
| Gate | **PARTIAL** — can default with sign-off |

### O-4 — MLOANIDT precedence for 109 policies 🟡 MEDIUM

| Attribute | Detail |
|-----------|--------|
| Evidence | Trace policy: all date fields equal |
| Fleet | 109 active policies missing LAST_REPAY_DATE |
| Proposed | ACCRUAL_DATE first in precedence |
| Required input | SME confirm ACCRUAL_DATE = paid-to date |
| Gate | **PARTIAL** |

### O-5 — Emit scope (zero-balance, STATUS) 🟡 MEDIUM

| Attribute | Detail |
|-----------|--------|
| Evidence | None from screenshot |
| Gate | **UNCHANGED — FAIL** |

### O-6 — Data quality policy 9011190668 🟢 LOW

| Attribute | Detail |
|-----------|--------|
| Status | Unchanged — blank ACCRUAL_DATE, $621.78 balance |
| Gate | **FAIL for that policy** |

---

## 4. Updated Decision Matrix

| Condition | Route |
|-----------|-------|
| SME confirms QLAdmin recalculates MLOANACCR (emit 0, MLOANBAL = LOAN_BALANCE or QLAdmin derives) | **Ownership Decision** → conditional Development |
| SME provides accrual formula + as-of date rule | **Ownership Decision** → Development with calc spec |
| SME cannot resolve accrual | **HOLD** — request LifePRO actuarial/IT |
| Partial sign-off (rate/principal/dates only) | **HOLD** — insufficient for emit |

---

## 5. Artifacts Updated by This Gate Pass

| Artifact | Update |
|----------|--------|
| `Issue_32_LifePRO_Screenshot_Evidence_Trace.md` | New — full trace |
| `Issue_32_Policy_9010331768_Trace.csv` | New — comparison table |
| `Issue_32_Field_Mapping_Revision.md` | New — v1.1 mapping |
| `Issue_32_SME_Questions_Updated.md` | Revised question list |
| `Issue_32_Next_Stage_Prompt.md` | Revised handoff |
| `Issue_32_Screenshot_Fleet_Stats.json` | Fleet follow-up stats |

**Unchanged:** `quikloan_derivation_rules.json`, `quikloan_converter.py`, `app.py`

---

## 6. Recommended SME Session (Focused)

1. Show screenshot vs PLOAN trace table (`Issue_32_Policy_9010331768_Trace.csv`)  
2. **Single decisive question:** Does QLAdmin calculate loan interest from MLOANPRIN + MLOANINT + dates, or must MLOANACCR be loaded?  
3. Confirm fleet-wide **Interest in Advance** → `MLOANINTX = A`  
4. Optional: second screenshot policy at 7.40% rate to confirm scale  

---

## 7. Gate Verdict

**Dependency Gate: PARTIAL PASS**

- **3 critical mapping questions resolved** (rate scale, principal, balance date)  
- **1 critical mapping question opened wider** (accrued interest not in PLOAN)  
- **1 derivation revised** (net balance ≠ LOAN_BALANCE)  
- **Development: STILL BLOCKED**

**Next route:** Ownership Decision Agent — accrual ownership question only.

---

**Stop point:** Gate update complete. No code, config, or emit changes.
