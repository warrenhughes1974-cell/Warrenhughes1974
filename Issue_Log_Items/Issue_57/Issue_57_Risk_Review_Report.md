# Issue #57 — Risk Review Report

**Issue:** #57 — NFO Option incorrect  
**Framework stage:** Risk Agent (G3)  
**Status:** **Conditional Go** — Ready for Development after user approval of **Option B**  
**Fallback simulated:** Option A (translation only) vs Option B (translation + remove `PAID_UP_TYPE→MNFOPT`)  
**Generated:** 2026-07-13  
**Agent/script:** Risk Agent (Cursor Grok 4.5) · `_risk_review_issue57_options.py` · `_risk_review_issue57_nfo.py`  

**Status note:** Risk analysis only — no production code changes unless later approved.

**Authority:** LifePRO Product Book §12 / 6.167 NFO list (Eric) + Eric example policies.

---

## Go / No-Go Recommendation

**CONDITIONAL GO — Option B required** — Fix `Master_Value_Translation.csv` (`NF_3→1`, `NF_4→2`, `NF_5→3`) **and** remove the rulebook row `PAID_UP_TYPE → MNFOPT`. Translation-only (**Option A**) fails Eric’s RPU example **010392763C** and leaves **~290** LifePRO code 4/5 policies wrong because `PAID_UP_TYPE` overwrites PPBENTYP NFO on the last rulebook write.

Eric’s tracking **No-Go** should be treated as cleared for **research**; Development still needs explicit user approval of Option B (larger blast radius than A, but Product-Book-correct).

---

## 1. Current vs Proposed Mapping

| LifePRO code | Name (Product Book) | Current behavior | Proposed QLA `MNFOPT` | Change? |
|:---:|------|------|:---:|:---:|
| 0 | Lapse | 0 | **0** | No |
| 1 | APL/ETI | `NF_1→1` | **1 APL** | No (#21A) |
| 2 | APL/RPU | `NF_2→1` | **1 APL** | No (#21A) |
| **3** | **APL** | Passthrough **3** (= QLA RPU) | **1 APL** | **Yes — add `NF_3,1`** |
| **4** | **ETI** | `NF_4→0` | **2 ETI** | **Yes — `NF_4→2`** |
| **5** | **RPU** | `NF_5→0` | **3 RPU** | **Yes — `NF_5→3`** |
| 6–8 | APL/AR, AR, Process | →0 / unmapped | **0** | No (no QLA equiv.) |
| 9 | Special | `NF_9→0` | **0** | No |

| Rulebook | Current | Proposed (Option B) | Change? |
|----------|---------|---------------------|---------|
| `NFO_OPT → MNFOPT` | Default 0 + PPBENTYP enrich | Keep | **No** |
| **`PAID_UP_TYPE → MNFOPT`** | Last write; maps LE/ET/RU/PU… via `NF_*` | **Delete row** | **Yes** |

**Why Option A is insufficient:** Rulebook order is `NFO_OPT` then `PAID_UP_TYPE`. Non-blank `PAID_UP_TYPE` skips enrich-on-zero and overwrites the PPBENTYP election. Eric **010392763C** has LP code **5** (RPU) but `PAID_UP_TYPE=PU` → stays **`MNFOPT=0`** under Option A.

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| `quikmstr.MMODPREM` | MODE_PREMIUM | **No** |
| `quikridr.MPREM` | #26 | **No** |
| MPOLICY padding | #25 | **No** |
| `MDIVOPT` | DIVIDEND cache | **No** |
| `MSTATUS` / `PUT_*` status composites | CONTRACT / PAID_UP_TYPE → **status** | **No** (status path stays; only MNFOPT dual-map removed) |
| #21A `NF_1` / `NF_2` | APL | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `Configs/Sync_Rulebook_quikmstr.csv` L19–20 | `NFO_OPT→MNFOPT`; **`PAID_UP_TYPE→MNFOPT` (defect)** |
| `Master_Value_Translation.csv` (+ Mapping mirror) | `NF_3` missing; `NF_4→0`; `NF_5→0` |
| `app.py` ~6475–6490 | Enrich-on-zero from PPBENTYP `NON_FORFEITURE` / BF |
| `app.py` ~6637–6639 | `NF_` prefix translation |
| `app.py` ~6452–6454 | `PAID_UP_TYPE` for **MSTATUS** only (`PUT_`) — correct path; do not remove |

---

## 4. Population Analysis

| Metric | Option A | Option B |
|--------|----------:|----------:|
| Policies analyzed | 5,083 | 5,083 |
| `MNFOPT` would change | **1,962** | **2,721** |
| Unchanged | 3,121 | 2,362 |
| Eric examples PASS | **4 / 5** | **5 / 5** |
| LP 4/5 still wrong vs Product Book | **~290** | **0** |

### Option A transitions (translation only)

| Before → After | Count | Meaning |
|----------------|------:|---------|
| 0 → 2 | 1,825 | Code 4 ETI fix (blank PUT) |
| 3 → 1 | 104 | Code 3 APL fix |
| 0 → 3 | 33 | Code 5 RPU fix (blank PUT) |

### Option B additional / corrected transitions (drop PUT→MNFOPT)

| Before → After | Count | Assessment |
|----------------|------:|------------|
| 0 → 2 | +189 vs A (total 2,014) | Code 4 with PUT PU/LP/SP now get ETI |
| 0 → 3 | +8 (total 41) | Code 5 with PUT=PU (incl. Eric RPU) |
| 3 → 2 | 93 | Code 4 was showing RPU from PUT=RU → correct to ETI |
| 2 → 0 | 175 | LP code 0 + PUT=LE had fake ETI from status — election is Lapse |
| 3 → 0 | 99 | Blank LP + PUT=RU had fake RPU — no PPBENTYP election |
| 3 → 1 / 2 → 1 / 0 → 1 | residual | Codes 1–2 / 3 aligning to APL |

**Intentional corrections vs collateral:** Collateral `2→0` / `3→0` on Lapse/blank elections is **desired** if PPBENTYP is authority for NFO **option** (status remains on `MSTATUS`).

---

## 5. Fallback Recommendation

| Option | Rows changed | Eric PASS | Assessment |
|--------|-------------:|----------:|------------|
| **A — Translation only** | 1,962 | 4/5 | **Reject** — fails 010392763C; ~290 LP4/5 still wrong |
| **B — Translation + remove `PAID_UP_TYPE→MNFOPT`** | 2,721 | **5/5** | **Recommended** |
| C — Also remap codes 6–8 to APL | N/A (0 in fleet) | — | Not needed; keep →0 |

**Recommended:** Option B.

**Codes 6/7/8:** Map to **0** (no QLA AR/Process). None observed in current fleet join.

---

## 6. Trace Policies (Eric)

| Policy | LP code | PUT | Before | Option A | Option B | Want | Pass? |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|------|
| **010367131C** | 4 ETI | — | 0 | **2** | **2** | 2 | A+B |
| **010148272C** | 4 ETI | — | 0 | **2** | **2** | 2 | A+B |
| **010143726C** | 4 ETI | — | 0 | **2** | **2** | 2 | A+B |
| **010392763C** | 5 RPU | **PU** | 0 | **0** | **3** | 3 | **B only** |
| **011221309C** | 3 APL | — | 3 (shows RPU) | **1** | **1** | 1 | A+B |

---

## 7. Top change classes (Option B)

| Class | Count |
|-------|------:|
| Code 4 → ETI (2), was 0 | 2,014 |
| Code 3 → APL (1), was 3 | ~106 |
| Code 5 → RPU (3), was 0 | 41 |
| PUT-driven fake ETI/RPU cleared when LP blank/0 | 274 |
| Code 4 was RPU(3) from PUT=RU → ETI(2) | 93 |

(Numeric field N/A — categorical option codes.)

---

## 8. Material Calculation Impact

| Category | Count | Notes |
|----------|------:|-------|
| Intentional Product Book corrections (codes 3/4/5) | ~2,200+ | Core #57 fix |
| Remove status-as-option contamination | ~274–759 | PUT no longer drives `MNFOPT` |
| Accidental premium/status drift | **0** | Different fields |

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** — untouched |
| Issue #26 MPREM / MMODPREM | **Preserved** — untouched |
| Issue #21A codes 1/2 → APL | **Preserved** — `NF_1`/`NF_2` unchanged |
| Issue #21A BF cache | **Preserved** — no app cache change required |
| `MSTATUS` PUT composites | **Preserved** — only MNFOPT rulebook dual-map removed |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Eric traces: 010367131C / 010148272C / 010143726C → `MNFOPT=2`
- [ ] Eric: 010392763C → `MNFOPT=3`
- [ ] Eric: 011221309C → `MNFOPT=1` (not 3)
- [ ] Sample code 1 BF policy still `MNFOPT=1` (#21A)
- [ ] `MDIVOPT`, `MSTATUS`, `MMODPREM`, `quikridr.MPREM` unchanged on Eric set
- [ ] `quikmstr` row count = 5,083
- [ ] MPOLICY width still 10 (#25)
- [ ] Spot-check PUT=LE policy: `MSTATUS` still LE-related status; `MNFOPT` follows PPBENTYP not LE

---

## 11. Recommended Development Agent Task

**Model:** Composer 2.5 (locked) — only after user says approved for Development.

1. **Translation (both files):**  
   `Master_Value_Translation.csv` and `QLA_Migration/Mapping/Master_Value_Translation.csv`  
   - Add `NF_3,1` and `NFO_3,1`  
   - Change `NF_4` / `NFO_4` from `0` → `2`  
   - Change `NF_5` / `NFO_5` from `0` → `3`  
   - Leave `NF_1`, `NF_2`, `NF_9`, `NF_LE`, `NF_RU`, `NF_ET` as-is  
2. **Rulebook:** Delete row `PAID_UP_TYPE,MNFOPT,0,...` from `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` (and mirror if any). **Do not** alter MSTATUS `PUT_` logic in `app.py`.  
3. **Do NOT change** enrich-on-zero / BF cache unless validator proves otherwise.  
4. Add `tools/validators/validate_issue57_mnfopt.py` — Eric five + fleet LP→MNFOPT checks.  
5. **Version bump:** Only if `app.py` is touched; Option B as specified needs **no** `app.py` edit. Document translation+rulebook release in Closure.  
6. Publish modified `quikmstr.csv` to `Output/Test_Validation/` after Validation PASS.

**Do NOT:** Remap codes 1/2; touch MPREM/MPOLICY; map codes 6–8 to non-zero without Eric; keep `PAID_UP_TYPE→MNFOPT`.

---

## Appendix

- Product Book screenshot: `Issue_Log_Items/Issue_57/evidence/LifePRO_ProductBook_NFO_codes.png`  
- Mapping correction: `Issue_57_NFO_Mapping_Correction.md`  
- Option simulation: `evidence/issue57_risk_options.csv`  
- Scripts: `QLA_Migration/_risk_review_issue57_options.py`, `_risk_review_issue57_nfo.py`  
- Related: Issue #21A (scope lock on codes 3–6 now superseded by Product Book + Eric)
