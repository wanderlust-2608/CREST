from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

MONEY_RE = r"\b(?:credit\w*|refund\w*|reimburs\w*|compensat\w*|money|cash|voucher\w*)\b"


@dataclass(frozen=True)
class EventDef:
    code: str
    name: str
    plural: str
    confirmatory: bool
    onset_rule: str
    subtypes: tuple
    excluded_behaviours: tuple = ()
    occurrence_filters: dict = field(default_factory=dict)
    synonyms: tuple = ()


EVENTS: dict[str, EventDef] = {
    "ESC": EventDef(
        "ESC", "escalation", "escalations", True,
        "the first turn in which the customer asks for a supervisor, manager or someone more senior, or the agent starts "
        "a handoff to one, or a supervisor speaks",
        ("customer_request", "agent_handoff"),
        excluded_behaviours=("agent_transfer",),
        synonyms=("escalat", "supervisor", "manager", "speak to someone", "higher up", "someone senior")),
    "REF": EventDef(
        "REF", "refund episode", "refund episodes", True,
        "the first turn in which either party raises a refund, compensation, money back, a credit back or a chargeback",
        ("customer_request", "agent_offer"),
        occurrence_filters={"offer_solution": MONEY_RE},
        synonyms=("refund", "money back", "reimburs", "compensat", "chargeback", "credit back")),
    "CHURN": EventDef(
        "CHURN", "churn threat", "churn threats", True,
        "the first customer turn stating an intent to cancel or close the account, switch provider or not renew",
        ("cancel", "switch", "not_renew", "other"),
        excluded_behaviours=("competitor_mention",),
        synonyms=("churn", "cancel", "leave", "leaving", "switch", "quit", "retention", "attrition")),
    "HANDOFF": EventDef("HANDOFF", "completed supervisor handoff", "completed supervisor handoffs", False,
                        "the first turn spoken by a supervisor", ("supervisor",)),
    "REF_GRANTED": EventDef("REF_GRANTED", "refund granted", "granted refunds", False,
                            "the first agent turn confirming that a refund or credit has been or will be issued", ("granted",)),
    "REF_DENIED": EventDef("REF_DENIED", "refund denied", "denied refunds", False,
                           "the first agent refusal within two turns of a customer refund request", ("denied",)),
    "CANCEL_DONE": EventDef("CANCEL_DONE", "cancellation completed", "completed cancellations", False,
                            "the first agent turn confirming that an account, policy or subscription was cancelled", ("done",)),
    "RISK": EventDef("RISK", "retention risk", "retention risks", False,
                     "the first customer turn with a churn threat, a competitor mentioned after the customer has complained or "
                     "been refused, or wavering loyalty (second thoughts, losing patience, 'is this how you treat loyal "
                     "customers')", ("explicit", "competitor", "wavering")),
}
PRIMARY_EVENTS = tuple(c for c, e in EVENTS.items() if e.confirmatory)

GRANT_RE = re.compile(r"\b(?:i have|i've|i will|i'll|we have|we've|we will|we'll)\s+(?:gone ahead and\s+)?"
                      r"(?:processed|issued|refunded|credited|approved|reversed)\b|\byour refund (?:has been|is being|will be) processed\b")
CANCEL_DONE_RE = re.compile(r"\b(?:i have|i've|we have|we've)\s+(?:gone ahead and\s+)?(?:cancell?ed|closed|terminated)\s+"
                            r"(?:your|the)\s+(?:\w+\s+)?(?:account|policy|subscription|service|membership|plan|contract)\b")
CHURN_SUBTYPE_RES = [
    ("not_renew", re.compile(r"\brenew")),
    ("switch", re.compile(r"\b(?:switch\w*|move|moving|leave|leaving|quit\w*|go(?:ing)? with|take|taking)\b")),
    ("cancel", re.compile(r"\b(?:cancel\w*|clos\w*|terminat\w*|discontinu\w*|drop\w*|end\w*)\b")),
]

NC_THANKS_RE = (r"\bthank(?:s| you)(?: so much| very much)? for (?:that|the|this|those|these|all the) "
                r"(?:information|info|details|detail)\b|\bthank(?:s| you) for confirming\b")
NC_READBACK_RE = (r"\b(?:just to confirm|to confirm|let me confirm|confirming|let me read (?:that|it) back|"
                  r"reading (?:that|it) back)\b.{0,40}?(?:\d|\b(?:zero|one|two|three|four|five|six|seven|eight|nine|oh)\b)")


@dataclass(frozen=True)
class Behaviour:
    id: str
    label: str
    short: str
    party: str
    detector: tuple
    actionable: bool
    negative_control: bool = False
    synonyms: tuple = ()


BEHAVIOURS: dict[str, Behaviour] = {b.id: b for b in [
    Behaviour("hold_request", "the agent puts the customer on hold or asks them to wait", "holds and wait requests",
              "Agent", ("cue", "cue_hold_request"), True,
              synonyms=("hold", "on hold", "wait", "waiting", "silence", "silences", "dead air")),
    Behaviour("hold_return", "the agent thanks the customer for waiting", "returns from hold", "Agent",
              ("cue", "cue_hold_return"), True, synonyms=("thanks for waiting", "return from hold", "back from hold")),
    Behaviour("apology", "the agent apologises", "agent apologies", "Agent", ("cue", "cue_apology"), True,
              synonyms=("apolog", "sorry")),
    Behaviour("empathy", "the agent expresses empathy", "empathy statements", "Agent", ("cue", "cue_empathy"), True,
              synonyms=("empath", "sympath", "understanding tone")),
    Behaviour("refusal", "the agent refuses a request or cites policy", "policy refusals", "Agent",
              ("cue", "cue_refusal"), True,
              synonyms=("refus", "policy", "deny", "denied", "declin", "no exceptions", "rejection", "reject")),
    Behaviour("offer_solution", "the agent offers a concrete solution", "solution offers", "Agent",
              ("cue", "cue_offer_solution"), True, synonyms=("offer", "solution", "resolv", "fix", "remed")),
    Behaviour("agent_transfer", "the agent transfers the call to another team", "transfers", "Agent",
              ("cue", "cue_agent_transfer"), True, synonyms=("transfer", "specialist", "another department", "routed")),
    Behaviour("negative_emotion", "the customer expresses frustration or anger", "customer frustration", "Customer",
              ("cue", "cue_negative_emotion"), False,
              synonyms=("angry", "anger", "frustrat", "upset", "annoyed", "negative emotion", "emotion", "irritat")),
    Behaviour("confusion", "the customer is confused or misunderstands", "customer confusion", "Customer",
              ("cue", "cue_confusion"), False, synonyms=("confus", "misunderstand", "don't understand", "clarif")),
    Behaviour("repeat_contact", "the customer says they already called or explained before", "repeat-contact mentions",
              "Customer", ("cue", "cue_repeat_contact"), False,
              synonyms=("repeat contact", "called before", "called again", "already called", "multiple calls", "callback")),
    Behaviour("issue_persistence", "the customer says the problem is still not fixed", "unresolved-issue complaints",
              "Customer", ("cue", "cue_issue_persistence"), False,
              synonyms=("still not", "persist", "unresolved", "ongoing problem", "not fixed")),
    Behaviour("repeat_question", "the customer repeats an earlier question or statement", "repeated questions",
              "Customer", ("column", "is_repeat"), False,
              synonyms=("repeat", "repeated question", "repeated queries", "asks again", "repetition")),
    Behaviour("hesitation", "the customer hesitates (two or more filled pauses)", "customer hesitations", "Customer",
              ("min_count", "n_filled_pauses", 2), False, synonyms=("hesitat", "filler", "filled pause", "um", "uh")),
    Behaviour("competitor_mention", "the customer mentions a competitor", "competitor mentions", "Customer",
              ("cue", "cue_competitor_mention"), False, synonyms=("competitor", "another provider", "other company")),
    Behaviour("nc_thanks_info", "the agent thanks the customer for information", "thank-you-for-the-information remarks",
              "Agent", ("regex", NC_THANKS_RE), True, negative_control=True,
              synonyms=("thanking the customer for", "thank the customer for", "thanks the customer for",
                        "thanks for the info", "thank you for the info", "thanks for info", "thanking for info")),
    Behaviour("nc_readback", "the agent reads back an id or number to confirm it", "read-backs", "Agent",
              ("regex", NC_READBACK_RE), True, negative_control=True,
              synonyms=("read back", "reads back", "reading back", "readback", "read-back", "repeating back",
                        "repeats back")),
]}
NEGATIVE_CONTROLS = tuple(b for b, d in BEHAVIOURS.items() if d.negative_control)


def candidate_behaviours(event: str) -> list[str]:
    ev = EVENTS[event]
    return [b for b, d in BEHAVIOURS.items() if not d.negative_control and b not in ev.excluded_behaviours]


INDUSTRIES = {
    "hospitality": ("hotel", "hotels", "hospitality", "resort", "resorts", "lodging", "accommodation"),
    "airline": ("airline", "airlines", "flight", "flights", "air travel", "aviation", "airways"),
    "telecom": ("telecom", "telco", "internet", "mobile", "broadband", "wifi", "wi-fi", "network provider", "phone company"),
    "banking": ("bank", "banks", "banking", "credit card", "cards", "loan", "loans", "financial"),
    "insurance": ("insurance", "insurer", "insurers", "claims", "policyholder", "policyholders"),
    "retail_ecommerce": ("retail", "e-commerce", "ecommerce", "shopping", "online store", "orders", "delivery", "deliveries"),
}
INDUSTRY_LABEL = {"hospitality": "hotel", "airline": "airline", "telecom": "telecom", "banking": "banking",
                  "insurance": "insurance", "retail_ecommerce": "retail", "unknown": "unclassified"}

UNSUPPORTED_ATTRIBUTES = {
    "customer tier": ("premium customer", "premium customers", "premium member", "premium members", "premium tier",
                      "premium account", "premium accounts", "premium client", "premium clients", "premium users", "vip",
                      "vips", "gold member", "gold members", "platinum", "loyalty tier", "loyalty members", "high value",
                      "high-value", "customer tier", "customer tiers", "tier", "tiers"),
    "plan or segment": ("premium plan", "basic plan", "standard plan", "family plan", "business plan", "enterprise plan",
                        "unlimited plan", "prepaid plan", "postpaid plan", "subscription plan", "subscription plans", "plan type",
                        "plan types", "which plan", "which plans", "by plan", "per plan", "each plan", "customer segment",
                        "customer segments", "segment", "segments", "enterprise customers", "business customers",
                        "small business customers", "smb", "b2b", "b2c", "contract type"),
    "account age": ("new customers", "new clients", "first-time customers", "long-time customers", "longtime customers",
                    "long-standing customers", "long standing customers", "loyal customers", "existing customers",
                    "returning customers", "repeat customers", "tenure", "account age", "years with us"),
    "demographics": ("age", "gender", "income", "young", "elderly", "senior citizens", "women", "men"),
    "location": ("city", "cities", "region", "regions", "country", "countries", "which state", "by state", "us state",
                 "miami", "london", "new york", "texas", "location", "zip code", "postcode"),
    "satisfaction scores": ("csat", "nps", "satisfaction score", "survey score", "rating"),
    "financials": ("revenue", "profit", "cost per call", "lifetime value", "clv", "ltv"),
    "agent identity": ("which agent", "agent name", "worst agent", "best agent", "agent performance ranking"),
    "call duration": ("seconds", "minutes long", "call duration", "handle time", "aht", "how long", "wait time",
                      "waiting time", "hold time", "hold duration", "duration", "long hold", "long holds", "long wait",
                      "long waits"),
    "audio": ("tone of voice", "voice tone", "voice", "pitch", "loudness", "shouting", "audio", "acoustic"),
    "unmeasured behaviour": ("sarcasm", "sarcastic", "rude", "rudeness", "polite", "politeness", "interrupt",
                             "interrupts", "interrupting", "interruption", "interruptions", "talking over", "accent",
                             "language barrier", "jargon", "upsell", "upselling", "script adherence", "small talk"),
}
UNSUPPORTED_MESSAGES = {
    "effect-size threshold": "Effects are estimated with uncertainty, so the threshold in the question is checked against "
                             "each behaviour's estimate and against its confidence interval.",
    "rate threshold": "The threshold in the question is compared with the share of calls that have the event.",
    "agent identity": "Individual agents are not ranked ('{text}'): agent names appear only in greetings, and per-agent "
                      "counts would mix each agent's skill with the calls they happen to get. The answer below describes the "
                      "agent behaviours instead.",
    "customer tier": "The data has no customer-tier field ('{text}'). Where customers say they are members or long-time "
                     "customers, that is used below as the nearest proxy.",
    "single-call counterfactual": "Whether one particular call would have gone differently with another agent action "
                                  "('{text}') cannot be estimated from the data; the estimate below is for comparable moments "
                                  "across calls.",
    "no clear effect": "'No clear effect' is read as: the confidence interval of the estimated difference includes zero. "
                       "That is not proof of no effect; each interval shows how large an effect the data cannot rule out.",
    "effect modification": "Effects are estimated over all comparable moments together, not separately for calls where "
                           "something else had already happened ('{text}'), so whether the effect is different there (effect "
                           "modification) is not estimated. The answer below gives the overall estimate.",
    "plan or segment": "The data has no plan or customer-segment field ('{text}'), so that part of the question cannot be "
                       "answered; the answer below covers all customers. An account_attributes.csv with a plan or segment "
                       "column (see the README) makes this filter available.",
    "account age": "The data has no account-age (tenure) field ('{text}'). Where customers say they are long-time, loyal or "
                   "member customers, that is used below as the nearest proxy.",
    "demographics": "The data has no age or other demographic fields ('{text}'), so that comparison cannot be made; the "
                    "answer below covers all customers.",
    "call duration": "The transcripts carry no timing information (no durations or timestamps inside calls), so "
                     "that part of the question ('{text}') cannot be answered.",
    "audio": "The transcripts are text only, so tone of voice and other audio cues ('{text}') cannot be analysed.",
    "unmeasured behaviour": "'{text}' is not one of the behaviours the system detects (it detects, for example, "
                            "refusals, apologies, holds, solution offers, empathy, customer frustration and repeated "
                            "questions), so that part of the question cannot be answered.",
    "two events": "The question mentions {text}. Each answer covers one event, so this answer is about {first}; ask "
                  "'what about {second}?' next for the other one.",
    "effects between events": "Effects of one event on another are not estimated (only behaviours inside the call are "
                              "studied as possible drivers), so the counts below only show how often {text} occur in "
                              "the same calls and which one started first.",
    "whole-call policy": "Effects are estimated for single moments in a call, not for a rule applied to every call "
                         "('{text}'), so the answer below covers that narrower question.",
}


def unsupported_message(u: dict) -> str:
    tpl = UNSUPPORTED_MESSAGES.get(u.get("attribute", ""))
    if tpl is None:
        return f"The data has no information on {u.get('attribute')} ('{u.get('text')}'), so that part of the question " \
               f"cannot be answered."
    return tpl.format(text=u.get("text", ""), first=u.get("first", ""), second=u.get("second", ""))

CATEGORY_RANK = {"none": 0, "correlational": 1, "conditional_causal": 2, "direct_causal": 3}
MAX_CATEGORY_FOR_LEVEL = {"L3": "conditional_causal", "L2": "correlational", "L1": "none", "L0": "none"}

DIRECT_CAUSAL_RE = re.compile(
    r"\b(?:caus(?:e|es|ed|ing)|lead(?:s|ing)? to|led to|result(?:s|ed|ing)? in|driv(?:e|es|en|ing)|drove|"
    r"trigger(?:s|ed|ing)?|responsible for|produc(?:e|es|ed|ing)|increas(?:e|es|ed|ing)|decreas(?:e|es|ed|ing)|"
    r"reduc(?:e|es|ed|ing)|rais(?:e|es|ed|ing)|lower(?:s|ed|ing)|(?:to|will|would|can|could|may|might|does|do|did) lower|"
    r"prevent(?:s|ed|ing)?|boost(?:s|ed|ing)?|"
    r"is the reason|are the reason|the reason (?:is|why)|the (?:main |key |primary |real |root )?(?:reasons?|causes?) "
    r"(?:for|of|behind)|(?:is|are|that's|this is|that is) why|explains? why|because of|due to|thanks to|"
    r"make[s]? (?:customers?|callers?|people|them) \w+)\b")
HEDGE_RE = re.compile(r"\b(?:may|might|could|can|estimated to|likely to|appears? to|seems? to|suggests?|"
                      r"would be expected to|potentially|possibly|tends? to)\b")
CORRELATIONAL_RE = re.compile(
    r"\b(?:associat\w*|correlat\w*|linked (?:to|with)|related to|relationship|predict\w*|more likely|less likely|"
    r"often precede\w*|preced\w*|warning sign\w*|co-?occur\w*|coincid\w*|higher (?:rate|share|chance|risk|odds|"
    r"probability|likelihood)|lower (?:rate|share|chance|risk|odds|probability|likelihood)|more (?:often|frequently|"
    r"common(?:ly)?)|less (?:often|frequently|common(?:ly)?)|(?:an? |the )?(?:increase|rise|decrease|drop|fall|spike|jump) "
    r"in)\b")
NEGATION_RE = re.compile(r"\b(?:not|no|never|cannot|can't|doesn't|don't|isn't|aren't|without|neither|nor|none)\b")
NOUN_CONTEXT = {"a", "an", "the", "any", "no", "this", "that", "its", "their", "every", "each", "some", "such", "higher",
                "lower", "larger", "smaller", "big", "small", "slight", "significant", "main", "possible", "likely"}


def definitions_snapshot() -> dict:
    return {
        "events": {k: {**asdict(v), "subtypes": list(v.subtypes)} for k, v in EVENTS.items()},
        "behaviours": {k: {**asdict(v), "detector": list(v.detector)} for k, v in BEHAVIOURS.items()},
        "money_re": MONEY_RE,
        "max_category_for_level": MAX_CATEGORY_FOR_LEVEL,
    }
