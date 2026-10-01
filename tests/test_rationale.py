import numpy as np
import pandas as pd

from crest.answer import Artifacts
from crest.rationale import RationaleBuilder, with_frequency


def _toy():
    rng = np.random.default_rng(0)
    rows, calls, onsets = [], [], {}
    for c in range(80):
        tid = f"c{c:03d}"
        event = c < 40
        n = 12
        calls.append({"transcript_id": tid, "split": "test", "opening_domain_vote": "airline", "brand": "x", "n_turns": n})
        onsets[tid] = 9 if event else -1
        for k in range(n):
            party = "Customer" if k % 2 else "Agent"
            refusal = party == "Agent" and ((event and k == 8) or (not event and k == 8 and rng.random() < 0.2))
            offer = party == "Agent" and k == 6 and not event
            rows.append({"call_idx": c, "turn_id": k, "party": party, "refusal": refusal, "offer_solution": offer,
                         "negative_emotion": party == "Customer" and k == 7})
    turns = pd.DataFrame(rows)
    for b in ("hold_request", "hold_return", "apology", "empathy", "agent_transfer", "confusion", "repeat_contact",
              "issue_persistence", "repeat_question", "hesitation", "competitor_mention", "nc_thanks_info", "nc_readback"):
        turns[b] = False
    text = {}
    for r in turns.itertuples(index=False):
        tid = f"c{r.call_idx:03d}"
        text[f"{tid}:{r.turn_id}"] = ("i'm calling because my flight was cancelled and i need help today" if r.turn_id == 1 else
                                     "i want to speak to a supervisor because you keep saying no" if r.turn_id == 9 else
                                     "i'm afraid that is against our policy" if r.turn_id == 8 else "okay thank you")
    labels = pd.DataFrame({"transcript_id": list(onsets), "ESC_onset": list(onsets.values()),
                           "ESC_subtype": ["customer_request" if v >= 0 else "" for v in onsets.values()]}).set_index("transcript_id")
    return Artifacts(library=pd.DataFrame(), calls=pd.DataFrame(calls), labels=labels, turn_text=pd.Series(text), turns=turns)


def test_rationale_finds_what_comes_before_the_event_and_what_is_missing():
    art = _toy()
    rb = RationaleBuilder(art)
    r = rb.compute("ESC", np.ones(80, dtype=bool), "all")
    assert not r["too_few"] and r["n_event_calls"] == 40
    top = r["precursors"][0]
    assert top["behaviour"] == "refusal" and top["share_event"] == 1.0 and top["share_other"] < 0.5
    assert r["contrast"][0]["behaviour"] == "offer_solution"
    assert r["who"]["subtype"] == "customer_request" and r["who"]["share"] == 1.0
    roles = [s["role"] for s in r["chain"]]
    assert roles == ["problem", "before", "event"]
    assert all(art.turn_text[s["turn_uid"]].startswith(s["quote"]) for s in r["chain"])
    assert r["reasons"] and "because" in r["reasons"][0]["quote"]
    few = rb.compute("ESC", np.arange(80) < 10, "ten")
    assert few["too_few"] and few["n_event_calls"] == 10


def test_frequency_words():
    assert with_frequency("the agent refused a request", 0.7) == "the agent usually refused a request"
    assert with_frequency("the customer was confused", 0.35) == "the customer was often confused"
    assert with_frequency("the customer said the problem was still not fixed", 0.1) == \
        "the customer sometimes said the problem was still not fixed"


def test_answers_lead_with_a_cited_rationale(engine):
    for q in ("Why do customers escalate?", "What drives refund requests in hotel calls?", "How can we reduce churn threats?"):
        ans, _ = engine.ask(q)
        kinds = [s["kind"] for s in ans["sentences"]]
        assert not ans["dropped"] and not ans["degraded"], (q, [d["text"] for d in ans["dropped"]])
        assert kinds.index("rationale") < kinds.index("count"), (q, kinds)
        assert ans["text"].startswith("Why, from the conversations") or ans["sentences"][0]["kind"] in ("notice", "premise")
        quotes = [s for s in ans["sentences"] if s["kind"] == "quote"]
        assert quotes and all(s["turn_uids"] for s in quotes)
    for q in ("How often do customers ask for refunds?", "Which industry has the highest escalation rate?",
              "Compare escalations between hotel and airline calls", "Are empathy statements linked to refund requests?"):
        ans, _ = engine.ask(q)
        assert not ans["dropped"], (q, [d["text"] for d in ans["dropped"]])
        assert "rationale" in {s["kind"] for s in ans["sentences"]}, (q, ans["text"])
