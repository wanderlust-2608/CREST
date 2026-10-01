from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class GoldSettings:
    n_random: int = 150
    n_stress: int = 50
    n_double: int = 40
    seed: int = 20260929


@dataclass
class LandmarkSettings:
    last_k: int = 3
    horizon: int = 6
    embed_dims: int = 32
    max_brands: int = 30


@dataclass
class EstimatorSettings:
    n_folds: int = 5
    learner: str = "auto"
    trim_upper: float = 0.9
    propensity_clip: float = 1e-3
    outcome_clip: bool = True
    bootstrap_draws: int = 2000
    alpha: float = 0.05
    bh_q: float = 0.05
    max_behaviours_per_event: int = 12
    min_treated_call_share: float = 0.02
    min_treated_rows_pilot: int = 50
    planted_effect: float = 0.08
    planted_sims: int = 100
    planted_subsample: float = 0.2
    planted_pairs: int = 2
    tune_max_rows: int = 60000
    n_jobs: int = 1
    threads_per_fit: int = 1
    seed: int = 7


@dataclass
class SupportSettings:
    events_sufficient: int = 20
    events_borderline: int = 10
    kept_sufficient: float = 0.8
    kept_borderline: float = 0.5
    halfwidth_sufficient: float = 0.10
    halfwidth_borderline: float = 0.20
    smd_sufficient: float = 0.10
    smd_borderline: float = 0.20


@dataclass
class ClaimSettings:
    gold_f1_min: float = 0.7
    onset_within1_min: float = 0.9
    precision_min: float = 0.8
    min_sensitivity: tuple = ("S2", "S3", "S5", "S8")


@dataclass
class EvidenceSettings:
    random_baseline_draws: int = 20
    dropout_share: float = 0.3
    max_spans_per_factor: int = 2
    spans_per_slice: int = 10
    window_turns: int = 3
    tfidf_features: int = 20000
    forecaster_C: float = 1.0
    forecast_max_negatives: int = 300000


@dataclass
class IndexSettings:
    window: int = 5
    stride: int = 3
    top_k: int = 10
    candidates: int = 200
    rrf_k: int = 60
    mmr_lambda: float = 0.7
    embed_backend: str = "auto"
    st_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    lsa_dims: int = 128
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    bm25_epsilon: float = 0.25


@dataclass
class LabellerSettings:
    semantic_churn: bool = True
    semantic_threshold: float = 0.9
    semantic_encoder: str = "auto"


@dataclass
class LLMSettings:
    backend: str = "none"
    model: str = "claude-opus-5-5"
    effort: str = "medium"
    max_tokens: int = 16000
    dev_sample_size: int = 1500


@dataclass
class Settings:
    data_dir: str = "cleaned_data"
    out_dir: str = "crest_out"
    opening_turns: int = 4
    seed: int = 20260929
    gold: GoldSettings = field(default_factory=GoldSettings)
    landmark: LandmarkSettings = field(default_factory=LandmarkSettings)
    estimator: EstimatorSettings = field(default_factory=EstimatorSettings)
    support: SupportSettings = field(default_factory=SupportSettings)
    claim: ClaimSettings = field(default_factory=ClaimSettings)
    evidence: EvidenceSettings = field(default_factory=EvidenceSettings)
    index: IndexSettings = field(default_factory=IndexSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    labeller: LabellerSettings = field(default_factory=LabellerSettings)

    def to_dict(self) -> dict:
        return json.loads(json.dumps(asdict(self)))

    def analysis_dict(self) -> dict:
        d = self.to_dict()
        d.pop("data_dir"), d.pop("out_dir")
        d["estimator"].pop("n_jobs", None)
        d["estimator"].pop("threads_per_fit", None)
        return d

    def hash(self) -> str:
        return hashlib.sha256(json.dumps(self.analysis_dict(), sort_keys=True).encode()).hexdigest()

    @classmethod
    def from_dict(cls, d: dict | None = None) -> "Settings":
        s = cls()
        for key, value in (d or {}).items():
            if not hasattr(s, key):
                raise KeyError(f"unknown setting '{key}'")
            current = getattr(s, key)
            if dataclasses.is_dataclass(current):
                if not isinstance(value, dict):
                    raise TypeError(f"setting '{key}' must be an object")
                for sub, v in value.items():
                    if not hasattr(current, sub):
                        raise KeyError(f"unknown setting '{key}.{sub}'")
                    old = getattr(current, sub)
                    setattr(current, sub, tuple(v) if isinstance(old, tuple) else v)
            else:
                setattr(s, key, value)
        s.validate()
        return s

    @classmethod
    def load(cls, path: str | Path | None) -> "Settings":
        if path is None:
            return cls()
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def validate(self) -> None:
        e = self.estimator
        if not 2 <= e.n_folds <= 20:
            raise ValueError("estimator.n_folds must be between 2 and 20")
        if not 0.5 < e.trim_upper < 1.0:
            raise ValueError("estimator.trim_upper must be in (0.5, 1)")
        if e.learner not in ("auto", "logistic_ridge", "hgb"):
            raise ValueError("estimator.learner must be auto | logistic_ridge | hgb")
        if e.n_jobs == 0 or e.threads_per_fit < 0 or e.planted_sims < 2 or e.bootstrap_draws < 100:
            raise ValueError("estimator: n_jobs must be non-zero (-1 = all cores), threads_per_fit >= 0, "
                             "planted_sims >= 2, bootstrap_draws >= 100")
        if self.llm.backend not in ("none", "anthropic"):
            raise ValueError("llm.backend must be none | anthropic")
        if self.index.embed_backend not in ("auto", "sentence-transformers", "lsa"):
            raise ValueError("index.embed_backend must be auto | sentence-transformers | lsa")
        if self.opening_turns < 1:
            raise ValueError("opening_turns must be >= 1")
        if not 0.5 <= self.labeller.semantic_threshold < 1.0 or self.labeller.semantic_encoder not in ("auto", "tfidf"):
            raise ValueError("labeller.semantic_threshold must be in [0.5, 1) and labeller.semantic_encoder auto | tfidf")
        bad = set(self.claim.min_sensitivity) - {f"S{i}" for i in range(1, 9)}
        if bad:
            raise ValueError(f"unknown sensitivity analyses in claim.min_sensitivity: {sorted(bad)}")
