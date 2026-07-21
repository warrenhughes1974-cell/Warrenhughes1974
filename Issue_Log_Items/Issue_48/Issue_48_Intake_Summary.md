# Issue #48 — Intake Summary

**Issue:** #48 — Secondary Rate File (PAAGERAT fallback)  
**Date:** 2026-07-10  
**Framework stage:** Intake complete (G0)  
**Status:** Approved → Planning  
**Owner:** Conversion (Warren) · **Assigned:** Warren  
**Business status:** No-Go for Development until G1 + G2 + G3  

---

## 1. Client / business symptom (verbatim + normalized)

**Issue log (verbatim):**

> 48 Active Secondary Rate File We have a secondary rate file to examine for rates if the rates dont currently exist in PAAGERAT.  
> The secondary rate file is in Source folder and it is named: Rate_Table_Extract_Txt.

**Normalized:**

When a needed rate is **absent from PAAGERAT**, the converter must also examine the secondary source file `QLA_Migration/Source/Rate_Table_Extract_Txt.txt` before treating the rate as missing. PAAGERAT remains the primary attained-age authority where present; the secondary file is a **fallback**, not a replacement.

**Example policies:** none provided at intake.

---

## 2. Suspected domain

| Layer | Path / table | Role |
|-------|--------------|------|
| Primary source | `PAAGERAT_AttainedAge_Rates_Extract_*.csv` | Attained-age rates (PR, BP, U5/U6, NF, etc.) |
| Secondary source | `QLA_Migration/Source/Rate_Table_Extract_Txt.txt` | Issue-age × duration Rate_Table extract (client-named fallback) |
| Existing twin | `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` | Same content already used by rate loaders |
| Targets | Quik rate tables (`QuikCvs`, `QuikNps`, `QuikTvs`, `QuikGps`, COI/GCOI, etc.) | Downstream emit depends on TYPE_CODE / plan family |

**Domain:** Rates / source authority — **not** policy master, riders, claims, or memo.

---

## 3. Intake evidence (measured — Planning will formalize)

| Check | Result |
|-------|--------|
| File present | Yes — `QLA_Migration/Source/Rate_Table_Extract_Txt.txt` (94,834,824 bytes; dated 2026-07-10) |
| Schema | Rate_Table shape: `COVERAGE_ID, TYPE_CODE, AGE, SEX, BAND, UNDERWRITING_CLASS, DURATION, VALUE` |
| Rows | 1,128,984 data rows · 65 coverages · 212 `(COVERAGE_ID, TYPE_CODE)` keys |
| TYPE_CODEs | NP, CV, RV, NN, PN, NF, DV, TP, TX, DB, PR, SL, UF |
| Identity vs primary Rate_Table | **Byte-identical** to `Rate_Table_Extract_20260427.csv` (MD5 `4f53014d280c0b980e788cb2d3866a36`) |
| New rate content? | **No** — redelivery/copy of existing Rate_Table extract into Source |
| Fills Issue #42 gaps? | **No** — `L01 10Y` NP and `L10 LP9595` still absent (same as current Rate_Table) |
| PAAGERAT overlap TYPE_CODEs | Shared vocabulary includes PR, NP, CV, RV, NF, DB (different grain: attained-age SEQ vs age×duration) |
| Current resolver wiring | `plan_source_paths.rate_table_extract()` points at `plan_analysis/.../Rate_Table_Extract_20260427.csv`; Source `.txt` name is **not** yet in the path resolver |
| Fallback chain today | Loaders use Rate_Table and PAAGERAT for **different** TYPE_CODE / product paths — **not** an explicit “if missing in PAAGERAT → Rate_Table” rule |

Evidence note: `evidence/issue48_source_identity.txt`

---

## 4. In scope / out of scope (first pass)

### In scope

- Define lookup precedence: **PAAGERAT first**, then secondary Rate_Table (`Rate_Table_Extract_Txt` / twin CSV) when PAAGERAT has no usable rows for the needed coverage/TYPE.
- Inventory which TYPE_CODEs / plan families are candidates for that fallback (grain-compatible only).
- Wire Source-folder discovery for `Rate_Table_Extract_Txt.txt` (or confirm twin path is sufficient).
- Document audit/trace when secondary source is used.

### Out of scope (unless Planning expands)

- Treating this file as new CSO content that closes Issue #42 (it does not).
- Replacing PAAGERAT attained-age loaders with Rate_Table age×duration grids without grain rules.
- Changing PDAGE usage (client named Rate_Table_Extract_Txt only; PDAGE exists separately in Source).
- Redesigning rate architecture or wholesale loader rewrites (`AGENTS.md`).

---

## 5. Related issues

| Issue | Relationship |
|-------|----------------|
| **#42** | Missing L01/L10 extract rows — **not** resolved by this file (identical to existing Rate_Table) |
| **#40 / #41** | CV inheritance / endpoint — Rate_Table CV path; must not regress |
| **#31** | ISWL PAAGERAT BP/U5/U6/PR authority — fallback must not override PAAGERAT when present |
| **#37** | Age/duration placement — Rate_Table CV grain rules |
| Rate inheritance validation | Shared Rate_Table / PAAGERAT completeness work |

---

## 6. Artifact inventory

| Artifact | Status |
|----------|--------|
| Issue log row (#48 Active Secondary Rate File) | Provided |
| Secondary file `Source/Rate_Table_Extract_Txt.txt` | Present |
| Primary PAAGERAT `Source/PAAGERAT_AttainedAge_Rates_Extract_20260630.csv` | Present |
| Existing Rate_Table twin `plan_analysis/.../Rate_Table_Extract_20260427.csv` | Present (identical bytes) |
| Example policies / screenshots | **Missing** — none provided |
| Written rule: which TYPE_CODEs may fall back | **Missing** — Planning must propose; may need client confirm |
| Written rule: grain conversion (attained SEQ ↔ age×duration) | **Missing** — critical open question |

---

## 7. Immediate blockers visible at intake

| Blocker | Blocks? | Notes |
|---------|---------|-------|
| Secondary file delivery | No | File is in Source |
| File readability / schema | No | Standard Rate_Table layout |
| New unique rates vs current Rate_Table | No for Planning | Identical — Planning scopes **precedence/wiring**, not new rows |
| Fallback TYPE_CODE / grain rules | **Yes for Development** | Dependency Gate / client may need to confirm which PAAGERAT gaps Rate_Table may fill |
| Example policies | Soft | Helpful for Validation; not required to start Planning |

---

## 8. Severity / owner / priority

| Field | Value |
|-------|--------|
| Severity | **Medium** — source-authority / completeness; does not by itself add new rate rows |
| Owner | Conversion |
| Priority (Go/No-Go) | **No-Go** until Planning + Dependency Gate + Risk |
| Recommended next status | **Planning** |

---

## 9. Gate G0 checklist

- [x] Issue folder created: `Issue_Log_Items/Issue_48/`
- [x] Intake summary written
- [x] Example policies listed (**none provided**)
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

---

## 10. Recommended next stage

**Planning Agent** — document:

1. Explicit precedence: PAAGERAT → Rate_Table secondary when PAAGERAT key absent.
2. Candidate TYPE_CODEs where Rate_Table can legally fill a PAAGERAT gap (and where it cannot because grain differs).
3. Path resolution: Source `Rate_Table_Extract_Txt.txt` vs existing twin CSV (same bytes today).
4. Impact inventory: coverages/TYPE_CODEs present in Rate_Table but absent (or empty) in PAAGERAT.
5. Open questions for Dependency Gate (especially PR and other shared TYPE_CODEs with incompatible axes).
