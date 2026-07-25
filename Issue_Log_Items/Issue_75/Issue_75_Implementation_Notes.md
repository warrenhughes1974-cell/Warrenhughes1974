# Issue #75 — Implementation Notes (REOPEN — PPCOM recovery)

**Issue:** Bank Acct / `MBANKNO` via PPCOM  
**Framework stage:** Development complete (G4)  
**Engine version:** v58.35  
**Date:** 2026-07-25  
**Model:** Cursor Grok 4.5 (locked)

---

## Summary

Rebuilt `aba_routing_lookup.csv` from June PPCOM for PPACH+PPPAC accounts (unique + latest-ambiguous, checksum-valid 9-digit ABA). Converter still enforces QLA-safe `MBANKNO` (`9digitABA/accountDigits`). Account leading zeros preserved from source; ABA leading zero kept when it is part of the validated 9-digit routing.

---

## Files changed

| File | Change |
|------|--------|
| `app.py` / `QLA_Migration/app.py` | v58.35 — checksum ABA helpers; PPCOM lookup comments; RNA uses checksum |
| `QLA_Migration/Source/aba_routing_lookup.csv` | Rebuilt from PPCOM 20260630 (4,562 keys) |
| `Issue_Log_Items/Issue_75/scripts/rebuild_aba_routing_lookup_from_ppcom.py` | Rebuild script |
| `Issue_Log_Items/Issue_75/evidence/aba_routing_lookup.csv` | Evidence copy |
| `Issue_Log_Items/Issue_75/evidence/issue75_ppcom_ambiguous_accounts.csv` | 361 ambiguous (latest chosen) |
| `Issue_Log_Items/Issue_75/scripts/validate_issue75_mbankno.py` | Trace keys + checksum expectations |

---

## Leading-zero rule (locked)

| Half | Rule |
|------|------|
| ABA | Keep leading `0` when present in checksum-valid 9-digit PPCOM/lookup value |
| Account | Keep source digits after punctuation strip; do not strip or invent zeros |

---

## Expected impact (pre-batch)

| Metric | Count |
|--------|------:|
| Blank bank-draft today | 910 |
| Expected fills via new lookup | ~859 |
| Still unresolved (no PPCOM) | ~51 |
| Ambiguous resolved via latest date | included |

---

## Validation

```text
python Issue_Log_Items/Issue_75/scripts/validate_issue75_mbankno.py
```

Requires full (or quikmstr) batch with v58.35 + rebuilt lookup. On PASS: copy `quikmstr.csv` → `Output/Test_Validation/`.
