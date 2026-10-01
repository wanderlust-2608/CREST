# Synthetic demo run (no hackathon data)

Everything in this folder was produced by

```bash
python -m crest demo --out demo_out          # 4,000 simulated calls, seed 11
```

on **invented calls** from `crest/simulate.py`, a call-centre simulator whose causal structure is known: agent
refusals raise a latent frustration that drives escalations, refunds and churn threats; solution offers lower it;
two behaviours (read-backs, "thanks for the information") have no effect and serve as negative controls. The
simulator's oracle computes the true effect of every behaviour, so the report can show how close the estimates are.
No transcript from the hackathon dataset is included.

| File | What it is |
|---|---|
| `REPORT.md` | the evaluation report: design checks, labeller quality on the (simulated) blind gold set, planted-effect test, recovery of the known effects, evidence quality, retrieval, answer metrics by category / difficulty / kind, baselines, the query set's distribution and diversity, and the known limitations |
| `factor_library.csv` | every pre-registered (event, behaviour) estimate with its claim level (L0–L3) and the checks it failed |
| `pilot.json`, `pilot_table.csv` | the train-only pilot: learner tuning, planted-effect test, confirmatory family |
| `prereg.json`, `prereg.sha256` | the frozen analysis plan and its hash |
| **`QUERY_OUTPUTS.md`** | **every query of the query set with its tags (task, difficulty, kind, use case), the expected behaviour, the outcome and the full answer with its cited dialogue turns; follow-up sessions turn by turn** |
| `queries_dev.jsonl`, `queries_test.jsonl`, `queries_lock.json` | the generated query set (98 queries: 85 single questions and 13 follow-up sessions), the lock on the test third, the distribution and diversity of the set |
| `queries.csv`, `queries_review.csv` | every question in one table; the sheet for the human review of the questions |
| `outputs_dev.jsonl`, `outputs_test.jsonl` | every answer, machine-readable: text, sentences with factor ids and cited `turn_uid`s, gate results, route, parsed question |
| `metrics.json` | all numbers behind `REPORT.md` |
| `forecaster_quality.json`, `factor_faithfulness.csv` | evidence-stage diagnostics (forecaster AUC and calibration, faithfulness per factor) |
| `build_checks.json` | future-invariance and outcome-blindness checks, event counts |

Regenerate it with the command above; the numbers are reproducible for the same package versions.

The query set and how it was built are described in [`docs/QUERY_DATASET.md`](../../docs/QUERY_DATASET.md).
