# Issue #84 — Planning Report

**Issue:** #84 — `quikclms` money-field decomposition (Policy-book parity)  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning Complete → Dependency Gate  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None  
**Scope authority:** `Issue_84_Scope_Decisions.md` (SD-84-1 … SD-84-12)

**ID note:** #80 Closed (CSO Valuation Setup). Claims money fields tracked as **#84**.

---

## 1. Executive Finding

QLAdmin Claims money panels are under-populated versus real `docs/Policy/quikclms.dbf`: DIVIDENDS / PREMIUM / SUSPENSE / MINTRATE are **0%** nonzero in our emit (prototype constants), while LOAN / NETDB / MINTAMT are thinly filled. Screenshots also show header↔payee breaks (`010360289C` MPAID 3129.06 vs payee 6139.10; `010391359C` MPAID 0 after #78 recovery). Recommended direction: map PACTG components into Policy-book fields by claim family, then reconcile header MPAID/PDDATE to existing `quikclmp` where needed — **without** changing CLAIMSTAT (#79) or inventing payees (#78). **Go for Dependency Gate / Risk.**

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source / authority | File pattern | In package? | Notes |
|--------------------|--------------|:-----------:|-------|
| Policy-book authority | `docs/Policy/quikclms.dbf` | Yes | 7,691 rows; component population target |
| Converted headers | `QLA_Migration/Output/quikclms.csv` | Yes | 5,624 rows |
| Converted payments | `QLA_Migration/Output/quikclmp.csv` | Yes | 6,151 rows post-#78 |
| PACTG accounting | `docs/claims_conversion_reference/PACTG_Accounting_Extract20260427.csv` | Yes | Component codes for decomposition |
| Derivation rules | `claims_analysis/config/quikclms_derivation_rules.json` | Yes | NETDB/MPAID/MINTAMT/MLOAN sources today |
| Balancing rules | `claims_analysis/config/claim_family_balancing_rules*.json` | Yes | Family formulas + coded components |
| Prototype defaults | `claims_analysis/config/prototype_dbf_generation_rules.json` | Yes | DIVIDENDS/PREMIUM/SUSPENSE/MINTRATE = constant 0 |

### Observed / candidate PACTG code signals

| Code (examples) | Observed role (intake evidence) | Likely QLAdmin field(s) |
|-----------------|---------------------------------|-------------------------|
| 530 / 0530 / 0519 | Face / death benefit | MFACE (gross), contributes to NETDB |
| 310 | Cash value / fund | May fold into MPAID / NETDB composite (see `010150740C`) |
| 110 / 0630 | Interest | MINTAMT |
| 94 / 0094 / 90 / 567 / 1900 | Payment / check | MPAID / `quikclmp.MAMOUNT` |
| Loan offsets (0411/0412 in balancing JSON) | Loan principal / interest | LOAN (often negative in Policy book) |
| TBD | Dividend / premium / suspense / adjustment | DIVIDENDS, PREMIUM, SUSPENSE, ADJUST |

Balancing JSON uses zero-padded family codes; inspected claim used short codes — Risk must normalize code width.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Screen label | Current conversion gap |
|-------|-------|--------------|------------------------|
| quikclms | MPAID | Net Payment | Mostly populated; gaps after #78; some ≠ payee sum |
| quikclms | MFACE | Amount Ins | Partial; Policy book denser |
| quikclms | DIVIDENDS | Dividends | Always 0 (constant) |
| quikclms | LOAN | Loan | Sparse vs book |
| quikclms | NETDB | Net Benefits | Under-populated (~37% vs ~76%) |
| quikclms | PREMIUM | Premium | Always 0 (constant) |
| quikclms | SUSPENSE | Suspense | Always 0 (constant) |
| quikclms | MINTRATE | IntRate | Always 0 (constant); book often 4.5 |
| quikclms | MINTAMT | Interest | Sparse (~9% vs ~44%) |
| quikclms | ADJUST | Adjustments | Always 0 (book nearly always 0 too) |
| quikclms | PDDATE | Paid date | Blank on some recovered-payment headers |

**Repo integration points (Development later — do not code now):**

| Location | Role |
|----------|------|
| `claims_analysis/config/quikclms_derivation_rules.json` | Declared sources |
| `claims_analysis/config/claim_family_balancing_rules*.json` | Family formulas |
| Claims Item 18 post-emit path | Prior partial death money fix |
| `QLA_Migration/app.py` / claims emit enhancements | Likely surgical hook |

---

## 4. Required Source-to-Target Field Mapping (planning)

| Target | Proposed authority | Notes |
|--------|--------------------|-------|
| MFACE | PACTG gross/face codes (530/0530/0519 family) | Death Amount Ins; surrenders may use cash codes |
| DIVIDENDS | PACTG dividend component(s) — **map TBD** | Book ~40% nonzero; ours 0% |
| LOAN | Loan principal/interest offsets (often signed negative in book) | Align sign convention to Policy book |
| PREMIUM | Premium due / refund component — **map TBD** | Book can be negative (`02393056W`) |
| SUSPENSE | Suspense component — **map TBD** | Rare in book |
| MINTAMT | Interest codes (110 / 0630 family) | Expand beyond current sparse fill |
| MINTRATE | Policy/claim interest rate source — **map TBD** | Book frequently 4.5; not invent if source missing |
| ADJUST | Residual / adjustment component — **map TBD** | Near-zero fleet |
| NETDB | Family formula (gross ± components) per balancing rules / Policy book | Not always = MPAID (`010150740C` style) |
| MPAID | Sum of live payees **or** PACTG payout total | Prefer reconcile to `quikclmp` when rows exist |
| PDDATE | Latest / settlement payment date from payees or PACTG | Only when money backfill requires it |

### Fields that must remain unchanged this issue

| Target | Touch? |
|--------|--------|
| `CLAIMSTAT` (#79) | **No** |
| New `quikclmp` invent (#78) | **No** |
| `quikmstr` / `quikridr` / rates | **No** |
| MPOLICY padding (#25) | **Preserve** |
| MPREM (#26) | **No** |

---

## 5. Open Client / Data Questions

1. **OBQ-84-1 — Exact PACTG → field map:** Confirm authoritative code lists for DIVIDENDS, PREMIUM, SUSPENSE, ADJUST, and MINTRATE (and zero-pad vs short codes).  
   - *Planning default:* Derive from Policy-book × PACTG joins on shared claim keys where possible; use balancing JSON as death/surrender baseline; leave blank/zero when no source evidence.

2. **OBQ-84-2 — #78 header backfill:** When recovered payees exist and header MPAID=0 / PDDATE blank, should Development set MPAID = sum(`quikclmp.MAMOUNT`) and PDDATE from payment date(s)?  
   - *Planning default:* **Yes** for headers that already have payee rows (no new payees) — reconciles screenshot defect without expanding #78.

3. **OBQ-84-3 — Family formula target:** Must every claim family reproduce Policy-book arithmetic exactly, or is “best-effort components + MPAID=payee total” enough for UAT?  
   - *Planning default:* Match Policy-book formulas **by claim family** where PACTG evidence supports it; document residual unbalanced rows rather than inventing.

4. **OBQ-84-4 — MINTRATE without source:** If no rate exists on PACTG/policy, leave 0 or default 4.5 from book mode?  
   - *Planning default:* **Leave 0** unless a LifePRO rate field is proven for that claim.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Money fields | Numeric, 2 decimals, QLA existing emit format |
| LOAN sign | Prefer Policy-book convention (often negative for loan offsets) |
| MINTRATE | Numeric rate (e.g. 4.5), not percent string |
| Audit | mpolicy, claimnum, before/after each money field, source codes, recon_flag |
| Idempotent | Rewrite only when derived value differs beyond $0.01 |

---

## 7. Memo / Text / Special Handling

Do not rewrite MEMOTEXT for money fixes. Lineage/audit belongs in Reports CSVs. Do not change CLAIMSTAT tokens.

---

## 8. Policy Number Key Handling

No key changes. Join via existing MPOLICY (#25) + CLAIMNUM/MPHASE as currently emitted. PACTG joins use established LifePRO policy key → QLA MPOLICY path from claims pipeline.

---

## 9. Estimated Record Counts (impact preview)

| Metric | Count / rate | Basis |
|--------|-------------:|-------|
| quikclms rows | 5,624 | Output |
| DIVIDENDS candidates (if book-like) | ~40% of headers | Book rate; our current 0 |
| PREMIUM candidates | ~17% | Book rate |
| MINTRATE candidates | ~44% | Book rate |
| Known recon defects | ≥2 examples | `010360289C`, `010391359C` |
| Item 18 prior death money touch | ~518 | Predecessor; may overlap |

Exact Development impact TBD at Risk (quantify deltas before Go).

---

## 10. Sample Trace Plan

| Policy | What to prove |
|--------|----------------|
| `010360289C` | Decompose components; explain MPAID vs payee 6139.10; fix or document |
| `010391359C` | Header MPAID/PDDATE backfill to match recovered payee (OBQ-84-2 default) |
| `010150740C` | Preserve correct composite: MFACE 1500 + CV + interest → pay 3213.59 |
| Policy-book W samples | Optional cross-check formulas if same LifePRO lineage available |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Wrong PACTG code → wrong DIVIDENDS/PREMIUM | High | OBQ-84-1; validate vs Policy book samples |
| Overwriting correct MFACE with pay total | High | Keep Amount Ins ≠ Net Payment where book does |
| Touching CLAIMSTAT / payees accidentally | Medium | SD-84-5/6; regression locks |
| Item 18 double-apply / drift | Medium | Replace or gate Item 18 path surgically |
| MINTRATE invent 4.5 | Medium | OBQ-84-4 default leave 0 |
| Header/payee intentional multi-check split | Medium | Reconcile with tolerance + audit exceptions |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source / authority present | Yes — Policy DBF + PACTG + Output |
| Field definitions confirmed | Yes — schema parity + Help screen labels |
| Client scope clear | Yes — SD-84-* ; OBQs have planning defaults |
| Example policies available | Yes — screenshots + book samples |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #84.

Read AI_Agents/Risk_Agent.md and Templates/Risk_Report_Template.md.
Also read Issue_84_Intake_Summary.md, Issue_84_Scope_Decisions.md,
Issue_84_Planning_Report.md, Issue_84_Dependency_Gate.md.

Model: Cursor Grok 4.5. Do not code.

Quantify money-field impact vs Policy-book fill rates; simulate header
MPAID/PDDATE backfill for #78-recovered payees; preserve CLAIMSTAT (#79)
and quikclmp invent (#78). Go/No-Go for Development.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Surgical derivation of `quikclms` money components from PACTG by claim family (extend beyond Item 18).
2. Optional header MPAID/PDDATE reconcile to existing `quikclmp` (OBQ-84-2 default).
3. Do not change CLAIMSTAT; do not invent payees.
4. Write `Reports/issue84_money_field_audit.csv` (and recon exceptions).
5. Version bump both `app.py` copies.
6. Validator: population rates, sample traces, #78/#79/#25/#26 guards, non-candidate tables unchanged.
7. On PASS: copy modified `quikclms.csv` to `Output/Test_Validation/`.

---

## Appendix

- Related: #78, #79, Claims Item 18, Item 16 unbalanced residuals  
- Authority: Policy `quikclms.dbf` + PACTG extract 20260427  
- Config: `quikclms_derivation_rules.json`, `claim_family_balancing_rules*.json`, `prototype_dbf_generation_rules.json`
