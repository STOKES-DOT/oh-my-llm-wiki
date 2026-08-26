# Agent Queries Knowledge-Graph Integration Design

Date: 2026-08-26
Status: proposed
Scope: `llm-wiki-maintainer` Agent Queries graph integration

## Goal

Make every Agent Queries artifact a useful participant in the Obsidian
knowledge graph and in later wiki retrieval. Agent Queries must connect paper
evidence, method families, concepts, shared topics, related papers, and prior
queries without creating a noisy standalone page for every generated question.

## Chosen architecture

Use a hybrid graph:

1. Every ingested paper retains exactly one durable paper-level Agent Queries
   page at `.wiki/wiki/queries/<paper-title>-agent-queries.md`.
2. The page stores Q1-Q3 and optional Q4-Q5 as anchored sections and links
   every question to evidence-backed wiki nodes.
3. A question becomes a standalone query page only when it has demonstrated
   cross-paper or reusable value.
4. Every accepted edge is represented by an Obsidian wikilink and by an
   evidence-bounded relation record.
5. Linked pages receive explicit reciprocal Agent Queries backlinks.

This produces visible graph connectivity without multiplying every routine
evaluation question into a separate note.

## Node model

### Required paper-level node

The paper-level Agent Queries page is always created, including
`review_pending` and `pipeline_blocked` runs. It links to:

- the maintained source page and immutable original PDF;
- relevant method-family topics;
- concepts directly used by a question or answer;
- shared topics supported by the paper or maintained wiki;
- papers used for comparisons;
- existing queries that address the same distinction;
- promoted reusable questions originating from the page.

### Optional promoted-question node

A generated question is promoted to `.wiki/wiki/queries/<question-slug>.md`
only when at least one condition holds:

- it applies to two or more papers;
- it captures a reusable method or concept distinction;
- a later paper or human question links back to it;
- the user explicitly asks to preserve it as a standalone research question.

The promoted page records `origin: AGENT-GENERATED`, its parent Agent Queries
page, contributing source papers, linked concepts/topics, evidence boundary,
and related queries. Promotion does not convert it into `USER-STATED` content.

## Edge model

Use these typed relations:

| Relation | Meaning | Typical target |
|---|---|---|
| `queries` | This Agent Queries page evaluates a paper | source page |
| `asks-about` | A question directly concerns a maintained node | concept, method, shared topic |
| `supported-by` | An answer depends on a maintained evidence node | source, concept, topic, relation |
| `compares-with` | A question or answer compares research objects | paper, method, query |
| `exposes-limitation` | The evaluation identifies a supported boundary | source, method, concept |
| `related-query` | Durable questions investigate a common distinction | query page |

Each edge record contains:

```yaml
from: "[[origin-page]]"
question_id: Q1
relation: asks-about
to: "[[target-page]]"
target_state: resolved | pending-target
evidence: "PDF p. X or maintained page/section"
status: VERIFIED | EXTRACTED | INFERRED | AMBIGUOUS
scope: paper | cross-paper | shared-topic
```

The tuple `(from, question_id, relation, to, scope)` is the de-duplication
identity. A changed evidence boundary creates a dated revision rather than a
silent overwrite.

## Page representation

The Agent Queries template gains a `## Knowledge graph neighborhood` section
with one row per accepted or pending edge:

```markdown
| Question | Relation | Target | Evidence | Status |
|---|---|---|---|---|
| Q1 | asks-about | [[concept-page]] | PDF p. 4 | VERIFIED |
```

Each question also contains a compact `Linked nodes` field so the connection
is visible beside the answer. Frontmatter stores unique resolved linked page
names in `graph_links: []` as a retrieval cache; the edge table and
`relations.md` remain the semantic record.

The durable graph neighborhood contains final Round 3 validated edges. Earlier
round links and rejected candidates remain in immutable round/machine history
but do not create reciprocal backlinks or canonical relation rows.

Every linked source, concept, topic, paper-query, or promoted-query page gains
or updates:

```markdown
## Agent Queries backlinks

- [[paper-title-agent-queries#Q1]] - asks-about; evidence: PDF p. 4
```

Obsidian renders the wikilinks as graph edges. Explicit backlinks make the
relation navigable outside Graph View and usable by agents that read Markdown
rather than Obsidian's backlink index.

## Canonical relation ownership

- `.wiki/wiki/relations.md` remains the canonical cross-page relation registry.
- The Agent Queries page is the complete per-run audit record.
- Target-page backlink sections are navigation indexes, not independent
  evidence authorities.
- Duplicate representations share the same relation type, target, evidence
  status, and source boundary.

## Pipeline data flow

1. The Main Agent extends the frozen Evidence Pack with the relevant existing
   graph neighborhood from `index.md`, `relations.md`, source pages, shared
   topics, concepts, and prior queries.
2. The Questioner proposes 3-5 questions and candidate links to existing nodes.
   Candidate links are not accepted facts.
3. The Organizer answers in the two existing lanes and cites the maintained
   nodes actually used for the knowledge-base-augmented answer.
4. The Evaluator checks target existence, lifecycle, semantic relevance,
   evidence support, and whether linked nodes genuinely contribute.
5. Link retrieval and synthesis quality contribute to `knowledge_base_answer`;
   broken or irreproducible links also reduce `citation_reproducibility` and may
   become critical when a material claim depends on them.
6. The Main Agent validates and de-duplicates edges, then writes the Agent
   Queries page, reciprocal backlinks, `relations.md`, `index.md`, and `log.md`
   as one publication set covered by the final manifest.

## Creation and missing-target rules

Agent Queries may discover that a useful concept or shared topic page is
missing, but it does not create a page merely to satisfy a candidate link.

- Create a shared concept/topic page only when ordinary full-paper ingest rules
  independently support it.
- If the target should exist but evidence or identity is unresolved, set
  `target_state: pending-target`, store a plain `target_label`, set `to: null`,
  and record the smallest next check. Do not emit a wikilink or reciprocal
  backlink until the target resolves.
- Never create dangling wikilinks, guessed paper identities, or placeholder
  personal topics.
- Preserve contradictory edges as separate `AMBIGUOUS` records until the
  source boundary is resolved.

## User-topic isolation

Agent Queries questions, answers, scores, feedback, candidate links, and
promoted queries are not user-interest evidence.

- Shared topics may receive evidence-backed edges.
- A confirmed personal topic may be referenced only when ordinary
  source-grounded ingest rules justify the update.
- Agent Queries cannot create, activate, rename, merge, or change the lifecycle
  of `.wiki/wiki/topics/users/**`.
- Human-focus content remains `USER-STATED` and must not be conflated with an
  `AGENT-GENERATED` question.

## Retrieval behavior

When answering from the wiki, an agent can start at any paper, concept, topic,
or query and traverse:

1. explicit Agent Queries backlinks;
2. typed edges in `relations.md`;
3. the paper-level Knowledge graph neighborhood;
4. promoted reusable queries for cross-paper synthesis.

Default retrieval is one hop, expanding to two hops only when the first hop
identifies a relevant method, concept, comparison paper, or related query.
Lifecycle and evidence status travel with every edge; graph proximity alone
does not establish evidence.

## Failure and consistency handling

- A nonexistent linked target or unresolved placeholder blocks publication of
  that edge, not source ingest. Other independently validated final edges may
  still publish with their own evidence status.
- A malformed edge table, inconsistent reciprocal backlink, or relation tuple
  mismatch is a structurally unscoreable validation failure under the existing
  one-retry rule.
- A weak but structurally valid graph connection is evaluator feedback and a
  score issue; it does not consume the execution/schema retry.
- The final manifest includes hashes of every Agent Queries page, promoted
  query, reciprocal backlink target, relation registry, index, and log update.

## Validation design

Implementation follows RED-GREEN-REFACTOR:

1. RED static contract: current template/skill lack the graph-neighborhood
   section, edge vocabulary, reciprocal backlinks, and promotion rules.
2. GREEN structural tests require the edge types, page section, target-page
   backlink contract, canonical registry, and user-topic prohibition.
3. GREEN behavior scenarios:
   - an existing concept and comparison paper produce validated reciprocal
     graph links;
   - an unsupported relation remains `pending-target` and creates no dangling
     page;
   - a cross-paper reusable question is promoted and linked to both parents;
   - an Agent Queries artifact cannot create or activate a personal topic.
4. REFACTOR review checks de-duplication, lifecycle/status propagation, and
   template/README/protocol consistency.

## Non-goals

- No standalone page for every generated question.
- No replacement of `relations.md` with an external graph database.
- No interpretation of Obsidian visual proximity as evidence.
- No change to three-round scoring weights or pass thresholds.
- No publication of the user's local wiki or original PDFs.
