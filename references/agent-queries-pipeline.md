# Agent Queries Pipeline

This protocol is mandatory for every new-paper ingest. It tests paper
understanding through paper-specific answers and tests whether the maintained
wiki can support careful extrapolation. Agent-generated questions are an
evaluation artifact, not evidence of the user's research interests.

## Trigger and prerequisites

Run the pipeline after the source PDF has been registered and read in full,
but before the Main Agent promotes the new source page or finishes index and
log updates. Required inputs are the immutable PDF, its SHA-256, the PDF page
count, a section/page index, the Main Agent's full-paper reading notes, and
the current
wiki index. If direct paper reading is incomplete, stop with
`answer_status: pipeline_blocked`; do not substitute an abstract or an
existing summary.

The pipeline has three read-only subagent roles: Organizer, Questioner, and
Evaluator. A role may return text and structured data to the Main Agent but
must not edit `.wiki/`, the source PDF, or another role's artifact.

## Main Agent

The Main Agent is the sole orchestrator and sole wiki writer. It MUST:

1. Build one immutable Evidence Pack and send the same version to all roles.
2. Enforce the role boundaries, 3-5 question count, exactly three rounds, and
   per-question scoring gates.
3. Reject citations outside the Evidence Pack and independently validate page
   numbers, maintained-page links, totals, and verdicts before writing.
4. Preserve every complete answer and every complete evaluator response.
5. Append every invocation input, output, and retry record to the unique
   staging run directory as it occurs. Publish the durable query page and
   accepted final manifest only after validation.
6. Continue the source ingest when the query pipeline is blocked, while
   recording the block in the source page, durable Agent Queries page,
   `.wiki/wiki/index.md`, and `.wiki/wiki/log.md`.
7. Reconcile the final answers and evaluator corrections with the Organizer's
   source-page draft before promotion. If they conflict, retain the supported
   version and keep the affected source claim draft, ambiguous, or pending
   rather than promoting it silently.

A `reviewed` query does not automatically make the source page `reviewed`; the
source page must independently satisfy the mandatory full-paper review gate.

The Main Agent never silently repairs a subagent's answer. A correction must
appear in the next full Organizer rewrite or in the final unresolved checks.

## Organizer

The Organizer receives the Evidence Pack and produces the source-page draft.
For each Questioner prompt it writes a complete answer in both required lanes.
In Rounds 2 and 3 it MUST emit a new complete standalone answer version that
addresses the evaluator feedback and preserve every earlier version unchanged;
a patch, diff, or abbreviated
"unchanged" response is invalid. The Organizer cites exact PDF pages for
paper claims and exact maintained wiki pages for knowledge-base claims. It
must state when either evidence layer is insufficient.

## Questioner

The Questioner reads the Evidence Pack, but not draft answers or evaluator
scores. It generates 3-5 non-duplicative, paper-specific questions spanning
method mechanism, evidence/results, assumptions or limitations, and at least
one useful cross-paper or method comparison when the Evidence Pack permits.
Questions must be answerable or explicitly boundary-testable from the paper
and maintained wiki. They MUST NOT infer a user-interest topic or demand facts
that require unprovided external sources.

## Evaluator

The Evaluator receives the frozen Evidence Pack, all questions, the current
round's complete answers, and prior feedback. It independently checks every
citation and scores every question against the six-dimension rubric. It
returns the complete numerical breakdown, `critical_failure`, pass/fail, and
specific correction instructions. The Evaluator does not rewrite answers and
does not edit wiki files. Round 3 is the final score; it may still return
feedback for unresolved weaknesses, but it cannot request Round 4.

## Evidence pack

The Main Agent freezes an Evidence Pack with:

- paper identity, version, source path, SHA-256, PDF page count, and extraction
  tool/version;
- full-paper section/page map and page-marked text or rendered page references;
- the Main Agent's full-paper reading notes for research question, method,
  data, results, assumptions, limitations, and unresolved transcription checks;
- the wiki index and only the maintained source, concept, topic, relation, and
  prior query pages selected for this run, each with its lifecycle and links;
- the evidence-pack hash or manifest identifier shared by every role.

For each role invocation, hash the complete input: role contract, Evidence
Pack identifier, frozen question set, current full answers, and all applicable
prior feedback. Assign a run-unique attempt ID. A retry must reuse the same
complete input hash. If any input must change, terminate the current run and
start a separately identified run. Finalize the abandoned run with
`answer_status: pipeline_blocked`, `terminal_reason: input_changed`, and
`superseded_by: <new-run-id>` in a non-reviewed terminal manifest. Changing
input never resets or extends the two-attempt limit inside a run.

A role may not browse beyond this pack during scoring. External verification,
if needed, is a separate Main Agent action and creates a new pack/run rather
than mutating evidence in place.

## Question schema

Each question record contains:

```yaml
question_id: Q1
origin: AGENT-GENERATED
prompt: "Paper-specific question"
intent: mechanism | evidence | limitation | comparison | boundary-test
paper_evidence_targets: ["PDF p. X, section/table/figure"]
wiki_evidence_targets: ["[[maintained-page]]"]
```

Use sequential IDs `Q1` through `Q3`, `Q4`, or `Q5`. Questions generated by
this module never create or activate a user-interest topic.

## Answer schema

Every question in every round stores a complete standalone record:

```yaml
question_id: Q1
round: 1
paper_grounded_answer: "Full answer with PDF-page citations"
knowledge_base_augmented_answer: "Full wiki-based answer or explicit insufficiency"
paper_citations: ["source PDF p. X"]
wiki_citations: ["[[maintained-page]]"]
uncertainties: []
```

The rendered answer uses the exact labels `Paper-grounded answer` and
`Knowledge-base-augmented answer`. Knowledge-base extrapolation means
answering the question from the maintained knowledge base, not adding general
model memory. A correct "not enough maintained evidence" response may score
well when it demonstrates sound retrieval and a precise negative evidence
boundary; fabrication must score as a critical failure.

## Round 1

The Organizer writes an initial complete two-lane answer for every frozen
question. The Evaluator returns a complete six-dimension score, evidence
checks, `critical_failure`, verdict, and full feedback for every question.
Both answer and feedback are appended to history unchanged.

## Round 2

The Organizer uses the Round 1 feedback to emit a new complete standalone
answer version
for every question, including answers that already passed. The Evaluator
rescans citations and returns a new complete score and complete feedback. Do
not store only changes from Round 1.

## Round 3

The Organizer uses all prior feedback to emit the final complete standalone
answer version for every question while preserving Rounds 1 and 2 unchanged.
The Evaluator performs the final independent score
and returns complete feedback. The Main Agent records the final verdict after
this evaluation. There is no Round 4 and no hidden repair after scoring.

## Scoring and verdict

Score each question independently on a 100-point scale:

<!-- data-score-weight="25" evidence_accuracy -->
<!-- data-score-weight="15" completeness -->
<!-- data-score-weight="15" boundary_quality -->
<!-- data-score-weight="10" clarity -->
<!-- data-score-weight="15" citation_reproducibility -->
<!-- data-score-weight="20" knowledge_base_answer -->

- `evidence_accuracy` (25): fidelity to the PDF and maintained pages.
- `completeness` (15): coverage of the question and material qualifications.
- `boundary_quality` (15): separation of paper evidence, wiki synthesis,
  inference, absence of evidence, and unresolved conflicts.
- `clarity` (10): direct, internally coherent, and usable explanation.
- `citation_reproducibility` (15): citations resolve to the stated source and
  exact PDF page or maintained page.
- `knowledge_base_answer` (20): relevant retrieval, synthesis, links, and
  epistemic control when answering from the maintained wiki.

Every subscore is a base-10 integer in the inclusive range from zero to its
declared weight. `total` is a base-10 integer and MUST equal the exact sum of
the six subscores. Reject decimals, negative values, out-of-range values, a
missing dimension, or a mismatched total before applying pass gates.

A question passes only when all gates hold simultaneously:

```text
total >= 80/100
evidence_accuracy >= 20/25
boundary_quality >= 11/15
knowledge_base_answer >= 14/20
critical_failure == false
```

Critical failures include a fabricated or nonexistent PDF page/source
citation, contradiction of supplied evidence, a material unsupported claim
presented as verified, deletion/concealment of a known contradiction, a
missing citation for a claim that requires one, or a mandatory citation that
cannot be resolved to supplied evidence. A
high total cannot override a critical failure or any subscore gate. Every
question must pass after Round 3; an average cannot hide a failed question.

The allowed structured state schema is:

answer_status: reviewed | review_pending | pipeline_blocked

Use `reviewed` only when every question passes. Use `review_pending` after
Round 3 when any question fails without a pipeline execution failure. Use
`pipeline_blocked` when prerequisites or a role fail under the retry rule.
For `reviewed`, page confidence is the arithmetic mean of final per-question
totals divided by 100. For both `review_pending` and `pipeline_blocked`, set
frontmatter confidence to numeric `0.0`; keep the actual final average as a
separate diagnostic when Round 3 completed.
Map state to page lifecycle exactly: `reviewed` uses `lifecycle: reviewed`,
`review_pending` uses `lifecycle: draft`, and `pipeline_blocked` uses
`lifecycle: quarantined`.

## Storage and write isolation

The Main Agent writes the durable, human-readable record to:

`wiki/queries/<paper-title>-agent-queries.md`

This path is relative to `.wiki/`, so its host-workspace-relative form is
`.wiki/wiki/queries/<paper-title>-agent-queries.md`. `<paper-title>` is a
path-safe title slug; if two source identities collide, append a short paper
SHA-256 suffix rather than overwriting either page.

The Main Agent writes the complete machine history to:

`.wiki/output/agent-query-runs/<paper-sha256>/<run-date>/`

This path is relative to the host workspace root. The approved directory placeholder
`<run-date>` maps exactly to the template field `run_id`; it is not the
display-only run date. Its value MUST be a unique run identifier of the form
`YYYY-MM-DDTHHMMSSZ-<evidence-pack-hash-prefix>`; a same-second
collision receives an additional monotonic suffix. Never reuse or overwrite a
prior run directory.

The Main Agent appends each attempt to a staging subdirectory before consuming
its result, including the attempt ID and complete-input hash. It then
atomically publishes a final manifest naming accepted attempts; staging
records remain append-only evidence. The machine directory contains the
Evidence Pack manifest, role inputs and outputs, every complete round answer,
every complete evaluator response, scores, retry events, and final verdict.
The durable page links the source
page and original PDF and is marked `AGENT-GENERATED`. Only the Main Agent may
write either layer or update source pages, relations, topics, index, or log.
No Agent Queries question, answer, score, feedback, or inferred relation may
create an interest signal or change any `wiki/topics/users/**` lifecycle.
Existing confirmed user topics may receive only ordinary source-grounded
ingest updates under the user-topic rules.

The final manifest is the commit marker and MUST be published last. It records
the content hash of the durable query page and every reconciled source, topic,
relation, index, and log target written by this run. Before that marker exists
and all hashes match, the run is incomplete staging and cannot be presented as
`reviewed`. On restart, preserve partial files, compare them with staging, and
either finish the same commit without changing inputs or begin a new run; do
not silently adopt or overwrite a partial publication.

Render frontmatter through a YAML serializer, not raw string substitution.
Escape Markdown labels and link destinations when inserting paper titles or
paths. Reject output that does not parse as YAML or whose links do not resolve
to the registered artifacts.
Before every durable write, remove every inapplicable optional section and
reject any unresolved `{{...}}` placeholder. In particular, a `reviewed` or
`review_pending` page MUST omit the entire `## Pipeline block record` section.

## Failure handling

Retry a failed Organizer, Questioner, or Evaluator invocation once with the
same complete invocation input and an explicit failure record. If the second attempt
fails, set `answer_status` to `pipeline_blocked`, preserve both attempts, and
stop query rounds. The Main Agent still completes the source ingest and marks
the query pipeline as blocked; it must not fabricate missing role output.

For a blocked run, instantiate the durable template in blocked mode: retain
metadata, the Pipeline block record, and only questions, answers, feedback,
and scores that actually completed. Omit unstarted question/round sections;
never leave fabricated history or unresolved template placeholders. Record the
failed stage, role, both attempt IDs, errors, and next check. Set frontmatter
`confidence` to numeric `0.0`, use a non-reviewed lifecycle, and record final
average as `not_applicable`.
For a prerequisite failure before any role invocation, record the prerequisite
evidence, create no role attempt records, and render any required attempt
fields as `not_applicable`. Require two attempt records only when a role or
validation invocation was actually retried.

An execution failure or structurally unscoreable output is an invocation
failure. Examples are malformed or missing score fields, fewer than 3 or more
than 5 questions, mutated question text between rounds, missing full
answers/feedback, or a fourth round. Preserve the invalid artifact, apply the
same one-retry rule to the responsible role, and fail closed if it recurs.

A fabricated, nonexistent, out-of-range, missing, or unresolvable citation in
an otherwise scoreable answer is a content critical failure, not an invocation
failure. It MUST receive complete Evaluator scores and feedback and must not
trigger an invocation retry that bypasses the three scheduled rounds. Carry
the feedback into the next scheduled full rewrite. If it remains after Round
3, set `answer_status: review_pending`; do not create Round 4.
