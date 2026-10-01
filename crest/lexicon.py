from __future__ import annotations

import re

SPELL_VOCAB = tuple("""
    escalate escalates escalated escalating escalation escalations supervisor supervisors manager managers refund refunds
    refunded refunding reimbursement reimburse compensation compensate chargeback chargebacks churn churned churning cancel cancels
    cancelled canceled cancelling canceling cancellation cancellations threaten threatens threatened threatening threat threats
    switch switching leave leaving quit quitting complain complains complaint complaints complaining customers customer callers caller
    agents agent calls often frequently compare comparison examples example trend trends changed reduce prevent drives drivers causes
    cause reasons reason linked happen happens percentage share rates which industry industries behaviours behaviors behaviour
    behavior apology apologies apologise apologize apologising apologizing empathy empathetic refusal refusals refuse refused refusing
    holds frustration frustrated angry anger confusion confused hesitation hesitations hesitate hesitant transfer transfers
    transferred solution solutions competitor competitors repeated hotel hotels airline airlines flight flights telecom insurance banking
    retail ecommerce hospitality money policy policies denied premium bank banks hold holding sorry delays waiting
""".split())
SPELL_KEEP = frozenset("""
    accents adeline agendas airlift airliner airliners airplane airplanes airtime alger analogies analogy ander ange 
    angel angered angers angler anglers angrier angrily anker apologised apologises apologist apologists apologized 
    apologizes arent argent auger augment augments avenger back backing backs baek bagging bailing baiting baking balding 
    balk balling bana banc band banding bands bandung bane bang banging bangs bani bankers banksy banning bans bark 
    barking barks barring bashing bask basking bathing batting bawling behaving behavioral behavioural bending benning 
    binding blacking blank blanks blinking bonding booking braking branding bucking bulking bunk bunks bunting cackling 
    calder caldera caliber caliper calipers call calle called callous callus cally calmer calms calvert campers campuses 
    cancer cancers candles canoeing careers cartels carters case cases casters caucuses causa caused cellars cells 
    chained chaining chaired chalked chalmers champlain chancel chances change changeling changer changers changes 
    channel channeled channeling channelled channels channing chanted chaplain chaplains charged charger charges charging 
    charing charmed charming charred charted charting chatted chiller chirping chuan chucked chucking chuffed chugging 
    chun chutney classes clause clauses collars collier colliers collusion commendation compact companion company 
    compared compares comparisons compass compassion compensated compensates compensating compete competition 
    competitions compile complacent complainant complainants complained compliant complies complying compose compute 
    comrade conceal concealed concealing conceals conceded conceding conclusion concussion condensate condensation 
    confessed confession confided confined confucian confuse confuses confusing conjured consumed coolers corning courses 
    coursing courted courting cranked crawler cringed cruises crushes cunning curbing curlers curling cursing curving 
    customary customs danvers decays decided decried defied defiled defined delay delayed delivers denier deniers denies 
    denoted dented deploys deprives derided derived derives desired devised divers diverse diverts dives drawers dries 
    drifters drillers drinkers drive drivel driven driver droves empathic escalade escalator escalators escapade 
    escapades examine examines excavate excavated excavating excavation excavations fight fights freight frequency 
    frequent frequented fright frustrate frustrates frustrating frustrations habitation halpern halting halving hampden 
    hampers handing hapless happend happened happier hardens harding harpers heading held helping herding heritage 
    hesitated hesitates hesitating hoarding hocking hogging hola holders holdin holdings hole holed holes holi hollins 
    holm holo holt holy honking hood hoods hooking hooters hoppers hopping hostel hostels hostess hosting hotness houdini 
    hounding housing howells howling hulking industrial industrious instance insurances issuance leaching leading leaking 
    leaning leanings leaping learning lease leasing leaved leavers leaves leavin leavitt lending lessing letting licked 
    liked lined lineker linkedin linker loading loaning mahoney maloney manage managed manages manatee manger manners 
    monet moneys monkey monkeys monty mooney morey parentage percent percentages percentile pervert police policed 
    polices policing polishes politics polity precept prefect preheat premier premise premiums present presents pretend 
    pretext prevalent prevented prevents prudent quid quiet quilt quilting quin quint quip quite quito quits quiz quot 
    quoting races rafters rages rakes rapes rate rated rats rattles raves reardon reasoned rebates rebound rebounded 
    rebounding rebounds rebuked reckons recluse recreated recuse reduced reduces reducing refined refining refueling 
    refuge refugee refuges refuses refute refuted refutes refuting regions reimbursed reimbursements rejected related 
    relates released relegated relented remanded reminded reminding reminds repealed repeatedly repeater repeaters 
    repeats repelled repented replaced replayed reported reposted repulse repulsed reputed resented resounding respected 
    restated resumed resuming retailer retails retain retains retrain retreated retrial reuse reused reusing revealed 
    reverted revised revising rites rotates rounded rounding rousing ryerson scare shade shae shake shale shame shane 
    shape shar shard shared shares shari shark sharkey sharp sharpe sharpen sharper sharpie shave sheared shearer shire 
    shore sketching snare snatching snitch sorcery spare stare stitch stitching superior superiors supervise supervised 
    supervises supervision supervisory surry swatch switched switcher switches telecoms telekom tend tends theater 
    theaters thoreau thread threaded threads throat throated throats thrusts transform transformed transforms transverse 
    tread treads treat treated treats trended trendy trent wagging wailing waitin waiving walking walling wanking wanting 
    warming warning warping warring washing wasting wetting whining whiting wich writhing writing writings
""".split())
_VOCAB_SET = frozenset(SPELL_VOCAB)
_VOCAB_BY_FIRST: dict[str, tuple] = {}
for _w in SPELL_VOCAB:
    _VOCAB_BY_FIRST[_w[0]] = _VOCAB_BY_FIRST.get(_w[0], ()) + (_w,)


def osa_distance(a: str, b: str, cap: int = 3) -> int:
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev2, prev = None, list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = a[i - 1] != b[j - 1]
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if prev2 is not None and i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        if min(cur) > cap:
            return cap + 1
        prev2, prev = prev, cur
    return prev[-1]


def correct_spelling(text: str, corpus_vocab: dict | None = None) -> tuple[str, list]:
    fixes = []
    known = corpus_vocab or {}

    def fix(m: re.Match) -> str:
        w = m.group(0)
        if len(w) < 4 or w in _VOCAB_SET or w in SPELL_KEEP or known.get(w, 0) >= 3:
            return w
        lim = 1 if len(w) <= 6 else 2
        cands = []
        for v in _VOCAB_BY_FIRST.get(w[0], ()):
            if abs(len(v) - len(w)) > lim:
                continue
            d = osa_distance(w, v, lim)
            if d <= lim:
                cands.append((d, -known.get(v, 0), v))
        if not cands:
            return w
        best = min(cands)[2]
        fixes.append((w, best))
        return best

    return re.sub(r"[a-z]+", fix, text), fixes


SLANG = [
    (r"\b(?:the|a|your|their|his|her|my|our) (?:big )?(?:boss|bosses|head honcho|higher[- ]ups?)\b", "a supervisor"),
    (r"\b(?:someone|somebody|the person|the people|whoever(?: is|'s)?) in charge\b", "a supervisor"),
    (r"\b(?:go|goes|going|went|gone) over (?:your|the agent'?s?|their|his|her|my|our) heads?\b", "escalate"),
    (r"\b(?:up|higher up) the (?:chain|ladder)\b", "to a supervisor"),
    (r"\b(?:take|takes|taking|took) (?:it|this|that|the (?:call|issue|matter|complaint)) (?:higher|further|upstairs|up a level)\b",
     "escalate"),
    (r"\b(?:tier|level) (?:2|two)(?: support)?\b|\bsecond[- ]level support\b", "a supervisor"),
    (r"\b(?:blow|blows|blowing|blown|blew) up\b|\b(?:lose|loses|losing|lost) (?:it|their temper|their cool|their patience|"
     r"patience|the plot)\b|\b(?:flip|flips|flipped|flipping|freak|freaks|freaked|freaking) out\b|\b(?:go|goes|going|went) "
     r"(?:ballistic|nuts|off)\b|\b(?:get|gets|getting|got) (?:heated|mad|worked up|pissed)\b|\birate\b|\bfuming\b|"
     r"\bpissed(?: off)?\b|\bticked off\b|\bfed up\b|\bmeltdowns?\b|\brant(?:s|ed|ing)?\b", "get frustrated"),
    (r"\b(?:walk|walks|walked|walking) away\b|\bjump(?:s|ed|ing)? ship\b|\b(?:take|takes|taking|took) (?:their|my|his|her|our) "
     r"business (?:elsewhere|somewhere else)\b|\b(?:go|goes|going|went) (?:elsewhere|somewhere else|to a rival|to a "
     r"competitor)\b|\bditch(?:es|ed|ing)? (?:us|the company|the brand)\b|\b(?:drop|drops|dropped|dropping) us\b",
     "threaten to leave the company"),
    (r"\b(?:their|my|his|her) (?:cash|dough) back\b|\bcash back\b|\b(?:get|gets|getting|got) (?:paid|reimbursed) back\b|"
     r"\bpay(?:s|ing)? (?:them|me|us|him|her) back\b|\b(?:there|thier)\s+(?:money|mony|munny)\s+(?:back|bak|bck|bac)\b|"
     r"\b(?:their|my|our|his|her|the)\s+(?:mony|munny)\s+(?:back|bak|bck|bac)\b|\b(?:their|my|our|his|her|the)\s+money\s+"
     r"(?:bak|bck|bac)\b", "money back"),
]
SLANG_RES = [(re.compile(p), r) for p, r in SLANG]


def apply_slang(text: str) -> tuple[str, list]:
    found = []
    for rx, rep in SLANG_RES:
        for m in rx.finditer(text):
            found.append((m.group(0), rep))
        text = rx.sub(rep, text)
    return text, found


SPANISH = [
    (r"[¿¡]", " "),
    (r"\bcon qu[eé] frecuencia\b", "how often"),
    (r"\bqu[eé] (?:causa|provoca|genera|impulsa)n?\b", "what causes"),
    (r"\bpor qu[eé]\b|\bporqu[eé]\b", "why"),
    (r"\bc[oó]mo (?:podemos|se puede|puedo)\b", "how can we"),
    (r"\bc[oó]mo\b", "how"),
    (r"\bcu[aá]nt[oa]s\b", "how many"),
    (r"\bcu[aá]l(?:es)?\b", "which"),
    (r"\bqu[eé]\b", "what"),
    (r"\bmu[eé]str(?:a|ame|enme|eme)\b", "show me"),
    (r"\bejemplos?\b", "examples"),
    (r"\bcompar(?:a|ar|e|en)\b", "compare"),
    (r"\b(?:los |las |l[oa]s? )?clientes\b", "customers"),
    (r"\b(?:el |la )?cliente\b", "customer"),
    (r"\b(?:los )?agentes\b", "agents"),
    (r"\b(?:las )?llamadas\b", "calls"),
    (r"\b(?:piden|solicitan|exigen|quieren|reclaman)\b", "ask for"),
    (r"\b(?:un |el )?reembolsos?\b|\b(?:la )?devoluci[oó]n (?:del|de su|de) dinero\b", "a refund"),
    (r"\b(?:escalan|escalar|escala)\b", "escalate"),
    (r"\b(?:las )?escalaci(?:o|ó)n(?:es)?\b|\b(?:los )?escalamientos?\b", "escalations"),
    (r"\b(?:un |el |al )?supervisor\b", "a supervisor"),
    (r"\b(?:un |el |al )?gerente\b", "a manager"),
    (r"\bamenazan con\b", "threaten to"),
    (r"\b(?:cancelan|cancelar|cancela)\b", "cancel"),
    (r"\b(?:dar(?:se|nos|me)? de baja|darse de baja|se dan de baja)\b", "cancel"),
    (r"\b(?:se van|irse|marcharse|abandonan|abandonar|dejan la empresa|dejar la empresa|se marchan|irse a la competencia)\b", "leave the company"),
    (r"\bcambiar(?:se)? de (?:proveedor|compa(?:ñ|n)[ií]a|empresa|banco|operador|aseguradora)\b", "switch provider"),
    (r"\b(?:los )?hoteles\b|\b(?:el )?hotel\b", "hotel"),
    (r"\b(?:las )?aerol[ií]neas?\b", "airline"),
    (r"\b(?:los )?seguros?\b", "insurance"),
    (r"\b(?:los )?bancos?\b", "bank"),
    (r"\b(?:est[aá]n? |son )?(?:relacionad|vinculad)[oa]s? (?:con|a)\b", "linked to"),
    (r"\bfrustraci[oó]n\b|\benojo\b|\benfado\b", "frustration"),
    (r"\bdisculpas?\b", "apologies"),
    (r"\bempat[ií]a\b", "empathy"),
    (r"\brechazos?\b|\bnegativas?\b", "refusals"),
    (r"\ben espera\b", "on hold"),
    (r"\b(?:reducir|disminuir|bajar)\b", "reduce"),
    (r"\b(?:podemos)\b", "can we"),
    (r"\bfrecuentes?\b|\bfrecuencia\b", "often"),
    (r"\bm[aá]s\b", "more"),
    (r"\by\b", "and"),
    (r"\b(?:de|del|la|el|los|las|un|una|en|se|lo|a|al|que|su|sus|por|para|con)\b", " "),
]
HINGLISH = [
    (r"\bkitni baar\b|\bkitni bar\b", "how often"),
    (r"\bkaise\b(?:\s+\w+){0,2}?\s+kam\b", "how to reduce"),
    (r"\bdhamki\b", "threaten to"),
    (r"\bjud(?:a|e|i)\b", "linked to"),
    (r"\bky(?:u|o|oo)n?\b", "why"),
    (r"\bkaise\b|\bkese\b", "how"),
    (r"\bkit(?:ne|ni|na)\b", "how many"),
    (r"\bgrahak\b", "customers"),
    (r"\b(?:maangte|mangte|maangti|mangti|maang|mang)\b", "ask for"),
    (r"\b(?:chhod|chod)(?:te|ti|na|ne|ni|ke|kar|enge|oge|denge|dena)?\b", "leave the company"),
    (r"\b(?:gussa|naraz|naaraz)\b", "frustrated"),
    (r"\bkam\b", "reduce"),
    (r"\b(?:kya|hai|hain|hota|hoti|hote|ho|karte|karti|karta|karo|kare|ke|ki|ka|mein|me|se|ko|ne|wale|wali|par|pe)\b", " "),
]
SPANISH_RES = [(re.compile(p), r) for p, r in SPANISH]
HINGLISH_RES = [(re.compile(p), r) for p, r in HINGLISH]
SPANISH_HINT_RE = re.compile(r"[¿¡ñáéíóú]|\b(?:por qu[eé]|clientes|llamadas|reembolsos?|piden|escalan|cu[aá]nt[oa]s|c[oó]mo|"
                             r"hoteles|aerol[ií]neas?|qu[eé])\b")
HINGLISH_STRONG_RE = re.compile(r"\b(?:kyun|kyon|kyu|kyoon|kaise|kese|kitne|kitni|kitna|grahak|maangte|mangte|maangti|"
                                r"mangti)\b")
HINGLISH_WEAK_RE = re.compile(r"\b(?:kya|hai|hain|hota|hoti|hote|karte|karti|karta|wale|wali|mein)\b")


FRENCH = [
    (r"\b[ldjnmst]'", " "),
    (r"\bcombien de fois\b|\b(?:à|a|avec) quelle fréquence\b", "how often"),
    (r"\bqu'?est-ce qui (?:cause|provoque|entraîne|pousse)\b|\bqu'?est-ce qui\b", "what causes"),
    (r"\bpourquoi\b", "why"),
    (r"\bcomment (?:pouvons-nous|peut-on|pourrait-on)\b", "how can we"),
    (r"\bcomment\b", "how"),
    (r"\bcombien\b", "how many"),
    (r"\bquel(?:le)?s?\b", "which"),
    (r"\bmontre(?:z)?(?:-moi)?\b", "show me"),
    (r"\bexemples?\b", "examples"),
    (r"\bcompar(?:e|er|ez)\b", "compare"),
    (r"\bclient(?:e)?s?\b", "customers"),
    (r"\bagents?\b|\bconseillers?\b", "agents"),
    (r"\bappels?\b", "calls"),
    (r"\b(?:demandent|réclament|veulent|exigent)\b", "ask for"),
    (r"\b(?:un |le |les |des )?remboursements?\b|\bse faire rembourser\b", "a refund"),
    (r"\bescalad(?:e|es|ent|er)\b|\bescalations?\b", "escalate"),
    (r"\b(?:un |le )?(?:superviseur|responsable|manager)\b", "a supervisor"),
    (r"\bmenacent(?:-ils|-elles)? de\b", "threaten to"),
    (r"\b(?:est-elle |est-il |sont-elles |sont-ils )?li[ée]e?s? (?:à|aux|au|avec)\b", "linked to"),
    (r"\b(?:résilient|résilier|annulent|annuler|résiliation)\b", "cancel"),
    (r"\b(?:partent|partir|quittent|quitter|s'en aller|aller ailleurs|vont ailleurs)(?!(?:-ils|-elles)? (?:en|au|à|a|pour) (?:vacances|voyage|week-end|weekend|séjour|hôtel|hotel|aéroport|vol))(?: l'?entreprise)?\b", "leave the company"),
    (r"\bchanger de (?:fournisseur|prestataire|compagnie|banque|opérateur)\b", "switch provider"),
    (r"\bhôtels?\b|\bhotels?\b", "hotel"),
    (r"\bcompagnies? aériennes?\b|\bvols?\b", "airline"),
    (r"\bassurances?\b|\bassureurs?\b", "insurance"),
    (r"\bbanques?\b", "bank"),
    (r"\bfrustration\b|\bcolère\b|\bénervés?\b", "frustration"),
    (r"\bexcuses\b", "apologies"),
    (r"\bempathie\b", "empathy"),
    (r"\brefus\b", "refusals"),
    (r"\ben attente\b", "on hold"),
    (r"\bréduire\b|\bdiminuer\b", "reduce"),
    (r"\bplus\b", "more"),
    (r"\bet\b", "and"),
    (r"\bou\b", "or"),
    (r"\b(?:de|du|des|la|le|les|un|une|en|que|qui|est|sont|ce|cette|pour|avec|dans|au|aux|se|ils|elles|on|il|y)\b", " "),
]
GERMAN = [
    (r"\bwie oft\b|\bwie häufig\b", "how often"),
    (r"\bwas (?:verursacht|führt zu|treibt|löst)\b", "what causes"),
    (r"\bwarum\b|\bwieso\b|\bweshalb\b", "why"),
    (r"\bwie können wir\b|\bwie kann man\b", "how can we"),
    (r"\bwie viele\b|\bwieviele\b", "how many"),
    (r"\bwie\b", "how"),
    (r"\bwelche[rsnm]?\b", "which"),
    (r"\bzeig(?:e|en sie)? mir\b|\bzeige\b", "show me"),
    (r"\bbeispiele?\b", "examples"),
    (r"\bvergleich(?:e|en)?\b", "compare"),
    (r"\bkund(?:en|innen)\b", "customers"),
    (r"\bmitarbeiter(?:innen)?\b|\bagenten\b", "agents"),
    (r"\banrufe?n?\b|\bgespräche?n?\b", "calls"),
    (r"\b(?:verlangen|fordern|wollen|möchten|bitten um)\b", "ask for"),
    (r"\b(?:eine |die )?(?:rückerstattung(?:en)?|erstattung(?:en)?|geld zurück)\b", "a refund"),
    (r"\beskalier(?:en|t)\b", "escalate"),
    (r"\beskalation(?:en)?\b", "escalations"),
    (r"\b(?:einen |den |ein )?(?:vorgesetzten|vorgesetzte[rn]?|supervisor|manager|teamleiter)\b", "a supervisor"),
    (r"\bdrohen mit\b|\bdrohen(?: damit)?(?:,)?(?: zu)?\b", "threaten to"),
    (r"\b(?:verbunden|verknüpft|zusammenhängend|zusammen)\b", "linked to"),
    (r"\bhotel\w+", "hotel"),
    (r"\bversicherungs\w+", "insurance"),
    (r"\b(?:kündigen|kündigung|stornieren|zu kündigen)\b", "cancel"),
    (r"\b(?:zu gehen|abzuwandern|abwandern|zur konkurrenz zu gehen|zur konkurrenz)\b", "leave the company"),
    (r"\b(?:den )?anbieter wechseln\b|\bwechseln\b", "switch provider"),
    (r"\bhotels?\b", "hotel"),
    (r"\bfluggesellschaften?\b|\bflüge?n?\b|\bairlines?\b", "airline"),
    (r"\bversicherung(?:en)?\b", "insurance"),
    (r"\bbanken?\b", "bank"),
    (r"\bfrust(?:ration)?\b|\bärger\b|\bwut\b", "frustration"),
    (r"\bentschuldigung(?:en)?\b", "apologies"),
    (r"\bempathie\b", "empathy"),
    (r"\bablehnung(?:en)?\b", "refusals"),
    (r"\bwarteschleife\b", "on hold"),
    (r"\breduzieren\b|\bverringern\b|\bsenken\b", "reduce"),
    (r"\bmehr\b", "more"),
    (r"\bund\b", "and"),
    (r"\boder\b", "or"),
    (r"\b(?:der|die|das|den|dem|des|ein|eine|einen|einem|einer|in|im|bei|von|zu|zur|zum|mit|für|ist|sind|es|sie|wir|man|um|auf|an)\b", " "),
]
PORTUGUESE = [
    (r"\bcom (?:que|qual) frequência\b", "how often"),
    (r"\bo que (?:causa|provoca|leva a)\b", "what causes"),
    (r"\bpor ?qu[eê]\b", "why"),
    (r"\bcomo (?:podemos|reduzir)\b", "how can we"),
    (r"\bcomo\b", "how"),
    (r"\bquant[oa]s\b", "how many"),
    (r"\bqua(?:l|is)\b", "which"),
    (r"\bmostr(?:e|a)(?:-me)?\b|\bme mostre\b", "show me"),
    (r"\bexemplos?\b", "examples"),
    (r"\bcompar(?:e|ar|a)\b", "compare"),
    (r"\bclientes\b", "customers"),
    (r"\batendentes\b|\bagentes\b", "agents"),
    (r"\bchamadas\b|\bligações\b", "calls"),
    (r"\b(?:pedem|solicitam|exigem|querem)\b", "ask for"),
    (r"\b(?:um |o )?reembolsos?\b|\bdinheiro de volta\b|\bestorno\b", "a refund"),
    (r"\b(?:escalam|escalar|escalonam|escalonar)\b", "escalate"),
    (r"\bescalaç(?:ão|ões)\b|\bescalonamentos?\b", "escalations"),
    (r"\b(?:um |o )?(?:supervisor|gerente)\b", "a supervisor"),
    (r"\bameaçam(?: de)?\b", "threaten to"),
    (r"\b(?:está |estão )?ligad[oa]s? (?:a|à|às|ao|aos|com)\b", "linked to"),
    (r"\b(?:cancelam|cancelar)\b", "cancel"),
    (r"\b(?:saem|sair|ir embora|deixam a empresa|deixar a empresa|abandonam|abandonar)\b", "leave the company"),
    (r"\btrocar de (?:operadora|fornecedor|empresa|banco)\b", "switch provider"),
    (r"\bhot[eé]is\b|\bhotel\b", "hotel"),
    (r"\bcompanhias? aéreas?\b|\bvoos?\b", "airline"),
    (r"\bseguros?\b|\bseguradoras?\b", "insurance"),
    (r"\bbancos?\b", "bank"),
    (r"\bfrustraç(?:ão|ões)\b|\braiva\b", "frustration"),
    (r"\bdesculpas?\b", "apologies"),
    (r"\bempatia\b", "empathy"),
    (r"\brecusas?\b", "refusals"),
    (r"\bem espera\b", "on hold"),
    (r"\breduzir\b|\bdiminuir\b", "reduce"),
    (r"\bmais\b", "more"),
    (r"\be\b", "and"),
    (r"\bou\b", "or"),
    (r"\b(?:o|a|os|as|de|do|da|dos|das|um|uma|em|no|na|nos|nas|com|para|por|que|se|é|são)\b", " "),
]
ITALIAN = [
    (r"\b[l]'", " "),
    (r"\bcon quale frequenza\b|\bquanto spesso\b|\bogni quanto\b", "how often"),
    (r"\bcosa (?:causa|provoca|porta a)\b", "what causes"),
    (r"\bperch[eé]\b", "why"),
    (r"\bcome possiamo\b", "how can we"),
    (r"\bcome\b", "how"),
    (r"\bquant[ie]\b", "how many"),
    (r"\bqual[ie]?\b", "which"),
    (r"\bmostra(?:mi)?\b", "show me"),
    (r"\besempi\b", "examples"),
    (r"\bconfront(?:a|are)\b", "compare"),
    (r"\bclienti\b", "customers"),
    (r"\boperatori\b|\bagenti\b", "agents"),
    (r"\bchiamate\b|\btelefonate\b", "calls"),
    (r"\b(?:chiedono|vogliono|pretendono)\b", "ask for"),
    (r"\b(?:un |il )?rimbors[oi]\b", "a refund"),
    (r"\b(?:escalano|escalare)\b", "escalate"),
    (r"\b(?:un |il )?(?:supervisore|responsabile)\b", "a supervisor"),
    (r"\bminacciano di\b", "threaten to"),
    (r"\b(?:è |sono )?collegat[oaie] (?:a|al|alla|alle|ai|agli|con)\b", "linked to"),
    (r"\b(?:disdicono|disdire|annullano|annullare|cancellano)\b", "cancel"),
    (r"\b(?:lasciano|lasciare|abbandonano|abbandonare|andarsene|andare via|se ne vanno)(?: l'?azienda| azienda)?\b", "leave the company"),
    (r"\bcambiare (?:fornitore|operatore|compagnia|banca)\b", "switch provider"),
    (r"\balberghi\b|\balbergo\b", "hotel"),
    (r"\bcompagnie aeree\b|\bvoli\b", "airline"),
    (r"\bassicurazion[ei]\b|\bassicurativ[eoia]\b", "insurance"),
    (r"\bbanche\b|\bbanca\b", "bank"),
    (r"\bfrustrazione\b|\brabbia\b", "frustration"),
    (r"\bscuse\b", "apologies"),
    (r"\bempatia\b", "empathy"),
    (r"\brifiuti\b", "refusals"),
    (r"\bin attesa\b", "on hold"),
    (r"\bridurre\b", "reduce"),
    (r"\bpiù\b", "more"),
    (r"\be\b", "and"),
    (r"\bo\b", "or"),
    (r"\b(?:il|lo|la|i|gli|le|di|del|della|dei|delle|un|una|in|nel|nella|con|per|che|si|è|sono|da)\b", " "),
]
DEVANAGARI = [
    (r"कितनी बार", "how often"),
    (r"कैसे कम", "how to reduce"),
    (r"धमकी", "threaten to"),
    (r"जुड़(?:ा|ी|े)", "linked to"),
    (r"नाराज़गी|नाराजगी", "frustration"),
    (r"क्यों|क्यूँ", "why"),
    (r"कैसे", "how"),
    (r"कितने|कितनी|कितना", "how many"),
    (r"ग्राहक(?:ों)?", "customers"),
    (r"रिफंड|धनवापसी|पैसे वापस", "a refund"),
    (r"एस्केलेशन|एस्केलेट", "escalation"),
    (r"सुपरवाइज़र|सुपरवाइजर|मैनेजर|प्रबंधक", "a supervisor"),
    (r"रद्द|कैंसिल", "cancel"),
    (r"छोड़(?:ते|ना|कर)?", "leave the company"),
    (r"मांगते|माँगते|मांगना", "ask for"),
    (r"होटल", "hotel"),
    (r"एयरलाइन|उड़ान", "airline"),
    (r"बैंक", "bank"),
    (r"बीमा", "insurance"),
    (r"कॉल", "calls"),
    (r"नाराज़|नाराज|गुस्सा", "frustrated"),
    (r"कम", "reduce"),
    (r"[ऀ-ॿ]+", " "),
]
LANG_TABLES = {"Spanish": SPANISH, "French": FRENCH, "German": GERMAN, "Portuguese": PORTUGUESE, "Italian": ITALIAN,
               "Hindi (romanised)": HINGLISH, "Hindi": DEVANAGARI}
LANG_RES = {k: [(re.compile(p), r) for p, r in v] for k, v in LANG_TABLES.items()}
LANG_MARKERS = {
    "Spanish": ("por qué porqué qué cómo cuántos cuántas cuál cuáles los las del para clientes llamadas piden reembolso "
                "reembolsos escalan quieren muéstrame hoteles aerolíneas también podemos reducir amenazan"),
    "French": ("pourquoi comment combien quels quelles quel quelle les des du est sont clients appels remboursement "
               "demandent annulent avec dans aussi pouvons réduire menacent"),
    "German": ("warum wieso weshalb wie oft welche welcher der die das den dem und ist sind kunden anrufe "
               "rückerstattung erstattung verlangen kündigen mit für auch können wir reduzieren drohen"),
    "Portuguese": ("porque por quê como quantos quantas quais os as dos das com para clientes chamadas ligações "
                   "reembolso pedem cancelam também não podemos reduzir ameaçam"),
    "Italian": ("perché come quanti quante quali il gli dei delle con per clienti chiamate rimborso chiedono annullano "
                "anche non possiamo ridurre le della minacciano"),
    "Hindi (romanised)": "kyun kyon kyu kyoon kaise kese kitne kitni kitna kya hai hain hota hote karte grahak maangte mangte",
    "English": ("why how what which who when where the a an of in on to for with do does did is are was were customers "
                "calls agents refund refunds escalate escalations churn often many show compare and or"),
}
_MARKER_SETS = {k: set(v.split()) for k, v in LANG_MARKERS.items()}
_ACCENT_HINTS = {"Spanish": "ñ¿¡", "Portuguese": "ãõ", "German": "äöüß", "French": "àâçèêëîïôûœ", "Italian": "ìò"}


def detect_language(text: str) -> tuple[str, float]:
    if re.search(r"[ऀ-ॿ]", text):
        return "Hindi", 1.0
    toks = re.findall(r"[^\W\d_]+", text.lower())
    if not toks:
        return "English", 0.0
    scores = {}
    for lang, words in _MARKER_SETS.items():
        hits = sum(t in words for t in toks)
        bonus = sum(ch in _ACCENT_HINTS.get(lang, "") for ch in text) * 0.5
        scores[lang] = (hits + bonus) / len(toks)
    if HINGLISH_STRONG_RE.search(text.lower()):
        return "Hindi (romanised)", scores["Hindi (romanised)"]
    best = max(scores, key=scores.get)
    if best != "English" and scores[best] > scores["English"] and scores[best] * len(toks) >= 1.5:
        return best, scores[best]
    return "English", scores["English"]


def translate(text: str) -> tuple[str, str]:
    lang, _ = detect_language(text)
    if lang == "English":
        return text, ""
    for rx, rep in LANG_RES[lang]:
        text = rx.sub(rep, text)
    text = re.sub(r"(?<=\w)-(?=\s|$)|(?<=\s)-(?=\w)", " ", text)
    return re.sub(r"\s+", " ", text).strip(" ?!.,-"), lang


def vocabulary(texts) -> dict:
    import pandas as pd
    s = pd.Series(list(texts), dtype=object).astype(str).str.lower().str.findall(r"[a-z]+")
    vc = s.explode().value_counts()
    return {str(k): int(v) for k, v in vc[vc >= 3].items()}
