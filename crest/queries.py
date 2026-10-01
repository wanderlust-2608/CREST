from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

from .definitions import BEHAVIOURS, PRIMARY_EVENTS

EV_WORD = {"ESC": ("escalations", "escalate", "ask for a supervisor"), "REF": ("refund requests", "ask for refunds", "want money back"),
           "CHURN": ("churn threats", "threaten to leave", "threaten to cancel")}
PRODUCT_Q = {"ESC": "What do customers complain about before they ask for a supervisor?",
             "REF": "Which product or service problems lead to refund requests?",
             "CHURN": "What should the product team fix to reduce churn threats?"}
RANK_Q = {"ESC": "Which industry has the highest escalation rate?",
          "REF": "Which industry has the most refund requests?",
          "CHURN": "Rank the industries by how often customers threaten to cancel"}
IND_WORD = {"hospitality": "hotel", "airline": "airline", "telecom": "telecom", "banking": "banking", "insurance": "insurance",
            "retail_ecommerce": "retail"}


QUERY_META = {
    "how_often": ("task1", "easy", "simple_retrieval", "monitoring"),
    "examples": ("task1", "easy", "simple_retrieval", "evidence_lookup"),
    "trend": ("task1", "easy", "simple_retrieval", "monitoring"),
    "why": ("task1", "medium", "multi_hop", "root_cause"),
    "compare": ("task1", "medium", "multi_hop", "segment_comparison"),
    "effect_of": ("task1", "medium", "multi_hop", "hypothesis_test"),
    "true_premise": ("task1", "medium", "premise_check", "hypothesis_test"),
    "what_to_change": ("task1", "hard", "multi_hop", "process_improvement"),
    "false_presupposition": ("task1", "hard", "premise_check", "guardrail"),
    "leading": ("task1", "hard", "premise_check", "guardrail"),
    "unanswerable": ("task1", "hard", "cannot_answer", "guardrail"),
    "unsupported_filter": ("task1", "hard", "cannot_answer", "guardrail"),
    "tiny_subgroup": ("task1", "hard", "cannot_answer", "guardrail"),
    "ambiguous": ("task1", "hard", "ambiguous", "guardrail"),
    "product_improvement": ("task1", "medium", "simple_retrieval", "product_improvement"),
    "ranking": ("task1", "easy", "simple_retrieval", "segment_comparison"),
    "multi_hop": ("task1", "hard", "multi_hop", "root_cause"),
    "out_of_scope": ("task1", "medium", "cannot_answer", "guardrail"),
    "known_limitation": ("task1", "hard", "known_limitation", "stress_test"),
    "session": ("task2", "medium", "follow_up", "follow_up"),
    "noisy_text": ("task1", "medium", "robustness", "robustness"),
    "multilingual": ("task1", "medium", "robustness", "robustness"),
    "conditional": ("task1", "hard", "multi_hop", "root_cause"),
    "before_after": ("task1", "hard", "impact_evaluation", "impact_evaluation"),
    "threshold": ("task1", "medium", "multi_hop", "hypothesis_test"),
    "behaviour_profile": ("task1", "medium", "simple_retrieval", "root_cause"),
    "overview": ("task1", "easy", "simple_retrieval", "monitoring"),
    "retention_risk": ("task1", "medium", "multi_hop", "root_cause"),
    "single_call": ("task1", "medium", "evidence_lookup", "root_cause"),
    "causal_failure": ("task1", "hard", "causal_audit", "causal_guardrail"),
    "counterevidence": ("task1", "hard", "counterevidence", "causal_guardrail"),
}
KNOWN_LIMITATIONS = [
    ("Kwa nini wateja wanaomba msimamizi?", {"behaviour": "answer", "event": "ESC", "question_type": "why"},
     "languages outside the built-in word lists (here Swahili) are read only when an LLM is configured; without one "
     "the system asks the user to rephrase"),
    ("Does empathy reduce escalations only when the customer is already frustrated?",
     {"behaviour": "estimate_modification", "event": "ESC"},
     "effects are estimated over all comparable moments together; an effect within calls where something else already "
     "happened (effect modification) is not estimated, so the overall estimate is given with a notice"),
    ("Why did escalations go up in hotel calls but not in airline calls?",
     {"behaviour": "answer_contrast", "event": "ESC"},
     "a contrast between two slices inside a why-question is answered for the first slice only; the second slice is "
     "read as an exclusion"),
    ("If agents had offered a solution earlier in this call, would the customer still have escalated?",
     {"behaviour": "answer_counterfactual", "event": "ESC"},
     "counterfactuals about one specific call are not estimated: estimates describe calls in general, and one call's "
     "outcome under a different agent action is not identifiable from the data"),
]
META_FIELDS = ("task", "difficulty", "query_type", "use_case")
CATEGORY_ORDER = ["how_often", "examples", "trend", "ranking", "product_improvement", "why", "compare", "effect_of", "causal_failure", "counterevidence",
                  "what_to_change", "multi_hop", "conditional", "before_after", "threshold", "behaviour_profile", "overview",
                  "retention_risk", "single_call", "noisy_text", "multilingual", "true_premise", "false_presupposition",
                  "leading", "unanswerable", "out_of_scope", "unsupported_filter", "tiny_subgroup", "ambiguous",
                  "known_limitation", "session"]
NOISY = {"ESC": ("why do custmers escalte so often?", "how often do customers escalate in {ind_typo} calls?"),
         "REF": ("y do customers want there money bak?", "wats driving refnds in {ind_typo} calls?"),
         "CHURN": ("y do custmrs threten to cancl?", "why do custmers threatn to leave in {ind_typo} calls?")}
IND_TYPO = {"hospitality": ("hotle", "hospitality"), "airline": ("airlnie", "airline"), "telecom": ("telcom", "telecom"),
            "banking": ("bankng", "banking"), "insurance": ("insurnace", "insurance"), "retail_ecommerce": ("retial", "retail_ecommerce")}
MULTILINGUAL = [("ESC", "Warum eskalieren Kunden?"), ("REF", "Pourquoi les clients demandent-ils un remboursement ?"),
                ("CHURN", "Por que os clientes ameaçam cancelar?"), ("CHURN", "customers cancel karne ki dhamki kyun dete hain?"),
                ("REF", "ग्राहक रिफंड क्यों मांगते हैं?")]
MULTI_IND = {"hospitality": ("¿Con qué frecuencia escalan los clientes en las llamadas de hoteles?", "ESC", "how_often"),
             "airline": ("Pourquoi les clients des compagnies aériennes menacent-ils de partir ?", "CHURN", "why")}
CONDITIONAL = [("Do refunds happen more in calls with escalations?", "REF", "why", ["ESC"]),
               ("How often do customers who were refused a refund threaten to cancel?", "CHURN", "how_often", ["REF_DENIED"]),
               ("Why do customers who were refused a refund and threatened to cancel escalate?", "ESC", "why",
                ["REF_DENIED", "CHURN"])]
PROFILES = [("Why are customers put on hold?", "hold_request"), ("When do agents refuse requests?", "refusal")]



def tag_query(item: dict) -> dict:
    task, diff, qtype, use = QUERY_META.get(item["category"], ("task1", "medium", "other", "other"))
    if item["category"] == "session" and len(item.get("session", [])) >= 4:
        diff = "hard"
    return {**item, "task": task, "difficulty": diff, "query_type": qtype, "use_case": use}


def rouge_l(a: str, b: str) -> float:
    x, y = a.lower().split(), b.lower().split()
    if not x or not y:
        return 0.0
    dp = [[0] * (len(y) + 1) for _ in range(len(x) + 1)]
    for i in range(len(x)):
        for j in range(len(y)):
            dp[i + 1][j + 1] = dp[i][j] + 1 if x[i] == y[j] else max(dp[i][j + 1], dp[i + 1][j])
    lcs = dp[-1][-1]
    p, r = lcs / len(x), lcs / len(y)
    return 0.0 if lcs == 0 else 2 * p * r / (p + r)


def _q(qid, cat, text, expect, event=None, qtype=None, filters=None, behaviour=None, extra=None):
    return {"id": qid, "category": cat, "question": text,
            "expected": {"behaviour": expect, "event": event, "question_type": qtype, "filters": filters or {},
                         "focus_behaviour": behaviour, **(extra or {})}}


def middle_date(calls: pd.DataFrame) -> str | None:
    if "call_date" not in calls.columns:
        return None
    d = pd.to_datetime(calls["call_date"], errors="coerce").dropna()
    if d.nunique() < 4:
        return None
    return str(d.sort_values().iloc[len(d) // 2].date())


def pick_calls(calls: pd.DataFrame, labels: pd.DataFrame | None) -> tuple[str | None, str | None]:
    if labels is None or "ESC_onset" not in labels.columns or "split" not in calls.columns:
        return None, None
    held = calls[calls["split"].isin(["dev", "test"])]["transcript_id"].astype(str)
    lab = labels.reindex(held)
    cols = [c for c in (f"{e}_onset" for e in ("ESC", "REF", "CHURN", "RISK")) if c in lab.columns]
    esc = lab.index[(lab["ESC_onset"].fillna(-1) >= 0).to_numpy()]
    quiet = lab.index[(lab[cols].fillna(-1) < 0).all(axis=1).to_numpy()]
    return (str(esc[len(esc) // 2]) if len(esc) else None), (str(quiet[len(quiet) // 2]) if len(quiet) else None)


def add_capability_queries(add, calls: pd.DataFrame, labels, inds: list, settings) -> None:
    has_risk = labels is not None and "RISK_onset" in labels.columns
    for k, e in enumerate(PRIMARY_EVENTS):
        plain, with_ind = NOISY[e]
        add("noisy_text", plain, "answer_read", e, "why" if not plain.startswith("how often") else "how_often")
        if k == 0:
            typo = IND_TYPO.get(inds[0], (inds[0], inds[0]))[0]
            add("noisy_text", with_ind.format(ind_typo=typo), "answer_read", e,
                "how_often" if with_ind.startswith("how often") else "why", {"industry": [inds[0]]})
    for e, q in MULTILINGUAL:
        add("multilingual", q, "answer_read", e, "why")
    for ind, (q, e, qt) in MULTI_IND.items():
        if ind in inds:
            add("multilingual", q, "answer_read", e, qt, {"industry": [ind]})
            break
    for q, e, qt, conds in CONDITIONAL:
        add("conditional", q, "answer_condition", e, qt, {"with_event": conds})
    day = middle_date(calls)
    if day:
        add("before_after", f"Did escalations go up after {day}?", "answer_change", "ESC", "trend", extra={"change_date": day})
        add("before_after", f"Compare refund requests before and after {day}", "answer_change", "REF", "trend",
            extra={"change_date": day})
    add("before_after", "Did escalations increase after the new refund policy was introduced?", "clarify", "ESC")
    add("threshold", "Which behaviours raise escalations by more than five percentage points?", "answer_threshold", "ESC",
        "why", extra={"threshold_target": "effect"})
    add("threshold", "Which industries have more than 20% refund requests?", "answer_threshold", "REF", "compare",
        extra={"threshold_target": "rate"})
    add("threshold", "Which behaviours do not affect churn threats?", "answer_threshold", "CHURN", "why",
        extra={"threshold_target": "effect"})
    for q, b in PROFILES:
        add("behaviour_profile", q, "answer_profile", None, "behaviour", behaviour=b)
    add("overview", f"What is happening in {IND_WORD[inds[0]]} calls?", "answer_overview", None, "overview",
        {"industry": [inds[0]]})
    add("overview", "What can you do?", "answer_help", None, "help")
    if has_risk:
        add("retention_risk", "Which customers are at risk of leaving?", "answer", "RISK", "why")
        add("retention_risk", f"How many {IND_WORD[inds[1 % len(inds)]]} calls had a retention risk?", "answer", "RISK",
            "how_often", {"industry": [inds[1 % len(inds)]]})
    esc_call, quiet_call = pick_calls(calls, labels)
    if esc_call:
        add("single_call", f"Why did call {esc_call} escalate?", "answer_call", "ESC", "call",
            {"call": [esc_call.lower()]})
    if quiet_call:
        add("single_call", f"What happened in call {quiet_call}?", "answer_call", None, "call", {"call": [quiet_call.lower()]})
    add("single_call", "What happened in call 00000000-0000-0000-0000-000000000000?", "clarify")


def build_query_set(corpus, library: pd.DataFrame, settings, labels: pd.DataFrame | None = None) -> dict:
    rng = np.random.default_rng(settings.seed + 5)
    calls = corpus.calls
    inds = [i for i in calls["opening_domain_vote"].astype(str).value_counts().index if i in IND_WORD][:6]
    brands = calls["brand"].astype(str).value_counts()
    brands = [b for b in brands.index if b not in ("none", "nan")]
    lib = library[(library["slice"] == "all") & ~library["negative_control"]]
    Q = []
    n = 0

    def add(*a, **k):
        nonlocal n
        n += 1
        Q.append(_q(f"q{n:03d}", *a, **k))

    unans = [("customer tier", "tier"), ("demographics", None), ("account age", "tenure_months"),
             ("plan or segment", "plan")]
    for k, e in enumerate(PRIMARY_EVENTS):
        w = EV_WORD[e]
        add("why", f"Why do customers {w[1]}?", "answer", e, "why")
        if k != 1:
            ind = inds[(k // 2) % len(inds)]
            add("why", f"What drives {w[0]} in {IND_WORD[ind]} calls?", "answer", e, "why", {"industry": [ind]})
        add("how_often", f"How often do customers {w[1]}?", "answer", e, "how_often")
        if k != 2:
            add("compare", f"Compare {w[0]} between {IND_WORD[inds[0]]} and {IND_WORD[inds[1 % len(inds)]]} calls", "answer",
                e, "compare")
            add("trend", f"How have {w[0]} changed over time?", "answer", e, "trend")
        if k != 1:
            add("what_to_change", f"How can we reduce {w[0]}?", "answer", e, "what_to_change")
            add("examples", f"Show me examples of calls where customers {w[1]}", "answer", e, "examples")
        rows = lib[lib["event"] == e]
        for r in rows.head(1).itertuples(index=False):
            b = BEHAVIOURS[r.behaviour]
            verb = "Are" if b.short.split()[-1].endswith("s") else "Is"
            add("effect_of", f"{verb} {b.short} linked to {w[0]}?", "answer", e, "effect_of", behaviour=r.behaviour)
        for r in rows.itertuples(index=False):
            b = BEHAVIOURS[r.behaviour]
            if r.level == "L3":
                verb = "increase" if r.att > 0 else "reduce"
                add("true_premise", f"Why do {b.short} {verb} {w[0]}?", "correct_premise", e, None,
                    behaviour=r.behaviour, extra={"premise_status": "supported"})
                wrong = "reduce" if r.att > 0 else "increase"
                add("false_presupposition", f"Why do {b.short} {wrong} {w[0]}?", "correct_premise", e, None,
                    behaviour=r.behaviour, extra={"premise_status": "contradicted"})
                break
        weak = rows[rows["level"].isin(["L2", "L1"])]
        if len(weak):
            r = weak.iloc[int(rng.integers(len(weak)))]
            b = BEHAVIOURS[r["behaviour"]]
            if k != 1:
                add("false_presupposition", f"Why does {b.short.rstrip('s')} cause {w[0]}?", "correct_premise", e, None,
                    behaviour=r["behaviour"], extra={"premise_status": "not_confirmed"})
            else:
                cause = "cause" if b.short.split()[-1].endswith("s") else "causes"
                add("leading", f"Isn't it true that {b.short} {cause} {w[0]}?", "correct_premise", e, None,
                    behaviour=r["behaviour"], extra={"premise_status": "not_confirmed"})
        for attr, col in unans[k:k + 1] + (unans[3:] if k == 0 else []):
            if attr == "customer tier" and col in calls.columns:
                add("unanswerable", f"Which tiers {w[1]} the most?", "answer_rank", e, "compare")
            elif attr == "customer tier":
                add("unanswerable", f"Which premium customers {w[1]} the most?", "refuse_part", e,
                    extra={"unsupported": "customer tier"})
            elif attr == "demographics":
                add("unanswerable", f"Do older customers {w[1]} more than young ones?", "refuse_part", e,
                    extra={"unsupported": "demographics"})
            elif attr == "account age" and col not in calls.columns:
                add("unanswerable", f"Do new customers {w[1]} more?", "refuse_part", e, extra={"unsupported": "account age"})
            elif attr == "plan or segment" and not {"plan", "segment"} & set(calls.columns):
                add("unanswerable", f"Why do customers on the premium plan {w[1]}?", "refuse_part", e,
                    extra={"unsupported": "plan or segment"})
        if k == 0:
            add("unsupported_filter", f"Why do calls whose reason for call mentions billing lead to {w[0]}?", "decline_filter",
                e, extra={"declined": "reason_for_call"})
        if brands and k == 1:
            small = brands[-1]
            add("tiny_subgroup", f"What drives {w[0]} for {small.title()} calls in {IND_WORD.get(inds[-1], inds[-1])} calls?",
                "answer_with_support_notice", e, "why", {"brand": [small]})
        add("product_improvement", PRODUCT_Q[e], "answer_topics", e, "issues")
        add("ranking", RANK_Q[e], "answer_rank", e, "compare")
    add("causal_failure", "Which apparent explanations are not supported by the causal checks?",
        "answer_causal_failure", None, "causal_failure")
    add("counterevidence", "Are there behaviours that occur frequently before an event but do not meaningfully distinguish event from non-event calls?",
        "answer_counterevidence", None, "counterevidence")
    add("ambiguous", "What tends to precede a complaint?", "clarify", extra={"unsupported": "complaint is not a labelled event"})
    add("ambiguous", "Why does this happen?", "clarify")
    add("ambiguous", "What about it?", "clarify")
    add("ambiguous", "Show me the numbers", "clarify")
    add("multi_hop", "Which industry has the highest escalation rate, and what drives escalations there?", "answer_rank",
        "ESC", "compare", extra={"explain_top": True})
    add("multi_hop", "Do the behaviours that raise escalations also raise churn threats?", "answer_shared", "ESC",
        "shared", extra={"events": ["ESC", "CHURN"]})
    add("multi_hop", "Is offering a solution linked to fewer refund requests and churn threats?", "answer_shared", "REF",
        "shared", behaviour="offer_solution", extra={"events": ["REF", "CHURN"]})
    add("out_of_scope", "Does sarcasm make customers threaten to cancel?", "refuse_part", "CHURN",
        extra={"unsupported": "unmeasured behaviour"})
    add("out_of_scope", "Does the customer's tone of voice predict escalations?", "refuse_part", "ESC",
        extra={"unsupported": "audio"})
    add("out_of_scope", "How long are customers kept on hold before they escalate?", "refuse_part", "ESC",
        extra={"unsupported": "call duration"})
    add("out_of_scope", "What would happen to refund requests if agents never refused anything?", "refuse_part", "REF",
        extra={"unsupported": "whole-call policy"})
    add("out_of_scope", "Do escalations lead to refund requests?", "answer_event_link", "ESC", "event_link",
        extra={"events": ["ESC", "REF"], "unsupported": "effects between events"})
    add("out_of_scope", "Which agent causes the most escalations?", "refuse_part", "ESC",
        extra={"unsupported": "agent identity"})
    add("out_of_scope", "What is the weather in London?", "clarify", extra={"unsupported": "location"})
    add_capability_queries(add, calls, labels, inds, settings)
    for text, expected, why in KNOWN_LIMITATIONS:
        add("known_limitation", text, expected["behaviour"], expected.get("event"), expected.get("question_type"),
            extra={k: v for k, v in expected.items() if k not in ("behaviour", "event", "question_type")} |
            {"limitation": why})
    kept = []
    for q in Q:
        ex = q["expected"]
        cell = (q["category"], ex.get("event"), json.dumps(ex.get("filters"), sort_keys=True), ex.get("focus_behaviour"))
        same = [k for k in kept if (k["category"], k["expected"].get("event"), json.dumps(k["expected"].get("filters"), sort_keys=True),
                                    k["expected"].get("focus_behaviour")) == cell]
        if all(rouge_l(q["question"], k["question"]) < 0.7 for k in same):
            kept.append(q)
    sessions = build_sessions(inds, brands, middle_date(calls), "tier" in calls.columns)
    return {"queries": kept, "sessions": sessions}


def build_sessions(inds, brands, day: str | None = None, has_tier: bool = False) -> list[dict]:
    i0, i1 = IND_WORD[inds[0]], IND_WORD[inds[1 % len(inds)]]
    typo0 = IND_TYPO.get(inds[0], (i0, inds[0]))[0]
    S = [
        [("Why do escalations happen in {i0} calls?".format(i0=i0), {"event": "ESC", "industry": [inds[0]], "route": "first"}),
         ("what about refunds?", {"event": "REF", "industry": [inds[0]], "route": "new_lookup"}),
         ("and across all industries?", {"event": "REF", "industry": [], "route": "refilter"}),
         ("explain the first factor", {"event": "REF", "industry": [], "route": "reuse", "question_type": "describe_factor"})],
        [("How often do customers threaten to cancel?", {"event": "CHURN", "industry": [], "route": "first"}),
         (f"only {i1} calls", {"event": "CHURN", "industry": [inds[1 % len(inds)]], "route": "refilter"}),
         ("why?", {"event": "CHURN", "industry": [inds[1 % len(inds)]], "route": "new_lookup", "question_type": "why"}),
         ("why?", {"event": "CHURN", "industry": [inds[1 % len(inds)]], "route": "reuse", "question_type": "why"}),
         ("what about escalations?", {"event": "ESC", "industry": [inds[1 % len(inds)]], "route": "new_lookup"})],
        [("What drives refund requests?", {"event": "REF", "industry": [], "route": "first"}),
         (f"what about {i0} and {i1} calls?", {"event": "REF", "industry": [inds[0], inds[1 % len(inds)]], "route": "refilter"}),
         ("what about that one?", {"event": "REF", "industry": [inds[0], inds[1 % len(inds)]], "route": "clarify"})],
        [("How can we reduce escalations?", {"event": "ESC", "industry": [], "route": "first"}),
         ("which tiers escalate the most?", {"event": "ESC", "industry": [], "route": "new_lookup", "question_type": "compare"})
         if has_tier else
         ("what about premium customers?", {"event": "ESC", "industry": [], "route": "reuse", "notice": "unsupported"}),
         ("and for refunds?", {"event": "REF", "industry": [], "route": "new_lookup"})],
        [(f"Why do {i0} customers threaten to leave?", {"event": "CHURN", "industry": [inds[0]], "route": "first"}),
         ("does empathy make a difference?", {"event": "CHURN", "industry": [inds[0]], "route": "new_lookup", "behaviour": "empathy"}),
         ("what about in general?", {"event": "CHURN", "industry": [], "route": "refilter"})],
        [("Why do refunds happen in {i1} calls?".format(i1=i1), {"event": "REF", "industry": [inds[1 % len(inds)]], "route": "first"}),
         ("also hotel calls", {"event": "REF", "industry": sorted({inds[1 % len(inds)], "hospitality"}), "route": "refilter"}),
         ("how often does that happen?", {"event": "REF", "industry": sorted({inds[1 % len(inds)], "hospitality"}), "route": "new_lookup",
                                          "question_type": "how_often"})],
        [("Which industry has the most refund requests?", {"event": "REF", "industry": [], "route": "first",
                                                           "question_type": "compare"}),
         (f"why in {i0} calls?", {"event": "REF", "industry": [inds[0]], "route": "new_lookup", "question_type": "why"})],
        [("Why do customers escalate?", {"event": "ESC", "industry": [], "route": "first"}),
         ("¿y los reembolsos?", {"event": "REF", "industry": [], "route": "new_lookup"}),
         (f"waht about refnds in {typo0} calls?", {"event": "REF", "industry": [inds[0]], "route": "refilter"})],
        [("Why do customers get frustrated?", {"event": None, "industry": [], "route": "first", "question_type": "behaviour"}),
         ("what about escalations?", {"event": "ESC", "industry": [], "route": "new_lookup", "question_type": "effect_of",
                                      "behaviour": "negative_emotion"})],
        [("Why do customers who were refused a refund escalate?", {"event": "ESC", "industry": [], "route": "first",
                                                                   "with_event": ["REF_DENIED"]}),
         (f"only {i1} calls", {"event": "ESC", "industry": [inds[1 % len(inds)]], "route": "refilter",
                               "with_event": ["REF_DENIED"]}),
         ("what about churn threats?", {"event": "CHURN", "industry": [inds[1 % len(inds)]], "route": "new_lookup",
                                        "with_event": ["REF_DENIED"]})],
        [("Why do customers escalate?", {"event": "ESC", "industry": [], "route": "first"}),
         ("tell me more about that call", {"event": "ESC", "industry": [], "route": "new_lookup", "question_type": "call"}),
         ("what about refunds?", {"event": "REF", "industry": [], "route": "new_lookup", "question_type": "call"}),
         (f"only {i0} calls", {"event": "REF", "industry": [inds[0]], "route": "new_lookup", "question_type": "why"})],
        [("Hello", {"event": None, "industry": [], "route": "first", "question_type": "help"}),
         ("give me an overview", {"event": None, "industry": [], "route": "new_lookup", "question_type": "overview"}),
         ("what about churn threats?", {"event": "CHURN", "industry": [], "route": "new_lookup", "question_type": "why"})],
    ]
    if day:
        S.append([("Did escalations increase after the new refund policy was introduced?",
                   {"event": "ESC", "industry": [], "route": "first", "question_type": "trend"}),
                  (f"it started on {day}", {"event": "ESC", "industry": [], "route": "new_lookup", "question_type": "trend",
                                            "change_date": day}),
                  ("what about refunds?", {"event": "REF", "industry": [], "route": "new_lookup", "question_type": "trend",
                                           "change_date": day})])
    return [{"id": f"s{i + 1:02d}", "turns": [{"question": q, "expected": ex} for q, ex in s]} for i, s in enumerate(S)]


def split_query_set(qs: dict, seed: int, test_share: float = 1 / 3) -> tuple[list, list]:
    rng = np.random.default_rng(seed)
    dev, test = [], []
    by_cat: dict[str, list] = {}
    for q in qs["queries"]:
        by_cat.setdefault(q["category"], []).append(q)
    for cat in sorted(by_cat):
        items = by_cat[cat]
        idx = rng.permutation(len(items))
        n_test = int(round(len(items) * test_share))
        for j, i in enumerate(idx):
            (test if j < n_test else dev).append(items[i])
    sess = qs["sessions"]
    idx = rng.permutation(len(sess))
    n_test = int(round(len(sess) * test_share))
    for j, i in enumerate(idx):
        (test if j < n_test else dev).append({"id": sess[i]["id"], "category": "session", "session": sess[i]["turns"]})
    return sorted(map(tag_query, dev), key=lambda x: x["id"]), sorted(map(tag_query, test), key=lambda x: x["id"])


def write_query_set(ws, qs: dict) -> dict:
    dev, test = split_query_set(qs, seed=20260930)
    pd_dev = ws.path("queries/queries_dev.jsonl")
    pd_test = ws.path("queries/queries_test.jsonl")
    pd_dev.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in dev), encoding="utf-8")
    pd_test.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in test), encoding="utf-8")
    sha = hashlib.sha256(pd_test.read_bytes()).hexdigest()
    def count(field):
        return dict(sorted({v: sum(q[field] == v for q in dev + test) for v in {q[field] for q in dev + test}}.items()))
    events = {}
    for q in dev + test:
        for ex in ([q["expected"]] if "expected" in q else [t["expected"] for t in q["session"]]):
            events[ex.get("event") or "none"] = events.get(ex.get("event") or "none", 0) + 1
    lock = {"n_dev": len(dev), "n_test": len(test), "test_sha256": sha,
            "distribution": {**{f: count(f) for f in META_FIELDS}, "category": count("category"),
                             "event_of_each_question": dict(sorted(events.items()))},
            "n_questions_total": sum(len(q.get("session", [])) or 1 for q in dev + test),
            "diversity": query_diversity(dev + test),
            "note": "commit queries_test.jsonl and this hash before any tuning; run the test queries once"}
    ws.write_json(lock, "queries/queries_lock.json")
    write_query_tables(ws, dev, test)
    return lock


def questions_of(items: list[dict]) -> list[tuple[str, str, dict, dict]]:
    out = []
    for q in items:
        if q.get("category") == "session":
            for i, t in enumerate(q["session"], 1):
                out.append((f"{q['id']}.{i}", t["question"], t["expected"], q))
        else:
            out.append((q["id"], q["question"], q["expected"], q))
    return out


def _entropy(values: list) -> float:
    counts = np.array(pd.Series(values).value_counts().to_numpy(), dtype=float)
    if len(counts) < 2:
        return 0.0
    p = counts / counts.sum()
    return float(-(p * np.log(p)).sum() / np.log(len(p)))


def query_diversity(items: list[dict]) -> dict:
    qs = questions_of(items)
    texts = [q.lower().split() for _, q, _, _ in qs]
    def distinct(n):
        grams = [tuple(t[i:i + n]) for t in texts for i in range(len(t) - n + 1)]
        return len(set(grams)) / len(grams) if grams else float("nan")
    pairs = [rouge_l(" ".join(a), " ".join(b)) for i, a in enumerate(texts) for b in texts[i + 1:]]
    combos = {json.dumps([ex.get("behaviour"), ex.get("event"), ex.get("question_type"), ex.get("filters") or
                          ({"industry": ex.get("industry")} if ex.get("industry") else {}), ex.get("focus_behaviour")],
                         sort_keys=True) for _, _, ex, _ in qs}
    return {"n_questions": len(qs), "distinct_1": distinct(1), "distinct_2": distinct(2),
            "mean_pairwise_rouge_l": float(np.mean(pairs)) if pairs else float("nan"),
            "max_pairwise_rouge_l": float(np.max(pairs)) if pairs else float("nan"),
            "distinct_expected_slots_share": len(combos) / len(qs) if qs else float("nan"),
            "evenness": {f: _entropy([q.get(f, "") for q in items]) for f in ("category",) + META_FIELDS},
            "evenness_event": _entropy([ex.get("event") or "none" for _, _, ex, _ in qs])}


def write_query_tables(ws, dev: list[dict], test: list[dict]) -> None:
    rows = []
    for split, items in (("dev", dev), ("test", test)):
        for qid, text, ex, item in questions_of(items):
            rows.append({"id": qid, "split": split, "category": item["category"], **{f: item.get(f, "") for f in META_FIELDS},
                         "question": text, "expected_behaviour": ex.get("behaviour") or ex.get("route", ""),
                         "expected_event": ex.get("event") or "", "expected_question_type": ex.get("question_type") or "",
                         "expected_filters": json.dumps(ex.get("filters") or ({"industry": ex["industry"]} if ex.get("industry") else {})),
                         "known_limitation": ex.get("limitation", "")})
    df = pd.DataFrame(rows)
    df.to_csv(ws.path("queries/queries.csv"), index=False)
    review = df[["id", "split", "category", "task", "difficulty", "query_type", "use_case", "question"]].copy()
    for col in ("realistic_1_5", "relevant_to_business_events_1_5", "category_and_tags_correct_y_n", "keep_edit_drop",
                "edited_question", "reviewer", "notes"):
        review[col] = ""
    review.to_csv(ws.path("queries/queries_review.csv"), index=False)


def load_jsonl(path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
