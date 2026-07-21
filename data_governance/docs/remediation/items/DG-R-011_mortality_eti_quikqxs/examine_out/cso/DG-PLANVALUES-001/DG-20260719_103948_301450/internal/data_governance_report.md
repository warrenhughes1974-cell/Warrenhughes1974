# QLAdmin Data Governance Executive Summary

## Overall Result

FAILED — problems were found that need attention

## Run Snapshot

| | |
|---|---|
| Data Region | `Q:\CSO\CSO_Test_6_30_2026` |
| Run ID | `DG-20260719_103948_301450` |
| Run Date | July 19, 2026 at 10:39:48 AM |
| Governance Items Executed | DG-PLANVALUES — Plan Value Reference Integrity |
| Rules Executed | 1 |
| Rules Passed | 0 |
| Rules Failed | 1 |
| Rules Not Run | 0 |
| Rules with Processing Errors | 0 |
| Total Records Reviewed | 508 |
| Records That Looked Fine | 245 |
| Problems Found | 263 |
| Data Conformance Accuracy | **48.23%** |

## Data Conformance Accuracy

**48.23%**

48.23% of the record checks completed without a governance exception.

Data Conformance Accuracy represents the percentage of evaluated records that matched the active governance rules during this run. It does not independently confirm that every value is factually or actuarially correct.

## Top Issues

1. 263 records failed 'Mortality Table Must Exist in QuikQxs' (example: QuikPlCv plan '130JEB' contains a blank mortality table.)

---

# QLAdmin Data Governance — Results (Plain Language)

## Bottom line

**FAILED — problems were found that need attention**

We found **263 problem(s)** in the data reviewed. Details are listed below by check. Nothing in the source files was changed — this report only points out issues for review.

## What this report covers

These checks review the selected QLAdmin tables against the active governance rules for this run (uniqueness, references, required fields, formats, and configured default values).

| | |
|---|---|
| When it ran | 2026-07-19 10:39:48 |
| Run ID | DG-20260719_103948_301450 |
| Data region (full path) | `Q:\CSO\CSO_Test_6_30_2026` |
| Output folder for this run | `C:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\remediation\items\DG-R-011_mortality_eti_quikqxs\examine_out\cso\DG-PLANVALUES-001\DG-20260719_103948_301450` |
| Source opened read-only | Yes |
| Source files modified | No |
| Records reviewed | 508 |
| Records that looked fine | 245 |
| Problems found | 263 |
| Data Conformance Accuracy | 48.23% |
| Technical errors | 0 |
| Validation guide | `data_governance_validation_guide.md` |
| Validation manifest | `data_governance_validation_manifest.json` |

## Item 6: Plan Value Reference Integrity

Validate that mortality tables, plans, gender codes, underwriting classes, bands, issue states, and effective dates used by QuikPlCv, QuikPlTv, QuikPlGp, QuikPlDb, and QuikPlDv are approved defaults or valid setup references.

### Check: Mortality Table Must Exist in QuikQxs

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure every populated normalized MORT value on applicable plan-value tables exists exactly once in QuikQxs.

Looked at **508** record(s): **245** looked fine, **263** had a problem.

**Problems found:**

1. QuikPlCv plan '130JEB' contains a blank mortality table.
2. QuikPlCv plan '1666AI' contains a blank mortality table.
3. QuikPlCv plan '1SALMI' contains a blank mortality table.
4. QuikPlCv plan '261PUA' contains a blank mortality table.
5. QuikPlCv plan '261PUA' contains a blank mortality table.
6. QuikPlCv plan '265PUA' contains a blank mortality table.
7. QuikPlCv plan '280PUA' contains a blank mortality table.
8. QuikPlCv plan '280PUA' contains a blank mortality table.
9. QuikPlCv plan '560STR' contains a blank mortality table.
10. QuikPlCv plan '578STR' contains a blank mortality table.
11. QuikPlCv plan 'A96DAR' contains a blank mortality table.
12. QuikPlCv plan '528CTR' contains a blank mortality table.
13. QuikPlCv plan '542STR' contains a blank mortality table.
14. QuikPlCv plan '543CTR' contains a blank mortality table.
15. QuikPlCv plan '578CTR' contains a blank mortality table.
16. QuikPlCv plan '57ATCR' contains a blank mortality table.
17. QuikPlCv plan '5CDT10' contains a blank mortality table.
18. QuikPlCv plan '719CDT' contains a blank mortality table.
19. QuikPlCv plan '719CTR' contains a blank mortality table.
20. QuikPlCv plan '719SDT' contains a blank mortality table.
21. QuikPlCv plan '7619PU' contains a blank mortality table.
22. QuikPlCv plan '7647SP' contains a blank mortality table.
23. QuikPlCv plan '7686S3' contains a blank mortality table.
24. QuikPlCv plan '7687J3' contains a blank mortality table.
25. QuikPlCv plan '7690DT' contains a blank mortality table.
26. QuikPlCv plan '778FTR' contains a blank mortality table.
27. QuikPlCv plan '7SDT10' contains a blank mortality table.
28. QuikPlCv plan '901ADB' contains a blank mortality table.
29. QuikPlCv plan '9065WP' contains a blank mortality table.
30. QuikPlCv plan '9085WP' contains a blank mortality table.
31. QuikPlCv plan '90OLWP' contains a blank mortality table.
32. QuikPlCv plan '90PDTH' contains a blank mortality table.
33. QuikPlCv plan '90POWP' contains a blank mortality table.
34. QuikPlCv plan '910RWP' contains a blank mortality table.
35. QuikPlCv plan '910SWP' contains a blank mortality table.
36. QuikPlCv plan '920ADB' contains a blank mortality table.
37. QuikPlCv plan '934JWP' contains a blank mortality table.
38. QuikPlCv plan '934SWP' contains a blank mortality table.
39. QuikPlCv plan '943CWP' contains a blank mortality table.
40. QuikPlCv plan '9595WP' contains a blank mortality table.
41. QuikPlCv plan '960ADB' contains a blank mortality table.
42. QuikPlCv plan '960CWP' contains a blank mortality table.
43. QuikPlCv plan '960GIO' contains a blank mortality table.
44. QuikPlCv plan '960SWP' contains a blank mortality table.
45. QuikPlCv plan '965ADB' contains a blank mortality table.
46. QuikPlCv plan '9665WP' contains a blank mortality table.
47. QuikPlCv plan '967ADB' contains a blank mortality table.
48. QuikPlCv plan '976659' contains a blank mortality table.
49. QuikPlCv plan '977ADB' contains a blank mortality table.
50. QuikPlCv plan '980JPO' contains a blank mortality table.
51. QuikPlCv plan '982JPO' contains a blank mortality table.
52. QuikPlCv plan '9896WP' contains a blank mortality table.
53. QuikPlCv plan '996ADB' contains a blank mortality table.
54. QuikPlCv plan '9ADB10' contains a blank mortality table.
55. QuikPlCv plan '9CDTWP' contains a blank mortality table.
56. QuikPlCv plan '9CTRWP' contains a blank mortality table.
57. QuikPlCv plan '9DIS20' contains a blank mortality table.
58. QuikPlCv plan '9DIS24' contains a blank mortality table.
59. QuikPlCv plan '9DIS25' contains a blank mortality table.
60. QuikPlCv plan '9DIS29' contains a blank mortality table.
61. QuikPlCv plan '9DIS70' contains a blank mortality table.
62. QuikPlCv plan '9DIS80' contains a blank mortality table.
63. QuikPlCv plan '9DIS90' contains a blank mortality table.
64. QuikPlCv plan '9DS24B' contains a blank mortality table.
65. QuikPlCv plan '9DS24C' contains a blank mortality table.
66. QuikPlCv plan '9FTRWP' contains a blank mortality table.
67. QuikPlCv plan '9GPO10' contains a blank mortality table.
68. QuikPlCv plan '9GPO79' contains a blank mortality table.
69. QuikPlCv plan '9JPO10' contains a blank mortality table.
70. QuikPlCv plan '9JPO46' contains a blank mortality table.
71. QuikPlCv plan '9L01WP' contains a blank mortality table.
72. QuikPlCv plan '9L05WP' contains a blank mortality table.
73. QuikPlCv plan '9L16PF' contains a blank mortality table.
74. QuikPlCv plan '9OLDWP' contains a blank mortality table.
75. QuikPlCv plan '9POADB' contains a blank mortality table.
76. QuikPlCv plan '9SLADB' contains a blank mortality table.
77. QuikPlCv plan '9STRWP' contains a blank mortality table.
78. QuikPlCv plan '9WP646' contains a blank mortality table.
79. QuikPlCv plan '9WPL10' contains a blank mortality table.
80. QuikPlCv plan 'A60MIR' contains a blank mortality table.
81. QuikPlCv plan '130JEB' contains a blank mortality table.
82. QuikPlCv plan '1666AI' contains a blank mortality table.
83. QuikPlCv plan '265PUA' contains a blank mortality table.
84. QuikPlCv plan '578STR' contains a blank mortality table.
85. QuikPlCv plan '5CDT10' contains a blank mortality table.
86. QuikPlCv plan '719CTR' contains a blank mortality table.
87. QuikPlCv plan '719SDT' contains a blank mortality table.
88. QuikPlCv plan '7619PU' contains a blank mortality table.
89. QuikPlCv plan '7686S3' contains a blank mortality table.
90. QuikPlCv plan '7687J3' contains a blank mortality table.
91. QuikPlCv plan '7690DT' contains a blank mortality table.
92. QuikPlCv plan '7SDT10' contains a blank mortality table.
93. QuikPlCv plan '901ADB' contains a blank mortality table.
94. QuikPlCv plan '9065WP' contains a blank mortality table.
95. QuikPlCv plan '9085WP' contains a blank mortality table.
96. QuikPlCv plan '90OLWP' contains a blank mortality table.
97. QuikPlCv plan '910RWP' contains a blank mortality table.
98. QuikPlCv plan '934SWP' contains a blank mortality table.
99. QuikPlCv plan '9595WP' contains a blank mortality table.
100. QuikPlCv plan '960ADB' contains a blank mortality table.
101. QuikPlCv plan '960SWP' contains a blank mortality table.
102. QuikPlCv plan '965ADB' contains a blank mortality table.
103. QuikPlCv plan '9665WP' contains a blank mortality table.
104. QuikPlCv plan '976659' contains a blank mortality table.
105. QuikPlCv plan '9896WP' contains a blank mortality table.
106. QuikPlCv plan '996ADB' contains a blank mortality table.
107. QuikPlCv plan '9ADB10' contains a blank mortality table.
108. QuikPlCv plan '9L01WP' contains a blank mortality table.
109. QuikPlCv plan '9L05WP' contains a blank mortality table.
110. QuikPlCv plan '9L16PF' contains a blank mortality table.
111. QuikPlCv plan '9OLDWP' contains a blank mortality table.
112. QuikPlCv plan '9POADB' contains a blank mortality table.
113. QuikPlCv plan '9WPL10' contains a blank mortality table.
114. QuikPlCv plan 'A60MIR' contains a blank mortality table.
115. QuikPlTv plan '130JEB' contains a blank mortality table.
116. QuikPlTv plan '130JEB' contains a blank mortality table.
117. QuikPlTv plan '1666AI' contains a blank mortality table.
118. QuikPlTv plan '1666AI' contains a blank mortality table.
119. QuikPlTv plan '261PUA' contains a blank mortality table.
120. QuikPlTv plan '261PUA' contains a blank mortality table.
121. QuikPlTv plan '265PUA' contains a blank mortality table.
122. QuikPlTv plan '265PUA' contains a blank mortality table.
123. QuikPlTv plan '280PUA' contains a blank mortality table.
124. QuikPlTv plan '280PUA' contains a blank mortality table.
125. QuikPlTv plan '528CTR' contains a blank mortality table.
126. QuikPlTv plan '542STR' contains a blank mortality table.
127. QuikPlTv plan '542STR' contains a blank mortality table.
128. QuikPlTv plan '543CTR' contains a blank mortality table.
129. QuikPlTv plan '543CTR' contains a blank mortality table.
130. QuikPlTv plan '560STR' contains a blank mortality table.
131. QuikPlTv plan '578STR' contains a blank mortality table.
132. QuikPlTv plan '578STR' contains a blank mortality table.
133. QuikPlTv plan '5CDT10' contains a blank mortality table.
134. QuikPlTv plan '5CDT10' contains a blank mortality table.
135. QuikPlTv plan '5CDT10' contains a blank mortality table.
136. QuikPlTv plan '5CDT10' contains a blank mortality table.
137. QuikPlTv plan '5CDT10' contains a blank mortality table.
138. QuikPlTv plan '5CDT10' contains a blank mortality table.
139. QuikPlTv plan '719CTR' contains a blank mortality table.
140. QuikPlTv plan '719CTR' contains a blank mortality table.
141. QuikPlTv plan '719SDT' contains a blank mortality table.
142. QuikPlTv plan '719SDT' contains a blank mortality table.
143. QuikPlTv plan '7619PU' contains a blank mortality table.
144. QuikPlTv plan '7619PU' contains a blank mortality table.
145. QuikPlTv plan '7686S3' contains a blank mortality table.
146. QuikPlTv plan '7686S3' contains a blank mortality table.
147. QuikPlTv plan '7686S3' contains a blank mortality table.
148. QuikPlTv plan '7686S3' contains a blank mortality table.
149. QuikPlTv plan '7687J3' contains a blank mortality table.
150. QuikPlTv plan '7687J3' contains a blank mortality table.
151. QuikPlTv plan '7687J3' contains a blank mortality table.
152. QuikPlTv plan '7690DT' contains a blank mortality table.
153. QuikPlTv plan '7690DT' contains a blank mortality table.
154. QuikPlTv plan '778FTR' contains a blank mortality table.
155. QuikPlTv plan '778FTR' contains a blank mortality table.
156. QuikPlTv plan '7SDT10' contains a blank mortality table.
157. QuikPlTv plan '7SDT10' contains a blank mortality table.
158. QuikPlTv plan '7SDT10' contains a blank mortality table.
159. QuikPlTv plan '7SDT10' contains a blank mortality table.
160. QuikPlTv plan '7SDT10' contains a blank mortality table.
161. QuikPlTv plan '7SDT10' contains a blank mortality table.
162. QuikPlTv plan '901ADB' contains a blank mortality table.
163. QuikPlTv plan '901ADB' contains a blank mortality table.
164. QuikPlTv plan '901ADB' contains a blank mortality table.
165. QuikPlTv plan '901ADB' contains a blank mortality table.
166. QuikPlTv plan '9065WP' contains a blank mortality table.
167. QuikPlTv plan '9065WP' contains a blank mortality table.
168. QuikPlTv plan '910RWP' contains a blank mortality table.
169. QuikPlTv plan '910RWP' contains a blank mortality table.
170. QuikPlTv plan '910RWP' contains a blank mortality table.
171. QuikPlTv plan '910RWP' contains a blank mortality table.
172. QuikPlTv plan '910RWP' contains a blank mortality table.
173. QuikPlTv plan '910RWP' contains a blank mortality table.
174. QuikPlTv plan '910RWP' contains a blank mortality table.
175. QuikPlTv plan '960ADB' contains a blank mortality table.
176. QuikPlTv plan '960ADB' contains a blank mortality table.
177. QuikPlTv plan '960SWP' contains a blank mortality table.
178. QuikPlTv plan '960SWP' contains a blank mortality table.
179. QuikPlTv plan '965ADB' contains a blank mortality table.
180. QuikPlTv plan '965ADB' contains a blank mortality table.
181. QuikPlTv plan '976659' contains a blank mortality table.
182. QuikPlTv plan '976659' contains a blank mortality table.
183. QuikPlTv plan '976659' contains a blank mortality table.
184. QuikPlTv plan '976659' contains a blank mortality table.
185. QuikPlTv plan '976659' contains a blank mortality table.
186. QuikPlTv plan '976659' contains a blank mortality table.
187. QuikPlTv plan '976659' contains a blank mortality table.
188. QuikPlTv plan '976659' contains a blank mortality table.
189. QuikPlTv plan '9896WP' contains a blank mortality table.
190. QuikPlTv plan '9896WP' contains a blank mortality table.
191. QuikPlTv plan '996ADB' contains a blank mortality table.
192. QuikPlTv plan '996ADB' contains a blank mortality table.
193. QuikPlTv plan '996ADB' contains a blank mortality table.
194. QuikPlTv plan '996ADB' contains a blank mortality table.
195. QuikPlTv plan '9ADB10' contains a blank mortality table.
196. QuikPlTv plan '9ADB10' contains a blank mortality table.
197. QuikPlTv plan '9ADB10' contains a blank mortality table.
198. QuikPlTv plan '9ADB10' contains a blank mortality table.
199. QuikPlTv plan '9ADB10' contains a blank mortality table.
200. QuikPlTv plan '9ADB10' contains a blank mortality table.
201. QuikPlTv plan '9L01WP' contains a blank mortality table.
202. QuikPlTv plan '9L01WP' contains a blank mortality table.
203. QuikPlTv plan '9L01WP' contains a blank mortality table.
204. QuikPlTv plan '9L01WP' contains a blank mortality table.
205. QuikPlTv plan '9POADB' contains a blank mortality table.
206. QuikPlTv plan '9POADB' contains a blank mortality table.
207. QuikPlTv plan 'A60MIR' contains a blank mortality table.
208. QuikPlTv plan 'A96DAR' contains a blank mortality table.
209. QuikPlTv plan '1SALMI' contains a blank mortality table.
210. QuikPlTv plan '578CTR' contains a blank mortality table.
211. QuikPlTv plan '57ATCR' contains a blank mortality table.
212. QuikPlTv plan '719CDT' contains a blank mortality table.
213. QuikPlTv plan '7647SP' contains a blank mortality table.
214. QuikPlTv plan '9085WP' contains a blank mortality table.
215. QuikPlTv plan '90OLWP' contains a blank mortality table.
216. QuikPlTv plan '90PDTH' contains a blank mortality table.
217. QuikPlTv plan '90POWP' contains a blank mortality table.
218. QuikPlTv plan '910SWP' contains a blank mortality table.
219. QuikPlTv plan '920ADB' contains a blank mortality table.
220. QuikPlTv plan '934JWP' contains a blank mortality table.
221. QuikPlTv plan '934SWP' contains a blank mortality table.
222. QuikPlTv plan '943CWP' contains a blank mortality table.
223. QuikPlTv plan '9595WP' contains a blank mortality table.
224. QuikPlTv plan '960CWP' contains a blank mortality table.
225. QuikPlTv plan '960GIO' contains a blank mortality table.
226. QuikPlTv plan '9665WP' contains a blank mortality table.
227. QuikPlTv plan '967ADB' contains a blank mortality table.
228. QuikPlTv plan '977ADB' contains a blank mortality table.
229. QuikPlTv plan '980JPO' contains a blank mortality table.
230. QuikPlTv plan '982JPO' contains a blank mortality table.
231. QuikPlTv plan '9CDTWP' contains a blank mortality table.
232. QuikPlTv plan '9CTRWP' contains a blank mortality table.
233. QuikPlTv plan '9DIS20' contains a blank mortality table.
234. QuikPlTv plan '9DIS24' contains a blank mortality table.
235. QuikPlTv plan '9DIS25' contains a blank mortality table.
236. QuikPlTv plan '9DIS29' contains a blank mortality table.
237. QuikPlTv plan '9DIS70' contains a blank mortality table.
238. QuikPlTv plan '9DIS80' contains a blank mortality table.
239. QuikPlTv plan '9DIS90' contains a blank mortality table.
240. QuikPlTv plan '9DS24B' contains a blank mortality table.
241. QuikPlTv plan '9DS24C' contains a blank mortality table.
242. QuikPlTv plan '9FTRWP' contains a blank mortality table.
243. QuikPlTv plan '9GPO10' contains a blank mortality table.
244. QuikPlTv plan '9GPO79' contains a blank mortality table.
245. QuikPlTv plan '9JPO10' contains a blank mortality table.
246. QuikPlTv plan '9JPO46' contains a blank mortality table.
247. QuikPlTv plan '9L05WP' contains a blank mortality table.
248. QuikPlTv plan '9L16PF' contains a blank mortality table.
249. QuikPlTv plan '9OLDWP' contains a blank mortality table.
250. QuikPlTv plan '9SLADB' contains a blank mortality table.
251. QuikPlTv plan '9STRWP' contains a blank mortality table.
252. QuikPlTv plan '9WP646' contains a blank mortality table.
253. QuikPlTv plan '9WPL10' contains a blank mortality table.
254. QuikPlTv plan '9085WP' contains a blank mortality table.
255. QuikPlTv plan '90OLWP' contains a blank mortality table.
256. QuikPlTv plan '934SWP' contains a blank mortality table.
257. QuikPlTv plan '9595WP' contains a blank mortality table.
258. QuikPlTv plan '9665WP' contains a blank mortality table.
259. QuikPlTv plan '9L05WP' contains a blank mortality table.
260. QuikPlTv plan '9L16PF' contains a blank mortality table.
261. QuikPlTv plan '9OLDWP' contains a blank mortality table.
262. QuikPlTv plan '9WPL10' contains a blank mortality table.
263. QuikPlTv plan 'A60MIR' contains a blank mortality table.

## What to do next

1. Review each problem listed above with the business owner of the related data.
2. Correct the source QLAdmin data if the finding is valid (this tool does **not** change the data for you).
3. Re-run the governance checks after corrections.

Companion files: `data_governance_validation_guide.md` (what was validated), `data_governance_validation_manifest.json`, `data_governance_findings.csv`, `data_governance_summary.csv`.
