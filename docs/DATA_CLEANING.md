# Data cleaning & formatting — design, decisions, validation

Notebook: [`notebooks/01_data_cleaning.ipynb`](../notebooks/01_data_cleaning.ipynb).
Output folder: `cleaned_data/` (git-ignored; the data is copyrighted).
Reference numbers such as [B2] point to [`LITERATURE_REVIEW.md`](LITERATURE_REVIEW.md).

## 1 · What the raw file looks like (from `analysis.ipynb`)

* **19,621** records.
  * Keys: `transcript_id`, `time_of_interaction`, `domain`, `intent`, `reason_for_call`, `conversation[{speaker, text}]`.
  * No nulls in the provided file, but the README says every field except `transcript_id` *may* be null.
* **686,764** raw turns in total, 35.0 turns per call on average (min 1, max 79).
* **35 intents**; `domain` is `"Insurance"` for **all** calls, although the calls are about hotels, airlines, banks, telecom, retail and insurance.
* Calls were made between 2025-11-04 and 2025-11-12, 09:00–16:59.
* Speaker labels:
  * 330,420 `Agent` and 316,449 `Customer` turns;
  * **1,332 calls** use person names (`James O'Connor`, `Mia`, `Chloe Adams` …);
  * `Supervisor` (946 turns), `Manager` (27), `Fraud/Loan/Escalation_Specialist`, transferred agents such as `Rob`;
  * **75 annotation "turns" in 56 calls** (`- Key Event`, `[Call Summary`, `(Note`, `Domain`, `Outcome`, `Key Events`, `Student` …).
* **4 calls** hold whole dialogues inside one turn as literal `\n 2 customer … \n 3 agent …`. Three of them therefore looked like "1-speaker" calls.
* ASR-style text: lower-case, no punctuation, fillers (*um, uh*), repetitions (*i i*), curly apostrophes, and stage directions (`*transferring call*`, `(pause)`, `call ended`).
* 19,590 unique `reason_for_call` values for 19,621 calls, so duplicates are possible.

## 2 · Pipeline (in execution order)

| § | Step | Output / effect |
|---|---|---|
| 2 | load + schema audit, SHA-256 of the raw file, coerce types, resolve duplicate ids | `schema_audit`, `qc_log` |
| 3 | text & label utilities, **with self-tests** that run every time | fails loudly if a regex regresses |
| 4 | structural pass: split embedded dialogues → quarantine annotation turns → normalise text → extract stage directions → marker-only turns become events → label rules | exact accounting identity is asserted |
| 5 | exact duplicates dropped; near-duplicates flagged; **template groups** (MinHash on word 3-grams with numbers masked, giant-group guard); deterministic hash split `train/dev/test` **by template group**, locked here | `duplicates.csv`, `template_group`, `split` |
| 6 | speaker-role resolution for name-labelled calls, **validated by hiding labels** on held-out correctly-labelled calls | `speaker_role_map.csv`, `ROLE_EVAL` |
| 7 | turn table: `turn_id`, `turn_uid`, `speaker`, `party`, `block_id`, `rel_position`, `phase` | — |
| 8 | metadata: timestamps, `intent_key`, `brand` (from the opening), **`business_domain`** (keyword vote + intent majority with purity; votes from train only) and **`opening_domain_vote`** (first 4 turns only) | `domain_mapping.csv` |
| 9 | turn features: hesitation, holds/silences, questions, backchannels, repeated queries (vocabulary fitted on train), agent-response and customer-state cues | `turns.parquet` |
| 10 | call aggregates, **weak event signals with the turn where each event starts**, quality flags | `conversations.parquet` |
| 10.2 | **metadata leakage audit** on non-test calls: content probe (does the field describe what happened in the call?) + predictive probe (does it predict events better than the opening turns?) | `leakage_audit.csv` |
| 10.3 | **column-availability registry**: when each column is known (`design`, `turn-past`, `opening`, `metadata`, `whole-call`, `outcome`) | `column_availability.csv` |
| 11 | 19 hard integrity checks (the notebook stops if one fails) | `cleaning_report.json` |
| 12 | save JSON / parquet / CSV, report, data card | `cleaned_data/` |
| 13 | before/after examples, one per repaired defect | — |

## 3 · Decision log

| Defect | Decision | Alternatives rejected (why) | Ref. |
|---|---|---|---|
| Person-name speaker labels | label rules → TF-IDF + logistic-regression role classifier trained on the ~18k correctly-labelled calls → per-speaker summed log-odds + "speaks first" prior → rank assignment → context rules for third speakers. Short names are merged into full names within a call ("mia" → "mia hernandez"). | *First speaker = agent* (fails when the customer speaks first or labels mix). *Drop the calls* (loses 6.8% of data and biases toward "clean" calls). | [B5] [B6] |
| Supervisors, specialists, transferred agents | fine-grained `speaker` (Agent / Customer / Supervisor / Specialist / System) **plus** two-party `party` (Agent vs Customer) | Collapsing to 2 roles loses the strongest escalation evidence, the supervisor joining. | [C4] |
| Annotation turns | quarantined to `annotations_quarantine`; never evidence | Keeping them leaks outcome labels ("no escalation occurred") into retrieval and training. Deleting them loses an audit / weak-validation source. | [I2] |
| Embedded `\n 2 customer …` dialogues | regex split, which requires a turn number or a colon so that ordinary speech is never split. Embedded numbering is *not* trusted because the EDA found gaps. | Leaving them: 3 calls look like monologues and their turns cannot be cited. | — |
| Stage directions / marker-only turns | typed non-verbal events (PAUSE, HOLD, TRANSFER, CALL_END, NOISE, SIGH, LAUGH, TYPING). Marker-only turns move to call-level `events` anchored at `after_turn_id`. | Deleting them loses the only silence and hold signal (there are no timestamps). | [B3] |
| Fillers / repetitions | two views: `text` (normalised verbatim) and `text_clean` (fillers and repetitions removed, spelled-out ids protected). Hesitation is **counted before removal**. | A single cleaned text loses the hesitation signal the brief asks for. A single raw text hurts retrieval and NLI. | [B2] [B4] |
| Discourse markers inside key phrases ("speak to a *you know* supervisor") | cue matching uses `text_clean` with *you know / i mean / like* also stripped | Matching on `text_clean` alone missed real escalation requests; this was caught by the test suite. | — |
| A repeated word that starts a discourse marker ("thank *you you know* for that") | the repetition collapse skips a word whose last copy begins *you know* / *i mean*, so the cue view keeps "thank you" | Collapsing first and then stripping the marker deleted "you" and broke the *thanks for the information* negative-control cue; this was caught by the end-to-end oracle test. | — |
| Consecutive same-speaker turns | kept, linked by `block_id` and `same_speaker_as_prev` | Merging them changes citation granularity. | [B1] |
| Constant, wrong `domain` | `domain_raw` is kept; `business_domain` = intent-majority of a transparent keyword vote when the intent is ≥75% pure, else the per-call vote. The table is saved and `DOMAIN_OVERRIDES` allows manual fixes. | *Hard-coded intent→domain map* (unverifiable without the data; some intents, e.g. *Loyalty Program*, may span industries). | — |
| Inconsistent intent casing | `intent_key` slug | — | — |
| Duplicates | exact duplicates dropped; near-duplicates (Jaccard ≥ 0.9 on number-masked 3-grams) flagged and kept in one split | Near-duplicate deletion at 0.9 could remove legitimately similar templated calls. | [I3] |
| How similar calls are found | MinHash + LSH banding (32 bands × 4 rows) **implemented in the notebook** (SHA-1 shingle hashes, permutations from numpy's frozen legacy `RandomState`). Groups are the connected components of "**exact** Jaccard ≥ threshold" over the LSH candidates; candidates are taken in descending order of their MinHash estimate and a pair whose calls are already connected is skipped, which gives the same groups as checking every candidate (tested) at a fraction of the work (34 s for 20,000 heavily templated calls) | The `datasketch` package gave *different template groups — and so a different locked split —* under versions 1.6 and 2.0 on the same corpus, because pairs were accepted on the MinHash *estimate*. Now the split depends only on the data (identical signatures and splits verified on numpy 1.24 / pandas 2.0 and numpy 2.4 / pandas 3.0). | [I3] |
| Template re-use (same wording, different ids/amounts) | calls with Jaccard ≥ 0.5 are linked into template groups. A giant-group guard raises the threshold in 0.1 steps until no group holds > 1% of calls, so chaining cannot swallow the corpus. | Splitting by single call leaks templates between train and test and inflates results (Elangovan et al., EACL 2021). | — |
| No outcome labels | lexical cues → weak `ev_*` signals + `*_turn_id` of first occurrence. The notebook cross-checks them against the quarantined notes. | Waiting for an LLM labeller blocks all analysis. The cues are the cheap, auditable first pass; refine with TnT-LLM-style labelling. | [A1] [F3] |
| Train/test contamination in causal claims | deterministic hash split **by template group** (80/10/10), locked before any labelling | A random split changes with row order and library versions. | [E3] |
| Metadata of unknown timing (`reason_for_call` is unique per call and may be a post-call summary) | leakage audit: a content probe plus a predictive probe against the opening turns. Flagged fields, and fields derived from them, are never pre-treatment variables or filters. | Trusting the metadata risks conditioning on the outcome (post-treatment bias). Dropping it blindly loses a possibly useful pre-call variable. | — |
| Columns that use the whole call (`rel_position` divides by the call length; counts; QC flags) | availability registry; causal models at turn *k* may use only `turn-past` columns of earlier turns and `opening` columns | Leaves a silent route for future information into causal models. | — |
| Industry control for causal models | `opening_domain_vote`: the lexicon on the first 4 turns only | `business_domain` reads `reason_for_call`, whose timing is unknown. | — |
| Learned transforms (role classifier, repeat vocabulary, intent → domain votes) | fitted on the train split only | Fitting on all splits lets test text shape the features. | — |

## 4 · Output schema (key fields)

The full, auto-generated schema with every column is in `cleaned_data/DATA_CARD.md`.

**`turns.parquet`** — one row per turn:

* **ids:** `transcript_id`, `turn_id`, `turn_uid`
* **speaker:** `speaker`, `party`, `speaker_name`, `role_method`
* **text:** `text`, `text_clean`, `text_raw`
* **position:** `block_id`, `rel_position`, `phase`
* **non-verbal events:** `nonverbal_types`
* **hesitation:** `n_filled_pauses`, `n_repetitions`, `n_hedges`
* **dialogue acts:** `is_question`, `is_backchannel`
* **repeated queries:** `is_repeat`, `repeat_of_turn_id`
* **cues:** 16 `cue_*` booleans and the `cues` list
* **denormalised call metadata:** `business_domain`, `intent_key`, `split`, `qc_ok`

**`conversations.parquet`** — one row per call:

* **metadata:** `time_of_interaction`, `call_hour`, `intent`, `intent_key`, `reason_for_call`, `brand`, `domain_raw`, `business_domain`
* **counts per role:** `n_turns_<role>`
* **per-party aggregates:** `agent_*`, `customer_*` (word share, filler rate, cue counts)
* **non-verbal event counts**
* **weak event signals:** `ev_escalation` (+ `esc_supervisor_joined`, `esc_customer_requested`, `esc_agent_escalated`), `ev_transfer`, `ev_refund`, `ev_churn_risk`, `ev_repeat_contact`, each with its `*_turn_id`
* **quality flags:** `qc_*`, `qc_ok`
* **split & dedup:** `split`, `dedup_group`, `template_group`, `template_group_size`
* **pre-behaviour industry:** `opening_domain_vote`, `opening_domain_confidence`

**Audit tables:**

* `leakage_audit.csv` — one row per probe: content (share of outcome language) and predictive (AUC of field vs opening turns, per event).
* `column_availability.csv` — table, column, availability class, leakage flag, and whether the column may be a covariate.
* The data card's schema tables also carry the availability class of every column.

**`cleaned_data.json`** — the raw record shape. Each call has:

* `conversation[{turn_id, speaker, party, speaker_name, text, text_clean, cues, nonverbal_types}]`
* `speakers`, `signals`, `quality`, `events`

## 5 · Validation

Automated, every run:

* **Self-tests** of every regex and label rule, including the defects seen in the EDA: `Customer'S`, `(After A Moment) Noah`, `Escalation_Specialist`, `- Key Event`, `*[System Note`, literal `\n 2 customer …`, and "four four five" ids.
* **Exact accounting identity:** raw turns + split turns − quarantined − marker-only − empty − duplicate-call turns = output turns.
* **19 hard integrity checks:**
  * unique ids; contiguous `turn_id`s; canonical roles;
  * no empty text; no leftover `\n`; no annotation labels left;
  * the turn accounting identity above;
  * splits complete; near-duplicate clusters and **template groups** never straddle splits; near-duplicate clusters nest inside template groups;
  * **every output column has an availability class**; **leakage-flagged columns are never usable as covariates**;
  * event turn ids in range.
* **Hidden-label role validation** on held-out test-split calls with correct labels, in three settings: two-party; with a labelled supervisor; with all three labels hidden.

Test suite (`pytest -q tests/`). A synthetic corpus with ground truth (`tests/make_synthetic_fixture.py`, invented text) injects every defect above. The notebook is then executed headlessly and its outputs are compared with the ground truth.

**14/14 tests pass**. They cover:

* role sequence of every call;
* annotation and marker counts;
* embedded re-splits;
* duplicates;
* business domain recovery (≥ 97%);
* event signals per scenario;
* escalation turn ≤ first supervisor turn;
* text-view invariants;
* splits;
* **calls re-used with only the numbers changed share one template group and one split;**
* **the leakage audit flags a `reason_for_call` that leaks the refund outcome, and leaves `intent` unflagged;**
* **the availability registry covers every column** (`rel_position` = whole-call, cues = turn-past, `ev_*` = outcome);
* **`opening_domain_vote` recovers the true industry (≥ 90%) without reading metadata.**

Portability and scale:

* **Identical outputs under pandas 2.2 + scikit-learn 1.5 and pandas 3.0 + scikit-learn 1.9.**
  * Every JSON and CSV output, including `leakage_audit.csv`, is byte-for-byte equal.
  * Parquet tables have identical contents; their bytes differ only in embedded library metadata.
  * The audit's cross-validation folds come from a hash of the template group, so they do not depend on library versions.
* **Scale test** on a synthetic corpus with 679k raw turns (about the real file's 686k) in 46k calls: 5.1 min and 3.9 GB peak RAM on 4 CPUs.
  * Template grouping took 56 s; the leakage audit took 29 s.
  * Real turns are longer, so plan for 5–7 GB. If RAM is tight, set `NEAR_DUP_DETECTION = False`, but the split then falls back to single calls.

## 6 · What to check on the first run with the real data (10 minutes)

1. **§6 `ROLE_EVAL`.** Two-party conversation accuracy should be ≥ 0.97. Then inspect `speaker_role_map.csv` rows with `low_confidence = True`.
2. **§8 domain table.** Every intent's `majority_domain` should make sense. Look at `purity` below 0.75 (per-call vote is used there). Add `DOMAIN_OVERRIDES` if needed.
3. **§4 "Quarantined labels".** Only annotation-like labels should appear.
4. **§9 prevalence table + §13 examples.** Sample 20 turns per cue with `turns[turns.cue_refusal].sample(20)` and note the precision. The notebook reports lexicon prevalence; you estimate precision this way.
5. **§10.1 note agreement.** Disagreements with the quarantined notes are worth reading.
6. **§5 template groups.** Note the template threshold used and the largest group. If the guard raised the threshold, read a few calls from the largest group.
7. **§10.2 leakage audit.** Which fields are flagged, and why: content probe or predictive probe? The flagged list decides which metadata the downstream pipeline may never use (METHODOLOGY rule R3).
8. **§8 opening-only vote.** It should agree with `business_domain` on most calls where both are decided.

## 7 · Configuration knobs (first code cell)

| Knob | Default |
|---|---|
| `DROP_EXACT_DUPLICATES` | True |
| `NEAR_DUP_DETECTION` | True |
| `NEAR_DUP_THRESHOLD` | 0.9 (number-masked word 3-grams) |
| `TEMPLATE_JACCARD` | 0.5 |
| `TEMPLATE_MAX_GROUP_SHARE` | 0.01 |
| `OPENING_TURNS` | 4 |
| `LEAKAGE_AUC_FLAG` / `LEAKAGE_EXCESS_AUC` | 0.75 / 0.05 |
| `LEAKAGE_CONTENT_SHARE` | 0.05 |
| `SPLIT_FRACTIONS` | 0.8 / 0.1 / 0.1 |
| `SPLIT_SALT` | *do not change once experiments start* |
| `ROLE_CLF_MAX_TRAIN_TURNS` | 200k |
| `ROLE_MIN_MARGIN` | 2.0 |
| `REPEAT_SIM_THRESHOLD` | 0.5 |
| `MIN_TURNS_OK` | 4 |
| `DOMAIN_INTENT_PURITY` | 0.75 |
| `DOMAIN_OVERRIDES` | {} |

## 8 · Known limitations

* Roles for name-labelled calls are inferred; they are audited and validated, but not guaranteed.
* Cues are lexicon proxies with moderate recall. Treat `ev_*` as candidate labels and validate a human-labelled sample before causal estimation.
* The text is unpunctuated, so `is_question` is heuristic.
* There are no per-turn timestamps, so silences are approximated.
* `business_domain` is inferred; review `domain_mapping.csv`.
* The leakage audit can flag a leaky metadata field, but a clean result does not prove the field was written before the call. Downstream causal models therefore keep metadata out of their main adjustment set anyway.
