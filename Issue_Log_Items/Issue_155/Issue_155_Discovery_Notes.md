# Issue #155 — Account value discovery

**Date:** 2026-09-23  
**Stage:** Discovery only. No policy data or calculation logic was changed.

## Conclusion

The contractual $1,000 value per unit loaded correctly. The LifePRO account value did not.

On policy 9010902968, LifePRO holds a stored fund balance of **$15,219.16** as of 2026-06-06, and the 2026-06-30 valuation extract carries that same amount. QLAdmin conversion writes **$0.00** to the account field. The QLAdmin valuation file generated 2026-09-02 then contains a calculated account of **$12,577.88**. That $2,641.28 gap is the first verified dollar difference.

The exported $2,522.74 is not LifePRO’s fund divided by units. It comes from the QLAdmin calculated account. The reported $35.70 difference is rounding: the exact QLAdmin extension is $12,613.70, which is **$35.82** above its own $12,577.88 account. The QLAdmin valuation program that creates those two figures is not in this repository, so the $35.82 itself is verified arithmetic, not a reconstructed charge.

This is not limited to the workbook’s 152 policies. On the paired 6/30 files, **0 of 1,121** matched ISWL policies have the same account value within one cent. **170** also had the valuation-file value per unit rewritten above $1,000. The saved workbook row list was not retained, so the original 152 cannot be reproduced exactly; the example and its $2,522.74 are in the 170.

## LifePRO

The account is a stored fund-benefit balance, not the coverage value per unit.

| Record | What it holds | 9010902968 |
|---|---|---:|
| PPBEN benefit 1, type BF | Coverage | 5 units at $1,000; modal premium $23.16 |
| PPBEN benefit 99, type UV | Specified amount | $5,000 |
| PPBEN benefit 2, type FV | Stored fund | Basis $10,339.57 + income $4,879.59 = balance **$15,219.16** |
| PFNDR fund history | Same balance, component rollforward | **$15,219.16** at valuation date 2026-06-06 |
| VALXLIFE base row | 2026-06-30 valuation report | Fund $15,219.16; surrender $15,219.16; value per unit $1,000 |

The FV identity on this policy is exact:

```text
FV_BALANCE2 = FV_BASIS2 + FV_INCOME2
15,219.16 = 10,339.57 + 4,879.59
```

The fund-history identity is also exact, using a more detailed component set:

```text
FUND_BALANCE = GROSS_DEPOSITS + GROSS_EARNINGS - GROSS_DEDUCTIONS - GROSS_DEPOS_LOADS
15,219.16 = 10,339.57 + 9,544.75 - 3,473.56 - 1,191.60
```

Deposit loads of $1,191.60 and guaranteed rate 4.50% are stored on the FV benefit. There is no surrender charge: fund value equals surrender value. The 2026-08-31 extract shows the stored balance later moved to $15,382.23 at 2026-08-06, so LifePRO does update it after the June processing date. Transaction-level history from 2002/2003 forward is in `PFNDRDET`; see the 2026-09-24 update below.

The FV benefit on this policy is plan/fund code `659 CEN II`. The coverage benefit is `659 CEN SR`. Across the 6/30 extract, 641 policies have coverage `659 CEN SR` with fund code `659 CEN II`. That is a product-configuration fact. It is not yet proof that the dollar gap comes from using the wrong plan rates.

## QLAdmin

| Field | Source | 9010902968 |
|---|---|---:|
| `quikridr.MUNIT` / `MVPU` | PPBEN coverage units and value per unit | 5 / 1,000.00 |
| `QuikIswl.MACCTBAL` | Issue 124 month-0 seed; explicitly zero | 0.00 |
| `QuikIswl.MDB` | Units × 1,000 | 5,000.00 |
| `QuikValf.MACCTBAL` | Written by QLAdmin valuation, not conversion | 12,577.88 on the 2026-09-02 file; 0.00 on the 2026-09-22 file |
| `QuikValf.MVPU` | Written by QLAdmin valuation | 2,522.74 on 2026-09-02; 1,000.00 on 2026-09-22 |

`qla_core/quikiswl_loader.py` creates one month-0 seed and sets `MACCTBAL` to 0.00. Issue 124 expressly rejected rebuilding fund history from LifePRO. No conversion code reads `FV_BALANCE2` or `PFNDR.FUND_BALANCE`.

The current Q: `QuikIswl.dbf` still has one zero-balance seed for this policy. It was rewritten 2026-09-22 at 6:21 PM, before that evening’s valuation. The 2026-09-02 valuation output therefore cannot be replayed from the fund table now on disk.

## Worked reconciliation — 9010902968

Common reporting date: **2026-06-30**. LifePRO’s stored fund date is **2026-06-06**; the 6/30 extract did not change it.

| Step | LifePRO | QLAdmin | Difference |
|---|---:|---:|---:|
| Contract units and value per unit | 5 × $1,000 | Loaded 5 × $1,000 | $0.00 |
| Stored/opening account | $15,219.16 | Loaded $0.00 | Account was not converted |
| 2026-06-30 reported account | $15,219.16 | $12,577.88 in the 2026-09-02 valuation file | **-$2,641.28** |
| Value-per-unit export | $1,000.00 | $2,522.74 | Export measure differs |
| Exported extension | Not applicable | $2,522.74 × 5 = $12,613.70 | $35.82 above the QLAdmin account |

`$12,578 × 5` does not explain $2,522.74. The $12,578 in the issue note is the QLAdmin account rounded from $12,577.88. Using that rounded figure produces the stated $35.70. The exact figures produce $35.82. Neither figure equals LifePRO’s $15,219.16.

The 2026-09-22 valuation, run while the zero seed was present, exported account $0.00 and value per unit $1,000.00. That confirms the rewritten value per unit depends on a calculated account. It does not identify the interest, premium, or charge steps inside the 2026-09-02 calculation.

## Population

Comparison date 2026-06-30. Account tolerance is one cent, matching the valuation comparison. Evidence:

`Issue_Log_Items/Issue_155/evidence/issue155_account_comparison_20260630.csv`

Repeatable read-only check:

```text
python Issue_Log_Items/Issue_155/scripts/compare_issue155_account_values.py
```

| Result | Count |
|---|---:|
| Matched ISWL base rows | 1,121 |
| Account values equal within $0.01 | 0 |
| Contractual value per unit loaded as $1,000 | Included in the load check |
| 2026-09-02 valuation value per unit rewritten above $1,000 | 170 |
| Those 170 accounts equal to LifePRO | 0 |

## Cause

The verified cause is conversion mapping plus later valuation processing:

1. Conversion stores the coverage unit value and intentionally stores a zero account seed.
2. QLAdmin valuation calculates an account that does not match the stored LifePRO fund.
3. On 170 policies in the 2026-09-02 file, valuation also writes a fund-based value per unit into the export. That export is not LifePRO fund ÷ units.

## Evidence still required

- ~~`PFNDRDET` transaction history~~ — found 2026-09-24 (below).
- The QLAdmin valuation configuration or program logic that calculates `MACCTBAL` and rewrites `MVPU`.
- The `QuikIswl` table as it existed when the 2026-09-02 valuation was generated.

No conversion change should be made until those items establish whether QLAdmin should start from the LifePRO fund balance or continue calculating its own account.

## 2026-09-24 update — LifePRO fund history found

`PFNDRDET_FundHistoryDET_Extract_20260831.csv` was in the 8/31 LifePRO zip all along (never unpacked because of size). ISWL subset extracted to `QLA_Migration/Source/PFNDRDET_FundHistoryDET_ISWL_Extract_20260831.csv` (2,694,998 rows, all 2,348 fund policies).

What it holds, per monthiversary: interest credited (rate + amount), each premium deposit (gross, load, deposit interest), deductions (`PF` policy fee, `MT` mortality), withdrawals, loans. History starts 2002/2003 with one `CV` record per policy that carries gross deposits to date, not the balance.

**It ties.** Opening balance at the `CV` date = PFNDR lifetime totals minus itemized detail (earnings, deductions, loads, withdrawals). Rolling forward:

| Policy | Opening 3/31/2003 | 12/31/2017 | Rebuilt 8/19/2026 | LifePRO 8/19/2026 |
|---|---:|---:|---:|---:|
| 9010713704 | 11,925.92 | 29,317.76 | 45,906.83 | 45,906.83 |
| 9010713705 | 7,292.40 | 16,983.46 | 26,479.01 | 26,479.01 |
| 9010713707 | 2,647.86 | 6,097.21 | 8,193.53 | 8,193.53 |

Book-wide (2,268 QL ISWL policies, all fund plan `659 CEN II`): 2,139 tie at both the 6/30 and 8/31 cuts; 106 differ (median ~$15, 102 active); 23 have no PFNDR summary. 109 have no interest records after 2002/2003.

**Credited rate.** Every interest record 2003–2026 is 4.50% current and 4.50% guaranteed. 2002 shows 299 records at 9.00% then 4.50% — policies stepped down at their 2002 anniversary, consistent with PDINTTBL rule 3 timing, not a rate locked at issue.

**Negative balances.** 248 QL ISWL policies have a negative LifePRO fund at 8/31 (164 active; total −$3.92M), driven by `MT` mortality deductions. Base plans: 658 CEN I 175, 659 CEN SR 55, 658 CEN SD 12, 659 CEN II 6. Largest: 9010737619 −$754,705.97; 9010779727 −$180,012.63.

Evidence: `evidence/issue155_pfndrdet_rollforward_20260831.csv`, `evidence/issue155_fund_population_20260831.csv`, `evidence/issue155_credited_rates_by_year_20260831.csv`. Probes: `tools/_pfndrdet_rollforward_probe.py`, `tools/_pfndrdet_population_probe.py`.

**Closed-row conflicts if Option A proceeds (need Warren's written OK):** #124 (zero month-0 seed), possibly #32 (QuikUint union schedule) and #21F (pre-2018 lump).

### Warren decisions — 2026-09-24

1. **#124 override:** approved **conditional on** Robert's QL test matching LifePRO 8/19 balances (9010713704 45,906.83; 9010713705 26,479.01; 9010713707 8,193.53) after seeding 6/19 balances (45,551.94; 26,251.74; 8,146.88). Not effective until the test passes.
2. **Negative LifePRO funds (248):** floor QL account at 0.00 and list for review — `evidence/issue155_negative_fund_review_list_20260831.csv`.
3. **Proof-test email:** to Robert, Eric, Sajitha (cc Jill).

Next gate: Robert's test result → "Proceed to Intake" → Intake–Risk → Development approval.
