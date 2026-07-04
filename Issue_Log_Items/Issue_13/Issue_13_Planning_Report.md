# Issue #13 — Planning Report

**Issue:** #13 — Incorrect QL Status  
**Framework stage:** Planning Agent (G1)  
**Status:** Ready for Dependency Gate  
**Generated:** 2026-07-04  
**Decision:** **Option A** — when `CONTRACT_CODE = T`, termination (`CONTRACT_CODE` + `CONTRACT_REASON`) takes precedence over `PAID_UP_TYPE` for `quikmstr.MSTATUS`  
**Owner:** Conversion (Warren) · **Reporter:** Eric

---

## 1. Executive Finding

Issue #13 is confirmed: **611** terminated policies carry a non-forfeiture `PAID_UP_TYPE`, and the converter currently emits QLAdmin codes **41 / 44 / 45** (Paid Up, Extended Term, RPU) instead of termination codes **53 / 54 / 55 / 56 / 57** aligned with LifePRO `PPBEN` and `PPOLC` contract status.

**Warren approved Option A (2026-07-04):** for **`CONTRACT_CODE = T`**, build the MSTATUS composite key from **`CONTRACT_CODE` + `CONTRACT_REASON`** only; ignore `PAID_UP_TYPE`. For all other contract codes, retain existing PAID_UP_TYPE-first logic.

Simulated fleet impact: **607 policies** change `MSTATUS`; **4,477** unchanged. Sample **010516211C** moves **44 → 54** (Lapsed); **011101663C** moves **41 → 56** (Expired). Surgical single-interceptor change in `app.py`; no rulebook or `Master_Value_Translation.csv` edits required.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File | In Source/? | Row count |
|--------------|------|-------------|----------:|
| Policy Master | `PPOLC_PolicyMaster_Extract_20260530.csv` | Yes | 5,084 |
| Policy Benefit | `PPBEN_PolicyBenefit_Extract_20260530.csv` | Yes | (benefit grain) |

### Available source fields (MSTATUS drivers)

| Field | Column | Populated | Notes |
|-------|--------|-----------|-------|
| Policy number | `POLICY_NUMBER` | 100% | Join via `Master_Crosswalk.csv` |
| Contract status | `CONTRACT_CODE` | 100% | A/T/S/P/I/D — **T = Terminated** |
| Termination reason | `CONTRACT_REASON` | ~99% | DC, SR, LP, MA, EX, CV, … |
| Non-forfeiture type | `PAID_UP_TYPE` | subset | PU, RU, ET, LE, LP, SP — **ignored when T** |
| Status date | `CONTRACT_DATE` | populated | Maps to `MSTATDATE` (unchanged) |

**PPBEN** `STATUS_CODE` / `STATUS_REASON` — reference only; **not** used for `quikmstr.MSTATUS` today or after fix.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Role |
|-------|-------|------|------|
| `quikmstr` | `MSTATUS` | numeric code | Policy-level status |
| `quikmstr` | `MSTATDATE` | date | Contract/status date (unchanged) |
| `quikridr` | `MPHSTAT` | numeric code | Phase-1 inherits terminal `MSTATUS` from emitted `quikmstr` cache |

**Repo references:**

| Location | Role |
|----------|------|
| `app.py` ~5870–5878 | MSTATUS composite interceptor (**change here**) |
| `app.py` ~6035–6037 | `ST_*` prefix + `Master_Value_Translation.csv` lookup |
| `app.py` ~6170–6185 | quikridr phase-1 `MPHSTAT` inherits non-active `quikmstr.MSTATUS` |
| `Master_Value_Translation.csv` | `ST_T_*`, `ST_PUT_*` → QLAdmin codes |
| `Sync_Rulebook_quikmstr.csv` | `CONTRACT_CODE` → MSTATUS (overridden by interceptor) |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPOLC | `CONTRACT_CODE` + `CONTRACT_REASON` | `quikmstr.MSTATUS` | When `CONTRACT_CODE=T`: key `ST_{T}_{reason}` | **Yes** |
| PPOLC | `PAID_UP_TYPE` | `quikmstr.MSTATUS` | Used only when `CONTRACT_CODE ≠ T` | **Yes (precedence)** |
| PPOLC | `CONTRACT_DATE` | `MSTATDATE` | Direct | No |
| quikmstr | `MSTATUS` | `quikridr.MPHSTAT` | Phase-1 cache inherit (automatic on re-batch) | Indirect |

### Proposed interceptor logic (pseudocode — do not implement in Planning)

```python
if t_f == 'MSTATUS' and t_id.lower() == "quikmstr":
    c_code = normalize(CONTRACT_CODE)
    c_reason = normalize(CONTRACT_REASON)
    if c_code == 'T':
        val = f"{c_code}_{c_reason}" if c_reason else f"{c_code}_"
    else:
        put = normalize(PAID_UP_TYPE)
        if put in ['PU', 'RU', 'ET', 'LE', 'LP', 'SP']:
            val = f"PUT_{put}"
        else:
            val = f"{c_code}_{c_reason}" if c_reason else f"{c_code}_"
```

### Fields that must remain unchanged

| Target | Current source | Touch? |
|--------|----------------|--------|
| `quikmstr.MMODPREM` / modal fields | PPOLC | **No** |
| `quikridr.MPREM` | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| `MPOLICY` | `format_qladmin_mpolicy()` (#25) | **No** |
| `MNFOPT` / `MDIVOPT` | PPBENTYP cache (#21A) | **No** |
| `Master_Value_Translation.csv` | ST_* keys | **No** |
| Claim `CLAIMSTAT` | Phase 10B lifecycle | **No** |

---

## 5. Open Client Questions

1. ~~Termination vs non-forfeiture precedence~~ — **Resolved: Option A (termination wins when T).**
2. **Edge case:** `CONTRACT_CODE=T` with blank `CONTRACT_REASON` → key `ST_T_` (unmapped today). Recommend fallback to `ST_T_` → leave blank or map to generic terminated — **0 fleet policies** in current extract with T + blank reason + PUT set.
3. **UAT acceptance:** Eric to spot-check **010516211C** (54 Lapsed) and **011101663C** (56 Expired) after batch.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + 10-char MPOLICY padding (#25) — unchanged |
| MSTATUS | Numeric string via existing `ST_*` translation |
| Blanks | If proposed key unmapped, retain pre-translation composite (existing `trans_map.get` fallback) |

---

## 7. Memo / Text / Special Handling

N/A — no memo or long-text fields affected.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `Master_Crosswalk.csv` → QLA `MPOLICY`
2. `format_qladmin_mpolicy()` applied on emit — unchanged
3. Orphan handling — unchanged

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| PPOLC source policies | 5,084 | Source extract |
| quikmstr rows | 5,084 | 1:1 policy master |
| **MSTATUS would change** | **607** | `_risk_review_issue13_mstatus.py` |
| Unchanged | 4,477 | Same simulation |
| T + non-blank PUT (trigger population) | 611 | PPOLC scan |
| T + LP subset (Eric sample class) | 187 | Prior trace |

### Top transition buckets (current → proposed)

| Transition | Count |
|------------|------:|
| 41 Paid Up → 53 Terminated/Death | 174 |
| 44 Extended Term → 57 Matured | 86 |
| 45 RPU → 53 Terminated/Death | 78 |
| 44 Extended Term → 54 Lapsed | 69 |
| 44 Extended Term → 55 Surrendered | 63 |
| 41 Paid Up → 55 Surrendered | 29 |

---

## 10. Sample Trace (5 policies)

| Policy (QLA) | LifePRO | Before | After (Option A) | Notes |
|--------------|---------|-------:|-----------------:|-------|
| 010516211C | T / LP / LE | 44 | **54** | Eric sample — Lapsed |
| 011101663C | T / EX / PU | 41 | **56** | Eric sample — Expired |
| 010397318C | T / DC / RU | 45 | **53** | Death claim + RPU |
| 010464590C | T / DC / RU | 45 | **53** | Status analysis example |
| 010784054C | T / EX / (blank) | 56 | **56** | Already correct |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| 607 policies shift reporting/governance buckets (Issue #34 ISRR joins) | Medium | Re-run dependent governance after batch; document in validation |
| quikridr MPHSTAT inherits new terminal codes | Low | Automatic via existing cache; validate phase-1 rows |
| Unmapped `ST_*` keys (2 rows: header garbage + `ST_S_PC`) | Low | Pre-existing; not introduced by this change |
| Claims cross-domain pairs (RPU + Settled) | Low | Claim status unchanged; business already reviewed in status_analysis |
| Regression on #25 / #26 / #21A | Low | Validator + protected-issue checks |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| PPOLC in Source/ | Yes |
| Field definitions confirmed | Yes |
| Business rule (Option A) | Yes — Warren 2026-07-04 |
| Example policies | Yes |
| QLAdmin MSTATUS codes in Master_Value_Translation | Yes |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue #13: Incorrect QL Status (Option A)

Read AI_Agents/Risk_Agent.md, Issue_13_Planning_Report.md, and run
Issue_Log_Items/Issue_13/_risk_review_issue13_mstatus.py.

Quantify 607-policy MSTATUS transition impact. Confirm #25/#26 untouched.
Recommend GO for surgical app.py interceptor change only. Do not code.
```

---

## 14. Recommended Development Task (Do Not Implement Until G3 GO)

1. Edit `app.py` and `QLA_Migration/app.py` MSTATUS interceptor (~5870): add `CONTRACT_CODE == 'T'` branch per §4 pseudocode.
2. Bump version to **v57.48** with change note for Issue #13.
3. Add `tools/validators/validate_issue13_mstatus.py` — assert sample policies + fleet change count ≈ 607.
4. Re-run full batch; confirm `quikmstr` row count unchanged (5,084).
5. Update `plan_analysis/status_analysis/status_analysis_runner.py` `derive_mstatus_from_source_fields()` to mirror new rule (read-only parity).

---

## Appendix

- Simulation: `Issue_13_Risk_Simulation.csv`, `_risk_review_issue13_mstatus.py`
- Intake: `Issue_13_Intake_Summary.md`
- Related: `plan_analysis/status_analysis/`
