# Issue [ID] — Resolution Summary

**Issue:** [ID] — [Title]  
**Framework stage:** Closure Agent  
**Final status:** **Closed** | Ready for Client UAT  
**Engine version:** v[xx.xx]  
**Closed date:** [YYYY-MM-DD]  
**Owner:** Conversion | Client | Both

---

## Resolution (issue log — paste-ready)

**Resolution:** [One brief sentence — what the fix was. Plain language. Do not include engine version.]

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

[What the client reported — 1 short paragraph]

---

## Root Cause

**Category:** [ ] Mapping error  [ ] Source extract defect  [ ] Scope gap  [ ] Client definition  [ ] QLAdmin behavior  [ ] Other

[2–3 sentences explaining why the issue occurred]

---

## Resolution

[What was done — plain language, 1 paragraph]

### Files changed

| File | Change |
|------|--------|
| | |

### Rulebook changes

| Rulebook | Before | After |
|----------|--------|-------|
| | | |

### Engine changes

[Bullet list or "None — rulebook only"]

---

## Evidence

| Artifact | Path |
|----------|------|
| Planning report | |
| Risk review | |
| Validation report | PASS |
| Regression report | PASS |
| Validation script | `QLA_Migration/_validate_issue[id]_*.py` |

---

## Trace Policy Confirmation

| Policy | Client expected | Emitted | Match |
|--------|-----------------|---------|-------|
| | | | Yes |

---

## Explicitly Not Changed

- [ ] quikmstr.MMODPREM / modal premium totals
- [ ] Issue #26 MPREM mapping on unrelated logic
- [ ] Issue #25 MPOLICY padding
- [ ] MVPU, MUNIT, fees, premium history
- [ ] Client/relationship logic
- [ ] [issue-specific list]

---

## Fleet Impact

| Metric | Value |
|--------|------:|
| Rows changed (target field) | |
| Row count delta (all tables) | 0 |

---

## Production Readiness + Git Release (G7)

| Check | Status |
|-------|--------|
| Validators PASS (G5 + G6) | |
| `app.py` version bumped (if batch/rate path changed) | |
| Issue-scoped git commit | hash: |
| **`git push` to remote** | branch: |
| Network batch note (`Output/` gitignored) | GENERATE RATE TABLES / full batch after pull |

---

## Client UAT

| Item | Status |
|------|--------|
| QLAdmin screen verification | Pending / Pass / N/A |
| Client sign-off | [name/date if applicable] |

---

## Residual Risks / Follow-ups

| Item | Owner | Notes |
|------|-------|-------|
| None | — | — |

---

## Rollback

1. Revert commit [hash] or restore rulebook lines [x–y]
2. Re-run batch from baseline Source/
3. Confirm validators pass on prior version

---

## Issue Log Entry (paste-ready)

> **Issue #[ID] — [Title] — CLOSED ([date]).**  
> **Resolution:** [One brief sentence — what the fix was.]  
> **Evidence:** Validation and regression PASS; trace policies [list] confirmed. **Preserved:** MPOLICY padding (#25), MPREM mapping (#26), [other]. **Follow-ups:** [none or list].

---

## Framework Checklist

- [x] Intake
- [x] Planning
- [x] Dependency Gate PASS
- [x] Risk Go
- [x] Development
- [x] Validation PASS
- [x] Regression PASS
- [x] Closure — **`Resolution:`** one-line + long-form summary
- [x] Git commit + push (G7 release gate)
