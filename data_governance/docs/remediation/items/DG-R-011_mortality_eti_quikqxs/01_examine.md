# DG-R-011 — Examine: Mortality / ETI vs QuikQxs (DG-PLANVALUES-001/002)

**Status:** CLOSED (decision R1 applied)  
**Date:** 2026-07-19  
**Rule IDs:** DG-PLANVALUES-001 (MORT), DG-PLANVALUES-002 (ETIMORT)  
**Tables:** QuikPlCv / QuikPlTv → QuikQxs.MORT  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`  
**Production compare:** `Q:\WPA\WPA_GABIE`

---

## 1. What the rules currently require

| Rule | Field | Current enforcement |
|------|-------|---------------------|
| 001 | MORT on QuikPlCv + QuikPlTv | Null/blank **fail**; nonblank must exist once in QuikQxs |
| 002 | ETIMORT on QuikPlCv | Null/blank **fail**; nonblank must exist once in QuikQxs |

**Tension in the catalog itself**

- **Purpose** (both rules): ensure every **populated** value exists in QuikQxs.
- **Failure conditions / business_rule text:** null and blank fail.

`Data_Goverence.txt`: “MORT/ETIMORT — this needs to be in quikqxs” (reference check when present, not “must always be filled”).

Conversion (`cso_mortality_crosswalk.py`): **blank values stay blank**; never fabricates a code.

---

## 2. Live inventory — CSO (the surprise)

| Metric | Value |
|--------|------:|
| QuikQxs distinct MORT | 243 |
| QuikPlCv / QuikPlTv rows | 229 / 279 |
| Distinct MORT/ETIMORT codes used | 3 each (A1/O1/N1 and C1/Q1/N1) |
| Codes **missing** from QuikQxs | **0** |

| Rule | Evaluated | Passed | Findings | Category |
|------|----------:|-------:|---------:|----------|
| DG-PLANVALUES-001 | 508 | 245 | **263** | **100% BLANK_VALUE** |
| DG-PLANVALUES-002 | 229 | 102 | **127** | **100% BLANK_VALUE** |

There is **no** “orphan mortality code” problem on CSO. Every populated MORT/ETIMORT already resolves in QuikQxs.

### Who has blank MORT?

| Fact | Detail |
|------|--------|
| Plans with any blank MORT row | 78 |
| All of those plans | **BACTIVE = closed** |
| Common suffixes | ADB, WP, PUA, CTR, STR, JPO, riders / 9-series heavy |
| Plans with both blank and populated MORT rows | **0** (all-or-nothing per plan) |
| Traditional (0–8) with Cv/Tv but MORT all blank | 24 (PUA, term riders, etc.) |

---

## 3. Production — WPA_GABIE

| Metric | Cv.MORT | Tv.MORT | Cv.ETIMORT |
|--------|--------:|--------:|-----------:|
| Blank rows | 16 | **0** | 16 |
| Populated | 471 | 944 | 471 |
| Missing from QuikQxs | **0** | **0** | **0** |

WPA governance: **16 + 16** blank findings only (same 16 plans, mostly `517*` term family + `5RACTG`). Those plans have **populated QuikPlTv.MORT** while QuikPlCv.MORT/ETIMORT stay blank — production allows blank cash-value mortality when tabular is loaded.

---

## 4. Options

### Option R1 — Revise 001/002: skip blank/null; validate only populated codes (recommended)

Align implementation with the written **purpose** and with conversion blank-safe behavior:

- Blank/null MORT or ETIMORT → **skip** (not FAIL)
- Nonblank → must exist exactly once in QuikQxs (unchanged)
- Update catalog failure conditions, report wording, `Data_Goverence.txt`, tests
- **No** QuikPlCv / QuikPlTv / QuikQxs DBF writes

| Pros | Cons |
|------|------|
| Clears 390 CSO findings that are not “missing codes” | Blank no longer flagged as a data problem |
| Matches WPA (allows some Cv blanks) | Does not force closed riders to get a mortality table |
| Matches conversion “blank stays blank” | — |

Expected after R1 on CSO: **001/002 PASS** (0 missing codes today).

### Option A — Fill blank MORT/ETIMORT from crosswalk / default codes

Would invent actuarial keys on closed riders and shells. Contradicts conversion blank-safe policy and WPA blanks. **Not recommended** without product/actuarial sign-off per plan.

### Option B — Delete Cv/Tv rows that have blank MORT

Destructive; those rows may still carry gender/band/state/effdate structure. **Not recommended** as a mass fix.

### Option C — Require MORT only when PLANVALOPT / BACTIVE / traditional base

More complex hybrid. WPA blanks are on plans that still have Tv MORT, so a closed-only exception would not match production. Prefer R1’s clear “populated-only” reference rule.

---

## 5. Recommended option (discussion — not a decision)

**Option R1** — same family as DG-R-004 / 007 / 010: the check over-enforced beyond “populated value must exist in setup.”  
Baseline title said “missing in QuikQxs”; evidence shows **blanks**, not missing codes.

In plain English: if a cash/tabular row names a mortality table, that table must be on file. If the row leaves mortality blank (common on riders / some cash-value shells), that is allowed — do not invent a code.

---

## 6. Validation (after Implement)

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "<item>/validation_out" --rule DG-PLANVALUES-001
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "<item>/validation_out" --rule DG-PLANVALUES-002
```

Expect: PASS (or only true missing/ambiguous codes if any appear later).

---

## 7. Decision prompt

Reply with:

1. `Decision: Option R1 — revise 001/002: skip blank/null MORT/ETIMORT; validate QuikQxs only when populated; no data changes`
2. Other / defer
