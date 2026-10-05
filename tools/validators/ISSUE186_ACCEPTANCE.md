# Issue 186 acceptance run (v59.27)

The 9/30 LifePRO extract stays on Warren's PC. It is gitignored (`QLA_Migration/Source/`) and must not be committed. This repo is public.

The converter has no headless switch. `python app.py` always opens the QUIKConvert window, and the batch ends on a dialog that has to be clicked. Use the GUI steps below.

## What gets overwritten

Back these up before the v59.27 run. Copy the folders. Do not move them.

| Path | Why |
|---|---|
| `C:\Users\warren\Desktop\DBF_Append_Tool\input` | Hard-coded. A successful conversion copies `quikmstr.csv`, `quikridr.csv`, and the other quik CSVs here. |
| `C:\Users\warren\Desktop\DBF_Append_Tool\output` | Hard-coded. The same run writes the memo and claims DBFs here. QuikMstr and QuikRidr DBFs appear here only after the Append Tool itself is executed. |
| The Output folder set in the UI | Default is `QLA_Migration\Output` under the checkout that is running. That is where `quikmstr.csv` and `quikridr.csv` are written first. |

Those two desktop paths are constants in `app.py` (`DBF_APPEND_TOOL_INPUT` and `DBF_APPEND_TOOL_OUTPUT`). No environment variable redirects them.

`QLA_LAUNCH_DBF_APPEND_TOOL=0` only skips opening the Append Tool window. The copy into `\input` and `\output` still happens.

The CSV output folder can be redirected. In the UI, set Output to a new empty folder (for example `C:\temp\issue186-v5927-output`). The compare script reads that folder. It can also read the desktop `\input` CSVs, or `\output` DBFs after the Append Tool has been run. If a folder contains both the CSV and the DBF, the script uses the CSV.

## Fields the script compares

| File | Field | Meaning |
|---|---|---|
| `quikmstr.csv` or `QUIKMSTR.DBF` | `MSTATUS` | Policy header |
| `quikridr.csv` or `QUIKRIDR.DBF` | `MPHSTAT` where `MPHASE` is 1 | Coverage phase 1 |
| same phase-1 row | `MSAVESTAT` | Save status |

QLAdmin `MPOLICY` is the LifePRO `POLICY_NUMBER` plus `C`, right-justified to 11 characters (Issue #2). `9015FG8217` becomes `9015FG8217C`. Shorter numbers keep a leading space. The script compares them with the spaces removed.

## 1. Save the v59.26 results (before)

If the last 9/30 conversion is still the v59.26 output, copy that Output folder aside and do not run v59.26 again:

```bat
mkdir C:\temp\issue186-before
xcopy /E /I /Y C:\path\to\current\QLA_Migration\Output C:\temp\issue186-before
```

Use the folder that actually holds `quikmstr.csv` and `quikridr.csv` from that run. If those files now live only under the Append Tool input folder, copy that instead:

```bat
mkdir C:\temp\issue186-before
copy /Y C:\Users\warren\Desktop\DBF_Append_Tool\input\quikmstr.csv C:\temp\issue186-before\
copy /Y C:\Users\warren\Desktop\DBF_Append_Tool\input\quikridr.csv C:\temp\issue186-before\
```

If the v59.26 output is already gone, check out the base branch in a second worktree and run the same GUI steps into `C:\temp\issue186-before`:

```bat
cd /d C:\path\to\Warrenhughes1974
git fetch origin
git worktree add C:\temp\qla-v5926 origin/issue-34-pr7-quikisrr
```

## 2. Worktree for v59.27

Do this from the existing clone. Do not copy the extract into git.

```bat
cd /d C:\path\to\Warrenhughes1974
git fetch origin
git worktree add C:\temp\qla-issue186 origin/cursor/issue-186-active-lp-4564
```

The worktree does not contain `QLA_Migration\Source` (gitignored). Point the running app at the real source folder with a junction so the UI auto-path finds the 9/30 files:

```bat
mklink /J C:\temp\qla-issue186\QLA_Migration\Source C:\path\to\Warrenhughes1974\QLA_Migration\Source
```

Do not `git add` that folder.

Back up the desktop Append Tool folders now, before the run:

```bat
mkdir C:\temp\append-tool-backup
xcopy /E /I /Y C:\Users\warren\Desktop\DBF_Append_Tool\input C:\temp\append-tool-backup\input
xcopy /E /I /Y C:\Users\warren\Desktop\DBF_Append_Tool\output C:\temp\append-tool-backup\output
```

## 3. GUI run (required)

```bat
set QLA_VALUATION_DATE=20260930
set QLA_LAUNCH_DBF_APPEND_TOOL=0
cd /d C:\temp\qla-issue186
QLA_Migration\run_converter.bat
```

`run_converter.bat` starts `python app.py` from the worktree root. In the window:

1. Confirm the version banner says **v59.27**.
2. Source must resolve to `PPOLC_PolicyMaster_Extract_20260930.csv` (the log line shows the source file). If it does not, browse Source to the real `QLA_Migration\Source` folder.
3. Set Output to `C:\temp\issue186-v5927-output` (create the folder first). Leaving the worktree `QLA_Migration\Output` is also fine, because that folder is not the main checkout's Output.
4. Click **EXECUTE FULL BATCH MIGRATION**.
5. Wait for the Complete dialog and click OK.

There is no command that runs this batch without the window.

## 4. Compare

From the worktree, so the script is the v59.27 copy:

```bat
cd /d C:\temp\qla-issue186
python tools\validators\issue186_before_after.py --source-dir C:\path\to\Warrenhughes1974\QLA_Migration\Source --before-dir C:\temp\issue186-before --after-dir C:\temp\issue186-v5927-output --out C:\temp\issue186-compare.csv
```

`--source-dir` is the folder that contains `PPOLC_PolicyMaster_Extract_20260930.csv` (or a single subfolder that contains it). `--before-dir` and `--after-dir` are the folders that contain `quikmstr` and `quikridr` as CSV or DBF.

The script prints `Active+LP policies found: N` (about 40 on the 9/30 extract) and `PASS` or `FAIL`.

PASS means all three of these:

- Every Active + `PAID_UP_TYPE=LP` policy is 22 on header, phase 1, and save status after the run.
- `9015FG8217C` moves from 54 to 22 on all three.
- No policy outside that Active+LP set changes header `MSTATUS` between before and after. Any that do are listed on screen and in the CSV as `HEADER_CHANGE`.

Exit code 0 is PASS, 1 is FAIL, 2 means a file or column was missing. The report is only the `--out` CSV. Client extracts are not written.

A local check of the script, with fake policies and no client file, is:

```bat
python tools\validators\issue186_before_after.py --self-check
```
