from __future__ import annotations

import hashlib
import json
import math
import pickle
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

from .definitions import EVENTS

TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(str(text).lower())


class BM25:
    def __init__(self, docs_tokens: list[list[str]], k1: float = 1.5, b: float = 0.75, epsilon: float = 0.25):
        self.k1, self.b, self.epsilon = k1, b, epsilon
        vocab: dict[str, int] = {}
        rows, cols, vals = [], [], []
        doc_len = np.zeros(len(docs_tokens))
        for i, toks in enumerate(docs_tokens):
            doc_len[i] = len(toks)
            counts: dict[int, int] = {}
            for w in toks:
                j = vocab.setdefault(w, len(vocab))
                counts[j] = counts.get(j, 0) + 1
            rows += [i] * len(counts)
            cols += list(counts)
            vals += list(counts.values())
        self.vocab = vocab
        self.tf = sp.csc_matrix((np.asarray(vals, dtype=np.float64), (rows, cols)), shape=(len(docs_tokens), len(vocab)))
        self.doc_len = doc_len
        self.n_docs = len(docs_tokens)
        self.avgdl = float(doc_len.sum() / max(1, self.n_docs))
        df = np.diff(self.tf.indptr).astype(np.float64)
        idf = np.log(self.n_docs - df + 0.5) - np.log(df + 0.5)
        mean_idf = float(idf.mean()) if idf.size else 0.0
        idf[idf < 0] = self.epsilon * mean_idf
        self.idf = idf
        self._norm = self.k1 * (1 - self.b + self.b * self.doc_len / self.avgdl) if self.avgdl > 0 else np.ones(self.n_docs)

    def get_scores(self, query_tokens: list[str], rows: np.ndarray | None = None) -> np.ndarray:
        n = self.n_docs if rows is None else len(rows)
        out = np.zeros(n)
        norm = self._norm if rows is None else self._norm[rows]
        for w in query_tokens:
            j = self.vocab.get(w)
            if j is None:
                continue
            col = self.tf[:, j]
            if rows is None:
                idx, tf = col.indices, col.data
                out[idx] += self.idf[j] * tf * (self.k1 + 1) / (tf + norm[idx])
            else:
                tfv = col.toarray().ravel()[rows]
                nz = tfv > 0
                out[nz] += self.idf[j] * tfv[nz] * (self.k1 + 1) / (tfv[nz] + norm[nz])
        return out


@dataclass
class WindowEmbedder:
    backend: str
    dims: int
    model_name: str = ""
    vectorizer: object = None
    svd: object = None
    _st: object = field(default=None, repr=False)

    @classmethod
    def create(cls, settings, train_texts: list[str], seed: int, log=print) -> "WindowEmbedder":
        ix = settings.index
        if ix.embed_backend in ("auto", "sentence-transformers"):
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer(ix.st_model)
                emb = cls("sentence-transformers", int(model.get_sentence_embedding_dimension()), ix.st_model)
                emb._st = model
                return emb
            except Exception as exc:
                if ix.embed_backend == "sentence-transformers":
                    raise
                log(f"  sentence-transformers unavailable ({type(exc).__name__}); using the LSA embedder")
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=100_000, sublinear_tf=True, dtype=np.float32)
        X = vec.fit_transform(train_texts)
        n_comp = int(max(1, min(ix.lsa_dims, X.shape[1] - 1, X.shape[0] - 1)))
        svd = TruncatedSVD(n_components=n_comp, random_state=seed).fit(X)
        return cls("lsa", n_comp, "tfidf+svd", vec, svd)

    def encode(self, texts: list[str], batch: int = 256) -> np.ndarray:
        if self.backend == "sentence-transformers":
            if self._st is None:
                from sentence_transformers import SentenceTransformer
                self._st = SentenceTransformer(self.model_name)
            Z = self._st.encode(texts, batch_size=batch, normalize_embeddings=True, show_progress_bar=False)
            return np.asarray(Z, dtype=np.float32)
        Z = self.svd.transform(self.vectorizer.transform(texts)).astype(np.float32)
        nrm = np.linalg.norm(Z, axis=1, keepdims=True)
        return Z / np.where(nrm > 0, nrm, 1.0)

    def __getstate__(self):
        d = dict(self.__dict__)
        d["_st"] = None
        return d


def make_windows(corpus, labels: pd.DataFrame, occ: pd.DataFrame, width: int, stride: int) -> pd.DataFrame:
    t = corpus.turns
    calls = corpus.calls
    speaker = t["speaker"].astype(str).to_numpy()
    text = t["text"].astype(str).to_numpy()
    occ_np = occ.to_numpy()
    beh_names = list(occ.columns)
    onsets = {e: labels.loc[corpus.call_ids, f"{e}_onset"].to_numpy() for e in EVENTS}
    rows = []
    for ci, tid in enumerate(corpus.call_ids):
        n = int(calls["n_turns"].iat[ci])
        s0 = int(corpus.call_start[ci])
        starts = list(range(0, max(1, n - width + 1), stride))
        if starts[-1] + width < n:
            starts.append(n - width)
        for st in starts:
            en = min(n, st + width) - 1
            g = np.arange(s0 + st, s0 + en + 1)
            present = sorted({beh_names[j] for j in np.flatnonzero(occ_np[g].any(axis=0))})
            rec = {"call_idx": ci, "transcript_id": tid, "start": st, "end": en, "split": calls["split"].iat[ci],
                   "industry": calls["opening_domain_vote"].iat[ci], "brand": calls["brand"].iat[ci],
                   "behaviours": present,
                   "text": "\n".join(f"[{st + i}] {speaker[x]}: {text[x]}" for i, x in enumerate(g))}
            for e in EVENTS:
                o = int(onsets[e][ci])
                rec[f"pos_{e}"] = "none" if o < 0 else ("before" if en < o else "after" if st > o else "contains")
            rows.append(rec)
    w = pd.DataFrame(rows)
    w.insert(0, "window_id", np.arange(len(w)))
    w["provenance"] = "raw_dialogue"
    return w


class SearchIndex:
    def __init__(self, windows: pd.DataFrame, bm25: BM25, embedder: WindowEmbedder, emb: np.ndarray, settings_dict: dict):
        self.windows = windows
        self.bm25 = bm25
        self.embedder = embedder
        self.emb = emb
        self.settings = settings_dict
        h = hashlib.sha256()
        for txt in windows["text"]:
            h.update(str(txt).encode("utf-8"))
            h.update(b"\x00")
        h.update(json.dumps({"backend": embedder.backend, "model": embedder.model_name, "dims": embedder.dims,
                             **settings_dict}, sort_keys=True).encode())
        self.version = "idx-" + h.hexdigest()[:16]

    @classmethod
    def build(cls, corpus, labels, occ, settings, log=print) -> "SearchIndex":
        ix = settings.index
        w = make_windows(corpus, labels, occ, ix.window, ix.stride)
        toks = [tokenize(x) for x in w["text"]]
        bm = BM25(toks, ix.bm25_k1, ix.bm25_b, ix.bm25_epsilon)
        train_texts = w.loc[w["split"] == "train", "text"].tolist() or w["text"].tolist()
        emb_model = WindowEmbedder.create(settings, train_texts, settings.seed, log)
        E = emb_model.encode(w["text"].tolist())
        return cls(w, bm, emb_model, E, {"window": ix.window, "stride": ix.stride, "k1": ix.bm25_k1, "b": ix.bm25_b,
                                          "epsilon": ix.bm25_epsilon})

    def save(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self.windows.assign(behaviours=self.windows["behaviours"].map(json.dumps)).to_parquet(folder / "windows.parquet", index=False)
        np.save(folder / "embeddings.npy", self.emb)
        with open(folder / "index.pkl", "wb") as f:
            pickle.dump({"bm25": self.bm25, "embedder": self.embedder, "settings": self.settings, "version": self.version}, f)

    @classmethod
    def load(cls, folder: Path) -> "SearchIndex":
        w = pd.read_parquet(folder / "windows.parquet")
        w["behaviours"] = w["behaviours"].map(json.loads)
        with open(folder / "index.pkl", "rb") as f:
            d = pickle.load(f)
        obj = cls(w, d["bm25"], d["embedder"], np.load(folder / "embeddings.npy"), d["settings"])
        return obj

    def filter_mask(self, filters: dict | None) -> np.ndarray:
        w = self.windows
        m = np.ones(len(w), dtype=bool)
        for key, val in (filters or {}).items():
            if val is None or val == [] or val == "":
                continue
            vals = val if isinstance(val, (list, tuple, set)) else [val]
            if key in ("split", "industry", "brand", "transcript_id"):
                m &= w[key].astype(str).isin([str(v) for v in vals]).to_numpy()
            elif key.startswith("pos_"):
                m &= w[key].isin(vals).to_numpy()
            elif key == "behaviour":
                m &= w["behaviours"].map(lambda bs: any(v in bs for v in vals)).to_numpy()
            elif key == "call_idx":
                m &= w["call_idx"].isin(vals).to_numpy()
            else:
                raise KeyError(f"unknown search filter '{key}'")
        return m

    def search(self, query: str, filters: dict | None = None, top_k: int = 10, candidates: int = 200,
               rrf_k: int = 60, mmr_lambda: float = 0.7) -> list[dict]:
        rows = np.flatnonzero(self.filter_mask(filters))
        if rows.size == 0:
            return []
        q_toks = tokenize(query)
        bm = self.bm25.get_scores(q_toks, rows) if q_toks else np.zeros(rows.size)
        qv = self.embedder.encode([query])[0]
        cos = self.emb[rows] @ qv
        n_c = min(candidates, rows.size)
        fused: dict[int, float] = {}
        for scores in (bm, cos):
            if not np.any(scores):
                continue
            order = np.argsort(-scores, kind="mergesort")[:n_c]
            for rank, i in enumerate(order):
                fused[int(rows[i])] = fused.get(int(rows[i]), 0.0) + 1.0 / (rrf_k + rank + 1)
        if not fused:
            return []
        w = self.windows
        by_call: dict[int, list] = {}
        for wid, sc in sorted(fused.items(), key=lambda x: -x[1]):
            by_call.setdefault(int(w["call_idx"].iat[wid]), []).append((wid, sc))
        items = []
        for ci, hits in by_call.items():
            best_wid, best = hits[0]
            st, en = int(w["start"].iat[best_wid]), int(w["end"].iat[best_wid])
            for wid, _ in hits[1:]:
                s2, e2 = int(w["start"].iat[wid]), int(w["end"].iat[wid])
                if s2 <= en + 1 and e2 >= st - 1:
                    st, en = min(st, s2), max(en, e2)
            items.append({"call_idx": ci, "window_id": best_wid, "score": best, "start": st, "end": en})
        rel = np.array([it["score"] for it in items])
        rel = (rel - rel.min()) / (np.ptp(rel) or 1.0)
        V = self.emb[[it["window_id"] for it in items]]
        chosen: list[int] = []
        cand = list(range(len(items)))
        while cand and len(chosen) < top_k:
            if chosen:
                sim = V[cand] @ V[chosen].T
                mmr = mmr_lambda * rel[cand] - (1 - mmr_lambda) * sim.max(axis=1)
            else:
                mmr = rel[cand]
            pick = cand[int(np.argmax(mmr))]
            chosen.append(pick)
            cand.remove(pick)
        out = []
        for rank, i in enumerate(chosen):
            it = items[i]
            wr = w.iloc[it["window_id"]]
            out.append({"rank": rank + 1, "transcript_id": wr["transcript_id"], "call_idx": int(it["call_idx"]),
                        "start": it["start"], "end": it["end"], "window_id": int(it["window_id"]),
                        "score": float(it["score"]), "industry": wr["industry"], "split": wr["split"],
                        "text": wr["text"], "provenance": "raw_dialogue", "index_version": self.version})
        return out


def retrieval_metrics(index: SearchIndex, queries: list[dict], k: int = 10, draws: int = 1000, seed: int = 0) -> dict:
    rec, ndcg = [], []
    for q in queries:
        rel = set(q["relevant"])
        if not rel:
            continue
        hits = [h["transcript_id"] for h in index.search(q["query"], q.get("filters"), top_k=k)]
        rec.append(len(rel & set(hits)) / min(len(rel), k))
        dcg = sum(1.0 / math.log2(i + 2) for i, h in enumerate(hits) if h in rel)
        idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(rel), k)))
        ndcg.append(dcg / idcg if idcg else 0.0)
    rng = np.random.default_rng(seed)

    def ci(v):
        v = np.asarray(v)
        if v.size < 2:
            return [float("nan"), float("nan")]
        b = [v[rng.integers(0, v.size, v.size)].mean() for _ in range(draws)]
        return [float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))]
    return {"n_queries": len(rec), f"recall@{k}": float(np.mean(rec)) if rec else float("nan"), "recall_ci": ci(rec),
            f"ndcg@{k}": float(np.mean(ndcg)) if ndcg else float("nan"), "ndcg_ci": ci(ndcg)}
