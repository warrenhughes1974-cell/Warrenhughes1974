# Issue #135 — Phase B Reverse-Engineering Report

Generated: 2026-08-02T20:09:05Z

## Scope

- Population: **AVAILABLE_MISMATCH only** (61).
- Separated: **IN_OUTPUT_NO_DEATH_HEADER** (32) — shell/PS/disbursement; not death CLAIMSTAT=2 rules.
- Eric supply gaps (459): untouched; not conversion failures.
- `MINTAMT` remains 0.00 (Phase A).
- No production claim-amount code change in this pass.

## Separation

| Bucket | Count |
|---|---:|
| AVAILABLE_MISMATCH (death headers vs CSO) | 61 |
| … with CLAIMSTAT containing 2 | 61 |
| … with CLAIMSTAT containing 1 | 0 |
| NO_DEATH_SHELL_OR_PS (separated) | 32 |

## Evidence class frequencies (61 mismatches)

| Evidence class | Count | Hold | Example policies |
|---|---:|---|---|
| MULTIPLICITY_X3_REINSTATEMENT | 22 | CANDIDATE | 9010385491C; 9010745640C; 9010764834C |
| MULTIPLICITY_X2_DUPLICATE_OR_CLEARING | 17 | CANDIDATE | 9010411499C; 9010428771C; 9010500769C |
| CLEARING_DUPLICATION_SUSPECT | 10 | HOLD | 9010376540C; 9010834719C; 9010836057C |
| MISSING_DEATH_MPAID_BUT_PACTG_PAYOUT | 6 | CANDIDATE | 9010391359C; 9010786152C; 9011141895C |
| HEADER_PAYEE_MISALIGN_BOTH_OFF | 3 | HOLD | 9010768069C; 9010780003C; 9010783502C |
| LOAN_RESIDUAL_SHORTFALL | 2 | HOLD | 9010454002C; 9011212602C |
| INTEREST_IN_CHECK_RESIDUAL | 1 | HOLD | 9010847570C |

## Hold vs candidate

| Hold flag | Count |
|---|---:|
| CANDIDATE | 45 |
| HOLD | 16 |

## Phase B code decision

**Code change implemented:** `False`

No Phase B production claim-amount rule implemented. x2 (17) and x3 (22) have repeated PACTG proof, but the emit correction mechanism is unresolved (header scale vs payee dedupe vs exclude reinstatement/clearing loops). Forcing MPAID=Total_Paid without that path is disallowed. Missing-death PACTG payout cases are few (<5) and need the same mechanism choice.

### Candidate classes (not auto-implemented)

| Class | Count | Safe to implement? | Reason |
|---|---:|---|---|
| MULTIPLICITY_X3_REINSTATEMENT | 22 | False | Repeated PACTG pattern exists (ratio + clearing/reinstatement/0094-1058 legs). Correction mechanism is still ambiguous: scale header MPAID vs dedupe quikclmp payees vs exclude reinstatement/clearing loops in emit. Do not force MPAID=Total_Paid without an approved audit-reasoned path. Needs Development approval for the chosen mechanism. |
| MISSING_DEATH_MPAID_BUT_PACTG_PAYOUT | 6 | False | Repeated PACTG pattern exists (ratio + clearing/reinstatement/0094-1058 legs). Correction mechanism is still ambiguous: scale header MPAID vs dedupe quikclmp payees vs exclude reinstatement/clearing loops in emit. Do not force MPAID=Total_Paid without an approved audit-reasoned path. Needs Development approval for the chosen mechanism. |
| MULTIPLICITY_X2_DUPLICATE_OR_CLEARING | 17 | False | Repeated PACTG pattern exists (ratio + clearing/reinstatement/0094-1058 legs). Correction mechanism is still ambiguous: scale header MPAID vs dedupe quikclmp payees vs exclude reinstatement/clearing loops in emit. Do not force MPAID=Total_Paid without an approved audit-reasoned path. Needs Development approval for the chosen mechanism. |

## Teacher case refresh

| Policy | CSO | Death MPAID | Ratio | Evidence class | Hold |
|---|---:|---:|---:|---|---|
| 9010391359C | 1260.06 | 0.00 | 0.0 | MISSING_DEATH_MPAID_BUT_PACTG_PAYOUT | CANDIDATE |
| 9010914301C | 25019.98 | 50039.96 | 2.0 | MULTIPLICITY_X2_DUPLICATE_OR_CLEARING | CANDIDATE |
| 9011156098C | 15000.00 | 45000.00 | 3.0 | MULTIPLICITY_X3_REINSTATEMENT | CANDIDATE |

## Artifacts

- `issue135_phase_b_mismatch_deep_dive.csv` — per-policy deep dive
- `issue135_no_death_shell_ps_separated.csv` — 32 no-death/shell/PS separation
- `issue135_phase_b_reverse_eng_summary.json` — machine summary

## Safeguards preserved

- CSO Total_Paid is policy-level; never sum death + PS.
- Do not set MPAID=Total_Paid without PACTG evidence + audit reason.
- Unexplained → HOLD/UNEXPLAINED.
- Preserve #134 MEMOTEXT, #78/#84/#85 payee/header, Item 16/18, MPOLICY/MPREM.
