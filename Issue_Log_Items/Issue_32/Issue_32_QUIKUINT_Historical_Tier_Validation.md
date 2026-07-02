# Issue #32 — QUIKUINT Historical Tier Validation

**Issue:** #32 — ISWL Phase 5 QUIKUINT  
**Date:** 2026-06-30  
**Mode:** Planning validation only — no code changes  
**Sources:** `PDINT_DeclaredInterestRates_Extract_20260629.csv`, `PDINTTBL_DeclaredInterestRates_Extract_20260629.csv`

---

## Executive finding

**Rule 0 and Rule 3 are not duplicate representations.** They are **parallel PDINT rule headers** under the same `CENII / A1` identity with **different rate schedules** and **partially overlapping effective periods**.

**Filtering to DINT_RULE=3 only would violate the SME instruction** to load all historical interest rates, because Rule 0 contributes a unique tier at **MEFFDATE=19990101 @ 5.00000** that Rule 3 does not contain.

**Revised PR-5 approach:** **Union merge** — emit all **unique START_DATE** tiers across both Rule 0 and Rule 3, with tie-break at duplicate START_DATE (see §4).

---

## A. DINT_RULE comparison

### PDINT headers (CENII / A1)

| Field | DINT_RULE 0 | DINT_RULE 3 |
|-------|-------------|-------------|
| IDENT | CENII | CENII |
| TYPE_CODE | A1 | A1 |
| EFF_DATE | **20030813** | **19800101** |
| LOW_DATE / HIGH_DATE | 19800101 – 20991231 | 19800101 – 20991231 |
| MULTIPLIER | 1.000 | 1.000 |
| MOD metadata | (blank coder) | MDB1, mod 20031011 |

**Interpretation:** Rule 3 is the **original** declared-interest rule (EFF 1980). Rule 0 is a **later restatement** (EFF 2003-08-13) with a revised tier schedule. Same IDENT+TYPE, different DINT_RULE = different business rule variant — not duplicate rows.

### PDINTTBL tier comparison

| DINT_RULE | IDX | START_DATE | END_DATE | DECLARED_RATE |
|-----------|-----|------------|----------|---------------|
| **0** | 1 | 19800101 | 19981231 | **7.00000** |
| **0** | 2 | 19990101 | 20011231 | **5.00000** |
| **0** | 3 | 20020101 | 20991231 | **4.50000** |
| **3** | 1 | 19800101 | 19881231 | **11.00000** |
| **3** | 2 | 19890101 | 20011231 | **9.00000** |
| **3** | 3 | 20020101 | 20991231 | **4.50000** |

### Side-by-side START_DATE analysis

| START_DATE | Rule 0 | Rule 3 | Same rate? |
|------------|--------|--------|------------|
| 19800101 | 7.00000 (→19981231) | 11.00000 (→19881231) | **No — conflict** |
| 19890101 | — | 9.00000 (→20011231) | Rule 3 only |
| 19990101 | 5.00000 (→20011231) | — | Rule 0 only |
| 20020101 | 4.50000 (→20991231) | 4.50000 (→20991231) | **Yes — identical** |

**Period overlap note:** Rule 3 tier 2 (19890101–20011231 @ 9%) and Rule 0 tier 2 (19990101–20011231 @ 5%) overlap in calendar time but start on **different START_DATEs**. Both are distinct historical effective-date rows in LifePRO.

---

## B. Duplicate analysis

| Emit mode | Rows/MPLAN | Total (8 MPLANs) | Index-safe? | SME-compliant? |
|-----------|----------:|-----------------:|:-----------:|:--------------:|
| Rule 3 only | 3 | **24** | Yes | **No** — drops 19990101 @ 5% |
| Rule 0 only | 3 | **24** | Yes | **No** — drops 19890101 @ 9%, wrong 19800101 rate |
| Both rules raw | 6 | **48** | **No** — duplicate MEFFDATE at 19800101 and 20020101 | Partial — conflicts at 19800101 |
| **Union merge (recommended)** | **4** | **32** | **Yes** | **Yes** |

**Union merge result per MPLAN:**

| MEFFDATE | DECLARED_RATE | Source |
|----------|---------------|--------|
| 19800101 | 11.00000 | Rule 3 (tie-break — see §4) |
| 19890101 | 9.00000 | Rule 3 |
| 19990101 | 5.00000 | Rule 0 |
| 20020101 | 4.50000 | Both (identical) |

---

## C. Historical tier recommendation

**SME instruction:** *"Load all historical effective dates if available; otherwise load the current rate."*

**Conclusion:** The instruction requires tiers from **both** DINT_RULE headers, merged into a single chronological schedule keyed by unique `START_DATE`.

**Do not filter to Rule 3 only.** That omits the Rule 0 tier at 19990101.

**Do not emit both rules raw (48 rows).** That creates duplicate `(MPLAN, MEFFDATE)` keys at 19800101 (7% vs 11%) and redundant rows at 20020101.

---

## D. PR-5 selection rule (revised)

| Option | Verdict |
|--------|---------|
| Emit Rule 3 only | **Reject** — violates SME historical-load instruction |
| Emit Rule 0 only | **Reject** — omits Rule 3 tiers; wrong early history |
| Emit both raw | **Reject** — index collision / conflicting rates |
| **Union merge by START_DATE** | **Adopt** — SME-compliant, index-safe |

### Tie-break at duplicate START_DATE (19800101)

When both rules share a START_DATE but rates differ:

- Prefer **Rule 3** tier (11.00000) — original rule header (EFF 19800101); Rule 0 header EFF 20030813 indicates a later restatement.
- Document in loader config: `dint_rule_tiebreak: prefer_earliest_eff_date_header` or explicit `prefer_dint_rule: 3 on collision`.

---

## E. Final recommendation

**READY FOR DEVELOPMENT** — with **revised emit mode: `union_merge`**.

| Attribute | Value |
|-----------|-------|
| Expected rows | **32** (8 MPLANs × 4 unique START_DATEs) |
| Fallback (no history) | **8** (current tier only) |
| MCURRATE / MGTDRATE | DECLARED_RATE from merged tier; MGTDRATE = MCURRATE |
| MEFFDATE | PDINTTBL.START_DATE |

Planning documents updated to replace **DINT_RULE=3 only (24 rows)** with **union merge (32 rows)**.
