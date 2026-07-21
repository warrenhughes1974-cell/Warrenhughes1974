# Reinsurance Phase 1 — Open Business Questions

**Raised:** 2026-07-19  
**Source:** Comparison of Phase 1 emit (`plan_analysis/phase_r9_quikrein_rmst/`) vs `docs/Reinsure.pdf` (LifePRO Reinsurance Book) and sample QLAdmin reinsurance DBFs in `docs/` (`QUIKREIN.DBF`, `QUIKRMST.DBF`, `QUIKRBLL.DBF`, `QUIKRBLH.DBF`, `QUIKRPLN.DBF`, `QuikRval.dbf`)  
**Status:** WAITING ON CLIENT — email prepared for Eric 2026-07-19. No code changes; stored-value authority rule respected (values below are exactly as stored in LifePRO `PREINTRT`/`PREIN`).

## Issues log mapping

| Issue | Status | Short name | Policy (QLAdmin / LifePRO) |
|------:|--------|------------|----------------------------|
| 90 | Active | Reinsurance amount larger than the coverage itself | 011216797C / 9011216797 |
| 91 | Active | Three partners together cover 3x the policy amount | 011216680C / 9011216680 |
| 92 | Active | $20,000 of coverage unaccounted for between kept and ceded | 011274946C / 9011274946 |

## Client outreach log

| Date | Action | Contact | Result |
|------|--------|---------|--------|
| 2026-07-19 | Plain-language email prepared (Issues 90–92) | Eric | Waiting on response |

---

## Background — CSO/CSI treaty structure

The converted block uses two 3-way 100% cession families:

| Family | Treaties | Split | Emit rows |
|--------|----------|-------|----------:|
| L14 | L14 / L14CSI / L14CSO | 33.33 / 33.33 / 33.34 | 232 / 232 / 232 (symmetric) |
| L15 | L15 / L15CSI / L15CSO | 33.33 / 33.33 / 33.34 | 12 / 12 / **13** (asymmetric) |

`MRETAINED = 0.00` on all 733 rows (source: `PREIN.RETENTION_AMOUNT`), consistent with a 100% ceded block — except where noted below.

---

## Issue 90 (BQ-1) — Policy 011216797C: exists only on L15CSO, ceded > initial amount

| Field | Value |
|-------|-------|
| LifePRO policy | 9011216797 |
| QLAdmin policy / phase | 011216797C / 1 |
| Plan / status / UW class | 1L16GD / 45 / SM |
| Treaty rows | **L15CSO only** — no L15 or L15CSI rows in canonical PREINTRT |
| MINITAMT | 1,324.80 |
| MCEDED | 5,000.00 (**377% of initial amount**) |

**Questions:** Is the missing L15/L15CSI allocation intentional (e.g., other treaties terminated) or a LifePRO data gap? Is MCEDED 5,000.00 correct against a 1,324.80 initial amount, or is MINITAMT understated at source?

## Issue 91 (BQ-2) — Policy 011216680C: total ceded is ~3.3x the initial amount

| Treaty | MCEDED |
|--------|-------:|
| L15 | 11,966.25 |
| L15CSI | 1,516.65 |
| L15CSO | 1,517.10 |
| **Total** | **15,000.00** |

MINITAMT = 4,550.40 on all three rows (plan 1L16GD, status 53, UW class SM). The L15 base row alone is 263% of the initial amount, and the family split is not 33/33/34.

**Questions:** Which is authoritative — the 4,550.40 initial amount or the 15,000.00 total cession? Should the L15 row be 1,516.65-scale like its CSI/CSO siblings (possible source keying error on `PREINTRT.AMOUNT_REINSURED`)?

## Issue 92 (BQ-3) — Policy 011274946C: 60% ceded but retained stored as zero

| Treaty | MCEDED |
|--------|-------:|
| L14 | 9,999.00 |
| L14CSI | 9,999.00 |
| L14CSO | 10,002.00 |
| **Total** | **30,000.00** |

MINITAMT = 50,000.00 (plan 1L14SC, status 22, UW class NS). Total cession = 60% of face; the remaining 20,000.00 is unaccounted for, yet `PREIN.RETENTION_AMOUNT` = 0.00, so `MRETAINED` emits as 0.00.

**Questions:** Is the retained amount actually 20,000.00 (LifePRO `RETENTION_AMOUNT` not maintained), or was the cession reduced without updating the initial amount? Should QLAdmin carry MRETAINED = 20,000.00 for this policy?

---

## Impact if loaded as-is

- All values load exactly as stored in LifePRO (per the Phase 1 stored-value authority rule), so the load itself will not fail.
- QLAdmin reinsurance reporting/billing for these 3 policies (7 QuikRmst rows of 733) would reflect ceded amounts exceeding face (BQ-1, BQ-2) and an understated retained amount (BQ-3).
- The other 730 rows reconcile cleanly (ceded sum $4,101,000.00 source = emit; see `Issue_Reinsurance_Phase1_Implementation_Notes.md`).

## Disposition options (pending client answer)

1. Load as-is (stored-value authority) and correct in QLAdmin post-load.
2. Client corrects LifePRO source (`PREIN`/`PREINTRT`) and we re-extract.
3. Client provides documented overrides; add to a business-inputs crosswalk with full trace (would require a new Development-stage change — not authorized yet).

**Do not advance these policies to production load until answered.**
