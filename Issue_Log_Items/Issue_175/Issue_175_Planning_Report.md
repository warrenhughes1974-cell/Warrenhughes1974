# Issue 175 — Planning Report

**Issue:** 175 — Res Cat Unique Field
**Framework stage:** Planning Agent
**Status:** Planning
**Generated:** 2026-09-28
**Agent:** Cursor Grok

---

## 1. Executive Finding

The policy reserve category is the letter `L` because Issue 141 copies LifePRO `PCOVR.PRODUCT_TYPE` for the base coverage. L15, L16, and L17 BASE are stored as `L`. Eric wants 13, 13, and 12, which is already the product code on those three plan rows.

Change `quikspec.RESRVCAT` only, for those three LifePRO coverages. Leave the rest of Issue 141 in place, including the rule that the plan’s `ISWLFE` tag is not copied onto the policy.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Notes |
|---|---|---|---|
| PCOVR | `PCOVR_Coverage_Extract_20260630.csv` and `_20260831.csv` | Yes | `PRODUCT_TYPE` is `L` for L15, L16, and L17 BASE on both dates |
| PPBEN | `PPBEN_PolicyBenefit_Extract_20260630.csv` | Yes | Seq 1 `PLAN_CODE` is L15, L16, or L17 BASE for the 33 policies |

### Available source fields

| Field | Column | Notes |
|---|---|---|
| Coverage | PCOVR.COVERAGE_ID | L15, L16, L17 BASE |
| Reserve / product type | PCOVR.PRODUCT_TYPE | `L` on those three. L17 1 and L17 2+ are already `12`. L15 ADB is already `13`. |
| Policy | PPBEN.POLICY_NUMBER | Seq 1 only |
| Base coverage | PPBEN.PLAN_CODE | Trailing-space header in the extract. Loader already strips it. |

Discount coverages `DISCHO20 B`, `DISCHO25`, and `DISCHO80` are also product type `L`. None of them is a seq-1 coverage in this package. `L16POLFEE` is the same. They stay `L` if they ever become a base.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source |
|---|---|---|---|---|
| quikspec | RESRVCAT | char | 2 | Issue 141. Policy User Defined. |

Current `quikspec.csv` columns, in order: `MPOLICY`, `VANISH`, `VANISHDT`, `RESSTATE`, `RESRVCAT`, `SOR_POL`. 5,083 rows. Every policy key is 11 characters.

| Location | Role |
|---|---|
| `qla_core/quikspec_resrvcat.py` | Fills `RESRVCAT` from seq-1 coverage product type |
| `QLA_Migration/_validate_issue141_resrvcat.py` | Fails if any row differs from that product type |
| `app.py` / `QLA_Migration/app.py` | Calls the filler. Version is v59.26 |

`quikplan.PRODUCT` is already 13 on `1L15GD` and `1L16GD`, and 12 on `1L17SP`. That field is not the client screen that is wrong.

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|---|---|---|---|---|
| PCOVR | PRODUCT_TYPE | quikspec.RESRVCAT | Copy as-is | No, except the three rows below |
| PCOVR L15 | PRODUCT_TYPE `L` | quikspec.RESRVCAT | Emit `13` | Yes |
| PCOVR L16 | PRODUCT_TYPE `L` | quikspec.RESRVCAT | Emit `13` | Yes |
| PCOVR L17 BASE | PRODUCT_TYPE `L` | quikspec.RESRVCAT | Emit `12` | Yes |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|---|---|---|
| quikmstr modal premium | PPOLC | No |
| quikridr.MPREM | Issue 26 | No |
| MPOLICY width 11 | Issue 25 / Issue 2 | No |
| quikplan.PRODUCT / HLOB / MKTG | Issue 99 on ISWL; already 13/12 here | No |
| quikspec VANISH, VANISHDT, RESSTATE, SOR_POL | Issues 145, 132, 156 | No |
| RESRVCAT on every other coverage | Issue 141 product type | No |

---

## 5. Open Client Questions

None that block the gate. Eric named the three products and the three codes. Warren confirmed the spec field.

Assumption locked for planning: discount coverages and `L16POLFEE` keep product type `L`. They are not base coverages in this package.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|---|---|
| Policy key | Leave the existing 11-character key. Do not rebuild the row. |
| Category | `13` and `12`, two characters, no decimal. |
| Letter L | Remains valid for coverages that are not L15, L16, or L17 BASE. |
| Blank | Do not blank a filled category. |

---

## 7. Memo / Text / Special Handling

Not a memo field.

---

## 8. Policy Number Key Handling

The 33 policies already use source number plus `C`, width 11. `SOR_POL` is the source number without `C`. Neither key changes.

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|---|---:|---|
| quikspec rows | 5,083 | Current Output |
| Rows whose reserve category changes | 33 | 11 + 2 + 20 |
| Rows unchanged | 5,050 | |
| Category `L` after the change | 0 | These 33 are the only `L` rows |
| Category 13 added | 13 | 11 L15 + 2 L16. 832 already exist. |
| Category 12 added | 20 | L17 BASE. 521 already exist. |

---

## 10. Sample Trace

| Policy | LifePRO coverage | Before | After | Other spec fields |
|---|---|---|---|---|
| 9011210337C | L15 | L | 13 | Vanish F, state KY, source policy 9011210337 |
| 9011216680C | L16 | L | 13 | Vanish F, state IN, source policy 9011216680 |
| 9011217014C | L17 BASE | L | 12 | Vanish F, state LA, source policy 9011217014 |

Issue 141 controls that must stay: `9010143726C` and `9010148272C` = 03, `9010713704C` = 05.

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|---|---|---|
| Closed Issue 141 requires product type as-is, including `L` | High | Exception only for L15, L16, and L17 BASE. Update the 141 check in the same change. Warren must approve before code. |
| Copying `quikplan.PRODUCT` in general would put `ISWLFE` on 2,268 policies | High | Do not do that. Key the exception on the three coverage ids. |
| A later batch rewrites `quikspec` from the old filler | Medium | Put the exception in `apply_quikspec_resrvcat`, not only in the current file. |

---

## 12. Dependency Gate Preview

| Check | Met? |
|---|---|
| Source file present | Yes |
| Field definitions confirmed | Yes. Char 2. `13` and `12` fit. |
| Client scope clear | Yes |
| Example policies available | Yes, from the current package |

---

## 13. Recommended Risk Agent Prompt

Risk is in this same session. Simulate the 33-row change. Confirm no other `RESRVCAT` value moves. Treat the Issue 141 exception as a condition on Go.

---

## 14. Recommended Development Task (Do Not Implement)

1. In `qla_core/quikspec_resrvcat.py`, after the product-type lookup, map coverage `L15` and `L16` to `13` and `L17 BASE` to `12`.
2. Correct the 33 `RESRVCAT` cells in current `quikspec.csv`. Do not rewrite other columns or other tables.
3. Update `QLA_Migration/_validate_issue141_resrvcat.py` so those three coverages expect 13 / 13 / 12, and every other row still matches product type. Add a fail-closed Issue 175 check and register it at closure.
4. Bump `APP_VERSION` in both `app.py` files only if the batch path changes. v59.26 is current, so the next bump is v59.27.
5. Publish `quikspec.csv` to `Output/Test_Validation/` after validation.

Do not start this until Warren approves development, including the Closed Issue 141 exception.

---

## Appendix

- Population: `Issue_Log_Items/Issue_175/evidence/issue175_resrvcat_population.csv`
- Discovery: `Issue_175_Discovery_Notes.md`
- Related: Issue 141, Issue 99
