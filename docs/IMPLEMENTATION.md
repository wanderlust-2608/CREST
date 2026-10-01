# Implementation (v2.1) — how METHODOLOGY.md became working code

This document explains what was built, how to run it, which papers' code was used or re-implemented, how every part
was validated, and **which assumptions of METHODOLOGY v2 turned out to be wrong and were corrected** while building and
testing. Read METHODOLOGY.md for the *why* of each step; this file is the *how* and the *evidence*.

**Package:** `crest/` (Causal Rationale Extraction and Synthesis Toolkit). Pure Python on numpy, pandas, scipy and
scikit-learn. Everything runs offline; every LLM use is optional and has a deterministic fallback.

---

## 1 · What was built

| Step | Module | What it does | Acceptance test (automated) |
|---|---|---|---|
| 0 | `notebooks/01_data_cleaning.ipynb` | cleaning, template groups, locked split, leakage audit, availability registry (built earlier) | 19 integrity checks; `tests/test_cleaning_notebook.py` (14 tests) |
| 1 | `crest/events.py`, `crest/churn.py`, `crest/definitions.py` | event taxonomy with onset rules and exclusion lists; lexicon labeller v2 (default: escalation needs a handoff to a named senior person or an accepted offer; churn adds hedged intent towards competitors or "elsewhere", without prospects, negations or regret) with the v4 hybrid churn detector (disengagement rules plus a semantic layer trained on train-split rule labels) and the secondary retention-risk event (see `docs/REAL_DATA_REVIEW.md` §3 and §7.2) or LLM development sample → quote check → turn-level onset detector (TnT-LLM); blind gold sample from held-out calls with known inclusion probabilities; ingest with validation; inverse-probability-weighted P/R/F1 with CIs, onset accuracy, κ | `test_gold_set_rules`, `test_gold_ingest_rejects_bad_files`, `test_event_rules.py` |
| 2 | `crest/landmarks.py`, `crest/analysis.py` (`RiskSetBuilder`) | landmark rows (call, turn *k*): exclusive cumulative history features from turns before *k* only; the target-trial eligibility rules | `test_build_checks_passed` (future-invariance, bit-identical), `test_risk_sets_follow_the_protocol` |
| 3 | `crest/behaviours.py` | 16 behaviours (14 candidates + 2 negative controls), turn-local detectors, outcome-blindness proofs, precision sheets, co-occurrence and families, optional D5-style LLM proposals | blindness checks; `test_cue_copy_is_in_sync_with_the_notebook` |
| 4 | `crest/analysis.py`, `crest/prereg.py`, `crest/library.py` | pilot on train (learner tuning, planted-effect test, mechanical family rule) → frozen pre-registration (SHA-256) → confirmation once on held-out: cross-fitted AIPW-ATT with template-cluster SEs, trimming, balance, cluster bootstrap, BH, negative controls, E-values, dev/test replication, S1–S8, DSL gold correction → Factor Library with claim levels computed by code | `test_estimator.py` (incl. DoubleML cross-check), `test_prereg_is_enforced`, `test_levels_are_computed_by_code`, `test_known_effects_are_recovered` |
| 5 | `crest/evidence.py` | grounding spans; cross-fitted discrete-time hazard forecaster trained with turn dropout; faithfulness (remove / neutral / random) and ERASER comprehensiveness; AUC and calibration | `test_perturbations_use_the_same_code_path`, `test_evidence_spans_are_before_onset_and_quotable`, `test_evidence_quality_reported` |
| 6 | `crest/index.py`, `crest/graph.py` | Evidence Graph tables with provenance; 5-turn windows over raw dialogue; BM25 + embeddings (sentence-transformers or LSA fallback) → RRF → one window per call → MMR | `test_search_index`, `test_bm25_matches_rank_bm25` |
| 7 | `crest/query.py`, `crest/lexicon.py`, `crest/parser_bench.py` | QuerySpec; brand spans removed before other slots; language identification and phrase tables for Spanish, French, German, Portuguese, Italian and Hindi; corpus-protected spelling correction (Damerau) and slang, each reported in the answer; optional LLM normalisation; a dev/test parser benchmark; call ids (single-call questions); several conditions; "no clear effect"; notices for effect modification, one-call counterfactuals and missing plan, segment or account-age fields; effect and rate thresholds; policy-change dates (clarify, then before/after); conditions between events (*customers who were refused a refund*); behaviour-only questions; allowed filters only (opening-class + unflagged metadata); unsupported attributes (incl. audio, call timing, undetected behaviours, whole-call policies, a second event); declined filters; presuppositions and leading questions; question kinds incl. product / service topics, rankings (optionally "then explain the top group"), behaviours shared by several events, and two events in one call | `test_query_session.py`, `test_query_dataset.py`, `test_robust_questions.py` |
| 8 | `crest/answer.py`, `crest/rationale.py`, `crest/its.py` | evidence pack built by code; a conversation rationale in every answer type (precursors against the same point in calls without the event, customers' own words, one call step by step); condition, before/after (interrupted time series with placebo dates and a comparison series), threshold, tier-proxy, account-field, behaviour-profile, overview and single-call sections; template writer (placeholders only, wording per claim level, quotes from different calls, counter-counts, caveats; rankings, topics customers raise before the event, shared factors, event co-occurrence and order); optional LLM writer | `test_template_answers_always_pass_the_gates`, `test_rationale.py`, `test_robust_questions.py` |
| 9 | `crest/gates.py` | numbers gate, causal-claim licensing gate (Yu et al. categories), evidence gate (exact quotes, raw dialogue only); rewrite → drop → L0 | `test_gates.py` (every adversarial case caught) |
| 10–12 | `crest/session.py` | session state (validated when loaded; an unusable state starts a new conversation with a notice); follow-up → delta → validated deterministic merge; routes reuse / re-filter / new lookup / clarify; *that call / the third example* resolve to the calls quoted in the last answer; cache keyed by library, index and writer versions | `test_followups_keep_unmentioned_filters`, `test_engine_session_and_versioned_cache` |
| 13 | `crest/evaluate.py` | metrics with bootstrap CIs, per category / difficulty / kind of query; known limitations reported separately; baselines B0 (plain retrieval), B2 (free rewriting), B3 (associational); causal validity against a simulator oracle; human-audit sheet and PPI correction; optional LLM judge of the queries (brands masked); `REPORT.md` and the readable `outputs/QUERY_OUTPUTS.md` | `test_query_set_answers`, `test_readable_outputs_and_review_sheet` |
| 14 | `crest/queries.py` | query grid (why / how often / compare / trend / what to change / effect / examples / false premise / leading / unanswerable / declined filter / tiny subgroup / ambiguous / product improvement / ranking / multi-hop / out of scope / conditional / before-after / threshold / behaviour profile / overview / retention risk / single call / noisy text / multilingual / known limitation) + 14 follow-up sessions; tags by task, difficulty, kind and use case; ROUGE-L de-duplication; diversity measures; dev / locked-test split with a hash; `queries.csv` and a human review sheet (see [`QUERY_DATASET.md`](QUERY_DATASET.md)) | `test_locked_test_queries_detect_tampering`, `test_queries_are_organised_by_task_difficulty_kind_and_use_case` |
| — | `crest/simulate.py` | synthetic call centre with a **known causal structure** and an **oracle** that computes the true effect of every behaviour on every event | used by every end-to-end test and by `python -m crest demo` |
| — | `crest/pipeline.py`, `crest/cli.py` | resumable stages with a manifest (hashes of every output) and guards against unsafe order | `test_every_stage_recorded`, `test_confirm_refuses_without_prereg` |
| — | `crest/llm.py` | optional Claude client: JSON-schema outputs, refusal / truncation handling, schema validation, disk cache keyed by prompt hash, call log | `test_llm.py` (fake client + signature check against the installed SDK) |

**Test suite:** `pytest -q tests/` runs 199 tests in about 4 minutes (it simulates a 1,600-call corpus with a causal
oracle, cleans it with the real notebook, runs every stage, and checks the results against the truth). Four
cross-checks against reference packages run when those packages are installed (`pip install -r requirements-optional.txt`),
and the 14 notebook tests need Jupyter's `nbconvert`; otherwise they are skipped. All 199 pass on Python 3.11 (numpy
2.4, pandas 3.0, scikit-learn 1.9); on Python 3.10 with the oldest supported versions (numpy 1.24, pandas 2.0,
scikit-learn 1.2) the 181 tests that do not need the optional tools pass, and both produce the same locked split.

---

## 2 · How to run it on the hackathon data

```bash
pip install -r requirements.txt                       # core: numpy, pandas, scipy, scikit-learn, pyarrow
jupyter nbconvert --to notebook --execute notebooks/01_data_cleaning.ipynb --output 01_data_cleaning.executed.ipynb

python -m crest build                                  # Steps 1-3: labels, behaviours, landmark features, integrity tests
python -m crest gold-sample                            # Step 1e: crest_out/gold/ (blind packets + gold_to_label.csv)
python -m crest precision-sheets                       # Step 3: crest_out/precision/precision_<behaviour>.csv
#   HUMANS: two teammates fill gold_to_label.csv blind (README.txt in that folder), 40 calls double-coded, ADJ rows
#   for disagreements; one teammate fills the 'correct' column of each precision sheet (20 turns each).
python -m crest gold-ingest --file crest_out/gold/gold_to_label.csv
python -m crest pilot                                  # Step 4 phase 1 (train only)
python -m crest prereg                                 # freeze; then COMMIT crest_out/prereg/prereg.json + prereg.sha256
python -m crest confirm                                # Step 4 phase 3: once, on held-out calls -> Factor Library
python -m crest evidence                               # Step 5
python -m crest index                                  # Step 6
python -m crest ask "Why do escalations happen in telecom calls?"
python -m crest ask "what about refunds?" --session my_session.json   # Task 2: the state file carries the context
python -m crest chat                                   # interactive Task 2 session
python -m crest queries                                # Step 14: dev + LOCKED test queries (commit the hash)
python -m crest run-queries                            # outputs/outputs_dev.jsonl, outputs/outputs_test.jsonl
python -m crest evaluate                               # Step 13: eval/metrics.json + REPORT.md
python -m crest status                                 # what is done, what is next
```

* `python -m crest demo --out demo_out` runs the whole thing on a synthetic corpus with known causes (no real data
  needed; it also simulates the human steps). Use it to see what every output looks like.
* Settings live in `crest/config.py`; override any of them with `--config my.json`
  (e.g. `{"estimator": {"n_jobs": 4}}`). Changing an analysis setting after `prereg` makes `confirm` refuse to run.
* Without a gold set the pipeline still runs, but the labeller is unverified, so **no claim can reach L3** (check
  `gold_f1_ok`). Without the precision sheets, `precision_verified` fails likewise. This is intended.
* **Data rules.** Outputs under `crest_out/` contain transcript excerpts. They are git-ignored; share them only as the
  hackathon allows. The LLM backend is off by default; enable it (`--llm`, `llm.backend = "anthropic"`) only if the
  data rules allow sending transcripts to an external API.

---

## 3 · Papers and repositories: used as code, or re-implemented (and how it was validated)

| Method (paper) | Reference code | Decision | Why | Validation |
|---|---|---|---|---|
| DML, ATTE score (Chernozhukov et al. 2018; DoubleML, JMLR 2022) | DoubleML 0.11.4 | **Re-implemented** (`analysis.att_core`) | needed: the DSL-corrected score with risk-set membership, template-cluster standard errors (Chiang et al. 2022), trimming by dropping rows (Crump et al. 2009), deterministic group folds, and per-split replication from the same out-of-fold nuisances | `test_matches_doubleml_on_identical_folds`: identical estimate to `DoubleMLIRM(score="ATTE")` with the same folds and learners (difference < 0.002); `test_att_core_is_the_doubleml_atte_score` |
| DSL (Egami et al., NeurIPS 2023) | `dsl` (R) | **Re-implemented** and **extended** | our estimand needs the gold correction on the risk-set indicator as well as the outcome (see §4, C3); no Python package exists | `test_dsl_is_unbiased_for_the_full_label_estimate` (exact unbiasedness over 300 gold draws), `test_dsl_correction_removes_label_error_bias_end_to_end`, `test_dsl_corrects_risk_set_membership` |
| Target trial / sequential trials (Hernán & Robins 2016; Keogh et al. 2023) | `ruthkeogh/sequential_trials` (R) | design reference | the landmark table is a pandas construction | future-invariance test (bit-identical features after scrambling the future) |
| BM25 (rank_bm25) | `rank_bm25` 0.2.2 | **Re-implemented** on sparse matrices | speed on ~100k windows; identical formula (idf floor = ε·mean idf) | `test_bm25_matches_rank_bm25`: identical scores |
| PPI (Angelopoulos et al., Science 2023) | `ppi_py` | **Re-implemented** (`stats.ppi_mean_ci`, 10 lines) | avoid a heavy dependency | `test_ppi_mean_matches_formula_and_reference_package` (CI equal within 0.002) |
| Sentence-BERT (EMNLP 2019) | `sentence-transformers` | **Used** when installed and the model is available locally; else LSA | offline robustness | backend recorded in the index version |
| RRF (SIGIR 2009), MMR (SIGIR 1998) | — | implemented (a few lines each) | — | `test_search_index` (one hit per call); Recall@10 on synthetic queries |
| TnT-LLM (KDD 2024) | none official | re-implemented (`events.llm_dev_labels`, `train_onset_detectors`) | — | quote check on every LLM onset; gold metrics |
| D5 (NeurIPS 2023) | `ruiqi-zhong/D5` | prompt re-written (`behaviours.propose_with_llm`) | the repo targets older models | proposals are candidates only (never claims) |
| ERASER (ACL 2020) | `jayded/eraserbenchmark` | comprehensiveness re-implemented with a random-removal baseline; sufficiency dropped (Hase et al. 2021) | the benchmark code is tied to its datasets | `test_perturbations_use_the_same_code_path` |
| Yu et al. causal-language categories (EMNLP 2019) | `junwang4/causal-language-use-in-science` | categories used; transparent regex classifier (+ optional LLM) | offline, auditable | `test_gates.py` adversarial set |
| AlignScore (ACL 2023) | `yuh-zha/AlignScore` | **not used**: the evidence gate requires exact quotes, and a sentence that cites turns without quoting must have lexical support ≥ 0.5 (share of its content words found in the cited turns) | needs a 355M-parameter checkpoint and GPU time; exact quoting needs no model | evidence gate tests |
| IC-DST (Findings EMNLP 2022) | `Yushi-Hu/IC-DST` | delta format and few-shot prompt re-implemented; rule-based delta by default | the repo targets MultiWOZ + Codex | carry-over tests; B2 baseline |
| Claude API | `anthropic` SDK | **Used** (optional) | — | request shape checked against the installed SDK 1.9.0 signatures (`betas`, `fallbacks="default"`, `output_config`) |

---

## 4 · Corrections to METHODOLOGY v2 found while building and testing

Each correction was forced by evidence (a failing check, a simulation with a known truth, or an API fact). They are
now part of the method; METHODOLOGY.md §14 lists them too.

| # | v2 said | Problem found | Correction (v2.1) | Evidence |
|---|---|---|---|---|
| C1 | Primary analysis keeps moments after another event (earlier events as covariates); "clean" risk sets are sensitivity S5 | after an escalation the agent's behaviour is often part of the handoff procedure ("please hold" while getting a supervisor) — a different version of the treatment (compound treatment, Hernán & VanderWeele, *Epidemiology* 2011) | **Primary = clean moments** (no other confirmatory event and no supervisor handoff before *k*); S5 = the old primary | on the synthetic oracle, hold → refund/churn was biased (−2 points vs a true +1) in the old primary and correct in the clean analysis |
| C2 | Balance: every covariate's SMD ≤ 0.1 | with ~100 covariates the largest SMD is dominated by sampling noise (≈0.2 at 300 treated rows even with perfect weights); a propensity-score SMD is biased by construction (the weights are a function of it) | gate on the **prognostic-score SMD** (Stuart, Lee & Leacy, *J Clin Epidemiol* 2013); per-covariate SMDs and the propensity SMD are reported, not gated | before: almost every factor "insufficient" although estimates matched the truth; after: prognostic SMD ≤ 0.09 where estimates are right |
| C3 | DSL corrects the outcome | the labeller also decides **which moments are at risk** (a missed escalation leaves post-event rows in the risk set) | the correction is applied to the call-level numerator and denominator of the ATT score (Horvitz–Thompson), which also fixes risk-set membership | exact-unbiasedness test; the corrected estimates match those with perfect labels |
| C4 | Learners: logistic regression or gradient boosting, loss-based choice | the untuned logistic model overfitted (out-of-fold weights left SMDs up to 0.56) and lbfgs was slow and stopped early | regularisation **tuned on train** over a small grid (C, ridge α, boosting shape), chosen by cross-fitted loss and pre-registered; Newton–Cholesky solver (30–70× faster, exact); tuning fits only the model being tuned, on at most 60,000 train rows per behaviour | pilot 274 s → 60 s on 2,500 calls; balance restored |
| C5 | Truncated calls are censored in the main analysis; S3 includes them | the truncation flag covers mostly closing-only truncation (outcome complete), and "follow-up reaches the cut-off" is true for every row of a flagged call | primary treats every transcript as complete; **S3 excludes flagged calls** | — |
| C6 | L3 needs sign stability across S2, S5, S8 | truncation (S3) is a real threat on this corpus | L3 requires **S2, S3, S5 and S8** (`claim.min_sensitivity`) | — |
| C7 | Planted test: bias < 1 point, coverage 90–98%, false alarms ≤ 7% | point thresholds fail by Monte-Carlo noise alone | pass rules allow for Monte-Carlo error (|bias| ≤ max(1 point, 2.5 MC s.e.); Wilson intervals for coverage and false alarms); **100 simulations per pair** | a correct estimator failed the point rule at 60 simulations |
| C8 | Prevalence ≥ 2% of eligible train **rows** | each call contributes many rows and at most one treated row, so common behaviours fall below 2% of rows | ≥ 2% of risk-set **calls** in which the behaviour starts | — |
| C9 | Negative controls: any CI excluding 0 caps the event | with two controls and no multiplicity correction the false-alarm rate is ≈ 10% per event when nothing is wrong | kept (deliberately cautious), but the rate is now stated; slices inherit the event's all-calls control status | 4 fresh synthetic corpora: control "effects" centred on 0 with random signs |
| C10 | "Temperature 0" for reproducibility | current Claude models do not take sampling parameters | reproducibility from a **response cache** keyed by the prompt hash, plus a call log (model, request id, tokens) | SDK / API documentation |
| C11 | Faithfulness: removing the span should lower the forecast | protective behaviours (solution offers) *raise* the forecast when removed | faithfulness is **direction-aware** (sign of the factor's effect) | offers scored 50% before, correctly directional after |
| C12 | L2 = "associated with / warning sign" | an L2 estimate whose CI includes 0 was worded as "associated with a higher chance" | L2 with a CI including 0 is worded **"no clear difference"**; warning signs with a clear direction are ranked first | answer review |
| C13 | behaviour occurrences are counted everywhere | "offer a refund" counted as a solution offer inside a refund episode is part of the event | event-specific occurrence filters (solution offers that mention money are not treatments for REF) | — |
| C14 | cleaning notebook: repeated words are collapsed | "thank you you know for …" collapsed to "thank you know …" and the cue view then deleted "you know", destroying "thank you" | a repeated word whose last copy starts a discourse marker is no longer collapsed (notebook + `crest/cues.py`, kept in sync by a test) | the simulator's turn check caught it; the 14 notebook tests still pass |
| C15 | Pre-registration in YAML | nothing in the stack needs YAML | canonical JSON (`prereg.json`) + `prereg.sha256` | — |
| C16 | Detector precision checked | unverified detectors could still reach L3 | L3 check #11: human precision ≥ 0.8 on ≥ 20 judged turns | — |
| C18 | Planted test: bias within max(1 point, 2.5 MC s.e.) | on one split the estimator showed a real +1.4-point bias (0.30 of its standard error, coverage 0.94, false alarms 0.04) from strongly regularised nuisance models; an absolute 1-point rule ignores the estimator's precision | bias is also allowed up to **0.4 × the median standard error** (standardized bias < 40% is not practically important; Collins, Schafer & Kam, *Psychol Methods* 2001); coverage and false-alarm rules unchanged; the standardized bias is reported | re-run on that split with the diagnostics in `planted_effect_test` |
| C17 | Negative controls: a control that cannot be estimated fails the check | one rare control phrase would veto every L3 claim for an event, although a control too rare to estimate is evidence of nothing | the check needs **at least one estimable control, and every estimable control compatible with 0**; `pilot` warns when no control is estimable on train | `test_negative_control_rule_needs_one_estimable_control` |

### 4b · Failures found by the robustness review, and their fixes

After the method passed on the synthetic oracle, the whole command-line chain was run on inputs built to break it:
the **defect fixture** (`tests/make_synthetic_fixture.py`: the real data's quirks: name labels, analyst notes stored
as turns, embedded dialogues, duplicates, empty calls, heavy template reuse) with **no gold labels and no precision
sheets**; a **20,000-call** corpus (the real one has ~19.6k); and **Python 3.10 with the oldest supported libraries**.
Every failure below was reproduced, fixed and turned into a regression test.

| # | Failure | Cause | Fix | Regression test |
|---|---|---|---|---|
| R1 | `build` crashed on the defect fixture | the notebook keeps empty conversations (flagged `qc_empty`); per-call turn offsets assumed ≥ 1 turn | calls without dialogue turns are set aside at load time and reported (build log, `build_checks.json`, `REPORT.md`) | `test_calls_without_turns_are_set_aside` |
| R2 | one sensitivity analysis took 491 s on 528 rows | gradient boosting parallelises every tiny tree with OpenMP threads that spin-wait; with another process on the CPU each fit stalled (100 s vs 0.45 s single-threaded) | every nuisance fit runs single-threaded (`estimator.threads_per_fit = 1`); parallelism comes from `n_jobs` across folds. Execution settings are excluded from the pre-registration hash | `test_thread_settings_do_not_change_the_preregistration_hash` |
| R3 | the planted-effect test silently did not run on a small corpus | its 20% train subsample had too few treated moments; the log printed `nan` | the subsample grows (20% → 50% → all) until it holds ≥ 20 treated moments; if the test still cannot run, `pilot` and `REPORT.md` say so and why (and no claim can reach L3) | defect-fixture run |
| R4 | `run-queries` and `evaluate` crashed without a gold set | missing values are stored as JSON `null`; code read them with `.get(key, {})` and formatted `None` | `None`-safe reads; every number in `REPORT.md` goes through one formatter that prints `n/a` | `test_report_numbers_tolerate_missing_values` |
| R5 | "effect of X" questions about a factor with no reliable estimate (L1) degraded to "cannot answer reliably" | the L1 sentence was not a core sentence and promised counts it did not show | L1 answers give the reasons in plain words (numbers only via checked placeholders) and the counts; "why" answers say "counts only" when nothing reaches L2; a quote is used at most once per answer | `test_effect_question_about_a_factor_without_estimate_gives_counts` |
| R6 | questions about a negative control were answered as if about something else | the parser ignored control behaviours | controls are recognised and the answer says what they are for | `test_question_about_a_negative_control_says_so` |
| R7 | the same corpus got a **different locked split** on another machine | the notebook's MinHash grouping used `datasketch`, whose hashing changed between versions 1.6 and 2.0, and accepted pairs on the MinHash estimate | MinHash-LSH is implemented in the notebook (SHA-1 shingles, frozen `RandomState` permutations) and every link is confirmed with the **exact** Jaccard similarity; identical splits on Python 3.10 / numpy 1.24 / pandas 2.0 and Python 3.11 / numpy 2.4 / pandas 3.0. The corpus fingerprint frozen into the pre-registration now includes a hash of the split, so a changed split stops `confirm` | notebook tests; both test environments |
| R9 | the planted-effect test produced no result on the defect fixture, so no claim could ever reach L3 | it tested the behaviours with the most treated moments; the top one (hold requests) happens in every call at the same point, so no comparable moment without it exists and every simulated dataset was non-estimable | the test uses behaviours that are estimable with enough overlap (the pool the confirmatory family comes from); a behaviour whose simulated datasets are mostly non-estimable is set aside with the reason; if the most frequent behaviours are unusable, the learner is re-tuned on usable ones (recorded in `pilot.json`) | defect-fixture `run-all`: test runs on solution offers and passes |
| R10 | an estimate of +100.1 points on a near-deterministic pair | the linear outcome model predicted below 0 for some moments, and the doubly robust estimator is not bounded | the outcome model's predictions are clipped to [0, 1] (the outcome is binary, so this can only move each prediction closer to the truth); switchable (`estimator.outcome_clip`) so the DoubleML comparison stays exact | `test_att_core_is_the_doubleml_atte_score`, `test_matches_doubleml_on_identical_folds` |
| R8 | the first self-contained grouping took > 4 minutes on 20,000 calls | it checked every LSH candidate pair (8.5 million on this heavily templated corpus) in a Python loop | only the connected components are needed: candidates are taken in descending order of their MinHash estimate, pairs already connected are skipped, and the remaining exact Jaccard values are computed in vectorised blocks from a sparse call × shingle matrix: 34 s, same groups as checking every candidate | equivalence check against checking every candidate at four thresholds |
| R11 | an audit of the query set against the brief: 8 of 12 hand-written probe questions were answered as a different question without saying so ("which industry has the highest escalation rate?" got the overall causal answer; "does sarcasm make customers threaten to cancel?" ignored sarcasm; "do escalations lead to refund requests?" answered about escalations only) | the parser always produced *some* answerable question; parts it could not map were dropped silently | notices for everything the data cannot answer (call timing, audio, undetected behaviours, whole-call policies, a second event left out, relative dates); new question kinds with their own descriptive or multi-hop answers (product / service topics, rankings with an optional "explain the top group" hop, behaviours shared by several events, co-occurrence and order of two events); a comparison without groups asks which groups; questions that still fail are kept as a separately reported *known limitation* category ([`QUERY_DATASET.md`](QUERY_DATASET.md)) | `test_questions_that_used_to_be_answered_as_something_else`, `test_new_categories_answered_as_expected` |

---

## 5 · Validation against a known truth (synthetic corpus with a causal oracle)

`crest/simulate.py` generates calls in the raw file format from invented dynamics: a latent frustration score that
agent behaviour moves (refusals raise it, solution offers lower it) and that drives escalation, refund and churn
hazards; confounding that changes over the call; two behaviours with **no** effect (negative controls); paraphrased
events the lexicon misses. For every first occurrence of a behaviour it continues the call 80 times with the behaviour
forced on and off (common random numbers): the average difference is the **true ATT** of the landmark design.

Results of `python -m crest demo` (4,000 calls, seed 11; the full pipeline including the real cleaning notebook and
simulated blind gold labels). Every output is in [`examples/synthetic_demo/`](../examples/synthetic_demo/):

| Check | Result |
|---|---|
| 95% CIs covering the true ATT | 12 of 12 factors with an oracle |
| Mean absolute error | 0.015 (system) vs 0.054 (associational baseline B3); paired difference 0.038 (95% CI 0.017–0.066) |
| L3 claims | 5, all with the right sign and none on the wrong side of the truth: refusal → escalation +32.2 points (true +30.9); solution offer → escalation −31.5 (−28.9); hold request → escalation +8.6 (+6.2); solution offer → refund −15.9 (−12.7); solution offer → churn −7.7 (−8.7) |
| Negative controls | all 6 CIs include 0; none shown as a claim |
| Planted-effect test | passed (bias −0.007, 26% of the typical standard error, allowed 40%; coverage 0.94; false alarms 0.06) |
| Labeller vs blind gold | F1 0.995 / 1.00 / 1.00 (ESC / REF / CHURN); the churn semantic layer added no turns here (the simulated threats are all caught by the rules) |
| Forecaster | AUC 0.93 / 0.87 / 0.89; calibration slopes 1.05–1.09 |
| Retrieval | Recall@10 0.94 (18 queries with known relevant calls) |
| Query set (98 queries: 85 single questions + 13 follow-up sessions; 126 questions with the turns) | expected behaviour met 100% of dev and locked-test questions, in every category including noisy, multilingual, conditional, before/after, threshold, profile, overview, retention-risk and single-call questions; 0 sentences removed by the gates; 0 degraded answers; follow-up carry-over and route accuracy 100% vs 13–37% carry-over for free rewriting (B2); plain retrieval (B0) corrects 0% of false premises; the 4 known limitations are reported separately (0 handled as an ideal system would — see [`QUERY_DATASET.md`](QUERY_DATASET.md) §5) |

The defect fixture (no gold labels, heavy template reuse) and 20,000 calls: see §4b and §6.

---

## 6 · Scale and runtime

The real corpus has ~19.6k calls. A synthetic corpus of **20,000 calls** (380,140 turns; 300,140 landmark rows × 117
features) went through every stage of the v4 code on 4 CPU cores with the default settings (`n_jobs = 1`, 2,000
bootstrap draws, 100 planted simulations per behaviour), all stages in one Python process (`python -m crest demo
--n-calls 20000`):

| Stage | Time | Peak memory |
|---|---|---|
| simulation, cleaning notebook, `gold-sample`, `precision-sheets`, `gold-ingest` | 322 s | 3.9 GB (notebook kernel) |
| `build` (labels incl. the churn semantic layer, behaviours, landmark features, integrity tests) | 69 s | 4.9 GB |
| `pilot` (tuning, train estimates, planted-effect test) | 1,293 s | 4.9 GB |
| `prereg` | < 1 s | 4.9 GB |
| `confirm` (29 estimates with sensitivity analyses, industry slices) | 1,288 s | 4.9 GB |
| `evidence` (forecaster on all turns, grounding spans, faithfulness) | 288 s | 4.9 GB |
| `index` (120,350 windows) | 40 s | 4.9 GB |
| `queries`, `run-queries` (98 queries, 0.06 s per answer), `evaluate` | 16 s | 4.9 GB |
| **total** | **about 55 minutes** | **4.9 GB** |

The pilot chooses the outcome and propensity learners by cross-validated loss on the train split. Here it chose the
gradient-boosting learner, which is much slower to fit than the logistic learner it chose for the 4,000-call demo;
the first 20,000-call test, on an earlier version, took about 17 minutes in all. The learner choice is part of the
frozen plan. Run as separate commands (`python -m crest <stage>`), each stage releases its memory when it
ends. Setting `{"estimator": {"n_jobs": 4}}` in a `--config` file runs the cross-fitting folds in parallel; results do
not change.

Quality at this size: the planted-effect test passed (bias +0.003, 22% of the typical standard error; coverage 0.95);
6 L3 claims, all with the right sign and none on the wrong side of the truth; mean absolute error 0.011 vs 0.041 for
the associational baseline; the event labeller matched the simulator's truth on every call (the simulated gold
annotators' own mistakes put the gold-sample churn F1 at 0.97); retrieval Recall@10 0.93; every query answered as
expected with 0 degraded answers, and every follow-up carried its context. **11 of 12** intervals covered the true
effect. The miss is refusal → refund (truth +2.5 points, estimate −0.0, 95% CI −2.2 to +2.1): an L2 "no clear
difference" estimate, not a claim. In the first 20,000-call test, outcome label error (the lexicon then missed 5–10% of
simulated events) pulled the refusal and solution-offer effects 1–4 points toward zero; with the v2 labeller there is no
label error left on synthetic data, and the remaining miss is ordinary sampling variation (one in twelve 95%
intervals). The lesson for the real data is in §7.

---

## 7 · What people still have to do on the real data

1. Run the cleaning notebook and read its checklist (METHODOLOGY Step 0 acceptance test).
2. Label the gold sample **blind** (two people for the 40 double-coded calls; resolve disagreements with ADJ rows).
   On ~20k calls the label-error correction, not the estimator, limits precision (§6). If time allows, raise
   `gold.n_random` so that 300–400 calls are labelled; the correction then needs fewer lucky draws to remove the
   labeller's bias. Do this **before** `prereg`: the gold sample may not be redrawn after freezing.
3. Fill the precision sheets (20 turns per behaviour; only the turn and the two before it are shown).
4. Commit `prereg.json` and `prereg.sha256` **before** `confirm`; commit `queries_test.jsonl` and its hash before tuning.
5. Review the generated queries in `queries/queries_review.csv` (realistic? relevant? right category? keep / edit / drop;
   optionally triaged first by `evaluate --llm`), rebuild them with `queries --force` **before** running the test split,
   and score the 30 answers in `eval/human_audit.csv`; add judge scores for all answers to get the PPI-corrected score.
6. Read answers before business decisions — the gates constrain wording, not judgement.

## 8 · Limits

The limits of METHODOLOGY §13 stand: unmeasured confounding (probed by E-values and negative controls), single-turn
decisions not policies, this corpus only, text only, label error corrected on average (timing probed by S8), and
LLM prose only when enabled — gated, but still to be read by a person.
