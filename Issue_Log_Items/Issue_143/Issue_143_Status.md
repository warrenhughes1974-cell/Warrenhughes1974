# Issue #143 — Status Record

**Issue:** Units Incorrect (RPU)  
**Last updated:** 2026-08-18  
**Package:** `Issue_Log_Items/Issue_143/`  
**Framework status:** **CLOSED**  
**Resolution version:** **v58.96**

---

## Current Status

| Stage | Status |
|-------|--------|
| Discovery | Complete |
| Intake | Complete |
| Planning | Complete |
| Dependency Gate | Complete |
| Risk | Complete — Go |
| Development | Complete — v58.96 (no further logic changes) |
| Validation | **PASS** |
| Regression | **PASS** |
| Dedicated smoke | **PASS 9/9** |
| Release smoke | **PASS** / **RELEASE_OK** |
| Authorized #124 reseed | **COMPLETE** |
| Closure (G7) | **CLOSED** — 2026-08-18 |

---

## Recorded gates

| Gate | Result |
|------|--------|
| Resolution Version | **v58.96** |
| Validation | **PASS** |
| Regression | **PASS** |
| Smoke | **PASS 9/9** |
| Release smoke (`--smoke-only`) | **PASS** / **RELEASE_OK** (captured 2026-08-18T08:48:36; `#143 BF RPU MUNIT` PASS) |
| Authorized #124 reseed | **COMPLETE** |

---

## Population lock

| Item | Count |
|------|------:|
| Authorized MUNIT corrections | **23** |
| Unauthorized corrections | **0** |
| Unexplained regression differences | **0** |
| Outstanding #143 downstream dependencies | **0** |

---

## Gold policy `9010757606C`

| Field | Value |
|-------|------:|
| Corrected `MUNIT` | 19.10196 |
| Pre-reseed `MDB` | 25000.00 |
| Post-reseed `MDB` | 19101.96 |

---

## Authorized #124 reseed

Existing emitter only (`Issue_Log_Items/Issue_124/tools/quikiswl_emit.py`).  
Existing rule unchanged: `MDB = MUNIT × 1000`.  
QuikIswl rows = **2,268** (unchanged). All 23 Issue #143 ISWL records now store `MDB` from the corrected `MUNIT`. Unrelated `MDB ≠ current MUNIT × 1000` = **0**.

---

## Final resolution

Issue #143 is Closed in v58.96. The 23 SME-authorized BF Reduced Paid-Up policies now derive MUNIT from BF_CURRENT_DB / VALUE_PER_UNIT so QLAdmin Amount Ins reproduces the LifePRO paid-up death benefit. Validation, Regression, and final Smoke testing passed. The existing Issue #124 QuikIswl emit was subsequently executed, and all 23 affected ISWL records now store MDB = corrected MUNIT × 1000. Gold policy 9010757606C now contains MUNIT 19.10196 and MDB 19101.96. No unauthorized or unexplained differences remain.

---

## Next action

None. Issue #143 is Closed. No outstanding #143 downstream dependencies.
