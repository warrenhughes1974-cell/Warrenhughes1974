# DG-R-005 — Examine: HCOMMIP / HRIGPKEY logicals (DG-QUIKPLAN-030)

**Status:** AWAITING_DECISION  
**Date:** 2026-07-18  
**Rule ID:** DG-QUIKPLAN-030  
**Primary table:** QuikPlan  
**Fields:** `PLANTYPE`, `HCOMMIP`, `HRIGPKEY`  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`

---

## 1. What the rule requires

| Condition | Required |
|-----------|----------|
| `PLANTYPE` = MEDS | `HCOMMIP` and `HRIGPKEY` both **true** (Y/T/1) |
| Any other / blank plan type | Both **false** (F/N/0) |
| Unreadable logical | **Fail** |

Business text (`Data_Goverence.txt` line 161):

> IF THE PLANTYPE IS MEDS THEN HCOMMIP AND HRIGPKEY NEED TO BE YES OTHERWISE THEY NEED TO BE F

Baseline report message “could not be read” / Current Value `/` = both logicals failed `decode_logical`.

---

## 2. Live inventory — CSO

| Metric | Value |
|--------|------:|
| QuikPlan rows | 142 |
| PLANTYPE blank | **142** (0 MEDS) |
| HCOMMIP decoded | all `None` (unreadable) |
| HRIGPKEY decoded | all `None` (unreadable) |
| Raw HCOMMIP bytes | `?` × **141**, space × **1** |
| Raw HRIGPKEY bytes | `?` × **141**, space × **1** |

So every CSO plan fails DG-QUIKPLAN-030 as **INVALID_LOGICAL**, not as “wrong true/false for MEDS.”

---

## 3. Production check — WPA_GABIE

| Check | Result |
|-------|--------|
| Path | `Q:\WPA\WPA_GABIE\QUIKPLAN.DBF` |
| Read this session | **Permission denied** (file likely open in QLAdmin) |
| User screenshot (earlier) | `HCOMMIP` / `HRIGPKEY` columns appear empty for visible rows |

Cannot confirm raw `?` vs space vs `.F.` on production until the file is closed/readable. Empty UI cells often mean space or uninitialized logical — same failure class as CSO.

---

## 4. Options (business decision)

### Option A — Fix data: set both logicals to **False** for non-MEDS (recommended for CSO)

**Action on CSO QuikPlan:**

- Where PLANTYPE is not MEDS (all 142 today): set `HCOMMIP = .F.` and `HRIGPKEY = .F.`
- If any MEDS appear later: set both `.T.`

Also (optional same package): conversion QuikPlan emit defaults both to False unless PLANTYPE=MEDS.

| Pros | Cons |
|------|------|
| Matches written business rule (F otherwise) | Touches 142 logical fields |
| Clears unreadable `?` / space bytes | Need WPA read/confirm before applying same to production |

### Option B — Soften decoder/rule: treat blank / `?` / space as False for non-MEDS

**Action:** Code-only — no DBF rewrite. Pass non-MEDS when logical is blank/unreadable; still require True for MEDS.

| Pros | Cons |
|------|------|
| Matches “empty in UI” production look without mass update | Hides corrupt logical storage; MEDS mis-set as `?` would incorrectly pass as non-true |
| No Q: writes | Weaker than explicit `.F.` |

### Option C — Defer until WPA file is readable

Inventory production raw bytes first; then choose A or B.

### Option D — Change business rule (not recommended without evidence)

Only if production intentionally stores blank/`?` as the standard and ops reject writing `.F.`.

---

## 5. Recommended option (discussion — not a decision)

**Option A on CSO** (explicit `.F.`), plus **Option C-style caution for WPA** (do not touch production until unlocked and inventoried).  
Unlike DG-R-004 (NAPLAN), the written rule here **matches** “otherwise F”; CSO data is corrupt/uninitialized logicals, not an alternate valid code.

---

## 6. Validation (after Implement)

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "<item>/validation_out" --rule DG-QUIKPLAN-030
```

Expect: PASS for all non-MEDS with False/False.

---

## 7. Regression guards

- Only HCOMMIP / HRIGPKEY (and optionally conversion defaults)  
- PLANTYPE / MNAICLOB / QuikDate / List unchanged  
- DG-R-004 NAPLAN rule unchanged  

---

## 8. What we need from you

Example:

`Decision: Option A — set HCOMMIP/HRIGPKEY to False on all non-MEDS CSO QuikPlan rows; leave WPA until we can inventory; conversion default False unless MEDS`

Or:

`Decision: Option C — wait until I close WPA QuikPlan so we can inventory production first`
