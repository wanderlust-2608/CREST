from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .definitions import BEHAVIOURS, EVENTS, INDUSTRY_LABEL, PRIMARY_EVENTS, unsupported_message
from .gates import PLACEHOLDER_RE, run_gates
from .its import analyse as its_analyse
from .its import call_times
from .library import CHECKS
from .query import EVENT_PATTERNS, PRODUCT_RE, QuerySpec, _norm
from .rationale import DONE, WINDOW, RationaleBuilder, _clip_quote, with_frequency
from .rationale import placeholders as rationale_placeholders

WRITER_VERSION = "template-v5"
RANK_MIN_CALLS = 30
RANK_MAX_GROUPS = 7
COND_LABEL = {"ESC": "calls with an escalation", "REF": "calls with a refund episode", "CHURN": "calls with a churn threat",
              "RISK": "calls with a retention risk",
              "HANDOFF": "calls where a supervisor joined", "REF_GRANTED": "calls where a refund was granted",
              "REF_DENIED": "calls where a refund was refused", "CANCEL_DONE": "calls where a cancellation was completed"}
COND_CLAUSE = {"ESC": "an escalation came up", "REF": "a refund episode came up", "CHURN": "a churn threat came up",
               "RISK": "a retention risk came up", "HANDOFF": "a supervisor joined", "REF_GRANTED": "a refund was granted",
               "REF_DENIED": "a refund was refused", "CANCEL_DONE": "a cancellation was completed"}
COND_PARENT = {"HANDOFF": "ESC", "REF_GRANTED": "REF", "REF_DENIED": "REF", "CANCEL_DONE": "CHURN"}
COND_OTHER = {"HANDOFF": "escalated calls where no supervisor joined", "REF_GRANTED": "calls where a refund came up but was not granted",
              "REF_DENIED": "calls where a refund came up but was not refused",
              "CANCEL_DONE": "calls with a churn threat where no cancellation was completed"}
TIER_RE = re.compile(r"\b(?:(?:gold|silver|platinum|diamond|elite|premium|premier|vip|bronze|titanium) (?:member|members|"
                     r"membership|status|tier|level|card ?holder|customer|guest|flyer|plan)|loyalty (?:member|members|membership|"
                     r"status|tier|level|program(?:me)?)|(?:long[- ]?time|loyal|valued|frequent) (?:customer|member|guest|client|"
                     r"flyer|traveller|traveler)|member (?:since|for)|been (?:a |your )?(?:customer|member|client) (?:for|since)|"
                     r"(?:i'?m|i am|as) (?:a |an )?(?:gold|silver|platinum|diamond|elite|premium|vip|loyalty|rewards) member)\b")
TIER_NAMES = ("platinum", "diamond", "gold", "silver", "bronze", "elite", "premium", "vip")
ACCOUNT_FILTERS = ("tier", "plan", "segment")
TENURE_LABEL = {"new": "new customers (under six months)", "long": "long-standing customers (two years or more)"}


def self_reported_status(call_idx: np.ndarray, turn_id: np.ndarray, party: np.ndarray, texts, n_calls: int):
    first = np.full(n_calls, -1, dtype=np.int64)
    word = np.array([""] * n_calls, dtype=object)
    for i, k, p, txt in zip(call_idx, turn_id, party, texts):
        if p != "Customer" or first[i] >= 0:
            continue
        m = TIER_RE.search(str(txt).lower())
        if m:
            first[i] = k
            word[i] = next((w for w in TIER_NAMES if w in m.group(0)), "member")
    return first, word


@dataclass
class Artifacts:
    library: pd.DataFrame
    calls: pd.DataFrame
    labels: pd.DataFrame
    turn_text: pd.Series
    spans: pd.DataFrame = field(default_factory=pd.DataFrame)
    faithfulness: pd.DataFrame = field(default_factory=pd.DataFrame)
    report: dict = field(default_factory=dict)
    index: object = None
    library_version: str = ""
    index_version: str = "none"
    opening_turns: int = 4
    turns: pd.DataFrame | None = None


def fmt_pts(x: float, sign: bool = True) -> str:
    if x is None or not np.isfinite(x):
        return "n/a"
    v = round(100 * x, 1) + 0.0
    return (f"{v:+.1f}" if sign else f"{abs(v):.1f}") + " percentage points"


def fmt_ci_pts(lo: float, hi: float) -> str:
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "95% CI not available"
    return f"95% CI {100 * lo:+.1f} to {100 * hi:+.1f} points"


def fmt_pct(x: float) -> str:
    return "n/a" if x is None or not np.isfinite(x) else f"{100 * x:.1f}%"


def fmt_int(x) -> str:
    try:
        return f"{int(round(float(x))):,}"
    except (TypeError, ValueError, OverflowError):
        return "n/a"


def slice_label(filters: dict) -> str:
    parts = []
    if filters.get("call"):
        parts.append("one call")
    if filters.get("industry"):
        parts.append(" / ".join(INDUSTRY_LABEL.get(i, i) for i in filters["industry"]) + " calls")
    if filters.get("brand"):
        parts.append("calls to " + " / ".join(b.title() for b in filters["brand"]))
    if filters.get("intent"):
        parts.append("calls with intent " + " / ".join(filters["intent"]))
    if filters.get("date_from") or filters.get("date_to"):
        parts.append("calls in the selected dates")
    if filters.get("with_event"):
        parts.append(cond_label(filters["with_event"]))
    if filters.get("tier"):
        parts.append("calls from " + " / ".join(filters["tier"]) + " tier customers")
    if filters.get("plan"):
        parts.append("calls from customers on the " + " / ".join(filters["plan"]) + " plan")
    if filters.get("segment"):
        parts.append("calls from the " + " / ".join(filters["segment"]) + " segment")
    if filters.get("tenure"):
        parts.append("calls from " + TENURE_LABEL.get(filters["tenure"], "customers by tenure"))
    if filters.get("self_status"):
        who = " / ".join("a member" if w == "member" else f"a {w} member" for w in filters["self_status"])
        parts.append(f"calls where the customer says they are {who} (self-reported, not a verified tier)")
    return ", ".join(parts) if parts else "all calls"


def cond_label(conds: list) -> str:
    if len(conds) == 1:
        return COND_LABEL.get(conds[0], "calls with " + EVENTS[conds[0]].name)
    clauses = [COND_CLAUSE.get(c, EVENTS[c].name + " came up") for c in conds]
    return "calls where " + ", ".join(clauses[:-1]) + " and " + clauses[-1]


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def call_mask(calls: pd.DataFrame, filters: dict, labels: pd.DataFrame | None = None) -> np.ndarray:
    m = np.ones(len(calls), dtype=bool)
    if filters.get("call"):
        m &= calls["transcript_id"].astype(str).str.lower().isin([str(c).lower() for c in filters["call"]]).to_numpy()
    if filters.get("with_event") and labels is not None:
        for c in filters["with_event"]:
            col = f"{c}_onset"
            if col in labels.columns:
                m &= (labels[col].reindex(calls["transcript_id"].astype(str)).fillna(-1).to_numpy() >= 0)
    if filters.get("industry"):
        m &= calls["opening_domain_vote"].astype(str).isin(filters["industry"]).to_numpy()
    if filters.get("brand"):
        m &= calls["brand"].astype(str).str.lower().isin([b.lower() for b in filters["brand"]]).to_numpy()
    if filters.get("intent") and "intent" in calls.columns:
        m &= calls["intent"].astype(str).str.lower().isin([i.lower() for i in filters["intent"]]).to_numpy()
    for f in ACCOUNT_FILTERS:
        if filters.get(f) and f in calls.columns:
            m &= calls[f].astype(str).str.lower().isin([v.lower() for v in filters[f]]).to_numpy()
    if filters.get("tenure") and "tenure_months" in calls.columns:
        ten = pd.to_numeric(calls["tenure_months"], errors="coerce").to_numpy()
        m &= (ten < 6) if filters["tenure"] == "new" else (ten >= 24)
    if filters.get("self_status") and "self_status" in calls.columns:
        st = calls["self_status"].astype(str).to_numpy()
        m &= (st != "") if filters["self_status"] == ["member"] else np.isin(st, filters["self_status"])
    if (filters.get("date_from") or filters.get("date_to")) and "call_date" in calls.columns:
        d = calls["call_date"].astype(str)
        if filters.get("date_from"):
            m &= (d >= filters["date_from"]).to_numpy()
        if filters.get("date_to"):
            m &= (d <= filters["date_to"]).to_numpy()
    return m


def event_counts(art: Artifacts, event: str, filters: dict) -> dict:
    m = call_mask(art.calls, filters, art.labels)
    on = art.labels.loc[art.calls["transcript_id"], f"{event}_onset"].to_numpy()
    n = int(m.sum())
    k = int(((on >= 0) & m).sum())
    opening = int(((on >= 0) & (on < art.opening_turns) & m).sum())
    return {"calls": n, "event_calls": k, "rate": k / n if n else float("nan"),
            "opening_share": opening / k if k else float("nan")}


PLAIN_REASON = {k: v for k, v in CHECKS.items()}
REASON_ORDER = ["preregistered", "actionable", "negative_controls_clean", "bh_significant", "support_sufficient",
                "gold_f1_ok", "precision_verified", "sensitivity_stable", "dev_test_agree", "bootstrap_excludes_zero",
                "planted_test_passed"]


def _factor_placeholders(fid: str, r: dict, extra: dict) -> dict:
    ph = {
        f"{fid}.att": fmt_pts(r["att"]), f"{fid}.att_abs": fmt_pts(r["att"], sign=False),
        f"{fid}.ci": fmt_ci_pts(r["ci_low"], r["ci_high"]),
        f"{fid}.p_treated": fmt_pct(r.get("p_treated")), f"{fid}.p_counterfactual": fmt_pct(r.get("p_counterfactual")),
        f"{fid}.n_treated": fmt_int(r.get("n_treated")), f"{fid}.n_calls": fmt_int(r.get("n_calls")),
        f"{fid}.attributable": fmt_int(abs(r["attributable"])) if np.isfinite(r.get("attributable", np.nan)) else "n/a",
        f"{fid}.attributable_ci": (f"95% CI {fmt_int(min(abs(r['attributable_ci'][0]), abs(r['attributable_ci'][1])))} to "
                                   f"{fmt_int(max(abs(r['attributable_ci'][0]), abs(r['attributable_ci'][1])))}")
        if isinstance(r.get("attributable_ci"), (list, tuple)) and all(np.isfinite(r["attributable_ci"])) else "n/a",
        f"{fid}.e_value": f"{r['e_value']:.2f}" if np.isfinite(r.get("e_value", np.nan)) else "n/a",
        f"{fid}.e_value_ci": f"{r['e_value_ci']:.2f}" if np.isfinite(r.get("e_value_ci", np.nan)) else "n/a",
        f"{fid}.q": f"{r['q']:.3f}" if np.isfinite(r.get("q", np.nan)) else "n/a",
    }
    ph.update({f"{fid}.{k}": v for k, v in extra.items()})
    return ph


def premise_status(p: dict, row: dict | None) -> str:
    if row is None or row.get("status") != "ok" or row.get("level") in ("L0", "L1", "NC"):
        return "not_estimated"
    s = np.sign(row["att"])
    excludes0 = row["ci_low"] > 0 or row["ci_high"] < 0
    if excludes0 and s == -p["direction"]:
        return "contradicted"
    if not excludes0:
        return "not_supported"
    return "supported" if row["level"] == "L3" else "weak"


def _finite(x) -> bool:
    try:
        return bool(np.isfinite(float(x)))
    except (TypeError, ValueError):
        return False


class PackBuilder:
    def __init__(self, art: Artifacts, settings, max_l2: int = 3):
        self.art = art
        self.s = settings
        self.max_l2 = max_l2
        lib = art.library
        self.lib = lib[~lib["negative_control"]].copy()
        self.nc = lib[lib["negative_control"]]
        self.rat = RationaleBuilder(art)

    def rationale(self, e: str, filters: dict, prefix: str) -> dict:
        key = json.dumps({k: v for k, v in sorted(filters.items())}, sort_keys=True, default=str)
        r = dict(self.rat.compute(e, call_mask(self.art.calls, filters, self.art.labels), key))
        r.pop("all", None)
        tp = self.topics(e, filters, n=3, prefix=prefix + "K")
        r["topics"] = {"terms": [] if tp.get("note") else [{"term": t["term"]} for t in tp["terms"]], "label": tp["label"]}
        r["label"] = slice_label(filters)
        r["prefix"] = prefix
        ph = rationale_placeholders(r, prefix)
        ph.update(tp["placeholders"])
        return {"data": r, "placeholders": ph}

    def rationale_focus(self, e: str, filters: dict, behaviour: str) -> dict | None:
        key = json.dumps({k: v for k, v in sorted(filters.items())}, sort_keys=True, default=str)
        return self.rat.focus(e, call_mask(self.art.calls, filters, self.art.labels), key, behaviour)

    def factors_for(self, event: str, slice_key: str) -> pd.DataFrame:
        f = self.lib[(self.lib["event"] == event) & (self.lib["slice"] == slice_key)]
        order = {"L3": 0, "L2": 1, "L1": 2, "L0": 3}
        return f.assign(_o=f["level"].map(order), _a=-f["attributable"].abs().fillna(0)).sort_values(["_o", "_a"])

    def resolve_slice(self, spec: QuerySpec) -> tuple[str, str, bool, list]:
        f = spec.filters
        notes = []
        extra = [k for k in ("brand", "intent", "date_from", "date_to", "with_event", "tier", "plan", "segment", "tenure",
                             "self_status") if f.get(k)]
        inds = f.get("industry") or []
        if len(inds) == 1:
            key = f"opening_domain_vote={inds[0]}"
            if (self.lib["slice"] == key).any():
                notes.append(f"estimates for {slice_label({'industry': inds})} alone are exploratory (only the all-calls "
                             f"analysis was pre-registered), so they are shown as warning signs at most")
                if extra:
                    notes.append("effects are estimated per industry only; the other filters apply to the counts")
                return key, slice_label({"industry": inds}), True, notes
            notes.append(f"no effect estimates exist for {slice_label(f)} (too few calls); the effects shown are for all calls")
            return "all", "all calls", False, notes
        if inds or extra:
            notes.append("effect estimates are available for all calls and for single industries; the filters apply to the counts only")
        return "all", "all calls", False, notes

    def spans_for(self, fid_all: str, filters: dict, n: int) -> list[dict]:
        sp = self.art.spans
        if sp is None or not len(sp):
            return []
        s = sp[sp["factor_id"] == fid_all]
        if filters.get("industry"):
            s = s[s["industry"].isin(filters["industry"])]
        if filters.get("brand"):
            s = s[s["brand"].str.lower().isin([b.lower() for b in filters["brand"]])]
        if not len(s):
            return []
        s = s.assign(_clean=s["quote"].str.len().rank(pct=True),
                     _faith=s["faithfulness_percentile"].fillna(50)).sort_values(["_faith", "_clean"], ascending=[False, True])
        out, seen = [], set()
        for r in s.itertuples(index=False):
            qkey = str(r.quote).strip().lower()
            if r.transcript_id in seen or qkey in seen:
                continue
            seen.update({r.transcript_id, qkey})
            out.append({"quote": r.quote, "turn_uid": r.turn_uid, "transcript_id": r.transcript_id, "turn_id": int(r.turn_id),
                        "faithfulness_percentile": float(r.faithfulness_percentile) if np.isfinite(r.faithfulness_percentile) else None})
            if len(out) >= n:
                break
        return out

    def no_estimate_reasons(self, fid: str, r: dict) -> list[str]:
        if r.get("status") != "ok":
            return ["there were too few comparable moments to estimate it"]
        sup = self.s.support
        out = []
        ev_t, ev_c = r.get("events_treated"), r.get("events_control")
        if _finite(ev_t) and _finite(ev_c) and min(ev_t, ev_c) < sup.events_sufficient:
            out.append(f"only {{{fid}.events_min}} events in the smaller comparison group")
        if _finite(r.get("kept_share")) and r["kept_share"] < sup.kept_sufficient:
            out.append("few of these moments have comparable moments without the behaviour")
        if _finite(r.get("ci_low")) and _finite(r.get("ci_high")) and (r["ci_high"] - r["ci_low"]) / 2 > sup.halfwidth_sufficient:
            out.append(f"the error bar is too wide ({{{fid}.ci}})")
        if not _finite(r.get("balance_smd")) or r["balance_smd"] > sup.smd_sufficient:
            out.append("the compared moments are still not alike enough")
        return out or ["the checks for a reliable estimate did not pass"]

    def build(self, spec: QuerySpec, shown: list | None = None) -> dict:
        art, s = self.art, self.s
        e = spec.event
        pack = {"spec": spec.to_dict(), "library_version": art.library_version, "index_version": art.index_version,
                "prereg_sha256": art.report.get("prereg_sha256"), "writer": WRITER_VERSION, "placeholders": {},
                "factors": [], "notices": [], "premises": [], "counts": {}, "before_call": {}, "examples": []}
        ph = pack["placeholders"]
        for u in spec.unsupported:
            pack["notices"].append({"kind": "unsupported", "attribute": u.get("attribute"), "text": unsupported_message(u)})
        for d in spec.declined_filters:
            pack["notices"].append({"kind": "declined", "text": f"The filter on {d['field'].replace('_', ' ')} was not applied: "
                                                               f"{d['reason']}. Instead: {d['alternative']}."})
        for i, n in enumerate(spec.notes or []):
            if n.get("kind") == "language":
                ph[f"N{i + 1}.text"] = n["text"]
                pack["notices"].append({"kind": "reading", "text": f"The question looks like {n['language']}; it was read with "
                                                                   f"a small built-in word list as: '{{N{i + 1}.text}}'. For the "
                                                                   f"most reliable answer, ask in English."})
            elif n.get("kind") == "llm_reading":
                ph[f"N{i + 1}.text"] = n["text"]
                pack["notices"].append({"kind": "reading", "text": f"The question was read (with the LLM) as: "
                                                                   f"'{{N{i + 1}.text}}'."})
            elif n.get("kind") == "reading" and n.get("items"):
                ph[f"N{i + 1}.text"] = "; ".join(f"'{a}' as '{b}'" for a, b in n["items"][:6])
                pack["notices"].append({"kind": "reading", "text": f"I read {{N{i + 1}.text}}."})
            elif n.get("kind") == "restart":
                pack["notices"].append({"kind": "reading", "text": "The saved conversation could not be used (it was "
                                                                   "written by another version or edited), so this "
                                                                   "question was read on its own."})
        if spec.filters.get("call"):
            return self.call_pack(spec, pack)
        if e is None:
            if spec.question_type == "behaviour" and spec.behaviour:
                pack["behaviour_profile"] = self.behaviour_profile(spec)
                ph.update(pack["behaviour_profile"].pop("placeholders"))
            elif spec.question_type == "overview":
                pack["overview"] = self.overview(spec)
                ph.update(pack["overview"].pop("placeholders"))
            elif spec.question_type == "help":
                pack["help"] = True
            return pack
        missing = [c for c in [e] + list(spec.filters.get("with_event") or []) + list((spec.compare or {}).get("values") or [])
                   if c in EVENTS and f"{c}_onset" not in art.labels.columns]
        if missing:
            names = _join([EVENTS[c].plural for c in dict.fromkeys(missing)])
            pack["clarify"] = (f"This workspace was built before {names} were labelled, so they cannot be counted yet. Rerun "
                               f"`python -m crest build` and the later stages to add them, or ask about escalations, refunds "
                               f"or churn threats.")
            pack["event"] = {"code": e, "name": EVENTS[e].name, "plural": EVENTS[e].plural, "confirmatory": EVENTS[e].confirmatory}
            return pack
        ev = EVENTS[e]
        pack["event"] = {"code": e, "name": ev.name, "plural": ev.plural, "confirmatory": ev.confirmatory}
        if spec.question_type == "compare" and not spec.compare:
            pack["clarify"] = f"Could you clarify {spec.ambiguous or 'which groups to compare'}?"
            return pack
        if spec.change and not spec.change.get("date"):
            ph["CH.what"] = ("the " + spec.change["what"]) if spec.change.get("what") else "the change"
            ph["CH.example"] = self.example_date()
            pack["clarify"] = (f"When did {{CH.what}} start? Give the date (for example 'after {{CH.example}}') and I will "
                               f"compare {ev.plural} before and after it.")
            return pack
        if spec.ambiguous:
            ph["AMB.text"] = spec.ambiguous
            pack["notices"].append({"kind": "ambiguous", "text": "Part of the question was unclear ({AMB.text}), so the "
                                                                 "answer below leaves that part out."})
        slice_key, label, exploratory, notes = self.resolve_slice(spec)
        pack["slice"] = {"key": slice_key, "label": label, "exploratory": exploratory, "filters": spec.filters}
        pack["notices"] += [{"kind": "slice", "text": n[0].upper() + n[1:] + "."} for n in notes]
        cnt = event_counts(art, e, spec.filters)
        pack["counts"] = cnt
        gm = ((art.report.get("gold_metrics") or {}).get("by_event") or {}).get(e) or {}
        corr = (art.report.get("corrected_rates") or {}).get(e)
        ph.update({"D.calls": fmt_int(cnt["calls"]), "D.event_calls": fmt_int(cnt["event_calls"]), "D.rate": fmt_pct(cnt["rate"]),
                   "D.opening_share": fmt_pct(cnt["opening_share"]),
                   "D.f1": f"{gm['f1']:.2f}" if gm and gm.get("f1") is not None and np.isfinite(gm.get("f1", np.nan)) else "not measured"})
        if corr and not spec.filters:
            ph.update({"D.corrected_rate": fmt_pct(corr["rate"]), "D.corrected_ci": f"95% CI {fmt_pct(corr['ci'][0])} to {fmt_pct(corr['ci'][1])}"})
        if spec.filters.get("with_event"):
            pack["condition"] = self.condition(e, spec.filters)
            ph.update(pack["condition"].pop("placeholders"))
        if spec.change and spec.change.get("date"):
            pack["change"] = self.change(e, spec)
            ph.update(pack["change"].pop("placeholders"))
        if any(u.get("attribute") in ("customer tier", "account age") for u in spec.unsupported):
            pack["proxy"] = self.tier_proxy(e, spec.filters)
            ph.update(pack["proxy"].pop("placeholders"))
        terms = (art.report.get("opening_terms") or {}).get(e) or []
        own = re.compile(EVENT_PATTERNS.get(e, r"$^"))
        chosen = []
        for t in terms:
            if own.search(t["term"]) or any(set(t["term"].split()) & set(c.split()) for c in chosen):
                continue
            chosen.append(t["term"])
        pack["before_call"] = {"opening_share": cnt["opening_share"], "terms": chosen[:4]}
        nc = self.nc[(self.nc["event"] == e) & (self.nc["slice"] == "all")]
        pack["nc_clean"] = bool(len(nc) and nc["negative_controls_clean"].all()) if "negative_controls_clean" in nc else False
        pack["nc_estimable"] = int((nc["status"] == "ok").sum()) if "status" in nc else 0
        fr = self.factors_for(e, slice_key)
        all_rows = self.factors_for(e, "all").set_index("behaviour")
        faith = art.faithfulness.set_index("factor_id") if len(art.faithfulness) else pd.DataFrame()
        l3 = fr[fr["level"] == "L3"]
        l2 = fr[fr["level"] == "L2"]
        clear = (l2["ci_low"] > 0) | (l2["ci_high"] < 0)
        l2 = pd.concat([l2[clear], l2[~clear]]).head(self.max_l2)
        shown_rows = pd.concat([l3, l2])
        if not len(shown_rows) and slice_key != "all":
            fb = self.factors_for(e, "all")
            fb = pd.concat([fb[fb["level"] == "L3"], fb[fb["level"] == "L2"].head(self.max_l2)])
            if len(fb):
                pack["notices"].append({"kind": "slice", "text": f"For {label} alone no behaviour has a usable estimate; the "
                                                                 f"factors below are for all calls (the nearest supported slice)."})
                pack["slice"]["fallback"] = "all"
                shown_rows = fb
        if not len(shown_rows):
            shown_rows = fr.head(3)
        def entry(r: dict) -> dict:
            fid = r["factor_id"]
            fid_all = all_rows.loc[r["behaviour"], "factor_id"] if r["behaviour"] in all_rows.index else fid
            fs = faith.loc[fid_all].to_dict() if len(faith) and fid_all in faith.index else {}
            spans = self.spans_for(fid_all, spec.filters, s.evidence.max_spans_per_factor)
            ev_t, ev_c = r.get("events_treated"), r.get("events_control")
            extra = {"calls_with": fmt_int(fs.get("calls_with_behaviour")), "calls_without_event": fmt_int(fs.get("calls_without_event")),
                     "faith_pct": f"{fs['median_percentile']:.0f}%" if fs.get("faithfulness_passed") else "n/a",
                     "events_treated": fmt_int(ev_t),
                     "events_min": fmt_int(min(ev_t, ev_c)) if _finite(ev_t) and _finite(ev_c) else "n/a"}
            ph.update(_factor_placeholders(fid, r, extra))
            return {"id": fid, "behaviour": r["behaviour"], "label": r["behaviour_label"], "short": r["behaviour_short"],
                    "party": r["party"], "actionable": bool(r["actionable"]), "level": r["level"], "att": float(r["att"]),
                    "ci": [float(r["ci_low"]), float(r["ci_high"])], "support_band": r["support_band"],
                    "failed_checks": list(r["failed_checks"]), "co_occurring": [c[0] for c in (r.get("co_occurring") or [])],
                    "spans": spans, "faithfulness_ok": bool(fs.get("faithfulness_passed")),
                    "counter_available": bool(fs.get("calls_with_behaviour")), "e_value": r.get("e_value"),
                    "sensitivity_ran": bool(r.get("sensitivity")), "status": r.get("status"),
                    "negative_control": bool(r.get("negative_control")),
                    "counts_available": bool(r.get("status") == "ok" and _finite(r.get("n_treated")) and _finite(ev_t)),
                    "no_estimate_reasons": self.no_estimate_reasons(fid, r)}
        for r in shown_rows.to_dict("records"):
            pack["factors"].append(entry(r))
        pack["n_l3"] = sum(f["level"] == "L3" for f in pack["factors"])
        pack["n_l2"] = sum(f["level"] == "L2" for f in pack["factors"])
        ph["A.n_l3"] = fmt_int(pack["n_l3"])
        ph["A.n_l2"] = fmt_int(pack["n_l2"])
        if spec.threshold and spec.threshold.get("target", "effect") == "rate" and not (spec.compare or {}).get("rank"):
            v = spec.threshold["value"]
            ph["TH.rate"] = fmt_pct(v)
            pack["rate_check"] = {"above": bool(np.isfinite(cnt["rate"]) and cnt["rate"] > v)}
        if spec.threshold and spec.threshold.get("target", "effect") == "effect" and \
                spec.question_type not in ("compare", "how_often", "trend"):
            th = spec.threshold
            ok = fr[(fr["status"] == "ok") & fr["level"].isin(["L2", "L3"]) & fr["att"].notna()].copy()
            d, v = th.get("direction", 0), th["value"]
            if d:
                ok["_x"], ok["_lb"], ok["_ub"] = d * ok["att"], np.where(d > 0, ok["ci_low"], -ok["ci_high"]), \
                    np.where(d > 0, ok["ci_high"], -ok["ci_low"])
            else:
                ok["_x"] = ok["att"].abs()
                ok["_lb"] = np.where(ok["ci_low"] > 0, ok["ci_low"], np.where(ok["ci_high"] < 0, -ok["ci_high"], 0.0))
                ok["_ub"] = np.maximum(ok["ci_low"].abs(), ok["ci_high"].abs())
            if th["op"] == "null":
                sel = ok[(ok["ci_low"] <= 0) & (ok["ci_high"] >= 0)].assign(_x=lambda x: x["att"].abs())
                clear = sel.iloc[:0]
            else:
                sel = ok[ok["_x"] > v] if th["op"] == "gt" else ok[ok["_x"] < v]
                clear = sel[sel["_lb"] > v] if th["op"] == "gt" else sel[sel["_ub"] < v]
            sel = sel.sort_values("_x", ascending=th["op"] != "gt")
            rest = ok.drop(sel.index).sort_values("_x", ascending=th["op"] != "gt")
            ph["TH.value"] = fmt_pts(v, sign=False)
            pack["threshold"] = {"op": th["op"], "direction": d, "rows": [entry(r) for r in sel.head(6).to_dict("records")],
                                 "ids": list(sel["factor_id"]), "clear": list(clear["factor_id"]), "n_estimable": int(len(ok)),
                                 "nearest": entry(rest.iloc[0].to_dict()) if len(rest) else None}
        for p in spec.presuppositions:
            if p["event"] != e:
                continue
            rows = fr[fr["behaviour"] == p["behaviour"]]
            row = rows.iloc[0].to_dict() if len(rows) else None
            if row is None and p["behaviour"] in all_rows.index:
                row = all_rows.loc[p["behaviour"]].to_dict()
                row["factor_id"] = all_rows.loc[p["behaviour"], "factor_id"]
            st = premise_status(p, row)
            if row is not None:
                ph.update(_factor_placeholders(row["factor_id"], row, {}))
            pack["premises"].append({**p, "status": st, "factor_id": row["factor_id"] if row is not None else None,
                                     "level": row.get("level") if row is not None else None,
                                     "label": BEHAVIOURS[p["behaviour"]].label, "short": BEHAVIOURS[p["behaviour"]].short,
                                     "excluded": p["behaviour"] in EVENTS[e].excluded_behaviours})
        if spec.behaviour and spec.question_type in ("effect_of",):
            rows = fr[fr["behaviour"] == spec.behaviour]
            if not len(rows) and spec.behaviour in all_rows.index:
                rows = self.factors_for(e, "all")
                rows = rows[rows["behaviour"] == spec.behaviour]
            pack["focus"] = entry(rows.iloc[0].to_dict()) if len(rows) else None
        if spec.question_type == "describe_factor" and spec.factor_ref:
            fid = spec.factor_ref
            if fid.startswith("#") and shown:
                i = int(fid[1:]) - 1
                fid = shown[i] if 0 <= i < len(shown) else None
            rows = self.lib[self.lib["factor_id"] == fid] if fid else self.lib.iloc[:0]
            if len(rows) and rows.iloc[0]["event"] != e:
                rows = rows.iloc[:0]
            pack["focus"] = entry(rows.iloc[0].to_dict()) if len(rows) else None
            if fid and pack["focus"] is None:
                pack["notices"].append({"kind": "factor", "text": "That factor number is not in the current answer; "
                                                                  "ask again about the factors shown last."})
            elif spec.factor_ref.startswith("#") and not shown:
                pack["notices"].append({"kind": "factor", "text": "The last answer did not list any factors."})
        if spec.question_type == "compare" and spec.compare and not spec.compare.get("rank"):
            pack["compare"] = []
            vals = spec.compare["values"]
            for i, v in enumerate(vals):
                if spec.compare["dimension"] == "industry":
                    c = event_counts(art, e, {**spec.filters, "industry": [v]})
                    lab = INDUSTRY_LABEL.get(v, v) + " calls"
                    ev_code = e
                else:
                    c = event_counts(art, v, spec.filters)
                    lab = EVENTS[v].plural
                    ev_code = v
                pack["compare"].append({"label": lab, "event": ev_code, **c})
                ph.update({f"C{i + 1}.rate": fmt_pct(c["rate"]), f"C{i + 1}.calls": fmt_int(c["calls"]),
                           f"C{i + 1}.event_calls": fmt_int(c["event_calls"])})
        if spec.question_type == "trend" and "call_date" in art.calls.columns:
            m = call_mask(art.calls, spec.filters, art.labels)
            on = art.labels.loc[art.calls["transcript_id"], f"{e}_onset"].to_numpy() >= 0
            d = pd.to_datetime(art.calls["call_date"], errors="coerce")
            wk = d.dt.to_period("W").astype(str)
            tab = pd.DataFrame({"w": wk[m], "y": on[m]}).groupby("w")["y"].agg(["size", "mean"]).reset_index()
            tab = tab[tab["size"] >= 20].tail(8)
            pack["trend"] = tab.to_dict("records")
            for i, r in enumerate(pack["trend"]):
                ph.update({f"T{i + 1}.label": r["w"], f"T{i + 1}.rate": fmt_pct(r["mean"]), f"T{i + 1}.calls": fmt_int(r["size"])})
        qt = spec.question_type
        if qt == "issues" or (qt == "what_to_change" and PRODUCT_RE.search(_norm(spec.raw))):
            pack["topics"] = self.topics(e, spec.filters)
            ph.update(pack["topics"].pop("placeholders"))
        if qt in ("why", "what_to_change", "how_often", "examples", "effect_of", "trend", "issues", "describe_factor"):
            r = self.rationale(e, spec.filters, "Q")
            ph.update(r["placeholders"])
            pack["rationale"] = r["data"]
            fb = spec.behaviour if qt == "effect_of" else (pack.get("focus") or {}).get("behaviour") if qt == "describe_factor" \
                else None
            if fb and fb in DONE:
                fo = self.rationale_focus(e, spec.filters, fb)
                if fo is not None:
                    pack["rationale_focus"] = fo
                    ph.update({"QF.share_event": fmt_pct(fo["share_event"]), "QF.share_other": fmt_pct(fo["share_other"])})
        if qt == "compare" and pack.get("compare"):
            for i, c in enumerate(pack["compare"]):
                f2 = {**spec.filters, "industry": [spec.compare["values"][i]]} if spec.compare["dimension"] == "industry" \
                    else dict(spec.filters)
                r = self.rationale(c["event"], f2, f"QG{i + 1}")
                ph.update(r["placeholders"])
                c["rationale"] = r["data"]
        if qt == "compare" and spec.compare and spec.compare.get("rank"):
            pack["rank"] = self.rank(spec)
            ph.update(pack["rank"].pop("placeholders"))
            top_g = pack["rank"]["groups"][:1]
            if top_g and not spec.compare.get("explain_top"):
                dim = spec.compare["dimension"]
                ev_t = top_g[0]["value"] if dim == "event" else e
                f2 = dict(spec.filters) if dim == "event" else {**spec.filters, dim: [top_g[0]["value"]]}
                r = self.rationale(ev_t, f2, "QT")
                ph.update(r["placeholders"])
                pack["rank"]["rationale"] = r["data"]
                pack["rank"]["rationale_event"] = {"code": ev_t, "name": EVENTS[ev_t].name, "plural": EVENTS[ev_t].plural}
            pack["factors"] = []
            top = pack["rank"]["groups"][:1]
            if spec.compare.get("explain_top") and top:
                sub = QuerySpec(raw=spec.raw, event=e, question_type="why", filters=dict(spec.filters))
                dim, v = spec.compare["dimension"], top[0]["value"]
                if dim == "event":
                    sub.event = v
                else:
                    sub.filters[dim] = [v]
                subpack = self.build(sub)
                pack["then"] = {"spec": sub.to_dict(), "pack": subpack}
                ph.update(subpack["placeholders"])
                pack["factors"] = subpack["factors"]
        if qt == "shared" and spec.compare and len(spec.compare.get("values", [])) >= 2:
            pack["shared"] = self.shared(spec, slice_key)
            ph.update(pack["shared"].pop("placeholders"))
            pack["factors"] = []
            pack["shared"]["rationales"] = []
            for i, ev_i in enumerate(pack["shared"]["events"]):
                r = self.rationale(ev_i, spec.filters, f"QG{i + 1}")
                ph.update(r["placeholders"])
                pack["shared"]["rationales"].append({"event": ev_i, "data": r["data"]})
        if qt == "event_link" and spec.compare and len(spec.compare.get("values", [])) >= 2:
            pack["link"] = self.event_link(spec)
            ph.update(pack["link"].pop("placeholders"))
            pack["factors"] = []
            a, b = pack["link"]["a"], pack["link"]["b"]
            r = self.rationale(b, {**spec.filters, "with_event": [a]}, "QL")
            ph.update(r["placeholders"])
            pack["link"]["rationale"] = r["data"]
            pack["link"]["chain"] = self.rat.link_chain(a, b, call_mask(art.calls, spec.filters, art.labels))
        if qt == "issues":
            pack["factors"] = []
        return pack

    def behaviour_profile(self, spec: QuerySpec) -> dict:
        b = spec.behaviour
        out = {"behaviour": b, "available": self.rat.ok, "negative_control": BEHAVIOURS[b].negative_control,
               "label": slice_label(spec.filters), "events": [], "placeholders": {}}
        if not self.rat.ok or out["negative_control"]:
            return out
        ph = out["placeholders"]
        m = call_mask(self.art.calls, spec.filters, self.art.labels)
        on = self.rat.behaviour_onset(b)
        has = m & (on >= 0)
        ph.update({"B.calls": fmt_int(m.sum()), "B.with": fmt_int(has.sum()),
                   "B.rate": fmt_pct(has.sum() / m.sum() if m.sum() else np.nan)})
        for i, e in enumerate(PRIMARY_EVENTS):
            oe = self.rat.onset(e)
            he = oe >= 0
            both = has & he
            ph.update({f"B{i + 1}.with": fmt_pct(he[has].mean() if has.any() else np.nan),
                       f"B{i + 1}.without": fmt_pct(he[m & ~has].mean() if (m & ~has).any() else np.nan),
                       f"B{i + 1}.first": fmt_pct((both & (on < oe)).sum() / both.sum() if both.any() else np.nan)})
            out["events"].append(e)
        key = json.dumps({k: v for k, v in sorted(spec.filters.items())}, sort_keys=True, default=str)
        r = dict(self.rat.profile(b, m, key))
        r.pop("all", None)
        r["prefix"], r["label"] = "QB", out["label"]
        ph.update(rationale_placeholders(r, "QB"))
        out["rationale"] = r
        return out

    def overview(self, spec: QuerySpec) -> dict:
        art = self.art
        m = call_mask(art.calls, spec.filters, art.labels)
        n = int(m.sum())
        ph = {"O.calls": fmt_int(n)}
        out = {"label": slice_label(spec.filters), "events": [], "industries": [], "behaviours": [], "topics": [],
               "placeholders": ph}
        for e in PRIMARY_EVENTS + ("RISK",):
            col = f"{e}_onset"
            if col not in art.labels.columns:
                continue
            on = art.labels[col].reindex(art.calls["transcript_id"].astype(str)).fillna(-1).to_numpy() >= 0
            i = len(out["events"]) + 1
            ph.update({f"O{i}.rate": fmt_pct(on[m].mean() if n else np.nan), f"O{i}.k": fmt_int((on & m).sum())})
            out["events"].append(e)
        if not spec.filters.get("industry") and n:
            vc = art.calls.loc[m, "opening_domain_vote"].astype(str)
            vc = vc[vc != "unknown"].value_counts().head(4)
            for j, (v, k) in enumerate(vc.items(), 1):
                ph[f"OI{j}.share"] = fmt_pct(k / n)
                out["industries"].append(INDUSTRY_LABEL.get(v, v))
        if self.rat.ok and n:
            shares = []
            for b in self.rat.behs:
                if BEHAVIOURS[b].negative_control or b in ("hesitation", "repeat_question"):
                    continue
                on = self.rat.behaviour_onset(b) >= 0
                shares.append((float(on[m].mean()), b))
            for j, (sh, b) in enumerate(sorted(shares, reverse=True)[:4], 1):
                ph[f"OB{j}.share"] = fmt_pct(sh)
                out["behaviours"].append(b)
        for e in PRIMARY_EVENTS:
            tp = self.topics(e, spec.filters, n=2, prefix=f"OT{e}")
            if tp.get("terms") and not tp.get("note"):
                out["topics"].append({"event": e, "terms": [t["term"] for t in tp["terms"]]})
        return out

    def example_date(self) -> str:
        if "call_date" not in self.art.calls.columns:
            return "2025-01-01"
        d = pd.to_datetime(self.art.calls["call_date"], errors="coerce").dropna()
        return str(d.quantile(0.5).date()) if len(d) else "2025-01-01"

    def condition(self, e: str, filters: dict) -> dict:
        art = self.art
        conds = list(filters["with_event"])
        c = conds[0]
        base = {k: v for k, v in filters.items() if k != "with_event"}
        m = call_mask(art.calls, base, art.labels)
        ids = art.calls["transcript_id"]
        ons = np.column_stack([art.labels.loc[ids, f"{x}_onset"].to_numpy() for x in conds])
        oc = np.where((ons >= 0).all(axis=1), ons.max(axis=1), -1)
        oe = art.labels.loc[ids, f"{e}_onset"].to_numpy()
        parent = COND_PARENT.get(c) if len(conds) == 1 else None
        hc = m & (oc >= 0)
        other = m & (oc < 0)
        if parent and f"{parent}_onset" in art.labels.columns:
            other &= art.labels.loc[ids, f"{parent}_onset"].to_numpy() >= 0
        he = oe >= 0
        n_c, k_c, n_o, k_o = int(hc.sum()), int((hc & he).sum()), int(other.sum()), int((other & he).sum())
        ph = {"W.calls": fmt_int(n_c), "W.event_calls": fmt_int(k_c), "W.rate": fmt_pct(k_c / n_c if n_c else np.nan),
              "W.other_calls": fmt_int(n_o), "W.other_rate": fmt_pct(k_o / n_o if n_o else np.nan),
              "W.all_rate": fmt_pct(int((m & he).sum()) / int(m.sum()) if m.sum() else np.nan),
              "W.cond_first": fmt_int(int((hc & he & (oc < oe)).sum())), "W.event_first": fmt_int(int((hc & he & (oe < oc)).sum())),
              "W.same": fmt_int(int((hc & he & (oc == oe)).sum()))}
        return {"cond": c, "conds": conds, "parent": parent, "n": n_c, "k": k_c, "n_other": n_o, "placeholders": ph}

    def change(self, e: str, spec: QuerySpec) -> dict:
        art = self.art
        ch = spec.change
        out = {"available": "call_date" in art.calls.columns, "what": ch.get("what") or "", "placeholders": {}}
        ph = out["placeholders"]
        ph["CH.date"] = ch["date"]
        ph["CH.what"] = ("the " + ch["what"]) if ch.get("what") else "the change"
        ph["CH.min_calls"] = fmt_int(RANK_MIN_CALLS)
        if not out["available"]:
            return out
        d = pd.to_datetime(art.calls["call_date"], errors="coerce")
        D = pd.Timestamp(ch["date"])
        base = {k: v for k, v in spec.filters.items() if k not in ("date_from", "date_to")}
        m = call_mask(art.calls, base, art.labels) & d.notna().to_numpy()
        on = art.labels.loc[art.calls["transcript_id"], f"{e}_onset"].to_numpy() >= 0
        bef, aft = m & (d < D).to_numpy(), m & (d >= D).to_numpy()
        nb, na = int(bef.sum()), int(aft.sum())
        out.update({"n_before": nb, "n_after": na})
        if m.any():
            ph["CH.first"], ph["CH.last"] = str(d[m].min().date()), str(d[m].max().date())
        ph.update({"CH.n_before": fmt_int(nb), "CH.n_after": fmt_int(na)})
        if nb < RANK_MIN_CALLS or na < RANK_MIN_CALLS:
            out["too_few"] = True
            return out
        rb, ra = on[bef].mean(), on[aft].mean()
        diff = ra - rb
        se = np.sqrt(rb * (1 - rb) / nb + ra * (1 - ra) / na)
        lo, hi = diff - 1.96 * se, diff + 1.96 * se
        out.update({"diff": float(diff), "ci": [float(lo), float(hi)], "clear": bool(lo > 0 or hi < 0)})
        ph.update({"CH.rate_before": fmt_pct(rb), "CH.rate_after": fmt_pct(ra), "CH.diff": fmt_pts(diff),
                   "CH.ci": fmt_ci_pts(lo, hi)})
        ind = art.calls["opening_domain_vote"].astype(str)
        pb, pa = ind[bef].value_counts(normalize=True), ind[aft].value_counts(normalize=True)
        out["mix_shift"] = float(0.5 * pb.subtract(pa, fill_value=0).abs().sum())
        ctrl = None
        if any(spec.filters.get(k) for k in ("industry", "brand", "intent", "with_event")):
            ctrl = d.notna().to_numpy() & ~call_mask(art.calls, base, art.labels)
            ph["CH.ctrl_label"] = "calls outside " + slice_label(base)
        its = its_analyse(call_times(art.calls), on, m, ch["date"], ctrl)
        out["its"] = its
        if its.get("available"):
            unit = its["unit"]
            ph.update({"CH.unit": unit, "CH.its_pre": fmt_int(its["n_pre"]), "CH.its_post": fmt_int(its["n_post"]),
                       "CH.pre_slope": fmt_pts(its["pre_slope"]), "CH.level": fmt_pts(its["level"]),
                       "CH.level_ci": fmt_ci_pts(*its["level_ci"]), "CH.slope": fmt_pts(its["slope"]),
                       "CH.slope_ci": fmt_ci_pts(*its["slope_ci"]),
                       "CH.rho1": f"{its['rho1']:.2f}" if np.isfinite(its["rho1"]) else "n/a",
                       "CH.n_placebo": fmt_int(len(its["placebo_levels"])), "CH.n_placebo_large": fmt_int(its["placebo_large"])})
            if its.get("control"):
                c = its["control"]
                ph.update({"CH.ctrl_level": fmt_pts(c["level"]), "CH.ctrl_level_ci": fmt_ci_pts(*c["level_ci"]),
                           "CH.did": fmt_pts(c["diff"]), "CH.did_ci": fmt_ci_pts(*c["diff_ci"])})
        day = (D - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        for key, f2, pre, lab in (("before", {**base, "date_to": day}, "QB", "calls before {CH.date}"),
                                  ("after", {**base, "date_from": ch["date"]}, "QA", "calls from {CH.date} on")):
            r = self.rationale(e, f2, pre)
            r["data"]["label"] = lab
            ph.update(r["placeholders"])
            out[f"rationale_{key}"] = r["data"]
        return out

    def _tier_mentions(self) -> tuple[np.ndarray, np.ndarray]:
        if getattr(self, "_tier", None) is not None:
            return self._tier
        calls = self.art.calls
        if "self_status_turn" in calls.columns:
            self._tier = (calls["self_status_turn"].to_numpy(dtype=np.int64), calls["self_status"].astype(str).to_numpy(dtype=object))
            return self._tier
        rat = self.rat
        n = len(rat.tids) if rat.ok else 0
        first = np.full(n, -1, dtype=np.int64)
        word = np.array([""] * n, dtype=object)
        if rat.ok:
            cust = np.flatnonzero(rat.party == "Customer")
            uids = pd.Index([f"{rat.tids[rat.ci[j]]}:{rat.k[j]}" for j in cust])
            texts = self.art.turn_text.reindex(uids).fillna("").astype(str).str.lower().to_numpy()
            for j, txt in zip(cust, texts):
                i = rat.ci[j]
                if first[i] >= 0 and first[i] <= rat.k[j]:
                    continue
                mt = TIER_RE.search(txt)
                if mt:
                    first[i] = rat.k[j]
                    word[i] = next((w for w in TIER_NAMES if w in mt.group(0)), "member")
        self._tier = (first, word)
        return self._tier

    def light_entry(self, r: dict, ph: dict) -> dict:
        fid = r["factor_id"]
        ph.update(_factor_placeholders(fid, r, {}))
        return {"id": fid, "behaviour": r["behaviour"], "label": r["behaviour_label"], "short": r["behaviour_short"],
                "party": r["party"], "actionable": bool(r["actionable"]), "level": r["level"], "att": float(r["att"]),
                "ci": [float(r["ci_low"]), float(r["ci_high"])], "support_band": r.get("support_band"),
                "failed_checks": list(r["failed_checks"]), "co_occurring": [], "spans": [], "faithfulness_ok": False,
                "counter_available": False, "e_value": r.get("e_value"), "sensitivity_ran": bool(r.get("sensitivity")),
                "status": r.get("status"), "negative_control": bool(r.get("negative_control")), "counts_available": False,
                "no_estimate_reasons": []}

    def call_pack(self, spec: QuerySpec, pack: dict) -> dict:
        art, ph = self.art, pack["placeholders"]
        want = str(spec.filters["call"][0]).lower()
        tids = art.calls["transcript_id"].astype(str)
        low = tids.str.lower()
        hit = np.flatnonzero((low == want).to_numpy())
        if not len(hit) and len(want) >= 6:
            hit = np.flatnonzero(low.str.startswith(want).to_numpy())
        c = {"found": len(hit) == 1, "n_matches": int(len(hit))}
        pack["call"] = c
        ph["CALL.asked"] = want
        if len(hit) > 1:
            ph["CALL.matches"] = ", ".join(tids.iloc[hit[:5]])
        if len(hit) != 1:
            return pack
        i = int(hit[0])
        row = art.calls.iloc[i]
        tid = tids.iloc[i]
        ph["CALL.id"] = tid
        ph["CALL.turns"] = fmt_int(row["n_turns"]) if "n_turns" in art.calls.columns else "n/a"
        c["industry"] = INDUSTRY_LABEL.get(str(row.get("opening_domain_vote", "unknown")), "unclassified")
        brand = str(row.get("brand", "") or "")
        c["brand"] = brand.lower() not in ("", "none", "nan", "unknown")
        ph["CALL.brand"] = brand.title()
        when = call_times(art.calls.iloc[[i]]).iloc[0]
        c["dated"] = bool(pd.notna(when))
        ph["CALL.when"] = str(when)[:16] if pd.notna(when) else ""
        lab = art.labels.loc[tid] if tid in art.labels.index else None
        evs = []
        for code in EVENTS:
            col = f"{code}_onset"
            if lab is not None and col in art.labels.columns and pd.notna(lab[col]) and lab[col] >= 0:
                evs.append({"code": code, "onset": int(lab[col])})
        evs.sort(key=lambda x: (x["onset"], list(EVENTS).index(x["code"])))
        for j, x in enumerate(evs):
            ph[f"CE{j + 1}.turn"] = str(x["onset"])
        c["events"] = evs
        main = [x for x in evs if x["code"] in PRIMARY_EVENTS + ("RISK",)]
        target = spec.event if spec.event in EVENTS else (main[0]["code"] if main else None)
        c["target"] = target
        o = -1
        if target is not None:
            ev = EVENTS[target]
            pack["event"] = {"code": target, "name": ev.name, "plural": ev.plural, "confirmatory": ev.confirmatory}
            o = next((x["onset"] for x in evs if x["code"] == target), -1)
            gm = ((art.report.get("gold_metrics") or {}).get("by_event") or {}).get(target) or {}
            ph["D.f1"] = f"{gm['f1']:.2f}" if gm.get("f1") is not None and np.isfinite(gm.get("f1", np.nan)) else "not measured"
        c["onset"] = o
        ph["CALL.onset"] = str(o)
        ph["CALL.window"] = str(WINDOW)
        st = self.rat.call_story(i, o, target, spec.behaviour)
        c["story"] = st
        if st.get("problem"):
            ph["CALL.problem_turn"] = str(st["problem"]["turn"])
        if st.get("focus"):
            ph["CALL.focus_turn"] = str(st["focus"]["turn"])
        for j, m in enumerate(st["moments"]):
            ph[f"CM{j + 1}.turn"] = str(m["turn"])
            ph[f"CM{j + 1}.share_event"] = fmt_pct(m["share_event"]) if m["share_event"] is not None else "n/a"
            ph[f"CM{j + 1}.share_other"] = fmt_pct(m["share_other"]) if m["share_other"] is not None else "n/a"
        if target is not None and o >= 0:
            rows = self.factors_for(target, "all")
            present = [m["behaviour"] for m in st["moments"]]
            rows = rows[rows["behaviour"].isin(present) & rows["level"].isin(["L2", "L3"]) & ~rows["negative_control"]]
            pack["factors"] = [self.light_entry(r, ph) for r in rows.head(3).to_dict("records")]
        return pack

    def tier_proxy(self, e: str, filters: dict) -> dict:
        out = {"available": self.rat.ok, "groups": [], "quote": None, "placeholders": {}}
        if not self.rat.ok:
            return out
        first, word = self._tier_mentions()
        m = call_mask(self.art.calls, filters, self.art.labels)
        on = self.rat.onset(e)
        n_turns = self.rat.n_turns
        ev = on >= 0
        med = int(np.median(on[ev & m])) if (ev & m).any() else int(np.median(n_turns))
        ref = np.where(ev, on, np.minimum(med, np.maximum(n_turns - 1, 0)))
        has = m & (first >= 0) & (first < ref)
        rest = m & ~has
        ph = out["placeholders"]
        out["n"] = int(has.sum())
        ph.update({"P.calls": fmt_int(has.sum()), "P.rate": fmt_pct(ev[has].mean() if has.any() else np.nan),
                   "P.other_calls": fmt_int(rest.sum()), "P.rate_other": fmt_pct(ev[rest].mean() if rest.any() else np.nan)})
        groups = []
        for w in TIER_NAMES:
            g = has & (word == w)
            if g.sum() >= RANK_MIN_CALLS:
                groups.append({"word": w, "n": int(g.sum()), "rate": float(ev[g].mean())})
        groups.sort(key=lambda x: -x["rate"])
        for i, g in enumerate(groups[:5]):
            ph.update({f"P{i + 1}.rate": fmt_pct(g["rate"]), f"P{i + 1}.calls": fmt_int(g["n"])})
        out["groups"] = groups[:5]
        cand = np.flatnonzero(has & self.rat.held_out) if (has & self.rat.held_out).any() else np.flatnonzero(has)
        for i in cand[:50]:
            uid = f"{self.rat.tids[i]}:{int(first[i])}"
            txt = str(self.art.turn_text.get(uid, "") or "")
            if 6 <= len(txt.split()) <= 60:
                out["quote"] = {"quote": txt, "turn_uid": uid}
                break
        return out

    def topics(self, e: str, filters: dict, n: int = 5, prefix: str = "K") -> dict:
        it = (self.art.report.get("issue_terms") or {}).get(e)
        out = {"terms": [], "quotes": [], "note": None, "label": "calls", "placeholders": {}}
        if it is None:
            out["note"] = "Topic statistics are not available for this workspace (run `python -m crest confirm` again)."
            return out
        inds = filters.get("industry") or []
        key = "all"
        if len(inds) == 1:
            key, out["label"] = f"opening_domain_vote={inds[0]}", slice_label({"industry": inds})
            if key not in it:
                out["note"] = f"There are too few {out['label']} to list the words customers use in them."
        elif inds or any(v for k, v in filters.items() if k != "industry"):
            out["note"] = "Words are listed for all calls or for a single industry; the other filters do not apply to them."
        d = it.get(key) or {}
        out["terms"] = [dict(t) for t in (d.get("terms") or [])[:n]]
        ph = out["placeholders"]
        ph[f"{prefix}.event_calls"] = fmt_int(d.get("n_event_calls"))
        seen = set()
        for i, t in enumerate(out["terms"]):
            ph[f"{prefix}{i + 1}.share"] = fmt_pct(t.get("share_event"))
            ph[f"{prefix}{i + 1}.share_other"] = fmt_pct(t.get("share_other"))
            for uid in t.get("examples") or []:
                call = uid.rsplit(":", 1)[0]
                txt = self.art.turn_text.get(uid)
                if txt and call not in seen and str(txt).strip().lower() not in seen and len(out["quotes"]) < 3:
                    seen.update({call, str(txt).strip().lower()})
                    out["quotes"].append({"quote": str(txt), "turn_uid": uid, "term": t["term"]})
                    break
        return out

    def rank(self, spec: QuerySpec) -> dict:
        art, e, dim = self.art, spec.event, spec.compare["dimension"]
        groups, small = [], 0
        if dim == "event":
            cands = [(EVENTS[v].plural, v, event_counts(art, v, spec.filters)) for v in spec.compare["values"] if v in EVENTS]
        else:
            col = {"industry": "opening_domain_vote", "brand": "brand"}.get(dim, dim)
            vals = [v for v in art.calls[col].astype(str).value_counts().index if v.lower() not in ("unknown", "nan", "none")] \
                if col in art.calls.columns else []
            base = {k: v for k, v in spec.filters.items() if k != dim}
            cands = []
            for v in vals:
                lab = (INDUSTRY_LABEL.get(v, v) + " calls" if dim == "industry" else f"calls to {v.title()}" if dim == "brand"
                       else f"{v} {dim} calls")
                cands.append((lab, v, event_counts(art, e, {**base, dim: [v]})))
        for lab, v, c in cands:
            if dim != "event" and c["calls"] < RANK_MIN_CALLS:
                small += 1
                continue
            groups.append({"label": lab, "value": v, **c})
        groups.sort(key=lambda g: (-(g["rate"] if np.isfinite(g["rate"]) else -1), g["label"]))
        th = None
        if spec.threshold:
            v, op = spec.threshold["value"], spec.threshold["op"]
            th = {"op": op, "labels": [g["label"] for g in groups if np.isfinite(g["rate"]) and
                                       (g["rate"] > v if op == "gt" else g["rate"] < v)]}
        groups = groups[:RANK_MAX_GROUPS]
        ph = {"R.min_calls": fmt_int(RANK_MIN_CALLS), "R.n_small": fmt_int(small)}
        if th is not None:
            ph["TH.rate"] = fmt_pct(spec.threshold["value"])
        for i, g in enumerate(groups):
            ph.update({f"R{i + 1}.rate": fmt_pct(g["rate"]), f"R{i + 1}.calls": fmt_int(g["calls"]),
                       f"R{i + 1}.event_calls": fmt_int(g["event_calls"])})
        return {"dimension": dim, "groups": groups, "n_small": small, "placeholders": ph, "threshold": th}

    def shared(self, spec: QuerySpec, slice_key: str) -> dict:
        evs = [v for v in spec.compare["values"] if v in EVENTS][:3]
        ph, per_event, fallback = {}, [], False
        for i, ev in enumerate(evs):
            c = event_counts(self.art, ev, spec.filters)
            ph.update({f"E{i + 1}.rate": fmt_pct(c["rate"]), f"E{i + 1}.event_calls": fmt_int(c["event_calls"]),
                       f"E{i + 1}.calls": fmt_int(c["calls"])})
            fr = self.factors_for(ev, slice_key)
            if slice_key != "all" and not fr["level"].isin(["L2", "L3"]).any():
                fr, fallback = self.factors_for(ev, "all"), True
            per_event.append(fr)
        rows = []
        for b, d in BEHAVIOURS.items():
            if d.negative_control or (spec.behaviour and b != spec.behaviour):
                continue
            cells = []
            for ev, fr in zip(evs, per_event):
                r = fr[fr["behaviour"] == b]
                if not len(r):
                    cells.append(None)
                    continue
                r = r.iloc[0].to_dict()
                estimable = r.get("status") == "ok" and r["level"] in ("L2", "L3") and _finite(r.get("att"))
                if estimable:
                    ph.update(_factor_placeholders(r["factor_id"], r, {}))
                cells.append({"event": ev, "id": r["factor_id"], "level": r["level"],
                              "att": float(r["att"]) if estimable else float("nan"), "estimable": estimable,
                              "flagged": estimable and (r["ci_low"] > 0 or r["ci_high"] < 0)})
            if any(cells):
                rows.append({"behaviour": b, "short": d.short, "actionable": d.actionable, "cells": cells})
        return {"events": evs, "rows": rows, "fallback": fallback, "asked": spec.compare.get("asked"),
                "focus": spec.behaviour, "placeholders": ph}

    def event_link(self, spec: QuerySpec) -> dict:
        a, b = spec.compare["values"][:2]
        art = self.art
        m = call_mask(art.calls, spec.filters, art.labels)
        ids = art.calls["transcript_id"]
        oa = art.labels.loc[ids, f"{a}_onset"].to_numpy()
        ob = art.labels.loc[ids, f"{b}_onset"].to_numpy()
        ha, hb = (oa >= 0) & m, (ob >= 0) & m
        both = ha & hb
        not_a = m & ~ha
        ph = {"L.calls": fmt_int(m.sum()), "L.a_calls": fmt_int(ha.sum()), "L.b_calls": fmt_int(hb.sum()),
              "L.both": fmt_int(both.sum()), "L.a_first": fmt_int((both & (oa < ob)).sum()),
              "L.b_first": fmt_int((both & (ob < oa)).sum()), "L.same": fmt_int((both & (oa == ob)).sum()),
              "L.b_given_a": fmt_pct(both.sum() / ha.sum() if ha.sum() else float("nan")),
              "L.b_given_not_a": fmt_pct((hb & not_a).sum() / not_a.sum() if not_a.sum() else float("nan"))}
        return {"a": a, "b": b, "both": int(both.sum()), "a_calls": int(ha.sum()), "placeholders": ph}


def _S(text, kind, factor_ids=(), turn_uids=(), quote=None, core=False):
    return {"text": text, "kind": kind, "factor_ids": list(factor_ids), "turn_uids": list(turn_uids), "quote": quote,
            "core": core}


def premise_sentences(pack: dict) -> list[dict]:
    out = []
    ev = pack.get("event", {})
    for p in pack["premises"]:
        f, lab = p["factor_id"], p["short"]
        up = p["direction"] > 0
        if p["excluded"]:
            out.append(_S(f"The question assumes a link between {lab} and {ev['plural']}, but {lab} {_be(lab)} part of how "
                          f"{ev['plural']} are defined here, so the data cannot test that link.", "premise", core=True))
        elif p["status"] == "supported":
            verb = "raise" if up else "lower"
            out.append(_S(f"The data supports a limited version of this premise: under the stated assumptions, {lab} {_be(lab)} "
                          f"estimated to {verb} the chance of {article(ev['name'])} {ev['name']} later in the call "
                          f"({{{f}.att}}, {{{f}.ci}}) [{f}].", "premise", [f], core=True))
        elif p["status"] == "weak":
            rel = "higher" if up else "lower"
            out.append(_S(f"The data does not establish this premise as an effect: {lab} {_be(lab)} only associated with a {rel} "
                          f"chance of {article(ev['name'])} {ev['name']} ({{{f}.att}}, {{{f}.ci}}) [{f}].", "premise", [f], core=True))
        elif p["status"] == "contradicted":
            rel = "lower" if up else "higher"
            out.append(_S(f"The data does not support this premise: {lab} {_be(lab)} associated with a {rel} chance of "
                          f"{article(ev['name'])} {ev['name']}, the opposite direction ({{{f}.att}}, {{{f}.ci}}) [{f}].",
                          "premise", [f], core=True))
        elif p["status"] == "not_supported":
            out.append(_S(f"The data does not support this premise: for {lab}, the estimated difference is compatible "
                          f"with no difference at all ({{{f}.ci}}) [{f}].", "premise", [f], core=True))
        else:
            out.append(_S(f"The data cannot confirm this premise: no reliable estimate exists for {lab} and "
                          f"{ev['plural']}.", "premise", core=True))
    return out


def _plural(noun: str) -> bool:
    return noun.split()[-1].endswith("s")


def _be(noun: str) -> str:
    return "are" if _plural(noun) else "is"


def _cap(t: str) -> str:
    return t[0].upper() + t[1:] if t else t


def factor_sentences(pack: dict, f: dict, detail: str = "full") -> list[dict]:
    ev = pack["event"]
    fid, lvl, lab = f["id"], f["level"], f["short"]
    up = f["att"] > 0
    out = []
    be = _be(lab)
    if lvl == "L3":
        verb = "raise" if up else "lower"
        out.append(_S(f"Under the stated assumptions, {lab} {be} estimated to {verb} the chance of {article(ev['name'])} "
                      f"{ev['name']} later in the call by {{{fid}.att_abs}} ({{{fid}.ci}}) at the moments where "
                      f"{'they' if _plural(lab) else 'it'} happened [{fid}].", "factor", [fid], core=True))
        if detail == "full":
            more = "extra" if up else "fewer"
            out.append(_S(f"Under the same assumptions, that is about {{{fid}.attributable}} {more} {ev['plural']} among the "
                          f"held-out calls ({{{fid}.attributable_ci}}) [{fid}].", "factor", [fid]))
    elif lvl == "L2":
        clear = f["ci"][0] > 0 or f["ci"][1] < 0
        if clear:
            rel = "higher" if up else "lower"
            out.append(_S(f"Warning sign: {lab} {be} associated with a {rel} chance of {article(ev['name'])} {ev['name']} "
                          f"later in the call ({{{fid}.att}}, {{{fid}.ci}}) [{fid}].", "factor", [fid], core=True))
        else:
            out.append(_S(f"No clear difference: for {lab} the estimate is compatible with no difference in the chance of "
                          f"{article(ev['name'])} {ev['name']} ({{{fid}.att}}, {{{fid}.ci}}) [{fid}].", "factor", [fid], core=True))
        reasons = []
        for c in sorted(f["failed_checks"], key=lambda c: REASON_ORDER.index(c) if c in REASON_ORDER else 99):
            if c == "preregistered" and pack.get("slice", {}).get("exploratory"):
                reasons.append("estimates for a single industry are exploratory (not pre-registered)")
            elif c == "sensitivity_stable" and not f.get("sensitivity_ran", True):
                reasons.append("the sensitivity analyses were not run (they run only for effects that survive the "
                               "multiplicity correction)")
            elif c in PLAIN_REASON:
                reasons.append(PLAIN_REASON[c])
        if reasons and clear:
            out.append(_S("Not a confirmed effect: " + "; ".join(reasons[:2 if detail == "brief" else 3]) + f" [{fid}].",
                          "factor", [fid]))
    else:
        why = f.get("no_estimate_reasons") or ["the checks for a reliable estimate did not pass"]
        out.append(_S(f"There is no reliable estimate for {lab} and {ev['plural']}: " + "; ".join(why[:2]) + f" [{fid}].",
                      "factor", [fid], core=detail == "full"))
        if lvl == "L1" and f.get("counts_available"):
            out.append(_S(f"Counts only: {lab} happened at {{{fid}.n_treated}} comparable moments in held-out calls, and "
                          f"{{{fid}.events_treated}} of those moments had {article(ev['name'])} {ev['name']} later in the call "
                          f"[{fid}].", "count", [fid], core=detail == "full"))
    if lvl not in ("L2", "L3"):
        if detail == "full" and lvl == "L1":
            for sp in f["spans"][:1]:
                out.append(_S(f"“{sp['quote']}” [{sp['turn_uid']}]", "quote", [fid], [sp["turn_uid"]], quote=sp["quote"]))
        return out
    if detail == "full" and f["co_occurring"]:
        names = ", ".join(BEHAVIOURS[b].short for b in f["co_occurring"][:3] if b in BEHAVIOURS)
        out.append(_S(f"{_cap(lab)} often {'happen' if _plural(lab) else 'happens'} in the same calls as {names}; their "
                      f"estimated effects are not independent and do not add up [{fid}].", "caveat", [fid]))
    if detail == "full" and f["counter_available"]:
        out.append(_S(f"{_cap(lab)} also happened in {{{fid}.calls_without_event}} of {{{fid}.calls_with}} held-out calls "
                      f"where no {ev['name']} followed [{fid}].", "counter", [fid]))
    spans = f["spans"][:2 if detail == "full" else 1]
    for sp in spans:
        out.append(_S(f"“{sp['quote']}” [{sp['turn_uid']}]", "quote", [fid], [sp["turn_uid"]], quote=sp["quote"]))
    if detail == "full" and f["faithfulness_ok"] and spans:
        out.append(_S(f"In the risk forecaster, removing such a turn moves the forecast more than removing "
                      f"{{{fid}.faith_pct}} of the same speaker's other turns (a check of the model, not proof of "
                      f"what happened) [{fid}].", "faithfulness", [fid]))
    return out


def caveat_sentences(pack: dict, written: list | None = None) -> list[dict]:
    ev = pack["event"]
    out = []
    shown = [f for f in (pack["factors"] if written is None else written) if f["level"] in ("L2", "L3")]
    if any(f["level"] == "L3" for f in shown):
        ids = [f["id"] for f in shown if f["level"] == "L3"]
        ev_txt = ", ".join(f"{{{i}.e_value}}" for i in ids[:3])
        out.append(_S(f"Assumptions: the conversation before each moment contains every common influence on both the "
                      f"behaviour and the {ev['name']}; single moments are compared, not whole-call policies. A hidden "
                      f"factor would need a risk ratio of at least {ev_txt} with both to explain the estimates away "
                      f"(E-values).", "caveat", ids))
    if not pack.get("nc_clean", True) and shown:
        if pack.get("nc_estimable", 1):
            out.append(_S(f"A check for hidden bias (negative controls) flagged {ev['plural']}, so no finding for this event "
                          f"is shown as more than a warning sign.", "caveat"))
        else:
            out.append(_S(f"The check for hidden bias (negative controls) could not be run for {ev['plural']} because the "
                          f"control behaviours were too rare, so no finding for this event is shown as more than a warning "
                          f"sign.", "caveat"))
    if len(shown) > 1:
        out.append(_S("These behaviours often occur together; their estimated effects are not independent and do not add up.", "caveat"))
    out.append(_S("All numbers describe this corpus of calls, not customers in general.", "caveat"))
    return out


def _join(items: list[str]) -> str:
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _ev_phrase(code: str) -> str:
    name = EVENTS[code].name
    return f"{article(name)} {name}"


def topic_sentences(pack: dict, core: bool = True) -> list[dict]:
    ev = pack["event"]
    tp = pack.get("topics") or {}
    out = []
    if tp.get("note"):
        out.append(_S(tp["note"], "notice"))
    if not tp.get("terms"):
        if (tp.get("note") or "").startswith("Topic statistics"):
            return out
        out.append(_S(f"No product, service or problem words stand out at the start of {tp.get('label', 'calls')} that "
                      f"later had {article(ev['name'])} {ev['name']} (too few calls, or no clear difference from other "
                      f"calls).", "topics", core=core))
        return out
    parts = [f"'{k['term']}' ({{K{i + 1}.share}} of those calls, {{K{i + 1}.share_other}} of calls without one)"
             for i, k in enumerate(tp["terms"])]
    out.append(_S(f"At the start of {tp.get('label', 'calls')} that later had {article(ev['name'])} {ev['name']}, "
                  f"customers use these words more than in calls without one: " + "; ".join(parts) + ".", "topics",
                  core=core))
    for q in tp.get("quotes", [])[:2]:
        out.append(_S(f"“{q['quote']}” [{q['turn_uid']}]", "quote", [], [q["turn_uid"]], quote=q["quote"]))
    out.append(_S(f"These are word counts from what customers say before the {ev['name']} starts, not estimated "
                  f"effects. To see which agent behaviours matter for {ev['plural']}, ask 'why do {ev['plural']} "
                  f"happen?'", "caveat"))
    return out


COND_FIRST = {"RISK": "the first sign of risk", "REF_DENIED": "the refusal", "REF_GRANTED": "the refund", "HANDOFF": "the supervisor joining",
              "CANCEL_DONE": "the completed cancellation", "ESC": "the escalation", "REF": "the refund episode",
              "CHURN": "the churn threat"}


EVENT_VERB = {"ESC": "escalate", "REF": "ask for refunds", "CHURN": "threaten to cancel"}
CALL_ASK = {"ESC": "why did it escalate?", "REF": "why did the customer ask for a refund?",
            "CHURN": "why did the customer threaten to cancel?"}
IN_CALL = {"ESC": "an escalation", "REF": "a refund episode", "CHURN": "a churn threat", "RISK": "a retention risk",
           "HANDOFF": "a supervisor joining", "REF_GRANTED": "a refund being granted", "REF_DENIED": "a refund being refused",
           "CANCEL_DONE": "a completed cancellation"}


def call_sentences(pack: dict, spec: QuerySpec) -> list[dict]:
    c = pack["call"]
    if not c["found"]:
        if c["n_matches"] > 1:
            return [_S("Several calls have an id starting with '{CALL.asked}': {CALL.matches}. Which one do you mean?",
                       "clarify", core=True)]
        return [_S("No call with the id '{CALL.asked}' is in the data. The call id is the part before the colon in the "
                   "brackets after each quote.", "clarify", core=True)]
    st = c["story"]
    where = f"{article(c['industry'])} {c['industry']} call" + (" to {CALL.brand}" if c["brand"] else "")
    when = " from {CALL.when}" if c["dated"] else ""
    out = [_S(f"Call {{CALL.id}} is {where}{when}, with {{CALL.turns}} turns.", "count", core=True)]
    evs = c["events"]
    if evs:
        parts = [f"{IN_CALL.get(x['code'], EVENTS[x['code']].name)} at turn {{CE{j + 1}.turn}}" for j, x in enumerate(evs)]
        out.append(_S("Business events detected in this call, in order: " + "; ".join(parts) + ".", "count", core=True))
    else:
        out.append(_S("None of the business events (escalations, refund episodes, churn threats, retention risks) was "
                      "detected in this call.", "count", core=True))
    target, o = c["target"], c["onset"]
    ev = pack.get("event")
    if ev and o < 0:
        out.append(_S(f"No {ev['name']} was detected in this call, so there is no {ev['name']} to explain. The event "
                      f"labeller can miss events (its presence F1 on the gold set: {{D.f1}}); the turns are quoted below so "
                      f"you can check.", "short", core=True))
    f = st.get("focus")
    if spec.behaviour:
        did = DONE.get(spec.behaviour, BEHAVIOURS[spec.behaviour].label)
        if f:
            rel = "" if not ev or o < 0 else (f", before the {ev['name']}" if f["before_event"] else f", after the {ev['name']} "
                                                                                                    f"had started")
            out.append(_S(f"Yes: {did} at turn {{CALL.focus_turn}}{rel}: “{f['shown']}” [{f['turn_uid']}]", "quote", [],
                          [f["turn_uid"]], quote=f["quote"]))
        else:
            out.append(_S(f"No moment where {did} was detected in this call.", "short", core=True))
    moments = st.get("moments") or []
    if st.get("problem"):
        p = st["problem"]
        same = [m["text"] for m in moments if m["turn"] == p["turn"]]
        tag = f"; {_join(same)}" if same else ""
        out.append(_S(f"The customer's problem (turn {{CALL.problem_turn}}{tag}): “{p['shown']}” [{p['turn_uid']}]", "quote",
                      [], [p["turn_uid"]], quote=p["quote"]))
        moments = [m for m in moments if m["turn"] != p["turn"]]
    if moments:
        lead = (f"Step by step, in the {{CALL.window}} turns before the {ev['name']}" if ev and o >= 0 else
                "What happened in this call")
        idx = {id(m): j for j, m in enumerate(st.get("moments") or [])}
        for n, m in enumerate(moments):
            pre = f"{lead}: turn" if n == 0 else "Turn"
            out.append(_S(f"{pre} {{CM{idx[id(m)] + 1}.turn}}, {m['text']}: “{m['shown']}” [{m['turn_uid']}]", "quote", [],
                          [m["turn_uid"]], quote=m["quote"]))
    elif ev and o >= 0 and not st.get("moments"):
        out.append(_S(f"None of the measured behaviours happened in the {{CALL.window}} turns before the {ev['name']}.",
                      "rationale", core=True))
    if ev and o >= 0 and st.get("event"):
        x = st["event"]
        out.append(_S(f"Then the {ev['name']} (turn {{CALL.onset}}): “{x['shown']}” [{x['turn_uid']}]", "quote", [],
                      [x["turn_uid"]], quote=x["quote"]))
    if ev and o >= 0 and st.get("moments"):
        parts = [f"{m['text']} in {{CM{j + 1}.share_event}} of calls with one (against {{CM{j + 1}.share_other}} at the "
                 f"same point in calls without one)" for j, m in enumerate(st["moments"]) if m.get("share_event") is not None]
        if parts:
            out.append(_S(f"How common these moments are across all calls, in the {{CALL.window}} turns before "
                          f"{article(ev['name'])} {ev['name']}: " + "; ".join(parts) + ".", "rationale", core=True))
    for fx in pack.get("factors", []):
        out += factor_sentences(pack, fx, "brief")
    if ev and o >= 0:
        out.append(_S(f"This walks through one call from its own turns. The shares and estimates describe calls in general; "
                      f"they are not proof of why this particular call ended in {article(ev['name'])} {ev['name']}.",
                      "caveat"))
    others = [x["code"] for x in evs if x["code"] in EVENT_VERB and x["code"] != target]
    if not spec.event and others:
        out.append(_S(f"To walk through {_join([IN_CALL[x] for x in dict.fromkeys(others)][:2])} instead, ask for example "
                      f"'{CALL_ASK[others[0]]}'.", "hint"))
    return out


def condition_sentences(pack: dict) -> list[dict]:
    c = pack.get("condition")
    if not c:
        return []
    ev = pack["event"]
    conds = c.get("conds") or [c["cond"]]
    cl = cond_label(conds)
    if not c["n"]:
        return [_S(f"There are no {cl} in this slice, so this question cannot be answered from the data.", "count", core=True)]
    many = len(conds) > 1
    other = ("the other calls in the slice" if many else
             COND_OTHER.get(c["cond"], "calls without " + _ev_phrase(c["cond"])))
    out = [_S(f"This answer looks only at {cl} ({{W.calls}} calls).", "count", core=True),
           _S(f"In those calls, {{W.event_calls}} ({{W.rate}}) had {_ev_phrase(ev['code'])}, against {{W.other_rate}} of "
              f"{other} and {{W.all_rate}} of all calls in the slice.", "count", core=True)]
    if c["k"] and many:
        out.append(_S(f"In the calls with all of these, the {ev['name']} came after the last of them in {{W.cond_first}}, "
                      f"before it in {{W.event_first}}, and in the same turn in {{W.same}}.", "count"))
    elif c["k"]:
        out.append(_S(f"In the calls with both, {COND_FIRST.get(c['cond'], 'the first event')} came first in {{W.cond_first}}, "
                      f"the {ev['name']} came first in {{W.event_first}}, and both started in the same turn in {{W.same}}.",
                      "count"))
    return out


def change_sentences(pack: dict) -> list[dict]:
    ch = pack.get("change")
    if not ch:
        return []
    ev = pack["event"]
    if not ch["available"]:
        return [_S("The data has no usable call dates, so a before/after comparison cannot be made.", "notice", core=True)]
    out = [_S("Calls in the data run from {CH.first} to {CH.last}: {CH.n_before} fall before {CH.date} and {CH.n_after} on "
              "or after it.", "count", core=True)]
    if ch.get("too_few"):
        if not ch.get("n_before") or not ch.get("n_after"):
            out.append(_S("That date is outside the calls in the data, so there is nothing to compare; give a date between "
                          "{CH.first} and {CH.last}.", "count", core=True))
        else:
            out.append(_S("One of the two periods has fewer than {CH.min_calls} calls, so their rates cannot be compared "
                          "reliably.", "count", core=True))
        return out
    out.append(_S(f"{_cap(_ev_phrase(ev['code']))} happened in {{CH.rate_before}} of calls before {{CH.date}} and in "
                  f"{{CH.rate_after}} of calls from {{CH.date}} on: a difference of {{CH.diff}} ({{CH.ci}}).", "count",
                  core=True))
    if ch["clear"]:
        out.append(_S("The interval excludes zero, so the two periods do differ.", "count"))
    else:
        out.append(_S("The interval includes zero, so the data cannot tell the two periods apart.", "count", core=True))
    its = ch.get("its") or {}
    if its.get("available"):
        out.append(_S("Interrupted time series ({CH.unit} periods: {CH.its_pre} before {CH.date} and {CH.its_post} from it): "
                      "before the date the share was moving by {CH.pre_slope} per {CH.unit}; at the date its level shifted "
                      "by {CH.level} ({CH.level_ci}) and its trend changed by {CH.slope} per {CH.unit} ({CH.slope_ci}).",
                      "count", core=True))
        if its.get("season"):
            out.append(_S(f"The model allows for the usual {its['season']} pattern, and its intervals use Newey–West "
                          f"standard errors (never narrower than the classical ones; lag-one residual autocorrelation "
                          f"{{CH.rho1}}).", "count"))
        else:
            out.append(_S("Its intervals use Newey–West standard errors (never narrower than the classical ones; lag-one "
                          "residual autocorrelation {CH.rho1}).", "count"))
        if its.get("placebo_levels"):
            excl = its["level_ci"][0] > 0 or its["level_ci"][1] < 0
            tail = (", so the shift at the real date stands out from the series' usual movement." if excl and
                    not its["placebo_large"] else ", so the shift at the real date is within the series' usual movement."
                    if its["placebo_large"] else ".")
            out.append(_S("Placebo check: at {CH.n_placebo} made-up dates before {CH.date}, {CH.n_placebo_large} level "
                          "shifts were at least as large as the real one" + tail, "count"))
        if its.get("control"):
            out.append(_S("Comparison series ({CH.ctrl_label}): at the same date its level shifted by {CH.ctrl_level} "
                          "({CH.ctrl_level_ci}); the difference between the two shifts is {CH.did} ({CH.did_ci}).",
                          "count"))
    else:
        out.append(_S("There are too few time periods with enough calls on each side of the date for an interrupted "
                      "time series, so only the simple comparison is shown.", "notice"))
    if ch.get("mix_shift", 0) > 0.1:
        out.append(_S("The mix of industries also changed between the two periods, and that alone moves the overall "
                      "share.", "caveat"))
    out += rationale_sentences(ev, ch.get("rationale_after"), "brief", core=False)
    out += rationale_sentences(ev, ch.get("rationale_before"), "brief", core=False)
    if ch.get("what"):
        out.append(_S("Read with care: these comparisons tie a change to the date, not to {CH.what}; anything else that "
                      "changed around {CH.date} (the season, the mix of calls, staffing) would show up the same way.",
                      "caveat"))
    else:
        out.append(_S("Read with care: these comparisons tie a change to the date only; anything that changed around "
                      "{CH.date} (the season, the mix of calls, staffing) would show up the same way.", "caveat"))
    return out


def threshold_sentences(pack: dict) -> list[dict]:
    th = pack.get("threshold")
    if th is None:
        return []
    ev = pack["event"]
    what = "beyond" if th["op"] == "gt" else "within"
    chance = f"the chance of {_ev_phrase(ev['code'])} later in the call"
    if not th["n_estimable"]:
        return [_S(f"No behaviour has a usable estimate for {ev['plural']} here, so the threshold cannot be checked.",
                   "factor", core=True)]
    rows = th["rows"]
    out = []
    if th["op"] == "null":
        if not rows:
            return [_S(f"Every behaviour with a usable estimate shows a clear difference in {chance}: none of their "
                       f"intervals includes zero.", "factor", core=True)]
        parts = [f"{f['short']} ({{{f['id']}.att}}, {{{f['id']}.ci}}) [{f['id']}]" for f in rows]
        return [_S(f"Behaviours with no clear difference in {chance} (the interval includes zero): " + "; ".join(parts) + ".",
                   "factor", [f["id"] for f in rows], core=True),
                _S("The wider an interval, the larger the effect the data cannot rule out, so these are not shown to have "
                   "no effect.", "caveat")]
    if rows:
        parts = [f"{f['short']} ({{{f['id']}.att}}, {{{f['id']}.ci}}) [{f['id']}]" for f in rows]
        out.append(_S(f"Behaviours whose estimated difference in {chance} is {what} {{TH.value}}: " + "; ".join(parts) + ".",
                      "factor", [f["id"] for f in rows], core=True))
        clear = [f for f in rows if f["id"] in th["clear"]]
        if th["op"] == "gt" and clear:
            tail = "; for the others the interval reaches below the threshold." if len(clear) < len(rows) else "."
            out.append(_S("For " + _join([f"{f['short']} [{f['id']}]" for f in clear]) + ", the whole confidence interval "
                          "is beyond {TH.value}" + tail, "factor", [f["id"] for f in clear]))
        elif th["op"] == "gt":
            out.append(_S("For none of them is the whole confidence interval beyond {TH.value}, so the data cannot confirm "
                          "that any behaviour crosses the threshold.", "factor", core=True))
    else:
        f = th.get("nearest")
        near = f"; the nearest is {f['short']} ({{{f['id']}.att}}, {{{f['id']}.ci}}) [{f['id']}]." if f else "."
        out.append(_S(f"No behaviour's estimated difference in {chance} is {what} {{TH.value}}" + near, "factor",
                      [f["id"]] if f else [], core=True))
    return out


def proxy_sentences(pack: dict) -> list[dict]:
    px = pack.get("proxy")
    if not px or not px.get("available"):
        return []
    ev = pack["event"]
    if not px["n"]:
        return [_S(f"No customer mentions a membership, a loyalty status or a long tenure before the point where "
                   f"{ev['plural']} start, so there is no proxy for customer tier in these calls either.", "count", core=True)]
    out = [_S(f"Nearest proxy: in {{P.calls}} calls the customer says they are a member, have a loyalty status or are a "
              f"long-time customer before the point where {ev['plural']} start; {{P.rate}} of these calls had "
              f"{_ev_phrase(ev['code'])}, against {{P.rate_other}} of the other {{P.other_calls}} calls.", "count", core=True)]
    if px["groups"]:
        parts = [f"{g['word']} {{P{i + 1}.rate}} ({{P{i + 1}.calls}} calls)" for i, g in enumerate(px["groups"])]
        out.append(_S("By the status customers name, from the highest share to the lowest: " + "; ".join(parts) + ".", "count",
                      core=True))
    if px.get("quote"):
        q = px["quote"]
        out.append(_S(f"For example: “{q['quote']}” [{q['turn_uid']}]", "quote", [], [q["turn_uid"]], quote=q["quote"]))
    out.append(_S("This proxy only counts customers who mention their status; it is not a customer-tier field, and these "
                  "are counts, not effects.", "caveat"))
    return out


def behaviour_profile_sentences(pack: dict) -> list[dict]:
    bp = pack["behaviour_profile"]
    b = BEHAVIOURS[bp["behaviour"]]
    short = b.short
    if bp["negative_control"]:
        return [_S(f"{_cap(short)} {_be(short)} a negative control: {'they are' if _plural(short) else 'it is'} measured only "
                   f"to check the method for hidden bias, so {'they are' if _plural(short) else 'it is'} not profiled.",
                   "notice", core=True)]
    if not bp["available"]:
        return [_S("Turn-level behaviour data is not available in this workspace, so this behaviour cannot be profiled.",
                   "notice", core=True)]
    did = DONE.get(bp["behaviour"], b.label)
    out = [_S(f"In {bp['label']}, {{B.with}} of {{B.calls}} calls ({{B.rate}}) had at least one moment where {did}.", "count",
              core=True)]
    r = bp.get("rationale") or {}
    prec = r.get("precursors") or []
    first = f"the first time {did}"
    if r.get("too_few"):
        out.append(_S(f"There are too few such calls to describe what usually comes before {first}.", "rationale"))
    elif prec:
        parts = [f"{x['text']} in {{QBP{i + 1}.share_event}} of these calls (against {{QBP{i + 1}.share_other}} at the same "
                 f"point in calls without it)" for i, x in enumerate(prec)]
        out.append(_S(f"Why, from the conversations: in the {{QB.window}} turns before {first}, " + "; ".join(parts) + ".",
                      "rationale", core=True))
    else:
        out.append(_S(f"Why, from the conversations: no other behaviour stands out in the turns before {first}, compared "
                      f"with the same point in calls without it.", "rationale", core=True))
    for q in (r.get("reasons") or [])[:2]:
        out.append(_S(f"In the customer's own words: “{q['shown']}” [{q['turn_uid']}]", "quote", [], [q["turn_uid"]],
                      quote=q["quote"]))
    chain = r.get("chain") or []
    if len(chain) >= 2:
        before_text = prec[0]["text"] if prec else None
        for j, st in enumerate(chain):
            lead = "One call, step by step: " if j == 0 else ""
            what = ("the customer's problem" if st["role"] == "problem" else f"then {before_text}" if st["role"] == "before"
                    else f"then {did}")
            out.append(_S(f"{lead}{what if lead else _cap(what)}: “{st['shown']}” [{st['turn_uid']}]", "quote", [],
                          [st["turn_uid"]], quote=st["quote"]))
    parts = [f"{_ev_phrase(e)} in {{B{i + 1}.with}} of calls with {short} and in {{B{i + 1}.without}} of calls without "
             f"{'them' if _plural(short) else 'it'}" for i, e in enumerate(bp["events"])]
    out.append(_S("How this relates to the business events: " + "; ".join(parts) + ".", "count", core=True))
    out.append(_S("These are counts and patterns, not effects. To test one event, ask a follow-up such as 'what about "
                  "escalations?'", "caveat"))
    return out


def overview_sentences(pack: dict) -> list[dict]:
    ov = pack["overview"]
    names = {"ESC": "escalations", "REF": "refund episodes", "CHURN": "churn threats", "RISK": "retention risks"}
    parts = [f"{names[e]} in {{O{i + 1}.rate}} ({{O{i + 1}.k}} calls)" for i, e in enumerate(ov["events"])]
    out = [_S(f"In {ov['label']} ({{O.calls}} calls): " + "; ".join(parts) + ".", "count", core=True)]
    if ov["industries"]:
        out.append(_S("The largest industries: " + "; ".join(f"{lab} calls {{OI{j + 1}.share}}"
                                                          for j, lab in enumerate(ov["industries"])) + ".", "count"))
    if ov["behaviours"]:
        out.append(_S("The most common moments: " + "; ".join(f"{DONE.get(b, BEHAVIOURS[b].label)} in {{OB{j + 1}.share}} of "
                                                              f"calls" for j, b in enumerate(ov["behaviours"])) + ".",
                      "count"))
    for tp in ov["topics"]:
        words = _join([f"“{w}”" for w in tp["terms"]])
        out.append(_S(f"Calls that later had {_ev_phrase(tp['event'])} more often open with {words}.", "topics"))
    out.append(_S("To see what lies behind any of these, ask for example “Why do customers escalate?”, “What drives refunds "
                  "in hotel calls?” or “What should agents stop doing?”", "hint"))
    return out


HELP_TEXT = [
    "I answer questions about escalations, refund episodes, churn threats and retention risks in these calls, and about "
    "what agents and customers did before them.",
    "Examples: “Why do customers escalate?”, “How often do customers ask for refunds in hotel calls?”, “Is customer "
    "frustration linked to churn threats?”, “Why do customers who were refused a refund escalate?”, “Did escalations change "
    "after the new policy?”, “Which industry has the most refunds?”, “Why do customers get frustrated?”",
    "Follow-ups keep the context: “what about refunds?”, “only airline calls”, “explain the first factor”, “compare with "
    "churn threats”.",
    "Questions can be in English, Spanish, French, German, Portuguese, Italian or Hindi, and spelling mistakes are corrected; "
    "every answer says how the question was read.",
]


def link_chain_sentences(pack: dict) -> list[dict]:
    lk = pack.get("link") or {}
    chain = lk.get("chain") or []
    if len(chain) < 2:
        return []
    out = []
    for j, st in enumerate(chain):
        lead = "One call with both, step by step: " if j == 0 else ""
        what = "the customer's problem" if st["role"] == "problem" else f"the {EVENTS[st['role']].name}"
        what = what if lead else "then " + what
        out.append(_S(f"{lead}{what if lead else _cap(what)}: “{st['shown']}” [{st['turn_uid']}]", "quote", [],
                      [st["turn_uid"]], quote=st["quote"]))
    return out


def rationale_sentences(ev: dict, r: dict | None, mode: str = "full", core: bool = True, quotes: bool = False) -> list[dict]:
    if not r or not r.get("available"):
        return []
    p, lab = r["prefix"], r["label"]
    out = []
    if r.get("too_few"):
        if mode == "full":
            out.append(_S(f"Why: there are too few {ev['plural']} in {lab} ({{{p}.event_calls}} calls) to describe a typical "
                          f"pattern from the conversations.", "rationale", core=core))
        return out
    terms = [f"“{t['term']}”" for t in (r.get("topics") or {}).get("terms", [])[:3]]
    prec = r.get("precursors") or []
    lead = _join([with_frequency(x["text"], x["share_event"]) for x in prec[:2]])
    opening = f"calls that open with {_join(terms).replace(' and ', ' or ')}" if terms else ""
    neg = (r.get("contrast") or [])[:1]
    missing = (f"{neg[0]['text']} in only {{{p}N1.share_event}} of them (against {{{p}N1.share_other}} at the same point "
               f"in other calls)") if neg else ""
    if opening and lead:
        short = (f"Why, from the conversations: in {lab}, {ev['plural']} come up more in {opening}, and in the turns just "
                 f"before the {ev['name']} {lead}" + (f", while {missing}." if missing else "."))
    elif lead:
        short = (f"Why, from the conversations: in {lab}, in the turns just before the {ev['name']} {lead}"
                 + (f", while {missing}." if missing else "."))
    elif opening and missing:
        short = (f"Why, from the conversations: in {lab}, {ev['plural']} come up more in {opening}, and before the "
                 f"{ev['name']} {missing}.")
    elif missing:
        short = f"Why, from the conversations: in {lab}, before the {ev['name']} {missing}."
    elif opening:
        short = (f"Why, from the conversations: in {lab}, {ev['plural']} come up more in {opening}; no single agent or "
                 f"customer behaviour in the turns before the {ev['name']} stands out against calls without one.")
    else:
        short = (f"Why, from the conversations: in {lab}, no opening problem words or behaviours before the {ev['name']} "
                 f"stand out against calls without one; the {ev['plural']} look spread across many situations.")
    out.append(_S(short, "rationale", core=core))
    if mode == "brief":
        if prec:
            x = prec[0]
            out.append(_S(f"In the {{{p}.window}} turns before the {ev['name']}, {x['text']} in {{{p}P1.share_event}} of these "
                          f"calls, against {{{p}P1.share_other}} at the same point in calls without one.", "rationale"))
        if quotes:
            for q in (r.get("reasons") or [])[:2]:
                out.append(_S(f"In the customer's own words: “{q['shown']}” [{q['turn_uid']}]", "quote", [], [q["turn_uid"]],
                              quote=q["quote"]))
        return out
    if terms:
        parts = [f"{t} ({{{p}K{i + 1}.share}} vs {{{p}K{i + 1}.share_other}})"
                 for i, t in enumerate(terms)]
        out.append(_S("The situation: words customers use at the start of the call, before anything the agent does, with "
                      "the share of these calls and of other calls that contain them: "
                      + "; ".join(parts) + ".", "rationale"))
    if prec:
        parts = [f"{x['text']} in {{{p}P{i + 1}.share_event}} of these calls (against {{{p}P{i + 1}.share_other}} at the same "
                 f"point in calls without one)" for i, x in enumerate(prec)]
        out.append(_S(f"What happened in the {{{p}.window}} turns before the {ev['name']}: " + "; ".join(parts) + ".", "rationale"))
    for i, c in enumerate(r.get("common") or [], 1):
        short_b = BEHAVIOURS[c["behaviour"]].short
        pl = _plural(short_b)
        out.append(_S(f"{_cap(short_b)} {'were' if pl else 'was'} common before the {ev['name']} too "
                      f"({{{p}C{i}.share_event}}), but about as common at the same point in calls without one "
                      f"({{{p}C{i}.share_other}}), so on {'their' if pl else 'its'} own {'they do' if pl else 'it does'} "
                      f"not set these calls apart.", "rationale"))
    if r.get("who"):
        out.append(_S(f"{{{p}.who_share}} of these {ev['plural']} start with {r['who']['text']}.", "rationale"))
    for q in (r.get("reasons") or [])[:2]:
        out.append(_S(f"In the customer's own words: “{q['shown']}” [{q['turn_uid']}]", "quote", [], [q["turn_uid"]],
                      quote=q["quote"]))
    out += chain_sentences(ev, r.get("chain") or [], prec[0]["text"] if prec else None)
    out.append(_S("How strong this is: these are patterns in the transcripts, checked against the same point in calls "
                  "without the event; the causal test on held-out calls is reported next.", "rationale"))
    return out


def chain_sentences(ev: dict, chain: list, before_text: str | None) -> list[dict]:
    out = []
    if len(chain) < 2:
        return out
    for j, st in enumerate(chain):
        lead = "One call, step by step: " if j == 0 else ""
        if st["role"] == "problem":
            what = "the customer's problem"
        elif st["role"] == "before":
            what = f"then {before_text}" if before_text else "then"
        else:
            what = f"then the {ev['name']}"
        out.append(_S(f"{lead}{_cap(what) if not lead else what}: “{st['shown']}” [{st['turn_uid']}]", "quote", [],
                      [st["turn_uid"]], quote=st["quote"]))
    return out


def rank_sentences(pack: dict, spec: QuerySpec) -> list[dict]:
    ev, rk = pack["event"], pack["rank"]
    out = []
    if not rk["groups"]:
        out.append(_S("No group has at least {R.min_calls} calls, so no ranking can be shown.", "rank", core=True))
        return out + caveat_sentences(pack)[-1:]
    if rk["dimension"] == "event":
        parts = [f"{g['label']} {{R{i + 1}.rate}} ({{R{i + 1}.event_calls}} of {{R{i + 1}.calls}} calls)"
                 for i, g in enumerate(rk["groups"])]
        out.append(_S(f"Share of {slice_label(spec.filters)} with each event, from most to least common: "
                      + "; ".join(parts) + ".", "rank", core=True))
    else:
        parts = [f"{g['label']} {{R{i + 1}.rate}} ({{R{i + 1}.event_calls}} of {{R{i + 1}.calls}})"
                 for i, g in enumerate(rk["groups"])]
        out.append(_S(f"Ranked by the share of calls with {article(ev['name'])} {ev['name']}: " + "; ".join(parts) + ".",
                      "rank", core=True))
    if rk.get("threshold") is not None:
        side = "above" if rk["threshold"]["op"] == "gt" else "below"
        labs = rk["threshold"]["labels"]
        out.append(_S(f"Groups with a share {side} {{TH.rate}}: " + (_join(labs) if labs else "none") + ".", "rank", core=True))
    if rk["n_small"]:
        out.append(_S("Groups with fewer than {R.min_calls} calls are left out ({R.n_small} of them).", "notice"))
    out.append(_S("These are counts; differences between groups of calls are not effects of anything in the calls.", "caveat"))
    top = rk["groups"][0]
    if pack.get("then"):
        sub = pack["then"]
        what = sub["pack"]["event"]["plural"] if rk["dimension"] == "event" else f"{ev['plural']} in {top['label']}"
        out.append(_S(f"Next step, the top group: here is what the data shows for {what}.", "short"))
        out += _write_answer(sub["pack"], QuerySpec.from_dict(sub["spec"]))
        return out
    if rk.get("rationale"):
        out += rationale_sentences(rk["rationale_event"], rk["rationale"], "brief", core=False)
    if rk["dimension"] == "industry":
        out.append(_S(f"For the full reasoning and the causal test for {ev['plural']} in {top['label']}, ask a follow-up "
                      f"such as 'why in {top['label']}?'", "hint"))
    return out + caveat_sentences(pack)[-1:]


def shared_sentences(pack: dict, spec: QuerySpec) -> list[dict]:
    sh = pack["shared"]
    evs = sh["events"]
    names = _join([EVENTS[e].plural for e in evs])
    out = [_S(f"In {slice_label(spec.filters)}: " + "; ".join(f"{EVENTS[e].plural} in {{E{i + 1}.rate}} of calls"
                                                             for i, e in enumerate(evs)) + ".", "count", core=True)]
    if sh.get("fallback"):
        out.append(_S(f"For {pack['slice']['label']} alone some of these events have no usable estimates, so the "
                      f"behaviours below are for all calls.", "notice"))
    rows = sh["rows"]

    def chance(c):
        rel = "higher" if c["att"] > 0 else "lower"
        return f"a {rel} chance of {_ev_phrase(c['event'])} ({{{c['id']}.att}}, {{{c['id']}.ci}}) [{c['id']}]"

    if sh.get("focus"):
        for r in rows:
            for c in r["cells"]:
                if c is None:
                    continue
                lab, pl = r["short"], EVENTS[c["event"]].plural
                if c["flagged"]:
                    extra = " It passed every causal check for this event." if c["level"] == "L3" else ""
                    out.append(_S(f"For {pl}: {lab} {_be(lab)} associated with {chance(c)}.{extra}", "shared", [c["id"]],
                                  core=True))
                elif c["estimable"]:
                    out.append(_S(f"For {pl}: no clear difference for {lab} ({{{c['id']}.ci}}) [{c['id']}].", "shared",
                                  [c["id"]], core=True))
                else:
                    out.append(_S(f"For {pl}: there is no reliable estimate for {lab} [{c['id']}].", "shared", [c["id"]],
                                  core=True))
        if not any(c for r in rows for c in r["cells"]):
            out.append(_S("This behaviour has no estimates for these events.", "notice", core=True))
    else:
        flagged_all = [r for r in rows if all(c and c["flagged"] for c in r["cells"])]
        same = [r for r in flagged_all if len({c["att"] > 0 for c in r["cells"]}) == 1]
        mixed = [r for r in flagged_all if r not in same]
        for r in same:
            ids = [c["id"] for c in r["cells"]]
            rel = "higher" if r["cells"][0]["att"] > 0 else "lower"
            parts = [f"of {_ev_phrase(c['event'])} ({{{c['id']}.att}}, {{{c['id']}.ci}}) [{c['id']}]" for c in r["cells"]]
            out.append(_S(f"Warning sign for {names}: {r['short']} {_be(r['short'])} associated with a {rel} chance "
                          + _join(parts) + ".", "shared", ids, core=True))
        for r in mixed:
            out.append(_S(f"Mixed: {r['short']} {_be(r['short'])} associated with " + _join([chance(c) for c in r["cells"]])
                          + ".", "shared", [c["id"] for c in r["cells"]], core=True))
        if not flagged_all:
            out.append(_S(f"No behaviour is a warning sign for {names} alike in {pack['slice']['label']}.", "shared",
                          core=True))
        for i, e in enumerate(evs):
            only = [r for r in rows if r not in flagged_all and r["cells"][i] and r["cells"][i]["flagged"]]
            if only:
                out.append(_S(f"Warning signs for {EVENTS[e].plural} only: " +
                              ", ".join(f"{r['short']} [{r['cells'][i]['id']}]" for r in only) + ".", "shared",
                              [r["cells"][i]["id"] for r in only], core=not flagged_all))
        l3 = [(r, c) for r in rows for c in r["cells"] if c and c["flagged"] and c["level"] == "L3"]
        if l3:
            out.append(_S("Of these, the following passed every causal check for their event: " +
                          ", ".join(f"{r['short']} for {EVENTS[c['event']].plural} [{c['id']}]" for r, c in l3) + ".",
                          "shared", [c["id"] for _, c in l3]))
        if sh.get("asked") == "what_to_change":
            acts = [(r, c) for r, c in l3 if r["actionable"]]
            for r, c in acts:
                more = c["att"] < 0
                out.append(_S(f"What could change: at comparable moments, {'doing more' if more else 'doing less'} of "
                              f"{r['short']} is estimated to lower the chance of {_ev_phrase(c['event'])} by up to "
                              f"{{{c['id']}.att_abs}}, under the stated assumptions [{c['id']}].", "action", [c["id"]],
                              core=True))
            if not acts:
                out.append(_S("No behaviour passed every causal check for these events, so the data does not support a "
                              "recommendation; the warning signs above can guide what to review.", "action", core=True))
    for x in sh.get("rationales") or []:
        ce = EVENTS[x["event"]]
        out += rationale_sentences({"code": x["event"], "name": ce.name, "plural": ce.plural}, x["data"], "brief", core=False)
    out.append(_S("Each event was analysed separately; a behaviour flagged for several events is not shown to connect "
                  "the events to each other. Ask about one event for its full answer with quotes.", "caveat"))
    return out + caveat_sentences(pack)[-1:]


def link_sentences(pack: dict, spec: QuerySpec) -> list[dict]:
    lk = pack["link"]
    a, b = EVENTS[lk["a"]], EVENTS[lk["b"]]
    out = [_S(f"In {slice_label(spec.filters)}, {{L.a_calls}} of {{L.calls}} calls had {article(a.name)} {a.name}, "
              f"{{L.b_calls}} had {article(b.name)} {b.name} and {{L.both}} had both.", "link", core=True)]
    if lk["both"]:
        out.append(_S(f"When both happened, the {a.name} started first in {{L.a_first}} calls, the {b.name} started first "
                      f"in {{L.b_first}}, and both started in the same turn in {{L.same}}.", "link", core=True))
    if lk["a_calls"]:
        out.append(_S(f"{_cap(article(b.name))} {b.name} occurred in {{L.b_given_a}} of calls with {article(a.name)} "
                      f"{a.name} and in {{L.b_given_not_a}} of calls without one.", "link"))
    if lk.get("rationale"):
        out += rationale_sentences({"code": lk["b"], "name": b.name, "plural": b.plural}, lk["rationale"], "brief", core=False,
                                   quotes=True)
    out += link_chain_sentences(pack)
    out.append(_S("These counts show how often the two events occur together and in which order, not whether one event "
                  "makes the other more likely.", "caveat"))
    return out + caveat_sentences(pack)[-1:]


def write_answer(pack: dict, spec: QuerySpec) -> list[dict]:
    seen, out = set(), []
    for x in _write_answer(pack, spec):
        if x["kind"] == "quote" and x.get("turn_uids") and x["turn_uids"][0] in seen:
            continue
        if x["kind"] == "quote":
            seen.update(x.get("turn_uids") or [])
        out.append(x)
    return out


COUNT_ONLY_TYPES = ("how_often", "examples", "trend", "compare", "issues", "event_link")


RATIONALE_FIRST_TYPES = ("why", "what_to_change", "effect_of")


def _write_answer(pack: dict, spec: QuerySpec) -> list[dict]:
    S: list[dict] = []
    S += [_S(n["text"], "notice") for n in pack["notices"]
          if not (n.get("kind") == "slice" and spec.question_type in COUNT_ONLY_TYPES + RATIONALE_FIRST_TYPES)]
    later_notices = [_S(n["text"], "notice") for n in pack["notices"]
                     if n.get("kind") == "slice" and spec.question_type in RATIONALE_FIRST_TYPES]
    if pack.get("clarify"):
        S.append(_S(pack["clarify"], "clarify", core=True))
        return S
    if pack.get("call"):
        return S + call_sentences(pack, spec)
    if "event" not in pack:
        if pack.get("behaviour_profile"):
            return S + behaviour_profile_sentences(pack) + [_S("All numbers describe this corpus of calls, not customers in "
                                                               "general.", "caveat")]
        if pack.get("overview"):
            return S + overview_sentences(pack) + [_S("All numbers describe this corpus of calls, not customers in general.",
                                                      "caveat")]
        if pack.get("help"):
            return S + [_S(t, "short", core=True) for t in HELP_TEXT]
        S.append(_S("Which business event do you mean: escalations, refunds or churn threats?", "clarify", core=True))
        return S
    ev = pack["event"]
    sl = pack["slice"]
    S += premise_sentences(pack)
    S += condition_sentences(pack)
    S += proxy_sentences(pack)
    if pack.get("rate_check") is not None:
        side = "above" if pack["rate_check"]["above"] else "not above"
        S.append(_S(f"In {slice_label(spec.filters)}, {{D.event_calls}} of {{D.calls}} calls ({{D.rate}}) had "
                    f"{article(ev['name'])} {ev['name']}: {side} the threshold in the question ({{TH.rate}}).", "count",
                    core=True))
    qt = spec.question_type
    cnt_sentence = _S(f"In {slice_label(spec.filters)}, {{D.event_calls}} of {{D.calls}} "
                      f"calls ({{D.rate}}) had {article(ev['name'])} {ev['name']} (event labeller presence F1 on the "
                      f"gold set: {{D.f1}}).", "count", core=qt in ("how_often",))
    if qt == "compare" and pack.get("rank") is not None:
        return S + rank_sentences(pack, spec)
    if qt == "shared" and pack.get("shared"):
        return S + shared_sentences(pack, spec)
    if qt == "event_link" and pack.get("link"):
        return S + link_sentences(pack, spec)
    if qt == "issues":
        S.append(cnt_sentence)
        S += topic_sentences(pack)
        S += rationale_sentences(ev, pack.get("rationale"), "brief", core=False, quotes=True)
        return S + caveat_sentences(pack)[-1:]
    if qt == "how_often":
        S.append(cnt_sentence)
        if "D.corrected_rate" in pack["placeholders"]:
            S.append(_S("Corrected for labeller errors with the blind gold sample, the held-out rate is {D.corrected_rate} "
                        "({D.corrected_ci}).", "count"))
        S.append(_S(f"{{D.opening_share}} of these {ev['plural']} started within the opening turns.", "count"))
        S += rationale_sentences(ev, pack.get("rationale"), "brief", core=False)
        S += caveat_sentences(pack)[-1:]
        return S
    if qt == "compare" and pack.get("compare"):
        parts = [f"{{C{i + 1}.rate}} of {c['label']} ({{C{i + 1}.event_calls}} of {{C{i + 1}.calls}})"
                 if pack["spec"]["compare"]["dimension"] == "industry" else
                 f"{{C{i + 1}.rate}} of calls had {article(EVENTS[c['event']].name)} {EVENTS[c['event']].name}"
                 for i, c in enumerate(pack["compare"])]
        S.append(_S("Share of calls with the event: " + "; ".join(parts) + ".", "count", core=True))
        for c in pack["compare"]:
            ce = EVENTS[c["event"]]
            S += rationale_sentences({"code": c["event"], "name": ce.name, "plural": ce.plural}, c.get("rationale"),
                                     "brief", core=False)
        S.append(_S("These are counts and patterns in the transcripts; differences between groups of calls are not effects "
                    "of anything in the calls.", "caveat"))
        S += caveat_sentences(pack)[-1:]
        return S
    if qt == "trend":
        if pack.get("change"):
            S += change_sentences(pack)
            return S + caveat_sentences(pack)[-1:]
        if pack.get("trend"):
            parts = [f"{{T{i + 1}.label}}: {{T{i + 1}.rate}}" for i in range(len(pack["trend"]))]
            S.append(_S(f"Weekly share of calls with {article(ev['name'])} {ev['name']}: " + "; ".join(parts) + ".", "count", core=True))
        else:
            S.append(_S("The data has no usable call dates, so a trend over time cannot be shown.", "notice", core=True))
        S += rationale_sentences(ev, pack.get("rationale"), "brief", core=False)
        S.append(_S("Week-to-week changes in these shares can come from the mix of calls in each week as well as from what "
                    "happens in the calls.", "caveat"))
        S += caveat_sentences(pack)[-1:]
        return S
    if qt == "examples":
        S.append(cnt_sentence)
        ex = pack.get("examples") or []
        if not ex:
            for f in pack["factors"]:
                ex += [dict(sp, factor=f["id"]) for sp in f["spans"]]
        seen = set()
        n = 0
        for sp in ex:
            if sp["transcript_id"] in seen:
                continue
            seen.add(sp["transcript_id"])
            S.append(_S(f"“{sp['quote']}” [{sp['turn_uid']}]", "quote", [sp["factor"]] if sp.get("factor") else [],
                        [sp["turn_uid"]], quote=sp["quote"], core=True))
            n += 1
            if n >= 5:
                break
        if not n:
            S.append(_S("No matching examples were found.", "notice", core=True))
        S += rationale_sentences(ev, pack.get("rationale"), "brief", core=False)
        S.append(_S("Examples illustrate; they are not counts or evidence of an effect.", "caveat"))
        return S
    if qt in ("effect_of", "describe_factor") and "focus" in pack:
        foc = pack["focus"]
        fo = pack.get("rationale_focus")

        def focus_lines(core: bool) -> list[dict]:
            if fo is None:
                return []
            return [_S(f"From the conversations: in the {{Q.window}} turns before {article(ev['name'])} {ev['name']}, "
                       f"{fo['text']} in {{QF.share_event}} of these calls, against {{QF.share_other}} at the same point in "
                       f"calls without one.", "rationale", core=core)] + chain_sentences(ev, fo.get("chain") or [], fo["text"])

        if foc is None:
            beh = spec.behaviour
            if qt == "describe_factor":
                if any(n.get("kind") == "factor" for n in pack["notices"]):
                    S.append(_S(f"Ask a question that lists factors first, for example 'Why do customers "
                                f"{EVENT_VERB.get(ev['code'], 'have ' + ev['plural'])}?', then ask about one of them.",
                                "clarify", core=True))
                else:
                    S.append(_S("Please name a factor from the last answer, for example 'the first factor'.", "clarify",
                                core=True))
                return S
            elif beh and BEHAVIOURS[beh].negative_control:
                short = BEHAVIOURS[beh].short
                S.append(_S(f"{_cap(short)} {_be(short)} a negative control: {'they are' if _plural(short) else 'it is'} "
                            f"measured only to check the method for hidden bias and {'are' if _plural(short) else 'is'} "
                            f"never reported as a factor.", "notice", core=True))
            elif beh and beh in EVENTS[ev["code"]].excluded_behaviours:
                short = BEHAVIOURS[beh].short
                S.append(_S(f"{_cap(short)} {_be(short)} part of how {ev['plural']} are defined here, so "
                            f"{'they' if _plural(short) else 'it'} cannot be studied as a possible cause of them.", "notice", core=True))
            else:
                S.append(_S("This behaviour was not in the pre-registered set for this event, so no causal estimate exists.",
                            "notice", core=True))
            if not (beh and BEHAVIOURS[beh].negative_control):
                S += focus_lines(True)
            if fo is None:
                S += rationale_sentences(ev, pack.get("rationale"), "brief", core=False)
            S.append(cnt_sentence)
            return S
        S += focus_lines(True)
        if fo is None:
            S += rationale_sentences(ev, pack.get("rationale"), "brief", core=False)
        S += later_notices
        S += factor_sentences(pack, foc, "full")
        th = pack.get("threshold")
        if th is not None:
            if foc["level"] not in ("L2", "L3"):
                msg = "there is no reliable estimate to compare with it"
            elif foc["id"] in th["clear"]:
                msg = "the estimate and its whole confidence interval are beyond {TH.value}"
            elif foc["id"] in th.get("ids", []):
                msg = "the estimate is beyond {TH.value}, but its confidence interval reaches below it"
            else:
                msg = "the estimate is not beyond {TH.value}"
            S.append(_S(f"Against the threshold in the question: {msg} [{foc['id']}].", "factor", [foc["id"]], core=True))
        S += caveat_sentences(pack, [foc])
        return S
    if pack.get("threshold") is not None:
        S += threshold_sentences(pack)
        S += rationale_sentences(ev, pack.get("rationale"), "brief", core=False)
        S.append(cnt_sentence)
        S += later_notices
        S += caveat_sentences(pack, pack["threshold"]["rows"])
        return S
    S += rationale_sentences(ev, pack.get("rationale"), "full", core=True)
    S.append(cnt_sentence)
    S += later_notices
    if pack["n_l3"]:
        S.append(_S(f"Causal test: for {ev['plural']} in {sl['label']}, {{A.n_l3}} in-call behaviour(s) passed every causal "
                    f"check and {{A.n_l2}} more are warning signs only.", "short", core=True))
    elif pack["n_l2"]:
        S.append(_S(f"Causal test: no in-call behaviour passed every causal check for {ev['plural']} in {sl['label']}; the "
                    f"behaviours below are warning signs only.", "short", core=True))
    else:
        S.append(_S(f"Causal test: no in-call behaviour has a reliable estimate for {ev['plural']} in {sl['label']}; any "
                    f"behaviours below are shown as counts only.", "short", core=True))
    if not (pack.get("rationale") or {}).get("available") and np.isfinite(pack["before_call"].get("opening_share", np.nan)) \
            and pack["before_call"]["opening_share"] > 0:
        terms = pack["before_call"]["terms"]
        tail = (" Customers in those calls often mention: " + ", ".join(f"'{t}'" for t in terms) + ".") if terms else ""
        S.append(_S(f"Before-call drivers: {{D.opening_share}} of these {ev['plural']} started within the opening turns, "
                    f"before anything the agent did could matter.{tail}", "driver"))
    n_l2_full = 0
    written = []
    for f in pack["factors"]:
        if qt == "what_to_change" and f["level"] != "L3":
            continue
        written.append(f)
        if f["level"] == "L3":
            detail = "full"
        else:
            detail = "full" if (f["level"] == "L2" and n_l2_full < 1 and not pack["n_l3"]) else "brief"
            n_l2_full += detail == "full"
        S += factor_sentences(pack, f, detail)
    if qt == "what_to_change":
        acts = [f for f in pack["factors"] if f["level"] == "L3" and f["actionable"]]
        if not acts:
            S.append(_S("No behaviour passed every causal check, so the data does not support a recommendation; the "
                        "warning signs above can guide what to review.", "action", core=True))
        for f in acts:
            more = f["att"] < 0
            S.append(_S(f"What could change: at comparable moments, {'doing more' if more else 'doing less'} of this is "
                        f"estimated to lower the chance of {article(ev['name'])} {ev['name']} by up to {{{f['id']}.att_abs}}, "
                        f"under the stated assumptions [{f['id']}].", "action", [f["id"]], core=True))
        if pack.get("topics"):
            S += topic_sentences(pack, core=False)
    S += caveat_sentences(pack, written)
    return S


LLM_ANSWER_SCHEMA = {
    "type": "object",
    "properties": {"sentences": {"type": "array", "items": {
        "type": "object",
        "properties": {"text": {"type": "string"}, "kind": {"type": "string", "enum": ["short", "premise", "notice", "count",
                                                                                          "driver", "factor", "quote", "action",
                                                                                          "caveat", "counter", "faithfulness",
                                                                                          "rank", "topics", "shared", "link", "rationale"]},
                       "factor_ids": {"type": "array", "items": {"type": "string"}},
                       "turn_uids": {"type": "array", "items": {"type": "string"}},
                       "quote": {"type": "string"}},
        "required": ["text", "kind", "factor_ids", "turn_uids", "quote"], "additionalProperties": False}}},
    "required": ["sentences"], "additionalProperties": False,
}
LLM_WRITER_RULES = """You write the prose of an answer about customer-service calls from an evidence pack.
Rules (a checker enforces them; sentences that break them are removed):
1. Never type a number. Use only the placeholders listed in the pack, written like {F3.att} or {D.rate}.
2. Wording must match each factor's claim level: L3 = "is estimated to raise/lower ... under the stated assumptions";
   L2 = "is associated with / is a warning sign of"; L1/L0 = counts only, no link words. Never write "causes",
   "leads to", "drives", "results in" or "the reason is".
3. Every sentence that links a behaviour to an event carries its factor id in square brackets, e.g. [F3].
4. Quotes: copy a span's exact words, put them in curly quotes and cite its turn id, e.g. “...” [<turn_uid>]; set
   "quote" to the exact words and "turn_uids" to [turn_uid]. Use only spans from the pack.
5. If the pack has premises, correct or confirm them first. Mention notices. End with the caveats.
Return JSON: {"sentences": [...]} with "quote" = "" when the sentence has no quote."""


def llm_write(llm, pack: dict, feedback: list | None = None) -> list[dict]:
    user = json.dumps({"pack": {k: v for k, v in pack.items() if k != "placeholders"},
                       "placeholders": sorted(pack["placeholders"]), "failed_sentences": feedback or []},
                      ensure_ascii=False, default=str)
    out = llm.json_call(system=LLM_WRITER_RULES, user=user, schema=LLM_ANSWER_SCHEMA, purpose="write_answer")
    core = ("short", "premise", "factor", "action", "rank", "topics", "shared", "link")
    return [{**s, "quote": s["quote"] or None, "core": s["kind"] in core} for s in out["sentences"]]


def render(text: str, placeholders: dict) -> str:
    return PLACEHOLDER_RE.sub(lambda m: placeholders.get(m.group(1), "{" + m.group(1) + "}"), text)


def finalize(sentences: list[dict], pack: dict, levels: dict, turn_text, llm=None, rewrite=None) -> dict:
    lookup = _TurnLookup(turn_text)
    gated = run_gates(sentences, pack["placeholders"], levels, lookup)
    rewrites = 0
    if rewrite is not None and any(not s["passed"] for s in gated):
        failed = [{"text": s["text"], "problems": s["gates"]} for s in gated if not s["passed"]]
        try:
            gated = run_gates(rewrite(failed), pack["placeholders"], levels, lookup)
            rewrites = 1
        except Exception:
            pass
    kept = [s for s in gated if s["passed"]]
    dropped = [s for s in gated if not s["passed"]]
    degraded = False
    if not any(s.get("core") for s in kept):
        degraded = True
        why = "the evidence needed for a reliable answer did not pass the checks"
        kept = [s for s in kept if s["kind"] in ("notice",)] + [
            {"text": f"The data cannot answer this reliably because {why}.", "kind": "L0", "factor_ids": [], "turn_uids": [],
             "quote": None, "core": True, "gates": {}, "passed": True}]
    text = "\n".join(render(s["text"], pack["placeholders"]) for s in kept)
    return {"text": text, "sentences": kept, "dropped": dropped, "rewrites": rewrites, "degraded": degraded}


class _TurnLookup(dict):
    def __init__(self, series):
        super().__init__()
        self._s = series

    def __contains__(self, key):
        return key in self._s.index

    def __getitem__(self, key):
        return self._s.loc[key]

    def get(self, key, default=None):
        return self._s.get(key, default)
