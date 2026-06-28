# Issue #21D — Remaining Client Actions

**Date:** 2026-06-27  
**Converter version:** v57.35  
**Audience:** Client / New Era / LifePRO extract team

---

## Summary

| Priority | Action | Track | Blocks Development? | Blocks release? |
|----------|--------|-------|---------------------|-----------------|
| **P1** | RNA re-extract (PRELSA) for 18 policies | B2 | No | **Yes (full Track B / full #21D)** |
| **P2** | UAT — Dividend Accum Int Rate 4.50% on ISWL | A | No | **Yes (Track A)** |
| **P3** | UAT — name display (partial then full) | B1/B2 | No | **Yes (Track B)** |
| **P4** | Confirm non-ISWL MDEPINT 4.00% acceptable | A | No | Recommended |
| **P5** | #21E cash value decision (separate issue) | A↔E | No | #21E only |

QLAdmin will proceed with Track A and B1 Development **without waiting** for P1.

---

## P1 — RNA re-extract (REQUIRED for full Track B)

### Owner

**Client / LifePRO extract team** — this is a **client-owned activity**. QLAdmin cannot manufacture missing IN/PO relationship rows.

### What to deliver

| Field | Specification |
|-------|---------------|
| **Extract name** | `RelationshipNameAddress_Extract_*.csv` (PRELSA) |
| **Delivery path** | `QLA_Migration/Source/` |
| **Required roles** | `IN`, `PO` (and related roles where present in LifePRO) for listed policies |
| **Reference list** | `Issue_Log_Items/Issue_21/Issue_21D/Issue_21D_Blank_Name_Population.csv` |

### Policies requiring IN and PO (9 — neither role in current RNA)

| MPOLICY | Legacy (approx.) | Notes |
|---------|------------------|-------|
| 010713704C | 9010713704 | Issue #21 golden; SA+BK only today |
| 010713705C | — | Same pattern as sibling policy |
| 010826551C | — | ISWL |
| 010422977C | — | |
| 010948278C | — | |
| 014112C | — | |
| 018900C | — | |
| 010150910C | — | |
| 01ML8151C | — | |

### Policies requiring IN only (3)

010774773C, 010816156C, 010877890C

### Policies requiring PO only (6)

011188773C, 010397945C, 010790779C, 010834096C, 011062307C, 011064567C

### Acceptance criteria

- [ ] Each listed policy has RNA rows with `RELATE_CODE` IN and/or PO as applicable
- [ ] NAME_ID values join to quikclnt after re-batch
- [ ] QLAdmin blank-name validator shows 0 remaining (or documented exceptions)

### Evidence of gap (for extract team)

Policy **9010713704** (`010713704C`): LifePRO relationship hierarchy includes IN|PA|PO|B1|B2|BK|SA; delivered RNA contains **SA + BK only**.

---

## P2 — UAT Track A (after QLAdmin delivers v57.36+)

### Owner

**Client**

### Sample policies

| MPOLICY | Check |
|---------|-------|
| 010713704C | Dividend Accum Int Rate = **4.50%** |
| 010718309C | ISWL sample |
| Any non-ISWL sample | Rate remains **4.00%** |

### Pass criteria

- ISWL policies show 4.50% Dividend Accum Int Rate
- Non-ISWL policies unchanged at 4.00%
- No unexpected QLAdmin display regressions

---

## P3 — UAT Track B

### Phase B1 partial UAT (after quikclnt fix, before RNA)

**Owner:** Client

| MPOLICY | Expected |
|---------|----------|
| 010766896C | Insured/owner: JOHNSON, PENNY |
| 011080481C | Insured: YOUNTS, JOSHUA |
| 010464869C / 010464870C | Names display (not blank commas) |

**Note:** 18 policies will **still** show blank names until P1 completes.

### Phase B2 full UAT (after RNA re-extract)

**Owner:** Client

| MPOLICY | Expected |
|---------|----------|
| 010713704C | Insured and owner names display |
| Full 25-policy list | No blank-name defects |

---

## P4 — Non-ISWL rate confirmation (recommended)

### Owner

**Client / Actuarial**

### Question

Confirm that non-ISWL policies should continue to receive **MDEPINT = 4.00%** until a separate actuarial governance process assigns other rates.

### Why it matters

A fleet-wide 4.50% constant would affect 2,815 non-ISWL policies. QLAdmin implementation is ISWL-scoped; this confirmation supports production sign-off.

---

## P5 — Issue #21E coordination (separate issue)

### Owner

**Client** (business decision) · **Shared** (UAT)

Track A MDEPINT fix may affect cash value display on ISWL/UL samples. Issue #21E (load vs compute) remains a **separate client decision**. Joint UAT on 010713704C and 010818663C recommended.

---

## Client action tracker

| ID | Action | Owner | Due | Status |
|----|--------|-------|-----|--------|
| CA-1 | RNA re-extract for 18-policy list | Client / LifePRO | TBD | **Open** |
| CA-2 | UAT Track A (4.50% ISWL) | Client | After v57.36 | **Pending** |
| CA-3 | UAT Track B1 (partial names) | Client | After v57.36 | **Pending** |
| CA-4 | UAT Track B2 (full names) | Client | After CA-1 + re-batch | **Pending** |
| CA-5 | Non-ISWL 4.00% confirmation | Client / Actuarial | Before prod | **Recommended** |
| CA-6 | #21E cash value decision | Client | Separate | **Open** |

---

*QLAdmin action: deliver v57.36 Track A + B1; provide CA-1 policy list to client if not already shared.*
