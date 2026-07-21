# Issue #78 — Planning Report

**Issue:** #78 — Recover missing `quikclmp` claim payments with approved payee fallback  
**Framework stage:** Planning Agent  
**Status:** Planning Complete → Dependency Gate  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None  
**Scope authority:** `Issue_78_Scope_Decisions.md` (SD-78-1 … SD-78-10)

---

## 1. Executive Finding

**744** `quikclms` policies have **no** `quikclmp` rows. LifePRO **PACTG** still holds live payout transactions for **729** of those policies (**932** rows, **~$7.37M**). Payee name is not on the accounting row (`GOVT_NAME` blank in extract); payees for already-emitted payments came from **RelationshipNameAddress** (`PE`). User locked a three-tier payee rule (single PE → multi PE → B1/estate). Recommended direction: surgical recovery emit into `quikclmp` for the 729 recoverable policies, leave existing payment rows untouched, audit Tier 2/3. **Go for Dependency Gate / Risk** — sources and business rule are present.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count (approx) |
|--------------|--------------|---------------------|-------------------:|
| PACTG | `PACTG_Accounting_Extract20260630.csv` | Yes | Large (chunked) |
| Relationship / Name-Address | `RelationshipNameAddress_Extract_20260630.csv` | Yes | Parsed with bad-line skip |
| Claim headers (converted) | `Output/quikclms.csv` | Yes | 5,624 |
| Claim payments (converted) | `Output/quikclmp.csv` | Yes | 5,219 |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Policy number | PACTG / Rel `POLICY_NUMBER` | High | Map via crosswalk + #25 padding |
| Payout amount | PACTG `TRANS_AMOUNT` | High on payout codes | Credit/Debit side per catalog |
| Payout date | PACTG `EFFECTIVE_DATE` | High | → `MPMTDATE` / `MCHKDATE` |
| Reversal filter | PACTG `REVERSAL_CODE` | — | Exclude Y/R/V |
| Payee name | Rel `KEY_NAME` / name parts | High on PE | PE present on 731/744 missing-pay policies |
| Payee address | Rel `ADDR_LINE_1`, `CITY`, `STATE`, `ZIP` | High on PE sample | Confirmed populated on PE rows |
| Payee identity | Rel `NAME_ID` | High | Distinct count drives Tier 1 vs 2 |
| Control / check | PACTG `CONTROL_NUMBER` | Partial | Prefer when usable |
| Claim family | `quikclms.MEMOTEXT` lineage | High | Death / surrender / disbursement |

**Payout codes (semantic catalog):** 90, 92, 94, 567, 1900 (and zero-padded variants if present).

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source |
|-------|-------|------|--------|--------|
| quikclmp | MPOLICY | C | 10 | Schema / Help; #25 padding |
| quikclmp | MPHASE | N | — | Match claim header phase (usually 1) |
| quikclmp | MCHECKNO | C | — | CONTROL_NUMBER or derivation default |
| quikclmp | MAMOUNT | N | — | PACTG TRANS_AMOUNT |
| quikclmp | MPAYNAME … MPAYZIP2 | C | — | PE / B1 / estate |
| quikclmp | MCHKDATE / MPMTDATE | D | — | EFFECTIVE_DATE |
| quikclmp | MSEQ | N | — | Existing non-98 default 0 |
| quikclmp | MHOLDINT / MFEDTAX / MSTTAX / MGROSS | N | — | Follow Phase 10A defaults unless PACTG has tax |

**Repo references:**

| Location | Role |
|----------|------|
| `QLA_Migration/Configs/Sync_Rulebook_quikclmp.csv` | Field defaults |
| `claims_analysis/phase10a_quikclmp_derivation/` | Existing payment derivation |
| `claims_analysis/phase8_payee_distribution/` | PE / beneficiary assignment patterns |
| `qla_core/claims_emit_enhancements.py` | Post-emit CLAIMNUM / MSEQ rules |
| `QLA_Migration/app.py` claims orchestration | UAT emit path |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PACTG | POLICY_NUMBER | MPOLICY | Crosswalk + `format_qladmin_mpolicy` | Yes (new rows) |
| quikclms | MPHASE | MPHASE | Copy from matching claim header | Yes |
| PACTG | TRANS_AMOUNT | MAMOUNT / MGROSS | Money format per existing emit | Yes |
| PACTG | EFFECTIVE_DATE | MPMTDATE, MCHKDATE | YYYYMMDD | Yes |
| PACTG | CONTROL_NUMBER | MCHECKNO | If usable; else existing default | Yes |
| Rel PE | KEY_NAME + ADDR_* | MPAYNAME…ZIP | Tier 1 / 2 | Yes |
| Rel B1 / IN | KEY_NAME + ADDR_* | MPAYNAME…ZIP | Tier 3 | Yes |
| — | — | MTIN / MBANKNO | Blank unless already derived elsewhere | No invent |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| Existing `quikclmp` rows | Current emit | **No** (SD-78-6) |
| `quikclms` CLAIMSTAT / ORIGSTTUS / CAUSE | Current emit | **No** (SD-78-7) |
| quikmstr.MMODPREM | PPOLC | **No** |
| quikridr.MPREM | #26 | **No** |
| MPOLICY padding | #25 | **Preserve** |

---

## 5. Open Client Questions

1. **OBQ-78-1 (Tier 2 pairing):** For multi-PE policies where payout count ≠ payee count, is primary-PE-on-all-rows + audit tag acceptable for UAT, or should Tier 2 remain held?
   - *Planning default per SD-78-3:* emit with primary PE + tag (recover dollars; flag for review).

2. **OBQ-78-2 (check number):** When `CONTROL_NUMBER` is blank/non-numeric, confirm reuse of Phase 10A synthetic check convention vs leave blank.
   - *Planning default:* match Phase 10A existing behavior for emitted payments.

3. **OBQ-78-3:** Should recovered payments for `CLAIMSTAT=1` headers also trigger settling the header in the same change?
   - *Planning default per SD-78-7:* **No** — separate companion issue unless client folds it in at Risk.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + 10-char MPOLICY padding (#25) |
| Dates | YYYYMMDD from PACTG EFFECTIVE_DATE |
| Money | Same decimal emit as current `quikclmp` |
| Blanks / zeros | Do not invent TIN/bank; address from Rel when present |
| Estate name | `ESTATE OF ` + insured display name (trim length to field) |
| Audit | Reports CSV with `recovery_tier` ∈ {1,2,3} |

---

## 7. Memo / Text / Special Handling

- Do not overwrite `quikclms.MEMOTEXT` unless Risk requires a short recovery tag; prefer **Reports** audit lineage.
- Optional: append `ISSUE78_TIER{n}` to payment-side audit only if an existing payment memo field is used by Phase 10A — otherwise keep audit off-table.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `Master_Crosswalk.csv` → QLA  
2. Apply `format_qladmin_mpolicy()` for CHARACTER(10)  
3. Only recover when QLA policy already has a `quikclms` row and zero `quikclmp` rows  
4. Orphan PACTG payouts with no claim header: **out of scope** (log only)

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| Claim policies missing payments | 744 | Output join |
| Recoverable (live PACTG payout) | 729 | 2026-07-17 scan |
| Expected new `quikclmp` rows | ~932 | Payout txn grain |
| Tier 1 policies (single PE) | 646 | Rel distinct NAME_ID |
| Tier 2 policies (multi PE) | 85 | Rel |
| Tier 3 policies (no PE) | 13 | Rel |
| No payout evidence (leave missing) | 15 | 744 − 729 |
| Existing `quikclmp` rows (unchanged) | 5,219 | Output |

---

## 10. Sample Trace (5 policies)

| Policy (QLA) | LifePRO | Before | After (proposed) | Status |
|--------------|---------|--------|------------------|--------|
| `010150740C` | 9010150740 | Claim header; 0 payments; MPAID 3213.59 | ≥1 `quikclmp` from PACTG; Tier 1 PE name/addr | Ready |
| `010154425C` | 9010154425 | Disbursement header; 0 payments | Recover if PACTG payout exists; Tier 1 | Ready |
| `010331157C` | 9010331157 | Death; MPAID 19636.31; 0 payments | Recover; Tier 2 multi-PE rule | Review tag |
| `015000341C` | 9015000341 | Death; no PE | Recover; Tier 3 B1/estate | Review tag |
| `010469081C` | 9010469081 | Surrender CLAIMSTAT=1; no PE | Recover payment only; header stay 1 | Companion OBQ |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Tier 2 wrong payee on split checks | Medium | Audit tag; optional hold Tier 2 at Risk |
| Estate fallback inaccurate for assignee/funeral home | Medium | Prefer B1; spot-check Tier 3 in UAT |
| Dollar mismatch vs `quikclms.MPAID` | Medium | Report delta; do not force header rewrite this issue |
| Re-opening Phase 17 governance holds incorrectly | Medium | Explicit recovery path for **missing-row** population only |
| Double-emit if rebatch run twice | Low | Idempotent: only when payment count == 0 |
| GOVT_NAME forever blank | Low | Confirmed Rel is payee authority |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes — PACTG + Relationship |
| Field definitions confirmed | Yes — quikclmp schema + Help patterns |
| Client scope clear | Yes — SD-78-* locked |
| Example policies available | Yes — §10 |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #78.

Read AI_Agents/Risk_Agent.md and AI_Agents/Templates/Risk_Report_Template.md.
Also read:
- Issue_Log_Items/Issue_78/Issue_78_Intake_Summary.md
- Issue_Log_Items/Issue_78/Issue_78_Scope_Decisions.md
- Issue_Log_Items/Issue_78/Issue_78_Planning_Report.md
- Issue_Log_Items/Issue_78/Issue_78_Dependency_Gate.md

Model: Cursor Grok 4.5 (locked). Do not code.

Produce before/after impact analysis for recovering ~932 quikclmp rows
(~729 policies, ~$7.37M) under SD-78 Tier 1/2/3 payee rules.
Quantify Tier 2 / Tier 3 residual risk and go/no-go for Development.
Preserve #25 MPOLICY and #26 MPREM.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Add surgical recovery hook (claims emit / post-governance) that:
   - selects `quikclms` policies with zero `quikclmp`
   - loads live PACTG payouts for those policies
   - resolves payee via Tier 1 → 2 → 3 (SD-78-2..4)
   - appends `quikclmp` rows using existing schema emit helpers
2. Write `QLA_Migration/Reports/issue78_quikclmp_recovery_audit.csv`
3. Version bump both `app.py` copies (next APP_VERSION after current)
4. Validation script: `QLA_Migration/_validate_issue78_quikclmp_recovery.py`
   - recovered policy count; non-candidate unchanged
   - tier distribution; dollar totals; sample policies in §10
5. On validator PASS: copy modified `quikclmp.csv` (and `quikclms` only if touched) to `Output/Test_Validation/`

---

## Appendix

- Related: Claims items #15, #16, #19; Phase 8 / 10A / 17  
- Companion open items (not this issue): ORIGSTTUS, 494 Pending→Settled, CAUSE defaults  
- References: `claims_analysis/phase2_semantic_catalog/catalog/Claims_Transaction_Code_Catalog.csv`  
- No diagnostic script required beyond Planning research already performed in session
