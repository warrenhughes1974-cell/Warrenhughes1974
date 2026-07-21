# QLAdmin Data Governance Executive Summary

## Overall Result

FAILED — problems were found that need attention

## Run Snapshot

| | |
|---|---|
| Data Region | `Q:\CSO\CSO_Test_6_30_2026` |
| Run ID | `DG-20260719_103948_701830` |
| Run Date | July 19, 2026 at 10:39:48 AM |
| Governance Items Executed | DG-PLANVALUES — Plan Value Reference Integrity |
| Rules Executed | 1 |
| Rules Passed | 0 |
| Rules Failed | 1 |
| Rules Not Run | 0 |
| Rules with Processing Errors | 0 |
| Total Records Reviewed | 229 |
| Records That Looked Fine | 102 |
| Problems Found | 127 |
| Data Conformance Accuracy | **44.54%** |

## Data Conformance Accuracy

**44.54%**

44.54% of the record checks completed without a governance exception.

Data Conformance Accuracy represents the percentage of evaluated records that matched the active governance rules during this run. It does not independently confirm that every value is factually or actuarially correct.

## Top Issues

1. 127 records failed 'ETI Mortality Table Must Exist in QuikQxs' (example: QuikPlCv plan '130JEB' contains a blank ETI mortality table.)

---

# QLAdmin Data Governance — Results (Plain Language)

## Bottom line

**FAILED — problems were found that need attention**

We found **127 problem(s)** in the data reviewed. Details are listed below by check. Nothing in the source files was changed — this report only points out issues for review.

## What this report covers

These checks review the selected QLAdmin tables against the active governance rules for this run (uniqueness, references, required fields, formats, and configured default values).

| | |
|---|---|
| When it ran | 2026-07-19 10:39:48 |
| Run ID | DG-20260719_103948_701830 |
| Data region (full path) | `Q:\CSO\CSO_Test_6_30_2026` |
| Output folder for this run | `C:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\remediation\items\DG-R-011_mortality_eti_quikqxs\examine_out\cso\DG-PLANVALUES-002\DG-20260719_103948_701830` |
| Source opened read-only | Yes |
| Source files modified | No |
| Records reviewed | 229 |
| Records that looked fine | 102 |
| Problems found | 127 |
| Data Conformance Accuracy | 44.54% |
| Technical errors | 0 |
| Validation guide | `data_governance_validation_guide.md` |
| Validation manifest | `data_governance_validation_manifest.json` |

## Item 6: Plan Value Reference Integrity

Validate that mortality tables, plans, gender codes, underwriting classes, bands, issue states, and effective dates used by QuikPlCv, QuikPlTv, QuikPlGp, QuikPlDb, and QuikPlDv are approved defaults or valid setup references.

### Check: ETI Mortality Table Must Exist in QuikQxs

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure every populated normalized ETIMORT value exists exactly once in QuikQxs.

Looked at **229** record(s): **102** looked fine, **127** had a problem.

**Problems found:**

1. QuikPlCv plan '130JEB' contains a blank ETI mortality table.
2. QuikPlCv plan '1666AI' contains a blank ETI mortality table.
3. QuikPlCv plan '1SALMI' contains a blank ETI mortality table.
4. QuikPlCv plan '261PUA' contains a blank ETI mortality table.
5. QuikPlCv plan '261PUA' contains a blank ETI mortality table.
6. QuikPlCv plan '265PUA' contains a blank ETI mortality table.
7. QuikPlCv plan '280PUA' contains a blank ETI mortality table.
8. QuikPlCv plan '280PUA' contains a blank ETI mortality table.
9. QuikPlCv plan '560STR' contains a blank ETI mortality table.
10. QuikPlCv plan '578STR' contains a blank ETI mortality table.
11. QuikPlCv plan 'A96DAR' contains a blank ETI mortality table.
12. QuikPlCv plan '528CTR' contains a blank ETI mortality table.
13. QuikPlCv plan '542STR' contains a blank ETI mortality table.
14. QuikPlCv plan '543CTR' contains a blank ETI mortality table.
15. QuikPlCv plan '5646AT' contains a blank ETI mortality table.
16. QuikPlCv plan '5667AT' contains a blank ETI mortality table.
17. QuikPlCv plan '578CTR' contains a blank ETI mortality table.
18. QuikPlCv plan '57ATCR' contains a blank ETI mortality table.
19. QuikPlCv plan '5CDT10' contains a blank ETI mortality table.
20. QuikPlCv plan '5L0110' contains a blank ETI mortality table.
21. QuikPlCv plan '5L01MA' contains a blank ETI mortality table.
22. QuikPlCv plan '5L0510' contains a blank ETI mortality table.
23. QuikPlCv plan '5L075Y' contains a blank ETI mortality table.
24. QuikPlCv plan '719CDT' contains a blank ETI mortality table.
25. QuikPlCv plan '719CTR' contains a blank ETI mortality table.
26. QuikPlCv plan '719SDT' contains a blank ETI mortality table.
27. QuikPlCv plan '7619DT' contains a blank ETI mortality table.
28. QuikPlCv plan '7619PU' contains a blank ETI mortality table.
29. QuikPlCv plan '7647SP' contains a blank ETI mortality table.
30. QuikPlCv plan '7686S3' contains a blank ETI mortality table.
31. QuikPlCv plan '7687J3' contains a blank ETI mortality table.
32. QuikPlCv plan '7690DT' contains a blank ETI mortality table.
33. QuikPlCv plan '778FTR' contains a blank ETI mortality table.
34. QuikPlCv plan '7SDT10' contains a blank ETI mortality table.
35. QuikPlCv plan '901ADB' contains a blank ETI mortality table.
36. QuikPlCv plan '9065WP' contains a blank ETI mortality table.
37. QuikPlCv plan '9085WP' contains a blank ETI mortality table.
38. QuikPlCv plan '90OLWP' contains a blank ETI mortality table.
39. QuikPlCv plan '90PDTH' contains a blank ETI mortality table.
40. QuikPlCv plan '90POWP' contains a blank ETI mortality table.
41. QuikPlCv plan '910RWP' contains a blank ETI mortality table.
42. QuikPlCv plan '910SWP' contains a blank ETI mortality table.
43. QuikPlCv plan '920ADB' contains a blank ETI mortality table.
44. QuikPlCv plan '934JWP' contains a blank ETI mortality table.
45. QuikPlCv plan '934SWP' contains a blank ETI mortality table.
46. QuikPlCv plan '943CWP' contains a blank ETI mortality table.
47. QuikPlCv plan '9595WP' contains a blank ETI mortality table.
48. QuikPlCv plan '960ADB' contains a blank ETI mortality table.
49. QuikPlCv plan '960CWP' contains a blank ETI mortality table.
50. QuikPlCv plan '960GIO' contains a blank ETI mortality table.
51. QuikPlCv plan '960SWP' contains a blank ETI mortality table.
52. QuikPlCv plan '965ADB' contains a blank ETI mortality table.
53. QuikPlCv plan '9665WP' contains a blank ETI mortality table.
54. QuikPlCv plan '967ADB' contains a blank ETI mortality table.
55. QuikPlCv plan '976659' contains a blank ETI mortality table.
56. QuikPlCv plan '977ADB' contains a blank ETI mortality table.
57. QuikPlCv plan '980JPO' contains a blank ETI mortality table.
58. QuikPlCv plan '982JPO' contains a blank ETI mortality table.
59. QuikPlCv plan '9896WP' contains a blank ETI mortality table.
60. QuikPlCv plan '996ADB' contains a blank ETI mortality table.
61. QuikPlCv plan '9ADB10' contains a blank ETI mortality table.
62. QuikPlCv plan '9CDTWP' contains a blank ETI mortality table.
63. QuikPlCv plan '9CTRWP' contains a blank ETI mortality table.
64. QuikPlCv plan '9DIS20' contains a blank ETI mortality table.
65. QuikPlCv plan '9DIS24' contains a blank ETI mortality table.
66. QuikPlCv plan '9DIS25' contains a blank ETI mortality table.
67. QuikPlCv plan '9DIS29' contains a blank ETI mortality table.
68. QuikPlCv plan '9DIS70' contains a blank ETI mortality table.
69. QuikPlCv plan '9DIS80' contains a blank ETI mortality table.
70. QuikPlCv plan '9DIS90' contains a blank ETI mortality table.
71. QuikPlCv plan '9DS24B' contains a blank ETI mortality table.
72. QuikPlCv plan '9DS24C' contains a blank ETI mortality table.
73. QuikPlCv plan '9FTRWP' contains a blank ETI mortality table.
74. QuikPlCv plan '9GPO10' contains a blank ETI mortality table.
75. QuikPlCv plan '9GPO79' contains a blank ETI mortality table.
76. QuikPlCv plan '9JPO10' contains a blank ETI mortality table.
77. QuikPlCv plan '9JPO46' contains a blank ETI mortality table.
78. QuikPlCv plan '9L01WP' contains a blank ETI mortality table.
79. QuikPlCv plan '9L05WP' contains a blank ETI mortality table.
80. QuikPlCv plan '9L16PF' contains a blank ETI mortality table.
81. QuikPlCv plan '9OLDWP' contains a blank ETI mortality table.
82. QuikPlCv plan '9POADB' contains a blank ETI mortality table.
83. QuikPlCv plan '9SLADB' contains a blank ETI mortality table.
84. QuikPlCv plan '9STRWP' contains a blank ETI mortality table.
85. QuikPlCv plan '9WP646' contains a blank ETI mortality table.
86. QuikPlCv plan '9WPL10' contains a blank ETI mortality table.
87. QuikPlCv plan 'A60MIR' contains a blank ETI mortality table.
88. QuikPlCv plan '130JEB' contains a blank ETI mortality table.
89. QuikPlCv plan '1666AI' contains a blank ETI mortality table.
90. QuikPlCv plan '265PUA' contains a blank ETI mortality table.
91. QuikPlCv plan '5646AT' contains a blank ETI mortality table.
92. QuikPlCv plan '578STR' contains a blank ETI mortality table.
93. QuikPlCv plan '5CDT10' contains a blank ETI mortality table.
94. QuikPlCv plan '5L0110' contains a blank ETI mortality table.
95. QuikPlCv plan '5L01MA' contains a blank ETI mortality table.
96. QuikPlCv plan '5L0510' contains a blank ETI mortality table.
97. QuikPlCv plan '5L075Y' contains a blank ETI mortality table.
98. QuikPlCv plan '719CTR' contains a blank ETI mortality table.
99. QuikPlCv plan '719SDT' contains a blank ETI mortality table.
100. QuikPlCv plan '7619DT' contains a blank ETI mortality table.
101. QuikPlCv plan '7619PU' contains a blank ETI mortality table.
102. QuikPlCv plan '7686S3' contains a blank ETI mortality table.
103. QuikPlCv plan '7687J3' contains a blank ETI mortality table.
104. QuikPlCv plan '7690DT' contains a blank ETI mortality table.
105. QuikPlCv plan '7SDT10' contains a blank ETI mortality table.
106. QuikPlCv plan '901ADB' contains a blank ETI mortality table.
107. QuikPlCv plan '9065WP' contains a blank ETI mortality table.
108. QuikPlCv plan '9085WP' contains a blank ETI mortality table.
109. QuikPlCv plan '90OLWP' contains a blank ETI mortality table.
110. QuikPlCv plan '910RWP' contains a blank ETI mortality table.
111. QuikPlCv plan '934SWP' contains a blank ETI mortality table.
112. QuikPlCv plan '9595WP' contains a blank ETI mortality table.
113. QuikPlCv plan '960ADB' contains a blank ETI mortality table.
114. QuikPlCv plan '960SWP' contains a blank ETI mortality table.
115. QuikPlCv plan '965ADB' contains a blank ETI mortality table.
116. QuikPlCv plan '9665WP' contains a blank ETI mortality table.
117. QuikPlCv plan '976659' contains a blank ETI mortality table.
118. QuikPlCv plan '9896WP' contains a blank ETI mortality table.
119. QuikPlCv plan '996ADB' contains a blank ETI mortality table.
120. QuikPlCv plan '9ADB10' contains a blank ETI mortality table.
121. QuikPlCv plan '9L01WP' contains a blank ETI mortality table.
122. QuikPlCv plan '9L05WP' contains a blank ETI mortality table.
123. QuikPlCv plan '9L16PF' contains a blank ETI mortality table.
124. QuikPlCv plan '9OLDWP' contains a blank ETI mortality table.
125. QuikPlCv plan '9POADB' contains a blank ETI mortality table.
126. QuikPlCv plan '9WPL10' contains a blank ETI mortality table.
127. QuikPlCv plan 'A60MIR' contains a blank ETI mortality table.

## What to do next

1. Review each problem listed above with the business owner of the related data.
2. Correct the source QLAdmin data if the finding is valid (this tool does **not** change the data for you).
3. Re-run the governance checks after corrections.

Companion files: `data_governance_validation_guide.md` (what was validated), `data_governance_validation_manifest.json`, `data_governance_findings.csv`, `data_governance_summary.csv`.
