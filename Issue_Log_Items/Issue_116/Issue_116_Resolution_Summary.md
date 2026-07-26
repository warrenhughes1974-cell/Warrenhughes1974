# Issue #116 — Resolution Summary (Stage 8, Closure)

**Closed:** 2026-07-26  
**Engine:** v58.37  
**Status:** Closed — G7 gate satisfied  

---

Resolution: QuikDvdp Interest Paid To now uses the last dividend-interest credit date from accounting (PACTG 0641), looked up under both policy-number formats so QLAdmin stops accruing backwards into a negative figure.

---

## The problem, in plain terms

QLAdmin shows Accrued Interest by counting forward from Interest Paid To. We had been loading the premium paid-to date instead of the date interest was last credited. On policies where those dates differ by months, accrued interest went negative (example: −$126.93 against a $9,220.33 balance).

## Root cause

Interest dates were already in the accounting extract and the converter was reading them, but it cached them under the crosswalk `New_Value` key and later looked them up by emitted `MPOLICY`. That lookup never hit, so every policy fell through to the premium date.

## Fix (v58.37)

Dual-key cache for PACTG 0641 interest dates (crosswalk New_Value **and** emitted MPOLICY) plus hit logging. No change to dividend balances or row population.

## Validation / G7 (full Output 2026-07-26)

| Check | Result |
|---|---|
| `validate_issue116.py` on `Output/quikdvdp.csv` | **PASS** |
| Rows | 5,083 unchanged |
| Balance-carrying policies with future MINTDATE | 15 → **0** |
| MDEPOSIT drift | 0 |
| Accountability | **IN_DATA** |

## Rollback

Revert `app.py` / `QLA_Migration/app.py` v58.37 MINTDATE cache change (or restore prior quikdvdp). Related commit on branch `issue-34-pr7-quikisrr`.
