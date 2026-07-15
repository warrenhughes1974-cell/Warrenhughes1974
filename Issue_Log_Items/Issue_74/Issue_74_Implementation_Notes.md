# Issue #74 — Implementation Notes

**Issue:** Var DB Code (`VARDB`) `4` → `0` only  
**Version:** Rulebook-only (no `app.py` bump)  
**Date:** 2026-07-15  
**Model:** Composer 2.5 (Development)

---

## Change summary

Changed Sync Rulebook default for `quikplan.VARDB` from **`4`** to **`0`**. Option B structure overrides left enabled — 20 plans keep `1`/`2`/`3`.

---

## Files changed

| File | Change |
|------|--------|
| `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv` | `VARDB` Default_Value `4` → `0` |
| `tools/validators/validate_issue74_vardb.py` | New fleet validator |
| `Issue_Log_Items/Issue_74/scripts/validate_issue74_vardb.py` | Wrapper |
| `QLA_Migration/Output/quikplan.csv` | Re-emitted via product setup runner (141 rows) |
| `QLA_Migration/Output/Test_Validation/quikplan.csv` | Published for partial UAT reload |

**Not changed:** `app.py`, Option B (`apply_vardb_structure_overrides*`), `VARGP`, QuikDbs, quikmstr/quikridr, #25/#26.

---

## Before / after trace

| PLAN | VARDB before | VARDB after | Notes |
|------|--------------|-------------|-------|
| `920ADB` | 4 | **0** | In scope |
| `965ADB` | 4 | **0** | In scope |
| `130JEB` | 3 | **3** | Structure — unchanged |
| `17CSI3` | 2 | **2** | Structure — unchanged |
| `1659SR` | 1 | **1** | Structure — unchanged |
| `A60MIR` | 2 | **2** | Structure — unchanged |

**Fleet:** 121 × `4`→`0`; 20 structure plans unchanged. Distribution: `0`:121 · `1`:3 · `2`:7 · `3`:10 · `4`:0.

---

## Validation

```bash
python tools/validators/validate_issue74_vardb.py
```

**Result (2026-07-15):** **PASS** — 0 residual `VARDB=4`; structure baseline stable; trace plans OK; `VARGP` all `4`.

Evidence: `Issue_Log_Items/Issue_74/evidence/issue74_validation_summary.csv`

### Issue #72 regression guard

```bash
python tools/validators/validate_issue72_mnfopt_status.py
```

**Result:** **FAIL (expected collateral)** — 91 NFO>0 life-with-CV failures on policies whose phase-1 plan now has `VARDB=0` and no QuikPlCv key (e.g. `5667AT`). Issue #72 MNFOPT 44/45 rules still **PASS** (0 bad44/bad45; `010407670C` OK). Collateral is from removing the `VARDB≠0` alternate path on default plans — documented in Risk §8. **Not in Issue #74 scope** to revert or rebuild QuikPlCv.

---

## UAT

1. Reload `Output/Test_Validation/quikplan.csv` into QLAdmin Data Admin (plan catalog)  
2. Spot-check Var DB Code: default plan → **`0`**; structure plan (e.g. `130JEB`) → **`3`**  
3. Confirm `VARGP` unchanged on sample plans  

---

## Re-emit command

```bash
python plan_governance/phase_p2_product_setup_runner/product_setup_runner.py --emit --output-dir QLA_Migration/Output
```

---

## Publish

**Published:** `QLA_Migration/Output/Test_Validation/quikplan.csv` only.
