# Issue #40 — Intake Validation Matrix (Acceptance Criteria)

**Issue:** Inherited Cash Value Rate Load  
**Purpose:** Define **exhaustive** proof required before Issue #40 can close.  
**Principle:** Every emitted inherited CV cell must trace to an authoritative LifePRO source row. No spot-check-only closure.

---

## 1. Validation philosophy

Prior CV issues (#37, #41) showed that **correct-looking values in the wrong duration column** or **missing plans entirely** can pass casual review. Issue #40 adds a third risk: **emitting under the wrong plan code** or **copying the wrong rate-owner segment**.

Because there is **no complete data dictionary** for LifePRO → QLAdmin CV inheritance, closure requires:

1. **Structural proof** — issuing plan has QuikCvs keys; rate-owner plan unchanged.
2. **Value proof** — every emitted cell matches source after Issue #37/#41 grid remap.
3. **Fleet proof** — every actuarial-approved inherited plan in scope passes the same tests.
4. **Regression proof** — direct-loaded plans and non-CV tables unchanged.

---

## 2. Per-plan mandatory checks (each approved inherited plan)

For each plan approved for inherited CV emit:

| # | Check | Pass criteria |
|---|-------|---------------|
| V40-01 | Issuing plan row count | `QuikCvs` keys for issuing plan **> 0** (was 0 at intake) |
| V40-02 | Rate-owner plan unchanged | Rate-owner plan key count **unchanged** vs pre-fix baseline |
| V40-03 | Source row coverage | 100% of emitted cells trace to Rate_Table CV rows on approved rate-owner coverage(s) |
| V40-04 | Plan code on emit | Every emitted row has `PLAN = issuing plan`, not rate-owner plan |
| V40-05 | First non-zero CV | Matches source at correct QL duration index (Issue #41 rules) |
| V40-06 | Mid-grid CV | At least one mid-duration point matches source |
| V40-07 | Age-100 endpoint | Terminal non-zero CV matches source at attained age 100 |
| V40-08 | Emitted CSV = grid | `QuikCvs.csv` cell values match in-memory grid for sample keys |
| V40-09 | QuikPlCv key | Rate-key row exists for issuing plan with CSO assumptions |
| V40-10 | No duplicate cells | Pipeline reports zero BLOCKER collisions on inherited emit |

---

## 3. GL85 anchor proof pack (`17085M` — required)

Minimum evidence set before client UAT:

| Proof | Source | QLA target | Expected |
|-------|--------|------------|----------|
| P-GL85-01 | `Rate_Table` `670 GL85-8` CV rows | `QuikCvs` `PLAN=17085M` | Key count ≈ inherited grid from rate owner (post-#37/#41 placement) |
| P-GL85-02 | Same slice as `170858` for sex/age/band/uw | `17085M` vs `170858` | **Identical values** at same QL duration index; **different PLAN** |
| P-GL85-03 | PCOVRSGT slots 2,3,12,13,22,29,32,33 | Loader manifest | Documented rate-owner = `670 GL85-8` |
| P-GL85-04 | Policy `010367438C` on plan `17085M` | QLAdmin CV calc | Proceeds without missing-rate failure (client UAT) |

**Pay-age 85 vs 88:** If actuarial confirms **same CV table**, P-GL85-02 is sufficient. If actuarial requires **different factors**, intake must be reopened with alternate table spec — do not assume.

---

## 4. Fleet inherited-CV proof pack (all approved plans)

For each row in `Issue_40_Fleet_CV_Inheritance_Audit.csv` approved for emit:

| Plan | Minimum comparisons | Notes |
|------|--------------------:|-------|
| `17085M` | **Full grid spot + 3 anchor points** | Client anchor |
| High-count plans (`1L10SO`, `1L10SR`, …) | **3 points per plan** + key count reconciliation | Multi rate-owner — actuarial selection rule required |
| Medium/Low PUA plans | **3 points per plan** | Confirm rider CV target behavior |

Automated validator (to be built at Development):  
`QLA_Migration/_validate_issue40_inherited_cv_source_parity.py` — **not written at intake**.

Manual evidence at G5: CSV per plan modeled on Issue #41 `issue41_quikcvs_10_plan_validation.csv`.

---

## 5. Regression guards (G6 — must PASS)

| Guard | Requirement |
|-------|-------------|
| Issue #37 / #41 | All prior CV placement proof cases remain PASS |
| Issue #31 baseline | Rebaselined intentionally; document key-count deltas |
| `170858` / `170588` | Existing QuikCvs emits unchanged |
| QuikNps / QuikGps / QuikDbs / QuikTvs / QuikDvs | Row counts unchanged |
| Issue #25 MPOLICY padding | PASS |
| Issue #26 MPREM | PASS |
| `quikplan.PLAN` for `670 GL85-M` | Remains **`17085M`** |
| Issue #21J PAC GL85 modal | Unchanged |

---

## 6. Closure definition (G7)

Issue #40 may close only when:

1. Actuarial written approval is on file for scope (GL85 minimum; fleet if approved).
2. **100%** of mandatory checks in §2 pass for every in-scope plan.
3. GL85 anchor proof pack (§3) is PASS.
4. Client UAT confirms CV calculation on **≥ 2** policies from `Issue_40_Population.csv`.
5. Resolution summary states inherited emit rule and lists validated plans.

**Not sufficient for closure:**

- “Rates look close on one screenshot.”
- Emitting only GL85 while High-priority fleet plans remain at zero QuikCvs rows (unless scope explicitly narrowed by client).
- Skipping CSV-vs-grid parity because pipeline has unrelated blockers (regenerate `QuikCvs.csv` from validated grid if needed).

---

## 7. Intake recommendation

Proceed to **Dependency Gate** with actuarial questions unchanged. Do **not** start Development until:

- [ ] Actuarial approves GL85 inherited table equivalence (85 vs 88)
- [ ] Actuarial approves fleet scope or narrowed plan list
- [ ] This validation matrix accepted by Conversion + Client as G5 acceptance standard
