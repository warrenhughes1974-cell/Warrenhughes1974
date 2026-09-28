# Issue 173 — Resolution Summary

**Issue:** 173 — ISWL negative fund balances
**Closed:** 2026-09-28

09/28/2026 Resolution: ISWL policies whose LifePRO fund is below zero now keep that negative amount on the last history row, instead of storing 0.00. Earlier months are unchanged. Examples: 9010779727C account -172,395.45; 9010737619C account -718,363.35; 9010735781C account -121,065.25.

The old always-on check that required these balances to be 0.00 stays removed. The new check fails if the negative ending balances disappear.
