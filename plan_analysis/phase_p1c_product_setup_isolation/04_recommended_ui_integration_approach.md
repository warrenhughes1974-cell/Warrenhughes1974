# Recommended UI Integration Approach (Phase P1C)

## Principle

app.py v55.7 remains an **orchestration wrapper / launcher / governance controller**.

The Product Setup Conversion UI is a **launcher panel**, not a conversion engine.

---

## Proposed UI: "Product Setup Conversion" Tab

Add a second tab (or labeled frame) alongside existing batch controls. Keep policy batch UI unchanged.

### Panel Layout

```
┌─ Product Setup Conversion ────────────────────────────────────────┐
│                                                                  │
│  Source:     [plan_analysis/quikplan_source.csv        ] [Browse]│
│  Crosswalk:  [Policy Form Crosswalk 5.22.26.xlsx     ] [Browse]│
│  Rulebook:   [Sync_Rulebook_quikplan.csv              ] [Browse]│
│  PCOMP:      [plan_analysis/PCOMP.csv                 ] [Browse]│
│  Output:     [QLA_Migration/Output                    ] [Browse]│
│                                                                  │
│  [ ] Stage only (do not emit to output/)                         │
│  [ ] Generate quikplan.dbf (UAT — production_dbf_flag=N)         │
│  [ ] Block emit on diagnostic ERROR                              │
│                                                                  │
│  [ Run Product Setup ]  [ Rollback Last Emit ]                   │
│                                                                  │
│  Status: READY | Last run: 2026-05-23 14:30 | Rows: 133/133     │
│  Diagnostics: 94 WARN | 1 ERROR | 7 orphan MPLAN               │
│                                                                  │
│  ── Console (shared or tab-scoped) ──                           │
│  PRODUCT_SETUP_STATUS: SUCCESS                                   │
│  ...                                                             │
└──────────────────────────────────────────────────────────────────┘
```

### UI Responsibilities (app.py only)

| Responsibility | In app.py? |
|---|---|
| Path pickers with defaults | Yes |
| Launch subprocess | Yes |
| Display stdout / status | Yes |
| Parse structured status lines | Yes |
| Load diagnostics summary for panel | Yes |
| Rollback button (restore snapshot) | Yes |
| Field mapping / rulebook logic | **No** |
| Crosswalk join logic | **No** |
| CSV/DBF generation | **No** |

---

## Integration with Existing Batch UI

### Batch Mode Behavior (when isolated)

Add checkbox (default OFF until validated):

```
[ ] Product setup isolated (skip quikplan in batch — use output/quikplan.csv)
```

When checked:

- Sets `QLA_PRODUCT_SETUP_ISOLATED=1` for batch thread
- Removes `quikplan` from batch table list
- Pre-flight check: `output/quikplan.csv` must exist
- Logs catalog row count + last manifest timestamp

When unchecked:

- Current v55.7 behavior (quikplan processed in batch loop)

### Single-Table Mode

Existing dropdown remains for ad-hoc quikplan runs during transition. Once isolated runner validated:

- Dropdown quikplan option redirects to Product Setup tab launcher
- Or: dropdown quikplan invokes same subprocess internally

---

## Status Banner (Mirror UAT Claims Pattern)

Extend existing UAT status banner area with product setup line:

```
Product Setup: EMITTED 133 rows | DBF: NOT GENERATED | Last: 2026-05-23
```

Load from `plan_governance/manifests/product_setup_run_manifest.csv` most recent row.

---

## Configuration Persistence

Store product setup paths in existing `path_vars` pattern or separate `product_path_vars`:

```python
self.product_path_vars = {
    "ProductSrc":  [tk.StringVar(value="plan_analysis/quikplan_source.csv"), ...],
    "ProductXwalk": [tk.StringVar(value="docs/plan_conversion_reference/..."), ...],
    "ProductRule": [tk.StringVar(value="QLA_Migration/Configs/Sync_Rulebook_quikplan.csv"), ...],
    ...
}
```

Do not merge into claims path configuration.

---

## Version Display

Product setup panel shows:

- `app.py v55.7` (unchanged)
- `Product Runner: P2.0` (subprocess version from manifest)
- `Rulebook: Sync_Rulebook_quikplan.csv`
- `Crosswalk: Policy Form Crosswalk 5.22.26.xlsx`

---

## Minimal app.py Diff Estimate (P2)

| Change | Lines (est.) |
|---|---|
| Product tab UI frame | ~60 |
| Subprocess launcher method | ~35 |
| Stdout parser | ~25 |
| Batch skip quikplan flag | ~15 |
| Status banner extension | ~20 |
| **Total** | **~155 lines** |

No changes to claims orchestration (Phase 18–22).
No changes to rulebook processing loop (extracted to qla_core instead).

---

## User Workflow (Business)

1. Business updates Policy Form Crosswalk (versioned xlsx)
2. Analyst runs **Product Setup Conversion** (stage only)
3. Review diagnostics CSV — resolve WARN/ERROR with business
4. Re-run until clean
5. Emit to `output/quikplan.csv`
6. Optionally generate `quikplan.dbf` for QLAdmin UAT load
7. Run policy batch with **Product setup isolated** checked
8. Policy conversion references stable product catalog

Product maintenance does not require full policy reconversion.
