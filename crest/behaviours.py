from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from . import cues
from .definitions import BEHAVIOURS, EVENTS, NEGATIVE_CONTROLS

PRECISION_COLUMNS = ["behaviour", "turn_uid", "context_before", "turn_text", "correct"]


def _detect(turns: pd.DataFrame, detector: tuple, views: np.ndarray | None) -> np.ndarray:
    kind = detector[0]
    if kind == "cue":
        return turns[detector[1]].to_numpy().astype(bool)
    if kind == "column":
        return turns[detector[1]].fillna(False).to_numpy().astype(bool)
    if kind == "min_count":
        return turns[detector[1]].fillna(0).to_numpy() >= detector[2]
    if kind == "regex":
        rx = re.compile(detector[1])
        return np.array([bool(rx.search(v)) for v in views], dtype=bool)
    raise ValueError(f"unknown detector {detector}")


def occurrence_matrix(turns: pd.DataFrame, behaviour_ids=None) -> pd.DataFrame:
    behaviour_ids = list(behaviour_ids or BEHAVIOURS)
    views = None
    if any(BEHAVIOURS[b].detector[0] == "regex" for b in behaviour_ids):
        views = np.array([cues.cue_view(t) for t in turns["text_clean"].to_numpy()], dtype=object)
    party = turns["party"].to_numpy()
    out = {}
    for b in behaviour_ids:
        d = BEHAVIOURS[b]
        out[b] = _detect(turns, d.detector, views) & (party == d.party)
    return pd.DataFrame(out, index=turns.index)


def treatment_mask(turns: pd.DataFrame, occ: pd.DataFrame, event: str, behaviour: str) -> np.ndarray:
    m = occ[behaviour].to_numpy().copy()
    pattern = EVENTS[event].occurrence_filters.get(behaviour)
    if pattern:
        rx = re.compile(pattern)
        hits = np.array([bool(rx.search(t)) for t in turns["text_clean"].to_numpy()], dtype=bool)
        m &= ~hits
    return m


def first_occurrence(corpus, mask: np.ndarray) -> np.ndarray:
    from .events import first_turn_per_call
    return first_turn_per_call(corpus, mask)


def blindness_check(turns: pd.DataFrame, sample: int | None = None, seed: int = 0) -> dict:
    idx = np.arange(len(turns))
    if sample is not None and sample < len(turns):
        idx = np.sort(np.random.default_rng(seed).choice(idx, size=sample, replace=False))
    sub = turns.iloc[idx]
    mismatches = {c: 0 for c in cues.CUE_COLS}
    fp_mismatch = 0
    for r in sub.itertuples(index=False):
        fired = cues.cues_for_turn(r.text_clean, r.party)
        for name in cues.CUE_NAMES:
            if (name in fired) != bool(getattr(r, f"cue_{name}")):
                mismatches[f"cue_{name}"] += 1
        if cues.count_filled_pauses(r.text) != int(r.n_filled_pauses):
            fp_mismatch += 1
    total = int(sum(mismatches.values()))
    return {"turns_checked": int(len(sub)), "cue_mismatches": total, "by_cue": {k: v for k, v in mismatches.items() if v},
            "filled_pause_mismatches": fp_mismatch, "passed": total == 0 and fp_mismatch == 0,
            "past_only_by_construction": ["repeat_question (is_repeat)"]}


def regex_blindness_check(turns: pd.DataFrame, behaviour_ids=None) -> dict:
    ids = [b for b in (behaviour_ids or BEHAVIOURS) if BEHAVIOURS[b].detector[0] == "regex"]
    full = occurrence_matrix(turns, ids)
    one_by_one = pd.concat([occurrence_matrix(turns.iloc[[i]], ids) for i in range(min(len(turns), 2000))])
    same = (full.iloc[:len(one_by_one)].to_numpy() == one_by_one.to_numpy()).all()
    return {"behaviours": ids, "passed": bool(same)}


def prevalence(corpus, occ: pd.DataFrame) -> pd.DataFrame:
    calls_with = occ.groupby(corpus.turns["call_idx"].to_numpy()).any().mean()
    return pd.DataFrame({"share_of_turns": occ.mean(), "share_of_calls": calls_with})


def phi_matrix(a: np.ndarray) -> np.ndarray:
    x = a.astype(float)
    n = x.shape[0]
    p = x.mean(axis=0)
    cov = (x.T @ x) / n - np.outer(p, p)
    sd = np.sqrt(p * (1 - p))
    with np.errstate(divide="ignore", invalid="ignore"):
        phi = cov / np.outer(sd, sd)
    phi[~np.isfinite(phi)] = 0.0
    np.fill_diagonal(phi, 1.0)
    return phi


def cooccurrence(corpus, occ: pd.DataFrame) -> pd.DataFrame:
    cols = list(occ.columns)
    turn_phi = phi_matrix(occ.to_numpy())
    calls_any = occ.groupby(corpus.turns["call_idx"].to_numpy()).any()
    call_phi = phi_matrix(calls_any.to_numpy())
    rows = []
    for i, a in enumerate(cols):
        for j in range(i + 1, len(cols)):
            b = cols[j]
            same_party = BEHAVIOURS[a].party == BEHAVIOURS[b].party
            rows.append({"a": a, "b": b, "turn_phi": float(turn_phi[i, j]) if same_party else float("nan"),
                         "call_phi": float(call_phi[i, j])})
    return pd.DataFrame(rows)


def families(co: pd.DataFrame, threshold: float) -> dict:
    parent: dict[str, str] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for r in co.itertuples(index=False):
        if np.isfinite(r.turn_phi) and r.turn_phi > threshold:
            ra, rb = find(r.a), find(r.b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    groups: dict[str, list] = {}
    for b in list(parent):
        groups.setdefault(find(b), []).append(b)
    return {"+".join(sorted(v)): sorted(v) for v in groups.values() if len(v) > 1}


def precision_sheets(corpus, occ: pd.DataFrame, folder: Path, n: int = 20, seed: int = 0, splits=("train",)) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    t = corpus.turns
    in_split = t["split"].isin(list(splits)).to_numpy()
    paths = []
    for b in occ.columns:
        idx = np.flatnonzero(occ[b].to_numpy() & in_split)
        if idx.size == 0:
            continue
        pick = np.sort(rng.choice(idx, size=min(n, idx.size), replace=False))
        rows = []
        for i in pick:
            k = int(t["turn_id"].iat[i])
            before = t.iloc[max(0, i - min(2, k)):i]
            ctx = " | ".join(f"{r.speaker}: {r.text}" for r in before.itertuples(index=False))
            rows.append({"behaviour": b, "turn_uid": t["turn_uid"].iat[i], "context_before": ctx,
                         "turn_text": f"{t['speaker'].iat[i]}: {t['text'].iat[i]}", "correct": ""})
        p = folder / f"precision_{b}.csv"
        pd.DataFrame(rows, columns=PRECISION_COLUMNS).to_csv(p, index=False)
        paths.append(p)
    return paths


def read_precision(folder: Path) -> dict:
    out = {}
    if not folder.is_dir():
        return out
    for p in sorted(folder.glob("precision_*.csv")):
        df = pd.read_csv(p, dtype=str).fillna("")
        judged = df["correct"].str.strip().str.lower()
        judged = judged[judged.isin(["yes", "y", "no", "n", "1", "0", "true", "false"])]
        if len(judged) == 0:
            continue
        b = p.stem[len("precision_"):]
        ok = judged.isin(["yes", "y", "1", "true"])
        out[b] = {"precision": float(ok.mean()), "n_judged": int(len(judged))}
    return out


def negative_controls() -> list[str]:
    return list(NEGATIVE_CONTROLS)


PROPOSAL_SCHEMA = {
    "type": "object",
    "properties": {"behaviours": {"type": "array", "items": {
        "type": "object",
        "properties": {"question": {"type": "string"}, "party": {"type": "string", "enum": ["Agent", "Customer"]},
                       "short_name": {"type": "string"}},
        "required": ["question", "party", "short_name"], "additionalProperties": False}}},
    "required": ["behaviours"], "additionalProperties": False,
}


def propose_with_llm(corpus, labels: pd.DataFrame, event: str, llm, n_windows: int = 20, seed: int = 0) -> list[dict]:
    from .events import render_call
    rng = np.random.default_rng(seed)
    calls = corpus.calls
    train = calls.index[calls["split"] == "train"]
    onset = labels.loc[train, f"{event}_onset"]
    pos = onset[onset > corpus.opening_turns + 2]
    neg = onset[onset < 0]
    if len(pos) < 5 or len(neg) < 5:
        return []
    pos_ids = rng.choice(pos.index.to_numpy(), size=min(n_windows, len(pos)), replace=False)
    neg_ids = rng.choice(neg.index.to_numpy(), size=min(n_windows, len(neg)), replace=False)

    def window(tid, end):
        tt = corpus.turns_of(tid)
        return render_call(tt.iloc[max(0, end - 6):end])
    ends = [int(pos[t]) for t in pos_ids]
    group_a = [window(t, e) for t, e in zip(pos_ids, ends)]
    group_b = [window(t, min(int(calls.loc[t, "n_turns"]), ends[i % len(ends)])) for i, t in enumerate(neg_ids)]
    system = ("You compare two groups of short call excerpts. Group A excerpts end just BEFORE a business event; "
              "group B excerpts come from calls where it never happened, cut at similar points. Propose up to 8 "
              "differences as yes/no questions about a SINGLE turn (for example 'Does the agent promise a callback "
              "without giving a time?'). Do not describe the event itself or anything that happens after the excerpt.")
    user = "GROUP A\n\n" + "\n---\n".join(group_a) + "\n\nGROUP B\n\n" + "\n---\n".join(group_b)
    out = llm.json_call(system=system, user=user, schema=PROPOSAL_SCHEMA, purpose=f"propose_{event}")
    return [dict(p, event=event) for p in out.get("behaviours", [])]
