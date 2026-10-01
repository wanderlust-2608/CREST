from __future__ import annotations

import argparse
import json
import random
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path

AGENT_NAMES = ["maya ortiz", "tom reyes", "lena park", "omar haddad", "grace okafor",
               "victor lin", "nina petrova", "sam whitfield", "ivy chen", "raj mehta"]
CUSTOMER_NAMES = ["peter holm", "anika rao", "diego santos", "clara weiss", "felix moreau",
                  "hana sato", "leo brandt", "zara khan", "owen doyle", "mira novak",
                  "jonas berg", "tara quinn", "ellis ford", "noor aziz", "kai lund"]
SUPERVISOR_NAMES = ["rob", "dana", "martin keller", "priscilla young"]

DOMAINS = {
    "hospitality": {
        "brands": ["seaview lodge", "maple grand hotel", "harbor point resorts"],
        "intents": ["Booking Errors", "Upgrade Requests", "Cancellation Policies",
                    "Service Complaints", "Loyalty Program"],
        "thing": "reservation", "id_phrase": "booking id", "id_fmt": "hx {a} {b}",
        "issue": ["my room was double booked", "the room type was not what i reserved",
                  "i want to upgrade my room for my stay next week",
                  "the cancellation fee on my reservation seems wrong",
                  "the housekeeping and noise at the hotel were really bad"],
        "detail": ["i checked in on friday and the front desk had no record",
                   "it is a three night stay at the downtown property",
                   "the amenities listed on the site were not available"],
        "fix": ["i have moved you to a deluxe room at no extra charge",
                "i have corrected the reservation and sent a new confirmation",
                "i have waived the cancellation fee on this booking"],
    },
    "airline": {
        "brands": ["northstar airways", "bluejet air"],
        "intents": ["Delay Management", "Refund Policy", "Loyalty Program", "Price Sensitivity"],
        "thing": "flight", "id_phrase": "booking reference", "id_fmt": "pnr q{a}{b}",
        "issue": ["my flight to denver was delayed by five hours",
                  "my connecting flight was cancelled and i missed my meeting",
                  "the fare on my flight went up after i booked",
                  "i want to use my frequent flyer miles for a seat upgrade"],
        "detail": ["i am at the airport right now near gate twelve",
                   "the boarding pass still shows the old departure time",
                   "my baggage was checked through to the final destination"],
        "fix": ["i have rebooked you on the next flight departing at six pm",
                "i have added a travel credit to your account for the delay",
                "i have confirmed your seat on the earlier flight"],
    },
    "telecom": {
        "brands": ["linkwave internet", "cirrus mobile"],
        "intents": ["Network Outages", "Technical Support", "Churn Prediction", "Plan Upgrades"],
        "thing": "service", "id_phrase": "account number", "id_fmt": "ac {a} {b}",
        "issue": ["my internet has been down since last night",
                  "the wifi keeps dropping every few minutes",
                  "i want to change my data plan to something cheaper",
                  "the router you sent does not connect at all"],
        "detail": ["i already restarted the modem twice",
                   "the signal is weak in every room of the house",
                   "i pay for the three hundred megabit plan"],
        "fix": ["i have reset the line from our side and the connection is back",
                "i have scheduled a technician visit for tomorrow morning",
                "i have moved you to the unlimited data plan with a discount"],
    },
    "banking": {
        "brands": ["riverstone bank"],
        "intents": ["Fraud Alerts", "Fee Complaints", "Credit Limit Requests", "Loan Application"],
        "thing": "account", "id_phrase": "card number ending", "id_fmt": "ending {a}",
        "issue": ["there is a transaction on my credit card that i did not make",
                  "i was charged an overdraft fee i do not understand",
                  "i want to increase the credit limit on my card",
                  "i applied for a personal loan and have not heard back"],
        "detail": ["the charge was from an online store i have never used",
                   "my checking account had enough balance that day",
                   "my credit score went up this year"],
        "fix": ["i have blocked the card and opened a fraud dispute",
                "i have reversed the overdraft fee on your checking account",
                "i have submitted the credit limit increase for review"],
    },
    "insurance": {
        "brands": ["evergreen mutual"],
        "intents": ["Policy renewal", "Claims & refunds", "Customer trust"],
        "thing": "policy", "id_phrase": "policy number", "id_fmt": "pl {a} {b}",
        "issue": ["my claim has been under review for three weeks",
                  "my premium went up at renewal and nobody told me",
                  "i want to understand the deductible on my home insurance",
                  "my claim was denied and i do not know why"],
        "detail": ["i sent the documents to the adjuster twice",
                   "i have been a policyholder since twenty eighteen",
                   "the coverage letter says something different"],
        "fix": ["i have flagged the claim for priority review",
                "i have applied a loyalty discount to your premium",
                "i have sent you the updated coverage summary"],
    },
    "retail_ecommerce": {
        "brands": ["shopnest"],
        "intents": ["Delivery Delays", "Product Returns", "Replacement vs Refund"],
        "thing": "order", "id_phrase": "order number", "id_fmt": "sn {a} {b}",
        "issue": ["my order still has not been delivered after two weeks",
                  "the blender i ordered arrived damaged",
                  "i want to return the jacket because it does not fit",
                  "the tracking number says delivered but there is no package"],
        "detail": ["the courier left a note but nothing was at the door",
                   "the item was a gift so i need it by friday",
                   "i kept the original box and the receipt"],
        "fix": ["i have shipped a replacement with express delivery",
                "i have emailed you a prepaid return label",
                "i have opened a trace with the courier for your package"],
    },
}
SCENARIOS = ["smooth", "smooth", "escalation", "refund", "churn", "confusion", "hold"]
FILLERS = ["um", "uh", "like", "you know", "i mean"]


def disfluent(text: str, rng: random.Random, rate: float = 0.12) -> str:
    out = []
    for w in text.split():
        if not w.replace("'", "").isalnum():
            out.append(w)
            continue
        r = rng.random()
        if r < rate:
            out.append(rng.choice(FILLERS))
        elif r < rate + 0.03:
            out.append(w)
        out.append(w)
    return " ".join(out)


def curly(text: str, rng: random.Random) -> str:
    return text.replace("'", "’") if rng.random() < 0.3 else text


def make_id(rng: random.Random, fmt: str) -> str:
    return fmt.format(a=rng.randint(1000, 9999), b=rng.randint(100, 999))


def build_dialogue(rng: random.Random, dom: dict, brand: str, agent: str, cust: str,
                   scenario: str, sup_name: str):
    first_agent = agent.split()[0]
    first_cust = cust.split()[0]
    thing, idp = dom["thing"], dom["id_phrase"]
    turns = [
        ("agent", f"thank you for calling {brand} this is {agent} how can i help you today"),
        ("customer", f"hi {first_agent} this is {cust} i'm calling because {rng.choice(dom['issue'])}"),
        ("agent", f"i'm sorry to hear that {first_cust} can you please give me your {idp}"),
        ("customer", f"sure it's {make_id(rng, dom['id_fmt'])}"),
        ("agent", "thank you let me pull that up for you one moment please"),
        ("agent", f"okay i can see your {thing} here can you tell me a bit more about what happened"),
        ("customer", rng.choice(dom["detail"])),
    ]
    if scenario == "smooth":
        turns += [
            ("agent", f"thanks for explaining that {first_cust} {rng.choice(dom['fix'])}"),
            ("customer", "oh great that's really helpful thank you"),
            ("agent", "you're welcome is there anything else i can help you with"),
        ]
    elif scenario == "escalation":
        turns += [
            ("customer", "honestly this is the third time i've called about this and i'm really frustrated"),
            ("agent", "i understand how frustrating that must be unfortunately per our policy i'm not able to change that"),
            ("customer", "that's unacceptable i want to speak to a supervisor right now"),
            ("agent", "i completely understand let me escalate this to my supervisor please hold *transferring call*"),
            ("supervisor", f"hi {first_cust} this is {sup_name} the supervisor i've reviewed your {thing}"),
            ("customer", "finally someone who can actually help me"),
            ("supervisor", f"i apologize for the trouble {rng.choice(dom['fix'])}"),
            ("customer", "okay that works thank you for fixing it"),
        ]
    elif scenario == "refund":
        turns += [
            ("customer", "i would like a full refund for this please"),
            ("agent", "i can offer a partial refund or a credit toward your next purchase"),
            ("customer", "i'd rather have the money back to my card"),
            ("agent", "understood i have processed the refund and you'll see it in five business days"),
        ]
    elif scenario == "churn":
        turns += [
            ("customer", "to be honest i'm thinking about switching to another provider they offered me a better price"),
            ("agent", "i'd hate to lose you as a customer what i can do is offer a discount for the next six months"),
            ("customer", "i guess i'm not sure maybe i'll just cancel my account"),
            ("agent", "i understand let me send you the offer by email so you can decide"),
        ]
    elif scenario == "confusion":
        turns += [
            ("agent", "that falls under the secondary adjustment window of the terms"),
            ("customer", "sorry i don't understand what you mean by that"),
            ("agent", "no problem let me explain it more simply"),
            ("customer", "can you repeat that part about the dates"),
            ("agent", f"of course {rng.choice(dom['fix'])}"),
        ]
    elif scenario == "hold":
        turns += [
            ("agent", "let me check with the team please hold for a moment"),
            ("customer", "sure i'll wait"),
            ("agent", "thank you for holding i really appreciate your patience"),
            ("agent", f"{rng.choice(dom['fix'])}"),
            ("customer", "alright thanks"),
        ]
    turns += [
        ("customer", "no that's all thank you"),
        ("agent", f"thank you for calling {brand} have a great day"),
        ("customer", "bye"),
    ]
    return turns


ANNOTATION_STYLES = [
    ("- Key Event", "customer asked for a supervisor after the policy explanation"),
    ("[Call Summary", "the agent resolved the issue and the customer was satisfied"),
    ("(Note", "the customer seemed frustrated after the long hold"),
    ("Key Events", "refund processed at the end of the call"),
    ("Domain", "insurance"),
    ("Outcome", "resolved"),
    ("*[System Note", "no escalation occurred throughout the call"),
    ("Student", "mhm"),
]


def generate(n: int, seed: int = 7):
    rng = random.Random(seed)
    start = datetime(2025, 11, 4, 9, 0, 0)
    records, truth = [], []
    for i in range(n):
        dname = rng.choice(list(DOMAINS))
        dom = DOMAINS[dname]
        brand = rng.choice(dom["brands"])
        agent = rng.choice(AGENT_NAMES)
        cust = rng.choice(CUSTOMER_NAMES)
        scenario = rng.choice(SCENARIOS)
        intent = rng.choice(dom["intents"])
        sup_name = rng.choice(SUPERVISOR_NAMES)
        canon = build_dialogue(rng, dom, brand, agent, cust, scenario, sup_name)

        named = rng.random() < 0.08
        sup_label_is_name = named or rng.random() < 0.3
        label_for = {
            "agent": agent.title() if named else "Agent",
            "customer": cust.title() if named else "Customer",
            "supervisor": sup_name.title() if sup_label_is_name else "Supervisor",
        }
        if not named and rng.random() < 0.01:
            label_for["customer"] = "Customer'S"
        turns = [{"speaker": label_for[r], "text": curly(disfluent(t, rng), rng)} for r, t in canon]
        expected_roles = [r for r, _ in canon]

        if named and rng.random() < 0.3:
            idx = next(k for k in range(3, len(turns)) if expected_roles[k] == "agent")
            turns[idx]["speaker"] = f"(After A Moment) {label_for['agent']}"

        n_marker_only = 0
        if rng.random() < 0.05:
            pos = rng.randint(2, len(turns) - 1)
            turns.insert(pos, {"speaker": label_for["agent"], "text": "(pause)"})
            n_marker_only += 1
        if rng.random() < 0.05:
            turns.append({"speaker": label_for["agent"], "text": "call ended"})
            n_marker_only += 1
        if rng.random() < 0.03:
            k = rng.randrange(len(turns))
            if turns[k]["text"] not in {"(pause)", "call ended"}:
                turns[k]["text"] += " [inaudible]"

        n_ann = 0
        if rng.random() < 0.04:
            for _ in range(rng.randint(1, 3)):
                lab, txt = rng.choice(ANNOTATION_STYLES)
                turns.append({"speaker": lab, "text": txt})
                n_ann += 1

        embedded = (not named) and n_ann == 0 and n_marker_only == 0 and rng.random() < 0.012
        if embedded:
            first = turns[0]["text"]
            rest = " ".join(
                f"\\n {k + 1} {'customer' if expected_roles[k] == 'customer' else 'agent'} {t['text']}"
                for k, t in enumerate(turns[1:], start=1)
            )
            expected_roles = ["agent"] + [
                "customer" if r == "customer" else "agent" for r in expected_roles[1:]
            ]
            turns = [{"speaker": "Agent", "text": f"{first} {rest}"}]

        rec = {
            "transcript_id": str(uuid.UUID(int=rng.getrandbits(128))),
            "time_of_interaction": (start + timedelta(minutes=rng.randint(0, 8 * 24 * 60))).strftime("%Y-%m-%d %H:%M:%S"),
            "domain": "Insurance",
            "intent": intent,
            "reason_for_call": f"Customer {cust.title()} called {brand.title()} because {canon[1][1].split('because ', 1)[-1]}.",
            "conversation": turns,
        }
        if scenario == "refund" and rng.random() < 0.85:
            rec["reason_for_call"] += " The agent processed a refund at the end of the call."
        if rng.random() < 0.01:
            rec[rng.choice(["time_of_interaction", "intent", "reason_for_call"])] = None
        records.append(rec)
        truth.append({
            "transcript_id": rec["transcript_id"], "domain": dname, "scenario": scenario,
            "named_speakers": named, "embedded": embedded, "n_annotations": n_ann,
            "n_marker_only": n_marker_only, "expected_roles": expected_roles,
            "has_supervisor": scenario == "escalation" and not embedded,
            "duplicate_of": None, "near_dup_of": None,
        })

    for _ in range(max(1, n // 300)):
        j = rng.randrange(len(records))
        dup = json.loads(json.dumps(records[j]))
        dup["transcript_id"] = str(uuid.UUID(int=rng.getrandbits(128)))
        records.append(dup)
        t = dict(truth[j]); t["transcript_id"] = dup["transcript_id"]; t["duplicate_of"] = records[j]["transcript_id"]
        truth.append(t)

    for _ in range(max(2, n // 200)):
        j = rng.randrange(n)
        src = records[j]
        if not any(ch.isdigit() for t in src["conversation"] for ch in t["text"]):
            continue
        var = json.loads(json.dumps(src))
        var["transcript_id"] = str(uuid.UUID(int=rng.getrandbits(128)))
        while var["conversation"] == src["conversation"]:
            for t in var["conversation"]:
                t["text"] = re.sub(r"\d", lambda m: str(rng.randint(0, 9)), t["text"])
        records.append(var)
        t = dict(truth[j]); t["transcript_id"] = var["transcript_id"]; t["near_dup_of"] = src["transcript_id"]
        truth.append(t)

    for conv in ([], [{"speaker": "Agent", "text": "thank you for calling shopnest how can i help"}]):
        tid = str(uuid.UUID(int=rng.getrandbits(128)))
        records.append({"transcript_id": tid, "time_of_interaction": "2025-11-05 10:00:00",
                        "domain": "Insurance", "intent": "Product Returns",
                        "reason_for_call": "Call dropped.", "conversation": conv})
        truth.append({"transcript_id": tid, "domain": "retail_ecommerce", "scenario": "degenerate",
                      "named_speakers": False, "embedded": False, "n_annotations": 0,
                      "n_marker_only": 0, "expected_roles": ["agent"] * len(conv),
                      "has_supervisor": False, "duplicate_of": None, "near_dup_of": None})
    return records, truth


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=800)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=Path, default=Path("data/raw/synthetic_transcripts.json"))
    args = ap.parse_args()
    records, truth = generate(args.n, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    truth_path = args.out.with_name(args.out.stem + "_truth.json")
    truth_path.write_text(json.dumps(truth, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(records)} records -> {args.out}\nwrote truth -> {truth_path}")


if __name__ == "__main__":
    main()
