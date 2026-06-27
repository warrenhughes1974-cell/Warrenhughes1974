# Issue 21M-FU — Merge Risk Report

**Issue:** QUIKMEMO grain mismatch — multiple rows per `MEMOKEY` vs production one-row model  
**Framework stage:** Risk Agent (Stage 4)  
**Status:** **CONDITIONAL GO**  
**Engine version analyzed:** v57.33 (`quikmemo.csv` / `quikmemo_uat_dbf`)  
**Generated:** 2026-06-24  
**Analysis:** Read-only simulation — no production code or output changes

**Status note:** Risk analysis only — no conversion logic modified.

---

## Go / No-Go Recommendation

### **CONDITIONAL GO**

Changing converted QUIKMEMO from **one row per PNOTE/PENSE source row** to **one row per `MEMOKEY` with merged `MEMOTEXT`** is **safe on memo size, DBT capacity, and regression surface**. Development may proceed **provided**:

1. **Grain rule:** Exactly **one DBF row per `MEMOKEY`** after merge; zero duplicate keys.
2. **Issue #25:** `MEMOKEY` remains **fixed 10-character** via `format_qladmin_mpolicy()` — no strip/re-pad in DBF writer.
3. **Formatting (interim):** Retain current `[PNOTE]` / `[ENS]` segment headers; separate entries with `\n---\n` until native format is verified.
4. **Client deliverable:** **`QUIKMEMO_ex.DBT`** still required for **pre-UAT format sign-off** (not a Development blocker for grain change).
5. **Scope:** Touch **only** `quikmemo` pipeline — no changes to quikmstr, quikridr, quikprmh, quikplan, quikclid, quikclnt, Issue #25, or Issue #26.

**Not NO-GO:** Largest merged memo is **22,039 characters** — well within FoxPro/VFP MEMO field limits (theoretical max ~4 GB; production DBF memo block indices reach **240,834** blocks).

---

## 1. Current vs Proposed Mapping

| Dimension | Current (v57.33) | Proposed (21M-FU) | Change? |
|-----------|------------------|-------------------|---------|
| **Grain** | 1 row per PNOTE or PENSE source row | 1 row per `MEMOKEY` | **Yes** |
| **MEMOKEY** | `format_qladmin_mpolicy()` — 10-char | Same | No |
| **MEMOTEXT** | Single source note/message per row | All segments concatenated | **Yes** |
| **Row count** | 29,279 | **4,380** | **Yes** (−24,899 rows) |
| **Duplicate MEMOKEY** | 3,466 keys duplicated | **0** | **Yes** |
| **PNOTE/PENSE sources** | Unchanged extracts | Unchanged extracts | No |
| **Other tables** | N/A | Untouched | No |

---

## 2. Premium / Related Fields Untouched

| Target | Issue | Touched? |
|--------|-------|----------|
| `quikmstr.MPOLICY` / padding | #25 | **No** |
| `quikridr.MPREM` | #26 | **No** |
| `quikmstr.MMODPREM` | #26 | **No** |
| `quikmstr`, `quikridr`, `quikprmh`, `quikplan`, `quikclid`, `quikclnt` | — | **No** |

Merge affects **`quikmemo` only**. `MEMOKEY` values remain a subset of existing `quikmstr.MPOLICY` keys (no new orphan keys introduced by merge).

---

## 3. Current Converted Output — Quantified

| Metric | Value |
|--------|------:|
| Total `quikmemo` rows | **29,279** |
| Unique `MEMOKEY` (stripped) | **4,380** |
| Duplicate `MEMOKEY` groups | **3,466** |
| Extra rows beyond one per key | **24,899** |
| Max rows per `MEMOKEY` | **207** (`010785099C`) |
| PNOTE-only policies | **976** |
| PENSE-only policies | **1,079** |
| Both PNOTE and PENSE | **2,325** |
| PNOTE rows | 6,003 |
| PENSE rows | 23,276 |
| `MEMOKEY` width ≠ 10 | **0** |

**Source:** `QLA_Migration/Output/quikmemo.csv` (v57.33 batch)

---

## 4. Simulated Merged Output — Quantified

**Simulation method:** Group by `MEMOKEY`; preserve existing row order within group (already newest-first from converter sort); join segments with `\n---\n`; retain full `[PNOTE]`/`[ENS]` text per segment.

| Metric | Current | Simulated merged |
|--------|--------:|-----------------:|
| Total rows | 29,279 | **4,380** |
| Unique `MEMOKEY` | 4,380 | **4,380** |
| Duplicate `MEMOKEY` groups | 3,466 | **0** |
| Total `MEMOTEXT` characters | 4,157,759 | 4,282,254 |
| Separator overhead | — | **+124,495 chars (+2.99%)** |
| Min merged length | 86 | **86** |
| Avg merged length | 142 | **978** |
| Median merged length | 114 | **652** |
| P95 merged length | — | **2,847** |
| Max merged length | 176 | **22,039** |
| `MEMOKEY` width violations | 0 | **0** |

### Merged size distribution (policies)

| Size bucket (chars) | Policy count |
|---------------------|-------------:|
| 0–500 | 2,205 |
| 501–1,000 | 1,101 |
| 1k–2k | 584 |
| 2k–5k | 384 |
| 5k–10k | 71 |
| 10k–20k | 30 |
| 20k–50k | **5** |
| 50k+ | **0** |

**Artifacts:**

- `Issue_21M_FollowUp_Simulated_Merged_QUIKMEMO_Population.csv` — all 4,380 simulated rows
- `Issue_21M_FollowUp_Largest_MEMOTEXT_Report.csv` — top 25 by size
- `Issue_21M_FollowUp_Merge_Simulation_Summary.csv` — summary metrics
- `Issue_21M_FollowUp_Merged_Size_Distribution.csv` — bucket counts

---

## 5. Memo-Size and DBT Safety

| Check | Result | Assessment |
|-------|--------|------------|
| Largest merged memo | **22,039 chars** (`010785099C`, 207 segments) | **Safe** |
| Policies > 50k chars | **0** | **Safe** |
| Policies > 100k chars | **0** | **Safe** |
| FoxPro/VFP MEMO field limit | ~4 GB theoretical | **No risk** |
| Production reference | Memo block indices to **240,834** in `QUIKMEMO_ex.DBF` | Production tolerates **much larger** blobs than conversion max |
| Current `quikmemo.dbt` size | 14,990,916 bytes (~14.3 MB) | Baseline |
| Estimated merged DBT (512-byte blocks, rough) | ~4.5 MB payload + overhead | **Similar or smaller** (fewer memo field headers; +3% text) |
| DBT readability after merge | Same generator path | **Valid** — fewer rows, co-located DBF+DBT unchanged |

**Conclusion:** MEMOTEXT size and DBT growth do **not** block Development.

### Top 5 largest merged policies

| QLA policy | Source rows | PNOTE segs | PENSE segs | Merged chars |
|------------|------------:|-----------:|-----------:|-------------:|
| 010785099C | 207 | 1 | 206 | **22,039** |
| 010887927C | 197 | 2 | 195 | 20,859 |
| 010866396C | 152 | — | — | 21,327 |
| 010803417C | 150 | — | — | 21,280 |
| 010817483C | 186 | — | — | 20,349 |

*(Full top 25 in `Issue_21M_FollowUp_Largest_MEMOTEXT_Report.csv`.)*

---

## 6. Ordering Rule Recommendation

### Primary rule: **Newest first** (match QLAdmin Help §5.1.1.4)

Preserve the **existing converter sort** within each `MEMOKEY` before concatenation:

```
Sort: MEMOKEY ASC,
      _sort_a DESC,   # date (PNOTE MMDDYYYY→sortable; PENSE EVENT_DATE)
      _sort_b DESC,   # time / event sub-key
      _sort_c DESC,   # RECORD_SEQ / tie-break
      _src_order ASC  # PNOTE (0) before PENSE (1) on exact tie
```

### PNOTE vs PENSE interleaving

**Do not** block-separate all PNOTE then all PENSE. **Interleave by date descending** across both sources (current file order for each key).

**Example `010713704C`:** PNOTE `2025-06-10` appears **before** PENSE `2004-02-04` in merged output (newest first).

### Segment separator (interim)

Between entries: **`\n---\n`** (newline + three hyphens + newline)

- Visible in QLAdmin memo viewer
- Unlikely to appear inside LifePRO note bodies
- Replace if `QUIKMEMO_ex.DBT` reveals native delimiter

---

## 7. Formatting Recommendation

| Item | Recommendation | Status |
|------|----------------|--------|
| Segment headers | Keep **`[PNOTE]`** and **`[ENS]`** blocks with Date/Time/User/Seq lines | **Interim approved** |
| Native format | Compare to `QUIKMEMO_ex.DBT` when supplied | **Pending client** |
| Prefix removal | Do **not** remove until native sample proves otherwise | Deferred |
| Blank segments | Skip at source (unchanged) | No change |
| Character encoding | Latin-1 compatible (unchanged) | No change |

**Production DBT status:** **`QUIKMEMO_ex.DBT` still missing** from `docs/`. Structural proof (one row per key) is sufficient for grain change; **exact** native separator/format requires DBT before **client UAT sign-off**.

---

## 8. Key Behavior Confirmation

| Rule | Simulated result |
|------|------------------|
| One row per `MEMOKEY` | **4,380 rows / 4,380 keys** ✓ |
| No duplicate `MEMOKEY` after merge | **0 duplicate groups** ✓ |
| `MEMOKEY` width = 10 | **0 violations** ✓ |
| Issue #25 padding preserved | Merge uses existing `MEMOKEY` column verbatim ✓ |

---

## 9. Regression Risk

| Surface | Risk | Mitigation |
|---------|------|------------|
| `quikmstr` | **None** | No shared logic |
| `quikridr` / MPREM (#26) | **None** | Isolated table |
| `quikprmh`, `quikplan`, `quikclid`, `quikclnt` | **None** | Not referenced by merge |
| Issue #25 MPOLICY/MEMOKEY | **Low** | Reuse `format_qladmin_mpolicy()`; DBF writer must not strip padding |
| Issue #26 MPREM | **None** | No quikridr changes |
| DBF/DBT packaging | **Low** | Same `quikmemo_uat_dbf/` co-location; row count drops; re-validate `_validate_issue21m_dbf_packaging.py` |
| Row-count validators | **Medium** | Update `_validate_issue21m_quikmemo.py` expected counts (29,279 → 4,380) |
| Client UAT expectations | **Medium** | UAT brief: memo **count** in DBF drops; memo **content** preserved in merged blob |
| QLAdmin display | **Low–Medium** | Aligns with production grain; UAT must confirm multi-segment visibility in one memo |

---

## 10. Trace Policies — Before vs Simulated

| Policy | Before rows | After rows | Merged chars | Notes |
|--------|------------:|-----------:|-------------:|-------|
| **010335038C** | 2 | **1** | 223 | 2× PNOTE; UAT defect policy |
| **010713704C** | 2 | **1** | ~264 | 1× PNOTE + 1× PENSE; different dates |
| **010818663C** | 3 | **1** | ~513 | 3× PNOTE |
| **010785099C** | 207 | **1** | **22,039** | Fleet max size |
| **010718309C** | 1 | **1** | 86 | Single-segment — unchanged length |
| **010448806C** | 1 | **1** | 177 | PENSE-only single — unchanged |

---

## 11. Fallback Options

| Option | Rows | Assessment |
|--------|-----:|------------|
| **A — Merge per MEMOKEY (recommended)** | 4,380 | Matches production `QUIKMEMO_ex.DBF`; fixes QLAdmin display |
| **B — Keep multi-row; QLAdmin vendor fix** | 29,279 | **Reject** — contradicts production structure |
| **C — Synthetic MEMOKEY suffix** | 29,279+ | **Reject** — breaks MPOLICY relation |
| **D — Timestamp-only fix (no merge)** | 29,279 | **Reject** — production has zero duplicate keys |

**Recommended:** **Option A** only.

---

## 12. Open Client Request — `QUIKMEMO_ex.DBT`

Please place **`QUIKMEMO_ex.DBT`** (or `.FPT`) in `docs/` alongside `QUIKMEMO_ex.DBF`.

**Purpose:**

1. Read native `MEMOTEXT` body format and separators  
2. Confirm whether `[PNOTE]`/`[ENS]`-style headers are used in production  
3. Finalize separator string before client UAT sign-off  

**Not required to start Development** on grain merge; **required before UAT closure** if native format differs from interim `\n---\n` + header blocks.

---

## 13. Validation Checklist (for Validation Agent post-Development)

- [ ] `quikmemo.csv` row count = **4,380**
- [ ] Zero duplicate `MEMOKEY` (stripped and raw width check)
- [ ] All `MEMOKEY` length = 10 (Issue #25)
- [ ] All `MEMOKEY` ⊆ `quikmstr.MPOLICY`
- [ ] Segment count preserved: sum of source rows = 29,279 (audit metric)
- [ ] Trace policies: 010335038C → 1 row; 010713704C → 1 row
- [ ] Max merged `MEMOTEXT` ≤ 25,000 chars (sanity vs simulation 22,039)
- [ ] DBF + DBT co-located in `quikmemo_uat_dbf/`
- [ ] `quikmstr`, `quikridr`, `quikprmh`, `quikplan`, `quikclid`, `quikclnt` row counts **unchanged**
- [ ] Issue #26 MPREM spot check unchanged
- [ ] QLAdmin UAT: 010335038C Memo tab shows **both** note texts in one entry

---

## 14. Recommended Development Agent Prompt

```
Development Agent — Issue 21M-FU: QUIKMEMO merge per MEMOKEY

Prerequisites: Risk Agent CONDITIONAL GO (Issue_21M_FollowUp_Merge_Risk_Report.md)

Implement surgical change ONLY in quikmemo pipeline:
- After PNOTE/PENSE emit list is built and sorted (existing sort keys), merge to
  one row per MEMOKEY by concatenating MEMOTEXT with separator "\n---\n".
- Preserve existing [PNOTE]/[ENS] segment formatting from _format_pnote_memotext /
  _format_pense_memotext.
- Preserve MEMOKEY via format_qladmin_mpolicy() — Issue #25; no .strip() in DBF writer.
- Expected output: 4,380 rows (not 29,279); 0 duplicate MEMOKEY.

Files (expected):
- qla_core/quikmemo_converter.py — merge step before final DataFrame
- QLA_Migration/_validate_issue21m_quikmemo.py — update expected counts + duplicate-key check
- app.py / QLA_Migration/app.py — version bump only if already touching app.py

Do NOT touch: quikmstr, quikridr, MPREM (#26), MPOLICY padding rule (#25), unrelated rulebooks.

Validate: full batch + _validate_issue21m_quikmemo.py + DBF packaging check.
UAT policy: 010335038C must have 1 row with both PNOTE segments visible in MEMOTEXT.
```

---

## 15. Gate G3 — Risk Approved

- [x] Risk report published with **CONDITIONAL GO**
- [x] Impact quantified (29,279 → 4,380 rows; max memo 22,039 chars)
- [x] Unrelated fields marked untouched
- [x] Issue #25 / #26 preservation confirmed
- [ ] User / project lead acknowledged recommendation (pending)

**Next stage:** User approval → **Development Agent** (surgical merge in `quikmemo_converter.py` only)

---

## Related Artifacts

| File | Purpose |
|------|---------|
| `Issue_21M_FollowUp_Production_QUIKMEMO_Analysis.md` | Production grain evidence |
| `Issue_21M_FollowUp_Simulated_Merged_QUIKMEMO_Population.csv` | Full simulation |
| `Issue_21M_FollowUp_Largest_MEMOTEXT_Report.csv` | Top 25 sizes |
| `Issue_21M_FollowUp_Merge_Simulation_Summary.csv` | Summary metrics |
| `Issue_21M_FollowUp_Merged_Size_Distribution.csv` | Size buckets |
