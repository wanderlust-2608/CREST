from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field

from .definitions import BEHAVIOURS, EVENTS, INDUSTRIES, PRIMARY_EVENTS, UNSUPPORTED_ATTRIBUTES
from .lexicon import apply_slang, correct_spelling, translate

QUESTION_TYPES = ("why", "how_often", "examples", "compare", "trend", "what_to_change", "effect_of", "describe_factor",
                  "issues", "shared", "event_link", "behaviour", "overview", "help", "call", "unknown")
UUID_RE = re.compile(r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?::\d+)?\b")
CALL_WORD_RE = re.compile(r"\b(?:call|transcript|conversation|interaction|case|ticket|chat|record)s?\s*(?:id|number|no\.?)?\s*[:#]?\s*"
                          r"([0-9a-z][0-9a-z_.-]{2,}[0-9a-z])(?::\d+)?\b")
ID_TOKEN_RE = re.compile(r"[0-9a-z][0-9a-z_.-]{2,}[0-9a-z](?::\d+)?")
OVERVIEW_RE = re.compile(r"\b(?:overview|summary|summari[sz]e|big picture|key (?:insights|findings|numbers|metrics)|main "
                         r"(?:findings|insights|issues|problems)|highlights|what(?:'s| is) (?:going on|happening)|tell me "
                         r"about (?:the )?(?:data|dataset|calls|corpus|conversations)|what happens in|how (?:are|is) "
                         r"(?:things|it) going)\b")
HELP_RE = re.compile(r"^\s*(?:hi|hello|hey|help|what can you do|how (?:do|does) (?:this|it|you) work|what (?:can|should) "
                     r"i ask)\b")

SECONDARY_PATTERNS = {
    "HANDOFF": r"\b(?:handoffs?|handed (?:over|off) to (?:a )?supervisor|supervisor (?:actually )?(?:joins?|joined|took over|takes over)|completed (?:supervisor )?handoffs?|"
               r"(?:spoke|talked) (?:to|with) (?:a |the |their )?(?:supervisor|manager))\b",
    "REF_GRANTED": r"\brefunds? (?:requests? )?(?:were |was |is |are |being |get |got )?(?:granted|approved|issued|processed|given)\b|"
                   r"\bgranted (?:a |the |their )?refunds?\b|\b(?:got|received|were given|was given) (?:a|the|their|his|her|my|any) refund\b",
    "REF_DENIED": r"\brefunds? (?:requests? )?(?:were |was |is |are |being |get |got |gets )?(?:denied|refused|rejected|declined|turned down)\b|"
                  r"\b(?:denied|refused|rejected|declined|turned down)(?: (?:a|the|their|his|her|my|your|any))? refunds?\b|"
                  r"\b(?:didn't|did not|couldn't|could not|don't|do not|can't|cannot) get (?:a|the|their|his|her|my|any) refund\b|"
                  r"\bno refunds?\b|\brefund (?:denials?|refusals?|rejections?)\b",
    "RISK": r"\b(?:retention risks?|at[- ]risk(?: customers| calls| guests| clients)?|risk of (?:churn|leaving|losing (?:them|customers))|"
            r"likely to (?:leave|churn)|wavering(?: customers| loyalty)?|loyalty risks?|churn risks?)\b",
    "CANCEL_DONE": r"\b(?:completed cancellations?|cancellations? (?:were |was )?(?:completed|done|processed)|accounts? (?:were |was |got )?(?:actually )?(?:cancell?ed|closed))\b",
}
EVENT_PATTERNS = {
    "ESC": r"\b(?:escalat\w*|supervisors?|(?:ask\w*|request\w*|demand\w*|want\w*) (?:for |to (?:speak|talk) (?:to|with) )?(?:a |the |your )?manager|(?:speak|talk)(?:ing)? (?:to|with) (?:a |the |your )?manager|higher[- ]ups?|someone (?:senior|higher)|(?:speak|talk)(?:ing)? to someone (?:else|higher|senior))\b",
    "REF": r"\b(?:refunds?|refunded|money back|reimburs\w*|compensat\w*|chargebacks?|credit(?:s|ed)? back)\b",
    "CHURN": r"\b(?:churn\w*|cancel\w*|leav(?:e|es|ing) (?:the company|us)|switch\w* (?:provider|company|to)|quit(?:s|ting)?|attrition|retention|threat\w* to (?:leave|cancel|switch))\b",
}
TYPE_PATTERNS = [
    ("what_to_change", r"\b(?:what (?:should|can|could) (?:we|agents?|the company|the team)|how (?:can|could|do|should) we (?:\w+ ){0,3}?(?:reduce|lower|prevent|avoid|cut|decrease|stop)|how to (?:reduce|lower|prevent|avoid|cut|decrease)|what (?:would|will) (?:reduce|lower|prevent|help)|recommend\w*|what to change|action items?)\b"),
    ("examples", r"\b(?:show me|give me (?:some |a few |an? )?(?:examples?|quotes?|calls?)|examples?|quotes?|excerpts?|^(?:the |some |all )?(?:transcripts?|calls?) where|(?:list|pull|get|find|see|show)(?: me)?(?: the| some| all)? (?:calls|transcripts?)(?: where)?|evidence of)\b"),
    ("trend", r"\b(?:trend\w*|over time|by (?:week|month|day)|per (?:week|month|day)|weekly|monthly|changed? over|increas\w* over|decreas\w* over)\b"),
    ("compare", r"\b(?:compare\w*|comparison|versus|vs\.?|difference between|differ\w* (?:between|across)|which (?:industry|industries|brand|event|tiers?|plans?|segments?)|relative to|rank\w* (?:the )?(?:industries|sectors|brands|events|tiers|plans|segments))\b"),
    ("how_often", r"\b(?:how (?:many|often|much|common|frequent(?:ly)?)|what (?:share|percentage|percent|proportion|fraction|rate)|rates? of|frequency|count of|number of|percentage of|share of|what(?:'s| is| are| was| were) the (?:\w+ ){0,2}(?:rates?|share|percentage|proportion))\b"),
    ("issues", r"\b(?:products?|service (?:problems?|issues?|faults?)|(?<!issue )complain(?:t|ts|s|ing)?|pain points?|"
               r"(?:what|which) (?:kinds? of |types? of )?(?:issues|problems|topics|themes|complaints)|"
               r"what (?:do|did|are) (?:customers|callers|people) (?:say|saying|mention|mentioning|talk about|talking about|"
               r"rais(?:e|ing))|topics?|themes?)\b"),
    ("effect_of", r"\b(?:effect of|impact of|affect\w*|influence\w*|does .{1,40} (?:cause|lead to|increase|decrease|reduce|raise|lower|drive|trigger|prevent)|is .{1,40} (?:linked|associated|related|correlated) (?:to|with))\b"),
    ("describe_factor", r"\b(?:factor\s*#?\s*\d+|factor f\d+|\bf\d+\b|tell me more about|explain (?:the )?(?:first|second|third|fourth|fifth|\d+(?:st|nd|rd|th)?) (?:factor|one|reason))\b"),
    ("why", r"\b(?:why|what causes?|what drives?|drivers?|root causes?|reasons? (?:for|behind|why)|what leads? to|what makes|what triggers?|explain (?:the )?(?:escalations?|refunds?|churn))\b"),
]
LEADING_RE = re.compile(r"\b(?:isn't it true|is it not true|surely|obviously|clearly|don't you agree|wouldn't you agree|"
                        r"right\s*\?|correct\s*\?|as we all know|everyone knows)\b")
PRESUPPOSE_UP = r"(?:cause[sd]?|causing|lead(?:s)? to|led to|result(?:s|ed)? in|drive[sn]?|drove|trigger(?:s|ed)?|increase[sd]?|raise[sd]?|boost(?:s|ed)?|make[s]? (?:customers?|people|callers?) \w+)"
PRESUPPOSE_DOWN = r"(?:reduce[sd]?|decrease[sd]?|lower(?:s|ed)?|prevent(?:s|ed)?|stop(?:s|ped)?|avoid(?:s|ed)?|cut(?:s)?)"
ASSERTIVE_RE = re.compile(r"^\s*(?:why|how much|how come|since|given that|because|so|now that|to what extent|by how much)\b|"
                          r"\b(?:right|correct|true)\s*\??\s*$|,\s*(?:right|correct)\b")
WHY_RE = re.compile(dict(TYPE_PATTERNS)["why"])
PRODUCT_RE = re.compile(dict(TYPE_PATTERNS)["issues"])
EVENT_LINK_RE = re.compile(r"\b(?:lead(?:s|ing)? to|led to|caus(?:e|es|ed|ing)|result(?:s|ed|ing)? in|trigger(?:s|ed|ing)?|"
                           r"turn(?:s|ed)? into|end(?:s|ed)? (?:up )?in|followed by|follow(?:s|ed)?|preced\w*|before|after|"
                           r"prior to|more likely|less likely|chance of|risk of)\b")
SEQUENCE_RE = re.compile(r"\b(?:which (?:one |event )?(?:comes?|came|happens?|starts?) first|(?:comes?|came|happens?) first|"
                         r"in what order|which order)\b")
EVENT_COMPARE_RE = re.compile(r"\b(?:vs\.?|versus|compared?|comparison|more (?:common|often|frequent)|less (?:common|often|"
                              r"frequent)|than)\b")
SHARED_RE = re.compile(r"\b(?:both|also|same|in common|shared?|overlap\w*|as well|each|either)\b|\b(?:and|or)\b")
POLICY_RE = re.compile(r"\bif (?:(?:the |our )?agents?|we|staff|the company|the team|reps?) (?:never|always|stop(?:ped)?|"
                       r"no longer|didn'?t|did not|don'?t|do not|could not|couldn'?t)(?: \w+){1,3}|\bwhat (?:would|will) "
                       r"happen\b|\bwhat if\b|\b(?:banned|banning|ban on|a rule that)\b")
RANK_INDUSTRY_RE = re.compile(r"\b(?:which|what) (?:industry|industries|sector|sectors)\b|\b(?:by|per|across|each|every) "
                              r"(?:industry|industries|sector)\b|\brank\w* (?:the )?(?:industries|sectors)\b")
RANK_BRAND_RE = re.compile(r"\b(?:which|what) (?:brand|brands|client|clients|company|companies)\b|\b(?:by|per|across|each|"
                           r"every) (?:brand|client|company)\b|\brank\w* (?:the )?(?:brands|clients|companies)\b")
RANK_ACCOUNT_RE = re.compile(r"\b(?:which|what) (tier|tiers|plan|plans|segment|segments|membership levels?)\b|\b(?:by|per|across|"
                             r"each|every) (tier|plan|segment)\b|\brank\w* (?:the )?(tiers|plans|segments)\b")
SELF_STATUS_RE = re.compile(r"\b(?:who|that) (?:say|said|says|mention\w*|claim\w*|report\w*) (?:they(?:'re| are| were)|to be) "
                            r"(?:an? )?(gold|silver|platinum|diamond|elite|premium|vip|bronze|loyalty|loyal|rewards)?\s*"
                            r"(?:members?|customers?|status)\b|\bself[- ]reported (gold|silver|platinum|diamond|elite|premium|vip|"
                            r"bronze)?\s*(?:status|members?|tiers?)\b")
RANK_EVENT_RE = re.compile(r"\b(?:which|what) (?:event|events|business event|outcome|outcomes)\b|\bmost common (?:event|"
                           r"outcome)\b")
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                        "september", "october", "november", "december"], 1)}
MONTH_RE = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                "fifteen": 15, "twenty": 20, "twenty five": 25, "thirty": 30, "fifty": 50, "half a": 0.5}
THRESHOLD_RE = re.compile(r"\b(?:by |of )?(more than|over|above|at least|greater than|bigger than|larger than|exceeding|"
                          r"less than|under|below|at most|smaller than)\s+(\d+(?:\.\d+)?|" +
                          "|".join(sorted(NUMBER_WORDS, key=len, reverse=True)) +
                          r")\s*(?:%|percent(?:age)?(?: points?)?|pp\b|points?\b|percentage points?)")
CHANGE_NOUN = (r"(?:polic(?:y|ies)|rules?|process(?:es)?|procedures?|systems?|scripts?|changes?|updates?|launch|roll-?out|"
               r"campaign|training|pricing|prices?|fees?|app|website|outage|merger|reorg\w*|guidelines?|terms)")
CHANGE_RE = re.compile(r"\b(after|before|since|following|once|prior to)\s+(?:the |our |a |this |that |their )?"
                       r"((?:(?:new|recent|updated|latest|revised|changed|current)\s+)?(?:[a-z']+\s+){0,3}?" + CHANGE_NOUN + r")"
                       r"((?:\s+(?:was|were|got|has been|had been|is|went|came)\s+(?:introduced|launched|changed|updated|rolled out|"
                       r"implemented|started|put in place|announced|released|live|into effect|in))?)")
CHANGE_VERB_RE = re.compile(r"\b(?:before and after|compar\w*|increas\w*|ris(?:e|es|en|ing)|rose|go(?:ne)? up|went up|grow\w*|grew|drop\w*|fall|fell|fallen|"
                            r"decreas\w*|go(?:ne)? down|went down|chang\w*|improv\w*|worsen\w*|spik\w*|jump\w*|differ\w*|"
                            r"more|fewer|less|higher|lower)\b")
DIRECTION_RE = re.compile(r"\b(?:did|do|does|have|has|are|is|were|was|will)\b(?:\s+[\w'-]+){1,5}?\s+(?:go(?:ne|ing)? (?:up|down)|"
                          r"went (?:up|down)|ris(?:e|en|ing)|rose|fall(?:en|ing)?|fell|drop(?:ped|ping)?|increas(?:e|ed|ing)|"
                          r"decreas(?:e|ed|ing)|declin(?:e|ed|ing)|grow(?:n|ing)?|grew|spik(?:e|ed|ing)|jump(?:ed|ing)?|"
                          r"climb(?:ed|ing)?|shr[iu]nk(?:ing)?|improv(?:e|ed|ing)|worsen(?:ed|ing)?|get(?:ting)? (?:better|worse)|"
                          r"got (?:better|worse)|chang(?:e|ed|ing))\b(?!\s+(?:the\s+)?(?:number|rate|share|chance|risk|escalat|"
                          r"refund|churn|cancel|threat|customers?|calls?))")
EFFECT_MOD_RE = re.compile(r"\b(?:only (?:when|if|in calls where)|(?:when|if|once|after|for customers who|for callers who|in calls "
                           r"where) (?:the )?(?:customers?|callers?|they|he|she)?\s*(?:is|are|was|were|has|have|had|gets?|got|"
                           r"becomes?|became)? ?already|(?:depend\w*|differ\w*|vary|varies|change\w*) (?:on|with|by) whether|"
                           r"(?:more|less) (?:effective|helpful|useful) (?:when|if|for))\b[^?.]*")
COUNTERFACTUAL_RE = re.compile(r"\b(?:if (?:the |our |that |this )?agents? (?:had|hadn't|had not|would have)|had (?:the |our |that )?agents? "
                               r"(?:not )?\w+|would (?:the customer|they|he|she|this customer|that customer|the caller|the call) "
                               r"(?:still|not|never|have)|what if (?:the |our |that )?agents? had)\b[^,?.;]*")
SINGLE_CALL_RE = re.compile(r"\b(?:this|that|the same|a single|one particular|this particular|that particular) (?:call|customer|caller|"
                            r"conversation)\b|\bthe customer still\b")
COND_PARENT_EVENT = {"HANDOFF": "ESC", "REF_GRANTED": "REF", "REF_DENIED": "REF", "CANCEL_DONE": "CHURN"}
COND_REL_RE = re.compile(r"\b(?:customers?|callers?|people|clients?|users?|guests?|passengers?|calls?|conversations?|cases?|"
                         r"those|ones|anyone|everyone)\s+(?:who|that|whose|where|which|in which|with)\b")
COND_SUB_RE = re.compile(r"\b(?:after|when|whenever|once|if|following)\b")
COND_LINK_VERBS = re.compile(r"\b(?:lead(?:s|ing)? to|led to|caus(?:e|es|ed|ing)|result(?:s|ed|ing)? in|trigger(?:s|ed|ing)?)\b")
ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "5th": 5}


@dataclass
class QuerySpec:
    raw: str = ""
    event: str | None = None
    question_type: str = "unknown"
    filters: dict = field(default_factory=dict)
    behaviour: str | None = None
    factor_ref: str | None = None
    compare: dict | None = None
    presuppositions: list = field(default_factory=list)
    unsupported: list = field(default_factory=list)
    declined_filters: list = field(default_factory=list)
    leading: bool = False
    ambiguous: str = ""
    parser: str = "rules"
    notes: list = field(default_factory=list)
    threshold: dict | None = None
    change: dict | None = None

    def to_dict(self) -> dict:
        return json.loads(json.dumps(asdict(self)))

    @classmethod
    def from_dict(cls, d: dict) -> "QuerySpec":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def key(self) -> str:
        d = self.to_dict()
        d.pop("raw", None)
        d.pop("parser", None)
        return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()


def _norm(text: str) -> str:
    t = text.lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", t).strip()


def behaviour_patterns() -> dict[str, re.Pattern]:
    pats = {}
    for b, d in BEHAVIOURS.items():
        words = set(d.synonyms) | {d.short.lower()}
        alts = sorted({re.escape(w.lower()) for w in words if w}, key=len, reverse=True)
        pats[b] = re.compile(r"\b(?:" + "|".join(alts) + r")\w*")
    return pats


_BEH_PATS = behaviour_patterns()


def find_behaviours(text: str) -> list[tuple[int, str]]:
    t = _norm(text)
    hits = []
    for b, rx in _BEH_PATS.items():
        for m in rx.finditer(t):
            hits.append((m.start(), m.end(), b))
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    out, last_end = [], -1
    for s, e, b in hits:
        if s >= last_end:
            out.append((s, b))
            last_end = e
    return out


def event_spans(text: str) -> list[tuple[int, int, str]]:
    t = _norm(text)
    hits = []
    for e, pat in SECONDARY_PATTERNS.items():
        for m in re.finditer(pat, t):
            hits.append((m.start(), m.end(), e))
    for e, pat in EVENT_PATTERNS.items():
        for m in re.finditer(pat, t):
            if any(s <= m.start() < en for s, en, _ in hits):
                continue
            hits.append((m.start(), m.end(), e))
    hits.sort()
    return hits


def find_events(text: str) -> list[tuple[int, str]]:
    return [(s, e) for s, _, e in event_spans(text)]


COORD_RE = re.compile(r"\s*,?\s*(?:and|or|and also|and then|then|as well as|plus|but|&)?\s*(?:(?:were|was|had|have|has|got|get|"
                      r"been|the|a|an|their|they|then|also|later|still|even|who|that)\s+){0,4}")


def condition_split(t: str, spans: list) -> tuple[list[str], str] | None:
    first = {}
    for s, en, e in spans:
        first.setdefault(e, (s, en))
    if len(first) < 2:
        return None
    order = sorted(first.items(), key=lambda kv: kv[1][0])
    (e1, (p1, q1)), (e2, (p2, _)) = order[:2]
    if COND_LINK_VERBS.search(t[q1:p2]):
        return None
    starts = [s for s, _, _ in spans]

    def near(m, pos):
        return pos - m.end() <= 40 and not any(m.end() <= s < pos for s in starts)

    def joined(i):
        return bool(COORD_RE.fullmatch(t[order[i][1][1]:order[i + 1][1][0]])) and \
            bool(re.search(r"\b(?:and|or|as well as|plus|but)\b|,|&", t[order[i][1][1]:order[i + 1][1][0]]))

    if any(near(m, p1) for m in COND_REL_RE.finditer(t[:p1])) or any(near(m, p1) for m in COND_SUB_RE.finditer(t[:p1])):
        conds, i = [e1], 0
        while i + 2 < len(order) and joined(i):
            conds.append(order[i + 1][0])
            i += 1
        return conds, order[i + 1][0]
    between = [m for rx in (COND_REL_RE, COND_SUB_RE) for m in rx.finditer(t) if q1 <= m.start() and m.end() <= p2]
    if any(near(m, p2) for m in between):
        conds, i = [e2], 1
        while i + 1 < len(order) and joined(i):
            conds.append(order[i + 1][0])
            i += 1
        return conds, e1
    return None


def find_call_ids(t: str, known: set | None = None) -> tuple[list[str], str]:
    ids, spans = [], []
    for m in UUID_RE.finditer(t):
        ids.append(m.group(1))
        spans.append((m.start(), m.end()))
    for m in CALL_WORD_RE.finditer(t):
        tok = m.group(1)
        if any(a <= m.start(1) < b for a, b in spans) or not re.search(r"\d", tok):
            continue
        if re.fullmatch(r"(?:19|20)\d\d|\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/.-]\d{1,2}(?:[/.-]\d{2,4})?|\d+\.\d+", tok) and \
                not (known and tok in known):
            continue
        ids.append(tok)
        spans.append((m.start(1), m.end()))
    if known:
        for m in ID_TOKEN_RE.finditer(t):
            tok = m.group(0).split(":")[0]
            if any(a <= m.start() < b for a, b in spans):
                continue
            hit = tok in known
            if not hit and len(tok) >= 6 and re.search(r"\d", tok) and re.search(r"[a-z]", tok):
                pre = [k for k in known if k.startswith(tok)][:2]
                hit = len(pre) == 1
            if hit:
                ids.append(tok)
                spans.append((m.start(), m.end()))
    for a, b in sorted(spans, reverse=True):
        t = t[:a] + " " + t[b:]
    return list(dict.fromkeys(ids)), t


def find_industries(text: str) -> list[str]:
    t = _norm(text)
    out = []
    for ind, words in INDUSTRIES.items():
        if any(re.search(r"\b" + re.escape(w) + r"\b", t) for w in words):
            out.append(ind)
    return out


EXCLUDE_WORDS = (r"(?:other than|except(?: for)?|excluding|exclude|apart from|besides|outside(?: of)?|not(?: in| for| from)?|"
                 r"but not|non)")


def find_excluded_industries(text: str) -> list[str]:
    t = _norm(text)
    out = []
    for ind, words in INDUSTRIES.items():
        for w in words:
            if re.search(r"\b" + EXCLUDE_WORDS + r"[\s-]+(?:(?:the|in|for|of|from|any)\s+){0,2}" + re.escape(w) + r"\b", t):
                out.append(ind)
                break
    return out


def find_unsupported(text: str) -> list[dict]:
    t = _norm(text)
    out = []
    for attr, words in UNSUPPORTED_ATTRIBUTES.items():
        for w in words:
            if re.search(r"\b" + re.escape(w) + r"\b", t):
                out.append({"attribute": attr, "text": w})
                break
    return out


def parse_dates(text: str, year_hint: int | None) -> dict:
    t = _norm(text)
    out = {}
    iso = re.findall(r"\b(20\d\d-\d\d-\d\d)\b", t)
    if len(iso) >= 2:
        out["date_from"], out["date_to"] = sorted(iso)[:2]
    elif len(iso) == 1:
        if re.search(r"\b(?:after|since|from)\b", t):
            out["date_from"] = iso[0]
        elif re.search(r"\b(?:before|until|till|up to)\b", t):
            out["date_to"] = iso[0]
        else:
            out["date_from"] = out["date_to"] = iso[0]
    else:
        for name, mnum in MONTHS.items():
            m = re.search(r"\b(?:in|during|for|of)\s+" + name + r"(?:\s+(20\d\d))?\b", t)
            if m:
                year = int(m.group(1)) if m.group(1) else year_hint
                if year:
                    import calendar
                    last = calendar.monthrange(year, mnum)[1]
                    out["date_from"], out["date_to"] = f"{year}-{mnum:02d}-01", f"{year}-{mnum:02d}-{last:02d}"
                else:
                    out["_ambiguous"] = f"which year for {name}?"
                break
    if not any(k in out for k in ("date_from", "date_to", "_ambiguous")):
        m = re.search(r"\b(after|since|from|before|until|till|on)\b", t)
        d = parse_point_date(t, year_hint) if m else None
        if d:
            if m.group(1) in ("after", "since", "from"):
                out["date_from"] = d
            elif m.group(1) == "on":
                out["date_from"] = out["date_to"] = d
            else:
                out["date_to"] = d
    if re.search(r"\b(?:last|this|past|previous) (?:week|month|year|quarter)\b|\byesterday\b|\btoday\b", t):
        out["_relative"] = True
    return out


def _month_num(word: str) -> int:
    return [m[:3] for m in MONTHS].index(word[:3]) + 1


def _iso(y, mo, d) -> str | None:
    import datetime
    try:
        return datetime.date(int(y), int(mo), int(d)).isoformat()
    except (TypeError, ValueError):
        return None


def parse_point_date(t: str, year_hint: int | None) -> str | None:
    m = re.search(r"\b(20\d\d)[-/](\d\d?)[-/](\d\d?)\b", t)
    if m:
        return _iso(m.group(1), m.group(2), m.group(3))
    m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(" + MONTH_RE + r")\.?,?(?:\s+(20\d\d))?\b", t)
    if m:
        y = int(m.group(3)) if m.group(3) else year_hint
        return _iso(y, _month_num(m.group(2)), m.group(1)) if y else None
    m = re.search(r"\b(?:after|since|before|from|on|in|until|till|of|following)\s+(?:early\s+|mid\s+|late\s+)?(" + MONTH_RE +
                  r")\.?(?:\s+(\d{1,2})(?:st|nd|rd|th)?)?,?(?:\s+(20\d\d))?\b", t)
    if m:
        y = int(m.group(3)) if m.group(3) else year_hint
        return _iso(y, _month_num(m.group(1)), m.group(2) or 1) if y else None
    return None


NULL_EFFECT_RE = re.compile(r"\b(?:(?:do(?:es)?n'?t|do not|does not|never) (?:really )?(?:affect|matter|make (?:a|any) difference|"
                            r"influence|change|impact)|(?:have|has|show|shows|with) (?:no|zero) (?:clear |real |measurable )?"
                            r"(?:effect|impact|difference|influence)|makes? no difference|(?:irrelevant|unrelated) to)\b")


def parse_threshold(t: str) -> dict | None:
    m = THRESHOLD_RE.search(t)
    if not m:
        return None
    raw = m.group(2)
    v = float(raw) if raw[0].isdigit() else float(NUMBER_WORDS[raw])
    op = "lt" if m.group(1) in ("less than", "under", "below", "at most", "smaller than") else "gt"
    up = re.search(r"\b(?:rais\w*|increas\w*|higher|more likely|push\w* up|boost\w*|worsen\w*)\b", t)
    down = re.search(r"\b(?:reduc\w*|lower\w*|decreas\w*|cut\w*|fewer|less likely|prevent\w*)\b", t)
    direction = 1 if up and not down else -1 if down and not up else 0
    return {"value": v / 100, "op": op, "direction": direction, "text": m.group(0).strip()}


class QueryParser:
    def __init__(self, brands=(), intents=(), flagged=(), year_hint: int | None = None, has_dates: bool = True,
                 vocab: dict | None = None, account: dict | None = None, has_tenure: bool = False,
                 call_ids: set | None = None):
        self.brands = sorted({b.lower() for b in brands if b and b.lower() not in ("none", "nan")}, key=len, reverse=True)
        self.intents = sorted({i.lower() for i in intents if i and i.lower() not in ("none", "nan")}, key=len, reverse=True)
        self.flagged = set(flagged)
        self.year_hint = year_hint
        self.has_dates = has_dates
        self.vocab = vocab or {}
        self.account = account or {}
        self.has_tenure = has_tenure
        self.call_ids = call_ids

    @classmethod
    def from_corpus_calls(cls, calls, flagged=()) -> "QueryParser":
        year = None
        if "call_date" in calls.columns:
            d = calls["call_date"].dropna().astype(str)
            if len(d):
                year = int(d.str[:4].mode().iat[0])
        intents = calls["intent"].dropna().astype(str).unique() if "intent" in calls.columns else ()
        account = {f: sorted(set(calls[f].astype(str).str.lower()) - {"unknown", "nan", "none", "", "<na>"})
                   for f in ("tier", "plan", "segment") if f in calls.columns and f not in set(flagged)}
        return cls(calls["brand"].dropna().astype(str).unique(), intents, flagged, year,
                   "call_date" in calls.columns or "time_of_interaction" in calls.columns,
                   account={k: v for k, v in account.items() if v},
                   has_tenure="tenure_months" in calls.columns and "tenure_months" not in set(flagged),
                   call_ids=set(calls["transcript_id"].astype(str).str.lower()) if "transcript_id" in calls.columns else None)

    def account_filters(self, t: str, spec: QuerySpec) -> None:
        acc = self.account
        m = SELF_STATUS_RE.search(t)
        if m:
            w = m.group(1) or m.group(2) or "member"
            spec.filters["self_status"] = ["member" if w in ("loyalty", "loyal", "rewards") else w]
            t = t[:m.start()] + " " + t[m.end():]
        if acc.get("tier"):
            named = [v for v in acc["tier"] if re.search(r"\b" + re.escape(v) + r"\b", t)]
            if not named and re.search(r"\b(?:premium|vip|top[- ]tier|high[- ]value)\s+(?:customers?|members?|guests?|clients?)\b", t):
                named = [v for v in acc["tier"] if any(w in v for w in ("premium", "vip", "gold", "platinum", "diamond", "elite"))]
                if not named:
                    spec.ambiguous = spec.ambiguous or ("which tiers count as premium (the data has: " +
                                                        ", ".join(acc["tier"][:8]) + ")")
            if named:
                spec.filters["tier"] = named
        for f, words in (("plan", r"plans?|subscriptions?|packages?"), ("segment", r"segments?")):
            if acc.get(f) and re.search(r"\b(?:" + words + r")\b", t):
                named = [v for v in acc[f] if len(v) > 2 and re.search(r"\b" + re.escape(v) + r"\b", t)]
                if named:
                    spec.filters[f] = named
        if self.has_tenure:
            if re.search(r"\bnew (?:customers|clients|members|guests)\b", t):
                spec.filters["tenure"] = "new"
            elif re.search(r"\b(?:long[- ](?:time|standing|term)|loyal|existing) (?:customers|clients|members|guests)\b", t):
                spec.filters["tenure"] = "long"

    def find_change(self, t: str) -> tuple[dict | None, str]:
        when = parse_point_date(t, self.year_hint)
        cm = CHANGE_RE.search(t)
        if cm:
            what = cm.group(2).strip()
            news = re.match(r"(?:new|recent|updated|latest|revised|changed)\b", what) or re.search(
                r"\b(?:changes?|updates?|launch|roll-?out|merger|outage|reorg\w*)$", what)
            if news or cm.group(3).strip() or when:
                return {"what": what, "side": cm.group(1), "date": when}, t[:cm.start()] + " " + t[cm.end():]
        if when and CHANGE_VERB_RE.search(t):
            m = re.search(r"\b(after|since|before|following|from)\b", t)
            if m:
                return {"what": "", "side": m.group(1), "date": when}, t
        return None, t

    def parse(self, text: str) -> QuerySpec:
        t = _norm(text)
        call_ids, t = find_call_ids(t, self.call_ids)
        spec = QuerySpec(raw=text)
        brands = [b for b in self.brands if re.search(r"\b" + re.escape(b) + r"\b", t)]
        for b in brands:
            t = re.sub(r"\b" + re.escape(b) + r"\b", " ", t)
        t, lang = translate(t)
        t, slang = apply_slang(t)
        t, fixes = correct_spelling(t, self.vocab)
        t = re.sub(r"\s+", " ", t).strip()
        if lang:
            spec.notes.append({"kind": "language", "language": lang, "text": t})
        if fixes or slang:
            spec.notes.append({"kind": "reading", "items": [[a, b] for a, b in fixes + slang]})
        change, t = self.find_change(t)
        spans = event_spans(t)
        cond = condition_split(t, spans)
        t_beh = t
        if cond:
            for s0, e0, code in spans:
                if code in cond[0]:
                    t_beh = t_beh[:s0] + " " * (e0 - s0) + t_beh[e0:]
        events = [(s0, code) for s0, _, code in spans]
        ev_codes = list(dict.fromkeys(e for _, e in events))
        behs = find_behaviours(t_beh)
        beh_codes = list(dict.fromkeys(b for _, b in behs))
        for qt, pat in TYPE_PATTERNS:
            if re.search(pat, t):
                spec.question_type = qt
                break
        notices = []
        primary = [e for e in ev_codes if e in PRIMARY_EVENTS]
        secondary = [e for e in ev_codes if e not in PRIMARY_EVENTS]
        if cond:
            spec.event = cond[1]
            spec.filters["with_event"] = list(cond[0])
        elif secondary:
            spec.event = secondary[0]
        elif len(primary) == 1:
            spec.event = primary[0]
        elif len(primary) > 1:
            spec.event = primary[0]
            first = {e: min(p for p, x in events if x == e) for e in primary}
            between = t[first[primary[0]]:first[primary[1]]]
            linked = bool(EVENT_LINK_RE.search(between) or SEQUENCE_RE.search(t))
            if linked and (spec.question_type not in ("why", "what_to_change", "issues") or
                           (spec.question_type == "why" and not beh_codes)):
                spec.question_type = "event_link"
                spec.compare = {"dimension": "event", "values": primary[:2]}
                notices.append({"attribute": "effects between events",
                                "text": " and ".join(EVENTS[e].plural for e in primary[:2])})
            elif spec.question_type in ("compare", "how_often", "trend") or EVENT_COMPARE_RE.search(t):
                spec.compare = {"dimension": "event", "values": primary}
                spec.question_type = "compare"
            elif spec.question_type in ("why", "what_to_change", "effect_of", "unknown") and SHARED_RE.search(t):
                spec.compare = {"dimension": "event", "values": primary, "asked": spec.question_type}
                spec.question_type = "shared"
            else:
                names = [EVENTS[e].plural for e in primary]
                notices.append({"attribute": "two events", "text": " and ".join(names), "first": names[0],
                                "second": names[1]})
        inds = find_industries(t)
        excluded = find_excluded_industries(t)
        if excluded:
            kept = [i for i in inds if i not in excluded]
            inds = kept or [i for i in INDUSTRIES if i not in excluded]
        if inds:
            if spec.question_type == "compare" and len(inds) > 1:
                spec.compare = {"dimension": "industry", "values": inds}
            else:
                spec.filters["industry"] = inds
        if brands:
            spec.filters["brand"] = brands
        self.account_filters(t, spec)
        acc_rank = RANK_ACCOUNT_RE.search(t)
        acc_dim = next((g.rstrip("s").split()[0] for g in (acc_rank.groups() if acc_rank else ()) if g), None)
        acc_dim = "tier" if acc_dim == "membership" else acc_dim
        if spec.question_type == "compare" and not spec.compare:
            dim = ("industry" if RANK_INDUSTRY_RE.search(t) else "brand" if RANK_BRAND_RE.search(t) else
                   acc_dim if acc_dim in self.account else "event" if RANK_EVENT_RE.search(t) else None)
            if dim:
                spec.compare = {"dimension": dim, "values": list(PRIMARY_EVENTS) if dim == "event" else [], "rank": True}
                spec.filters.pop(dim, None)
                if dim == "event" and spec.event is None:
                    spec.event = PRIMARY_EVENTS[0]
                if WHY_RE.search(t):
                    spec.compare["explain_top"] = True
            else:
                spec.ambiguous = ("which groups to compare: two industries (for example hotel vs airline calls), two "
                                  "events (for example escalations vs refunds), or a ranking (for example 'which industry "
                                  "has the most escalations?')")
        intents = [i for i in self.intents if re.search(r"\b" + re.escape(i) + r"\b", t)]
        if intents:
            if {"intent", "intent_key"} & self.flagged:
                spec.declined_filters.append({"field": "intent", "value": intents[0],
                                              "reason": "the leakage audit flagged this field: it may describe the call's outcome",
                                              "alternative": "industry from the opening turns"})
            else:
                spec.filters["intent"] = intents
        if re.search(r"\b(?:reason for (?:the )?call|call reason|reason_for_call)\b", t):
            spec.declined_filters.append({"field": "reason_for_call",
                                          "reason": "free-text reasons may be written after the call and can contain the outcome",
                                          "alternative": "industry from the opening turns, or the words customers use in the opening"})
        if change:
            spec.change = change
            spec.question_type = "trend"
            if spec.compare and spec.compare.get("dimension") != "event":
                spec.compare = None
            if spec.ambiguous.startswith("which groups to compare"):
                spec.ambiguous = ""
            if not self.has_dates or {"time_of_interaction", "call_date"} & self.flagged:
                spec.declined_filters.append({"field": "date", "reason": "call dates are not available as a usable field",
                                              "alternative": "no before/after comparison"})
        else:
            dates = parse_dates(t, self.year_hint)
            if dates.get("_relative"):
                spec.ambiguous = spec.ambiguous or "relative dates ('last week') need an explicit date range"
            if dates.get("_ambiguous"):
                spec.ambiguous = spec.ambiguous or dates["_ambiguous"]
            dvals = {k: v for k, v in dates.items() if not k.startswith("_")}
            if dvals:
                if not self.has_dates or {"time_of_interaction", "call_date"} & self.flagged:
                    spec.declined_filters.append({"field": "date", "reason": "call dates are not available as a usable field",
                                                  "alternative": "no date filter"})
                else:
                    spec.filters.update(dvals)
        if spec.question_type in ("issues", "what_to_change"):
            behs = [(p, b) for p, b in behs if not re.match(r"(?:fix|solv|resolv|remed)", t_beh[p:p + 6])]
            beh_codes = list(dict.fromkeys(b for _, b in behs))
        if beh_codes and spec.question_type != "issues":
            spec.behaviour = beh_codes[0]
        m = re.search(r"\b(?:factor\s*#?\s*(\d+)|f(\d+)\b|(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th) (?:factor|one|reason))", t)
        if m:
            if m.group(2):
                spec.factor_ref = f"F{m.group(2)}"
            else:
                spec.factor_ref = f"#{m.group(1) or ORDINALS[m.group(3)]}"
        cf = COUNTERFACTUAL_RE.search(t)
        if cf and SINGLE_CALL_RE.search(t):
            notices.append({"attribute": "single-call counterfactual", "text": cf.group(0).strip()})
        mod = EFFECT_MOD_RE.search(t)
        if mod and beh_codes and (len(beh_codes) >= 2 or re.match(r"(?:only|depend|differ|vary|varies|change)", mod.group(0))):
            notices.append({"attribute": "effect modification", "text": mod.group(0).strip()})
        th = parse_threshold(t)
        nm = NULL_EFFECT_RE.search(t)
        if not th and nm and spec.event and (not beh_codes or re.search(r"\b(?:which|what) (?:behaviou?rs?|factors?|"
                                                                          r"actions?|things?)\b", t)):
            spec.threshold = {"value": 0.0, "op": "null", "direction": 0, "text": nm.group(0), "target": "effect"}
            spec.behaviour = None
            beh_codes = []
            if spec.question_type in ("effect_of", "unknown"):
                spec.question_type = "why"
            notices.append({"attribute": "no clear effect", "text": nm.group(0)})
        if th:
            effect = bool(re.search(r"\bby (?:more than|over|above|at least|greater than|bigger than|larger than|less than|"
                                    r"under|below|at most|smaller than)\b", t) or beh_codes or
                          re.search(r"\b(?:behaviou?rs?|factors?|effects?|impacts?)\b", t))
            th["target"] = "effect" if effect and spec.question_type not in ("compare", "how_often", "trend") else "rate"
            spec.threshold = th
            notices.append({"attribute": "effect-size threshold" if th["target"] == "effect" else "rate threshold",
                            "text": th["text"]})
        spec.leading = bool(LEADING_RE.search(t))
        spec.presuppositions = self.presuppositions(t_beh, behs, events, spec.leading) if not cond else []
        if spec.presuppositions and spec.question_type in ("unknown", "why", "effect_of", "how_often"):
            spec.question_type = "effect_of" if spec.question_type != "why" else "why"
            if spec.behaviour is None:
                spec.behaviour = spec.presuppositions[0]["behaviour"]
        if spec.question_type in ("unknown", "how_often") and spec.event and not beh_codes and DIRECTION_RE.search(t):
            spec.question_type = "trend"
        if spec.question_type == "unknown" and spec.behaviour and spec.event:
            spec.question_type = "effect_of"
        if spec.question_type == "unknown" and spec.event:
            spec.question_type = "why"
        policy = max((m.group(0) for m in POLICY_RE.finditer(t)), key=len, default=None)
        if policy and spec.event:
            notices.append({"attribute": "whole-call policy", "text": policy})
        spec.unsupported = find_unsupported(t) + notices
        if spec.filters.get("tier") or spec.filters.get("self_status") or (spec.compare or {}).get("dimension") == "tier":
            spec.unsupported = [u for u in spec.unsupported if u.get("attribute") != "customer tier"]
        if spec.filters.get("tenure"):
            spec.unsupported = [u for u in spec.unsupported if u.get("attribute") != "account age"]
        if any(spec.filters.get(k) for k in ("plan", "segment")) or (spec.compare or {}).get("dimension") in ("plan", "segment"):
            spec.unsupported = [u for u in spec.unsupported if u.get("attribute") != "plan or segment"]
        elif any(u.get("attribute") == "plan or segment" for u in spec.unsupported) and (self.account.get("plan") or
                                                                                          self.account.get("segment")):
            spec.unsupported = [u for u in spec.unsupported if u.get("attribute") != "plan or segment"]
            have = [f"{k}: " + ", ".join(self.account[k][:8]) for k in ("plan", "segment") if self.account.get(k)]
            spec.ambiguous = spec.ambiguous or ("which plan or segment (the data has " + "; ".join(have) + ")")
        if spec.event is None and not spec.behaviour and not spec.factor_ref and not spec.unsupported and (
                (spec.question_type in ("what_to_change", "why") and
                 re.search(r"\b(?:agents?|behaviou?rs?|factors?|staff|reps?|we|our team)\b", t)) or
                (spec.question_type == "unknown" and re.search(r"\b(?:behaviou?rs?|factors?)\b", t))):
            spec.event = PRIMARY_EVENTS[0]
            spec.compare = {"dimension": "event", "values": list(PRIMARY_EVENTS), "asked": spec.question_type}
            spec.question_type = "shared"
        if spec.event is None and spec.behaviour and not spec.factor_ref and spec.question_type in (
                "why", "how_often", "unknown", "examples", "trend", "what_to_change", "effect_of"):
            spec.question_type = "behaviour"
            spec.presuppositions = []
        if spec.event is None and not spec.behaviour and not spec.factor_ref:
            if HELP_RE.search(t) and spec.question_type == "unknown":
                spec.question_type = "help"
            elif OVERVIEW_RE.search(t) or spec.question_type == "issues" or (
                    any(spec.filters.get(k) for k in ("industry", "brand", "tier", "plan", "segment", "tenure", "self_status"))
                    and spec.question_type in ("unknown", "why", "how_often", "examples")):
                spec.question_type = "overview"
        if spec.event is None and spec.question_type not in ("describe_factor", "behaviour", "overview", "help") and \
                not spec.unsupported:
            spec.ambiguous = spec.ambiguous or "which business event (escalation, refund or churn) is the question about?"
        if call_ids:
            spec.filters = {"call": call_ids[:1]}
            spec.question_type, spec.compare, spec.threshold, spec.change, spec.ambiguous = "call", None, None, None, ""
            spec.presuppositions, spec.factor_ref = [], None
            spec.unsupported = [u for u in spec.unsupported if u.get("attribute") not in ("two events", "rate threshold",
                                                                                      "effect-size threshold")]
            if spec.event and spec.event not in PRIMARY_EVENTS + ("RISK",):
                spec.event = COND_PARENT_EVENT.get(spec.event, spec.event)
        return spec

    @staticmethod
    def presuppositions(t: str, behs, events, leading: bool) -> list[dict]:
        if not behs or not events:
            return []
        assertive = bool(ASSERTIVE_RE.search(t)) or leading
        if not assertive:
            return []
        out = []
        for bpos, b in behs:
            after = [(p, e) for p, e in events if p > bpos]
            if not after:
                continue
            epos, e = after[0]
            seg = t[bpos:epos]
            if re.search(r"\b" + PRESUPPOSE_DOWN + r"\b", seg):
                direction = -1
            elif re.search(r"\b" + PRESUPPOSE_UP + r"\b", seg):
                direction = 1
            else:
                continue
            if e in PRIMARY_EVENTS or e in EVENTS:
                out.append({"behaviour": b, "event": e, "direction": direction, "strength": "causal"})
        return out


LLM_SPEC_SCHEMA = {
    "type": "object",
    "properties": {
        "event": {"type": "string", "enum": list(EVENTS) + ["none"]},
        "question_type": {"type": "string", "enum": list(QUESTION_TYPES)},
        "industry": {"type": "array", "items": {"type": "string", "enum": list(INDUSTRIES)}},
        "behaviour": {"type": "string", "enum": [b for b, d in BEHAVIOURS.items() if not d.negative_control] + ["none"]},
        "presupposition_behaviour": {"type": "string", "enum": [b for b, d in BEHAVIOURS.items() if not d.negative_control] + ["none"]},
        "presupposition_direction": {"type": "integer", "enum": [-1, 0, 1]},
        "leading": {"type": "boolean"},
    },
    "required": ["event", "question_type", "industry", "behaviour", "presupposition_behaviour", "presupposition_direction", "leading"],
    "additionalProperties": False,
}


LLM_NORMALIZE_SCHEMA = {
    "type": "object",
    "properties": {"english": {"type": "string"}, "language": {"type": "string"}},
    "required": ["english", "language"],
    "additionalProperties": False,
}


def unsure(spec: QuerySpec) -> bool:
    return spec.event is None and spec.behaviour is None and not spec.factor_ref


def llm_normalize(llm, text: str) -> dict:
    system = ("Rewrite a manager's question about customer-service calls as one plain English question. Fix spelling, "
              "translate any other language, and replace slang with plain words (for example 'demand the boss' -> 'ask "
              "for a supervisor', 'jump ship' -> 'threaten to leave'). Keep every condition, filter, date and number. "
              "Do not answer the question. language = the language the question was written in.")
    return llm.json_call(system=system, user=text, schema=LLM_NORMALIZE_SCHEMA, purpose="normalize_query", effort="low")


def llm_parse(llm, text: str, rules: QuerySpec) -> QuerySpec:
    system = ("Map a manager's question about customer-service calls to fixed slots. Use only the allowed values. "
              "event: ESC escalation, REF refund episode, CHURN churn threat (or a secondary event). "
              "presupposition_*: a causal claim the question takes for granted (e.g. 'why does empathy cause escalations' "
              "-> empathy, +1); 'none'/0 when the question only asks.")
    out = llm.json_call(system=system, user=text, schema=LLM_SPEC_SCHEMA, purpose="parse_query", effort="low")
    spec = QuerySpec.from_dict(rules.to_dict())
    spec.parser = "llm+rules"
    spec.event = None if out["event"] == "none" else out["event"]
    spec.question_type = out["question_type"]
    if out["industry"]:
        spec.filters["industry"] = out["industry"]
    spec.behaviour = None if out["behaviour"] == "none" else out["behaviour"]
    spec.leading = bool(out["leading"]) or rules.leading
    if out["presupposition_behaviour"] != "none" and out["presupposition_direction"] != 0 and spec.event:
        spec.presuppositions = [{"behaviour": out["presupposition_behaviour"], "event": spec.event,
                                 "direction": int(out["presupposition_direction"]), "strength": "causal"}]
    return spec
