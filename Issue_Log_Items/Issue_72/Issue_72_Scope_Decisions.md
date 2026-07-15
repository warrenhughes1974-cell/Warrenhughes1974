# Issue #72 — Scope Decisions

**Locked for Planning / Risk:** 2026-07-15  
**Authority:** Robert validation rule (Warren confirmed) — exercised ETI/RPU status wins over #57 election for `MSTATUS` 44/45 only

| ID | Decision |
|----|----------|
| **SD-72-1** | If final `quikmstr.MSTATUS` **= 44**, force `MNFOPT` **= 2** (ETI). |
| **SD-72-2** | If final `quikmstr.MSTATUS` **= 45**, force `MNFOPT` **= 3** (RPU). |
| **SD-72-3** | Force applies **always** for 44/45 (overwrite 0/1/2/3), not only when blank. |
| **SD-72-4** | Issue **#57** LifePRO election mapping (LP 3/4/5 → QLA 1/2/3 via PPBENTYP + `NF_` translation) **remains** for all statuses **other than** 44/45. |
| **SD-72-5** | Do **not** restore rulebook `PAID_UP_TYPE→MNFOPT` for the whole fleet. Use a narrow post-map override keyed off **final** `MSTATUS` only. |
| **SD-72-6** | Override must run **after** final `MSTATUS` is known (after #13 / #59 interceptor, `ST_` translation, and **#49** active-phase override). |
| **SD-72-7** | No change to `MSTATUS`, `MDIVOPT`, `quikridr`, rates, MPOLICY (#25), or MPREM (#26). |
| **SD-72-8** | UAT: reload `Test_Validation/quikmstr.csv`; spot-check `010407670C` (45→NFO 3) + one status-44 policy. |
