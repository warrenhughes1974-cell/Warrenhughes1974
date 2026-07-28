# Issue #121 — Planning Report

**Issue:** #121 — Annual Renewable Term must not emit ETI status  
**Date:** 2026-07-28  
**Framework stage:** Planning complete (G1)  
**Code changes:** none (prohibited; Development held for research)

---

## 1. Executive finding

On **`5667AT`** (LifePRO `667 ART`), **90 policies** emit ETI (`MSTATUS` 44) because `PAID_UP_TYPE=LE` maps via `ST_PUT_LE` → 44. ART must not be ETI.

ART-family research found **two sibling products** (`5646AT` / `646 ART`, `57ATCR` / `667 ART CR`). They share `PUT=LE` but are terminated (T/LP) and correctly emit **54** via Issue #13 — **no current ETI**. Recommended fix: suppress PUT `LE`/`ET` for the **entire ART family**, not only `5667AT`.

Simulated impact today: **90** status changes on `5667AT` only (86 → 22, 4 → 54); siblings unchanged.

---

## 2. Confirmed LifePRO source(s)

| Source | Role |
|--------|------|
| PPOLC | `CONTRACT_CODE`, `CONTRACT_REASON`, `PAID_UP_TYPE` |
| PPBEN | LifePRO plan (`667 ART`, `646 ART`, `667 ART CR`) |
| Crosswalk / modal factors | QL emit `5667AT`, `5646AT`, `57ATCR` |

See `Issue_121_ART_Family_Research.md`.

---

## 3. Confirmed QLAdmin target

| Table | Field | Rule |
|-------|-------|------|
| `quikmstr` | `MSTATUS` | Never `44` on ART family |
| `quikridr` | `MPHSTAT` | Follow corrected master status |

---

## 4. Proposed mapping

| Step | Current | Proposed |
|------|---------|----------|
| MSTATUS interceptor | PUT in `{PU,RU,ET,LE,LP,SP}` → `PUT_*` | If base plan is ART family **and** PUT in `{LE,ET}` → use `CONTRACT_CODE`+`REASON` instead |
| ART family detect | n/a | QL: `5667AT`, `5646AT`, `57ATCR` **or** LifePRO: `667 ART`, `646 ART`, `667 ART CR` |
| Global `ST_PUT_LE` | 44 | **Unchanged** |

### Untouched

#25/#2 MPOLICY, #26 MPREM, non-ART ETI, rate/CV holds for ART.

---

## 5. Open client questions

| ID | Question | Default |
|----|----------|---------|
| OQ-1 | Active+LE on ART → Active **22**? | **Yes** |
| OQ-2 | Scope all three ART plans preventively? | **Yes — ART family** |
| OQ-3 | Block both LE and ET on ART? | **Yes** |

---

## 6. Counts

| Population | Count |
|------------|------:|
| ART family policies | 197 |
| False ETI today | **90** (all `5667AT`) |
| Sibling ART (clean) | 2 |
| Would change if Option A applied now | 90 |

---

## 7. Sample trace

| MPOLICY | Plan | Now | Proposed |
|---------|------|-----|----------|
| 9010764158C | 5667AT | 44 | **22** |
| 9010761450C | 5667AT | 44 | **54** |
| 9010516211C | 5646AT | 54 | 54 |
| 9010916282C | 57ATCR | 54 | 54 |

---

## 8. Dev surfaces (when approved)

1. MSTATUS interceptor ART-family guard  
2. Align phase-1 `MPHSTAT` for the 90  
3. Validator: zero ETI on ART family; siblings remain non-ETI  
4. Version bump both `app.py` copies  
5. Do not globally remap `ST_PUT_LE`  
