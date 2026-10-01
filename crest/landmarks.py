from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .behaviours import occurrence_matrix
from .cues import CUE_DEFS, CUE_NAMES

EXTRA_BEHAVIOURS = ("nc_thanks_info", "nc_readback", "repeat_question", "hesitation")
NONVERBAL = ("HOLD", "PAUSE", "TRANSFER")
_NOT_RECENT = {"a:turn", "c:turn", "a:words", "c:words", "c:filled_pauses"}


def signal_spec() -> list[tuple[str, list[str]]]:
    spec = [("a:turn", ["party"]), ("c:turn", ["party"]), ("a:words", ["n_words", "party"]),
            ("c:words", ["n_words", "party"]), ("a:question", ["is_question", "party"]),
            ("c:question", ["is_question", "party"]), ("c:backchannel", ["is_backchannel", "party"]),
            ("c:filled_pauses", ["n_filled_pauses", "party"]), ("sup:turn", ["speaker"]), ("spec:turn", ["speaker"])]
    spec += [(f"nv:{v.lower()}", ["nonverbal_types"]) for v in NONVERBAL]
    for cue in CUE_NAMES:
        scope = CUE_DEFS[cue][0]
        if scope in ("Agent", "Any"):
            spec.append((f"a:{cue}", [f"cue_{cue}", "party"]))
        if scope in ("Customer", "Any"):
            spec.append((f"c:{cue}", [f"cue_{cue}", "party"]))
    src = {"nc_thanks_info": ["text_clean", "party"], "nc_readback": ["text_clean", "party"],
           "repeat_question": ["is_repeat", "party"], "hesitation": ["n_filled_pauses", "party"]}
    from .definitions import BEHAVIOURS
    spec += [(f"{'a' if BEHAVIOURS[b].party == 'Agent' else 'c'}:{b}", src[b]) for b in EXTRA_BEHAVIOURS]
    return spec


def turn_signals(turns: pd.DataFrame, occ: pd.DataFrame | None = None) -> np.ndarray:
    if occ is None:
        occ = occurrence_matrix(turns, EXTRA_BEHAVIOURS)
    a = (turns["party"] == "Agent").to_numpy()
    c = ~a
    nw = turns["n_words"].fillna(0).to_numpy(dtype=float)
    q = turns["is_question"].to_numpy(dtype=bool)
    nv = turns["nonverbal_types"].to_numpy()
    cols = []
    for name, _src in signal_spec():
        side, what = name.split(":", 1)
        if name == "a:turn":
            v = a
        elif name == "c:turn":
            v = c
        elif what == "words":
            v = nw * (a if side == "a" else c)
        elif what == "question":
            v = q & (a if side == "a" else c)
        elif name == "c:backchannel":
            v = turns["is_backchannel"].to_numpy(dtype=bool) & c
        elif name == "c:filled_pauses":
            v = turns["n_filled_pauses"].fillna(0).to_numpy(dtype=float) * c
        elif name == "sup:turn":
            v = (turns["speaker"] == "Supervisor").to_numpy()
        elif name == "spec:turn":
            v = (turns["speaker"] == "Specialist").to_numpy()
        elif side == "nv":
            key = what.upper()
            v = np.array([key in (x if isinstance(x, (list, tuple, np.ndarray)) else []) for x in nv], dtype=bool)
        elif what in CUE_NAMES:
            v = turns[f"cue_{what}"].to_numpy(dtype=bool) & (a if side == "a" else c)
        else:
            v = occ[what].to_numpy(dtype=bool)
        cols.append(np.asarray(v, dtype=np.float32))
    return np.column_stack(cols).astype(np.float32)


def exclusive_cumsum(M: np.ndarray, call_of_row: np.ndarray) -> np.ndarray:
    M64 = np.asarray(M, dtype=np.float64)
    inc = pd.DataFrame(M64).groupby(np.asarray(call_of_row), sort=False).cumsum().to_numpy()
    excl = np.zeros_like(inc)
    if len(M64) > 1:
        same = np.asarray(call_of_row)[1:] == np.asarray(call_of_row)[:-1]
        excl[1:][same] = inc[:-1][same]
    return excl


def history_features(S: np.ndarray, E: np.ndarray | None, call_start: np.ndarray, call_of_row: np.ndarray,
                     rows_call: np.ndarray, rows_k: np.ndarray, last_k: int) -> np.ndarray:
    names = [n for n, _ in signal_spec()]
    recent_idx = [i for i, n in enumerate(names) if n not in _NOT_RECENT]
    excl = exclusive_cumsum(S, call_of_row)
    s = call_start[rows_call]
    i = s + rows_k
    cum = excl[i]
    lo = s + np.maximum(0, rows_k - last_k)
    recent = (cum - excl[lo])[:, recent_idx] > 0
    k = rows_k.astype(np.float64)
    idx = {n: j for j, n in enumerate(names)}
    fp_rate = cum[:, idx["c:filled_pauses"]] / np.maximum(1.0, cum[:, idx["c:words"]])
    neg_share = cum[:, idx["c:negative_emotion"]] / np.maximum(1.0, cum[:, idx["c:turn"]])
    parts = [k[:, None], np.log1p(k)[:, None], cum, recent.astype(np.float64), fp_rate[:, None], neg_share[:, None]]
    if E is not None and E.shape[1] > 0:
        e_excl = exclusive_cumsum(E, call_of_row)
        parts.append(e_excl[i] / np.maximum(1.0, k)[:, None])
    return np.hstack(parts).astype(np.float32)


def history_feature_names(embed_dims: int) -> list[str]:
    names = [n for n, _ in signal_spec()]
    recent = [n for n in names if n not in _NOT_RECENT]
    out = ["k", "log1p_k"] + [f"cum:{n}" for n in names] + [f"recent:{n}" for n in recent]
    out += ["rate:customer_filled_pauses", "share:customer_negative_turns"]
    out += [f"emb:{j}" for j in range(embed_dims)]
    return out


def history_feature_sources(embed_dims: int) -> dict:
    spec = dict(signal_spec())
    src = {"k": ["turn_id"], "log1p_k": ["turn_id"], "rate:customer_filled_pauses": ["n_filled_pauses", "n_words", "party"],
           "share:customer_negative_turns": ["cue_negative_emotion", "party"]}
    for n, cols in spec.items():
        src[f"cum:{n}"] = cols
        src[f"recent:{n}"] = cols
    for j in range(embed_dims):
        src[f"emb:{j}"] = ["text_clean"]
    return src


@dataclass
class TextEmbedder:
    dims: int
    vectorizer: object = None
    svd: object = None

    def fit(self, texts: list[str], seed: int) -> "TextEmbedder":
        if self.dims <= 0:
            return self
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=50_000, sublinear_tf=True,
                                          dtype=np.float32)
        X = self.vectorizer.fit_transform(texts)
        n_comp = int(min(self.dims, max(1, X.shape[1] - 1), max(1, X.shape[0] - 1)))
        self.svd = TruncatedSVD(n_components=n_comp, random_state=seed)
        self.svd.fit(X)
        return self

    def transform(self, texts: list[str]) -> np.ndarray | None:
        if self.dims <= 0 or self.vectorizer is None:
            return None
        Z = self.svd.transform(self.vectorizer.transform(texts)).astype(np.float32)
        if Z.shape[1] < self.dims:
            Z = np.hstack([Z, np.zeros((Z.shape[0], self.dims - Z.shape[1]), dtype=np.float32)])
        return Z


@dataclass
class Landmarks:
    meta: pd.DataFrame
    X: np.ndarray
    names: list
    sources: dict
    embedder: TextEmbedder
    opening_levels: dict = field(default_factory=dict)

    def save(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self.meta.to_parquet(folder / "meta.parquet", index=False)
        np.save(folder / "X.npy", self.X)
        (folder / "features.json").write_text(pd.Series(self.names).to_json(orient="values"), encoding="utf-8")
        with open(folder / "transform.pkl", "wb") as f:
            pickle.dump({"embedder": self.embedder, "opening_levels": self.opening_levels, "sources": self.sources}, f)

    @classmethod
    def load(cls, folder: Path) -> "Landmarks":
        import json
        meta = pd.read_parquet(folder / "meta.parquet")
        X = np.load(folder / "X.npy")
        names = json.loads((folder / "features.json").read_text(encoding="utf-8"))
        with open(folder / "transform.pkl", "rb") as f:
            extra = pickle.load(f)
        return cls(meta, X, names, extra["sources"], extra["embedder"], extra["opening_levels"])


def opening_levels(corpus, max_brands: int) -> dict:
    train = corpus.calls[corpus.calls["split"] == "train"]
    industries = sorted(train["opening_domain_vote"].astype(str).unique())
    brands = train["brand"].astype(str).value_counts()
    brands = [b for b in brands.index if b != "none"][:max_brands]
    return {"industry": industries, "brand": brands}


def opening_features(calls: pd.DataFrame, levels: dict) -> tuple[np.ndarray, list[str]]:
    ind = calls["opening_domain_vote"].astype(str).to_numpy()
    br = calls["brand"].astype(str).to_numpy()
    cols, names = [], []
    for v in levels["industry"]:
        cols.append(ind == v)
        names.append(f"open:industry={v}")
    for v in levels["brand"]:
        cols.append(br == v)
        names.append(f"open:brand={v}")
    cols.append(~np.isin(br, levels["brand"]) & (br != "none"))
    names.append("open:brand=other")
    return np.column_stack(cols).astype(np.float32), names


def build_landmarks(corpus, settings) -> Landmarks:
    lm_cfg = settings.landmark
    t = corpus.turns
    occ = occurrence_matrix(t, EXTRA_BEHAVIOURS)
    S = turn_signals(t, occ)
    embedder = TextEmbedder(lm_cfg.embed_dims)
    train_text = t.loc[t["split"] == "train", "text_clean"].tolist()
    if lm_cfg.embed_dims > 0 and len(train_text) >= 10:
        if len(train_text) > 150_000:
            rng = np.random.default_rng(settings.seed)
            train_text = [train_text[i] for i in rng.choice(len(train_text), 150_000, replace=False)]
        embedder.fit(train_text, settings.seed)
    E = embedder.transform(t["text_clean"].tolist())
    k_all = t["turn_id"].to_numpy()
    keep = k_all >= corpus.opening_turns
    rows_call = t["call_idx"].to_numpy()[keep]
    rows_k = k_all[keep]
    call_len = corpus.calls["n_turns"].to_numpy()
    call_of_row = t["call_idx"].to_numpy()
    H = history_features(S, E, corpus.call_start, call_of_row, rows_call, rows_k, lm_cfg.last_k)
    names = history_feature_names(E.shape[1] if E is not None else 0)
    levels = opening_levels(corpus, lm_cfg.max_brands)
    O, onames = opening_features(corpus.calls, levels)
    X = np.hstack([H, O[rows_call]])
    sources = history_feature_sources(E.shape[1] if E is not None else 0)
    sources.update({n: ["opening_domain_vote"] if "industry" in n else ["brand"] for n in onames})
    names = names + onames
    idx = np.flatnonzero(keep)
    cum = history_features(S, None, corpus.call_start, call_of_row, rows_call, rows_k, lm_cfg.last_k)
    hn = history_feature_names(0)
    both = (cum[:, hn.index("cum:a:turn")] > 0) & (cum[:, hn.index("cum:c:turn")] > 0)
    calls = corpus.calls
    meta = pd.DataFrame({
        "row": np.arange(len(idx)), "turn_index": idx, "call_idx": rows_call, "k": rows_k,
        "transcript_id": t["transcript_id"].to_numpy()[keep], "party": t["party"].to_numpy()[keep],
        "speaker": t["speaker"].to_numpy()[keep], "split": t["split"].to_numpy()[keep],
        "template_group": calls["template_group"].to_numpy()[rows_call].astype(str),
        "both_spoken": both, "n_turns": call_len[rows_call],
    })
    lm = Landmarks(meta, X, names, sources, embedder, levels)
    check_sources(lm, corpus)
    return lm


def check_sources(lm: Landmarks, corpus) -> None:
    av = corpus.availability
    if av is None:
        return
    allowed = set(av.loc[av["availability"].isin(["turn-past", "opening"]), "column"]) | {"turn_id"}
    bad = {n: s for n, s in lm.sources.items() if not set(s) <= allowed}
    if bad:
        raise AssertionError(f"features built from columns not known before the landmark: {bad}")


def features_for_call(turns_one_call: pd.DataFrame, call_row: pd.DataFrame, lm: Landmarks, ks, last_k: int) -> np.ndarray:
    occ = occurrence_matrix(turns_one_call, EXTRA_BEHAVIOURS)
    S = turn_signals(turns_one_call, occ)
    E = lm.embedder.transform(turns_one_call["text_clean"].tolist())
    ks = np.asarray(ks, dtype=np.int64)
    H = history_features(S, E, np.array([0]), np.zeros(len(turns_one_call), dtype=np.int64),
                         np.zeros(len(ks), dtype=np.int64), ks, last_k)
    O, _ = opening_features(call_row, lm.opening_levels)
    return np.hstack([H, np.repeat(O, len(ks), axis=0)])


def future_invariance_test(corpus, lm: Landmarks, n: int, seed: int, last_k: int) -> dict:
    rng = np.random.default_rng(seed)
    rows = rng.choice(len(lm.meta), size=min(n, len(lm.meta)), replace=False)
    t = corpus.turns
    donor_text = t["text_clean"].to_numpy()
    bool_cols = [c for c in t.columns if c.startswith("cue_")] + ["is_question", "is_backchannel", "is_repeat"]
    failures = 0
    for r in rows:
        m = lm.meta.iloc[r]
        tid, k = m["transcript_id"], int(m["k"])
        one = corpus.turns_of(tid).copy()
        fut = one["turn_id"].to_numpy() >= k
        nf = int(fut.sum())
        one.loc[fut, "text_clean"] = rng.choice(donor_text, size=nf)
        one.loc[fut, "text"] = one.loc[fut, "text_clean"]
        for c in bool_cols:
            one.loc[fut, c] = rng.random(nf) < 0.5
        one.loc[fut, "party"] = rng.choice(["Agent", "Customer"], size=nf)
        one.loc[fut, "speaker"] = rng.choice(["Agent", "Customer", "Supervisor"], size=nf)
        one.loc[fut, "n_words"] = rng.integers(1, 60, size=nf)
        one.loc[fut, "n_filled_pauses"] = rng.integers(0, 5, size=nf)
        x = features_for_call(one, corpus.calls.loc[[tid]], lm, [k], last_k)[0]
        if not np.array_equal(x, lm.X[r]):
            failures += 1
    return {"rows_checked": int(len(rows)), "failures": failures, "passed": failures == 0}
