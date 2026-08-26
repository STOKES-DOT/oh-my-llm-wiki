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

<!-- Render YAML with a serializer and escape Markdown labels/destinations.
     Do not perform blind placeholder replacement. -->

> [!important] Provenance and scope
> These questions are `AGENT-GENERATED`. They evaluate paper understanding and
> maintained-wiki retrieval; they do not represent a user-interest topic.
> Original PDF: [{{pdf_filename}}]({{relative_path_to_original_pdf}})

## Run metadata

- Source page: [[{{source_page}}]]
- Paper SHA-256: `{{paper_sha256}}`
- PDF pages: {{pdf_page_count}}
- Evidence Pack: `{{evidence_pack_id_or_hash}}`
- Run date: {{run_date}}
- Unique run ID: {{run_id}}
- Full machine history: `.wiki/output/agent-query-runs/{{paper_sha256}}/{{run_id}}/`
- Roles: Main Agent (sole writer), Organizer, Questioner, Evaluator
- Question count: {{3_to_5}}

Allowed state schema:

answer_status: reviewed | review_pending | pipeline_blocked

Before writing the durable page, replace `final_answer_status`,
`final_confidence`, and `final_lifecycle` in frontmatter with the Final verdict
values. Use this exact lifecycle mapping:

- `reviewed` -> `lifecycle: reviewed`
- `review_pending` -> `lifecycle: draft`
- `pipeline_blocked` -> `lifecycle: quarantined`

For
`reviewed`, confidence is the Round 3 per-question average divided by 100; for
`review_pending` or `pipeline_blocked`, use numeric `0.0` and keep any
completed Round 3 average as a separate diagnostic only.

## Pipeline block record

Fill this section only when `answer_status` is `pipeline_blocked`:

- Failed stage: {{prerequisite_or_Organizer_or_Questioner_or_Evaluator_or_validation}}
- Failed role: {{role_or_not_applicable}}
- Prerequisite evidence: {{record_or_not_applicable}}
- Attempt 1 ID/input hash/error: {{complete_record_or_not_applicable_before_invocation}}
- Attempt 2 ID/input hash/error: {{complete_record_or_not_applicable_before_invocation}}
- Completed artifacts retained: {{exact_list_or_none}}
- Unstarted artifacts omitted: {{exact_list}}
- Final average: `not_applicable`
- Confidence: `0.0`
- Next check: {{smallest_action_that_can_unblock_the_pipeline}}

In blocked mode, retain only real completed question/round sections and omit
all unstarted sections below. Never publish placeholder answers or scores.
For `reviewed` or `review_pending`, remove this entire
`## Pipeline block record` section before writing the durable page.

## Frozen questions

### Q1

- Origin: `AGENT-GENERATED`
- Intent: {{mechanism_or_evidence_or_limitation_or_comparison_or_boundary_test}}
- Prompt: {{question_text}}
- Paper evidence targets: {{PDF_pages_sections_tables_figures}}
- Wiki evidence targets: {{maintained_page_links_or_none}}

### Questions Q2-Q5

Repeat the complete Q1 question block for Q2 and Q3, and optionally Q4 and Q5.
Use 3-5 sequential IDs. Freeze every prompt before Round 1; do not rename,
merge, delete, or rewrite questions between rounds.

## Round 1

Repeat the four H3 blocks below as one complete unit for every frozen question
Q1-Q3 and optional Q4-Q5. Never replace a full answer with a diff.

### Round 1 answer

- Question ID: {{Q1}}
- Question: {{frozen_question_text}}

### Paper-grounded answer

{{complete_initial_answer_with_exact_PDF_page_citations}}

Paper citations: {{source_PDF_page_and_section_table_figure}}

- Uncertainties: {{none_or_complete_Round_1_uncertainty_list}}

### Knowledge-base-augmented answer

{{complete_initial_wiki_based_answer_or_not_enough_maintained_evidence}}

Wiki citations: {{maintained_page_links_or_none}}

### Round 1 evaluator feedback

- Question ID: {{Q1}}
- Evidence accuracy: {{score}}/25
- Completeness: {{score}}/15
- Boundary quality: {{score}}/15
- Clarity: {{score}}/10
- Citation reproducibility: {{score}}/15
- Knowledge-base answer: {{score}}/20
- Total: {{score}}/100
- Critical failure: {{false_or_true}}
- Gate verdict: {{pass_or_fail}}
- Citation checks: {{complete_check_results}}
- Full feedback: {{complete_specific_feedback_for_the_next_rewrite}}

## Round 2

Repeat the four H3 blocks below as one complete unit for every frozen question
Q1-Q3 and optional Q4-Q5. Store a standalone rewrite, not only the changes.

### Round 2 answer

- Question ID: {{Q1}}
- Question: {{frozen_question_text}}
- Feedback addressed: {{Round_1_feedback_items}}

### Paper-grounded answer

{{complete_Round_2_rewrite_with_exact_PDF_page_citations}}

Paper citations: {{source_PDF_page_and_section_table_figure}}

- Uncertainties: {{none_or_complete_Round_2_uncertainty_list}}

### Knowledge-base-augmented answer

{{complete_Round_2_wiki_based_rewrite_or_not_enough_maintained_evidence}}

Wiki citations: {{maintained_page_links_or_none}}

### Round 2 evaluator feedback

- Question ID: {{Q1}}
- Evidence accuracy: {{score}}/25
- Completeness: {{score}}/15
- Boundary quality: {{score}}/15
- Clarity: {{score}}/10
- Citation reproducibility: {{score}}/15
- Knowledge-base answer: {{score}}/20
- Total: {{score}}/100
- Critical failure: {{false_or_true}}
- Gate verdict: {{pass_or_fail}}
- Citation checks: {{complete_check_results}}
- Full feedback: {{complete_specific_feedback_for_the_next_rewrite}}

## Round 3

Repeat the four H3 blocks below as one complete unit for every frozen question
Q1-Q3 and optional Q4-Q5. This is the final full rewrite and final score; do
not create Round 4.

### Round 3 answer

- Question ID: {{Q1}}
- Question: {{frozen_question_text}}
- Feedback addressed: {{Round_1_and_Round_2_feedback_items}}

### Paper-grounded answer

{{complete_final_rewrite_with_exact_PDF_page_citations}}

Paper citations: {{source_PDF_page_and_section_table_figure}}

- Uncertainties: {{none_or_complete_Round_3_uncertainty_list}}

### Knowledge-base-augmented answer

{{complete_final_wiki_based_rewrite_or_not_enough_maintained_evidence}}

Wiki citations: {{maintained_page_links_or_none}}

### Round 3 evaluator feedback

- Question ID: {{Q1}}
- Evidence accuracy: {{score}}/25
- Completeness: {{score}}/15
- Boundary quality: {{score}}/15
- Clarity: {{score}}/10
- Citation reproducibility: {{score}}/15
- Knowledge-base answer: {{score}}/20
- Total: {{score}}/100
- Critical failure: {{false_or_true}}
- Gate verdict: {{pass_or_fail}}
- Citation checks: {{complete_check_results}}
- Full feedback: {{complete_final_feedback_and_remaining_weaknesses}}

## Final verdict

- Q1: {{final_total}}/100; {{pass_or_fail}}; critical failure: {{false_or_true}}
- Q2: {{final_total}}/100; {{pass_or_fail}}; critical failure: {{false_or_true}}
- Q3: {{final_total}}/100; {{pass_or_fail}}; critical failure: {{false_or_true}}
- Q4: {{omit_if_not_generated_or_record_final_verdict}}
- Q5: {{omit_if_not_generated_or_record_final_verdict}}
- All questions pass: {{true_or_false}}
- Final average: {{arithmetic_mean_of_Round_3_question_totals}}/100
- Answer status: {{reviewed_or_review_pending_or_pipeline_blocked}}
- Confidence: {{final_average_divided_by_100_only_when_reviewed_else_0.0}}

A question passes only if total >= 80/100, evidence accuracy >= 20/25,
boundary quality >= 11/15, knowledge-base answer >= 14/20, and critical
failure is false. Every question must pass; the final average cannot hide a
failed question. If any question fails after Round 3, use `review_pending`.
If a role fails twice, use `pipeline_blocked` and preserve both attempts in
the machine history while allowing the source ingest to continue.
Each score is an integer within its dimension range, and Total must equal the
sum of all six dimension scores. A missing or unresolvable mandatory citation
is a critical failure.

## Links and unresolved checks

- Source page: [[{{source_page}}]]
- Related concepts/topics: {{maintained_links_supported_by_evidence}}
- Related papers/methods: {{maintained_links_supported_by_evidence}}
- Unresolved evidence checks: {{none_or_explicit_list}}
- Retry/failure records: {{none_or_machine_history_paths}}
- Verification boundary: {{what_was_and_was_not_checked}}
