# Issue #71 — Planning Report

**Issue:** #71 — Rate / plan / policy BAND standardize to `00`  
**Framework stage:** Planning Agent  
**Status:** Ready for Dependency Gate  
**Generated:** 2026-07-14  
**Model:** Cursor Grok 4.5 (locked)  
**Scope decisions:** `Issue_71_Scope_Decisions.md`

---

## 1. Executive Finding

Policy Display cash values are zero for policies like **`010718309C`** because **`quikridr.MBAND=00`** (correct per Chris) while rate tables emit **`BAND=01`**. QLAdmin cannot join factors.  

**Direction:** Remap / emit all rate keys and plan band definitions as **`00`**. Policy side already matches. Only material risk is **QuikGps / QuikPlGp** multi-band collapse (duplicate keys if naïvely remapped).

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/? | Role |
|--------------|--------------|:-----------:|------|
| PDAGE / Rate_Table / PAAGE* | YE `*_20260102` + Rate_Table | Yes | LifePRO band often `1` → today mapped to QLAdmin `01` via `BAND_MAP` |
| Policy benefits / riders | PPBEN / batch ridr path | Yes | `MBAND` rulebook default **`00`** (not source-driven `01`) |

Band mismatch is **conversion emit**, not missing YE extract.

### Available source fields

| Field | Source | Notes |
|-------|--------|-------|
| LifePRO BAND | Rate extracts | Often `1`/`2`/`3` → `map_band` → `01`/`02`/`03` |
| Policy band | Rulebook default | Forced **`00`** (Chris) |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Domain | Source |
|-------|-------|------|--------|--------|
| quikridr | MBAND | C(2) | `00`–`03` | Schema + rulebook |
| QuikCvs / QuikNps / QuikTvs / … | BAND | C(2) | `00`–`03` | `rate_dbf_schema.py` |
| QuikPlCv / QuikPlTv / … | BAND | C(2) | `00`–`03` | same |
| QuikPlBd | BDCODE | C(2) | band codes | `BAND_LABEL`: `00`=NOT APPLICABLE |

**Repo references (population paths):**

| Location | Role |
|----------|------|
| `qla_core/rate_dbf_schema.py` | `BAND_MAP = {1→01,2→02,3→03}`; `map_band()` |
| `qla_core/rate_factor_loader.py` | Factor row BAND |
| `qla_core/rate_key_setup.py` | Key-table BAND |
| `qla_core/rate_member_setup.py` | QuikPlBd BDCODE / BDDESCR |
| `qla_core/rate_validation.py` | `BAND_DOMAIN = {00,01,02,03}` |
| `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | MBAND default `00` |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO / current emit | QLAdmin target | Transformation | Change? |
|------------------------|----------------|----------------|---------|
| Rate BAND `01` (from LP `1`) | Factor/key `BAND` | Force **`00`** at emit (or post-map) | **Yes** |
| Rate BAND `02`/`03` (GP only) | Factor/key `BAND` | Force **`00`** + collapse duplicates (keep former `01`) | **Yes** |
| QuikPlBd `BDCODE=01` | QuikPlBd | **`00`** / NOT APPLICABLE | **Yes** |
| quikridr MBAND | MBAND | Keep **`00`** | **No** (already correct) |

### Fields that must remain unchanged

| Target | Touch? |
|--------|--------|
| MPOLICY padding (#25) | **No** |
| quikridr.MPREM (#26) | **No** |
| NFOINT / MORT / ETIMORT | **No** |
| MUWCLASS / MSEX / MUNIT / MCV0 values | **No** (keys only for BAND) |
| LOANINTX (#70) | **No** |

---

## 5. Open Client Questions

1. **OBQ-71-1:** For `QuikGps` plans with true multi-band content (`5L01MA` etc.), is collapsing to a single `00` row (keep former `01` factors, drop `02`/`03`) acceptable for YE UAT?  
   - **Planning assumption (SD-71-5):** Yes unless CSO objects — document in Risk as Conditional Go surface.

2. **OBQ-71-2:** Confirm no product in this block requires QLAdmin band variation (`BDVARY*` = Y with live multi-band). Quick check: most CV plans are single-band today.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Band code | Always **`00`** (2-char) for this conversion fleet |
| QuikPlBd label | `NOT APPLICABLE` (`BAND_LABEL["00"]`) |
| Policy MBAND | Remain rulebook default **`00`** |
| Validation | `BAND_DOMAIN` already allows `00`; after fix expect **no** `01` on CV/NPS/TVS/PlCv for this book |

---

## 7. Policy Key Handling

- MPOLICY: unchanged (#25)  
- Crosswalk: unchanged  
- Rate seek key: `(PLAN, GENDER, UWCLASS, BAND, …)` with **BAND=`00`** matching `MBAND`

---

## 8. Estimated Record Counts (YE Output)

| Object | Rows | Current BAND | After |
|--------|-----:|--------------|-------|
| quikridr | 6,936 | `00` 100% | unchanged |
| QuikCvs | 38,047 | `01` | → `00` |
| QuikNps | 46,998 | `01` | → `00` |
| QuikTvs | 48,181 | `01` | → `00` |
| QuikNff | 18,525 | `01` | → `00` |
| QuikPlCv | 94 | `01` | → `00` |
| QuikPlTv | 160 | `01` | → `00` |
| QuikGps | 1,135 | `01`/`02`/`03` | → `00` + dedupe (~1080 collision rows) |
| QuikPlGp | 14 | mix | → `00` + dedupe |
| QuikPlBd | 75 | BDCODE `01`(+2/3) | → `00` |

---

## 9. Sample Trace

| Policy | Plan | MBAND now | Rate BAND now | After rate BAND | Expected UI |
|--------|------|-----------|---------------|-----------------|-------------|
| 010718309C | 1658C1 | 00 | 01 | **00** | CV lookup can resolve (still need Data Admin rebuild) |
| 010713704C | 1659C2 | 00 | 01 | **00** | same |
| 015000057C | 17CSI5 | 00 | 01 | **00** | same |

Stored `MCV0` on 010718309C (~986) must remain unchanged.

---

## 10. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| QuikGps key collisions on collapse | Medium | Dedupe keep-`01`-as-`00`; UAT GP plans |
| BDVARYCV=Y plans expecting multi-band | Low–Med | Inventory; most CV single-band |
| Partial Test_Validation reload without rates | Med | Publish full `rates/` + quikridr if touched |
| Operator skips Data Admin rebuild | Med | UAT checklist |

---

## 11. Recommended Risk Agent Prompt

```
Risk Agent — Issue #71 BAND→00

Read Issue_71_Intake_Summary.md, Issue_71_Planning_Report.md, Issue_71_Scope_Decisions.md.
Quantify before/after BAND remaps; simulate QuikGps collision collapse.
Go / Conditional Go / No-Go for Development.
No code.
```

---

## 12. Recommended Development Task (do not implement)

1. Surgical change in rate emit path (`map_band` / post-emit normalize) so **all** factor+key `BAND` values become **`00`** for this conversion.  
2. QuikPlBd: `BDCODE=00`, `BDDESCR=NOT APPLICABLE`.  
3. QuikGps/QuikPlGp: after remap, drop duplicate keys keeping former `01` content.  
4. Do **not** change quikridr MBAND default (already `00`).  
5. Bump `APP_VERSION` both `app.py` copies if engine path touched.  
6. Regen rates → publish `Output/rates` + `Test_Validation/rates`.  
7. Validator: assert no `BAND=01` on QuikCvs/QuikPlCv; sample `010718309C` keys align.

**Model for Development:** Composer 2.5 (locked).

---

## Gate Criteria (G1 — Planning Complete)

- [x] Planning report published  
- [x] Mapping + collision rule documented  
- [x] Open questions listed (assumed SD-71-5)  
- [x] No code changes  
