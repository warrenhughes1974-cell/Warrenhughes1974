# Issue #85 — Implementation Notes

**Issue:** #85 — Duplicate claim headers (same policy + phase)  
**Framework stage:** Development (G5)  
**Status:** Implemented — **v58.03** — validator PASS  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (**one-time Development override** — user: “Approve but lets stay with Grok 4.5”)

---

## Summary

Hybrid structure fix (approved D1–D5):

| Action | Count |
|--------|------:|
| Headers before → after | 5,624 → **5,447** |
| True-duplicate merges dropped | **177** |
| Distinct claims re-phased | **3,034** |
| Payees re-phased | **3,115** |
| Payee match exceptions (flagged, not dropped) | **15** |
| Duplicate policy+phase after | **0** |
| `quikclmp` row count | **6,151** (unchanged) |

CLAIMSTAT rules (#79) and payee invent (#78) untouched. Remaining money imbalance is **#84 Track B**.

---

## Code changes

| File | Change |
|------|--------|
| `qla_core/issue85_claim_header_structure.py` | **New** — merge / re-phase / payee re-attach |
| `QLA_Migration/app.py` | Post-emit hook after #79; **v58.03** |
| `app.py` | Sync copy — **v58.03** |
| `QLA_Migration/_rebatch_issue85_claim_structure.py` | Headless rebatch |
| `QLA_Migration/_validate_issue85_claim_structure.py` | Risk checklist validator |

---

## Output artifacts

| Artifact | Location |
|----------|----------|
| Updated headers | `QLA_Migration/Output/quikclms.csv` |
| Updated payee phases | `QLA_Migration/Output/quikclmp.csv` |
| UAT partial reload | `Output/Test_Validation/quikclms.csv` + `quikclmp.csv` |
| Merge audit | `QLA_Migration/Reports/issue85_merge_audit.csv` |
| Rephase/payee audit | `QLA_Migration/Reports/issue85_rephase_payee_audit.csv` |
| Pre-change backups | `Output/Archive/quikclms_pre_issue85.csv`, `quikclmp_pre_issue85.csv` |

---

## Validation results

```
PASS
  headers: 5447
  payees: 6151
  merge drops: 177
  dup pol+phase: 0
  CLAIMSTAT: {99: 4210, 2: 1237}   # post-merge survivors; no Pending/Settled
```

Traces: `010914301C` → 1 header MPAID 50039.96; `011156098C` → 45000; `011054606C` unique phases; `010150740C` unchanged.

---

## UAT

Reload **`Output/Test_Validation/quikclms.csv`** and **`quikclmp.csv`**. Spot-check merge and rephase traces above; review 15 `PAYEE_EXCEPTION` rows in the rephase/payee audit.

---

## Next framework stage

**Validation Agent** (Cursor Grok 4.5) — read-only regression.  
Then #84 Track B money balancing may proceed; #84 Track A remains available.
