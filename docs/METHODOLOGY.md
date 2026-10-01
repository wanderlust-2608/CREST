# Methodology, Results and Discussion
**Abstract.** Customer-service calls record escalations, refund requests and churn threats, but not *why* they happen.
CREST turns about 19,600 calls into evidence-based causal explanations that cite the responsible dialogue turns (Task 1)
and keeps the analytical context across follow-up questions (Task 2). Offline, every call is cut into decision moments
described only by what was said before them, behaviours are measured at those moments, and their effect on a later
event is estimated with a cross-fitted doubly robust estimator inside a pre-registered, label-error-corrected design;
code assigns every factor a claim level. Online, questions are read robustly (misspellings, six languages), answered
from the resulting Factor Library and a hybrid search index, written from placeholders, and checked by three gates, while
follow-ups are validated changes to an explicit state. On a synthetic call centre with known causes, the 95% intervals
covered all 12 true effects, the error of an unadjusted comparison was cut by about 72%, every confirmed claim had the
right sign, 81 of 81 scored questions were answered as expected and 40 of 40 follow-up turns kept their context. On
the real corpus, a blind sample showed that the event labeller's recall is still modest (escalation 0.77, churn 0.56),
which the label-error correction absorbs. The main limits are observational identification, validation on synthetic data,
and the absence of human and model judges so far.

**Contents.** 1 Problem · 2 Objectives · 3 Approach · 4 Task 1 methodology · 5 Task 2 methodology · 6 Evaluation design ·
7 Quantitative results · 8 Qualitative results · 9 Analysis · 10 Limitations · 11 Improvements · 12 Conclusion ·
Appendix A (which paper is used where).

---

## 1. Problem definition and motivation

### 1.1 The problem

The project addresses **causal rationale extraction and synthesis from conversational data on business events**. The
corpus holds about **19,600 customer-service conversations** between customers, agents and, in some calls,
supervisors or specialists. Many of them end in one of three business events:

* an **escalation** to a supervisor;
* a **refund or compensation** request;
* a **churn threat** (cancel, switch, not renew).

The question is not *"what was said in calls where an escalation occurred?"*. That is a retrieval question. The
question is:

> **Which conversational behaviours plausibly contribute to a later business event, what evidence in the dialogue
> supports that, and how can the result be communicated without overstating causality?**

The brief asks for two capabilities:

* **Task 1:** a question about an event returns an *evidence-based causal explanation* that cites the dialogue turns
  responsible.
* **Task 2:** *follow-up questions* that depend on the earlier analysis ("what about refunds?", "only airline
  calls", "explain the second factor") are answered in context.

### 1.2 Why the problem arises

**The business reason.** Escalations, refunds and churn threats are the visible symptoms of failed interactions, and
each costs money. Contact-centre research has shown that these outcomes can be *predicted* from transcripts (Mishne et
al., 2005; Park & Gates, 2009; Coussement & Van den Poel, 2008, 2009; Montgomery & Damian, 2017) and that conversations
carry early warning signs before they derail (Zhang et al., 2018; Chang & Danescu-Niculescu-Mizil, 2019). Prediction,
however, does not tell a manager *what to change*. An agent behaviour is a lever only if changing it would change the
outcome. That is a causal question.

**Four obstacles make it hard in this data.**

1. **The data contain outcomes but no rationales.** Nothing in the corpus says which turn caused or contributed to an
   event. Annotated cause spans exist for emotions in dialogue (Poria et al., 2021) but not for business events, so the
   system has to reconstruct both the *event trajectory* and the *candidate mechanisms*.
2. **Correlation is not causation.** A refusal, an apology, a hold or an expression of frustration may be frequent
   before an escalation without causing it: it may merely reflect how severe the issue is or how the customer already
   feels. Text-based causal inference needs explicit adjustment for such confounders (Feder et al., 2022; Keith et al.,
   2020), and language models asked directly perform close to chance on causal inference (Jin et al., 2024).
3. **Questions are contextual.** Business users ask "why do escalations happen in telecom calls?", then "what about
   refunds?", then "only for airlines". Systems that treat every turn alone, or rewrite the whole question, silently lose
   the event or the filter, and conversational systems fail most on later turns (Katsis et al., 2025).
4. **The raw data are messy and constrained.** Speaker labels are sometimes names; analyst notes are typed into the
   dialogue; the same call is reused with only the numbers changed; call-level fields written after the call leak the
   outcome (Kaufman et al., 2012); there are no timestamps inside calls; user questions are misspelled, use slang or are
   not in English; and the dataset is copyrighted, so everything must run locally.

| Challenge | What the system has to do | Where |
|---|---|---|
| No cause labels | reconstruct events and their onset turn; define measurable behaviours | §4.1, §4.3 |
| Confounded correlations | estimate effects while adjusting for the conversation so far, and say how strong a hidden confounder would have to be | §4.2, §4.4 |
| Overstated claims | make the wording depend on the strength of the evidence | §4.4 (claim ladder), §4.9 (gates) |
| No provenance | cite exact turns, never paraphrased ones | §4.5, §4.6, §4.8 |
| Contextual follow-ups | keep an explicit state and change only what the user changed | §5 |
| Messy or unsupported questions | read noisy and multilingual questions; name the parts that cannot be answered | §4.7 |
| Data defects and leakage | clean, audit, and split the data before any analysis | §3.4 |

### 1.3 How the problem was solved, in one paragraph

CREST (Causal Rationale Extraction and Synthesis Toolkit) splits the work into an **offline analytical layer** and an
**online reasoning layer**. Offline, each call is turned into a sequence of decision moments ("landmarks") described
only by what was said *before* them; behaviours of agents and customers are measured at those moments; the effect of
each behaviour on a later event is estimated with a cross-fitted doubly robust estimator (Chernozhukov et al., 2018)
inside a pre-registered, label-error-corrected design (Egami et al., 2022, 2023), then stress-tested with negative
controls, sensitivity analyses and a self-test of the estimator. The output is a **Factor Library**: each factor has an
effect, an interval and a **claim level** computed by code. Online, a question is parsed into a small validated form,
answered from the Factor Library and a hybrid search index, written from placeholders so that numbers and claim
strength cannot drift, and checked by three gates (numbers, causal wording, quotes). Follow-ups change an explicit
state through validated deltas. Everything runs offline; an LLM is optional and never decides a number or a cause.

---

## 2. Objectives

**Objective 1: identify business events and their onset.** For every call, decide whether each event occurred and find
the first turn at which it became explicit.

**Objective 2: estimate behavioural effects rather than retrieve correlations.** For a measurable behaviour, estimate
whether its occurrence at a particular moment changes the later probability of the event, given the history before that
moment.

**Objective 3: ground every explanation in the dialogue.** For each reported factor, show the actual turns where the
behaviour occurs, with exact provenance (`transcript_id:turn`).

**Objective 4: support contextual follow-ups.** Keep an analytical state so that a follow-up changes only the
dimensions the user named.

**Cross-cutting requirements** (they shape every design choice below):

* **R1. Never claim more than the evidence allows**, and say what cannot be answered.
* **R2. Provenance for every statement:** numbers from a record, quotes from a turn.
* **R3. Reproducibility:** a frozen, hashed analysis plan; a locked test set; deterministic outputs.
* **R4. Works offline.** Optional LLM components must have a deterministic fallback.
* **R5. Robust to real questions:** misspellings, slang, other languages, unsupported filters, false premises.

The system should therefore answer not only *what happened?* but also *what preceded it, what is statistically
supported as a potential driver, what evidence illustrates it, and how does the conclusion change under a follow-up?*

---

## 3. Overall approach

### 3.1 Two layers

```text
OFFLINE (once per corpus)
  raw calls ─► cleaning, leakage audit, split by template group          (Step 0)
            ─► event labels + onset turns (+ blind gold sample)         (Step 1)
            ─► landmark risk sets: moments described by the past only   (Step 2)
            ─► behaviour measurement (+ negative controls)              (Step 3)
            ─► effect estimation: pilot → pre-register → confirm once   (Step 4)
            ─► Factor Library (effect, interval, claim level L0–L3)
            ─► evidence spans + faithfulness; hybrid search index       (Steps 5–6)

ONLINE (per question)
  question ─► reading: language, spelling, slots, premises, unsupported   (Step 7)
           ─► [Task 2: state + delta, routing]                            (Step 10–12)
           ─► evidence pack (numbers, factors, quotes, caveats)           (Step 8)
           ─► answer from placeholders ─► gates: numbers · wording · quotes  (Step 9)
```

### 3.2 The design principle

> **The AI proposes and synthesises; statistical identification and predefined validation tests constrain what can be
> claimed.**

This follows two findings. Language models are close to random at inferring causation from correlational statements
(Jin et al., 2024), but strong at knowledge-based causal tasks such as proposing candidate causes and confounders
(Kıcıman et al., 2024). So hypotheses may come from a model or a lexicon, while estimation, claim levels and number
formatting are done by code. The separation is literal:

```text
statistics → code        evidence → retrieval        language → templates (or an LLM bound to placeholders)
```

### 3.3 With or without an LLM

| Component | Default: offline and deterministic | Optional: with an LLM | What never moves into the LLM |
|---|---|---|---|
| Event labels | lexicon rules, a hybrid churn layer, retention risk | an LLM labels a development sample, each onset quote is checked against the turn, a light classifier is trained (TnT-LLM; Wan et al., 2024) | accuracy, measured on the human gold sample |
| Behaviours | fixed registry of 14 behaviours and 2 negative controls | an LLM proposes candidate behaviours from event-versus-control windows (D5; Zhong et al., 2023) | filters, precision check, estimation |
| Reading a question | rules, phrase tables, spelling correction | an LLM translates or normalises when the rules find no event; proposes follow-up deltas (IC-DST style; Hu et al., 2022) | slot validation, allowed vocabulary |
| Writing | templates filled with placeholders | an LLM writes sentences bound to the same placeholders (ALCE-style citations; Gao et al., 2023) | numbers, claim levels, the gates |
| Judging the query set | deterministic expectations per query | an LLM judge of realism, brands masked (Zheng et al., 2023) | the human audit |

The optional paths are implemented and unit-tested with a stub client. **No result in this document uses them**:
sending transcripts to an external service is allowed only if the hackathon's data rules permit it.

### 3.4 Step 0: data preparation

A cleaning notebook turns the raw file (19,621 records) into analysis tables **without changing the raw data**:

* speaker roles resolved for calls whose speakers are names, validated by hiding the labels on held-out calls
  (role-recognition idea: Salamin & Vinciarelli, 2012; Flemotomos et al., 2020);
* analyst notes typed into the dialogue are **quarantined** and never used as evidence (leakage; Kaufman et al., 2012);
* stage directions, fillers and repetitions normalised, with hesitation signals counted before fillers are removed
  (Clark & Fox Tree, 2002);
* exact duplicates dropped; near-duplicates (MinHash with exact verification; Lee et al., 2022) grouped into **template
  groups**;
* a **locked 80/10/10 train/dev/test split by template group**, so templated calls never straddle splits (Elangovan et
  al., 2021), which also implements the split-sample workflow of Egami et al. (2022): discover on train, confirm on
  held-out;
* a **leakage audit** of every metadata field; fields that may describe the outcome (such as a free-text reason for
  call) are never used as filters or covariates;
* a data card (Gebru et al., 2021).

Turns stay atomic and citeable (Sacks et al., 1974). The corpus has no timestamps inside calls, so silences are only
approximated by hold phrases and pause markers (Heldner & Edlund, 2010).

### 3.5 Algorithm choices at a glance

| Decision | Chosen | Alternatives not chosen | Why |
|---|---|---|---|
| Event labels | lexicon rules with explicit exclusions, a weakly supervised churn layer, a gold sample to measure and correct | an LLM labelling every call; keywords alone | transparent, free to run, nothing leaves the machine; errors are measured and corrected rather than hidden (§4.1) |
| Comparison design | landmark risk sets: moments described only by the past | comparing whole calls with and without a behaviour | a whole-call comparison conditions on what happens later in the call (§4.2) |
| Effect estimator | cross-fitted doubly robust estimator of the effect on the treated, with template-cluster errors | raw rates; matching; causal-discovery algorithms; asking an LLM | raw rates exaggerated harmful effects by 1.5 to 6 times, discovery is unstable with dozens of behaviours, and models are near chance at causal inference (§4.4, §7.2) |
| Sub-groups and policies | not estimated unless pre-registered; single-moment effects only | causal-forest sub-group search; marginal structural models | the first invites fishing, the second answers a different question; both are named as extensions (§10.1, §11) |
| Faithfulness of evidence | cross-fitted hazard forecaster with comprehensiveness against random removal | training rationale networks; attention weights | rationale networks need reliable labels and GPU time, and a faithfulness score is a model check, not a causal claim (§4.5) |
| Retrieval | BM25 plus dense or latent-semantic embeddings, fused by rank, one diverse window per call | dense only; a trained conversational retriever; LLM-built graphs | specific terms and paraphrases both matter; no supervised data; deterministic and cheap (§4.6) |
| Reading a question | rules, phrase tables and spelling correction, validated against a vocabulary; an LLM only as a fallback | LLM-only parsing | deterministic slots that can be tested; works offline (§4.7) |
| Writing an answer | templates filled with placeholders; an optional LLM bound to the same placeholders | a free-text LLM answer | numbers and claim strength cannot drift, and three gates check the result (§4.8, §4.9) |
| Follow-ups | explicit state, validated delta, four routes | rewriting the whole question; long-term memory frameworks | a rewrite can silently drop a filter, and a session needs a small explicit state, not weeks of memory (§5) |
| Before/after questions | interrupted time series with placebo dates | the simple difference of two periods alone; synthetic controls | the simple difference cannot separate a trend from a change, and a synthetic control needs several untreated comparable units, which a question about all calls does not have (§4.10, §11) |

---

## 4. Methodology for Task 1: evidence-based causal explanation

### 4.1 Step 1: events and their onset

| Event | Onset: the first turn where… | Subtypes stored |
|---|---|---|
| **Escalation** | the customer asks for a supervisor, manager or "someone above you"; or the agent hands the call to a *named senior person or team*; or the agent offers to and the customer accepts in the next turn | customer request, agent handoff |
| **Refund** | either party raises a refund, compensation, credit-back or chargeback | customer request, agent offer |
| **Churn threat** | the customer states an intention to cancel, close, switch or not renew, including hedged intent towards a competitor or "elsewhere" and clear disengagement ("you just lost a customer") | cancel, switch, not renew, other |

Five **secondary events** are labelled so that they can be used as conditions and asked about (a completed supervisor
handoff, a granted refund, a refused refund, a completed cancellation, and **retention risk**). They are never merged with
the three confirmatory events, and no causal effects are estimated for them: they get counts and the rationale from the
conversations only.

**Inference strategy.**

* **Rules for precision.** The default labeller is a lexicon labeller with explicit exclusions, so that every mistake is
  inspectable. Reading real transcripts showed three recurring errors that the rules now avoid. Agents talk *about*
  escalation (as a topic, negated, offered conditionally, or routed to a department), which is the use–mention problem
  (Gligorić et al., 2024) combined with negation and hedge scope (Chapman et al., 2001; Farkas et al., 2010). Customers
  voice churn softly, with an intent word towards a competitor or "elsewhere" (Abbet et al., 2018). Prospects switching
  *to* the company and booking-only cancellations are not churn.
* **A hybrid churn layer** in the spirit of weak supervision (Ratner et al., 2017). The rules (explicit intent plus
  disengagement phrases) act as labelling functions. A logistic classifier trained **only on the train split**, with
  the rule-labelled turns as positives and sampled customer turns from calls without churn or competitor talk as
  negatives, scores the remaining customer turns that follow a complaint, a refusal or a competitor mention and contain
  a leave-related word. A turn is added when its score is at least 0.9. Word and character TF-IDF are the default
  features; sentence embeddings (Reimers & Gurevych, 2019) are used when that package is installed. The number of turns
  added is written to the build checks.
* **Retention risk** is a separate event: churn intent, **or** a competitor mention after the customer has complained or
  been refused, **or** wavering ("second thoughts", "last chance"); its subtype records which. It answers *who is at
  risk of leaving?* without blurring the stricter churn event.
* **Optional LLM route (TnT-LLM; Wan et al., 2024).** An LLM fills a JSON form for about 1,500 stratified train calls
  (present, onset turn, exact onset quote, subtype); each quote must be found in the cited turn or the label is
  discarded; a turn-level logistic classifier is trained on the verified labels and applied to the corpus.

**Validation: a blind gold sample.** 200 held-out calls (150 simple random plus 50 rare-event "stress" calls) are drawn
with *known inclusion probabilities* and labelled by two teammates blind to every system output; 40 calls are
double-coded for Cohen's κ. Metrics are inverse-probability weighted, so they describe the real corpus rather than the
oversampled one: presence precision, recall and F1 with bootstrap intervals, and onset accuracy exactly and within one
turn. The gold sample is never used for tuning.

**Correcting label error downstream.** Any labeller errs, and errors bias effects: if the labeller notices escalations
more easily in calls with refusals, refusals look worse than they are. **Design-based supervised learning** (DSL; Egami
et al., 2023), a close relative of prediction-powered inference (Angelopoulos et al., 2023), uses the random gold
sample and its known inclusion probabilities to keep downstream estimates unbiased, with honest intervals, *however
imperfect the labeller is*. Section 4.4 extends it to the question of which moments are still at risk.

**Why this choice.** Keywords alone miss paraphrases; an LLM on every call is slow, costly, and sends data out. Rules
plus a small learned layer are transparent and free to run, and the gold sample measures and corrects whatever they
miss.

### 4.2 Step 2: landmark risk sets

The causal design treats a conversation as a sequence of decision points. Imagine pausing every call at turn $k$. Among
calls where the event has *not happened yet*, the agent does a behaviour $B$ right now in some and not in others. We
compare what happens later, using only what was said **before** $k$ to make the groups comparable, and pool over all
$k$. This is how records are used to emulate a trial in epidemiology (target-trial emulation; Hernán & Robins, 2016),
and because each turn reacts to the last, the single-turn treatment with the full past adjusted for is the
sequential-trials set-up (Keogh et al., 2023).

$$
B_k=\mathbb 1[\text{behaviour } B \text{ occurs at turn } k],\qquad
Y_k=\mathbb 1[\text{event starts at some turn after } k],\qquad
\text{history}_{<k}\rightarrow B_k\rightarrow Y_k .
$$

**Protocol.**

* **Eligibility at turn $k$:** $k\ge 4$ (after the opening); the event's onset is later than $k$; **no other confirmatory
  event and no supervisor handoff has started before $k$** (after a handoff the agent's "please hold" is part of a
  procedure, a different version of the treatment; Hernán & VanderWeele, 2011); behaviour $B$ has not occurred before
  $k$; turn $k$ is spoken by $B$'s party.
* **Time zero** is turn $k$: eligibility, treatment and follow-up start together, which avoids immortal-time bias
  (Hernán et al., 2016). The call ending counts as part of the outcome, so the estimate is a total effect (Young et al.,
  2020).
* **Covariates** come only from turns before $k$ (117 features): turns and words so far per party; counts of every cue
  per party; earlier behaviours and earlier events; hesitation, repeated questions and holds so far; indicators for the
  last three turns; the opening-based industry and brand; and a 32-dimensional summary of earlier turns. **Turn $k$
  itself is excluded**, because its text reveals $B$ and destroys overlap (Gui & Veitch, 2023), and so is total call
  length, which is known only at the end (post-treatment bias; Montgomery et al., 2018).
* **Events already present in the opening** (before turn 4) are in no risk set; in-call behaviours cannot explain them,
  so their share is reported as "before-call drivers".
* **Future-invariance test.** For 1,000 random rows, every turn after $k$ is replaced by random text and the covariates
  are rebuilt; they must be bit-identical. The build fails otherwise. In the demo: 0 failures in 1,000 rows.

Ordering is an *eligibility rule*, not proof of cause: turn-by-turn forecasting of derailment (Zhang et al., 2018; Chang
& Danescu-Niculescu-Mizil, 2019) is the precedent for looking at the conversation before the event, but causal status
comes only from Step 4. Marginal structural models and g-computation would be needed for *sustained* strategies such as
"never refuse"; this is listed as an extension (§11), not claimed.

### 4.3 Step 3: behaviours and negative controls

The registry has **14 candidate behaviours**: seven by agents (hold request, return from hold, apology, empathy, refusal
or policy citation, concrete solution offer, transfer) and seven by customers (frustration, confusion, repeat contact,
issue persistence, repeated question, hesitation, competitor mention). It adds **two negative controls**, neutral agent
behaviours that should have no effect on any event: reading back an id, and thanking the customer for information.

* **Outcome-blind detectors.** Each detector is turn-local: it is recomputed from that turn's own text alone and must
  give the identical answer (a check that fails the build), and the repeated-question detector looks only at earlier
  turns, so no detector can see the outcome or the future. Behaviours that are definitional or near-synonyms of an event
  (for example supervisor-request wording for escalation) are excluded as causes of that event.
* **Actionability.** Customer states (frustration, confusion) cannot be changed by the company, so they can be reported
  as warning signs but never reach the strongest claim level (well-defined interventions; Hernán & Taubman, 2008).
* **Noisy proxies.** The lexicons are imperfect measurements of the underlying behaviour, the situation analysed by
  TextCause (Pryzant et al., 2021). A person judges 20 turns per detector on a *precision sheet*, and the strongest
  claim level requires precision of at least 0.8 on at least 20 judged turns.
* **Families.** Behaviours that co-occur strongly (phi at least 0.7 across calls) are grouped, and answers say that
  co-occurring effects "do not add up".
* **Optional discovery.** An LLM can propose further candidate behaviours by contrasting windows before the event with
  comparable event-free windows (D5; Zhong et al., 2023; concept induction in the spirit of Lam et al., 2024). Proposals
  are *candidates only*: they must pass the same outcome-blindness, prevalence and precision filters and are never
  claims by themselves.
* **Negative controls** (Lipsitch et al., 2010) pass through exactly the same pipeline. If one shows an effect, hidden
  bias is suspected and every claim for that event is capped.

### 4.4 Step 4: causal effect estimation

**Three phases (Egami et al., 2022; Nosek et al., 2018).**

1. **Pilot, train split only.** Run the whole pipeline, tune the learners, inspect overlap, and run the
   **planted-effect test**: on real train rows an outcome with a known +8-point effect (and with no effect) is simulated
   100 times for each of two behaviour–event pairs, and the code must recover the effect with small bias (below 40% of
   the estimator's standard error), about 95% interval coverage and about 5% false alarms under the null (Dorie et al.,
   2019).
2. **Pre-register.** Before any held-out estimate is computed, the analysis plan is frozen with a SHA-256 hash of the
   settings, the event and behaviour definitions and the labels: events, at most 12 behaviours per event chosen by a
   written mechanical rule, the estimand, covariates, learners, trimming, support thresholds, sensitivity analyses and
   claim-level rules. `confirm` refuses to run without it; changing the plan afterwards is recorded as an amendment and
   caps every result at L2.
3. **Confirm once, held-out calls** (dev and test, about 3,900 calls): estimate every pre-registered effect once. Anything
   not pre-registered (for example a single-industry slice) is exploratory and capped at L2.

**Estimand.** The average effect on the treated moments:

$$
\tau_{B\rightarrow E}=\mathbb E\big[\,Y_k(1)-Y_k(0)\,\big|\,B_k=1,\ \text{call still at risk at }k\,\big].
$$

**Estimator.** A cross-fitted, doubly robust (augmented inverse-propensity) ATT, i.e. the "ATTE" score of double/debiased
machine learning (Chernozhukov et al., 2018), re-implemented so that the label-error correction, the risk-set
membership and template-cluster inference fit in, and checked to give identical estimates to the reference
`DoubleMLIRM(score="ATTE")` on the same folds (Bach et al., 2022):

$$
\hat\tau=\frac{\sum_i a_i\kappa_i\Big[T_i-(1-T_i)\dfrac{\hat e_i}{1-\hat e_i}\Big]\big(Y_i-\hat g_{0,i}\big)}
{\sum_i a_i\kappa_i T_i},\qquad
\widehat{\mathrm{SE}}=\frac{\sqrt{\tfrac{G}{G-1}\sum_{g}S_g^{2}}}{\sum_i a_i\kappa_i T_i},
$$

where $T_i$ is the behaviour indicator, $\hat e_i$ the cross-fitted propensity, $\hat g_{0,i}$ the cross-fitted outcome
model under no behaviour, $a_i$ the at-risk indicator, $\kappa_i=\mathbb 1[\hat e_i\le 0.9]$ the overlap trimming
(Crump et al., 2009), and $S_g$ the sum of the score's residual contributions in template group $g$ (cluster-robust
errors over $G$ groups; Chiang et al., 2022). Five folds are formed **by template group**. Propensity and outcome models
are logistic or gradient-boosting learners, tuned on train and fixed in the pre-registration.

**Label-error correction (DSL, extended).** The labeller decides both the outcome and *which moments are at risk*, so
each call's contribution $c$ to the numerator and denominator is replaced by
$\tilde c=c^{\text{lab}}+\tfrac{R}{\pi}\,(c^{\text{gold}}-c^{\text{lab}})$, with $R=1$ for gold calls and $\pi$ their
inclusion probability (Egami et al., 2023). A missed escalation then no longer leaves post-event rows in the risk set.

**Safeguards before anything is called a finding.**

| Safeguard | What it checks | Paper |
|---|---|---|
| Overlap | treated moments with no comparable untreated moments are dropped, and the share is reported | Crump et al. (2009) |
| Balance | after weighting, the standardised difference of the *prognostic score* is at most 0.1 | Stuart et al. (2013); Austin (2009) |
| Clustered uncertainty | template-group standard errors plus a 2,000-draw cluster bootstrap | Chiang et al. (2022) |
| Many tests | Benjamini–Hochberg at q = 0.05 over the whole pre-registered family | Benjamini & Hochberg (1995) |
| Negative controls | a control with an effect caps all claims for the event | Lipsitch et al. (2010) |
| Hidden confounding | the E-value: the risk ratio a hidden factor would need with both behaviour and event, $E=RR+\sqrt{RR(RR-1)}$ | VanderWeele & Ding (2017) |
| Replication | dev and test estimates must agree in sign | Egami et al. (2022) |
| Sensitivity | S1 six-turn horizon; S2 without inferred-role calls; S3 without possibly truncated calls; S4 with unflagged metadata; S5 moments after another event; S6 the other learner; S7 single-call template groups; S8 onset shifted by one turn. S2, S3, S5 and S8 must keep the sign | — |
| Estimator self-test | the planted-effect test above | Dorie et al. (2019) |
| Population impact | attributable events = ATT × number of treated moments, with an interval | — |

**Claim levels, computed by code, never edited by hand.** A factor reaches **L3** only if all eleven checks pass: it is
pre-registered; it is actionable; support is sufficient (at least 20 events in each arm, at least 80% of treated moments
kept, interval half-width at most 10 points, balance at most 0.1); the BH q-value is below 0.05; the cluster-bootstrap
interval excludes zero; the required sensitivity analyses keep the sign; dev and test agree; the negative controls are
clean; the planted-effect test passed; the labeller's gold F1 is at least 0.7; and the detector's precision was verified
by a person.

| Level | Meaning | Wording the gates allow |
|---|---|---|
| **L3** | every check passed | "is estimated to raise / lower … under the stated assumptions" |
| **L2** | an estimate exists, but a check failed (the failed checks are shown) | "is associated with …", "warning sign", or "no clear difference" when the interval includes zero |
| **L1** | counts only | no link words |
| **L0** | nothing reliable | the answer says so |
| **NC** | negative control | used only to detect hidden bias |

**Why this algorithm.** Raw comparisons mix cause and coincidence. Asking an LLM whether X causes Y is near chance (Jin et
al., 2024). Causal-discovery algorithms are unstable with dozens of behaviours. Matching was replaced rather than
patched: double machine learning with overlap and balance diagnostics does what matching was meant to do, reports when it
cannot, and gives valid error bars with flexible nuisance models for a high-dimensional history (Chernozhukov et al.,
2018; Keith et al., 2020; Egami et al., 2022).

### 4.5 Step 5: evidence spans and faithfulness

A causal estimate alone does not show *where* the behaviour happens. For every factor the system retrieves **grounding
spans**: in held-out calls, the first turn after the opening where the behaviour occurs, before any onset of the event.
Only raw dialogue is citeable, and each span carries its provenance (call, turn, speaker, split, industry).

Three claims are kept apart and never merged into "this line caused the event":

$$
\boxed{\text{causal effect}\ \neq\ \text{dialogue evidence}\ \neq\ \text{model faithfulness}}
$$

* **Causal effect:** Step 4.
* **Dialogue evidence:** the turn where the behaviour occurs.
* **Faithfulness:** how much a *risk forecaster* relies on that turn. The forecaster is a cross-fitted discrete-time
  hazard model (class-weighted logistic regression on cue-token TF-IDF and the history features, trained with random
  turn dropout, folds by template group), following the turn-by-turn forecasting of Chang & Danescu-Niculescu-Mizil
  (2019). Faithfulness is measured by removing the span, replacing it by a neutral turn, and removing random turns of
  the same speaker, as in the comprehensiveness measure of ERASER (DeYoung et al., 2020). It is **direction-aware** (a
  protective behaviour should *raise* the forecast when removed), the keep-only sufficiency variant is dropped because
  such inputs are out of distribution (Hase et al., 2021), and a factor passes when at least five spans are scored and
  the median percentile against the random baseline exceeds 50. A high score is a check of the model, never proof of
  causation (Jacovi & Goldberg, 2020).

### 4.6 Step 6: evidence graph and hybrid search

Raw dialogue is split into overlapping 5-turn windows (stride 3). Retrieval fuses a lexical and a semantic ranking:

* **BM25** (k1 = 1.5, b = 0.75) for exact, domain-specific terms;
* **dense embeddings** from a sentence encoder when available (Reimers & Gurevych, 2019), with a latent-semantic-analysis
  embedder (128 dimensions) as the offline fallback; the backend is recorded in the index version;
* **Reciprocal Rank Fusion** (Cormack et al., 2009; k = 60) to combine them;
* **one window per call** and **Maximal Marginal Relevance** (Carbonell & Goldstein, 1998; λ = 0.7) for diversity.

Hybrid retrieval gives better coverage than either ranking alone: business questions use specific terms, but the evidence
may be phrased differently. Short, ranked evidence is also what long-context generators use best (Liu et al., 2024).

### 4.7 Step 7: understanding the question

Each question becomes a small validated form (`QuerySpec`): the event, the filters, the kind of question (why, how often,
examples, compare, trend, what to change, effect of a behaviour, explain a factor, product problems, behaviours shared
by several events, link between two events, behaviour profile, overview, one call), the behaviour, the premises it
presupposes, and the parts the data cannot answer.

**Reading robustly (without an LLM).** The question is processed in a fixed order, and every change is reported in the
answer ("I read 'custmers' as 'customers'"):

1. **Brand names are masked first**, so that a brand word is never mistaken for an industry.
2. **Language identification** by scoring the question against frequency profiles of stop words and accented letters
   for English, Spanish, French, German, Portuguese, Italian, romanised Hindi and Devanagari Hindi (the profile idea of
   Cavnar & Trenkle, 1994, with word and accent profiles instead of character n-grams); a strong code-mixing marker wins
   over English words in Hinglish (code-mixing is hard for general systems; Khanuja et al., 2020). Domain phrase tables
   map event words, industries, behaviours, thresholds and question words to English.
3. **Slang** ("blow up", "the boss", "jump ship") is mapped to the vocabulary the parser knows.
4. **Spelling correction** by edit distance with transpositions (Damerau, 1964) to a domain vocabulary, taking the
   closest word and, among equals, the more frequent one (a simplified noisy-channel choice; Brill & Moore, 2000), but
   **never changing a word that occurs at least three times in the corpus itself**, so real words of this dataset are
   protected.
5. The remaining slots: policy or change dates, conditions between events (*customers who were refused a refund and
   threatened to cancel*, one or several), effect or rate thresholds (*by more than five percentage points*, *which
   behaviours do not affect…*), call ids, filters, behaviours, and the event.
6. **With an LLM configured,** if the rules find no event or had to translate, the LLM rewrites the question in English and
   the rules read *that*; the answer shows the reading. Slot values are always validated against the allowed vocabulary.

**Allowed filters and account fields.** Only industry from the opening turns, brand, dates and unflagged metadata are
allowed. A field that may be written after the call would select calls by their outcome (selection bias; Hernán et al.,
2004), so such filters are declined with an explanation. If an `account_attributes.csv` is supplied (tier, plan, segment,
tenure), those fields become filters and ranking dimensions; without it the answer says which field is missing. What
customers *say* about their status is kept as a separate, explicitly labelled variable ("self-reported, not a verified
tier") and used only as a proxy.

**Premises and guard-rails.** A presupposition such as *"Why does empathy cause escalations?"* is checked against the
Factor Library before it is answered, and a false premise is corrected first with the estimate (false presuppositions:
Yu et al., 2023; agreeing with the user's premise: Sharma et al., 2024). Parts that cannot be answered are named in a
notice, never silently dropped or re-interpreted:

* audio and tone of voice, and timing inside calls (there are none in the data);
* behaviours the system does not detect, and whole-call policies ("if agents never refused");
* an effect of one event on another (only co-occurrence and order are shown);
* individual agents, demographics, location, and satisfaction scores;
* an effect **within a sub-group** ("only when the customer is already frustrated"; effect modification, VanderWeele,
  2009), and the counterfactual of **one particular call** ("would this customer still have escalated?"), which is not
  identified from data (Tian & Pearl, 2000);
* "no effect" is read as "the interval includes zero", with the warning that absence of evidence is not evidence of
  absence (Altman & Bland, 1995).

**Support policy.** Every requested slice (event × filters) is checked against four criteria: events per arm, share of
treated moments kept, interval half-width, and balance. The worst band decides: borderline slices carry a warning and
are at most L2; insufficient ones are reported as not estimable, with counts and the nearest supported slice.

### 4.8 Step 8: evidence pack and answer synthesis

Code builds an **evidence pack**: validated estimates, claim levels, counts, quotes, support diagnostics, co-occurring
factors, caveats and provenance ids. The writer, a template by default or an LLM bound to the same placeholders, never
sees a number it could change:

```text
{F2.att}   {F2.ci}   {F2.n_treated}      →  filled in by code from the Factor Library
```

Every answer starts with a **rationale drawn from the conversations themselves**, clearly labelled as description, before
the causal test is reported:

* the *situation*: words that customers use in the opening, before anything the agent does;
* *what happened in the six turns before the event*, against the same point in calls without it (the same idea as
  contrastive scoring of call fragments, Mishne et al., 2005);
* who started the event, the customers' own words, and one call step by step;
* then the *causal test* on held-out calls, with the claim level of each factor.

The six-turn contrast is descriptive. It uses the same placeholders, gates and claim ladder, and it is never worded as an
effect. The citation format (`[transcript_id:turn]`) follows ALCE (Gao et al., 2023). Questions about **one call**
(`Why did call <id> escalate?`, `tell me more about that call`) get that call's own events in order, the customer's
problem, the behaviours in the turns before the event with quotes, how common those moments are across calls, and the
confirmed factors among them, with the caveat that general estimates do not prove why one call went the way it did.

### 4.9 Step 9: three gates

Every sentence passes three **separate** checks, because numerical consistency, causal validity and textual support are
different verification problems:

1. **Numbers.** Every digit must come from a placeholder; unknown placeholders, and quantities written in words
   ("half of", "twice"), are rejected.
2. **Causal wording.** Each sentence is classified into the categories of causal-language use (no relation,
   correlational, conditional causal, direct causal; Yu et al., 2019). *Direct causal wording ("causes", "leads to",
   "drives") is never allowed*; the strongest wording a sentence may use is bounded by the weakest factor it cites (L3:
   conditional causal; L2: correlational; L1 and L0: none), and a sentence linking a behaviour to an event must cite a
   factor.
3. **Evidence.** Every quotation must be an exact substring of the cited raw turn; a descriptive sentence that cites turns
   without quoting needs lexical support of at least 0.5 in them. (A learned entailment scorer such as AlignScore, Zha et
   al., 2023, would need a large model and a GPU; exact quoting needs neither.)

A failing sentence is rewritten once (LLM writer only), then dropped; an answer with nothing left degrades to an honest
"cannot be answered".

### 4.10 Changes over time: before/after questions

For *"did X change after <date>?"* the answer first gives the simple comparison of the two periods with a 95% interval.
It then fits an **interrupted time series**, a segmented regression of the event share per period (Wagner et al., 2002;
Lopez Bernal et al., 2017):

$$
y_t=\beta_0+\beta_1 t+\beta_2 D_t+\beta_3\,(t\,D_t)+\textstyle\sum_s\gamma_s S_{st}+\varepsilon_t,\qquad D_t=\mathbb 1[t\ge t_0],
$$

where $\beta_1$ is the **pre-trend**, $\beta_2$ the **level change** at the date and $\beta_3$ the **slope change**.
Periods are weighted by their number of calls; the period length (week, day, six hours, hour) is chosen so that each side
has at least six periods with enough calls; time-of-day or day-of-week terms $S_{st}$ are added when the series is long
enough; standard errors are the larger of the Newey–West (Newey & West, 1987) and the classical estimate. The answer adds
**placebo dates** (the same model at up to 20 made-up dates before the real one, counting how many shifts are as large;
placebo logic in time: Abadie et al., 2010) and, when the question has a filter, a **comparison series** of the other
calls. The last sentence always says that a change is tied to the date, not to its cause. If no date is given (*"after the
new refund policy"*), the system asks for it.

---

## 5. Methodology for Task 2: contextual follow-up reasoning

Task 2 maintains analytical context across turns. Consider:

> **Q1:** Why do escalations happen in telecom calls? **Q2:** What about refunds? **Q3:** Only for airlines.

The system must infer `event = escalation, industry = telecom`; then change only `event = refund`; then change only
`industry = airline`. Everything else stays.

### 5.1 State and delta

**State.** The session keeps the current question form (event, filters, kind, behaviour, condition, threshold, change
date), the factor ids and cited turns already shown, the library and index versions, a short summary, and the calls quoted
in the last answer.

**Delta.** A follow-up is turned into a *set of changes* to known slots (set, add, remove, replace-all), not into a
rewritten question. By default the delta comes from rules; with an LLM configured it can come from a few-shot prompt in
the style of in-context dialogue-state tracking (IC-DST; Hu et al., 2022), and rules still add the slots the LLM schema
does not cover. **Code validates** every delta (an unknown slot, event, industry or value triggers a clarifying question)
and **merges it deterministically**, so a slot the user did not mention cannot be dropped. Free rewriting of the whole
question (CANARD; Elgohary et al., 2019; QReCC; Anantha et al., 2021) can silently remove a filter; LLM rewriting is used,
if at all, only for *retrieval text* (LLM4CS; Mao et al., 2023) and never sets filters.

**Follow-up behaviours the rules handle:** a new event (*what about refunds?*), a new filter or its removal (*only hotel
calls*, *remove the filter*, *other industries*), a factor reference (*explain the second factor*), a ranking followed by
*why?* (the top group is explained), a behaviour followed by an event (*what about escalations?*), a comparison with
another event or industry, a policy date given in a follow-up, a condition or threshold carried to the next event,
*hello* → *overview* → an event, and *that call* or *the third example* after an answer with quotes.

### 5.2 Routing

After the delta is applied, the system chooses one of four routes (the decision of when to reuse and when to retrieve
follows Roy et al., 2024, implemented as rules with no training):

| Route | When | What runs |
|---|---|---|
| **Reuse** | no slot changed (*explain the second factor*) | the evidence pack already built |
| **Re-filter** | a filter changed | the support policy is re-run on the new slice, then a new pack |
| **New lookup** | the event or kind of question changed | question reading → pack → writing |
| **Clarify** | the delta is invalid, empty or ambiguous | one short question; the state is not changed |

Whenever the population changes, the support policy is recomputed, so an estimate is never carried into a sub-group for
which the data are too thin. Answers are cached by a hash of the question form and the library, index and writer
versions, so an update can never serve a stale answer.

### 5.3 Robustness of the session

A saved session is validated on load: a corrupt, hand-edited or stale file (an unknown event or question kind, a malformed
filter) is not trusted; the conversation restarts with a notice instead of failing. An unknown call id keeps the previous
state. These cases are covered by 19 scripted multi-turn flows and unit tests (§7.7).

---

## 6. Evaluation design

### 6.1 What is evaluated on what

1. **A synthetic call centre with a causal oracle** (4,000 calls, seed 11; a 20,000-call run for scale). A latent
   severity and a policy-strictness state evolve through each call; agent refusals raise the customer's frustration,
   which drives escalations, refunds and churn threats; solution offers lower it; holds have small effects; two neutral
   behaviours have none. The **oracle replays every treated moment with and without the behaviour** and so gives the
   true effect on exactly the moments the estimator sees. The simulator writes raw files with the real data's defects
   (name-labelled speakers, analyst notes inside dialogues, duplicates, templated reuse), which go through the **real
   cleaning notebook**; the "blind" gold labels come from simulated annotators with small error rates (0.5% on presence,
   3% on onset).
2. **Checks on the real corpus that need no causal truth:** the event labeller against the 200-call blind gold sample; a
   manual read of 112 real transcripts; and the team's own list of 82 questions and 11 follow-up sessions, run through
   the question parser.
3. **A query set generated by code** from the data (`python -m crest queries`): 98 queries (85 single questions and 13
   follow-up sessions with 41 turns, 126 questions in all), tagged by task, difficulty, kind and use case, de-duplicated
   by ROUGE-L, split into dev queries and a **locked test set whose SHA-256 is recorded before any tuning** and which is
   run once. Each query carries an *expected behaviour* (answer, clarify, refuse part, correct premise, …) that code
   checks (Wang et al., 2023, for the generate-then-filter idea; Yu et al., 2023, for the false-premise categories).

### 6.2 Metrics

| Component | Metrics | Why these |
|---|---|---|
| Event labels | inverse-probability-weighted precision, recall, F1 with bootstrap intervals; onset exact and within ±1 turn; Cohen's κ | measure the labeller on the real population, not the oversampled strata (Wan et al., 2024; Egami et al., 2023) |
| Estimator | planted-effect bias, coverage and null false-alarm rate; **coverage of the true effect, absolute error against an unadjusted baseline, sign of every L3 claim**; negative-control intervals | with a known truth, bias and coverage are the direct measures of a causal method (Dorie et al., 2019) |
| Forecaster and evidence | AUC (next turn, within three turns), calibration slope, expected calibration error; comprehensiveness minus a random-removal baseline | a faithfulness measure is meaningful only if the model forecasts and is calibrated (DeYoung et al., 2020) |
| Retrieval | Recall@10, nDCG@10 on queries with known relevant calls | standard rank-quality measures: is the evidence in the shown set, and how high is it ranked |
| Answers | expected behaviour met per query; slot accuracy (event, kind, filters, behaviour); sentences removed by each gate; wording violations after the gates; degraded answers; seconds per answer | correctness of *what was asked* and of the claim control (Gao et al., 2023; Yu et al., 2019) |
| Task 2 | carry-over accuracy of the state (event, industries, kind, behaviour, conditions, change date); route accuracy | context preservation and routing are scored per turn, as multi-turn benchmarks do (Anantha et al., 2021; Katsis et al., 2025) |
| Question reading | all-slots accuracy on a held-out parser benchmark of clean, misspelled, multilingual and slang questions | the parser is the first point of failure |

All intervals are 95% bootstrap intervals unless a Wilson interval is named; differences between systems use a paired
bootstrap (Dror et al., 2018).

**Not run here:** the human audit of 30 answers and 30 evidence spans (the sheets are generated and empty), the
LLM-as-judge of the query set (it needs an external service), and every LLM-writer or LLM-reader path.

### 6.3 Baselines (and what they are, exactly)

* **B0, retrieval only:** the hybrid search's top-10 windows, with no Factor Library and **no premise or attribute
  checks**. It therefore cannot correct a false premise or flag an unsupported attribute *by construction*; its
  usefulness for counts is measured as the error of a rate estimated from hit counts. It is a structural lower bound,
  not a trained retrieval-augmented LLM.
* **B1, the pipeline without the gates:** not scored separately. The template writer never triggers a gate in this
  benchmark (0 sentences removed), so removing them changes nothing; their value would show with an LLM writer. Adversarial
  unit tests show that the gates catch direct causal wording, typed numbers and altered quotes.
* **B2, stateless reading of follow-ups:** each follow-up is read as a standalone question, which is the best a rewriter
  without the session state can do. It is scored on the **event and industry** of the 27 later turns that are not
  clarifications, and the system is scored on exactly the same turns and slots for the comparison. An LLM rewriter that
  sees the history would do better and was not run.
* **B3, an associational library:** the raw difference in event rate between treated and untreated at-risk moments, with
  no adjustment, compared with the truth.

---

## 7. Quantitative results

### 7.1 Event labelling

**Synthetic corpus (simulated blind gold set, 200 calls).**

| Event | Precision | Recall | F1 (95% CI) | Onset within 1 turn | κ |
|---|---|---|---|---|---|
| Escalation | 0.991 | 1.000 | 0.995 (0.985–1.000) | 1.00 | 1.00 |
| Refund | 1.000 | 1.000 | 1.000 | 1.00 | 1.00 |
| Churn threat | 1.000 | 1.000 | 1.000 | 1.00 | 1.00 |

Against the simulator's own truth on all 4,000 calls the labeller is exact. This is optimistic: simulated speech is far
more regular than real speech, so it shows that the plumbing works, not what accuracy to expect on real calls.

**Real corpus (200-call blind gold sample; rules only; unweighted; measured once, with the errors not inspected).**

| Event | Precision | Recall | F1 | First version of the rules |
|---|---|---|---|---|
| Escalation | 1.00 | 0.77 | 0.87 | 0.50 / 1.00 / 0.67 |
| Refund | 0.95 | 0.88 | 0.92 | 0.95 / 0.88 / 0.92 |
| Churn threat | 0.82 | 0.56 | 0.67 | 0.74 / 0.29 / 0.42 |

The rewrite was driven by reading 112 real transcripts (never by the gold sample): escalations fell from 19 to 6 calls,
all six consistent with the definition (the old rule had counted agents *talking about* escalation), and churn threats
rose from 10 to 29 calls (soft, competitor-directed forms), with 56 calls showing retention risk. The semantic layer
added one turn in that sample, which was correct; it learns from the full corpus and **cannot be measured on the gold
sample until the corpus is rebuilt**. The DSL correction keeps the effect estimates valid either way; a better labeller
only makes them tighter.

### 7.2 The estimator: self-test and recovery of known effects

**Planted-effect test** (200 simulations on the train rows, +8 points planted): bias −0.0074 (Monte-Carlo s.e.
0.0028), which is −26% of the estimator's standard error (allowed: 40%); coverage 0.94 (Wilson 0.875–0.972); false alarms
under the null 0.06 (0.028–0.125). Passed.

**Recovery of the true effects** (4,000 calls; percentage points; truth from the oracle):

| Event | Behaviour | Level | Truth | Estimate (95% CI) | Unadjusted (B3) |
|---|---|---|---|---|---|
| Escalation | solution offer | L3 | −28.9 | −31.5 (−37.8, −25.2) | −36.6 |
| Escalation | policy refusal | L3 | +30.9 | +32.2 (+26.6, +37.7) | +46.9 |
| Escalation | hold request | L3 | +6.2 | +8.6 (+2.6, +14.5) | +17.3 |
| Refund | solution offer | L3 | −12.7 | −15.9 (−22.0, −9.9) | −16.1 |
| Refund | hold request | L2 | +1.1 | +2.8 (−2.5, +8.1) | +6.8 |
| Refund | policy refusal | L2 | +3.1 | +2.2 (−3.0, +7.4) | +10.6 |
| Churn | solution offer | L3 | −8.7 | −7.7 (−11.6, −3.8) | −7.6 |
| Churn | policy refusal | L2 | +4.2 | +4.1 (+0.2, +8.0) | +8.8 |
| Churn | hold request | L2 | +1.0 | +2.9 (−1.4, +7.1) | +4.5 |
| Escalation / refund / churn | neutral control (thanks for information) | NC | 0.0 | +0.7 / −1.7 / +0.9 (all intervals include 0) | −1.9 / −0.2 / +1.7 |

* **Coverage:** the 95% interval contained the true effect for **12 of 12** factors with an oracle.
* **Accuracy against the unadjusted baseline:** mean absolute error **0.015** (95% CI 0.011–0.021) against **0.054**
  (0.032–0.081) for B3; the paired difference is 0.038 (0.017–0.066), so adjusting for the conversation so far removes
  about 72% of the error. The unadjusted comparison *exaggerates* harmful behaviours: it puts policy refusals at +46.9
  points for escalation (truth +30.9) and hold requests at +17.3 (truth +6.2); the adjusted estimates are +32.2 and +8.6.
* **Claims:** 5 confirmed (L3) claims; all 5 have the correct sign and none has an interval on the wrong side of the truth.
* **Negative controls:** all six intervals include zero; the largest estimate is 3.0 points.
* **Where the claims stand:** of 26 behaviour–event estimates, **5 reach L3, 16 stay at L2 (warning sign or "no clear
  difference") and 5 are L1** (counts only); 6 more are negative controls. Most findings are deliberately cautious.
* **Fragility is reported, not hidden:** the E-values of the three L3 escalation findings are 4.41 (solution offers), 3.16
  (refusals) and 1.70 (holds), so a modest hidden factor could explain away the hold effect, and the answer says so.

**At 20,000 calls** (about the real corpus size): the planted-effect test passed (bias +0.003, 22% of the standard error,
coverage 0.95); **11 of 12** intervals covered the truth (the miss, refusal → refund, is an L2 "no clear difference"
estimate: truth +2.5, estimate −0.0, interval −2.2 to +2.1); 6 L3 claims, all with the right sign; mean absolute error
0.011 against 0.041 for B3.

### 7.3 Evidence: forecaster, faithfulness and retrieval

| Event | Forecaster AUC, next turn (95% CI) | AUC within three turns | Calibration slope | ECE | Comprehensiveness minus random (95% CI; calls) |
|---|---|---|---|---|---|
| Escalation | 0.934 (0.922–0.945) | 0.851 | 1.05 | 0.004 | +0.056 (+0.038, +0.076; 255) |
| Refund | 0.871 (0.856–0.885) | 0.760 | 1.09 | 0.004 | −0.011 (−0.024, +0.001; 137) |
| Churn threat | 0.891 (0.871–0.910) | 0.792 | 1.06 | 0.003 | +0.009 (+0.001, +0.017; 97) |

The forecasters are accurate and well calibrated, so the faithfulness measure is meaningful. **13 of the 26 factors**
pass the faithfulness check (median percentile above 50 against random removal). The turns the model relies on most are
refusals (80th percentile for escalation), holds (71st) and hesitation (88th); **solution offers**, the strongest
*protective* factor, are not among them (39th). The forecaster reads the customer's mood and the agent's refusals more
than the offer itself, which is exactly why faithfulness is reported as a check of the model and never as evidence of a
cause.

**Retrieval** (18 queries with known relevant calls, offline LSA embeddings): Recall@10 **0.939** (0.883–0.983), nDCG@10
**0.935** (0.866–0.988).

### 7.4 Answer quality on the query set

* **Expected behaviour met: 81 of 81 scored single questions** (95% Wilson interval 95.5–100%): 53 of 53 dev
  (93–100%) and 28 of 28 in the locked test set (88–100%), in all 27 scored categories, at every difficulty (12 easy,
  43 medium, 26 hard). The four *known-limitation* questions are reported separately and are not in this score (§10).
* **Slot accuracy:** event 71 of 71, question kind 56 of 56, filters 12 of 12, behaviour 15 of 15.
* **Claim control:** **0 of 1,342 sentences removed by the gates**, 372 quotes all exact substrings of their cited
  turns, **0 wording violations, 0 degraded answers**.
* **Guard-rail categories** (false and true premises, leading questions, unanswerable, out-of-scope, unsupported filters,
  tiny sub-groups, ambiguous): **all as expected**: false premises were corrected with the estimate, unsupported parts
  were named, ambiguous questions were clarified.
* **Newer capabilities** (noisy text, six languages, conditions, before/after, thresholds, behaviour profiles, overviews,
  retention risk, single calls): all as expected.
* **Speed:** median 0.05 s and 95th percentile 0.09 s per answer on one CPU core with the template writer.

The dev and test queries come from the same generator, and the dev set was used while building, so this result shows that
the designed behaviours work and do not regress. Evidence of generalisation comes from the real-question reviews (§7.7,
§9.4).

### 7.5 Task 2: follow-ups

| Measure | Dev | Locked test | Pooled |
|---|---|---|---|
| Sessions (turns) | 9 | 4 | 13 (41) |
| State carry-over (event, industries, kind, behaviour, conditions, change date) | 28 of 28 | 12 of 12 | **40 of 40** (Wilson 91–100%) |
| Route accuracy (reuse, re-filter, new lookup, clarify) | 19 of 19 | 9 of 9 | **28 of 28** (88–100%) |

Beyond the scored sessions, **19 scripted multi-turn flows** (including clarify-then-answer, a ranking followed by *why?*,
a policy date given in a follow-up, a follow-up in Spanish, a condition carried across events, *that call*, and
*hello → overview → event*), round-trips of the session state through JSON, corrupt and stale session files, and a
battery of 62 unusual single questions plus 7 further sessions (30 turns: empty text, a 500-character string, unknown
ids, mixed languages, false premises, unsupported filters) ran with **no crash and no dropped sentence**, including on a
workspace built before the v4 changes.

### 7.6 Comparison with the baselines

| Baseline | Measure | Baseline | CREST |
|---|---|---|---|
| **B0**, retrieval only | false premises corrected / unsupported attributes flagged (9 questions each) | 0 of 9 / 0 of 9 (by construction) | 9 of 9 / 9 of 9 |
| **B0** | absolute error of a rate estimated from the top-10 hits | 0.186 (2 queries, dev), 0.047 (1 query, test) | exact counts from the event table |
| **B2**, stateless reading of follow-ups | carry-over of event and industry on the 27 later, non-clarify turns | 7 of 19 (dev, 37%), 1 of 8 (test, 12.5%); pooled 8 of 27 (30%, Wilson 16–48%) | 27 of 27 (19 of 19 dev, 8 of 8 test; Wilson 87–100%); the full six-slot state on all 40 scored turns: 40 of 40 |
| **B3**, unadjusted library | mean absolute error of the effects | 0.054 | 0.015 |
| **B1**, no gates | removed sentences | not scored (the template writer never triggers a gate) | 0 of 1,342 |

These are *structural* baselines (§6.3). They show what each component adds: B0 has no premise or attribute checks, B2
has no state, and B3 has no adjustment. They are not measurements of a tuned LLM system, which was not run.

### 7.7 Robustness, scale and the real-data reviews

* **Question parser benchmark** (`python -m crest parser-bench`): 52 dev and 51 test questions in four groups (clean,
  keyboard-typo misspellings, six languages, slang). All slots right for **51 of 51** test questions (Wilson 93–100%) and
  52 of 52 on dev. The questions were written by the developers and the test split was run once before it was used
  again only to check for regressions, so this is an upper bound.
* **Question loopholes found on the team's real query list:** 12 (misspellings and slang found no event; effect thresholds
  silently ignored; a policy-change question read as "two events in one call"; *customers who were refused a refund*
  answered about refunds; brand names leaking into industries; …), all fixed and turned into regression tests.
* **Interrupted-time-series intervals** (simulation: 1,500 series per setting, a +5-point level shift, 300 calls a day,
  the underlying daily rate following an AR(1) process): the 95% interval for the level shift covered the truth in
  **95%** of series with independent errors, **92%** (20 days), **90%** (30 days) and **89%** (60 days) with
  autocorrelation 0.5, and 89% with 0.8 (30 days); Newey–West alone covered only 78–84%. The interval is therefore close to
  nominal for independent errors and somewhat too narrow under strong autocorrelation; the answer prints the lag-one
  residual autocorrelation and, from 0.3 up, says that the interval can be too narrow.
* **Scale:** 20,000 calls (380,140 turns; 300,140 landmark rows × 117 features) ran through every stage in about
  **55 minutes** on 4 cores with a **4.9 GB** peak, most of it in the pilot and the confirmation with the
  gradient-boosting learner.
* **Software checks:** 202 automated tests (the four cross-checks against reference packages run when those are
  installed): the estimator gives the same estimates as `DoubleMLIRM(score="ATTE")` on identical folds (difference below
  0.002), the BM25 implementation matches `rank_bm25`, and the prediction-powered mean matches `ppi_py`. On Python 3.10
  with the oldest supported libraries (numpy 1.24, pandas 2.0, scikit-learn 1.2), the 184 tests that need no optional tool
  pass.

---

## 8. Qualitative results

The examples below are verbatim from the synthetic demo (`examples/synthetic_demo/QUERY_OUTPUTS.md`, which has every query
with its full answer); the calls are invented. Long answers are shortened with "…". The question was whether the system
answered *the question actually asked*, kept causal and descriptive claims apart, and grounded what it said.

**Shared drivers, and wording tied to the weakest factor.** *"Do the behaviours that raise escalations also raise churn
threats?"* The two events are analysed separately, and a sentence that cites factors of different strength is worded for
the weaker one:

> Warning sign for escalations and churn threats: policy refusals are associated with a higher chance of an escalation
> (+32.2 percentage points, 95% CI +26.6 to +37.7 points) [F2] and of a churn threat (+4.1 percentage points, 95% CI +0.2
> to +8.0 points) [F20]. … Of these, the following passed every causal check for their event: holds and wait requests for
> escalations [F3], policy refusals for escalations [F2], solution offers for escalations [F1], solution offers for churn
> threats [F19]. … Each event was analysed separately; a behaviour flagged for several events is not shown to connect the
> events to each other.

[F2] is L3 but [F20] is L2, so the shared sentence says "associated" and the L3-only sentence is kept separate.

**A false premise.** *"Why do solution offers increase escalations?"*

> The data does not support this premise: solution offers are associated with a lower chance of an escalation, the opposite
> direction (−31.5 percentage points, 95% CI −37.8 to −25.2 points) [F1]. Why, from the conversations: … the agent offered a
> concrete solution in only 27.3% of them (against 68.7% at the same point in other calls). … Under the stated assumptions,
> solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points … [F1].

**Two events that co-occur.** *"Do escalations lead to refund requests?"* The system separates co-occurrence, order and
effect:

> Effects of one event on another are not estimated (only behaviours inside the call are studied as possible drivers), so
> the counts below only show how often escalations and refund episodes occur in the same calls and which one started first.

A related condition question, *"Do refunds happen more in calls with escalations?"*, answers from the condition: 38.4% of
the 1,865 calls with an escalation had a refund episode, against 23.7% of the calls without one; in the calls with both,
the refund came first in 636 and the escalation first in 81.

**Missing information, and a policy that is not a moment.** *"How long are customers kept on hold before they
escalate?"*

> The transcripts carry no timing information (no durations or timestamps inside calls), so that part of the question
> ('how long') cannot be answered. From the conversations: in the 6 turns before an escalation, the agent put the customer
> on hold or asked them to wait in 37.2% of these calls, against 26.9% at the same point in calls without one.

*"What would happen to refund requests if agents never refused anything?"* is answered with *"Effects are estimated for
single moments in a call, not for a rule applied to every call … so the answer below covers that narrower question."*

**Support policy in a follow-up.** After *"Which industry has the most refund requests?"* (a ranking with counts, and the
caveat that differences between groups of calls "are not effects of anything in the calls"), the follow-up *"why in hotel
calls?"* keeps the event, adds the filter, and states:

> Estimates for hotel calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as
> warning signs at most. Causal test: no in-call behaviour passed every causal check for refund episodes in hotel calls;
> the behaviours below are warning signs only.

**One call, step by step.** *"Why did call 716bf356-… escalate?"*

> Call 716bf356-… is a retail call to Shopnest from 2025-11-04 19:28, with 35 turns. Business events detected in this call,
> in order: a refund episode at turn 5; an escalation at turn 27; a supervisor joining at turn 29. The customer's problem
> (turn 1): "hi i'm calling because my package was not delivered after two weeks …" Step by step, in the 6 turns before the
> escalation: turn 25, the customer expressed frustration or anger: "i see this is ridiculous …" Turn 26, the agent refused
> a request or cited policy: "… unfortunately per our policy um i'm not able to change that" Then the escalation (turn 27):
> "i want to speak to a supervisor right you know now this is ridiculous" … *This walks through one call from its own
> turns. The shares and estimates describe calls in general; they are not proof of why this particular call ended in an
> escalation.*

**A change over time.** *"Compare refund requests before and after 2025-11-08."*

> A refund episode happened in 29.3% of calls before 2025-11-08 and in 31.7% of calls from 2025-11-08 on: a difference of
> +2.5 percentage points (95% CI −0.4 to +5.3 points). The interval includes zero, so the data cannot tell the two periods
> apart. Interrupted time series (6-hour block periods: 15 before … and 18 from it): … at the date its level shifted by
> +4.5 percentage points (95% CI −3.4 to +12.4 points) and its trend changed by +0.5 percentage points per 6-hour block
> (95% CI −0.4 to +1.3 points). … Placebo check: at 4 made-up dates before 2025-11-08, 2 level shifts were at least as large
> as the real one, so the shift at the real date is within the series' usual movement. … Read with care: these
> comparisons tie a change to the date only; anything that changed around 2025-11-08 (the season, the mix of calls,
> staffing) would show up the same way.

**Noisy and non-English questions.** *"why do custmers escalte so often?"* → *"I read 'custmers' as 'customers'; 'escalte'
as 'escalate'."* and then the full answer. *"Pourquoi les clients demandent-ils un remboursement ?"* → *"The question
looks like French; it was read with a small built-in word list as: 'why customers ask for a refund'. For the most
reliable answer, ask in English."* A threshold question, *"Which behaviours raise escalations by more than five
percentage points?"*, is checked against each estimate **and** its interval: *"For policy refusals [F2], the whole
confidence interval is beyond 5.0 percentage points; for the others the interval reaches below the threshold."*

---

## 9. Analysis and discussion

### 9.1 What the results show

**Adjusting for the conversation so far matters, and in a known direction.** The unadjusted comparison (B3) is wrong by
5.4 points on average and **exaggerates harmful behaviours by a factor of 1.5 to 6** (refusals, holds): customers who
are refused or put on hold are also the ones whose conversations were already going badly. The landmark design with
cross-fitted doubly robust adjustment brings the average error to 1.5 points and the 95% intervals cover the truth for
all 12 factors. A descriptive library of raw rates would have told a manager that holds are almost three times as
harmful for escalation as they are (Feder et al., 2022; Keith et al., 2020).

**The claim ladder behaves like a conservative filter that is right when it speaks.** Only 5 of 26 estimates reach L3,
and all five have the right sign with no interval on the wrong side of the truth. The four L2 estimates with an oracle
(refusal and hold effects on refunds and churn) have true effects of 1.0 to 4.2 points, small enough that the data cannot
confirm them; the system calls them warning signs or "no clear difference" instead of confirming them. Customer states
(frustration, confusion) can never reach L3. Answers say so in plain words ("Not a confirmed effect: it is a customer
state, not something the company can change").

**Residual confounding is small but visible, and the system reports it.** All three hold-request estimates sit above the
truth (by 1.7 to 2.4 points at 4,000 calls, and 0.7 to 2.3 at 20,000), the signature of a little remaining confounding by
how the customer is feeling. The negative controls stay at zero, so there is no sign of gross bias, and the E-value for the
hold finding is the lowest (1.70): the answer states that a modest hidden factor could explain it away. This is the
intended division of labour between estimate, check and wording (Lipsitch et al., 2010; VanderWeele & Ding, 2017).

**Evidence, effect and faithfulness really are different things.** Solution offers have the strongest protective effect
but only the 39th percentile of forecaster reliance, while refusals and holds are relied on heavily. If faithfulness had
been read as causal evidence, the most useful lever would have looked unimportant. Reporting it only as a model check, and
only when it passes, avoids that (DeYoung et al., 2020; Jacovi & Goldberg, 2020).

**An explicit state beats having none, but the comparison is structural.** Reading follow-ups with no state keeps the
event and industry in 30% of the later turns (8 of 27); the state-and-delta engine keeps them in all 27 of those turns
(and the full six-slot state in 40 of 40 turns), and routes all 28 turns correctly. This shows what the state adds; it does not say how a history-aware LLM rewriter would do, which is the
fairer opponent (Elgohary et al., 2019; Mao et al., 2023) and was not run.

**The gates are a guarantee, not a measured gain.** No sentence was removed because the template writer follows the
rules by construction, and all 372 quotes are exact. Their value appears when a free-text writer is used; the adversarial
unit tests show that they catch direct causal wording, digits typed outside placeholders, and altered quotes (Yu et al.,
2019; Gao et al., 2023). Retrieval alone cannot offer these guarantees: B0 does not correct a premise or flag an
unsupported attribute because it has no component that could.

### 9.2 Design corrections forced by evidence

Building the system against the oracle changed the method several times. Each change was triggered by a failing check, a
simulation with a known truth, or an API fact, and is now part of the method:

| What the plan said | What went wrong | What changed |
|---|---|---|
| Keep moments after another event, with earlier events as covariates | after a handoff the agent's "please hold" is part of the procedure, a different treatment (compound treatment; Hernán & VanderWeele, 2011); hold → refund and churn were biased by about 3 points (−2 against a true +1) | the primary analysis uses only moments with no earlier confirmatory event or handoff |
| Every covariate's standardised difference ≤ 0.1 | with about 100 covariates the largest one is noise (≈ 0.2 at 300 treated rows even with perfect weights); almost every factor was "insufficient" although the estimates were right | the gate is on the prognostic score (Stuart et al., 2013); per-covariate differences are reported, not gated |
| DSL corrects the outcome | the labeller also decides which moments are at risk | the correction is applied to the call-level numerator and denominator of the score (Egami et al., 2023, extended) |
| Untuned logistic nuisance models | overfitting left standardised differences up to 0.56 | regularisation tuned on train and pre-registered; much faster solver |
| Planted test: bias < 1 point, coverage 90–98% | point rules fail by Monte-Carlo noise alone; a correct estimator failed at 60 simulations | rules allow for Monte-Carlo error, bias is compared with the estimator's own standard error, 100 simulations per pair |
| Faithfulness: removing a span lowers the forecast | protective behaviours *raise* the forecast when removed | the measure is direction-aware |
| An L2 estimate is "associated with a higher chance" | an L2 interval including zero was worded as an association | L2 with an interval including zero is worded "no clear difference" |
| Notebook: collapse repeated words | "thank you you know for…" lost "you know"; a simulator check caught it | repeated words that start a discourse marker are not collapsed |

### 9.3 What the real data and real questions taught us

* **A labeller can fail in opposite directions.** The first escalation rule had precision 0.50 (agents talk *about*
  escalation) and the first churn rule recall 0.29 (customers hedge). Fixing precision cost some recall (escalation
  1.00 → 0.77); the gold correction is what keeps the downstream effects valid anyway. A labeller that looks excellent on
  synthetic data (F1 ≈ 1.00) can be mediocre on real speech.
* **A parser is only as good as the questions it has seen.** Reading the team's own 82 questions and 11 sessions exposed 12
  silent mis-readings. The most instructive was *"Why do customers who were refused a refund escalate?"*, which the parser
  answered about refunds; relative clauses are now read as conditions on the calls.
* **"Answer anything" is bounded by design.** The goal is not an answer to every question but a *useful and honest* one:
  an answer to the part the data supports, an explicit notice for the part it does not, and a clarifying question when the
  request is empty or ambiguous. Effects within sub-groups, individual counterfactuals, and per-agent results are refused
  with a reason (Tian & Pearl, 2000; VanderWeele, 2009).

---

## 10. Limitations

### 10.1 Causal identification

* **Observational data.** Estimates assume that the history before each moment (plus opening industry and brand) captures
  everything that drives both the behaviour and the event. Unobserved factors may remain: the customer's history and
  value, agent skill (agent names appear only in greetings), the policy in force, and issue severity beyond what is said.
  E-values and negative controls probe this; they cannot prove it, and the small consistent bias in the hold estimates
  (§9.1) shows it is not hypothetical.
* **Single-moment effects.** The estimand is the effect of doing a behaviour *now* at the moments where it happened (ATT).
  It is not the effect of a *policy* ("never refuse"), which needs methods for sustained strategies (§11), and it says
  nothing about interactions or mediation between behaviours; co-occurring behaviours "do not add up".
* **Structure the model does not see.** Repeated customers and agents (no customer or agent id) and template reuse beyond
  the template groups can create dependence the cluster-robust errors do not capture.
* **Measurement of the treatment.** Event-label error is corrected by the gold sample; error in the *behaviour* detectors
  is only checked (20-turn precision sheets), not corrected.

### 10.2 What the validation does and does not show

* **Synthetic validation checks the implementation, not real-world truth.** The simulator's mechanisms (a latent mood with
  observable cues) fit the estimator's assumptions, which is favourable. The synthetic labeller F1 of about 1.00 reflects
  regular simulated phrasing. Neither shows that real causal claims are right; that needs independent validation, ideally
  an A/B test of agent guidance.
* **Small real gold sample.** 200 calls (rare events have few) give wide intervals; the churn correction in particular
  is noisy, and a better labeller would tighten it.
* **The real-corpus Factor Library is not in this document.** It depends on the team's gold labels, precision sheets and
  a full run; without them no finding can reach L3, by design.

### 10.3 Measurement and scope of the data

* **Rules cover surface forms.** Escalation recall on the real gold sample is 0.77 and churn recall 0.56; the learned
  churn layer is built to help but cannot be measured until the corpus is rebuilt.
* **A fixed behaviour registry** (14 behaviours) cannot find mechanisms it does not contain (for example ownership of the
  problem or proactive explanation); the discovery path is optional and was not exercised.
* **Text only.** No audio, no timestamps inside calls, so durations, silences and tone cannot be analysed; call-level
  dates exist, which is what the before/after analysis uses.
* **English transcripts.** Questions can be asked in several languages, but the evidence is English dialogue.

### 10.4 Questions the system cannot answer well

The query set keeps four *known limitations* and scores them 0 of 4 as "answered as an ideal system would":

| Question | Ideal | What the system does |
|---|---|---|
| a question in a language outside the six (Swahili) | answer about escalations | without an LLM it asks the user to rephrase |
| *Does empathy reduce escalations only when the customer is already frustrated?* | an estimate within that sub-group | says effects inside sub-groups are not estimated and gives the overall estimate |
| *Why did escalations go up in hotel calls but not in airline calls?* | a contrast of two slices | answers for hotel calls; a comparison question gives both side by side |
| *If agents had offered a solution earlier in this call, would the customer still have escalated?* | the counterfactual for that call | says it cannot be estimated and gives the general estimate |

* **Impact evaluation** ties a change to a date, not to its cause; with strong autocorrelation the intervals are somewhat
  too narrow (§7.7); short series fall back to the simple comparison; the comparison series is only as good as the
  filter that defines it.
* **A rule-based question parser** covers what its word lists and rules cover. Its benchmark was written by the
  developers (an upper bound), and the LLM fallback, which would extend it, was not evaluated. Two or more conditions
  work only when they are coordinated ("and", "or").

### 10.5 Evaluation gaps and operational limits
* **Style.** Template answers are long and formulaic; 
* **Cost and discipline.** At the real corpus size the pipeline takes about an hour on four cores. Any change to labels or
  definitions after the plan is frozen needs a new pre-registration, or an amendment that caps results at L2.

---

## 11. Potential improvements

**Strengthen identification (§10.1).**

* Adjust better for the text itself: causally sufficient embeddings (Veitch et al., 2020) and noisy-proxy adjustment
  (Pryzant et al., 2021).
* Add more and better negative controls, for outcomes as well as exposures (Lipsitch et al., 2010).
* Use any quasi-random routing of calls to agents as a natural experiment, and validate the top levers with a controlled
  trial of agent guidance, the only way to confirm a real-world cause.
* Estimate **sustained strategies** with marginal structural models or g-computation (Keogh et al., 2023), and
  pre-register subgroup or heterogeneous effects (effect modification; VanderWeele, 2009) with honest inference, instead
  of the unrestricted subgroup search the design deliberately avoids.

**Improve measurement (§10.2–10.3).**

* Collect more gold labels with sampling that oversamples rare events, add a second annotator, and calibrate the churn
  semantic layer on them; extend the correction to treatment-measurement error (Kuroki & Pearl, 2014).
* Replace or complement cue lexicons by learned turn classifiers built through the verified LLM-sample route (Wan et al.,
  2024) and discover further behaviours (Zhong et al., 2023; Lam et al., 2024), each with human sign-off and a precision
  check, when the data rules permit.
* Add timestamps or audio features if they become available.

**Evaluate more honestly (§10.5).**

* Fill the human audit sheets and correct judge scores with prediction-powered inference (Angelopoulos et al., 2023;
  Saad-Falcon et al., 2024), using a judge from a different model family (Panickssery et al., 2024; Zheng et al., 2023).
* Run the LLM writer with and without the gates (B1), a history-aware LLM rewriter (B2), and a multi-turn study with
  human sessions (Katsis et al., 2025).
* Build a larger, judged set of real retrieval queries; use sentence embeddings and a reranker.

**Questions and answers.**

* Broaden and evaluate the language coverage, with an LLM-assisted normaliser that is validated against the vocabulary,
  and a code-switching test set (Khanuja et al., 2020).
* Add retrieval-oriented rewriting (Mao et al., 2023) and a learned routing policy (Roy et al., 2024) where rules fall short.
* Offer a short summary mode and an interactive view of the Factor Library.

**Impact evaluation.**

* Use autoregressive errors or small-sample corrections for the time-series intervals, longer histories, and, where
  several comparable units exist, a controlled design with synthetic controls (Abadie et al., 2010).

**Operations.** Turn the risk forecasters (AUC 0.87–0.93 on synthetic data) into a live early-warning tool (Zhang et al.,
2018; Chang & Danescu-Niculescu-Mizil, 2019), after validating them on real calls.

---

## 12. Conclusion

CREST answers *why* business events happen in conversations, and what changes under follow-up questions, by making
statistical identification, not language generation, the authority on what may be claimed. On a synthetic call centre
with known causes it recovered every true effect within its 95% interval (12 of 12), cut the error of an unadjusted
comparison by about 72%, confirmed five effects all with the right sign, kept every negative-control interval around zero, answered
all 81 scored questions as expected including premise corrections and refusals of unsupported parts, and preserved the
context of all 40 scored follow-up turns. On real data it exposed, and the team fixed, labeller and question-reading
failures that the synthetic data could not show. Its main limits are the ones every observational study has (unobserved
confounding), a labeller whose recall on real speech is still modest, and an evaluation that stops short of human and LLM
judges; the improvements above target exactly those.

**Reproducibility.** `python -m crest demo --out demo_out` regenerates every synthetic number on the same package
versions; the analysis plan is frozen with a SHA-256 hash; the test queries are locked by hash; 202 automated tests
check the implementation. The repository is private, and the dataset, which is copyrighted and for this hackathon only,
is never committed.

---

