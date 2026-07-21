# CFIC_Rates — README

Citizens / CFI rate source from the Access **CFI Proposal Maker** tool.

## Layout

| Path | Purpose |
|------|---------|
| `source/` | Read-only archive (`CFIProposalMaker.zip`, `.mdb`) |
| `extracted/` | CSV exports of each user table (canonical working copy) |
| `docs/` | Decisions, walkthrough, product catalog, green-sheet extraction plan, **plan/rate PDF inventory** |
| `mapping/` | Future product / column crosswalks |
| `validation/` | Future parity checks vs Access quotes |
| `Issue_Log/` | CFIC issue framework artifacts (independent from Warren `Issue_Log_Items/`) |
| `Output/rates/` | **QLAdmin load package** — PascalCase `Quik*.csv` only (`RUN_GUIDE.md`) |
| `Reports/` | Emit manifests and run summaries |
| `Validation/` | Parity / checkpoint CSVs |
| `tracking/` | **Rate load tracker** — expected vs received vs QLAdmin loaded (`tracking/README.md`) |

## Status (2026-07-08)

1. Target platform — **DECIDED: QLAdmin** → `docs/target_platform.md`
2. All products — **Active** → `docs/product_catalog.md`
3. Business walkthrough — **checklist ready** → `docs/access_app_walkthrough.md`
4. CSV export — **complete** → `extracted/*.csv` (11 tables)
5. Green-sheet extraction — **CFIC Issue #01 Risk complete (G3)** — Conditional Go Wave 1; see `Issue_Log/CFIC_Issue_01/`

## Do not

- Merge into Warren `QLA_Migration/` until Citizens plan/rate crosswalk is defined
- Integrate green-sheet extraction into `app.py` — **one-time standalone scripts only** (`CFIC_Issue_01_Scope_Decisions.md`)
- Treat illustration columns as admin rates without business sign-off
