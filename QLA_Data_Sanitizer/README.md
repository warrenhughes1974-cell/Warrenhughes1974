# QLA Data Sanitizer (standalone)



Self-contained folder — everything needed to run PII sanitization is here.



## Folder layout



```

QLA_Data_Sanitizer/

  sanitize_app.py          ← GUI (launch this)

  sanitize_test_data.py    ← Engine (CLI + library)

  run_gui.bat              ← Windows double-click launcher

  requirements.txt         ← pip install -r requirements.txt (dbf package)

  config/

    field_masking_rules.json

  Input/                   ← Optional: drop CSV/DBF here

  Output/                  ← Default sanitized output + audit log

  README.md                ← This file

```



## Quick start (GUI)



```powershell

cd QLA_Data_Sanitizer

pip install -r requirements.txt

python sanitize_app.py

```



Or double-click `run_gui.bat`.



1. **Input** defaults to `../QLA_Migration/Source` if that folder has CSV/DBF files; otherwise `Input/`.

2. **Output** defaults to `Output/` in this folder.

3. Batch patterns default to `*.csv,*.dbf`.

4. Click **SANITIZE ALL FILES IN FOLDER**.

5. Review `Output/Sanitization_Audit_Log.txt`.



## Quick start (command line)



```powershell

cd QLA_Data_Sanitizer



python sanitize_test_data.py --input-dir ".\Input" --output-dir ".\Output" --patterns "*.csv,*.dbf"



python sanitize_test_data.py --input ".\Input\quikclnt.dbf" --output ".\Output\quikclnt.dbf"



python sanitize_test_data.py --input-dir "..\QLA_Migration\Source" --output-dir ".\Output"

```



## Requirements



- Python 3.x (same as QLA conversion project)

- **dbf** package: `pip install -r requirements.txt`

- tkinter (included with standard Windows Python)



No dependency on `app.py` or conversion packages.



## DBF behavior



- Same masking rules as CSV (`config/field_masking_rules.json`).

- Only **character (`C`)** fields are transformed; dates, numerics, and logicals are unchanged.

- Record count and DBF schema are preserved.

- `.FPT` / index sidecars are copied when present next to the source file.



## Deploy to another path (e.g. network `M:` drive)

Copy the **entire** `QLA_Data_Sanitizer` folder — not only `sanitize_app.py`. DBF support is in `sanitize_test_data.py` engine **1.1.0**.

```powershell
cd M:\QL32\Support\SupportTools\QLA_Data_Sanitizer
pip install -r requirements.txt
python check_setup.py
python sanitize_app.py
```

If you see **"No CSV files matched"** (batch) or **"new-line character seen in unquoted field"** (single file on `.dbf`), the `M:` copy is still using an old engine that reads DBF as CSV. Replace the full folder from the repo and re-run `check_setup.py`.



## After sanitization



Point the **QLAdmin conversion app** Source path at the **Output** folder (or copy sanitized files into `QLA_Migration/Source` for a dedicated UAT copy).



Keep original production extracts offline.

