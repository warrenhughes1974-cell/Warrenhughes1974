# CFIC Rate Load Tracker

Track **which Citizens rates we expect**, **when source files arrive**, and **when each rate is loaded into QLAdmin**.

## Files

| File | Purpose |
|------|---------|
| `CFIC_Rate_Load_Tracker.csv` | **Main tracker** — one row per plan × rate category (1,841 rows) |
| `CFIC_Rate_Load_Tracker_Wave1.csv` | Filtered view — Traditional Permanent Life only (840 rows) |
| `CFIC_Rate_Load_Summary.csv` | Roll-up counts by wave |
| `CFIC_Rate_Load_Status_Overrides.csv` | **Manual checkoffs** — preserved when tracker is regenerated |
| `_build_rate_load_tracker.py` | Rebuild from Excel sources + merge overrides |

**Source spreadsheets** (do not edit for status — edit overrides or Google Sheet):

- `Citizens_Plan_Rate_Requirements_Catalog.xlsx` — what rates each plan needs
- `Citizens_Plan_Crosswak.xlsx` — CFIC plan → QLPlan mapping

## Workflow columns (update these when work progresses)

| Step | Columns | Values |
|------|---------|--------|
| 1. Source received | `source_received`, `source_received_date`, `source_file_location` | Y/N, date, path or filename |
| 2. Extracted | `extract_status`, `extract_complete_date` | Not Started → In Progress → Complete / Failed |
| 3. Load package | `load_package_ready` | Y when DBF/CSV package is ready for QLAdmin |
| 4. Loaded | `qladmin_loaded`, `qladmin_load_date`, `loaded_by` | Y + date + initials |
| 5. Validated | `validated_in_qladmin`, `validation_date` | Y after spot-check in QLAdmin |

Each row also shows: `qladmin_factor_table` (e.g. `QuikCvs`), `qladmin_key_table` (e.g. `QuikPlCv`), and `priority_wave` (Wave 1 = permanent life first).

---

## Google Sheets setup (recommended for the team)

Everyone with a Google account can use this. No special software.

### One-time setup

1. Open [Google Sheets](https://sheets.google.com) → **Blank spreadsheet**.
2. Name it **CFIC Rate Load Tracker**.
3. **File → Import → Upload** → select `CFIC_Rate_Load_Tracker.csv` (or `CFIC_Rate_Load_Tracker_Wave1.csv` for a smaller first pass).
4. Import location: **Replace current sheet**; separator: **Comma**.
5. **Share** the sheet with your team (Editor access for people who update status; Viewer for read-only).

### Make checkoffs easier

**Data validation (Y/N columns)** — select columns `source_received`, `load_package_ready`, `qladmin_loaded`, `validated_in_qladmin`:

- Data → Data validation → Criteria: **List of items** → `Y,N`

**Extract status dropdown** — column `extract_status`:

- List: `Not Started,In Progress,Complete,Failed,N/A`

**Conditional formatting** — highlight loaded rows:

- Format → Conditional formatting → Custom formula: `=$T2="Y"` (adjust column letter for `qladmin_loaded`) → green fill.

**Filter views** (recommended tabs or saved filters):

| View | Filter |
|------|--------|
| Wave 1 only | `priority_wave` = Wave 1 |
| Ready to load | `extract_status` = Complete AND `load_package_ready` = Y AND `qladmin_loaded` = N |
| Not started | `source_received` = N |
| In crosswalk | `in_plan_crosswalk` = Y |

### Optional: Summary tab

Add a second sheet **Summary** with:

```
=COUNTIF(Tracker!T:T,"Y")     -- qladmin_loaded count
=COUNTA(Tracker!A:A)-1        -- total rows
```

Or import `CFIC_Rate_Load_Summary.csv` as a second tab and refresh after each rebuild.

---

## Updating after you receive / load a rate

### Option A — Google Sheets only (simplest)

1. Find the row(s) for the plan — filter on `cfic_plan_code` (e.g. `P7MN`).
2. Set `source_received` = **Y**, fill date and file path.
3. As extract finishes: `extract_status` = **Complete**, `load_package_ready` = **Y**.
4. After QLAdmin load: `qladmin_loaded` = **Y**, date, your name in `loaded_by`.
5. After UAT: `validated_in_qladmin` = **Y**.

**Tip:** Sort by `last_updated` or add a filter on rows you changed this week.

### Option B — Repo + overrides (version-controlled)

When you want checkoffs in git:

1. Edit `CFIC_Rate_Load_Status_Overrides.csv` (one row per `tracker_id` you changed).
2. Run:

```powershell
python CFIC_Rates/tracking/_build_rate_load_tracker.py
```

3. Re-import or copy updated status columns into Google Sheets.

**Export from Google Sheets to overrides:** Download sheet as CSV, copy changed status columns into `CFIC_Rate_Load_Status_Overrides.csv` (must include `tracker_id`).

---

## When the Excel catalog changes

Citizens updates `Citizens_Plan_Rate_Requirements_Catalog.xlsx`:

```powershell
python CFIC_Rates/tracking/_build_rate_load_tracker.py
```

- New plan/rate rows are added with defaults (Not Started / N).
- Existing checkoffs in `CFIC_Rate_Load_Status_Overrides.csv` are **merged back** automatically.

Re-import the new `CFIC_Rate_Load_Tracker.csv` into Google Sheets, or use **File → Import → Replace** and re-apply validation rules once.

---

## Row grain

One tracker row = **Plan Code + Rate Category** (e.g. `P7MN|Cash / Surrender Values`).

Only categories marked **Expected**, **Conditional**, or descriptive requirements in the catalog are included. Pure "Not expected" / "Not indicated" rows are omitted.

## Priority waves

| Wave | Product families |
|------|------------------|
| Wave 1 | Traditional Permanent Life |
| Wave 2 | Term Life, Paid-Up / Nonforfeiture, Nonforfeiture Status |
| Wave 3 | Rider |
| Later | Annuity, A&H, Merchandise, etc. |

---

## Related

- Green-sheet extract: `Issue_Log/CFIC_Issue_01/`
- QLAdmin table schemas: `qla_core/rate_dbf_schema.py`
- Target platform: `docs/target_platform.md`
