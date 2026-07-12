# Issue #45 — Implementation Notes

**Issue:** PPPAC `E_ACCOUNT_NUMBER` fallback for bank-draft `MBANKNO`  
**Framework stage:** Development complete (G4)  
**Engine version:** v57.77  
**Date:** 2026-07-12  
**Model:** Composer 2.5 (locked Development stage)

---

## Summary

Implemented Eric’s request to incorporate `PPPAC_PACDetail_Extract_20260630` as a **fallback account source** when PPACH has no usable account. PPACH remains primary for policies already banked via history. `MBANKNO` is emitted only when **both** account and ABA resolve (lookup → RNA).

---

## Files changed

| File | Change |
|------|--------|
| `app.py` | v57.77 — PPPAC fallback banking cache + Issue #45 gate |
| `QLA_Migration/app.py` | Same (synced) |
| `QLA_Migration/_validate_issue45_pppac_fallback.py` | New validation script |
| `Issue_Log_Items/Issue_45/Issue_45_Implementation_Notes.md` | This file |

**Not changed:** rulebooks, crosswalk, MBILLFRM mapping, #25/#26 paths.

---

## Code changes (surgical)

### 1. Helpers (`_issue45_usable_bank_account`, `_issue45_lookup_aba_for_account`)

- PPPAC account usability: ≥4 digits, not masked/zero/placeholder.
- ABA lookup tries raw digits, strip-leading-zeros, and zfill(17) keys.

### 2. PPPAC banking cache (after PPACH load)

- Load RNA `ELEC_ABA_NUMBER` / `PAPER_ABA_NUM` per policy.
- Load PPPAC via `find_extract('pppac')`.
- For policies **not** already in `_ppach_bank_map`:
  - Use PPPAC `E_ACCOUNT_NUMBER`.
  - Resolve ABA: lookup first, then RNA (single distinct ABA only).
  - On success → `_ppach_bank_map` + `_ppach_acct_meta` with `bank_source=PPPAC`.
  - On account but no ABA → `_pppac_acct_only_meta` (exception `MISSING_ROUTING`).

### 3. Issue #45 gate

- Skip exception when meta has **both** account and ABA.
- Refine reasons: `MISSING_BANK_ACCOUNT` vs `MISSING_ROUTING`.
- Exception CSV adds optional columns: `PPPAC_ACCOUNT`, `ABA_SOURCE`, `BANK_SOURCE`.

---

## Before / after trace (masked)

| MPOLICY | Before | After (expected) |
|---------|--------|------------------|
| 010157076C | blank + exception | `ABA/ACCOUNT` via PPPAC+RNA |
| 010161748C | blank + exception | `ABA/ACCOUNT` via PPPAC+RNA |
| 010348734C | blank + exception | `ABA/ACCOUNT` via PPPAC+RNA |
| PPACH-banked control | existing `MBANKNO` | unchanged |
| 9015000043 (neither source) | blank + exception | still exception |

---

## Expected fleet impact

| Metric | Before | After (est.) |
|--------|-------:|-------------:|
| Exception rows | 763 | ~15 |
| New `MBANKNO` fills | 0 | ~748 |
| PPACH-primary unchanged | 1,369 | 1,369 |

---

## Validation

```text
python QLA_Migration/_validate_issue45_pppac_fallback.py
```

Evidence: `Issue_Log_Items/Issue_45/evidence/`

---

## Next stage

**Validation Agent** (Cursor Grok 4.5): run full batch, compare `quikmstr.MBANKNO`, exception CSV, regression on non-candidates. On PASS, copy `quikmstr.csv` to `Output/Test_Validation/`.

---

## Regression risks

| Risk | Mitigation |
|------|------------|
| Overwrite PPACH-banked policies | Skip if `pol in _ppach_bank_map` |
| Emit account without ABA | Require both before map entry |
| RNA multi-ABA guess | Skip → `MISSING_ROUTING` |
| #21H PPACH path | PPACH block unchanged; fallback runs after |
