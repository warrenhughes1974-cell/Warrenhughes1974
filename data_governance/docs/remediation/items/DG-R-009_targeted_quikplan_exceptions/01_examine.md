# DG-R-009 — Examine: Targeted QuikPlan exceptions

**Status:** AWAITING_DECISION  
**Date:** 2026-07-18  
**Rule IDs:** DG-QUIKPLAN-003, DG-QUIKPLAN-005, DG-QUIKPLAN-010, DG-QUIKPLAN-018  
**Primary table:** QuikPlan  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026` (141 plans after DG-R-008)

This item is a **small mixed bag** — four different checks, not one mass default.

---

## 1. Rules (plain English)

| Rule | Meaning |
|------|---------|
| **003** | Plan code must not end in PA / XP / XF / XS (those endings are reserved to *build* paid-up additions) |
| **005** | Plans starting with **A** need a valid annuity BASIS (NONQ, QUAL, NQIA, QLIA, TXBL). Other plans must leave BASIS blank |
| **010** | For plans not starting with 5: PAYYRS and PAYAGE cannot both be zero |
| **018** | Rounding rule (RRULE) must be **B** |

---

## 2. CSO findings (live)

| Rule | Findings | Plans |
|------|---------:|-------|
| 003 | **1** | `1970PA` |
| 005 | **2** | `A60MIR`, `A96DAR` (A-plans, blank BASIS) |
| 010 | **8** | Single premium / JPO set below |
| 018 | **0** | All 141 already RRULE=**B** |

### 010 detail — payment both zero

| PLAN | DESCR | PAYYRS / PAYAGE |
|------|-------|-----------------|
| 1668SP | SINGLE PREMIUM WHOLE LIFE | 0 / 0 |
| 10L171 | SINGLE PREMIUM WHOLE LIFE | 0 / 0 |
| 10L172 | SINGLE PREMIUM WHOLE LIFE | 0 / 0 |
| 17MJPO | SINGLE PREMIUM WHOLE LIFE | 0 / 0 |
| 1L17SP | SINGLE PREMIUM, WHOLE LIFE | 0 / 0 |
| 117JPO | SINGLE PREMIUM WHOLE LIFE | 0 / 0 |
| 986JPO | JUVENILE FUTURE PURCHASE OPTION | 0 / 0 |
| 982JPO | JUVENILE FUTURE PURCHASE OPTION | 0 / 0 |

### 005 / 003 detail

| PLAN | DESCR | Issue |
|------|-------|-------|
| A60MIR | MONTHLY INCOME RIDER | A-prefix → BASIS required, currently blank |
| A96DAR | DEPOSIT ANNUITY RIDER | A-prefix → BASIS required, currently blank |
| 1970PA | PAID UP ADDS - JUV EST BUILD PU AT 85 | Ends with **PA** (reserved suffix) — but description says it *is* a PUA product |

---

## 3. Production (WPA) comparison — important

| Topic | WPA evidence |
|-------|----------------|
| Single premium PAYYRS/PAYAGE | **7/7** SPWL plans use **PAYYRS=1, PAYAGE=0** (matches `Data_Goverence.txt`) |
| A-plan BASIS | **0** blank; values QUAL/NONQ/NQIA/TXBL only |
| PUA suffix (PA/XP/XF/XS) | **0** plans |
| RRULE | **1847 = A**, 1 blank — **not B** |

So:

- Single-premium fix on CSO should follow WPA (**1 / 0**), not invent something new.
- Blank BASIS on A-plans is wrong relative to WPA (they always populate it) — but we **must not guess** QUAL vs NONQ without business/source.
- `1970PA` is a CSO-only naming conflict with the PUA-suffix rule.
- **RRULE:** CSO already matches the written default B; WPA unanimously uses **A**. Same family as DG-R-004/006/007 — do **not** mass-flip WPA to B in this item without a separate rounding decision.

---

## 4. Conversion / rulebook

| Field | Sync_Rulebook today |
|-------|---------------------|
| RRULE | Default **B** (CSO matches; WPA does not) |
| PAYYRS / PAYAGE | From PREM_CEASE_POINT via ROUTE_PAY_*; default 0 |
| BASIS | Blank default (no annuity mapping) |

`Data_Goverence.txt`: single premium → PAYYRS=1, PAYAGE=0; rounding default B; no PA/XP/XF/XS endings; A-plans need valid BASIS.

---

## 5. Options by cluster

### Cluster SP — Single premium payment period (010) — **recommended to fix**

**Action on CSO:** for the six clearly single-premium whole life plans  
`1668SP, 10L171, 10L172, 17MJPO, 1L17SP, 117JPO`  
set **PAYYRS=1, PAYAGE=0**.

Also: conversion follow-on so single-premium emits 1/0 (document in CONVERSION_SYSTEM_DEFAULTS; code only if emit path does not already).

| Pros | Cons |
|------|------|
| Matches WPA + written business rule | Touches 6 plans |

### Cluster JPO — 986JPO / 982JPO (010)

Not labeled single premium. Options: (J1) set PAYYRS=1/PAYAGE=0 like SP, (J2) leave until business confirms, (J3) governance exception.

**Recommend J2** unless you know these are single-pay.

### Cluster BASIS — A60MIR / A96DAR (005)

Need the correct BASIS code(s). **Do not invent.** Options: (B1) business provides codes then set data, (B2) hold list / defer, (B3) revise “A = annuity” rule if these riders should be exempt.

**Recommend B2** until codes are known (A96DAR is annuity-related; A60MIR may or may not be).

### Cluster PUA — 1970PA (003)

Options: (P1) rename plan (high blast radius — not recommended), (P2) governance exception / hold for known PUA product codes, (P3) retire/soften 003 (not recommended — rule protects real PUA construction).

**Recommend P2** — keep the rule; treat `1970PA` as an approved exception or leave as known residual.

### Cluster RRULE — (018)

CSO: nothing to do.  
WPA A vs rule B: **out of scope for data rewrite in this item.** Separate decision later (revise rule to allow A, or confirm B and plan a controlled WPA change).

---

## 6. Recommended package (discussion — not a decision)

1. **Approve Cluster SP** — set CSO single-premium plans to PAYYRS=1 / PAYAGE=0; note conversion default.  
2. **Defer JPO** until confirmed.  
3. **Defer BASIS** until business codes for A60MIR / A96DAR.  
4. **Exception/hold 1970PA** (do not rename).  
5. **RRULE WPA** — park as follow-on (production uses A).

---

## 7. Validation (after any Implement)

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "<item>/validation_out" \
  --rule DG-QUIKPLAN-003 --rule DG-QUIKPLAN-005 --rule DG-QUIKPLAN-010 --rule DG-QUIKPLAN-018
```

---

## 8. Decision prompt

Reply with something like:

`Decision: SP yes (PAYYRS=1/PAYAGE=0 on 6 SPWL); JPO defer; BASIS defer; 1970PA exception/hold; RRULE WPA out of scope`

Or adjust any cluster.
