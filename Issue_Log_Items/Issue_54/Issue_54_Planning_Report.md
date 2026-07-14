# Issue #54 — Planning Report

**Issue:** #54 — Full Loan History Load (LifePRO → QLAdmin Loan History)  
**Framework stage:** Planning Agent  
**Status:** **Blocked — Awaiting Client / New Era Clarification** (target table undefined)  
**Generated:** 2026-07-11  
**Agent/script:** Planning Agent (Cursor Grok 4.5) · evidence under `Issue_Log_Items/Issue_54/evidence/`

**Model:** Cursor Grok 4.5 (locked Planning stage)

---

## 1. Executive Finding

Eric wants the LifePRO **loan history sheet** visible in QLAdmin **Loan History** (§5.1.2.7). Issue **#32 / #44** already cover the **current outstanding loan** only (`QuikLoan`, one row per `MPOLICY`). That is **not** history.

**Confirmed:** LifePRO has two usable history sources — `PLOAN` accrual snapshots (~94k rows / 916 policies on 2026-06-30 extract) and `PACTG` 04xx Borrowed Money transactions (~37k rows / 685 policies). Phase 22C already correctly holds 04xx out of QUIKCLMS because they belong in the loan domain.

**Blocked for Development:** QLAdmin Help documents Loan History **UI fields** (Transaction Type, Date, Amount, Balance) and lists **QuikLoan** as the table “affected” when viewing Loan History — but QuikLoan’s published schema (§7.150) is **only nine current-loan fields** keyed by `MPOLICY` alone. Loan *processing* also writes **QuikAudt** (before/after memo), which is not a structured Type/Date/Amount/Balance ledger. This conversion repo has **no proven multi-row Loan History load table**.

**Direction:** Freeze **source** recommendation as **PACTG 04xx primary for transaction history** + **QuikLoan (#32) for current summary**; do **not** code until New Era / client confirms the **import table and field layout** that populates Loan History.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/? | Row count (2026-06-30) |
|--------------|--------------|-------------|------------------------:|
| **PLOAN** | `PLOAN_LoanInformation_Extract_20260630.csv` | Yes | **94,152** data rows / **916** policies |
| **PACTG** (04xx Borrowed Money) | `PACTG_Accounting_Extract20260630.csv` | Yes | **37,375** rows with credit/debit in `{0411,0412,0413,0414,0415,0416,0417,0451}` / **685** policies |

### PLOAN — available fields (history grain)

| Field | Populated? | Notes |
|-------|------------|-------|
| `POLICY_NUMBER` | Yes | Crosswalk → MPOLICY |
| `ACCRUAL_DATE` | Yes | Snapshot / event date |
| `STATUS_CODE` | Yes | Fleet: mostly `H` history; `A` active; `R` repaid-related |
| `TYPE_CODE` | Yes | `R` regular accrual, `A` adjustment (not QLAdmin Loan History types) |
| `ORIG_LOAN_AMOUNT` | Yes | Row-open principal |
| `LOAN_AMT_ADDED` | Yes | Delta for this snapshot (can be negative = payment-like) |
| `LOAN_BALANCE` | Yes | Running balance after row |
| `CAPITALIZED_AMOUNT` / `LAST_REPAY_AMOUNT` | Often | Event amounts when present |
| `INTEREST_RATE` | Yes | Rate at snapshot (QuikLoan current rate, not history type) |

**PLOAN grain:** Accrual/adjustment **snapshots**, not LifePRO accounting transaction codes. Example `9010331768`: **88** rows; deltas via `LOAN_AMT_ADDED` (capitalizations positive; payments negative).

### PACTG — available fields (transaction grain)

| Field | Notes |
|-------|-------|
| `POLICY_NUMBER` | Crosswalk → MPOLICY |
| `CREDIT_CODE` / `DEBIT_CODE` | Numeric (e.g. `412` / `451`); normalize to 4-digit `0412` / `0451` |
| `EFFECTIVE_DATE` | Transaction date |
| `TRANS_AMOUNT` | Amount |
| `REVERSAL_CODE` | `Y` = reverse; **521** reversed among 04xx set |
| `DESCRIPTION` | Often blank on loan rows |

**PACTG 04xx code hits (leg counts; a row may hit both sides):**

| Code | Definition (LifePRO Accounting) | Leg hits |
|------|---------------------------------|---------:|
| 0411 | Loan Principal | 3,617 |
| 0412 | Loan Interest Capitalized | 25,589 |
| 0413 | Loan Payment | 8,168 |
| 0414–0417 | Non-collateral / write-off | 0 in this extract |
| 0451 | Unearned Interest Income (offset to 0412) | 25,591 |

**Recommendation — source authority:**

| Role | Source | Why |
|------|--------|-----|
| **Loan History transactions (Type / Date / Amount)** | **PACTG 04xx** (exclude or pair-collapse **0451**) | True accounting events; maps to Help types (granted / payment / interest charged) |
| **Running balance (if required on each history line)** | Derive chronologically from PACTG, **or** align to nearest **PLOAN** `LOAN_BALANCE` by date | PACTG alone has no ending balance field |
| **Current loan summary panel** | **PLOAN latest → QuikLoan (#32/#44)** | Already designed; do not replace with history |

---

## 3. Confirmed QLAdmin Target Structure

### 3.1 What Help documents

| UI / table | Fields | Help |
|------------|--------|------|
| **Loan History window** | Transaction Type, Date, Amount, Balance; Accrued Interest; Current Balance; Interest Paid To | §5.1.2.7 p.74–75 |
| **QuikLoan** | `MPOLICY`, `MLOANPRIN`, `MLOANBAL`, `MLOANINT`, `MLOANINTX`, `MLOANIDT`, `MLOANDATE`, `MLOANACCR`, `MLOANBILL` | §7.150 p.827–828 |
| **QuikAudt** | `MUSER`, `MDATE`, `MTIME`, `MDBF`, `MPOLICY`, `MAUDIT` (memo) | §7.41 p.705 |

### 3.2 What this **does not** prove

| Claim | Finding |
|-------|---------|
| QuikLoan stores multi-row history | **False** — index `QuikLoan.ntx` = `MPOLICY` only; schema is current loan |
| QuikAudt is Loan History ledger | **Unlikely** — free-text before/after `MAUDIT`; Issue #34 recommended exclude for historical events |
| Conversion already has a Loan History CSV/DBF target | **None** in `schema_manifest.json`, `QLAdmin_Converted_Tables.txt`, or `qla_core` |

**Repo references:**

| Location | Role |
|----------|------|
| `qla_core/schema_constants.py` → `QUIKLOAN_SCHEMA` | Current loan only (9 fields) |
| `qla_core/quikloan_converter.py` | #32/#44 latest-row emit |
| `plan_governance/config/quikloan_derivation_rules.json` | Snapshot rules |
| `claims_analysis/config/claim_domain_eligibility_rules.json` | 04xx → QuikLoan + Loan History (not QUIKCLMS) |
| `validation_config/schema_manifest.json` → `quikloan` | Same 9 fields |

### 3.3 Target status for G1

| Item | Status |
|------|--------|
| Loan History **UI** confirmed | Yes |
| Loadable **history table / field layout** | **GAP — blocks Development** |
| QuikLoan as companion current balance | Confirmed (existing #32) |

---

## 4. Required Source-to-Target Field Mapping

### 4.1 Proposed mapping (**conditional** on New Era naming the history table)

Assume a future history target with logical columns matching Help: `MPOLICY`, `TXN_TYPE`, `TXN_DATE`, `TXN_AMT`, `TXN_BAL` (names TBD).

| LifePRO source | LifePRO field | Proposed QLAdmin history field | Transformation | Change? |
|----------------|---------------|--------------------------------|----------------|---------|
| PACTG | `POLICY_NUMBER` | MPOLICY | Crosswalk + `format_qladmin_mpolicy` (#25) | Yes — new emit |
| PACTG | `CREDIT_CODE`/`DEBIT_CODE` | Transaction Type | Map 0411→loan granted; 0412→loan interest charged; 0413→loan payment; exclude 0451 (or collapse pair) | Yes |
| PACTG | `EFFECTIVE_DATE` | Date | `YYYYMMDD` | Yes |
| PACTG | `TRANS_AMOUNT` | Amount | N(10.2); sign rules per type (TBD SME) | Yes |
| PACTG chronological +/or PLOAN | derived / `LOAN_BALANCE` | Balance | Running balance after txn (method TBD) | Yes |
| PACTG | `REVERSAL_CODE=Y` | — | Exclude or emit reversing type (SME) | Yes |

### 4.2 QuikLoan companion (no redesign)

| LifePRO | QuikLoan | Change under #54? |
|---------|----------|-------------------|
| PLOAN latest `LOAN_BALANCE` | MLOANPRIN / MLOANBAL | **No** — preserve #32/#44 |
| PLOAN `INTEREST_RATE` | MLOANINT | **No** |
| — | MLOANACCR=0 | **No** |

### 4.3 Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| QuikLoan mapping v1.2 / #44 HHMMSS sort | `quikloan_converter.py` | **No** (unless Risk finds conflict) |
| QUIKCLMS Phase 22C hold on 04xx | semantic governance | **No** — keep held from claims |
| `quikmstr` / `quikridr.MPREM` (#26) | existing | **No** |
| MPOLICY padding (#25) | `format_qladmin_mpolicy` | **No** — reuse only |
| QuikAudt synthesis | — | **No** unless New Era proves required |

### 4.4 Draft transaction-type crosswalk (SME sign-off required)

| PACTG code | LifePRO meaning | Proposed Loan History type label |
|------------|-----------------|----------------------------------|
| 0411 | Loan Principal | Loan granted |
| 0412 | Loan Interest Capitalized | Loan interest charged |
| 0413 | Loan Payment | Loan payment |
| 0414 | Non-collateralized Loan | Loan granted |
| 0415 | Non-collateralized Loan Interest | Loan interest charged |
| 0416 | Non-collateralized Payment | Loan payment |
| 0417 | Loan Write Off | Loan write-off / adjustment |
| 0451 | Unearned Interest Income | **Exclude** (0412 offset pair) |
| APL | Automatic premium loan | **Not observed** as distinct 04xx in extract — open |

---

## 5. Open Client Questions

1. **Where does QLAdmin persist Loan History rows for conversion load?** (table name, DBF/CSV layout, index). QuikLoan alone cannot hold them.
2. Confirm **PACTG 04xx** (not PLOAN snapshots) as the LifePRO “loan history sheet” authority for Type/Date/Amount.
3. Confirm **0451** handling: exclude vs show as paired offset.
4. Confirm **reversed** rows (`REVERSAL_CODE=Y`): omit vs emit reverse transactions.
5. Is **running Balance** required on each history line at conversion, or only Type/Date/Amount?
6. Should **paid-off** policies (QuikLoan not emitted) still get full history?
7. Exact **display labels** / codes New Era expects for transaction types (including APL if any).
8. Does Loan History UI **require** QuikLoan current row present to open / show header (Accrued / Current / Paid To)?

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + 10-char left-pad (#25) |
| Dates | `YYYYMMDD` from `EFFECTIVE_DATE` / `ACCRUAL_DATE` |
| Money | 2 decimal; absolute amount + type-driven sign if UI requires |
| Code normalize | Strip; digits only; zfill to 4 (`412` → `0412`) |
| Reversals | Default **exclude** until SME answers Q4 |
| 0451 | Default **exclude** until SME answers Q3 |
| Blanks | Skip rows missing policy, date, or amount |

---

## 7. Memo / Text / Special Handling

N/A for structured history. **Do not** attempt to encode history inside QuikAudt `MAUDIT` memos unless New Era mandates it.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `Master_Crosswalk.csv` → QLA  
2. `format_qladmin_mpolicy()` for CHARACTER(10)  
3. Orphans: audit + skip (same pattern as QuikLoan)

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| PLOAN history rows | 94,152 | 2026-06-30 extract |
| PLOAN policies | 916 | same |
| Latest non-zero QuikLoan candidates | ~356 | latest `LOAN_BALANCE ≠ 0` (extract drift vs #32’s 384 on May extract) |
| PACTG 04xx rows (incl. 0451 legs) | 37,375 | credit/debit in borrowed-money set |
| PACTG 04xx policies | 685 | same |
| Emit if exclude 0451 + reversals (order of magnitude) | ~**15k–20k** history lines | Planning estimate — refine after SME filter rules |

---

## 10. Sample Trace (3 policies)

| Policy (QLA) | LifePRO | Before (QL today) | After (proposed) | Status |
|--------------|---------|-------------------|------------------|--------|
| `010331768C` | `9010331768` | QuikLoan snapshot only (if emit on); Loan History empty; 0412/0413 held from claims | QuikLoan unchanged; Loan History rows from PACTG 0411/0412/0413 (0451 excluded); PLOAN 88 snapshots for balance recon | **Ready once target table known** |
| `010346921C` | `9010346921` | Same pattern (Phase 22C annual 0412 chain) | Same | Ready once target known |
| `010367438C` | `9010367438` | Same | Same | Ready once target known |

Evidence traces: `evidence/issue54_pactg_sample_traces.csv` (when research write completes).

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Wrong / missing history table → silent empty Loan History or corrupt load | **Critical** | Dependency Gate block until New Era confirms |
| Loading 04xx into QuikAudt as fake audits | High | Reject unless proven; #34 precedent |
| Double-counting 0412+0451 pairs | High | Exclude 0451 by default |
| History balances disagree with QuikLoan current | High | Reconcile last history balance to #32 MLOANBAL |
| Expanding QuikLoan to multi-row breaks `QuikLoan.ntx` | Critical | Do not change QuikLoan grain |
| Re-opening 04xx into QUIKCLMS | High | Keep Phase 22C hold |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present (PLOAN + PACTG) | **Met** |
| Field definitions confirmed (history **table**) | **Missing** |
| Client scope clear (want history in QL) | **Met** (Eric) |
| Transaction-type map signed | **Missing** |
| Example policies available | **Met** (soft — #32 traces) |
| #25 / #26 preserved in plan | **Met** |

**Gate expectation:** **NO-GO** until history target table confirmed.

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #54 ONLY AFTER Dependency Gate clears
(New Era confirms Loan History load table + field layout).

Read AI_Agents/Risk_Agent.md.
Model: Cursor Grok 4.5. Do not code.

Quantify: PACTG 04xx emit population (with/without 0451, reversals),
overlap with QuikLoan #32 policies, balance reconciliation risk vs PLOAN,
and regression risk to QUIKCLMS Phase 22C hold and QuikLoan snapshot.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Obtain New Era Loan History import spec (table + columns + index).  
2. Add isolated converter module (e.g. `qla_core/loan_history_converter.py`) — **do not** overload `quikloan_converter.py` grain.  
3. Map PACTG 04xx → history rows; default exclude 0451 + `REVERSAL_CODE=Y`.  
4. Keep QuikLoan #32/#44 untouched; optionally enable companion emit under existing gates.  
5. Validator: type map coverage, MPOLICY pad, no QUIKCLMS 04xx leak, sample policy row counts, last balance vs QuikLoan.  
6. Version bump both `app.py` copies when wiring batch.  
7. Validation script: `tools/validators/validate_issue54_loan_history.py`

---

## Appendix

### Diagnostic / evidence

- `Issue_Log_Items/Issue_54/evidence/issue54_ploan_summary.csv`
- `Issue_Log_Items/Issue_54/evidence/issue54_pactg_04xx_summary.csv`
- `Issue_Log_Items/Issue_54/evidence/issue54_pactg_sample_traces.csv`

### Related issues

- #32 QuikLoan snapshot · #44 LAST_CHG_TIME · Phase 22C 04xx hold · #34 QuikAudt exclude · #25 MPOLICY

### References

- QLAdmin Help §5.1.2.7 Loan History; §5.1.3.7 Processing a Loan; §7.150 QuikLoan; §7.41 QuikAudt  
- LifePRO Accounting Transactions — 04xx Borrowed Money  
- `Issue_32_*` mapping pack · `claim_domain_eligibility_rules.json`
