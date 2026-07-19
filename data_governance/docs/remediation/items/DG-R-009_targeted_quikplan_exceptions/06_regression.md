# DG-R-009 — Regression

**Date:** 2026-07-18

| Guard | Result |
|-------|--------|
| Only listed SP plans updated on CSO | **Pass** |
| Non-SP PAYYRS/PAYAGE untouched | **Pass** (JPO residuals intentionally unchanged) |
| Conversion config-driven (no hardcode in emit loop) | **Pass** — CSV list |
| APP_VERSION both app.py copies | **v58.10** |

**CLOSED** with documented residuals (JPO / BASIS / 1970PA / WPA RRULE). Next: DG-R-010.
