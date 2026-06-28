# Issue #21D — Client Test Scenarios

**Date:** 2026-06-27  
**Converter version:** v57.36  
**UAT environment:** QLAdmin loaded with v57.36 batch output (`QLA_Migration/Output/`)  
**Scope:** Track A + Track B1 only — Track B2 excluded from pass/fail

---

## Scenario index

| ID | Track | Priority | Scenario |
|----|-------|----------|----------|
| A-01 | A | P0 | Golden ISWL rate — 010713704C |
| A-02 | A | P0 | Golden ISWL rate — 010818663C |
| A-03 | A | P1 | Client-selected ISWL sample |
| A-04 | A | P0 | Non-ISWL rate unchanged |
| A-05 | A | P1 | Non-ISWL second sample |
| B1-01 | B1 | P0 | Recovered name — 010766896C |
| B1-02 | B1 | P0 | Recovered name — 011080481C |
| B1-03 | B1 | P1 | B1 cohort — remaining five policies |
| B1-04 | B1 | P1 | No MPRIMID type-flag display |
| B2-01 | B2 | Info | Expected blank — 010713704C (out of scope) |
| B2-02 | B2 | Info | Nine-policy RNA gap acknowledgment |

---

## Track A scenarios

### A-01 — Golden ISWL rate (010713704C)

| Field | Value |
|-------|-------|
| **Policy** | 010713704C |
| **Product** | ISWL (MPLAN 1659C2) |
| **QLAdmin field** | Dividend Accum Int Rate |
| **Expected** | **4.50%** |
| **Pre-fix (v57.35)** | 4.00% |

**Steps:**
1. Open Policy Display for 010713704C
2. Locate Dividend Accum Int Rate
3. Record displayed value

**Pass:** Value = 4.50%  
**Fail:** Any other value

---

### A-02 — Golden ISWL rate (010818663C)

| Field | Value |
|-------|-------|
| **Policy** | 010818663C |
| **Product** | ISWL |
| **Expected** | **4.50%** |

**Pass:** Value = 4.50%

---

### A-03 — Client-selected ISWL sample

| Field | Value |
|-------|-------|
| **Policy** | _(client to select from ISWL book)_ |
| **Reference** | `Issue_21D_Interest_Rate_Population.csv` (2,268 policies) |
| **Expected** | **4.50%** |

**Pass:** Value = 4.50% on client-selected ISWL policy

---

### A-04 — Non-ISWL unchanged (required)

| Field | Value |
|-------|-------|
| **Policy** | Client selects term/UL/non-ISWL (e.g. 010948278C, MPLAN 5667AT) |
| **Expected** | **4.00%** |

**Pass:** Value = 4.00%

---

### A-05 — Non-ISWL second sample

| Field | Value |
|-------|-------|
| **Policy** | Second non-ISWL policy (different product family) |
| **Expected** | **4.00%** |

**Pass:** Value = 4.00%

---

## Track B1 scenarios

### B1-01 — Recovered insured name (010766896C)

| Field | Value |
|-------|-------|
| **Policy** | 010766896C |
| **Expected insured** | JOHNSON, PENNY |
| **Pre-fix** | Missing client 592064 in quikclnt |

**Steps:**
1. Open Policy Display
2. Verify insured name visible
3. Compare to LifePRO if available

**Pass:** Insured name displays JOHNSON, PENNY (or equivalent QLAdmin format)

---

### B1-02 — Partial recovery (011080481C)

| Field | Value |
|-------|-------|
| **Policy** | 011080481C |
| **Expected insured** | YOUNTS, JOSHUA |
| **Expected owner** | YOUNTS, JOSHUA (owner was already present pre-fix) |

**Pass:** Insured name displays correctly

---

### B1-03 — B1 cohort (five additional policies)

| MPOLICY | Expected insured (minimum) |
|---------|----------------------------|
| 010464869C | ULMER, ARTHUR |
| 010464870C | ULMER, IRENE |
| 010872417C | EPLEY, JOHN |
| 011047402C | ULMER, IRENE |
| 011047403C | ULMER, ARTHUR |

**Pass:** All five show populated insured names

---

### B1-04 — No type-flag leak (spot check)

| Field | Value |
|-------|-------|
| **Check** | Any policy — insured ID must not display as single letter "I" |
| **Expected** | No policy shows "I" as client ID in name fields |

**Pass:** No `MPRIMID='I'` display observed (automated QA: 0 fleet-wide)

---

## Track B2 scenarios (informational — do not fail UAT)

### B2-01 — Expected blank (010713704C names)

| Field | Value |
|-------|-------|
| **Policy** | 010713704C |
| **Rate UAT** | Track A — expect 4.50% ✅ |
| **Name UAT** | **Out of scope** — RNA missing IN/PO |
| **Expected names** | Blank (until PRELSA re-extract) |

**Action:** Acknowledge as B2 data gap — **not a converter failure**

---

### B2-02 — Nine-policy RNA gap acknowledgment

Client confirms understanding that these policies remain blank pending RNA:

`010422977C`, `010713704C`, `010713705C`, `010826551C`, `010948278C`, `014112C`, `018900C`, `010150910C`, `01ML8151C`

**Action:** Sign B2 acknowledgment on sign-off form

---

## Defect triage guide

| Observation | Triage |
|-------------|--------|
| ISWL shows 4.00% | **Track A defect** — escalate to QLAdmin |
| Non-ISWL shows 4.50% | **Track A defect** — escalate immediately |
| B1 sample missing name | **Track B1 defect** — escalate to QLAdmin |
| B2 nine policies blank | **Expected** — client RNA action (B2) |
| 010713704C blank names but 4.50% rate | **A pass / B2 expected** |

---

*Client test scenarios ready for execution.*
