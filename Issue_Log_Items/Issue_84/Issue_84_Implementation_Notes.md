# Issue #84 — Implementation Notes (Track A)

**Issue:** #84 — `quikclms` money-field decomposition  
**Track:** A only (header MPAID/PDDATE backfill)  
**Version:** v58.12  
**Date:** 2026-07-19  
**Status:** Implemented — Awaiting Validation

## What changed

When a `quikclms` header has **MPAID ≈ 0** and matching `quikclmp` payee rows exist on the same **(MPOLICY, MPHASE)** claim key:

- Set **MPAID** = sum of payee `MAMOUNT` (2-decimal format)
- Set **PDDATE** from latest payee `MPMTDATE` / `MCHKDATE` when header PDDATE is blank

## What did not change

- **CLAIMSTAT** (#79) — untouched
- **quikclmp** rows (#78) — no invent/delete; payee amounts unchanged
- Non-zero header MPAID — preserved (including intentional face/net vs payee splits)
- Track B components (DIVIDENDS, PREMIUM, etc.) — deferred

## Code

| File | Role |
|------|------|
| `qla_core/issue84_track_a_header_backfill.py` | Core backfill + audit writer |
| `QLA_Migration/app.py` / root `app.py` | Post-emit hook after #85 in claims UAT finale |
| `tests/test_issue84_track_a.py` | Unit tests |

## Pipeline order (claims UAT emit)

1. UAT emit → Items 18–19 overlays  
2. Issue #78 payee recovery  
3. Issue #79 CLAIMSTAT remap  
4. Issue #85 header structure  
5. **Issue #84 Track A header backfill** ← new

## Audit

`QLA_Migration/Reports/issue84_money_field_audit.csv` — one row per backfilled header (not in Output/).

## Validation targets

- [ ] `010391359C`: MPAID=1260.06; PDDATE=20211119; CLAIMSTAT still 2
- [ ] Claim-key HEADER_ZERO count → 0 (or exception-audited)
- [ ] `quikclmp` row count unchanged (6,151 baseline)
- [ ] `010150740C` unchanged (non-zero MPAID preserved)

## Track B (not in this release)

PACTG component decomposition + policy-level MPAID↔payee recon (898 policies) — separate Development approval.
