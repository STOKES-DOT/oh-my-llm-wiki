# Agent Queries Token-Efficiency and Completeness Design

Date: 2026-08-30
Status: approved

## Goal

Reduce repeated LLM input while preserving full-paper coverage, page-level
provenance, three complete review rounds, and final scientific quality.

## Core separation

Full-paper organization and Agent Queries are independent gates:

1. Main Agent reads every PDF page once in bounded page batches and persists an
   Evidence Pack.
2. Source Page is compiled from that pack and passes a deterministic coverage
   gate.
3. Agent Queries receives question-scoped views of the pack rather than the raw
   full PDF.
4. The Wiki query page stores final answers and score trajectory; complete round
   answers and feedback remain under `.wiki/output/agent-query-runs/`.

A failed Agent Queries run never erases or downgrades a complete Evidence Pack.
A passing Agent Queries run never upgrades an incomplete Source Page.

## Evidence Pack

Each run stores:

```text
evidence-pack/
├── manifest.json
├── page-ledger.jsonl
├── evidence-cards.jsonl
├── coverage.json
└── views/
    └── Q1.json
```

`page-ledger.jsonl` accounts for every page from 1 through the `pdfinfo` page
count. Each record has page type, review status, visual-review status, referenced
card IDs, and an explicit open check when unresolved.

`evidence-cards.jsonl` stores compact page-bounded method, data, result,
limitation, quantitative, relation, and reproducibility evidence. Cards retain
source SHA-256, PDF page, section, content, and uncertainty.

`coverage.json` records `research_question`, `method`, `data`, `results`,
`limitations`, and `relations` as `covered`, `none-found`, or
`not-applicable`. Every `covered` dimension lists one or more existing Evidence
Card IDs. Missing or pending dimensions and unsupported `covered` dimensions
fail the Source Page gate.

## Full reading without repeated raw input

Main Agent processes the page-marked extraction sequentially in batches of 4-8
pages. Completed raw batches are replaced by persistent cards; later batches
receive only paper identity, section ledger, card IDs, and unresolved cross-page
checks. The complete raw PDF and complete page-marked full text are never sent
to Organizer, Questioner, or Evaluator. Evidence expansion may add only newly
selected page-bounded Evidence Cards or rendered artifacts through a re-frozen
scoped view.

Figures, tables, equations, key numerical pages, identity ambiguities, and text
extraction failures are rendered. Their ledger records use the matching visual
page type, `visual_status: reviewed`, and a `rendered_path` that resolves to an
existing artifact inside the Evidence Pack. `not_required` is valid only when
none of those conditions applies. Other pages are read from page-marked text
without image rendering.

## Role-scoped views

Default Questioner output is exactly three questions covering mechanism/results,
reproducibility/limitations, and knowledge-base comparison/boundary. Four or five
questions require an explicit distinct research object or user request.

Each question view contains only relevant Evidence Card IDs, shared source,
concept, topic, relation and query pages, the current answer, and unresolved
feedback. It must exclude `.wiki/wiki/topics/users/**`. Agent Queries artifacts
never create, activate, or modify personal topics; user-stated interests remain
separate Human-focus records.

Organizer, Questioner, and Evaluator never receive the complete raw PDF or the
complete inherited conversation. Evaluator reads cited cards and disputed
cards; missing evidence triggers a Main Agent expansion and re-freeze of the
question-scoped view.

## Three-round preservation

Exactly three rounds remain mandatory. Every round stores complete standalone
answers and complete evaluator feedback under the machine-history directory.
Passing feedback may be concise but must include all scores, citation verdict,
and conclusion. Failure feedback remains detailed and actionable.

Default answer budget is 600-1000 Chinese characters per question, with explicit
exceptions for quantitative tables, multi-method comparisons, evidence
conflicts, or user-requested depth. This is a target, not a truncation rule.

## Lightweight durable query page

The maintained Wiki page stores:

- the frozen questions;
- Round 3 final complete answers;
- per-round score trajectory;
- final verdict and unresolved checks;
- Source/Concept/Topic/Query graph links;
- links to complete round artifacts.

Retrieval uses `retrieval_mode: ordinary | audit | recheck | round-history`.
Ordinary mode is limited to index, source, concept, shared topic, relation, and
the lightweight query page. An output link is returned as a path but is not
expanded. `.wiki/output/**` may be loaded only in the three non-ordinary modes;
those modes record the request type, loaded file list, and reason.

## Deterministic completeness validation

`scripts/validate_evidence_pack.py` validates:

- SHA-256 and positive PDF page count;
- exact, unique page coverage from 1 through N;
- no pending visual checks;
- explicit open checks for unresolved pages;
- unique Evidence Card IDs and in-range pages;
- card SHA agreement and ledger references;
- all six coverage dimensions resolved.

The validator never judges scientific truth; it proves structural coverage and
provenance completeness.

## Non-goals

- No reduction below three review rounds.
- No deletion of complete answers or feedback.
- No claim of exact provider billing or cache savings.
- No use of model memory to replace missing Evidence Cards.
- No Source Page promotion based only on Agent Queries scores.
