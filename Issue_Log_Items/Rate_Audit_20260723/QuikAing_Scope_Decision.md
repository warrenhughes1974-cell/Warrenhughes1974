# QuikAing Scope Decision

**Decision:** `QuikAing` is tracked separately from the current enterprise rate package fix.

## Reason

The current fix scope is:

- Issue #98 CV duration placement in `QuikCvs`
- Issue #96 durable `1SALMI` `QuikPlCv` / `QuikPlTv` M+F key reproduction
- Full `QLA_Migration/Output/rates` source-to-package parity

`QuikAing` is not emitted by the main `qla_core.rate_pipeline` / `QLA_Migration/Output/rates` path today. Existing `QuikAing` artifacts live in the separate `PFSA_Annuity_interest/` workstream, and Issue #51 documented `QuikAing` / `QuikAinf` only as a fallback if QuikAint did not resolve projected-values UAT.

## Gate

Do not add `QuikAing` to the enterprise package without a separate issue that confirms:

- Source authority
- QLAdmin target table requirements
- Affected plans
- Expected row count and rates
- Post-load QLAdmin proof

For this rate audit cycle, `QuikAing` is not a blocker to fixing #98 / #96 or publishing the changed `QuikCvs`, `QuikPlCv`, and `QuikPlTv` tables.

