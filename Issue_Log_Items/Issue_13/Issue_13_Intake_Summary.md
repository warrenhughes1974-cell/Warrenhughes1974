# Issue #13 — Intake Summary

**Issue:** Incorrect QL Status  
**Date:** 2026-07-04  
**Framework stage:** Intake complete (G0)  
**Status:** **Ready for Development** (Option A approved 2026-07-04)  
**Owner:** Conversion (Warren) · **Reporter:** Eric · **Business status:** No-Go (unchanged)

---

## Client symptom

Policies appear **Active / non-forfeiture** in QLAdmin (`MSTATUS` 41 Paid Up, 44 Extended Term, etc.) while LifePRO benefit extract shows **Terminated** with a termination reason (Expired, Lapsed, etc.).

Examples cited:

| LifePRO policy | QLAdmin key | QLAdmin status (reported) | LifePRO PPBEN status |
|----------------|-------------|---------------------------|----------------------|
| 9011101663 | 011101663C | Paid Up (41) | T / EX — Terminated Expired |
| 9010516211 | 010516211C | Extended Term (44) | T / LP — Terminated Lapsed |

---

## Normalized finding (2026-07-04 verification)

**The reported behavior still exists in the current production batch** (`QLA_Migration/Output/quikmstr.csv`, engine v57.47 run 2026-07-04).

This is **not a silent mapping failure**. The converter **intentionally** applies **PAID_UP_TYPE-first** logic in the `MSTATUS` composite interceptor (`app.py` ~5870–5878), then translates via `Master_Value_Translation.csv` `ST_PUT_*` / `ST_T_*` keys.

LifePRO holds **two status dimensions** on terminated non-forfeiture contracts:

| Source | Fields | Sample 011101663C | Sample 010516211C |
|--------|--------|-------------------|-------------------|
| **PPOLC** (policy master) | `CONTRACT_CODE`, `CONTRACT_REASON`, `PAID_UP_TYPE` | T / EX / **PU** | T / LP / **LE** |
| **PPBEN** (benefit row) | `STATUS_CODE`, `STATUS_REASON` | T / EX | T / LP |

Both sources agree the contract is **terminated**. The converter emits non-forfeiture QLAdmin codes because `PAID_UP_TYPE` wins:

| Policy | Converter key | Emitted `MSTATUS` | If termination-first |
|--------|---------------|-------------------|----------------------|
| 011101663C | `ST_PUT_PU` | **41** Paid Up | `ST_T_EX` → **56** Expired |
| 010516211C | `ST_PUT_LE` | **44** Extended Term | `ST_T_LP` → **54** Lapsed |

**Conclusion at intake:** Issue #13 is a **business precedence question**, not an unidentified conversion defect — unless the client decides termination must override non-forfeiture.

---

## Open business question (from issue log — unanswered)

> When a policy has both a terminated contract status (`CONTRACT_CODE=T`) and a non-forfeiture value (`PAID_UP_TYPE` = PU, RU, ET, LE, …), should QLAdmin reflect:
>
> 1. The **termination status** (Expired, Lapsed, Death, etc.), or  
> 2. The **non-forfeiture status** (Paid Up, Extended Term, Reduced Paid Up, etc.)?

The converter currently implements **option 2**. **Warren approved Option A (2026-07-04):** termination wins when `CONTRACT_CODE = T`.

---

## Fleet impact (read-only scan)

Policies with `CONTRACT_CODE=T` **and** `PAID_UP_TYPE` in `{PU, RU, ET, LE, LP, SP}`: **611**

| `PAID_UP_TYPE` | Count |
|----------------|------:|
| PU | 220 |
| ET | 170 |
| RU | 110 |
| LE | 89 |
| LP | 22 |

All 611 would change `MSTATUS` if precedence flipped to termination-first. Top `CONTRACT_REASON` values: DC (306), SR (126), MA (99), LP (75), EX (4).

Prior status analysis (`plan_analysis/status_analysis/`, 2026-05-28) documented the same PAID_UP_TYPE-first design and recommended **no conversion change until business confirms** cross-domain semantics.

---

## Domain and scope (first pass)

| In scope | Out of scope (initial) |
|----------|------------------------|
| `quikmstr.MSTATUS` precedence rule | Claim `CLAIMSTAT` (separate domain; status analysis already covers) |
| `quikridr` rider status if it mirrors master | UV benefit rows (no PPBEN status code) |
| Business sign-off on 611-policy population | Wholesale status rulebook rewrite |

---

## Related issues / research

| Reference | Relationship |
|-----------|--------------|
| `plan_analysis/status_analysis/` | Documented PAID_UP_TYPE-first interceptor; 0 policy MSTATUS conversion drift vs its own rules |
| Issue #34 | Uses `quikmstr.MSTATUS` for governance context |
| Issue #25 / #26 | Must not regress MPOLICY / MPREM |

---

## Artifacts

| Artifact | Status |
|----------|--------|
| Client issue description | Provided (issue log row) |
| Example policies | 011101663C, 010516211C |
| LifePRO PPOLC / PPBEN extracts | Present in `QLA_Migration/Source/` |
| Current `quikmstr.csv` | Present (2026-07-04 batch) |
| QLAdmin Help — MSTATUS semantics for post-termination NFO | **Not confirmed** |
| Client answer to precedence question | **Resolved — Option A** (Warren 2026-07-04) |
| Issue folder / intake summary | This document |
| Sample trace | `Issue_13_Sample_Trace.csv`, `_trace_issue13_samples.py` |

---

## G0 gate

- [x] Issue folder created (`Issue_Log_Items/Issue_13/`)
- [x] Intake summary written
- [x] Example policies listed and traced against current output
- [x] Owner assigned
- [x] No `app.py` / rulebook changes

**Framework progress:** G0 Intake ✅ · G1 Planning ✅ · G2 Dependency Gate ✅ · G3 Risk **GO** ✅  
**Next stage:** Development Agent (surgical `app.py` interceptor, v57.48, validator)
