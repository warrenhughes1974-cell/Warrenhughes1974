# Issue #72 — Intake Summary

**Issue:** #72 — NFO option must match ETI/RPU status (`MSTATUS` 44/45 → `MNFOPT` 2/3)  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Planning  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (primary)  
**Priority:** Go-No Go — Robert validation rule; wrong NFO on exercised ETI/RPU misleads Policy Display / CV path  
**Reporter chain:** Robert (validation checklist) · Warren YE UAT · sample `010407670C` (Status RPU / NFO ETI)

---

## Client symptom (verbatim)

Robert:

> Also, validate that the NFO opt code matches the status (i.e. if the status is 44, the NFO code is 2 for ETI; if the status code is 45, the NFO code is 3 for RPU.

Observed on Policy Display **`010407670C`**: Status **RPU** (`MSTATUS=45`) while Options NFO shows **2** (ETI).

---

## Normalized symptom

| Field | Meaning | Required when exercised |
|-------|---------|-------------------------|
| `quikmstr.MSTATUS` **44** | On ETI | `MNFOPT` **2** |
| `quikmstr.MSTATUS` **45** | On RPU | `MNFOPT` **3** |

Today `MNFOPT` is driven by LifePRO **elected** NFO on `PPBENTYP.NON_FORFEITURE` / `BF_NON_FORFEITURE`, translated per Issue **#57** (LP 3/4/5 → QLA 1/2/3). That election often **does not** equal the currently exercised status from `PAID_UP_TYPE` (e.g. PUT=`RU` → status 45 while election was LP `4` ETI → `MNFOPT=2`).

**Design conflict to resolve in Planning:** #57 made election authoritative and removed `PAID_UP_TYPE→MNFOPT`. Robert’s rule requires **exercised status to win for 44/45 only**.

---

## Example policies

| QLA | MSTATUS | MNFOPT today | Required MNFOPT | LifePRO notes |
|-----|---------|--------------|-----------------|---------------|
| **`010407670C`** | **45** RPU | **2** ETI | **3** RPU | `NON_FORFEITURE=4` (ETI election); `PAID_UP_TYPE=RU` |
| Peer class | 44 | ≠2 | 2 | Fleet mismatches below |
| Peer class | 45 | ≠3 | 3 | Fleet mismatches below |

Issue #57 Eric samples (for regression guard — most are **not** status 44/45 today):

| Policy | MSTATUS | MNFOPT | Note |
|--------|---------|--------|------|
| 010367131C | 22 | 2 | Active; election ETI — **out of 44/45 force scope** |
| 010148272C | 22 | 2 | Same |
| 010143726C | 22 | 2 | Same |
| 010392763C | 53 | 3 | Not 44/45 |
| 011221309C | 53 | 1 | Not 44/45 |

---

## Fleet snapshot (Output `quikmstr.csv`, 2026-07-15)

| Status | Policies | MNFOPT mismatch vs Robert | Distribution (MNFOPT) |
|--------|----------|---------------------------|------------------------|
| **44** | 206 | **98** (≠2) | 2:108 · 0:86 · 1:12 |
| **45** | 194 | **179** (≠3) | 0:80 · 1:55 · 2:44 · 3:15 |
| **Total force candidates** | 400 | **277** | — |

---

## Suspected domain

**Policy master (`quikmstr.MNFOPT`)** — post-map or post-status override when `MSTATUS` ∈ {44, 45}.  
Not a rate-table issue. Not `quikridr` unless Planning finds a rider-level NFO display dependency (none known at intake).

Affected QLAdmin table: **`quikmstr`** (`QLAdmin_Converted_Tables.txt`).

---

## In scope / out of scope (first pass)

| In scope | Out of scope |
|----------|----------------|
| When `MSTATUS` is **44**, set/force `MNFOPT=2` | Changing MSTATUS / PUT mapping (#13, #49, #59) |
| When `MSTATUS` is **45**, set/force `MNFOPT=3` | Reverting #57 LP 3/4/5 → 1/2/3 for **non**-44/45 policies |
| Preserve #57 election path for statuses other than 44/45 | MDIVOPT / dividend rules |
| Validator asserting Robert’s 44→2 / 45→3 rule | Blanking NFO on active policies |
| Re-batch `quikmstr` + `Test_Validation` publish | Rebuild-CV tooling itself (UAT follow-up only) |

---

## Related issues

| Issue | Relationship |
|-------|----------------|
| **#57** (CLOSED) | Election mapping LP→QLA; removed PUT→MNFOPT. **#72 narrows** that for exercised 44/45 only. |
| **#21A** (CLOSED) | BF_NON_FORFEITURE cache; NF_1/NF_2→APL |
| **#13 / #49 / #59** | MSTATUS derivation — do not reopen unless status itself is wrong |
| **#60** | NFOINT / PUA CV — separate (interest), not MNFOPT |

**Not a regression of #25 / #26** (MPOLICY pad / MPREM).

---

## Artifact inventory

| Have | Missing |
|------|---------|
| Robert rule (verbatim) | Written CSO/Eric sign-off that status overrides election for 44/45 (Planning may treat Robert as authority) |
| Sample policy + screenshot context (`010407670C`) | None required for Intake |
| Output fleet counts | — |
| LifePRO source proof (`NON_FORFEITURE=4`, `PAID_UP_TYPE=RU`) | — |
| Tracking row TSV | — |

---

## Immediate blockers visible at intake

None for Intake. Planning must lock:

1. **Override timing** — after status is final (including any #49-style MSTATUS overrides).  
2. **Authority** — Robert wins over #57 election for 44/45 only.  
3. **Whether status 44/45 with MNFOPT currently 0/1/2/3 all get forced** (intake assumes **yes — always force**).

---

## Gate Criteria (G0 — Intake Complete)

- [x] Issue folder created under `Issue_Log_Items/Issue_72/`
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

---

## Recommended next step

**Planning Agent** (Cursor Grok 4.5) — surgical override design, blast radius on 277 policies, interaction relative to #57, validator spec.
