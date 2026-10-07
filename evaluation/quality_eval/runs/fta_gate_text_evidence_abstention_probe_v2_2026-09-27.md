# External Text-Evidence Gate Probe v2 (2026-09-27)

## Purpose and boundary

This is an incremental text-evidence smoke test for the existing FTA gate classifier. It adds one textual AND positive and one new possible-cause-list case containing grammatical `and`, while reusing the four v1 results as the baseline. It does not change production code, a gate threshold, Gold, database state, or readiness flags.

The six combined observations are from six document clusters, but remain a tiny exploratory set. Labels were assigned by the primary AI agent before inference from the quoted evidence and the direct-evidence rule; no human-domain-expert sign-off or independent second-reviewer sign-off was obtained. The model was not shown source identity, expected labels, or review rationale.

## Sources and case definitions

| Case | Source evidence | Expected label | Why |
| --- | --- | --- | --- |
| NASA TP-2000-209902, Fig. 28 explanatory text | “However, both a critical pump failure and a safety system failure to mitigate the failure must occur for a catastrophic fire/explosion to occur.” | AND | The source explicitly requires both supplied child conditions. The quote is on printed p. 49 (PDF page index 63, zero-based). |
| NASA-TM-104382, possible-cause statement | “As possible causes of the capacity decrease, we have observed electrode expansion, rupture and corrosion of the nickel electrode substrate, active material redistribution, and accumulation of electrochemically undischargeable active material with cycling.” | unknown | It lists possible causes and joins list items grammatically, but does not say that any one is sufficient or that all listed items must occur together. |

Both source PDFs were fetched directly in memory from NASA NTRS and checked with text extraction. SHA-256 values are recorded in the [extension fixture](../datasets/fta_gate_text_evidence_abstention_extension_v1.json). Source records: [NASA/TP-2000-209902](https://ntrs.nasa.gov/citations/20000021229) and [NASA-TM-104382](https://ntrs.nasa.gov/citations/19910013920).

## Run result

The existing v1 run had 4 requests (3 unknown, 1 OR); this extension made 2 additional requests. The same `deepseek-flash` model, temperature 0, and unchanged prompt builder were used. Both extension requests succeeded.

| Combined descriptive metric (v1 baseline + 2 extension rows) | Result |
| --- | ---: |
| Top-1 label agreement | 6/6 |
| Unknown retained | 4/4 |
| Unknown falsely accepted as AND/OR | 0/4 |
| Explicit gate positives correct | 2/2 (one OR, one AND) |
| Decisive predictions | 2/6 (33.3%) |
| Decisive quotes that are exact evidence substrings | 2/2 |

The AND prediction quoted `both a critical pump failure and a safety system failure to mitigate the failure must occur`, which is an exact substring of the source-scope evidence. The possible-cause-list row remained `unknown` and returned no gate-evidence quote. Raw extension output: [JSON run artifact](fta_gate_text_evidence_abstention_extension_v1_2026-09-27.json). The baseline raw output remains [v1 JSON](fta_gate_text_evidence_abstention_probe_v1_2026-09-27.json).

These are descriptive counts, not statistically reliable accuracy estimates. The model's self-reported scores are uncalibrated and are not event probabilities or production thresholds. The one AND and one OR example are direct textual controls, not broad paraphrase coverage.

## Verification

- `python -m unittest evaluation.quality_eval.public_sources.test_probe_fta_gate_text_evidence_abstention_v1 -v` — 6 tests passed.
- `python evaluation/quality_eval/public_sources/probe_fta_gate_text_evidence_abstention_v1.py --dataset evaluation/quality_eval/datasets/fta_gate_text_evidence_abstention_extension_v1.json --output evaluation/quality_eval/runs/fta_gate_text_evidence_abstention_extension_v1_2026-09-27.json` — completed; 2/2 requests succeeded.
- PDF SHA-256 and quoted text were checked against direct NASA NTRS PDF downloads; no PDF was copied into the repository.

## Remaining gaps and status

- No human expert Gold; labels are AI-assigned and the extension did not receive a second-agent review.
- Only one AND and one OR positive; no probability calibration, paraphrase robustness, extraction, cause-completeness, recursive-tree, or end-to-end FTA validation.
- No gate policy or confidence threshold was selected. `formal_gold=false`, `database_written=false`, `gate_policy_selected=false`, `fta_ready=false`, and `production_ready=false` remain unchanged.
- The next useful test is not more copies of explicit “both” wording; it is independently sourced direct-AND paraphrases plus unknown/near-miss cases where `and` appears only in list grammar, with all evidence spans checked before inference.
