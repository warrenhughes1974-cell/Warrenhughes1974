# Issue 21M-FU — Production QUIKMEMO Analysis

**Issue:** Converted QUIKMEMO has multiple rows per `MEMOKEY`; QLAdmin displays only one memo  
**Framework stage:** Planning / Research (follow-up)  
**Engine version:** v57.33  
**Generated:** 2026-06-24  
**Code changes:** None

---

## 1. Executive Finding

Production-working examples in `docs/` establish that **working QUIKMEMO uses exactly one DBF row per `MEMOKEY`** — **19,777 rows / 19,777 unique keys, zero duplicate-key groups**. Converted output uses **one row per PNOTE/PENSE source row** — **29,279 rows / 4,380 unique keys**, with **3,466 keys (79%) having multiple rows** (max **207** rows per policy).

This is a **grain mismatch**, not a DBF/DBT corruption issue on the converted side. QLAdmin behavior on policy `010335038C` (one visible memo, two DBF rows) is **consistent with production storage semantics** (one indexed row per policy), not with the current conversion model.

**MEMOTEXT body format** from production **cannot be fully verified** because `QUIKMEMO_ex.DBT` / `.FPT` was **not supplied** with the example DBF. Structural proof (one row per key) is sufficient to route to **Risk Agent**; exact concatenation delimiters require the memo sidecar before Development.

**Recommendation:** Advance to **Risk Agent** to approve changing conversion grain to **one QUIKMEMO row per `MEMOKEY`** with merged `MEMOTEXT`. Request client provide **`QUIKMEMO_ex.DBT`** for delimiter/format matching before Development Agent work.

---

## 2. Production Example Files Located

**Path:** `C:\Users\warren\Documents\GitHub\Warrenhughes1974\docs`

| File | Present | Size | Role |
|------|---------|-----:|------|
| **`QUIKMEMO_ex.DBF`** | Yes | 415,416 | Production-working memo table |
| **`QUIKMEMO_Ex.ntx`** | Yes | 762,880 | Index on `MEMOKEY` (NTX header confirms expression `MEMOKEY`) |
| **`QUIKMEMO_ex.DBT`** | **No** | — | **Required** for FoxPro/VFP memo text (MEMO field sidecar) |
| **`QUIKMEMO_ex.FPT`** | No | — | Alternative VFP memo sidecar — not present |
| Second separate DBF example | **No** | — | Only one production DBF in `docs/` |

**Interpretation of “two production-working example files”:** The repo contains **two companion artifacts** — **`QUIKMEMO_ex.DBF` + `QUIKMEMO_Ex.ntx`**. There is **not** a second independent production DBF sample.

---

## 3. File Type and Schema Comparison

| Attribute | Production `QUIKMEMO_ex.DBF` | Converted `quikmemo.dbf` |
|-----------|------------------------------|---------------------------|
| DBF version byte | 131 (0x83 — Visual FoxPro + memo) | VFP-style with memo |
| Fields | `MEMOKEY C(10)`, `MEMOTEXT M` | `MEMOKEY C(10)`, `MEMOTEXT M` |
| Record length | 21 bytes | Same pattern |
| Memo sidecar | **Missing from package** | `quikmemo.dbt` (14,990,916 bytes) co-located |
| Index shipped | `QUIKMEMO_Ex.ntx` on `MEMOKEY` | Not shipped (QLAdmin rebuilds) |
| MEMOTEXT readable | **No** (no DBT/FPT) | **Yes** |

---

## 4. Production Storage Model

### 4.1 Row grain

| Metric | Production | Converted |
|--------|----------:|----------:|
| Total DBF rows | **19,777** | **29,279** |
| Unique `MEMOKEY` (stripped) | **19,777** | **4,380** |
| Duplicate `MEMOKEY` groups | **0** | **3,466** |
| Max rows per `MEMOKEY` | **1** | **207** |
| **Grain** | **One row per policy (`MEMOKEY`)** | **One row per PNOTE/PENSE source row** |

**Conclusion:** Production-working QUIKMEMO does **not** use multiple DBF rows per policy. It uses **one row per `MEMOKEY`**.

### 4.2 `MEMOKEY` format (production)

| Observation | Detail |
|-------------|--------|
| Width | All keys **10 characters** |
| Padding | Space-padded where needed; **1 blank-key row** present |
| Prefix patterns (stripped keys) | `W` ≈ 17,206; `F` ≈ 2,124; `M` ≈ 413; `T` ≈ 33 |
| Example keys | `W00000001S`, `F00000001S`, `T00001328S` |
| Overlap with converted QLA keys (`010…C`) | **0 policies** — different policy universe / numbering scheme |

Production examples use **client-native policy key shapes**, not the LifePRO-converted `010335038C` style. Structural rules still apply: **unique `MEMOKEY` = one row**.

### 4.3 `MEMOTEXT` (production) — partial analysis

| Observation | Detail |
|-------------|--------|
| Memo pointers | Present in every row (ASCII block numbers in 10-byte memo field, e.g. `3`, `228433`, `240834`) |
| Empty memo blocks | **0** — all rows point to memo data |
| Block number range | Min **3** → max **240,834** (wide variance → varying memo sizes) |
| Full text content | **Not readable** without `QUIKMEMO_ex.DBT` |
| Concatenation | **Not directly observed**, but **strongly inferred**: with zero duplicate keys, multiple historical notes for one policy **must** live inside a **single `MEMOTEXT`** blob in production |

**Guardrail honored:** Concatenation is **inferred from grain**, not assumed from text samples we could not read.

---

## 5. Converted Output Analysis

### 5.1 Files compared

| File | Rows / keys | Notes |
|------|-------------|-------|
| `QLA_Migration/Output/quikmemo.csv` | 29,279 rows; 4,380 unique `MEMOKEY` | Source of truth for conversion |
| `QLA_Migration/Output/quikmemo_uat_dbf/quikmemo.dbf` | 29,279 rows | Matches CSV |
| `QLA_Migration/Output/quikmemo_uat_dbf/quikmemo.dbt` | Sidecar present | Both memo rows readable for test policies |

### 5.2 `MEMOTEXT` format (converted)

Each source row becomes a structured plain-text block:

```
[PNOTE]
Date: YYYY-MM-DD
Time: HH:MM:SS
User: -
Seq: {RECORD_SEQ}
BenSeq: {BENEFIT_SEQ}
{LINE_1}
{LINE_2}
...
```

PENSE rows use `[ENS]` header with `Event:`, `User:`, `Seq:` lines (see `qla_core/quikmemo_converter.py`).

**Not observed in production** (unverified without DBT): `[PNOTE]` / `[ENS]` prefixes, multi-line Date/Time/User header blocks, or LifePRO conversion markers.

---

## 6. Policy 010335038C — Specific Comparison

| Aspect | Converted (current) | Production example file | Production-compatible expectation |
|--------|---------------------|-------------------------|-----------------------------------|
| Present in file? | **Yes** | **No** (0 rows) | N/A — policy not in prod sample |
| DBF rows | **2** | — | **1** (one row per `MEMOKEY`) |
| Row 1 `MEMOTEXT` | Seq 2 — `5/18/18 - LETTER & CHECK MAILED TO PB.` | — | Part of single merged blob |
| Row 2 `MEMOTEXT` | Seq 1 — `PB = PATSY MILLER` / `5/1/18 - PROOF OF DEATH TO PB.` | — | Part of single merged blob |
| Shared timestamp | Both rows: `2018-05-18 08:45:28` | — | Native format TBD (needs DBT) |
| Merged size (approx.) | 219 chars if newline-joined | — | Well within MEMO limits |

**QLAdmin symptom explained:** With production semantics, QLAdmin positions on **`MEMOKEY` via `QuikMemo.ntx`** and reads **one record**. Converted data violates production grain by supplying **two records** for the same key; the UI shows **one**.

---

## 7. What Production Examples Prove

| Question | Answer | Confidence |
|----------|--------|------------|
| Are **multiple DBF rows per `MEMOKEY`** used in working production? | **No** — zero duplicates in 19,777 rows | **High** |
| Is **one row per `MEMOKEY`** required? | **Yes** for production parity | **High** |
| Must memo text be **concatenated**? | **Inferred yes** — only one row exists per policy | **Medium** (text not read) |
| Is the issue purely QLAdmin/environment/index? | **No** — converted grain conflicts with production structure | **High** |
| Does `[PNOTE]`/`[ENS]` header format match production? | **Unknown** — DBT missing | **Blocked** |

---

## 8. Exact Differences — Production vs Converted

| # | Dimension | Production-working | Converted v57.33 |
|---|-----------|-------------------|------------------|
| 1 | **Row grain** | 1 row / `MEMOKEY` | 1 row / PNOTE or PENSE source row |
| 2 | **Duplicate `MEMOKEY`** | Never | 3,466 keys duplicated (24,899 extra rows) |
| 3 | **Row count** | 19,777 | 29,279 |
| 4 | **Index file** | `QUIKMEMO_Ex.ntx` bundled | Not emitted (QLAdmin rebuild) |
| 5 | **Memo sidecar in package** | DBT **missing from repo** | `quikmemo.dbt` co-located with DBF |
| 6 | **`MEMOTEXT` layout** | Native QLAdmin memo stream (unread) | Structured `[PNOTE]`/`[ENS]` blocks |
| 7 | **Policy key universe** | `W…S`, `F…S`, etc. | `010……C` LifePRO crosswalk keys |
| 8 | **Sort order** | N/A (single row) | Newest-first per source sort before emit |
| 9 | **QLAdmin Memo tab** | One row → one display entry | Multiple rows → one visible entry (UAT) |

---

## 9. Root-Cause Recommendation

### Primary root cause (conversion)

**Grain mismatch:** Issue 21M implemented **one QUIKMEMO row per LifePRO PNOTE/PENSE row** based on QLAdmin Help language suggesting a multi-memo list UI. Production-working `QUIKMEMO_ex.DBF` proves the **persisted table shape** is **one row per policy key**, with memo history carried in **`MEMOTEXT` content**, not duplicate `MEMOKEY` rows.

### Secondary factor (QLAdmin read path)

QLAdmin Memo tab behavior on converted data (**one visible memo**) aligns with **single-record index positioning** on `MEMOKEY`, matching production storage — not a random display bug.

### Not root cause (ruled out for 010335038C)

- DBF/DBT corruption on converted output — both memo blobs readable
- Missing conversion rows — two rows present; one hidden
- Issue #25 `MEMOKEY` padding defect for this policy — key is 10-char `010335038C`

---

## 10. Recommended Next Framework Stage

| Stage | Recommendation | Rationale |
|-------|----------------|-----------|
| **Risk Agent** | **Proceed now** | Production proof requires **grain change**; Risk must approve concatenation rules, separator design, and regression scope |
| **Development Agent** | **Only after Risk GO / CONDITIONAL GO** | Do not change `quikmemo_converter.py` until Risk signs off |
| **More Planning only** | **If client supplies `QUIKMEMO_ex.DBT`** | Re-run MEMOTEXT delimiter analysis before Development (can be parallel to Risk) |
| **No conversion change** | **Not supported** | Production structure contradicts current multi-row output |

### Client deliverable still needed

Please add **`QUIKMEMO_ex.DBT`** (or `.FPT`) alongside the production DBF so Planning can document:

- Native memo **separators** between historical entries
- Whether **Date/Time/User** lines match QLAdmin-native format
- Whether **`[PNOTE]`/`[ENS]` prefixes** are used or must be removed

---

## 11. Recommended Risk Agent Prompt

```
Risk Agent — Issue 21M-FU: Production QUIKMEMO Grain Mismatch

Read:
- Issue_Log_Items/Issue_21M/Issue_21M_FollowUp_Production_QUIKMEMO_Analysis.md
- Issue_Log_Items/Issue_21M/Issue_21M_Production_vs_Converted_QUIKMEMO_Comparison.csv
- Issue_Log_Items/Issue_21M/Issue_21M_MEMOTEXT_Format_Examples.csv
- Issue_Log_Items/Issue_21M/Issue_21M_Multiple_Memo_Display_Research_Report.md

Production evidence (docs/QUIKMEMO_ex.DBF):
- 19,777 rows, 19,777 unique MEMOKEY, ZERO duplicate keys
- Working production = one QUIKMEMO row per MEMOKEY

Converted evidence (v57.33):
- 29,279 rows, 4,380 unique MEMOKEY, 3,466 keys with multiple rows
- 010335038C has 2 rows; QLAdmin shows 1

Assess Risk GO for changing conversion to ONE row per MEMOKEY with merged MEMOTEXT
(PNOTE + PENSE segments, newest-first, separator TBD until QUIKMEMO_ex.DBT supplied).

Preserve Issue #25 MEMOKEY padding and Issue #26 MPREM. No code in Risk stage.

Deliver: Issue_21M_FU_Risk_Report.md with GO/NO-GO/CONDITIONAL GO and dev conditions.
```

---

## 12. Related Deliverables

| Artifact | Path |
|----------|------|
| Production vs converted comparison | `Issue_Log_Items/Issue_21M/Issue_21M_Production_vs_Converted_QUIKMEMO_Comparison.csv` |
| MEMOTEXT format examples | `Issue_Log_Items/Issue_21M/Issue_21M_MEMOTEXT_Format_Examples.csv` |
| Prior UAT probe plan | `Issue_Log_Items/Issue_21M/Issue_21M_FollowUp_UAT_Probe_Checklist.md` |
| DBF trace 010335038C | `Issue_Log_Items/Issue_21M/Issue_21M_010335038C_DBF_DBT_Trace.csv` |
| Intake | `Issue_Log_Items/Issue_21M/Issue_21M_FollowUp_Intake_Summary.md` |

---

## 13. Guardrails Confirmation

- [x] No code changes
- [x] No QUIKMEMO output modified
- [x] No DBF/DBT packaging changes
- [x] No PNOTE/PENSE conversion changes
- [x] Issue #25 / #26 untouched
- [x] Concatenation not assumed as exact format — only as **inferred grain** pending DBT

**Stop point:** Planning/Research complete for production comparison. Next gate: **Risk Agent**.
