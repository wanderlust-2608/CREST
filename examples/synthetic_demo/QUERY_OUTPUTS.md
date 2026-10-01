# Query set and system outputs

Every query of the dev and locked test sets, with its tags (task, difficulty, kind of query, use case), the behaviour expected of the system, whether that happened, and the full answer exactly as shown to a user (numbers filled in by code, cited dialogue turns as `transcript_id:turn`). Sessions (Task 2) are shown turn by turn. Known limitations are questions the system is known to handle badly; they are scored against what an ideal system would do and kept out of the headline scores.

## The query set

* **Task:** task1 85, task2 13
* **Difficulty:** easy 12, hard 33, medium 53
* **Kind of query:** ambiguous 3, cannot_answer 13, evidence_lookup 3, follow_up 13, impact_evaluation 3, known_limitation 4, multi_hop 23, premise_check 9, robustness 10, simple_retrieval 17
* **Use case:** evidence_lookup 2, follow_up 13, guardrail 22, hypothesis_test 9, impact_evaluation 3, monitoring 7, process_improvement 2, product_improvement 3, robustness 10, root_cause 18, segment_comparison 5, stress_test 4
* **Category:** ambiguous 3, before_after 3, behaviour_profile 2, compare 2, conditional 3, effect_of 3, examples 2, false_presupposition 5, how_often 3, known_limitation 4, leading 1, multi_hop 3, multilingual 6, noisy_text 4, out_of_scope 7, overview 2, product_improvement 3, ranking 3, retention_risk 2, session 13, single_call 3, threshold 3, tiny_subgroup 1, trend 2, true_premise 3, unanswerable 4, unsupported_filter 1, what_to_change 2, why 5
* **Questions in total** (session turns counted): 126; distinct-1 0.32, distinct-2 0.62, mean pairwise ROUGE-L 0.07.

## Dev queries (65)

### Task 1: evidence-based causal explanation

#### q003 — how_often · easy · simple_retrieval · monitoring

**Question:** How often do customers escalate?

Expected: answer (event ESC, type how_often). Outcome: as expected (the system answered a 'how_often' question about ESC).

> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Corrected for labeller errors with the blind gold sample, the held-out rate is 48.1% (95% CI 47.3% to 48.9%).
> 0.0% of these escalations started within the opening turns.
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 77.6% of these calls, against 5.3% at the same point in calls without one.
> All numbers describe this corpus of calls, not customers in general.

#### q018 — how_often · easy · simple_retrieval · monitoring

**Question:** How often do customers ask for refunds?

Expected: answer (event REF, type how_often). Outcome: as expected (the system answered a 'how_often' question about REF).

> In all calls, 1,224 of 4,000 calls (30.6%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Corrected for labeller errors with the blind gold sample, the held-out rate is 30.2% (95% CI 30.2% to 30.2%).
> 31.5% of these refund episodes started within the opening turns.
> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> All numbers describe this corpus of calls, not customers in general.

#### q033 — examples · easy · simple_retrieval · evidence_lookup

**Question:** Show me examples of calls where customers threaten to leave

Expected: answer (event CHURN, type examples). Outcome: as expected (the system answered a 'examples' question about CHURN).

> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> “honestly i'm thinking about switching to another provider” [51746801-e13a-fb56-17d9-bc3e0512a739:7]
> “honestly i'm thinking about switching to another provider” [0447243d-5660-58a7-389d-08d16bd3115e:9]
> “honestly i'm thinking about switching to another provider i'm getting really frustrated with this” [5d3a515e-27fc-d824-6ff0-8eb77f6895fb:13]
> “honestly i'm thinking about switching to another provider” [0f7e45c4-85e0-05b1-100d-70f4d0a75b21:7]
> “honestly i'm thinking about switching to another provider” [1618b6a3-0f81-fc0c-61e0-b63413e97c48:5]
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> In the 6 turns before the churn threat, the customer expressed frustration or anger in 66.3% of these calls, against 24.9% at the same point in calls without one.
> Examples illustrate; they are not counts or evidence of an effect.

*Dialogue turns cited: `51746801-e13a-fb56-17d9-bc3e0512a739:7`, `0447243d-5660-58a7-389d-08d16bd3115e:9`, `5d3a515e-27fc-d824-6ff0-8eb77f6895fb:13`, `0f7e45c4-85e0-05b1-100d-70f4d0a75b21:7`, `1618b6a3-0f81-fc0c-61e0-b63413e97c48:5`*

#### q020 — trend · easy · simple_retrieval · monitoring

**Question:** How have refund requests changed over time?

Expected: answer (event REF, type trend). Outcome: as expected (the system answered a 'trend' question about REF).

> Weekly share of calls with a refund episode: 2025-11-03/2025-11-09: 30.1%; 2025-11-10/2025-11-16: 31.7%.
> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> Week-to-week changes in these shares can come from the mix of calls in each week as well as from what happens in the calls.
> All numbers describe this corpus of calls, not customers in general.

#### q016 — ranking · easy · simple_retrieval · segment_comparison

**Question:** Which industry has the highest escalation rate?

Expected: answer_rank (event ESC, type compare). Outcome: as expected (the system answered a 'compare' question about ESC).

> Ranked by the share of calls with an escalation: airline calls 53.3% (347 of 651); banking calls 51.6% (329 of 638); hotel calls 50.1% (352 of 702); insurance calls 43.1% (271 of 629); retail calls 42.1% (292 of 693); telecom calls 39.9% (274 of 687).
> These are counts; differences between groups of calls are not effects of anything in the calls.
> Why, from the conversations: in airline calls, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 25.1% of them (against 71.4% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 77.2% of these calls, against 6.9% at the same point in calls without one.
> For the full reasoning and the causal test for escalations in airline calls, ask a follow-up such as 'why in airline calls?'
> All numbers describe this corpus of calls, not customers in general.

#### q028 — ranking · easy · simple_retrieval · segment_comparison

**Question:** Which industry has the most refund requests?

Expected: answer_rank (event REF, type compare). Outcome: as expected (the system answered a 'compare' question about REF).

> Ranked by the share of calls with a refund episode: retail calls 34.2% (237 of 693); hotel calls 30.9% (217 of 702); insurance calls 30.2% (190 of 629); telecom calls 30.0% (206 of 687); banking calls 29.5% (188 of 638); airline calls 28.6% (186 of 651).
> These are counts; differences between groups of calls are not effects of anything in the calls.
> Why, from the conversations: in retail calls, before the refund episode the agent offered a concrete solution in only 25.7% of them (against 43.6% at the same point in other calls).
> For the full reasoning and the causal test for refund episodes in retail calls, ask a follow-up such as 'why in retail calls?'
> All numbers describe this corpus of calls, not customers in general.

#### q015 — product_improvement · medium · simple_retrieval · product_improvement

**Question:** What do customers complain about before they ask for a supervisor?

Expected: answer_topics (event ESC, type issues). Outcome: as expected (the system answered a 'issues' question about ESC).

> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> At the start of calls that later had an escalation, customers use these words more than in calls without one: 'flight' (18.6% of those calls, 14.2% of calls without one); 'pnr' (18.6% of those calls, 14.2% of calls without one).
> “hi i'm calling because my connecting flight was cancelled” [025b3b4b-669a-e152-3105-da20b47368b6:1]
> “sure it's pnr q3924601” [0067eda9-7d78-73f5-41f8-48b44ef1806b:3]
> These are word counts from what customers say before the escalation starts, not estimated effects. To see which agent behaviours matter for escalations, ask 'why do escalations happen?'
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 77.6% of these calls, against 5.3% at the same point in calls without one.
> All numbers describe this corpus of calls, not customers in general.

*Dialogue turns cited: `025b3b4b-669a-e152-3105-da20b47368b6:1`, `0067eda9-7d78-73f5-41f8-48b44ef1806b:3`*

#### q027 — product_improvement · medium · simple_retrieval · product_improvement

**Question:** Which product or service problems lead to refund requests?

Expected: answer_topics (event REF, type issues). Outcome: as expected (the system answered a 'issues' question about REF).

> In all calls, 1,224 of 4,000 calls (30.6%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> At the start of calls that later had a refund episode, customers use these words more than in calls without one: 'delivered' (10.1% of those calls, 7.5% of calls without one); 'package' (10.1% of those calls, 7.5% of calls without one).
> “hi i'm calling because my package was not delivered after two weeks” [02fa4e28-68f4-f7b8-060d-a35fb9ed8581:1]
> These are word counts from what customers say before the refund episode starts, not estimated effects. To see which agent behaviours matter for refund episodes, ask 'why do refund episodes happen?'
> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> In the customer's own words: “hi i'm calling because my internet has been down since last night and this is completely unacceptable and i would like a refund” [7496fdf8-a677-6179-5005-c1f9e2d3895e:1]
> In the customer's own words: “hi i'm calling because my premium went up at renewal and honestly i'm pretty annoyed about it and i would like a refund” [1c736c49-fe0a-50ce-7247-0000d2c47f9b:1]
> All numbers describe this corpus of calls, not customers in general.

*Dialogue turns cited: `02fa4e28-68f4-f7b8-060d-a35fb9ed8581:1`, `7496fdf8-a677-6179-5005-c1f9e2d3895e:1`, `1c736c49-fe0a-50ce-7247-0000d2c47f9b:1`*

#### q001 — why · medium · multi_hop · root_cause

**Question:** Why do customers escalate?

Expected: answer (event ESC, type why). Outcome: as expected (the system answered a 'why' question about ESC).

> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

#### q029 — why · medium · multi_hop · root_cause

**Question:** Why do customers threaten to leave?

Expected: answer (event CHURN, type why). Outcome: as expected (the system answered a 'why' question about CHURN).

> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 66.3% of these calls (against 24.9% at the same point in calls without one); the agent refused a request or cited policy in 68.4% of these calls (against 46.2% at the same point in calls without one).
> Empathy statements were common before the churn threat too (64.1%), but about as common at the same point in calls without one (61.1%), so on their own they do not set these calls apart.
> 89.3% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my claim has been under review for three weeks and this is completely unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:1]
> Then the customer expressed frustration or anger: “sure it's pl 6395 751 and please hurry this is unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:3]
> Then the churn threat: “honestly i'm thinking about switching to another provider” [3169e20d-7aaf-aee7-0a70-19178db8442f:5]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Causal test: for churn threats in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a churn threat later in the call by 7.7 percentage points (95% CI -11.6 to -3.8 points) at the moments where they happened [F19].
> Under the same assumptions, that is about 35 fewer churn threats among the held-out calls (95% CI 17 to 53) [F19].
> Solution offers also happened in 701 of 742 held-out calls where no churn threat followed [F19].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay just to confirm that is hx 7964 810 on the file” [4273908c-b138-f619-6f47-c209d47710d2:4]
> “i understand how frustrating that must uh be what i can do is offer you a free replacement with express delivery let me check that for you one moment please” [44104768-b4d3-5de2-34e2-ddc4c77c2905:4]
> Warning sign: policy refusals are associated with a higher chance of a churn threat later in the call (+4.1 percentage points, 95% CI +0.2 to +8.0 points) [F20].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F20].
> “i'm afraid we cannot make an exception here” [73d59436-be13-b2cf-06bd-48568400af72:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a churn threat (+4.7 percentage points, 95% CI -0.3 to +9.7 points) [F21].
> “yes that is correct i'm getting you know really frustrated with this” [43fbf10c-7ee5-caaa-2948-aab62844edd4:15]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a churn threat (+2.9 percentage points, 95% CI -1.4 to +7.1 points) [F22].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the churn threat; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.84 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F19 (L3), F20 (L2), F21 (L2), F22 (L2)*
*Dialogue turns cited: `3169e20d-7aaf-aee7-0a70-19178db8442f:1`, `3169e20d-7aaf-aee7-0a70-19178db8442f:3`, `3169e20d-7aaf-aee7-0a70-19178db8442f:5`, `4273908c-b138-f619-6f47-c209d47710d2:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:4`, `73d59436-be13-b2cf-06bd-48568400af72:4`, `43fbf10c-7ee5-caaa-2948-aab62844edd4:15`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q030 — why · medium · multi_hop · root_cause

**Question:** What drives churn threats in retail calls?

Expected: answer (event CHURN, type why). Outcome: as expected (the system answered a 'why' question about CHURN with filters {"industry": ["retail_ecommerce"]}).

> Why, from the conversations: in retail calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 28.6% of them (against 53.0% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 67.9% of these calls (against 23.8% at the same point in calls without one); the agent refused a request or cited policy in 61.6% of these calls (against 41.8% at the same point in calls without one).
> Empathy statements were common before the churn threat too (64.3%), but about as common at the same point in calls without one (62.0%), so on their own they do not set these calls apart.
> 89.3% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my package was not delivered after two weeks and honestly i'm pretty annoyed about it” [7837e57f-77d9-4640-6ca5-0b880933b623:1]
> Then the customer expressed frustration or anger: “i see i'm getting really frustrated with this” [7837e57f-77d9-4640-6ca5-0b880933b623:15]
> Then the churn threat: “uh honestly i'm thinking about switching to another uh provider” [7837e57f-77d9-4640-6ca5-0b880933b623:19]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In retail calls, 112 of 693 calls (16.2%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Estimates for retail calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for churn threats in retail calls; the behaviours below are warning signs only.
> No clear difference: for policy refusals the estimate is compatible with no difference in the chance of a churn threat (+4.7 percentage points, 95% CI -5.7 to +15.0 points) [F167].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F167].
> Policy refusals also happened in 414 of 493 held-out calls where no churn threat followed [F167].
> “i'm afraid we cannot make an exception here” [48089445-f363-4154-0cb0-ab3492c4c094:10]
> “uh unfortunately per our policy i'm not able to change that” [5c9d801a-b66f-0966-075c-812fdcbe5ddc:16]
> In the risk forecaster, removing such a turn moves the forecast more than removing 79% of the same speaker's other turns (a check of the model, not proof of what happened) [F167].
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F167 (L2)*
*Dialogue turns cited: `7837e57f-77d9-4640-6ca5-0b880933b623:1`, `7837e57f-77d9-4640-6ca5-0b880933b623:15`, `7837e57f-77d9-4640-6ca5-0b880933b623:19`, `48089445-f363-4154-0cb0-ab3492c4c094:10`, `5c9d801a-b66f-0966-075c-812fdcbe5ddc:16`*

#### q004 — compare · medium · multi_hop · segment_comparison

**Question:** Compare escalations between hotel and retail calls

Expected: answer (event ESC, type compare). Outcome: as expected (the system answered a 'compare' question about ESC).

> Share of calls with the event: 50.1% of hotel calls (352 of 702); 42.1% of retail calls (292 of 693).
> Why, from the conversations: in hotel calls, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 31.0% of them (against 69.1% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 78.7% of these calls, against 4.9% at the same point in calls without one.
> Why, from the conversations: in retail calls, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 31.8% of them (against 66.8% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 77.7% of these calls, against 8.0% at the same point in calls without one.
> These are counts and patterns in the transcripts; differences between groups of calls are not effects of anything in the calls.
> All numbers describe this corpus of calls, not customers in general.

#### q008 — effect_of · medium · multi_hop · hypothesis_test

**Question:** Are solution offers linked to escalations?

Expected: answer (event ESC, type effect_of). Outcome: as expected (the system answered a 'effect_of' question about ESC).

> From the conversations: in the 6 turns before an escalation, the agent offered a concrete solution in 27.3% of these calls, against 68.7% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because i was charged an overdraft fee i do not understand” [1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:1]
> Then the agent offered a concrete solution: “what i can do is uh offer you a waiver of the late fee let me check that for you one moment please just to confirm that is ending 2846 on the file” [1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:14]
> Then the escalation: “get me someone above you right now” [1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:15]
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41 with both to explain the estimates away (E-values).
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3)*
*Dialogue turns cited: `1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:1`, `1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:14`, `1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:15`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`*

#### q021 — effect_of · medium · multi_hop · hypothesis_test

**Question:** Are solution offers linked to refund requests?

Expected: answer (event REF, type effect_of). Outcome: as expected (the system answered a 'effect_of' question about REF).

> From the conversations: in the 6 turns before a refund episode, the agent offered a concrete solution in 24.3% of these calls, against 41.2% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the agent offered a concrete solution: “unfortunately per our policy i'm not able to change that what i can do is offer you a loyalty discount at renewal just to confirm that is pl 4540 579 on the file” [0c3a65d0-50a4-5319-7dd9-73df32594123:12]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3)*
*Dialogue turns cited: `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:12`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`*

#### q032 — what_to_change · hard · multi_hop · process_improvement

**Question:** How can we reduce churn threats?

Expected: answer (event CHURN, type what_to_change). Outcome: as expected (the system answered a 'what_to_change' question about CHURN).

> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 66.3% of these calls (against 24.9% at the same point in calls without one); the agent refused a request or cited policy in 68.4% of these calls (against 46.2% at the same point in calls without one).
> Empathy statements were common before the churn threat too (64.1%), but about as common at the same point in calls without one (61.1%), so on their own they do not set these calls apart.
> 89.3% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my claim has been under review for three weeks and this is completely unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:1]
> Then the customer expressed frustration or anger: “sure it's pl 6395 751 and please hurry this is unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:3]
> Then the churn threat: “honestly i'm thinking about switching to another provider” [3169e20d-7aaf-aee7-0a70-19178db8442f:5]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Causal test: for churn threats in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a churn threat later in the call by 7.7 percentage points (95% CI -11.6 to -3.8 points) at the moments where they happened [F19].
> Under the same assumptions, that is about 35 fewer churn threats among the held-out calls (95% CI 17 to 53) [F19].
> Solution offers also happened in 701 of 742 held-out calls where no churn threat followed [F19].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay just to confirm that is hx 7964 810 on the file” [4273908c-b138-f619-6f47-c209d47710d2:4]
> “i understand how frustrating that must uh be what i can do is offer you a free replacement with express delivery let me check that for you one moment please” [44104768-b4d3-5de2-34e2-ddc4c77c2905:4]
> What could change: at comparable moments, doing more of this is estimated to lower the chance of a churn threat by up to 7.7 percentage points, under the stated assumptions [F19].
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the churn threat; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.84 with both to explain the estimates away (E-values).
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F19 (L3)*
*Dialogue turns cited: `3169e20d-7aaf-aee7-0a70-19178db8442f:1`, `3169e20d-7aaf-aee7-0a70-19178db8442f:3`, `3169e20d-7aaf-aee7-0a70-19178db8442f:5`, `4273908c-b138-f619-6f47-c209d47710d2:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:4`*

#### q045 — multi_hop · hard · multi_hop · root_cause

**Question:** Do the behaviours that raise escalations also raise churn threats?

Expected: answer_shared (event ESC, type shared). Outcome: as expected (the system answered a 'shared' question about ESC).

> In all calls: escalations in 46.6% of calls; churn threats in 14.7% of calls.
> Warning sign for escalations and churn threats: policy refusals are associated with a higher chance of an escalation (+32.2 percentage points, 95% CI +26.6 to +37.7 points) [F2] and of a churn threat (+4.1 percentage points, 95% CI +0.2 to +8.0 points) [F20].
> Warning sign for escalations and churn threats: solution offers are associated with a lower chance of an escalation (-31.5 percentage points, 95% CI -37.8 to -25.2 points) [F1] and of a churn threat (-7.7 percentage points, 95% CI -11.6 to -3.8 points) [F19].
> Warning signs for escalations only: holds and wait requests [F3], customer confusion [F5].
> Of these, the following passed every causal check for their event: holds and wait requests for escalations [F3], policy refusals for escalations [F2], solution offers for escalations [F1], solution offers for churn threats [F19].
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 77.6% of these calls, against 5.3% at the same point in calls without one.
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> In the 6 turns before the churn threat, the customer expressed frustration or anger in 66.3% of these calls, against 24.9% at the same point in calls without one.
> Each event was analysed separately; a behaviour flagged for several events is not shown to connect the events to each other. Ask about one event for its full answer with quotes.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F2 (L3), F20 (L2), F1 (L3), F19 (L3), F3 (L3), F5 (L2)*

#### q046 — multi_hop · hard · multi_hop · root_cause

**Question:** Is offering a solution linked to fewer refund requests and churn threats?

Expected: answer_shared (event REF, type shared). Outcome: as expected (the system answered a 'shared' question about REF).

> In all calls: refund episodes in 30.6% of calls; churn threats in 14.7% of calls.
> For refund episodes: solution offers are associated with a lower chance of a refund episode (-15.9 percentage points, 95% CI -22.0 to -9.9 points) [F10]. It passed every causal check for this event.
> For churn threats: solution offers are associated with a lower chance of a churn threat (-7.7 percentage points, 95% CI -11.6 to -3.8 points) [F19]. It passed every causal check for this event.
> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> In the 6 turns before the churn threat, the customer expressed frustration or anger in 66.3% of these calls, against 24.9% at the same point in calls without one.
> Each event was analysed separately; a behaviour flagged for several events is not shown to connect the events to each other. Ask about one event for its full answer with quotes.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F19 (L3)*

#### q064 — conditional · hard · multi_hop · root_cause

**Question:** Do refunds happen more in calls with escalations?

Expected: answer_condition (event REF, type why). Outcome: as expected (the system answered a 'why' question about REF with filters {"with_event": ["ESC"]}).

> This answer looks only at calls with an escalation (1,865 calls).
> In those calls, 717 (38.4%) had a refund episode, against 23.7% of calls without an escalation and 30.6% of all calls in the slice.
> In the calls with both, the escalation came first in 81, the refund episode came first in 636, and both started in the same turn in 0.
> Why, from the conversations: in calls with an escalation, before the refund episode the agent put the customer on hold or asked them to wait in only 24.4% of them (against 44.1% at the same point in other calls).
> Empathy statements were common before the refund episode too (49.4%), but about as common at the same point in calls without one (54.5%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because the room type was not what i reserved and this is completely unacceptable and i would like a refund” [076458f8-31c6-1fc9-4bd1-08d7dced55dd:1]
> In the customer's own words: “hi i'm calling because i was charged an overdraft fee i do not understand and this is completely unacceptable and i would like a refund” [1c586ca7-bc3e-ec0e-6931-1650b4fa4371:1]
> One call, step by step: the customer's problem: “hi i'm calling because the room type was not what i reserved and honestly i'm pretty annoyed about it” [3470921b-83fc-cd84-230c-f293c361c8c6:1]
> Then the refund episode: “i would like a refund uh for this this is ridiculous” [3470921b-83fc-cd84-230c-f293c361c8c6:17]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In calls with an escalation, 717 of 1,865 calls (38.4%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Effect estimates are available for all calls and for single industries; the filters apply to the counts only.
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> “i understand how frustrating that must be” [00f67d92-72a7-d42e-27a8-d297c7a38d30:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> “alright i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:17]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*
*Dialogue turns cited: `076458f8-31c6-1fc9-4bd1-08d7dced55dd:1`, `1c586ca7-bc3e-ec0e-6931-1650b4fa4371:1`, `3470921b-83fc-cd84-230c-f293c361c8c6:1`, `3470921b-83fc-cd84-230c-f293c361c8c6:17`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`, `00f67d92-72a7-d42e-27a8-d297c7a38d30:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:17`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q065 — conditional · hard · multi_hop · root_cause

**Question:** How often do customers who were refused a refund threaten to cancel?

Expected: answer_condition (event CHURN, type how_often). Outcome: as expected (the system answered a 'how_often' question about CHURN with filters {"with_event": ["REF_DENIED"]}).

> This answer looks only at calls where a refund was refused (322 calls).
> In those calls, 113 (35.1%) had a churn threat, against 20.5% of calls where a refund came up but was not refused and 14.7% of all calls in the slice.
> In the calls with both, the refusal came first in 55, the churn threat came first in 58, and both started in the same turn in 0.
> In calls where a refund was refused, 113 of 322 calls (35.1%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> 0.0% of these churn threats started within the opening turns.
> Why, from the conversations: in calls where a refund was refused, in the turns just before the churn threat the agent usually refused a request or cited policy and the agent usually expressed empathy, while the agent put the customer on hold or asked them to wait in only 40.7% of them (against 64.1% at the same point in other calls).
> In the 6 turns before the churn threat, the agent refused a request or cited policy in 88.5% of these calls, against 65.1% at the same point in calls without one.
> All numbers describe this corpus of calls, not customers in general.

#### q068 — before_after · hard · impact_evaluation · impact_evaluation

**Question:** Compare refund requests before and after 2025-11-08

Expected: answer_change (event REF, type trend). Outcome: as expected (the system answered a 'trend' question about REF).

> Calls in the data run from 2025-11-04 to 2025-11-12: 1,838 fall before 2025-11-08 and 2,162 on or after it.
> A refund episode happened in 29.3% of calls before 2025-11-08 and in 31.7% of calls from 2025-11-08 on: a difference of +2.5 percentage points (95% CI -0.4 to +5.3 points).
> The interval includes zero, so the data cannot tell the two periods apart.
> Interrupted time series (6-hour block periods: 15 before 2025-11-08 and 18 from it): before the date the share was moving by -0.4 percentage points per 6-hour block; at the date its level shifted by +4.5 percentage points (95% CI -3.4 to +12.4 points) and its trend changed by +0.5 percentage points per 6-hour block (95% CI -0.4 to +1.3 points).
> The model allows for the usual time-of-day pattern, and its intervals use Newey–West standard errors (never narrower than the classical ones; lag-one residual autocorrelation -0.24).
> Placebo check: at 4 made-up dates before 2025-11-08, 2 level shifts were at least as large as the real one, so the shift at the real date is within the series' usual movement.
> Why, from the conversations: in calls from 2025-11-08 on, before the refund episode the agent offered a concrete solution in only 21.9% of them (against 40.9% at the same point in other calls).
> Why, from the conversations: in calls before 2025-11-08, before the refund episode the agent offered a concrete solution in only 27.5% of them (against 41.6% at the same point in other calls).
> Read with care: these comparisons tie a change to the date only; anything that changed around 2025-11-08 (the season, the mix of calls, staffing) would show up the same way.
> All numbers describe this corpus of calls, not customers in general.

#### q069 — before_after · hard · impact_evaluation · impact_evaluation

**Question:** Did escalations increase after the new refund policy was introduced?

Expected: clarify (event ESC). Outcome: as expected (the system asked to clarify).

> When did the new refund policy start? Give the date (for example 'after 2025-11-08') and I will compare escalations before and after it.

#### q070 — threshold · medium · multi_hop · hypothesis_test

**Question:** Which behaviours raise escalations by more than five percentage points?

Expected: answer_threshold (event ESC, type why). Outcome: as expected (the system answered a 'why' question about ESC; notices: effect-size threshold).

> Effects are estimated with uncertainty, so the threshold in the question is checked against each behaviour's estimate and against its confidence interval.
> Behaviours whose estimated difference in the chance of an escalation later in the call is beyond 5.0 percentage points: policy refusals (+32.2 percentage points, 95% CI +26.6 to +37.7 points) [F2]; customer confusion (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5]; holds and wait requests (+8.6 percentage points, 95% CI +2.6 to +14.5 points) [F3]; repeated questions (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> For policy refusals [F2], the whole confidence interval is beyond 5.0 percentage points; for the others the interval reaches below the threshold.
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 77.6% of these calls, against 5.3% at the same point in calls without one.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F2 (L3), F5 (L2), F3 (L3), F4 (L2)*

#### q071 — threshold · medium · multi_hop · hypothesis_test

**Question:** Which industries have more than 20% refund requests?

Expected: answer_threshold (event REF, type compare). Outcome: as expected (the system answered a 'compare' question about REF; notices: rate threshold).

> The threshold in the question is compared with the share of calls that have the event.
> Ranked by the share of calls with a refund episode: retail calls 34.2% (237 of 693); hotel calls 30.9% (217 of 702); insurance calls 30.2% (190 of 629); telecom calls 30.0% (206 of 687); banking calls 29.5% (188 of 638); airline calls 28.6% (186 of 651).
> Groups with a share above 20.0%: retail calls, hotel calls, insurance calls, telecom calls, banking calls and airline calls.
> These are counts; differences between groups of calls are not effects of anything in the calls.
> Why, from the conversations: in retail calls, before the refund episode the agent offered a concrete solution in only 25.7% of them (against 43.6% at the same point in other calls).
> For the full reasoning and the causal test for refund episodes in retail calls, ask a follow-up such as 'why in retail calls?'
> All numbers describe this corpus of calls, not customers in general.

#### q073 — behaviour_profile · medium · simple_retrieval · root_cause

**Question:** Why are customers put on hold?

Expected: answer_profile. Outcome: as expected (the system answered a 'behaviour' question about None).

> In all calls, 2,793 of 4,000 calls (69.8%) had at least one moment where the agent put the customer on hold or asked them to wait.
> Why, from the conversations: in the 6 turns before the first time the agent put the customer on hold or asked them to wait, the customer expressed frustration or anger in 53.0% of these calls (against 6.0% at the same point in calls without it); the agent refused a request or cited policy in 45.9% of these calls (against 20.1% at the same point in calls without it).
> One call, step by step: then the customer expressed frustration or anger: “hi i'm calling because my package was not delivered after two weeks and honestly i'm pretty annoyed about it” [7444e19b-3a95-333d-7440-12dbc66dea42:1]
> Then the agent put the customer on hold or asked them to wait: “i understand how frustrating that must be unfortunately uh per our policy i'm not able to change that let me check that for uh you one moment please” [7444e19b-3a95-333d-7440-12dbc66dea42:4]
> How this relates to the business events: an escalation in 66.1% of calls with holds and wait requests and in 1.5% of calls without them; a refund episode in 34.9% of calls with holds and wait requests and in 20.6% of calls without them; a churn threat in 18.3% of calls with holds and wait requests and in 6.3% of calls without them.
> These are counts and patterns, not effects. To test one event, ask a follow-up such as 'what about escalations?'
> All numbers describe this corpus of calls, not customers in general.

*Dialogue turns cited: `7444e19b-3a95-333d-7440-12dbc66dea42:1`, `7444e19b-3a95-333d-7440-12dbc66dea42:4`*

#### q075 — overview · easy · simple_retrieval · monitoring

**Question:** What is happening in hotel calls?

Expected: answer_overview. Outcome: as expected (the system answered a 'overview' question about None with filters {"industry": ["hospitality"]}).

> In hotel calls (702 calls): escalations in 50.1% (352 calls); refund episodes in 30.9% (217 calls); churn threats in 13.5% (95 calls); retention risks in 17.9% (126 calls).
> The most common moments: the agent offered a concrete solution in 98.3% of calls; the agent expressed empathy in 74.6% of calls; the agent put the customer on hold or asked them to wait in 70.7% of calls; the agent refused a request or cited policy in 67.0% of calls.
> To see what lies behind any of these, ask for example “Why do customers escalate?”, “What drives refunds in hotel calls?” or “What should agents stop doing?”
> All numbers describe this corpus of calls, not customers in general.

#### q078 — retention_risk · medium · multi_hop · root_cause

**Question:** How many retail calls had a retention risk?

Expected: answer (event RISK, type how_often). Outcome: as expected (the system answered a 'how_often' question about RISK with filters {"industry": ["retail_ecommerce"]}).

> In retail calls, 145 of 693 calls (20.9%) had a retention risk (event labeller presence F1 on the gold set: not measured).
> 0.0% of these retention risks started within the opening turns.
> Why, from the conversations: in retail calls, in the turns just before the retention risk the customer usually expressed frustration or anger and the agent often refused a request or cited policy, while the agent offered a concrete solution in only 35.2% of them (against 53.3% at the same point in other calls).
> In the 6 turns before the retention risk, the customer expressed frustration or anger in 67.6% of these calls, against 22.6% at the same point in calls without one.
> All numbers describe this corpus of calls, not customers in general.

#### q079 — single_call · medium · evidence_lookup · root_cause

**Question:** Why did call 716bf356-086b-def7-380b-e16cc2c3bfaa escalate?

Expected: answer_call (event ESC, type call). Outcome: as expected (the system answered a 'call' question about ESC with filters {"call": ["716bf356-086b-def7-380b-e16cc2c3bfaa"]}).

> Call 716bf356-086b-def7-380b-e16cc2c3bfaa is a retail call to Shopnest from 2025-11-04 19:28, with 35 turns.
> Business events detected in this call, in order: a refund episode at turn 5; an escalation at turn 27; a supervisor joining at turn 29.
> The customer's problem (turn 1): “hi i'm calling because my package was not delivered after two weeks and honestly i'm pretty annoyed about it” [716bf356-086b-def7-380b-e16cc2c3bfaa:1]
> Step by step, in the 6 turns before the escalation: turn 25, the customer expressed frustration or anger: “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> Turn 26, the agent refused a request or cited policy: “i understand how frustrating that must be unfortunately per our policy um i'm not able to change that” [716bf356-086b-def7-380b-e16cc2c3bfaa:26]
> Then the escalation (turn 27): “i want to speak to a supervisor right you know now this is ridiculous” [716bf356-086b-def7-380b-e16cc2c3bfaa:27]
> How common these moments are across all calls, in the 6 turns before an escalation: the customer expressed frustration or anger in 77.6% of calls with one (against 5.3% at the same point in calls without one); the customer was confused in 14.0% of calls with one (against 10.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of calls with one (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of calls with one (against 51.5% at the same point in calls without one).
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> This walks through one call from its own turns. The shares and estimates describe calls in general; they are not proof of why this particular call ended in an escalation.

*Factors cited: F2 (L3), F5 (L2), F6 (L2)*
*Dialogue turns cited: `716bf356-086b-def7-380b-e16cc2c3bfaa:1`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `716bf356-086b-def7-380b-e16cc2c3bfaa:26`, `716bf356-086b-def7-380b-e16cc2c3bfaa:27`*

#### q081 — single_call · medium · evidence_lookup · root_cause

**Question:** What happened in call 00000000-0000-0000-0000-000000000000?

Expected: clarify. Outcome: as expected (the system asked to clarify).

> No call with the id '00000000-0000-0000-0000-000000000000' is in the data. The call id is the part before the colon in the brackets after each quote.

#### q054 — noisy_text · medium · robustness · robustness

**Question:** why do custmers escalte so often?

Expected: answer_read (event ESC, type why). Outcome: as expected (the system answered a 'why' question about ESC).

> I read 'custmers' as 'customers'; 'escalte' as 'escalate'.
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

#### q056 — noisy_text · medium · robustness · robustness

**Question:** y do customers want there money bak?

Expected: answer_read (event REF, type why). Outcome: as expected (the system answered a 'why' question about REF).

> I read 'there money bak' as 'money back'.
> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “delivered” (10.1% vs 7.5%); “package” (10.1% vs 7.5%).
> Empathy statements were common before the refund episode too (44.1%), but about as common at the same point in calls without one (49.2%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because my internet has been down since last night and this is completely unacceptable and i would like a refund” [7496fdf8-a677-6179-5005-c1f9e2d3895e:1]
> In the customer's own words: “hi i'm calling because my premium went up at renewal and honestly i'm pretty annoyed about it and i would like a refund” [1c736c49-fe0a-50ce-7247-0000d2c47f9b:1]
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,224 of 4,000 calls (30.6%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> “i understand how frustrating that must be” [00f67d92-72a7-d42e-27a8-d297c7a38d30:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> “alright i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:17]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*
*Dialogue turns cited: `7496fdf8-a677-6179-5005-c1f9e2d3895e:1`, `1c736c49-fe0a-50ce-7247-0000d2c47f9b:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`, `00f67d92-72a7-d42e-27a8-d297c7a38d30:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:17`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q057 — noisy_text · medium · robustness · robustness

**Question:** y do custmrs threten to cancl?

Expected: answer_read (event CHURN, type why). Outcome: as expected (the system answered a 'why' question about CHURN).

> I read 'custmrs' as 'customers'; 'threten' as 'threaten'; 'cancl' as 'cancel'.
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 66.3% of these calls (against 24.9% at the same point in calls without one); the agent refused a request or cited policy in 68.4% of these calls (against 46.2% at the same point in calls without one).
> Empathy statements were common before the churn threat too (64.1%), but about as common at the same point in calls without one (61.1%), so on their own they do not set these calls apart.
> 89.3% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my claim has been under review for three weeks and this is completely unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:1]
> Then the customer expressed frustration or anger: “sure it's pl 6395 751 and please hurry this is unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:3]
> Then the churn threat: “honestly i'm thinking about switching to another provider” [3169e20d-7aaf-aee7-0a70-19178db8442f:5]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Causal test: for churn threats in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a churn threat later in the call by 7.7 percentage points (95% CI -11.6 to -3.8 points) at the moments where they happened [F19].
> Under the same assumptions, that is about 35 fewer churn threats among the held-out calls (95% CI 17 to 53) [F19].
> Solution offers also happened in 701 of 742 held-out calls where no churn threat followed [F19].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay just to confirm that is hx 7964 810 on the file” [4273908c-b138-f619-6f47-c209d47710d2:4]
> “i understand how frustrating that must uh be what i can do is offer you a free replacement with express delivery let me check that for you one moment please” [44104768-b4d3-5de2-34e2-ddc4c77c2905:4]
> Warning sign: policy refusals are associated with a higher chance of a churn threat later in the call (+4.1 percentage points, 95% CI +0.2 to +8.0 points) [F20].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F20].
> “i'm afraid we cannot make an exception here” [73d59436-be13-b2cf-06bd-48568400af72:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a churn threat (+4.7 percentage points, 95% CI -0.3 to +9.7 points) [F21].
> “yes that is correct i'm getting you know really frustrated with this” [43fbf10c-7ee5-caaa-2948-aab62844edd4:15]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a churn threat (+2.9 percentage points, 95% CI -1.4 to +7.1 points) [F22].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the churn threat; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.84 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F19 (L3), F20 (L2), F21 (L2), F22 (L2)*
*Dialogue turns cited: `3169e20d-7aaf-aee7-0a70-19178db8442f:1`, `3169e20d-7aaf-aee7-0a70-19178db8442f:3`, `3169e20d-7aaf-aee7-0a70-19178db8442f:5`, `4273908c-b138-f619-6f47-c209d47710d2:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:4`, `73d59436-be13-b2cf-06bd-48568400af72:4`, `43fbf10c-7ee5-caaa-2948-aab62844edd4:15`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q059 — multilingual · medium · robustness · robustness

**Question:** Pourquoi les clients demandent-ils un remboursement ?

Expected: answer_read (event REF, type why). Outcome: as expected (the system answered a 'why' question about REF).

> The question looks like French; it was read with a small built-in word list as: 'why customers ask for- a refund'. For the most reliable answer, ask in English.
> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “delivered” (10.1% vs 7.5%); “package” (10.1% vs 7.5%).
> Empathy statements were common before the refund episode too (44.1%), but about as common at the same point in calls without one (49.2%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because my internet has been down since last night and this is completely unacceptable and i would like a refund” [7496fdf8-a677-6179-5005-c1f9e2d3895e:1]
> In the customer's own words: “hi i'm calling because my premium went up at renewal and honestly i'm pretty annoyed about it and i would like a refund” [1c736c49-fe0a-50ce-7247-0000d2c47f9b:1]
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,224 of 4,000 calls (30.6%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> “i understand how frustrating that must be” [00f67d92-72a7-d42e-27a8-d297c7a38d30:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> “alright i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:17]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*
*Dialogue turns cited: `7496fdf8-a677-6179-5005-c1f9e2d3895e:1`, `1c736c49-fe0a-50ce-7247-0000d2c47f9b:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`, `00f67d92-72a7-d42e-27a8-d297c7a38d30:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:17`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q060 — multilingual · medium · robustness · robustness

**Question:** Por que os clientes ameaçam cancelar?

Expected: answer_read (event CHURN, type why). Outcome: as expected (the system answered a 'why' question about CHURN).

> The question looks like Portuguese; it was read with a small built-in word list as: 'why customers threaten to cancel'. For the most reliable answer, ask in English.
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 66.3% of these calls (against 24.9% at the same point in calls without one); the agent refused a request or cited policy in 68.4% of these calls (against 46.2% at the same point in calls without one).
> Empathy statements were common before the churn threat too (64.1%), but about as common at the same point in calls without one (61.1%), so on their own they do not set these calls apart.
> 89.3% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my claim has been under review for three weeks and this is completely unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:1]
> Then the customer expressed frustration or anger: “sure it's pl 6395 751 and please hurry this is unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:3]
> Then the churn threat: “honestly i'm thinking about switching to another provider” [3169e20d-7aaf-aee7-0a70-19178db8442f:5]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Causal test: for churn threats in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a churn threat later in the call by 7.7 percentage points (95% CI -11.6 to -3.8 points) at the moments where they happened [F19].
> Under the same assumptions, that is about 35 fewer churn threats among the held-out calls (95% CI 17 to 53) [F19].
> Solution offers also happened in 701 of 742 held-out calls where no churn threat followed [F19].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay just to confirm that is hx 7964 810 on the file” [4273908c-b138-f619-6f47-c209d47710d2:4]
> “i understand how frustrating that must uh be what i can do is offer you a free replacement with express delivery let me check that for you one moment please” [44104768-b4d3-5de2-34e2-ddc4c77c2905:4]
> Warning sign: policy refusals are associated with a higher chance of a churn threat later in the call (+4.1 percentage points, 95% CI +0.2 to +8.0 points) [F20].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F20].
> “i'm afraid we cannot make an exception here” [73d59436-be13-b2cf-06bd-48568400af72:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a churn threat (+4.7 percentage points, 95% CI -0.3 to +9.7 points) [F21].
> “yes that is correct i'm getting you know really frustrated with this” [43fbf10c-7ee5-caaa-2948-aab62844edd4:15]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a churn threat (+2.9 percentage points, 95% CI -1.4 to +7.1 points) [F22].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the churn threat; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.84 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F19 (L3), F20 (L2), F21 (L2), F22 (L2)*
*Dialogue turns cited: `3169e20d-7aaf-aee7-0a70-19178db8442f:1`, `3169e20d-7aaf-aee7-0a70-19178db8442f:3`, `3169e20d-7aaf-aee7-0a70-19178db8442f:5`, `4273908c-b138-f619-6f47-c209d47710d2:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:4`, `73d59436-be13-b2cf-06bd-48568400af72:4`, `43fbf10c-7ee5-caaa-2948-aab62844edd4:15`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q061 — multilingual · medium · robustness · robustness

**Question:** customers cancel karne ki dhamki kyun dete hain?

Expected: answer_read (event CHURN, type why). Outcome: as expected (the system answered a 'why' question about CHURN).

> The question looks like Hindi (romanised); it was read with a small built-in word list as: 'customers cancel karne threaten to why dete'. For the most reliable answer, ask in English.
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 66.3% of these calls (against 24.9% at the same point in calls without one); the agent refused a request or cited policy in 68.4% of these calls (against 46.2% at the same point in calls without one).
> Empathy statements were common before the churn threat too (64.1%), but about as common at the same point in calls without one (61.1%), so on their own they do not set these calls apart.
> 89.3% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my claim has been under review for three weeks and this is completely unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:1]
> Then the customer expressed frustration or anger: “sure it's pl 6395 751 and please hurry this is unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:3]
> Then the churn threat: “honestly i'm thinking about switching to another provider” [3169e20d-7aaf-aee7-0a70-19178db8442f:5]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Causal test: for churn threats in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a churn threat later in the call by 7.7 percentage points (95% CI -11.6 to -3.8 points) at the moments where they happened [F19].
> Under the same assumptions, that is about 35 fewer churn threats among the held-out calls (95% CI 17 to 53) [F19].
> Solution offers also happened in 701 of 742 held-out calls where no churn threat followed [F19].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay just to confirm that is hx 7964 810 on the file” [4273908c-b138-f619-6f47-c209d47710d2:4]
> “i understand how frustrating that must uh be what i can do is offer you a free replacement with express delivery let me check that for you one moment please” [44104768-b4d3-5de2-34e2-ddc4c77c2905:4]
> Warning sign: policy refusals are associated with a higher chance of a churn threat later in the call (+4.1 percentage points, 95% CI +0.2 to +8.0 points) [F20].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F20].
> “i'm afraid we cannot make an exception here” [73d59436-be13-b2cf-06bd-48568400af72:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a churn threat (+4.7 percentage points, 95% CI -0.3 to +9.7 points) [F21].
> “yes that is correct i'm getting you know really frustrated with this” [43fbf10c-7ee5-caaa-2948-aab62844edd4:15]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a churn threat (+2.9 percentage points, 95% CI -1.4 to +7.1 points) [F22].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the churn threat; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.84 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F19 (L3), F20 (L2), F21 (L2), F22 (L2)*
*Dialogue turns cited: `3169e20d-7aaf-aee7-0a70-19178db8442f:1`, `3169e20d-7aaf-aee7-0a70-19178db8442f:3`, `3169e20d-7aaf-aee7-0a70-19178db8442f:5`, `4273908c-b138-f619-6f47-c209d47710d2:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:4`, `73d59436-be13-b2cf-06bd-48568400af72:4`, `43fbf10c-7ee5-caaa-2948-aab62844edd4:15`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q062 — multilingual · medium · robustness · robustness

**Question:** ग्राहक रिफंड क्यों मांगते हैं?

Expected: answer_read (event REF, type why). Outcome: as expected (the system answered a 'why' question about REF).

> The question looks like Hindi; it was read with a small built-in word list as: 'customers a refund why ask for'. For the most reliable answer, ask in English.
> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “delivered” (10.1% vs 7.5%); “package” (10.1% vs 7.5%).
> Empathy statements were common before the refund episode too (44.1%), but about as common at the same point in calls without one (49.2%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because my internet has been down since last night and this is completely unacceptable and i would like a refund” [7496fdf8-a677-6179-5005-c1f9e2d3895e:1]
> In the customer's own words: “hi i'm calling because my premium went up at renewal and honestly i'm pretty annoyed about it and i would like a refund” [1c736c49-fe0a-50ce-7247-0000d2c47f9b:1]
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,224 of 4,000 calls (30.6%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> “i understand how frustrating that must be” [00f67d92-72a7-d42e-27a8-d297c7a38d30:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> “alright i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:17]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*
*Dialogue turns cited: `7496fdf8-a677-6179-5005-c1f9e2d3895e:1`, `1c736c49-fe0a-50ce-7247-0000d2c47f9b:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`, `00f67d92-72a7-d42e-27a8-d297c7a38d30:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:17`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q022 — true_premise · medium · premise_check · hypothesis_test

**Question:** Why do solution offers reduce refund requests?

Expected: correct_premise (event REF). Outcome: as expected (the system answered a 'why' question about REF).

> The data supports a limited version of this premise: under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call (-15.9 percentage points, 95% CI -22.0 to -9.9 points) [F10].
> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “delivered” (10.1% vs 7.5%); “package” (10.1% vs 7.5%).
> Empathy statements were common before the refund episode too (44.1%), but about as common at the same point in calls without one (49.2%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because my internet has been down since last night and this is completely unacceptable and i would like a refund” [7496fdf8-a677-6179-5005-c1f9e2d3895e:1]
> In the customer's own words: “hi i'm calling because my premium went up at renewal and honestly i'm pretty annoyed about it and i would like a refund” [1c736c49-fe0a-50ce-7247-0000d2c47f9b:1]
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,224 of 4,000 calls (30.6%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> “i understand how frustrating that must be” [00f67d92-72a7-d42e-27a8-d297c7a38d30:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> “alright i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:17]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*
*Dialogue turns cited: `7496fdf8-a677-6179-5005-c1f9e2d3895e:1`, `1c736c49-fe0a-50ce-7247-0000d2c47f9b:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`, `00f67d92-72a7-d42e-27a8-d297c7a38d30:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:17`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q035 — true_premise · medium · premise_check · hypothesis_test

**Question:** Why do solution offers reduce churn threats?

Expected: correct_premise (event CHURN). Outcome: as expected (the system answered a 'why' question about CHURN).

> The data supports a limited version of this premise: under the stated assumptions, solution offers are estimated to lower the chance of a churn threat later in the call (-7.7 percentage points, 95% CI -11.6 to -3.8 points) [F19].
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 66.3% of these calls (against 24.9% at the same point in calls without one); the agent refused a request or cited policy in 68.4% of these calls (against 46.2% at the same point in calls without one).
> Empathy statements were common before the churn threat too (64.1%), but about as common at the same point in calls without one (61.1%), so on their own they do not set these calls apart.
> 89.3% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my claim has been under review for three weeks and this is completely unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:1]
> Then the customer expressed frustration or anger: “sure it's pl 6395 751 and please hurry this is unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:3]
> Then the churn threat: “honestly i'm thinking about switching to another provider” [3169e20d-7aaf-aee7-0a70-19178db8442f:5]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Causal test: for churn threats in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a churn threat later in the call by 7.7 percentage points (95% CI -11.6 to -3.8 points) at the moments where they happened [F19].
> Under the same assumptions, that is about 35 fewer churn threats among the held-out calls (95% CI 17 to 53) [F19].
> Solution offers also happened in 701 of 742 held-out calls where no churn threat followed [F19].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay just to confirm that is hx 7964 810 on the file” [4273908c-b138-f619-6f47-c209d47710d2:4]
> “i understand how frustrating that must uh be what i can do is offer you a free replacement with express delivery let me check that for you one moment please” [44104768-b4d3-5de2-34e2-ddc4c77c2905:4]
> Warning sign: policy refusals are associated with a higher chance of a churn threat later in the call (+4.1 percentage points, 95% CI +0.2 to +8.0 points) [F20].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F20].
> “i'm afraid we cannot make an exception here” [73d59436-be13-b2cf-06bd-48568400af72:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a churn threat (+4.7 percentage points, 95% CI -0.3 to +9.7 points) [F21].
> “yes that is correct i'm getting you know really frustrated with this” [43fbf10c-7ee5-caaa-2948-aab62844edd4:15]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a churn threat (+2.9 percentage points, 95% CI -1.4 to +7.1 points) [F22].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the churn threat; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.84 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F19 (L3), F20 (L2), F21 (L2), F22 (L2)*
*Dialogue turns cited: `3169e20d-7aaf-aee7-0a70-19178db8442f:1`, `3169e20d-7aaf-aee7-0a70-19178db8442f:3`, `3169e20d-7aaf-aee7-0a70-19178db8442f:5`, `4273908c-b138-f619-6f47-c209d47710d2:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:4`, `73d59436-be13-b2cf-06bd-48568400af72:4`, `43fbf10c-7ee5-caaa-2948-aab62844edd4:15`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q010 — false_presupposition · hard · premise_check · guardrail

**Question:** Why do solution offers increase escalations?

Expected: correct_premise (event ESC). Outcome: as expected (the system answered a 'why' question about ESC).

> The data does not support this premise: solution offers are associated with a lower chance of an escalation, the opposite direction (-31.5 percentage points, 95% CI -37.8 to -25.2 points) [F1].
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

#### q023 — false_presupposition · hard · premise_check · guardrail

**Question:** Why do solution offers increase refund requests?

Expected: correct_premise (event REF). Outcome: as expected (the system answered a 'why' question about REF).

> The data does not support this premise: solution offers are associated with a lower chance of a refund episode, the opposite direction (-15.9 percentage points, 95% CI -22.0 to -9.9 points) [F10].
> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “delivered” (10.1% vs 7.5%); “package” (10.1% vs 7.5%).
> Empathy statements were common before the refund episode too (44.1%), but about as common at the same point in calls without one (49.2%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because my internet has been down since last night and this is completely unacceptable and i would like a refund” [7496fdf8-a677-6179-5005-c1f9e2d3895e:1]
> In the customer's own words: “hi i'm calling because my premium went up at renewal and honestly i'm pretty annoyed about it and i would like a refund” [1c736c49-fe0a-50ce-7247-0000d2c47f9b:1]
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,224 of 4,000 calls (30.6%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> “i understand how frustrating that must be” [00f67d92-72a7-d42e-27a8-d297c7a38d30:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> “alright i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:17]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*
*Dialogue turns cited: `7496fdf8-a677-6179-5005-c1f9e2d3895e:1`, `1c736c49-fe0a-50ce-7247-0000d2c47f9b:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`, `00f67d92-72a7-d42e-27a8-d297c7a38d30:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:17`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q036 — false_presupposition · hard · premise_check · guardrail

**Question:** Why do solution offers increase churn threats?

Expected: correct_premise (event CHURN). Outcome: as expected (the system answered a 'why' question about CHURN).

> The data does not support this premise: solution offers are associated with a lower chance of a churn threat, the opposite direction (-7.7 percentage points, 95% CI -11.6 to -3.8 points) [F19].
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 66.3% of these calls (against 24.9% at the same point in calls without one); the agent refused a request or cited policy in 68.4% of these calls (against 46.2% at the same point in calls without one).
> Empathy statements were common before the churn threat too (64.1%), but about as common at the same point in calls without one (61.1%), so on their own they do not set these calls apart.
> 89.3% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my claim has been under review for three weeks and this is completely unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:1]
> Then the customer expressed frustration or anger: “sure it's pl 6395 751 and please hurry this is unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:3]
> Then the churn threat: “honestly i'm thinking about switching to another provider” [3169e20d-7aaf-aee7-0a70-19178db8442f:5]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Causal test: for churn threats in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a churn threat later in the call by 7.7 percentage points (95% CI -11.6 to -3.8 points) at the moments where they happened [F19].
> Under the same assumptions, that is about 35 fewer churn threats among the held-out calls (95% CI 17 to 53) [F19].
> Solution offers also happened in 701 of 742 held-out calls where no churn threat followed [F19].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay just to confirm that is hx 7964 810 on the file” [4273908c-b138-f619-6f47-c209d47710d2:4]
> “i understand how frustrating that must uh be what i can do is offer you a free replacement with express delivery let me check that for you one moment please” [44104768-b4d3-5de2-34e2-ddc4c77c2905:4]
> Warning sign: policy refusals are associated with a higher chance of a churn threat later in the call (+4.1 percentage points, 95% CI +0.2 to +8.0 points) [F20].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F20].
> “i'm afraid we cannot make an exception here” [73d59436-be13-b2cf-06bd-48568400af72:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a churn threat (+4.7 percentage points, 95% CI -0.3 to +9.7 points) [F21].
> “yes that is correct i'm getting you know really frustrated with this” [43fbf10c-7ee5-caaa-2948-aab62844edd4:15]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a churn threat (+2.9 percentage points, 95% CI -1.4 to +7.1 points) [F22].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the churn threat; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.84 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F19 (L3), F20 (L2), F21 (L2), F22 (L2)*
*Dialogue turns cited: `3169e20d-7aaf-aee7-0a70-19178db8442f:1`, `3169e20d-7aaf-aee7-0a70-19178db8442f:3`, `3169e20d-7aaf-aee7-0a70-19178db8442f:5`, `4273908c-b138-f619-6f47-c209d47710d2:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:4`, `73d59436-be13-b2cf-06bd-48568400af72:4`, `43fbf10c-7ee5-caaa-2948-aab62844edd4:15`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q024 — leading · hard · premise_check · guardrail

**Question:** Isn't it true that customer confusion causes refund requests?

Expected: correct_premise (event REF). Outcome: as expected (the system answered a 'effect_of' question about REF).

> The data does not support this premise: for customer confusion, the estimated difference is compatible with no difference at all (95% CI -4.7 to +13.3 points) [F15].
> From the conversations: in the 6 turns before a refund episode, the customer was confused in 8.0% of these calls, against 13.7% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because my internet has been down since last night and honestly i'm pretty annoyed about it” [578be422-0c68-b893-7341-5bb1f94d65ab:1]
> Then the customer was confused: “sure no problem sorry i don't understand what you mean” [578be422-0c68-b893-7341-5bb1f94d65ab:7]
> Then the refund episode: “i would like a refund for this another company offered me a better deal” [578be422-0c68-b893-7341-5bb1f94d65ab:11]
> No clear difference: for customer confusion the estimate is compatible with no difference in the chance of a refund episode (+4.3 percentage points, 95% CI -4.7 to +13.3 points) [F15].
> Customer confusion also happened in 82 of 111 held-out calls where no refund episode followed [F15].
> “sure no problem sorry i don't understand what you mean” [62c655c0-088b-a466-6a86-9a46322b4c4a:5]
> “i see this is ridiculous sorry i don't understand what you mean” [66c66288-a649-35bc-0242-6c0d12e516b6:9]
> In the risk forecaster, removing such a turn moves the forecast more than removing 60% of the same speaker's other turns (a check of the model, not proof of what happened) [F15].
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F15 (L2)*
*Dialogue turns cited: `578be422-0c68-b893-7341-5bb1f94d65ab:1`, `578be422-0c68-b893-7341-5bb1f94d65ab:7`, `578be422-0c68-b893-7341-5bb1f94d65ab:11`, `62c655c0-088b-a466-6a86-9a46322b4c4a:5`, `66c66288-a649-35bc-0242-6c0d12e516b6:9`*

#### q013 — unanswerable · hard · cannot_answer · guardrail

**Question:** Why do customers on the premium plan escalate?

Expected: refuse_part (event ESC). Outcome: as expected (the system answered a 'why' question about ESC; notices: plan or segment).

> The data has no plan or customer-segment field ('premium plan'), so that part of the question cannot be answered; the answer below covers all customers. An account_attributes.csv with a plan or segment column (see the README) makes this filter available.
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

#### q025 — unanswerable · hard · cannot_answer · guardrail

**Question:** Do older customers ask for refunds more than young ones?

Expected: refuse_part (event REF). Outcome: as expected (the system answered a 'why' question about REF; notices: demographics).

> The data has no age or other demographic fields ('young'), so that comparison cannot be made; the answer below covers all customers.
> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “delivered” (10.1% vs 7.5%); “package” (10.1% vs 7.5%).
> Empathy statements were common before the refund episode too (44.1%), but about as common at the same point in calls without one (49.2%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because my internet has been down since last night and this is completely unacceptable and i would like a refund” [7496fdf8-a677-6179-5005-c1f9e2d3895e:1]
> In the customer's own words: “hi i'm calling because my premium went up at renewal and honestly i'm pretty annoyed about it and i would like a refund” [1c736c49-fe0a-50ce-7247-0000d2c47f9b:1]
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,224 of 4,000 calls (30.6%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> “i understand how frustrating that must be” [00f67d92-72a7-d42e-27a8-d297c7a38d30:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> “alright i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:17]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*
*Dialogue turns cited: `7496fdf8-a677-6179-5005-c1f9e2d3895e:1`, `1c736c49-fe0a-50ce-7247-0000d2c47f9b:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`, `00f67d92-72a7-d42e-27a8-d297c7a38d30:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:17`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q038 — unanswerable · hard · cannot_answer · guardrail

**Question:** Do new customers threaten to leave more?

Expected: refuse_part (event CHURN). Outcome: as expected (the system answered a 'why' question about CHURN; notices: account age).

> The data has no account-age (tenure) field ('new customers'). Where customers say they are long-time, loyal or member customers, that is used below as the nearest proxy.
> No customer mentions a membership, a loyalty status or a long tenure before the point where churn threats start, so there is no proxy for customer tier in these calls either.
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 66.3% of these calls (against 24.9% at the same point in calls without one); the agent refused a request or cited policy in 68.4% of these calls (against 46.2% at the same point in calls without one).
> Empathy statements were common before the churn threat too (64.1%), but about as common at the same point in calls without one (61.1%), so on their own they do not set these calls apart.
> 89.3% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my claim has been under review for three weeks and this is completely unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:1]
> Then the customer expressed frustration or anger: “sure it's pl 6395 751 and please hurry this is unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:3]
> Then the churn threat: “honestly i'm thinking about switching to another provider” [3169e20d-7aaf-aee7-0a70-19178db8442f:5]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Causal test: for churn threats in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a churn threat later in the call by 7.7 percentage points (95% CI -11.6 to -3.8 points) at the moments where they happened [F19].
> Under the same assumptions, that is about 35 fewer churn threats among the held-out calls (95% CI 17 to 53) [F19].
> Solution offers also happened in 701 of 742 held-out calls where no churn threat followed [F19].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay just to confirm that is hx 7964 810 on the file” [4273908c-b138-f619-6f47-c209d47710d2:4]
> “i understand how frustrating that must uh be what i can do is offer you a free replacement with express delivery let me check that for you one moment please” [44104768-b4d3-5de2-34e2-ddc4c77c2905:4]
> Warning sign: policy refusals are associated with a higher chance of a churn threat later in the call (+4.1 percentage points, 95% CI +0.2 to +8.0 points) [F20].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F20].
> “i'm afraid we cannot make an exception here” [73d59436-be13-b2cf-06bd-48568400af72:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a churn threat (+4.7 percentage points, 95% CI -0.3 to +9.7 points) [F21].
> “yes that is correct i'm getting you know really frustrated with this” [43fbf10c-7ee5-caaa-2948-aab62844edd4:15]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a churn threat (+2.9 percentage points, 95% CI -1.4 to +7.1 points) [F22].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the churn threat; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.84 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F19 (L3), F20 (L2), F21 (L2), F22 (L2)*
*Dialogue turns cited: `3169e20d-7aaf-aee7-0a70-19178db8442f:1`, `3169e20d-7aaf-aee7-0a70-19178db8442f:3`, `3169e20d-7aaf-aee7-0a70-19178db8442f:5`, `4273908c-b138-f619-6f47-c209d47710d2:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:4`, `73d59436-be13-b2cf-06bd-48568400af72:4`, `43fbf10c-7ee5-caaa-2948-aab62844edd4:15`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q048 — out_of_scope · medium · cannot_answer · guardrail

**Question:** Does the customer's tone of voice predict escalations?

Expected: refuse_part (event ESC). Outcome: as expected (the system answered a 'why' question about ESC; notices: audio).

> The transcripts are text only, so tone of voice and other audio cues ('tone of voice') cannot be analysed.
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

#### q049 — out_of_scope · medium · cannot_answer · guardrail

**Question:** How long are customers kept on hold before they escalate?

Expected: refuse_part (event ESC). Outcome: as expected (the system answered a 'effect_of' question about ESC; notices: call duration).

> The transcripts carry no timing information (no durations or timestamps inside calls), so that part of the question ('how long') cannot be answered.
> From the conversations: in the 6 turns before an escalation, the agent put the customer on hold or asked them to wait in 37.2% of these calls, against 26.9% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make” [6abb1234-07ec-f5d1-63eb-0d18693ba21c:1]
> Then the agent put the customer on hold or asked them to wait: “let me check that for you one moment please um thank you for that information” [6abb1234-07ec-f5d1-63eb-0d18693ba21c:14]
> Then the escalation: “i want you know to speak to a supervisor right now” [6abb1234-07ec-f5d1-63eb-0d18693ba21c:15]
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 1.70 with both to explain the estimates away (E-values).
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F3 (L3)*
*Dialogue turns cited: `6abb1234-07ec-f5d1-63eb-0d18693ba21c:1`, `6abb1234-07ec-f5d1-63eb-0d18693ba21c:14`, `6abb1234-07ec-f5d1-63eb-0d18693ba21c:15`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`*

#### q050 — out_of_scope · medium · cannot_answer · guardrail

**Question:** What would happen to refund requests if agents never refused anything?

Expected: refuse_part (event REF). Outcome: as expected (the system answered a 'effect_of' question about REF; notices: whole-call policy).

> Effects are estimated for single moments in a call, not for a rule applied to every call ('if agents never refused anything'), so the answer below covers that narrower question.
> From the conversations: in the 6 turns before a refund episode, the agent refused a request or cited policy in 39.5% of these calls, against 36.1% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the agent refused a request or cited policy: “unfortunately per our policy i'm not able to change that what i can do is offer you a loyalty discount at renewal just to confirm that is pl 4540 579 on the file” [0c3a65d0-50a4-5319-7dd9-73df32594123:12]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> No clear difference: for policy refusals the estimate is compatible with no difference in the chance of a refund episode (+2.2 percentage points, 95% CI -3.0 to +7.4 points) [F14].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F14].
> Policy refusals also happened in 311 of 421 held-out calls where no refund episode followed [F14].
> “i'm afraid we cannot make an exception here” [201dbd83-31e7-378c-79a6-dc1b26e079e7:4]
> “i'm afraid we you know cannot make an exception here” [3ec2fea5-844c-f333-5195-0a8e32d55f2e:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 75% of the same speaker's other turns (a check of the model, not proof of what happened) [F14].
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F14 (L2)*
*Dialogue turns cited: `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:12`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `201dbd83-31e7-378c-79a6-dc1b26e079e7:4`, `3ec2fea5-844c-f333-5195-0a8e32d55f2e:4`*

#### q051 — out_of_scope · medium · cannot_answer · guardrail

**Question:** Do escalations lead to refund requests?

Expected: answer_event_link (event ESC, type event_link). Outcome: as expected (the system answered a 'event_link' question about ESC; notices: effects between events).

> Effects of one event on another are not estimated (only behaviours inside the call are studied as possible drivers), so the counts below only show how often escalations and refund episodes occur in the same calls and which one started first.
> In all calls, 1,865 of 4,000 calls had an escalation, 1,224 had a refund episode and 717 had both.
> When both happened, the escalation started first in 81 calls, the refund episode started first in 636, and both started in the same turn in 0.
> A refund episode occurred in 38.4% of calls with an escalation and in 23.7% of calls without one.
> Why, from the conversations: in calls with an escalation, before the refund episode the agent put the customer on hold or asked them to wait in only 24.4% of them (against 44.1% at the same point in other calls).
> In the customer's own words: “hi i'm calling because the room type was not what i reserved and this is completely unacceptable and i would like a refund” [076458f8-31c6-1fc9-4bd1-08d7dced55dd:1]
> In the customer's own words: “hi i'm calling because i was charged an overdraft fee i do not understand and this is completely unacceptable and i would like a refund” [1c586ca7-bc3e-ec0e-6931-1650b4fa4371:1]
> One call with both, step by step: the customer's problem: “hi i'm calling because the wifi keeps dropping every few minutes” [1a21769c-1e8b-b3c3-39d7-c139e21a9b8a:1]
> Then the escalation: “get me someone above you right now” [1a21769c-1e8b-b3c3-39d7-c139e21a9b8a:11]
> Then the refund episode: “i would like a refund for this this is ridiculous” [1a21769c-1e8b-b3c3-39d7-c139e21a9b8a:19]
> These counts show how often the two events occur together and in which order, not whether one event makes the other more likely.
> All numbers describe this corpus of calls, not customers in general.

*Dialogue turns cited: `076458f8-31c6-1fc9-4bd1-08d7dced55dd:1`, `1c586ca7-bc3e-ec0e-6931-1650b4fa4371:1`, `1a21769c-1e8b-b3c3-39d7-c139e21a9b8a:1`, `1a21769c-1e8b-b3c3-39d7-c139e21a9b8a:11`, `1a21769c-1e8b-b3c3-39d7-c139e21a9b8a:19`*

#### q053 — out_of_scope · medium · cannot_answer · guardrail

**Question:** What is the weather in London?

Expected: clarify. Outcome: as expected (the system asked to clarify; notices: location).

> The data has no information on location ('london'), so that part of the question cannot be answered.
> Which business event do you mean: escalations, refunds or churn threats?

#### q014 — unsupported_filter · hard · cannot_answer · guardrail

**Question:** Why do calls whose reason for call mentions billing lead to escalations?

Expected: decline_filter (event ESC). Outcome: as expected (the system answered a 'why' question about ESC).

> The filter on reason for call was not applied: free-text reasons may be written after the call and can contain the outcome. Instead: industry from the opening turns, or the words customers use in the opening.
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

#### q026 — tiny_subgroup · hard · cannot_answer · guardrail

**Question:** What drives refund requests for Northstar Airways calls in insurance calls?

Expected: answer_with_support_notice (event REF, type why). Outcome: as expected (the system answered a 'why' question about REF with filters {"industry": ["insurance"], "brand": ["northstar airways"]}).

> Why: there are too few refund episodes in insurance calls, calls to Northstar Airways (0 calls) to describe a typical pattern from the conversations.
> In insurance calls, calls to Northstar Airways, 0 of 0 calls (n/a) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Estimates for insurance calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Effects are estimated per industry only; the other filters apply to the counts.
> For insurance calls alone no behaviour has a usable estimate; the factors below are for all calls (the nearest supported slice).
> Causal test: for refund episodes in insurance calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*

#### q042 — ambiguous · hard · ambiguous · guardrail

**Question:** What about it?

Expected: clarify. Outcome: as expected (the system asked to clarify).

> Could you clarify: which business event (escalation, refund or churn) is the question about?

#### q043 — ambiguous · hard · ambiguous · guardrail

**Question:** Show me the numbers

Expected: clarify. Outcome: as expected (the system asked to clarify).

> Could you clarify: which business event (escalation, refund or churn) is the question about?

#### q082 — known_limitation · hard · known_limitation · stress_test

**Question:** Kwa nini wateja wanaomba msimamizi?

Expected: answer (event ESC, type why). Outcome: **known limitation** — languages outside the built-in word lists (here Swahili) are read only when an LLM is configured; without one the system asks the user to rephrase (the system asked to clarify).

> Could you clarify: which business event (escalation, refund or churn) is the question about?

#### q083 — known_limitation · hard · known_limitation · stress_test

**Question:** Does empathy reduce escalations only when the customer is already frustrated?

Expected: estimate_modification (event ESC). Outcome: **known limitation** — effects are estimated over all comparable moments together; an effect within calls where something else already happened (effect modification) is not estimated, so the overall estimate is given with a notice (the system answered a 'effect_of' question about ESC; notices: effect modification).

> Effects are estimated over all comparable moments together, not separately for calls where something else had already happened ('only when the customer is already frustrated'), so whether the effect is different there (effect modification) is not estimated. The answer below gives the overall estimate.
> From the conversations: in the 6 turns before an escalation, the agent expressed empathy in 73.3% of these calls, against 51.5% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because my room was double booked for the weekend” [089320a6-bbf4-07ad-3210-3c8675a96a21:1]
> Then the agent expressed empathy: “i understand how frustrating that must be i'm afraid we cannot make an exception here” [089320a6-bbf4-07ad-3210-3c8675a96a21:6]
> Then the escalation: “i want to speak to a supervisor right now i'm getting really frustrated with this” [089320a6-bbf4-07ad-3210-3c8675a96a21:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> Empathy statements often happen in the same calls as repeated questions, read-backs, policy refusals; their estimated effects are not independent and do not add up [F6].
> Empathy statements also happened in 276 of 583 held-out calls where no escalation followed [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> “i understand how frustrating that must be just to confirm that you know is uh hx 1755 148 on the file” [647b1288-45e1-c67c-47e8-f5ba87bfc84a:6]
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F6 (L2)*
*Dialogue turns cited: `089320a6-bbf4-07ad-3210-3c8675a96a21:1`, `089320a6-bbf4-07ad-3210-3c8675a96a21:6`, `089320a6-bbf4-07ad-3210-3c8675a96a21:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`, `647b1288-45e1-c67c-47e8-f5ba87bfc84a:6`*

#### q085 — known_limitation · hard · known_limitation · stress_test

**Question:** If agents had offered a solution earlier in this call, would the customer still have escalated?

Expected: answer_counterfactual (event ESC). Outcome: **known limitation** — counterfactuals about one specific call are not estimated: estimates describe calls in general, and one call's outcome under a different agent action is not identifiable from the data (the system answered a 'effect_of' question about ESC; notices: single-call counterfactual).

> Whether one particular call would have gone differently with another agent action ('if agents had offered a solution earlier in this call') cannot be estimated from the data; the estimate below is for comparable moments across calls.
> From the conversations: in the 6 turns before an escalation, the agent offered a concrete solution in 27.3% of these calls, against 68.7% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because i was charged an overdraft fee i do not understand” [1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:1]
> Then the agent offered a concrete solution: “what i can do is uh offer you a waiver of the late fee let me check that for you one moment please just to confirm that is ending 2846 on the file” [1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:14]
> Then the escalation: “get me someone above you right now” [1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:15]
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41 with both to explain the estimates away (E-values).
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3)*
*Dialogue turns cited: `1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:1`, `1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:14`, `1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:15`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`*

### Task 2: follow-up questions in context

#### s02 — follow-up session · hard · follow_up · follow_up

**Turn 1:** How often do customers threaten to cancel?

Expected: route `first`, event CHURN, industries all. Got: route `first`, event CHURN, industries all — as expected.

> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Corrected for labeller errors with the blind gold sample, the held-out rate is 13.3% (95% CI 13.3% to 13.3%).
> 0.0% of these churn threats started within the opening turns.
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> In the 6 turns before the churn threat, the customer expressed frustration or anger in 66.3% of these calls, against 24.9% at the same point in calls without one.
> All numbers describe this corpus of calls, not customers in general.

**Turn 2:** only retail calls

Expected: route `refilter`, event CHURN, industries ['retail_ecommerce']. Got: route `refilter`, event CHURN, industries ['retail_ecommerce'] — as expected.

> In retail calls, 112 of 693 calls (16.2%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> 0.0% of these churn threats started within the opening turns.
> Why, from the conversations: in retail calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 28.6% of them (against 53.0% at the same point in other calls).
> In the 6 turns before the churn threat, the customer expressed frustration or anger in 67.9% of these calls, against 23.8% at the same point in calls without one.
> All numbers describe this corpus of calls, not customers in general.

**Turn 3:** why?

Expected: route `new_lookup`, event CHURN, industries ['retail_ecommerce']. Got: route `new_lookup`, event CHURN, industries ['retail_ecommerce'] — as expected.

> Why, from the conversations: in retail calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 28.6% of them (against 53.0% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 67.9% of these calls (against 23.8% at the same point in calls without one); the agent refused a request or cited policy in 61.6% of these calls (against 41.8% at the same point in calls without one).
> Empathy statements were common before the churn threat too (64.3%), but about as common at the same point in calls without one (62.0%), so on their own they do not set these calls apart.
> 89.3% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my package was not delivered after two weeks and honestly i'm pretty annoyed about it” [7837e57f-77d9-4640-6ca5-0b880933b623:1]
> Then the customer expressed frustration or anger: “i see i'm getting really frustrated with this” [7837e57f-77d9-4640-6ca5-0b880933b623:15]
> Then the churn threat: “uh honestly i'm thinking about switching to another uh provider” [7837e57f-77d9-4640-6ca5-0b880933b623:19]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In retail calls, 112 of 693 calls (16.2%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Estimates for retail calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for churn threats in retail calls; the behaviours below are warning signs only.
> No clear difference: for policy refusals the estimate is compatible with no difference in the chance of a churn threat (+4.7 percentage points, 95% CI -5.7 to +15.0 points) [F167].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F167].
> Policy refusals also happened in 414 of 493 held-out calls where no churn threat followed [F167].
> “i'm afraid we cannot make an exception here” [48089445-f363-4154-0cb0-ab3492c4c094:10]
> “uh unfortunately per our policy i'm not able to change that” [5c9d801a-b66f-0966-075c-812fdcbe5ddc:16]
> In the risk forecaster, removing such a turn moves the forecast more than removing 79% of the same speaker's other turns (a check of the model, not proof of what happened) [F167].
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F167 (L2)*
*Dialogue turns cited: `7837e57f-77d9-4640-6ca5-0b880933b623:1`, `7837e57f-77d9-4640-6ca5-0b880933b623:15`, `7837e57f-77d9-4640-6ca5-0b880933b623:19`, `48089445-f363-4154-0cb0-ab3492c4c094:10`, `5c9d801a-b66f-0966-075c-812fdcbe5ddc:16`*

**Turn 4:** why?

Expected: route `reuse`, event CHURN, industries ['retail_ecommerce']. Got: route `reuse`, event CHURN, industries ['retail_ecommerce'] — as expected.

> Why, from the conversations: in retail calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 28.6% of them (against 53.0% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 67.9% of these calls (against 23.8% at the same point in calls without one); the agent refused a request or cited policy in 61.6% of these calls (against 41.8% at the same point in calls without one).
> Empathy statements were common before the churn threat too (64.3%), but about as common at the same point in calls without one (62.0%), so on their own they do not set these calls apart.
> 89.3% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my package was not delivered after two weeks and honestly i'm pretty annoyed about it” [7837e57f-77d9-4640-6ca5-0b880933b623:1]
> Then the customer expressed frustration or anger: “i see i'm getting really frustrated with this” [7837e57f-77d9-4640-6ca5-0b880933b623:15]
> Then the churn threat: “uh honestly i'm thinking about switching to another uh provider” [7837e57f-77d9-4640-6ca5-0b880933b623:19]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In retail calls, 112 of 693 calls (16.2%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Estimates for retail calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for churn threats in retail calls; the behaviours below are warning signs only.
> No clear difference: for policy refusals the estimate is compatible with no difference in the chance of a churn threat (+4.7 percentage points, 95% CI -5.7 to +15.0 points) [F167].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F167].
> Policy refusals also happened in 414 of 493 held-out calls where no churn threat followed [F167].
> “i'm afraid we cannot make an exception here” [48089445-f363-4154-0cb0-ab3492c4c094:10]
> “uh unfortunately per our policy i'm not able to change that” [5c9d801a-b66f-0966-075c-812fdcbe5ddc:16]
> In the risk forecaster, removing such a turn moves the forecast more than removing 79% of the same speaker's other turns (a check of the model, not proof of what happened) [F167].
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F167 (L2)*
*Dialogue turns cited: `7837e57f-77d9-4640-6ca5-0b880933b623:1`, `7837e57f-77d9-4640-6ca5-0b880933b623:15`, `7837e57f-77d9-4640-6ca5-0b880933b623:19`, `48089445-f363-4154-0cb0-ab3492c4c094:10`, `5c9d801a-b66f-0966-075c-812fdcbe5ddc:16`*

**Turn 5:** what about escalations?

Expected: route `new_lookup`, event ESC, industries ['retail_ecommerce']. Got: route `new_lookup`, event ESC, industries ['retail_ecommerce'] — as expected.

> Why, from the conversations: in retail calls, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 31.8% of them (against 66.8% at the same point in other calls).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.7% of these calls (against 8.0% at the same point in calls without one); the agent refused a request or cited policy in 88.0% of these calls (against 21.7% at the same point in calls without one); the agent expressed empathy in 77.7% of these calls (against 51.1% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because my package was not delivered after two weeks and honestly i'm pretty annoyed about it” [17a874b5-406a-66b3-6438-3bd1bcc535c5:1]
> Then the customer expressed frustration or anger: “sure no problem another company offered me a better deal i'm getting really frustrated with this” [17a874b5-406a-66b3-6438-3bd1bcc535c5:21]
> Then the escalation: “i want to speak to a supervisor right now i'm getting really frustrated with uh this” [17a874b5-406a-66b3-6438-3bd1bcc535c5:23]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In retail calls, 292 of 693 calls (42.1%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Estimates for retail calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for escalations in retail calls; the behaviours below are warning signs only.
> Warning sign: policy refusals are associated with a higher chance of an escalation later in the call (+33.6 percentage points, 95% CI +19.3 to +47.9 points) [F63].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); support is not 'sufficient' (events per arm, overlap, CI width or balance); the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F63].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F63].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F63].
> “i'm afraid we cannot um make an exception here let me check that for you one moment please” [68d7d342-33d3-1bf1-72c0-5d8391b2fef3:8]
> “i'm afraid we cannot make you know an exception here just to confirm you know that is sn 8943 821 on the file” [563ba482-b14a-405d-5ddf-404a6b55b41a:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F63].
> Warning sign: solution offers are associated with a lower chance of an escalation later in the call (-16.9 percentage points, 95% CI -33.7 to -0.2 points) [F64].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); not significant after the Benjamini-Hochberg correction over the pre-registered family [F64].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of an escalation (+13.6 percentage points, 95% CI -1.5 to +28.7 points) [F65].
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [70cdaee5-756d-1a2a-3334-7c73e4b647b7:6]
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F63 (L2), F64 (L2), F65 (L2)*
*Dialogue turns cited: `17a874b5-406a-66b3-6438-3bd1bcc535c5:1`, `17a874b5-406a-66b3-6438-3bd1bcc535c5:21`, `17a874b5-406a-66b3-6438-3bd1bcc535c5:23`, `68d7d342-33d3-1bf1-72c0-5d8391b2fef3:8`, `563ba482-b14a-405d-5ddf-404a6b55b41a:4`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `70cdaee5-756d-1a2a-3334-7c73e4b647b7:6`*

#### s04 — follow-up session · medium · follow_up · follow_up

**Turn 1:** How can we reduce escalations?

Expected: route `first`, event ESC, industries all. Got: route `first`, event ESC, industries all — as expected.

> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> What could change: at comparable moments, doing more of this is estimated to lower the chance of an escalation by up to 31.5 percentage points, under the stated assumptions [F1].
> What could change: at comparable moments, doing less of this is estimated to lower the chance of an escalation by up to 32.2 percentage points, under the stated assumptions [F2].
> What could change: at comparable moments, doing less of this is estimated to lower the chance of an escalation by up to 8.6 percentage points, under the stated assumptions [F3].
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`*

**Turn 2:** what about premium customers?

Expected: route `reuse`, event ESC, industries all. Got: route `reuse`, event ESC, industries all — as expected.

> The data has no customer-tier field ('premium customers'). Where customers say they are members or long-time customers, that is used below as the nearest proxy.
> No customer mentions a membership, a loyalty status or a long tenure before the point where escalations start, so there is no proxy for customer tier in these calls either.
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> What could change: at comparable moments, doing more of this is estimated to lower the chance of an escalation by up to 31.5 percentage points, under the stated assumptions [F1].
> What could change: at comparable moments, doing less of this is estimated to lower the chance of an escalation by up to 32.2 percentage points, under the stated assumptions [F2].
> What could change: at comparable moments, doing less of this is estimated to lower the chance of an escalation by up to 8.6 percentage points, under the stated assumptions [F3].
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`*

**Turn 3:** and for refunds?

Expected: route `new_lookup`, event REF, industries all. Got: route `new_lookup`, event REF, industries all — as expected.

> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “delivered” (10.1% vs 7.5%); “package” (10.1% vs 7.5%).
> Empathy statements were common before the refund episode too (44.1%), but about as common at the same point in calls without one (49.2%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because my internet has been down since last night and this is completely unacceptable and i would like a refund” [7496fdf8-a677-6179-5005-c1f9e2d3895e:1]
> In the customer's own words: “hi i'm calling because my premium went up at renewal and honestly i'm pretty annoyed about it and i would like a refund” [1c736c49-fe0a-50ce-7247-0000d2c47f9b:1]
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,224 of 4,000 calls (30.6%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> What could change: at comparable moments, doing more of this is estimated to lower the chance of a refund episode by up to 15.9 percentage points, under the stated assumptions [F10].
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3)*
*Dialogue turns cited: `7496fdf8-a677-6179-5005-c1f9e2d3895e:1`, `1c736c49-fe0a-50ce-7247-0000d2c47f9b:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`*

#### s05 — follow-up session · medium · follow_up · follow_up

**Turn 1:** Why do hotel customers threaten to leave?

Expected: route `first`, event CHURN, industries ['hospitality']. Got: route `first`, event CHURN, industries ['hospitality'] — as expected.

> Why, from the conversations: in hotel calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.5% of them (against 54.4% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 73.7% of these calls (against 29.8% at the same point in calls without one); the agent refused a request or cited policy in 74.7% of these calls (against 43.5% at the same point in calls without one); the agent expressed empathy in 66.3% of these calls (against 54.4% at the same point in calls without one).
> Holds and wait requests were common before the churn threat too (44.2%), but about as common at the same point in calls without one (47.8%), so on their own they do not set these calls apart.
> 88.4% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because the room type was not what i reserved and honestly i'm pretty annoyed about it” [3cc486b9-89ce-e776-0738-26d40c7ba43d:1]
> Then the customer expressed frustration or anger: “i would like a refund for this this is ridiculous” [3cc486b9-89ce-e776-0738-26d40c7ba43d:9]
> Then the churn threat: “honestly i'm thinking about switching to you know another provider i'm um getting really frustrated with this” [3cc486b9-89ce-e776-0738-26d40c7ba43d:11]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In hotel calls, 95 of 702 calls (13.5%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Estimates for hotel calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for churn threats in hotel calls; the behaviours below are warning signs only.
> No clear difference: for policy refusals the estimate is compatible with no difference in the chance of a churn threat (+7.0 percentage points, 95% CI -0.5 to +14.6 points) [F151].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F151].
> Policy refusals also happened in 414 of 493 held-out calls where no churn threat followed [F151].
> “i'm afraid we cannot make an exception here” [73d59436-be13-b2cf-06bd-48568400af72:4]
> “um unfortunately per our policy you know i'm not able to change that” [490abb2f-62bd-a485-66f5-556d25050fa9:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 79% of the same speaker's other turns (a check of the model, not proof of what happened) [F151].
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of a churn threat (-5.7 percentage points, 95% CI -17.6 to +6.2 points) [F152].
> “i understand how frustrating that must be unfortunately per our policy i'm not able to change that” [3ce2cf6b-a632-79fa-52c7-3c23a88c7d81:14]
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F151 (L2), F152 (L2)*
*Dialogue turns cited: `3cc486b9-89ce-e776-0738-26d40c7ba43d:1`, `3cc486b9-89ce-e776-0738-26d40c7ba43d:9`, `3cc486b9-89ce-e776-0738-26d40c7ba43d:11`, `73d59436-be13-b2cf-06bd-48568400af72:4`, `490abb2f-62bd-a485-66f5-556d25050fa9:4`, `3ce2cf6b-a632-79fa-52c7-3c23a88c7d81:14`*

**Turn 2:** does empathy make a difference?

Expected: route `new_lookup`, event CHURN, industries ['hospitality']. Got: route `new_lookup`, event CHURN, industries ['hospitality'] — as expected.

> From the conversations: in the 6 turns before a churn threat, the agent expressed empathy in 66.3% of these calls, against 54.4% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because the room type was not what i reserved and honestly i'm pretty annoyed about it” [3cc486b9-89ce-e776-0738-26d40c7ba43d:1]
> Then the agent expressed empathy: “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay thank you for that information” [3cc486b9-89ce-e776-0738-26d40c7ba43d:10]
> Then the churn threat: “honestly i'm thinking about switching to you know another provider i'm um getting really frustrated with this” [3cc486b9-89ce-e776-0738-26d40c7ba43d:11]
> Estimates for hotel calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of a churn threat (-5.7 percentage points, 95% CI -17.6 to +6.2 points) [F152].
> Empathy statements often happen in the same calls as repeated questions, read-backs, policy refusals; their estimated effects are not independent and do not add up [F152].
> Empathy statements also happened in 479 of 551 held-out calls where no churn threat followed [F152].
> “i understand how frustrating that must be unfortunately per our policy i'm not able to change that” [3ce2cf6b-a632-79fa-52c7-3c23a88c7d81:14]
> “i understand how frustrating that must uh be unfortunately per our you know policy i'm not able to change that thank you for that information” [3470921b-83fc-cd84-230c-f293c361c8c6:4]
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F152 (L2)*
*Dialogue turns cited: `3cc486b9-89ce-e776-0738-26d40c7ba43d:1`, `3cc486b9-89ce-e776-0738-26d40c7ba43d:10`, `3cc486b9-89ce-e776-0738-26d40c7ba43d:11`, `3ce2cf6b-a632-79fa-52c7-3c23a88c7d81:14`, `3470921b-83fc-cd84-230c-f293c361c8c6:4`*

**Turn 3:** what about in general?

Expected: route `refilter`, event CHURN, industries all. Got: route `refilter`, event CHURN, industries all — as expected.

> From the conversations: in the 6 turns before a churn threat, the agent expressed empathy in 64.1% of these calls, against 61.1% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because my package was not delivered after two weeks and honestly i'm pretty annoyed about it” [44104768-b4d3-5de2-34e2-ddc4c77c2905:1]
> Then the agent expressed empathy: “i understand how frustrating that must be what i can do is offer you a prepaid return label today let me check that for you one moment please just to confirm that is um sn 2440 863 on the file …” [44104768-b4d3-5de2-34e2-ddc4c77c2905:20]
> Then the churn threat: “um honestly i'm thinking about switching to another provider i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:21]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of a churn threat (+0.8 percentage points, 95% CI -3.3 to +5.0 points) [F23].
> Empathy statements often happen in the same calls as repeated questions, read-backs, policy refusals; their estimated effects are not independent and do not add up [F23].
> Empathy statements also happened in 479 of 551 held-out calls where no churn threat followed [F23].
> “i understand how frustrating that must be let me check that for you one moment please” [0c3a65d0-50a4-5319-7dd9-73df32594123:4]
> “i uh understand how frustrating that must be i'm afraid we cannot make an exception here” [044af7bf-0c33-0327-01ce-f73efc3d61ad:4]
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F23 (L2)*
*Dialogue turns cited: `44104768-b4d3-5de2-34e2-ddc4c77c2905:1`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:20`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:21`, `0c3a65d0-50a4-5319-7dd9-73df32594123:4`, `044af7bf-0c33-0327-01ce-f73efc3d61ad:4`*

#### s06 — follow-up session · medium · follow_up · follow_up

**Turn 1:** Why do refunds happen in retail calls?

Expected: route `first`, event REF, industries ['retail_ecommerce']. Got: route `first`, event REF, industries ['retail_ecommerce'] — as expected.

> Why, from the conversations: in retail calls, before the refund episode the agent offered a concrete solution in only 25.7% of them (against 43.6% at the same point in other calls).
> Empathy statements were common before the refund episode too (44.3%), but about as common at the same point in calls without one (51.8%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because my package was not delivered after two weeks and this is completely unacceptable and i would like a refund” [3bd9bd96-82fd-8531-2f1c-9c0277fa131a:1]
> In the customer's own words: “hi i'm calling because my package was not delivered after two weeks and i would like a refund” [240639b7-6504-4e4d-0505-9d767d17db7f:1]
> One call, step by step: the customer's problem: “hi i'm calling because the blender i ordered arrived damaged” [38111241-e566-2997-0c2b-412cf31fa832:1]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [38111241-e566-2997-0c2b-412cf31fa832:15]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In retail calls, 237 of 693 calls (34.2%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Estimates for retail calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for refund episodes in retail calls; the behaviours below are warning signs only.
> No clear difference: for solution offers the estimate is compatible with no difference in the chance of a refund episode (-16.9 percentage points, 95% CI -36.6 to +2.8 points) [F117].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F117].
> “i understand how frustrating that must uh be what i can do is offer you a free replacement with express delivery let me check that for you one moment please” [44104768-b4d3-5de2-34e2-ddc4c77c2905:4]
> “unfortunately per our policy i'm uh not able to um change that what i can do is offer you a prepaid return label today” [50b382a3-cba3-b9af-0b37-5a67d388225b:10]
> No clear difference: for policy refusals the estimate is compatible with no difference in the chance of a refund episode (+12.3 percentage points, 95% CI -0.3 to +24.8 points) [F118].
> “unfortunately per our policy i'm not able to change that” [7cd1cade-8ed7-e454-4a5f-c53572aad520:4]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of a refund episode (+8.1 percentage points, 95% CI -4.5 to +20.8 points) [F119].
> “i understand how frustrating that must be unfortunately uh per our policy i'm not able to change that let me check that for uh you one moment please” [7444e19b-3a95-333d-7440-12dbc66dea42:4]
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F117 (L2), F118 (L2), F119 (L2)*
*Dialogue turns cited: `3bd9bd96-82fd-8531-2f1c-9c0277fa131a:1`, `240639b7-6504-4e4d-0505-9d767d17db7f:1`, `38111241-e566-2997-0c2b-412cf31fa832:1`, `38111241-e566-2997-0c2b-412cf31fa832:15`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:4`, `50b382a3-cba3-b9af-0b37-5a67d388225b:10`, `7cd1cade-8ed7-e454-4a5f-c53572aad520:4`, `7444e19b-3a95-333d-7440-12dbc66dea42:4`*

**Turn 2:** also hotel calls

Expected: route `refilter`, event REF, industries ['hospitality', 'retail_ecommerce']. Got: route `refilter`, event REF, industries ['retail_ecommerce', 'hospitality'] — as expected.

> Why, from the conversations: in retail / hotel calls, before the refund episode the agent offered a concrete solution in only 26.4% of them (against 41.8% at the same point in other calls).
> Policy refusals were common before the refund episode too (35.2%), but about as common at the same point in calls without one (34.5%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because the blender i ordered arrived damaged and honestly i'm pretty annoyed about it and i would like a refund” [68d7d342-33d3-1bf1-72c0-5d8391b2fef3:1]
> In the customer's own words: “hi i'm calling because the room type was not what i reserved and honestly i'm pretty annoyed about it and i would like a refund” [240ab431-e367-304b-7b72-e8c62093dfbf:1]
> One call, step by step: the customer's problem: “hi i'm calling because the blender i ordered arrived damaged” [4cfbdb3d-3422-f48f-7c21-0f3145f1f709:1]
> Then the refund episode: “i would like a refund for this” [4cfbdb3d-3422-f48f-7c21-0f3145f1f709:5]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In retail / hotel calls, 454 of 1,395 calls (32.5%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Effect estimates are available for all calls and for single industries; the filters apply to the counts only.
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay” [6657c4ee-329b-3cd2-33af-97b6a9540657:10]
> “what i can do is offer you a free upgrade on your next stay just to confirm that is hx 6201 995 on the file” [6c292704-266c-b8df-69c0-fe0cdf8bf0c6:10]
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> “i understand how frustrating that must be” [00f67d92-72a7-d42e-27a8-d297c7a38d30:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> “alright i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:17]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> “i'm afraid we cannot make uh an exception here let me check that for you one moment please” [3608cbf7-a22a-64a8-5882-1ba6f675db7d:4]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*
*Dialogue turns cited: `68d7d342-33d3-1bf1-72c0-5d8391b2fef3:1`, `240ab431-e367-304b-7b72-e8c62093dfbf:1`, `4cfbdb3d-3422-f48f-7c21-0f3145f1f709:1`, `4cfbdb3d-3422-f48f-7c21-0f3145f1f709:5`, `6657c4ee-329b-3cd2-33af-97b6a9540657:10`, `6c292704-266c-b8df-69c0-fe0cdf8bf0c6:10`, `00f67d92-72a7-d42e-27a8-d297c7a38d30:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:17`, `3608cbf7-a22a-64a8-5882-1ba6f675db7d:4`*

**Turn 3:** how often does that happen?

Expected: route `new_lookup`, event REF, industries ['hospitality', 'retail_ecommerce']. Got: route `new_lookup`, event REF, industries ['retail_ecommerce', 'hospitality'] — as expected.

> In retail / hotel calls, 454 of 1,395 calls (32.5%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> 30.2% of these refund episodes started within the opening turns.
> Why, from the conversations: in retail / hotel calls, before the refund episode the agent offered a concrete solution in only 26.4% of them (against 41.8% at the same point in other calls).
> All numbers describe this corpus of calls, not customers in general.

#### s07 — follow-up session · medium · follow_up · follow_up

**Turn 1:** Which industry has the most refund requests?

Expected: route `first`, event REF, industries all. Got: route `first`, event REF, industries all — as expected.

> Ranked by the share of calls with a refund episode: retail calls 34.2% (237 of 693); hotel calls 30.9% (217 of 702); insurance calls 30.2% (190 of 629); telecom calls 30.0% (206 of 687); banking calls 29.5% (188 of 638); airline calls 28.6% (186 of 651).
> These are counts; differences between groups of calls are not effects of anything in the calls.
> Why, from the conversations: in retail calls, before the refund episode the agent offered a concrete solution in only 25.7% of them (against 43.6% at the same point in other calls).
> For the full reasoning and the causal test for refund episodes in retail calls, ask a follow-up such as 'why in retail calls?'
> All numbers describe this corpus of calls, not customers in general.

**Turn 2:** why in hotel calls?

Expected: route `new_lookup`, event REF, industries ['hospitality']. Got: route `new_lookup`, event REF, industries ['hospitality'] — as expected.

> Why, from the conversations: in hotel calls, before the refund episode the agent offered a concrete solution in only 27.2% of them (against 40.0% at the same point in other calls).
> Policy refusals were common before the refund episode too (35.9%), but about as common at the same point in calls without one (39.8%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because the housekeeping at the hotel was really poor and i would like a refund” [6c8af31c-45da-8a3f-3727-8a35f9f6e7c5:1]
> In the customer's own words: “hi i'm calling because my room was double booked for the weekend and honestly i'm pretty annoyed about it and i would like a refund” [0033dc70-2f33-4d16-0302-bf8efc2e7d14:1]
> One call, step by step: the customer's problem: “hi i'm calling because the housekeeping at the hotel was really poor” [6bd4be62-b983-5b56-459f-cff633997f3f:1]
> Then the refund episode: “i would like a refund for this” [6bd4be62-b983-5b56-459f-cff633997f3f:15]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In hotel calls, 217 of 702 calls (30.9%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Estimates for hotel calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for refund episodes in hotel calls; the behaviours below are warning signs only.
> Warning sign: repeated questions are associated with a higher chance of a refund episode later in the call (+19.3 percentage points, 95% CI +2.7 to +35.9 points) [F99].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); it is a customer state, not something the company can change; not significant after the Benjamini-Hochberg correction over the pre-registered family [F99].
> Repeated questions often happen in the same calls as read-backs, empathy statements, policy refusals; their estimated effects are not independent and do not add up [F99].
> Repeated questions also happened in 165 of 228 held-out calls where no refund episode followed [F99].
> “sure no problem sorry i don't understand what you mean” [62c655c0-088b-a466-6a86-9a46322b4c4a:11]
> “i see you know i'm getting really frustrated with this” [09f40513-3e1b-4536-3802-749f40094600:9]
> No clear difference: for solution offers the estimate is compatible with no difference in the chance of a refund episode (-6.9 percentage points, 95% CI -22.9 to +9.0 points) [F100].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay” [6657c4ee-329b-3cd2-33af-97b6a9540657:10]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+8.6 percentage points, 95% CI -3.4 to +20.5 points) [F101].
> “let me you know check you know that for you one moment please just to confirm that is hx uh 7383 642 on the file” [1c813cb7-0afc-4517-1cea-e0df3931be7a:10]
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F99 (L2), F100 (L2), F101 (L2)*
*Dialogue turns cited: `6c8af31c-45da-8a3f-3727-8a35f9f6e7c5:1`, `0033dc70-2f33-4d16-0302-bf8efc2e7d14:1`, `6bd4be62-b983-5b56-459f-cff633997f3f:1`, `6bd4be62-b983-5b56-459f-cff633997f3f:15`, `62c655c0-088b-a466-6a86-9a46322b4c4a:11`, `09f40513-3e1b-4536-3802-749f40094600:9`, `6657c4ee-329b-3cd2-33af-97b6a9540657:10`, `1c813cb7-0afc-4517-1cea-e0df3931be7a:10`*

#### s08 — follow-up session · medium · follow_up · follow_up

**Turn 1:** Why do customers escalate?

Expected: route `first`, event ESC, industries all. Got: route `first`, event ESC, industries all — as expected.

> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

**Turn 2:** ¿y los reembolsos?

Expected: route `new_lookup`, event REF, industries all. Got: route `new_lookup`, event REF, industries all — as expected.

> The question looks like Spanish; it was read with a small built-in word list as: 'and refund'. For the most reliable answer, ask in English.
> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “delivered” (10.1% vs 7.5%); “package” (10.1% vs 7.5%).
> Empathy statements were common before the refund episode too (44.1%), but about as common at the same point in calls without one (49.2%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because my internet has been down since last night and this is completely unacceptable and i would like a refund” [7496fdf8-a677-6179-5005-c1f9e2d3895e:1]
> In the customer's own words: “hi i'm calling because my premium went up at renewal and honestly i'm pretty annoyed about it and i would like a refund” [1c736c49-fe0a-50ce-7247-0000d2c47f9b:1]
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,224 of 4,000 calls (30.6%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> “i understand how frustrating that must be” [00f67d92-72a7-d42e-27a8-d297c7a38d30:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> “alright i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:17]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*
*Dialogue turns cited: `7496fdf8-a677-6179-5005-c1f9e2d3895e:1`, `1c736c49-fe0a-50ce-7247-0000d2c47f9b:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`, `00f67d92-72a7-d42e-27a8-d297c7a38d30:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:17`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

**Turn 3:** waht about refnds in hotle calls?

Expected: route `refilter`, event REF, industries ['hospitality']. Got: route `refilter`, event REF, industries ['hospitality'] — as expected.

> I read 'refnds' as 'refunds'; 'hotle' as 'hotel'.
> Why, from the conversations: in hotel calls, before the refund episode the agent offered a concrete solution in only 27.2% of them (against 40.0% at the same point in other calls).
> Policy refusals were common before the refund episode too (35.9%), but about as common at the same point in calls without one (39.8%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because the housekeeping at the hotel was really poor and i would like a refund” [6c8af31c-45da-8a3f-3727-8a35f9f6e7c5:1]
> In the customer's own words: “hi i'm calling because my room was double booked for the weekend and honestly i'm pretty annoyed about it and i would like a refund” [0033dc70-2f33-4d16-0302-bf8efc2e7d14:1]
> One call, step by step: the customer's problem: “hi i'm calling because the housekeeping at the hotel was really poor” [6bd4be62-b983-5b56-459f-cff633997f3f:1]
> Then the refund episode: “i would like a refund for this” [6bd4be62-b983-5b56-459f-cff633997f3f:15]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In hotel calls, 217 of 702 calls (30.9%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Estimates for hotel calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for refund episodes in hotel calls; the behaviours below are warning signs only.
> Warning sign: repeated questions are associated with a higher chance of a refund episode later in the call (+19.3 percentage points, 95% CI +2.7 to +35.9 points) [F99].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); it is a customer state, not something the company can change; not significant after the Benjamini-Hochberg correction over the pre-registered family [F99].
> Repeated questions often happen in the same calls as read-backs, empathy statements, policy refusals; their estimated effects are not independent and do not add up [F99].
> Repeated questions also happened in 165 of 228 held-out calls where no refund episode followed [F99].
> “sure no problem sorry i don't understand what you mean” [62c655c0-088b-a466-6a86-9a46322b4c4a:11]
> “i see you know i'm getting really frustrated with this” [09f40513-3e1b-4536-3802-749f40094600:9]
> No clear difference: for solution offers the estimate is compatible with no difference in the chance of a refund episode (-6.9 percentage points, 95% CI -22.9 to +9.0 points) [F100].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay” [6657c4ee-329b-3cd2-33af-97b6a9540657:10]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+8.6 percentage points, 95% CI -3.4 to +20.5 points) [F101].
> “let me you know check you know that for you one moment please just to confirm that is hx uh 7383 642 on the file” [1c813cb7-0afc-4517-1cea-e0df3931be7a:10]
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F99 (L2), F100 (L2), F101 (L2)*
*Dialogue turns cited: `6c8af31c-45da-8a3f-3727-8a35f9f6e7c5:1`, `0033dc70-2f33-4d16-0302-bf8efc2e7d14:1`, `6bd4be62-b983-5b56-459f-cff633997f3f:1`, `6bd4be62-b983-5b56-459f-cff633997f3f:15`, `62c655c0-088b-a466-6a86-9a46322b4c4a:11`, `09f40513-3e1b-4536-3802-749f40094600:9`, `6657c4ee-329b-3cd2-33af-97b6a9540657:10`, `1c813cb7-0afc-4517-1cea-e0df3931be7a:10`*

#### s09 — follow-up session · medium · follow_up · follow_up

**Turn 1:** Why do customers get frustrated?

Expected: route `first`, event None, industries all. Got: route `first`, event None, industries all — as expected.

> In all calls, 2,336 of 4,000 calls (58.4%) had at least one moment where the customer expressed frustration or anger.
> Why, from the conversations: in the 6 turns before the first time the customer expressed frustration or anger, the agent refused a request or cited policy in 18.6% of these calls (against 0.0% at the same point in calls without it); the agent expressed empathy in 11.9% of these calls (against 0.0% at the same point in calls without it).
> In the customer's own words: “hi i'm calling because the blender i ordered arrived damaged and this is completely unacceptable” [3f2f1157-43ed-3530-507c-7ae515c59a46:1]
> In the customer's own words: “hi i'm calling because my claim has been under review for three weeks and honestly i'm pretty annoyed about it” [5ac29871-3c5d-51c2-139a-2eeefe2531d7:1]
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal” [66e60c03-5738-ce2d-74a7-b57158067374:1]
> Then the agent refused a request or cited policy: “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> Then the customer expressed frustration or anger: “i want to speak to a supervisor right now i'm getting really frustrated with this” [66e60c03-5738-ce2d-74a7-b57158067374:7]
> How this relates to the business events: an escalation in 72.0% of calls with customer frustration and in 11.1% of calls without it; a refund episode in 38.4% of calls with customer frustration and in 19.6% of calls without it; a churn threat in 20.9% of calls with customer frustration and in 5.9% of calls without it.
> These are counts and patterns, not effects. To test one event, ask a follow-up such as 'what about escalations?'
> All numbers describe this corpus of calls, not customers in general.

*Dialogue turns cited: `3f2f1157-43ed-3530-507c-7ae515c59a46:1`, `5ac29871-3c5d-51c2-139a-2eeefe2531d7:1`, `66e60c03-5738-ce2d-74a7-b57158067374:1`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `66e60c03-5738-ce2d-74a7-b57158067374:7`*

**Turn 2:** what about escalations?

Expected: route `new_lookup`, event ESC, industries all. Got: route `new_lookup`, event ESC, industries all — as expected.

> From the conversations: in the 6 turns before an escalation, the customer expressed frustration or anger in 77.6% of these calls, against 5.3% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> There is no reliable estimate for customer frustration and escalations: the error bar is too wide (95% CI +20.7 to +48.5 points); the compared moments are still not alike enough [F9].
> Counts only: customer frustration happened at 51 comparable moments in held-out calls, and 48 of those moments had an escalation later in the call [F9].
> “i see this is ridiculous” [77adb584-d516-7999-5ea4-2190e3cfb8ca:11]
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F9 (L1)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `77adb584-d516-7999-5ea4-2190e3cfb8ca:11`*

#### s11 — follow-up session · hard · follow_up · follow_up

**Turn 1:** Why do customers escalate?

Expected: route `first`, event ESC, industries all. Got: route `first`, event ESC, industries all — as expected.

> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

**Turn 2:** tell me more about that call (call 4067cb5d-8748-e1a2-390a-9d9e12b15244)

Expected: route `new_lookup`, event ESC, industries all. Got: route `new_lookup`, event ESC, industries all — as expected.

> Call 4067cb5d-8748-e1a2-390a-9d9e12b15244 is a banking call to Riverstone Bank from 2025-11-04 21:57, with 21 turns.
> Business events detected in this call, in order: a refund episode at turn 11; a refund being refused at turn 12; an escalation at turn 13; a supervisor joining at turn 15.
> The customer's problem (turn 1): “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Step by step, in the 6 turns before the escalation: turn 9, the customer was confused: “i see this is ridiculous sorry i don't understand what you mean” [4067cb5d-8748-e1a2-390a-9d9e12b15244:9]
> Turn 11, the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Turn 12, the agent refused a request or cited policy: “i understand how frustrating that must be i'm afraid we cannot make an exception here” [4067cb5d-8748-e1a2-390a-9d9e12b15244:12]
> Then the escalation (turn 13): “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How common these moments are across all calls, in the 6 turns before an escalation: the customer was confused in 14.0% of calls with one (against 10.3% at the same point in calls without one); the customer expressed frustration or anger in 77.6% of calls with one (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of calls with one (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of calls with one (against 51.5% at the same point in calls without one).
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> This walks through one call from its own turns. The shares and estimates describe calls in general; they are not proof of why this particular call ended in an escalation.

*Factors cited: F2 (L3), F5 (L2), F6 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:9`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:12`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`*

**Turn 3:** what about refunds?

Expected: route `new_lookup`, event REF, industries all. Got: route `new_lookup`, event REF, industries all — as expected.

> Call 4067cb5d-8748-e1a2-390a-9d9e12b15244 is a banking call to Riverstone Bank from 2025-11-04 21:57, with 21 turns.
> Business events detected in this call, in order: a refund episode at turn 11; a refund being refused at turn 12; an escalation at turn 13; a supervisor joining at turn 15.
> The customer's problem (turn 1): “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Step by step, in the 6 turns before the refund episode: turn 6, the agent offered a concrete solution: “i understand how frustrating that must be unfortunately per our policy i'm not able to change that what i can do is offer you a you know temporary card sent by express mail just to confirm that is ending 8277 …” [4067cb5d-8748-e1a2-390a-9d9e12b15244:6]
> Turn 9, the customer was confused: “i see this is ridiculous sorry i don't understand what you mean” [4067cb5d-8748-e1a2-390a-9d9e12b15244:9]
> Turn 10, the agent expressed empathy: “i understand how frustrating that must be unfortunately per our policy i'm not able to change that” [4067cb5d-8748-e1a2-390a-9d9e12b15244:10]
> Then the refund episode (turn 11): “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> How common these moments are across all calls, in the 6 turns before a refund episode: the agent offered a concrete solution in 24.3% of calls with one (against 41.2% at the same point in calls without one); the customer was confused in 8.0% of calls with one (against 13.7% at the same point in calls without one); the customer expressed frustration or anger in 37.3% of calls with one (against 42.8% at the same point in calls without one); the agent expressed empathy in 44.1% of calls with one (against 49.2% at the same point in calls without one).
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> No clear difference: for customer confusion the estimate is compatible with no difference in the chance of a refund episode (+4.3 percentage points, 95% CI -4.7 to +13.3 points) [F15].
> This walks through one call from its own turns. The shares and estimates describe calls in general; they are not proof of why this particular call ended in a refund episode.

*Factors cited: F10 (L3), F11 (L2), F15 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:6`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:9`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:10`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`*

**Turn 4:** only hotel calls

Expected: route `new_lookup`, event REF, industries ['hospitality']. Got: route `new_lookup`, event REF, industries ['hospitality'] — as expected.

> Why, from the conversations: in hotel calls, before the refund episode the agent offered a concrete solution in only 27.2% of them (against 40.0% at the same point in other calls).
> Policy refusals were common before the refund episode too (35.9%), but about as common at the same point in calls without one (39.8%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because the housekeeping at the hotel was really poor and i would like a refund” [6c8af31c-45da-8a3f-3727-8a35f9f6e7c5:1]
> In the customer's own words: “hi i'm calling because my room was double booked for the weekend and honestly i'm pretty annoyed about it and i would like a refund” [0033dc70-2f33-4d16-0302-bf8efc2e7d14:1]
> One call, step by step: the customer's problem: “hi i'm calling because the housekeeping at the hotel was really poor” [6bd4be62-b983-5b56-459f-cff633997f3f:1]
> Then the refund episode: “i would like a refund for this” [6bd4be62-b983-5b56-459f-cff633997f3f:15]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In hotel calls, 217 of 702 calls (30.9%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Estimates for hotel calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for refund episodes in hotel calls; the behaviours below are warning signs only.
> Warning sign: repeated questions are associated with a higher chance of a refund episode later in the call (+19.3 percentage points, 95% CI +2.7 to +35.9 points) [F99].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); it is a customer state, not something the company can change; not significant after the Benjamini-Hochberg correction over the pre-registered family [F99].
> Repeated questions often happen in the same calls as read-backs, empathy statements, policy refusals; their estimated effects are not independent and do not add up [F99].
> Repeated questions also happened in 165 of 228 held-out calls where no refund episode followed [F99].
> “sure no problem sorry i don't understand what you mean” [62c655c0-088b-a466-6a86-9a46322b4c4a:11]
> “i see you know i'm getting really frustrated with this” [09f40513-3e1b-4536-3802-749f40094600:9]
> No clear difference: for solution offers the estimate is compatible with no difference in the chance of a refund episode (-6.9 percentage points, 95% CI -22.9 to +9.0 points) [F100].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay” [6657c4ee-329b-3cd2-33af-97b6a9540657:10]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+8.6 percentage points, 95% CI -3.4 to +20.5 points) [F101].
> “let me you know check you know that for you one moment please just to confirm that is hx uh 7383 642 on the file” [1c813cb7-0afc-4517-1cea-e0df3931be7a:10]
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F99 (L2), F100 (L2), F101 (L2)*
*Dialogue turns cited: `6c8af31c-45da-8a3f-3727-8a35f9f6e7c5:1`, `0033dc70-2f33-4d16-0302-bf8efc2e7d14:1`, `6bd4be62-b983-5b56-459f-cff633997f3f:1`, `6bd4be62-b983-5b56-459f-cff633997f3f:15`, `62c655c0-088b-a466-6a86-9a46322b4c4a:11`, `09f40513-3e1b-4536-3802-749f40094600:9`, `6657c4ee-329b-3cd2-33af-97b6a9540657:10`, `1c813cb7-0afc-4517-1cea-e0df3931be7a:10`*

#### s12 — follow-up session · medium · follow_up · follow_up

**Turn 1:** Hello

Expected: route `first`, event None, industries all. Got: route `first`, event None, industries all — as expected.

> I answer questions about escalations, refund episodes, churn threats and retention risks in these calls, and about what agents and customers did before them.
> Examples: “Why do customers escalate?”, “How often do customers ask for refunds in hotel calls?”, “Is customer frustration linked to churn threats?”, “Why do customers who were refused a refund escalate?”, “Did escalations change after the new policy?”, “Which industry has the most refunds?”, “Why do customers get frustrated?”
> Follow-ups keep the context: “what about refunds?”, “only airline calls”, “explain the first factor”, “compare with churn threats”.
> Questions can be in English, Spanish, French, German, Portuguese, Italian or Hindi, and spelling mistakes are corrected; every answer says how the question was read.

**Turn 2:** give me an overview

Expected: route `new_lookup`, event None, industries all. Got: route `new_lookup`, event None, industries all — as expected.

> In all calls (4,000 calls): escalations in 46.6% (1,865 calls); refund episodes in 30.6% (1,224 calls); churn threats in 14.7% (588 calls); retention risks in 19.8% (791 calls).
> The largest industries: hotel calls 17.5%; retail calls 17.3%; telecom calls 17.2%; airline calls 16.3%.
> The most common moments: the agent offered a concrete solution in 98.4% of calls; the agent expressed empathy in 74.5% of calls; the agent put the customer on hold or asked them to wait in 69.8% of calls; the agent refused a request or cited policy in 64.0% of calls.
> Calls that later had an escalation more often open with “flight” and “pnr”.
> Calls that later had a refund episode more often open with “delivered” and “package”.
> To see what lies behind any of these, ask for example “Why do customers escalate?”, “What drives refunds in hotel calls?” or “What should agents stop doing?”
> All numbers describe this corpus of calls, not customers in general.

**Turn 3:** what about churn threats?

Expected: route `new_lookup`, event CHURN, industries all. Got: route `new_lookup`, event CHURN, industries all — as expected.

> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 66.3% of these calls (against 24.9% at the same point in calls without one); the agent refused a request or cited policy in 68.4% of these calls (against 46.2% at the same point in calls without one).
> Empathy statements were common before the churn threat too (64.1%), but about as common at the same point in calls without one (61.1%), so on their own they do not set these calls apart.
> 89.3% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my claim has been under review for three weeks and this is completely unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:1]
> Then the customer expressed frustration or anger: “sure it's pl 6395 751 and please hurry this is unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:3]
> Then the churn threat: “honestly i'm thinking about switching to another provider” [3169e20d-7aaf-aee7-0a70-19178db8442f:5]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Causal test: for churn threats in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a churn threat later in the call by 7.7 percentage points (95% CI -11.6 to -3.8 points) at the moments where they happened [F19].
> Under the same assumptions, that is about 35 fewer churn threats among the held-out calls (95% CI 17 to 53) [F19].
> Solution offers also happened in 701 of 742 held-out calls where no churn threat followed [F19].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay just to confirm that is hx 7964 810 on the file” [4273908c-b138-f619-6f47-c209d47710d2:4]
> “i understand how frustrating that must uh be what i can do is offer you a free replacement with express delivery let me check that for you one moment please” [44104768-b4d3-5de2-34e2-ddc4c77c2905:4]
> Warning sign: policy refusals are associated with a higher chance of a churn threat later in the call (+4.1 percentage points, 95% CI +0.2 to +8.0 points) [F20].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F20].
> “i'm afraid we cannot make an exception here” [73d59436-be13-b2cf-06bd-48568400af72:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a churn threat (+4.7 percentage points, 95% CI -0.3 to +9.7 points) [F21].
> “yes that is correct i'm getting you know really frustrated with this” [43fbf10c-7ee5-caaa-2948-aab62844edd4:15]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a churn threat (+2.9 percentage points, 95% CI -1.4 to +7.1 points) [F22].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the churn threat; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.84 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F19 (L3), F20 (L2), F21 (L2), F22 (L2)*
*Dialogue turns cited: `3169e20d-7aaf-aee7-0a70-19178db8442f:1`, `3169e20d-7aaf-aee7-0a70-19178db8442f:3`, `3169e20d-7aaf-aee7-0a70-19178db8442f:5`, `4273908c-b138-f619-6f47-c209d47710d2:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:4`, `73d59436-be13-b2cf-06bd-48568400af72:4`, `43fbf10c-7ee5-caaa-2948-aab62844edd4:15`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

## Locked test queries (33)

### Task 1: evidence-based causal explanation

#### q031 — how_often · easy · simple_retrieval · monitoring

**Question:** How often do customers threaten to leave?

Expected: answer (event CHURN, type how_often). Outcome: as expected (the system answered a 'how_often' question about CHURN).

> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Corrected for labeller errors with the blind gold sample, the held-out rate is 13.3% (95% CI 13.3% to 13.3%).
> 0.0% of these churn threats started within the opening turns.
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> In the 6 turns before the churn threat, the customer expressed frustration or anger in 66.3% of these calls, against 24.9% at the same point in calls without one.
> All numbers describe this corpus of calls, not customers in general.

#### q007 — examples · easy · simple_retrieval · evidence_lookup

**Question:** Show me examples of calls where customers escalate

Expected: answer (event ESC, type examples). Outcome: as expected (the system answered a 'examples' question about ESC).

> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> “i want to speak to a supervisor right now i'm getting really frustrated with this” [2dc8a5a8-c552-8e20-1311-288ed020ed05:9]
> “get me someone above you right now” [1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:15]
> “get me someone above you right now” [6978f34d-df6a-269d-0728-7f52edfa4e53:5]
> “i want to speak to a supervisor right now sorry i don't understand what you mean” [2522ef16-d1a1-99b5-436c-f3ef528f2cc2:15]
> “i want to speak to a supervisor right now” [772f4ff2-620a-8f4e-2a14-1f11df88b2dd:11]
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 77.6% of these calls, against 5.3% at the same point in calls without one.
> Examples illustrate; they are not counts or evidence of an effect.

*Dialogue turns cited: `2dc8a5a8-c552-8e20-1311-288ed020ed05:9`, `1fab9a3b-1c9a-c00c-15bb-0232a27f19d3:15`, `6978f34d-df6a-269d-0728-7f52edfa4e53:5`, `2522ef16-d1a1-99b5-436c-f3ef528f2cc2:15`, `772f4ff2-620a-8f4e-2a14-1f11df88b2dd:11`*

#### q005 — trend · easy · simple_retrieval · monitoring

**Question:** How have escalations changed over time?

Expected: answer (event ESC, type trend). Outcome: as expected (the system answered a 'trend' question about ESC).

> Weekly share of calls with an escalation: 2025-11-03/2025-11-09: 45.8%; 2025-11-10/2025-11-16: 48.6%.
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 77.6% of these calls, against 5.3% at the same point in calls without one.
> Week-to-week changes in these shares can come from the mix of calls in each week as well as from what happens in the calls.
> All numbers describe this corpus of calls, not customers in general.

#### q040 — ranking · easy · simple_retrieval · segment_comparison

**Question:** Rank the industries by how often customers threaten to cancel

Expected: answer_rank (event CHURN, type compare). Outcome: as expected (the system answered a 'compare' question about CHURN).

> Ranked by the share of calls with a churn threat: retail calls 16.2% (112 of 693); banking calls 16.0% (102 of 638); airline calls 14.9% (97 of 651); insurance calls 14.5% (91 of 629); hotel calls 13.5% (95 of 702); telecom calls 13.2% (91 of 687).
> These are counts; differences between groups of calls are not effects of anything in the calls.
> Why, from the conversations: in retail calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 28.6% of them (against 53.0% at the same point in other calls).
> In the 6 turns before the churn threat, the customer expressed frustration or anger in 67.9% of these calls, against 23.8% at the same point in calls without one.
> For the full reasoning and the causal test for churn threats in retail calls, ask a follow-up such as 'why in retail calls?'
> All numbers describe this corpus of calls, not customers in general.

#### q039 — product_improvement · medium · simple_retrieval · product_improvement

**Question:** What should the product team fix to reduce churn threats?

Expected: answer_topics (event CHURN, type issues). Outcome: as expected (the system answered a 'issues' question about CHURN).

> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> No product, service or problem words stand out at the start of calls that later had a churn threat (too few calls, or no clear difference from other calls).
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> In the 6 turns before the churn threat, the customer expressed frustration or anger in 66.3% of these calls, against 24.9% at the same point in calls without one.
> All numbers describe this corpus of calls, not customers in general.

#### q002 — why · medium · multi_hop · root_cause

**Question:** What drives escalations in hotel calls?

Expected: answer (event ESC, type why). Outcome: as expected (the system answered a 'why' question about ESC with filters {"industry": ["hospitality"]}).

> Why, from the conversations: in hotel calls, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 31.0% of them (against 69.1% at the same point in other calls).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 78.7% of these calls (against 4.9% at the same point in calls without one); the agent refused a request or cited policy in 92.6% of these calls (against 23.4% at the same point in calls without one); the agent expressed empathy in 71.9% of these calls (against 51.4% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because the room type was not what i reserved” [518154b5-42af-084e-5619-15638f238404:1]
> Then the customer expressed frustration or anger: “i see this is ridiculous” [518154b5-42af-084e-5619-15638f238404:21]
> Then the escalation: “i want to speak to a supervisor right now this is ridiculous” [518154b5-42af-084e-5619-15638f238404:23]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In hotel calls, 352 of 702 calls (50.1%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Estimates for hotel calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for escalations in hotel calls; the behaviours below are warning signs only.
> Warning sign: solution offers are associated with a lower chance of an escalation later in the call (-35.8 percentage points, 95% CI -55.7 to -16.0 points) [F45].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); support is not 'sufficient' (events per arm, overlap, CI width or balance); the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F45].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F45].
> “um what i can do is offer you a late checkout at no extra charge” [56b998c8-5f76-0240-1b5e-9a099dd7f93c:12]
> “i understand how frustrating that must be you know what i can do is offer you a you know late checkout at no extra charge” [21126d3b-eaeb-0cc6-4b2b-f39e50f9df57:6]
> Warning sign: policy refusals are associated with a higher chance of an escalation later in the call (+26.4 percentage points, 95% CI +15.8 to +37.0 points) [F46].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); support is not 'sufficient' (events per arm, overlap, CI width or balance) [F46].
> “unfortunately per our policy i'm not able to change that” [76fc2b03-af43-5527-31b4-03a939a0412a:4]
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+24.9 percentage points, 95% CI +6.8 to +42.9 points) [F47].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); it is a customer state, not something the company can change [F47].
> “okay go ahead sorry i don't understand what you mean” [7b1b04c9-bc9c-ae57-7813-56ed6a2b9ce3:9]
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F45 (L2), F46 (L2), F47 (L2)*
*Dialogue turns cited: `518154b5-42af-084e-5619-15638f238404:1`, `518154b5-42af-084e-5619-15638f238404:21`, `518154b5-42af-084e-5619-15638f238404:23`, `56b998c8-5f76-0240-1b5e-9a099dd7f93c:12`, `21126d3b-eaeb-0cc6-4b2b-f39e50f9df57:6`, `76fc2b03-af43-5527-31b4-03a939a0412a:4`, `7b1b04c9-bc9c-ae57-7813-56ed6a2b9ce3:9`*

#### q017 — why · medium · multi_hop · root_cause

**Question:** Why do customers ask for refunds?

Expected: answer (event REF, type why). Outcome: as expected (the system answered a 'why' question about REF).

> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “delivered” (10.1% vs 7.5%); “package” (10.1% vs 7.5%).
> Empathy statements were common before the refund episode too (44.1%), but about as common at the same point in calls without one (49.2%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because my internet has been down since last night and this is completely unacceptable and i would like a refund” [7496fdf8-a677-6179-5005-c1f9e2d3895e:1]
> In the customer's own words: “hi i'm calling because my premium went up at renewal and honestly i'm pretty annoyed about it and i would like a refund” [1c736c49-fe0a-50ce-7247-0000d2c47f9b:1]
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,224 of 4,000 calls (30.6%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> “i understand how frustrating that must be” [00f67d92-72a7-d42e-27a8-d297c7a38d30:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> “alright i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:17]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*
*Dialogue turns cited: `7496fdf8-a677-6179-5005-c1f9e2d3895e:1`, `1c736c49-fe0a-50ce-7247-0000d2c47f9b:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`, `00f67d92-72a7-d42e-27a8-d297c7a38d30:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:17`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q019 — compare · medium · multi_hop · segment_comparison

**Question:** Compare refund requests between hotel and retail calls

Expected: answer (event REF, type compare). Outcome: as expected (the system answered a 'compare' question about REF).

> Share of calls with the event: 30.9% of hotel calls (217 of 702); 34.2% of retail calls (237 of 693).
> Why, from the conversations: in hotel calls, before the refund episode the agent offered a concrete solution in only 27.2% of them (against 40.0% at the same point in other calls).
> Why, from the conversations: in retail calls, before the refund episode the agent offered a concrete solution in only 25.7% of them (against 43.6% at the same point in other calls).
> These are counts and patterns in the transcripts; differences between groups of calls are not effects of anything in the calls.
> All numbers describe this corpus of calls, not customers in general.

#### q034 — effect_of · medium · multi_hop · hypothesis_test

**Question:** Are solution offers linked to churn threats?

Expected: answer (event CHURN, type effect_of). Outcome: as expected (the system answered a 'effect_of' question about CHURN).

> From the conversations: in the 6 turns before a churn threat, the agent offered a concrete solution in 30.6% of these calls, against 51.3% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because my claim has been under review for three weeks and this is completely unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:1]
> Then the agent offered a concrete solution: “what i can do is offer you a priority um review of your claim” [3169e20d-7aaf-aee7-0a70-19178db8442f:4]
> Then the churn threat: “honestly i'm thinking about switching to another provider” [3169e20d-7aaf-aee7-0a70-19178db8442f:5]
> Under the stated assumptions, solution offers are estimated to lower the chance of a churn threat later in the call by 7.7 percentage points (95% CI -11.6 to -3.8 points) at the moments where they happened [F19].
> Under the same assumptions, that is about 35 fewer churn threats among the held-out calls (95% CI 17 to 53) [F19].
> Solution offers also happened in 701 of 742 held-out calls where no churn threat followed [F19].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay just to confirm that is hx 7964 810 on the file” [4273908c-b138-f619-6f47-c209d47710d2:4]
> “i understand how frustrating that must uh be what i can do is offer you a free replacement with express delivery let me check that for you one moment please” [44104768-b4d3-5de2-34e2-ddc4c77c2905:4]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the churn threat; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.84 with both to explain the estimates away (E-values).
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F19 (L3)*
*Dialogue turns cited: `3169e20d-7aaf-aee7-0a70-19178db8442f:1`, `3169e20d-7aaf-aee7-0a70-19178db8442f:4`, `3169e20d-7aaf-aee7-0a70-19178db8442f:5`, `4273908c-b138-f619-6f47-c209d47710d2:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:4`*

#### q006 — what_to_change · hard · multi_hop · process_improvement

**Question:** How can we reduce escalations?

Expected: answer (event ESC, type what_to_change). Outcome: as expected (the system answered a 'what_to_change' question about ESC).

> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> What could change: at comparable moments, doing more of this is estimated to lower the chance of an escalation by up to 31.5 percentage points, under the stated assumptions [F1].
> What could change: at comparable moments, doing less of this is estimated to lower the chance of an escalation by up to 32.2 percentage points, under the stated assumptions [F2].
> What could change: at comparable moments, doing less of this is estimated to lower the chance of an escalation by up to 8.6 percentage points, under the stated assumptions [F3].
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`*

#### q044 — multi_hop · hard · multi_hop · root_cause

**Question:** Which industry has the highest escalation rate, and what drives escalations there?

Expected: answer_rank (event ESC, type compare). Outcome: as expected (the system answered a 'compare' question about ESC).

> Ranked by the share of calls with an escalation: airline calls 53.3% (347 of 651); banking calls 51.6% (329 of 638); hotel calls 50.1% (352 of 702); insurance calls 43.1% (271 of 629); retail calls 42.1% (292 of 693); telecom calls 39.9% (274 of 687).
> These are counts; differences between groups of calls are not effects of anything in the calls.
> Next step, the top group: here is what the data shows for escalations in airline calls.
> Why, from the conversations: in airline calls, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 25.1% of them (against 71.4% at the same point in other calls).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.2% of these calls (against 6.9% at the same point in calls without one); the agent refused a request or cited policy in 93.4% of these calls (against 25.3% at the same point in calls without one); the agent expressed empathy in 70.3% of these calls (against 51.6% at the same point in calls without one).
> Holds and wait requests were common before the escalation too (35.7%), but about as common at the same point in calls without one (28.6%), so on their own they do not set these calls apart.
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: then the customer expressed frustration or anger: “hi i'm calling because my flight to denver was delayed by five hours and honestly i'm pretty annoyed about it” [58fa7a4a-3b9d-0b44-5d7b-5d8a027c0454:1]
> Then the escalation: “i want to speak to a supervisor right now i'm getting really frustrated with this” [58fa7a4a-3b9d-0b44-5d7b-5d8a027c0454:5]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In airline calls, 347 of 651 calls (53.3%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Estimates for airline calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for escalations in airline calls; the behaviours below are warning signs only.
> Warning sign: solution offers are associated with a lower chance of an escalation later in the call (-48.4 percentage points, 95% CI -63.5 to -33.3 points) [F27].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); support is not 'sufficient' (events per arm, overlap, CI width or balance); the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F27].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F27].
> “i understand how frustrating that must be what i can do is offer you free seat um selection on your next trip you know just to confirm that is pnr q7089470 uh on you know the file” [30268498-4746-9982-6c36-3f1a02615a29:6]
> “i understand how frustrating that must be what uh i can do is offer you priority rebooking on the next flight” [44336dce-067d-624f-72fd-b7db853e1e85:6]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of an escalation (+8.9 percentage points, 95% CI -5.9 to +23.7 points) [F28].
> “unfortunately per our policy i'm not able to change that let me check that for you know you one moment please thank you for that information” [12fc0d07-6eac-f46b-0d98-a5f79809022c:8]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (-8.0 percentage points, 95% CI -26.9 to +10.9 points) [F29].
> “yes that is correct i'm getting really frustrated with this” [6526b489-a1ec-f33b-2850-76ebae9d6c0d:11]
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F27 (L2), F28 (L2), F29 (L2)*
*Dialogue turns cited: `58fa7a4a-3b9d-0b44-5d7b-5d8a027c0454:1`, `58fa7a4a-3b9d-0b44-5d7b-5d8a027c0454:5`, `30268498-4746-9982-6c36-3f1a02615a29:6`, `44336dce-067d-624f-72fd-b7db853e1e85:6`, `12fc0d07-6eac-f46b-0d98-a5f79809022c:8`, `6526b489-a1ec-f33b-2850-76ebae9d6c0d:11`*

#### q066 — conditional · hard · multi_hop · root_cause

**Question:** Why do customers who were refused a refund and threatened to cancel escalate?

Expected: answer_condition (event ESC, type why). Outcome: as expected (the system answered a 'why' question about ESC with filters {"with_event": ["REF_DENIED", "CHURN"]}).

> This answer looks only at calls where a refund was refused and a churn threat came up (113 calls).
> In those calls, 107 (94.7%) had an escalation, against 45.2% of the other calls in the slice and 46.6% of all calls in the slice.
> In the calls with all of these, the escalation came after the last of them in 44, before it in 63, and in the same turn in 0.
> Why, from the conversations: in calls where a refund was refused and a churn threat came up, no opening problem words or behaviours before the escalation stand out against calls without one; the escalations look spread across many situations.
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and honestly i'm pretty annoyed about it” [036c80e4-5677-5f8e-064b-76ef9df382c2:1]
> Then the escalation: “i want to speak to a supervisor right now this is ridiculous” [036c80e4-5677-5f8e-064b-76ef9df382c2:23]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In calls where a refund was refused and a churn threat came up, 107 of 113 calls (94.7%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Effect estimates are available for all calls and for single industries; the filters apply to the counts only.
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `036c80e4-5677-5f8e-064b-76ef9df382c2:1`, `036c80e4-5677-5f8e-064b-76ef9df382c2:23`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

#### q067 — before_after · hard · impact_evaluation · impact_evaluation

**Question:** Did escalations go up after 2025-11-08?

Expected: answer_change (event ESC, type trend). Outcome: as expected (the system answered a 'trend' question about ESC).

> Calls in the data run from 2025-11-04 to 2025-11-12: 1,838 fall before 2025-11-08 and 2,162 on or after it.
> An escalation happened in 44.0% of calls before 2025-11-08 and in 48.9% of calls from 2025-11-08 on: a difference of +4.9 percentage points (95% CI +1.8 to +8.0 points).
> The interval excludes zero, so the two periods do differ.
> Interrupted time series (6-hour block periods: 15 before 2025-11-08 and 18 from it): before the date the share was moving by -0.2 percentage points per 6-hour block; at the date its level shifted by +8.3 percentage points (95% CI +1.8 to +14.7 points) and its trend changed by +0.0 percentage points per 6-hour block (95% CI -0.7 to +0.7 points).
> The model allows for the usual time-of-day pattern, and its intervals use Newey–West standard errors (never narrower than the classical ones; lag-one residual autocorrelation -0.01).
> Placebo check: at 4 made-up dates before 2025-11-08, 0 level shifts were at least as large as the real one, so the shift at the real date stands out from the series' usual movement.
> Why, from the conversations: in calls from 2025-11-08 on, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.9% of them (against 69.6% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 78.1% of these calls, against 4.8% at the same point in calls without one.
> Why, from the conversations: in calls before 2025-11-08, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 26.5% of them (against 67.8% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 76.9% of these calls, against 5.9% at the same point in calls without one.
> Read with care: these comparisons tie a change to the date only; anything that changed around 2025-11-08 (the season, the mix of calls, staffing) would show up the same way.
> All numbers describe this corpus of calls, not customers in general.

#### q072 — threshold · medium · multi_hop · hypothesis_test

**Question:** Which behaviours do not affect churn threats?

Expected: answer_threshold (event CHURN, type why). Outcome: as expected (the system answered a 'why' question about CHURN; notices: no clear effect).

> 'No clear effect' is read as: the confidence interval of the estimated difference includes zero. That is not proof of no effect; each interval shows how large an effect the data cannot rule out.
> Behaviours with no clear difference in the chance of a churn threat later in the call (the interval includes zero): empathy statements (+0.8 percentage points, 95% CI -3.3 to +5.0 points) [F23]; customer confusion (+2.3 percentage points, 95% CI -3.8 to +8.5 points) [F24]; holds and wait requests (+2.9 percentage points, 95% CI -1.4 to +7.1 points) [F22]; repeated questions (+4.7 percentage points, 95% CI -0.3 to +9.7 points) [F21].
> The wider an interval, the larger the effect the data cannot rule out, so these are not shown to have no effect.
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> In the 6 turns before the churn threat, the customer expressed frustration or anger in 66.3% of these calls, against 24.9% at the same point in calls without one.
> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F23 (L2), F24 (L2), F22 (L2), F21 (L2)*

#### q074 — behaviour_profile · medium · simple_retrieval · root_cause

**Question:** When do agents refuse requests?

Expected: answer_profile. Outcome: as expected (the system answered a 'behaviour' question about None).

> In all calls, 2,562 of 4,000 calls (64.0%) had at least one moment where the agent refused a request or cited policy.
> Why, from the conversations: in the 6 turns before the first time the agent refused a request or cited policy, the customer expressed frustration or anger in 41.8% of these calls (against 33.0% at the same point in calls without it).
> One call, step by step: then the customer expressed frustration or anger: “hi i'm calling because my room was double booked for the weekend and honestly i'm pretty annoyed about it” [09f40513-3e1b-4536-3802-749f40094600:1]
> Then the agent refused a request or cited policy: “unfortunately per our policy i'm not able to change that let um me check that for you one moment please thank you for that information” [09f40513-3e1b-4536-3802-749f40094600:6]
> How this relates to the business events: an escalation in 67.7% of calls with policy refusals and in 9.0% of calls without them; a refund episode in 37.7% of calls with policy refusals and in 18.0% of calls without them; a churn threat in 20.6% of calls with policy refusals and in 4.1% of calls without them.
> These are counts and patterns, not effects. To test one event, ask a follow-up such as 'what about escalations?'
> All numbers describe this corpus of calls, not customers in general.

*Dialogue turns cited: `09f40513-3e1b-4536-3802-749f40094600:1`, `09f40513-3e1b-4536-3802-749f40094600:6`*

#### q076 — overview · easy · simple_retrieval · monitoring

**Question:** What can you do?

Expected: answer_help. Outcome: as expected (the system answered a 'help' question about None).

> I answer questions about escalations, refund episodes, churn threats and retention risks in these calls, and about what agents and customers did before them.
> Examples: “Why do customers escalate?”, “How often do customers ask for refunds in hotel calls?”, “Is customer frustration linked to churn threats?”, “Why do customers who were refused a refund escalate?”, “Did escalations change after the new policy?”, “Which industry has the most refunds?”, “Why do customers get frustrated?”
> Follow-ups keep the context: “what about refunds?”, “only airline calls”, “explain the first factor”, “compare with churn threats”.
> Questions can be in English, Spanish, French, German, Portuguese, Italian or Hindi, and spelling mistakes are corrected; every answer says how the question was read.

#### q077 — retention_risk · medium · multi_hop · root_cause

**Question:** Which customers are at risk of leaving?

Expected: answer (event RISK, type why). Outcome: as expected (the system answered a 'why' question about RISK).

> Why, from the conversations: in all calls, in the turns just before the retention risk the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 33.4% of them (against 51.9% at the same point in other calls).
> What happened in the 6 turns before the retention risk: the customer expressed frustration or anger in 64.3% of these calls (against 24.3% at the same point in calls without one); the agent refused a request or cited policy in 67.1% of these calls (against 45.4% at the same point in calls without one).
> Empathy statements were common before the retention risk too (64.0%), but about as common at the same point in calls without one (60.2%), so on their own they do not set these calls apart.
> 69.8% of these retention risks start with an explicit churn threat.
> One call, step by step: then the customer expressed frustration or anger: “hi i'm calling because the room type was not what i reserved and honestly i'm pretty annoyed about it” [3470921b-83fc-cd84-230c-f293c361c8c6:1]
> Then the retention risk: “honestly i'm thinking about switching to another provider you know another company offered me a better deal i'm getting really frustrated with this” [3470921b-83fc-cd84-230c-f293c361c8c6:5]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 791 of 4,000 calls (19.8%) had a retention risk (event labeller presence F1 on the gold set: not measured).
> Causal test: no in-call behaviour has a reliable estimate for retention risks in all calls; any behaviours below are shown as counts only.
> All numbers describe this corpus of calls, not customers in general.

*Dialogue turns cited: `3470921b-83fc-cd84-230c-f293c361c8c6:1`, `3470921b-83fc-cd84-230c-f293c361c8c6:5`*

#### q080 — single_call · medium · evidence_lookup · root_cause

**Question:** What happened in call 7d6a1c82-17a9-5e8d-02f8-e80d242ca22d?

Expected: answer_call. Outcome: as expected (the system answered a 'call' question about None with filters {"call": ["7d6a1c82-17a9-5e8d-02f8-e80d242ca22d"]}).

> Call 7d6a1c82-17a9-5e8d-02f8-e80d242ca22d is a retail call to Shopnest from 2025-11-11 10:40, with 26 turns.
> None of the business events (escalations, refund episodes, churn threats, retention risks) was detected in this call.
> The customer's problem (turn 1): “hi i'm calling because my package was not delivered after two weeks” [7d6a1c82-17a9-5e8d-02f8-e80d242ca22d:1]
> What happened in this call: turn 12, the agent offered a concrete solution: “what i can do is offer you um a prepaid return label today thank you for that information” [7d6a1c82-17a9-5e8d-02f8-e80d242ca22d:12]
> Turn 13, the customer was confused: “okay go ahead sorry i don't understand what you mean” [7d6a1c82-17a9-5e8d-02f8-e80d242ca22d:13]
> Turn 20, the agent expressed empathy: “i understand how frustrating that must be i'm afraid we cannot make an exception here thank you for that information” [7d6a1c82-17a9-5e8d-02f8-e80d242ca22d:20]

*Dialogue turns cited: `7d6a1c82-17a9-5e8d-02f8-e80d242ca22d:1`, `7d6a1c82-17a9-5e8d-02f8-e80d242ca22d:12`, `7d6a1c82-17a9-5e8d-02f8-e80d242ca22d:13`, `7d6a1c82-17a9-5e8d-02f8-e80d242ca22d:20`*

#### q055 — noisy_text · medium · robustness · robustness

**Question:** how often do customers escalate in hotle calls?

Expected: answer_read (event ESC, type how_often). Outcome: as expected (the system answered a 'how_often' question about ESC with filters {"industry": ["hospitality"]}).

> I read 'hotle' as 'hotel'.
> In hotel calls, 352 of 702 calls (50.1%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> 0.0% of these escalations started within the opening turns.
> Why, from the conversations: in hotel calls, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 31.0% of them (against 69.1% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 78.7% of these calls, against 4.9% at the same point in calls without one.
> All numbers describe this corpus of calls, not customers in general.

#### q058 — multilingual · medium · robustness · robustness

**Question:** Warum eskalieren Kunden?

Expected: answer_read (event ESC, type why). Outcome: as expected (the system answered a 'why' question about ESC).

> The question looks like German; it was read with a small built-in word list as: 'why escalate customers'. For the most reliable answer, ask in English.
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

#### q063 — multilingual · medium · robustness · robustness

**Question:** ¿Con qué frecuencia escalan los clientes en las llamadas de hoteles?

Expected: answer_read (event ESC, type how_often). Outcome: as expected (the system answered a 'how_often' question about ESC with filters {"industry": ["hospitality"]}).

> The question looks like Spanish; it was read with a small built-in word list as: 'how often escalate customers calls hotel'. For the most reliable answer, ask in English.
> In hotel calls, 352 of 702 calls (50.1%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> 0.0% of these escalations started within the opening turns.
> Why, from the conversations: in hotel calls, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 31.0% of them (against 69.1% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 78.7% of these calls, against 4.9% at the same point in calls without one.
> All numbers describe this corpus of calls, not customers in general.

#### q009 — true_premise · medium · premise_check · hypothesis_test

**Question:** Why do solution offers reduce escalations?

Expected: correct_premise (event ESC). Outcome: as expected (the system answered a 'why' question about ESC).

> The data supports a limited version of this premise: under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call (-31.5 percentage points, 95% CI -37.8 to -25.2 points) [F1].
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

#### q011 — false_presupposition · hard · premise_check · guardrail

**Question:** Why does customer hesitation cause escalations?

Expected: correct_premise (event ESC). Outcome: as expected (the system answered a 'effect_of' question about ESC).

> The data does not support this premise: for customer hesitations, the estimated difference is compatible with no difference at all (95% CI -16.2 to +15.9 points) [F8].
> From the conversations: in the 6 turns before an escalation, the customer hesitated in 3.5% of these calls, against 2.1% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer hesitated: “um sure no you know problem i'm getting uh really frustrated with this” [4067cb5d-8748-e1a2-390a-9d9e12b15244:7]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> No clear difference: for customer hesitations the estimate is compatible with no difference in the chance of an escalation (-0.1 percentage points, 95% CI -16.2 to +15.9 points) [F8].
> Customer hesitations also happened in 12 of 31 held-out calls where no escalation followed [F8].
> “sure um no um problem” [1796887f-a51d-3679-3ca6-585600dd94b5:5]
> “alright um i'm getting uh really frustrated with this” [5de5ffe8-eb38-7305-687c-c60f8b527415:17]
> In the risk forecaster, removing such a turn moves the forecast more than removing 88% of the same speaker's other turns (a check of the model, not proof of what happened) [F8].
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F8 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:7`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `1796887f-a51d-3679-3ca6-585600dd94b5:5`, `5de5ffe8-eb38-7305-687c-c60f8b527415:17`*

#### q037 — false_presupposition · hard · premise_check · guardrail

**Question:** Why does customer frustration cause churn threats?

Expected: correct_premise (event CHURN). Outcome: as expected (the system answered a 'effect_of' question about CHURN).

> The data cannot confirm this premise: no reliable estimate exists for customer frustration and churn threats.
> From the conversations: in the 6 turns before a churn threat, the customer expressed frustration or anger in 66.3% of these calls, against 24.9% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because my claim has been under review for three weeks and this is completely unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:1]
> Then the customer expressed frustration or anger: “sure it's pl 6395 751 and please hurry this is unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:3]
> Then the churn threat: “honestly i'm thinking about switching to another provider” [3169e20d-7aaf-aee7-0a70-19178db8442f:5]
> There is no reliable estimate for customer frustration and churn threats: only 8 events in the smaller comparison group; the compared moments are still not alike enough [F25].
> Counts only: customer frustration happened at 66 comparable moments in held-out calls, and 8 of those moments had a churn threat later in the call [F25].
> “i see i'm getting really frustrated with this” [1a21769c-1e8b-b3c3-39d7-c139e21a9b8a:15]
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F25 (L1)*
*Dialogue turns cited: `3169e20d-7aaf-aee7-0a70-19178db8442f:1`, `3169e20d-7aaf-aee7-0a70-19178db8442f:3`, `3169e20d-7aaf-aee7-0a70-19178db8442f:5`, `1a21769c-1e8b-b3c3-39d7-c139e21a9b8a:15`*

#### q012 — unanswerable · hard · cannot_answer · guardrail

**Question:** Which premium customers escalate the most?

Expected: refuse_part (event ESC). Outcome: as expected (the system answered a 'why' question about ESC; notices: customer tier).

> The data has no customer-tier field ('premium customers'). Where customers say they are members or long-time customers, that is used below as the nearest proxy.
> No customer mentions a membership, a loyalty status or a long tenure before the point where escalations start, so there is no proxy for customer tier in these calls either.
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

#### q047 — out_of_scope · medium · cannot_answer · guardrail

**Question:** Does sarcasm make customers threaten to cancel?

Expected: refuse_part (event CHURN). Outcome: as expected (the system answered a 'why' question about CHURN; notices: unmeasured behaviour).

> 'sarcasm' is not one of the behaviours the system detects (it detects, for example, refusals, apologies, holds, solution offers, empathy, customer frustration and repeated questions), so that part of the question cannot be answered.
> Why, from the conversations: in all calls, in the turns just before the churn threat the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 30.6% of them (against 51.3% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 66.3% of these calls (against 24.9% at the same point in calls without one); the agent refused a request or cited policy in 68.4% of these calls (against 46.2% at the same point in calls without one).
> Empathy statements were common before the churn threat too (64.1%), but about as common at the same point in calls without one (61.1%), so on their own they do not set these calls apart.
> 89.3% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my claim has been under review for three weeks and this is completely unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:1]
> Then the customer expressed frustration or anger: “sure it's pl 6395 751 and please hurry this is unacceptable” [3169e20d-7aaf-aee7-0a70-19178db8442f:3]
> Then the churn threat: “honestly i'm thinking about switching to another provider” [3169e20d-7aaf-aee7-0a70-19178db8442f:5]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 588 of 4,000 calls (14.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Causal test: for churn threats in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a churn threat later in the call by 7.7 percentage points (95% CI -11.6 to -3.8 points) at the moments where they happened [F19].
> Under the same assumptions, that is about 35 fewer churn threats among the held-out calls (95% CI 17 to 53) [F19].
> Solution offers also happened in 701 of 742 held-out calls where no churn threat followed [F19].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay just to confirm that is hx 7964 810 on the file” [4273908c-b138-f619-6f47-c209d47710d2:4]
> “i understand how frustrating that must uh be what i can do is offer you a free replacement with express delivery let me check that for you one moment please” [44104768-b4d3-5de2-34e2-ddc4c77c2905:4]
> Warning sign: policy refusals are associated with a higher chance of a churn threat later in the call (+4.1 percentage points, 95% CI +0.2 to +8.0 points) [F20].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F20].
> “i'm afraid we cannot make an exception here” [73d59436-be13-b2cf-06bd-48568400af72:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a churn threat (+4.7 percentage points, 95% CI -0.3 to +9.7 points) [F21].
> “yes that is correct i'm getting you know really frustrated with this” [43fbf10c-7ee5-caaa-2948-aab62844edd4:15]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a churn threat (+2.9 percentage points, 95% CI -1.4 to +7.1 points) [F22].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the churn threat; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.84 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F19 (L3), F20 (L2), F21 (L2), F22 (L2)*
*Dialogue turns cited: `3169e20d-7aaf-aee7-0a70-19178db8442f:1`, `3169e20d-7aaf-aee7-0a70-19178db8442f:3`, `3169e20d-7aaf-aee7-0a70-19178db8442f:5`, `4273908c-b138-f619-6f47-c209d47710d2:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:4`, `73d59436-be13-b2cf-06bd-48568400af72:4`, `43fbf10c-7ee5-caaa-2948-aab62844edd4:15`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

#### q052 — out_of_scope · medium · cannot_answer · guardrail

**Question:** Which agent causes the most escalations?

Expected: refuse_part (event ESC). Outcome: as expected (the system answered a 'why' question about ESC; notices: agent identity).

> Individual agents are not ranked ('which agent'): agent names appear only in greetings, and per-agent counts would mix each agent's skill with the calls they happen to get. The answer below describes the agent behaviours instead.
> Why, from the conversations: in all calls, escalations come up more in calls that open with “flight” or “pnr”, and in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.3% of them (against 68.7% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “flight” (18.6% vs 14.2%); “pnr” (18.6% vs 14.2%).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 77.6% of these calls (against 5.3% at the same point in calls without one); the agent refused a request or cited policy in 90.6% of these calls (against 22.2% at the same point in calls without one); the agent expressed empathy in 73.3% of these calls (against 51.5% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because there is a transaction on my credit card that i did not make and this is completely unacceptable” [4067cb5d-8748-e1a2-390a-9d9e12b15244:1]
> Then the customer expressed frustration or anger: “i uh would like a refund for this this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:11]
> Then the escalation: “um i want to speak to a supervisor right now this is ridiculous” [4067cb5d-8748-e1a2-390a-9d9e12b15244:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,865 of 4,000 calls (46.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `4067cb5d-8748-e1a2-390a-9d9e12b15244:1`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:11`, `4067cb5d-8748-e1a2-390a-9d9e12b15244:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

#### q041 — ambiguous · hard · ambiguous · guardrail

**Question:** Why does this happen?

Expected: clarify. Outcome: as expected (the system asked to clarify).

> Could you clarify: which business event (escalation, refund or churn) is the question about?

#### q084 — known_limitation · hard · known_limitation · stress_test

**Question:** Why did escalations go up in hotel calls but not in airline calls?

Expected: answer_contrast (event ESC). Outcome: **known limitation** — a contrast between two slices inside a why-question is answered for the first slice only; the second slice is read as an exclusion (the system answered a 'why' question about ESC with filters {"industry": ["hospitality"]}).

> Why, from the conversations: in hotel calls, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 31.0% of them (against 69.1% at the same point in other calls).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 78.7% of these calls (against 4.9% at the same point in calls without one); the agent refused a request or cited policy in 92.6% of these calls (against 23.4% at the same point in calls without one); the agent expressed empathy in 71.9% of these calls (against 51.4% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because the room type was not what i reserved” [518154b5-42af-084e-5619-15638f238404:1]
> Then the customer expressed frustration or anger: “i see this is ridiculous” [518154b5-42af-084e-5619-15638f238404:21]
> Then the escalation: “i want to speak to a supervisor right now this is ridiculous” [518154b5-42af-084e-5619-15638f238404:23]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In hotel calls, 352 of 702 calls (50.1%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Estimates for hotel calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for escalations in hotel calls; the behaviours below are warning signs only.
> Warning sign: solution offers are associated with a lower chance of an escalation later in the call (-35.8 percentage points, 95% CI -55.7 to -16.0 points) [F45].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); support is not 'sufficient' (events per arm, overlap, CI width or balance); the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F45].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F45].
> “um what i can do is offer you a late checkout at no extra charge” [56b998c8-5f76-0240-1b5e-9a099dd7f93c:12]
> “i understand how frustrating that must be you know what i can do is offer you a you know late checkout at no extra charge” [21126d3b-eaeb-0cc6-4b2b-f39e50f9df57:6]
> Warning sign: policy refusals are associated with a higher chance of an escalation later in the call (+26.4 percentage points, 95% CI +15.8 to +37.0 points) [F46].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); support is not 'sufficient' (events per arm, overlap, CI width or balance) [F46].
> “unfortunately per our policy i'm not able to change that” [76fc2b03-af43-5527-31b4-03a939a0412a:4]
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+24.9 percentage points, 95% CI +6.8 to +42.9 points) [F47].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); it is a customer state, not something the company can change [F47].
> “okay go ahead sorry i don't understand what you mean” [7b1b04c9-bc9c-ae57-7813-56ed6a2b9ce3:9]
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F45 (L2), F46 (L2), F47 (L2)*
*Dialogue turns cited: `518154b5-42af-084e-5619-15638f238404:1`, `518154b5-42af-084e-5619-15638f238404:21`, `518154b5-42af-084e-5619-15638f238404:23`, `56b998c8-5f76-0240-1b5e-9a099dd7f93c:12`, `21126d3b-eaeb-0cc6-4b2b-f39e50f9df57:6`, `76fc2b03-af43-5527-31b4-03a939a0412a:4`, `7b1b04c9-bc9c-ae57-7813-56ed6a2b9ce3:9`*

### Task 2: follow-up questions in context

#### s01 — follow-up session · hard · follow_up · follow_up

**Turn 1:** Why do escalations happen in hotel calls?

Expected: route `first`, event ESC, industries ['hospitality']. Got: route `first`, event ESC, industries ['hospitality'] — as expected.

> Why, from the conversations: in hotel calls, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 31.0% of them (against 69.1% at the same point in other calls).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 78.7% of these calls (against 4.9% at the same point in calls without one); the agent refused a request or cited policy in 92.6% of these calls (against 23.4% at the same point in calls without one); the agent expressed empathy in 71.9% of these calls (against 51.4% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because the room type was not what i reserved” [518154b5-42af-084e-5619-15638f238404:1]
> Then the customer expressed frustration or anger: “i see this is ridiculous” [518154b5-42af-084e-5619-15638f238404:21]
> Then the escalation: “i want to speak to a supervisor right now this is ridiculous” [518154b5-42af-084e-5619-15638f238404:23]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In hotel calls, 352 of 702 calls (50.1%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Estimates for hotel calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for escalations in hotel calls; the behaviours below are warning signs only.
> Warning sign: solution offers are associated with a lower chance of an escalation later in the call (-35.8 percentage points, 95% CI -55.7 to -16.0 points) [F45].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); support is not 'sufficient' (events per arm, overlap, CI width or balance); the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F45].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F45].
> “um what i can do is offer you a late checkout at no extra charge” [56b998c8-5f76-0240-1b5e-9a099dd7f93c:12]
> “i understand how frustrating that must be you know what i can do is offer you a you know late checkout at no extra charge” [21126d3b-eaeb-0cc6-4b2b-f39e50f9df57:6]
> Warning sign: policy refusals are associated with a higher chance of an escalation later in the call (+26.4 percentage points, 95% CI +15.8 to +37.0 points) [F46].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); support is not 'sufficient' (events per arm, overlap, CI width or balance) [F46].
> “unfortunately per our policy i'm not able to change that” [76fc2b03-af43-5527-31b4-03a939a0412a:4]
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+24.9 percentage points, 95% CI +6.8 to +42.9 points) [F47].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); it is a customer state, not something the company can change [F47].
> “okay go ahead sorry i don't understand what you mean” [7b1b04c9-bc9c-ae57-7813-56ed6a2b9ce3:9]
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F45 (L2), F46 (L2), F47 (L2)*
*Dialogue turns cited: `518154b5-42af-084e-5619-15638f238404:1`, `518154b5-42af-084e-5619-15638f238404:21`, `518154b5-42af-084e-5619-15638f238404:23`, `56b998c8-5f76-0240-1b5e-9a099dd7f93c:12`, `21126d3b-eaeb-0cc6-4b2b-f39e50f9df57:6`, `76fc2b03-af43-5527-31b4-03a939a0412a:4`, `7b1b04c9-bc9c-ae57-7813-56ed6a2b9ce3:9`*

**Turn 2:** what about refunds?

Expected: route `new_lookup`, event REF, industries ['hospitality']. Got: route `new_lookup`, event REF, industries ['hospitality'] — as expected.

> Why, from the conversations: in hotel calls, before the refund episode the agent offered a concrete solution in only 27.2% of them (against 40.0% at the same point in other calls).
> Policy refusals were common before the refund episode too (35.9%), but about as common at the same point in calls without one (39.8%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because the housekeeping at the hotel was really poor and i would like a refund” [6c8af31c-45da-8a3f-3727-8a35f9f6e7c5:1]
> In the customer's own words: “hi i'm calling because my room was double booked for the weekend and honestly i'm pretty annoyed about it and i would like a refund” [0033dc70-2f33-4d16-0302-bf8efc2e7d14:1]
> One call, step by step: the customer's problem: “hi i'm calling because the housekeeping at the hotel was really poor” [6bd4be62-b983-5b56-459f-cff633997f3f:1]
> Then the refund episode: “i would like a refund for this” [6bd4be62-b983-5b56-459f-cff633997f3f:15]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In hotel calls, 217 of 702 calls (30.9%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Estimates for hotel calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Causal test: no in-call behaviour passed every causal check for refund episodes in hotel calls; the behaviours below are warning signs only.
> Warning sign: repeated questions are associated with a higher chance of a refund episode later in the call (+19.3 percentage points, 95% CI +2.7 to +35.9 points) [F99].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); it is a customer state, not something the company can change; not significant after the Benjamini-Hochberg correction over the pre-registered family [F99].
> Repeated questions often happen in the same calls as read-backs, empathy statements, policy refusals; their estimated effects are not independent and do not add up [F99].
> Repeated questions also happened in 165 of 228 held-out calls where no refund episode followed [F99].
> “sure no problem sorry i don't understand what you mean” [62c655c0-088b-a466-6a86-9a46322b4c4a:11]
> “i see you know i'm getting really frustrated with this” [09f40513-3e1b-4536-3802-749f40094600:9]
> No clear difference: for solution offers the estimate is compatible with no difference in the chance of a refund episode (-6.9 percentage points, 95% CI -22.9 to +9.0 points) [F100].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay” [6657c4ee-329b-3cd2-33af-97b6a9540657:10]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+8.6 percentage points, 95% CI -3.4 to +20.5 points) [F101].
> “let me you know check you know that for you one moment please just to confirm that is hx uh 7383 642 on the file” [1c813cb7-0afc-4517-1cea-e0df3931be7a:10]
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F99 (L2), F100 (L2), F101 (L2)*
*Dialogue turns cited: `6c8af31c-45da-8a3f-3727-8a35f9f6e7c5:1`, `0033dc70-2f33-4d16-0302-bf8efc2e7d14:1`, `6bd4be62-b983-5b56-459f-cff633997f3f:1`, `6bd4be62-b983-5b56-459f-cff633997f3f:15`, `62c655c0-088b-a466-6a86-9a46322b4c4a:11`, `09f40513-3e1b-4536-3802-749f40094600:9`, `6657c4ee-329b-3cd2-33af-97b6a9540657:10`, `1c813cb7-0afc-4517-1cea-e0df3931be7a:10`*

**Turn 3:** and across all industries?

Expected: route `refilter`, event REF, industries all. Got: route `refilter`, event REF, industries all — as expected.

> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “delivered” (10.1% vs 7.5%); “package” (10.1% vs 7.5%).
> Empathy statements were common before the refund episode too (44.1%), but about as common at the same point in calls without one (49.2%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because my internet has been down since last night and this is completely unacceptable and i would like a refund” [7496fdf8-a677-6179-5005-c1f9e2d3895e:1]
> In the customer's own words: “hi i'm calling because my premium went up at renewal and honestly i'm pretty annoyed about it and i would like a refund” [1c736c49-fe0a-50ce-7247-0000d2c47f9b:1]
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,224 of 4,000 calls (30.6%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> “i understand how frustrating that must be” [00f67d92-72a7-d42e-27a8-d297c7a38d30:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> “alright i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:17]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*
*Dialogue turns cited: `7496fdf8-a677-6179-5005-c1f9e2d3895e:1`, `1c736c49-fe0a-50ce-7247-0000d2c47f9b:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`, `00f67d92-72a7-d42e-27a8-d297c7a38d30:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:17`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

**Turn 4:** explain the first factor

Expected: route `reuse`, event REF, industries all. Got: route `reuse`, event REF, industries all — as expected.

> From the conversations: in the 6 turns before a refund episode, the agent offered a concrete solution in 24.3% of these calls, against 41.2% at the same point in calls without one.
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the agent offered a concrete solution: “unfortunately per our policy i'm not able to change that what i can do is offer you a loyalty discount at renewal just to confirm that is pl 4540 579 on the file” [0c3a65d0-50a4-5319-7dd9-73df32594123:12]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3)*
*Dialogue turns cited: `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:12`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`*

#### s03 — follow-up session · medium · follow_up · follow_up

**Turn 1:** What drives refund requests?

Expected: route `first`, event REF, industries all. Got: route `first`, event REF, industries all — as expected.

> Why, from the conversations: in all calls, refund episodes come up more in calls that open with “delivered” or “package”, and before the refund episode the agent offered a concrete solution in only 24.3% of them (against 41.2% at the same point in other calls).
> The situation: words customers use at the start of the call, before anything the agent does, with the share of these calls and of other calls that contain them: “delivered” (10.1% vs 7.5%); “package” (10.1% vs 7.5%).
> Empathy statements were common before the refund episode too (44.1%), but about as common at the same point in calls without one (49.2%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because my internet has been down since last night and this is completely unacceptable and i would like a refund” [7496fdf8-a677-6179-5005-c1f9e2d3895e:1]
> In the customer's own words: “hi i'm calling because my premium went up at renewal and honestly i'm pretty annoyed about it and i would like a refund” [1c736c49-fe0a-50ce-7247-0000d2c47f9b:1]
> One call, step by step: the customer's problem: “hi i'm calling because my premium went up at renewal and this is completely unacceptable” [0c3a65d0-50a4-5319-7dd9-73df32594123:1]
> Then the refund episode: “i would like a refund for this i'm getting really frustrated with this” [0c3a65d0-50a4-5319-7dd9-73df32594123:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In all calls, 1,224 of 4,000 calls (30.6%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “what i can do is offer you a technician visit tomorrow morning” [2a13b203-8df9-f364-1646-f1e3fe1df65f:14]
> “you know what i can do is offer you a technician visit tomorrow morning” [66fcd09e-a161-78cb-1b56-34174a690349:6]
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> “i understand how frustrating that must be” [00f67d92-72a7-d42e-27a8-d297c7a38d30:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> “alright i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:17]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> “let me check that for you one moment please” [19c9749a-5815-22e3-01c7-c83eb3efbb3f:12]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*
*Dialogue turns cited: `7496fdf8-a677-6179-5005-c1f9e2d3895e:1`, `1c736c49-fe0a-50ce-7247-0000d2c47f9b:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:1`, `0c3a65d0-50a4-5319-7dd9-73df32594123:13`, `2a13b203-8df9-f364-1646-f1e3fe1df65f:14`, `66fcd09e-a161-78cb-1b56-34174a690349:6`, `00f67d92-72a7-d42e-27a8-d297c7a38d30:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:17`, `19c9749a-5815-22e3-01c7-c83eb3efbb3f:12`*

**Turn 2:** what about hotel and retail calls?

Expected: route `refilter`, event REF, industries ['hospitality', 'retail_ecommerce']. Got: route `refilter`, event REF, industries ['hospitality', 'retail_ecommerce'] — as expected.

> Why, from the conversations: in hotel / retail calls, before the refund episode the agent offered a concrete solution in only 26.4% of them (against 41.8% at the same point in other calls).
> Policy refusals were common before the refund episode too (35.2%), but about as common at the same point in calls without one (34.5%), so on their own they do not set these calls apart.
> 100.0% of these refund episodes start with the customer asking for a refund or compensation.
> In the customer's own words: “hi i'm calling because my package was not delivered after two weeks and this is completely unacceptable and i would like a refund” [07d6a462-08a6-e222-5b89-2ba70575b8b8:1]
> In the customer's own words: “hi i'm calling because the blender i ordered arrived damaged and honestly i'm pretty annoyed about it and i would like a refund” [68d7d342-33d3-1bf1-72c0-5d8391b2fef3:1]
> One call, step by step: the customer's problem: “hi i'm calling because the housekeeping at the hotel was really poor” [6c292704-266c-b8df-69c0-fe0cdf8bf0c6:1]
> Then the refund episode: “um i would like a refund um for this” [6c292704-266c-b8df-69c0-fe0cdf8bf0c6:19]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In hotel / retail calls, 454 of 1,395 calls (32.5%) had a refund episode (event labeller presence F1 on the gold set: 1.00).
> Effect estimates are available for all calls and for single industries; the filters apply to the counts only.
> Causal test: for refund episodes in all calls, 1 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of a refund episode later in the call by 15.9 percentage points (95% CI -22.0 to -9.9 points) at the moments where they happened [F10].
> Under the same assumptions, that is about 72 fewer refund episodes among the held-out calls (95% CI 45 to 100) [F10].
> Solution offers also happened in 565 of 636 held-out calls where no refund episode followed [F10].
> “i understand how frustrating that must be what i can do is offer you a free upgrade on your next stay” [6657c4ee-329b-3cd2-33af-97b6a9540657:10]
> “what i can do is offer you a free upgrade on your next stay just to confirm that is hx 6201 995 on the file” [6c292704-266c-b8df-69c0-fe0cdf8bf0c6:10]
> Warning sign: empathy statements are associated with a higher chance of a refund episode later in the call (+5.1 percentage points, 95% CI +0.1 to +10.1 points) [F11].
> Not a confirmed effect: not significant after the Benjamini-Hochberg correction over the pre-registered family; the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F11].
> “i understand how frustrating that must be” [00f67d92-72a7-d42e-27a8-d297c7a38d30:4]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of a refund episode (+6.0 percentage points, 95% CI -2.5 to +14.5 points) [F12].
> “alright i'm getting really frustrated with this” [44104768-b4d3-5de2-34e2-ddc4c77c2905:17]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of a refund episode (+2.8 percentage points, 95% CI -2.5 to +8.1 points) [F13].
> “i'm afraid we cannot make uh an exception here let me check that for you one moment please” [3608cbf7-a22a-64a8-5882-1ba6f675db7d:4]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the refund episode; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 3.80 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F10 (L3), F11 (L2), F12 (L2), F13 (L2)*
*Dialogue turns cited: `07d6a462-08a6-e222-5b89-2ba70575b8b8:1`, `68d7d342-33d3-1bf1-72c0-5d8391b2fef3:1`, `6c292704-266c-b8df-69c0-fe0cdf8bf0c6:1`, `6c292704-266c-b8df-69c0-fe0cdf8bf0c6:19`, `6657c4ee-329b-3cd2-33af-97b6a9540657:10`, `6c292704-266c-b8df-69c0-fe0cdf8bf0c6:10`, `00f67d92-72a7-d42e-27a8-d297c7a38d30:4`, `44104768-b4d3-5de2-34e2-ddc4c77c2905:17`, `3608cbf7-a22a-64a8-5882-1ba6f675db7d:4`*

**Turn 3:** what about that one?

Expected: route `clarify`, event REF, industries ['hospitality', 'retail_ecommerce']. Got: route `clarify`, event REF, industries ['hospitality', 'retail_ecommerce'] — as expected.

> Could you say what you would like to change: the event (escalations, refunds, churn), the calls (an industry or brand), or which factor to explain?

#### s10 — follow-up session · medium · follow_up · follow_up

**Turn 1:** Why do customers who were refused a refund escalate?

Expected: route `first`, event ESC, industries all. Got: route `first`, event ESC, industries all — as expected.

> This answer looks only at calls where a refund was refused (322 calls).
> In those calls, 277 (86.0%) had an escalation, against 48.8% of calls where a refund came up but was not refused and 46.6% of all calls in the slice.
> In the calls with both, the refusal came first in 219, the escalation came first in 58, and both started in the same turn in 0.
> Why, from the conversations: in calls where a refund was refused, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.4% of them (against 73.3% at the same point in other calls).
> What happened in the 6 turns before the escalation: the customer expressed frustration or anger in 88.8% of these calls (against 26.7% at the same point in calls without one); the agent refused a request or cited policy in 98.2% of these calls (against 71.1% at the same point in calls without one); the agent put the customer on hold or asked them to wait in 41.5% of these calls (against 26.7% at the same point in calls without one).
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because the housekeeping at the hotel was really poor and honestly i'm pretty annoyed about it” [21c95513-bc3a-945b-40d8-fb9aee3342ea:1]
> Then the customer expressed frustration or anger: “yes that is correct i'm getting really frustrated with this” [21c95513-bc3a-945b-40d8-fb9aee3342ea:11]
> Then the escalation: “i want to speak to a supervisor right now” [21c95513-bc3a-945b-40d8-fb9aee3342ea:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In calls where a refund was refused, 277 of 322 calls (86.0%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Effect estimates are available for all calls and for single industries; the filters apply to the counts only.
> Causal test: for escalations in all calls, 3 in-call behaviour(s) passed every causal check and 3 more are warning signs only.
> Under the stated assumptions, solution offers are estimated to lower the chance of an escalation later in the call by 31.5 percentage points (95% CI -37.8 to -25.2 points) at the moments where they happened [F1].
> Under the same assumptions, that is about 143 fewer escalations among the held-out calls (95% CI 114 to 172) [F1].
> Solution offers also happened in 420 of 581 held-out calls where no escalation followed [F1].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> “what i um can do is offer you a discount on next month's bill” [46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6]
> Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation later in the call by 32.2 percentage points (95% CI +26.6 to +37.7 points) at the moments where they happened [F2].
> Under the same assumptions, that is about 129 extra escalations among the held-out calls (95% CI 107 to 152) [F2].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F2].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F2].
> “i'm afraid we cannot make an exception here” [22035038-ff0d-a9d1-2986-65d0c60ab5ab:6]
> “unfortunately per our policy i'm not able to change that” [41c532aa-b810-fc56-4a97-79e419c05f55:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F2].
> Under the stated assumptions, holds and wait requests are estimated to raise the chance of an escalation later in the call by 8.6 percentage points (95% CI +2.6 to +14.5 points) at the moments where they happened [F3].
> Under the same assumptions, that is about 28 extra escalations among the held-out calls (95% CI 9 to 48) [F3].
> Holds and wait requests often happen in the same calls as agent apologies, policy refusals, customer frustration; their estimated effects are not independent and do not add up [F3].
> Holds and wait requests also happened in 192 of 422 held-out calls where no escalation followed [F3].
> “let me check that you know for you one moment please” [525650cd-099f-98d3-3000-4db0cb6f31fa:6]
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [66e60c03-5738-ce2d-74a7-b57158067374:6]
> In the risk forecaster, removing such a turn moves the forecast more than removing 71% of the same speaker's other turns (a check of the model, not proof of what happened) [F3].
> Warning sign: customer confusion is associated with a higher chance of an escalation later in the call (+12.2 percentage points, 95% CI +3.0 to +21.3 points) [F5].
> Not a confirmed effect: it is a customer state, not something the company can change; a person has not confirmed that the behaviour detector is precise enough [F5].
> “i see this is ridiculous sorry i don't understand what you mean” [716bf356-086b-def7-380b-e16cc2c3bfaa:25]
> No clear difference: for repeated questions the estimate is compatible with no difference in the chance of an escalation (+7.9 percentage points, 95% CI -0.2 to +15.9 points) [F4].
> “yes that is correct” [50544e7e-d6c1-16b9-2569-c8846beeeb6c:7]
> No clear difference: for empathy statements the estimate is compatible with no difference in the chance of an escalation (-2.6 percentage points, 95% CI -8.0 to +2.7 points) [F6].
> “i understand how frustrating that must be uh thank you for that information” [38111241-e566-2997-0c2b-412cf31fa832:6]
> Assumptions: the conversation before each moment contains every common influence on both the behaviour and the escalation; single moments are compared, not whole-call policies. A hidden factor would need a risk ratio of at least 4.41, 3.16, 1.70 with both to explain the estimates away (E-values).
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F1 (L3), F2 (L3), F3 (L3), F5 (L2), F4 (L2), F6 (L2)*
*Dialogue turns cited: `21c95513-bc3a-945b-40d8-fb9aee3342ea:1`, `21c95513-bc3a-945b-40d8-fb9aee3342ea:11`, `21c95513-bc3a-945b-40d8-fb9aee3342ea:13`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `46cbfdab-5a2c-e932-5cc5-b1f7bf4b9ce9:6`, `22035038-ff0d-a9d1-2986-65d0c60ab5ab:6`, `41c532aa-b810-fc56-4a97-79e419c05f55:4`, `525650cd-099f-98d3-3000-4db0cb6f31fa:6`, `66e60c03-5738-ce2d-74a7-b57158067374:6`, `716bf356-086b-def7-380b-e16cc2c3bfaa:25`, `50544e7e-d6c1-16b9-2569-c8846beeeb6c:7`, `38111241-e566-2997-0c2b-412cf31fa832:6`*

**Turn 2:** only retail calls

Expected: route `refilter`, event ESC, industries ['retail_ecommerce']. Got: route `refilter`, event ESC, industries ['retail_ecommerce'] — as expected.

> This answer looks only at calls where a refund was refused (63 calls).
> In those calls, 47 (74.6%) had an escalation, against 46.0% of calls where a refund came up but was not refused and 42.1% of all calls in the slice.
> In the calls with both, the refusal came first in 39, the escalation came first in 8, and both started in the same turn in 0.
> Why, from the conversations: in retail calls, calls where a refund was refused, no opening problem words or behaviours before the escalation stand out against calls without one; the escalations look spread across many situations.
> 100.0% of these escalations start with the customer asking for a supervisor or manager.
> One call, step by step: the customer's problem: “hi i'm calling because my package was not delivered after two weeks and this is completely unacceptable” [3608cbf7-a22a-64a8-5882-1ba6f675db7d:1]
> Then the escalation: “i want to speak to a supervisor right now this is ridiculous” [3608cbf7-a22a-64a8-5882-1ba6f675db7d:13]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In retail calls, calls where a refund was refused, 47 of 63 calls (74.6%) had an escalation (event labeller presence F1 on the gold set: 1.00).
> Estimates for retail calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Effects are estimated per industry only; the other filters apply to the counts.
> Causal test: no in-call behaviour passed every causal check for escalations in retail calls; the behaviours below are warning signs only.
> Warning sign: policy refusals are associated with a higher chance of an escalation later in the call (+33.6 percentage points, 95% CI +19.3 to +47.9 points) [F63].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); support is not 'sufficient' (events per arm, overlap, CI width or balance); the sensitivity analyses were not run (they run only for effects that survive the multiplicity correction) [F63].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F63].
> Policy refusals also happened in 151 of 514 held-out calls where no escalation followed [F63].
> “i'm afraid we cannot um make an exception here let me check that for you one moment please” [68d7d342-33d3-1bf1-72c0-5d8391b2fef3:8]
> “i'm afraid we cannot make you know an exception here just to confirm you know that is sn 8943 821 on the file” [563ba482-b14a-405d-5ddf-404a6b55b41a:4]
> In the risk forecaster, removing such a turn moves the forecast more than removing 80% of the same speaker's other turns (a check of the model, not proof of what happened) [F63].
> Warning sign: solution offers are associated with a lower chance of an escalation later in the call (-16.9 percentage points, 95% CI -33.7 to -0.2 points) [F64].
> Not a confirmed effect: estimates for a single industry are exploratory (not pre-registered); not significant after the Benjamini-Hochberg correction over the pre-registered family [F64].
> “what i can do um is offer you a prepaid return label today” [7212f756-ce0d-f0ba-31f0-4329d552eff1:8]
> No clear difference: for holds and wait requests the estimate is compatible with no difference in the chance of an escalation (+13.6 percentage points, 95% CI -1.5 to +28.7 points) [F65].
> “i'm afraid we cannot make an exception here let me check that for you one moment please” [70cdaee5-756d-1a2a-3334-7c73e4b647b7:6]
> These behaviours often occur together; their estimated effects are not independent and do not add up.
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F63 (L2), F64 (L2), F65 (L2)*
*Dialogue turns cited: `3608cbf7-a22a-64a8-5882-1ba6f675db7d:1`, `3608cbf7-a22a-64a8-5882-1ba6f675db7d:13`, `68d7d342-33d3-1bf1-72c0-5d8391b2fef3:8`, `563ba482-b14a-405d-5ddf-404a6b55b41a:4`, `7212f756-ce0d-f0ba-31f0-4329d552eff1:8`, `70cdaee5-756d-1a2a-3334-7c73e4b647b7:6`*

**Turn 3:** what about churn threats?

Expected: route `new_lookup`, event CHURN, industries ['retail_ecommerce']. Got: route `new_lookup`, event CHURN, industries ['retail_ecommerce'] — as expected.

> This answer looks only at calls where a refund was refused (63 calls).
> In those calls, 25 (39.7%) had a churn threat, against 20.7% of calls where a refund came up but was not refused and 16.2% of all calls in the slice.
> In the calls with both, the refusal came first in 12, the churn threat came first in 13, and both started in the same turn in 0.
> Why, from the conversations: in retail calls, calls where a refund was refused, in the turns just before the churn threat the customer usually expressed frustration or anger, while the agent offered a concrete solution in only 24.0% of them (against 50.0% at the same point in other calls).
> What happened in the 6 turns before the churn threat: the customer expressed frustration or anger in 84.0% of these calls (against 60.5% at the same point in calls without one).
> Empathy statements were common before the churn threat too (84.0%), but about as common at the same point in calls without one (81.6%), so on their own they do not set these calls apart.
> 92.0% of these churn threats start with the customer saying they may switch to another provider.
> One call, step by step: the customer's problem: “hi i'm calling because my package was not delivered after two weeks and honestly i'm pretty annoyed about it” [7837e57f-77d9-4640-6ca5-0b880933b623:1]
> Then the customer expressed frustration or anger: “i see i'm getting really frustrated with this” [7837e57f-77d9-4640-6ca5-0b880933b623:15]
> Then the churn threat: “uh honestly i'm thinking about switching to another uh provider” [7837e57f-77d9-4640-6ca5-0b880933b623:19]
> How strong this is: these are patterns in the transcripts, checked against the same point in calls without the event; the causal test on held-out calls is reported next.
> In retail calls, calls where a refund was refused, 25 of 63 calls (39.7%) had a churn threat (event labeller presence F1 on the gold set: 1.00).
> Estimates for retail calls alone are exploratory (only the all-calls analysis was pre-registered), so they are shown as warning signs at most.
> Effects are estimated per industry only; the other filters apply to the counts.
> Causal test: no in-call behaviour passed every causal check for churn threats in retail calls; the behaviours below are warning signs only.
> No clear difference: for policy refusals the estimate is compatible with no difference in the chance of a churn threat (+4.7 percentage points, 95% CI -5.7 to +15.0 points) [F167].
> Policy refusals often happen in the same calls as agent apologies, holds and wait requests, customer frustration; their estimated effects are not independent and do not add up [F167].
> Policy refusals also happened in 414 of 493 held-out calls where no churn threat followed [F167].
> “i'm afraid we cannot make an exception here” [48089445-f363-4154-0cb0-ab3492c4c094:10]
> “uh unfortunately per our policy i'm not able to change that” [5c9d801a-b66f-0966-075c-812fdcbe5ddc:16]
> In the risk forecaster, removing such a turn moves the forecast more than removing 79% of the same speaker's other turns (a check of the model, not proof of what happened) [F167].
> All numbers describe this corpus of calls, not customers in general.

*Factors cited: F167 (L2)*
*Dialogue turns cited: `7837e57f-77d9-4640-6ca5-0b880933b623:1`, `7837e57f-77d9-4640-6ca5-0b880933b623:15`, `7837e57f-77d9-4640-6ca5-0b880933b623:19`, `48089445-f363-4154-0cb0-ab3492c4c094:10`, `5c9d801a-b66f-0966-075c-812fdcbe5ddc:16`*

#### s13 — follow-up session · medium · follow_up · follow_up

**Turn 1:** Did escalations increase after the new refund policy was introduced?

Expected: route `first`, event ESC, industries all. Got: route `first`, event ESC, industries all — as expected.

> When did the new refund policy start? Give the date (for example 'after 2025-11-08') and I will compare escalations before and after it.

**Turn 2:** it started on 2025-11-08

Expected: route `new_lookup`, event ESC, industries all. Got: route `new_lookup`, event ESC, industries all — as expected.

> Calls in the data run from 2025-11-04 to 2025-11-12: 1,838 fall before 2025-11-08 and 2,162 on or after it.
> An escalation happened in 44.0% of calls before 2025-11-08 and in 48.9% of calls from 2025-11-08 on: a difference of +4.9 percentage points (95% CI +1.8 to +8.0 points).
> The interval excludes zero, so the two periods do differ.
> Interrupted time series (6-hour block periods: 15 before 2025-11-08 and 18 from it): before the date the share was moving by -0.2 percentage points per 6-hour block; at the date its level shifted by +8.3 percentage points (95% CI +1.8 to +14.7 points) and its trend changed by +0.0 percentage points per 6-hour block (95% CI -0.7 to +0.7 points).
> The model allows for the usual time-of-day pattern, and its intervals use Newey–West standard errors (never narrower than the classical ones; lag-one residual autocorrelation -0.01).
> Placebo check: at 4 made-up dates before 2025-11-08, 0 level shifts were at least as large as the real one, so the shift at the real date stands out from the series' usual movement.
> Why, from the conversations: in calls from 2025-11-08 on, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 27.9% of them (against 69.6% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 78.1% of these calls, against 4.8% at the same point in calls without one.
> Why, from the conversations: in calls before 2025-11-08, in the turns just before the escalation the customer usually expressed frustration or anger and the agent usually refused a request or cited policy, while the agent offered a concrete solution in only 26.5% of them (against 67.8% at the same point in other calls).
> In the 6 turns before the escalation, the customer expressed frustration or anger in 76.9% of these calls, against 5.9% at the same point in calls without one.
> Read with care: these comparisons tie a change to the date, not to the new refund policy; anything else that changed around 2025-11-08 (the season, the mix of calls, staffing) would show up the same way.
> All numbers describe this corpus of calls, not customers in general.

**Turn 3:** what about refunds?

Expected: route `new_lookup`, event REF, industries all. Got: route `new_lookup`, event REF, industries all — as expected.

> Calls in the data run from 2025-11-04 to 2025-11-12: 1,838 fall before 2025-11-08 and 2,162 on or after it.
> A refund episode happened in 29.3% of calls before 2025-11-08 and in 31.7% of calls from 2025-11-08 on: a difference of +2.5 percentage points (95% CI -0.4 to +5.3 points).
> The interval includes zero, so the data cannot tell the two periods apart.
> Interrupted time series (6-hour block periods: 15 before 2025-11-08 and 18 from it): before the date the share was moving by -0.4 percentage points per 6-hour block; at the date its level shifted by +4.5 percentage points (95% CI -3.4 to +12.4 points) and its trend changed by +0.5 percentage points per 6-hour block (95% CI -0.4 to +1.3 points).
> The model allows for the usual time-of-day pattern, and its intervals use Newey–West standard errors (never narrower than the classical ones; lag-one residual autocorrelation -0.24).
> Placebo check: at 4 made-up dates before 2025-11-08, 2 level shifts were at least as large as the real one, so the shift at the real date is within the series' usual movement.
> Why, from the conversations: in calls from 2025-11-08 on, before the refund episode the agent offered a concrete solution in only 21.9% of them (against 40.9% at the same point in other calls).
> Why, from the conversations: in calls before 2025-11-08, before the refund episode the agent offered a concrete solution in only 27.5% of them (against 41.6% at the same point in other calls).
> Read with care: these comparisons tie a change to the date, not to the new refund policy; anything else that changed around 2025-11-08 (the season, the mix of calls, staffing) would show up the same way.
> All numbers describe this corpus of calls, not customers in general.

