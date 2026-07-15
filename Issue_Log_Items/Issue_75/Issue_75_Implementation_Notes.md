# Issue #75 — Implementation Notes

**Issue:** Bank Acct / `MBANKNO` QLA validation  
**Framework stage:** Development complete (G4)  
**Engine version:** v57.92  
**Date:** 2026-07-15  
**Model:** Composer 2.5 (locked Development stage)

---

## Summary

Hardened `quikmstr.MBANKNO` emit so QLAdmin Bank Acct passes routing validation: **9-digit ABA only**, **digits-only account**, **single `/`**. Truncated routing, hyphenated accounts, and literal `//` values are no longer emitted. Bank-draft policies without recoverable 9-digit ABA stay blank with refined exception reasons (`ABA_NOT_9`, `ACCT_INVALID`).

---

## Files changed

| File | Change |
|------|--------|
| `app.py` | v57.92 — Issue #75 MBANKNO helpers + cache/gate |
| `QLA_Migration/app.py` | Same (synced) |
| `QLA_Migration/_validate_issue75_mbankno.py` | Validator wrapper |
| `Issue_Log_Items/Issue_75/scripts/validate_issue75_mbankno.py` | Validator + helper unit tests |
| `Issue_Log_Items/Issue_75/Issue_75_Implementation_Notes.md` | This file |

**Not changed:** rulebooks, crosswalk, `MBILLFRM`, #25/#26 paths.

---

## Code changes (surgical)

### 1. New helpers (`_issue75_*`)

- `_issue75_usable_acct_digits` — digits-only account (≥4), via #45 usability rules  
- `_issue75_usable_aba_digits` — lookup then raw; **only len==9**  
- `_issue75_build_mbankno` — `9digitABA/accountDigits`  
- `_issue75_mbankno_is_ql_safe` — QLA format gate  

### 2. `_issue45_lookup_aba_for_account`

- Returns ABA only when **exactly 9 digits** (was `>=5`).

### 3. PPACH banking cache

- Normalize account to digits; recover ABA via lookup / 9-digit raw only.  
- Do **not** fall back to truncated PPACH ABA.  
- Store meta for exception detail when account exists but ABA not 9-digit.

### 4. PPPAC fallback (#45)

- RNA ABA aid: only **9-digit** values.  
- Emit digits-only account; require 9-digit ABA from lookup or RNA.

### 5. Bank-draft gate (`_apply_issue45_bank_draft_gate`)

- Pass only when `_issue75_mbankno_is_ql_safe(MBANKNO)`.  
- New reasons: `ABA_NOT_9`, `ACCT_INVALID`.

---

## Before / after trace (expected post-batch)

| Policy | Before | After (expected) |
|--------|--------|------------------|
| **010161748C** | `09130385/000000200-058-1` | blank + `ABA_NOT_9` exception |
| 010157076C | `10491013/212919` (8-digit ABA) | blank + exception |
| 010348734C | `08151811/208787` (8-digit ABA) | blank + exception |
| 010464590C | `09140068//7562700387` | blank + `ACCT_INVALID` |
| **010713704C** | `104000016/47374579` | **unchanged** (regression guard) |
| Policies with punct + valid 9-digit ABA | e.g. `…/…-…` | `ABA/digits` cleanup |

---

## Validation

```text
python Issue_Log_Items/Issue_75/scripts/validate_issue75_mbankno.py
```

- **Helper unit tests:** PASS (v57.92 import)  
- **Output format check:** requires full batch re-run — current Output is pre-v57.92  

After batch PASS: copy `quikmstr.csv` → `Output/Test_Validation/`.

---

## Next stage

**Validation Agent** (Cursor Grok 4.5): full batch, output compare, regression on non-candidates, publish Test_Validation.
