from __future__ import annotations

import hashlib
import re

import numpy as np
import pandas as pd

from .definitions import BEHAVIOURS, EVENTS

WINDOW = 6
MIN_EVENT_CALLS = 20
MIN_SHARE = 0.10
MIN_DIFF = 0.08
SKIP = {"hesitation", "repeat_question"}
DONE = {
    "hold_request": "the agent put the customer on hold or asked them to wait",
    "hold_return": "the agent came back from a hold",
    "apology": "the agent apologised",
    "empathy": "the agent expressed empathy",
    "refusal": "the agent refused a request or cited policy",
    "offer_solution": "the agent offered a concrete solution",
    "agent_transfer": "the agent transferred the call or brought in another team",
    "negative_emotion": "the customer expressed frustration or anger",
    "confusion": "the customer was confused",
    "repeat_contact": "the customer said they had called or explained before",
    "issue_persistence": "the customer said the problem was still not fixed",
    "repeat_question": "the customer repeated an earlier question",
    "competitor_mention": "the customer mentioned a competitor",
    "hesitation": "the customer hesitated",
}
STARTS = {
    ("ESC", "customer_request"): "the customer asking for a supervisor or manager",
    ("ESC", "agent_handoff"): "the agent handing the call to a supervisor or manager",
    ("REF", "customer_request"): "the customer asking for a refund or compensation",
    ("REF", "agent_offer"): "the agent offering a refund, credit or compensation",
    ("CHURN", "cancel"): "the customer saying they want to cancel",
    ("CHURN", "switch"): "the customer saying they may switch to another provider",
    ("CHURN", "not_renew"): "the customer saying they may not renew",
    ("CHURN", "other"): "the customer saying they may leave",
    ("RISK", "explicit"): "an explicit churn threat",
    ("RISK", "competitor"): "the customer comparing the company with a competitor after a complaint",
    ("RISK", "wavering"): "the customer voicing doubts about staying",
}
REASON_RE = re.compile(r"\b(?:because|since|cause|after|i've been|i have been|it's been|it has been|this is the \w+ time|"
                       r"again|still|keeps?|every time|no one|nobody|already|waiting|never|so i|that's why)\b")


def with_frequency(text: str, share: float) -> str:
    adv = "usually" if share >= 0.6 else "often" if share >= 0.3 else "sometimes"
    words = text.split(" ", 3)
    if len(words) >= 3 and words[0] == "the" and words[1] in ("agent", "customer"):
        if words[2] in ("was", "were") and len(words) == 4:
            return f"the {words[1]} {words[2]} {adv} {words[3]}"
        return f"the {words[1]} {adv} {' '.join(words[2:])}"
    return text


def _pct(x: float) -> str:
    return "n/a" if x is None or not np.isfinite(x) else f"{100 * x:.1f}%"


def _clip_quote(text: str, max_words: int = 40) -> tuple[str, str]:
    words = str(text).split()
    if len(words) <= max_words:
        return str(text), str(text)
    q = " ".join(words[:max_words])
    return q, q + " …"


class RationaleBuilder:
    def __init__(self, art, window: int = WINDOW):
        self.art = art
        self.window = window
        t = art.turns
        self.ok = t is not None and len(t) > 0
        if not self.ok:
            return
        self.ci = t["call_idx"].to_numpy()
        self.k = t["turn_id"].to_numpy()
        self.party = t["party"].to_numpy()
        self.behs = [b for b in BEHAVIOURS if b in t.columns]
        self.flags = t[self.behs].to_numpy(dtype=bool)
        calls = art.calls
        self.tids = calls["transcript_id"].astype(str).to_numpy()
        self.n_turns = calls["n_turns"].to_numpy() if "n_turns" in calls.columns else \
            np.bincount(self.ci, minlength=len(calls))
        self.held_out = calls["split"].isin(["dev", "test"]).to_numpy() if "split" in calls.columns else \
            np.ones(len(calls), dtype=bool)
        self.start = np.concatenate([[0], np.cumsum(self.n_turns)[:-1]]).astype(np.int64)
        self.cache: dict = {}
        self.orders: dict = {}

    def onset(self, e: str) -> np.ndarray:
        col = f"{e}_onset"
        lab = self.art.labels
        if col not in lab.columns:
            return np.full(len(self.tids), -1)
        return lab[col].reindex(self.tids).fillna(-1).to_numpy().astype(np.int64)

    def subtype(self, e: str) -> np.ndarray:
        col = f"{e}_subtype"
        lab = self.art.labels
        if col not in lab.columns:
            return np.array([""] * len(self.tids), dtype=object)
        return lab[col].reindex(self.tids).fillna("").astype(str).to_numpy()

    def text(self, i: int, k: int) -> str:
        return str(self.art.turn_text.get(f"{self.tids[i]}:{k}", "") or "")

    def behaviour_onset(self, b: str) -> np.ndarray:
        out = np.full(len(self.tids), -1, dtype=np.int64)
        if not self.ok or b not in self.behs:
            return out
        idx = np.flatnonzero(self.flags[:, self.behs.index(b)])
        if idx.size:
            calls, pos = np.unique(self.ci[idx], return_index=True)
            out[calls] = self.k[idx[pos]]
        return out

    def compute(self, e: str, mask: np.ndarray, key: str) -> dict:
        return self._compute(e, mask, key, self.onset(e) if self.ok else None, self.subtype(e) if self.ok else None,
                             set(EVENTS[e].excluded_behaviours))

    def profile(self, b: str, mask: np.ndarray, key: str) -> dict:
        return self._compute("B:" + b, mask, key, self.behaviour_onset(b) if self.ok else None, None, {b})

    def _compute(self, e: str, mask: np.ndarray, key: str, on, sub, excluded: set) -> dict:
        ck = (e, key)
        if ck in self.cache:
            return self.cache[ck]
        out = {"available": self.ok, "n_event_calls": 0, "precursors": [], "common": [], "contrast": [], "who": None, "reasons": [],
               "chain": [], "too_few": True}
        if not self.ok:
            return out
        ev_all = mask & (on >= 0)
        ev = mask & (on >= 1)
        oth = mask & (on < 0)
        out["n_event_calls"] = int(ev_all.sum())
        out["n_other_calls"] = int(oth.sum())
        if sub is not None and ev_all.any():
            vc = pd.Series(sub[ev_all]).replace("", np.nan).dropna().value_counts(normalize=True)
            if len(vc) and (e, vc.index[0]) in STARTS:
                out["who"] = {"subtype": vc.index[0], "share": float(vc.iloc[0]), "text": STARTS[(e, vc.index[0])]}
        if ev.sum() < MIN_EVENT_CALLS:
            self.cache[ck] = out
            return out
        out["too_few"] = False
        ref = np.full(len(self.tids), -1, dtype=np.int64)
        ref[ev] = on[ev]
        med = int(np.median(on[ev]))
        ref[oth] = np.minimum(med, np.maximum(self.n_turns[oth] - 1, 0))
        r = ref[self.ci]
        win_turn = (r >= 1) & (self.k < r) & (self.k >= r - self.window)
        win = np.zeros((len(self.tids), len(self.behs)), dtype=bool)
        np.logical_or.at(win, self.ci[win_turn], self.flags[win_turn])
        se = win[ev].mean(axis=0)
        so = win[oth].mean(axis=0) if oth.sum() >= MIN_EVENT_CALLS else np.full(len(self.behs), np.nan)
        rows = []
        for j, b in enumerate(self.behs):
            if BEHAVIOURS[b].negative_control or b in excluded:
                continue
            rows.append({"behaviour": b, "share_event": float(se[j]), "share_other": float(so[j]),
                         "diff": float(se[j] - so[j]) if np.isfinite(so[j]) else np.nan, "text": DONE.get(b, BEHAVIOURS[b].label)})
        out["all"] = rows
        rows = [x for x in rows if x["behaviour"] not in SKIP]
        spec_rows = [x for x in rows if np.isfinite(x["diff"]) and x["share_event"] >= MIN_SHARE and x["diff"] >= MIN_DIFF]
        out["precursors"] = sorted(spec_rows, key=lambda x: -x["diff"])[:3]
        common = [x for x in rows if np.isfinite(x["diff"]) and x["share_event"] >= 0.3 and abs(x["diff"]) < MIN_DIFF]
        out["common"] = sorted(common, key=lambda x: -x["share_event"])[:1]
        contrast = [x for x in rows if np.isfinite(x["diff"]) and x["share_other"] >= MIN_SHARE and x["diff"] <= -MIN_DIFF]
        out["contrast"] = sorted(contrast, key=lambda x: x["diff"])[:1]
        seed = int(hashlib.sha256(f"{e}|{key}".encode()).hexdigest()[:8], 16)
        order = np.random.default_rng(seed).permutation(np.flatnonzero(ev))
        order = np.concatenate([order[self.held_out[order]], order[~self.held_out[order]]])
        self.orders[ck] = (order, on)
        out["reasons"] = self._reasons(e, order, on)
        top = out["precursors"][0]["behaviour"] if out["precursors"] else None
        out["chain"] = self._chain(order, on, top)
        self.cache[ck] = out
        return out

    def focus(self, e: str, mask: np.ndarray, key: str, behaviour: str) -> dict | None:
        r = self.compute(e, mask, key)
        row = next((x for x in r.get("all", []) if x["behaviour"] == behaviour), None)
        if row is None or (e, key) not in self.orders:
            return None
        order, on = self.orders[(e, key)]
        return {**row, "chain": self._chain(order, on, behaviour)}

    def link_chain(self, a: str, b: str, mask: np.ndarray) -> list[dict]:
        if not self.ok:
            return []
        oa, ob = self.onset(a), self.onset(b)
        cand = np.flatnonzero(mask & (oa >= 0) & (ob > oa))
        if not len(cand):
            cand = np.flatnonzero(mask & (ob >= 0) & (oa > ob))
            a, b, oa, ob = b, a, ob, oa
        if not len(cand):
            return []
        seed = int(hashlib.sha256(f"{a}>{b}".encode()).hexdigest()[:8], 16)
        order = np.random.default_rng(seed).permutation(cand)
        order = np.concatenate([order[self.held_out[order]], order[~self.held_out[order]]])
        for i in order[:2000]:
            s, ka, kb = int(self.start[i]), int(oa[i]), int(ob[i])
            first = next((k for k in range(0, min(ka, 6)) if self.party[s + k] == "Customer" and
                          len(self.text(i, k).split()) >= 6), None)
            steps = ([("problem", first)] if first is not None else []) + [(a, ka), (b, kb)]
            out = []
            for role, k in steps:
                q, shown = _clip_quote(self.text(i, k))
                if not q.strip():
                    break
                out.append({"role": role, "quote": q, "shown": shown, "turn_uid": f"{self.tids[i]}:{k}"})
            if len(out) == len(steps):
                return out
        return []

    def call_story(self, i: int, o: int, e: str | None, focus: str | None = None, max_moments: int = 4) -> dict:
        out = {"available": self.ok, "problem": None, "moments": [], "event": None}
        if not self.ok:
            return out
        s, n = int(self.start[i]), int(self.n_turns[i])
        end = o if o >= 0 else n
        for k in range(0, min(end, 6)):
            if self.party[s + k] == "Customer" and len(self.text(i, k).split()) >= 6:
                q, shown = _clip_quote(self.text(i, k))
                out["problem"] = {"turn": k, "quote": q, "shown": shown, "turn_uid": f"{self.tids[i]}:{k}"}
                break
        lo = max(0, o - self.window) if o >= 0 else 0
        excluded = set(EVENTS[e].excluded_behaviours) if e in EVENTS else set()
        pop = {}
        if e in EVENTS:
            pop = {x["behaviour"]: x for x in self.compute(e, np.ones(len(self.tids), dtype=bool), "call-population")
                   .get("all", [])}
        latest = {}
        for k in range(lo, end):
            for j, b in enumerate(self.behs):
                if self.flags[s + k, j] and not BEHAVIOURS[b].negative_control and b not in excluded and \
                        (b not in SKIP or b == focus):
                    latest[b] = k if o >= 0 else latest.get(b, k)

        def gap(b):
            d = (pop.get(b) or {}).get("diff", np.nan)
            return -abs(d) if np.isfinite(d) else 0.0

        for b in sorted(latest, key=lambda b: (b != focus, gap(b), -latest[b]))[:max_moments]:
            k = latest[b]
            q, shown = _clip_quote(self.text(i, k))
            p = pop.get(b) or {}
            out["moments"].append({"behaviour": b, "text": DONE.get(b, BEHAVIOURS[b].label), "turn": k,
                                   "party": str(self.party[s + k]), "quote": q, "shown": shown,
                                   "turn_uid": f"{self.tids[i]}:{k}", "share_event": p.get("share_event"),
                                   "share_other": p.get("share_other")})
        out["moments"].sort(key=lambda x: x["turn"])
        out["focus"] = None
        if focus in self.behs:
            j = self.behs.index(focus)
            hits = [k for k in range(n) if self.flags[s + k, j]]
            if hits:
                q, shown = _clip_quote(self.text(i, hits[0]))
                out["focus"] = {"behaviour": focus, "turn": hits[0], "quote": q, "shown": shown,
                                "turn_uid": f"{self.tids[i]}:{hits[0]}", "before_event": o < 0 or hits[0] < o}
        if o >= 0:
            q, shown = _clip_quote(self.text(i, o))
            out["event"] = {"turn": o, "quote": q, "shown": shown, "turn_uid": f"{self.tids[i]}:{o}"}
        return out

    def _reasons(self, e: str, order: np.ndarray, on: np.ndarray, n: int = 2) -> list[dict]:
        out, seen = [], set()
        for i in order[:4000]:
            o = int(on[i])
            for k in (o, o - 1):
                if k < 0:
                    continue
                s = int(self.start[i]) + k
                if self.party[s] != "Customer":
                    continue
                txt = self.text(i, k)
                low = txt.lower()
                if len(low.split()) < 8 or not REASON_RE.search(low) or low in seen:
                    continue
                seen.add(low)
                q, shown = _clip_quote(txt)
                out.append({"quote": q, "shown": shown, "turn_uid": f"{self.tids[i]}:{k}"})
                break
            if len(out) >= n:
                break
        return out

    def _chain(self, order: np.ndarray, on: np.ndarray, top: str | None) -> list[dict]:
        j = self.behs.index(top) if top in self.behs else None
        for i in order[:4000]:
            o = int(on[i])
            s = int(self.start[i])
            lo = max(0, o - self.window)
            mid = None
            if j is not None:
                hits = [k for k in range(o - 1, lo - 1, -1) if self.flags[s + k, j]]
                if not hits:
                    continue
                mid = hits[0]
            first = None
            for k in range(0, max(1, min(o, 6))):
                if self.party[s + k] == "Customer" and len(self.text(i, k).split()) >= 6:
                    first = k
                    break
            steps = []
            if first is not None and (mid is None or first < mid) and first < o:
                steps.append(("problem", first))
            if mid is not None:
                steps.append(("before", mid))
            steps.append(("event", o))
            if len(steps) < 2:
                continue
            out = []
            for role, k in steps:
                q, shown = _clip_quote(self.text(i, k))
                if not q.strip():
                    break
                out.append({"role": role, "quote": q, "shown": shown, "turn_uid": f"{self.tids[i]}:{k}"})
            if len(out) == len(steps):
                return out
        return []


def placeholders(r: dict, prefix: str) -> dict:
    ph = {f"{prefix}.window": str(WINDOW), f"{prefix}.event_calls": f"{r.get('n_event_calls', 0):,}"}
    for i, x in enumerate(r.get("precursors", []), 1):
        ph[f"{prefix}P{i}.share_event"] = _pct(x["share_event"])
        ph[f"{prefix}P{i}.share_other"] = _pct(x["share_other"])
    for i, x in enumerate(r.get("common", []), 1):
        ph[f"{prefix}C{i}.share_event"] = _pct(x["share_event"])
        ph[f"{prefix}C{i}.share_other"] = _pct(x["share_other"])
    for i, x in enumerate(r.get("contrast", []), 1):
        ph[f"{prefix}N{i}.share_event"] = _pct(x["share_event"])
        ph[f"{prefix}N{i}.share_other"] = _pct(x["share_other"])
    if r.get("who"):
        ph[f"{prefix}.who_share"] = _pct(r["who"]["share"])
    return ph
