# Issue #57 — Planning Report

**Issue:** #57 — NFO Option incorrect  
**Framework stage:** Planning Agent  
**Status:** Planning complete · Dependency Gate **CONDITIONAL PASS** (see companion gate doc)  
**Generated:** 2026-07-13  
**Agent/script:** Planning Agent (Cursor Grok 4.5) · `QLA_Migration/_research_issue57_nfo_code4.py`  
**Engine analyzed:** current batch Output / `app.py` post-#21A (v57.47+)  

---

## 1. Executive Finding

Client example **010367131C** has LifePRO **ETI (code 4)** on PPBENTYP `NON_FORFEITURE` and QLAdmin **`MNFOPT=0`**. This is **working as designed under the #21A scope lock**: translation entries **`NF_4→0`** / **`NFO_4→0`** deliberately zero LifePRO ETI elections. The #21A BF cache fix is **not** the defect here — the golden policy is **TYPE_CODE=BA** and the code **is** cached; translation maps it to 0.

**Recommended direction:** Unlock LifePRO **code 4 → QLAdmin ETI (`MNFOPT=2`)** by changing **`NF_4` / `NFO_4`** from `0` to `2` (mirror both translation CSVs). Optionally unlock **code 5 → RPU (`MNFOPT=3`)** in the same change. Preserve enrich-on-zero guard and #21A **codes 1/2 → APL (1)**.

**Go/no-go for next stage:** Ready for **Risk Agent** to quantify ~**2,014** `0→2` policies (code 4) and optional ~**41** `0→3` (code 5). Development requires explicit unlock of the #21A codes 4/5 exclusion (client/Eric).

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| **PPBENTYP** | `PPBENTYP_BenefitType_Extract_20260630.csv` | Yes | ~7k (seq1 used) |
| PPOLC `NFO_OPT` | Rulebook default path | N/A | Often blank → 0; not primary |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Policy number | `POLICY_NUMBER` | 100% | Crosswalk → QLA |
| Benefit filter | `BENEFIT_SEQ=1` | Engine filter | Same as #21A |
| Traditional NFO | `NON_FORFEITURE` | BA rows | Golden: **4** |
| ISWL NFO | `BF_NON_FORFEITURE` | BF rows | Code 4 also common (953 fleet) |
| Dividend | `DIVIDEND` | — | Out of scope |

**LifePRO numeric NFO meanings (from #21A / Product Book / client #57):**

| LifePRO code | Meaning | QLAdmin target |
|:---:|:---|:---:|
| 1 | APL/ETI (APL first) | **1** APL (#21A) |
| 2 | APL/RPU (APL first) | **1** APL (#21A) |
| 3 | RPU (typical) | **3** passthrough |
| **4** | **ETI** | **2** ← **this issue** |
| **5** | **RPU** | **3** ← optional companion |
| 9 | Special / non-convertible | **0** (#21A safety) |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| quikmstr | **MNFOPT** | C | 1 | 0=none, **1=APL**, **2=ETI**, **3=RPU** |

**Repo references** (population paths only):

| Location | Role |
|----------|------|
| `Sync_Rulebook_quikmstr.csv` | `NFO_OPT→MNFOPT` default 0 |
| `app.py` PPBENTYP cache | Loads `NON_FORFEITURE` / `BF_NON_FORFEITURE` (#21A) |
| `app.py` enrich-on-zero | Pulls cache only when `MNFOPT` is 0/blank |
| `app.py` `NF_` prefix | Translation lookup |
| `Master_Value_Translation.csv` | **`NF_4,0`** / **`NFO_4,0`** — root of defect |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPBENTYP | `NON_FORFEITURE` / `BF_NON_FORFEITURE` | `MNFOPT` | Cache → `NF_*` / `NFO_*` | No (cache OK) |
| Translation | LifePRO **4** | `MNFOPT` | **`NF_4` / `NFO_4` → `2`** | **Yes** |
| Translation | LifePRO **5** (optional) | `MNFOPT` | **`NF_5` / `NFO_5` → `3`** | **Yes if in scope** |
| Translation | Codes 1/2 | `MNFOPT` | `NF_1`/`NF_2` → 1 | **No** |
| Translation | Code 9 | `MNFOPT` | `NF_9` → 0 | **No** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| MPOLICY padding | format_qladmin_mpolicy (#25) | **No** |
| MDIVOPT | DIVIDEND cache | **No** |
| MNFOPT for codes 1/2 | NF_1/NF_2 → 1 | **No** |
| Non-zero MNFOPT (guard) | enrich-on-zero | **No overwrite** |

---

## 5. Open Client Questions

1. **Unlock #21A scope:** Confirm LifePRO **code 4 (ETI) → `MNFOPT=2`** is approved for conversion (replaces prior “codes 3–6 unchanged” lock).  
2. **Code 5 companion:** Include LifePRO **code 5 (RPU) → `MNFOPT=3`** in the same fix (**41** policies at 0), or defer?  
3. **Code 4 already at `MNFOPT=3`:** **93** policies have source code 4 but current `MNFOPT=3` — enrich-on-zero will **leave them at 3**. Confirm that is acceptable (do not force overwrite to 2).  
4. **UAT acceptance:** Golden **010367131C** must show NFO = **ETI (2)** in QLAdmin after reload.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + 10-char MPOLICY padding (#25) |
| NFO digits | QLAdmin domain 0–3 only |
| Blanks / zeros | Enrich only when current `MNFOPT` is 0/blank |
| Codes 7–9 | Remain 0 |

---

## 7. Memo / Text / Special Handling

N/A — single-digit option field.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `Master_Crosswalk.csv` → QLA  
2. Apply `format_qladmin_mpolicy()` for CHARACTER(10) keys  
3. Orphan policies: skip (no quikmstr row)

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| Converted `quikmstr` rows | 5,083 | Current Output |
| Fleet policies with LP code **4** | **2,336** | PPBENTYP seq1 + crosswalk |
| Code 4 currently `MNFOPT=0` (would → **2**) | **2,014** | Research script |
| Code 4 already `MNFOPT=2` (unchanged) | 229 | Guard |
| Code 4 already `MNFOPT=3` (unchanged by guard) | 93 | Client Q3 |
| Code 5 currently `MNFOPT=0` (optional → **3**) | **41** | Research script |
| Code 5 already `MNFOPT=3` | 24 | Unchanged |

Evidence: `Issue_Log_Items/Issue_57/evidence/issue57_nfo_code4_fleet.csv`

---

## 10. Sample Trace (5 policies)

| Policy (QLA) | LifePRO LP | Source | Before `MNFOPT` | After (proposed) | Status |
|--------------|------------|--------|----------------:|-----------------:|--------|
| 010367131C | 9010367131 | BA / NON_FORFEITURE=**4** | **0** | **2** | Client golden |
| 010391895C | 9010391895 | BA / 4 | 0 | **2** | #21A residual |
| 010713704C | 9010713704 | BF / BF_NON_FORFEITURE=4 | 0 | **2** | #21A residual |
| 010391876C | 9010391876 | BA / 4 | **2** | **2** | Must not change |
| 010448806C | 9010448806 | BA / **5** | 0 | **3** (if unlocked) | Optional |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Large blast radius (~2k `MNFOPT` changes) | High | Risk Agent simulation; UAT sample set |
| Overwriting correct non-zero options | Medium | Keep enrich-on-zero guard |
| 93 policies code4@`MNFOPT=3` stay 3 | Medium | Client Q3; do not force rewrite |
| Accidental change to codes 1/2 APL rule | High | Do not touch `NF_1`/`NF_2` |
| Confusing NFO **option** with ETI **status** | Low | Document; MSTATUS untouched |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes |
| Field definitions confirmed | Yes (QLA 0–3; LP 4=ETI) |
| Client scope clear | **Partial** — #57 unlocks code 4; code 5 TBD |
| Example policies available | Yes |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #57.

Read AI_Agents/Risk_Agent.md and AI_Agents/Templates/Risk_Report_Template.md.
Model: Cursor Grok 4.5 (locked). Do not code.

Context: #21A left NF_4→0 / NF_5→0. Client #57: LifePRO ETI (code 4) shows MNFOPT=0;
golden 010367131C. Propose NF_4/NFO_4→2 and optional NF_5/NFO_5→3.
Use Issue_57_Planning_Report.md and evidence/issue57_nfo_code4_fleet.csv.
Quantify 0→2 / 0→3 / unchanged (guard). Preserve #21A codes 1/2→1, #25, #26.
Produce go/no-go with client unlock prerequisites.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Change `Master_Value_Translation.csv` and `QLA_Migration/Mapping/Master_Value_Translation.csv`:  
   - `NF_4,0` → `NF_4,2`  
   - `NFO_4,0` → `NFO_4,2`  
   - If approved: `NF_5,0` → `NF_5,3` and `NFO_5,0` → `NFO_5,3`  
2. **Do not** change `app.py` unless validation proves translation prefix path misses numeric `4` (unlikely — #21A used same path). If no engine change, still document version bump only if required by project convention for translation-only releases (prefer bump if batch reload expected).  
3. Add `tools/validators/validate_issue57_mnfopt.py` — golden + fleet counts.  
4. Version bump: only if `app.py` touched; otherwise note translation-only release in Closure.  
5. Regression: codes 1/2 distribution stable; non-candidate `MNFOPT` unchanged; MPOLICY/MPREM untouched.

---

## Appendix

- Diagnostic script: `QLA_Migration/_research_issue57_nfo_code4.py`  
- Fleet evidence: `Issue_Log_Items/Issue_57/evidence/issue57_nfo_code4_fleet.csv`  
- Related: `Issue_Log_Items/Issue_21/Issue_21A/*`  
- References: #21A Planning (codes 3–6 scope lock); `Master_Value_Translation.csv` `NF_ETI,2` / `NF_4,0`
