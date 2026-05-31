# Executive Status Analysis Summary

Generated: 2026-05-28 15:00:09

## Scope

Business validation comparing converted QLAdmin outputs (quikclms, quikmstr) to LifePRO source.
No automatic error classification — flagged rows are for business review only.

## Volume

- Claim rows analyzed: **1271**
- Flagged for review (unusual combo or missing quikmstr): **313**
- Conversion changed policy status (ST_ path vs emitted MSTATUS): **0**
- Conversion changed claim status (lifecycle vs CLAIMSTAT): **320**
- Review-only cross-domain combos (no conversion delta): **182**

## Top status combinations (converted)

| Combination | Count |
|-------------|-------|
| Terminated/Death + Settled | 749 |
| Active + Surrender | 137 |
| Paid Up + Settled | 83 |
| Reduced Paid Up + Settled | 57 |
| Terminated/Death + Surrender | 54 |
| Surrendered + Surrender | 36 |
| Extended Term + Surrender | 30 |
| Matured + Surrender | 29 |
| Paid Up + Surrender | 28 |
| Extended Term + Settled | 20 |
| Lapsed + Surrender | 19 |
| Terminated/Death + Pending | 14 |
| Expired + Surrender | 6 |
| Reduced Paid Up + Surrender | 5 |
| Lapsed + Settled | 2 |

## Investigation answers

### 1. Did source already contain Reduced Paid Up + Settled?

**Yes — for death-settlement cases like 010464590C.** Source policy master shows Reduced Paid Up with Contract Terminated and Reason Death Claim. PACTG reconstruction yields **Settled (Claim Fully Resolved)** for the death claim. These are different LifePRO domains (contract maintenance vs accounting/claims reconstruction).

### 2. Were statuses changed during conversion?

Policy MSTATUS changes detected: **0** rows. Claim CLAIMSTAT changes vs PACTG lifecycle mapping: **320** rows. Example **010464590C**: policy status **Reduced Paid Up** matches source; claim status **Settled** matches PACTG lifecycle — **no conversion drift**.

### 3. Does Master_Value_Translation alter statuses?

**Yes for quikmstr MSTATUS only.** Composite keys (`ST_*`, `PUT_*`) map LifePRO `CONTRACT_CODE`/`CONTRACT_REASON`/`PAID_UP_TYPE` to QLAdmin numeric codes. Claims CLAIMSTAT is mapped from reconstructed lifecycle in Phase 10B derivation rules, not from a LifePRO claim-status column.

### 4. Do rulebooks transform statuses?

**quikmstr:** MSTATUS rulebook points at CONTRACT_CODE but **app.py composite interceptor** overrides with PAID_UP_TYPE-first logic, then ST_ translation. **quikclms:** CLAIMSTAT defaults in rulebook; actual values come from Phase 10B lifecycle→CLAIMSTAT mapping.

### 5. Are claim statuses independent of policy statuses in LifePRO?

**Yes.** LifePRO does not expose a single paired policy/claim status field. Policy status lives on the contract extract; claim lifecycle is inferred from PACTG transactions.

### 6. Patterns

Most common converted pattern: **Terminated/Death + Settled** and **Reduced Paid Up + Settled** on death claims where PAID_UP_TYPE=RU or contract reason=DC. Surrender/disbursement claims cluster as **Paid in Full** with varied policy statuses.

### 7. Expected vs review

- **Expected:** RPU/PU/ET + Settled on post-death non-forfeiture outcomes.
- **Review:** Active + Settled, Lapsed + Open/Pending — may indicate timing or semantic mismatch.
- **True defects:** Rows where STATUS_CHANGED_FLAG=Y or CLAIM_STATUS_CHANGED_FLAG=Y (conversion drift).

## Example: 010464590C

- Target policy status: **Reduced Paid Up**
- Target claim status: **Settled**
- Claim type: **Death Claim**
- Combination: **Reduced Paid Up + Settled**
- Review flag: **Y** (cross-domain review, not conversion error)

## Recommendations

1. **Business sign-off** on death-claim + RPU/PU combinations — likely valid post-settlement contract state.
2. **Prioritize review** of Active/Lapsed policy + Settled/Pending claim rows.
3. **Do not change conversion** until business confirms which cross-domain pairs are invalid in QLAdmin.
4. Investigate any row with POTENTIAL_CONVERSION_ISSUE=Y in report 3.

## Regenerate

```powershell
python plan_analysis/status_analysis/status_analysis_runner.py
```
