# Issue #21 Open Items — Implementation Notes (v57.63)

**Date:** 2026-07-09  
**Engine:** v57.63  
**Decisions:** `Issue_21_Open_Items_Official_Decisions.md`

## What changed in code

### 21E — UL fund balance → `quikridr.MCV0`
- New module: `qla_core/issue21_open_item_decisions.py`
- Before FV rows are filtered from PPBEN, build cache: LifePRO `POLICY_NUMBER` → `FV_BALANCE2`
- On phase-1 quikridr rows only, set `MCV0` from that cache (keyed by **source** `POLICY_NUMBER`, not crosswalked `MPOLICY`)
- Traditional policies: `MCV0/1/2` remain blank (QuikCvs compute path)

**Validated offline:** 1,830 UL policies with non-zero `FV_BALANCE2`  
**Golden samples:** 9010713704 → 45551.94; 9010818663 → 12475.03

### 21G — Staged premium/basis report
- Full batch writes `QLA_Migration/Reports/issue21g_premium_basis_totals.csv`
- Traditional: PPBENTYP BA/BF + PU premiums/basis  
- ISWL/UL: PPBEN `FV_GUAR_DEPOSITS` / `FV_BASIS2`
- **Not** written to Output (load package stays table CSVs only)

**Validated offline:** 4,886 policy totals staged

### 21D / 21F / 21I
- Documentation + tracking only (no new logic)
- Rulebook comments updated for `MRELATION` and `MCV0`

## Files
| File | Change |
|---|---|
| `qla_core/issue21_open_item_decisions.py` | New helpers |
| `app.py` / `QLA_Migration/app.py` | Wire 21E + 21G; version v57.63 |
| `Configs/Sync_Rulebook_quikbenf.csv` | Comment: MRELATION=1000 intentional |
| `Configs/Sync_Rulebook_quikridr.csv` | Comment: MCV0 UL-only |

## Regression risks
- UL `MCV0` only when FV cache hit + phase 1 — traditional unchanged
- 21G report in `Reports/` only — no Output pollution
- Schema field order unchanged

## Next for full dataset
1. Re-run full batch conversion (picks up MCV0 + 21G report)
2. Re-run rate tables (#40/#41) for traditional CV compute path
3. Spot-check UL policies 010713704C / 010818663C `MCV0` after batch
