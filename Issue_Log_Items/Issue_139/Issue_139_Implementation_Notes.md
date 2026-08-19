# Issue 139 — Implementation Notes (2026-08-19 restore)

Root `app.py` had imported `suppress_policy_fees` but did not call it. `run_converter.bat` launches that file, so a later `quikridr` emit reloaded #21C/#58 fees including ISWL $25.

Restored the QLA_Migration withhold block on root `app.py`, re-applied withhold to current Output, and added fail-closed convert-time + `SMOKE_JOBS` smoke (same class of lock as Bank Acct #75).
