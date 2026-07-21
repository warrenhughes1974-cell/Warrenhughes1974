# Issue A — A3 Planning Report (Default PVO keys — no rates)

**Sub-item:** A3  
**Framework stage:** Planning (A3 scope)  
**Status:** **Blocked — Awaiting Eric Clarification** (TESTRD template + 15-plan disposition)  
**Generated:** 2026-07-20  
**Track:** Internal only

---

## 1. Executive finding

Robert: **every plan** must have default PVO category records and default keys **`0` / `00` / etc.**, even when **no rates** are loaded. Gold example: **TESTRD** (CSO UAT — not in our conversion quikplan today).

Issue **#77 (v57.95)** fixed default keys and members for plans **with loaded factor rates** (`rated_plans_from_grids`). It did **not** cover plans that appear on **quikplan only** with zero rate grids.

**Confirmed gap:** **15 / 141 plans** have **no** member tables and **no** rate keys — identical to Go-Live **Item 07**.

---

## 2. QLAdmin targets

| Layer | Tables | Minimum per plan (TESTRD pattern) |
|-------|--------|-----------------------------------|
| **Category members** | `QuikPlGd`, `QuikPlBd`, `QuikPlUw`, `QuikPlSt` | At least one row each (Gender / Band / UW / State) |
| **Rate keys** | `QuikPlGp`, `QuikPlDb`, `QuikPlCv`, `QuikPlTv`, `QuikPlDv` | Default stub key(s); CV/TV basis fields **may be empty** |
| **Plan header** | `quikplan` *VARY* + `PLANVALOPT` | Must align with keys (Issue #77 logic; A6 overlap) |

**Not the same as A4:** blank **`PLAN`** row in QuikPl* (global orphan) — separate check.

---

## 3. Current fleet state (Output `rates/` + quikplan v58.20)

| Metric | Count |
|--------|------:|
| quikplan plans | 141 |
| Missing **all four** member tables | **15** |
| Missing **any** member table | **15** |
| No GP keys **and** no QuikGps factors | **15** (same set) |
| TESTRD in quikplan.csv | **No** (CSO UAT-only example) |

### 15 plans with no PVO member rows

`10L171`, `10L172`, `117JPO`, `121PUA`, `165PUA`, `170PUA`, `185PUA`, `1970PA`, `1OLPUA`, `1POPUA`, `7647CH`, `94PDIS`, `976658`, `986JPO`, `9ADB15`

Inventory: `Issue_Log_Items/Issue_A/Reports/A3_pvo_default_inventory.csv`

---

## 4. Root cause (code)

Rate pipeline (**Issue #77**) only stubs keys for **`rated_plans`**:

```355:368:qla_core/rate_pipeline.py
    # Issue #77: default key stub for each GP/DB/CV/TV/DV family missing rates
    rated_plans = K.rated_plans_from_grids(res.grids)
    res.default_key_stubs = K.ensure_default_key_stubs(
        res.key_rows, rated_plans, assumptions=assumptions, effdate=config.effdate,
    )
    ...
    res.member_rows, res.member_placeholders = MB.build_member_rows(res.grids, config.effdate)
    ...
    MB.ensure_members_for_keys(res.member_rows, res.key_rows, effdate=config.effdate)
```

- `build_member_rows` derives members **only from rate grids** — zero-rate plans → **zero members**.
- `ensure_members_for_keys` runs **after** key stubs but only for keys that exist — no keys on zero-rate plans → **no members**.

**A3 fix direction:** After #77 steps, union **`quikplan` PLAN universe** with `rated_plans` and emit TESTRD-style defaults for plans still missing members/keys.

---

## 5. TESTRD gold pattern (from Robert)

Per Robert’s UAT example (screenshots / narrative):

| Dimension | Default |
|-----------|---------|
| Gender | `0` (Not Applicable) |
| Band | `00` |
| UW Class | `00` |
| Country / State | `0000` / `00` (or ALL OTHER) |
| GP/DB/CV/TV/DV keys | Present with defaults |
| CV/TV basis columns | **Empty** on default-only keys |
| Rates (QuikGps, etc.) | **None required** |

**Need Eric:** confirm TESTRD row values match what conversion should emit.

---

## 6. Relationship to Issue #77

| #77 scope | A3 extension |
|-----------|----------------|
| Plans **with** factor grids | Unchanged |
| Default key stub per GP/DB/CV/TV/DV family | Same stub shape |
| Member codes from segmentation | Add **explicit NA defaults** when no grid |
| PVO *VARY* recompute from keys | Must run for new stubs |
| **Plans without any rates** | **Not covered → A3** |

Regression risk: **medium** — extend stub logic, do not change factor values on rated plans.

---

## 7. Recommended implementation (after Eric confirms)

1. Load full **quikplan PLAN list** into rate pipeline (or post-pass hook).
2. For each plan **missing** any of PlGd/Bd/Uw/St, append TESTRD-style member rows (`0`, `00`, `0000`/`00`).
3. For each plan missing key families, call existing `make_default_key_row` for GP/DB/CV/TV/DV (NA segmentation).
4. Re-run Issue #77 PVO flag enrichment on affected quikplan rows only.
5. **Do not** invent QuikGps/QuikCvs factor values.
6. Validator: every quikplan PLAN has ≥1 row in each of 4 member tables + ≥1 stub per key family (or documented exception list from Eric).

**Estimated new rows (if all 15 get full TESTRD minimum):**

| Table | ~Rows added |
|-------|------------:|
| QuikPlGd/Bd/Uw/St | 15 each → 60 |
| QuikPlGp/Db/Cv/Tv/Dv stubs | 15 × 5 → 75 |
| QuikPlNb | 15 (with St) |

---

## 8. Open questions — Eric (required before Development)

1. Confirm **TESTRD** as canonical minimum template for this region.
2. **15-plan list** — add defaults for all, or remove unused plans from quikplan?
3. **Gender `0` vs F/M** on no-rate life plans (Item 29 overlap).
4. **Category checkboxes** on no-rate plans — which GP/DB/CV/TV/DV flags should be Y?

(Full email draft: `Issue_A_Email_Questions.md` § A3.)

---

## 9. Risk preview

| Risk | Severity |
|------|----------|
| PVO flag drift on 126 rated plans | Low if scoped to 15 plans only |
| Accidental factor invention | Low — stubs only |
| DG / #77 validator regression | Medium — re-run Issue #77 validator |
| #25 / #26 | None |

**Recommendation:** **NO-GO for Development** until Eric confirms §8.

---

## 10. Next steps

| Step | Owner |
|------|-------|
| Eric answers §8 | Eric |
| Risk Agent (optional, after Eric) | Warren |
| Development in `rate_pipeline.py` + apply script | Composer 2.5 after approval |
| Re-run rates + quikplan; checklist A3 | Warren |

---

## Appendix

- Script: `Issue_Log_Items/Issue_A/scripts/_research_issueA_a3_pvo_defaults.py`
- Go-Live Item 07: `Issue_Log_Items/Go_Live_Open_Items_Running.txt`
- Issue #77: `Issue_Log_Items/Issue_77/Issue_77_Implementation_Notes.md`
