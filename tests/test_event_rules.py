import numpy as np
import pandas as pd

from crest.cues import CUE_NAMES, cues_for_turn, make_clean_text
from crest.events import lexicon_labels
from crest.io import fill_domain_from_brand


class _Corpus:
    def __init__(self, calls):
        rows = []
        for ci, turns in enumerate(calls):
            for k, (speaker, text) in enumerate(turns):
                party = "Customer" if speaker == "Customer" else "Agent"
                clean = make_clean_text(text)
                cues = cues_for_turn(clean, party)
                rows.append({"transcript_id": f"c{ci}", "turn_id": k, "speaker": speaker, "party": party, "text": text,
                             "text_clean": clean, "call_idx": ci, **{f"cue_{n}": n in cues for n in CUE_NAMES}})
        self.turns = pd.DataFrame(rows)
        self.call_ids = np.array([f"c{i}" for i in range(len(calls))])
        self.n_calls = len(calls)
        n = np.array([len(c) for c in calls])
        self.call_start = np.concatenate([[0], np.cumsum(n)[:-1]]).astype(np.int64)


def _labels(*calls):
    return lexicon_labels(_Corpus(list(calls)))


OPEN = [("Agent", "thanks for calling how can i help you today"), ("Customer", "hi my room booking was wrong")]


def test_escalation_needs_a_handoff_a_request_or_an_accepted_offer():
    lab = _labels(
        OPEN + [("Agent", "acknowledging issues quickly helps us cut down on escalations overall")],
        OPEN + [("Agent", "good news no escalation was needed today")],
        OPEN + [("Agent", "would you like me to escalate this to my supervisor"), ("Customer", "yes please")],
        OPEN + [("Agent", "i can escalate this to a manager if you want"), ("Customer", "no that is not necessary")],
        OPEN + [("Agent", "i'll escalate this to management right away")],
        OPEN + [("Agent", "i'll escalate this to housekeeping for you")],
        OPEN + [("Customer", "can i talk to someone above you please")],
        OPEN + [("Supervisor", "hello this is the supervisor how can i help")],
        OPEN + [("Agent", "i can also escalate this to a supervisor if necessary"), ("Customer", "what would they do")])
    on, sub = lab["ESC_onset"].tolist(), lab["ESC_subtype"].tolist()
    assert on == [-1, -1, 2, -1, 2, -1, 2, 2, -1]
    assert sub[2] == "agent_handoff" and sub[6] == "customer_request"


def test_churn_includes_soft_and_named_competitor_threats_but_not_prospects():
    lab = _labels(
        OPEN + [("Customer", "honestly i'm thinking about moving to marriott after this")],
        OPEN + [("Customer", "if this is not fixed i'd rather go with another hotel")],
        OPEN + [("Customer", "i might just look elsewhere")],
        OPEN + [("Customer", "this really makes me question my loyalty to you")],
        OPEN + [("Customer", "i'm thinking about switching from hilton to your hotels")],
        OPEN + [("Customer", "how do your rates compare to hilton")],
        OPEN + [("Customer", "i don't want to switch to another provider")],
        OPEN + [("Customer", "i almost switched to marriott last year")],
        OPEN + [("Customer", "will this affect my loyalty points")],
        OPEN + [("Customer", "i want to cancel my membership")])
    assert (lab["CHURN_onset"] >= 0).tolist() == [True, True, True, True, False, False, False, False, False, True]


def test_unknown_industry_is_filled_from_a_clear_brand_majority():
    votes = pd.Series(["hospitality"] * 12 + ["unknown"] * 3 + ["airline"] * 5 + ["telecom"] * 6 + ["unknown"] * 2)
    brands = pd.Series(["seaview"] * 15 + ["mixed"] * 5 + ["mixed"] * 6 + ["mixed"] * 2)
    out, n = fill_domain_from_brand(votes, brands)
    assert n == 3 and (out[12:15] == "hospitality").all() and (out[26:] == "unknown").all()
