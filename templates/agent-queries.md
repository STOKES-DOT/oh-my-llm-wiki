---
type: query
title: "{{paper_title}} - Agent Queries"
sources:
  - "[[{{source_page}}]]"
last_updated: "{{YYYY-MM-DD}}"
confidence: {{final_confidence}}
lifecycle: "{{final_lifecycle}}"
answer_status: "{{final_answer_status}}"
origin: AGENT-GENERATED
source_path: "{{relative_path_to_original_pdf}}"
source_sha256: "{{paper_sha256}}"
run_path: ".wiki/output/agent-query-runs/{{paper_sha256}}/{{run_id}}/"
---

# {{paper_title}} - Agent Queries

> [!important] Provenance and scope
> These questions are `AGENT-GENERATED`. This maintained page is the lightweight
> final view. Complete round answers and feedback remain in the linked machine
> history. Original PDF: [{{pdf_filename}}]({{relative_path_to_original_pdf}})

## Run metadata

- Source page: [[{{source_page}}]]
- Paper SHA-256: `{{paper_sha256}}`
- PDF pages: {{pdf_page_count}}
- Page coverage: {{reviewed_page_count}}/{{pdf_page_count}}
- Evidence Pack: `{{evidence_pack_id_or_hash}}`
- Evidence Pack validation: {{pass_or_fail}}
- Run date: {{run_date}}
- Unique run ID: {{run_id}}
- Full machine history: `.wiki/output/agent-query-runs/{{paper_sha256}}/{{run_id}}/`
- Question count: {{3_by_default_or_justified_4_to_5}}

Before writing, render frontmatter with a YAML serializer and use this mapping:

- `reviewed` -> `lifecycle: reviewed`; confidence is final average / 100
- `review_pending` -> `lifecycle: draft`; confidence is `0.0`
- `pipeline_blocked` -> `lifecycle: quarantined`; confidence is `0.0`

## Pipeline block record

Remove this section for `reviewed` or `review_pending`. For `pipeline_blocked`:

- Failed stage: {{stage}}
- Failed role: {{role_or_not_applicable}}
- Completed artifacts retained: {{exact_list_or_none}}
- Next check: {{smallest_action_that_can_unblock_the_pipeline}}

## Knowledge graph links

- Source page: [[{{source_page}}]]
- Concepts: {{existing_concept_wikilinks_or_none}}
- Shared topics: {{existing_shared_topic_wikilinks_or_none}}
- Related papers: {{existing_paper_wikilinks_or_none}}
- Related queries: {{existing_query_wikilinks_or_none}}

For every resolved link, update `## Agent Queries backlinks` on the target page.
Record supported cross-paper or cross-method edges in `wiki/relations.md`.

## Frozen questions

### Q1

- Origin: `AGENT-GENERATED`
- Intent: mechanism-and-results
- Prompt: {{question_text}}
- Evidence view: `evidence-pack/views/Q1.json`

### Q2

- Origin: `AGENT-GENERATED`
- Intent: reproducibility-and-limitations
- Prompt: {{question_text}}
- Evidence view: `evidence-pack/views/Q2.json`

### Q3

- Origin: `AGENT-GENERATED`
- Intent: knowledge-base-comparison-and-boundary
- Prompt: {{question_text}}
- Evidence view: `evidence-pack/views/Q3.json`

Add Q4 or Q5 only when a distinct research object or explicit user request is
recorded in the run manifest.

## Final answers

Repeat this complete block for every frozen question.

### Q1

#### Question

{{frozen_question_text}}

#### Paper-grounded answer

{{round_3_complete_paper_grounded_answer}}

Paper citations: {{PDF_pages_sections_tables_figures}}

#### Knowledge-base-augmented answer

{{round_3_complete_knowledge_base_answer_or_explicit_insufficiency}}

Wiki citations: {{maintained_page_links_or_none}}

Unresolved checks: {{none_or_explicit_list}}

## Score trajectory

| Question | Round 1 | Round 2 | Round 3 | Final gate |
|---|---:|---:|---:|---|
| Q1 | {{score}}/100 | {{score}}/100 | {{score}}/100 | {{pass_or_fail}} |
| Q2 | {{score}}/100 | {{score}}/100 | {{score}}/100 | {{pass_or_fail}} |
| Q3 | {{score}}/100 | {{score}}/100 | {{score}}/100 | {{pass_or_fail}} |
| Q4 | {{omit_or_scores}} | {{omit_or_scores}} | {{omit_or_scores}} | {{omit_or_gate}} |
| Q5 | {{omit_or_scores}} | {{omit_or_scores}} | {{omit_or_scores}} | {{omit_or_gate}} |

## Final verdict

- All questions pass: {{true_or_false}}
- Final average: {{round_3_arithmetic_mean}}/100
- Answer status: {{reviewed_or_review_pending_or_pipeline_blocked}}
- Confidence: {{final_average_divided_by_100_only_when_reviewed_else_0.0}}
- Critical failures: {{none_or_question_ids_and_reasons}}

## Full history

Complete standalone answers and complete evaluator feedback are retained at:

- `round-1/answers.md`
- `round-1/evaluator-feedback.md`
- `round-2/answers.md`
- `round-2/evaluator-feedback.md`
- `round-3/answers.md`
- `round-3/evaluator-feedback.md`

Base directory:
`.wiki/output/agent-query-runs/{{paper_sha256}}/{{run_id}}/`

Load these files only for audit, recheck, or an explicit request to inspect
round history.

Retrieval contract: `retrieval_mode: ordinary | audit | recheck | round-history`.
Ordinary mode returns the paths above without opening them. Any non-ordinary
load records its mode, exact files, and reason in the operation log.

## Links and unresolved checks

- Source page: [[{{source_page}}]]
- Related concepts/topics: {{maintained_links_supported_by_evidence}}
- Related papers/methods: {{maintained_links_supported_by_evidence}}
- Unresolved evidence checks: {{none_or_explicit_list}}
- Verification boundary: {{what_was_and_was_not_checked}}
