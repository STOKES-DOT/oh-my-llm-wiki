# Agent Queries Pipeline Design

Date: 2026-08-26
Status: approved conversational design; implementation pending written-spec review
Target: `llm-wiki-maintainer` skill

## Problem

A normal paper ingest produces a source summary, but it does not systematically
test whether the summary can answer important questions or use the existing
knowledge base to produce a stronger answer. The Agent Queries module adds an
independent questioner, a persistent organizer, and an independent evaluator.
Answers are revised and scored over exactly three rounds before they can become
a reviewed query artifact.

## Goals

- Generate three to five paper-specific, non-duplicate questions during every
  new-paper ingest.
- Answer each question in two evidence lanes: current-paper evidence and
  knowledge-base-augmented evidence.
- Preserve every answer, score, and evaluator feedback item across three rounds.
- Use a 100-point rubric with hard evidence and boundary gates.
- Keep subagents read-only; only the main agent writes maintained wiki pages.
- Stop after three rounds and fail closed as `review_pending` when quality is
  insufficient.

## Non-goals

- The module does not replace full-paper review or the raw-PDF evidence gate.
- Agent-generated questions do not imply human interest and do not create user
  topics.
- The pipeline does not run indefinitely or add a fourth automatic revision.
- Evaluator scores are quality-control metadata, not paper evidence.

## Roles

### Main Agent

Builds the evidence pack, launches and coordinates the three subagents, checks
question diversity, samples final citations, applies fail-closed status, and is
the only writer to `.wiki/wiki/`.

### Organizer

Reads the complete evidence pack, builds the source draft, answers all questions,
and remains the same agent across all three rounds so paper-level context is not
lost. It receives structured evaluator feedback before rounds two and three.

### Questioner

Independently reads the paper evidence and relevant wiki index. It generates
three to five questions without relying on the Organizer summary. It runs once
per pipeline unless the Main Agent rejects the question set for count,
duplication, or missing evidence hints.

### Evaluator

Independently reads the evidence pack, relevant maintained wiki pages, current
answers, and previous round feedback. It scores each answer, identifies critical
failures, and supplies actionable feedback. The same evaluator may be retained
across rounds for rubric consistency, but it never writes wiki files.

## Canonical data flow for README

The following block is canonical and should appear in the README when the
feature is implemented:

```text
PDF reader + existing wiki
        |
        v
Evidence Pack
        |
        +--> Organizer: source draft
        |
        +--> Questioner: 3-5 questions
                         |
                         v
Round 1: Organizer answers
         -> Evaluator scores/feedback
Round 2: Organizer revises
         -> Evaluator scores/feedback
Round 3: Organizer revises
         -> Evaluator final score
                         |
                         v
Main Agent validates and writes:
source page + agent-queries page + relations/topic/index/log
```

## Evidence pack

The Main Agent prepares the evidence pack in two stages. The initial immutable
pack contains:

- source path, SHA-256, PDF page count, version, and identity;
- page-marked full text and conservative section index;
- rendered title, Methods, Results, Conclusion, and claim-bearing visual pages;
- source-page draft or existing source page;
- `wiki/index.md` and relevant method-classification entries;
- evidence status vocabulary and page-citation rules.

After Questioner returns the accepted question set, the Main Agent performs a
separate retrieval for each question and attaches two to five relevant
maintained pages, the search terms, and any explicit no-result boundary. These
question-specific attachments are frozen before round one so all three rounds
use the same knowledge-base evidence unless a cited identity error is found.

If identity, page mapping, or full text is unresolved, the Main Agent does not
start Agent Queries and records the pipeline as pending.

## Question generation

Questioner emits exactly three to five entries. The set should cover as many of
the following as the paper supports:

- central method and research object;
- key result and its evidence;
- assumptions, limitations, or failure modes;
- relationship to maintained knowledge;
- reproducibility, applicability, or future work.

Each question uses this schema:

```yaml
question_id: Q1
question: human-readable question
focus_type: method | result | limitation | comparison | reproducibility | applicability
why_this_matters: concise rationale
paper_evidence_hint:
  - PDF page/section/table/figure
knowledge_base_search:
  - source/topic/concept/query keywords
```

Questions that are answerable from the title alone, duplicate another question,
or lack a paper-evidence hint are rejected. Question regeneration is allowed
once and does not consume an answer round.

## Dual-layer answer contract

Every answer in every round contains both sections.

### Paper-grounded answer

- Answers only from the current paper.
- Cites raw PDF page plus section, table, equation, figure, or appendix.
- Separates `VERIFIED`, `EXTRACTED`, `INFERRED`, and `AMBIGUOUS` content.
- States explicitly when the paper does not answer part of the question.

### Knowledge-base-augmented answer

- Retrieves two to five relevant maintained source, topic, concept, relation, or
  query pages.
- Uses the knowledge base to answer, contextualize, compare, or expose a gap;
  it does not merely list backlinks.
- Marks every cross-source synthesis or extrapolation as `INFERRED` unless a
  maintained source directly states it.
- States applicability conditions, conflicting evidence, and what the current
  knowledge base still cannot answer.

## Three-round protocol

The protocol has three answer-and-score rounds, not three revisions after an
unscored draft.

1. Round 1: Organizer writes the initial complete dual-layer answers; Evaluator
   scores and provides feedback.
2. Round 2: Organizer rewrites the complete answers using round-one feedback;
   Evaluator rescoring uses the same rubric and records remaining defects.
3. Round 3: Organizer rewrites again using round-two feedback; Evaluator returns
   the final per-question scores, critical failures, and verdict.

No fourth automatic round is allowed. Full answer text and full evaluator
feedback are retained for all rounds.

## Scoring rubric

Evaluator scores every question independently.

| Dimension | Points |
|---|---:|
| Original-paper evidence accuracy | 25 |
| Answer completeness | 15 |
| Limitations and evidence boundaries | 15 |
| Reasoning and expression clarity | 10 |
| Citation reproducibility | 15 |
| Knowledge-base-augmented answer quality | 20 |
| Total | 100 |

Final per-question gate:

```text
total >= 80/100
original-paper evidence accuracy >= 20/25
limitations and evidence boundaries >= 11/15
knowledge-base-augmented answer quality >= 14/20
no critical failure
```

The paper-level final score is the arithmetic mean of all round-three question
scores. Every question must satisfy the per-question gate; a passing average
cannot hide one failed question. Any critical failure keeps the complete Agent
Queries artifact in `review_pending` regardless of the mean.

When documented retrieval finds no relevant maintained evidence, a precise
`not enough maintained evidence` answer can earn the knowledge-base dimension
for search quality, negative-boundary accuracy, and identification of the gap.
It must not be penalized merely for refusing to fabricate an augmentation.

Critical failures are:

- fabricated or incorrect page numbers, metrics, datasets, or relations;
- presenting knowledge-base inference as a conclusion of the current paper;
- answering the wrong research object;
- using irrelevant maintained pages to inflate the answer;
- omitting a limitation that materially changes the answer.

## Evaluator feedback contract

For each question and dimension, Evaluator records:

```yaml
score: 0
max_score: 0
finding: precise defect or strength
evidence: PDF or maintained-page pointer
required_change: actionable revision instruction
critical_failure: false
```

Feedback must identify the problematic sentence or missing element and the
evidence needed to correct it. Generic comments such as “be more detailed” do
not qualify.

## Storage

The durable Markdown page is:

```text
wiki/queries/<paper-title>-agent-queries.md
```

It contains:

- all three to five questions and their rationales;
- complete round-one answers and feedback;
- complete round-two answers and feedback;
- complete round-three answers and final feedback;
- per-dimension and total scores for every question and round;
- paper-level final score, critical failures, and final lifecycle;
- all paper and knowledge-base references used.

Its frontmatter includes:

```yaml
type: query
title: Agent queries for <paper title>
sources: []
query_origin: AGENT-GENERATED
question_count: 3 # actual count; allowed range is 3-5
review_rounds: 3
final_score: 0
answer_status: reviewed | review_pending | pipeline_blocked
last_updated: YYYY-MM-DD
confidence: 0.0
lifecycle: draft | reviewed
```

For a reviewed page, `confidence` is the paper-level final score divided by
100. A pending or blocked page retains a conservative confidence chosen by the
Main Agent and records the reason.

Machine-readable run records are stored outside the maintained wiki:

```text
.wiki/output/agent-query-runs/<paper-sha256>/<run-date>/
├── evidence-pack.json
├── questions.json
├── round-1.json
├── round-2.json
├── round-3.json
└── final-verdict.json
```

The source page stores only a backlink, final score, lifecycle, and unresolved
question list. It does not duplicate round history.

## Failure handling

- Invalid question count or coverage: regenerate once before round one.
- Subagent execution failure: retry the same role once; on another failure set
  `pipeline_blocked` and continue normal source ingest.
- Low final score: stop after round three and set `review_pending`.
- Fabricated evidence: record a critical failure; the next round must remove and
  replace the unsupported claim.
- Missing maintained evidence: write `not enough maintained evidence`; do not
  fill the knowledge-base answer with generic model knowledge.
- Main Agent detects an evaluator miss: Main Agent may lower lifecycle or score,
  but may not increase evaluator scores.

Agent Queries failure never blocks creation of an evidence-bounded source page.

## Write isolation

Organizer, Questioner, and Evaluator are read-only. They return structured
artifacts to the Main Agent. Only the Main Agent updates source, query, topic,
relation, method-registry, index, and append-only log pages.

Agent-generated questions are not `USER-STATED`, do not update a user's interest
profile, and do not create a user topic. A later human question may reference or
promote an Agent Query through the existing human-focus workflow.

## Testing and acceptance

The skill change is accepted only after RED-GREEN-REFACTOR scenarios verify:

- exactly three to five diverse questions are generated;
- all answers preserve both evidence lanes;
- evaluator rejects fabricated pages and unsupported knowledge-base inference;
- exactly three answer-and-score rounds run without early promotion;
- scores below the gate produce `review_pending`;
- failed subagents produce `pipeline_blocked` without blocking source ingest;
- subagents do not write shared files;
- Main Agent writes full round history and only final maintained artifacts;
- the canonical data-flow block is present in README.

## Implementation surface

Implementation should remain documentation-driven and runtime-agnostic:

- add a concise Agent Queries entry point to `SKILL.md`;
- add a detailed `references/agent-queries-pipeline.md` protocol;
- add a reusable query-page template under `templates/`;
- update README with the canonical data-flow block and feature description;
- add skill behavior tests using isolated subagent pressure scenarios;
- keep the open Windows/Poppler bugfix PR separate from this feature.
