# Issue #21J — Memo Generation Design

**Version:** v57.37  
**Architecture:** Extends Issue #21M / #21M-FU QUIKMEMO pipeline

---

## 1. Design principle

Reuse the existing QUIKMEMO converter — **no parallel memo subsystem**. Issue #21J adds a post-merge enrichment step that prepends a standardized `[CONVERSION]` segment to each policy's MEMOTEXT.

---

## 2. Component diagram

```
PNOTE.csv ──┐
            ├──> convert_quikmemo_from_pnote_pense() ──> memo_df (4380 rows, #21M)
PENSE.csv ──┘                                              │
                                                           │
quikmstr.csv ──> policy MEMOKEY list (5083)                │
quikridr.csv ──> phase-1 MPLAN lookup                      │
                                                           v
                              append_issue21j_conversion_memos()
                                                           │
                                                           v
                                              quikmemo.csv (5083 rows)
                                                           │
                                                           v
                                              write_quikmemo_dbf() (#21M)
```

---

## 3. Grain and merge rules

| Rule | Value |
|------|-------|
| Output grain | One row per MEMOKEY (#21M-FU) |
| Segment separator | `\n---\n` |
| #21J segment position | **First** (prepended) |
| Idempotency | If MEMOTEXT already starts with `[CONVERSION]`, replace first segment only |

---

## 4. Policy population

**Authority:** `quikmstr.csv` MPOLICY list (converted fleet). Fallback: crosswalk QLA values if quikmstr unavailable (single-table quikmemo run).

**Plan lookup:** `quikridr.csv` where `MPHASE = 1`; key = `format_qladmin_mpolicy(MPOLICY)` (#25 alignment).

---

## 5. Memo template

Built by `format_conversion_modal_factor_memo(conversion_version, plan_code)`:

```
[CONVERSION]
Conversion Version: {version}
Product Plan: {MPLAN}
Plan-level modal premium factors used during conversion:
  Annual = 100
  Semi-Annual = 51
  Quarterly = 26.5
  Monthly Draft = 9.25
  Monthly Billing = 9.25
These are QLAdmin standard product modal factors.
Policy premium quotes may differ because runtime premium quote calculations are separate from product setup.
WARNING: If plan-level modal factors are modified after conversion, all affected policy premiums should be recalculated.
```

Constants defined in `ISSUE21J_MODAL_FACTORS` tuple — single source for template values.

---

## 6. Integration point

`app.py` quikmemo batch branch (after `convert_quikmemo_from_pnote_pense`):

```python
output_df, conv_stats = append_issue21j_conversion_memos(
    output_df,
    cw_map=cw_map,
    conversion_version="v57.37",
    quikridr_path=quikridr_path,
    quikmstr_path=quikmstr_path,
)
```

Requires `quikridr.csv` and `quikmstr.csv` in output directory (standard full-batch order satisfies this).

---

## 7. Statistics emitted

| Stat | Meaning |
|------|---------|
| `conversion_memos_added` | Total policies receiving #21J segment |
| `conversion_memos_merged` | Policies with existing PNOTE/PENSE content |
| `conversion_memos_new_row` | Policies with conversion-only memo (no prior notes) |
| `policies_without_plan` | MPLAN lookup miss (expected 0 in full batch) |
| `converted_policies` | quikmstr policy count |

---

## 8. Out of scope (by design)

- Reading modal factors dynamically from `quikplan.csv` (documentation uses approved standard values)
- Automatic premium recalculation
- Runtime Premium Quote engine changes
- MODE_PREMIUM conversion changes
