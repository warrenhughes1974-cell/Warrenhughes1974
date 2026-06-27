# Issue 21M-FU — UAT Probe Checklist

**Issue:** QLAdmin Memo tab shows one memo; QUIKMEMO has multiple rows per MEMOKEY  
**Framework stage:** UAT Probe Plan (between Planning G1 and Dependency Gate / Risk Agent)  
**Engine version under test:** v57.33  
**Generated:** 2026-06-24  
**Code changes:** None — probe execution only

---

## Purpose

Determine **why** QLAdmin displays only one memo when `QUIKMEMO.DBF` contains multiple rows for the same `MEMOKEY`. Results from this checklist decide whether to advance to **Risk Agent** (behavior proven) or schedule **additional UAT probing** (still inconclusive).

**Do not change** `quikmemo.csv`, `quikmemo.dbf`, DBT packaging, or conversion logic until probes complete and Risk Agent approves a remediation path.

---

## Prerequisites

| Item | Detail |
|------|--------|
| **UAT environment** | QLAdmin loaded with v57.33 conversion output |
| **Memo DBF location** | `QLA_Migration/Output/quikmemo_uat_dbf/quikmemo.dbf` + `quikmemo.dbt` (must remain co-located) |
| **DBF inspection tool** | FoxPro, DBF viewer, or approved read-only utility — **do not edit** production/UAT DBF during probes except native test policy (Probe 3) |
| **Tester role** | Client UAT lead + Sys-Op user (required for Probe 3 memo add and Print Memo) |
| **Evidence capture** | Screenshots, Print Memo PDF/output, DBF row counts, short text snippets — record in `Issue_21M_FollowUp_Client_Test_Grid.csv` |

### Expected DBF baseline (conversion output — read-only reference)

| Policy | QUIKMEMO rows | Source mix | Key distinction |
|--------|--------------:|------------|-----------------|
| **010335038C** | 2 | 2× PNOTE | **Same** embedded Date/Time on both rows (`2018-05-18 08:45:28`) |
| **010713704C** | 2 | 1× PNOTE + 1× PENSE | **Different** dates (`2025-06-10` vs `2004-02-04`) |
| **010818663C** (optional) | 3 | 3× PNOTE | Two rows share identical Date/Time (`2011-08-23 15:43:11`) |

Full trace: `Issue_21M_010335038C_DBF_DBT_Trace.csv`, `Issue_21M_Multi_Memo_Policy_Samples.csv`.

---

## Probe Execution Order

Run probes **in sequence** where possible. Probes 1–2 and 4 can run in one UAT session. Probe 3 requires a **dedicated test policy**. Probe 5 follows Probe 1–4 if index rebuild is available. Probe 6 is optional but high value if a native multi-memo policy exists.

| Order | Probe | Est. time | Blocker if skipped |
|------:|-------|-----------|-------------------|
| 1 | 010335038C — which memo displays? | 5 min | Cannot distinguish SEEK-first vs timestamp dedupe |
| 2 | 010713704C — one or multiple memos? | 5 min | Cannot isolate duplicate-key vs date-mix behavior |
| 4 | 010335038C — Print Memo | 5 min | UI vs print path may differ — unknown |
| 3 | Native two-memo add on test policy | 15 min | **Critical** — proves native storage model |
| 5 | Index rebuild + retest | 10 min | Rules out NTX rebuild as root cause |
| 6 | Native multi-memo reference policy | 15 min | Gold-standard layout comparison |

---

## Probe 1 — Policy 010335038C: Which Memo Displays?

### Objective

Identify **which** of two converted PNOTE rows QLAdmin shows on the Memo tab.

### Steps

1. Open **Policy Display** for policy **`010335038C`**.
2. Go to the **Memo** tab.
3. Count visible memo **entries** in the list (not lines within one entry).
4. Record the **body text** (or first distinctive line) of each visible entry.
5. Compare to expected conversion output:

| DBF row | Seq | Expected distinctive text |
|---------|-----|---------------------------|
| Row 1 (recno 198, newest in file) | 2 | `5/18/18 - LETTER & CHECK MAILED TO PB.` |
| Row 2 (recno 199) | 1 | `PB = PATSY MILLER` / `5/1/18 - PROOF OF DEATH TO PB.` |

### Record

| Field | Value |
|-------|-------|
| Memo tab entry count | 1 / 2 / other: ___ |
| Visible text matches Seq 2? | Yes / No / Partial |
| Visible text matches Seq 1? | Yes / No / Partial |
| Screenshot attached? | Yes / No |

### Interpretation

| Result | Meaning |
|--------|---------|
| **1 entry, Seq 2 text** | Likely **index SEEK / first-or-newest-in-index-order** only |
| **1 entry, Seq 1 text** | Likely **last matching row** or reverse index order |
| **1 entry, other / truncated** | Possible **format/parser** issue — capture full screenshot |
| **2 entries** | Defect may be **intermittent or environment-specific** — recheck DBF load path |

---

## Probe 2 — Policy 010713704C: Mixed Sources, Different Dates

### Objective

Test whether QLAdmin shows multiple memos when rows have **different embedded dates** and **different source types** (PNOTE vs PENSE).

### Expected DBF content

| Row | Type | Date | Distinctive text |
|-----|------|------|------------------|
| 1 | `[PNOTE]` | 2025-06-10 | `4-22-25 SWTA MAILED ANNUAL STMT` |
| 2 | `[ENS]` | 2004-02-04 | `A Rebill Has Been Processed Due To Mode/Premium/Form Change Or Prem Reversal` |

### Steps

1. Open Policy Display for **`010713704C`**.
2. Memo tab — count entries.
3. Note whether **both** PNOTE and ENS-style content appear.
4. Note list order (newest first per Help §5.1.1.4).

### Record

| Field | Value |
|-------|-------|
| Memo tab entry count | 1 / 2 / other: ___ |
| PNOTE visible? | Yes / No |
| ENS / rebill message visible? | Yes / No |
| List order (newest first?) | Yes / No / N/A |

### Interpretation

| Result | Meaning |
|--------|---------|
| **2 entries** | Multi-row **can** work when dates differ — points to **timestamp dedupe** or **same-day batch** issue for 010335038C |
| **1 entry (PNOTE only)** | SEEK may return **newest row only** regardless of source |
| **1 entry (ENS only)** | Unexpected — capture screenshot; verify correct policy loaded |

---

## Probe 3 — Native Two-Memo Add (Test Policy)

### Objective

Determine how **native QLAdmin** persists memos when a user adds two memos — **one row per memo** vs **one row with concatenated MEMOTEXT**.

> **Critical probe.** Outcome directly selects conversion remediation grain.

### Setup

1. Select or create a **blank test policy** with **no existing QUIKMEMO rows** (or document baseline row count).
2. Record test policy **`MEMOKEY` / MPOLICY`**: _______________
3. Use Sys-Op account (required to add memos per Help §5.1.1.4).

### Steps

1. Policy Display → Memo tab → **Edit** → add memo **A** with unique text:  
   `UAT-21MFU-PROBE-A [date/time noted]`
2. Save. Confirm memo A visible in UI.
3. Add memo **B** with unique text:  
   `UAT-21MFU-PROBE-B [date/time noted]`
4. Save. Note Memo tab entry count (expect 2 if multi-row UI works).
5. **Close QLAdmin** (or ensure memo file flushed).
6. Open `QUIKMEMO.DBF` (+ DBT) for test policy **only** — read-only unless client uses dedicated UAT copy.

### Record

| Field | Value |
|-------|-------|
| Test policy MEMOKEY | |
| QUIKMEMO row count before | |
| QUIKMEMO row count after 2 adds | 1 / 2 / other: ___ |
| Memo A in separate row? | Yes / No |
| Memo B in separate row? | Yes / No |
| Both in one MEMOTEXT? | Yes / No |
| Native MEMOTEXT format (paste first ~10 lines) | |
| UI shows 2 entries? | Yes / No |

### Interpretation

| DBF rows | UI entries | Conversion implication |
|----------|------------|------------------------|
| **2 rows** | **2 entries** | Native = multi-row; conversion **should stay one row per source** — investigate format/index/load |
| **2 rows** | **1 entry** | Native storage multi-row but UI broken — **vendor/config** path; concatenation is workaround only |
| **1 row** | **1 entry** (both texts in MEMOTEXT) | Native = **concatenated** — conversion should move to **one QUIKMEMO row per MEMOKEY** |
| **1 row** | **2 entries** | UI splits one blob — unlikely; capture MEMOTEXT verbatim |

---

## Probe 4 — Policy 010335038C: Print Memo

### Objective

Determine whether **Print Memo** (Help §5.1.1.4 / Policy Display) outputs one memo or full history when DBF has two rows.

### Steps

1. Open **`010335038C`** → Memo tab.
2. Run **Print Memo** (Sys-Op menu per Help).
3. Save or screenshot print preview / PDF.
4. Count distinct memo blocks in output.
5. Check whether **both** Seq 1 and Seq 2 body text appear.

### Record

| Field | Value |
|-------|-------|
| Print output includes Seq 2 (`LETTER & CHECK`)? | Yes / No |
| Print output includes Seq 1 (`PB = PATSY MILLER`)? | Yes / No |
| Distinct memo blocks in print | 1 / 2 / other: ___ |
| Print matches Memo tab count? | Yes / No |

### Interpretation

| Result | Meaning |
|--------|---------|
| Print shows **both**, UI shows **one** | UI list bug/limitation; print uses full scan — concatenation may **not** be required for history |
| Print shows **one** | Consistent single-record read path — supports SEEK-only or single-row model |
| Print shows **both**, UI shows **two** | Original defect not reproduced — re-verify environment |

---

## Probe 5 — Index Rebuild and Retest

### Objective

Rule out **QuikMemo.ntx** rebuild behavior as cause (duplicate collapse, wrong tag order).

### Steps

1. Document whether **`QuikMemo.ntx`** exists before rebuild (path): _______________
2. Perform client-standard **index rebuild** for QUIKMEMO (or full QLAdmin reindex if that is normal deploy step).
3. Confirm **`quikmemo.dbf` row count** for `010335038C` still = **2** (rebuild must not drop rows).
4. Retest Probe 1 (Memo tab count and visible text).

### Record

| Field | Value |
|-------|-------|
| Rebuild procedure used | |
| NTX present before/after | |
| DBF row count 010335038C after rebuild | |
| Memo tab entry count after rebuild | 1 / 2 |
| Visible text changed after rebuild? | Yes / No |

### Interpretation

| Result | Meaning |
|--------|---------|
| DBF still 2 rows, UI still 1 | Index rebuild **not** the cause — display/read logic |
| DBF drops to 1 row | **Index rebuild dedupes** — escalate vendor; do not concatenate without Risk review |
| UI shows 2 after rebuild | Load order / missing NTX was cause — document rebuild as deploy requirement |

---

## Probe 6 — Native Multi-Memo Reference Policy (Optional)

### Objective

Compare a **client-native** policy known to have multiple memos (pre-conversion or non-converted) against converted layout.

### Steps

1. Identify policy with **known multiple memos** in production/history: _______________
2. Memo tab — count entries.
3. Export or inspect `QUIKMEMO.DBF` for that policy:
   - Row count for MEMOKEY
   - MEMOTEXT shape (headers, date lines, delimiters)
   - DBT sidecar present
4. Compare structure to converted `[PNOTE]` / `[ENS]` header format.

### Record

| Field | Value |
|-------|-------|
| Reference policy MEMOKEY | |
| Native UI memo count | |
| Native QUIKMEMO row count | |
| Multiple rows with same MEMOKEY? | Yes / No |
| MEMOTEXT sample (anonymized) | |
| Matches converted header pattern? | Yes / No / Partial |

### Interpretation

| Result | Meaning |
|--------|---------|
| Native multi-row + multi UI | Conversion should match native MEMOTEXT **shape**, not necessarily grain change |
| Native single-row concatenated | Supports **one row per MEMOKEY** remediation |
| Native multi-row, UI one | Confirms QLAdmin display limitation — concatenation workaround likely |

---

## Decision Matrix (After All Probes)

Use this matrix to classify root cause and **next framework stage**. Fill `Outcome` column in test grid as probes complete.

| ID | Condition (probes) | Root-cause classification | Next stage |
|----|-------------------|---------------------------|------------|
| **D1** | Probe 3: native **2 DBF rows + 2 UI entries**; Probes 1–2 show **1 entry** for converted | Conversion format, load, or index order — **not** native grain | **Risk Agent** → likely format/timestamp fix (B3) before grain change |
| **D2** | Probe 3: native **1 DBF row** (concatenated MEMOTEXT) | Native storage = **one row per policy** | **Risk Agent** → recommend **one QUIKMEMO row per MEMOKEY** (concatenate) |
| **D3** | Probe 3: native **2 DBF rows** but UI **always 1 entry** for converted and native | QLAdmin **display limitation** on duplicate MEMOKEY | **Risk Agent** → concatenation workaround (safest) + vendor ticket |
| **D4** | Probe 2: **2 entries** for 010713704C; Probe 1: **1 entry** for 010335038C only | **Timestamp dedupe** (same Date/Time in header) | **Risk Agent** → distinct timestamp formatting (B3) **before** grain change |
| **D5** | Probe 5: DBF row count **drops** after rebuild | Index rebuild **dedupes** keys | **More UAT** + vendor; **no conversion change** until clarified |
| **D6** | Probe 4: print shows **both**, UI shows **one** | UI-only limitation | **Risk Agent** — print parity may reduce concatenation urgency |
| **D7** | Probes **inconclusive** (missing Sys-Op, no test policy, DBF not inspected) | Behavior **not proven** | **More UAT probing** — do not advance to Risk Agent |

### Remediation preview (for Risk Agent — not approved here)

| Decision | Conversion direction |
|----------|---------------------|
| D1 | Keep one row per source; fix MEMOTEXT header / sort / deploy index |
| D2 | **One QUIKMEMO row per MEMOKEY** — merge PNOTE/PENSE with separators |
| D3 | **Concatenated MEMOTEXT per policy** as safest workaround |
| D4 | Keep multi-row; make **Date/Time unique per source row** (e.g., incorporate Seq) |
| D5 | Hold — vendor/index investigation |
| D6 | Evaluate UI-only impact with client; may defer concatenation |

---

## Evidence Checklist (Sign-Off)

Before closing UAT probe phase, confirm:

- [ ] `Issue_21M_FollowUp_Client_Test_Grid.csv` completed for Probes 1–4 (minimum)
- [ ] Probe 3 attempted or explicitly waived with reason
- [ ] Screenshots or Print Memo output stored (client share path): _______________
- [ ] Decision matrix row **D1–D7** selected
- [ ] No conversion code or QUIKMEMO output modified during probing

---

## Recommendation for Next Framework Stage

| Probe outcome | Next stage |
|---------------|------------|
| Any of **D1–D4** or **D6** with completed grid + Probe 3 result | **Risk Agent** — assess concatenation vs timestamp fix vs vendor path; preserve Issue #25 / #26 |
| **D5** (index drops rows) | **More UAT probing** + QLAdmin vendor; Dependency Gate blocked |
| **D7** (inconclusive) | **More UAT probing** — prioritize Probe 3 and Probe 6; do **not** start Risk Agent |
| Probe 3 waived without native reference (Probe 6) | **Conditional:** Risk Agent may run with **CONDITIONAL GO** only if client accepts assumption documented in grid |

### Suggested Risk Agent entry criteria (G2 prep)

Advance to Risk Agent when:

1. Probe 3 outcome is **known** (or Probe 6 provides equivalent native evidence), **and**
2. Probes 1 and 2 document **visible memo count and text** for both trace policies, **and**
3. Decision matrix row is selected with tester sign-off.

---

## Related Artifacts

| Document | Role |
|----------|------|
| `Issue_21M_FollowUp_Intake_Summary.md` | Intake G0 |
| `Issue_21M_Multiple_Memo_Display_Research_Report.md` | Planning G1 |
| `Issue_21M_FollowUp_Client_Test_Grid.csv` | Probe results capture |
| `Issue_21M_010335038C_DBF_DBT_Trace.csv` | Expected DBF content for Probe 1 / 4 |

**Stop point:** UAT Probe Plan complete. No Development Agent work until Risk Agent **GO** / **CONDITIONAL GO**.
