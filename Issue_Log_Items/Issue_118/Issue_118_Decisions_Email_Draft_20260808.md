# Issue #118 — Decisions email draft (2026-08-08)

Paste-ready note to Eric summarizing locked conversion decisions.

---

Eric —

Quick wrap-up on the underwriting class remap decisions so we’re aligned before we build.

We’re matching your **Underwriting Classes by Form** spreadsheet as the source of truth, plus the L14 letter map you already confirmed (N→NT, T→ST, Q→PQ, R→PR).

What we locked on our side:

1. **Class 0 / single-class products** — keep QLAdmin code **00**, description **Standard** (not Not Applicable). We are not re-keying those rate tables to ST. Having both 00=Standard and ST=Standard is fine.

2. **Form-aware letters** — B→Blended (BL) on L10; S→Smoker on L10 and S→Standard on preferred/standard forms, per your sheet.

3. **L14** — map policies to NT/ST/PQ/PR and load all four premium classes. We will **not** invent cash-value tables for ST/PQ/PR (LifePRO only has those for N). We’ll note on the final report that cash values are missing for L14 policies in ST, PQ, and PR.

4. **Descriptions that don’t fit the 20-character field** — truncate: NT = STANDARD NON-TOBACCO, PQ = PREFERRED NON-TOBAC.

5. **Plans not on the spreadsheet** — leave as they convert today. We’re only changing what you asked for on the sheet.

6. **Dropdown** — drop NS. L14 uses NT; ISWL uses ST/PR.

7. **Blank underwriting class on Standard-only forms** — your sheet lists **SAL ML** and **SAL OL** as Standard only, so we’re treating blank LifePRO underwriting class on those as Standard (code 00, joins the existing Standard/00 rates). Exact base-benefit rows we used:

```text
POLICY_NUMBER | BENEFIT_SEQ | BENEFIT_TYPE | PLAN_CODE | STATUS_CODE | STATUS_REASON | UNDERWRITING_CLASS
901353D732    | 1           | BA           | SAL ML    | A           | CR            | (blank)
9012FG8217    | 1           | BA           | SAL ML    | T           | DC            | (blank)
9014048       | 1           | BA           | SAL ML    | T           | DC            | (blank)
901122D991    | 1           | BA           | SAL OL    | A           |               | (blank)
901222DC      | 1           | BA           | SAL OL    | A           | CR            | (blank)
```

Source file for those rows: `PPBEN_PolicyBenefit_Extract_20260630.csv`.

If anything above doesn’t match what you intended, say so and we’ll adjust before we code.

Thanks,  
Warren
