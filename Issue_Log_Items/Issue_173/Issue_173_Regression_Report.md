# Issue 173 — Regression Report

**Date:** 2026-09-28
**Verdict:** PASS

The history file was not rebuilt again. The 2026-09-25 QuikIswl emit is still the file under test: 545,150 rows.

| Check | Result |
|---|---|
| 9010779727C last account and cash value | −172,395.45 |
| 9010737619C last account and cash value | −718,363.35 |
| 9010735781C last account and cash value | −121,065.25 |
| 9010713704C last account and cash value | 45,551.94, unchanged |
| Policies ending negative | 247 or more, cash value equals account |

Earlier months still use the in-month floor. The reserve file was not rewritten. Plan and rate files were not rewritten.
