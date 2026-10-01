from __future__ import annotations

import json
import os
import sys
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONWARNINGS", "ignore")


def small_settings(data_dir: Path, out_dir: Path):
    from crest.config import Settings
    s = Settings()
    s.data_dir, s.out_dir = str(data_dir), str(out_dir)
    s.estimator.bootstrap_draws = 500
    s.evidence.spans_per_slice = 4
    s.evidence.random_baseline_draws = 10
    s.gold.n_random, s.gold.n_stress, s.gold.n_double = 150, 50, 30
    return s


@pytest.fixture(scope="session")
def demo(tmp_path_factory):
    from crest.devtools import run_cleaning_notebook
    from crest.pipeline import Pipeline
    from crest.simulate import SimConfig, fill_gold_labels, fill_precision_sheets, write_corpus
    from crest.cli import write_retrieval_queries
    root = tmp_path_factory.mktemp("demo")
    raw, _ = write_corpus(root / "synthetic_transcripts.json", SimConfig(n_calls=1600, seed=23, oracle_reps=40))
    truth = json.loads((root / "synthetic_transcripts_truth.json").read_text())["calls"]
    run_cleaning_notebook(raw, root / "cleaned_data", log_path=root / "cleaning.log")
    pipe = Pipeline(small_settings(root / "cleaned_data", root / "crest_out"), log=lambda m: None)
    pipe.build()
    csv = pipe.gold_sample()
    sample = pipe.ws.read_parquet("gold/sample.parquet")
    filled = fill_gold_labels(sample, truth, csv, pipe.ws.root / "gold" / "gold_labelled.csv", seed=3)
    pipe.precision_sheets()
    fill_precision_sheets(pipe.ws.root / "precision", truth)
    pipe.gold_ingest(filled)
    pipe.pilot()
    pipe.prereg()
    pipe.confirm()
    pipe.evidence()
    pipe.index()
    write_retrieval_queries(pipe, truth)
    pipe.queries()
    pipe.run_queries("all")
    metrics = pipe.evaluate(truth)
    return {"pipe": pipe, "truth": truth, "root": root, "metrics": metrics}


@pytest.fixture(scope="session")
def engine(demo):
    return demo["pipe"].engine()
