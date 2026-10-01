# Loopholes found on the real questions and transcripts, and how they were closed (v3, v4)

This note records a review done after the first full run on the hackathon data. Three inputs were checked:

1. **The team's own query list** (`queries.csv`: 82 single questions and 11 follow-up sessions), run through the
   question parser and the answer writer.
2. **A sample of 112 real transcripts** shared by the team. It was used only on a local machine to find labeller errors;
   no transcript, quote or call id from it is stored in this repository. Example sentences below are paraphrases.
3. **The 200-call gold sample**, used once at the end to measure the labeller before and after the change. Its errors
   were not inspected, so it was not used for tuning.

Every fix keeps the frozen definitions (`definitions_snapshot()` hash unchanged), the claim ladder, the gates and the
pre-registration rules. Nothing below turns a pattern into a causal claim.

## 1 · Question understanding

| # | Loophole (what happened) | Fix | Where | Background |
|---|---|---|---|---|
| Q1 | Misspelled words (*custmers escalte*) found no event, so the system asked to clarify | Damerau–Levenshtein correction against a small domain vocabulary; one edit for short words, two for long ones; same first letter; common English words near the vocabulary are never changed (*quite* stays *quite*, *back* stays *back*); the answer says how each word was read | `crest/lexicon.py`, `QueryParser.parse` | Damerau, CACM 1964 [R1] |
| Q2 | Slang (*blow up*, *demand the boss*, *jump ship*, *take my business elsewhere*) was not recognised | phrase table rewrites slang to the vocabulary the parser knows; the answer says how it was read | `crest/lexicon.py` | — |
| Q3 | Non-English questions (Spanish; romanised Hindi such as *refund kyun maangte hain*) found no event | small word lists for Spanish and romanised Hindi, used only when the question looks like one of them; the answer shows the English reading and suggests asking in English; the optional LLM parser handles other languages | `crest/lexicon.py` | code-switching benchmarks [R2] |
| Q4 | A threshold on effects (*by more than five percentage points*) was silently ignored | the threshold is parsed (value, direction, more/less) and checked against each estimate **and** its confidence interval; a threshold on rates (*industries with more than 20% refunds*) marks the groups above it | `parse_threshold`, `PackBuilder.build`, `rank` | — |
| Q5 | *Did escalations increase after the new refund policy was introduced?* was read as "escalations and refunds in the same call" | change questions are recognised; without a date the system asks for it (and gives an example date from the data); with a date it compares the two periods with a 95% CI, shows the conversation patterns in each period, and warns that a before/after difference is not an effect of the policy | `find_change`, `PackBuilder.change`, session follow-up | interrupted time series [R3] |
| Q6 | *Why do customers who were refused a refund escalate?* was answered about refunds | relative and conditional clauses (*customers who …*, *after …*, *calls with …*) turn the first event into a condition: the answer covers escalations **in calls where a refund was refused**, compares them with calls where a refund came up but was not refused, gives the order of the two events, and explains the pattern in those calls | `condition_split`, `with_event` filter | — |
| Q7 | Brand names leaked into industries (*Northstar Airways calls in telecom calls* became airline + telecom) | brand spans are removed before any other slot is read | `QueryParser.parse` | — |
| Q8 | *What should the product team fix …* set the behaviour "solution offers" from the verb *fix* | verbs such as fix/solve/resolve are not behaviours in product and what-to-change questions | `QueryParser.parse` | — |
| Q9 | *quite* matched the churn word *quit* | the churn pattern now matches *quit, quits, quitting* only | `EVENT_PATTERNS` | — |
| Q10 | Questions about a behaviour alone (*Why do customers get frustrated?*) were sent back with "which event?" | a behaviour profile: how often it happens, what usually comes before its first occurrence (against the same point in calls without it), the customers' own words, one call step by step, and the event rates in calls with and without it; a follow-up such as *what about escalations?* becomes the effect question for that behaviour | `behaviour_profile` | precedents for looking before the turn [R4][R5] |
| Q11 | *Which premium customers escalate the most?* had no data behind it | there is still no tier field, but where customers **say** they are members, have a status or are long-time customers before the event point, that is shown as the nearest proxy, with a per-status breakdown when groups are large enough; clearly labelled as a proxy and as counts | `tier_proxy` | proxies measure with error [R6] |
| Q12 | *Which agent causes the most escalations?* got a generic notice | the notice now says why agents are not ranked (names appear only in greetings; per-agent counts mix skill with call mix) and points to the agent behaviours instead | `UNSUPPORTED_MESSAGES` | — |

## 2 · Answers without reasoning

Every answer type now carries a conversation rationale, not only *why* answers:

| Answer type | What was added |
|---|---|
| trend | the usual pattern before the event, and a caveat that weekly changes can come from the call mix |
| product / issues | what usually comes before the event and the customers' own words |
| shared (one behaviour, several events) | a short rationale for each event |
| event link (*do escalations lead to refunds?*) | what comes before the second event in calls with the first, the customers' words, and one call with both events step by step |
| effect of a behaviour, explain a factor | the behaviour's share before the event against the same point in calls without the event, and one call step by step; this now works for every behaviour, including hesitations and repeated questions |
| before/after a date, condition, threshold, proxy | see Q4–Q6, Q11 |

All of these are descriptive: they use the same placeholders, gates and claim ladder as before, and every quote is an
exact turn cited by its id.

## 3 · Event labeller (v2)

The review of the 112-call sample showed that the escalation and churn rules failed in opposite directions.

* **Escalation precision.** The agent-side rule fired on any *escalate/escalation* or *my supervisor*. Agents often talk
  about escalation as a topic (*quick acknowledgement helps reduce escalations*), deny it (*no escalation was needed*),
  offer it conditionally (*I can escalate this if necessary*), or route the issue to a department (*escalate this to
  housekeeping*). These are mentions, not escalations — the use–mention problem that also trips hate-speech and
  misinformation classifiers [R7], and the negation/hedge problem known from clinical text [R8][R9].
* **Churn recall.** The customer-side rule required firm forms (*cancel my account*, *switching to another provider*).
  Real customers hedge and name competitors: *I might just look elsewhere*, *I'd rather go with [competitor] if this
  doesn't change*, *this makes me question my loyalty*. Churn-intent detection in customer chat is known to need these
  soft forms [R10].

The new rules (`crest/events.py`), written from the definitions in `crest/definitions.py` and the gold conventions:

| Event | Counts | Does not count |
|---|---|---|
| Escalation (agent side) | a handoff to a named senior person or team (*escalate this to my supervisor / to management*, *let me get my manager*, *my supervisor will join*); an **offer** to escalate only when the customer accepts in the next turn or a handoff follows | escalation as a topic, negated or conditional mentions, routing to other departments, unprompted *I'll escalate this* with no senior person and no acceptance |
| Escalation (customer side) | the old request forms, plus *someone above you / someone in charge / talk to your superior* | — |
| Churn | the old firm forms, plus intent words (*considering, thinking about, might, would rather, going to, maybe*) followed by switch/move/go/stay/book/look/try **to a competitor or "elsewhere / another hotel / other options"**; *look elsewhere*; *question / rethink / reconsider my loyalty*; *why should I stick with you*; *won't book with you again* | prospects switching **to** the company (*switching from [competitor] to you*), negated forms (*I don't want to switch*), regret (*I almost switched*), comparisons without intent (*how do your rates compare to [competitor]*), questions about loyalty points or status |

**Results.** On the 112-call sample (by reading every changed call): escalations 19 → 6, all six consistent with the
definition; churn threats 10 → 26, the two removed ones being a prospect and a negated statement. On the 200-call gold
sample, measured once, unweighted:

| Event | Precision | Recall | F1 |
|---|---|---|---|
| Escalation | 0.50 → **1.00** | 1.00 → 0.77 | 0.67 → **0.87** |
| Refund | 0.95 → 0.95 | 0.88 → 0.88 | 0.92 → 0.92 |
| Churn | 0.74 → **0.82** | 0.29 → **0.58** | 0.42 → **0.68** |

The weighted F1 that `gold-ingest` reports will differ a little because it uses the inclusion probabilities. The DSL
correction [R11] keeps the effect estimates valid either way; a better labeller makes them tighter.

**Industry for calls without industry words in the opening.** In the sample, 46 of 112 hotel calls had no industry
word in the first four turns, so *in hotel calls* missed them. The brand named in the greeting is also an opening-only
field, so an unknown industry is now filled from the brand's own majority when that brand has at least 10 calls with a
known industry and at least 80% of them agree (`fill_domain_from_brand` in `crest/io.py`). The number of filled calls is
written to `checks/build_checks.json`.

## 4 · What the team has to rerun

* **Question parsing and answers** (sections 1, 2 and 7.5) work on an existing workspace straight away. Questions about
  retention risk and the self-reported status column need the v4 build.
* **The labeller, the retention-risk event, the account fields and the industry fill** change the event labels and the
  call table, so they take effect only after a rebuild. The gold sample, the gold labels and the precision sheets stay
  valid: retention risk is a secondary event and is not part of the gold sheet, and the gold sample is never redrawn
  once it exists.
* v4 also changes the labeller settings and adds an event to the frozen definitions, so the pre-registration hash
  changes. Two honest options:
  * **Same workspace:** `prereg --force` records an *amendment*; every result is then capped at L2, because the plan
    changed after the first confirmatory run.
  * **New workspace** (recommended for the presentation): copy `gold/sample.parquet`, `gold/gold_to_label.csv` and
    `precision/` into it, freeze a fresh pre-registration before its `confirm`, let it build a fresh v4 query set (the
    old set stays in the old workspace for comparison), and report the change as a documented deviation: the labeller
    was revised after errors were found in transcripts outside the gold sample; behaviours, estimator and thresholds did
    not change; the gold sample was used only to measure.

The exact commands are in the README (section 3, *Updating a finished run to v4*).

## 5 · Other things checked on the sample

* **Named speakers** (person names instead of Agent/Customer) appeared in 6 of 112 calls; the cleaning notebook's role
  classifier assigned every one of them correctly.
* **Swapped lines.** In 4 of 112 calls a line near the end carries the other speaker's label (mostly closings such as
  *have a great day*; once the agent's sign-off). These lines rarely carry a behaviour cue, so they were left as they are.
* **Domain metadata.** The `domain` field of the sample said *Insurance* for hotel calls. CREST never slices on that
  field: industries come from the opening turns (and now the greeting's brand), and the notebook's own domain check
  maps these intents to hospitality.

## 6 · Limits that remain

* **Languages.** Without an LLM, questions are read in English, Spanish, French, German, Portuguese, Italian and Hindi
  (romanised and Devanagari) through small phrase tables. Other languages (Swahili, for example) are read only when an
  LLM is configured; otherwise the system asks the user to rephrase. The parser benchmark (7.1) was written by the
  developer and is therefore optimistic.
* **Churn recall.** The rule part still misses threats with neither an intent word nor a competitor nor a clear
  disengagement phrase; rules-only recall on the gold sample is 0.56. The semantic layer (7.2) is designed for these
  cases, but it learns from the full corpus and can only be measured on the team's gold sample after the rebuild.
* **Tier and plan.** Without `account_attributes.csv` there is no verified tier, plan, segment or tenure; the answers say
  so and use the self-reported status only as a labelled proxy.
* **Before/after questions.** The interrupted time series ties a change to a date, not to a cause; anything else that
  changed at the same time shows up the same way. Short series fall back to the simple comparison.
* **Effects inside sub-groups** (*does empathy help only when the customer is already frustrated?*) are not estimated;
  the answer gives the overall estimate and says so.
* **One call's counterfactual** (*would this customer still have escalated if…*) cannot be estimated from data
  [R19]; the answer says so and describes the call and the general estimate instead.
* **Contrasts inside a why-question** (*why did escalations rise in hotel calls but not in airline calls?*) are answered
  for the first slice; ask a comparison question for the two slices side by side.

## 7 · The planned improvements, implemented (v4)

The first version of this note listed four improvements as future work. All four are now in the code, together with
the fixes found while testing them.

### 7.1 · Reading noisy and non-English questions

| Part | What it does | Where |
|---|---|---|
| Language identification | scores the question against stop-word and accent profiles for each supported language, the same idea as profile-based language identification [R12]; a strong code-mixing marker (*kyun*, *karne*, *dhamki*) wins over English words in Hinglish | `detect_language` in `crest/lexicon.py` |
| Domain terminology per language | phrase tables for Spanish, French, German, Portuguese, Italian and Hindi (romanised and Devanagari) that map business-event words, industries, behaviours and question words to English; German compounds such as *Hotelanrufen* are split by prefix | `LANG_TABLES` |
| Contextual spelling correction | Damerau edit distance [R1] to the domain vocabulary, but a word is never changed when it occurs at least three times in the corpus itself (`index/vocab.json`), so real words of this dataset are protected; ties go to the more frequent word, the noisy-channel idea [R13] | `correct_spelling` |
| Slang and common misspellings | phrase table (*blow up*, *the boss*, *jump ship*, *there money bak*) | `SLANG` |
| LLM fallback | only when an LLM is configured: if the rules find no event, or the question was translated by the word lists, the LLM rewrites the question in English and the rules read that; the answer shows the reading | `llm_normalize`, `Engine.read_question` |
| Benchmark | `python -m crest parser-bench`: clean, misspelled (keyboard-neighbour typos), multilingual and slang questions with the expected event, question type and filters; a dev split for building and a test split written separately and run once | `crest/parser_bench.py` |

Result of the single test run: all slots right for 51 of 51 test questions (95% Wilson interval 93–100%); dev 52 of 52
(five leave-verb questions were added to dev after the test run, when the gap in section 7.5 was found). The questions
were written by the developer, so this is an upper bound; the team should add its own.

### 7.2 · Churn: explicit intent and broader retention risk

The churn labeller is now a hybrid in the spirit of weak supervision [R14]:

1. **Rules** (unchanged definitions): explicit intent, plus clear **disengagement** (*I'm done with your company*, *you
   just lost a customer*, *never booking with you again*). Booking-only cancellations (*cancel my reservation, my plans
   changed*) and loyalty statements (*I always choose you over [competitor]*) are excluded.
2. **Semantic layer**: a classifier trained on the rule labels of the *train* split only (positives: rule churn turns;
   negatives: customer turns in calls without churn or competitor talk) scores the remaining customer turns that occur
   after a complaint, refusal or competitor mention and contain a leave-related word. Turns scoring at least 0.9 are
   added. With `sentence-transformers` installed it uses sentence embeddings [R15]; otherwise word and character
   TF-IDF. `build_checks.json` records how many turns it added.
3. **Retention risk** (`RISK`, a new secondary event) = churn intent **or** a competitor mention after the customer has
   complained or been refused **or** wavering (*second thoughts*, *last chance*, *losing my trust in you*). Its subtype
   says which. It answers *who is at risk of leaving?* without blurring the stricter churn event.

Results: on the synthetic demo the labeller now matches the simulator's truth on all 4,000 calls for every event
(F1 1.00 for escalation, refund and churn; the semantic layer added no turns there, because the rules already catch
every simulated threat). On the 200-call gold sample, rules only: escalation F1 0.87 (precision 1.00, recall 0.77),
refund 0.92, churn 0.67 (precision 0.82, recall 0.56). The semantic layer cannot be measured there yet (see section 6).
On the shared sample: churn in 29 calls, retention risk in 56; the semantic layer added one turn, which was correct.

### 7.3 · Customer tier, plan, segment and tenure

* If `cleaned_data/account_attributes.csv` exists (columns `transcript_id` and any of `tier`, `plan`, `segment`,
  `tenure_months`), it is joined to the calls. Questions can then filter (*premium tier*, *new customers*), rank
  (*which tier escalates most?*) and compare by these fields. Unknown values stay unknown. These must be account facts
  known before the call; a column that records an outcome (a churn flag, a cancellation date) must not be added, because
  filtering on it would leak the outcome into the answer.
* Without the file, the answer says which field is missing (*customer tier*, *plan or segment*, *account age*).
* What customers **say** about their status is a separate, labelled variable (`self_status`, with the turn where it is
  first said). It is used for *customers who say they are gold members* and as the nearest proxy for tier, and is
  always shown as *self-reported, not a verified tier*.

### 7.4 · Before/after questions: interrupted time series

For *did X change after <date>?* the answer gives, in this order:

1. the simple comparison of the two periods with a 95% interval;
2. a **segmented regression** of the event share per period [R3][R16]: the trend before the date, the **level shift**
   at the date and the **change in slope**, each with a 95% interval. The period length is chosen from the data (week,
   day, six hours or hour) so that each side has at least six periods with enough calls. The model adds time-of-day or
   day-of-week terms when the series is long enough, weights periods by their number of calls, and uses Newey–West
   standard errors [R13a], never narrower than the classical ones (in simulations this kept 95% intervals at 92–97%
   coverage, where Newey–West alone gave 83–87% on short series);
3. **placebo dates**: the same model fitted at up to 20 made-up dates before the real one, reporting how many give a
   level shift at least as large [R17];
4. a **comparison series**: when the question has a filter (an industry, a brand, a condition), the same model on the
   other calls, and the difference between the two level shifts;
5. the conversation patterns in each period, and the caveat that a change is tied to the date, not to its cause.

### 7.5 · Other loopholes closed while testing v4

| Loophole | Fix |
|---|---|
| *Why do customers who were refused a refund **and** threatened to cancel escalate?* was answered about churn | several conditions joined by *and/or* all become conditions; the last event is the subject |
| *Why did call <id> escalate?* ignored the id; *What happened in call <id>?* asked for clarification | call ids (full ids, unique prefixes, and *that call / the third example* after an answer with quotes) open a step-by-step account of that call: its events in order, the customer's problem, the behaviours in the turns before the event with quotes, how common those moments are across calls, and the confirmed factors among them, with the caveat that general estimates do not prove why one call went the way it did [R19] |
| *Which behaviours do not affect escalations?* got the generic answer | lists the behaviours whose interval includes zero, with the warning that this is not proof of no effect [R18] |
| *Does empathy help only when the customer is already frustrated?* was answered as a general question without saying so | an *effect modification* notice [R20]; the overall estimate follows |
| *Did escalations go up in the second week?* was read as a why-question | direction words (*go up, rise, drop, change*) with an event make a trend question |
| *Why do customers on the premium plan…* and *Do new customers…* were silently answered for everyone | notices for missing plan/segment and account-age fields (or a filter when `account_attributes.csv` has them) |
| *amenazan con irse*, *menacent de partir*, *drohen zu gehen*, *chhodne ki dhamki* found no event | leave verbs added for every supported language (*partir en vacances* is excluded) |
| *What drives churn threats in calls where a supervisor joined?* became an examples request | *calls where* means examples only when the question asks to show or list calls |
| *give me an overview* as a follow-up asked for clarification | overview and help follow-ups switch the question type |
| a hand-edited or old session file could crash a follow-up | the saved state is validated; anything unusable starts a fresh conversation with a notice |

## References (checked on 1 Oct 2026)

* **[R1]** F. J. Damerau. *A technique for computer detection and correction of spelling errors.* Communications of the
  ACM 7(3), 1964. <https://www.semanticscholar.org/paper/d2767a9010ae11b10be2589f4f433174e7aab6e5>
* **[R2]** S. Khanuja, S. Dandapat, A. Srinivasan, S. Sitaram, M. Choudhury. *GLUECoS: An Evaluation Benchmark for
  Code-Switched NLP.* ACL 2020. <https://aclanthology.org/2020.acl-main.329/>
* **[R3]** J. Lopez Bernal, S. Cummins, A. Gasparrini. *Interrupted time series regression for the evaluation of public
  health interventions: a tutorial.* International Journal of Epidemiology 46(1), 2017.
  <https://pubmed.ncbi.nlm.nih.gov/27283160/>
* **[R4]** J. Zhang et al. *Conversations Gone Awry: Detecting Early Signs of Conversational Failure.* ACL 2018.
  <https://aclanthology.org/P18-1125/>
* **[R5]** J. P. Chang, C. Danescu-Niculescu-Mizil. *Trouble on the Horizon: Forecasting the Derailment of Online
  Conversations as they Develop.* EMNLP-IJCNLP 2019. <https://aclanthology.org/D19-1481/>
* **[R6]** M. Kuroki, J. Pearl. *Measurement bias and effect restoration in causal inference.* Biometrika 101, 2014.
  <https://ftp.cs.ucla.edu/pub/stat_ser/r366-reprint.pdf>
* **[R7]** K. Gligorić, M. Cheng, L. Zheng, E. Durmus, D. Jurafsky. *NLP Systems That Can't Tell Use from Mention Censor
  Counterspeech, but Teaching the Distinction Helps.* NAACL 2024. <https://aclanthology.org/2024.naacl-long.331/>
* **[R8]** W. W. Chapman, W. Bridewell, P. Hanbury, G. F. Cooper, B. G. Buchanan. *A simple algorithm for identifying
  negated findings and diseases in discharge summaries* (NegEx). Journal of Biomedical Informatics 34(5), 2001.
  <https://doi.org/10.1006/jbin.2001.1029>
* **[R9]** R. Farkas, V. Vincze, G. Móra, J. Csirik, G. Szarvas. *The CoNLL-2010 Shared Task: Learning to Detect Hedges and
  their Scope in Natural Language Text.* CoNLL 2010. <https://aclanthology.org/W10-3001/>
* **[R10]** C. Abbet, M. M'hamdi, A. Giannakopoulos, R. West, A. Hossmann, M. Baeriswyl, C. Musat. *Churn Intent Detection in
  Multilingual Chatbot Conversations and Social Media.* CoNLL 2018. <https://aclanthology.org/K18-1016/>
* **[R11]** N. Egami, M. Hinck, B. M. Stewart, H. Wei. *Using Imperfect Surrogates for Downstream Inference:
  Design-based Supervised Learning for Social Science Applications of Large Language Models.* NeurIPS 2023.
  <https://proceedings.neurips.cc/paper_files/paper/2023/file/d862f7f5445255090de13b825b880d59-Paper-Conference.pdf>
* **[R12]** W. B. Cavnar, J. M. Trenkle. *N-Gram-Based Text Categorization.* Proceedings of SDAIR-94, 3rd Annual
  Symposium on Document Analysis and Information Retrieval, 1994, pp. 161–175.
* **[R13]** E. Brill, R. C. Moore. *An Improved Error Model for Noisy Channel Spelling Correction.* ACL 2000.
  <https://aclanthology.org/P00-1037/>
* **[R13a]** W. K. Newey, K. D. West. *A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation
  Consistent Covariance Matrix.* Econometrica 55(3), 1987, 703–708. <https://doi.org/10.2307/1913610>
* **[R14]** A. Ratner, S. H. Bach, H. Ehrenberg, J. Fries, S. Wu, C. Ré. *Snorkel: Rapid Training Data Creation with Weak
  Supervision.* PVLDB 11(3), 2017, 269–282. <https://www.vldb.org/pvldb/vol11/p269-ratner.pdf>
* **[R15]** N. Reimers, I. Gurevych. *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* EMNLP-IJCNLP 2019.
  <https://aclanthology.org/D19-1410/>
* **[R16]** A. K. Wagner, S. B. Soumerai, F. Zhang, D. Ross-Degnan. *Segmented regression analysis of interrupted time
  series studies in medication use research.* Journal of Clinical Pharmacy and Therapeutics 27(4), 2002, 299–309.
  <https://doi.org/10.1046/j.1365-2710.2002.00430.x>
* **[R17]** A. Abadie, A. Diamond, J. Hainmueller. *Synthetic Control Methods for Comparative Case Studies: Estimating the
  Effect of California's Tobacco Control Program.* JASA 105(490), 2010, 493–505 (placebo tests in time and space).
  <https://doi.org/10.1198/jasa.2009.ap08746>
* **[R18]** D. G. Altman, J. M. Bland. *Absence of evidence is not evidence of absence.* BMJ 311, 1995, 485.
  <https://pubmed.ncbi.nlm.nih.gov/14988165/>
* **[R19]** J. Tian, J. Pearl. *Probabilities of causation: Bounds and identification.* Annals of Mathematics and
  Artificial Intelligence 28, 2000, 287–313. <https://link.springer.com/article/10.1023/A:1018912507879>
* **[R20]** T. J. VanderWeele. *On the distinction between interaction and effect modification.* Epidemiology 20(6),
  2009, 863–871.
* Related, for the rationale design: S. Poria et al., *Recognizing Emotion Cause in Conversations* (RECCON),
  Cognitive Computation 13, 2021 — causes of an emotion are looked for in the turns before it, as the rationale does for
  business events.
