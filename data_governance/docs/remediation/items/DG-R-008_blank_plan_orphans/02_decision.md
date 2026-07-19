# DG-R-008 — Business Decision

**Status:** DECIDED  
**Date:** 2026-07-18  
**Approved by:** User (chat)

## Decision

**Option A — Delete blank shells on CSO only.**

1. Backup CSO tables before write.
2. Delete the 1 QuikPlan row with blank PLAN.
3. Delete the 1 blank-PLAN row in each of: QuikPlGp, QuikPlDb, QuikPlCv, QuikPlTv, QuikPlDv, QuikPlGd, QuikPlUw, QuikPlBd.
4. **Do not** touch WPA orphan rates.
5. Conversion emit already has 0 blank PLAN — document in CONVERSION_SYSTEM_DEFAULTS; no APP_VERSION unless code changes.

## Out of scope

- WPA orphan QuikTvs / QuikGps / QuikPlGp plans  
- Softening governance rules 001/002/003  
