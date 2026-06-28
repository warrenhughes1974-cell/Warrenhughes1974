# Issue #21D — Client UAT Package

**Date:** 2026-06-27  
**Converter version:** v57.36  
**Release scope:** Track A + Track B1 (partial)  
**Audience:** Client / New Era UAT team

---

## 1. Release summary for client

Issue #21D addresses two converter defects in **v57.36**:

| Track | Fix | UAT required? |
|-------|-----|---------------|
| **A** | ISWL Dividend Accum Int Rate → **4.50%** | **Yes** |
| **B1** | Missing client names (quikclnt integrity) | **Yes** |
| **B2** | RNA data gaps (9 policies) | **No** — client data remediation, not a converter defect |

**Important:** This release is a **partial fix**. Nine policies will still show blank insured/owner names until PRELSA RNA is re-delivered (see Section 4).

---

## 2. Track A UAT — Interest crediting rate

### What changed

QLAdmin field **Dividend Accum Int Rate** (`quikdvdp.MDEPINT`) now shows **4.50%** for all **Interest-Sensitive Whole Life (ISWL)** policies. All other products remain **4.00%**.

### Expected business behavior

- ISWL policies display **4.50%** Dividend Accum Int Rate in QLAdmin Policy Display
- Non-ISWL policies (term, UL, etc.) continue to show **4.00%**
- Plan NFO interest code (`quikplan.NFOINT = A`) was already correct — unchanged

### Sample policies to verify

| MPOLICY | Product | Expected Dividend Accum Int Rate |
|---------|---------|----------------------------------|
| **010713704C** | ISWL (1659C2) | **4.50%** |
| **010818663C** | ISWL (1659C2) | **4.50%** |
| Any non-ISWL sample | e.g. term | **4.00%** (unchanged) |

### UAT steps

1. Open each sample policy in QLAdmin Policy Display
2. Locate **Dividend Accum Int Rate**
3. Confirm ISWL samples show **4.50%**
4. Confirm at least two non-ISWL samples show **4.00%**
5. Record PASS/FAIL per policy

### Pass criteria

- All ISWL samples @ 4.50%
- No non-ISWL sample @ 4.50%
- No unexpected rate on products outside ISWL family

---

## 3. Track B1 UAT — Owner / insured names

### What changed

Twelve client records that existed in LifePRO RNA but were missing from `quikclnt` are now emitted. **Seven policies** in the original defect list now display names correctly.

### Expected business behavior

- Policies where names were missing due to converter quikclnt gap now show insured/owner names
- Policies where RNA lacks IN/PO rows **remain blank** (Track B2 — not this release)

### Sample policies to verify (B1 — expect names)

| MPOLICY | Expected insured (sample) | Notes |
|---------|---------------------------|-------|
| **010766896C** | JOHNSON, PENNY | Was missing client 592064 |
| **011080481C** | YOUNTS, JOSHUA (insured) | Was missing client 607190 |
| **010464869C** | ULMER, ARTHUR | |
| **010464870C** | ULMER, IRENE | |
| **010872417C** | EPLEY, JOHN | |
| **011047402C** | ULMER, IRENE | |
| **011047403C** | ULMER, ARTHUR | |

### UAT steps

1. Open each sample policy in QLAdmin Policy Display
2. Verify **insured** and/or **owner** name fields are populated
3. Confirm names match LifePRO expectations
4. Record PASS/FAIL per policy

### Pass criteria

- All seven B1 sample policies show correct names
- No duplicate or wrong-person names observed

---

## 4. Track B2 — Client data remediation (NOT converter UAT)

### Status

**Not fixed in v57.36.** These policies lack IN and/or PO rows in the delivered PRELSA extract. The converter cannot create relationship identities.

### Policies still expected blank (do not fail UAT for these)

| MPOLICY |
|---------|
| 010422977C |
| **010713704C** |
| 010713705C |
| 010826551C |
| 010948278C |
| 014112C |
| 018900C |
| 010150910C |
| 01ML8151C |

### Client action required

Re-extract PRELSA / `RelationshipNameAddress_Extract` with IN and PO rows where they exist in LifePRO. Reference: `Issue_21D_Blank_Name_Population.csv`

**This is a data delivery item, not a converter defect.**

---

## 5. UAT sign-off template

| Track | Tester | Date | Result | Notes |
|-------|--------|------|--------|-------|
| A — ISWL rate | | | PASS / FAIL | |
| A — non-ISWL unchanged | | | PASS / FAIL | |
| B1 — name samples (7) | | | PASS / FAIL | |
| B2 acknowledged out of scope | | | YES / N/A | |

---

## 6. Reference artifacts

| Document | Purpose |
|----------|---------|
| `Issue_21D_Development_Report.md` | Technical change summary |
| `Issue_21D_Validation_Report.md` | QA evidence |
| `Issue_21D_Blank_Name_Population.csv` | Full affected policy list |
| `Issue_21D_Interest_Rate_Population.csv` | ISWL rate population (2,268) |

---

*Client UAT package ready for distribution.*
