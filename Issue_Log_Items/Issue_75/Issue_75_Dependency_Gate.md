# Issue #75 — Dependency Gate (REOPEN)

**Issue:** #75 — Bank Acct / `MBANKNO` via PPCOM  
**Framework stage:** Dependency Gate (G2)  
**Date:** 2026-07-25  
**Model:** Cursor Grok 4.5 (locked)  
**Verdict:** **PASS**

---

## Dependencies checked

| Dependency | Status | Notes |
|------------|--------|-------|
| #21H ABA recovery pattern | PASS | Pattern exists; lookup file is stale vs 20260630 PPCOM / PPPAC blanks |
| #45 PPPAC account fallback | PASS | Closed; still supplies accounts for all 910 blanks |
| #75 v57.92 QLA-safe gate | PASS | Must remain; reopen adds fill, not loosen format |
| PPCOM extract present | PASS | `Source/PPCOM_PACAccountInformation_Extract_20260630.csv` |
| PPACH / PPPAC present | PASS | 20260630 extracts in Source |
| Issue #2 policy keys | PASS | Join uses source policy + `C`; PPCOM joins by account only |
| Claims / other tables | N/A | Out of scope |

---

## Blockers

None. Ambiguous ABA (205) and leading-zero account rule are **Risk/client decisions**, not hard dependency blocks.

---

## Gate criteria

- [x] Upstream bank issues understood (#21H/#45/#75 v1)
- [x] Source files available for proposed mapping
- [x] No conflicting open Development that owns `MBANKNO`
- [x] Safe to proceed to Risk

**Result: PASS → Risk Agent**
