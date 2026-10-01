# CREST evaluation report

Generated 2026-10-01 09:29 from `demo_out/crest_out`. Every number below is computed by `crest/evaluate.py` from the stored outputs; confidence intervals are bootstrap intervals.

## 1. Data and design checks

* Landmark rows: 59,857 with 117 history features.
* Future-invariance test: 0 failures in 1000 rows.
* Outcome-blindness of behaviour detectors: passed.
* Leakage-flagged metadata columns (never used): none.
* Calls without dialogue turns set aside: 0.

## 2. Event labels (blind gold set, inverse-probability weighted)

| Event | Precision | Recall | F1 (95% CI) | Onset within 1 turn | kappa |
|---|---|---|---|---|---|
| ESC | 0.991 | 1.000 | 0.995 (0.985–1.000) | 1.00 | 1.00 |
| REF | 1.000 | 1.000 | 1.000 (1.000–1.000) | 1.00 | 1.00 |
| CHURN | 1.000 | 1.000 | 1.000 (1.000–1.000) | 1.00 | 1.00 |

## 3. Causal pipeline

* Planted-effect test: passed = True; bias -0.0074 (MC s.e. 0.0028; -26% of the typical standard error, allowed 40%); coverage 0.94; null false-alarm rate 0.06 over 200 simulations.
* Pre-registration: sha256 `61c6938f907358ec5fa216ade288af3d856b6ea2fd5ba26ad0a6968909a72cab`; intact = True.
* Negative controls (95% CI):
  * ESC × nc_readback: +3.0 points (-2.8 to +8.8)
  * ESC × nc_thanks_info: +0.7 points (-5.2 to +6.6)
  * REF × nc_readback: -2.3 points (-8.1 to +3.6)
  * REF × nc_thanks_info: -1.7 points (-7.1 to +3.8)
  * CHURN × nc_readback: -1.3 points (-5.8 to +3.1)
  * CHURN × nc_thanks_info: +0.9 points (-3.3 to +5.0)
* Claim levels (all calls): {"CHURN": {"L1": 2, "L2": 5, "L3": 1, "NC": 2}, "ESC": {"L1": 1, "L2": 5, "L3": 3, "NC": 2}, "REF": {"L1": 2, "L2": 6, "L3": 1, "NC": 2}}

| Factor | Event | Behaviour | Level | ATT (points) | 95% CI | q | E-value | Failed checks |
|---|---|---|---|---|---|---|---|---|
| F1 | ESC | offer_solution | L3 | -31.5 | -37.8 to -25.2 | 0.000 | 4.41 | — |
| F2 | ESC | refusal | L3 | +32.2 | +26.6 to +37.7 | 0.000 | 3.16 | — |
| F3 | ESC | hold_request | L3 | +8.6 | +2.6 to +14.5 | 0.020 | 1.70 | — |
| F4 | ESC | repeat_question | L2 | +7.9 | -0.2 to +15.9 | 0.139 | 1.64 | actionable, bh_significant, bootstrap_excludes_zero, sensitivity_stable, precision_verified |
| F5 | ESC | confusion | L2 | +12.2 | +3.0 to +21.3 | 0.034 | 1.88 | actionable, precision_verified |
| F6 | ESC | empathy | L2 | -2.6 | -8.0 to +2.7 | 0.480 | 1.29 | bh_significant, bootstrap_excludes_zero, sensitivity_stable, dev_test_agree |
| F7 | ESC | competitor_mention | L2 | +2.6 | -4.9 to +10.2 | 0.583 | 1.29 | actionable, bh_significant, bootstrap_excludes_zero, sensitivity_stable, dev_test_agree, precision_verified |
| F8 | ESC | hesitation | L2 | -0.1 | -16.2 to +15.9 | 0.987 | 1.05 | actionable, support_sufficient, bh_significant, bootstrap_excludes_zero, sensitivity_stable, dev_test_agree, precision_verified |
| F10 | REF | offer_solution | L3 | -15.9 | -22.0 to -9.9 | 0.000 | 3.80 | — |
| F11 | REF | empathy | L2 | +5.1 | +0.1 to +10.1 | 0.128 | 1.79 | bh_significant, sensitivity_stable |
| F12 | REF | repeat_question | L2 | +6.0 | -2.5 to +14.5 | 0.310 | 1.97 | actionable, bh_significant, bootstrap_excludes_zero, sensitivity_stable, precision_verified |
| F13 | REF | hold_request | L2 | +2.8 | -2.5 to +8.1 | 0.457 | 1.50 | bh_significant, bootstrap_excludes_zero, sensitivity_stable, dev_test_agree |
| F14 | REF | refusal | L2 | +2.2 | -3.0 to +7.4 | 0.524 | 1.41 | bh_significant, bootstrap_excludes_zero, sensitivity_stable |
| F15 | REF | confusion | L2 | +4.3 | -4.7 to +13.3 | 0.480 | 1.69 | actionable, bh_significant, bootstrap_excludes_zero, sensitivity_stable, dev_test_agree, precision_verified |
| F16 | REF | competitor_mention | L2 | +0.3 | -7.2 to +7.8 | 0.978 | 1.13 | actionable, bh_significant, bootstrap_excludes_zero, sensitivity_stable, dev_test_agree, precision_verified |
| F19 | CHURN | offer_solution | L3 | -7.7 | -11.6 to -3.8 | 0.001 | 3.84 | — |
| F20 | CHURN | refusal | L2 | +4.1 | +0.2 to +8.0 | 0.128 | 2.05 | bh_significant, sensitivity_stable |
| F21 | CHURN | repeat_question | L2 | +4.7 | -0.3 to +9.7 | 0.139 | 2.72 | actionable, bh_significant, bootstrap_excludes_zero, sensitivity_stable, precision_verified |
| F22 | CHURN | hold_request | L2 | +2.9 | -1.4 to +7.1 | 0.328 | 1.89 | bh_significant, bootstrap_excludes_zero, sensitivity_stable |
| F23 | CHURN | empathy | L2 | +0.8 | -3.3 to +5.0 | 0.782 | 1.34 | bh_significant, bootstrap_excludes_zero, sensitivity_stable |
| F24 | CHURN | confusion | L2 | +2.3 | -3.8 to +8.5 | 0.568 | 1.86 | actionable, support_sufficient, bh_significant, bootstrap_excludes_zero, sensitivity_stable, precision_verified |

### Recovery of known effects (synthetic corpus with a causal oracle)

* CI coverage of the true ATT: 100.0% (95% CI 100.0%–100.0%, n=12) over 12 factors with an oracle.
* Mean absolute error: system 0.015 (95% CI 0.011–0.021, n=12); associational baseline B3 0.054 (95% CI 0.032–0.081, n=12); paired difference (B3 − system) 0.038 (95% CI 0.017 to 0.066).
* L3 claims: 5; sign correct 100%; L3 claims whose CI excludes the true effect on the wrong side: 0.

| Event | Behaviour | Level | Truth | Estimate (95% CI) | Naive (B3) |
|---|---|---|---|---|---|
| ESC | offer_solution | L3 | -28.9 | -31.5 (-37.8 to -25.2) | -36.6 |
| ESC | refusal | L3 | +30.9 | +32.2 (+26.6 to +37.7) | +46.9 |
| ESC | hold_request | L3 | +6.2 | +8.6 (+2.6 to +14.5) | +17.3 |
| REF | offer_solution | L3 | -12.7 | -15.9 (-22.0 to -9.9) | -16.1 |
| REF | hold_request | L2 | +1.1 | +2.8 (-2.5 to +8.1) | +6.8 |
| REF | refusal | L2 | +3.1 | +2.2 (-3.0 to +7.4) | +10.6 |
| CHURN | offer_solution | L3 | -8.7 | -7.7 (-11.6 to -3.8) | -7.6 |
| CHURN | refusal | L2 | +4.2 | +4.1 (+0.2 to +8.0) | +8.8 |
| CHURN | hold_request | L2 | +1.0 | +2.9 (-1.4 to +7.1) | +4.5 |
| ESC | nc_thanks_info | NC | +0.0 | +0.7 (-5.2 to +6.6) | -1.9 |
| REF | nc_thanks_info | NC | +0.0 | -1.7 (-7.1 to +3.8) | -0.2 |
| CHURN | nc_thanks_info | NC | +0.0 | +0.9 (-3.3 to +5.0) | +1.7 |

## 4. Evidence (forecaster: faithfulness only, never causal)

* ESC: AUC next turn 0.934 (0.922–0.945); within 3 turns 0.851; calibration slope 1.05; ECE 0.004.
* REF: AUC next turn 0.871 (0.856–0.885); within 3 turns 0.760; calibration slope 1.09; ECE 0.004.
* CHURN: AUC next turn 0.891 (0.871–0.910); within 3 turns 0.792; calibration slope 1.06; ECE 0.003.
* Comprehensiveness minus random baseline, ESC: +0.056 (+0.038 to +0.076), 255 calls.
* Comprehensiveness minus random baseline, REF: -0.011 (-0.024 to +0.001), 137 calls.
* Comprehensiveness minus random baseline, CHURN: +0.009 (+0.001 to +0.017), 97 calls.

## 5. Retrieval

* Recall@10 0.939 (95% CI 0.883–0.983); nDCG@10 0.935; 18 queries.

## 6a. Answers — dev queries (53 single questions, 9 sessions)

* Expected behaviour met: 100.0% (95% CI 100.0%–100.0%, n=53).
* Slot accuracy: event 100.0% (95% CI 100.0%–100.0%, n=47); question type 100.0% (95% CI 100.0%–100.0%, n=35); filters 100.0% (95% CI 100.0%–100.0%, n=7).
* Gates: 0 of 880 sentences dropped ({"numbers": 0, "causal": 0, "evidence": 0}); degraded answers 0; wording violations after gates 0.
* Follow-ups: carry-over 100.0% (95% CI 100.0%–100.0%, n=28); route accuracy 100.0% (95% CI 100.0%–100.0%, n=19).
* Baseline B2 (free rewriting) carry-over: 36.8% (95% CI 15.8%–57.9%, n=19).
* Baseline B0 (plain retrieval): premises corrected 0.0% (95% CI 0.0%–0.0%, n=6); unsupported attributes flagged 0.0% (95% CI 0.0%–0.0%, n=6); absolute error of rates from search hits 0.186 (95% CI 0.106–0.266, n=2).
* Seconds per answer: median 0.047, p95 0.087.
* Known limitations (kept out of every score above; see 6c): 0 of 3 handled as an ideal system would.

| Category | Share as expected | n |
|---|---|---|
| ambiguous | 100% | 2 |
| before_after | 100% | 2 |
| behaviour_profile | 100% | 1 |
| compare | 100% | 1 |
| conditional | 100% | 2 |
| effect_of | 100% | 2 |
| examples | 100% | 1 |
| false_presupposition | 100% | 3 |
| how_often | 100% | 2 |
| leading | 100% | 1 |
| multi_hop | 100% | 2 |
| multilingual | 100% | 4 |
| noisy_text | 100% | 3 |
| out_of_scope | 100% | 5 |
| overview | 100% | 1 |
| product_improvement | 100% | 2 |
| ranking | 100% | 2 |
| retention_risk | 100% | 1 |
| single_call | 100% | 2 |
| threshold | 100% | 2 |
| tiny_subgroup | 100% | 1 |
| trend | 100% | 1 |
| true_premise | 100% | 2 |
| unanswerable | 100% | 3 |
| unsupported_filter | 100% | 1 |
| what_to_change | 100% | 1 |
| why | 100% | 3 |

| Difficulty | Share as expected | n |
|---|---|---|
| easy | 100% | 7 |
| hard | 100% | 18 |
| medium | 100% | 28 |

| Kind of query | Share as expected | n |
|---|---|---|
| ambiguous | 100% | 2 |
| cannot_answer | 100% | 10 |
| evidence_lookup | 100% | 2 |
| impact_evaluation | 100% | 2 |
| multi_hop | 100% | 14 |
| premise_check | 100% | 6 |
| robustness | 100% | 7 |
| simple_retrieval | 100% | 10 |

## 6b. Answers — test queries (28 single questions, 4 sessions)

* Expected behaviour met: 100.0% (95% CI 100.0%–100.0%, n=28).
* Slot accuracy: event 100.0% (95% CI 100.0%–100.0%, n=24); question type 100.0% (95% CI 100.0%–100.0%, n=21); filters 100.0% (95% CI 100.0%–100.0%, n=5).
* Gates: 0 of 462 sentences dropped ({"numbers": 0, "causal": 0, "evidence": 0}); degraded answers 0; wording violations after gates 0.
* Follow-ups: carry-over 100.0% (95% CI 100.0%–100.0%, n=12); route accuracy 100.0% (95% CI 100.0%–100.0%, n=9).
* Baseline B2 (free rewriting) carry-over: 12.5% (95% CI 0.0%–37.5%, n=8).
* Baseline B0 (plain retrieval): premises corrected 0.0% (95% CI 0.0%–0.0%, n=3); unsupported attributes flagged 0.0% (95% CI 0.0%–0.0%, n=3); absolute error of rates from search hits 0.047 (95% CI 0.047–0.047, n=1).
* Seconds per answer: median 0.047, p95 0.089.
* Known limitations (kept out of every score above; see 6c): 0 of 1 handled as an ideal system would.

| Category | Share as expected | n |
|---|---|---|
| ambiguous | 100% | 1 |
| before_after | 100% | 1 |
| behaviour_profile | 100% | 1 |
| compare | 100% | 1 |
| conditional | 100% | 1 |
| effect_of | 100% | 1 |
| examples | 100% | 1 |
| false_presupposition | 100% | 2 |
| how_often | 100% | 1 |
| multi_hop | 100% | 1 |
| multilingual | 100% | 2 |
| noisy_text | 100% | 1 |
| out_of_scope | 100% | 2 |
| overview | 100% | 1 |
| product_improvement | 100% | 1 |
| ranking | 100% | 1 |
| retention_risk | 100% | 1 |
| single_call | 100% | 1 |
| threshold | 100% | 1 |
| trend | 100% | 1 |
| true_premise | 100% | 1 |
| unanswerable | 100% | 1 |
| what_to_change | 100% | 1 |
| why | 100% | 2 |

| Difficulty | Share as expected | n |
|---|---|---|
| easy | 100% | 5 |
| hard | 100% | 8 |
| medium | 100% | 15 |

| Kind of query | Share as expected | n |
|---|---|---|
| ambiguous | 100% | 1 |
| cannot_answer | 100% | 3 |
| evidence_lookup | 100% | 1 |
| impact_evaluation | 100% | 1 |
| multi_hop | 100% | 9 |
| premise_check | 100% | 3 |
| robustness | 100% | 3 |
| simple_retrieval | 100% | 7 |

## 6c. The query set

* 98 queries (126 questions with the session turns); every answer is in `outputs/QUERY_OUTPUTS.md`; the list is in `queries/queries.csv` and the human review sheet in `queries/queries_review.csv`.
* Task: task1 85, task2 13.
* Difficulty: easy 12, hard 33, medium 53.
* Kind of query: ambiguous 3, cannot_answer 13, evidence_lookup 3, follow_up 13, impact_evaluation 3, known_limitation 4, multi_hop 23, premise_check 9, robustness 10, simple_retrieval 17.
* Use case: evidence_lookup 2, follow_up 13, guardrail 22, hypothesis_test 9, impact_evaluation 3, monitoring 7, process_improvement 2, product_improvement 3, robustness 10, root_cause 18, segment_comparison 5, stress_test 4.
* Diversity: distinct-1 0.32, distinct-2 0.62; mean pairwise ROUGE-L 0.07 (max 1.00); distinct expected-slot combinations 71% of questions; evenness (normalised entropy) of categories 0.95, difficulty 0.87, events 0.84.
* LLM judge: not run (optional; `python -m crest evaluate --llm`).

Known limitations (questions the system handles badly, shown with what it did):

| Query | Question | Ideal behaviour | What the system did | Why |
|---|---|---|---|---|
| q082 | Kwa nini wateja wanaomba msimamizi? | answer | asked to clarify | languages outside the built-in word lists (here Swahili) are read only when an LLM is configured; without one the system asks the user to rephrase |
| q083 | Does empathy reduce escalations only when the customer is already frustrated? | estimate_modification | answered a 'effect_of' question about ESC; notices: effect modification | effects are estimated over all comparable moments together; an effect within calls where something else already happened (effect modification) is not estimated, so the overall estimate is given with a notice |
| q084 | Why did escalations go up in hotel calls but not in airline calls? | answer_contrast | answered a 'why' question about ESC with filters {"industry": ["hospitality"]} | a contrast between two slices inside a why-question is answered for the first slice only; the second slice is read as an exclusion |
| q085 | If agents had offered a solution earlier in this call, would the customer still have escalated? | answer_counterfactual | answered a 'effect_of' question about ESC; notices: single-call counterfactual | counterfactuals about one specific call are not estimated: estimates describe calls in general, and one call's outcome under a different agent action is not identifiable from the data |

## 7. Human audit and judge

* Status: human audit incomplete (0 human scores) or no judge scores for all answers. Fill `eval/human_audit.csv` (30 test answers); judge scores from a different model family go in `judge_score_0_1`; the PPI-corrected score is then computed by `crest evaluate`.

## 8. Limits (stated in every report)

1. Unmeasured confounding: estimates assume the history before each moment captures what drives both the behaviour and the event; E-values and negative controls probe this.
2. Single-turn decisions, not policies.
3. This corpus only.
4. Text only (no audio or timestamps).
5. Label error is corrected on average by DSL; onset timing is probed by S8.
6. Wording is gated, but a human should read answers before business decisions.
