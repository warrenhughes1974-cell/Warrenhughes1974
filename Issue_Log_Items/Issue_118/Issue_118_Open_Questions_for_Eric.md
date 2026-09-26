# Issue #118 — Open Questions for Eric

**Date:** 2026-08-09  
**Purpose:** Final client decisions after the UW remap is proven on a full conversion batch.  
**Companion report:** `evidence/Issue_118_Plan_Underwriting_Classes.xlsx` (every plan × underwriting class from Output)

---

## Already decided (no action needed)

These are locked from our earlier clarifications and are already in the conversion:

| Topic | Decision |
|-------|----------|
| Spreadsheet is source of truth for form-aware S / B | B → Blended (`BL`); S → Smoker on L10, Standard on Preferred/Standard forms |
| L14 four classes | N→NT, T→ST, Q→PQ, R→PR |
| Class `0` | Keep code `00`, description **Standard** (do not re-key to ST) |
| QuikUwpo | Drop `NS`; use BL / NT / PQ labels (NT/PQ truncated to 20 chars) |
| L14 cash values | Do **not** invent CV/reserve grids for ST / PQ / PR |
| Blank UW on Standard-only forms (SAL ML, SAL OL, …) | Treat as Standard → `00` |
| Unlisted plans | Keep prior mapping except spreadsheet / Eric items |

---

## Open questions (need your call)

### Q1 — `5L01MA` (L01 10Y MA): Preferred on the sheet, but not in LifePRO rates

Your spreadsheet lists Preferred and Standard for this form. LifePRO only supplies one underwriting class of rates for the plan, and the one in-force policy converts as **Standard (`ST`)**. Nothing converts to Preferred because there is no Preferred rate grid in the source.

**Ask:** Is Preferred listed on the sheet by mistake for this form, or should Preferred stay on the plan dropdown with no rates behind it?

---

### Q2 — Extra rate classes with no in-force policies

These plans match your sheet for the classes policies actually use, but LifePRO still has rate tables for additional classes that no converted policy uses today:

| QL Plan | Form | Classes in force today | Extra classes with rates, zero policies |
|---------|------|-----------------------|-----------------------------------------|
| `1668SP` | 668 SPWL | ST (80 policies) | Preferred (PR) |
| `1679CS` | 679 CEN SD | ST (2 policies) | Non-Tobacco (NT), Preferred (PR), Preferred Non-Tobacco (PQ) |
| `1L10SO` | L10 SR OLD | BL (441 policies) | Preferred (PR), Smoker (SM) |
| `1L10SR` | L10 LP95SR | BL (159 policies) | Preferred (PR), Smoker (SM) |

*Table refreshed from the 2026-08-09 full batch; `1679CS` now carries the four L14-family classes after the Issue 118 remap.*

**Ask:** Keep those extra rate grids and dropdown entries (product historically supported them), or trim the plan dropdown to match the sheet only and leave the unused rate rows alone / drop them?

Our current rule (your direction): the plan dropdown shows only classes that are actually present (rates or policies). So for the pairs above that have rates but no policies, Preferred/Smoker still appear in the dropdown because LifePRO sent rates.

---

### Q3 — L14 missing cash values (confirmation for the report)

Already approved: we map L14 policies to NT / ST / PQ / PR and emit premiums for all four. Cash value and reserve tables exist in LifePRO for Non-Tobacco (`NT`) only.

**Ask for the final report wording:** Confirm you are comfortable with this note on the plan report:

> On L14, LifePRO provides cash value and reserve tables only for Non-Tobacco. Policies in Standard, Preferred, and Preferred Non-Tobacco have their own premium rates but no separate cash value table in the source.

No code change — confirmation only.

---

## Not asking you (internal)

| Item | Why |
|------|-----|
| Four L10 riders that were briefly missing from our L10 list (`9JPO10`, `9GPO10`, `910SWP`, `9CDTWP`) | Fixed in v58.84; smokers stay Smoker |
| Empty dropdown cleanup | Done — no orphan SM/ST entries with neither rates nor policies |
| Full-batch re-proof of Output | Done 2026-08-09 — UAT smoke 11/11 PASS on full Output |

---

## What we are sending with this note

1. `Issue_118_Plan_Underwriting_Classes.xlsx` — every converted plan and every underwriting class on that plan (policy counts, premium/CV rate flags, sheet comparison, exceptions).  
2. This open-questions list.  
3. After the full batch finishes: confirmation that the UAT smoke policies still land on the expected classes in Output.
