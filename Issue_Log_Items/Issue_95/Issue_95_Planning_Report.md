# Issue #95 — Planning Report

**Issue:** #95 — Declared Interest Rates Incorrect  
**Framework stage:** Planning Agent  
**Status:** Planning → Dependency Gate  
**Generated:** 2026-07-22  
**Agent/script:** Planning Agent (Cursor Grok 4.5) + `QLA_Migration/_research_issue95_pdinttbl.py`

---

## 1. Executive Finding

LifePRO `PDINTTBL` **current tiers already match Eric’s stated rates** (DAR01/DIV01/IBA01/L1001 = 3.50%, SAL01 = 2.00%, CENII = 4.50%). The conversion gap is on the QLAdmin side: **`QuikUint` today emits only the 8 ISWL MPLANs from IDENT `CENII`** (Issue #32). There are **no QuikUint rows** for SAL (`1SALOL` / `1SALML`) at 2.00% or for the residual “everything else” life plans at 3.50%.

Recommended direction: extend the QuikUint / PDINTTBL loader beyond ISWL-only CENII to emit declared rates by IDENT family per Eric’s rule (after Dependency Gate clears MPLAN membership and product-class questions). Do **not** treat this as an Issue #21D `MDEPINT` change unless Eric confirms that screen.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/? | Row count |
|--------------|--------------|-------------|----------:|
| PDINT | `PDINT_DeclaredInterestRates_Extract_20260630.csv` | Yes | 10 |
| PDINTTBL | `PDINTTBL_DeclaredInterestRates_Extract_20260630.csv` | Yes | 38 (37 data + header dash row) |

### Available source fields (PDINTTBL)

| Field | Populated | Notes |
|-------|-----------|-------|
| IDENT | Yes | CENII, DAR01, DIV01, IBA01, L1001, SAL01, SPWL, SPWL+ |
| TYPE_CODE | Yes | A1 / C1 / C3 by IDENT |
| DINT_RULE | Yes | 0 / 1 / 3 |
| START_DATE / END_DATE | Yes | Schedule tiers |
| DECLARED_RATE | Yes | Percent literal (e.g. `3.50000`) |

### Current-tier rates (authority check vs Eric)

| IDENT | TYPE | Current START→END | DECLARED_RATE | Matches Eric? |
|-------|------|-------------------|--------------:|:-------------:|
| DAR01 | A1 | 19930801→20991231 | **3.50000** | Yes |
| DIV01 | C3 | 20060131→20991231 | **3.50000** | Yes |
| IBA01 | C1 | 20060131→20991231 | **3.50000** | Yes |
| L1001 | C1 | 20060131→20991231 | **3.50000** | Yes |
| SAL01 | C1 | 19000101→20991231 | **2.00000** | Yes |
| CENII | A1 | 20020101→20991231 | **4.50000** | Yes |
| SPWL / SPWL+ | A1 | …→20991231 | **4.50000** | **Not mentioned by Eric** |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Source |
|-------|-------|------|--------|
| **QuikUint** | MPLAN | C(6) | Help §7.223 |
| QuikUint | MEFFDATE | D(8) | Help §7.223 |
| QuikUint | MGTDRATE | N(8.4) | Guaranteed = mirror current (#32 SME) |
| QuikUint | MCURRATE | N(8.4) | Current declared rate |

**Repo references**

| Location | Role |
|----------|------|
| `qla_core/quikuint_loader.py` | PDINTTBL → QuikUint (CENII/A1 ISWL only today) |
| `qla_core/rate_pipeline.py` | `quikuint_enabled` / emit wiring |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `iswl_phase5` + extract paths |
| `Output/rates/QuikUint.csv` | Current emit: **32 rows / 8 ISWL plans** |
| Issue #32 blueprint / SME answers | ISWL CENII mapping closed |

**Explicitly not primary target (unless Eric redirects):**

| Table/field | Why separate |
|-------------|--------------|
| `quikdvdp.MDEPINT` | #21D dividend accum (ISWL 4.50 / non-ISWL 4.00) |
| `QuikAint` | Annuity (#51); A96DAR is Deposit Annuity Rider |
| `quikplan.DEPINT` | All 141 plans currently `0.00` |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PDINTTBL | DECLARED_RATE (current tier by IDENT) | QuikUint.MCURRATE | Percent N(8.4); IDENT→MPLAN map | **Yes** (expand) |
| PDINTTBL | DECLARED_RATE | QuikUint.MGTDRATE | Mirror MCURRATE (#32 rule) | **Yes** (expand) |
| PDINTTBL | START_DATE | QuikUint.MEFFDATE | Current-only **or** full history (OBQ) | **Yes** |
| Crosswalk / allowlist | PLAN | QuikUint.MPLAN | Family buckets below | **Yes** |

### Proposed IDENT → MPLAN buckets (Planning hypothesis — needs gate)

| Bucket | PDINT IDENT | Rate | Candidate QLA plans |
|--------|-------------|-----:|---------------------|
| ISWL | CENII | 4.50% current (+ history already) | `1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS` (**already emitted**) |
| SAL | SAL01 | 2.00% | `1SALOL`, `1SALML` (Eric); optionally `1SALMI` |
| Residual life | DAR01 / DIV01 / IBA01 / L1001 | 3.50% | “Everything but SAL and ISWL” — **membership TBD** (L10 bases? all non-ISWL/non-SAL base plans? exclude riders/annuities?) |
| SPWL | SPWL / SPWL+ | 4.50% in extract | `1668SP`? — **Eric silent** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| MPOLICY padding | `format_qladmin_mpolicy` (#25) | **No** |
| quikridr.MPREM | ANN_PPU + #88 fallback (#26/#88) | **No** |
| quikdvdp.MDEPINT | #21D allowlist | **No** (unless Eric confirms) |
| QuikAint A60MIR/A96DAR | #51 stubs | **No** |
| ISWL CENII historical schedule | #32 union_merge | **Preserve** unless validated equal |

---

## 5. Open Client Questions

1. **Target screen/table:** Confirm Eric is reviewing **QuikUint** (UL Declared Interest), not Dividend Accum Int (`MDEPINT`) or Annuity Interest (`QuikAint`).
2. **Product 668:** Catalog has ISWL **`1669SR`** (669) and SPWL **`1668SP`** (668). Which did Eric mean for the 4.50% ISWL note?
3. **3.50% MPLAN list:** Exact plans that must receive DAR01/DIV01/IBA01/L1001 rates — all non-SAL/non-ISWL **base** life plans in `quikplan`, or a named list (e.g. L10 bases only)?
4. **Exclude:** Confirm riders (`9*`), annuities (`A*`), and `1668SP` are in or out of the 3.50% residual bucket.
5. **`1SALMI`:** Include with SAL01 at 2.00%, or only `1SALOL` / `1SALML`?
6. **History:** For non-ISWL IDENTs, emit **current tier only** or **full PDINTTBL history** (ISWL already emits history)?
7. **Example policies / screenshot:** At least one SAL and one residual-plan policy showing the wrong declared rate.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | N/A (plan-level QuikUint) |
| Rates | N(8.4) percent literal (`3.5000`, `2.0000`, `4.5000`) — match #32 |
| MGTDRATE | Mirror MCURRATE |
| Blanks | Do not invent rates for plans outside approved IDENT map |
| Dates | `YYYYMMDD` MEFFDATE from PDINTTBL START_DATE |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

Plan-level table — no MPOLICY. Preserve #25/#26 on any unrelated policy tables (do not touch).

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| PDINTTBL data rows | 37 | Source extract |
| Current QuikUint rows | 32 | 8 ISWL × 4 historical tiers |
| ISWL plans already OK at current 4.50% | 8 | Output rates |
| SAL plans needing 2.00% | 2–3 | `1SALOL`, `1SALML` (+ optional `1SALMI`) |
| Residual 3.50% plans | **TBD** | Depends on OBQ-3/4 (could be tens of `quikplan` rows) |

---

## 10. Sample Trace (plan-level)

| QLA plan | IDENT (proposed) | Before (QuikUint current) | After (proposed) | Status |
|----------|------------------|---------------------------|------------------|--------|
| `1659C2` | CENII | MEFF 20020101 / 4.5000 | Unchanged 4.5000 | Likely OK |
| `1669SR` | CENII | 4.5000 | Unchanged 4.5000 | Likely OK (if Eric’s “668” meant 669) |
| `1SALOL` | SAL01 | **Missing** | 2.0000 | Gap |
| `1SALML` | SAL01 | **Missing** | 2.0000 | Gap |
| `1L1095` (example residual) | L1001 / residual | **Missing** | 3.5000 | Gap (if in scope) |
| `1668SP` | SPWL? | **Missing** | TBD | OBQ |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Emitting QuikUint for traditional non-UL plans may be wrong product class | High | Confirm target with Eric before Dev |
| Broad “everything else = 3.50%” over-emits riders/annuities | High | Named allowlist or base-plan filter |
| Conflating with #21D MDEPINT 4.00 | Medium | Keep out of scope unless confirmed |
| Changing ISWL historical tiers while fixing residual | Medium | Freeze CENII union_merge; regression vs #32 baseline |
| SPWL silent in Eric note but present in extract | Medium | OBQ before emit |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | **Yes** |
| Field definitions confirmed | **Partial** — QuikUint known; screen confirmation pending |
| Client scope clear | **Partial** — rates clear; MPLAN membership / 668 unclear |
| Example policies available | **No** |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #95.

Read AI_Agents/Risk_Agent.md and Templates/Risk_Report_Template.md.
Model: Cursor Grok 4.5. Do not code.

Context: PDINTTBL current rates match Eric (3.50 / 2.00 / 4.50). QuikUint is ISWL-only today.
Quantify before/after QuikUint row counts by IDENT bucket once OBQs are answered (or under documented assumptions).
Preserve Issue #32 ISWL CENII schedule; do not touch #21D MDEPINT, #25/#26/#88, QuikAint.
Go / No-Go for expanding quikuint_loader beyond ISWL.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. After Risk GO and OBQs closed: extend `qla_core/quikuint_loader.py` (or thin companion) with IDENT→MPLAN maps for SAL01 + residual 3.50% bucket; keep CENII ISWL path intact.
2. Wire config allowlists in `rate_loader_config.json` (not hardcoded magic in unrelated modules).
3. Version bump `APP_VERSION` in root + `QLA_Migration/app.py` if batch path touched.
4. Validator: `QLA_Migration/_validate_issue95_quikuint_pdinttbl.py` — assert current rates by plan family vs PDINTTBL; ISWL regression vs #32 expected schedule.
5. Publish `Output/rates/QuikUint.csv` (+ `Test_Validation/rates/` on PASS).

---

## Appendix

- Diagnostic script: `QLA_Migration/_research_issue95_pdinttbl.py`
- Related: Issue #31, #32, #21D, #51
- References: QLAdmin Help §7.223; `docs/research/ISWL_Implementation/ISWL_QUIKUINT_Implementation_Blueprint.md`
