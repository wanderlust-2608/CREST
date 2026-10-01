# CREST — Causal Rationale Extraction and Synthesis from Conversational Data on Business Events

## Abstract

The dataset comprises approximately 19,600 recorded agent–customer calls, covering three key business events:
- Escalation — when a customer requests a supervisor or the interaction is transferred to one.
- Refund — when a conversation involves a refund request, discussion, or resolution.
- Churn Threat — when a customer indicates an intention to cancel, leave, or switch to an alternative provider.

CREST addresses two complementary analytical tasks:

- Task 1 — Causal Rationale Extraction:
Why did a business event occur? CREST identifies the conversational factors that contributed to the event and produces an evidence-grounded causal explanation, explicitly citing the dialogue turns or segments that support the rationale.

- Task 2 — Context-Aware Follow-Up Reasoning:
How can the analysis be refined through contextual follow-up questions? CREST supports multi-turn analytical queries that preserve the context of the preceding interaction. For example, a user may ask “What about refunds?”, narrow the analysis to “Only airline calls”, or request further elaboration such as “Explain the second factor.” The system resolves these follow-ups against the existing analytical context rather than treating each query as an independent reques

**Separating causes from coincidences.** Calls that end in an escalation may simply be calls where the customer was
angry from the start. So CREST does not just count words that appear before events. It turns every call into a
sequence of **decision moments** ("landmarks"), each described only by what was said *before* it. It then compares
moments where the agent did something (for example, refused a request citing policy) with comparable moments in other
calls where the agent did not, and estimates the difference in what happened next. The estimator is doubly robust and
cross-fitted, with standard errors clustered by call template and a correction for errors in the automatic event
labels, measured on a small blind hand-labelled sample.

**Claim levels.** Every finding goes through 11 predefined checks: overlap, balance, multiplicity, negative controls,
sensitivity analyses, dev/test agreement, a planted-effect self-test of the estimator, label and detector accuracy, and
more. Code then assigns a **claim level**:

| Level | Meaning | Allowed wording |
|---|---|---|
| **L3** | passed every check | "is estimated to raise / lower … under the stated assumptions" |
| **L2** | a warning sign | "is associated with …" |
| **L1** | counts only | no link words |
| **L0** | nothing reliable | the answer says so |

**Answers.** Answers are built from an evidence pack. Code fills in every number. The wording may never claim more than
the claim level allows. Every quote must match the transcript exactly and cite its turn (`transcript_id:turn`). Three
gates (numbers, causal wording, evidence) enforce these rules, and a sentence that fails is removed.

**Pre-registration.** The analysis plan is frozen with a SHA-256 fingerprint before the confirmatory numbers are
computed, so it cannot be bent to fit the results.

**Validation.** The real data has no answer key, so the whole system is validated on a **synthetic call centre whose
true causes are known**. On 4,000 invented calls:
* all 12 true effects fell inside their 95% intervals;
* all 5 confirmed (L3) findings had the right sign;
* the negative controls stayed at zero;
* every question in the query set was answered as expected.

An LLM (Claude, by Anthropic) is **optional**. Without it everything runs offline on rules and statistics. With it,
Claude can write the prose and read follow-up questions, but it never decides a number or a cause.

---

## Project Deliverables

| **Deliverable**                                    | **Location / Command**                                                                                                                                                                                          | **Description**                                                                                                                                                                                                                     |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **End-to-End Implementation of Task 1 and Task 2** | [`crest/`](crest/) · `python -m crest …` · [`notebooks/01_data_cleaning.ipynb`](notebooks/01_data_cleaning.ipynb)                                                                                               | Complete implementation of the CREST pipeline, covering data preparation, causal analysis, evidence extraction, indexing, and context-aware query handling.                                                                         |
| **Setup and Execution Instructions**               | This README — [Setup](#1--setup), [Preprocessing](#3--run-on-the-real-data-without-the-llm-default), [Training and Analysis](#training), and [Application](#application)                                        | Step-by-step instructions for installing dependencies, preprocessing the data, running the analysis pipeline (`build` → `pilot` → `confirm` → `evidence` → `index`), and using the resulting system through `ask` and `chat`.       |
| **Core Dependencies**                              | [`requirements.txt`](requirements.txt)                                                                                                                                                                          | Required Python dependencies for the core CREST implementation.                                                                                                                                                                     |
| **Optional Dependencies**                          | [`requirements-optional.txt`](requirements-optional.txt)                                                                                                                                                        | Additional dependencies for optional functionality, including LLM-based generation, dense embeddings, and statistical or methodological cross-checks.                                                                               |
| **Technical Documentation**                        | [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) · [`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md) · [`docs/DATA_CLEANING.md`](docs/DATA_CLEANING.md) · [`docs/LITERATURE_REVIEW.md`](docs/LITERATURE_REVIEW.md) | Detailed documentation of the methodology, implementation, validation procedures, data-cleaning workflow, corrections, scalability considerations, and supporting literature.                                                       |
| **Run-Specific Reports**                           | `REPORT.md` generated for each run                                                                                                                                                                              | Each execution produces a run-specific report containing the configuration, analysis details, validation results, and outputs. An example is available at [`examples/synthetic_demo/REPORT.md`](examples/synthetic_demo/REPORT.md). |
| **Query Dataset and System Outputs**               | [`docs/QUERY_DATASET.md`](docs/QUERY_DATASET.md) · [`examples/synthetic_demo/QUERY_OUTPUTS.md`](examples/synthetic_demo/QUERY_OUTPUTS.md) · `queries.csv` · `queries_review.csv` · `outputs_*.jsonl`            | Curated query set covering **50–100 queries**, organized by task, difficulty, and use case, together with the query-generation process, taxonomy, refinement history, human review, LLM-based judging, and complete system outputs. |
| **Evaluation**                                     | `python -m crest evaluate` → `eval/metrics.json` + `REPORT.md`                                                                                                                                                  | Automated evaluation of the pipeline, including generation of quantitative metrics and a corresponding evaluation report. Synthetic-demo results are reported in [Results](#7--results-synthetic-demo).                             |
| **Synthetic Demonstration**                        | `python -m crest demo`                                                                                                                                                                                          | End-to-end demonstration using an internally generated set of synthetic calls, allowing the complete pipeline to be executed without requiring the real dataset.                                                                    |
| **Interactive Task 2 Demonstration**               | `python -m crest chat`                                                                                                                                                                                          | Interactive interface for testing context-aware follow-up queries and multi-turn analytical reasoning.                                                              
---

## Repository layout

```
causal-rationale-hackathon/
├── crest/                    the program: every step as a Python module (python -m crest <command>)
├── notebooks/
│   └── 01_data_cleaning.ipynb   Step 0: cleaning and formatting of the raw file -> cleaned_data/
├── docs/                     methodology, implementation report, data cleaning, query dataset, literature review
├── tests/                    127 automated tests (unit, reference cross-checks, adversarial gates, end to end)
├── examples/
│   └── synthetic_demo/       every shareable output of a full run on 4,000 invented calls
├── README.md                 this file
├── requirements.txt          core libraries
├── requirements-optional.txt optional: Claude client, dense embeddings, reference packages for cross-checks
└── .gitignore                keeps the data and every pipeline output out of git
```

Created on your computer when you use the project:

```
.venv/            your Python environment 
data/       the dataset (final_transcripts.json)
cleaned_data/     output of the cleaning notebook
crest_out/        every result of a run on the real data (layout below)
demo_out/         the same for the synthetic demo
```

### What each folder does

**`notebooks/01_data_cleaning.ipynb` — preprocessing.** It repairs the raw file without changing it:

* speaker labels that are person names;
* supervisor turns;
* analyst notes typed into the dialogue (quarantined, never used as evidence);
* stage directions;
* fillers and repetitions;
* duplicates and calls reused from the same template;
* a wrong domain field.

It also creates a locked train / dev / test split by template group, and a leakage audit of the metadata.

**`crest/` — the program.** The function of each file is listed below:

| **Module**                                                           | **Primary Responsibility**                                                                                                                                                                     |
| -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`cli.py`](crest/cli.py), [`__main__.py`](crest/__main__.py)         | Define the command-line interface and expose the main pipeline commands, including `build`, `pilot`, `confirm`, `evidence`, `index`, `ask`, `chat`, `evaluate`, and `demo`.                    |
| [`pipeline.py`](crest/pipeline.py)                                   | Orchestrate pipeline stages in the required order, prevent unsafe execution sequences, and record generated artefacts and their hashes in `manifest.json`.                                     |
| [`config.py`](crest/config.py)                                       | Centralize project configuration and analysis settings, with support for overriding defaults through `--config`.                                                                               |
| [`io.py`](crest/io.py)                                               | Load and validate cleaned datasets, manage workspace paths, and handle the input/output structure used across pipeline stages.                                                                 |
| [`definitions.py`](crest/definitions.py)                             | Define the formal event and behaviour taxonomy, operational definitions, and rules governing permissible analytical wording.                                                                   |
| [`cues.py`](crest/cues.py)                                           | Maintain the keyword and rule-based conversational cues used for initial detection. A consistency test keeps these cues aligned with the data-cleaning notebook.                               |
| [`events.py`](crest/events.py)                                       | Identify the presence and onset turn of each business event, manage the blinded gold sample, and compute corresponding event-detection accuracy metrics.                                       |
| [`behaviours.py`](crest/behaviours.py)                               | Detect agent and customer behaviours of interest, such as refusal, apology, solution offering, and expressed customer frustration, together with their precision evaluations.                  |
| [`landmarks.py`](crest/landmarks.py)                                 | Construct the sequential decision-point table, representing each landmark using only information available before that turn.                                                                   |
| [`analysis.py`](crest/analysis.py), [`stats.py`](crest/stats.py)     | Perform causal estimation and statistical validation, including confidence intervals, cluster bootstrap procedures, multiplicity adjustment, sensitivity analyses, and planted-effect testing. |
| [`prereg.py`](crest/prereg.py)                                       | Create, freeze, fingerprint, and verify the pre-registered analysis plan before confirmatory analysis is executed.                                                                             |
| [`library.py`](crest/library.py)                                     | Construct the Factor Library, apply the defined validation checks, assign claim-strength levels, and generate supporting descriptive summaries and customer-topic statistics.                  |
| [`evidence.py`](crest/evidence.py)                                   | Retrieve dialogue spans supporting identified behaviours and evaluate quotation faithfulness using the independent risk-forecasting check.                                                     |
| [`index.py`](crest/index.py), [`graph.py`](crest/graph.py)           | Build and query the hybrid retrieval layer using BM25 and dense embeddings over five-turn windows, while maintaining provenance links between analytical claims and source dialogue turns.     |
| [`query.py`](crest/query.py)                                         | Parse user questions into structured components, including event, filters, question type, premises, and unsupported or unanswerable components.                                                |
| [`answer.py`](crest/answer.py)                                       | Assemble the evidence package and generate the final response using controlled placeholders rather than directly inventing analytical values.                                                  |
| [`gates.py`](crest/gates.py)                                         | Apply the three output-validation gates covering numerical integrity, causal wording, and evidence grounding.                                                                                  |
| [`session.py`](crest/session.py)                                     | Maintain conversational state for Task 2, process follow-up queries as validated state changes, route requests, and manage versioned response caching.                                         |
| [`queries.py`](crest/queries.py), [`evaluate.py`](crest/evaluate.py) | Construct and manage the evaluation query set, compute evaluation metrics, run baseline comparisons, and generate `REPORT.md` and `QUERY_OUTPUTS.md`, with optional LLM-based judging.         |
| [`llm.py`](crest/llm.py)                                             | Provide the optional Claude client used for LLM-assisted components. LLM functionality is disabled by default.                                                                                 |
| [`simulate.py`](crest/simulate.py)                                   | Generate a synthetic call-centre environment with controlled conversational behaviours and known causal effects for end-to-end validation.                                                     |
| [`devtools.py`](crest/devtools.py)                                   | Maintain consistency between the implementation and the accompanying data-cleaning notebook and support development-time validation.                                                           |




**`docs/` — the written documentation:**

* `METHODOLOGY.md`;
* `IMPLEMENTATION.md`;
* `QUERY_DATASET.md`;
* `DATA_CLEANING.md`;
* `LITERATURE_REVIEW.md`.

**`tests/` — automated checks.** They cover:

* the cleaning notebook against known answers;
* the statistics, including cross-checks against DoubleML, rank_bm25 and ppi_py when installed;
* adversarial gate cases;
* follow-up handling and the query dataset;
* the whole pipeline on a synthetic corpus, scored against the known truth.

**`examples/synthetic_demo/` — sample results.** The report, Factor Library, frozen plan, query set and every answer of
one demo run. It contains no hackathon data.

**`crest_out/` (created by a run) — the workspace:**

| Folder | Contents |
|---|---|
| `events/` | event labels |
| `behaviours/` | behaviour detections |
| `landmarks/` | decision-moment features |
| `checks/` | integrity tests |
| `gold/` | blind labelling packets and accuracy |
| `precision/` | detector check sheets |
| `pilot/` | train-only trial run |
| `prereg/` | the frozen plan |
| `library/` | the Factor Library, counts and topics |
| `evidence/` | quotes and faithfulness |
| `graph/`, `index/` | provenance and search |
| `queries/` | query set, lock, csv, review sheet |
| `outputs/` | answers, including `QUERY_OUTPUTS.md` |
| `eval/` | metrics, human-audit sheet, optional judge ratings |

It also holds `REPORT.md` and `manifest.json`.

---

## 1 · Setup

Python 3.10 or newer. The code is tested on Python 3.11 with numpy 2.4 / pandas 3.0 / scikit-learn 1.9, and on
Python 3.10 with the oldest supported versions (numpy 1.24 / pandas 2.0 / scikit-learn 1.2). Use 8 GB RAM or more for
the full dataset.

```bash
git clone <this private repository>  &&  cd <repository folder>

# macOS / Linux
python3.11 -m venv .venv && source .venv/bin/activate
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
pip install -r requirements-optional.txt     # optional: Claude client, dense embeddings, reference packages

pytest -q tests/                             # about 3 minutes; tests needing optional packages are skipped without them
```

In VS Code, open the project folder, run `Python: Select Interpreter`, choose `.venv`, and run every command from the
project root (the folder that contains `README.md`).

## 2 · Test on synthetic data

```bash
python -m crest demo --out demo_out
```

This simulates 4,000 calls whose true causes are known, cleans them with the real notebook, and simulates the human
labelling steps. It then runs every stage and writes `demo_out/crest_out/REPORT.md` and
`demo_out/crest_out/outputs/QUERY_OUTPUTS.md`. To ask the demo questions yourself:

```bash
python -m crest ask "Why do escalations happen in telecom calls?" --data demo_out/cleaned_data --out demo_out/crest_out
python -m crest ask "what about refunds?" --session s.json --data demo_out/cleaned_data --out demo_out/crest_out
python -m crest chat --data demo_out/cleaned_data --out demo_out/crest_out
```

## 3 · Run on the real data WITHOUT the LLM (default)

Nothing leaves your computer on this path.

**Step 1 — data.** Put the file at `data/raw/final_transcripts.json`, or set `RAW_TRANSCRIPTS_PATH`.

**Step 2 — preprocessing.** Run the cleaning notebook. It takes a few minutes and writes to `cleaned_data/`.

```bash
jupyter nbconvert --to notebook --execute notebooks/01_data_cleaning.ipynb --output 01_data_cleaning.executed.ipynb --ExecutePreprocessor.timeout=1800
# or open it in Jupyter / VS Code and "Run All"
```

**Step 3 — prepare the analysis.**

```bash
python -m crest build               # event labels, behaviours, decision-moment features, integrity tests
python -m crest gold-sample         # blind gold sample from held-out calls -> crest_out/gold/
python -m crest precision-sheets    # detector check sheets -> crest_out/precision/
```

**Step 4**

* label `crest_out/gold/gold_to_label.csv` blind: about 200 calls, 40 of them labelled by both. Its
  `README.txt` explains how.
* One person fills the `correct` column of each sheet in `crest_out/precision/` (20 turns each).
* replace the `crest_out/gold/gold_to_label.csv` with the already manually labelled file from `to_replace/gold_to_label.csv` and `crest_out/precision/` with `to_replace/precision` before moving forward

**Step 5 — training and confirmation.**

```bash
python -m crest gold-ingest --file crest_out/gold/gold_to_label.csv   # labeller accuracy (F1, onset, kappa)
python -m crest pilot               # train split only: learner tuning, planted-effect test, confirmatory family
python -m crest prereg              # freeze the plan; commit it NOW:
git add -f crest_out/prereg/prereg.json crest_out/prereg/prereg.sha256 
git commit -m "Freeze pre-registration"
python -m crest confirm             # once, on held-out calls -> Factor Library with claim levels
python -m crest evidence            # quotes + faithfulness of a cross-fitted risk forecaster
python -m crest index               # provenance tables + hybrid search index
```

**Step 6 — application (Task 1 and Task 2).**

```bash
python -m crest ask "Why do escalations happen in telecom calls?"          # Task 1
python -m crest ask "what about refunds?" --session s.json                 # Task 2: the state file keeps the context
python -m crest chat                                                        # interactive session
```

**Step 7 — query dataset and evaluation.**

```bash
python -m crest queries             # dev + LOCKED test queries, queries.csv, review sheet
python -m crest run-queries         # answers -> crest_out/outputs/
python -m crest evaluate            # eval/metrics.json, REPORT.md, outputs/QUERY_OUTPUTS.md
python -m crest status              # what is done and what is next
```

**Shortcut if the hand labelling cannot be finished.** `python -m crest run-all` runs every stage without the human
inputs. It works, but no finding can reach L3 (everything stays a warning sign at most)

## 4 · Run WITH the LLM (Claude; optional)

What it adds:

* `--llm-writer`: Claude writes the prose from the same evidence pack. It must use the same placeholders and
  citations, and passes the same gates, with one rewrite and then removal of failing sentences.
* `--llm-parser`: Claude reads questions and follow-ups into the same validated slots.
* `build --labeller llm`: Claude labels events on a training sample, and an onset detector is trained on it.
* `evaluate --llm`: an LLM judge rates the query set (brands masked).

It never decides a number or a cause. If the service fails, the rule-based path is used and the answer says so.

**Check the hackathon's data rules first.** Enabling the LLM sends transcript excerpts (or, for the judge, the
questions) to Anthropic's API. The demo data is always safe to use.

```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."          # PowerShell: $env:ANTHROPIC_API_KEY = "sk-ant-..."   (never commit keys)

# safe test on the synthetic demo
python -m crest ask "Why do escalations happen in telecom calls?" --data demo_out/cleaned_data --out demo_out/crest_out --llm --llm-writer --llm-parser

# on the real data (after steps 1-5 above)
python -m crest ask "Why do escalations happen in telecom calls?" --llm --llm-writer --llm-parser
python -m crest chat --llm --llm-writer --llm-parser
python -m crest run-queries --llm --llm-writer --llm-parser
python -m crest evaluate --llm
```

The default model is `claude-opus-5-5` (`crest/config.py`, `llm.model`). Replies are validated against a JSON schema,
cached on disk (`crest_out/llm_cache/`, git-ignored) and logged with request ids and token counts. Switch the LLM on
with the `--llm` flags, not through `--config`: the frozen plan includes the analysis settings.


## 5 · The query dataset

The query set is generated by code from the data (`python -m crest queries`). It has 99 queries in the demo: 88 single
questions and 11 follow-up sessions, 122 questions with the session turns. They are split into dev queries and a
locked test set.

* Every query is tagged by **task** (1 or 2), **difficulty** (easy / medium / hard), **kind** and **use case**. The
  kinds are simple retrieval, multi-hop, premise check, cannot answer, ambiguous, follow-up and known limitation. The
  use cases are monitoring, root cause, segment comparison, product improvement, process improvement, hypothesis test,
  guardrail, evidence lookup and follow-up.
* The events covered are escalations, refunds and churn threats, plus product and service problems customers raise.
* A **known-limitation** category holds questions the system handles badly: misspellings, slang, non-English, effect
  thresholds, policy-change timing, and two events in one question. They are reported separately and never counted in
  the scores.
* Outputs are machine-readable (`outputs_*.jsonl`) and readable (`QUERY_OUTPUTS.md`: every query, its tags, the
  expected behaviour, the outcome and the full answer with the cited turns).
* Human review uses a sheet (`queries_review.csv`) and a 30-answer audit sheet with a PPI-corrected score. There is
  also an optional LLM-as-judge for realism, contextual fit and category.

## 6· Tests

```bash
pytest -q tests/                      # 127 tests
python -m crest sync-cues --check     # the cue lexicons in crest/cues.py still equal the notebook's
```
## For the updated system output, kindly run the file again. Due to shortage of time, the latest version was not able to submit on the deliverables link
