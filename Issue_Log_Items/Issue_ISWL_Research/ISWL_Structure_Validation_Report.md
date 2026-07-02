# ISWL Structure Validation Report

**Date:** 2026-06-28  
**Purpose:** Compare dimensional grain across LifePRO ISWL rate sources and expected QLAdmin target tables  
**Scope:** Research only — no mapping implementation

---

## 1. ISWL plan universe

All analyses filter to eight LifePRO coverage IDs mapped to QLA MPLAN codes (see discovery report §2.1).

**Policy fleet:** 2,268 ISWL policies (Issue #21D).

---

## 2. Source grain summary

### 2.1 Rate_Table_Extract (issue-age × duration family)

**Total file rows:** 1,128,985  
**ISWL rows:** 251,950

| Dimension | CV | NP | RV | Values observed (ISWL) |
|-----------|----|----|----|-----------------------|
| SEX | ✓ | ✓ | ✓ | F, M |
| BAND | ✓ | ✓ | ✓ | 1 only |
| UNDERWRITING_CLASS | ✓ | ✓ | ✓ | P, S |
| AGE (issue) | ✓ | ✓ | ✓ | 0–99 (plan-dependent subset) |
| DURATION | ✓ | ✓ | ✓ | 1–95 (CV); 1–100 (NP/RV) |
| Effective date | ✗ | ✗ | ✗ | Not in extract — loader must default EFFDATE |
| State / country | ✗ | ✗ | ✗ | Defaults ISSCNTRY=0000, ISSUEST=00 |

**File level:** Table-level actuarial factors keyed by coverage ID (plan form).

**Maps to QLAdmin WL family:** QuikCvs / QuikNps / QuikTvs — **issue age + policy year** grid (VARGP=2 per Issue #21D population `QUikPLAN_VARGP=4` on sample policies — *variation code 4 = not-on-file* may require QuikPlan flag update separate from this research).

---

### 2.2 PAAGERAT (attained-age family)

**Total file rows:** 24,425  
**ISWL rows:** 3,287

| Dimension | NC | U6 | BP | NF | Values observed (ISWL) |
|-----------|----|----|----|----|-------------------------|
| SEX | ✓ | ✓ | ✓ | ✓ | F, M |
| BAND | ✓ | ✓ | ✓ | ✓ | 1 only |
| UWCLS | ✓ | ✓ | ✓ | ✓ | P, S |
| Attained age | ✓ (SEQ) | ✓ (SEQ) | ✓ (SEQ) | ✓ (SEQ) | SEQ ranges vary by plan/type (e.g. NC 2–76 on 658 CEN I) |
| Duration | ✗ | ✗ | ✗ | ✗ | Not present — attained-age-only |
| Effective date | ✗ | ✗ | ✗ | ✗ | Not in extract |

**File level:** Table-level; segment ID = COVERAGE_ID (requires PCOVRSGT for resolution).

**Hypothesized QLA targets:** QUIKCOI (NC), QUIKGCOI (U6), QUIKGPS (BP) — **unconfirmed**.

---

### 2.3 iswl-prem.csv (PFSA matrix)

| Dimension | Present | Values |
|-----------|---------|--------|
| Gender + UW | ✓ (row prefix) | 10 segments: MSP B2, FJV B2, MRN B1, … |
| Band | ✓ (B1/B2 in prefix) | B1, B2 |
| Duration | ✓ (row suffix) | 1–121 |
| Issue age | ✓ (column headers) | -2 through 99 |
| MPLAN / COVERAGE_ID | ✗ | Not embedded — **mapping unknown** |
| Effective date | ✗ | Not present |

**File level:** Single matrix file; not keyed to individual MPLAN codes.

---

### 2.4 CSO crosswalk (plan assumptions)

| Dimension | Present | Values |
|-----------|---------|--------|
| Plan | ✓ | 8 ISWL MPLAN rows |
| Guaranteed interest | ✓ | 4.50% all plans |
| Mortality / ETI | ✓ | Gender × UW class codes |
| Effective date | ✗ | Not present |

**File level:** Plan-level only — no age/duration grid.

---

## 3. Per-plan data availability matrix

| MPLAN | Coverage | Rate_Table CV | Rate_Table NP/RV | PAAGERAT NC | PAAGERAT U6 | PAAGERAT BP |
|-------|----------|---------------|------------------|-------------|-------------|-------------|
| 1658C1 | 658 CEN I | ✓ 18,124 | ✓ | ✓ 294 | ✓ 400 | ✓ 294 |
| 1658CS | 658 CEN SD | ✓ 9,113 | ✓ | ✗ | ✗ | ✓ 150 |
| 1659C2 | 659 CEN II | ✓ 9,678 | ✓ | ✓ 330 | ✓ 400 | ✓ 330 |
| 1659CR | 659 CEN SR | ✓ 9,678 | ✓ | ✗ | ✗ | ✓ 172 |
| 1659CS | 659 CEN SD | ✓ 9,288 | ✓ | ✗ | ✗ | ✓ 152 |
| 1659SR | 659 SR GD | ✓ 9,700 | ✓ | ✗ | ✗ | ✗ |
| 1669SR | 669 SR GD | ✓ 2,340 | ✗ | ✗ | ✗ | ✗ |
| 1679CS | 679 CEN SD | ✓ 4,350 | ✗ | ✓ 66 | ✗ | ✓ 66 |

**Finding:** CV coverage is universal across all eight plans. COI/GCOI/GP attained-age tables are **sparse** for senior/grandfathered variants.

---

## 4. Cross-table dimensional consistency

### 4.1 Segmentation tuple (SEX × BAND × UW)

| Source family | SEX | BAND | UW classes | Consistent across ISWL? |
|---------------|-----|------|------------|-------------------------|
| Rate_Table CV/NP/RV | F, M | 1 | P, S | **Yes** — uniform |
| PAAGERAT NC/U6/BP | F, M | 1 | P, S | **Yes** where present |
| iswl-prem.csv | M/F via prefix | B1, B2 | 10 PFSA UW codes | **No** — richer segmentation than LifePRO P/S |

**Validation result:** LifePRO Rate_Table and PAAGERAT share **F/M + Band 1 + P/S** when both exist. iswl-prem uses a **different UW vocabulary** (MSP, MRN, FJV, etc.) — not directly joinable without a crosswalk.

---

### 4.2 Age / duration axis

| QLA target | Expected axis (hypothesis) | LifePRO source axis | Match? |
|------------|---------------------------|---------------------|--------|
| QUIKCVS | Issue age × duration (QuikCvs grid) | Rate_Table CV: AGE × DURATION | **Yes** |
| QUIKGPS | Issue age × duration OR attained age (VARGP-dependent) | No PR; BP is attained-age SEQ | **Unclear** — axis mismatch if BP=GP |
| QUIKCOI | Attained age (typical UL) | PAAGERAT NC: SEQ | **Likely** if NC=COI |
| QUIKGCOI | Attained age | PAAGERAT U6: SEQ | **Likely** if U6=GCOI |
| QUIKUINT | Plan and/or policy level rates | CSO plan / PPBEN policy | **N/A** — not a factor grid |
| QUIKISSC | Duration or policy year | Not found | **N/A** |

**Validation result:** **CV is structurally aligned** with the existing WL QuikCvs loader. COI/GCOI/GP sources use **attained-age PAAGERAT** which differs from CV's **issue-age × duration** grain — QLAdmin may require different `VARGP`/`VARCV` variation codes per table family.

---

### 4.3 Effective date and state variation

| Dimension | Consistent across COI, GCOI, SC, GP, CV? |
|-----------|------------------------------------------|
| EFFDATE | **Yes** — absent in all LifePRO extracts reviewed; all would use same loader default until business supplies filing dates |
| ISSCNTRY / ISSUEST | **Yes** — absent; default 0000/00 for all families |
| Smoker status | **Partial** — LifePRO uses UWCLS P/S (preferred/smoker); iswl-prem uses SP/PN/RN/RT codes — different encoding |

---

## 5. Comparison to QLAdmin target table expectations

### Documented in repo (WL factor tables)

**QuikCvs / QuikGps grain (from `qla_core/rate_dbf_schema.py`):**

```
PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST + EFFDATE + AGE + CNTL
```

Factor columns: CV0–CV9 or GP0–GP9 (10 durations per CNTL page).

| Target | LifePRO best fit | Structural fit |
|--------|------------------|----------------|
| QUIKCVS | Rate_Table CV | **Strong** — requires long→grid pivot (existing R5 pipeline) |
| QUIKGPS | Rate_Table PR (missing) or PAAGERAT BP or iswl-prem | **Weak** — no PR; BP is attained-age; iswl-prem is custom matrix |

### Not documented in repo (UL tables)

| Target | Expected grain (industry typical) | LifePRO candidate | Structural fit |
|--------|-----------------------------------|-------------------|----------------|
| QUIKUINT | Plan-level rate rows + effective dates | CSO / PPBEN | **Unknown schema** |
| QUIKCOI | Attained age × gender × UW × band | PAAGERAT NC | **Plausible** — pending TYPE_CODE confirm |
| QUIKGCOI | Same as COI, guaranteed schedule | PAAGERAT U6 | **Plausible** — pending confirm |
| QUIKISSC | Duration or year schedule | None found | **No fit** |

---

## 6. Uniformity verdict

| Question | Answer |
|----------|--------|
| Do COI, GCOI, surrender, GP, and CV use the same dimensions in LifePRO? | **No.** CV/NP/RV share issue-age×duration; NC/U6/BP share attained-age; iswl-prem uses yet another layout; surrender absent. |
| Are UW class and band consistent where tables coexist? | **Yes** for Rate_Table vs PAAGERAT (F/M, Band 1, P/S). **No** for iswl-prem vs LifePRO. |
| Does structure vary by product/plan? | **Yes** — senior/grandfathered plans lack PAAGERAT entirely; 659 CEN II has extra excluded TYPE_CODEs. |
| Does structure vary by effective date? | **Not observable** — no effective date dimension in extracts. |

---

## 7. Implications for future mapping (research notes only)

1. **QUIKCVS** can reuse the proven Rate_Table → QuikCvs transform with ISWL MPLAN crosswalk.
2. **QUIKCOI / QUIKGCOI / QUIKGPS** likely need a **separate PAAGERAT loader** (or extension) — not the current WL TYPE_TO_TABLE map which excludes NC/U6/BP.
3. **Dimensional mismatch** between CV (issue+duration) and COI (attained age) is **expected** for UL/ISWL products — not necessarily an error, but QuikPlan variation flags must align.
4. **Do not merge** iswl-prem segments with LifePRO P/S without an approved crosswalk (PFSA column_legend_DRAFT is UL/term-oriented and unconfirmed for ISWL MPLAN codes).

---

## 8. Validation artifacts

- Row counts and TYPE_CODE inventory: `tools/research/iswl_source_discovery.py`
- R3 routing proof for CV: `plan_analysis/phase_r3_rate_reconciliation/rate_reconciliation_report.csv` (1658C1 samples)
- Segment crosswalk draft: `PFSA Rates/reconciliation/column_legend_DRAFT.csv` (iswl row note only — not validated)

---

*End of report*
