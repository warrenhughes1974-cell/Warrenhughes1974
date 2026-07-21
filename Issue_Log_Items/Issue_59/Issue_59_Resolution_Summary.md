# Issue #59 — Resolution Summary

**Issue:** #59 — Incorrect QL Status (`quikmstr.MSTATUS`)  
**Framework stage:** Closure Agent  
**Final status:** **CLOSED** (conversion complete; client business status remains No-Go until UAT Go)  
**Engine version:** **v57.84**  
**Closed date:** 2026-07-14  
**Owner:** Conversion (Warren) · **Reporter:** Eric  

---

## Resolution (issue log — paste-ready)

**Resolution:** For seven client-cited policies only, Active contracts with PAID_UP_TYPE=LP now emit Active (22) instead of Lapsed (54), and Suspended Death Claim Pending (S/DP) emits status 50 instead of Paid Up.

```text
59 Closed Incorrect QL Status — Scoped to seven client policies: Active+PAID_UP_TYPE=LP emit MSTATUS 22 (not 54); CONTRACT_CODE=S+DP emits 50 Death Claim Pending (not PUT Paid Up). No other policies' status changed. Traces: 01122D991C, 014FG8217C, 016FG8217C, 01ML8171C, 01ML8250C, 01ML8522C → 22; 010521213C → 50.
```

---

## Problem Statement

Six policies showed Lapsed in QLAdmin while Active on the 6/30/26 extract. One policy (`010521213C`) showed Paid Up / “Active” in QLAdmin while LifePRO was Death Claim Pending.

---

## Root Cause

**Category:** [x] Mapping error

The `quikmstr.MSTATUS` interceptor let `PAID_UP_TYPE` override non-terminated contracts. `PUT_LP` → 54 on Active contracts, and `PUT_PU` → 41 on Suspended `S`/`DP` (skipping existing `ST_S_DP` → 50). Issue #49 had already corrected other Active+LP cases via later-phase override; these seven had no such path.

---

## Resolution

Interceptor updated in **v57.84** with **hard scope to the seven client policy keys only** (per Development instruction — no fleet-wide PUT change). Surgical Output patch applied the same seven `MSTATUS` values (and matching phase-1 `MPHSTAT`). Validator hard-guards that no other `MSTATUS` differs from the pre-fix baseline.

### Files changed

| File | Change |
|------|--------|
| `app.py` / `QLA_Migration/app.py` | Scoped MSTATUS branches + **v57.84** |
| `tools/validators/validate_issue59_mstatus.py` | New — 7-only delta guard |
| `QLA_Migration/Output/quikmstr.csv` | 7 MSTATUS values (gitignored load package) |
| `QLA_Migration/Output/quikridr.csv` | 7 phase-1 MPHSTAT values |
| `Issue_Log_Items/Issue_59/*` | Framework artifacts |

### Rulebook changes

None — `ST_A_` and `ST_S_DP` already existed.

### Engine changes

- After Issue #13 `T` branch: scoped `S` → `S_{REASON}`; scoped `A`+`LP` → `A_`
- Else existing PUT / code_reason logic unchanged

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_59_Intake_Summary.md` |
| Planning | `Issue_59_Planning_Report.md` |
| Dependency Gate | `Issue_59_Dependency_Gate.md` — PASS |
| Risk | `Issue_59_Risk_Review_Report.md` — GO |
| Implementation | `Issue_59_Implementation_Notes.md` |
| Validation | `Issue_59_Validation_Report.md` — **PASS** |
| Regression | `Issue_59_Regression_Report.md` — **PASS** |
| Validator | `tools/validators/validate_issue59_mstatus.py` |
| Baseline | `evidence/quikmstr_pre_v5784_baseline.csv` |

---

## Trace Policy Confirmation

| Policy | Client expected | Emitted | Match |
|--------|-----------------|---------|-------|
| 01122D991C | Active | 22 | Yes |
| 014FG8217C | Active | 22 | Yes |
| 016FG8217C | Active | 22 | Yes |
| 01ML8171C | Active | 22 | Yes |
| 01ML8250C | Active | 22 | Yes |
| 01ML8522C | Active | 22 | Yes |
| 010521213C | Death Claim Pending | 50 | Yes |

---

## Explicitly Not Changed

- [x] Issue #25 MPOLICY padding  
- [x] Issue #26 MPREM mapping  
- [x] Issue #13 `T` termination-first  
- [x] Issue #49 later-active-phase cohort (35 policies)  
- [x] Non-scoped Active+LP / Suspended statuses  
- [x] `Master_Value_Translation.csv` / Sync rulebooks  
- [x] MNFOPT / premium / client tables  

---

## Fleet Impact

| Metric | Value |
|--------|------:|
| `MSTATUS` rows changed | **7** |
| Row count delta (all tables) | **0** |
| Non-scoped `MSTATUS` changes | **0** |

---

## Production Readiness + Git Release (G7)

| Check | Status |
|-------|--------|
| Validators PASS (G5 + G6) | **PASS** |
| `app.py` version bumped | **v57.84** (both copies) |
| Issue-scoped git commit | `79d199dbc721bb4a10936ee60877bfc260e9b8f7` |
| **`git push` to remote** | `origin/issue-34-pr7-quikisrr` |
| Network batch note | Output gitignored — reload `Test_Validation` CSVs after pull; full batch optional (scoped interceptor) |

---

## Client UAT

| Item | Status |
|------|--------|
| QLAdmin screen verification | **Pending** — reload `Output/Test_Validation/quikmstr.csv` + `quikridr.csv` |
| Client sign-off | Pending Eric |

---

## Residual Risks / Follow-ups

| Item | Owner | Notes |
|------|-------|-------|
| Client UAT on seven policies | Eric | Business No-Go until Go |
| Broader Active+LP / S-reason (non-scoped) | Conversion | Intentionally out of scope unless new tickets |

---

## Rollback

1. Revert v57.84 interceptor branches in both `app.py` files (or revert closure commit)  
2. Restore `MSTATUS` / phase-1 `MPHSTAT` from `evidence/quikmstr_pre_v5784_baseline.csv` (and prior ridr if archived)  
3. Re-run `validate_issue59_mstatus.py` (expect FAIL on traces) and confirm #49/#13 samples  

---

## Issue Log Entry (paste-ready)

> **Issue #59 — Incorrect QL Status — CLOSED (2026-07-14).**  
> **Resolution:** For seven client-cited policies only, Active contracts with PAID_UP_TYPE=LP now emit Active (22) instead of Lapsed (54), and Suspended Death Claim Pending (S/DP) emits status 50 instead of Paid Up.  
> **Evidence:** Validation and regression PASS; traces 01122D991C–01ML8522C → 22; 010521213C → 50; exactly 7 MSTATUS deltas. **Preserved:** MPOLICY (#25), MPREM (#26), #13, #49. **Follow-ups:** Client UAT reload quikmstr+quikridr.

---

## Framework Checklist

- [x] Intake  
- [x] Planning  
- [x] Dependency Gate PASS  
- [x] Risk Go  
- [x] Development (v57.84, scoped)  
- [x] Validation PASS  
- [x] Regression PASS  
- [x] Closure — **Resolution:** one-line + this summary  
