from __future__ import annotations

import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .definitions import CATEGORY_RANK, MAX_CATEGORY_FOR_LEVEL
from .gates import classify_causal, links_behaviour_to_event
from .queries import load_jsonl
from .session import SessionState
from .stats import paired_bootstrap_diff, ppi_mean_ci


def _slim(ans: dict) -> dict:
    return {"question": ans.get("question"), "route": ans.get("route"), "text": ans.get("text"),
            "spec": ans.get("spec"), "levels": ans.get("levels"), "degraded": ans.get("degraded"),
            "rewrites": ans.get("rewrites"), "seconds": ans.get("seconds"), "cache_hit": ans.get("cache_hit"),
            "sentences": [{k: s.get(k) for k in ("text", "kind", "factor_ids", "turn_uids", "quote")} for s in ans.get("sentences", [])],
            "dropped": [{"text": s.get("text"), "gates": s.get("gates")} for s in ans.get("dropped", [])],
            "notices": [n["text"] for n in (ans.get("pack") or {}).get("notices", [])],
            "premises": [{k: p.get(k) for k in ("behaviour", "event", "direction", "status", "factor_id", "level")}
                         for p in (ans.get("pack") or {}).get("premises", [])],
            "factors_shown": [{"id": f["id"], "behaviour": f["behaviour"], "level": f["level"]}
                              for f in (ans.get("pack") or {}).get("factors", [])],
            "versions": ans.get("versions")}


def _meta(item: dict) -> dict:
    return {k: item[k] for k in ("task", "difficulty", "query_type", "use_case") if k in item}


def run_query_file(engine, path, out_path) -> dict:
    items = load_jsonl(path)
    rows = []
    for it in items:
        if it.get("category") == "session":
            state = SessionState(library_version=engine.art.library_version, index_version=engine.art.index_version)
            turns = []
            for t in it["session"]:
                ans, state = engine.ask(t["question"], state)
                turns.append({**_slim(ans), "expected": t["expected"]})
            rows.append({"id": it["id"], "category": "session", **_meta(it), "turns": turns})
        else:
            ans, _ = engine.ask(it["question"])
            rows.append({"id": it["id"], "category": it["category"], **_meta(it), "expected": it["expected"], **_slim(ans)})
    Path(out_path).write_text("".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in rows), encoding="utf-8")
    return {"n": len(rows), "path": str(out_path)}


def expectation_met(r: dict) -> bool:
    ex = r["expected"]
    b = ex["behaviour"]
    kinds = [s["kind"] for s in r["sentences"]]
    spec = r.get("spec") or {}
    flagged = [u.get("attribute") for u in spec.get("unsupported") or []]
    answered = not r.get("degraded") and r.get("route") != "clarify" and "clarify" not in kinds and \
        (not ex.get("event") or spec.get("event") == ex["event"])
    if b == "clarify":
        return r.get("route") == "clarify" or "clarify" in kinds
    if b == "refuse_part":
        want = ex.get("unsupported")
        return bool(r.get("notices")) and (want in flagged if want else bool(flagged))
    if b == "answer_topics":
        return answered and "topics" in kinds
    if b == "answer_rank":
        return answered and "rank" in kinds and (not ex.get("explain_top") or ("factor" in kinds and "count" in kinds))
    if b == "answer_shared":
        return answered and "shared" in kinds and set(ex.get("events", [])) <= set((spec.get("compare") or {}).get("values", []))
    if b == "answer_event_link":
        return answered and "link" in kinds and "effects between events" in flagged
    if b == "decline_filter":
        return any("was not applied" in n.lower() for n in r.get("notices", []))
    if b == "correct_premise":
        ps = r.get("premises", [])
        if not ps or "premise" not in kinds:
            return False
        want = ex.get("premise_status")
        got = ps[0]["status"]
        if want == "supported":
            return got == "supported"
        if want == "contradicted":
            return got in ("contradicted", "not_supported", "weak")
        return got in ("weak", "not_supported", "contradicted", "not_estimated")
    if b == "answer_with_support_notice":
        return bool(r.get("notices")) and not r.get("degraded")
    filt = spec.get("filters") or {}
    if b == "answer_read":
        read = any(n.startswith(("I read ", "The question looks like", "The question was read")) for n in r.get("notices", []))
        return answered and read and slots_match(r)
    if b == "answer_condition":
        return answered and sorted(filt.get("with_event", [])) == sorted(ex["filters"].get("with_event", [])) and \
            any(s["text"].startswith(("This answer looks only at", "There are no")) for s in r["sentences"])
    if b == "answer_change":
        ch = spec.get("change") or {}
        return answered and ch.get("date") == ex.get("change_date") and f"before {ex.get('change_date')}" in (r.get("text") or "")
    if b == "answer_threshold":
        th = spec.get("threshold") or {}
        return answered and th.get("target") == ex.get("threshold_target") and bool(flagged)
    if b == "answer_profile":
        return r.get("route") != "clarify" and spec.get("question_type") == "behaviour" and \
            spec.get("behaviour") == ex.get("focus_behaviour") and "rationale" in kinds
    if b == "answer_overview":
        return spec.get("question_type") == "overview" and "count" in kinds and slots_match(r)
    if b == "answer_help":
        return spec.get("question_type") == "help" and "short" in kinds
    if b == "answer_call":
        return spec.get("question_type") == "call" and filt.get("call") == ex["filters"].get("call") and \
            "quote" in kinds and not any(s["kind"] == "clarify" for s in r["sentences"])
    if b in ("estimate_modification", "answer_contrast", "answer_counterfactual"):
        return False
    ok = not r.get("degraded") and r.get("route") != "clarify" and "clarify" not in kinds
    spec = r.get("spec") or {}
    if ex.get("event"):
        ok &= spec.get("event") == ex["event"]
    return bool(ok)


def slots_match(r: dict) -> bool:
    return all(slot_scores(r).values())


def slot_scores(r: dict) -> dict:
    ex, spec = r["expected"], r.get("spec") or {}
    out = {}
    if ex.get("event"):
        out["event"] = spec.get("event") == ex["event"]
    if ex.get("question_type"):
        out["question_type"] = spec.get("question_type") == ex["question_type"]
    if ex.get("filters"):
        f = spec.get("filters", {})
        out["filters"] = all(sorted(f.get(k, [])) == sorted(v) for k, v in ex["filters"].items())
    if ex.get("focus_behaviour"):
        out["behaviour"] = spec.get("behaviour") == ex["focus_behaviour"]
    return out


def wording_violations(r: dict) -> int:
    bad = 0
    lv = r.get("levels") or {}
    for s in r["sentences"]:
        cat = classify_causal(s["text"])
        if cat == "direct_causal":
            bad += 1
            continue
        ids = [f for f in s.get("factor_ids", []) if f in lv]
        if ids:
            allowed = min((MAX_CATEGORY_FOR_LEVEL.get(lv[f], "none") for f in ids), key=lambda c: CATEGORY_RANK[c])
            bad += CATEGORY_RANK[cat] > CATEGORY_RANK[allowed]
        elif links_behaviour_to_event(s["text"]) and cat != "none":
            bad += 1
    return bad


def boot_mean(values, draws=2000, seed=0):
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return {"mean": float("nan"), "ci": [float("nan"), float("nan")], "n": 0}
    rng = np.random.default_rng(seed)
    b = [v[rng.integers(0, v.size, v.size)].mean() for _ in range(draws)] if v.size > 1 else [v.mean()]
    return {"mean": float(v.mean()), "ci": [float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))], "n": int(v.size)}


def turn_carry_over(t: dict) -> bool | None:
    ex, spec = t["expected"], t.get("spec") or {}
    if ex["route"] == "clarify":
        return None
    filt = spec.get("filters") or {}
    ok = spec.get("event") == ex["event"]
    if ex.get("industry") is not None:
        ok &= sorted(filt.get("industry", [])) == sorted(ex["industry"])
    if ex.get("question_type"):
        ok &= spec.get("question_type") == ex["question_type"]
    if ex.get("behaviour"):
        ok &= spec.get("behaviour") == ex["behaviour"]
    if ex.get("with_event"):
        ok &= sorted(filt.get("with_event", [])) == sorted(ex["with_event"])
    if ex.get("change_date"):
        ok &= (spec.get("change") or {}).get("date") == ex["change_date"]
    return bool(ok)


def outcome_summary(r: dict) -> str:
    spec = r.get("spec") or {}
    if r.get("route") == "clarify" or any(s["kind"] == "clarify" for s in r.get("sentences", [])):
        what = "asked to clarify"
    elif r.get("degraded"):
        what = "declined (nothing passed the checks)"
    else:
        what = f"answered a '{spec.get('question_type')}' question about {spec.get('event')}"
        if spec.get("filters"):
            what += f" with filters {json.dumps(spec['filters'])}"
    flagged = [u.get("attribute") for u in spec.get("unsupported") or []]
    if flagged:
        what += f"; notices: {', '.join(flagged)}"
    return what


def score_outputs(rows: list[dict]) -> dict:
    limits = [r for r in rows if r["category"] == "known_limitation"]
    singles = [r for r in rows if r["category"] not in ("session", "known_limitation")]
    sessions = [r for r in rows if r["category"] == "session"]
    exp = [expectation_met(r) for r in singles]
    slots = [slot_scores(r) for r in singles]
    by_cat = pd.DataFrame({"category": [r["category"] for r in singles], "ok": exp}).groupby("category")["ok"].agg(["mean", "size"])
    by_tag = {}
    for tag in ("difficulty", "query_type"):
        if singles and all(tag in r for r in singles):
            g = pd.DataFrame({tag: [r[tag] for r in singles], "ok": exp}).groupby(tag)["ok"].agg(["mean", "size"])
            by_tag["by_" + tag] = {k: {"share_ok": float(v["mean"]), "n": int(v["size"])} for k, v in g.iterrows()}
    sent = sum(len(r["sentences"]) for r in singles)
    dropped = sum(len(r["dropped"]) for r in singles)
    gate_counts = {"numbers": 0, "causal": 0, "evidence": 0}
    for r in singles:
        for d in r["dropped"]:
            for g, probs in (d.get("gates") or {}).items():
                gate_counts[g] += bool(probs)
    quotes = [s for r in singles for s in r["sentences"] if s.get("quote")]
    carry, route_ok = [], []
    for s in sessions:
        for i, t in enumerate(s["turns"]):
            if i > 0:
                route_ok.append(t.get("route") == t["expected"]["route"])
            ok = turn_carry_over(t)
            if ok is not None:
                carry.append(ok)
    secs = [r["seconds"] for r in singles if r.get("seconds") is not None]
    return {
        "n_single": len(singles), "n_sessions": len(sessions),
        "expected_behaviour_met": boot_mean(exp),
        "by_category": {k: {"share_ok": float(v["mean"]), "n": int(v["size"])} for k, v in by_cat.iterrows()}, **by_tag,
        "slot_accuracy": {k: boot_mean([s[k] for s in slots if k in s]) for k in ("event", "question_type", "filters", "behaviour")},
        "sentences": sent, "sentences_dropped_by_gates": dropped, "dropped_by_gate": gate_counts,
        "degraded_answers": int(sum(bool(r.get("degraded")) for r in singles)),
        "wording_violations_after_gates": int(sum(wording_violations(r) for r in singles)),
        "quotes": len(quotes),
        "followup_carry_over": boot_mean(carry), "followup_route_accuracy": boot_mean(route_ok),
        "seconds_per_answer": {"median": float(np.median(secs)) if secs else float("nan"),
                               "p95": float(np.quantile(secs, 0.95)) if secs else float("nan")},
        "known_limitations": {"n": len(limits), "handled_as_ideal": int(sum(expectation_met(r) for r in limits)),
                              "items": [{"id": r["id"], "question": r["question"], "ideal": r["expected"]["behaviour"],
                                         "met": expectation_met(r), "system_did": outcome_summary(r),
                                         "why": r["expected"].get("limitation", "")} for r in limits]},
    }


def baseline_b0(engine, rows: list[dict]) -> dict:
    idx = engine.art.index
    out = {"premise_corrected": [], "unsupported_flagged": [], "count_error": []}
    if idx is None:
        return {"available": False}
    calls = engine.art.calls
    for r in rows:
        if r["category"] in ("session", "known_limitation"):
            continue
        hits = idx.search(r["question"], {"split": ["dev", "test"]}, top_k=10)
        if r["expected"]["behaviour"] == "correct_premise":
            out["premise_corrected"].append(False)
        if r["expected"]["behaviour"] == "refuse_part":
            out["unsupported_flagged"].append(False)
        if r["category"] == "how_often" and r["expected"].get("event"):
            e = r["expected"]["event"]
            m = np.ones(len(calls), dtype=bool)
            if r["expected"]["filters"].get("industry"):
                m &= calls["opening_domain_vote"].isin(r["expected"]["filters"]["industry"]).to_numpy()
            onset = engine.art.labels.loc[calls["transcript_id"], f"{e}_onset"]
            true_rate = float((onset.to_numpy()[m] >= 0).mean())
            hit_rate = float(np.mean([onset.loc[h["transcript_id"]] >= 0 for h in hits])) if hits else 0.0
            out["count_error"].append(abs(hit_rate - true_rate))
    return {"available": True, "premise_corrected": boot_mean(out["premise_corrected"]),
            "unsupported_flagged": boot_mean(out["unsupported_flagged"]),
            "abs_error_of_rate_from_search_hits": boot_mean(out["count_error"]),
            "note": "B0 answers from the top-10 windows; rates from hit counts; no premise or attribute checks"}


def event_and_industry_ok(spec: dict | None, ex: dict) -> bool:
    spec = spec or {}
    filt = spec.get("filters") or {}
    return bool(spec.get("event") == ex["event"] and (
        ex.get("industry") is None or sorted(filt.get("industry", [])) == sorted(ex["industry"])))


def baseline_b2(engine, rows: list[dict]) -> dict:
    ok, ok_system = [], []
    for s in rows:
        if s["category"] != "session":
            continue
        for i, t in enumerate(s["turns"]):
            ex = t["expected"]
            if i == 0 or ex["route"] == "clarify":
                continue
            ok.append(event_and_industry_ok(engine.parser.parse(t["question"]).to_dict(), ex))
            ok_system.append(event_and_industry_ok(t.get("spec"), ex))
    return {"carry_over": boot_mean(ok), "carry_over_system_same_turns": boot_mean(ok_system)}


def causal_validity(pipe, truth_calls: list[dict]) -> dict:
    from .analysis import HELD_OUT
    from .simulate import ORACLE_BEHAVIOURS, oracle_att
    lib = pipe.library()
    corpus = pipe.corpus()
    held = set(corpus.calls.index[corpus.calls["split"].isin(HELD_OUT)])
    rows = []
    builder = pipe.builder(with_gold=False)
    for r in lib[(lib["slice"] == "all")].itertuples(index=False):
        if r.behaviour not in ORACLE_BEHAVIOURS:
            continue
        o = oracle_att(truth_calls, r.behaviour, held, r.event, clean=True)
        rs = builder.build(r.event, r.behaviour)
        lab = rs.a_lab
        naive = float(rs.Y[lab & (rs.T == 1)].mean() - rs.Y[lab & (rs.T == 0)].mean()) if (lab & (rs.T == 1)).any() else float("nan")
        rows.append({"factor_id": r.factor_id, "event": r.event, "behaviour": r.behaviour, "level": r.level,
                     "truth": o["att"], "estimate": r.att, "ci_low": r.ci_low, "ci_high": r.ci_high,
                     "covered": bool(r.ci_low <= o["att"] <= r.ci_high), "naive_B3": naive,
                     "abs_error": abs(r.att - o["att"]), "abs_error_B3": abs(naive - o["att"])})
    df = pd.DataFrame(rows)
    if df.empty:
        return {"n": 0}
    l3 = df[df["level"] == "L3"]
    return {"n": int(len(df)), "coverage": boot_mean(df["covered"].astype(float)),
            "mean_abs_error": boot_mean(df["abs_error"]), "mean_abs_error_B3": boot_mean(df["abs_error_B3"]),
            "paired_error_B3_minus_system": paired_bootstrap_diff(df["abs_error_B3"], df["abs_error"]),
            "l3_sign_correct": float((np.sign(l3["estimate"]) == np.sign(l3["truth"])).mean()) if len(l3) else float("nan"),
            "l3_count": int(len(l3)), "false_l3": int(((l3["ci_low"] > 0) & (l3["truth"] <= 0)).sum() + ((l3["ci_high"] < 0) & (l3["truth"] >= 0)).sum()),
            "table": df.to_dict("records")}


def human_audit_template(pipe, rows: list[dict], n: int = 30, seed: int = 0) -> Path:
    rng = np.random.default_rng(seed)
    singles = [r for r in rows if r["category"] != "session" and r["expected"]["behaviour"] != "clarify"]
    pick = rng.choice(len(singles), size=min(n, len(singles)), replace=False) if singles else []
    recs = [{"id": singles[i]["id"], "question": singles[i]["question"], "answer": singles[i]["text"], "correct_0_1": "",
             "grounded_0_1": "", "claim_strength_calibrated_0_1": "", "useful_0_1": "", "judge_score_0_1": ""} for i in pick]
    p = pipe.ws.path("eval/human_audit.csv")
    pd.DataFrame(recs).to_csv(p, index=False)
    return p


def ppi_from_audit(pipe, all_judge_scores: list[float] | None = None) -> dict:
    p = pipe.ws.root / "eval" / "human_audit.csv"
    if not p.is_file():
        return {"status": "no audit file"}
    df = pd.read_csv(p)
    h = pd.to_numeric(df["correct_0_1"], errors="coerce")
    j = pd.to_numeric(df["judge_score_0_1"], errors="coerce")
    ok = h.notna() & j.notna()
    if ok.sum() < 10 or not all_judge_scores:
        return {"status": f"human audit incomplete ({int(h.notna().sum())} human scores) or no judge scores for all answers"}
    theta, lo, hi = ppi_mean_ci(h[ok].to_numpy(), j[ok].to_numpy(), np.asarray(all_judge_scores, dtype=float))
    return {"status": "ok", "ppi_mean": theta, "ci": [lo, hi], "n_human": int(ok.sum())}


JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"ratings": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "realism": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
                       "contextual_fit": {"type": "integer", "enum": [1, 2, 3, 4, 5]}, "category_ok": {"type": "boolean"},
                       "comment": {"type": "string"}},
        "required": ["id", "realism", "contextual_fit", "category_ok", "comment"], "additionalProperties": False}}},
    "required": ["ratings"], "additionalProperties": False,
}
JUDGE_RULES = """You review questions written to test a question-answering system over customer-service call transcripts
(business events: escalations, refund requests, churn threats; industries such as airline, hotel, telecom, banking,
insurance and retail). For every question give:
- realism 1-5: would a contact-centre manager or analyst plausibly ask this?
- contextual_fit 1-5: does it fit questions about business events in customer-service calls? A follow-up turn is judged
  in the context of the earlier turns of its session, which are given.
- category_ok: do its category and tags (task, difficulty, query_type, use_case) describe it correctly?
- comment: at most twenty words.
Categories such as known_limitation, out_of_scope, ambiguous and unanswerable are hard or out of scope on purpose:
judge whether a real user might ask them, not whether they can be answered. Brand names are masked as <brand>."""


def judge_queries(llm, items: list[dict], brands=(), batch: int = 25) -> dict:
    from .queries import questions_of
    pats = [re.compile(r"\b" + re.escape(b) + r"\b", re.I) for b in sorted({str(b) for b in brands if b and str(b).lower()
                                                                            not in ("none", "nan")}, key=len, reverse=True)]

    def mask(text: str) -> str:
        for p in pats:
            text = p.sub("<brand>", text)
        return text

    qs = questions_of(items)
    ratings: dict = {}
    for i in range(0, len(qs), batch):
        chunk = qs[i:i + batch]
        payload = []
        for qid, text, ex, item in chunk:
            rec = {"id": qid, "question": mask(text), **{k: item.get(k, "") for k in ("category", "task", "difficulty",
                                                                                       "query_type", "use_case")}}
            if item.get("category") == "session":
                turn = int(qid.rsplit(".", 1)[1])
                rec["earlier_turns"] = [mask(t["question"]) for t in item["session"][:turn - 1]]
            payload.append(rec)
        out = llm.json_call(system=JUDGE_RULES, user=json.dumps(payload, ensure_ascii=False), schema=JUDGE_SCHEMA,
                            purpose="judge_queries", effort="low")
        ids = {c[0] for c in chunk}
        for r in out["ratings"]:
            if r["id"] in ids:
                ratings[r["id"]] = r
    vals = list(ratings.values())
    summary = {"status": "ok", "model": getattr(llm, "model", ""), "n_questions": len(qs), "n_rated": len(vals),
               "missing": [q[0] for q in qs if q[0] not in ratings],
               "realism_mean": float(np.mean([v["realism"] for v in vals])) if vals else float("nan"),
               "contextual_fit_mean": float(np.mean([v["contextual_fit"] for v in vals])) if vals else float("nan"),
               "category_ok_share": float(np.mean([v["category_ok"] for v in vals])) if vals else float("nan"),
               "flagged_for_review": sorted(v["id"] for v in vals if v["realism"] <= 2 or v["contextual_fit"] <= 2
                                            or not v["category_ok"])}
    return {"summary": summary, "ratings": ratings}


TASK_TITLE = {"task1": "Task 1: evidence-based causal explanation", "task2": "Task 2: follow-up questions in context"}


def _answer_block(r: dict) -> list[str]:
    lines = [f"> {ln}" if ln.strip() else ">" for ln in (r.get("text") or "").split("\n")]
    cited = list(dict.fromkeys(u for s in r.get("sentences", []) for u in s.get("turn_uids") or []))
    factors = list(dict.fromkeys(f for s in r.get("sentences", []) for f in s.get("factor_ids") or []))
    extra = []
    if factors:
        extra.append("Factors cited: " + ", ".join(f"{f} ({(r.get('levels') or {}).get(f, '?')})" for f in factors))
    if cited:
        extra.append("Dialogue turns cited: " + ", ".join(f"`{u}`" for u in cited))
    if r.get("dropped"):
        extra.append(f"Sentences removed by the gates: {len(r['dropped'])}")
    return lines + ([""] + [f"*{x}*" for x in extra] if extra else [])


def render_query_outputs(pipe, res: dict) -> Path:
    from .queries import CATEGORY_ORDER
    ws = pipe.ws
    L = ["# Query set and system outputs", "",
         "Every query of the dev and locked test sets, with its tags (task, difficulty, kind of query, use case), the "
         "behaviour expected of the system, whether that happened, and the full answer exactly as shown to a user "
         "(numbers filled in by code, cited dialogue turns as `transcript_id:turn`). Sessions (Task 2) are shown turn "
         "by turn. Known limitations are questions the system is known to handle badly; they are scored against what "
         "an ideal system would do and kept out of the headline scores.", ""]
    qs = res.get("query_set") or {}
    if qs.get("distribution"):
        L += ["## The query set", ""]
        for f, title in (("task", "Task"), ("difficulty", "Difficulty"), ("query_type", "Kind of query"),
                         ("use_case", "Use case"), ("category", "Category")):
            d = qs["distribution"].get(f) or {}
            L.append(f"* **{title}:** " + ", ".join(f"{k} {v}" for k, v in d.items()))
        dv = qs.get("diversity") or {}
        L += [f"* **Questions in total** (session turns counted): {dv.get('n_questions', 'n/a')}; distinct-1 "
              f"{_fmt(dv.get('distinct_1'), '.2f')}, distinct-2 {_fmt(dv.get('distinct_2'), '.2f')}, mean pairwise "
              f"ROUGE-L {_fmt(dv.get('mean_pairwise_rouge_l'), '.2f')}.", ""]
    for sp in ("dev", "test"):
        p = ws.root / "outputs" / f"outputs_{sp}.jsonl"
        if not p.is_file():
            continue
        rows = load_jsonl(p)
        L += [f"## {'Dev' if sp == 'dev' else 'Locked test'} queries ({len(rows)})", ""]
        for task in ("task1", "task2"):
            trows = [r for r in rows if r.get("task", "task2" if r["category"] == "session" else "task1") == task]
            if not trows:
                continue
            L += [f"### {TASK_TITLE[task]}", ""]
            order = {c: i for i, c in enumerate(CATEGORY_ORDER)}
            for r in sorted(trows, key=lambda r: (order.get(r["category"], 99), r["id"])):
                tags = " · ".join(str(r.get(k, "")) for k in ("difficulty", "query_type", "use_case") if r.get(k))
                if r["category"] == "session":
                    L += [f"#### {r['id']} — follow-up session · {tags}", ""]
                    for i, t in enumerate(r["turns"], 1):
                        ex = t["expected"]
                        ok = turn_carry_over(t)
                        good = (t.get("route") == ex["route"] if i > 1 else True) and ok is not False
                        want = f"route `{ex['route']}`, event {ex.get('event')}, industries {ex.get('industry') or 'all'}"
                        L += [f"**Turn {i}:** {t['question']}", "",
                              f"Expected: {want}. Got: route `{t.get('route')}`, event {(t.get('spec') or {}).get('event')}, "
                              f"industries {((t.get('spec') or {}).get('filters') or {}).get('industry') or 'all'} — "
                              f"{'as expected' if good else 'NOT as expected'}.", ""]
                        L += _answer_block(t) + [""]
                    continue
                ex = r["expected"]
                met = expectation_met(r)
                want = ex["behaviour"] + (f" (event {ex['event']}" + (f", type {ex['question_type']}" if ex.get("question_type") else "")
                                          + ")" if ex.get("event") else "")
                if r["category"] == "known_limitation":
                    verdict = ("handled as an ideal system would" if met else
                               f"**known limitation** — {ex.get('limitation', '')}")
                else:
                    verdict = "as expected" if met else "**NOT as expected**"
                L += [f"#### {r['id']} — {r['category']} · {tags}", "", f"**Question:** {r['question']}", "",
                      f"Expected: {want}. Outcome: {verdict} (the system {outcome_summary(r)}).", ""]
                L += _answer_block(r) + [""]
    p = ws.path("outputs/QUERY_OUTPUTS.md")
    p.write_text("\n".join(L) + "\n", encoding="utf-8")
    return p


def evaluate_all(pipe, truth_calls: list[dict] | None = None, llm=None) -> dict:
    from .queries import query_diversity
    ws = pipe.ws
    eng = pipe.engine()
    res = {}
    items = [q for sp in ("dev", "test") if (ws.root / "queries" / f"queries_{sp}.jsonl").is_file()
             for q in load_jsonl(ws.root / "queries" / f"queries_{sp}.jsonl")]
    if items:
        lock = ws.read_json("queries/queries_lock.json") if ws.exists("queries/queries_lock.json") else {}
        res["query_set"] = {"n_queries": len(items), "distribution": lock.get("distribution"),
                            "diversity": query_diversity(items)}
        if llm is not None and getattr(llm, "available", False):
            try:
                judged = judge_queries(llm, items, brands=pipe.corpus().calls["brand"].dropna().astype(str).unique())
                ws.write_json(judged, "eval/query_judge.json")
                res["query_judge"] = judged["summary"]
            except Exception as exc:
                res["query_judge"] = {"status": f"failed: {type(exc).__name__}: {exc}"}
        else:
            res["query_judge"] = {"status": "not run (optional; `python -m crest evaluate --llm`)"}
    for sp in ("dev", "test"):
        p = ws.root / "outputs" / f"outputs_{sp}.jsonl"
        if p.is_file():
            rows = load_jsonl(p)
            res[sp] = score_outputs(rows)
            res[sp]["B0"] = baseline_b0(eng, rows)
            res[sp]["B2"] = baseline_b2(eng, rows)
            if sp == "test":
                human_audit_template(pipe, rows)
    res["library"] = ws.read_json("library/library_report.json")
    res["build_checks"] = ws.read_json("checks/build_checks.json")
    if ws.exists("evidence/forecaster_quality.json"):
        res["evidence"] = ws.read_json("evidence/forecaster_quality.json")
        fq = pd.read_csv(ws.root / "evidence" / "factor_faithfulness.csv")
        res["faithfulness"] = fq.to_dict("records")
    if truth_calls is not None:
        res["causal_validity"] = causal_validity(pipe, truth_calls)
        rq = ws.root / "eval" / "retrieval_queries.jsonl"
        if rq.is_file() and eng.art.index is not None:
            from .index import retrieval_metrics
            res["retrieval"] = retrieval_metrics(eng.art.index, load_jsonl(rq))
    res["human_audit"] = ppi_from_audit(pipe)
    ws.write_json(res, "eval/metrics.json")
    (ws.root / "REPORT.md").write_text(render_report(res, pipe), encoding="utf-8")
    render_query_outputs(pipe, res)
    return res


def _fmt(x, spec: str = ".3f", scale: float = 1.0) -> str:
    try:
        v = float(x) * scale
    except (TypeError, ValueError):
        return "n/a"
    return format(v, spec) if np.isfinite(v) else "n/a"


def _ci(d: dict, pct: bool = True) -> str:
    if not d or _fmt(d.get("mean")) == "n/a":
        return "n/a"
    def f(x):
        v = _fmt(x, ".1f", 100) if pct else _fmt(x, ".3f")
        return v + "%" if pct and v != "n/a" else v
    ci = d.get("ci") or [None, None]
    return f"{f(d['mean'])} (95% CI {f(ci[0])}–{f(ci[1])}, n={d.get('n', 'n/a')})"


def render_report(res: dict, pipe) -> str:
    L = ["# CREST evaluation report", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M')} from `{pipe.ws.root}`. Every number below is computed by "
         "`crest/evaluate.py` from the stored outputs; confidence intervals are bootstrap intervals.", ""]
    lib = res.get("library", {})
    bc = res.get("build_checks", {})
    L += ["## 1. Data and design checks", "",
          f"* Landmark rows: {_fmt(bc.get('landmark_rows'), ',.0f')} with {bc.get('n_features', 'n/a')} history features.",
          f"* Future-invariance test: {bc.get('future_invariance', {}).get('failures', 'n/a')} failures in "
          f"{bc.get('future_invariance', {}).get('rows_checked', 'n/a')} rows.",
          f"* Outcome-blindness of behaviour detectors: {'passed' if bc.get('cue_blindness', {}).get('passed') else 'FAILED'}.",
          f"* Leakage-flagged metadata columns (never used): {', '.join(bc.get('leakage_flagged_columns') or []) or 'none'}.",
          f"* Calls without dialogue turns set aside: {len(bc.get('excluded_calls') or [])}.", ""]
    gm = lib.get("gold_metrics") or {}
    L += ["## 2. Event labels (blind gold set, inverse-probability weighted)", ""]
    if gm:
        L += ["| Event | Precision | Recall | F1 (95% CI) | Onset within 1 turn | kappa |", "|---|---|---|---|---|---|"]
        for e, d in (gm.get("by_event") or {}).items():
            f1_ci = d.get("f1_ci") or [None, None]
            L.append(f"| {e} | {_fmt(d.get('precision'))} | {_fmt(d.get('recall'))} | {_fmt(d.get('f1'))} "
                     f"({_fmt(f1_ci[0])}–{_fmt(f1_ci[1])}) | {_fmt(d.get('onset_within1'), '.2f')} | "
                     f"{_fmt(d.get('kappa_presence'), '.2f')} |")
    else:
        L.append("No gold labels ingested: every claim is capped at L2 (check `gold_f1_ok`).")
    pl = lib.get("planted_effect_test") or {}
    planted = (f"* Planted-effect test: passed = {pl.get('passed')}; bias {_fmt(pl.get('bias'), '+.4f')} "
               f"(MC s.e. {_fmt(pl.get('bias_mcse'), '.4f')}; {_fmt(pl.get('standardized_bias'), '.0%')} of the typical "
               f"standard error, allowed 40%); coverage {_fmt(pl.get('coverage'), '.2f')}; "
               f"null false-alarm rate {_fmt(pl.get('false_alarm_rate'), '.2f')} over {pl.get('n_sims', 0)} simulations."
               if pl.get("n_sims") else f"* Planted-effect test: NOT RUN ({pl.get('reason', 'no result')}); no claim can reach L3.")
    L += ["", "## 3. Causal pipeline", "", planted,
          f"* Pre-registration: sha256 `{lib.get('prereg_sha256')}`; intact = {lib.get('prereg_ok')}.",
          "* Negative controls (95% CI):"]
    for nc in lib.get("negative_controls") or []:
        L.append(f"  * {nc['event']} × {nc['behaviour']}: {_fmt(nc.get('att'), '+.1f', 100)} points "
                 f"({_fmt(nc.get('ci_low'), '+.1f', 100)} to {_fmt(nc.get('ci_high'), '+.1f', 100)})"
                 + ("" if _fmt(nc.get("att")) != "n/a" else " -- not estimable (too rare); the event's check uses its "
                                                             "estimable controls and needs at least one"))
    L.append(f"* Claim levels (all calls): {json.dumps(lib.get('levels', {}))}")
    lib_df = pipe.library()
    main = lib_df[(lib_df["slice"] == "all") & ~lib_df["negative_control"] & lib_df["level"].isin(["L3", "L2"])]
    if len(main):
        L += ["", "| Factor | Event | Behaviour | Level | ATT (points) | 95% CI | q | E-value | Failed checks |", "|---|---|---|---|---|---|---|---|---|"]
        for r in main.itertuples(index=False):
            L.append(f"| {r.factor_id} | {r.event} | {r.behaviour} | {r.level} | {_fmt(r.att, '+.1f', 100)} | "
                     f"{_fmt(r.ci_low, '+.1f', 100)} to {_fmt(r.ci_high, '+.1f', 100)} | {_fmt(r.q)} | {_fmt(r.e_value, '.2f')} | "
                     f"{', '.join(r.failed_checks) or '—'} |")
    cv = res.get("causal_validity")
    if cv and cv.get("n"):
        L += ["", "### Recovery of known effects (synthetic corpus with a causal oracle)", "",
              f"* CI coverage of the true ATT: {_ci(cv['coverage'])} over {cv['n']} factors with an oracle.",
              f"* Mean absolute error: system {_ci(cv['mean_abs_error'], False)}; associational baseline B3 "
              f"{_ci(cv['mean_abs_error_B3'], False)}; paired difference (B3 − system) {_fmt(cv['paired_error_B3_minus_system'].get('diff'))} "
              f"(95% CI {_fmt((cv['paired_error_B3_minus_system'].get('ci') or [None, None])[0])} to "
              f"{_fmt((cv['paired_error_B3_minus_system'].get('ci') or [None, None])[1])}).",
              f"* L3 claims: {cv['l3_count']}; sign correct {_fmt(cv.get('l3_sign_correct'), '.0f', 100)}%; L3 claims whose CI "
              f"excludes the true effect on the wrong side: {cv['false_l3']}.", "",
              "| Event | Behaviour | Level | Truth | Estimate (95% CI) | Naive (B3) |", "|---|---|---|---|---|---|"]
        for r in cv["table"]:
            L.append(f"| {r['event']} | {r['behaviour']} | {r['level']} | {_fmt(r.get('truth'), '+.1f', 100)} | "
                     f"{_fmt(r.get('estimate'), '+.1f', 100)} ({_fmt(r.get('ci_low'), '+.1f', 100)} to "
                     f"{_fmt(r.get('ci_high'), '+.1f', 100)}) | {_fmt(r.get('naive_B3'), '+.1f', 100)} |")
    ev = res.get("evidence")
    if ev:
        L += ["", "## 4. Evidence (forecaster: faithfulness only, never causal)", ""]
        for e, q in (ev.get("forecaster_quality") or {}).items():
            if q.get("auc_next_turn") is not None:
                auc_ci = q.get("auc_next_turn_ci") or [None, None]
                L.append(f"* {e}: AUC next turn {_fmt(q['auc_next_turn'])} ({_fmt(auc_ci[0])}–{_fmt(auc_ci[1])}); "
                         f"within 3 turns {_fmt(q.get('auc_within_3'))}; calibration slope {_fmt(q.get('calibration_slope'), '.2f')}; "
                         f"ECE {_fmt(q.get('ece'))}.")
        for e, c in (ev.get("comprehensiveness") or {}).items():
            if c.get("n_calls"):
                cci = c.get("ci") or [None, None]
                L.append(f"* Comprehensiveness minus random baseline, {e}: {_fmt(c.get('comprehensiveness_minus_random'), '+.3f')} "
                         f"({_fmt(cci[0], '+.3f')} to {_fmt(cci[1], '+.3f')}), {c['n_calls']} calls.")
    if res.get("retrieval"):
        r = res["retrieval"]
        rci = r.get("recall_ci") or [None, None]
        L += ["", "## 5. Retrieval", "", f"* Recall@10 {_fmt(r.get('recall@10'))} (95% CI {_fmt(rci[0])}–{_fmt(rci[1])}); "
              f"nDCG@10 {_fmt(r.get('ndcg@10'))}; {r.get('n_queries', 0)} queries."]
    for sp in ("dev", "test"):
        s = res.get(sp)
        if not s:
            continue
        L += ["", f"## 6{'a' if sp == 'dev' else 'b'}. Answers — {sp} queries ({s['n_single']} single questions, {s['n_sessions']} sessions)", "",
              f"* Expected behaviour met: {_ci(s['expected_behaviour_met'])}.",
              f"* Slot accuracy: event {_ci(s['slot_accuracy']['event'])}; question type {_ci(s['slot_accuracy']['question_type'])}; "
              f"filters {_ci(s['slot_accuracy']['filters'])}.",
              f"* Gates: {s['sentences_dropped_by_gates']} of {s['sentences']} sentences dropped ({json.dumps(s['dropped_by_gate'])}); "
              f"degraded answers {s['degraded_answers']}; wording violations after gates {s['wording_violations_after_gates']}.",
              f"* Follow-ups: carry-over {_ci(s['followup_carry_over'])}; route accuracy {_ci(s['followup_route_accuracy'])}.",
              f"* Baseline B2 (each follow-up read without the session state; event and industry of the later turns) "
              f"carry-over: {_ci(s['B2']['carry_over'])}; the system on the same turns and slots: "
              f"{_ci(s['B2'].get('carry_over_system_same_turns', {}))}.",
              f"* Baseline B0 (plain retrieval): premises corrected {_ci(s['B0'].get('premise_corrected', {}))}; unsupported "
              f"attributes flagged {_ci(s['B0'].get('unsupported_flagged', {}))}; absolute error of rates from search hits "
              f"{_ci(s['B0'].get('abs_error_of_rate_from_search_hits', {}), False)}.",
              f"* Seconds per answer: median {_fmt(s['seconds_per_answer'].get('median'))}, p95 {_fmt(s['seconds_per_answer'].get('p95'))}.",
              f"* Known limitations (kept out of every score above; see 6c): {(s.get('known_limitations') or {}).get('handled_as_ideal', 0)} "
              f"of {(s.get('known_limitations') or {}).get('n', 0)} handled as an ideal system would.",
              "", "| Category | Share as expected | n |", "|---|---|---|"]
        for c, v in s["by_category"].items():
            L.append(f"| {c} | {_fmt(v.get('share_ok'), '.0f', 100)}% | {v['n']} |")
        for key, title in (("by_difficulty", "Difficulty"), ("by_query_type", "Kind of query")):
            if s.get(key):
                L += ["", f"| {title} | Share as expected | n |", "|---|---|---|"]
                for c, v in s[key].items():
                    L.append(f"| {c} | {_fmt(v.get('share_ok'), '.0f', 100)}% | {v['n']} |")
    qs = res.get("query_set")
    if qs:
        dv = qs.get("diversity") or {}
        dist = qs.get("distribution") or {}
        L += ["", "## 6c. The query set", "",
              f"* {qs['n_queries']} queries ({dv.get('n_questions', 'n/a')} questions with the session turns); every "
              f"answer is in `outputs/QUERY_OUTPUTS.md`; the list is in `queries/queries.csv` and the human review sheet "
              f"in `queries/queries_review.csv`."]
        for f, title in (("task", "Task"), ("difficulty", "Difficulty"), ("query_type", "Kind of query"), ("use_case", "Use case")):
            if dist.get(f):
                L.append(f"* {title}: " + ", ".join(f"{k} {v}" for k, v in dist[f].items()) + ".")
        ev = dv.get("evenness") or {}
        L += [f"* Diversity: distinct-1 {_fmt(dv.get('distinct_1'), '.2f')}, distinct-2 {_fmt(dv.get('distinct_2'), '.2f')}; "
              f"mean pairwise ROUGE-L {_fmt(dv.get('mean_pairwise_rouge_l'), '.2f')} (max {_fmt(dv.get('max_pairwise_rouge_l'), '.2f')}); "
              f"distinct expected-slot combinations {_fmt(dv.get('distinct_expected_slots_share'), '.0%')} of questions; "
              f"evenness (normalised entropy) of categories {_fmt(ev.get('category'), '.2f')}, difficulty "
              f"{_fmt(ev.get('difficulty'), '.2f')}, events {_fmt(dv.get('evenness_event'), '.2f')}."]
        jd = res.get("query_judge") or {}
        if jd.get("status") == "ok":
            L.append(f"* LLM judge ({jd.get('model')}, brands masked): realism {_fmt(jd.get('realism_mean'), '.2f')} / 5, "
                     f"contextual fit {_fmt(jd.get('contextual_fit_mean'), '.2f')} / 5, categories correct "
                     f"{_fmt(jd.get('category_ok_share'), '.0%')}; {len(jd.get('flagged_for_review') or [])} questions flagged "
                     f"for human review ({', '.join(jd.get('flagged_for_review') or []) or 'none'}).")
        else:
            L.append(f"* LLM judge: {jd.get('status', 'not run')}.")
        lim = [it for sp in ("dev", "test") for it in ((res.get(sp) or {}).get("known_limitations") or {}).get("items", [])]
        if lim:
            L += ["", "Known limitations (questions the system handles badly, shown with what it did):", "",
                  "| Query | Question | Ideal behaviour | What the system did | Why |", "|---|---|---|---|---|"]
            for it in sorted(lim, key=lambda x: x["id"]):
                L.append(f"| {it['id']} | {it['question']} | {it['ideal']} | {it['system_did']}"
                         f"{' (as ideal)' if it['met'] else ''} | {it['why']} |")
    ha = res.get("human_audit", {})
    L += ["", "## 7. Human audit and judge", "",
          f"* Status: {ha.get('status')}. Fill `eval/human_audit.csv` (30 test answers); judge scores from a different model "
          "family go in `judge_score_0_1`; the PPI-corrected score is then computed by `crest evaluate`."]
    L += ["", "## 8. Limits (stated in every report)", "",
          "1. Unmeasured confounding: estimates assume the history before each moment captures what drives both the "
          "behaviour and the event; E-values and negative controls probe this.",
          "2. Single-turn decisions, not policies.", "3. This corpus only.", "4. Text only (no audio or timestamps).",
          "5. Label error is corrected on average by DSL; onset timing is probed by S8.",
          "6. Wording is gated, but a human should read answers before business decisions."]
    return "\n".join(L) + "\n"
