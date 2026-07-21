# Issue #78 — Risk Review Report

**Issue:** #78 — Recover missing `quikclmp` claim payments with approved payee fallback  
**Framework stage:** Risk Agent (G3)  
**Status:** **Conditional Go → Ready for Development** (pending explicit user approval)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Status note:** Risk analysis only — no production code changes.  
**Evidence:** `evidence/issue78_risk_recovery_simulation.csv` · `scripts/risk_review_issue78_quikclmp_recovery.py`  
**Scope:** `Issue_78_Scope_Decisions.md` (SD-78-1 … SD-78-10)

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Blast radius is quantified; sources and payee tiers are locked; residual risk is concentrated in Tier 2 mismatched pairing and header dollar drift (headers stay unchanged by design).

| Factor | Assessment |
|--------|------------|
| Scope | Append-only `quikclmp` for policies with **zero** payments today |
| Impact | **729** policies / **932** new payment rows / **$7,374,674.62** |
| Tier mix | **641** Tier 1 · **85** Tier 2 · **3** Tier 3 |
| Tier 2 residual | **37** pairable 1:1; **48** use primary-PE-on-all + audit (SD-78-3) |
| Existing payments | **1,521** policies / **5,219** rows **untouched** |
| No payout evidence | **15** policies remain without payments (correct) |
| Headers | `quikclms` **not** rewritten (SD-78-7) — including **408** still `CLAIMSTAT=1` |
| #25 / #26 | Untouched |

Development may proceed after user says **Approved for Development** and switches to **Composer 2.5**, under the locks in §5 and §11.

---

## 1. Current vs Proposed Mapping

| Field / row set | Current | Proposed | Change? |
|-----------------|---------|----------|---------|
| `quikclmp` for 729 recoverable missing-pay policies | Absent | New rows from PACTG payouts + Tier 1/2/3 payee | **Yes** (append) |
| `quikclmp` for 1,521 policies that already have payments | Present | Unchanged | **No** |
| `quikclms` CLAIMSTAT / MPAID / ORIGSTTUS / CAUSE | As today | Unchanged | **No** |
| Payee on recovered rows | N/A | PE single / PE multi / B1·B2·estate | **Yes** (new) |
| Amounts / dates | N/A | PACTG `TRANS_AMOUNT` / `EFFECTIVE_DATE` | **Yes** (new) |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| MPOLICY padding (#25) | **No** (reuse formatter only) |
| quikridr.MPREM / quikmstr.MMODPREM (#26) | **No** |
| Existing `quikclmp` rows | **No** |
| `quikclms` lifecycle / cause / ORIGSTTUS | **No** |
| Rates / plan / master policy fields | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `claims_analysis/phase10a_quikclmp_derivation/` | Existing payment emit conventions |
| `claims_analysis/phase8_payee_distribution/` | PE / beneficiary patterns |
| `claims_analysis/phase17_*/deferred_governance_payments.csv` | Prior orphan hold precedent |
| `QLA_Migration/Configs/Sync_Rulebook_quikclmp.csv` | Field defaults |
| `qla_core/claims_emit_enhancements.py` | Post-emit MSEQ / CLAIMNUM |
| `QLA_Migration/app.py` claims orchestration | Integration point for recovery hook |

---

## 4. Population Analysis (simulated on current Output)

| Metric | Count |
|--------|------:|
| `quikclms` policies | 5,624 |
| Policies with ≥1 `quikclmp` today | 1,521 |
| Policies with 0 `quikclmp` | 744 |
| Recoverable (live non-reversed PACTG payout) | **729** |
| New payment rows expected | **932** |
| Dollar total recovered | **$7,374,674.62** |
| No payout evidence (stay missing) | 15 |
| Existing payment rows unchanged | 5,219 |

### Tier breakdown (recoverable only)

| Tier | Policies | Payment rows | Dollars | Payee rule |
|------|--------:|-------------:|--------:|------------|
| **1** Single PE | 641 | 708 | $5,893,716.97 | PE name + address |
| **2** Multi PE | 85 | 221 | $1,363,145.97 | Pair 1:1 if counts match; else primary PE + audit |
| **3** No PE | 3 | 3 | $117,811.68 | B2 / estate of insured |
| **Total** | 729 | 932 | $7,374,674.62 | |

### Tier 2 pairing quality

| Outcome | Policies | Assessment |
|---------|--------:|------------|
| `PAIR_OK` (payout count = PE count) | 37 | Low residual payee risk |
| `PRIMARY_PE_ALL` (counts differ) | 48 | Medium residual — audit required; dollars still correct |

### Claim status on recoverable headers (unchanged)

| CLAIMSTAT | Policies | Note |
|-----------|--------:|------|
| 1 (Pending) | 408 | Payments may appear under Pending headers — companion issue if client wants settle |
| 99 | 171 | Disbursement / other |
| 3 (Settled) | 150 | Cleanest UAT story |

### Header `MPAID` vs recovered payout dollars

| Metric | Count / value |
|--------|---------------|
| Exact match (\|Δ\| < $0.01) | 259 / 729 |
| Header `MPAID=0` but payout > 0 | 169 |
| Median \|Δ\| | $21.60 |
| P90 \|Δ\| | ~$5,122 |
| Max \|Δ\| | $67,035.20 |

**Risk lock:** Do **not** rewrite `quikclms.MPAID` under #78. Report deltas in the recovery audit. Header reconciliation is a separate decision.

---

## 5. Fallback Recommendation

| Option | Rows / policies | Assessment |
|--------|----------------:|------------|
| **A. Emit all Tier 1+2+3 per SD-78 (recommended)** | 932 / 729 | Matches user approval; audit Tier 2/3 |
| B. Emit Tier 1 only; hold Tier 2+3 | 708 / 641 | Safer payee; leaves $1.48M + 88 policies out |
| C. Emit Tier 1 + Tier 2 `PAIR_OK` only | ~ (641+37) policies | Middle ground; still holds 48+3 |
| D. Also settle `CLAIMSTAT=1` headers | 408 headers | **Reject for #78** — SD-78-7; open companion |
| E. Do nothing | 0 | Reject — $7.37M gap remains |

**Recommended:** **Option A** with mandatory `Reports/issue78_quikclmp_recovery_audit.csv` including `tier`, `pair_note`, `payee_source`, payout vs header `MPAID` delta.

**OBQ locks for Development:**

| OBQ | Lock |
|-----|------|
| OBQ-78-1 Tier 2 mismatch | Emit with primary PE + `PRIMARY_PE_ALL` audit tag (SD-78-3) |
| OBQ-78-2 Check number | Prefer `CONTROL_NUMBER`; else Phase 10A convention |
| OBQ-78-3 Settle Pending headers | **Out of scope** this issue |

---

## 6. Trace Policies

| Policy | Tier | Before | Proposed | Pass? |
|--------|------|--------|----------|-------|
| `010150740C` | 1 | Claim settled; MPAID 3213.59; **0** payments | 1 payment $3,213.59; single PE; Δ=$0 | **Yes** |
| `010154425C` | 1 | CLAIMSTAT 99; MPAID 0; **0** payments | 1 payment $2,107.95; single PE; header MPAID stays 0 | **Yes** (header drift expected) |
| `010331157C` | 2 | Settled; MPAID 19636.31; **0** payments | 5 payments totaling $19,446.62; `PAIR_OK` (5 PE); Δ≈−$189.69 | **Yes** (audit Δ) |
| `015000341C` | 3 | Settled; no PE | 1 payment $5,201.97; payee B2; Δ≈−$15.67 | **Yes** (Tier 3 review) |
| `010469081C` | — | CLAIMSTAT 1; no PE | **No recovery** (no live PACTG payout in codes) | **Expected** |

---

## 7. Top 10 Largest Recovered Amounts

| Policy | Tier | Recovered $ | CLAIMSTAT | Payee source |
|--------|------|------------:|-----------|--------------|
| `011136690C` | 1 | 119,795.38 | 3 | PE_SINGLE |
| `011198344C` | 2 | 105,244.48 | 3 | PE_MULTI_PAIR_OK |
| `011083028C` | 1 | 101,188.34 | 3 | PE_SINGLE |
| `011064372C` | 1 | 100,412.53 | 3 | PE_SINGLE |
| `010726104C` | 1 | 100,399.60 | 3 | PE_SINGLE |
| `011056407C` | 1 | 100,257.55 | 3 | PE_SINGLE |
| `011062307C` | 3 | 100,188.08 | 3 | ESTATE_IN |
| `010983828C` | 1 | 100,142.50 | 3 | PE_SINGLE |
| `011004587C` | 1 | 75,220.31 | 3 | PE_SINGLE |
| `010774484C` | 1 | 70,114.95 | 3 | PE_SINGLE |

---

## 8. Material Calculation Impact

- **Intentional:** Historical claim payments that were withheld by governance/orphan logic are restored with LifePRO accounting amounts and relationship payees.
- **Not accidental drift:** Existing 5,219 payment rows are not recalculated.
- **Known residual:** Header `MPAID` will often disagree with sum of recovered payments (470 policies with material Δ). That is **display/header consistency**, not inventing money — money comes from PACTG.
- **UAT optics:** ~408 recovered policies still show `CLAIMSTAT=1`. Payments under Pending is allowable under SD-78-7 but should be called out in UAT notes.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserve** — use existing formatter; no key redesign |
| Issue #26 MPREM / MMODPREM | **N/A / untouched** |
| Claims #15/#16/#19 prior promotions | Do not reverse; only fill **zero-payment** gap |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Trace: `010150740C` (T1 exact $), `010331157C` (T2 PAIR_OK), `015000341C` (T3), `010154425C` (T1 header MPAID=0)
- [ ] `010469081C` still has **0** payments (no false recovery)
- [ ] Existing payment policies: row count and sample amounts **unchanged** (1,521 policies)
- [ ] New fleet: `quikclmp` row count ≈ 5,219 + 932
- [ ] Audit CSV: 729 policies; tier counts 641 / 85 / 3
- [ ] No `quikclms` CLAIMSTAT / MPAID mass rewrite
- [ ] No `quikmstr` / `quikridr` / rates changes
- [ ] MPOLICY length/padding still CHARACTER(10) on new rows
- [ ] Spot-check 5 of 48 `PRIMARY_PE_ALL` + all 3 Tier 3 in UAT

---

## 11. Recommended Development Agent Task

1. Surgical recovery path (claims emit / post-governance) that selects `quikclms` policies with **zero** `quikclmp`, loads live PACTG payouts (codes 90/92/94/567/1900, non-reversed), resolves payee Tier 1→2→3 per SD-78-2..4, appends `quikclmp` rows via existing emit helpers.
2. Idempotent: never append if policy already has ≥1 payment row.
3. Write `QLA_Migration/Reports/issue78_quikclmp_recovery_audit.csv` (tier, pair_note, payee_source, amounts, header MPAID delta).
4. Do **NOT** change: existing `quikclmp` rows; `quikclms` CLAIMSTAT/MPAID/ORIGSTTUS/CAUSE; `quikmstr`/`quikridr`/rates; #25/#26 logic.
5. Version bump both `app.py` copies: current `v57.97` → **`v57.98`**.
6. Validation script: `QLA_Migration/_validate_issue78_quikclmp_recovery.py` covering §10 checklist.
7. On PASS: copy modified `quikclmp.csv` only to `Output/Test_Validation/`.

---

## Appendix

- Simulation CSV: `Issue_Log_Items/Issue_78/evidence/issue78_risk_recovery_simulation.csv`
- Simulation script: `Issue_Log_Items/Issue_78/scripts/risk_review_issue78_quikclmp_recovery.py`
- Companion (not #78): Pending→Settled (408), ORIGSTTUS, CAUSE defaults, header MPAID rebalance
