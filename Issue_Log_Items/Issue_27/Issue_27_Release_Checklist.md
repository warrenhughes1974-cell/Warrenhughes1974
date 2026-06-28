# Issue #27 — Release Checklist

**Version:** v57.39  
**Date:** 2026-06-28  
**Issue:** SL Phase of Insurance — quikridr suppression

---

## Pre-release (complete)

| # | Item | Owner | Status |
|---|------|-------|--------|
| 1 | Root cause confirmed (SL ≠ coverage) | Planning | ✅ |
| 2 | Business rule approved (rating structure) | Client | ✅ |
| 3 | Development complete (v57.39) | Dev | ✅ |
| 4 | Full batch run (6,934 quikridr rows) | Dev | ✅ |
| 5 | Validation PASS | Validation | ✅ |
| 6 | Suppression audit CSV (68 rows) | Dev | ✅ |
| 7 | Validator baselines updated (quikridr 6934) | Regression | ✅ |
| 8 | Protected issues verified | Regression | ✅ |
| 9 | Release notes drafted | Regression | ✅ |
| 10 | Client UAT package finalized | Regression | ✅ |

---

## Client UAT (pending)

| # | Item | Owner | Status |
|---|------|-------|--------|
| 11 | UAT on trace policy `010448806C` | Client | ☐ |
| 12 | UAT on 10-policy random sample | Client | ☐ |
| 13 | Confirm duplicate face removed (46 policies) | Client | ☐ |
| 14 | Confirm mode premium unchanged | Client | ☐ |
| 15 | Client sign-off | Eric | ☐ |

---

## Production deployment (after UAT)

| # | Item | Owner | Status |
|---|------|-------|--------|
| 16 | Git commit v57.39 (if authorized) | DevOps | ☐ |
| 17 | Production batch conversion | Ops | ☐ |
| 18 | QLAdmin load verification | Ops | ☐ |
| 19 | Issue #27 closure | PM | ☐ |
| 20 | Update master tracking sheet | PM | ☐ |

---

## Rollback plan

| Step | Action |
|------|--------|
| 1 | Revert to v57.38 `app.py` / `QLA_Migration/app.py` |
| 2 | Restore quikridr baseline to 7,002 in validators |
| 3 | Re-run full batch |

**Rollback risk:** Low — isolated SL filter.

---

## Release artifacts location

`Issue_Log_Items/Issue_27/` — see `Issue_27_Release_Package.md`

---

**Checklist status:** Pre-release ✅ complete — awaiting Client UAT
