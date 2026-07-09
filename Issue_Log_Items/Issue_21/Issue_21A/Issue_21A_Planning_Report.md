# Issue #21A — Planning Report

**Issue:** NFO / Dividend Options  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete · **Dependency Gate PASS** (G2)  
**Scope lock:** Codes **1–2** + BF cache only; codes **3–6 unchanged**  
**Generated:** 2026-07-04  
**Engine analyzed:** v57.46 (`app.py` / `QLA_Migration/app.py`)  
**Agent:** Planning Agent (read-only research)

---

## 1. Executive finding

**Confirmed defect:** `quikmstr.MNFOPT` fails to reflect LifePRO non-forfeiture elections for a large share of the fleet (**3,768 / 5,083** policies show `0`). Issue #21 ISWL validation policies (ETI, RPU, APL ETI) remain at **0** despite LifePRO screenshots showing real elections. **`MDIVOPT`** is partially working (**811** non-zero) but **4 ISWL samples** still show **0** in the current batch.

**Confirmed root cause (two tracks, independent):**

| Track | Layer | Finding |
|---|---|---|
| **A — ISWL / BF rows** | PPBENTYP cache | Engine reads only column **`NON_FORFEITURE`** on **`BENEFIT_SEQ=01`**. ISWL whole-life NFO lives on **`BF_NON_FORFEITURE`** when **`TYPE_CODE=BF`** (2,348 PPBENTYP rows in May extract). That column is **never loaded**. |
| **B — Code 2 only** | Value translation | LifePRO code **2** passthroughs to QLAdmin **2** — SME says **1** (APL). Codes **3–6** **out of scope** — leave **`NF_4→0`**, **`NF_5→0`**, and passthrough **unchanged**. |

**Approved direction:** (1) PPBENTYP cache reads **`BF_NON_FORFEITURE`** for **`TYPE_CODE=BF`**; (2) add **`NF_2→1`** (and **`NF_1→1`** if needed). **No changes** to LifePRO codes **3–6**. **7–9** stay **0**.

**Dependency Gate:** **PASS** — see `Issue_21A_Dependency_Gate.md`. **Next:** Risk Agent.

---

## 2. Confirmed LifePRO source table/file(s)

| Source table | File pattern | In local Source/? | Row grain (May 20260530 profile) |
|---|---|:---:|---|
| **PPBENTYP** — Benefit Type | `PPBENTYP_BenefitType_Extract_20260530.csv` | **Yes** | Policy + Benefit Seq + **Type_Code** (BA/BF at seq 1) |
| **PPOLC** — Policy Master | `PPOLC_PolicyMaster_Extract_*.csv` | No | Policy; rulebook maps **`NFO_OPT → MNFOPT`** (often blank/0) |
| **PPCOM** — PAC billing | `PROD_PPCOM_*.csv` | No | Has `NF_OPTION` / `DIVIDEND_OPTION` — **not** primary path per Issue #21 analysis |

### PPBENTYP structure (May 20260530 zip profile — authoritative for Planning)

| Field | Column | TYPE_CODE context | Notes |
|---|---|---|---|
| Policy key | `POLICY_NUMBER` | all | Join via crosswalk |
| Benefit filter | `BENEFIT_SEQ` | all | Engine filters seq **01** only |
| Product type row | `TYPE_CODE` | BA:2,735 · **BF:2,348** · SU:1,210 · … | Multiple rows per policy possible |
| NFO (traditional) | `NON_FORFEITURE` | **BA** rows | Numeric LifePRO codes (`4` = ETI on sample 9010143726) |
| NFO (whole-life / ISWL) | **`BF_NON_FORFEITURE`** | **BF** rows | Client cited as authoritative for ISWL; **not read today** |
| Dividend | `DIVIDEND` | BA (+ others) | Numeric; `DV_*` passthrough 1–5 |

**Important correction vs Issue #21 draft:** `BF_NON_FORFEITURE` is a **separate column** on the same PPBENTYP file, not an alias for `NON_FORFEITURE`. Client “Col DB” reference maps to this BF-segment field.

---

## 3. Confirmed QLAdmin target structure

From `validation_config/schema_manifest.json` and Issue #21 UAT screenshots:

| Table | Field | QLAdmin meaning | Format |
|---|---|---|---|
| **quikmstr** | **`MNFOPT`** | Non-Forfeiture Option | Single digit: **0=none/lapse, 1=APL, 2=ETI, 3=RPU** — **no codes 4–9** |

### QLAdmin NFO crosswalk authority (`Master_Value_Translation.csv`)

QLAdmin **`MNFOPT`** accepts only **four values**. The translation file defines the full target set — there are **no `NF_7`, `NF_8`, or `NF_9` entries** and no QLAdmin equivalents for LifePRO AR / Process / Special:

| QLAdmin `MNFOPT` | Translation keys (existing) |
|:---:|---|
| **0** | `NF_NONE`, `NF_BLANK`, `NF_PU`, `NF_SP`, `NF_LP`, `NF_UM`, `NF_` (blank), erroneous `NF_4`, `NF_5` |
| **1** | `NF_APL`, `NF_API`, `NFO_APL` |
| **2** | `NF_ETI`, `NF_ET`, `NF_LE`, `NFO_ETI` |
| **3** | `NF_RPU`, `NF_RU`, `NFO_RPU` |

**Planning rule:** LifePRO Product Book codes **7, 8, 9** are **not convertible** to a distinct QLAdmin NFO code. If they appear in source, they follow the same pattern as other non-mapped LifePRO values → **`MNFOPT = 0`**. (Source scan: **`BF_NON_FORFEITURE = 9`** on **83** policies; no codes 7 or 8 in the May extract.)

| **quikmstr** | **`MDIVOPT`** | Dividend Option | Single digit **0–5** (`DV_0`–`DV_5` passthrough; `DV_6`–`DV_9` → 0) |

**Repo references:**

| Location | Role |
|---|---|
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` | `NFO_OPT→MNFOPT` default 0; `MDIVOPT` default 0 |
| `app.py` ~5327–5356 | PPBENTYP cache: `NON_FORFEITURE`, `DIVIDEND` only |
| `app.py` ~5858–5875 | Pull cache when rulebook value is 0 |
| `app.py` ~6012–6018 | `NF_` / `DV_` prefix translation + numeric shield |
| `Master_Value_Translation.csv` | Text + broken numeric NFO mappings |
| `Issue_Log_Items/Issue_21/reports/Issue_21_Final_Analysis.md` | Screenshot-validated defect |

---

## 4. Required source-to-target field mapping

### Track A — ISWL / BF segment (primary fix for Issue #21 samples)

| LifePRO source | LifePRO field | Filter | QLAdmin target | Transformation | Change? |
|---|---|---|---|---|---|
| PPBENTYP | `POLICY_NUMBER` | seq 1 | `MPOLICY` | Crosswalk + `format_qladmin_mpolicy()` (#25) | No |
| PPBENTYP | **`BF_NON_FORFEITURE`** | **`TYPE_CODE=BF`**, seq 1 | **`MNFOPT`** | Text → `NF_*` translation (APL ETI → 1) | **Yes** |
| PPBENTYP | `DIVIDEND` | BF or BA row with value | `MDIVOPT` | `DV_*` passthrough | **Maybe** (if ISWL div on BF row) |

**Cache resolution order (proposed):**

1. If **`TYPE_CODE=BF`** row exists at benefit seq 1 with non-blank **`BF_NON_FORFEITURE`** → use that value.
2. Else if **`NON_FORFEITURE`** populated on seq 1 row → use that value (current behavior).
3. Else keep rulebook default / `NFO_OPT` from PPOLC.

### Track B — LifePRO codes 1–2 only (SME-approved)

**Client scope lock (2026-07-04):** Do **not** change translation for LifePRO codes **3, 4, 5, or 6**. Existing crosswalk entries (**`NF_4→0`**, **`NF_5→0`**, passthrough for **3** / **6**) **remain as-is**.

| LifePRO code | SME / client rule | QLAdmin `MNFOPT` | Change? |
|:---:|:---|:---:|:---:|
| **1** | APL/ETI → APL | **1** | Add **`NF_1→1`** if needed; mostly passthrough today |
| **2** | APL/RPU → APL | **1** | **`NF_2→1`** (new) — fixes 2 policies on wrong **2** today |

#### LifePRO codes 3–6 — no change

| Code | Current engine behavior | Action |
|:---:|:---|:---:|
| **3** | Passthrough → `MNFOPT=3` | **Leave** |
| **4** | `NF_4→0` | **Leave** |
| **5** | `NF_5→0` | **Leave** |
| **6** | Passthrough (if seen) | **Leave** |

#### LifePRO codes 7–9 — not in QLAdmin crosswalk

Default **`MNFOPT=0`**. Optional explicit **`NF_9→0`** only if passthrough would emit invalid digit; **83** BF policies have source **9**.

#### Text label → QLAdmin (existing + new)

| LifePRO text | Translation key | QLAdmin | Status |
|---|---|:---:|:---|
| APL | `NF_APL` | 1 | Exists |
| ETI | `NF_ETI` | 2 | Exists |
| RPU | `NF_RPU` | 3 | Exists |
| **APL ETI** / **APL/ETI** | **`NF_APL ETI`** (new) | **1** | SME implied |
| **APL RPU** / **APL/RPU** | **`NF_APL RPU`** (new) | **1** | SME implied |
| ET | `NF_ET` | 2 | Exists |
| RU | `NF_RU` | 3 | Exists |

**Development translation changes only:** add **`NF_2→1`**, **`NF_1→1`**; add text **`NF_APL ETI`**, **`NF_APL RPU`** → **1** if needed. **Do not modify `NF_3`–`NF_6` or `NF_4`/`NF_5` zero mappings.**

### Track C — Dividend Option

| LifePRO source | Field | QLAdmin | Transformation | Change? |
|---|---|---|---|---|
| PPBENTYP | `DIVIDEND` | `MDIVOPT` | `DV_0`–`DV_5` passthrough (already in translation file) | Fix cache only if BF-row gap |

**Current batch note:** 010391895C and 010448806C already show **`MDIVOPT=4`** — dividend cache works for some products. ISWL samples with **`MDIVOPT=0`** may need Track A cache fix, not new dividend translation.

### Fields that must remain unchanged

| Target | Current behavior | Touch this issue? |
|---|---|---|
| `quikmstr.MMODPREM` | PPOLC modal premium | **No** (#26) |
| `quikridr.MPREM` | ANN_PREM_PER_UNIT + fallback | **No** (#26) |
| `MPOLICY` padding | `format_qladmin_mpolicy()` | **No** (#25) |
| `quikplan.NFOINT` | CSO crosswalk plan interest code | **No** (#21D) |
| `quikdvdp.*` | Issue #38 MDEPOSIT fix | **No** |
| Row count `quikmstr` | 5,083 | **No change expected** |

---

## 5. Options evaluated

| Option | Description | Decision |
|---|---|---|
| **A** | Rulebook-only: map PPOLC `NFO_OPT` | **Rejected** — field often blank; not authoritative per Issue #21 |
| **B** | Translation table only (fix `NF_4`, `NF_2`) | **Partial** — fixes numeric fleet subset, not ISWL text/BF column |
| **C** | Cache-only: add `BF_NON_FORFEITURE` | **Partial** — fixes ISWL, not numeric crosswalk errors |
| **D** | **Cache + translation (recommended)** | **Selected** — Track A + Track B together |
| **E** | Map PPCOM `NF_OPTION` | **Rejected** — billing snapshot, not benefit-type election |

---

## 6. Open client questions

1. **Dividend on ISWL** — is `DIVIDEND` on the BF row correct source when BA row dividend is blank?
2. **UAT acceptance** — verify NFO on BF/code-1 and code-2 policies after fix (see Dependency Gate expected outcomes).

**Closed:**

- Codes **1–2** → SME approved (**APL = 1**).
- Codes **3–6** → **no translation changes** (Warren 2026-07-04).
- Codes **7–9** → not in QLAdmin crosswalk; **0**.

---

## 7. Recommended formatting rules

| Rule | Recommendation |
|---|---|
| Policy key | Crosswalk LPOL→MPOLICY + 10-char padding (#25) |
| Source text | Strip whitespace; normalize `APL/ETI` → `APL ETI` before translation lookup |
| Numeric codes | Strip padding; map via `NF_<code>` **before** strict numeric shield |
| Blanks | Blank source → retain **0** (no fabrication) |
| Invalid / unknown | Log + retain **0**; do not silently passthrough LifePRO code to QLAdmin |

---

## 8. Policy number key handling

1. LifePRO `POLICY_NUMBER` (9010…) → `Master_Crosswalk.csv` → QLA `MPOLICY` (010…C)
2. Cache keyed by **legacy** and **QLA** id (existing `reverse_cw_map` pattern in `app.py`)
3. Apply `format_qladmin_mpolicy()` on emit — **no change**

---

## 9. Estimated record counts

| Metric | Count | Basis |
|---|---:|---|
| Total `quikmstr` policies | 5,083 | Current batch |
| `MNFOPT = 0` today | 3,768 | Output analysis |
| PPBENTYP TYPE_CODE=BF rows | 2,348 | May 20260530 zip profile |
| Issue #38 pop — would change under proposed numeric map | **20** | Cross-check script |
| Issue #21 ISWL validation policies | 7 | Screenshot packet |
| Policies with extract `NON_FORFEITURE=2` wrong today | **2** | SME mismatch confirmed |

**Expected delta after full fix (estimate):** hundreds to low-thousands of `MNFOPT` corrections (BF column + numeric map); exact count requires PPBENTYP join — run `_research_issue21a_nfo.py` when Source/ populated.

---

## 10. Sample trace (7 policies) — **confirmed against Source**

Traced 2026-07-04 from `PPBENTYP_BenefitType_Extract_20260530.csv` + v57.46 `quikmstr.csv`.

| MPOLICY | TYPE | Source value | LifePRO UI | Before | After (approved scope) | Fix |
|---|---|---|:---:|:---:|:---:|---|
| 010765930C | BF | **1** | APL ETI | 0 | **1** | Cache + code 1 |
| 010718309C | BF | **1** | APL ETI | 0 | **1** | Cache + code 1 |
| 010818663C | BF | **1** | ETI | 0 | **1** | Cache + code 1 |
| 010469666C | BA | **2** | — | 2 | **1** | `NF_2→1` |
| 010391895C | BA | **4** | ETI | 0 | **0** | **No change** (code 4 out of scope) |
| 010448806C | BA | **5** | RPU | 0 | **0** | **No change** (code 5 out of scope) |
| 010713704C | BF | **4** | ETI | 0 | **0** | **No change** (code 4 out of scope) |
| 010391876C | BA | **4** | ETI | 2 | **2** | Unchanged |

**Key finding:** LifePRO UI shows text labels (ETI, RPU, APL ETI) but the extract stores **numeric LifePRO codes** — even on **`BF_NON_FORFEITURE`**. ISWL policies use **`TYPE_CODE=BF`** with **`NON_FORFEITURE` blank**; traditional policies use **`TYPE_CODE=BA`** with values in **`NON_FORFEITURE`**.

**Dividend:** BA-row policies (010391895C, 010448806C) already emit **`MDIVOPT=4`** correctly. BF-row ISWL policies have **blank `DIVIDEND`** in PPBENTYP — **`MDIVOPT=0` may be source-empty**, not a conversion bug. Confirm with client whether dividend election lives elsewhere for ISWL.

Full trace file: `Issue_21A_Trace_Samples.csv`

---

## 11. Risks and unknowns

| Risk | Severity | Mitigation |
|---|---|---|
| Wrong TYPE_CODE row selected when multiple seq-1 rows | Medium | Explicit priority: **BF** `BF_NON_FORFEITURE` > **BA** `NON_FORFEITURE` |
| LifePRO code 9 in source (83 BF policies) | Low | **`NF_9→0`** — no QLAdmin Special code; matches crosswalk |
| Regression on 438+ policies already at MNFOPT=1 | Low | Numeric map preserves code 1; validate sample |
| MDIVOPT regression on 479 policies at DIV=4 | Low | No change to `DV_*` table; cache-only if needed |
| MPOLICY / MPREM regression | Low | Validator asserts #25 / #26 unchanged |

---

## 12. Dependency Gate preview

| Check | Met? |
|---|---|
| PPBENTYP extract in Source/ | **Yes** (`20260530`, 5,083 seq-1 rows) |
| Column headers documented | **Yes** — trace confirms BA vs BF columns |
| ISWL sample trace complete | **Yes** — 7/7 policies |
| SME codes 1–2 approved | **Yes** |
| Codes 3–6 explicitly excluded | **Yes** |
| Example policies + screenshots | **Yes** |
| Plan preserves #25 / #26 | **Yes** |

**Gate result:** **PASS** — see `Issue_21A_Dependency_Gate.md`

**Next stage:** Risk Agent

```
Risk Agent — Issue #21A: NFO / Dividend Options

Read AI_Agents/Risk_Agent.md and Issue_Log_Items/Issue_21/Issue_21A/Issue_21A_Planning_Report.md.

Quantify blast radius for:
1. PPBENTYP cache extension (BF_NON_FORFEITURE, TYPE_CODE=BF priority)
2. Master_Value_Translation.csv LifePRO numeric NF_* crosswalk (codes 0-6)
3. New text keys NF_APL ETI, NF_APL RPU

Confirm regression guards for Issue #25 MPOLICY and Issue #26 MPREM.
Do not code.
```

---

## 14. Recommended Development task (Do not implement)

1. **Cache (`app.py` + mirror):** When building `lifepro_extra['NON_FORFEITURE']`, scan PPBENTYP seq-1 rows; prefer **`BF_NON_FORFEITURE`** from **`TYPE_CODE=BF`**; fallback to **`NON_FORFEITURE`**. Apply same pattern for **`DIVIDEND`** if BF row carries dividend and BA row does not.
2. **Translation (`Master_Value_Translation.csv` + mirror):** Add **`NF_1→1`**, **`NF_2→1`** only. Optional text **`NF_APL ETI`**, **`NF_APL RPU`** → **1**. **Do not change `NF_3`–`NF_6`, `NF_4`, or `NF_5`.**
3. **Optional normalize:** Collapse `APL/ETI` → `APL ETI` before translation lookup (engine pre-step or extra translation keys).
4. **Version bump:** `app.py` → v57.47 (Issue #21A).
5. **Validator:** `tools/validators/validate_issue21a_mnfopt.py` — assert 7 sample policies + Issue #38 numeric cross-check rows + no MPOLICY/MPREM drift.

---

## Appendix

| Artifact | Path |
|---|---|
| Intake summary | `Issue_21A_Intake_Summary.md` |
| Population samples | `Issue_21A_Policy_Population.csv` |
| Trace samples (confirmed) | `Issue_21A_Trace_Samples.csv` |
| PPBENTYP profile | `docs/research/iswl_zip_table_profile_20260530.md` |
| Parent analysis | `Issue_Log_Items/Issue_21/reports/Issue_21_Final_Analysis.md` |

### G1 gate checklist

- [x] Planning report published
- [x] Source and target documented (PPBENTYP gap explicit)
- [x] Trace table included (7 policies + numeric samples)
- [x] Open questions enumerated
- [x] Development task outlined — **not executed**
- [x] No code, rulebook, or output changes

**Next stage:** Dependency Gate Agent
