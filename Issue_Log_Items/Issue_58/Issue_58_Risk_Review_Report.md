# Issue #58 — Risk Review Report

**Issue:** #58 — Premium Mode Amounts Incorrect  
**Framework stage:** Risk Agent (G3)  
**Status:** **Conditional Go**  
**Fallback simulated:** Option B — GL85 / high-confidence plans only (reject as primary)  
**Generated:** 2026-07-13  
**Agent:** Risk Agent (read-only) · Model: Cursor Grok 4.5  
**Simulation:** `evidence/issue58_risk_simulation.csv`  
**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Implement post-emit `quikridr` modal-fee derivation (`MANNLFEE × post-PAC quikmstr factors`) for all base rows with `MANNLFEE > 0`; require re-batch with #36 factors populated; treat ISWL Names-tab UAT as mandatory; leave OBQ-1 open (client may later restrict plan set).

Rationale: Eric’s policy and PAC GL85 samples reconcile exactly; blast radius is four fee columns only; unrelated premium fields untouched. GPT/Planning caveat remains: fee schedule may differ from premium factors on some products — Conditional, not No-Go.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| quikridr.MANNLFEE | PPOLC POLICY_FEE (#21C) | unchanged | **No** |
| quikridr.MSEMIFEE | blank | `MANNLFEE × MSEMI/100` | **Yes** |
| quikridr.MQTRLFEE | blank | `MANNLFEE × MQTRL/100` | **Yes** |
| quikridr.MMTHDFEE | blank | `MANNLFEE × MMTHD/100` | **Yes** |
| quikridr.MMTHBFEE | blank | `MANNLFEE × MMTHB/100` | **Yes** |
| quikmstr MSEMI…MMTHB | #36 + PAC | read after PAC | **No** |
| quikplan *FEE | 0.0000 | leave | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikmstr.MMODEPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | #26 | **No** |
| quikridr.MANNLFEE | #21C | **No** |
| quikmstr MSEMI/MQTRL/MMTHD/MMTHB | #36 / PAC | **No** (read-only) |
| MPOLICY padding | #25 | **No** |
| Sync_Rulebook_quikplan fee defaults | 0.0000 | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `app.py` / `QLA_Migration/app.py` | #21C MANNLFEE; post-ridr #36 factor + PAC on quikmstr |
| `qla_core/modal_premium_factors.py` | Factor + PAC; **add fee apply here** |
| `Sync_Rulebook_quikridr.csv` | M*FEE unmapped — keep post-emit pattern |
| Live `Output/quikmstr.csv` | **0** non-blank MSEMI — stale vs #36; **must re-batch** |
| Live `Output/quikridr.csv` | 4,457 MANNLFEE populated; modal fees blank |

---

## 4. Population Analysis

**Simulation basis:** Issue_45 `quikmstr` (factors present) + Issue_49 `quikridr` (fees). Live Output alone cannot simulate amounts until factors are re-emitted.

| Metric | Count |
|--------|------:|
| Base quikridr rows | 5,083 |
| `MANNLFEE` ≤ 0 (unchanged / no fee write) | 626 |
| Rows that would gain modal fees | **4,457** |
| Missing factors in sim baseline | 0 |
| Plans touched | 32 |
| Top plans | 1659C2 (1,147), 1659CR (641), 1658C1 (435), 1L1095 (378), 170858 (209), 17085M (153) |

### Before / after Names-tab (simulated)

QLAdmin display model used:  
`(MPREM × MUNIT × factor/100) + modal_fee`

| Policy | Before Q / Mth | After Q / Mth | Eric / note |
|--------|----------------|---------------|-------------|
| 010367131C | 13.13 / 4.46 | **15.90 / 5.40** | **PASS** |
| 010367132C | 13.13 / 4.46 | 15.90 / 5.40 | Sibling GL85 |
| 010560185C | 12.39 / 4.46 | 15.00 / 5.40 | PAC Q factor 25% |
| 010442216C | 29.03 / 9.86 | 31.80 / 10.80 | PAC S factor 50% on semi fee |
| 010380808C | 29.04 / 9.86 | 31.69 / 10.76 | Traditional |
| 010713704C | 135.52 / 46.18 | 142.27 / 48.48 | ISWL — UAT |

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| **A — Fleet all `MANNLFEE > 0`** | 4,457 | **Recommended Conditional Go** — matches #21C/#36 fleet pattern; OBQ-1 open |
| B — Allowlist high-confidence plans only (e.g. 17085M/170858 + 100% mode3/6 proxy) | ~few hundred | Reject as primary — leaves most fee-bearing policies broken |
| C — Wait for client OBQ-1 before any code | 0 | Reject — Eric No-Go clear; Help fields defined |
| D — Populate quikplan modal fees | plan table | **Reject** — no authority; defaults 0 |

**Recommended:** Option **A** with Conditional controls below.

### Conditional controls (required)

1. Wire fee derive **after** `apply_pac_gl85_modal_overrides`.  
2. Full batch must emit #36 factors (current Output fails this).  
3. Validation must assert Eric + PAC traces; ISWL sample UAT called out.  
4. If client later answers OBQ-1 “no for ISWL,” add plan exclude list in a follow-up issue — do not block Eric fix.

---

## 6. Trace Policies

| Policy | Proposed fees S/Q/D/B | After Q / Mth | Pass? |
|--------|----------------------|---------------|-------|
| 010367131C | 5.4288 / 2.7666 / 0.9396 / 0.8700 | 15.90 / 5.40 | **PASS** |
| 010560185C | 5.4288 / **2.6100** / 0.9396 / 0.8700 | 15.00 / 5.40 | **PASS** (PAC) |
| 010442216C | **5.2200** / 2.7666 / … | — | **PASS** fee uses MSEMI=50 |
| 010713704C | 13.1250 / 6.7500 / 2.3000 / 2.2005 | 142.27 / 48.48 | **UAT** |

---

## 7. Top Largest Changes (simulated Q delta)

Largest quarterly Names-tab increases = largest `MANNLFEE × MQTRL/100` (often $50 fee × ~27% ≈ **$13.50**).

| Policy | Plan | MANNLFEE | Before Q | After Q | ΔQ |
|--------|------|----------|----------|---------|-----|
| 011052719C | 5L0110 | 50.00 | 80.19 | 93.69 | 13.50 |
| 011053767C | 5L0110 | 50.00 | 324.00 | 337.50 | 13.50 |
| (10+ similar 5L0110) | … | 50.00 | … | … | 13.50 |

These are **intentional** fee add-backs, not base-premium rewrites.

---

## 8. Material Calculation Impact

| Impact | Assessment |
|--------|------------|
| Names-tab hypothetical modes | **Corrected** when fee present |
| Billed `MMODEPREM` | **Unchanged** (already includes fee in LifePRO mode prem) |
| Coverage `MPREM` | **Unchanged** |
| Current Output without factors | Fee derive alone **insufficient** — factors must be present first |

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserve** — join via `format_qladmin_mpolicy` |
| Issue #26 MPREM / MMODEPREM | **Preserve** — not in write set |
| Issue #21C MANNLFEE | **Preserve** |
| Issue #36 factors + PAC | **Preserve** — prerequisite; fees after PAC |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] `010367131C` Names amounts $60 / $31.20 / $15.90 / $5.40 (or CSV fee fields that produce them)
- [ ] PAC `010560185C` MQTRLFEE uses factor **25** → 2.6100
- [ ] PAC `010442216C` MSEMIFEE uses factor **50** → 5.2200
- [ ] `MANNLFEE`, `MPREM`, `MMODEPREM` unchanged vs pre-change baseline on Eric set
- [ ] Fleet: modal fees non-blank iff `MANNLFEE > 0` on MPHASE 1
- [ ] MPHASE > 1 modal fees remain blank
- [ ] `quikmstr` factors non-blank fleet-wide (re-batch smoke)
- [ ] ISWL sample `010713704C` documented for client UAT (not auto-fail if client disputes)

---

## 11. Recommended Development Agent Task

**Assigned model:** Composer 2.5 (Development stage)  
**Blocked until:** User acknowledges this Conditional Go

1. Add `apply_modal_policy_fees_to_quikridr(ridr_df, mstr_df)` in `qla_core/modal_premium_factors.py`.  
2. Call it in both `app.py` files **after** plan-factor copy **and** PAC overrides; rewrite `quikridr.csv`.  
3. Base phase only; skip `MANNLFEE ≤ 0`; format 4 decimals.  
4. Bump `APP_VERSION` in **both** app.py files.  
5. Add `tools/validators/validate_issue58_quikridr_modal_fees.py`.  
6. Do **not** change rulebooks for MANNLFEE/MPREM/MMODEPREM or quikplan *FEE defaults.  
7. Re-batch full conversion so factors + fees coexist in Output.

---

## Appendix

- Simulation: `evidence/issue58_risk_simulation.csv`  
- Planning evidence: `issue58_fee_factor_mode_match.csv`, `issue58_plan_mode36_match_rollup.csv`  
- Dependency Gate: `Issue_58_Dependency_Gate.md` (**PASS**)  
- Related: #21C, #21J, #36, #26, #25
