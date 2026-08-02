# Issue #135 — CSO × Output × PACTG Reconciliation

Generated: 2026-08-02T20:10:23Z

## Hard-control statements

- CSO has **no claim number**; `Total_Paid` is a **policy-level** hard control.
- Do **not** sum death-claim amounts with PS / surrender / shell rows.
- Policies in `MISSING_ERIC_SUPPLY` are absent because Eric has not supplied all policies yet — **not** a current conversion failure.
- Unexplained residuals are held as `UNEXPLAINED_RESIDUAL` — **not** force-fit to CSO.

## Population summary (available ~1,100 vs Eric gaps)

| Bucket | Count |
|---|---:|
| CSO death policies (control) | 1656 |
| AVAILABLE_MATCH | 1104 |
| AVAILABLE_MISMATCH | 61 |
| IN_OUTPUT_NO_DEATH_HEADER | 32 |
| MISSING_ERIC_SUPPLY | 459 |
| Available represented (match+mismatch+no-death) | 1197 |

PACTG path: `C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Source\PACTG_Accounting_Extract20260630.csv`
Output clms: `C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Output\quikclms.csv`

## Teacher death cases

| Policy | CSO Total_Paid | Death MPAID | Residual | Proposed rule |
|---|---:|---:|---:|---|
| 9010150740C | 3213.59 | 3213.59 | 0.00 | MATCH_CSO |
| 9010391359C | 1260.06 | 0.00 | 1260.06 | MISSING_DEATH_MPAID_BUT_PACTG_PAYOUT |
| 9010402010C | 8920.15 | 8920.15 | 0.00 | MATCH_CSO |
| 9010429064C | 22711.07 | 22711.07 | 0.00 | MATCH_CSO |
| 9010430296C | 11639.54 | 11639.54 | 0.00 | MATCH_CSO |
| 9010914301C | 25019.98 | 50039.96 | -25019.98 | DUPLICATE_PAYOUT |
| 9011156098C | 15000.00 | 45000.00 | -30000.00 | REINSTATEMENT_TRIPLE_COUNT |

## Surrender examples (separate workstream)

| Policy | In Output | Families | MPAID sum (all families) | Note |
|---|---|---|---:|---|
| 9010360289C | Y | SURRENDER | 3129.06 | Surrender workstream — not CSO Total_Paid hard control; do not sum with death |
| 9010753675C | Y | SURRENDER | 26155.88 | Surrender workstream — not CSO Total_Paid hard control; do not sum with death |
| 9010429711C | Y | SURRENDER | 5347.75 | Surrender workstream — not CSO Total_Paid hard control; do not sum with death |
| 9010746846C | Y | PARTIAL_SURRENDER | 1897.00 | Surrender workstream — not CSO Total_Paid hard control; do not sum with death |

## Proposed rule class counts (available mismatch only)

| Rule class | Count |
|---|---:|
| REINSTATEMENT_TRIPLE_COUNT | 22 |
| DUPLICATE_PAYOUT | 17 |
| INTEREST_IN_CHECK_REVIEW | 7 |
| MISSING_DEATH_MPAID_BUT_PACTG_PAYOUT | 6 |
| UNEXPLAINED_RESIDUAL | 4 |
| HEADER_PAYEE_MISALIGN | 3 |
| INTRACO_OR_REINSTATE_REVIEW | 2 |
