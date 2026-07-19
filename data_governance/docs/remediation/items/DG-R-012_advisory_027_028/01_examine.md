# DG-R-012 — Examine: Advisory warnings DG-QUIKPLAN-027 / 028

**Status:** CLOSED (decision R1 applied)  
**Date:** 2026-07-19  
**Rule IDs:** DG-QUIKPLAN-027 (traditional value tables), DG-QUIKPLAN-028 (annuity tables)  
**Severity:** Advisory (WARN) — overall rule status stays PASS  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`  
**Production compare:** `Q:\WPA\WPA_GABIE`

---

## 1. What the rules currently require

### 027 — Traditional (plan first char 0–8)

Warn if plan missing from **any** of: QuikPlCv, QuikPlTv, QuikCvs, QuikTvs, QuikNps.

`Data_Goverence.txt`: warn if those tables are absent — **“THIS NEEDS TO BE IN THE AUDIT LOG.”**

### 028 — Annuity (plan begins with A)

Warn if plan missing from **each** of: QuikAint, QuikAing, QuikAexp, QuikAinf (all four independently).

`Data_Goverence.txt` also says:

> IF THEY HAVE ONLY ONE VALUE QUIKAING OR QUIKAINF THEN WE USE THE OTHER VALUES.

So Aing and Ainf were meant to be **interchangeable**, not both mandatory. Current 028 over-enforces.

---

## 2. Live inventory — CSO

| Cohort | Count | Active |
|--------|------:|-------:|
| Traditional (0–8) | 83 | **0** (all closed) |
| A-prefix annuity | 2 | 0 |
| Other (9-series, etc.) | 56 | — |

### 027 findings: **98 WARN**

| Coverage | Plans |
|----------|------:|
| All 5 tables present | 42 |
| Partial gaps | 30 |
| Missing all 5 | 11 (mostly PUA / PA / JPO shells) |

| Missing table | Plans affected |
|---------------|---------------:|
| QuikCvs | 38 |
| QuikNps | 21 |
| QuikTvs | 17 |
| QuikPlCv / QuikPlTv | 11 each |

Common pattern: riders/term have PlCv+PlTv but no QuikCvs (20 plans).

### 028 findings: **6 WARN**

| Plan | Has | Missing |
|------|-----|---------|
| A60MIR, A96DAR | QuikAint only | QuikAing, QuikAexp, QuikAinf (×2) |

These are the same deposit-annuity riders deferred under DG-R-009 (BASIS). QuikAing/Aexp/Ainf files are empty on CSO.

---

## 3. Production — WPA_GABIE

### 027: **899 WARN** (same over-breadth as CSO)

| Coverage | Plans (of 609 trad) |
|----------|--------------------:|
| Complete | 262 |
| Partial | 281 |
| Missing all 5 | 66 |

Largest pattern: **245** plans missing QuikCvs + QuikPlCv (80 of them **active**). Production does not load the full five-table suite for every 0–8 plan.

### 028: **221 WARN** — QuikAinf is empty in production

| Table | Distinct MPLAN |
|-------|---------------:|
| QuikAint | 181 |
| QuikAing | 183 |
| QuikAexp | 187 |
| **QuikAinf** | **0** |

| Logic | A-plans that would “pass” |
|-------|--------------------------:|
| Require all 4 (current) | **0 / 193** |
| QuikAint + QuikAexp + (Aing **or** Ainf) | **175 / 193** |

WPA never uses QuikAinf; requiring it creates a permanent false advisory on every annuity plan.

---

## 4. Options

### Option R1 — Revise 028 (Aing/Ainf OR); accept 027 as audit warnings (recommended)

| Piece | Action |
|-------|--------|
| **028** | Require QuikAint and QuikAexp; require **QuikAing or QuikAinf** (not both). Align with `Data_Goverence.txt` + WPA. |
| **027** | **No rule change.** Keep as intentional advisory audit (written requirement). Document residuals as expected for closed riders / non-CV products. |
| Data | **No DBF writes.** |

| Pros | Cons |
|------|------|
| Fixes clear QuikAinf false positives | CSO A60MIR/A96DAR still warn (missing Aexp + neither Aing nor Ainf) — real gaps |
| 027 stays in audit log as designed | ~98 CSO / ~899 WPA traditional warnings remain |

### Option A — Accept both as advisory residuals (docs only)

No rule or data changes. Close item as “working as designed.” Leaves QuikAinf noise on every WPA annuity plan.

### Option R2 — Narrow 027 as well

e.g. warn only when missing **all five**, or only when missing both PlCv and PlTv. Reduces noise but **weakens** the written audit requirement. Only if business wants quieter reports.

### Option B — Mass-create missing rate/annuity rows

High actuarial risk; contradicts WPA. **Not recommended.**

---

## 5. Recommended option (discussion — not a decision)

**Option R1**

- **028** is a true rule bug relative to the business note and production (empty QuikAinf).
- **027** is doing what the governance text asked: advisory audit for incomplete traditional value setups. CSO’s book is entirely closed traditional; gaps are expected. Do not invent rate tables.

Residual after R1 on CSO 028: warnings on A60MIR/A96DAR until those riders get real annuity setup (out of scope / overlaps DG-R-009 deferral).

---

## 6. Validation (after Implement, if R1)

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "<item>/validation_out" --rule DG-QUIKPLAN-028
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "<item>/validation_out" --rule DG-QUIKPLAN-027
```

Expect: 028 findings drop (QuikAinf-only noise gone; CSO still ~4 warns on A60MIR/A96DAR); 027 unchanged (~98 warns).

---

## 7. Decision prompt

Reply with:

1. `Decision: Option R1 — revise 028 (Aint+Aexp+(Aing or Ainf)); accept 027 as advisory audit; no data changes`
2. `Decision: Option A — accept both 027/028 as advisory residuals; docs only`
3. Other / defer (e.g. also narrow 027)
