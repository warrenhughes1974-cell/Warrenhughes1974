# Issue #84 — Intake Summary

**Issue:** #84 — `quikclms` money-field decomposition (Policy-book parity)  
**Framework stage:** Intake Agent (G0)  
**Status:** Intake Complete → Planning (Pre-Risk Auto-Chain)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (Warren)  
**Priority:** High (claims UAT / QLAdmin Claims screen money panel)  
**Code changes:** None  

**ID note:** User requested Issue #80; that ID is already **Closed** (CSO Valuation Setup → QuikPlCv/QuikPlTv). This claims money-field issue is opened as **#84**.

---

## 1. Client / business symptom (verbatim + normalized)

**Verbatim (normalized from 2026-07-17 QLAdmin screenshots + Policy-book comparison):**

QLAdmin Claims screens show `quikclms` header money fields (Net Payment, Amount Ins, Dividends, Loan, Net Benefits, Premium, Suspense, IntRate, Interest, Adjustments) that do not reconcile with payee rows and/or are not populated like the real Policy book.

**Normalized:**

Populate / re-derive `quikclms` component money fields from LifePRO claim accounting so header decomposition matches Policy-book conventions and reconciles with `quikclmp` payee amounts where applicable.

---

## 2. Example policies

### Real Policy-book authority examples (`docs/Policy/quikclms.dbf`)

| MPOLICY | MPAID | MFACE | DIVIDENDS | LOAN | NETDB | PREMIUM | MINTRATE | MINTAMT | ADJUST |
|---------|------:|------:|----------:|-----:|------:|--------:|---------:|--------:|-------:|
| `02505824W` | 10277.12 | 8000.00 | 1040.62 | -800.47 | 8240.15 | 0.00 | 4.5 | 2036.97 | — |
| `02601839W` | 2464.27 | 3900.00 | 89.85 | -1576.72 | 2413.13 | 39.71 | 4.5 | 4.21 | — |
| `02695880W` | 4399.69 | 5000.00 | 163.67 | -1300.78 | 3862.89 | 337.09 | 4.5 | 199.71 | — |
| `02393056W` | 7487.19 | 7771.00 | — | — | — | -301.00 | 4.5 | 70.60 | -53.41 |

### Converted / screenshot examples (`QLA_Migration/Output`)

| MPOLICY | Symptom | Header snapshot | Payee / note |
|---------|---------|-----------------|--------------|
| `010360289C` | Component zeros + header/payee mismatch | CLAIMSTAT 99; MPAID 3129.06; MFACE/DIVIDENDS/LOAN/PREMIUM/SUSPENSE/MINTRATE/MINTAMT/ADJUST = 0; NETDB 3129.06; PDDATE blank | `quikclmp` MAMOUNT **6139.10** (MCHECKNO 462071303106, BRET S SACORA) |
| `010391359C` | #78 append-only gap | MPAID 0.00; PDDATE blank | Payee MAMOUNT 1260.06 recovered; header not backfilled |
| `010150740C` | “Normal” composite pay | MFACE 1500.00; MPAID/payee 3213.59 | PACTG: death benefit 1500 + cash value 1704.05 + interest 9.54 = 3213.59 |

---

## 3. Suspected domain

**Claims — `quikclms` financial decomposition fields** (not CLAIMSTAT, not new payee invent).

| Layer | Path / table | Role |
|-------|--------------|------|
| Authority | `docs/Policy/quikclms.dbf` (7,691 rows) | Target population / formula pattern |
| Converted header | `QLA_Migration/Output/quikclms.csv` (5,624 rows) | Before-state |
| Converted payee | `QLA_Migration/Output/quikclmp.csv` (6,151 rows post-#78) | Reconciliation partner |
| Source accounting | `docs/claims_conversion_reference/PACTG_Accounting_Extract20260427.csv` | Component codes (e.g. 530 face/DB, 310 CV/fund, 110 interest, 94 payment) |
| Derivation config | `claims_analysis/config/quikclms_derivation_rules.json` | Current NETDB/MPAID/MINTAMT/MLOAN sources |
| Balancing config | `claims_analysis/config/claim_family_balancing_rules*.json` | Family formulas / PACTG code families |
| Prototype defaults | `claims_analysis/config/prototype_dbf_generation_rules.json` | DIVIDENDS/PREMIUM/SUSPENSE/MINTRATE currently **constant 0** |

### Fleet population gap (nonzero rates)

| Screen / field | Real Policy book | Our Output |
|----------------|-----------------:|-----------:|
| Net Payment / MPAID | 7,313 (95.1%) | 5,301 (94.3%) |
| Amount Ins / MFACE | 6,709 (87.2%) | 4,810 (85.5%) |
| Dividends / DIVIDENDS | 3,115 (40.5%) | **0 (0.0%)** |
| Loan / LOAN | 704 (9.2%) | 52 (0.9%) |
| Net Benefits / NETDB | 5,815 (75.6%) | 2,066 (36.7%) |
| Premium / PREMIUM | 1,276 (16.6%) | **0 (0.0%)** |
| Suspense / SUSPENSE | 146 (1.9%) | **0 (0.0%)** |
| IntRate / MINTRATE | 3,364 (43.7%) | **0 (0.0%)** |
| Interest / MINTAMT | 3,416 (44.4%) | 508 (9.0%) |
| Adjustments / ADJUST | 1 | **0** |

Schema parity: columns match Policy DBF except known `ORIGSTTUS` vs `ORIGSTATUS` naming (out of scope here).

---

## 4. In scope / out of scope (first pass)

### In scope

- Investigate and plan derivation of `quikclms` money components toward Policy-book parity:
  - MPAID, MFACE, DIVIDENDS, LOAN, NETDB, PREMIUM, SUSPENSE, MINTRATE, MINTAMT, ADJUST
  - Related date fields only if required for money reconciliation (e.g. PDDATE when header MPAID backfilled)
- Header ↔ payee reconciliation analysis (MPAID vs sum(`quikclmp.MAMOUNT`))
- PACTG component → field mapping research (family-specific)
- Validation / audit design for before/after money fields
- Preserve #78 payments and #79 CLAIMSTAT outcomes

### Out of scope

- Changing `CLAIMSTAT` (Issue **#79**)
- Recovering new `quikclmp` payees (Issue **#78**)
- `quikmstr` / `quikridr` / rates / premiums / plan setup
- `ORIGSTATUS` / `ORIGSTTUS` rename or pre-death status carry-forward
- Production code / rulebook edits until G3 + Development approval
- Inventing money values without PACTG / Policy-book authority

---

## 5. Related issues

| Item | Relationship |
|------|----------------|
| **#78** | Append-only `quikclmp` recovery; did **not** backfill header MPAID/PDDATE |
| **#79** | CLAIMSTAT remap only; explicitly did **not** change money fields |
| **Claims Item 18** | Earlier death NETDB/MPAID/MFACE update for some rows; did **not** cover DIVIDENDS/PREMIUM/SUSPENSE/MINTRATE/ADJUST decomposition |
| **Item 16** | Unbalanced claims rebalance history — related residual risk |

---

## 6. Immediate blockers visible at intake

- Exact PACTG → QLAdmin component mapping not fully locked (prototype zeros + partial Item 18 coverage).
- Whether #78-recovered payments should force header MPAID/PDDATE backfill is a business decision (see Planning OBQs).
- No production blocker for documentation chain — sources and examples exist.

Development still blocked until G1 + G2 + G3 + explicit Development approval.

---

## Gate Criteria (G0)

- [x] Issue folder created (`Issue_Log_Items/Issue_84/`)
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes

**Recommended status:** Ready for Planning → Dependency Gate (auto-chain).
