# Issue #121 — Risk Review Report

**Issue:** #121 — Annual Renewable Term must not emit ETI status  
**Date:** 2026-07-28  
**Framework stage:** Risk complete (G3)  
**Code changes:** none (prohibited)  
**Dependency Gate:** PASS  
**Fallback simulated:** Option A — suppress PUT LE/ET on ART family  

**Status note:** Research complete. Development held pending user approval.

---

## Go / No-Go Recommendation

### **GO** (when approved)

Defect proven (90 false ETI on `5667AT`). Sibling ARTs do not show ETI today but share `PUT=LE`; family-scoped guard is low blast radius and prevents recurrence. Do not start coding until user says Approved for Development.

---

## 1. Current vs Proposed

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `MSTATUS` on Active+LE `5667AT` | 44 | 22 (contract path) | **Yes — 86** |
| `MSTATUS` on residual T/LP/LE `5667AT` at 44 | 44 | 54 | **Yes — 4** |
| `MSTATUS` on sibling ART | 54 | 54 | No |
| Global `ST_PUT_LE` | 44 | unchanged | No |

---

## 2. ART family research impact on risk

| Plan | ETI now | Risk if unguarded Active+LE appears later |
|------|--------:|-------------------------------------------|
| `5667AT` | 90 | Active defect |
| `5646AT` | 0 | Same LE present — would become 44 if Active |
| `57ATCR` | 0 | Same LE present — would become 44 if Active |

**Prefer family guard** over `5667AT`-only.

---

## 3. Population

| Metric | Count |
|--------|------:|
| ART family policies | 197 |
| Would change now | **90** |
| Sibling unchanged | 2 |
| Non-ART ETI | unchanged |

---

## 4. Fallback options

| Option | Assessment |
|--------|------------|
| **A. Suppress LE/ET PUT for ART family; use contract key** | **Prefer** |
| B. Global remap `ST_PUT_LE` | Reject |
| C. Force all ART ETI → 54 | Reject (86 are Active in LP) |
| D. Fix `5667AT` only | Acceptable short-term; weaker than A |

---

## 5. Trace

| Policy | Plan | Before | After |
|--------|------|--------|-------|
| 9010764158C | 5667AT | 44 | 22 |
| 9010761450C | 5667AT | 44 | 54 |
| 9010516211C | 5646AT | 54 | 54 |
| 9010916282C | 57ATCR | 54 | 54 |

---

## 6. Recommended Development task (when approved)

1. ART-family guard in MSTATUS interceptor (`5667AT`/`5646AT`/`57ATCR` or LifePRO ART plan codes).  
2. Align phase-1 `MPHSTAT` for the 90.  
3. Validator: zero `MSTATUS`/`MPHSTAT` 44 on ART family.  
4. Version bump both `app.py`.  
5. Do not edit global `ST_PUT_LE`.

---

## 7. Gate G3

- [x] Research incorporated  
- [x] GO with Option A  
- [x] No code at Risk  
- [x] Development deferred until explicit approval  
