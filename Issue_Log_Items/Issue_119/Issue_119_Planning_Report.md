# Issue #119 — Planning Report

**Issue:** #119 — PUA coverage MPAR must be 0 (non-participating)  
**Date:** 2026-07-27  
**Framework stage:** Planning complete (G1)  
**Code changes:** none (prohibited)

---

## 1. Executive finding

Robert’s QLAdmin rule: **a PUA coverage is never participating** — when QL adds a PA rider it sets coverage PAR/`MPAR` to **0**, regardless of whether the base is participating.

Our emit currently leaves `MPAR` at the value set under Issue #105 from the **pre-rewrite** catalog PUA plan (almost always `PAR=1`), then inheritance only changes `MPLAN`/dates/status. Validators (#105 v1.1 / #111) currently **require** PUA `MPAR` to equal the base — the opposite of Robert’s rule.

**Fix:** after PUA rider identity is known, force `quikridr.MPAR = "0"` for every PUA coverage row; update validators and briefing §10 to match §7.2.

---

## 2. Confirmed LifePRO source(s)

| Source | Role |
|--------|------|
| `PPBEN` / benefit row `PLAN_CODE` | Detects PUA product via `PAID_UP_ADDITION_*` sets (`_is_paid_up_addition_product`) |
| Phase-1 base row on same `MPOLICY` | Supplies inherited dates/age/status/MPLAN prefix — **not** participating flag under this issue |
| `quikplan.PAR` | Remains authority for **non-PUA** `#105` rows; catalog PUA plans’ PAR is irrelevant once coverage is forced non-par |

No new extract required.

---

## 3. Confirmed QLAdmin target

| Table | Field | Type | Semantics |
|-------|-------|------|-----------|
| `quikridr` | `MPAR` | CHAR(1) | `1` = participating, `0` = non-participating |

Robert: PA coverage → `MPAR = 0`. Base coverage may remain `MPAR = 1`.

Plan file: synthetic `*PA` codes remain **absent** from `quikplan` (unchanged #60 / #111 design).

---

## 4. Proposed source-to-target mapping

| Step | Current | Proposed |
|------|---------|----------|
| Row build `#105` | `MPAR = quikplan.PAR[MPLAN]` (catalog PUA often 1) | Keep for non-PUA |
| `_apply_pua_rider_inheritance` | Does not touch `MPAR` | **Set `row_data["MPAR"] = "0"`** for every PUA rider |
| Pending-row path | Same inheritance | Same force to `"0"` |
| Validator `#105` | PUA expected = base plan PAR | PUA expected = **`0`** always |
| Accountability `#105` spot-check | Same base-resolution | Same: PUA must be `0` |
| Briefing §10 | “matches base” | “PUA participating flag is 0” |

Detection: reuse `_is_paid_up_addition_product` / synthetic `len==6 and endswith("PA")` already used by validators — Development should prefer the same product detector used at emit so catalog `…PUA` rows that are true PUA products are covered even if naming differs.

---

## 5. Open client questions

| ID | Question | Default if unanswered |
|----|----------|------------------------|
| OQ-1 | Confirm force applies to **all** LifePRO PUA products in `PAID_UP_ADDITION_*`, not only synthetic `*PA` | **Yes — all PUA coverages** (Robert’s wording) |
| OQ-2 | Any exception where a PUA coverage should remain participating? | **None** unless Robert names one |

Neither blocks Development if defaults accepted.

---

## 6. Formatting / fallback rules

- Emit only `"0"` or `"1"` for `MPAR` (existing `#105` invariant).
- Unknown / non-PUA: unchanged `#105` product map.
- If base cache missing and PUA still emits: still force `MPAR=0` (participation does not depend on base).

---

## 7. Policy key handling

No change to MPOLICY padding (#2), MPREM (#26), or MPLAN synthesis (`base[:4]+"PA"`).

---

## 8. Estimated record counts (current Output)

| Population | Count |
|------------|------:|
| PUA rider rows | **494** |
| Expected `MPAR` 1 → 0 | **493** |
| Already `MPAR = 0` | **1** |
| Non-PUA `quikridr` rows | unchanged |

---

## 9. Sample trace (before → after)

| MPOLICY | MPHASE | MPLAN | MPAR before | MPAR after |
|---------|--------|-------|-------------|------------|
| 9010310404C | 2 | 1960PA | 1 | **0** |
| 9010150910C | 3 | 221EPA | 1 | **0** |
| 9010360290C | 2 | 1708PA | 1 | **0** |
| 9010391228C | 2 | 1970PA | 0 | **0** |
| 9010143726C | 1 | 221END (base, control) | 1 | **1** (untouched) |

---

## 10. Risks and unknowns

| Risk | Note |
|------|------|
| `#111` disposition “inheritance correct” | Superseded **only** for participation; missing PA plans still by design |
| `#105` validator rewrite | Must not weaken non-PUA product-PAR checks |
| Catalog plans `170PUA` etc. with `PAR=1` in `quikplan` | Plan-level PAR may stay; coverage `MPAR` is the field Robert called out |
| UAT / dividends | Confirm non-par PUA does not break dividend-purchase history (#114 path) — expected independent |

---

## 11. Recommended Risk Agent prompt

> Risk-review Issue #119: quantify MPAR 1→0 on PUA rows only; confirm zero non-PUA flips; list validator/briefing surfaces; GO/NO-GO for forcing MPAR=0 in `_apply_pua_rider_inheritance`.

---

## 12. Recommended Development task (do not implement)

1. In `_apply_pua_rider_inheritance` (and any equivalent path), set `MPAR = "0"` after PUA identity confirmed.  
2. Bump `APP_VERSION` in root + `QLA_Migration/app.py`.  
3. Update `validate_issue105_mpar.py` + accountability `#105` spot-check: PUA → expect `0`.  
4. Fix briefing builder §10 bullet; regenerate docx if shipping to Omaha.  
5. Rebatch `quikridr` / full Output; run validators; publish `Test_Validation/quikridr.csv` on PASS.
