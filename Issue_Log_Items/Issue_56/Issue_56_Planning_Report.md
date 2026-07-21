# Issue #56 — Planning Report

**Issue:** #56 — PUA CV is incorrect  
**Framework stage:** Planning Agent  
**Status:** Ready for Risk Review *(with open client questions — see Dependency Gate)*  
**Generated:** 2026-07-13  
**Agent/script:** Planning Agent (Cursor Grok 4.5) — read-only Output/Source/Mapping traces  
**Model:** Cursor Grok 4.5 (locked)

---

## 1. Executive Finding

On **010310404C**, LifePRO PUA plan **`960 PO PUA`** crosswalks to catalog plan **`1POPUA`**, but conversion **rewrites** the PUA rider `MPLAN` to synthetic **`1960PA`** (`base_mplan[:4] + "PA"` from base `1960PO`). **`Output/rates` has no QuikCvs (and no QuikPlCv) rows for `1960PA` or `1POPUA`**, while LifePRO holds **attained-age CV** for `960 PO PUA` in **PAAGERAT** (200 CV rows — Issue #48 inventory: PRIMARY_ONLY).

Client-reported PUA CV **$6,628.32** exceeds PUA face **$5,942.78** (`5.94278 × $1000`), which is actuarially implausible. Correct PAAGERAT CV × units at attained ages near current age would be **below** face (e.g. ~$4,928 at age 83). Base coverage CV matching LifePRO is treated as **out of scope** for this issue.

**Direction for Risk:** Quantify blast radius of (A) stopping/changing PUA `MPLAN` rewrite vs (B) emitting PUA QuikCvs from PAAGERAT under the plan key QLAdmin actually seeks — **do not code** until G3 and client answers on correct LifePRO CV + intended plan key.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Notes |
|--------------|--------------|---------------------|-------|
| Policy Benefit | `PPBEN_PolicyBenefit_Extract_20260630.csv` | Yes | PUA plan, units, ages |
| Benefit Type | `PPBENTYP_BenefitType_Extract_20260630.csv` | Yes | `PU_ACCRU_FACE_AMT` |
| Attained-age rates | `PAAGERAT_AttainedAge_Rates_Extract_20260630.csv` | Yes | `960 PO PUA` CV + PU |
| Age/duration rates | `PDAGE_…` / `Rate_Table_Extract_Txt.txt` | Yes | Base `960 PO` CV path (control) |
| Crosswalk | `Mapping/Master_Crosswalk.csv` | Yes | `960 PO PUA` → `1POPUA` |

### Sample policy — `9010310404` → `010310404C`

| Seq | Type | PLAN_CODE | ISSUE_AGE | NUMBER_OF_UNITS | Face | Notes |
|-----|------|-----------|----------:|----------------:|-----:|-------|
| 1 | BA | `960 PO` | 26 | 15.00000 | $15,000.00 | Base — client says CV OK |
| 2 | PU | `960 PO PUA` | **68** | 5.94278 | **$5,942.78** | `PU_ACCRU_FACE_AMT=5942.78`; `AUX_AGE=26` |

### PAAGERAT for `960 PO PUA`

| TYPE_CODE | Rows | Role |
|-----------|-----:|------|
| CV | 200 | Attained-age cash value factors (client hypothesis confirmed present) |
| PU | 234 | Paid-up / related factors |

Male CV SEQ≈age values are per-$1000-style factors (e.g. age 83 ≈ **829.28** → × 5.94278 ≈ **$4,928**), not the client’s $6,628.32.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field / object | Role |
|-------|----------------|------|
| `quikridr` | `MPLAN` | Rider plan key used to find CV rates |
| `quikridr` | `MUNIT` / `MVPU` / `MAGE` | Units, VPU, issue age on rider |
| `quikridr` | `MCV0/1/2` | Blank on traditional (by design #21E) |
| `Output/rates/QuikCvs` | CV grid by PLAN/AGE/duration | Traditional CV compute |
| `Output/rates/QuikPlCv` | Plan → CV table pointer | Must exist for plan |
| `quikplan` | Plan master | **`1POPUA` present; `1960PA` absent** |

**Current emit for sample:**

| MPHASE | MPLAN | MAGE | MUNIT | MCV* |
|-------:|-------|-----:|------:|------|
| 1 | `1960PO` | 26 | 15.00000 | blank |
| 2 | **`1960PA`** | 68 | 5.94278 | blank |

**Engine rule (confirmed):** `QLA_Migration/app.py` `_apply_pua_rider_inheritance`:

```text
new_mplan = base_mplan[:4] + "PA"   # 1960PO → 1960PA
```

`1POPUA` is listed in `PAID_UP_ADDITION_PRODUCTS`, so after crosswalk the rewrite fires.

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPBEN | `PLAN_CODE` `960 PO PUA` | `quikridr.MPLAN` | Crosswalk → **`1POPUA`**, then **overwritten** to `*PA` | **Likely Yes** — plan identity / rate attachment |
| PAAGERAT | `960 PO PUA` / `CV` | `QuikCvs` (+ `QuikPlCv`) under chosen PUA plan key | Attained-age → QLA CV grid (mechanism TBD) | **Likely Yes** — rates missing today |
| PPBEN | `NUMBER_OF_UNITS` | `MUNIT` | Direct | **No** |
| PPBEN | `VALUE_PER_UNIT` | `MVPU` | Direct | **No** |
| Base QuikCvs | `960 PO` / `1960PO` | Base CV compute | Existing | **No** (client: base matches) |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| Base `1960PO` QuikCvs / QuikPlCv | Rate pipeline | **No** |
| `quikridr.MPREM` | #26 | **No** |
| MPOLICY padding | #25 | **No** |
| UL `MCV0` / FV_BALANCE2 | #21E UL | **No** |
| Non-CV PUA inheritance (`261PUA` NP/RV/DV) | Separate actuarial track | **No** |

### Competing fix options (for Risk — do not implement yet)

| Option | Idea | Pros | Cons |
|--------|------|------|------|
| **A** | Keep synthetic `*PA` MPLAN; emit QuikCvs/QuikPlCv for each `*PA` from LifePRO PUA attained-age CV (or approved inheritance) | Matches current rider keys in Output | `1960PA` not in `quikplan`; many synthetic plans (`1708PA` 415 rows, `1960PA` 71, …) |
| **B** | Stop `[:4]+"PA"` rewrite; keep catalog `1POPUA` / peer PUA plans; emit QuikCvs under those keys from PAAGERAT | Aligns with crosswalk + `quikplan` | Changes rider MPLAN fleet-wide; may break any QLA setup expecting `*PA` |
| **C** | Point `*PA` QuikPlCv at base plan CV tables | Smaller rate emit | **Likely wrong** — client ties defect to **PUA attained-age** rates, not base duration CV |

---

## 5. Open Client Questions

1. **What is LifePRO’s correct PUA cash value** for `010310404C` as of the extract / UAT date? (Dollar amount for acceptance.)  
2. Please confirm **PUA death benefit / face** = **$5,942.78** (or provide LifePRO screen).  
3. Where is **$6,628.32** shown in QLAdmin (Coverage CV, Projected Values, Values tab)? Screenshot preferred.  
4. Should PUA riders use catalog plans (**`1POPUA`**, etc.) or the conversion synthetic **`xxxxPA`** keys in QLAdmin product setup?  
5. Confirm **attained-age CV** (PAAGERAT `TYPE_CODE=CV`) is the authority for PUA cash values (vs duration tables / other).  
6. Any additional sample policies beyond `010310404C`?

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + 10-char MPOLICY padding (#25) |
| PUA face | `MUNIT × MVPU`; preserve decimals (#21K display separate) |
| Money / CV rates | Match existing QuikCvs scale (per $1000) used for traditional plans |
| Blanks | Traditional `MCV0/1/2` remain blank unless #21E UL |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. `9010310404` → `010310404C` via `Master_Crosswalk.csv`  
2. `format_qladmin_mpolicy()` for CHARACTER(10)  
3. Orphans: existing batch behavior — do not change for this issue  

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| `quikridr` rows with `MPLAN=1960PA` | **71** | Current Output |
| Other synthetic `*PA` PUA-like plans | e.g. `1708PA` **415**, `280EPA` 3, … | Fleet rewrite pattern |
| `quikplan` row `1POPUA` | **1** | Present |
| `quikplan` / QuikCvs `1960PA` | **0** | Missing |
| PAAGERAT `960 PO PUA` CV | **200** | Source |
| Policies with LifePRO `960 PO PUA` | ~71 (aligns with `1960PA`) | PPBEN |

---

## 10. Sample Trace

| Policy (QLA) | LifePRO | Before (current) | After (proposed — pending Risk/client) | Status |
|--------------|---------|------------------|----------------------------------------|--------|
| `010310404C` | `9010310404` | PUA `MPLAN=1960PA`, no QuikCvs; QLA CV **$6,628.32** (client); face **$5,942.78** | PUA plan key + QuikCvs from `960 PO PUA` CV; CV ≤ face and match LifePRO | Trace ready |
| Peer `1960PA` (e.g. `010331768C`) | `9010331768` | Same rewrite pattern | Same class of fix | Fleet peer |
| Base-only control | — | Base CV OK per client | **Unchanged** | Control |

*(Only one client-named policy; peers selected from same `1960PA` population.)*

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Wrong fix option (A vs B) breaks New Era product setup | High | Client Q4 before Development |
| Emitting wrong CV scale/placement (#37/#41 class bugs) | High | Golden LifePRO CV + validator |
| Touching base `1960PO` rates while “fixing” PUA | High | Explicit non-touch list; regression on base CV |
| Large `*PA` fleet (`1708PA` etc.) | Medium | Risk count by plan family |
| $6,628.32 derivation still unexplained | Medium | Screenshot + QLAdmin calc path with client |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | **Yes** |
| Field definitions confirmed | **Partial** — target plan key ambiguous (`1POPUA` vs `1960PA`) |
| Client scope clear | **Partial** — symptom clear; acceptance CV missing |
| Example policies available | **Yes** (1 named + fleet peers) |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #56.

Read AI_Agents/Risk_Agent.md and AI_Agents/Templates/Risk_Report_Template.md.
Model: Cursor Grok 4.5 (locked). Do not code.

Context: PUA riders rewritten to synthetic MPLAN (*PA); no QuikCvs for 1960PA/1POPUA;
LifePRO 960 PO PUA CV lives in PAAGERAT (attained age). Sample 010310404C PUA CV
$6,628.32 > face $5,942.78; base CV OK.

Produce before/after impact for options A (rates under *PA) vs B (keep 1POPUA + rates)
vs C (point *PA at base CV — likely reject). Quantify quikridr *PA populations.
Preserve #25/#26 and base 1960PO CV path. Go/No-Go with conditions.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. After Risk + client answers: pick Option A or B.  
2. Surgical change only in PUA plan rewrite and/or rate emit for PUA CV (PAAGERAT → QuikCvs/QuikPlCv).  
3. **Do not** alter base `1960PO` QuikCvs content.  
4. Version bump both root and `QLA_Migration/app.py` if engine touched.  
5. Validator: `QLA_Migration/_validate_issue56_pua_cv.py` — sample `010310404C` PUA plan key, QuikCvs present, CV≤face smoke, LifePRO CV tolerance once client dollar known.  
6. Publish modified tables to `Output/Test_Validation/` on PASS.

---

## Appendix

- Intake: `Issue_Log_Items/Issue_56/Issue_56_Intake_Summary.md`  
- Related: #21E, #37, #40, #41, #21K, #48 (PAAGERAT inventory), #21F (same policy, unrelated)  
- Engine: `_apply_pua_rider_inheritance` / `PAID_UP_ADDITION_PRODUCTS` in `app.py`  
- Preserve: Issue #25 MPOLICY, Issue #26 MPREM  
