from __future__ import annotations

import re
import unicodedata

QUOTE_MAP = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'", "\u2032": "'", "\u00b4": "'", "`": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u2033": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u00a0": " ",
})
ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
LITERAL_ESCAPE_RE = re.compile(r"\\[nrt]")
WS_RE = re.compile(r"\s+")
WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
STRAY_MARKUP_RE = re.compile(r"[*\[\]<>{}|]")


def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(QUOTE_MAP)
    s = ZERO_WIDTH_RE.sub("", s)
    s = LITERAL_ESCAPE_RE.sub(" ", s)
    s = CONTROL_RE.sub(" ", s)
    s = s.lower()
    s = re.sub(r"\buh-huh\b", "uh huh", s)
    s = re.sub(r"\b(?:mm-hmm|mm-hm|mhm-hmm|um-hum|mm-mm)\b", "mm hmm", s)
    return WS_RE.sub(" ", s).strip()


# ---- filled pauses, repetitions, hedges -------------------------------------------------------
# "uh" is not a filler when it is part of the backchannel "uh huh"; "er" is excluded (ambiguous with "ER").
FILLED_PAUSE_RE = re.compile(r"\b(?:u+m+|u+h+m*(?!\s+huh\b)|e+r+m+|h+m+|a+h+)\b")
NUMBER_WORDS = set(("zero oh one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
                    "fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy "
                    "eighty ninety hundred thousand double triple").split())
REP_KEEP = {"bye", "very", "really", "ha", "haha", "hey", "hi", "no", "yes", "yeah", "okay", "ok", "so", "bla"}
REP_BIGRAM_RE = re.compile(r"\b([a-z']+ [a-z']+)(?: \1\b)+")
# a repeated word whose last copy starts a discourse marker is not a stutter ("thank you you know for ..."):
# collapsing it would let the cue view strip "you know" and destroy "thank you"
REP_WORD_RE = re.compile(r"\b([a-z']+)(?: \1\b)+(?! (?:know|mean)\b)")
HEDGE_RE = re.compile(r"\b(?:i guess|i suppose|maybe|perhaps|probably|i'm not sure|i am not sure|not sure|"
                      r"i don't know|i do not know|kind of|sort of|i think)\b")
DISCOURSE_MARKER_RE = re.compile(r"\b(?:you know|i mean)\b")


def _is_protected(token_or_bigram: str) -> bool:
    """Spelled-out numbers / single letters are ids ("four four five", "c c one"): never collapse them."""
    return any(w in NUMBER_WORDS or w.isdigit() or (len(w) == 1 and w not in ("i", "a"))
               for w in token_or_bigram.split())


def _collapse(m: re.Match) -> str:
    return m.group(0) if _is_protected(m.group(1)) else m.group(1)


def count_filled_pauses(text: str) -> int:
    return len(FILLED_PAUSE_RE.findall(text))


def count_repetitions(text: str) -> int:
    n = sum(1 for m in REP_WORD_RE.finditer(text) if m.group(1) not in REP_KEEP and not _is_protected(m.group(1)))
    return n + sum(1 for m in REP_BIGRAM_RE.finditer(text) if not _is_protected(m.group(1)))


def make_clean_text(text: str) -> str:
    t = FILLED_PAUSE_RE.sub(" ", text)
    t = WS_RE.sub(" ", t).strip()
    t = REP_BIGRAM_RE.sub(_collapse, t)
    t = REP_WORD_RE.sub(_collapse, t)
    t = WS_RE.sub(" ", t).strip()
    return t if t else text  # a turn that is only "um" keeps its verbatim form


# ---- stage directions / non-verbal markers ----------------------------------------------------
_PAREN_STAGE_WORDS = (r"(?:long |brief |short |slight |a )?(?:pause[sd]?|pausing|silence|sighs?|sighing|laugh(?:s|ing|ter)?|"
                      r"chuckl(?:e|es|ing)|inaudible|unintelligible|cross ?talk|background noise|noise|static|"
                      r"hold music|music|on hold|holding|typing|keyboard(?: typing)?|clears throat|cough(?:s|ing)?|"
                      r"after a (?:moment|pause|while|beat|few seconds)|a moment later|moments later|transferr?ing|"
                      r"transfers?|call (?:ended|ends|disconnected|drops|dropped)|end of call|beep|ringing|dial tone)")
STAGE_RES = [
    re.compile(r"\*\s*([^*]{1,80}?)\s*\*"),                  # *transferring call*
    re.compile(r"\[\s*([^\]]{1,200}?)\s*\]"),                # [inaudible], [note: …]
    re.compile(r"<\s*([^>]{1,80}?)\s*>"),                    # <laughs>
    re.compile(r"\(\s*(" + _PAREN_STAGE_WORDS + r"[^)]{0,40}?)\s*\)"),  # (pause) – only known stage words
]
NONVERBAL_TYPES = [
    ("CALL_END", re.compile(r"\b(?:call (?:ended|ends|end|disconnected|dropped|drops|terminated)|end of (?:the )?(?:call|transcript|conversation|recording)|hangs? up|hung up|disconnect(?:ed|s)?)\b")),
    ("TRANSFER", re.compile(r"\btransfer")),
    ("HOLD", re.compile(r"\b(?:hold|holding|music)\b")),
    ("PAUSE", re.compile(r"\b(?:pause[sd]?|pausing|silence|silent|moments?|beat|wait(?:ing)?|later|while|seconds)\b")),
    ("SIGH", re.compile(r"\bsigh")),
    ("LAUGH", re.compile(r"\b(?:laugh|chuckl|giggl)")),
    ("NOISE", re.compile(r"\b(?:inaudible|unintelligible|cross ?talk|noise|static|garbled|asr|unclear|mumbl|beep|ring|cough|clears throat|dial tone)")),
    ("TYPING", re.compile(r"\b(?:typing|keyboard|click)")),
    ("NOTE", re.compile(r"^(?:system note|note|notes|summary|system|agent note|annotator|comment|analysis|key events?|outcome|disposition|survey|tag|label|sentiment)\b")),
]
CALL_END_TEXT_RE = re.compile(
    r"^(?:the )?(?:call (?:ended|ends|end|disconnected|dropped|terminated|concluded)|end of (?:the )?(?:call|transcript|conversation|recording)|"
    r"(?:customer|caller|agent) (?:hung up|hangs up|disconnected)|transcript ends?|conversation ended|line disconnected)\W*$")


def classify_stage(content: str) -> str:
    c = content.lower().strip()
    for name, rx in NONVERBAL_TYPES:
        if rx.search(c):
            return name
    return "OTHER"


def extract_stage_directions(text: str):
    """Return (text_without_markers, [{'type','raw'}...], [inline_note_text...])."""
    events, notes = [], []

    def _grab(m: re.Match) -> str:
        content = m.group(1).strip()
        kind = classify_stage(content)
        if kind == "NOTE":
            notes.append(content)
        else:
            events.append({"type": kind, "raw": content})
        return " "

    for rx in STAGE_RES:
        text = rx.sub(_grab, text)
    text = STRAY_MARKUP_RE.sub(" ", text)
    return WS_RE.sub(" ", text).strip(), events, notes

CUE_DEFS = {
    # agent-side moves
    "hold_request": ("Agent", r"\b(?:(?:one|a|just a|just one|a quick|a brief|give me a|give me one)\s+(?:moment|minute|min|second|sec)s?\b|"
                              r"please hold|hold on|bear with me|(?:let me|i'll|i will|i'm going to|i am going to|allow me to)\s+(?:just\s+|quickly\s+)?"
                              r"(?:check|look|pull|see|verify|review|investigate|find|access|bring up|go through)\b|"
                              r"while i (?:check|look|pull|review|verify|see)|(?:put|place) you on (?:a )?(?:brief |short |quick )?hold)"),
    "hold_return": ("Agent", r"\b(?:thank(?:s| you)(?: so much| very much)? for (?:holding|waiting|your patience|being patient|bearing with me|hanging on)|"
                             r"sorry (?:for|about) (?:the|that) (?:wait|delay|hold)|sorry (?:for|about) keeping you (?:on hold|waiting)|appreciate your patience)\b"),
    "apology": ("Any", r"\b(?:sorry|apologi[sz]e|apologi[sz]ing|apologies)\b"),
    "empathy": ("Agent", r"\b(?:i (?:completely |totally |really |fully |absolutely )?understand|i can (?:imagine|see how|see why|understand)|"
                         r"(?:that|this|it) (?:must be|sounds|is|can be) (?:really |so |very |incredibly |quite |a bit |pretty )?"
                         r"(?:frustrating|stressful|difficult|upsetting|annoying|inconvenient|concerning|hard|worrying|disappointing)|"
                         r"i hear you|i know how (?:frustrating|stressful|difficult|upsetting)|i(?:'m| am) (?:so |really |very )?sorry to hear)\b"),
    "refusal": ("Agent", r"\b(?:unfortunately|i(?:'m| am) afraid|(?:i|we) (?:can't|cannot|can not|won't be able|will not be able|am unable|are unable|"
                         r"am not able|are not able|don't have the ability|do not have the ability)|(?:not|isn't|is not|aren't|are not) "
                         r"(?:eligible|possible|covered|refundable|allowed|permitted)|(?:against|per|according to|due to|under) (?:our |the |company )?"
                         r"polic(?:y|ies)|non-?refundable|no exceptions?)\b"),
    "offer_solution": ("Agent", r"\b(?:what i can do|i can (?:offer|provide|give|issue|waive|credit|refund|upgrade|rebook|replace|send|arrange|schedule|"
                                r"apply|process|extend|reverse|expedite)|i(?:'ve| have| will|'ll) (?:gone ahead and )?(?:offered|issued|waived|credited|"
                                r"refunded|upgraded|rebooked|replaced|sent|arranged|scheduled|applied|processed|extended|reversed|expedited|added|flagged)|"
                                r"as a (?:small )?(?:courtesy|goodwill gesture)|we can offer)\b"),
    "agent_escalation": ("Agent", r"\b(?:escalat(?:e|ed|ing|ion)|(?:my|a|the|our) (?:supervisor|manager|team lead(?:er)?|senior (?:agent|representative|colleague)))\b"),
    "agent_transfer": ("Agent", r"\b(?:transfer(?:ring)? (?:you|your call|the call|this call)|(?:connect|put) you (?:through )?(?:to|with) (?:a|the|my|our|someone)|"
                                r"(?:another|the relevant|the appropriate|a different|a specialized|our) (?:department|team)|(?:a|our|the) specialist)\b"),
    # customer-side states and intents
    "escalation_request": ("Customer", r"\b(?:(?:speak|talk|chat)(?:ing)? (?:to|with) (?:(?:a|your|the) )?(?:supervisor|manager|superior|boss)|"
                                       r"(?:speak|talk) (?:to|with) (?:someone|somebody) (?:else|senior|higher(?: up)?|in charge|more senior|with (?:more )?authority)|"
                                       r"(?:get|want|need) (?:a|your|the) (?:supervisor|manager)|escalate (?:this|it|my (?:case|issue|complaint|claim|request|problem)))\b"),
    "churn_intent": ("Customer", r"\b(?:(?:cancel(?:l?ing|l?ed|s)?|clos(?:e|es|ed|ing)|terminat(?:e|es|ed|ing)|end(?:s|ed|ing)?|discontinu(?:e|es|ed|ing)|"
                                 r"drop(?:s|ped|ping)?) (?:my|the|our) (?:\w+ )?(?:account|policy|subscription|service|"
                                 r"membership|contract|coverage|plan)|switch(?:ing)? (?:over )?(?:to )?(?:a |an |another |some )?(?:different |new |other )?"
                                 r"(?:provider|carrier|company|bank|insurer|airline|hotel chain|brand|competitor)s?|(?:take|taking|move|moving) my business|"
                                 r"(?:leave|leaving|quit|quitting) (?:you guys|your (?:company|service|bank|airline|network))|"
                                 r"(?:not|won't|will not|don't want to|do not want to|not going to) renew|(?:go|going|went) with (?:a |another |the )?"
                                 r"(?:competitor|other (?:company|provider|carrier|airline|bank|insurer))|(?:considering|thinking (?:about|of)) "
                                 r"(?:switching|leaving|cancell?ing|other (?:providers|options|companies|carriers|airlines|banks|insurers)))\b"),
    "refund": ("Any", r"\b(?:refund(?:s|ed|ing|able)?|reimburs(?:e|ed|ement|ing)|money back|charge ?back|compensat(?:e|ed|ion)|"
                      r"(?:travel|account|store) credit|credit (?:it |that )?back)\b"),
    "negative_emotion": ("Customer", r"\b(?:frustrat\w*|annoy\w*|upset|angry|mad|furious|ridiculous|unacceptable|disappoint\w*|terrible|horrible|"
                                     r"awful|worst|fed up|sick (?:and tired )?of|tired of|waste of (?:my )?time|not happy|unhappy|stress(?:ed|ful)?|"
                                     r"outrag\w*|infuriat\w*|irritat\w*|livid|absurd|nightmare|pathetic|useless|incompetent|unbelievable|disgusted|appalled)\b"),
    "confusion": ("Customer", r"\b(?:i(?:'m| am) (?:(?:a bit|a little|kind of|so|really|very) )?(?:confused|lost)|not sure i (?:follow|understand)|"
                              r"i (?:don't|do not|didn't|did not) (?:understand|get it|follow|get what)|what do you mean|what does that mean|"
                              r"that(?:'s| is) not what i (?:said|asked|meant)|(?:can|could) you (?:please )?(?:repeat|explain|clarify|say that again|rephrase)|"
                              r"(?:didn't|did not) (?:catch|hear|understand|get) that|makes? no sense|(?:doesn't|does not) make (?:any )?sense|"
                              r"pardon|come again|you(?:'re| are) not (?:listening|understanding|hearing me))\b"),
    "repeat_contact": ("Customer", r"\b(?:i(?:'ve| have)? already (?:told|said|explained|gave|given|sent|provided|called|tried|done)|as i (?:already )?"
                                   r"(?:said|mentioned|explained|told you)|like i (?:said|told you|mentioned)|for the (?:second|third|fourth|fifth) time|"
                                   r"(?:called|calling|contacted|reached out)(?: you(?: guys)?)? (?:back |in )?(?:again|multiple times|several times|many times|"
                                   r"twice|three times|so many times|before)|(?:this is|it's) (?:my|the) (?:second|third|fourth|fifth) (?:call|time)|"
                                   r"(?:second|third|fourth|fifth) time i(?:'ve| have)? called|every time i call|keep (?:calling|having to call))\b"),
    "issue_persistence": ("Customer", r"\bstill (?:hasn't|has not|haven't|have not|isn't|is not|not|no|doesn't|does not|don't|do not|can't|cannot|waiting|nothing|broken|down|pending|under review)\b"),
    "competitor_mention": ("Customer", r"\b(?:competitors?|competition|other (?:providers?|carriers?|companies|airlines?|banks?|insurers?|insurance companies|"
                                       r"hotels?|brands?|stores?)|(?:another|a different) (?:provider|carrier|company|airline|bank|insurer|hotel|brand|store))\b"),
}
CUES = {name: (scope, re.compile(p)) for name, (scope, p) in CUE_DEFS.items()}
DM_STRIP_RE = re.compile(r"\b(?:you know|i mean|like)\b")


def cue_view(clean: str) -> str:
    """text used for cue matching: text_clean without discourse markers inserted mid-phrase."""
    return WS_RE.sub(" ", DM_STRIP_RE.sub(" ", clean)).strip()


LEADING_DM_RE = re.compile(r"^(?:(?:so|and|but|well|okay|ok|alright|all right|oh|hi|hello|hey|yeah|yes|no|right|sure|now|then|also|just|"
                           r"sorry|like|you know|i mean|great|perfect|thanks|thank you)\s+)+")
QUESTION_START_RE = re.compile(r"^(?:what|why|how|when|where|which|who|whom|whose|is|are|was|were|am|do|does|did|can|could|would|will|"
                               r"should|shall|may|might|have|has|isn't|aren't|wasn't|weren't|don't|doesn't|didn't|can't|couldn't|"
                               r"wouldn't|won't|shouldn't|haven't|hasn't)\b")
QUESTION_ANY_RE = re.compile(  # question frames that also occur mid-turn (text has no punctuation)
    r"\b(?:(?:can|could|would|will) you (?:please |just |also )?(?:tell|explain|check|confirm|help|send|let|give|show|walk|clarify|"
    r"repeat|look|provide|verify|spell|hold)|(?:how|what) (?:can|may) i (?:help|assist|do)|is there (?:anything|any|a way|something)|"
    r"would you like|do you (?:know|have|need|want|mind|remember)|(?:may|can|could) i (?:have|get|ask|confirm|put|place)|"
    r"is (?:that|this|it) (?:right|correct|okay|possible|true)|(?:when|why|how long|how much|how many) (?:is|was|are|were|will|would|"
    r"did|do|does|can|should)|i was wondering|any chance|does that (?:make sense|work|help|sound))\b")
BACKCHANNEL_RE = re.compile(r"^(?:(?:uh huh|mm hmm|mhm|mm|hmm|um|uh|yeah|yep|yes|yup|okay|ok|right|sure|alright|all right|i see|got it|"
                            r"gotcha|oh|ah|go on|go ahead|understood|mm-hmm)\s*)+$")


def is_question(clean: str, raw: str) -> bool:
    if "?" in raw:
        return True
    t = LEADING_DM_RE.sub("", clean)
    return bool(QUESTION_START_RE.match(t) or QUESTION_ANY_RE.search(clean))


CUE_NAMES = list(CUE_DEFS)
CUE_COLS = [f"cue_{n}" for n in CUE_NAMES]


def pipeline_text_views(raw_text: str) -> tuple[str, str]:
    text, _events, _notes = extract_stage_directions(normalize_text(raw_text))
    return text, make_clean_text(text)


def cues_for_turn(text_clean: str, party: str) -> set[str]:
    view = cue_view(text_clean)
    return {name for name, (scope, rx) in CUES.items() if scope in ("Any", party) and rx.search(view)}
