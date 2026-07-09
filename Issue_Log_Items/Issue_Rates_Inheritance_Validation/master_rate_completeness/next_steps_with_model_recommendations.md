# Next Steps With Model Recommendations

Date: 2026-07-07

Going forward, each rate-completeness recommendation should include the suggested model.

## Step 1: Implement Inherited/Shared Rate Candidates for Confirmed Tables

Scope:

- Use `inherited_shared_rate_candidates.csv`.
- Start with confirmed target tables only: `CV`, `DB`, `DV`, `NP`, `RV`, `PR`, `NF`.
- Prioritize `PR` and `NF` shared/PAAGERAT candidates because `NF -> QuikNff` is now confirmed and `PR -> QuikGps` already exists.
- Do not include `NN` or `PN`.

Recommended model:

- GPT-5.5 Medium for implementation.
- Claude 4.6 Sonnet Medium Thinking for independent review after implementation.

## Step 2: Build a Proof-First Missing Source Response for Eric

Scope:

- Use `source_gap_proof/missing_source_proof.csv`.
- Explain that `PCOVRSGT` references exist, but required rate rows are absent from `Rate_Table` and `PAAGERAT`.
- Ask for source extract rows, not additional screenshots, for:
  - `L01 10Y` `NP`
  - `L10 LP9595` `NP/RV`

Recommended model:

- GPT-5.5 Medium for drafting the client explanation.
- Claude Opus 4.8 Thinking High if you want a second-pass executive/client wording review.

## Step 3: Resolve BP

Scope:

- Product Book says `BP` = Billable Premium Segment.
- Current destination for enabled BP rows is `QuikGps`.
- The blocker is not table shape; it is authority/gating. Confirm which plans should use BP instead of PR.

Recommended model:

- Claude 4.6 Sonnet Medium Thinking for planning/risk analysis.
- GPT-5.5 Medium for the controlled loader/config update after the BP authority list is approved.

## Step 4: Resolve NC

Scope:

- Product Book says `NC` = Net Premium Credited Segment for fixed premium UL.
- Do not load until QLAdmin destination is confirmed.
- Determine whether QLAdmin expects this in an existing rate table, product field, fund/value process, or not at all.

Recommended model:

- Claude Opus 4.8 Thinking High for research/planning because this is a semantic mapping question.
- GPT-5.5 Medium only after the destination is confirmed.

## Step 5: Keep Inventory as the Regression Gate

Scope:

- Rerun the master inventory after every rate-loader change.
- The actionable gap count should decrease only when rows are loaded or explicitly documented as not loadable.

Command:

```powershell
python "Issue_Log_Items\Issue_Rates_Inheritance_Validation\master_rate_completeness\build_rate_completeness_inventory.py"
```

Recommended model:

- GPT-5.5 Medium for routine reruns and interpretation.
- Claude 4.6 Sonnet Medium Thinking for independent QA before client delivery.
