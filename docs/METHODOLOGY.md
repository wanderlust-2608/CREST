# Methodology (v2.1) — how the system works, step by step

**Project:** Causal Rationale Extraction and Synthesis from Conversational Data on Business Events (Task 1 and Task 2)

**Version:** v2, 29 Sep 2026. It replaces v1 (commit `2cf5eb3`) after a line-by-line review of v1's loopholes. [§0](#0--what-changed-from-v1) lists what changed. [§8](#8--verdict-on-the-35-review-points) gives a verdict on each of the 35 review points, and [§9](#9--additional-loopholes-found-and-closed) lists 25 more loopholes we found.

**Status:**
* **Step 0 is built and tested** in [`notebooks/01_data_cleaning.ipynb`](../notebooks/01_data_cleaning.ipynb). It covers data cleaning, template groups, the locked split, the metadata leakage audit and the column-availability registry. It passes 19 built-in integrity checks and 14 end-to-end tests, with identical results on pandas 2.2 and 3.0 (JSON/CSV byte-identical; parquet contents identical).
* **Steps 1–14 are built and tested** in the `crest` package (`python -m crest …`). Each step ends with an **acceptance test**; each test is automated (`pytest -q tests/`, 116 tests). A step's output may be used only after its test passes.
* **v2.1 corrections.** Building and testing the system against a synthetic corpus with a *known* causal truth exposed 16 places where v2 was wrong or under-specified. They are corrected in the text below and listed with their evidence in [§14](#14--corrections-made-while-building-v21). How each step maps to code, which papers' code was used or re-implemented, and the validation results are in [`IMPLEMENTATION.md`](IMPLEMENTATION.md).

**Companion documents:**
* [`DATA_CLEANING.md`](DATA_CLEANING.md) — details of Step 0.
* [`LITERATURE_REVIEW.md`](LITERATURE_REVIEW.md) — the wider reading list. Where it disagrees with this document, this document wins.

**How the papers were chosen.**
* Only top conferences and journals, each checked on the publisher's or proceedings' page (28–29 Sep 2026).
* Each step still has **one main paper** and at most **one supporting paper**.
* A few extra "safeguard" papers are cited once each, only where they justify a specific check (for example, the overlap rule or the E-value).
* The 26 papers from the team's list are checked one by one in [Appendix A](#appendix-a--verification-of-the-26-papers-from-the-teams-list).

---

## 0 · What changed from v1

| Area | v1 | v2 | Why |
|---|---|---|---|
| Headline principle | "The AI proposes and writes; statistics and deletion tests decide." | **"The AI proposes and synthesizes; statistical identification and predefined validation tests constrain what can be claimed."** | Deletion tests measure *model faithfulness*, not real-world causes. DML gives a causal estimate only under stated assumptions. |
| Train/dev/test split | hash of the near-duplicate cluster | hash of the **template group**, locked before any labelling (built) | Near-identical templated calls in train and test inflate results (EACL 2021). |
| Metadata (`intent`, `reason_for_call`, `domain`) | `intent` used to form comparison groups | **Leakage audit** plus a **column-availability registry** (built). Metadata stays out of the main causal model. | `reason_for_call` may be a summary written after the call, so it could contain the answer. |
| Step 2 comparison groups | before-event windows; controls cut at a point borrowed from event calls; matched on total length | **Landmark risk sets** (sequential target trials). At every turn *k*, compare calls that are still event-free, using only what was said before *k*. | v1 used the outcome to choose controls, and matched on a length only known at the end. Both bias the result. |
| Treatment (the possible cause) | "the behaviour happens somewhere in the window" | "the behaviour **first happens at turn *k***" vs "not at turn *k*", written up in an **estimand card** | A cause must be a well-defined intervention (review point 11). |
| Step 4 output | effect + error bar | effect + **claim level L0–L3**, computed by code from predefined checks | It is impossible to over-claim by hand. |
| Step 5 | "proof lines" via deletion (necessary and sufficient) | **grounding spans** (the behaviour happens here) + a separate **faithfulness score** against a random-turn baseline; no "keep only this line" test | ERASER measures faithfulness to a model. Deleting text creates inputs the model never saw (NeurIPS 2021). |
| Events | escalation / refund / churn / product | explicit taxonomy with onset rules and **event-definition exclusion lists** | circular definitions (point 16); mixed outcome types (point 17) |
| Labels | LLM sample → classifier; 150 gold calls, which could overlap the LLM sample | LLM development sample from **train only**. Gold labels from **held-out calls only**, stratified with known sampling rates, labelled blind. **DSL correction** of label error. | point 21 (overlap); point 22 (prevalence); label error biases effects |
| Answer checking | AlignScore on each sentence | **three gates**: numbers (placeholders filled by code), causal-claim licensing (wording ≤ claim level), evidence (exact quotes + AlignScore) | AlignScore cannot verify a causal claim or a number (point 29). |
| Task 2 follow-ups | LLM rewrites the whole question | **state + delta**: the LLM proposes only the change; code merges it and validates filters; a minimum-support policy applies | Rewrites can silently drop filters (point 32); tiny subgroups get fake estimates (point 33). |
| Evaluation | query set + LLM judge | **locked test queries**, baselines, ablations, a judge from a different model family, a human audit, confidence intervals | points 7, 30 and 31 |

---

## 1 · The problem in plain words

A company recorded about **19,600 phone calls** between customer-service agents and customers, and turned them into text. Some calls end badly:

* the customer demands a supervisor (**escalation**);
* the customer wants money back (**refund**);
* the customer threatens to leave (**churn**).

Managers want to ask *"Why are escalations happening?"*. They want an answer that:

* separates **what the data can show is a likely cause** from **what merely happens at the same time**;
* shows **proof**: the exact lines of real calls;
* handles **follow-up questions** such as *"what about refunds?"* or *"only for airline calls"*.

Nobody labelled which calls escalated, when, or why, so the system has to work that out. It must also be honest about how sure it is.

## 2 · The core principle and the claim ladder

> **The AI proposes and synthesizes; statistical identification and predefined validation tests constrain what can be claimed.**

The system makes four kinds of statement. They are kept apart everywhere: in the tables, in the answer, and in the checks.

| Kind | Example | Comes from |
|---|---|---|
| **Estimated effect** | "At moments where the agent refused citing policy, escalation followed {F3.att} points more often than at otherwise-similar moments without a refusal ({F3.ci})." | Step 4, the Factor Library |
| **Evidence** | "Turn 17 of call `ab12…` shows a policy refusal." | Step 5, grounding spans |
| **Faithfulness** | "Removing turn 17 lowers the risk model's forecast more than removing 95% of other turns." | Step 5, the forecaster (never causal) |
| **Narrative** | the LLM's wording that links the three | Step 8, checked by Step 9 |

### The claim ladder

Every factor in the Factor Library gets a **claim level**, computed by code from the checks in Step 4. The level decides the wording the answer may use.

The wording categories come from a validated taxonomy of causal language: *direct causal*, *conditional causal*, *correlational*, *no relationship* [Yu et al., EMNLP 2019].

| Level | Meaning | Allowed wording | Required |
|---|---|---|---|
| **L3 — estimated effect under stated assumptions** | a pre-registered, actionable behaviour whose effect survived every check | *conditional causal*: "is estimated to raise the chance of …", "calls where X happened were N points more likely to … than otherwise-similar calls" + the assumptions | all Step 4 checks pass (§6, Step 4) |
| **L2 — warning sign / adjusted association** | an estimate exists, but at least one L3 check fails, or the behaviour is a customer state rather than something the company controls, or the slice was not pre-registered | *correlational*: "is associated with", "often precedes", "is a warning sign of" | estimate exists; support at least "borderline" |
| **L1 — descriptive** | counts, rates and examples, with no comparison implying cause | *no relationship*: "18% of calls escalated", "here are 3 examples" | enough calls to count |
| **L0 — not supported** | the data cannot answer reliably | "The data cannot answer this reliably because …" | — |

*Direct causal* wording ("X causes Y", "X leads to Y", "the reason is X") is **never** allowed, at any level. Gate 2 in Step 9 enforces this.

## 3 · The idea in one picture

```
 PREPARE ONCE (offline)                                           ANSWER EACH QUESTION (online)
 ──────────────────────                                           ─────────────────────────────
 RAW DATA                                                         USER QUERY
   │                                                                │
 STEP 0  clean ✅ ─ template groups ✅ ─ LOCK SPLIT ✅                STEP 7  parse → QuerySpec
   │     leakage audit ✅ ─ column-availability registry ✅            │      + presupposition check + support policy
   │          train 80%            │  held-out = dev 10% + test 10%   │
   ▼                               ▼                                STEPS 10–12 (Task 2)
 STEP 1  LLM development sample    HUMAN GOLD (blind, stratified,     │  state + delta → deterministic merge
         (train) → onset labeller  known sampling rates)              │  → route: reuse / re-filter / new lookup / clarify
   │     → labels for all calls ◄──── accuracy + DSL correction       ▼
   ▼                                                                STEP 6  retrieve (BM25 + embeddings, RRF)
 STEP 2  landmark risk sets: at turn k, only what was said before k   │  one window per call, MMR diversity
   ▼                                                                  ▼
 STEP 3  behaviours: Step-0 cues + D5 proposals (train)             STEP 8  evidence pack (built by code)
         → event-definition exclusion → outcome-blind detectors       │  → LLM writes; numbers = placeholders
   ▼                                                                  ▼
 STEP 4  PILOT (train) → PRE-REGISTER (hash) → CONFIRM ONCE         STEP 9  gates: numeric · causal-claim · evidence
         (held-out) → DSL-corrected DML (ATT), overlap, balance,      │
         BH, negative controls, E-values, sensitivity                 ▼
   ▼     → FACTOR LIBRARY with claim levels L0–L3                   FINAL ANSWER (every claim carries its level)
 STEP 5  grounding spans + faithfulness (cross-fitted forecaster)
   ▼
 STEP 6  EVIDENCE GRAPH (tables with provenance) + search index
                                     STEPS 13–14: metrics · query set (dev / LOCKED test) · baselines · ablations
```

## 4 · Mini glossary

| Word | Meaning in this document |
|---|---|
| call / transcript | the text of one phone call |
| turn | one person speaking once (one line of the transcript), numbered from 0 |
| event | a business outcome: escalation, refund or churn (definitions in Step 1) |
| **onset** | the first turn at which the event becomes explicit, e.g. the customer asks for a supervisor |
| behaviour | something said or done in one turn, e.g. *"agent refuses, citing policy"* |
| treatment | the behaviour we study as a possible cause, defined at a specific turn |
| **intervention** | the change we imagine: *"at this turn, the agent does not do X; afterwards the call goes on as it naturally would"* |
| **estimand** | the exact quantity we try to estimate, written down before looking at results |
| **landmark** | a turn *k* at which we "pause" a call and compare calls that are alike up to that point |
| **risk set** | the calls still "at risk" at turn *k*: the event has not happened yet and the behaviour has not happened yet |
| confounder | a third factor that affects both the behaviour and the event (an already-angry customer hears more refusals *and* escalates more) |
| post-treatment variable | something measured *after* the behaviour, such as total call length. Adjusting for it biases the result. |
| leakage | information from the answer (the outcome, the test data or the future) sneaking into the inputs |
| template group | calls that look generated from the same template; they always stay in the same split |
| overlap | for comparable moments, both "behaviour" and "no behaviour" really occur. Without overlap there is nothing to compare. |
| ATT | *average effect on the treated*: the average effect at the moments where the behaviour actually happened |
| confidence interval (CI) | the error bar around an estimate |
| faithfulness | whether a model's prediction actually depends on a given line. This says nothing about the real world. |
| provenance | where a piece of information came from: raw dialogue, a derived label, an estimate, an LLM summary … |
| train / dev / test | splits of the **calls**. Train: find ideas and tune. Dev + test (**held-out**): confirm the numbers once. |
| dev / locked test queries | splits of the **question set** (Step 14). Dev queries may tune the answering pipeline; locked test queries are run once. |

## 5 · Ground rules that apply to every step

| # | Rule | Enforced by |
|---|---|---|
| **R1** | **Locked split.** Train / dev / test are fixed by hashing the template group, before any labelling, discovery or tuning. No call, and no template, is ever in two splits. | Step 0 (built); integrity checks |
| **R2** | **Only the past.** A covariate used at landmark turn *k* may be computed only from turns before *k*. Every column has an availability class in `column_availability.csv`: `design`, `turn-past`, `opening`, `metadata`, `whole-call` or `outcome`. `whole-call` columns such as `rel_position`, `phase`, `n_turns` and QC flags are never covariates. | Step 0 registry (built); the Step 2 *future-invariance test* |
| **R3** | **Metadata stays out of the causal core.** `reason_for_call`, `intent` and `business_domain` have unknown timing. They are never in the main adjustment set. Fields flagged by the leakage audit are never used as covariates, filters or model inputs. Unflagged fields may be used as descriptive filters (any estimate on such a slice is exploratory, at most L2) and in sensitivity analysis S4. | Step 0 leakage audit (built) |
| **R4** | **An event cannot explain itself.** Each event has an exclusion list of behaviours that are part of it or synonyms of it. | `event_definitions.yaml` (Step 1); Step 3 filter |
| **R5** | **Discover → pre-register → confirm once.** Ideas and settings come from train. The analysis plan is frozen (file hash committed) before any held-out estimate is computed. Anything else is labelled *exploratory* and capped at L2. | Step 4 |
| **R6** | **Count calls, not snippets; cluster by template.** Statistics are computed per call (and per landmark row), never per retrieved window. Uncertainty treats calls from one template group as one cluster. | Steps 4, 6, 13 |
| **R7** | **Numbers only from tables.** The LLM never types a number. It writes placeholders such as `{F3.att}`, which code fills from the Factor Library. | Steps 8–9 |
| **R8** | **Wording follows the claim ladder.** | Gate 2 (Step 9) |
| **R9** | **Provenance.** Direct quotes may come only from raw dialogue. Numbers may come only from `causal_estimate` or `descriptive_stat` rows. Analyst notes and LLM summaries are never cited. | Steps 6, 9 |
| **R10** | **Everything is reproducible.** Seeds, library versions, model names and versions and prompt hashes are recorded. Current Claude models take no sampling parameters (no "temperature 0"), so every LLM reply is cached on disk under the hash of its prompt and replayed on re-runs (C10). Every answer is logged with its evidence pack and gate results. | run manifest; LLM cache and call log |

---

## 6 · The steps

Every step has the same parts:

* **In plain words** — what we do;
* **Precise specification**, when needed;
* **Why this option**;
* **Papers** and **Code**;
* **Output**;
* **Loopholes closed**;
* **Acceptance test**;
* **If short on time**.

### Step 0 — Clean the data, audit the metadata, lock the split ✅ (built)

**In plain words.** Turn the messy raw file into clean, numbered turns with the right speaker on every line. Then answer three questions before anyone looks for causes:

* which calls are copies of each other;
* which columns secretly contain the future;
* which metadata fields might already contain the answer.

**What is built** (details in [`DATA_CLEANING.md`](DATA_CLEANING.md)):

* **Cleaning (from v1):**
  * roles resolved for 1,332 name-labelled calls, validated by hiding labels;
  * 75 analyst notes quarantined (they say things like "no escalation occurred");
  * 4 squashed calls re-split;
  * stage directions turned into events;
  * two text views, `text` and `text_clean`;
  * 16 behaviour cues;
  * weak event flags with their first turn.
* **Template groups (new).**
  * Words are compared as 3-word sequences, with numbers masked so that ids and amounts do not hide re-use (MinHash, Jaccard ≥ 0.5).
  * A giant-group guard raises the threshold until no group holds more than 1% of calls. On the 19.6k-call synthetic test it rose from 0.5 to 0.6.
  * Near-duplicates are always nested inside template groups.
* **Locked split (new).** Train / dev / test = 80/10/10, by hashing the template group.
* **Learned transforms fitted on train only (new):** the role classifier, the repeat detector's vocabulary, and the intent → industry votes.
* **Opening-only industry (new).** `opening_domain_vote` uses only the first 4 turns, so it is safe as a control variable. `business_domain` reads `reason_for_call`.
* **Leakage audit of the metadata (new, §10.2 of the notebook).** It uses non-test calls only.
  * *Content probe:* the share of `reason_for_call` values that describe what happened *during* the call ("the agent processed a refund at the end of the call").
  * *Predictive probe:* each metadata field predicts each event flag with 5-fold cross-validation grouped by template. This is compared with the same model on the **opening turns**, which precede everything later in the call.
  * A field is flagged if it contains outcome language, or if it predicts an event much better than the opening does (AUC ≥ 0.75 and ≥ 0.05 above the opening). Columns derived from a flagged field inherit the flag.
* **Column-availability registry (new, §10.3).** Every output column gets a class (R2). For example, `rel_position` divides by the call length, so it is `whole-call` and never a covariate.
* **19 integrity checks** (new ones: template groups never straddle splits; near-duplicate clusters nest inside template groups; every column has an availability class; flagged columns are never usable) and **14 end-to-end tests**.
  * The synthetic fixture now injects a leaky `reason_for_call` for refund calls, and calls re-used with only the numbers changed.
  * The tests check that the audit flags the leaky field (refund AUC 0.92 vs 0.54 for the opening) and leaves `intent` unflagged.
  * They also check that re-used calls share one template group and one split.

**Papers.**
* Main: Kaufman et al., *Leakage in data mining*, **ACM TKDD 2012**.
* Supporting: Elangovan et al., *Memorization vs. Generalization*, **EACL 2021** (train/test template overlap).

**Loopholes closed.**

| Loophole | Fix | Check |
|---|---|---|
| Analyst notes leak outcomes | quarantined, never indexed | integrity check + test |
| Templated calls in train *and* test | split by template group | "never straddle" check + test |
| `reason_for_call` / `intent` written after the call | leakage audit; R3 | `leakage_audit.csv`; test with an injected leak |
| Whole-call columns used as if known earlier | availability registry | coverage check + test |
| Test-split text shaping train-fitted features | train-only fitting of vocabulary, votes and classifier | code review; `split_of` in §8–9 |

**Acceptance test on the real file.** Run the notebook, then check:

* `ROLE_EVAL` two-party accuracy is at least 0.97;
* all 19 checks pass;
* read `leakage_audit.csv` and note which fields are flagged;
* note the template threshold used and the largest template group;
* sanity-check the `domain_mapping.csv` table.

The flagged fields decide R3 for the rest of the project. **Do not change `SPLIT_SALT` after this point.**

---

### Step 1 — Event labels: which call, which event, which turn

**In plain words.**

* Write down exactly what counts as each event and where it *starts*.
* Let an AI label a sample of **train** calls, then train a fast labeller for the rest.
* Two teammates label a separate random sample of **held-out** calls without seeing any AI output. This gives an honest error rate.
* That error rate is later used to *correct* the effect estimates.

**1a. Event definitions (`event_definitions.yaml`, versioned).**

| Event (confirmatory) | Onset = first turn where … | Sub-types stored | Excluded as causes (definitional or near-synonyms) |
|---|---|---|---|
| **ESC** escalation | the customer asks for a supervisor, manager or "someone higher", **or** the agent starts a handoff to one | `customer_request`, `agent_handoff` | supervisor/manager request cues, agent escalation cues, transfer cues, supervisor/specialist speaking, TRANSFER markers |
| **REF** refund episode | either party raises a refund, compensation, credit-back or chargeback | `customer_request`, `agent_offer` | refund / compensation / credit talk by either side (incl. `cue_refund`, compensation offers) |
| **CHURN** churn threat | the customer states an intent to cancel, close, switch or not renew | `cancel`, `switch`, `not_renew` | churn-intent cues, competitor mentions |

Secondary events are exploratory only (L2 at most). Each is analysed on its own, never merged with a confirmatory event:

* `handoff_completed` (a supervisor actually speaks);
* `refund_granted`, `refund_denied`;
* `cancellation_done`;
* `product_problem`, `feature_request`.

Every call also gets an **`event_sequence`**: all onsets in time order.

**1b. Development sample (train only).**

* About **1,500 train calls**, stratified by the Step-0 weak flags, with known sampling rates. Flagged calls are over-sampled.
* The LLM fills a JSON form per call: for each event, `present`, `onset_turn`, `onset_quote` (the exact words), `subtype`, and the secondary outcomes.
* LLM settings: a pinned model, a hashed prompt, JSON-schema output, and a response cache keyed by the prompt hash (C10).

**1c. Quote check (catches invented onsets).**

* Code checks that `onset_quote` really appears in turn `onset_turn` (fuzzy match ≥ 0.9 on `text_clean`).
* If it does not, the LLM gets one retry. If that also fails, the label is marked unverifiable and not used.
* The team also checks **50 train calls** by hand while developing the prompt. These are train calls, never the gold set.

**1d. Fast labeller (TnT-LLM idea).**

* Per event, a **turn-level onset detector**: logistic regression on the words of the turn plus the previous turn, trained on the LLM labels.
* Onset = the first turn above a threshold chosen by cross-validation on train.
* Metadata is **never** an input (R3).
* *Budget option:* the LLM labels the ~3,900 held-out calls directly (about 4M input tokens), and the detector is used only for train. Either way, the gold set measures the labeller that was actually used.

**1e. Gold set — held-out calls only (two populations).**

* About **200 held-out calls**, drawn by stratified random sampling with **known inclusion probabilities**:
  * 150 simple random calls (representative);
  * 50 rare-event "stress" calls from flagged strata.
* Two teammates label them using the same form, **blind** to every AI output.
* 40 calls are labelled by both → Cohen's κ; disagreements are resolved by discussion.
* Metrics use inverse-probability weights, so they describe the real corpus rather than the over-sampled one:
  * presence precision / recall / F1, with confidence intervals;
  * onset exact, and within ±1 turn;
  * per stratum.
* **The gold set is never used for tuning.** It is used only to measure accuracy and for the Step 4 correction.

**Why this option.**

* *Keywords only* miss paraphrases.
* *LLM on every call* is possible but slow.
* *LLM sample → small labeller* is fast and consistent [TnT-LLM].
* Any labeller makes errors, and errors bias effects. For example, if the labeller "sees" escalation more readily in calls with refusals, refusals look worse than they are. The DSL design (Egami et al.) fixes this: a random gold subsample with known inclusion rates gives effect estimates that stay unbiased with honest CIs, **however imperfect the labeller is**. This is why the gold set comes from held-out calls with known sampling rates.

**Papers.**
* Main: Wan et al., *TnT-LLM*, **KDD 2024**.
* Supporting: Egami et al., *Using Imperfect Surrogates for Downstream Inference* (DSL), **NeurIPS 2023**.

**Code.**
* scikit-learn.
* The TnT-LLM tutorial in `langchain-ai/langgraph` as a guide.
* The DSL correction is three lines of numpy (Step 4).

**Output.**
* `events.parquet`: call, event, present, onset turn, subtype, source (`llm` / `detector` / `gold`), confidence, label version.
* `event_sequence`.
* `gold.parquet`, with inclusion probabilities.

**Loopholes closed.**

| Loophole | Fix |
|---|---|
| Mixed outcome types (point 17) | explicit taxonomy; three confirmatory events; others secondary |
| Circular events (point 16) | exclusion lists, stored with the definition |
| Gold calls seen in training (point 21) | development sample from train only; gold from held-out only |
| Prevalence distorted by over-sampling (point 22) | two populations; inverse-probability-weighted metrics |
| Invented onset turns | quote check; unverifiable labels dropped |
| Humans anchored on AI labels | blind labelling; κ on a double-labelled subset |
| Label error biasing effects | DSL correction in Step 4 |
| Metadata giving the answer away (point 35) | metadata never an input to the labeller |
| Tuning on the gold set | the gold set only measures and corrects; it never tunes prompts or thresholds |

**Acceptance test.**
* 100% of labels used downstream pass the quote check.
* Gold metrics are reported with CIs.
* **If presence F1 < 0.7 for an event, that event's claims are capped at L2.** This is not a target to tune toward: prompts are never tuned on gold.
* If fewer than 90% of true onsets are within ±1 turn, Step 4's onset-shift sensitivity (S8) must pass for L3.

**If short on time.**
* Use the Step-0 keyword onsets, confirmed by the LLM on flagged calls.
* Use 150 gold calls.
* The DSL correction still applies.

---

### Step 2 — Landmark risk sets: compare like with like, using only the past

**In plain words.**

1. Imagine pausing every call at turn *k*.
2. Among calls where the event **has not happened yet**, the agent does the behaviour **right now** in some, and not in others.
3. We compare what happens *later in those calls*.
4. We use only what was said **before** turn *k* to make the two groups comparable.
5. We repeat this for every turn *k* and pool the results.

This is how medical researchers emulate a clinical trial from records. It avoids "cheating with the future" [Hernán & Robins, AJE 2016], and it also handles conversations where each turn reacts to the last [sequential trials; Keogh et al., Stat Med 2023].

**Precise specification (the "target trial" protocol).** This is written into `prereg.yaml`.

| Protocol element | Specification |
|---|---|
| Eligibility at turn *k* | *k* ≥ 4 (after the opening); turn *k* exists; the event's onset is later than *k*; **no other confirmatory event and no supervisor handoff has started before *k*** (C1; S5 relaxes this); behaviour B has not happened before *k* (first use); turn *k* is spoken by B's party; both parties have spoken before *k* |
| Treatment strategies | "B at turn *k*" vs "no B at turn *k*". After *k*, the call continues as it naturally would. |
| Outcome | primary: the event starts at some turn after *k*, before the call ends. Secondary: within the next 6 turns. |
| Time zero | turn *k*: eligibility, treatment and follow-up all start here, so there is no "immortal time" |
| Causal contrast | ATT: the average effect at the moments where B actually happened |
| Covariates *H*<sub>k</sub> | only `opening` and `turn-past` columns of turns **before** *k* (R2) — see the list below |
| Unit and clusters | a row is (call, *k*); calls are nested in template groups, and the cluster is the template group |

**Covariates at turn *k*.** Everything is computed from turns before *k*:

* turns so far (*k*) and words so far per party;
* counts of every Step-0 cue per party so far;
* earlier behaviours (Step 3) so far;
* earlier *other* events (e.g. a refund episode before an escalation);
* hesitation rate so far, repeated questions so far, holds and pauses so far;
* cue indicators of the last 3 turns;
* `opening_domain_vote` and `brand`;
* a 32-dimensional summary of the earlier turns' sentence embeddings (PCA fitted on train).

**Never included:**

* turn *k* itself — including it breaks overlap, because the text of turn *k* reveals B [Gui & Veitch, ICLR 2023];
* total length, `rel_position`, `phase`, QC flags;
* metadata (except in sensitivity S4).

**Events at the call's end and truncated calls.**
* The call ending is part of the outcome: once it ends, the event can no longer happen. The estimate is therefore the *total* effect [Young et al., Stat Med 2020]. It is **not** treated as censoring.
* The main analysis treats every transcript as complete. The truncation flag mostly marks calls that lost only their closing lines (the outcome is complete), and every row of a flagged call "reaches the cut-off", so censoring them would drop whole calls. Sensitivity **S3 excludes the flagged calls**, and S3 is required for L3 (C5, C6).

**Events already present in the opening** (onset < 4) are not in any risk set. Their share is reported. In-call behaviours cannot explain them, so the answer describes them separately as **before-call drivers** (L1).

**Why this option.**

* v1 compared before-event windows with controls cut at a point borrowed from event calls, matched on total length. This had two flaws:
  * **Immortal-time bias:** it selected comparison windows using the outcome [Hernán et al., JCE 2016].
  * **Post-treatment bias:** total length is only known at the end [Montgomery et al., AJPS 2018].
* Landmark rows fix both.
* **Time-varying confounding:** the customer's frustration affects the agent, and the agent affects the frustration. With a *single-turn* treatment and the *full history* adjusted for, standard adjustment is valid at each landmark. This is the sequential-trials result [Keogh 2023].
* Special methods (marginal structural models, g-computation) are needed only for *sustained* strategies such as "never refuse all call". That is listed as a research extension, not claimed.

**Papers.**
* Main: Hernán & Robins, *Using Big Data to Emulate a Target Trial When a Randomized Trial Is Not Available*, **Am. J. Epidemiology 2016**.
* Supporting: Keogh et al., *Causal inference in survival analysis using longitudinal observational data: sequential trials and marginal structural models*, **Statistics in Medicine 2023**.
* Precedents for looking at the conversation *before* the event: Conversations Gone Awry (**ACL 2018**) and CRAFT (**EMNLP 2019**).

**Code.**
* pandas.
* `ruthkeogh/sequential_trials` (the paper's R simulation code) as a reference.

**Output.** `risk_sets/<event>/<behaviour>.parquet`, with columns: call, *k*, T, Y, Y₆, *H*<sub>k</sub>, template group, censored flag, split.

**Loopholes closed.**

| Loophole | Fix |
|---|---|
| "Before" treated as "cause" (point 13) | ordering is only an eligibility rule; causal status comes only from Step 4 |
| Treatment–confounder feedback (point 12) | single-turn treatment + full-history adjustment (sequential trials) |
| Matching on length at the end (points 4, 20) | only "length so far" |
| Outcome-selected controls | landmark rows; time zero = turn *k* |
| Several events per call (point 18) | earlier other events are history covariates; S5 = "clean" risk sets |
| Treatment turn inside the covariates | covariates strictly from turns < *k* |
| Truncated calls | censoring rule + S3 |

**Acceptance test.**
* **Future-invariance test.** For 1,000 random rows, replace every turn after *k* with random text and rebuild the covariates. They must be byte-identical.
* No row at or after the onset.
* At most one treated row per call and behaviour.
* Counts reported: rows, treated rows, events, prevalent-at-opening, censored.

**If short on time.**
* Use landmarks only at agent turns 4–30.
* Drop the embedding summary (cue counts only). This weakens the adjustment. E-values (Step 4) will show how fragile the result is.

---

### Step 3 — Candidate behaviours, measured without seeing the outcome

**In plain words.**

* Make the list of behaviours that might matter: the ones Step 0 already measures, plus new ones an AI suggests from train calls.
* Throw out anything that is really the event itself.
* Measure each behaviour at a turn using **only that turn and earlier ones**. Then the measurement cannot be influenced by knowing how the call ended.

**What we do.**

1. **Known behaviours (Step 0).**
   * Agent side: hold request, policy refusal, apology, empathy statement, offer of a solution, return from hold.
   * Customer side: negative emotion, confusion, repeated question, hesitation (fillers), "still not working", mention of a previous contact.
2. **AI-proposed behaviours (D5; train only).**
   * Show an LLM *pre-onset* windows (ending before the onset) from event calls, and windows from event-free calls cut at the *same turn number*.
   * Ask for differences, phrased as yes/no questions about **one turn**, e.g. *"Does the agent promise a callback without giving a time?"*
   * Repeat on several random batches, then merge the lists.
3. **Every candidate passes five filters:**
   1. **event-definition exclusion** — an LLM/NLI check ("does this describe the event itself?") against `event_definitions.yaml`, plus a human sign-off;
   2. **pre-treatment check** — observable in a single turn before the onset;
   3. **de-duplication** — embedding similarity > 0.85, plus a human check;
   4. **actionability tag** — an *agent or process* behaviour, which the company can change, versus a *customer state* (confusion, anger), which it cannot switch off. **Customer states are capped at L2** ("warning sign"): the intervention "the customer had not been confused" is not well defined [Hernán & Taubman, 2008];
   5. **prevalence** — the behaviour starts in at least 2% of the train risk-set **calls** (each call has many rows but at most one treated row, so a row-based threshold would drop common behaviours; C8), otherwise there is no statistical power.
4. **Outcome-blind detectors.**
   * A detector labels turn *k* seeing only turns ≤ *k*: never later turns, event labels or metadata.
   * Step-0 cues are turn-local by construction.
   * LLM-based detectors get a context window that ends at turn *k*.
   * *Blindness test:* cutting the call right after turn *k* must not change the label.
5. **Precision check.**
   * 20 train turns per behaviour, judged by a teammate who sees only the turn and the two before it.
   * Behaviours below 0.8 precision are dropped.
   * Confirmed factors get 20 more checks on held-out turns.
6. **Co-occurrence map.**
   * Measure how often behaviours occur together (phi coefficient), in the same turn and in the same call.
   * Behaviours with phi > 0.7 become one **family**: one treatment, not several.
7. **Negative-control behaviours** (two per event), expected to have no effect:
   * the agent reads back an id or number;
   * the agent thanks the customer for information.

   If they "show an effect", something unmeasured is distorting the analysis.

**Why this option.**

* *A fixed list* misses patterns specific to this data.
* *Topic models* give word clusters that are hard to read.
* D5 proposes readable, testable differences, but it states itself that these are **correlations**. So D5 is used only to *propose*; Step 4 decides.
* Behaviours measured by a classifier are noisy stand-ins for the real thing, and noise shrinks effects toward zero [Pryzant et al.]. This is why precision checks and outcome-blind detectors are required.

**Papers.**
* Main: Zhong et al., *Goal Driven Discovery of Distributional Differences via Language Descriptions* (D5), **NeurIPS 2023** — candidate generation only.
* Supporting: Pryzant et al., *Causal Effects of Linguistic Properties*, **NAACL 2021** — noisy proxy treatments.

**Code.** [ruiqi-zhong/D5](https://github.com/ruiqi-zhong/D5) (71★) as a design guide; its prompts need re-writing for a current LLM.

**Output.**
* `behaviours.yaml`: id, yes/no question, party, detector, actionability, exclusion sign-off, precision.
* `behaviour_occurrences.parquet`: turn_uid, behaviour, detector version.
* `cooccurrence.csv`.

**Loopholes closed.**

| Loophole | Fix |
|---|---|
| Discovery restates the event (point 23) | exclusion check + pre-treatment check + de-duplication |
| Behaviour judged after seeing the ending | outcome-blind detectors + blindness test |
| Correlated behaviours counted as separate causes (point 24) | families; co-occurrence reported in every answer |
| Undefined interventions (point 11) | actionability tag; customer states capped at L2 |
| Noisy detectors | precision ≥ 0.8; attenuation noted |

**Acceptance test.** Every behaviour in the confirmatory family has:

* an exclusion sign-off;
* precision ≥ 0.8;
* a passed blindness test;
* prevalence ≥ 2%.

**If short on time.** Use only the Step-0 cues, minus the excluded ones, and skip D5.

---

### Step 4 — Estimate effects: pilot, pre-register, confirm once

**In plain words.**

* For each behaviour and event, compare the "behaviour happened at turn *k*" moments with otherwise-similar "no behaviour at turn *k*" moments from Step 2.
* Flexible models make the groups comparable (Double Machine Learning, DML).
* Then we **try hard to break the result**, and let predefined rules decide how strongly the answer may speak.

**Three phases.**

1. **Pilot — train only.**
   * Run the whole pipeline and choose the model type for each part.
   * Look at overlap.
   * Run the **planted-effect test**:
     * on real train rows, simulate an outcome with a *known* effect (+8 points) and check that the code recovers it, with 95% CIs covering the truth ~95% of the time;
     * with a zero effect, check that false alarms occur at ~5%.

     Use ≥ 100 simulated datasets on a 20% subsample of train rows (about 10 minutes with logistic models). This is the standard way to test causal code [Dorie et al., Statistical Science 2019].
2. **Pre-register.** Before any held-out estimate is computed, freeze `prereg.yaml` and commit its SHA-256 hash. It fixes:
   * event definitions and exclusion lists;
   * the confirmatory family: **at most 12 behaviours per confirmatory event**, chosen by a written, mechanical rule (Step 3 filters passed, pilot overlap OK, ranked by pilot attributable events), plus the negative controls. Nothing seen while gold-labelling held-out calls may add or remove a behaviour;
   * the estimand, covariates, model types, trimming rule, support thresholds, sensitivity analyses and claim-level rules.
3. **Confirm once — held-out (dev + test, ~3,900 calls).**
   * Estimate every pre-registered effect once.
   * Code runs the checks and assigns the level.
   * Anything not pre-registered is *exploratory* and capped at L2 [Egami et al., Sci. Adv. 2022; Nosek et al., PNAS 2018].

**The estimator.**

| Part | Choice |
|---|---|
| Estimand | ATT: the effect of "B at turn *k*" vs "no B at turn *k*", natural course afterwards |
| Estimator | the DoubleML IRM "ATTE" score, re-implemented in `crest/analysis.py` (identical estimates to `DoubleMLIRM(score="ATTE")` on the same folds — tested), 5-fold cross-fitting with **folds by template group** and **cluster-robust standard errors** (clusters = template groups) [Chernozhukov et al. 2018; Chiang et al. 2022] |
| Nuisance models | propensity: logistic regression or a gradient-boosting classifier. Outcome: a linear or gradient-boosting **regressor**, because the DSL outcome below is not 0/1. Each family's regularisation is **tuned on train** over a small grid and the family with the lower cross-fitted loss is chosen; both tuned learners are fixed in the pre-registration (the other one is S6). Logistic models use the Newton–Cholesky solver (C4). |
| Label-error correction (DSL) | each call's contribution x to the ATT score (numerator and denominator) becomes x̃ = x<sub>labeller</sub> + (R/π)·(x<sub>gold</sub> − x<sub>labeller</sub>): R = 1 for gold calls, π = their inclusion probability. For the outcome this is the DSL pseudo-outcome Ỹ = Ŷ + (R/π)·(Y<sub>gold</sub> − Ŷ); applying it to the whole contribution also corrects **which moments are at risk** when the labeller misses or misplaces an onset (C3) [Egami et al. 2023]. |
| Overlap | cross-fitted propensity. Drop treated rows with probability > 0.9, since they have no comparable "no-B" moments. Report the share dropped [Crump et al., Biometrika 2009]. |
| Balance | after weighting, the standardized mean difference of the **prognostic score** (the predicted chance of the event without B) must be ≤ 0.1 [Austin, Stat. Med. 2009; Stuart, Lee & Leacy, J. Clin. Epidemiol. 2013]. Every covariate's SMD is reported, but not used as a gate: with ~100 covariates the largest one is dominated by sampling noise (C2). |
| Second uncertainty check | **cluster bootstrap** of the orthogonal score: resample template groups, 2,000 draws |
| Many tests | Benjamini–Hochberg at q = 0.05 over the **whole pre-registered family** (≤ 36 tests) [JRSS-B 1995]. Subgroups are a separate, exploratory family. |
| Negative controls | the two neutral behaviours per event go through the same pipeline. If one shows an effect (95% CI excluding 0; deliberately no multiplicity correction, to err toward caution), *all* claims for that event are capped at L2 [Lipsitch et al., Epidemiology 2010]. |
| Unmeasured confounding | E-value (after converting the ATT to a risk ratio among treated rows) for the estimate and its CI limit: how strong a hidden factor would have to be to explain the result away [VanderWeele & Ding, Ann. Intern. Med. 2017]. Reported with every L2/L3 factor. |
| Replication | estimate separately on dev and on test; the sign must agree |
| Sensitivity analyses | **S1** 6-turn horizon · **S2** without name-labelled calls (inferred roles) · **S3** without possibly truncated calls · **S4** + unflagged metadata · **S5** including moments after another event (earlier events as covariates) · **S6** the other model type · **S7** single-call template groups only · **S8** onset shifted ±1 turn |
| Population impact | **attributable events** = ATT × number of treated rows (with CI): roughly how many held-out events are linked to B, under the assumptions. Factors are ranked by this, not by effect size alone. |

**The claim level, computed by code.** A factor reaches **L3** only if **all** of these hold:

1. it is pre-registered;
2. it is actionable (an agent or process behaviour);
3. support is "sufficient" (Step 7 policy):
   * ≥ 20 events in each arm;
   * ≥ 80% of treated rows kept after trimming;
   * CI half-width ≤ 10 points;
   * prognostic-score standardized difference ≤ 0.1;
4. BH q < 0.05;
5. the cluster-bootstrap CI excludes 0;
6. S2, S3, S5 and S8 are estimable with the primary's sign, no other S that was run has the opposite sign, and none is significantly opposite (C6);
7. dev and test agree in sign;
8. the negative controls are clean;
9. the planted-effect test passed;
10. gold F1 ≥ 0.7 for the event;
11. the behaviour's detector precision was verified by a person: ≥ 0.8 on ≥ 20 judged turns (C16).

If an estimate exists but one of these fails, the factor is **L2**, and the failed checks are stored and shown. With no estimate, the factor is **L1** (counts only) or **L0**.

**Why this option.**

* *Raw comparisons* mix cause and coincidence.
* *Asking the LLM whether X causes Y* is near chance [Corr2Cause, ICLR 2024].
* *Causal-discovery algorithms* are unstable with dozens of behaviours.
* *Matching* was replaced, not patched. DML with overlap and balance diagnostics does what matching was meant to do, reports when it cannot, and gives valid error bars.
* *G-methods for sustained strategies* ("never refuse") are the research extension, not the deadline plan.

**Papers.**
* Main: Chernozhukov et al., *Double/debiased machine learning*, **Econometrics Journal 2018**.
* Main: Egami et al., *How to make causal inferences using texts*, **Science Advances 2022**.
* Safeguards: one line each in the table above.

**Code.**
* [DoubleML/doubleml-for-py](https://github.com/DoubleML/doubleml-for-py) (790★, v0.11.4; JMLR 2022): IRM with the ATTE score and cluster-robust inference.
* [py-why/dowhy](https://github.com/py-why/dowhy) (optional) for extra refuters.

**Output.** `factor_library.parquet`, one row per event × behaviour × slice:

* the estimand text;
* population counts, treated rows, events, share trimmed;
* ATT, CI, q-value, bootstrap CI;
* max standardized difference, overlap kept;
* E-values, negative-control status, sensitivity signs, dev/test signs, DSL flag, gold F1;
* attributable events (with CI);
* event rate among treated rows vs adjusted counterfactual rate;
* co-occurring factors, actionability;
* **claim level and failed checks**;
* `prereg_hash`, `library_version`.

**Loopholes closed.**

| Loophole | Fix |
|---|---|
| Ill-defined treatment (point 11) | estimand card in `prereg.yaml`; actionability tag |
| Matching ≠ balance (point 19) | overlap trimming + balance check; "not estimable" when they fail |
| Correlated behaviours (point 24) | families; co-occurrence stored; wording rule in Step 8 |
| Unplanned multiple testing (point 25) | pre-registered family; BH across it; subgroups exploratory |
| Templated calls (point 26) | template-cluster standard errors + cluster bootstrap |
| Tiny subgroups (point 33) | support policy |
| Corpus-specific results (point 34) | "within this corpus" in every L2/L3 statement |
| Label error | DSL correction |
| Unmeasured confounding | negative controls + E-values + careful wording |
| Code bugs, wrong error bars | planted-effect and null tests |
| Tuning on held-out data | pre-registration hash committed first |
| Trimming silently changes the population | share kept is reported; < 50% kept → not estimable |

**Acceptance test.**
* Planted-effect test (100 simulated datasets per pair, half null): |bias| ≤ max(1 point, 2.5 Monte-Carlo standard errors); the Wilson interval of the coverage overlaps 90–98%; the Wilson interval of the null false-alarm rate reaches ≤ 7% (C7).
* The pre-registration hash is committed before the held-out run.
* The library schema is validated.
* Levels are computed by code, never edited by hand.

**If short on time.**
* Run only the primary analysis, overlap/balance, BH, negative controls, E-values, and sensitivities S2, S5 and S8. That is the minimum for L3.
* Anything without these checks is capped at L2 automatically.

---

### Step 5 — Evidence spans: where the behaviour happens, and does the forecaster rely on it?

**In plain words.** For each example call we show two separate things. Neither is proof that the line caused the event:

1. **Grounding.** The exact turn where the behaviour happens, before the event.
2. **Faithfulness.**
   * A risk forecaster works like a weather forecast that updates after every turn.
   * We check whether removing that turn lowers its forecast more than removing a random turn.

**What we do.**

1. **Grounding spans.**
   * Turns where a Factor-Library behaviour occurs before the onset, in calls from that factor's population.
   * The quote is the exact turn text.
   * The span is cited as `turn_uid`.
2. **Risk forecaster (forecasting only).**
   * A discrete-time hazard model: at turn *t*, the chance that the event starts at turn *t + 1*, given that it has not started yet.
   * Features: the Step-2 history features plus the words of the last 3 turns; logistic regression.
   * Trained with **random turn dropout** (1–2 turns removed from 30% of training rows), so inputs with a turn removed are normal for the model [Hase et al., NeurIPS 2021].
   * **Cross-fitted** (5 folds by template group): every call is scored by a model that never saw it.
3. **Faithfulness score of span *s*.** At the last turn before the onset, compare the forecast with the full history against three variants:
   * (a) *s* removed;
   * (b) *s* replaced by a neutral turn from the same speaker ("okay");
   * (c) a random other turn from the same speaker removed (20 draws).

   Score = drop(a) − median drop(c), with the percentile of drop(a) among the drops in (c). Variant (b) must agree in sign with (a). The ERASER "keep only this line" test is **dropped**: such inputs are unlike anything the model saw.
4. **Forecaster quality.**
   * AUC for "event within the next 3 turns", and calibration, on held-out calls.
   * ERASER *comprehensiveness* (remove the top spans) vs the random-removal baseline.

**Why this option.**

* A deletion test shows what **the model** relies on. It does not show what caused the event in the real world [ERASER; faithfulness ≠ causality].
* So the answer states three separate things:
  * the **effect** (Step 4);
  * the **evidence** that the behaviour happened here;
  * the **faithfulness** of the forecaster.

**Papers.**
* Main: DeYoung et al., *ERASER*, **ACL 2020** — faithfulness metrics only.
* Supporting: Hase, Xie & Bansal, *The Out-of-Distribution Problem in Explainability*, **NeurIPS 2021**.
* CRAFT (**EMNLP 2019**) is the precedent for turn-by-turn conversational forecasting.

**Code.**
* [jayded/eraserbenchmark](https://github.com/jayded/eraserbenchmark) `metrics.py`.
* ConvoKit (optional, neural forecaster).

**Output.** `evidence_spans.parquet`: `turn_uid`, call, event, behaviour, factor id, turns before onset, faithfulness (a/b/c), percentile, forecaster version, provenance `raw_dialogue`.

**Loopholes closed.**

| Loophole | Fix |
|---|---|
| Deletion taken as causal proof (point 14) | renamed and separated; wording rule |
| "Keep only" inputs unlike training (point 15) | dropped; removal and neutral replacement vs random baseline, with dropout training |
| Faithfulness scored on calls the model trained on | cross-fitting |
| Forecaster mistaken for a cause-finder | labelled *forecasting*; never feeds the Factor Library |

**Acceptance test.**
* Forecaster AUC is reported with a CI.
* For Factor-Library spans, the median faithfulness percentile is > 50. If not, the spans remain valid grounding, but the faithfulness line is left out of answers.

**If short on time.** Show grounding spans only. The numbers come from Step 4 anyway.

---

### Step 6 — Evidence Graph and search index

**In plain words.** Store everything in linked tables that record where each item came from. Build a search that finds examples by exact words and by meaning, without returning the same call twice.

**What we do.**

1. **Evidence Graph (parquet tables).**
   * Tables: `calls`, `turns`, `events` (onsets + sequence), `behaviour_occurrences`, `factor_library`, `evidence_spans`, `gold`, `run_manifest`.
   * Every row has a **provenance** value: `raw_dialogue`, `derived_event_label`, `derived_behaviour_label`, `causal_estimate`, `descriptive_stat`, `metadata_unaudited`, `analyst_annotation` (never used) or `llm_summary` (never cited).
2. **Search index over raw dialogue only.**
   * 5-turn windows, starting every 3 turns.
   * Each window is tagged with: call, turn range, split, industry (`opening_domain_vote`), brand, onsets, and whether the window is before or after each onset, plus the behaviours present.
   * Quarantined notes and metadata text are **not** indexed as quotable evidence.
3. **Hybrid search.** BM25 (exact words) + sentence embeddings (meaning), merged with Reciprocal Rank Fusion.
4. **Collapse to calls.**
   * Keep at most one window per call; overlapping hits from one call merge into one span.
   * Re-rank with **MMR** for variety across calls.
   * "How many" questions are answered from the tables at call level, **never** by counting search hits.

**Papers.**
* Reimers & Gurevych, *Sentence-BERT*, **EMNLP 2019**.
* Cormack et al., *Reciprocal Rank Fusion*, **SIGIR 2009**.
* Supporting: Carbonell & Goldstein, *MMR*, **SIGIR 1998**.

**Code.**
* [UKPLab/sentence-transformers](https://github.com/UKPLab/sentence-transformers).
* [dorianbrown/rank_bm25](https://github.com/dorianbrown/rank_bm25).
* Plain NumPy for about 230k windows.

**Loopholes closed.**

| Loophole | Fix |
|---|---|
| Overlapping windows counted as independent evidence (point 27) | one window per call; counts from tables |
| No provenance (point 28) | provenance on every row; citation rules R9 |
| Notes or metadata quoted as evidence | not indexed as quotable; test |

**Acceptance test.**
* Call-level Recall@10 on 30 hand-written search queries (target ≥ 0.8, reported with a CI).
* No evidence pack contains two items from the same call.
* The index contains no quarantined text (automated test).

---

### Step 7 — Understand the question

**In plain words.** Turn the question into a small, checkable form. Make sure it only asks for things the data has, and check that it does not smuggle in a false assumption.

**What we do.**

1. **QuerySpec** (a validated JSON schema):
   * `event` — from the taxonomy, or `unknown`;
   * `filters` — industry, brand, date range, intent (intent only if the audit did not flag it);
   * `question_type` — why / how often / examples / compare / trend / what to change;
   * `presuppositions` — claims hidden inside the question;
   * `unsupported` — parts the data cannot answer.
2. **Allowed filters** are only `opening`-class columns and unflagged metadata (R3).
   * Anything else ("premium customers in Miami") is reported as *not in the data*.
   * Filtering on a possibly-after-the-call field would select calls by their outcome — *selection bias* [Hernán et al., Epidemiology 2004].
3. **Presupposition check.** Take *"Why does empathy cause escalations?"*. It presupposes that empathy causes escalation. If the Factor Library has no such licensed claim, or shows the opposite sign, the answer **corrects the premise first** [CREPE, ACL 2023].
4. **Sycophancy guard.** The system never adopts the user's causal premise without a library row [Sharma et al., ICLR 2024].
5. **Support policy for every requested slice** (event × filters). Each criterion has the same three bands:

   | Criterion | Sufficient | Borderline | Insufficient |
   |---|---|---|---|
   | Events in each arm | ≥ 20 | 10–19 | < 10 |
   | Treated rows kept after trimming | ≥ 80% | 50–80% | < 50% |
   | CI half-width | ≤ 10 points | 10–20 points | > 20 points |
   | Max standardized difference | ≤ 0.1 | 0.1–0.2 | > 0.2 |

   * The worst band decides.
   * **Borderline** → shown with a warning, at most L2.
   * **Insufficient** → "not estimable for this slice", plus counts (L1) and the nearest supported slice.
   * Slices that were not pre-registered are exploratory (at most L2) even when sufficient. Pre-registered slices use only the opening-based industry (`opening_domain_vote`).

**Papers.**
* Main: Yu, Min, Zettlemoyer & Hajishirzi, *CREPE: Open-Domain QA with False Presuppositions*, **ACL 2023**.
* Supporting: Sharma et al., *Towards Understanding Sycophancy in Language Models*, **ICLR 2024**.

**Code.** The LLM's structured-output (JSON) mode + a JSON-schema validator.

**Output.** `QuerySpec`.

**Loopholes closed:**
* point 8 (metadata inventory);
* point 33 (minimum support);
* leading questions;
* filtering on post-outcome fields.

**Acceptance test.** On dev queries, the filled slots are correct. On the locked test set, every false-premise and unsupported-filter query is handled as expected.

---

### Step 8 — Evidence pack → answer with placeholders

**In plain words.** Code, not the AI, assembles the facts. The AI only writes the prose around them. It cannot type numbers, and it may only use wording allowed for each fact's level.

**The evidence pack**, built by code, contains:

* the Factor-Library rows for the event and slice, each with its level, the allowed phrases for that level, its failed checks and its E-value;
* **before-call drivers**: the share of events starting in the opening, and the most common opening reasons (L1);
* for each factor, 1–2 grounding spans from **different calls**, each with a quote, `turn_uid` and faithfulness line (if Step 5 passed);
* for each factor, the counter-count: *"the behaviour occurred without the event in N of M calls"* (against cherry-picking);
* co-occurring factors;
* **the conversation rationale** (`crest/rationale.py`), computed for the event and the asked slice:
  * *the situation*: problem words customers use in the opening that are over-represented in calls with the event;
  * *the lead-up*: for every behaviour, the share of event calls where it happened in the 6 turns before the event's onset,
    against the share at the same point (the median onset turn) in calls of the same slice without the event. Behaviours at
    least 8 points more frequent before the event are reported as what came before it; behaviours at least 8 points less
    frequent are reported as what was missing; frequent behaviours with no difference are named as not distinguishing;
  * *who starts it* (the event's subtype shares);
  * *the customers' own words*: onset turns that state a reason ("because", "again", "still", "this is the third time", …);
  * *one call, step by step*: the customer's problem, the turn with the main lead-up behaviour, and the event turn, each quoted
    with its `turn_uid`.

  These are descriptive facts about the transcripts (no behaviour is credited with an effect), so they need no factor id
  and use temporal wording only ("in the turns before"). The causal claim, if any, comes from the Factor Library that follows.

**The LLM writes a fixed-shape answer:**

1. a short answer (the rationale above, in one sentence) and the rest of the rationale;
2. before-call drivers;
3. in-call factors, ranked by attributable events — L3 first, then L2 "warning signs";
4. quotes with citations `[call-id:turn]`;
5. what could change — **only for L3, actionable factors**;
6. caveats:
   * assumptions;
   * E-values;
   * *"these behaviours often occur together; their effects are not independent and do not add up"*;
   * *"within this corpus"*.

**Placeholder rules.**
* Numbers are written as placeholders (`{F3.att}`, `{F3.ci}`, `{F3.n_calls}`).
* Every sentence linking a behaviour to an event carries a factor id.
* Every quote carries a `turn_uid`.

**Paper.** Gao et al., *Enabling LLMs to Generate Text with Citations* (ALCE), **EMNLP 2023** — citation format and citation quality only.

**Code.** [princeton-nlp/ALCE](https://github.com/princeton-nlp/ALCE) (prompt formats; `eval.py` for citation metrics).

**Loopholes closed:**
* invented numbers (R7);
* cherry-picked examples (counter-counts);
* overlapping factors presented as separate causes (point 24);
* external validity (point 34).

---

### Step 9 — Three gates before anything is shown

| Gate | Checks | How |
|---|---|---|
| **1 · Numbers** | every number shown comes from a placeholder bound to a library row (with its version) or to a count in the pack; units match (points vs %) | deterministic: any digit typed by the LLM outside quotes and ids fails |
| **2 · Causal-claim licensing** | every sentence linking a behaviour to an event cites a factor id, and its causal strength does not exceed that factor's level | two parts: (i) a **blocklist** of direct-causal phrasings (*causes, leads to, results in, drives, the reason is*) → always fail; (ii) an LLM classifier using the four categories and annotation guidelines of Yu et al. (EMNLP 2019), with few-shot examples from the paper's released data. Rule: L3 → at most *conditional causal*; L2 → *correlational*; L1/L0 → no causal or correlational wording. |
| **3 · Evidence** | every quote is an exact substring of the cited turn's text (after normalisation); every descriptive sentence about calls is supported by its cited turns; every cited item is `raw_dialogue` | deterministic quote match + **AlignScore** above a threshold calibrated on dev queries |

**If a gate fails:**
1. one rewrite, with the failing sentences marked;
2. then the failing sentences are dropped;
3. if the core answer is gone, the system gives an L0 response.

**Papers.**
* Zha et al., *AlignScore*, **ACL 2023** — textual support only.
* Yu, Li & Wang, *Detecting Causal Language Use in Science Findings*, **EMNLP 2019**.

**Code.**
* [yuh-zha/AlignScore](https://github.com/yuh-zha/AlignScore).
* [junwang4/causal-language-use-in-science](https://github.com/junwang4/causal-language-use-in-science) (the paper's code and annotated data).

**Loopholes closed:**
* point 6 (causal-claim verifier);
* point 29 (AlignScore is not a causal or numeric verifier);
* paraphrased "quotes";
* number and unit drift.

**Acceptance test.**
* Adversarial unit tests: a wrong number, "X causes Y", a fake quote, a quote from an analyst note, a correct claim at the wrong level. **All must be caught.**
* The gates' false-rejection rate is measured on dev queries.

---

### Step 10 — Remember the conversation (Task 2)

**In plain words.** Keep a small, explicit notebook for the chat session.

**SessionState** (JSON):
* the current QuerySpec;
* factor ids and `turn_uid`s already shown;
* `library_version` and `index_version`;
* a 3-line summary of the last answer (for the LLM only, never cited);
* the turn count.

**Why.** Systems fail most on later turns and on questions that do not stand alone [MTRAG, TACL 2025]. An explicit state makes carry-over checkable.

**Paper.** Katsis et al., *MTRAG*, **TACL 2025** — motivation here, evaluation in Step 13.

---

### Step 11 — Follow-up → change only what changed (state + delta)

**In plain words.** The AI does not rewrite the whole question. It only says *what changed*. Code applies the change, so filters the user did not mention stay exactly as they were.

**What we do.**

1. **Delta proposal.**
   * The LLM, prompted in the IC-DST style with a few examples, outputs only a JSON **delta**: set or remove operations on known slots, with values from the allowed vocabulary.
   * It also outputs a free-text *retrieval intent*.
   * Example: after "Why do telecom calls escalate?", the follow-up *"what about refunds?"* → `{"event": {"old": "ESC", "new": "REF"}}`.
2. **Code validates** the delta: an unknown slot or value → ask a clarifying question.
3. **Code merges** deterministically: the slots not mentioned (industry, dates) persist.
4. **Re-check support.** The support policy (Step 7) runs again on the new slice.
5. **Retrieval text only.** LLM4CS-style rewriting produces the *retrieval text*. It never sets filters.

**Why this option.**

* *Free rewriting* can silently drop a filter such as "telecom" (point 32).
* IC-DST showed that predicting **state changes** with in-context examples works for few-shot dialogue state tracking.

**Papers.**
* Main: Hu et al., *In-Context Learning for Few-Shot Dialogue State Tracking* (IC-DST), **Findings of EMNLP 2022**.
* Supporting: Mao et al., *LLM4CS*, **Findings of EMNLP 2023** (retrieval text only).

**Code.**
* [Yushi-Hu/IC-DST](https://github.com/Yushi-Hu/IC-DST) (45★).
* [kyriemao/LLM4CS](https://github.com/kyriemao/LLM4CS).

**Acceptance test.** Carry-over tests from the query set, e.g. filters persist after *"what about refunds?"*: 100% correct merges. Ambiguous follow-ups trigger a clarifying question.

---

### Step 12 — Route: reuse, re-filter, look up anew, or clarify

| Move | When (rule on the delta) | What runs |
|---|---|---|
| a · reuse | no slot changed ("explain the second factor") | answer from the pack already shown |
| b · re-filter | a filter changed | new slice → support policy → library lookup (pre-registered slice or exploratory estimate) → new pack |
| c · new lookup | the event or question type changed | Steps 7–9 with the merged state |
| d · clarify | invalid or ambiguous delta, or low parser confidence | one short question |

* **Cache key** = hash of (QuerySpec, `library_version`, `index_version`, `prompt_version`). A change to the library or index can never return a stale answer.
* **Paper:** Roy et al., *Learning When to Retrieve, What to Rewrite, and How to Respond in Conversational QA*, **Findings of EMNLP 2024**. It is implemented as the rules above, with no training.

---

### Step 13 — Measure quality

| What | Metric (all with 95% bootstrap CIs; follow-ups resampled by session) | Paper |
|---|---|---|
| event labels (Step 1) | inverse-probability-weighted precision/recall/F1 on gold; onset ±1 accuracy; κ | TnT-LLM; DSL |
| causal pipeline (Step 4) | planted-effect bias and coverage; null false-alarm rate; negative controls; dev/test agreement | Dorie et al. 2019 |
| evidence (Step 5) | grounding precision (human, 30 spans); forecaster AUC and calibration; comprehensiveness vs random baseline | ERASER |
| search (Step 6) | call-level Recall@10, nDCG@10 | RRF |
| answers (Steps 8–9) | citation precision/recall; share of sentences removed by each gate; judged correctness, groundedness, **calibration of claim strength** and usefulness | ALCE; AlignScore |
| follow-ups (Steps 10–12) | slot carry-over accuracy; correct route; faithfulness on later turns; clarify/refuse on ambiguous and unanswerable queries | MTRAG |
| practicality | seconds and tokens per answer | — |

**Baselines**, run on the **locked test** queries:

* **B0** plain RAG: retrieve windows → LLM answer, with no library and no gates;
* **B1** the full system without the gates;
* **B2** the full system with free question rewriting instead of state + delta;
* **B3** an "associational library" of raw rates instead of Step 4 estimates.

**Ablations:** remove the call-level collapse/MMR, the presupposition check, the support policy.

**Judge.**
* A **different model family** from the answer writer, because judges favour their own outputs [Panickssery et al., NeurIPS 2024].
* A fixed rubric, and answer order swapped when comparing two answers [Zheng et al., NeurIPS 2023].
* A **human audit** of at least 30 answers. Judge scores are corrected with the human audit by prediction-powered inference, as in ARES [Saad-Falcon et al., NAACL 2024; Angelopoulos et al., Science 2023].

**Significance** between systems uses paired bootstrap tests [Dror et al., ACL 2018].

**Code.**
* [IBM/mt-rag-benchmark](https://github.com/IBM/mt-rag-benchmark).
* [stanford-futuredata/ARES](https://github.com/stanford-futuredata/ARES) (733★).
* [aangelopoulos/ppi_py](https://github.com/aangelopoulos/ppi_py) (301★).

---

### Step 14 — The query dataset (dev and locked test)

**What we do.**

1. **Grid** of question kinds:
   * task — first question / follow-up;
   * type — lookup, count, why, compare, trend, what to change, ambiguous, unanswerable, **false presupposition**, **leading question**, **unsupported filter**, **tiny subgroup**;
   * event;
   * difficulty.
2. Write 2–3 seeds per cell. An LLM writes variants, and near-duplicates are dropped (ROUGE-L ≥ 0.7) [Self-Instruct].
3. Simulate follow-ups for about 10 sessions (1 seed + 2–3 follow-ups each) [Kiesel et al.].
4. **Human review** of every question: realistic? answerable from *this* data? right category? expected behaviour (answer / clarify / refuse / correct the premise)?
5. **Split, before any system tuning:**
   * about **60 dev** queries (tuning allowed);
   * about **30 locked test** queries, stratified by category, whose file hash is committed.

   The test queries are **never** used to tune prompts, retrieval, routing, thresholds or answer format [Kapoor & Narayanan, Patterns 2023]. They are run once at the end.
6. For about 30 queries, store the correct calls and proof lines (feeds Step 13).

**Output.**
* `queries_dev.jsonl`, `queries_test.jsonl`.
* `outputs.jsonl`: the system's answers with evidence packs and gate logs — the "query dataset and outputs" deliverable.

**As built** (details in [`QUERY_DATASET.md`](QUERY_DATASET.md)):

* **No LLM writes the questions.** Templates are filled from the data (industries, brands, and Factor Library
  behaviours, so each premise's correct answer is known), plus hand-written items. This keeps the set offline and
  reproducible.
* **Realism checks:** a human review sheet (`queries_review.csv`) and an optional LLM judge (`evaluate --llm`; question
  texts only, brands masked).
* **Added categories:** product improvement, ranking, explicit multi-hop chains, out of scope, and a separately
  reported **known limitation** category.
* **Tags:** every query is tagged by task, difficulty, kind and use case.
* **Readable outputs:** `outputs/QUERY_OUTPUTS.md`.

**Papers.**
* Wang et al., *Self-Instruct*, **ACL 2023**.
* Kiesel et al., *Simulating Follow-Up Questions in Conversational Search*, **ECIR 2024**.

---

## 7 · End-to-end integrity: contracts between steps

### 7.1 Interface contracts

Each hand-off has a contract and an automated check. A failing check blocks the downstream step.

| From → to | Artifact | Contract | Automated check |
|---|---|---|---|
| 0 → all | `cleaned_data/` | unique `turn_uid`; split locked by template group; every column classed; flagged metadata never usable | 19 notebook checks; 14 tests |
| 1 → 2, 4 | `events.parquet`, `gold.parquet` | onset exists and its quote matches; events from the taxonomy; gold from held-out only, with inclusion probabilities | quote-match rate = 100%; zero overlap between the gold and development-sample calls |
| 2 → 4, 5 | `risk_sets/…` | covariates from turns < *k* only; no row at or after onset; ≤ 1 treated row per call × behaviour | future-invariance test; eligibility asserts |
| 3 → 2, 4 | `behaviours.yaml`, occurrences | exclusion sign-off; outcome-blind; precision ≥ 0.8 | blindness test; precision table |
| 4 → 6, 8, 9 | `factor_library.parquet` | level computed by code; `prereg_hash` matches the committed file; versioned | schema validation; hash comparison |
| 5 → 6, 8 | `evidence_spans.parquet` | span before onset; behaviour present; cross-fitted scores | asserts; faithfulness table |
| 6 → 8 | index + graph | provenance on every row; no quarantined or metadata text quotable | index test |
| 7, 10–12 → 8 | QuerySpec / SessionState | slots from the vocabulary; filters allowed by R3; support computed | schema validation; carry-over tests |
| 8 → 9 | draft answer | placeholders only; factor id on every causal sentence; `turn_uid` on every quote | Gates 1–3 |
| 9 → user | final answer | all gates pass, or the answer is degraded | gate log saved with the answer |

### 7.2 One query, followed end to end

1. **"Why do escalations happen in telecom calls?"** (Task 1).
   * **Step 7:** `{event: ESC, filters: {industry: telecom (opening_domain_vote)}, type: why}`.
   * **Support policy:** if the telecom slice was not pre-registered, its estimates are exploratory (at most L2). If support is insufficient, the answer gives the overall ESC factors plus telecom counts, labelled accordingly.
   * **Step 8:** the pack gets:
     * the ESC library rows, with their levels;
     * the share of ESC starting in the opening, and the top opening reasons;
     * two telecom grounding spans per factor, from different calls;
     * the counter-counts.
   * The LLM writes the answer with `{F…}` placeholders.
   * **Step 9:** the gates pass. The final answer shows L3 factors as "estimated to raise …, under the assumption that …" and L2 factors as "warning signs".
2. **"what about refunds?"** (Task 2).
   * **Step 11:** delta `{event: ESC → REF}`. The merge keeps `industry: telecom`.
   * **Step 12:** route (c), new lookup.
   * **Step 7:** support is re-checked for REF × telecom.
   * **Steps 8–9** run again.
3. **"so apologising causes refunds, right?"**
   * The presupposition check looks up "apology → REF". Suppose the row is L2, or has the opposite sign.
   * The answer first corrects the premise ("the data does not show that …"), then states what is supported, at its level.

### 7.3 When something fails

| Situation | What the system does |
|---|---|
| No factor reaches L3 for an event | shows L2 warning signs and L1 facts, and says no behaviour passed the causal checks |
| Slice support is insufficient | "not estimable for this slice" + counts + the nearest supported slice |
| Filter not in the data | says so; does not guess |
| Filter on a flagged field (e.g. `reason_for_call`) | declines; offers the opening-based equivalent |
| The question's premise contradicts the library | corrects it first |
| A gate fails twice | drops the failing sentences; L0 if the core answer is gone |
| Fewer than two examples for a factor | the factor is shown without examples, or dropped from the pack |
| Ambiguous follow-up | a clarifying question |
| Library or index updated mid-session | cache miss → recompute; the answer cites the new version |
| LLM unavailable, or data rules forbid external APIs | a local open-source model; if none, template-only answers (numbers + quotes, no narrative) |

---

## 8 · Verdict on the 35 review points

Parts of the pasted review arrived with blank code blocks, e.g. in points 20, 25, 27 and 31. Their meaning was inferred from the surrounding text.

**The ten proposed fixes**

| # | Point | Verdict | What v2 does |
|---|---|---|---|
| 1 | Locked conversation-level split | **Agree** | split locked by template group before any labelling (built) |
| 2 | Template clustering + cluster-robust inference | **Agree — "incomplete" is right** | grouping *before* the split (built) + template-cluster standard errors + cluster bootstrap (Step 4) |
| 3 | Audit `intent` (and `reason_for_call`, `domain`) | **Agree** | content + predictive leakage audit, availability registry (built); metadata out of the primary adjustment regardless (R3) |
| 4 | No post-treatment adjustment (total length) | **Agree** | covariates from turns < *k* only; future-invariance test |
| 5 | Hazard risk meter with censoring | **Agree, with a nuance** | a forecasting tool only. The call ending is a *terminal state* (part of the outcome), **not censoring**; only truncated transcripts are censored. |
| 6 | Causal-claim verifier | **Agree (essential)** | Gate 2 + claim ladder; Gate 1 for numbers |
| 7 | Locked query test set + baselines + ablations | **Agree** | Steps 13–14 |
| 8 | Metadata inventory + unsupported filters | **Agree** | registry (built) + support policy (Step 7) |
| 9 | Reranker | **Agree: optional** | not in the plan; a cross-encoder could be added after the deadline |
| 10 | Minimum viable system first | **Agree** | Task 1 end-to-end before the Task 2 extras (§12) |

**Loopholes 11–35**

| # | Point | Verdict | What v2 does (where) |
|---|---|---|---|
| 11 | Behaviour is not a well-defined treatment | **Agree** | estimand card (point intervention at turn *k*, natural course after); actionability tag; customer states capped at L2 (Steps 2–4) |
| 12 | Time-varying confounding | **Partly agree — corrected** | Right for v1's window-level treatments. But for a **single-turn** treatment with the **full history** adjusted for, standard adjustment is valid at each landmark (sequential trials, Keogh 2023). G-methods are needed only for *sustained* strategies ("never refuse"), which v2 does not claim. |
| 13 | "Before" ≠ "cause" | **Agree** | ordering is only an eligibility rule; the causal route runs only through Step 4 + checks + ladder |
| 14 | Deletion test is too strong | **Agree** | renamed to faithfulness; three separate claims (Step 5) |
| 15 | Sufficiency test is out-of-distribution | **Agree** | dropped; removal vs neutral replacement vs random-removal baseline; dropout training (Hase et al. 2021) |
| 16 | Circular event labels | **Agree** | exclusion lists (Step 1) + filter (Step 3) |
| 17 | Mixed outcome types | **Agree** | explicit taxonomy; three confirmatory "episode onset" events; granted/denied/cancelled as secondary (Step 1) |
| 18 | Several events per call | **Agree, different default** | all onsets stored in order. Earlier *other* events are history covariates (valid, since they precede *k*). The "exclude" version runs as sensitivity S5. The call ending is the only competing event and is part of the outcome (Young et al. 2020). |
| 19 | 3:1 matching is not enough | **Agree** | matching replaced by DML + overlap trimming + balance; "not estimable" when they fail |
| 20 | Length at the risk time | **Agree** | "turns so far" only |
| 21 | Pseudo-label contamination | **Agree** | development sample from train, gold from held-out |
| 22 | Two evaluation populations | **Agree** | over-sampled development set vs stratified gold with known rates; weighted metrics |
| 23 | Discovery can leak the event | **Agree** | exclusion → pre-treatment check → de-duplication → **outcome-blind measurement** (added) |
| 24 | Correlated behaviours | **Agree** | families, co-occurrence stored, wording rule |
| 25 | Multiple-testing family | **Agree** | pre-registered family ≤ 36 tests, BH over it; subgroups exploratory |
| 26 | Cluster bootstrap as a second check | **Agree** | template-cluster standard errors + cluster bootstrap of the score |
| 27 | Retrieval duplicates evidence | **Agree** | one window per call, MMR, counts from tables |
| 28 | Provenance | **Agree** | provenance on every row; citation rules R9 |
| 29 | AlignScore is not the final gate | **Agree** | three gates; AlignScore only inside the evidence gate |
| 30 | Same LLM as writer and judge | **Agree** | judge from another model family + human audit + PPI correction |
| 31 | Locked query test set | **Agree** | ~30 locked test queries, hash committed |
| 32 | State + delta follow-ups | **Agree** | IC-DST-style delta, deterministic merge (Step 11) |
| 33 | Unsupported filters / minimum support | **Agree** | support policy using event counts + overlap + CI width + balance |
| 34 | External validity | **Agree** | "within this corpus" in every L2/L3 statement; §13 |
| 35 | `reason_for_call` is dangerous | **Agree, now measured** | leakage audit built and tested. Either way (pre-call reason or post-call summary), it stays out of the causal core (R3). |

**The proposed architecture** is adopted (§3). v2 adds:

* the gold-set/DSL loop;
* the availability registry and the future-invariance test;
* pre-registration;
* the presupposition check;
* the claim ladder.

The leakage audit runs *after* the split is locked because it must use non-test calls only; its results change which columns may be used, not the split.

**The ten must-fixes before Step 4:**

| # | Must-fix | Status |
|---|---|---|
| 1 | Locked conversation-level split | built |
| 2 | Template grouping before the split | built |
| 3 | Full metadata audit | built |
| 4 | Event definitions and onsets | Step 1 |
| 5 | Exclude definitional behaviours | Steps 1 and 3 |
| 6 | No post-event controls | Step 2 + test |
| 7 | Defined treatments | Steps 2–4 |
| 8 | Time-varying confounding handled, with honest wording | Steps 2 and 4, §2 |
| 9 | Causal estimation separated from evidence | Step 5 |
| 10 | Locked query test set + baselines | Steps 13–14 |

**The wording change** is adopted verbatim (§2). **The paper roles** are adopted (§10).

## 9 · Additional loopholes found and closed

| # | Loophole | Why it matters | Fix (where) |
|---|---|---|---|
| X1 | v1 picked control windows using the event calls' onsets | immortal-time bias [Hernán et al., JCE 2016] | landmark risk sets (Step 2) |
| X2 | Whole-call columns (`rel_position`, `phase`, `n_turns`, QC flags) look innocent but use the future | post-treatment leakage | availability registry (built) + future-invariance test |
| X3 | Filtering on a field possibly written after the call | selection bias [Hernán et al., Epidemiology 2004] | filters only on `opening` / unflagged fields (Step 7) |
| X4 | LLM label errors in the outcome | biased effects, false precision | DSL correction with the gold set (Steps 1, 4) |
| X5 | Behaviour labels produced while seeing the call's ending | error that depends on the outcome → bias in any direction | outcome-blind detectors + blindness test (Step 3) |
| X6 | Turn *k*'s own text among the covariates | overlap violation [Gui & Veitch, ICLR 2023] | covariates from turns < *k* only |
| X7 | Unmeasured confounders (agent identity, customer history, policy) | residual bias | negative controls, E-values, wording (Step 4) |
| X8 | Wrong roles in name-labelled calls | agent behaviour counted as customer's | sensitivity S2 |
| X9 | Truncated transcripts | unknown outcomes | censoring rule + S3 |
| X10 | Invented onset turns | wrong risk sets | quote check (Step 1) |
| X11 | Tuning on held-out calls or test queries | optimistic numbers [Kapoor & Narayanan 2023] | pre-registration hash; locked queries |
| X12 | Estimator bugs, wrong error bars | silent failure | planted-effect and null tests [Dorie et al. 2019] |
| X13 | Stale cached answers in Task 2 | wrong numbers after an update | versioned cache key (Step 12) |
| X14 | Leading or false-premise questions | the AI agrees with the user | presupposition check + sycophancy guard (Step 7) |
| X15 | Metrics without error bars | over-reading small differences | bootstrap CIs, clustered by session [Dror et al. 2018] |
| X16 | Non-reproducible LLM steps | results cannot be checked | pinned model, prompt hashes, response cache keyed by the prompt hash, run manifest (R10, C10) |
| X17 | Faithfulness scored on training calls | inflated faithfulness | cross-fitted forecaster (Step 5) |
| X18 | Paraphrased "quotes", number/unit drift | fabricated evidence | exact-substring quote gate; placeholders (Step 9) |
| X19 | Human gold anchored on AI labels | inflated agreement | blind labelling; κ |
| X20 | Trimming silently changes the population | the estimate describes a different group | share kept reported; < 50% kept → not estimable |
| X21 | Learned transforms fitted on all splits | test text shapes features | train-only fitting (built) |
| X22 | Events already present in the opening | cannot be explained by in-call behaviour | excluded from risk sets, reported as before-call drivers |
| X23 | Counting search hits instead of calls | inflated counts | counts from tables, at call level |
| X24 | Cherry-picked examples | one-sided evidence | counter-counts in every pack |
| X25 | Copyrighted data sent to an external API against the rules | policy breach | check the hackathon rules; local model option |
| X26 | Agent talks *about* escalation (topic, negation, conditional offer, routing to a department) and the labeller counts it | escalation precision 0.50 on the gold sample | labeller v2: a handoff to a named senior person, or an offer the customer accepts ([`REAL_DATA_REVIEW.md`](REAL_DATA_REVIEW.md) §3) |
| X27 | Hedged churn and named competitors missed (*I might look elsewhere*, *I'd rather go with [competitor]*) | churn recall 0.29 | labeller v2: intent word + competitor/"elsewhere"; prospects, negations and regret excluded |
| X28 | Calls with no industry word in the opening fall out of every industry filter | *in hotel calls* undercounts | unknown industry filled from the greeting's brand majority (opening-only) |
| X29 | Misspellings, slang and non-English questions found no event | clarify instead of an answer | spelling, slang and language word lists; the answer says how the question was read (Step 7) |
| X30 | Thresholds, policy dates, conditions between events and brand names were misread or ignored | a different question answered silently | threshold check against estimate and CI; date clarify then before/after; *who were refused a refund* → condition; brand spans removed first (Step 7) |
| X31 | Trend, product, shared, event-link and factor answers had no reasoning | "only numbers" | rationale in every answer type; behaviour profiles for behaviour-only questions (Step 8) |
| X32 | Word lists cover few languages and are untested | silent misreadings of non-English or noisy questions | language identification, phrase tables for six languages, corpus-protected spelling correction, LLM normalisation when configured, and a dev/test parser benchmark (`parser-bench`) ([`REAL_DATA_REVIEW.md`](REAL_DATA_REVIEW.md) §7.1) |
| X33 | Rule-based churn misses threats without intent words; broad "risk" mixed into churn | churn recall 0.56; definitions blurred | rules + disengagement + a weakly supervised semantic layer trained on train-split rule labels; retention risk as a separate secondary event (§7.2) |
| X34 | Customer tier inferred from what customers say | self-reports treated as facts | real tier, plan, segment and tenure from `account_attributes.csv` when present; self-reported status kept as a separate, labelled variable (§7.3) |
| X35 | Before/after comparison ignores pre-trends, seasonality and autocorrelation | a drift or a weekly cycle read as a change at the date | interrupted time series (level and slope change, seasonal terms, Newey–West intervals with a classical floor), placebo dates, comparison series (§7.4) |
| X36 | Questions about one call, several conditions, "no effect", sub-group effects and one-call counterfactuals answered as something else | a different question answered silently | single-call answers, several conditions, the "no clear effect" list (an interval that includes zero is not proof of no effect), and notices for effect modification and one-call counterfactuals (§7.5) |

## 10 · Paper roles: what each paper licenses — and what it does not

| Paper | Used for | **Not** used for |
|---|---|---|
| TnT-LLM (KDD 2024) | LLM-sample → labeller pipeline | proving labels are correct (the gold set does that) |
| DSL (NeurIPS 2023); PPI (Science 2023) | valid estimates and CIs despite labeller or judge error | fixing confounding |
| Target trial (AJE 2016); sequential trials (Stat. Med. 2023) | the comparison design and time zero | removing unmeasured confounding |
| DML (Econometrics J. 2018); DoubleML (JMLR 2022) | estimating the effect with flexible models and valid CIs | identification: that rests on assumptions |
| Egami et al. (Sci. Adv. 2022) | discover on train, confirm on held-out | — |
| D5 (NeurIPS 2023) | *proposing* behaviours | causal claims (D5 finds correlations) |
| CRAFT (EMNLP 2019); CGA (ACL 2018) | turn-by-turn *forecasting*; precedent for looking before the event | deciding which turn caused the event |
| ERASER (ACL 2020); Hase et al. (NeurIPS 2021) | *faithfulness* of the forecaster | real-world causality |
| ALCE (EMNLP 2023) | citation format and citation quality | verifying causal claims |
| AlignScore (ACL 2023) | whether cited turns support a descriptive sentence | numbers; causal licensing |
| Yu et al. (EMNLP 2019) | classifying the *strength* of causal wording | whether the claim is true |
| CREPE (ACL 2023); Sharma et al. (ICLR 2024) | detecting false premises; guarding against agreeing | — |
| IC-DST (Findings EMNLP 2022) | follow-up as a state change | retrieval |
| LLM4CS (Findings EMNLP 2023) | retrieval text for follow-ups | setting filters |
| Roy et al. (Findings EMNLP 2024) | when to reuse or retrieve | — |
| MTRAG (TACL 2025) | multi-turn evaluation design | — |
| Zheng et al. (NeurIPS 2023); Panickssery et al. (NeurIPS 2024); ARES (NAACL 2024) | judge biases and judge correction | replacing the human audit |
| Corr2Cause (ICLR 2024) | why the LLM never decides causality | — |

## 11 · Deliberately not used

| Idea / paper | Why not |
|---|---|
| Marginal structural models / g-computation for *sustained* strategies ("never refuse") | These are the right tool for that question, but it is not the deadline's question. v2 estimates single-turn decisions and says so. Listed as the research extension. |
| Training rationale networks (Causal Rationalization, ICML 2023; MCD, NeurIPS 2023) | need reliable labels and GPU time; v2 makes no causal-rationale claims |
| Emotion-cause and utterance-causality models (CausalDialogue, EMNLP 2023 causal discrimination, IEEE TKDE 2024) | model emotions or reply generation, not business outcomes |
| CauseMotion | needs audio; this data is text only |
| Causal-forest subgroup search | invites subgroup fishing; subgroups are pre-registered or exploratory |
| Rerankers | useful engineering, not a safeguard (point 9); optional later |
| Long-term memory frameworks (RMM, SeCom, Memoria) | built for weeks-long chats; a session needs a small explicit state |
| Training a conversational retriever (HAConvDR) | needs supervised training data |
| Causal-discovery algorithms (GRaSP etc.) | unstable with dozens of behaviours |
| Causal agents (OrcheCause, AAAI 2026) | no public code; a fixed, auditable pipeline is safer |
| GraphRAG-style LLM-built graphs | costly over ~18M tokens; our graph is built deterministically |
| Papers from weak or unverifiable venues | see Appendix A |

## 12 · Plan to the deadline (Wed 30 Sep, 11:59 PM)

The work splits into three parallel tracks:

* **A** — labels and causal analysis;
* **B** — search, answering and Task 2;
* **C** — gold labels, queries, evaluation and report.

| When | Track A | Track B | Track C |
|---|---|---|---|
| **Tue 29, morning** | Step 0 on the real file + checklist (audit, template threshold). Write `event_definitions.yaml` + exclusion lists + labelling prompt; start the development sample (train). | Index v1 (windows, BM25 + embeddings, RRF, call collapse). | Draw the gold sample (held-out, stratified); start **blind** gold labelling. |
| **Tue 29, afternoon** | Quote check, onset detectors. Step 2 risk-set builder + future-invariance test. | QuerySpec schema, support policy, presupposition check; evidence-pack builder with placeholders. | Query grid + seeds; **split dev / locked test and commit the hash**. |
| **Tue 29, evening** | Step 3 exclusions, blindness test, precision checks (D5 optional). **Pilot** Step 4 on train + planted-effect test. | Gates 1–3 + adversarial unit tests. | Finish gold labelling + κ. |
| **Tue 29, night** | **Freeze and commit `prereg.yaml`.** | Task 1 end-to-end on dev queries. | Report skeleton. |
| **Wed 30, morning** | **Confirm once** on held-out: DSL correction, checks, levels → Factor Library v1. | Task 2: state + delta, router, versioned cache. | Human review of queries; gold evidence for ~30. |
| **Wed 30, afternoon** | Step 5 grounding (+ faithfulness if time). | Bug fixes using **dev queries only**. | Run the **locked test** once; metrics + CIs; judge + human audit; baselines. |
| **Wed 30, evening** | — | Demo. | Report + slides; **2-hour buffer**. |

**The minimum version is still loophole-free.** If time runs out, claims fall to lower levels automatically; nothing is overstated. The minimum version is:

* keyword onsets confirmed by the LLM, 150 gold calls, DSL correction;
* landmark risk sets;
* Step-0 cues only, minus exclusions;
* DoubleML ATT with overlap, balance, BH, negative controls, E-values and sensitivities S2, S5, S8;
* levels computed by code;
* grounding spans only;
* hybrid search with call collapse;
* the three gates;
* state + delta with four slots;
* locked test queries + baseline B0.

## 13 · Limits that remain, stated in every report

1. **Unmeasured confounding.** Estimates assume that the history before turn *k* captures everything that drives both the behaviour and the event. Agent identity, customer history and company policy are not fully observed. E-values say how strong a hidden factor would need to be; negative controls look for signs of one.
2. **Single-turn decisions, not policies.** "Refusal at that moment" is not "never refusing". The second question needs g-methods (§11).
3. **This corpus.** The calls look partly template-generated (e.g. an intent named "Churn Prediction"). Results describe *this* corpus, not real customers everywhere.
4. **Text only.** There is no audio and there are no timestamps: silences and tone are approximated by holds, pauses and words.
5. **Label error.** DSL corrects the outcome labels on average. Onset timing errors are handled by S8, not removed.
6. **The LLM's prose.** It is constrained by gates, but a human should read answers before business decisions.

---

## 14 · Corrections made while building (v2.1)

Building the system and testing it on a synthetic corpus whose causes are **known** (an oracle computes every true
effect) showed where v2 was wrong or under-specified. Each row below is now part of the method. Details, numbers and
the tests that prove each point are in [`IMPLEMENTATION.md` §4](IMPLEMENTATION.md#4--corrections-to-methodology-v2-found-while-building-and-testing).

| # | Area | v2 | v2.1 | Why |
|---|---|---|---|---|
| C1 | Step 2 population | moments after another event kept, events as covariates; "clean" = S5 | **clean moments are the primary population**; the old primary is S5 | after an escalation, agent behaviour is part of the handoff (a compound treatment; Hernán & VanderWeele, Epidemiology 2011); the simulation showed bias there |
| C2 | Step 4 balance | every covariate SMD ≤ 0.1 | prognostic-score SMD ≤ 0.1 (Stuart et al. 2013); covariate SMDs reported | the maximum over ~100 SMDs is sampling noise at held-out sizes |
| C3 | Step 4 DSL | correct the outcome | correct each call's whole score contribution (numerator and denominator) | the labeller also decides which moments are at risk |
| C4 | Step 4 learners | pick the family by loss | tune regularisation on train, then pick; Newton–Cholesky solver | untuned logistic weights overfitted; 3× faster pilot |
| C5 | Step 2 truncation | censor flagged calls in the main analysis | main analysis treats transcripts as complete; S3 drops flagged calls | the flag mostly marks closing-only truncation |
| C6 | Step 4 L3 rule | sign stable across S2, S5, S8 | S2, S3, S5, S8 required | truncation is a real threat here |
| C7 | Step 4 planted test | fixed thresholds, most frequent behaviours | Monte-Carlo-aware thresholds; 100 simulations per pair; the train subsample grows when too small; only behaviours estimable with enough overlap are used | a correct estimator failed the fixed thresholds by chance; a behaviour present in every call cannot test anything |
| C8 | Step 3 prevalence | 2% of rows | 2% of risk-set calls | at most one treated row per call |
| C9 | Step 4 negative controls | cap on any CI excluding 0 | kept, with its ≈10% per-event false-alarm rate stated; slices inherit the all-calls status | deliberate caution, now quantified |
| C10 | R10 | temperature 0 | response cache keyed by the prompt hash + call log | current models take no sampling parameters |
| C11 | Step 5 | a span's removal should lower the forecast | direction-aware (protective behaviours raise it) | offers scored at chance otherwise |
| C12 | Step 8 wording | L2 = "associated with" | L2 with a CI including 0 = "no clear difference" | avoid implying a direction the data does not show |
| C13 | Step 1/3 | behaviours counted everywhere | event-specific occurrence filters (money-mentioning offers are part of a refund episode) | an event cannot explain itself (R4) |
| C14 | Step 0 | repeated words collapsed | a repeated word that starts a discourse marker is kept ("thank you you know") | the collapse destroyed phrases before cue matching |
| C15 | files | YAML | canonical JSON + SHA-256 lock | fewer dependencies |
| C16 | Step 4 L3 rule | precision checked in Step 3 | L3 also requires verified detector precision (check 11) | unverified detectors could otherwise reach L3 |
| C17 | Step 4 negative controls | a control that cannot be estimated fails the check | at least one control must be estimable and every estimable one must cover 0; `pilot` warns early | one rare control phrase would otherwise veto every claim, although it is evidence of nothing |
| C18 | Step 4 planted test | bias within max(1 point, 2.5 MC s.e.) | bias may also reach 0.4 × the estimates' median standard error (Collins, Schafer & Kam 2001); standardized bias reported | a 0.3-SE bias with correct coverage failed an absolute 1-point rule |
| C19 | Step 0 split | MinHash from a package | MinHash-LSH implemented in the notebook, pairs confirmed by exact Jaccard; the split hash is frozen into the pre-registration | two package versions gave two different locked splits for the same data |
| C20 | Step 9 evidence gate | exact quotes + AlignScore | exact quotes + lexical support ≥ 0.5 for sentences that cite turns without quoting; AlignScore is not used | every template sentence either quotes exactly or carries its numbers through placeholders, so a 355M-parameter model adds cost without a case to check |
| C21 | Step 4 outcome model | predictions used as fitted | predictions clipped to [0, 1] | the outcome is binary; an unclipped linear model gave an estimate beyond +100 points |

C17–C21 came from a robustness review: the whole chain was run on a fixture with the real data's defects and no gold
labels, on 20,000 calls, and on the oldest supported library versions. That review also fixed the engineering
failures listed in [`IMPLEMENTATION.md` §4b](IMPLEMENTATION.md#4b--failures-found-by-the-robustness-review-and-their-fixes).

## Appendix A — Verification of the 26 papers from the team's list

Checked on 2026-09-28 against the ACL Anthology, PMLR, NeurIPS / ICLR / AAAI proceedings, ACM DL, IEEE Xplore, Springer and Taylor & Francis.

Key to the "Top venue?" column:

* ✅ top conference or journal
* ⚠️ peer-reviewed but a demo, industry or non-core venue
* ❌ workshop, preprint only, or weak venue

| # | Paper (as you listed it) | What we found | Top venue? | Used? |
|---|---|---|---|---|
| 1 | Towards Trustworthy Explanation: On Causal Rationalization — "Zhang et al., ICML 2023" | Correct: **ICML 2023** (PMLR 202), W. Zhang, T. Wu, Y. Wang, Y. Cai, H. Cai. [paper](https://proceedings.mlr.press/v202/zhang23ap/zhang23ap.pdf), [code](https://github.com/onepounchman/Causal-Retionalization) | ✅ | **Context only in v2.** v1 used it to define a "causal rationale"; v2 makes no causal-rationale claims (Step 5 measures faithfulness only) |
| 2 | D-Separation for Causal Self-Explanation — "Wu et al., NeurIPS 2023" | **NeurIPS 2023** is right, but the authors are **W. Liu, J. Wang, H. Wang et al.**, not "Wu et al." [paper](https://proceedings.neurips.cc/paper_files/paper/2023/hash/87e82678c0d6e5b729398426f82e9af6-Abstract-Conference.html), [code](https://github.com/jugechengzi/Rationalization-MCD) | ✅ | No — needs a trained rationaliser (§7) |
| 3 | CausalDialogue — "Tuan et al., ACL Findings 2023" | Correct: **Findings of ACL 2023**. [paper](https://aclanthology.org/2023.findings-acl.792/), [code](https://github.com/Pascalson/CausalDialogue) | ✅ | No — for training reply generators |
| 4 | Causal-ESC — "ACL 2026" | Correct: **ACL 2026 (long)**, Wang et al. [paper](https://aclanthology.org/2026.acl-long.886/) | ✅ | Supports the choice of doubly robust estimation (Step 4) |
| 5 | Decoding the Flow: CauseMotion — "arXiv 2025" | arXiv 2501.00778; an IEEE conference version also exists (exact venue not confirmed). Uses **audio** features. [arXiv](https://arxiv.org/abs/2501.00778) | ⚠️ | No — text-only data |
| 6 | How to Enhance Causal Discrimination of Utterances — "EMNLP 2023" | Correct: **EMNLP 2023**, H. Chen, X. Yang, J. Luo, W. Zhu. [paper](https://aclanthology.org/2023.emnlp-main.33/) | ✅ | No — emotion-cause model training |
| 7 | Evidence Contextualization and Counterfactual Attribution (RAGONITE) — "SIGIR 2025" | **Wrong venue:** it is a **WSDM 2025 demo** paper (Saha Roy et al.). [paper](https://dl.acm.org/doi/10.1145/3701551.3704126), [demo list](https://www.wsdm-conference.org/2025/accepted-demonstrations/), [code](https://github.com/Fraunhofer-IIS/RAGonite) | ⚠️ (demo) | Its counterfactual-attribution idea is echoed in Step 5's faithfulness score (model-level only); not a dependency |
| 8 | Fast Evidence Extraction for Grounded LM Outputs — "ACL 2024" | **Wrong venue:** **FEVER workshop 2024** (Mani, Liang, Lipton), not the ACL main conference. [paper](https://aclanthology.org/2024.fever-1.24/) | ❌ (workshop) | No |
| 9 | Unleashing Potential of Evidence in Knowledge-Intensive Dialogue Generation — "IEEE 2025" | arXiv 2023 plus an IEEE conference paper in 2025. About reply generation. [IEEE](https://ieeexplore.ieee.org/iel8/10887540/10887541/10890206.pdf) | ⚠️ | No |
| 10 | Customer Service Hot Event Discovery (CShe-D) — "ACM CACML 2023" | Exists: ACM CACML 2023 proceedings. [paper](https://dl.acm.org/doi/fullHtml/10.1145/3590003.3590011) | ❌ (not a top venue) | No |
| 11 | Implicit Life Event Discovery from Call Transcripts — "IEEE 2019" | **IEEE Access** 2019 (Ebadi, Lwowski, Jaloli, Rad). Needs multi-call customer histories. [paper](https://ieeexplore.ieee.org/document/8908668/) | ❌ (mega-journal) | No |
| 12 | Causal discovery & counterfactual reasoning for persuasive dialogue policies — "Tandfonline 2026" | *Behaviour & Information Technology* (Taylor & Francis), vol. 45; also arXiv 2503.16544. Reinforcement-learning policy work. [paper](https://www.tandfonline.com/doi/full/10.1080/0144929X.2025.2478276) | ⚠️ (not core ML/NLP) | No |
| 13 | Learning a Structural Causal Model for Intuition Reasoning in Conversation — "IEEE 2024" | **IEEE TKDE 2024** (H. Chen et al.). [paper](https://ieeexplore.ieee.org/document/10388481/) | ✅ | No — heavy latent-variable model |
| 14 | OrcheCause Agent — "AAAI 2026" | Correct: **AAAI 2026** (J. Yang, J. H. Kim, J. Lyu, S. Lee, W. Lim). [paper](https://ojs.aaai.org/index.php/AAAI/article/view/42397) | ✅ | No — no public code found; general-purpose |
| 15 | RMM: Reflective Memory Management — "Tan et al., ACL 2025" | Correct: **ACL 2025 (long)**. [paper](https://aclanthology.org/2025.acl-long.413/) | ✅ | No — long-term personal memory |
| 16 | Memoria — "IEEE 2025" | 5th International Conference on AI-ML-Systems 2025 (IEEE), plus arXiv. [IEEE](https://ieeexplore.ieee.org/document/11330332/) | ❌ (not a top venue) | No |
| 17 | SeCom — "ICLR 2025" | Correct: **ICLR 2025** (Microsoft). [paper](https://proceedings.iclr.cc/paper_files/paper/2025/hash/e56f394bbd4f0ec81393d767caa5a31b-Abstract-Conference.html), [code](https://github.com/microsoft/SeCom) | ✅ | No — long-term memory; sessions here are short |
| 18 | HAConvDR — "Mo et al., ACL Findings 2024" | Correct: **Findings of ACL 2024**. [paper](https://aclanthology.org/2024.findings-acl.792/), [code](https://github.com/fengranMark/HAConvDR) | ✅ | No — needs supervised training |
| 19 | RECOR — "Ali et al., ACL Findings 2026" | **Findings of ACL 2026** is correct. [paper](https://aclanthology.org/2026.findings-acl.129/), [code](https://github.com/RECOR-Benchmark/RECOR) | ✅ | Its finding supports Step 11 |
| 20 | MTRAG — "IBM Research, ACL 2025" | **Venue is TACL 2025** (a journal, vol. 13), not the ACL 2025 conference. [paper](https://aclanthology.org/2025.tacl-1.36/), [code](https://github.com/IBM/mt-rag-benchmark) | ✅ | **Yes** (Steps 10, 13) |
| 21 | CMT-RAG — "arXiv 2026" | arXiv 2607.26470 only. [arXiv](https://arxiv.org/abs/2607.26470) | ❌ (preprint) | No |
| 22 | Learning to Retrieve Engaging Follow-Up Queries — "Richardson et al., arXiv" | **Actually peer-reviewed:** **Findings of EACL 2023**. [paper](https://aclanthology.org/2023.findings-eacl.149/), [code](https://github.com/amazon-science/fq-bank) | ✅ | Optional (suggested questions in the UI) |
| 23 | DIRECT: Directional Relevance in Conversational Trajectories — "ACL 2026" | **Wrong venue:** **EACL 2026 Industry Track**. Relies on proprietary interaction logs. [paper](https://aclanthology.org/2026.eacl-industry.71/) | ⚠️ (industry track) | No |
| 24 | Simulating Follow-Up Questions in Conversational Search — "Kiesel et al., ECIR 2024" | Correct: **ECIR 2024** (LNCS 14609). [paper](https://link.springer.com/chapter/10.1007/978-3-031-56060-6_25), [code](https://github.com/webis-de/ECIR-24) | ✅ | **Yes** (Step 14) |
| 25 | Learning When to Retrieve, What to Rewrite, and How to Respond in Conversational QA — "Roy et al., ACL 2024" | **Wrong venue:** **Findings of EMNLP 2024**. [paper](https://aclanthology.org/2024.findings-emnlp.622/) | ✅ | **Yes** (Step 12, as prompt rules) |
| 26 | S2G-RAG — "arXiv" | **Actually peer-reviewed:** **ACL 2026 (long)**. [paper](https://aclanthology.org/2026.acl-long.1185/) | ✅ | Optional (Steps 9 / 12) |

**Summary:**

* **8 of the 26 listings had a wrong venue, wrong authors or a wrong "preprint" label:** #2, #7, #8, #20, #22, #23, #25, #26.
* **5 are not from a top venue** (❌: #8, #10, #11, #16, #21).
* **5 more are peer-reviewed but a demo, industry or non-core venue** (⚠️: #5, #7, #9, #12, #23).
* **3 are used directly** (#20, #24, #25). #4 and #19 are cited as supporting evidence, #22 and #26 are optional, and #1 is context only in v2.

## Appendix B — References used in this methodology (all verified)

Checked on 28–29 Sep 2026 on the publisher's or proceedings' page. The paper is marked **(main)** in the one step where it is that step's main paper; papers without a mark are supporting or safeguard references.

**Data, leakage and splits**

| # | Reference | Venue | Link | Used in |
|---|---|---|---|---|
| 1 | S. Kaufman, S. Rosset, C. Perlich, O. Stitelman — Leakage in data mining: formulation, detection, and avoidance | ACM TKDD 6(4), 2012 | <https://dl.acm.org/doi/10.1145/2382577.2382579> | Step 0 (main) |
| 2 | A. Elangovan, J. He, K. Verspoor — Memorization vs. Generalization: Quantifying Data Leakage in NLP Performance Evaluation | EACL 2021 | <https://aclanthology.org/2021.eacl-main.113/> | Step 0 |
| 3 | S. Kapoor, A. Narayanan — Leakage and the reproducibility crisis in machine-learning-based science | Patterns 4(9), 2023 | <https://doi.org/10.1016/j.patter.2023.100804> | Step 14, X11 |

**Causal design**

| # | Reference | Venue | Link | Used in |
|---|---|---|---|---|
| 4 | M. A. Hernán, J. M. Robins — Using Big Data to Emulate a Target Trial When a Randomized Trial Is Not Available | Am. J. Epidemiology 183(8), 2016 | <https://doi.org/10.1093/aje/kwv254> | Step 2 (main) |
| 5 | R. H. Keogh, J. M. Gran, S. R. Seaman, G. Davies, S. Vansteelandt — Causal inference in survival analysis using longitudinal observational data: sequential trials and marginal structural models | Statistics in Medicine 42(13), 2023 | <https://doi.org/10.1002/sim.9718> | Step 2; point 12 |
| 6 | M. A. Hernán, B. C. Sauer, S. Hernández-Díaz, R. Platt, I. Shrier — Specifying a target trial prevents immortal time bias and other self-inflicted injuries in observational analyses | J. Clinical Epidemiology 79, 2016 | <https://doi.org/10.1016/j.jclinepi.2016.04.014> | Step 2; X1 |
| 7 | M. A. Hernán, S. L. Taubman — Does obesity shorten life? The importance of well-defined interventions to answer causal questions | Int. J. Obesity 32, 2008 | <https://doi.org/10.1038/ijo.2008.82> | Step 3 (actionability); point 11 |
| 8 | J. G. Young, M. J. Stensrud, E. J. Tchetgen Tchetgen, M. A. Hernán — A causal framework for classical statistical estimands in failure-time settings with competing events | Statistics in Medicine 39(8), 2020 | <https://doi.org/10.1002/sim.8471> | Step 2 (call end = total effect) |
| 9 | J. M. Montgomery, B. Nyhan, M. Torres — How Conditioning on Posttreatment Variables Can Ruin Your Experiment and What to Do about It | Am. J. Political Science 62(3), 2018 | <https://doi.org/10.1111/ajps.12357> | Step 0 (audit), Step 2 |
| 10 | M. A. Hernán, S. Hernández-Díaz, J. M. Robins — A structural approach to selection bias | Epidemiology 15(5), 2004 | <https://doi.org/10.1097/01.ede.0000135174.63482.43> | Step 7 (filters); X3 |
| 11 | L. Gui, V. Veitch — Causal Estimation for Text Data with (Apparent) Overlap Violations | ICLR 2023 | <https://openreview.net/forum?id=Ha2MnQM9Ph> | Step 2 (no turn-*k* text in covariates); X6 |
| 51 | M. A. Hernán, T. J. VanderWeele — Compound treatments and transportability of causal inference | Epidemiology 22(3), 2011 | <https://doi.org/10.1097/EDE.0b013e3182109296> | Step 2 (clean primary population, C1) |

**Estimation and inference**

| # | Reference | Venue | Link | Used in |
|---|---|---|---|---|
| 12 | V. Chernozhukov et al. — Double/debiased machine learning for treatment and structural parameters | The Econometrics Journal 21(1), 2018 | <https://doi.org/10.1111/ectj.12097> | Step 4 (main) |
| 13 | N. Egami, C. J. Fong, J. Grimmer, M. E. Roberts, B. M. Stewart — How to make causal inferences using texts | Science Advances 8, 2022 | <https://www.science.org/doi/10.1126/sciadv.abg2652> | Step 4 (main) |
| 14 | P. Bach, V. Chernozhukov, M. S. Kurz, M. Spindler — DoubleML: An Object-Oriented Implementation of Double Machine Learning in Python | JMLR 23(53), 2022 | <https://jmlr.org/papers/v23/21-0862.html> | Step 4 (code) |
| 15 | H. D. Chiang, K. Kato, Y. Ma, Y. Sasaki — Multiway Cluster Robust Double/Debiased Machine Learning | J. Business & Economic Statistics 40(3), 2022 | <https://doi.org/10.1080/07350015.2021.1895815> | Step 4 (clusters) |
| 16 | N. Egami, M. Hinck, B. M. Stewart, H. Wei — Using Imperfect Surrogates for Downstream Inference: Design-based Supervised Learning (DSL) | NeurIPS 2023 | <https://proceedings.neurips.cc/paper_files/paper/2023/file/d862f7f5445255090de13b825b880d59-Paper-Conference.pdf> | Steps 1, 4 |
| 17 | R. K. Crump, V. J. Hotz, G. W. Imbens, O. A. Mitnik — Dealing with limited overlap in estimation of average treatment effects | Biometrika 96(1), 2009 | <https://doi.org/10.1093/biomet/asn055> | Step 4 (overlap) |
| 18 | P. C. Austin — Balance diagnostics for comparing the distribution of baseline covariates between treatment groups in propensity-score matched samples | Statistics in Medicine 28(25), 2009 | <https://doi.org/10.1002/sim.3697> | Step 4 (balance) |
| 19 | Y. Benjamini, Y. Hochberg — Controlling the False Discovery Rate | JRSS-B 57(1), 1995 | <https://doi.org/10.1111/j.2517-6161.1995.tb02031.x> | Step 4 (BH) |
| 20 | M. Lipsitch, E. Tchetgen Tchetgen, T. Cohen — Negative controls: a tool for detecting confounding and bias in observational studies | Epidemiology 21(3), 2010 | <https://doi.org/10.1097/EDE.0b013e3181d61eeb> | Steps 3–4 |
| 21 | T. J. VanderWeele, P. Ding — Sensitivity Analysis in Observational Research: Introducing the E-Value | Annals of Internal Medicine 167(4), 2017 | <https://doi.org/10.7326/M16-2607> | Step 4 |
| 22 | B. A. Nosek, C. R. Ebersole, A. C. DeHaven, D. T. Mellor — The preregistration revolution | PNAS 115(11), 2018 | <https://doi.org/10.1073/pnas.1708274114> | Step 4 (pre-registration) |
| 23 | V. Dorie, J. Hill, U. Shalit, M. Scott, D. Cervone — Automated versus Do-It-Yourself Methods for Causal Inference: Lessons Learned from a Data Analysis Competition | Statistical Science 34(1), 2019 | <https://doi.org/10.1214/18-STS667> | Step 4 (planted-effect test) |
| 24 | Z. Jin et al. — Can Large Language Models Infer Causation from Correlation? (Corr2Cause) | ICLR 2024 | <https://openreview.net/forum?id=vqIH0ObdqL> | Step 4 (why the LLM never decides) |
| 52 | E. A. Stuart, B. K. Lee, F. P. Leacy — Prognostic score-based balance measures can be a useful diagnostic for propensity score methods in comparative effectiveness research | J. Clinical Epidemiology 66(8 Suppl), 2013 | <https://doi.org/10.1016/j.jclinepi.2013.01.013> | Step 4 (balance gate, C2) |

**Labels and behaviours**

| # | Reference | Venue | Link | Used in |
|---|---|---|---|---|
| 25 | M. Wan et al. — TnT-LLM: Text Mining at Scale with Large Language Models | KDD 2024 | <https://dl.acm.org/doi/10.1145/3637528.3671647> | Step 1 (main) |
| 26 | R. Zhong et al. — Goal Driven Discovery of Distributional Differences via Language Descriptions (D5) | NeurIPS 2023 | <https://proceedings.neurips.cc/paper_files/paper/2023/hash/7e810b2c75d69be186cadd2fe3febeab-Abstract-Conference.html> | Step 3 (main) |
| 27 | R. Pryzant, D. Card, D. Jurafsky, V. Veitch, D. Sridhar — Causal Effects of Linguistic Properties | NAACL 2021 | <https://aclanthology.org/2021.naacl-main.323/> | Step 3 |

**Forecasting and faithfulness**

| # | Reference | Venue | Link | Used in |
|---|---|---|---|---|
| 28 | J. Zhang et al. — Conversations Gone Awry: Detecting Early Signs of Conversational Failure | ACL 2018 | <https://aclanthology.org/P18-1125/> | Step 2 (precedent) |
| 29 | J. P. Chang, C. Danescu-Niculescu-Mizil — Trouble on the Horizon (CRAFT) | EMNLP-IJCNLP 2019 | <https://aclanthology.org/D19-1481/> | Step 5 (forecasting precedent) |
| 30 | J. DeYoung et al. — ERASER: A Benchmark to Evaluate Rationalized NLP Models | ACL 2020 | <https://aclanthology.org/2020.acl-main.408/> | Step 5 (main) |
| 31 | P. Hase, H. Xie, M. Bansal — The Out-of-Distribution Problem in Explainability and Search Methods for Feature Importance Explanations | NeurIPS 2021 | <https://proceedings.neurips.cc/paper_files/paper/2021/hash/1def1713ebf17722cbe300cfc1c88558-Abstract.html> | Step 5 |

**Retrieval, answers and checking**

| # | Reference | Venue | Link | Used in |
|---|---|---|---|---|
| 32 | N. Reimers, I. Gurevych — Sentence-BERT | EMNLP-IJCNLP 2019 | <https://aclanthology.org/D19-1410/> | Step 6 (main) |
| 33 | G. V. Cormack, C. L. A. Clarke, S. Büttcher — Reciprocal Rank Fusion | SIGIR 2009 | <https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf> | Step 6 |
| 34 | J. Carbonell, J. Goldstein — The use of MMR, diversity-based reranking for reordering documents and producing summaries | SIGIR 1998 | <https://doi.org/10.1145/290941.291025> | Step 6 |
| 35 | X. V. Yu, S. Min, L. Zettlemoyer, H. Hajishirzi — CREPE: Open-Domain Question Answering with False Presuppositions | ACL 2023 | <https://aclanthology.org/2023.acl-long.583/> | Step 7 (main) |
| 36 | M. Sharma et al. — Towards Understanding Sycophancy in Language Models | ICLR 2024 | <https://openreview.net/forum?id=tvhaxkMKAn> | Step 7 |
| 37 | T. Gao, H. Yen, J. Yu, D. Chen — Enabling Large Language Models to Generate Text with Citations (ALCE) | EMNLP 2023 | <https://aclanthology.org/2023.emnlp-main.398/> | Step 8 (main) |
| 38 | Y. Zha, Y. Yang, R. Li, Z. Hu — AlignScore: Evaluating Factual Consistency with a Unified Alignment Function | ACL 2023 | <https://aclanthology.org/2023.acl-long.634/> | Step 9 |
| 39 | B. Yu, Y. Li, J. Wang — Detecting Causal Language Use in Science Findings | EMNLP-IJCNLP 2019 | <https://aclanthology.org/D19-1473/> | §2 claim ladder; Step 9 |

**Task 2 (follow-ups)**

| # | Reference | Venue | Link | Used in |
|---|---|---|---|---|
| 40 | Y. Katsis et al. (IBM Research) — MTRAG: A Multi-Turn Conversational Benchmark for Evaluating RAG Systems | TACL 13, 2025 | <https://aclanthology.org/2025.tacl-1.36/> | Steps 10 (main), 13 |
| 41 | Y. Hu, C.-H. Lee, T. Xie, T. Yu, N. A. Smith, M. Ostendorf — In-Context Learning for Few-Shot Dialogue State Tracking (IC-DST) | Findings of EMNLP 2022 | <https://aclanthology.org/2022.findings-emnlp.193/> | Step 11 (main) |
| 42 | K. Mao et al. — Large Language Models Know Your Contextual Search Intent (LLM4CS) | Findings of EMNLP 2023 | <https://aclanthology.org/2023.findings-emnlp.86/> | Step 11 (retrieval text only) |
| 43 | N. Roy, L. F. R. Ribeiro, R. Blloshmi, K. Small — Learning When to Retrieve, What to Rewrite, and How to Respond in Conversational QA | Findings of EMNLP 2024 | <https://aclanthology.org/2024.findings-emnlp.622/> | Step 12 (main) |

**Evaluation and the query set**

| # | Reference | Venue | Link | Used in |
|---|---|---|---|---|
| 44 | L. Zheng et al. — Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | NeurIPS 2023 (D&B) | <https://proceedings.neurips.cc/paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html> | Step 13 |
| 45 | A. Panickssery, S. R. Bowman, S. Feng — LLM Evaluators Recognize and Favor Their Own Generations | NeurIPS 2024 | <https://proceedings.neurips.cc/paper_files/paper/2024/hash/7f1f0218e45f5414c79c0679633e47bc-Abstract-Conference.html> | Step 13 |
| 46 | J. Saad-Falcon, O. Khattab, C. Potts, M. Zaharia — ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems | NAACL 2024 | <https://aclanthology.org/2024.naacl-long.20/> | Step 13 |
| 47 | A. N. Angelopoulos, S. Bates, C. Fannjiang, M. I. Jordan, T. Zrnic — Prediction-powered inference | Science 382(6671), 2023 | <https://doi.org/10.1126/science.adi6000> | Step 13 (judge correction); related to DSL |
| 48 | R. Dror, G. Baumer, S. Shlomov, R. Reichart — The Hitchhiker's Guide to Testing Statistical Significance in NLP | ACL 2018 | <https://aclanthology.org/P18-1128/> | Step 13 |
| 49 | Y. Wang et al. — Self-Instruct: Aligning Language Models with Self-Generated Instructions | ACL 2023 | <https://aclanthology.org/2023.acl-long.754/> | Step 14 |
| 50 | J. Kiesel, M. Gohsen, N. Mirzakhmedova, M. Hagen, B. Stein — Simulating Follow-Up Questions in Conversational Search | ECIR 2024 | <https://link.springer.com/chapter/10.1007/978-3-031-56060-6_25> | Step 14 |

**Optional or supporting, from the team's list:** Causal-ESC (ACL 2026), RECOR (Findings of ACL 2026), S2G-RAG (ACL 2026), Richardson et al. (Findings of EACL 2023).

**Code used or referenced.** Star counts and versions were read on 28–29 Sep 2026.

* DoubleML/doubleml-for-py — 790★, v0.11.4
* py-why/dowhy — v0.14
* aangelopoulos/ppi_py — 301★
* stanford-futuredata/ARES — 733★
* Yushi-Hu/IC-DST — 45★
* junwang4/causal-language-use-in-science
* ruthkeogh/sequential_trials
* ruiqi-zhong/D5 — 71★
* jayded/eraserbenchmark — 102★
* CornellNLP/ConvoKit — 649★
* UKPLab/sentence-transformers — v6.1.0
* dorianbrown/rank_bm25
* princeton-nlp/ALCE — 527★
* yuh-zha/AlignScore — 174★
* IBM/mt-rag-benchmark — 155★
* kyriemao/LLM4CS — 43★
