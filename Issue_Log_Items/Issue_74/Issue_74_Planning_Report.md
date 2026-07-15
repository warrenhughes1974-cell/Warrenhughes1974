# Issue #74 — Planning Report

**Issue:** #74 — Var DB Code (`VARDB`) `4` → `0` only  
**Framework stage:** Planning Agent  
**Status:** Ready for Dependency Gate  
**Generated:** 2026-07-15  
**Revised:** 2026-07-15 (scope: not all plans)  
**Model:** Cursor Grok 4.5 (locked)  
**Scope decisions:** `Issue_74_Scope_Decisions.md`  
**Intake:** `Issue_74_Intake_Summary.md`

---

## 1. Executive Finding

Client wants Var DB Code **`0`**, but **only** where the plan is currently **`4`**. Plans already at structure codes **`1` / `2` / `3` must not change**.

**Direction:** One-line Sync Rulebook default `VARDB` `4` → `0`. **Keep** Option B (`apply_vardb_structure_overrides*`) so ~20 structure plans continue to emit `1`/`2`/`3`. Expected: **121** plans `4`→`0`; **20** unchanged. Ready for Dependency Gate / Risk.

---

## 2. Confirmed LifePRO Source

N/A — rulebook constant. No LifePRO column for VARDB.

---

## 3. Confirmed QLAdmin Target

| Table | Field | Change |
|-------|-------|--------|
| quikplan | VARDB | Default `4` → `0`; Option B still may set `1`/`2`/`3` |

---

## 4. Mapping

| Source | Target | Transformation | Change? |
|--------|--------|----------------|---------|
| *(constant)* | `quikplan.VARDB` | Rulebook default **`0`** (was `4`) | **Yes** |
| Variation audit Option B | `quikplan.VARDB` | Keep applying `1`/`2`/`3` when classified | **No change to Option B** |

### Must not change

| Target | Touch? |
|--------|--------|
| Plans with VARDB 1/2/3 | **No** |
| VARGP | **No** |
| #25 / #26 | **No** |
| QuikDbs content | **No** |

---

## 5. Open Client Questions

1. **OBQ-74-1:** Confirm: only `4`→`0`; leave `1`/`2`/`3` alone.  
   - **Locked (client clarification):** **Yes.**

2. **OBQ-74-2:** Leave `VARGP` at `4`?  
   - **Assumption:** **Yes.**

No remaining blockers.

---

## 6. Formatting

`VARDB` literal `0` for default plans; structure codes remain single digit `1`/`2`/`3`.

---

## 7–8. Memo / Policy keys

N/A.

---

## 9. Estimated Record Counts

| Population | Count |
|------------|------:|
| quikplan rows | 141 |
| Change `4` → `0` | **121** |
| Unchanged (`1`/`2`/`3`) | **20** |
| Residual `VARDB=4` after fix (target) | **0** |

---

## 10. Sample Trace

| PLAN | VARDB today | After | Notes |
|------|-------------|-------|-------|
| `920ADB` | 4 | **0** | In scope |
| `130JEB` | 3 | **3** | Out of change scope |
| `17CSI3` | 2 | **2** | Out of change scope |
| `1659SR` | 1 | **1** | Out of change scope |
| `A60MIR` | 2 | **2** | Out of change scope |

---

## 11. Risks

| Risk | Notes |
|------|-------|
| Disabling Option B by mistake | Would zero out structure plans — **must not** do that under revised scope |
| Governance “VARDB ≠ 4 → QuikDbs” | Now applies to `0` plans + structure plans; Risk notes audit impact |
| #72 `VARDB≠0` alternate | Still true for structure plans; default plans use QuikPlCv |

---

## 12. Recommended Risk Prompt

```
Proceed to Risk Agent for Issue 74.

Read Issue_74_Planning_Report.md + Scope_Decisions (revised: 4→0 only).

Quantify 121 deltas; confirm 20 structure plans unchanged; rulebook-only path.
Do not code.
```

---

## 13. Recommended Development Task (do not implement)

1. Change `Sync_Rulebook_quikplan.csv` `VARDB` Default_Value `4` → `0`.
2. **Do not** disable `apply_vardb_structure_overrides*`.
3. Validator: count(`VARDB=4`)=0; count of `1`/`2`/`3` unchanged vs before baseline; spot-check `920ADB`→0 and `130JEB`→3.
4. On PASS: publish `quikplan.csv` to `Output/Test_Validation/`.
5. Version bump only if `app.py` touched (rulebook-only → typically no bump unless converter touched).

---

## Gate Criteria (G1)

- [x] Revised scope documented  
- [x] Trace includes keep vs change  
- [x] No code changes  
