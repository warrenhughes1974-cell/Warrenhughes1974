# Issue #27 — Ownership Decision

**Issue:** SL Phase of Insurance  
**Date:** 2026-06-28  
**Version:** v57.38  
**Stage:** Ownership Decision ✅

---

## 1. Decision summary

| Question | Decision |
|----------|----------|
| Is duplicate face amount a conversion defect? | **YES** — Converter ownership |
| Is SL a separate death benefit in LifePRO? | **NO** — Client + source evidence |
| Does QLAdmin have SL table rating implemented in conversion? | **NO** — Gap / client SME required |
| Is total policy premium wrong? | **NO** (generally) — `MMODEPREM` from PPOLC |
| Development authorized? | **NO** — Dependency Gate required first |

**Overall ownership:** **Mixed — Converter-primary**

---

## 2. Ownership matrix

| Data / behavior | LifePRO source | Current QLAdmin home | Correct owner | Required action |
|-----------------|----------------|----------------------|---------------|-----------------|
| Base death benefit face | PPBEN BA/BF `UNITS × VPU` | quikridr phase 1 `MUNIT/MVPU` | **Converter** | Preserve |
| PUA face | PPBEN PU | quikridr PUA phase | **Converter** | Preserve (existing PUA logic) |
| SL face (duplicate) | PPBEN SL mirrors base | quikridr SL phase | **Converter** | **Remove emit** |
| Substandard table code | PPBENTYP `SL_TABLE_CODE` | *(none)* | **Client SME + Converter** | Map to approved field OR document-only |
| Substandard extra premium | PPBEN SL `MODE_PREMIUM` | quikridr SL `MPREM` + quikmstr total | **Converter (display)** / **Runtime (billing)** | Suppress SL phase; total on `MMODEPREM` |
| Policy modal premium total | PPOLC `MODE_PREMIUM` | quikmstr `MMODEPREM` | **Converter** | No change |
| Underwriting class | PPBEN `UNDERWRITING_CLASS` | quikridr `MUWCLASS` | **Converter** | No change |
| Coverage tab layout | quikridr rows | QLAdmin UI | **Runtime (display)** | Correct when quikridr fixed |
| Table rating field semantics | LifePRO | QLAdmin field TBD | **Client (Eric) + QLAdmin SME** | **Dependency** |

---

## 3. Root cause ownership

| Layer | Verdict |
|-------|---------|
| **Converter** | **Primary** — emits SL as coverage; does not map `SL_TABLE_CODE` |
| **Product setup** | Not at fault — quikplan/MPLAN correct |
| **Runtime / QLAdmin** | **Display-only** — shows converted duplicate faithfully |
| **Client business rules** | **Input needed** — target field for table rating |
| **QLAdmin enhancement** | **Possible** if no field supports table rating |

---

## 4. Authorized fix direction (pending Dependency Gate)

**Converter (approved in principle, not authorized to code):**

1. Exclude `BENEFIT_TYPE = SL` from quikridr conversion (extend UV/FV filter pattern).
2. Optionally enrich base phase with `SL_TABLE_CODE` **only after** client confirms target QLAdmin field.
3. Do **not** merge SL premium into base `MPREM` unless client requests display change.
4. Emit SL governance audit CSV (policy, table code, SL premium, action taken).

**Explicitly NOT converter-owned:**

- QLAdmin runtime premium quote / coverage detail calculations
- New QLAdmin tables (`QuikUndw`) unless client expands scope

---

## 5. Client dependency

**BLOCKING for full closure:** Client / QLAdmin SME must confirm **where table rating should appear** (if anywhere beyond suppressing duplicate row).

**NON-BLOCKING for duplicate-face fix:** Suppressing SL quikridr rows can proceed once Development is authorized — does not require table rating mapping to fix No-Go duplicate face.

---

## 6. Impact recap

| Metric | Value |
|--------|------:|
| Policies with SL | 67 |
| Duplicate face policies | 46 |
| quikridr rows removed (if SL suppressed) | 68 |
| Premium-bearing SL rows | 28 (see premium analysis — PPOLC total preserved) |

---

## 7. Protected issues

Future fix must preserve: **#21M, #21M-FU, #21K, #25, #26, #28, #21D, #21J rollback**.

---

## 8. Go / No-Go

| Gate | Status |
|------|--------|
| Planning / Root Cause | ✅ PASS |
| Capability Discovery | ✅ PASS |
| Ownership Decision | ✅ PASS |
| **Dependency Gate** | ⏳ **REQUIRED** — client table-rating field |
| Development | ⛔ **NOT AUTHORIZED** |
| Validation | ⛔ **NOT AUTHORIZED** |

---

**Ownership Decision status:** ✅ COMPLETE
