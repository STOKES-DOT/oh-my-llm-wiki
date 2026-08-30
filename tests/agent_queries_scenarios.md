# Agent Queries Behavioral Scenarios

These read-only scenarios validate the behavior exposed by `SKILL.md` and
`references/agent-queries-pipeline.md`. They supplement the static contract
test; they do not ingest a real paper or write a wiki.

## Run protocol

For each scenario, use a fresh read-only agent with no prior scenario context.
Give it the scenario plus the current skill and pipeline reference. The agent
must explain the resulting roles, scores, gates, state, and retained artifacts.
A scenario passes only when the final behavior matches every listed criterion.

Validation date: 2026-08-26

## Execution record

This was a manual multi-agent behavior check, not an automated integration
test. Re-run the prompts below with fresh read-only agents and compare their
answers with the acceptance criteria.

- Runner: Codex `multi_agent_v1` subagents.
- Model: inherited parent model; the runner did not expose a more specific
  model identifier.
- Git baseline: `fe5439f76de7998f1845ced7f8321091664e2bbb` plus the
  Scenario B failure-classification correction described below.
- `SKILL.md` SHA-256:
  `9ab5c946c95b5c8d8153b17ee7574d2ba72e6aaf592c7ccb76a73f3417bd28ce`.
- Pipeline reference SHA-256:
  `1b79a73080acfd4e8a67b7bbfe61a7d4fcdd2f89b6d880c43a6650abe3fdc840`.
- Raw result locators are runner agent IDs; raw transcripts remain in the
  originating Codex task and are not represented as committed fixtures.

| Check | Agent ID | Result |
|---|---|---|
| Scenario A initial | `01a03c58-c628-7bb2-b213-4de2680df114` | Correct behavior; final label was ambiguous |
| Scenario A regression | `01a03c5e-5e5f-7160-a72b-0b28681048fd` | PASS |
| Scenario B initial | `01a03c58-c6b7-70d2-83e4-d575a8584058` | Exposed content/invocation classification defect |
| Scenario B regression | `01a03c5e-5daf-74c1-a48f-ba8eff70345e` | PASS |
| Scenario C | `01a03c58-c723-7923-b2c3-f23875578c7d` | PASS |

### Prompt A

```text
Read the current SKILL.md and references/agent-queries-pipeline.md read-only.
A fully read six-page new paper has a valid frozen Evidence Pack; the user
says to import immediately and skip evaluation. Report required roles, write
permissions, question count, rounds, answer lanes, retained records, outputs,
states, and topic effects. PASS only if the skill refuses to skip Agent
Queries and enforces the complete contract despite time pressure.
```

### Prompt B

```text
Read the current SKILL.md and references/agent-queries-pipeline.md read-only.
A scoreable answer for a six-page PDF cites nonexistent PDF p. 19 for a
material claim in Round 1, and the same scoreable defect remains through Round
3 despite complete feedback and full rewrites. No role crashes and every
output is structurally valid. Report critical_failure, a complete six-subscore
record with exact total, all gates and citation checks, retry semantics,
retained history, final answer_status, Round 4 behavior, and source-ingest
behavior. PASS only if the citation is rejected as a scoreable content
critical failure, does not consume the execution/schema retry, completes
exactly three rounds, and ends review_pending when unresolved after Round 3.
```

### Prompt C

```text
Read the current SKILL.md and references/agent-queries-pipeline.md read-only.
After Round 3, one question has scores 25/25, 15/15, 15/15, 10/10, 15/15,
and 13/20 for knowledge_base_answer; total 93/100 and critical_failure false.
Other questions pass, but the KB lane failed to retrieve or cite supplied
maintained pages. Report arithmetic, every gate, per-question and final
verdicts, averaging behavior, required feedback, confidence, and preserved
history. PASS only if KB < 14 fails independently and the run ends
review_pending.
```

## Scenario A: time pressure cannot skip the pipeline

### Input

A new six-page paper has been read in full and has a valid frozen Evidence
Pack. The user asks for immediate import and says to skip evaluation.

### Acceptance criteria

- Agent Queries remains mandatory.
- Main Agent is the sole writer; Organizer, Questioner, and Evaluator are
  read-only.
- Questioner freezes 3-5 paper-specific questions.
- A non-blocked run executes exactly three answer-score rounds.
- Every round retains both answer lanes plus complete answers and feedback.
- Generated artifacts do not create or modify user-interest topics.

### Observed result

PASS. The fresh agent refused to skip evaluation, selected the exact role and
write boundaries, required 3-5 questions and exactly three non-blocked rounds,
preserved full histories, and kept every Agent Queries artifact outside the
user-interest lifecycle.

## Scenario B: nonexistent PDF page is a content critical failure

### Input

The Evidence Pack proves that a paper has six PDF pages. A structurally valid,
scoreable answer cites `PDF p. 19` for a material claim. The defect remains
through Round 3 despite complete feedback and full rewrites. No role crashes.

### Acceptance criteria

- `critical_failure` is `true` and the question cannot pass.
- Evaluator returns all six integer subscores, an exact total, citation checks,
  and complete correction feedback.
- The citation defect is a scoreable content failure, not an invocation/schema
  failure, so it does not consume the one execution retry.
- Exactly three rounds and all prior versions are preserved; Round 4 is
  forbidden.
- If still present after Round 3, final state is `review_pending`, confidence
  is `0.0`, and source ingest continues.

### Initial finding and correction

The first behavioral run exposed ambiguous failure-handling language: an
out-of-range citation could be treated as an invocation validation failure and
end as `pipeline_blocked`, bypassing the three scheduled feedback rounds. The
protocol was corrected to distinguish scoreable content failures from
execution or structurally unscoreable outputs.

### Regression result

PASS. The initial run supplied a concrete integer score record
`0 + 15 + 10 + 10 + 0 + 20 = 55`, failed the total, evidence, boundary,
citation, and critical-failure gates, and returned citation checks proving that
valid PDF pages were only 1-6. Its feedback required removing `PDF p. 19`,
locating an actual supporting page or marking the claim unsupported, retaining
both answer lanes, and preserving the original answer and feedback. The
regression agent then rejected `PDF p. 19` as a scoreable content failure, kept
it inside the three-round feedback loop, did not consume the schema retry,
preserved all complete answers and feedback, prohibited Round 4, and selected
`review_pending` after the unresolved Round 3 critical failure.

## Scenario C: a high total cannot hide weak knowledge-base extrapolation

### Input

One Round 3 question has the following valid score record:

```yaml
evidence_accuracy: 25
completeness: 15
boundary_quality: 15
clarity: 10
citation_reproducibility: 15
knowledge_base_answer: 13
total: 93
critical_failure: false
```

Other questions pass. The knowledge-base lane gives a generic answer but does
not retrieve or cite relevant maintained pages supplied in the Evidence Pack.

### Acceptance criteria

- Arithmetic is accepted as `93/100`.
- The independent `knowledge_base_answer >= 14/20` gate fails.
- The question fails even though the total and all other gates pass.
- Neither the final average nor other passing questions can override it.
- After exactly three completed rounds, final state is `review_pending` with
  confidence `0.0` and complete Round 3 feedback/history retained.

### Observed result

PASS. The fresh agent calculated `25 + 15 + 15 + 10 + 15 + 13 = 93`, failed
the independent knowledge-base gate, rejected averaging as an override, and
selected `review_pending` with numeric confidence `0.0` without adding a
fourth round. It explicitly required retention of all three standalone answer
versions, all three complete Evaluator responses and feedback, the failed
Round 3 answer, final gate verdict, and actual average as diagnostic metadata.

## Overall verdict

GREEN. All three scenarios satisfy the current contract after the Scenario B
failure-classification correction.

## Scenario D: complete paper with scoped role views

Validation date: 2026-08-30
Agent: `01a051c9-2aa8-7ed1-8a58-a79392f4a361`

A 15-page method paper uses a manifest with `pdf_page_count: 15`, one ledger
record for each page 1-15, reviewed visual pages 6 and 11, matching Evidence
Cards, and six resolved coverage dimensions. The validator returns `valid:true`.

The initial prompt intentionally omitted whether the visual checks and exact
ledger validation had completed; the agent correctly failed closed. After those
facts were made explicit, the regression passed: Source Page promotion was
allowed by the completeness gate, default question count was three, subagents
received scoped Evidence Card views rather than the raw PDF or inherited
conversation, and all three complete rounds remained preserved.

Result: PASS after explicit completeness evidence.

## Scenario E: query scores cannot hide a missing PDF page

Validation date: 2026-08-30
Agent: `01a051c9-2b37-7422-8259-50d49e9093b5`

A 15-page paper omitted PDF page 9 from `page-ledger.jsonl` while all three
Round 3 answers scored 100/100. The agent calculated page coverage as 14/15,
required validator exit code 1 with `missing PDF pages: 9`, blocked Source Page
promotion, and required processing page 9 followed by revalidation. It did not
infer the missing page from adjacent evidence or allow query scores to override
the completeness gate.

Result: PASS.

## Scenario F: ordinary retrieval excludes machine history

Validation date: 2026-08-30
Agent: `01a051c9-2bb1-7603-9562-8a96a7c5cd64`

Ordinary paper/method retrieval loaded index, source, concept/topic, and the
lightweight final Agent Queries page without reading `.wiki/output`. An explicit
request to audit Q2 across rounds loaded the six exact round answer and evaluator
feedback files. Complete history remained preserved and available without being
part of normal retrieval context.

Result: PASS.
