# Issue #88 — Scope Decisions

**Issue:** #88 — ISWL QuikIssc / QuikUint empty in batch CSV package  
**Generated:** 2026-07-21  
**Status:** Locked for Pre-Risk Auto-Chain  

---

## In scope

1. **D1** — Add QuikIssc + QuikUint CSV writes to `qla_core/rate_emit.py` batch CSV path.  
2. **D2** — Repoint `psegt_csv`, `pdint_extract`, `pdinttbl_extract` to 20260630 Source extracts.  
3. Re-emit and validate QuikIssc (8 rows) + QuikUint (non-empty for ISWL fleet).  
4. Publish corrected tables to `Output/Test_Validation/rates/` after Validation PASS.  

## Out of scope

| Item | Where tracked |
|------|----------------|
| COI / GCOI fleet expansion | Issue_ISWL OBQ-7 / OBQ-8 |
| COI per-$1,000 basis | Issue_ISWL OBQ-6 |
| Guideline premiums / quikspec | Issue_ISWL OBQ-9 |
| Loan credited rate decode | Issue_ISWL OBQ-10 |
| Female QuikIssc companions | Issue_ISWL OBQ-3 (await Sujitha) |
| D3 COI reconcile vs 7/13 PAAGERAT | Follow-up after #88 close (optional new issue) |
| Changing SL schedule values or allowlists | Issue #33 closed design |

## Non-goals

- No rate loader algorithm changes  
- No policy conversion changes  
- No Sync_Rulebook changes  
