# Issue #86 — Intake Summary

**Issue:** #86 — QuikDate full rebuild (prior-month-end dates + screenshot defaults)  
**Framework stage:** Intake Agent (G0)  
**Status:** Intake Complete → Planning (Pre-Risk Auto-Chain)  
**Generated:** 2026-07-19  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (Warren)  
**Priority:** High (system control table; DG-QUIKDATE / batch load correctness)  
**Code changes:** None  

**Opened as:** Client screenshot of `Q:\CSO\CSO_TEST_6_30_2026_ROBERT\QUIKDATE.DBF` showing stale historical dates; request to totally rebuild QuikDate like other system-control emits.

---

## 1. Symptom in plain English

`QUIKDATE` is a **one-row system control** table (processing / billing cycle dates). The live region still shows old 2004-era bill dates (and related fields), while Governance expects **prior calendar month-end** for the bill-date family (for a 2026-07 run that is **2026-06-30**).

Conversion already emits a partial `quikdate.csv` (DG-R-003): only `PACBILL` / `DIRBILL` / `REINBILL` + ACH / ESC defaults. Other schema fields are left blank. That is **not** a full rebuild matching the client screenshot defaults or the Governance note to set **all dates** to prior month-end.

Client instruction (normalized):

1. Totally rebuild QuikDate (do not carry forward stale source/region values).  
2. **Date fields** → same prior-month-end rule used in Governance (`DG-QUIKDATE` / `Data_Goverence.txt`).  
3. **Non-date fields** → default to values visible on the client screenshot (VERSION, UPDATENUM, PDUEDAYS, ACH*).  
4. `ESC_DATE` stays blank (already locked by DG-QUIKDATE-006).

---

## 2. Evidence

| Artifact | Finding |
|----------|---------|
| Client screenshot | `QUIKDATE.DBF` under `CSO_TEST_6_30_2026_ROBERT`; row shows PROCDATE≈07/19/2026, ANNDATE/DIRBILL/PACBILL/GRPBILL/APLBILL/LOANBILL/CCBILL in 2004–2011, REINBILL/CPNBILL/ESC blank, PDUEDAYS=31, VERSION=5.318, UPDATENUM=359, ACHFILEID=0, ACHFILEID2=A |
| Edit buffer on screenshot | DIRBILL / PACBILL / REINBILL corrected toward **06/30/2026** |
| Current batch emit | `QLA_Migration/Output/quikdate.csv` has PAC/DIR/REIN=`20260630`, ACH defaults; **all other columns blank** |
| Governance catalog | `DG-QUIKDATE-001..006` + `Data_Goverence.txt`: “set all dates to [prior month end]” |
| Existing code | `qla_core/quikdate_converter.py` (partial emit only) |

Example policies: **N/A** (system table, not policy-grained).

---

## 3. Suspected domain

**System control emit — `quikdate.csv` full single-row rebuild**

Related: Data Governance Item 5 (`DG-QUIKDATE`), remediation DG-R-003 (incomplete relative to this request).

---

## 4. In scope / out of scope

### In scope

- Define full one-row QuikDate rebuild rules (all schema fields)  
- Align date fields to prior-month-end of conversion run date  
- Lock non-date defaults from screenshot  
- Preserve schema field order/names; emit on full batch like other rebuilt control tables  
- Validation against DG-QUIKDATE-001..006 after Development  

### Out of scope

- Policy/claims/rate table changes  
- Expanding Governance rules beyond what Development needs (optional follow-up if PROCDATE etc. should be audited)  
- Live DBF patching as the permanent fix (emit is the system of record)  

---

## 5. Related issues / artifacts

| Item | Relationship |
|------|----------------|
| DG-R-003 / `quikdate_converter.py` | Partial emit already shipped (v58.07) — this issue completes the full rebuild |
| `data_governance` Item 5 | Acceptance criteria for PAC/DIR/REIN/ACH/ESC |
| `QLA_Migration/Data_Goverence.txt` | Business authority: all dates → prior month end |

---

## 6. Immediate blockers at intake

None that stop Planning. Soft decisions (PROCDATE / blank date fields → PME vs run-date) documented in Scope Decisions with recommended defaults.

---

## 7. Gate Criteria (G0)

- [x] Issue folder created  
- [x] Intake summary written  
- [x] Example policies listed as N/A (system table)  
- [x] Owner / priority assigned  
- [x] No code or rulebook changes  

**Recommended status:** Ready for Planning → Dependency Gate (auto-chain).
