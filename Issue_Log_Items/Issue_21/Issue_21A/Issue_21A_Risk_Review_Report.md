# Issue #21A — Risk Review Report

**Issue:** #21A — NFO / Dividend Options  
**Date:** 2026-07-04  
**Converter version (baseline):** v57.46  
**Prior stages:** Intake ✅ · Planning ✅ · Dependency Gate ✅  
**Framework stage:** Risk Agent (G3)  
**Next stage:** Development Agent (awaiting explicit user authorization)

**Status note:** Risk analysis only — no production code changes in this stage.

---

## Go / No-Go Recommendation

```text
CONDITIONAL GO
```

Development may proceed for the **Dependency Gate approved scope**:

1. PPBENTYP cache reads **`BF_NON_FORFEITURE`** when **`TYPE_CODE=BF`** (benefit seq 1).
2. Translation **`NF_1→1`**, **`NF_2→1`** (SME APL-first for codes 1 and 2).
3. **`NF_9→0`** safety only — prevents invalid **`MNFOPT=9`** passthrough (not a business remap of code 9).

**Conditions:**

1. Cache enrichment runs **only when `MNFOPT` is already `0`/blank** (preserve existing `app.py` guard — **no regressions** on policies already at 2 or 3).
2. **Do not** change **`NF_3`–`NF_6`**, **`NF_4→0`**, or **`NF_5→0`** entries.
3. Post-dev validator on **8 trace policies** + row-count / #25 / #26 regression checks.

---

## 1. Current vs proposed mapping

| Component | Current | Proposed | Rows affected (surgical) |
|---|---|---|---|
| PPBENTYP cache | `NON_FORFEITURE` only on seq 1 | Prefer **`BF_NON_FORFEITURE`** when **`TYPE_CODE=BF`** | **~1,248** (`0→1`, source code **1**) |
| Translation | Code **2** passthrough → QLAdmin **2** | **`NF_2→1`** | **5** (`2→1`, source code **2**) |
| Translation | Code **1** mostly passthrough | **`NF_1→1`** (explicit) | Included in cache rows above |
| Codes **3–6** | `NF_4→0`, `NF_5→0`, passthrough **3** | **Unchanged** | **0** forced remaps |
| Code **9** | Not in cache today → output **0** | Cache may pull **9** → need **`NF_9→0`** | **83** stay at **0** |
| **`MDIVOPT`** | `DIVIDEND` cache | **No change** in this release | **0** |
| **`MPOLICY` / MPREM** | #25 / #26 | **Unchanged** | **0** |

**Total unique policies with `MNFOPT` change:** **~1,253** (1,248 zero-only enrich + 5 code-2 fixes; overlap minimal).

---

## 2. Premium / related fields untouched

| Target | Source / behavior | Touched? |
|---|---|:---:|
| `quikmstr.MMODPREM` | PPOLC modal premium | **No** |
| `quikridr.MPREM` | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| `MPOLICY` width | `format_qladmin_mpolicy()` (#25) | **No** |
| `quikplan.NFOINT` | CSO crosswalk (#21D) | **No** |
| `quikdvdp.*` | Issue #38 | **No** |
| Row count `quikmstr` | 5,083 | **No** |
| All other tables | — | **No** |

---

## 3. Repo references

| Location | Role |
|---|---|
| `QLA_Migration/app.py` ~5327–5356 | PPBENTYP cache build — **`NON_FORFEITURE` only today** |
| `QLA_Migration/app.py` ~5858–5875 | Cache pull when **`MNFOPT` is 0** — **must preserve guard** |
| `QLA_Migration/app.py` ~6012–6018 | `NF_` prefix translation + numeric shield |
| `Master_Value_Translation.csv` | Add **`NF_1`**, **`NF_2`**; optional **`NF_9→0`** |
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` | `NFO_OPT→MNFOPT` default 0 — **no rulebook change required** |
| `QLA_Migration/_risk_review_issue21a_nfo.py` | Simulation script |
| `Issue_21A_Risk_Simulation.csv` | Full before/after grid |

---

## 4. Population analysis (simulated)

| Metric | Count |
|---|---:|
| Total `quikmstr` policies | 5,083 |
| **`MNFOPT` changes (surgical rules)** | **~1,253** |
| **`MNFOPT` unchanged** | **~3,830** |
| Zero-only enrich `0→1` (source code **1**) | **1,237** |
| Translation fix `2→1` (source code **2**) | **5** |
| Additional zero-only (source **2**, was 0) | **~11** |
| Source code **4** / **5** at `MNFOPT=0` after fix | **0** (NF_4/NF_5 unchanged) |
| Source code **9** at risk of **`MNFOPT=9`** without safety | **83** → **0** with **`NF_9→0`** |

### Current output distribution (baseline v57.46)

| `MNFOPT` | Policies |
|:---:|:---:|
| 0 | 3,768 |
| 1 | 438 |
| 2 | 470 |
| 3 | 407 |

### Proposed net effect (approximate)

| Direction | Policies |
|---|---:|
| `0 → 1` | ~1,248 |
| `2 → 1` | 5 |
| All other values | unchanged |

---

## 5. Fallback recommendation

| Scenario | Rule | Assessment |
|---|---|---|
| BF row blank, BA `NON_FORFEITURE` populated | Use BA column (current fallback) | **Keep** |
| Both blank | `MNFOPT` stays **0** | **Keep** |
| Source code **9** after cache pull | **`NF_9→0`** → output **0** | **Required safety** — not a scope expansion |
| Source code **4** / **5** on zero rows | **`NF_4→0`**, **`NF_5→0`** unchanged | **By design** — client scope lock |
| `MNFOPT` already non-zero | **Do not overwrite** | **Critical** — prevents 667 false “full recompute” regressions |

**Rejected:** Full recompute of `MNFOPT` from PPBENTYP for all policies (would regress **667** rows currently at 2/3).

---

## 6. Trace policies (surgical simulation)

| Policy | Source | Before | After | Pass? |
|---|---|:---:|:---:|:---:|
| 010765930C | BF `BF_NF=1` | 0 | **1** | ✅ |
| 010718309C | BF `BF_NF=1` | 0 | **1** | ✅ |
| 010818663C | BF `BF_NF=1` | 0 | **1** | ✅ |
| 010469666C | `NF=2` | 2 | **1** | ✅ |
| 010391895C | BA `NF=4` | 0 | **0** | ✅ out of scope |
| 010448806C | BA `NF=5` | 0 | **0** | ✅ out of scope |
| 010713704C | BF `BF_NF=4` | 0 | **0** | ✅ out of scope |
| 010391876C | BA `NF=4` | 2 | **2** | ✅ no overwrite |

---

## 7. Material impact assessment

| Category | Assessment |
|---|---|
| **Intentional corrections** | ~1,253 policies gain correct **APL (1)** where LifePRO code **1** or **2** was in source but output was **0** or **2** |
| **Known non-fix** | Policies with LifePRO codes **4** / **5** remain **`MNFOPT=0`** per client scope — includes Issue #21 samples 010391895C, 010448806C, 010713704C |
| **Accidental drift risk** | **Low** if enrich-on-zero-only preserved; **High** if full recompute implemented |

---

## 8. Prior fix preservation

| Check | Result |
|---|---|
| Issue #25 MPOLICY padding | **Pass** — no MPOLICY logic in scope |
| Issue #26 MPREM / MMODPREM | **Pass** — quikridr/quikmstr premium fields untouched |
| Issue #38 quikdvdp | **Pass** — separate table |
| Issue #21D NFOINT | **Pass** — plan-level field separate path |

---

## 9. Regression testing checklist (Validation Agent)

- [ ] **010765930C**, **010718309C**, **010818663C** → `MNFOPT=1`
- [ ] **010469666C** → `MNFOPT=1` (was 2)
- [ ] **010391895C**, **010448806C**, **010713704C** → `MNFOPT=0` (unchanged)
- [ ] **010391876C** → `MNFOPT=2` (unchanged — non-zero not overwritten)
- [ ] Sample with source code **9** → `MNFOPT=0` (not 9)
- [ ] `quikmstr` row count = **5,083**
- [ ] #25 MPOLICY width validator pass
- [ ] #26 MPREM unchanged on control policies
- [ ] Policies with current `MNFOPT` ∈ {2,3} and source 4/5: **no change**

---

## 10. Recommended Development Agent task

1. **`app.py` / `QLA_Migration/app.py`:** In PPBENTYP cache build (~5327), for each policy at benefit seq 1, resolve NFO as: **`BF_NON_FORFEITURE`** if `TYPE_CODE=BF` and populated, else **`NON_FORFEITURE`**. Keep existing **`BENEFIT_SEQ=01`** filter and dedupe by policy.
2. **`Master_Value_Translation.csv`** (+ mirror): Add **`NF_1,1`** and **`NF_2,1`**. Add **`NF_9,0`** (safety only). **Do not** edit **`NF_3`–`NF_6`**, **`NF_4`**, **`NF_5`**.
3. **Preserve** cache pull guard: only enrich when rulebook value is **`0`/blank** (~5858).
4. **Version bump:** v57.47 (Issue #21A).
5. **Validator:** `tools/validators/validate_issue21a_mnfopt.py` — trace table + non-overwrite spot checks.

**Do NOT:** Full recompute MNFOPT; change MDIVOPT logic; remap codes 3–6.

---

## 11. G3 gate

- [x] Risk report published with **Conditional Go**
- [x] Impact quantified (~1,253 surgical changes)
- [x] Unrelated fields marked untouched
- [x] #25 / #26 preservation confirmed
- [ ] User authorization for Development

**Recommended issue status:** **Ready for Development**

---

## Appendix

- Simulation: `Issue_Log_Items/Issue_21/Issue_21A/Issue_21A_Risk_Simulation.csv`
- Script: `QLA_Migration/_risk_review_issue21a_nfo.py`
- Dependency Gate: `Issue_21A_Dependency_Gate.md`
