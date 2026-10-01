from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .cues import CUE_COLS

REQUIRED_TURN_COLS = ["transcript_id", "turn_id", "turn_uid", "speaker", "party", "text", "text_clean", "split",
                      "n_words", "n_filled_pauses", "is_question", "is_backchannel", "is_repeat",
                      "nonverbal_types"] + CUE_COLS
OPTIONAL_TURN_COLS = ["speaker_name", "role_method"]
REQUIRED_CALL_COLS = ["transcript_id", "file_order", "split", "template_group", "n_turns", "opening_domain_vote",
                      "brand", "qc_possibly_truncated", "had_named_speakers"]
OPTIONAL_CALL_COLS = ["template_group_size", "time_of_interaction", "call_date", "call_weekday", "call_hour", "intent",
                      "intent_key", "business_domain", "reason_for_call", "role_low_confidence", "qc_ok"]
SPLITS = ("train", "dev", "test")
ACCOUNT_COLUMNS = {
    "tier": ("tier", "customer_tier", "loyalty_tier", "membership_level", "membership_tier", "status_level", "loyalty_status"),
    "plan": ("plan", "plan_type", "subscription", "product_plan", "package"),
    "segment": ("segment", "customer_segment", "market_segment"),
    "tenure_months": ("tenure_months", "tenure", "months_as_customer", "customer_tenure_months"),
}


class DataValidationError(ValueError):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("cleaned data failed validation:\n  - " + "\n  - ".join(problems))


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def json_sha256(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _read_table(data_dir: Path, name: str, columns: list[str] | None) -> pd.DataFrame:
    pq, csv = data_dir / f"{name}.parquet", data_dir / f"{name}.csv"
    if pq.is_file():
        if columns is not None:
            import pyarrow.parquet as papq
            available = set(papq.ParquetFile(pq).schema_arrow.names)
            columns = [c for c in columns if c in available]
        return pd.read_parquet(pq, columns=columns)
    if csv.is_file():
        df = pd.read_csv(csv)
        if columns is not None:
            df = df[[c for c in columns if c in df.columns]]
        for c in df.columns:
            if df[c].dtype == object and df[c].astype(str).str.startswith("[").any():
                df[c] = df[c].map(lambda v: json.loads(v) if isinstance(v, str) and v.startswith("[") else v)
        return df
    raise FileNotFoundError(f"{name}.parquet (or .csv) not found in {data_dir}")


def load_account_attributes(data_dir: Path, calls: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    path = next((data_dir / f"account_attributes.{ext}" for ext in ("parquet", "csv")
                 if (data_dir / f"account_attributes.{ext}").is_file()), None)
    if path is None:
        return calls, {}
    acc = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    acc.columns = [str(c).strip().lower() for c in acc.columns]
    if "transcript_id" not in acc.columns:
        raise ValueError(f"{path.name} needs a transcript_id column")
    acc["transcript_id"] = acc["transcript_id"].astype(str)
    acc = acc.drop_duplicates("transcript_id")
    out, found = calls.copy(), {}
    for canon, names in ACCOUNT_COLUMNS.items():
        col = next((n for n in names if n in acc.columns), None)
        if col is None:
            continue
        v = acc.set_index("transcript_id")[col].reindex(out["transcript_id"].astype(str))
        if canon == "tenure_months":
            out[canon] = pd.to_numeric(v, errors="coerce").to_numpy()
        else:
            out[canon] = v.astype("string").str.strip().str.lower().fillna("unknown").to_numpy()
        found[canon] = {"source_column": col, "coverage": float(v.notna().mean())}
    return out, {"file": path.name, "fields": found}


def fill_domain_from_brand(votes: pd.Series, brands: pd.Series, min_known: int = 10, min_share: float = 0.8) -> tuple[pd.Series, int]:
    v = votes.astype(str)
    b = brands.astype(str).str.lower()
    known = v != "unknown"
    out = v.copy()
    filled = 0
    if not known.any() or known.all():
        return out, 0
    tab = pd.crosstab(b[known], v[known])
    for brand, row in tab.iterrows():
        n = int(row.sum())
        if brand in ("none", "nan", "", "unknown") or n < min_known or row.max() / n < min_share:
            continue
        m = (b == brand) & ~known
        out[m] = row.idxmax()
        filled += int(m.sum())
    return out, filled


class Corpus:
    def __init__(self, turns: pd.DataFrame, calls: pd.DataFrame, availability: pd.DataFrame | None,
                 leakage_flagged: set, report: dict, opening_turns: int, data_dir: Path | None = None,
                 excluded: pd.DataFrame | None = None):
        self.turns = turns
        self.calls = calls
        self.excluded = excluded if excluded is not None else pd.DataFrame(columns=["transcript_id", "split", "reason"])
        self.availability = availability
        self.leakage_flagged = leakage_flagged
        self.report = report
        self.opening_turns = opening_turns
        self.data_dir = data_dir
        n = calls["n_turns"].to_numpy()
        self.call_start = np.concatenate([[0], np.cumsum(n)[:-1]]).astype(np.int64)
        self.call_ids = calls.index.to_numpy()

    @property
    def n_calls(self) -> int:
        return len(self.calls)

    def fingerprint(self) -> dict:
        split = self.calls[["transcript_id", "split"]].sort_values("transcript_id")
        return {"raw_sha256": self.report.get("raw_sha256"), "n_calls": int(self.n_calls),
                "n_turns": int(len(self.turns)),
                "turn_uid_hash": hashlib.sha256("\n".join(self.turns["turn_uid"].astype(str)).encode()).hexdigest(),
                "split_hash": hashlib.sha256("\n".join(split["transcript_id"] + "\t" + split["split"]).encode()).hexdigest()}

    def turns_of(self, tid: str) -> pd.DataFrame:
        i = int(self.calls.loc[tid, "call_idx"])
        s = int(self.call_start[i])
        return self.turns.iloc[s:s + int(self.calls.loc[tid, "n_turns"])]

    def split_mask_turns(self, splits) -> np.ndarray:
        return self.turns["split"].isin(list(splits)).to_numpy()


def load_corpus(data_dir: str | Path, opening_turns: int | None = None) -> Corpus:
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        raise FileNotFoundError(f"cleaned data folder not found: {data_dir} (run notebooks/01_data_cleaning.ipynb first)")
    problems: list[str] = []
    turns = _read_table(data_dir, "turns", REQUIRED_TURN_COLS + OPTIONAL_TURN_COLS)
    calls = _read_table(data_dir, "conversations", REQUIRED_CALL_COLS + OPTIONAL_CALL_COLS)
    for name, df, req in (("turns", turns, REQUIRED_TURN_COLS), ("conversations", calls, REQUIRED_CALL_COLS)):
        missing = [c for c in req if c not in df.columns]
        if missing:
            problems.append(f"{name}: missing columns {missing} (re-run the current cleaning notebook)")
    if problems:
        raise DataValidationError(problems)

    report_path = data_dir / "cleaning_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
    rep_opening = (report.get("config") or {}).get("OPENING_TURNS")
    if opening_turns is None:
        opening_turns = int(rep_opening) if rep_opening is not None else 4
    elif rep_opening is not None and int(rep_opening) != int(opening_turns):
        problems.append(f"opening_turns={opening_turns} differs from the cleaning notebook's OPENING_TURNS={rep_opening}")

    calls = calls.copy()
    calls["transcript_id"] = calls["transcript_id"].astype(str)
    if not calls["transcript_id"].is_unique:
        problems.append("conversations: transcript_id is not unique")
    calls = calls.sort_values("file_order", kind="mergesort").set_index("transcript_id", drop=False)
    calls.index.name = None
    if not set(calls["split"].unique()) <= set(SPLITS):
        problems.append(f"conversations: unexpected split values {sorted(set(calls['split']) - set(SPLITS))}")
    if calls.groupby("template_group")["split"].nunique().max() > 1:
        problems.append("a template group straddles two splits (split must be locked by template group)")
    for c in ("qc_possibly_truncated", "had_named_speakers"):
        calls[c] = calls[c].fillna(False).astype(bool)
    calls["opening_domain_vote"] = calls["opening_domain_vote"].fillna("unknown").astype(str)
    calls["brand"] = calls["brand"].fillna("none").astype(str)
    calls["opening_domain_vote"], n_filled = fill_domain_from_brand(calls["opening_domain_vote"], calls["brand"])
    calls, account = load_account_attributes(data_dir, calls)
    report = {**report, "opening_domain_filled_from_brand": n_filled, "account_attributes": account}
    if "template_group_size" not in calls.columns:
        calls["template_group_size"] = calls.groupby("template_group")["transcript_id"].transform("size")
    calls["n_turns"] = pd.to_numeric(calls["n_turns"], errors="coerce").fillna(0).astype(np.int64)
    empty = calls["n_turns"] <= 0
    excluded = calls.loc[empty, ["transcript_id", "split"]].assign(reason="no dialogue turns").reset_index(drop=True)
    calls = calls.loc[~empty].copy()
    calls["call_idx"] = np.arange(len(calls), dtype=np.int64)

    turns = turns.copy()
    turns["transcript_id"] = turns["transcript_id"].astype(str)
    unknown = set(turns["transcript_id"]) - set(calls.index)
    if unknown:
        problems.append(f"turns: {len(unknown)} transcript_ids not in conversations")
    turns["call_idx"] = turns["transcript_id"].map(calls["call_idx"]).fillna(-1).astype(np.int64)
    turns = turns.sort_values(["call_idx", "turn_id"], kind="mergesort").reset_index(drop=True)
    if not turns["turn_uid"].is_unique:
        problems.append("turns: turn_uid is not unique")
    counts = turns.groupby("call_idx").size()
    n_turns = calls.set_index("call_idx")["n_turns"]
    if not counts.reindex(n_turns.index, fill_value=0).eq(n_turns).all():
        problems.append("turns: per-call turn counts differ from conversations.n_turns")
    pos = turns.groupby("call_idx").cumcount()
    if not (pos.to_numpy() == turns["turn_id"].to_numpy()).all():
        problems.append("turns: turn_id is not contiguous 0..n-1 within each call")
    if not set(turns["party"].unique()) <= {"Agent", "Customer"}:
        problems.append("turns: party must be Agent or Customer")
    split_turn = turns["transcript_id"].map(calls["split"])
    if not (split_turn == turns["split"]).all():
        problems.append("turns: split differs from the call's split")
    for c in CUE_COLS + ["is_question", "is_backchannel", "is_repeat"]:
        turns[c] = turns[c].fillna(False).astype(bool)
    turns["text"] = turns["text"].fillna("").astype(str)
    turns["text_clean"] = turns["text_clean"].fillna("").astype(str)
    turns["nonverbal_types"] = turns["nonverbal_types"].map(lambda v: list(v) if v is not None and not isinstance(v, float) else [])

    availability, leaky = None, set()
    av_path = data_dir / "column_availability.csv"
    if av_path.is_file():
        availability = pd.read_csv(av_path)
        leaky = set(availability.loc[availability["leakage_flag"].astype(bool), "column"])
    else:
        problems.append("column_availability.csv missing (re-run the current cleaning notebook)")
    for c in ("opening_domain_vote", "brand"):
        if availability is not None:
            cls = availability.loc[(availability["table"] == "conversations") & (availability["column"] == c), "availability"]
            if len(cls) and cls.iloc[0] != "opening":
                problems.append(f"{c} is not classed 'opening' in column_availability.csv")
    if problems:
        raise DataValidationError(problems)
    return Corpus(turns, calls, availability, leaky, report, int(opening_turns), data_dir, excluded)


class Workspace:
    def __init__(self, out_dir: str | Path):
        self.root = Path(out_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "manifest.json"

    def path(self, rel: str) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def exists(self, rel: str) -> bool:
        return (self.root / rel).is_file()

    def write_parquet(self, df: pd.DataFrame, rel: str) -> Path:
        p = self.path(rel)
        df.to_parquet(p, index=False)
        return p

    def read_parquet(self, rel: str) -> pd.DataFrame:
        p = self.root / rel
        if not p.is_file():
            raise FileNotFoundError(f"{p} not found -- run the stage that produces it first (see `python -m crest status`)")
        return pd.read_parquet(p)

    def write_json(self, obj, rel: str) -> Path:
        p = self.path(rel)
        p.write_text(json.dumps(sanitize_json(obj), indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
        return p

    def read_json(self, rel: str):
        p = self.root / rel
        if not p.is_file():
            raise FileNotFoundError(f"{p} not found -- run the stage that produces it first (see `python -m crest status`)")
        return json.loads(p.read_text(encoding="utf-8"))

    def manifest(self) -> dict:
        if self.manifest_path.is_file():
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return {"stages": {}}

    def record_stage(self, stage: str, outputs: list[str], settings_hash: str, extra: dict | None = None,
                     started: float | None = None) -> None:
        m = self.manifest()
        m.setdefault("stages", {})[stage] = {
            "finished_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "seconds": round(time.time() - started, 1) if started else None,
            "settings_hash": settings_hash,
            "outputs": {o: file_sha256(self.root / o) for o in outputs if (self.root / o).is_file()},
            **(extra or {}),
        }
        m["versions"] = runtime_versions()
        self.manifest_path.write_text(json.dumps(sanitize_json(m), indent=2, default=_json_default), encoding="utf-8")


def runtime_versions() -> dict:
    import sklearn
    import scipy
    return {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
            "scikit-learn": sklearn.__version__, "scipy": scipy.__version__, "platform": sys.platform}


def sanitize_json(obj):
    if isinstance(obj, dict):
        return {str(k): sanitize_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_json(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [sanitize_json(v) for v in obj.tolist()]
    if isinstance(obj, (float, np.floating)):
        return None if not np.isfinite(obj) else float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (set, tuple)):
        return list(o)
    if isinstance(o, Path):
        return str(o)
    raise TypeError(f"not JSON serialisable: {type(o).__name__}")
