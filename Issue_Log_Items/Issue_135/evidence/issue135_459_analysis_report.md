# Issue #135 — 459 Accounting Derivation ANALYSIS (read-only)

Generated: 2026-08-02T20:36:28Z

> **ANALYSIS ONLY** — derived candidates from PACTG accounting.  
> **Not** production Output. **Not** CSO-validated settlements unless `cso_validation_status=CSO_CROSSCHECK_MATCH`.  
> A derived amount ≠ verified against Total_Paid for load purposes without the separate cross-check flag.

## Premise challenge

- Prior label: MISSING_ERIC_SUPPLY labeled as Eric supply gap / awaiting source; sometimes described as absent from CSO join
- Finding: These 459 are PRESENT in the CSO Total_Paid workbook (policy-level control exists) and ABSENT from current Output quikclms (no policy row). Prior recon pactg_row_count=0 is an artifact of --pactg-scope=available, which excluded MISSING_ERIC_SUPPLY from the PACTG stream — not proof of no history.
- Grain: CSO Total_Paid is policy-level; one control row per mpolicy; no claim number
- Failure framing: Do NOT call these conversion failures solely because they are absent from Output; they lack Output representation. Whether they are extract/population gaps vs engine omissions requires PACTG/PRELSA presence (measured in this analysis).

| Premise metric | Count |
|---|---:|
| gap_policies | 459 |
| in_cso_with_total_paid_gt0 | 459 |
| in_current_output_any_row | 0 |
| in_current_output_death_header | 0 |
| prior_recon_pactg_row_count_zero | 459 |

## Category counts (all 459)

| Category | Count | Meaning |
|---|---:|---|
| NO_PACTG_HISTORY | 308 | No rows in PACTG extract for policy |
| DERIVED_HIGH | 142 | Accounting unique eco amount; equals CSO Total_Paid cross-check |
| HOLD_INCOMPLETE_SOURCE | 9 | PACTG present but death payout chain incomplete |

## Source availability

| Metric | Count |
|---|---:|
| With PACTG history | 151 |
| No PACTG history | 308 |
| With PRELSA rows | 151 |
| With PRELSA payee-relevant roles (PE/B1/B2/TR/CU/AS) | 151 |
| Derived candidate amounts (HIGH+MEDIUM) | 142 |
| Of derived, CSO cross-check match | 142 |
| Of derived, CSO cross-check mismatch | 0 |

## Confidence bands

| Band | Count |
|---|---:|
| 0 | 308 |
| 1-39 | 9 |
| 40-69 | 0 |
| 70-89 | 0 |
| 90-100 | 142 |

## Examples by category

### DERIVED_HIGH (142)

| Policy | CSO Total_Paid | Derived | Conf | Method | Payee roles | Note |
|---|---:|---:|---:|---|---|---|
| 9010367438C | 4469.37 | 4469.37 | 95 | ECO_SUBSET_MATCH_CSO_CROSSCHECK | 14 | selected_eco_legs=3 of 3; full_eco_sum=4469.37; uniq=[1489.79]; accounting_deriv |
| 9010378710C | 6715.85 | 6715.85 | 95 | ECO_SUBSET_MATCH_CSO_CROSSCHECK | 2 | selected_eco_legs=1 of 1; full_eco_sum=6715.85; uniq=[6715.85]; accounting_deriv |
| 9010395382C | 4012.31 | 4012.31 | 95 | ECO_SUBSET_MATCH_CSO_CROSSCHECK | 10 | selected_eco_legs=1 of 1; full_eco_sum=4012.31; uniq=[4012.31]; accounting_deriv |
| 9010403922C | 9666.78 | 9666.78 | 95 | ECO_SUBSET_MATCH_CSO_CROSSCHECK | 6 | selected_eco_legs=1 of 1; full_eco_sum=9666.78; uniq=[9666.78]; accounting_deriv |
| 9010404857C | 6292.70 | 6292.70 | 95 | ECO_SUBSET_MATCH_CSO_CROSSCHECK | 4 | selected_eco_legs=1 of 1; full_eco_sum=6292.70; uniq=[6292.7]; accounting_derive |

### NO_PACTG_HISTORY (308)

| Policy | CSO Total_Paid | Derived | Conf | Method | Payee roles | Note |
|---|---:|---:|---:|---|---|---|
| 9010381483C | 9702.00 |  | 0 |  | 0 | No PACTG rows in dated extract for this policy |
| 9010383050C | 4408.40 |  | 0 |  | 0 | No PACTG rows in dated extract for this policy |
| 9010394282C | 1238.74 |  | 0 |  | 0 | No PACTG rows in dated extract for this policy |
| 9010394783C | 12777.92 |  | 0 |  | 0 | No PACTG rows in dated extract for this policy |
| 9010398651C | 7949.87 |  | 0 |  | 0 | No PACTG rows in dated extract for this policy |

### HOLD_INCOMPLETE_SOURCE (9)

| Policy | CSO Total_Paid | Derived | Conf | Method | Payee roles | Note |
|---|---:|---:|---:|---|---|---|
| 9010395879C | 4916.26 |  | 25 |  | 36 | Death-family accounting signals present (funding/clearing/cash) but no open ECON |
| 9010741943C | 39515.55 |  | 25 |  | 3 | Death-family accounting signals present (funding/clearing/cash) but no open ECON |
| 9010771580C | 20089.71 |  | 25 |  | 14 | Death-family accounting signals present (funding/clearing/cash) but no open ECON |
| 9010771662C | 46125.62 |  | 25 |  | 21 | Death-family accounting signals present (funding/clearing/cash) but no open ECON |
| 9011153243C | 4669.56 |  | 25 |  | 3 | Death-family accounting signals present (funding/clearing/cash) but no open ECON |

## Grok validation (second pass)

- Overall: **PASS**
- Fail: 0 | Warn: 0 | Population=459: True

- Validates derived amounts are supported by open 2032→1058 eco rows after loop/reversal exclusion.
- Confirms HOLD/NO categories do not invent amounts.
- Confirms cso_match_yn arithmetic vs cso_total_paid.
- A CSO cross-check match is NOT the same as production CSO-validated Output settlement.

## Higher-model need

No higher model required for this analysis pass. Remaining blockers are source gaps (NO_PACTG_HISTORY=308, HOLD_INCOMPLETE=9) or ambiguous chains (0), not arithmetic failures.

## Artifacts

- `issue135_459_analysis_per_policy.csv` — one row per gap policy
- `issue135_459_analysis_summary.json` — machine summary
- `issue135_459_analysis_grok_validation.json` — second-pass review
- `issue135_459_analysis_included_excluded_events.csv` — eco/loop event detail (sample+all derived)

## Explicit non-claims

- Derived ≠ production MPAID.
- CSO cross-check match ≠ loaded/verified Output settlement.
- No app.py / Output / rulebook changes in this pass.
