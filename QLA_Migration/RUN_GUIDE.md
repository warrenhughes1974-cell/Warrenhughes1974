# LifePRO → QLAdmin Conversion — Operator Run Guide (v57.8)

Plain-language steps for running the conversion application from start to finish.

---

## What this app does (in one sentence)

It reads LifePRO source files, applies your mapping rules, and writes **CSV files** that QLAdmin can load — products (`quikplan`), policies/clients/riders, optional claims, and optional rate tables.

---

## Before you start

### 1. Open the app

From the project folder, run **either**:

```powershell
cd C:\Users\warren\Documents\GitHub\Warrenhughes1974
python app.py
```

**or**

```powershell
cd C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration
python app.py
```

You should see: **ENTERPRISE DATA INTEGRATION SUITE v57.8**

Maximize the window and scroll if needed — there are several sections.

### 2. Confirm your folders and files

At the top, under **System Configuration & Path Mapping**, check these paths:

| Field | Should point to |
|--------|------------------|
| **Field Mapping (Rulebook)** | A **`.csv`** rulebook, e.g. `QLA_Migration\Configs\Sync_Rulebook_quikplan.csv` |
| **Source Data File** | A LifePRO extract in `QLA_Migration\Source\` (e.g. `quikmstr.csv`) |
| **Value Translation (CSV)** | `QLA_Migration\Mapping\Master_Value_Translation.csv` |
| **ID Crosswalk (CSV)** | `QLA_Migration\Mapping\Master_Crosswalk.csv` |
| **Relational File (quikclid)** | Often filled in after the first run |
| **Output Directory** | `QLA_Migration\Output` |

**Important:** The rulebook must be a **`.csv`**, not an `.xlsx`.

### 3. Know where results go

| What | Where |
|------|--------|
| **Business CSV outputs** (for QLAdmin) | `QLA_Migration\Output\` |
| **Rate table CSVs** | `QLA_Migration\Output\rates\` |
| **Errors / failure details** | `QLA_Migration\Error_Logs\run_YYYYMMDD_HHMMSS\` |
| **Non-CSV reports moved out of Output** | `QLA_Migration\Reports\` |
| **Sandbox DBF files** (if you enable them) | `plan_analysis\phase_r5_rate_loader\emitted_dbf\` |

`Output` should contain **CSV files only** after a run. Logs and reports go elsewhere.

---

## Recommended run order (full conversion)

Think of it as **3 steps in order**:

```
Step 1 → Product Setup     (creates quikplan.csv — your product catalog)
Step 2 → Full Batch        (creates policy, client, rider, etc.)
Step 3 → Rate Tables       (creates rate CSVs — optional but usually needed)
```

You can run Step 3 manually, or have Step 2 do it automatically (see checkbox below).

---

## Step 1 — Product Setup (quikplan.csv)

**Purpose:** Build the product/plan file (`quikplan.csv`) that everything else depends on.

**Where:** Scroll to **Product Setup Conversion (Phase P2C)**

**Before you click:**

1. Check **Emit to Output (quikplan.csv)** — required if you want the file written to Output (off by default).
2. Leave **Isolate from batch** checked — batch will use this file instead of rebuilding quikplan.
3. Leave **Block emit on ERROR** checked for production-quality runs (stops bad data from being written).

**Click:** **RUN PRODUCT SETUP CONVERSION** (purple button in that section)

**Watch:**

- Progress bar: `Stage X of 5 — …`
- Elapsed timer: `00:00:00` counting up
- Log at the bottom

**Success looks like:**

- Popup: “Product setup conversion completed successfully”
- Progress: green **Complete — quikplan.csv written to QLA_Migration\Output**
- File exists: `QLA_Migration\Output\quikplan.csv`

**If blocked:**

- Popup warns that validation blocked the output
- Check **Validation Errors** in the Product Setup panel
- Details may be in `QLA_Migration\Error_Logs\run_…`
- Common fix: a plan in source isn’t in `product_catalog_crosswalk.csv` — fix the crosswalk or exclude that row from source

**Do not go to Step 2 until Step 1 succeeds and `quikplan.csv` exists.**

---

## Step 2 — Full Batch Migration

**Purpose:** Convert the main LifePRO tables — clients, policies, riders, accounting, etc.

**Where:** **Run Controls** section (near the progress bar)

**Before you click:**

1. Confirm **Output Directory** = `QLA_Migration\Output`
2. Confirm **quikplan.csv** is already in Output (from Step 1)
3. In **Rate Table Generation** (scroll down), if you want rates in the same run:
   - Check **Include in full batch migration**
   - Check **Emit append-ready CSV tables**

**Click:** **EXECUTE FULL BATCH MIGRATION** (green button)

**What it does:**

- Reads all source tables from the folder tied to your Source Data File
- Skips rebuilding `quikplan` if **Isolate from batch** is on (uses your Step 1 file)
- Writes CSVs to `QLA_Migration\Output`
- Optionally runs claims (UAT mode + environment flags)
- Optionally runs rate generation at the end if **Include in full batch migration** is checked

**Watch:**

- Progress: `Stage X of 9 — …` (full batch uses 9 stages)
- Log messages like “BATCH SOURCE LOCK”, table names, validation notes

**Success looks like:**

- Popup: “Conversion Finished” or batch completion with claims info
- Progress: green **Complete — CSV outputs written to QLA_Migration\Output**
- Multiple `.csv` files in `QLA_Migration\Output`

**If it fails:**

- Progress turns red: **Failed at [stage name]**
- Log points to `QLA_Migration\Error_Logs\run_…`
- Open that folder for `exception_traceback.txt`, `failed_stage.txt`, etc.

---

## Step 3 — Rate Table Generation

**Purpose:** Build rate factor/key/member tables as CSVs for QLAdmin.

**Skip this step if** you already ran batch with **Include in full batch migration** checked and rates succeeded.

**Where:** **Rate Table Generation (Phase R5)** section, or **Run Controls** → **GENERATE RATE TABLES** (teal)

**Before you click:**

1. Check **Emit append-ready CSV tables (Output/rates/)** — usually on by default
2. **Emit sandbox DBF tables** — only if you need DBF prototypes (optional)
3. **Include in full batch migration** — only matters when running batch, not for this standalone button

**Click:** **GENERATE RATE TABLES**

**Success looks like:**

- Popup: “Rate tables generated successfully”
- **16 tables**, about **96,858 CSV rows** (if source data unchanged)
- Files in: `QLA_Migration\Output\rates\`
- Manifest: `QLA_Migration\Output\rates\rate_csv_manifest.csv`

**If blocked:**

- Validation blockers prevented emit — check log and `plan_analysis\phase_r5_rate_loader\` validation reports
- Error details in `QLA_Migration\Error_Logs\run_…`

---

## Quick reference — which button when?

| Button | When to use |
|--------|-------------|
| **RUN PRODUCT SETUP CONVERSION** | First — creates `quikplan.csv` |
| **EXECUTE FULL BATCH MIGRATION** | Second — all main policy/client/rider tables |
| **GENERATE RATE TABLES** | Third — rate CSVs (unless included in batch) |
| **RUN SINGLE TABLE CONVERSION** | Testing one table only — pick from dropdown first |
| **FULL PROJECT BACKUP** | Before a big run — creates a snapshot zip |

---

## What to watch during any run

1. **Elapsed timer** — `Elapsed: HH:MM:SS`
2. **Stage line** — e.g. `Stage 4 of 9 — Applying rulebooks and crosswalks`
3. **Detail line** — sub-step under the stage
4. **Conversion log** — scroll to bottom for latest messages
5. **Popups** — success, blocked, or failed

**Green progress + “Complete”** = good.  
**Red progress + Error_Logs path** = stop and read the error folder before retrying.

---

## Checklist — “Did it work?”

After a full run, verify:

- [ ] `QLA_Migration\Output\quikplan.csv` exists
- [ ] Other expected CSVs in `QLA_Migration\Output\` (quikmstr, quikclnt, quikridr, etc.)
- [ ] Rate CSVs in `QLA_Migration\Output\rates\` (if you ran rates)
- [ ] `Output` contains **only `.csv` files** (no `.txt`, `.dbf`, `.json` left behind)
- [ ] No red failure message on the progress bar
- [ ] If something failed, you checked `QLA_Migration\Error_Logs\run_…`
- [ ] **Output validation** ran automatically at end of batch (**v57.10+**, Stage 8) — check log for `OUTPUT VALIDATION: PASS` or `FAIL`
- [ ] Reports in `QLA_Migration\Reports\validation\validation_report_<timestamp>.txt` (and matching `validation_findings_*.csv`)

Optional manual re-run:

```powershell
python validate_output.py QLA_Migration/Output --source-dir QLA_Migration/Source
```

Skip in-app validation only if needed: set environment variable `QLA_SKIP_OUTPUT_VALIDATION=1` before launch.

Exit code `0` = PASS; `1` = ERROR findings. See `validation_config/priority_validation_checks.txt`.

---

## Common problems (plain English)

| Problem | What it means | What to do |
|---------|---------------|------------|
| **Product Setup BLOCKED** | A plan failed validation | Fix crosswalk or source; read Error_Logs folder |
| **quikplan.csv not found in batch** | Step 1 wasn’t run or emit wasn’t checked | Re-run Step 1 with **Emit to Output** checked |
| **Rulebook path is .xlsx** | Wrong file type | Point rulebook to the `.csv` in `QLA_Migration\Configs\` |
| **Rate generation skipped in batch** | CSV/DBF emit not checked | Check emit options in Rate Table Generation panel |
| **Busy / already running** | Another job is running | Wait for it to finish |
| **Validation Errors: 1+** | Governance caught bad data | Don’t bypass unless demo-only; fix the data issue |

---

## One-page cheat sheet

```
START APP
  python app.py  (from repo root)

CHECK PATHS
  Rulebook = .csv
  Source   = QLA_Migration\Source\...
  Output   = QLA_Migration\Output

STEP 1 — PRODUCT SETUP
  [x] Emit to Output
  [x] Isolate from batch
  Click: RUN PRODUCT SETUP CONVERSION
  Wait for: quikplan.csv in Output

STEP 2 — FULL BATCH
  Click: EXECUTE FULL BATCH MIGRATION
  Optional: [x] Include rate generation in batch
  Wait for: CSVs in Output

STEP 3 — RATE TABLES (if not in batch)
  [x] Emit append-ready CSV tables
  Click: GENERATE RATE TABLES
  Wait for: CSVs in Output\rates\

DONE
  Output = CSV files only
  Errors = Error_Logs\run_...
```

---

## Optional: environment flags (advanced)

Most operators don’t need these. They’re for claims UAT and special modes:

- `QLA_BATCH_INCLUDE_CLAIMS_UAT=1` — include claims in batch (UAT mode)
- `QLA_BATCH_INCLUDE_RATE_TABLES=1` — same as “Include in full batch migration” checkbox
- `QLA_PRODUCT_SETUP_ISOLATED=1` — same as “Isolate from batch” checkbox

The checkboxes in the UI are usually enough.

---

*Document version: v57.8 — LifePRO → QLAdmin Enterprise Data Integration Suite*
