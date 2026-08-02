# Issue #135 — Discovery Notes (Search & Discuss)

**Issue:** #135 — Claims settlement amounts vs CSO Total_Paid / client accounting examples  
**Date:** 2026-08-02  
**Framework stage:** Stage 0 Discovery complete (G-D)  
**Status recommendation:** Discovery — await **Proceed to Intake** before Pre-Dev chain  
**Owner:** Conversion (Warren)  
**Raised by:** Warren (from client spreadsheets in `docs/Claims`)  
**Priority:** Go (claims financial hard control)  
**Code:** None (Discovery only)

---

## Client ask (normalized)

Client provided two workbooks under `docs/Claims/`:

1. **Claim Accounting examples.xlsx** — worked LifePRO accounting (PACTG-style) examples with **red text** marking wrong totals, excluded GL lines, and defect labels (`Double Counting Interest`, `Not Factoring Reinstatement`, `Death Date should not populate`).
2. **CSO Life claims summary - 2017 - 2025.xlsx** — ~1,656 death claims with **`Total_Paid`**.

**Locked at Discovery (user 2026-08-02):** `Total_Paid` is a **hard control** for death-claim settlement amounts. Conversion must reverse-engineer GL inclusion/exclusion rules so emitted claim paid amounts match `Total_Paid`.

---

## Spreadsheet meaning (plain language)

| Spreadsheet piece | Meaning |
|---|---|
| Accounting lines (DB/CR accounts + amounts) | The LifePRO journal entries that make up a claim settlement |
| **Column J formulas** | Client’s **correct** hand-total for that example (add the right lines, skip the bad ones) |
| **Column L values** (often red) | **Wrong** total — typically what a naive sum / current conversion produces |
| Entire row in **red** | Exclude that GL activity from claim amount/balancing (e.g. `603703R` / `2023` interest on div deposit) |
| Labels like “Double Counting Interest” | Interest already in the check must not be added again |
| “Not Factoring Reinstatement” | Reinstate / endow / intra-co loops create fake extra payments |
| Surrender header “Death Date should not populate” | Non-death claims must leave `DTOFDEATH` blank |

There is no separate “J chain” product concept — it only meant “the correct total computed in column J.”

---

## `MINTAMT` (locked at Intake — user 2026-08-02)

Schema: **`MINTAMT` = “Amount of interest earned”**.

**Lock:** Always emit **`MINTAMT = 0.00`**. Client does not need interest on converted claims; paid amount is carried in `MPAID` / payees only.

---

## Current behavior vs desired

| Area | Current (full Output sample) | Desired |
|---|---|---|
| Death `MPAID` vs CSO `Total_Paid` | ~1,111 match / ~86 mismatch / ~459 missing | **All** CSO death claims present with `MPAID` (and payee sum) = `Total_Paid` |
| Reinstatement example `9011156098C` | `MPAID=45000` (3×15k) | `15000` |
| Intra-co duplicate `9010914301C` | `MPAID=50039.96` | `25019.98` |
| Loan death `9010391359C` | `MPAID=0`, no payees | `1260.06` + payee |
| Div-on-deposit `9010150740C` | `MPAID=3213.59` (good); missing payee | Keep amount; emit payee |
| Interest double-count (selected) | `MPAID` good; `MINTAMT` still set | Keep correct `MPAID`; **`MINTAMT=0`** |
| Surrender `DTOFDEATH` | Often populated on `PS-*` | Blank for non-death |
| Surrender completeness | Often incomplete vs accounting examples | Full valid surrender funding (separate from death hard control, but same workbook) |

---

## Source / conversion path (where reverse-engineering plugs in)

| Layer | Location |
|---|---|
| Expected death paid | `docs/Claims/CSO Life claims summary - 2017 - 2025.xlsx` (`Total_Paid`) |
| Worked GL examples + red rules | `docs/Claims/Claim Accounting examples.xlsx` |
| Accounting extract | `QLA_Migration/Source/PACTG_Accounting_Extract*.csv` (claims resolve via `QLA_CLAIMS_PACTG_PATH` / dated extract) |
| Claim / payee reconstruct | `claims_analysis/` phases 4–10, 17, 22–24 |
| Existing partial rules | `claims_analysis/config/client_issue_log_decision_rules.json` (Items 14–19; Item 16 div-deposit; Item 18 loan combine) |
| Emit / post-process | `QLA_Migration/app.py` claims orchestration; `qla_core/claims_emit_enhancements.py`; issues 78/79/84/85/134 |
| Targets | `quikclms` (`MPAID`, `MFACE`, `NETDB`, `LOAN`, `MINTAMT`, `DTOFDEATH`, …), `quikclmp` (`MAMOUNT`, payee fields) |

---

## Proposed reverse-engineering method (Discovery recommendation)

**Goal:** discover durable include/exclude rules so every CSO death claim’s converted paid amount equals `Total_Paid`.

Accounting examples are the **teacher set** (why a line is in/out). CSO is the **exam** (must pass for all ~1,656).

Surrender population uses the same accounting-example method but is **not** covered by the CSO death `Total_Paid` hard control — track as a linked workstream inside this issue or a follow-on.

### Control-first steps

1. **Establish control total** — for each death claim match policy, claim/event dates, and CSO `Total_Paid`. Do **not** derive the expected amount from current `quikclms`/`quikclmp`.
2. **Build a control file** — one row per CSO policy: `Total_Paid`, notice/incurred/last-paid dates, plan, current Output `MPAID` / payee sum / claim family / hold reason.
3. **Reconstruct the PACTG ledger window** — pull related rows; normalize debit/credit; pair reversals; partition into layers (funding, payout, claim interest, div deposits, loan principal/interest, withholding, clearing/lifecycle, unrelated). Link payees via PRELSA.
4. **Learn include/exclude from the workbook** — column J = known-good settlement; red rows = exclusion / wrong-path; record rules by GL code, DB/CR account, description, and role (e.g. div-deposit balance may include while `603703R` interest on div deposit excludes).
5. **Work residual backward** — `Residual = Total_Paid - reconstructed_included_amount`. Classify: exact match; equals one known row; duplicate payout; reinstatement loop; loan domain; unexplained hold.
6. **Teacher regression cases first** — `9011156098C` (reinstatement), `9010914301C` (duplicate), `9010391359C` (loan-at-death), plus other red-annotated examples.
7. **Codify rules** into reconstruction / balancing / derivation so Phase 10A/10B **consume** the validated total rather than inventing a second paid amount.
8. **Hard-gate validation** — reconstructed total == CSO `Total_Paid` (cent tolerance); every include/exclude has a reason; no clearing+payout double count; unresolved claims blocked from production Output.

### Working formula (draft)

```text
Expected Total_Paid =
  included benefit components
+ included claim interest (only if not already inside the check)
+ included eligible deposits/credits
- included offsets / deductions
- excluded / reversed / duplicate representations
```

Clearing rows must not be counted merely because they carry the same dollars as the final payout.

### Repo phases that already support this (read-only reuse)

| Need | Path |
|---|---|
| Source paths | `claims_analysis/config/claims_source_paths.json`; PACTG `QLA_Migration/Source/PACTG_Accounting_Extract20260427.csv`; PRELSA `QLA_Migration/Source/RelationshipNameAddress_Extract.csv` |
| PACTG profiling | `claims_analysis/phase1_pactg_transaction_profiling/` |
| Claim reconstruction | `claims_analysis/phase4_claim_event_reconstruction/` |
| Financial reconciliation | `claims_analysis/phase5_financial_reconciliation/` |
| Death decomposition layers | `claims_analysis/phase7c_death_claim_decomposition/` |
| Payee / PRELSA | `claims_analysis/phase8_payee_distribution_intelligence/` |
| QUIKCLMP / QUIKCLMS derivation | `claims_analysis/phase10a_quikclmp_derivation_design/`, `phase10b_quikclms_derivation/` |
| Loan vs claim semantics | `claims_analysis/phase22_semantic_governance/`; `claims_analysis/config/claim_domain_eligibility_rules.json` |

### Reconciliation deliverable (for Intake/Planning)

Claim-level file with: policy/claim key, source `Total_Paid`, included rows/codes, excluded rows/codes, component totals, residual, rule explanations, confidence, validation status.

---

## Related issues (preserve / do not regress)

| Issue | Relevance |
|---|---|
| Client Items 14–19 / Phase 23–24 | Div-deposit exclusion, orphan standalones, loan combine — extend, don’t undo |
| #78 / #84 / #85 | Payee recovery, header backfill, claim identity |
| #79 | `CLAIMSTAT` remap |
| #134 | Claims memo (`MEMOTEXT`) — orthogonal |
| #34 / ISWL PS emit | Partial surrender `PS-*` rows; death-date and amount rules collide here |

---

## Open questions

1. ~~`MINTAMT`~~ — **Closed:** always 0 (user 2026-08-02).
2. **Missing ~459 CSO deaths:** extract gap vs conversion hold vs eligibility filter? Resolve during reverse-engineering before coding amount formulas.
3. **Surrender hard control:** is there a separate client paid-total file, or only the accounting examples for now?
4. **Authority when PACTG cannot hit `Total_Paid`:** hold (Planning default) / header-only / client exception list?

---

## Model recommendation (Discovery)

| Work | Higher model needed? |
|---|---|
| This Discovery / issue framing | No |
| Scripted reverse-engineering vs PACTG + CSO hard control | **Not required** — structured reconciliation + evidence; scripts matter more than model size ([Reverse-engineer plan](01e447e9-b338-4bca-acff-f8c137b810ce)) |
| Ambiguous residual review / competing GL explanations | **Optional escalate** (Opus/Sonnet high) when residual cannot be classified |
| Surgical conversion coding after patterns are proven | Deterministic + test-driven; higher model useful for review, not as GL authority |

---

## Proposed work list (for Planning after Intake)

1. CSO hard-control reconciliation workbook (match / mismatch / missing).
2. PACTG reverse-engineering for mismatch + teacher examples → draft include/exclude rules.
3. Fix proven defect classes: reinstatement multi-count, intra-co duplicates, loan death payouts, interest field policy, surrender death-date + completeness.
4. Validators: `MPAID` + payee sum == CSO `Total_Paid`; no `DTOFDEATH` on non-death.
5. Full Output re-batch + regression.

---

## Stop

Discovery complete; Pre-Dev chain continued on user **Proceed to Intake**. See Intake / Planning / Dependency Gate / Risk reports. Awaiting **Approved for Development**.
