from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

DOMAINS = {
    "hospitality": dict(brands=["seaview lodge", "maple grand hotel"], intents=["Booking Errors", "Upgrade Requests", "Service Complaints"],
                        thing="reservation", id_phrase="booking id", id_fmt="hx {a} {b}", policy=0.3,
                        issues=["my room was double booked for the weekend", "the room type was not what i reserved",
                                "the housekeeping at the hotel was really poor"],
                        offers=["a free upgrade on your next stay", "a late checkout at no extra charge"]),
    "airline": dict(brands=["northstar airways", "bluejet air"], intents=["Delay Management", "Price Sensitivity", "Loyalty Program"],
                    thing="flight", id_phrase="booking reference", id_fmt="pnr q{a}{b}", policy=0.5,
                    issues=["my flight to denver was delayed by five hours", "my connecting flight was cancelled",
                            "the fare on my flight went up after i booked"],
                    offers=["priority rebooking on the next flight", "free seat selection on your next trip"]),
    "telecom": dict(brands=["linkwave internet", "cirrus mobile"], intents=["Network Outages", "Technical Support", "Plan Upgrades"],
                    thing="service", id_phrase="account number", id_fmt="ac {a} {b}", policy=0.0,
                    issues=["my internet has been down since last night", "the wifi keeps dropping every few minutes",
                            "the router you sent does not connect at all"],
                    offers=["a discount on next month's bill", "a technician visit tomorrow morning"]),
    "banking": dict(brands=["riverstone bank"], intents=["Fraud Alerts", "Fee Complaints", "Credit Limit Requests"],
                    thing="account", id_phrase="card number ending", id_fmt="ending {a}", policy=0.5,
                    issues=["there is a transaction on my credit card that i did not make",
                            "i was charged an overdraft fee i do not understand"],
                    offers=["a waiver of the late fee", "a temporary card sent by express mail"]),
    "insurance": dict(brands=["evergreen mutual"], intents=["Policy renewal", "Claims", "Customer trust"],
                      thing="policy", id_phrase="policy number", id_fmt="pl {a} {b}", policy=0.3,
                      issues=["my claim has been under review for three weeks", "my premium went up at renewal"],
                      offers=["a priority review of your claim", "a loyalty discount at renewal"]),
    "retail_ecommerce": dict(brands=["shopnest"], intents=["Delivery Delays", "Product Returns", "Order Status"],
                             thing="order", id_phrase="order number", id_fmt="sn {a} {b}", policy=0.0,
                             issues=["my package was not delivered after two weeks", "the blender i ordered arrived damaged"],
                             offers=["a free replacement with express delivery", "a prepaid return label today"]),
}
AGENT_NAMES = ["maya ortiz", "tom reyes", "lena park", "omar haddad", "grace okafor", "victor lin", "ivy chen", "raj mehta"]
CUSTOMER_NAMES = ["peter holm", "anika rao", "diego santos", "clara weiss", "felix moreau", "hana sato", "leo brandt",
                  "zara khan", "owen doyle", "mira novak", "jonas berg", "tara quinn"]
SUPERVISOR_NAMES = ["dana", "martin keller", "priscilla young"]

AGENT_PHRASES = {
    "empathy": "i understand how frustrating that must be",
    "refusal": ["unfortunately per our policy i'm not able to change that", "i'm afraid we cannot make an exception here"],
    "offer_solution": "what i can do is offer you {offer}",
    "hold_request": "let me check that for you one moment please",
    "nc_readback": "just to confirm that is {id_value} on the file",
    "nc_thanks_info": "thank you for that information",
}
AGENT_NEUTRAL = ["alright i have the account details in front of me now", "okay i am reviewing the notes on your file",
                 "right i can see the history here"]
CUSTOMER_NEUTRAL = ["okay go ahead", "yes that is correct", "alright", "sure no problem", "i see"]
ESC_LEXICON = "i want to speak to a supervisor right now"
ESC_PARAPHRASE = "get me someone above you right now"
REF_LEXICON = "i would like a refund for this"
REF_PARAPHRASE = "i just want my money returned"
CHURN_LEXICON = "honestly i'm thinking about switching to another provider"
CHURN_PARAPHRASE = "i am done with your company for good"
COMPETITOR = "another company offered me a better deal"
NEG_MILD = "i'm getting really frustrated with this"
NEG_STRONG = "this is ridiculous"
CONFUSION = "sorry i don't understand what you mean"
SEVERITY_PHRASE = {1: "and honestly i'm pretty annoyed about it", 2: "and this is completely unacceptable"}
SEVERITY_ID_SUFFIX = "and please hurry this is unacceptable"

ORACLE_BEHAVIOURS = ("refusal", "offer_solution", "hold_request", "nc_thanks_info")
AGENT_BEHAVIOURS = ("refusal", "offer_solution", "hold_request", "empathy", "nc_thanks_info", "nc_readback")
BEHAVIOUR_CUE = {"refusal": "refusal", "offer_solution": "offer_solution", "hold_request": "hold_request",
                 "empathy": "empathy", "nc_thanks_info": None, "nc_readback": None}


@dataclass
class Dynamics:
    base_F: float = 0.15
    s0_F: float = 0.30
    refusal_F: float = 0.35
    hold_F: float = 0.08
    offer_F: float = -0.25
    empathy_F: float = -0.05
    F_max: float = 1.6
    refusal_a: float = -2.2
    refusal_F_coef: float = 2.2
    offer_a: float = -1.0
    offer_F_coef: float = -0.8
    offer_late: float = 0.4
    hold_p: float = 0.15
    empathy_a: float = -1.4
    empathy_F_coef: float = 1.8
    thanks_a: float = -1.0
    thanks_F_coef: float = -1.5
    readback_a: float = -2.2
    readback_F_coef: float = 1.0
    esc_a: float = -5.0
    esc_F_coef: float = 3.4
    esc_after_refusal: float = 1.0
    ref_a: float = -3.8
    ref_F_coef: float = 1.8
    ref_late: float = 0.5
    churn_a: float = -4.6
    churn_F_coef: float = 2.4
    churn_competitor: float = 0.8
    p_competitor: float = 0.03
    accept_p: float = 0.35
    accept_F_max: float = 0.5
    max_turns: int = 30


@dataclass
class SimConfig:
    n_calls: int = 2500
    seed: int = 11
    p_named_speakers: float = 0.06
    p_truncate_closing: float = 0.02
    p_truncate_midcall: float = 0.01
    paraphrase_esc: float = 0.15
    esc_paraphrase_no_handoff: float = 0.5
    paraphrase_ref: float = 0.10
    paraphrase_churn: float = 0.10
    p_confusion: float = 0.06
    disfluency: float = 0.04
    oracle_reps: int = 80
    oracle_behaviours: tuple = ORACLE_BEHAVIOURS
    start: str = "2025-11-04 09:00:00"
    dynamics: Dynamics = field(default_factory=Dynamics)


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


class State:
    FIELDS = ("s0", "pol", "n_ref", "n_off", "n_hold", "n_emp", "last_refused", "competitor", "esc", "ref", "churn",
              "ended", "t")

    def __init__(self, n: int, s0: float, pol: float, t: int):
        self.s0 = np.full(n, float(s0))
        self.pol = np.full(n, float(pol))
        for f in ("n_ref", "n_off", "n_hold", "n_emp"):
            setattr(self, f, np.zeros(n))
        for f in ("last_refused", "competitor", "esc", "ref", "churn", "ended"):
            setattr(self, f, np.zeros(n, dtype=bool))
        self.t = np.full(n, int(t))

    def copy_to(self, n: int) -> "State":
        new = State.__new__(State)
        for f in self.FIELDS:
            v = getattr(self, f)
            setattr(new, f, np.repeat(v[:1], n).copy())
        return new


def frustration(st: State, P: Dynamics) -> np.ndarray:
    F = P.base_F + P.s0_F * st.s0 + P.refusal_F * st.n_ref + P.hold_F * st.n_hold + P.offer_F * st.n_off \
        + P.empathy_F * st.n_emp
    return np.clip(F, 0.0, P.F_max)


def agent_probs(st: State, P: Dynamics) -> dict:
    F = frustration(st, P)
    return {
        "refusal": _sigmoid(P.refusal_a + P.refusal_F_coef * F + st.pol),
        "offer_solution": _sigmoid(P.offer_a + P.offer_F_coef * F + P.offer_late * (st.t > 10)),
        "hold_request": np.full(F.shape, P.hold_p),
        "empathy": _sigmoid(P.empathy_a + P.empathy_F_coef * F),
        "nc_thanks_info": _sigmoid(P.thanks_a + P.thanks_F_coef * F),
        "nc_readback": _sigmoid(P.readback_a + P.readback_F_coef * F),
    }


def agent_step(st: State, P: Dynamics, rng: np.random.Generator, force: tuple | None = None) -> dict:
    probs = agent_probs(st, P)
    n = st.t.shape[0]
    draws = {b: rng.random(n) < probs[b] for b in AGENT_BEHAVIOURS}
    if force is not None:
        b, value = force
        draws[b] = np.full(n, bool(value))
    active = ~st.ended
    for b in draws:
        draws[b] &= active
    st.n_ref += draws["refusal"]
    st.n_off += draws["offer_solution"]
    st.n_hold += draws["hold_request"]
    st.n_emp += draws["empathy"]
    st.last_refused = np.where(active, draws["refusal"], st.last_refused)
    st.t = st.t + active
    return draws


def customer_step(st: State, P: Dynamics, rng: np.random.Generator) -> dict:
    n = st.t.shape[0]
    active = ~st.ended
    F = frustration(st, P)
    comp = (rng.random(n) < P.p_competitor) & active
    st.competitor |= comp
    u_esc, u_ref, u_churn, u_acc = rng.random(n), rng.random(n), rng.random(n), rng.random(n)
    esc_now = active & ~st.esc & (u_esc < _sigmoid(P.esc_a + P.esc_F_coef * F + P.esc_after_refusal * st.last_refused))
    ref_now = active & ~st.ref & ~esc_now & (u_ref < _sigmoid(P.ref_a + P.ref_F_coef * F + P.ref_late * (st.t > 12)))
    churn_now = active & ~st.churn & ~esc_now & ~ref_now & \
        (u_churn < _sigmoid(P.churn_a + P.churn_F_coef * F + P.churn_competitor * st.competitor))
    accept = active & ~esc_now & ~ref_now & ~churn_now & (st.n_off >= 1) & (F < P.accept_F_max) & (u_acc < P.accept_p)
    st.esc |= esc_now
    st.ref |= ref_now
    st.churn |= churn_now
    st.t = st.t + active
    st.ended |= accept | (active & (st.t >= P.max_turns))
    return {"esc": esc_now, "ref": ref_now, "churn": churn_now, "competitor": comp, "accept": accept, "F": F}


def oracle_event_probs(snapshot: State, P: Dynamics, force: tuple, reps: int, seed: int,
                       p_continue_after_esc: float) -> dict:
    st = snapshot.copy_to(reps)
    rng = np.random.default_rng(seed)
    hit = {e: np.zeros(reps, dtype=bool) for e in ("ESC", "REF", "CHURN")}
    first = True
    while (~st.ended).any():
        agent_step(st, P, rng, force=force if first else None)
        first = False
        ev = customer_step(st, P, rng)
        u_cont = rng.random(reps)
        hit["ESC"] |= ev["esc"]
        hit["REF"] |= ev["ref"]
        hit["CHURN"] |= ev["churn"]
        esc_now = ev["esc"] & ~st.ended
        st.ended |= esc_now & ~(u_cont < p_continue_after_esc)
    return {e: float(h.mean()) for e, h in hit.items()}


def _check_turn(text: str, party: str, must: set, must_not: set, behaviours=()) -> set:
    import re
    from . import cues
    from .definitions import BEHAVIOURS
    _, clean = cues.pipeline_text_views(text)
    fired = cues.cues_for_turn(clean, party)
    missing, extra = must - fired, fired & must_not
    if missing or extra:
        raise AssertionError(f"generated turn {text!r} ({party}): missing cues {missing}, unexpected cues {extra}")
    view = cues.cue_view(clean)
    for b in ("nc_thanks_info", "nc_readback"):
        hit = party == BEHAVIOURS[b].party and bool(re.search(BEHAVIOURS[b].detector[1], view))
        if hit != (b in behaviours):
            raise AssertionError(f"generated turn {text!r} ({party}): negative control {b} detector={hit}, "
                                 f"simulated={b in behaviours}")
    return fired


SIMULATED_CUES = {"refusal", "offer_solution", "hold_request", "empathy", "escalation_request", "refund", "churn_intent"}


class CallSimulator:
    def __init__(self, cfg: SimConfig):
        self.cfg = cfg
        self.P = cfg.dynamics
        self.rng = np.random.default_rng(cfg.seed)
        self.t0 = datetime.strptime(cfg.start, "%Y-%m-%d %H:%M:%S")

    def _disfluent(self, text: str) -> str:
        if self.cfg.disfluency <= 0:
            return text
        out = []
        for w in text.split():
            r = self.rng.random()
            if r < self.cfg.disfluency:
                out.append(self.rng.choice(["um", "uh", "you know"]))
            out.append(w)
        return " ".join(out)

    def _id_value(self, dom: dict) -> str:
        return dom["id_fmt"].format(a=int(self.rng.integers(1000, 9999)), b=int(self.rng.integers(100, 999)))

    def simulate_call(self, index: int) -> tuple[dict, dict]:
        cfg, P, rng = self.cfg, self.P, self.rng
        dname = list(DOMAINS)[int(rng.integers(len(DOMAINS)))]
        dom = DOMAINS[dname]
        brand = dom["brands"][int(rng.integers(len(dom["brands"])))]
        agent = AGENT_NAMES[int(rng.integers(len(AGENT_NAMES)))]
        cust = CUSTOMER_NAMES[int(rng.integers(len(CUSTOMER_NAMES)))]
        sup = SUPERVISOR_NAMES[int(rng.integers(len(SUPERVISOR_NAMES)))]
        s0 = int(rng.choice([0, 1, 2], p=[0.5, 0.35, 0.15]))
        issue = dom["issues"][int(rng.integers(len(dom["issues"])))]
        id_value = self._id_value(dom)
        turns: list[dict] = []

        def add(role: str, text: str, behaviours=(), event=None, must=(), must_not=SIMULATED_CUES):
            party = "Customer" if role == "customer" else "Agent"
            must = set(must)
            _check_turn(text, party, must, set(must_not) - must, behaviours)
            turns.append({"role": role, "text": text, "behaviours": sorted(behaviours), "event": event})

        add("agent", f"thank you for calling {brand} this is {agent} how can i help you today")
        early_ref = rng.random() < 0.06 + 0.06 * s0
        t1 = f"hi i'm calling because {issue}" + (f" {SEVERITY_PHRASE[s0]}" if s0 else "")
        if early_ref:
            t1 += " and i would like a refund"
        add("customer", t1, event="REF" if early_ref else None, must={"refund"} if early_ref else set())
        add("agent", f"thanks for explaining can you please give me your {dom['id_phrase']}")
        add("customer", f"sure it's {id_value}" + (f" {SEVERITY_ID_SUFFIX}" if s0 == 2 else ""))

        st = State(1, s0=s0, pol=dom["policy"], t=4)
        st.ref[:] = early_ref
        onsets = {"REF": 1} if early_ref else {}
        oracle_rows = []
        first_seen: set = set()
        handoff_pending, paraphrased_esc, sup_mode = False, False, False
        truth_paraphrase = {}

        while True:
            prefix = None
            if handoff_pending:
                handoff_pending = False
                if paraphrased_esc and rng.random() < cfg.esc_paraphrase_no_handoff:
                    prefix = "there is no one else available to take the call right now"
                else:
                    add("agent", "okay let me get my supervisor for you please hold", behaviours=["hold_request"],
                        must={"hold_request"}, must_not=SIMULATED_CUES - {"hold_request"})
                    sup_mode = True
                    if "ESC" not in onsets:
                        onsets["ESC"] = len(turns) - 1
                    break
            k = len(turns)
            snapshot = st.copy_to(1)
            draws = agent_step(st, P, rng)
            sampled = [b for b in AGENT_BEHAVIOURS if bool(draws[b][0])]
            p_cont = cfg.paraphrase_esc * cfg.esc_paraphrase_no_handoff
            for b in cfg.oracle_behaviours:
                if b in sampled and b not in first_seen:
                    seed = int(rng.integers(2**31))
                    m1 = oracle_event_probs(snapshot, P, (b, True), cfg.oracle_reps, seed, p_cont)
                    m0 = oracle_event_probs(snapshot, P, (b, False), cfg.oracle_reps, seed, p_cont)
                    oracle_rows.append({"behaviour": b, "turn_id": k, "p_treated": m1, "p_untreated": m0,
                                        "prior": {"ESC": bool(snapshot.esc[0]), "REF": bool(snapshot.ref[0]),
                                                  "CHURN": bool(snapshot.churn[0])}})
            first_seen.update(sampled)
            parts = []
            for b in ["empathy", "refusal", "offer_solution", "hold_request", "nc_readback", "nc_thanks_info"]:
                if b in sampled:
                    phrase = AGENT_PHRASES[b]
                    if isinstance(phrase, list):
                        phrase = phrase[int(rng.integers(len(phrase)))]
                    parts.append(phrase.format(offer=dom["offers"][int(rng.integers(len(dom["offers"])))],
                                               id_value=self._id_value(dom)))
            if prefix is not None:
                parts.insert(0, prefix)
            if not parts:
                parts.append(AGENT_NEUTRAL[int(rng.integers(len(AGENT_NEUTRAL)))])
            must = {BEHAVIOUR_CUE[b] for b in sampled if BEHAVIOUR_CUE[b]}
            add("agent", self._disfluent(" ".join(parts)), behaviours=sampled, must=must)

            ev = customer_step(st, P, rng)
            pieces, event, must = [], None, set()
            if ev["esc"][0]:
                paraphrased_esc = rng.random() < cfg.paraphrase_esc
                pieces.append(ESC_PARAPHRASE if paraphrased_esc else ESC_LEXICON)
                event, handoff_pending = "ESC", True
                must = set() if paraphrased_esc else {"escalation_request"}
                truth_paraphrase["ESC"] = paraphrased_esc
            elif ev["ref"][0]:
                para = rng.random() < cfg.paraphrase_ref
                pieces.append(REF_PARAPHRASE if para else REF_LEXICON)
                event, must = "REF", (set() if para else {"refund"})
                truth_paraphrase["REF"] = para
            elif ev["churn"][0]:
                para = rng.random() < cfg.paraphrase_churn
                pieces.append(CHURN_PARAPHRASE if para else CHURN_LEXICON)
                event, must = "CHURN", (set() if para else {"churn_intent"})
                truth_paraphrase["CHURN"] = para
            elif ev["accept"][0]:
                pieces.append("okay that works for me thank you")
            else:
                pieces.append(CUSTOMER_NEUTRAL[int(rng.integers(len(CUSTOMER_NEUTRAL)))])
            if ev["competitor"][0]:
                pieces.append(COMPETITOR)
            F_now = float(ev["F"][0])
            if not ev["accept"][0]:
                if F_now > 0.9:
                    pieces.append(NEG_STRONG)
                elif F_now > 0.6:
                    pieces.append(NEG_MILD)
                if rng.random() < cfg.p_confusion:
                    pieces.append(CONFUSION)
            if event and event not in onsets:
                onsets[event] = len(turns)
            add("customer", self._disfluent(" ".join(pieces)), event=event, must=must)
            if bool(st.ended[0]):
                break

        if sup_mode:
            add("supervisor", f"hi {cust.split()[0]} this is {sup} the supervisor i've reviewed your {dom['thing']}",
                must_not=SIMULATED_CUES)
            add("customer", "okay thank you for taking my call")
            add("supervisor", f"i apologize for the trouble i can offer you {dom['offers'][0]}",
                behaviours=["offer_solution"], must={"offer_solution"}, must_not=SIMULATED_CUES - {"offer_solution"})
            add("customer", "okay that works thank you")
            add("supervisor", f"thank you for calling {brand} have a great day")
            add("customer", "bye")
        else:
            add("agent", "you're welcome is there anything else i can help you with")
            add("customer", "no that's all thank you")
            add("agent", f"thank you for calling {brand} have a great day")
            add("customer", "bye")

        n_full = len(turns)
        truncated = None
        u = rng.random()
        if u < cfg.p_truncate_midcall and n_full > 10:
            cut = int(rng.integers(8, n_full - 2))
            turns, truncated = turns[:cut], "midcall"
        elif u < cfg.p_truncate_midcall + cfg.p_truncate_closing:
            turns, truncated = turns[:-4], "closing"
        named = rng.random() < cfg.p_named_speakers
        labels = {"agent": agent.title() if named else "Agent", "customer": cust.title() if named else "Customer",
                  "supervisor": sup.title() if named else "Supervisor"}
        tid = str(uuid.UUID(int=int(rng.integers(2**63)) << 64 | int(rng.integers(2**63))))
        when = self.t0 + timedelta(minutes=int(rng.integers(0, 8 * 24 * 60)))
        rec = {
            "transcript_id": tid,
            "time_of_interaction": when.strftime("%Y-%m-%d %H:%M:%S"),
            "domain": "Insurance",
            "intent": dom["intents"][int(rng.integers(len(dom["intents"])))],
            "reason_for_call": f"Customer {cust.title()} called {brand.title()} about their {dom['thing']}.",
            "conversation": [{"speaker": labels[t["role"]], "text": t["text"]} for t in turns],
        }
        n_kept = len(turns)
        visible = {e: o for e, o in onsets.items() if o < n_kept}
        truth = {
            "transcript_id": tid, "domain": dname, "brand": brand, "s0": s0, "named_speakers": named,
            "truncated": truncated, "n_turns": n_kept, "n_turns_full": n_full,
            "roles": [t["role"] for t in turns],
            "onsets_true": onsets, "onsets_visible": visible, "paraphrase": truth_paraphrase,
            "behaviours": {str(i): t["behaviours"] for i, t in enumerate(turns) if t["behaviours"]},
            "oracle": oracle_rows,
        }
        return rec, truth


def simulate(cfg: SimConfig | None = None) -> tuple[list[dict], list[dict]]:
    cfg = cfg or SimConfig()
    sim = CallSimulator(cfg)
    records, truth = [], []
    for i in range(cfg.n_calls):
        r, t = sim.simulate_call(i)
        records.append(r)
        truth.append(t)
    return records, truth


def write_corpus(out_path: str | Path, cfg: SimConfig | None = None) -> tuple[Path, Path]:
    cfg = cfg or SimConfig()
    records, truth = simulate(cfg)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    truth_path = out_path.with_name(out_path.stem + "_truth.json")
    cfg_dict = asdict(cfg)
    truth_path.write_text(json.dumps({"config": cfg_dict, "calls": truth}, ensure_ascii=False), encoding="utf-8")
    return out_path, truth_path


def oracle_att(truth_calls: list[dict], behaviour: str, call_ids: set | None = None, event: str = "ESC",
               clean: bool = False) -> dict:
    others = [e for e in ("ESC", "REF", "CHURN") if e != event]
    diffs = []
    for t in truth_calls:
        if call_ids is not None and t["transcript_id"] not in call_ids:
            continue
        for r in t["oracle"]:
            if r["behaviour"] != behaviour or r["prior"][event]:
                continue
            if clean and any(r["prior"][o] for o in others):
                continue
            diffs.append(r["p_treated"][event] - r["p_untreated"][event])
    if not diffs:
        return {"att": float("nan"), "n": 0, "se_mc": float("nan")}
    d = np.asarray(diffs)
    return {"att": float(d.mean()), "n": int(d.size), "se_mc": float(d.std(ddof=1) / np.sqrt(d.size)) if d.size > 1 else float("nan")}

GOLD_SUBTYPE = {"ESC": "customer_request", "REF": "customer_request", "CHURN": "switch"}


def fill_gold_labels(sample, truth_calls: list[dict], template_csv: str | Path, out_csv: str | Path,
                     onset_noise: float = 0.03, presence_noise: float = 0.005, seed: int = 0) -> Path:
    import pandas as pd
    by_id = {t["transcript_id"]: t for t in truth_calls}
    rng = np.random.default_rng(seed)
    template = pd.read_csv(template_csv, dtype=str).fillna("")
    double = set(sample.loc[sample["double_coded"], "transcript_id"])
    events = ("ESC", "REF", "CHURN")

    def row(tid, ann, lab):
        r = {"transcript_id": tid, "annotator": ann}
        for e in events:
            on = lab[e]
            r[f"{e}_present"] = "yes" if on >= 0 else "no"
            r[f"{e}_onset"] = str(on) if on >= 0 else ""
            r[f"{e}_subtype"] = GOLD_SUBTYPE[e] if on >= 0 else ""
        return r

    rows, done = [], set()
    for tid in template["transcript_id"]:
        if tid in done:
            continue
        done.add(tid)
        t = by_id[tid]
        n = int(t["n_turns"])
        true = {e: int(t["onsets_visible"].get(e, -1)) for e in events}
        labs = {}
        for ann in (["A", "B"] if tid in double else ["A"]):
            lab = {}
            for e, on in true.items():
                o = on
                if o >= 0 and rng.random() < onset_noise:
                    o = int(min(max(0, o + rng.choice([-1, 1])), n - 1))
                if rng.random() < presence_noise:
                    o = -1 if o >= 0 else int(rng.integers(min(4, n - 1), n))
                lab[e] = o
            labs[ann] = lab
            rows.append(row(tid, ann, lab))
        if tid in double and labs["A"] != labs["B"]:
            rows.append(row(tid, "ADJ", true))
    out_csv = Path(out_csv)
    pd.DataFrame(rows, columns=list(template.columns)).to_csv(out_csv, index=False)
    return out_csv


def fill_precision_sheets(folder: str | Path, truth_calls: list[dict]) -> list[Path]:
    import pandas as pd
    by_id = {t["transcript_id"]: t for t in truth_calls}
    judged = set(AGENT_BEHAVIOURS)
    out = []
    for p in sorted(Path(folder).glob("precision_*.csv")):
        df = pd.read_csv(p, dtype=str).fillna("")
        b = p.stem[len("precision_"):]
        if b not in judged:
            continue
        verdicts = []
        for uid in df["turn_uid"]:
            tid, _, turn = uid.rpartition(":")
            beh = by_id[tid]["behaviours"].get(str(int(turn)), [])
            verdicts.append("yes" if b in beh else "no")
        df["correct"] = verdicts
        df.to_csv(p, index=False)
        out.append(p)
    return out
