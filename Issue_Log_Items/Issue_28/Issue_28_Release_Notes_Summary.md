# Issue #28 — Release Notes Summary

**Version:** v57.35  
**Date:** 2026-06-27  
**Issue:** #28 — CLOSED

---

## Headline

**Product catalog PLAN codes now match the client-approved Policy Form Crosswalk (5/22/2026).**

---

## What changed

- **33** quikplan PLAN values corrected from LifePRO passthrough to authoritative QLAdmin codes
- **DISCHO25** added to catalog (`9DIS25`)
- **quikridr MPLAN** aligns via P3E (default ON)
- **141/141** mappings validated; client UAT approved

---

## Client examples

| Source | Now |
|--------|-----|
| 10827 MN5K | 1CSIMN |
| 0823 960CH | 960CWP |
| 0824 P DIS | 94PDIS |

---

## Upgrade requirement

**Full batch re-run required** after deploying v57.35. v57.34 quikplan PLAN values are obsolete.

---

## Rollback

Revert to v57.34 code + set `QLA_CLOSED_MPLAN_AUTHORITY=0`. See `Issue_28_Rollback_Checklist.md`.

---

## Full release notes

`Release_Notes/v57.35_Release_Notes.md`

---

## Protected issues preserved

#25 MPOLICY, #26 MPREM, #21M QUIKMEMO, #21M-FU DBF — all PASS at release cut.
