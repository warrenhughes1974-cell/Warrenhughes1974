# Issue #143 — Closure Summary

**Issue:** #143 — Units Incorrect (RPU)  
**Framework stage:** Closure Agent (G7)  
**Final SDLC status:** **CLOSED**  
**Resolution version:** **v58.96**  
**Closed date:** 2026-08-18  
**Owner:** Conversion (Warren) · **Reporter:** Eric  
**Validation:** **PASS**  
**Regression:** **PASS**  
**Smoke:** **PASS 9/9** (`python tools/validators/validate_issue143_smoke.py`)  
**Release smoke:** **PASS** / **RELEASE_OK** (`python tools/validators/validate_release_closed_issues.py --smoke-only`, captured 2026-08-18T08:48:36)  
**Authorized #124 reseed:** **COMPLETE**  
**Accountability:** **IN_DATA** (issue validator PASS on full `QLA_Migration/Output/`)

---

## 1. Original issue statement

Some Reduced Paid-Up policies in LifePRO did not have units reduced. Client instruction: compare death benefit to PPBENTYP Column DD. Do not assume every RPU must have reduced units.

SME lock 2026-08-18: on policies where LifePRO units still show the original issue quantity but Column DD holds the paid-up death benefit, QLAdmin units must become `DD / VALUE_PER_UNIT` so Amount Ins equals LifePRO death benefit.

---

## 2. Root cause

**Category:** [x] Source extract / LifePRO NFO data  [x] Mapping (copy of unreduced units)  [ ] Scope gap  [ ] Client definition  [ ] QLAdmin behavior

LifePRO RPU (`PAID_UP_TYPE=RU`) does not always reduce `NUMBER_OF_UNITS`. On **23** BF policies, units remained the original issue quantity while `BF_CURRENT_DB` (Column DD) held the paid-up death benefit. The converter mapped `NUMBER_OF_UNITS → MUNIT` as-is, so Amount Ins stayed at original face. **82** other BF RPU rows already matched DD; **199** traditional BA RPU rows have no DD to remap.

---

## 3. Approved business rule

```text
IF PAID_UP_TYPE = RU
AND TYPE_CODE = BF
AND BF_CURRENT_DB > 0
AND abs(NUMBER_OF_UNITS - (BF_CURRENT_DB / VALUE_PER_UNIT)) > 0.01
THEN MUNIT = BF_CURRENT_DB / VALUE_PER_UNIT
```

Purpose: `MUNIT × MVPU` must equal PPBENTYP Column DD / `BF_CURRENT_DB`.

Identify RPU by `PAID_UP_TYPE=RU`, not `MSTATUS=45` only (10 of the 23 are status 53/55).

---

## 4. Implementation summary

Isolated post-map override in `qla_core/issue143_rpu_munit.py`, called from both `app.py` files after normal `NUMBER_OF_UNITS → MUNIT` and **before** Issue #55 decimal emit. PPOLC supplies the RU set; PPBENTYP supplies seq-1 `TYPE_CODE` and `BF_CURRENT_DB`. Output apply remapped the 23 current `quikridr` rows only.

**Not changed:** default rulebook map, `MPREM`, `MVPU`, `MSAVEUNIT` (#108A), MPOLICY (#2), #55 floor, #124 `MDB = MUNIT × 1000` formula.

---

## 5. Exact production version

**v58.96** — `app.py` and `QLA_Migration/app.py`.

---

## 6. Population affected

| Cohort | Count | Action |
|--------|------:|--------|
| BF RPU mismatch (authorized) | **23** | Remap `MUNIT` |
| BF RPU already aligned | **82** | Unchanged |
| Traditional BA RPU | **199** | Not remapped |
| QuikRidr total rows | **6,934** | Count unchanged |

All 23 are ISWL plans `1658C1` / `1659C2` / `1659CR`.

---

## 7. Gold-policy before/after trace

**Policy:** `9010757606C` · Plan `1659C2`

| Item | Before | After |
|------|--------|-------|
| LifePRO `NUMBER_OF_UNITS` | 25.00000 | 25.00000 (source unchanged) |
| QLAdmin `MUNIT` | 25.00000 | **19.10196** |
| `MVPU` | 1000.00 | 1000.00 |
| Amount Ins (`MUNIT × MVPU`) | 25000.00 | **19101.96** |
| `MPREM` | 9.77037 | 9.77037 |
| `MSAVEUNIT` | blank | blank (#108A) |
| `MPOLICY` | 9010757606C | 9010757606C |

---

## 8. Validation results

Independent Validation **PASS** (source-derived, not Development’s candidate helper):

- 23 independently derived candidates
- 23/23 corrected; 0 missing; 0 unauthorized
- 23/23 Amount Ins reconciliations within $0.02
- 82/82 aligned BF unchanged
- 0 of 199 BA remapped

Report: `Issue_143_Validation_Report.md`

---

## 9. Regression results

Regression **PASS**:

- QuikRidr 6,934 → 6,934
- Exactly 23 rows changed; field = `MUNIT` only
- 0 unauthorized remaps
- 0 unexplained differences

Report: `Issue_143_Regression_Report.md`

---

## 10. Protected-issue results

| Issue | Result |
|-------|--------|
| #2 | PASS / extra-C key behavior unchanged |
| #25 | Protected via #2 width-11 |
| #26 | Fleet `MPREM` diffs = 0 |
| #55 | PASS |
| #108A | PASS (`MSAVEUNIT` blank/unchanged) |
| #105 | PASS |
| #119 | PASS |

---

## 11. Pre-existing validator/environment observations

| Item | Class |
|------|-------|
| #26 script FAIL (missing `*_Extract_20260530.csv`) | PRE-EXISTING environment; MPREM identity proven vs baseline |
| #21K script FAIL (missing DBF / legacy key) | PRE-EXISTING; not caused by #143 |
| 15 BA “absent” naive keys | Lookup artifact vs Issue #2 extra-C (`9018166C` → `9018166CC`); rows exist in baseline and Output; **not** an #143 defect; **do not change #2** |

---

## 12. Issue #124 downstream reseed — COMPLETE

Issue #124 remains correct and was **not** modified.

Existing rule (unchanged): `MDB = MUNIT × 1000`.

Authorized reseed executed existing emitter only:

```text
python Issue_Log_Items/Issue_124/tools/quikiswl_emit.py
```

| Item | Result |
|------|--------|
| Action | Existing Issue #124 emit only |
| Emit status | **SUCCESS** |
| QuikIswl rows | **2,268** (unchanged) |
| Authorized #143 ISWL records with `MDB = corrected MUNIT × 1000` | **23 / 23** |
| Unrelated rows with `MDB ≠ current MUNIT × 1000` | **0** |
| Classification | **COMPLETE** |

Gold `9010757606C`:

| | Value |
|--|------:|
| Corrected `MUNIT` | **19.10196** |
| Pre-reseed stored `MDB` | 25000.00 |
| Post-reseed stored `MDB` | **19101.96** |

Smoke Condition #8 PASSes. **0 outstanding #143 downstream dependencies.**

---

## 13. Rollback reference

| Item | Path / action |
|------|----------------|
| Pre-#143 QuikRidr | `evidence/quikridr_pre_issue143_20260818T130527Z.csv` |
| Engine hook | Remove Issue #143 block in both `app.py` files (before `apply_quikridr_decimal_emit`) |
| Rule module | `qla_core/issue143_rpu_munit.py` |
| Restore Output | Copy baseline CSV over `QLA_Migration/Output/quikridr.csv` |
| Version | Revert `APP_VERSION` from v58.96 if rolling back the hook |

---

## 14. Final resolution statement

Issue #143 is Closed in v58.96. The 23 SME-authorized BF Reduced Paid-Up policies now derive MUNIT from BF_CURRENT_DB / VALUE_PER_UNIT so QLAdmin Amount Ins reproduces the LifePRO paid-up death benefit. Validation, Regression, and final Smoke testing passed. The existing Issue #124 QuikIswl emit was subsequently executed, and all 23 affected ISWL records now store MDB = corrected MUNIT × 1000. Gold policy 9010757606C now contains MUNIT 19.10196 and MDB 19101.96. No unauthorized or unexplained differences remain.

---

## 15. Final SDLC status

**CLOSED**

| Gate | Result |
|------|--------|
| Resolution version | **v58.96** |
| Validation | **PASS** |
| Regression | **PASS** |
| Dedicated smoke | **PASS 9/9** — `python tools/validators/validate_issue143_smoke.py` |
| Release smoke | **PASS** / **RELEASE_OK** — `python tools/validators/validate_release_closed_issues.py --smoke-only` (captured 2026-08-18T08:48:36; `#143 BF RPU MUNIT` PASS) |
| Authorized #124 reseed | **COMPLETE** — existing `quikiswl_emit.py` only; 2,268 rows; rule `MDB = MUNIT × 1000` unchanged |
| Authorized MUNIT corrections | **23** |
| Unauthorized corrections | **0** |
| Unexplained regression differences | **0** |
| Outstanding #143 downstream dependencies | **0** |
| Issue validator on full Output | PASS — `python tools/validators/validate_issue143_rpu_munit.py` |
| Accountability | **IN_DATA** (equivalent spot-check: issue validator PASS on current full Output) |
| Test_Validation | `QLA_Migration/Output/Test_Validation/quikridr.csv` published |
| Completed Issues guide | Row 143 updated (reseed COMPLETE) |

Git commit/push was not requested in this Closure instruction; issue-scoped files remain in the working tree for the user’s release commit.
