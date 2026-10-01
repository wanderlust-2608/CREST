# Literature review & research-grounded design

**Problem:** *Causal Rationale Extraction and Synthesis from Conversational Data on Business Events*,
with Task 1 (query → evidence-based causal explanation) and Task 2 (contextual follow-ups).

This document gives:

1. the inclusion criteria;
2. a map from every requirement in the problem statement to the research that addresses it;
3. an annotated bibliography of 50 peer-reviewed works and maintained repositories, each with what it contributes to *our* system;
4. a proposed architecture built from them, with the novel parts marked;
5. an evaluation-metric plan;
6. a plan for the 50–100-query dataset.

The data-cleaning decisions that already use this literature are in [`DATA_CLEANING.md`](DATA_CLEANING.md).

---

## 0 · Inclusion criteria

* **Peer-reviewed works only**, from top venues and journals:
  * Journals: *TACL*, *Computational Linguistics*, *Cognition*, *Language*, *Journal of Phonetics*, *Science Advances*,
    *The Econometrics Journal*, *IEEE/ACM TASLP*, *IEEE TAFFC*, *IEEE Trans. Multimedia*, *ACM TKDD*, *Communications of the ACM*,
    *Expert Systems with Applications*, *Information & Management*, *Cognitive Computation*, *Requirements Engineering*, *TMLR*.
  * Conferences: ACL, EMNLP, NAACL, EACL, NeurIPS, ICLR, KDD, SIGIR, CIKM, CHI, UAI, SIGDIAL, IEEE RE, Odyssey (ISCA).
  * In NLP the flagship venues are conferences with full peer review (ACL Anthology), so they are included alongside journals.
* **Two preprints are included only for their widely used, maintained software:** GraphRAG and DoWhy. They are marked *(preprint + software)*.
* **Every citation below was checked** for title, authors, venue and year against the publisher page, the ACL Anthology, or proceedings.

---

## 1 · Problem statement → research map

| Requirement in the problem statement | Research area | Key works (numbers refer to §2) |
|---|---|---|
| "surface the specific dialogue **spans** that most likely contributed to the event" | causal span / rationale extraction in dialogue | RECCON [D1], MECPE [D2], ERASER [D3], faithfulness [D4] |
| "infer **causal** relationships … rather than simple correlations" | causal inference with text | Feder et al. [E1], Keith et al. [E2], Egami et al. [E3], TextCause [E4], Veitch et al. [E5], DML [E6], DoWhy [E7], Corr2Cause [E8], Kıcıman et al. [E9] |
| "model **conversational dynamics** … temporal patterns that precede churn" | conversation forecasting, dialogue acts, satisfaction dynamics | Conversations Gone Awry [A1], CRAFT [A2], ConvoKit [A3], politeness [A4], ASAP (Hawkes) [A5], dialogue acts [A6] |
| "customer **hesitations**, **silences**, **repeated queries**, **misunderstandings**" | spoken-interaction phenomena | turn-taking [B1], uh/um [B2], pauses/gaps [B3], disfluency detection [B4] |
| speaker roles (Agent / Customer / Supervisor) in noisy transcripts | role recognition | Salamin & Vinciarelli [B5], Flemotomos et al. [B6] |
| **escalations, refunds, churn** in contact centres | contact-centre analytics | Mishne et al. [C1], Park & Gates [C2], Ando et al. [C3], Montgomery & Damian [C4], Coussement & Van den Poel [C5], ABCD [C6], USS [C7] |
| "**analytical querying** across the call corpus … recurring patterns and summary insights" | corpus-level hypothesis/pattern discovery, global sensemaking | D5 [F1], NL-parameterised models [F2], TnT-LLM [F3], LLooM [F4], GraphRAG [F5] |
| "responses … with **evidential references**" | attributed/grounded generation and its evaluation | ALCE [G1], RAGAS [G2], AlignScore [G3], Lost in the Middle [G4], RRF [G5], LLM-as-judge [G6] |
| Task 2: "**follow-up questions** contextually linked to prior analyses" | conversational QA and query rewriting | CANARD [H1], QReCC [H2], LLM4CS [H3] |
| "dataset of simulated user queries … LLM-generated, human-reviewed, LLM-as-judge" | synthetic data generation and judging | Self-Instruct [I1], LLM-as-judge [G6] |
| data cleaning, leakage, duplicates, documentation | data quality | leakage [I2], deduplication [I3], datasheets [I4] |

---

## 2 · Annotated bibliography

Format: **reference**, venue and link, then **what it offers** and **→ use in our system**.

### A. Conversational dynamics & early warning

* **[A1]** J. Zhang, J. P. Chang, C. Danescu-Niculescu-Mizil, L. Dixon, Y. Hua, D. Taraborelli, N. Thain. *Conversations Gone Awry: Detecting Early Signs of Conversational Failure.* **ACL 2018**. <https://aclanthology.org/P18-1125/>
  * **Offers:** predicts, from the very start of a conversation, whether it will later derail. Pragmatic devices in the first exchange (politeness strategies, rhetorical prompts) carry predictive signal.
  * **→ Use:** frames escalation as an *early-warning* problem. We anchor every event to the turn where it first appears (`escalation_turn_id`) and study the turns *before* it.
* **[A2]** J. P. Chang, C. Danescu-Niculescu-Mizil. *Trouble on the Horizon: Forecasting the Derailment of Online Conversations as they Develop.* **EMNLP-IJCNLP 2019**. <https://aclanthology.org/D19-1481/>. Code: [jpwchang/CRAFT](https://github.com/jpwchang/CRAFT)
  * **Offers:** CRAFT, a hierarchical recurrent encoder pre-trained on unlabelled conversations plus a supervised forecasting head. It updates the derailment probability after every utterance, giving early warning.
  * **→ Use:** a turn-by-turn escalation-risk model. **Turns where the forecast risk jumps are natural candidate rationale spans.**
* **[A3]** J. P. Chang, C. Chiam, L. Fu, A. Wang, J. Zhang, C. Danescu-Niculescu-Mizil. *ConvoKit: A Toolkit for the Analysis of Conversations.* **SIGDIAL 2020**. <https://aclanthology.org/2020.sigdial-1.8/>. Code: [CornellNLP/ConvoKit](https://github.com/CornellNLP/ConvoKit)
  * **Offers:** a unified corpus / utterance / speaker data model and feature transformers (politeness strategies, prompt types …).
  * **→ Use:** our turn table maps 1:1 to ConvoKit utterances, so its feature extractors can be reused directly.
* **[A4]** C. Danescu-Niculescu-Mizil, M. Sudhof, D. Jurafsky, J. Leskovec, C. Potts. *A computational approach to politeness with application to social factors.* **ACL 2013**. <https://aclanthology.org/P13-1025/>
  * **Offers:** operationalises politeness theory (indirection, deference, hedging, apologising, gratitude) as lexical/syntactic features.
  * **→ Use:** motivates the agent-response cues (apology, empathy, hedges) as candidate causes of de-/escalation.
* **[A5]** F. Ye, Z. Hu, E. Yilmaz. *Modeling User Satisfaction Dynamics in Dialogue via Hawkes Process.* **ACL 2023**. <https://aclanthology.org/2023.acl-long.494/>. Code: [smartyfh/ASAP](https://github.com/smartyfh/ASAP)
  * **Offers:** treats turn-level satisfaction as an event sequence with self-exciting (Hawkes) dynamics.
  * **→ Use:** models how dissatisfaction *accumulates* over turns before an escalation (temporal patterns).
* **[A6]** A. Stolcke et al. *Dialogue act modeling for automatic tagging and recognition of conversational speech.* **Computational Linguistics 26(3), 2000**. <https://aclanthology.org/J00-3003/>
  * **Offers:** dialogue acts (statement, question, backchannel, agreement, apology …) modelled with an HMM over act sequences.
  * **→ Use:** we tag `is_question` / `is_backchannel`. Dialogue-act n-grams are a compact way to describe "branching dialogue flows".

### B. Spoken-interaction phenomena and speaker roles (why hesitations and silences are *kept*)

* **[B1]** H. Sacks, E. A. Schegloff, G. Jefferson. *A simplest systematics for the organization of turn-taking for conversation.* **Language 50(4), 1974**.
  * **Offers:** the turn as the basic unit of talk.
  * **→ Use:** turns stay atomic and citeable; consecutive same-speaker turns are linked with `block_id` instead of being merged.
* **[B2]** H. H. Clark, J. E. Fox Tree. *Using uh and um in spontaneous speaking.* **Cognition 84, 2002**. <https://pubmed.ncbi.nlm.nih.gov/12062148/>
  * **Offers:** *uh/um* announce minor or major delays, i.e. searching for words, planning, or holding or ceding the floor.
  * **→ Use:** filled pauses are *hesitation signal*. They are counted before being removed from `text_clean`.
* **[B3]** M. Heldner, J. Edlund. *Pauses, gaps and overlaps in conversations.* **Journal of Phonetics 38, 2010**. doi:10.1016/j.wocn.2010.08.002
  * **Offers:** the structure of silences in turn-taking.
  * **→ Use:** the corpus has no timestamps, so silences are approximated by hold phrases and PAUSE/HOLD markers.
* **[B4]** P. Jamshid Lou, M. Johnson. *Improving Disfluency Detection by Self-Training a Self-Attentive Model.* **ACL 2020**. <https://aclanthology.org/2020.acl-main.346/>. Code: [pariajm/joint-disfluency-detector-and-parser](https://github.com/pariajm/joint-disfluency-detector-and-parser)
  * **Offers:** a state-of-the-art disfluency detector (repairs, restarts).
  * **→ Use:** upgrade path for our rule-based `text_clean` and `n_repetitions`.
* **[B5]** H. Salamin, A. Vinciarelli. *Automatic Role Recognition in Multiparty Conversations: An Approach Based on Turn Organization, Prosody, and Conditional Random Fields.* **IEEE Trans. Multimedia 14(2), 2012**. <https://ieeexplore.ieee.org/document/6062417/>
  * **Offers:** role is recoverable from behaviour.
  * **→ Use:** justifies the classifier that infers Agent/Customer for 1,332 name-labelled calls.
* **[B6]** N. Flemotomos, P. Georgiou, S. Narayanan. *Linguistically Aided Speaker Diarization Using Speaker Role Information.* **Odyssey 2020 (ISCA)**. <https://www.isca-archive.org/odyssey_2020/flemotomos20_odyssey.pdf>
  * **Offers:** role-specific language models separate speakers.
  * **→ Use:** same principle as our TF-IDF role classifier, which is validated by hiding labels on held-out calls.

### C. Contact-centre analytics & business outcomes

* **[C1]** G. Mishne, D. Carmel, R. Hoory, A. Roytman, A. Soffer. *Automatic analysis of call-center conversations.* **CIKM 2005**. <https://dl.acm.org/doi/10.1145/1099554.1099684>
  * **Offers:** scores the *domain-specific importance of conversation fragments* by divergence of corpus statistics, combined with IR tools.
  * **→ Use:** contrastive fragment scoring, e.g. pre-escalation windows vs matched controls.
* **[C2]** Y. Park, S. C. Gates. *Towards real-time measurement of customer satisfaction using automatically generated call transcripts.* **CIKM 2009**. <https://research.ibm.com/publications/towards-real-time-measurement-of-customer-satisfaction-using-automatically-generated-call-transcripts>
  * **Offers:** satisfaction predicted from linguistic and behavioural transcript features.
  * **→ Use:** baseline feature families and a strong "simple model" comparison.
* **[C3]** A. Ando et al. *Customer Satisfaction Estimation in Contact Center Calls Based on a Hierarchical Multi-Task Model.* **IEEE/ACM TASLP, 2020**. <https://ieeexplore.ieee.org/document/8960433/>
  * **Offers:** joint turn-level and call-level estimation.
  * **→ Use:** turn-level scores feeding a call-level outcome is exactly the structure of *span → event* attribution.
* **[C4]** L. Montgomery, D. Damian. *What Do Support Analysts Know About Their Customers? On the Study and Prediction of Support Ticket Escalations in Large Software Organizations.* **IEEE RE 2017**. Follow-up: Montgomery, Damian, Bulmer, Quader, *Customer support ticket escalation prediction using feature engineering*, **Requirements Engineering (Springer)**, <https://link.springer.com/article/10.1007/s00766-018-0292-3>
  * **Offers:** escalation predictors from support interactions.
  * **→ Use:** repeat contacts and persistence cues (`cue_repeat_contact`, `cue_issue_persistence`).
* **[C5]** K. Coussement, D. Van den Poel. *Improving customer attrition prediction by integrating emotions from client/company interaction emails and evaluating multiple classifiers.* **Expert Systems with Applications 36(3), 2009**. Also: *Integrating the voice of customers through call center emails into a decision support system for churn prediction*, **Information & Management 45(3), 2008**.
  * **Offers:** customer emotion and "voice of customer" text improves churn prediction.
  * **→ Use:** motivates `cue_negative_emotion` and `cue_churn_intent`.
* **[C6]** D. Chen, H. Chen, Y. Yang, A. Lin, Z. Yu. *Action-Based Conversations Dataset (ABCD).* **NAACL 2021**. <https://aclanthology.org/2021.naacl-main.239/>. Code: [asappresearch/abcd](https://github.com/asappresearch/abcd)
  * **Offers:** 10k+ customer-service dialogues whose agent actions are constrained by company *policies*.
  * **→ Use:** motivates "refusal citing policy" as a causal factor (`cue_refusal`). Also an external test bed.
* **[C7]** W. Sun, S. Zhang, K. Balog, Z. Ren, P. Ren, Z. Chen, M. de Rijke. *Simulating User Satisfaction for the Evaluation of Task-oriented Dialogue Systems.* **SIGIR 2021**. <https://dl.acm.org/doi/10.1145/3404835.3463241>. Code: [sunnweiwei/user-satisfaction-simulation](https://github.com/sunnweiwei/user-satisfaction-simulation)
  * **Offers:** USS, 6,800 dialogues (including e-commerce) with turn-level 5-point satisfaction labels.
  * **→ Use:** external labels to pre-train or validate a frustration/satisfaction model.

### D. Causal spans & rationales

* **[D1]** S. Poria et al. *Recognizing Emotion Cause in Conversations.* **Cognitive Computation, 2021**. <https://link.springer.com/article/10.1007/s12559-021-09925-7>. Code: [declare-lab/RECCON](https://github.com/declare-lab/RECCON)
  * **Offers:** two sub-tasks. *Causal Span Extraction*: given a target utterance, find the span that caused it. *Causal Emotion Entailment*: classify whether an utterance is a cause.
  * **→ Use:** replace "emotion" with "business event". Given the event turn, extract or classify cause spans in the preceding turns.
* **[D2]** F. Wang, Z. Ding, R. Xia, Z. Li, J. Yu. *Multimodal Emotion-Cause Pair Extraction in Conversations.* **IEEE Trans. Affective Computing 14(3), 2023**. Code: [NUSTM/MECPE](https://github.com/NUSTM/MECPE)
  * **Offers:** joint extraction of (effect, cause) utterance pairs.
  * **→ Use:** the output format for evidence, i.e. `(event_turn_uid, cause_turn_uid, factor)` pairs.
* **[D3]** J. DeYoung et al. *ERASER: A Benchmark to Evaluate Rationalized NLP Models.* **ACL 2020**. <https://aclanthology.org/2020.acl-main.408/>
  * **Offers:** agreement metrics with human rationales (token F1, IOU-F1, AUPRC) and faithfulness metrics. **Comprehensiveness** is the drop in prediction when the rationale is removed; **sufficiency** is the prediction from the rationale alone.
  * **→ Use:** faithfulness metrics for the evidence forecaster (METHODOLOGY v2, Step 5). Comprehensiveness shows what a *model* relies on; it is never presented as proof of a real-world cause, and keep-only sufficiency is dropped because such inputs are out-of-distribution (Hase et al., NeurIPS 2021).
* **[D4]** A. Jacovi, Y. Goldberg. *Towards Faithfully Interpretable NLP Systems: How Should We Define and Evaluate Faithfulness?* **ACL 2020**. <https://aclanthology.org/2020.acl-main.386/>
  * **Offers:** separates plausibility from faithfulness, and argues for *graded* faithfulness.
  * **→ Use:** report both human-plausibility and counterfactual faithfulness of our explanations.

### E. Causal inference with text (from correlation to causal claims)

* **[E1]** A. Feder et al. *Causal Inference in Natural Language Processing: Estimation, Prediction, Interpretation and Beyond.* **TACL 10, 2022**. <https://aclanthology.org/2022.tacl-1.66/>
  * **Offers:** a unifying survey: text as treatment, outcome or confounder.
  * **→ Use:** conversational behaviour is the *treatment*, the business event is the *outcome*, and intent, domain and issue severity are *confounders*.
* **[E2]** K. A. Keith, D. Jensen, B. O'Connor. *Text and Causal Inference: A Review of Using Text to Remove Confounding from Causal Estimates.* **ACL 2020**. <https://aclanthology.org/2020.acl-main.474/>
  * **Offers:** how to adjust for confounding measured from text, with data-processing and evaluation guidance.
  * **→ Use:** confounder adjustment design.
* **[E3]** N. Egami, C. J. Fong, J. Grimmer, M. E. Roberts, B. M. Stewart. *How to make causal inferences using texts.* **Science Advances 8, 2022**. <https://www.science.org/doi/10.1126/sciadv.abg2652>
  * **Offers:** **split-sample workflow**. Discover text measures on one split and estimate effects on another, avoiding identification and overfitting problems.
  * **→ Use:** implemented as the deterministic `train` / `dev` / `test` split in `cleaned_data`.
* **[E4]** R. Pryzant, D. Card, D. Jurafsky, V. Veitch, D. Sridhar. *Causal Effects of Linguistic Properties.* **NAACL 2021**. <https://aclanthology.org/2021.naacl-main.323/>. Code: [rpryzant/causal-text](https://github.com/rpryzant/causal-text)
  * **Offers:** TextCause estimates the effect of a linguistic property from noisy proxies (lexicons) plus BERT adjustment. Case study: complaint politeness → response time.
  * **→ Use:** our lexicon cues are exactly such noisy proxies, e.g. the effect of agent apology on escalation.
* **[E5]** V. Veitch, D. Sridhar, D. M. Blei. *Adapting Text Embeddings for Causal Inference.* **UAI 2020 (PMLR 124)**. <https://proceedings.mlr.press/v124/veitch20a.html>
  * **Offers:** causally sufficient embeddings for adjusting for confounding aspects of text.
  * **→ Use:** adjust for issue content and severity when estimating factor effects.
* **[E6]** V. Chernozhukov, D. Chetverikov, M. Demirer, E. Duflo, C. Hansen, W. Newey, J. Robins. *Double/debiased machine learning for treatment and structural parameters.* **The Econometrics Journal 21(1), 2018**. <https://doi.org/10.1111/ectj.12097>
  * **Offers:** valid confidence intervals for a treatment effect while using ML for high-dimensional nuisance functions (cross-fitting).
  * **→ Use:** effect sizes with CIs for each discovered factor.
* **[E7]** A. Sharma, E. Kıcıman. *DoWhy: An End-to-End Library for Causal Inference.* arXiv:2011.04216 *(preprint + software)*. Code: [py-why/dowhy](https://github.com/py-why/dowhy)
  * **Offers:** model → identify → estimate → **refute** (placebo treatment, random common cause, subset tests). Interoperates with EconML.
  * **→ Use:** robustness checks before a factor is reported as causal.
* **[E8]** Z. Jin et al. *Can Large Language Models Infer Causation from Correlation?* **ICLR 2024**. <https://openreview.net/forum?id=vqIH0ObdqL>. Code: [causalNLP/corr2cause](https://github.com/causalNLP/corr2cause)
  * **Offers:** LLMs perform close to random on pure causal inference from correlational statements.
  * **→ Use:** **design constraint.** The LLM must not "decide" causality; statistics are computed outside the LLM and only *verbalised* by it.
* **[E9]** E. Kıcıman, R. Ness, A. Sharma, C. Tan. *Causal Reasoning and Large Language Models: Opening a New Frontier for Causality.* **TMLR 2024**. <https://arxiv.org/abs/2305.00050>. Code: [py-why/pywhy-llm](https://github.com/py-why/pywhy-llm)
  * **Offers:** LLMs are strong at *knowledge-based* causal tasks, such as proposing causal graphs and background context.
  * **→ Use:** the LLM *proposes* hypotheses and confounders, and the data *tests* them.

### F. Corpus-level pattern discovery ("what patterns lead to escalations in billing?")

* **[F1]** R. Zhong, P. Zhang, S. Li, J. Ahn, D. Klein, J. Steinhardt. *Goal Driven Discovery of Distributional Differences via Language Descriptions* (D5). **NeurIPS 2023**. <https://proceedings.neurips.cc/paper_files/paper/2023/hash/7e810b2c75d69be186cadd2fe3febeab-Abstract-Conference.html>. Code: [ruiqi-zhong/D5](https://github.com/ruiqi-zhong/D5)
  * **Offers:** given a goal and two corpora, an LLM proposes natural-language differences, which are validated. Metrics: validity, relevance, novelty, significance.
  * **→ Use:** escalated vs matched non-escalated pre-event windows → candidate causal factors in plain English.
* **[F2]** R. Zhong, H. Wang, D. Klein, J. Steinhardt. *Explaining Datasets in Words: Statistical Models with Natural Language Parameters.* **NeurIPS 2024**. Code: [ruiqi-zhong/nlparam](https://github.com/ruiqi-zhong/nlparam)
  * **Offers:** clustering, time-series and classification models whose parameters are natural-language predicates. Applied to taxonomising chat dialogues.
  * **→ Use:** interpretable factor models over calls.
* **[F3]** M. Wan et al. *TnT-LLM: Text Mining at Scale with Large Language Models.* **KDD 2024**. <https://dl.acm.org/doi/10.1145/3637528.3671647>
  * **Offers:** an LLM builds a label taxonomy, then an LLM labels a sample to train *lightweight* classifiers that scale to the full corpus.
  * **→ Use:** the event/factor labelling strategy for 19.6k calls at low cost.
* **[F4]** M. S. Lam, J. Teoh, J. Landay, J. Heer, M. S. Bernstein. *Concept Induction: Analyzing Unstructured Text with High-Level Concepts Using LLooM.* **CHI 2024**. <https://dl.acm.org/doi/10.1145/3613904.3642830>. Code: [michelle123lam/lloom](https://github.com/michelle123lam/lloom)
  * **Offers:** high-level concepts with explicit natural-language inclusion criteria, scored back on the data.
  * **→ Use:** auditable pattern definitions.
* **[F5]** D. Edge et al. *From Local to Global: A Graph RAG Approach to Query-Focused Summarization.* arXiv:2404.16130 *(preprint + software, Microsoft Research)*. Code: [microsoft/graphrag](https://github.com/microsoft/graphrag)
  * **Offers:** vector RAG fails on *global* sensemaking questions. Community summaries plus map-reduce answering improve comprehensiveness and diversity.
  * **→ Use:** corpus-level questions are answered from factor/cluster summaries, not from a handful of retrieved turns.

### G. Grounded generation, retrieval & its evaluation

* **[G1]** T. Gao, H. Yen, J. Yu, D. Chen. *Enabling Large Language Models to Generate Text with Citations* (ALCE). **EMNLP 2023**. <https://aclanthology.org/2023.emnlp-main.398/>. Code: [princeton-nlp/ALCE](https://github.com/princeton-nlp/ALCE)
  * **Offers:** automatic metrics for fluency, correctness and **citation recall/precision** (NLI-based).
  * **→ Use:** the citation format (`[transcript_id:turn_id]`) and its evaluation.
* **[G2]** S. Es, J. James, L. Espinosa Anke, S. Schockaert. *RAGAs: Automated Evaluation of Retrieval Augmented Generation.* **EACL 2024 (demo)**. <https://aclanthology.org/2024.eacl-demo.16/>. Code: [explodinggradients/ragas](https://github.com/explodinggradients/ragas)
  * **Offers:** reference-free faithfulness, answer relevance and context relevance.
* **[G3]** Y. Zha, Y. Yang, R. Li, Z. Hu. *AlignScore: Evaluating Factual Consistency with a Unified Alignment Function.* **ACL 2023**. <https://aclanthology.org/2023.acl-long.634/>. Code: [yuh-zha/AlignScore](https://github.com/yuh-zha/AlignScore)
  * **Offers:** a consistency scorer trained on 4.7M examples from 7 tasks.
  * **→ Use:** claim-level verification of each generated sentence against its cited turns.
* **[G4]** N. F. Liu et al. *Lost in the Middle: How Language Models Use Long Contexts.* **TACL 12, 2024**. <https://aclanthology.org/2024.tacl-1.9/>
  * **Offers:** accuracy drops when the relevant evidence sits in the middle of a long context.
  * **→ Use:** short, ranked evidence packs, with the strongest evidence first.
* **[G5]** G. V. Cormack, C. L. A. Clarke, S. Büttcher. *Reciprocal rank fusion outperforms Condorcet and individual rank learning methods.* **SIGIR 2009**.
  * **→ Use:** fuse BM25 and dense retrieval over turn windows.
* **[G6]** L. Zheng et al. *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* **NeurIPS 2023 (Datasets & Benchmarks)**.
  * **Offers:** LLM judges agree well with humans but have position, verbosity and self-enhancement biases.
  * **→ Use:** judge prompts with order swapping and rubrics; judge the query dataset and the answers.

### H. Task 2: contextual follow-ups

* **[H1]** A. Elgohary, D. Peskov, J. Boyd-Graber. *Can You Unpack That? Learning to Rewrite Questions-in-Context* (CANARD). **EMNLP-IJCNLP 2019**. <https://aclanthology.org/D19-1605/>. Code: [aagohary/canard](https://github.com/aagohary/canard)
  * **Offers:** rewrite context-dependent questions into self-contained ones.
* **[H2]** R. Anantha et al. *Open-Domain Question Answering Goes Conversational via Question Rewriting* (QReCC). **NAACL 2021**. <https://aclanthology.org/2021.naacl-main.44/>. Code: [apple/ml-qrecc](https://github.com/apple/ml-qrecc)
  * **Offers:** evaluates rewriting, retrieval and reading as separate stages.
  * **→ Use:** our Task-2 evaluation protocol.
* **[H3]** K. Mao et al. *Large Language Models Know Your Contextual Search Intent: A Prompting Framework for Conversational Search* (LLM4CS). **Findings of EMNLP 2023**. <https://aclanthology.org/2023.findings-emnlp.86/>. Code: [kyriemao/LLM4CS](https://github.com/kyriemao/LLM4CS)
  * **Offers:** prompting that generates several rewrites (plus hypothetical answers) and aggregates them.
  * **→ Use:** follow-up rewriting with an LLM.

### I. Query dataset & data quality

* **[I1]** Y. Wang et al. *Self-Instruct: Aligning Language Models with Self-Generated Instructions.* **ACL 2023**. <https://aclanthology.org/2023.acl-long.754/>
  * **Offers:** bootstrapping from seed tasks with an LLM, plus similarity filtering.
  * **→ Use:** query generation, then human review.
* **[I2]** S. Kaufman, S. Rosset, C. Perlich, O. Stitelman. *Leakage in data mining: Formulation, detection, and avoidance.* **ACM TKDD 6(4), 2012**. <https://dl.acm.org/doi/10.1145/2382577.2382579>
  * **→ Use:** analyst notes such as "no escalation occurred" are quarantined and never used as evidence.
* **[I3]** K. Lee, D. Ippolito, A. Nystrom, C. Zhang, D. Eck, C. Callison-Burch, N. Carlini. *Deduplicating Training Data Makes Language Models Better.* **ACL 2022**. <https://aclanthology.org/2022.acl-long.577/>
  * **→ Use:** exact and MinHash near-duplicate handling; clusters are kept inside one split.
* **[I4]** T. Gebru et al. *Datasheets for Datasets.* **Communications of the ACM 64(12), 2021**. <https://dl.acm.org/doi/10.1145/3458723>
  * **→ Use:** the auto-generated `cleaned_data/DATA_CARD.md`.

---

## 3 · Proposed architecture (research-grounded, with novel parts)

> **Final plan:** the step-by-step methodology actually chosen is in [`METHODOLOGY.md`](METHODOLOGY.md) (v2). It weighs these options against the dataset and the deadline, and lists one paper and one repo per step. This section is the broader research view it was derived from. **Where they differ, METHODOLOGY v2 wins.** The main differences:
>
> * landmark risk sets (sequential target trials) instead of matched pre-event windows;
> * metadata kept out of the causal core after a leakage audit;
> * claim levels L0–L3 computed from predefined checks;
> * deletion tests reported as model faithfulness only;
> * three answer gates (numbers, causal-claim licensing, evidence);
> * state + delta for follow-ups.

Guiding principle (METHODOLOGY v2): **"The AI proposes and synthesizes; statistical identification and predefined validation tests constrain what can be claimed."** It builds on [E8] and [E9].

```
                    ┌───────────────────── OFFLINE (once) ─────────────────────┐
cleaned_data ──►  (1) Event labelling      weak cues → LLM check on candidates → light classifier   [F3][C4][C5]
(turns, calls,        + human-validated sample (P/R/F1)
 event turn ids)  (2) Landmark risk sets   at every turn k: calls still event-free; covariates only from
                                           turns < k (no call length, no metadata)                   [A1][A2][E3]
                  (3) Hypothesis discovery LLM proposes NL factors from window contrasts (train split) [F1][F2][F4]
                                           + existing cue features (holds, refusals, repeats, …)
                  (4) Causal estimation    pilot on train → pre-register → confirm once on dev+test:
                                           DML (ATT) adjusted for the history before k, overlap, balance,
                                           BH, negative controls, E-values, label-error correction   [E3][E4][E6][E7]
                                           ⇒ FACTOR LIBRARY (effect, CI, claim level L0–L3, exemplars)
                  (5) Evidence index       3–5-turn windows · BM25 + dense · RRF · metadata filters    [G5]
                    └──────────────────────────────────────────────────────────┘
                    ┌───────────────────── ONLINE (per query) ─────────────────┐
query ──► (6) query parser → {event, filters, question type}                (Task 2: + session state)
          (7) global: factor library / cluster summaries (map-reduce)                        [F5]
              local : retrieve windows → one per call → grounding spans (+ faithfulness score) [D3][A2]
          (8) synthesis: mechanism → factor → effect size → cited spans [id:turn] → caveats    [G1][G4]
          (9) verification gates: numbers (placeholders) · causal-claim level · evidence
              (exact quotes + AlignScore/NLI)                                                [G3]
          (10) Task 2: state {event, filters, factors, cited ids} + follow-up delta merge     [H1][H2][H3]
                    └──────────────────────────────────────────────────────────┘
```

**Novel elements**, i.e. combinations not found together in the cited work:

1. **Event-anchored evidence spans.** RECCON-style span extraction [D1] is applied to *business events*. Candidates are restricted to turns that precede the event's onset. Temporal precedence [A1][A2] is an eligibility rule, not proof of cause.
2. **Three separate claims per factor.** The *effect* comes from the causal estimate. The *evidence* is the turn where the behaviour occurs. The *faithfulness* is how much the forecaster relies on that turn (ERASER comprehensiveness [D3] vs a random-turn baseline). The three are never merged into "this line caused the event".
3. **"LLM proposes, statistics disposes."**
   * D5 / LLooM-style natural-language hypotheses [F1][F4] are discovered on `train`.
   * They are then estimated with DML and refuted with DoWhy on `dev`/`test` [E3][E6][E7].
   * The output is a *library of validated causal factors* with effect sizes and exemplar spans, not free-form LLM narratives.
4. **Claim-level faithfulness guard.** Every generated sentence must be entailed by its cited turns [G1][G3], and every number comes from the factor library.
5. **Analytical dialogue state for Task 2.** Follow-ups are rewritten [H1–H3] against an explicit state (active event, filters, factor ids, cited evidence), so "what about refunds?" or "only for airlines" reuse earlier analysis instead of starting over.

Everything above consumes `cleaned_data/` as produced by `notebooks/01_data_cleaning.ipynb`:

| Component | Fields it uses |
|---|---|
| citeable evidence | `turn_uid` |
| temporal anchoring | event onsets (Step 1 of METHODOLOGY); the weak `*_turn_id` signals are the starting point |
| factor features | `cue_*`, `is_repeat`, `n_filled_pauses` |
| filters | `opening_domain_vote`, `brand`; other metadata only if the leakage audit does not flag it |
| split-sample workflow | `split` |
| quality filter | `qc_ok` for descriptive statistics; causal eligibility uses the landmark rules and `column_availability.csv` |

---

## 4 · Evaluation plan (metrics)

| Component | Metric | Reference |
|---|---|---|
| speaker-role resolution | accuracy under hidden-label validation (reported by the cleaning notebook) | [B5] |
| event labelling | precision / recall / F1 vs a human-labelled sample; Cohen's κ between annotators | [F3] |
| retrieval | Recall@k, nDCG@10, MRR on queries with judged relevant windows | [G5] |
| evidence spans | grounding precision vs human judgement; **comprehensiveness** vs a random-removal baseline (faithfulness only; keep-only sufficiency dropped as out-of-distribution) | [D3], [D4] |
| causal factors | effect size with 95% CI; sign stability across bootstrap and splits; refutation pass rate (placebo, random common cause, subset) | [E3], [E6], [E7] |
| answer faithfulness | RAGAS faithfulness; AlignScore per claim; share of unsupported claims | [G2], [G3] |
| citation quality | ALCE citation recall / precision | [G1] |
| overall answer quality | LLM-as-judge rubric (correctness, groundedness, causal rigour, actionability, clarity) with position-swap; human rating on a subset | [G6] |
| Task 2 | follow-up rewrite accuracy vs gold rewrites; context carry-over (filters/event preserved); cross-turn consistency | [H1], [H2] |
| system | latency, tokens per answer | — |

---

## 5 · Query dataset plan (50–100 queries)

**Categories**, so that the distribution is balanced and reportable:

* **task:** T1 initial query / T2 follow-up (T2 grouped into 3–4-turn sessions).
* **type:**
  * simple retrieval ("show calls where …");
  * aggregation ("how often …");
  * causal explanation ("why …");
  * multi-hop / comparative ("do escalations in banking have different causes than in telecom?");
  * temporal ("what happens in the turns before customers mention cancelling?");
  * product improvement ("which complaints point to product fixes?");
  * ambiguous or under-specified ("why are customers unhappy?");
  * unanswerable or out-of-scope ("what is the CSAT score?", "which agent should be fired?").
* **event:** escalation / refund / churn / transfer / product feedback.
* **difficulty:** easy / medium / hard.

**Suggested target of 80 queries:**

* T1: 15 simple + 10 aggregation + 20 causal + 8 comparative/multi-hop + 5 temporal + 5 product + 5 ambiguous + 5 unanswerable.
* T2: 7 sessions of 1 seed + 2 follow-ups, i.e. about 21 follow-ups (the seeds overlap with T1).

**Process:**

1. Build the taxonomy and seed 2–3 hand-written queries per cell.
2. Generate paraphrases per cell with an LLM (Self-Instruct style [I1]); drop near-duplicates (ROUGE-L ≥ 0.7).
3. Human review for realism, answerability against *this* corpus, and correct category.
4. LLM-as-judge [G6] scores realism, clarity, diversity and category fit; low scores are revised.
5. Store each query with its category, the expected behaviour (answer / clarify / refuse), and — for a subset — gold relevant calls/spans for retrieval and span metrics.
6. Run the system, store outputs, and report metrics per category. This includes the failure cases the brief asks for.

---

## 6 · Repositories worth reusing

| Purpose | Repository |
|---|---|
| conversation features, corpus model | [CornellNLP/ConvoKit](https://github.com/CornellNLP/ConvoKit) |
| turn-by-turn forecasting | [jpwchang/CRAFT](https://github.com/jpwchang/CRAFT) |
| cause-span extraction in dialogue | [declare-lab/RECCON](https://github.com/declare-lab/RECCON), [NUSTM/MECPE](https://github.com/NUSTM/MECPE) |
| causal effects of text | [rpryzant/causal-text](https://github.com/rpryzant/causal-text), [py-why/dowhy](https://github.com/py-why/dowhy), [py-why/EconML](https://github.com/py-why/EconML), [py-why/pywhy-llm](https://github.com/py-why/pywhy-llm) |
| hypothesis / concept discovery | [ruiqi-zhong/D5](https://github.com/ruiqi-zhong/D5), [ruiqi-zhong/nlparam](https://github.com/ruiqi-zhong/nlparam), [michelle123lam/lloom](https://github.com/michelle123lam/lloom) |
| global corpus QA | [microsoft/graphrag](https://github.com/microsoft/graphrag) |
| attribution & RAG evaluation | [princeton-nlp/ALCE](https://github.com/princeton-nlp/ALCE), [explodinggradients/ragas](https://github.com/explodinggradients/ragas), [yuh-zha/AlignScore](https://github.com/yuh-zha/AlignScore) |
| follow-up rewriting | [aagohary/canard](https://github.com/aagohary/canard), [apple/ml-qrecc](https://github.com/apple/ml-qrecc), [kyriemao/LLM4CS](https://github.com/kyriemao/LLM4CS) |
| satisfaction dynamics | [smartyfh/ASAP](https://github.com/smartyfh/ASAP), [sunnweiwei/user-satisfaction-simulation](https://github.com/sunnweiwei/user-satisfaction-simulation) |
| customer-service dialogues | [asappresearch/abcd](https://github.com/asappresearch/abcd) |
| disfluency detection | [pariajm/joint-disfluency-detector-and-parser](https://github.com/pariajm/joint-disfluency-detector-and-parser) |
| near-duplicate detection | [ekzhu/datasketch](https://github.com/ekzhu/datasketch) (design reference; the notebook re-implements MinHash-LSH with exact verification so the split does not depend on the package version) |
