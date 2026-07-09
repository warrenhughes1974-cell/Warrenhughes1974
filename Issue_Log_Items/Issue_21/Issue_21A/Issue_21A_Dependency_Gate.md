# Issue #21A — Dependency Gate

**Issue:** #21A — NFO / Dividend Options  
**Framework stage:** Dependency Gate (G2)  
**Date:** 2026-07-04  
**Planning reference:** `Issue_21A_Planning_Report.md`  
**Client scope lock (2026-07-04):** LifePRO codes **1–2** only (SME); codes **3–6 unchanged**; **7–9** not in QLAdmin crosswalk

---

## 1. Approved development scope

| In scope | Out of scope |
|---|---|
| PPBENTYP cache: read **`BF_NON_FORFEITURE`** when **`TYPE_CODE=BF`** (Track A) | Remap LifePRO codes **3, 4, 5, 6** — **leave existing translation as-is** |
| Translation: **`NF_2→1`** (APL/RPU → APL per SME) | Change **`NF_4→0`**, **`NF_5→0`**, or add **`NF_3`**, **`NF_6`** |
| Translation: **`NF_1→1`** if needed for consistency | Codes **7–9** (no QLAdmin target; existing **0** behavior) |
| Text keys for combined labels (**`NF_APL ETI`**, **`NF_APL RPU`**) → **1** if source returns text | Dividend Option redesign (unless BF-row cache gap blocks MDIVOPT) |
| Validator for codes **1–2** + BF cache + regression guards | Premium, MPOLICY, MPREM, quikplan.NFOINT |

**Crosswalk authority:** QLAdmin **`MNFOPT`** accepts **0–3 only** (`Master_Value_Translation.csv`). No **`NF_7`–`NF_9`**.

---

## 2. Checklist

### Source data

| Check | Status |
|-------|--------|
| PPBENTYP in `QLA_Migration/Source/` | **Met** — `PPBENTYP_BenefitType_Extract_20260530.csv` |
| Row count > 0 | **Met** — 5,083 seq-1 rows |
| Columns documented | **Met** — `NON_FORFEITURE`, `BF_NON_FORFEITURE`, `TYPE_CODE`, `DIVIDEND` |
| Extract date matches batch | **Met** — `20260530` |
| Re-extract required | **N/A** |

### Field definitions

| Check | Status |
|-------|--------|
| QLAdmin target table | **Met** — `quikmstr` |
| `MNFOPT` semantics | **Met** — **0–3 only** per translation file |
| `MDIVOPT` semantics | **Met** — **0–5** passthrough (`DV_*`) |
| LifePRO source semantics | **Met** — BA vs BF column trace complete (7/7 samples) |
| Transformation notes | **Met** — numeric shield after `NF_` prefix |

### Client clarification

| Check | Status |
|-------|--------|
| Code **1** (APL/ETI) → QLAdmin **APL (1)** | **Met** — SME 2026-07-04 |
| Code **2** (APL/RPU) → QLAdmin **APL (1)** | **Met** — SME 2026-07-04 |
| Codes **3–6** | **Met** — **no change** to current crosswalk behavior (Warren 2026-07-04) |
| Codes **7–9** | **Met** — not in QLAdmin crosswalk; remain **0** |
| ISWL dividend on blank BF `DIVIDEND` | **Open** — not blocking NFO scope |
| UAT acceptance | **Met** — 7 Issue #21 sample policies identified |

### Evidence

| Check | Status |
|-------|--------|
| Example policies | **Met** — 7 policies + Issue #38 numeric samples |
| Screenshots | **Met** — Issue #21 evidence folder |
| Before-state measurable | **Met** — v57.46 `quikmstr.csv` |
| Source trace | **Met** — `Issue_21A_Trace_Samples.csv` |

### Regression guards

| Check | Status |
|-------|--------|
| Issue #25 MPOLICY padding | **Met** — no MPOLICY logic change |
| Issue #26 MPREM | **Met** — quikridr premium untouched |
| Policies with LifePRO codes **3–6** unchanged | **Met** — explicit scope exclusion |
| Unrelated rulebooks | **Met** — quikmstr cache + translation only |

---

## 3. Expected outcomes after fix (narrow scope)

| Policy | Source | Before | After (approved scope) | Notes |
|---|---|:---:|:---:|---|
| 010765930C | BF `BF_NF=1` | 0 | **1** | Cache + code 1 |
| 010718309C | BF `BF_NF=1` | 0 | **1** | Cache + code 1 |
| 010818663C | BF `BF_NF=1` | 0 | **1** | Cache + code 1 |
| 010469666C | `NF=2` | 2 | **1** | `NF_2→1` only |
| 010391895C | BA `NF=4` | 0 | **0** | **No change** — code 4 out of scope |
| 010448806C | BA `NF=5` | 0 | **0** | **No change** — code 5 out of scope |
| 010713704C | BF `BF_NF=4` | 0 | **0** | **No change** — code 4 out of scope |

---

## 4. Gate status

**Status: PASS** (approved scope)

| Blocker | Resolution |
|---------|------------|
| SME codes 1–2 | **Cleared** |
| Scope for 3–6 | **Cleared** — explicitly excluded |
| PPBENTYP extract | **Met** |
| QLAdmin field defs | **Met** |

**Not blocking Risk/Development:** ISWL `MDIVOPT=0` when BF `DIVIDEND` blank (source-empty candidate).

---

## 5. G2 gate

- [x] Dependency gate document published
- [x] Status **PASS** for approved scope
- [x] No code changes in this stage

**Recommended issue status:** **Ready for Risk Review**

**Next stage:** Risk Agent → Development (when authorized)
