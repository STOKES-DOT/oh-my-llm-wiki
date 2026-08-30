# Agent Queries Token-Efficiency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist complete page-level evidence once, use role-scoped views during three review rounds, and keep normal Wiki retrieval lightweight.

**Architecture:** Main Agent owns full-paper batched reading and a machine-validated Evidence Pack. Subagents consume selected cards; the durable query page keeps only final answers and score trajectory while machine history retains all rounds.

**Tech Stack:** Markdown skill protocol, JSON/JSONL, Python standard library, `unittest`.

---

### Task 1: RED evidence-pack validator tests

**Files:**
- Create: `tests/test_validate_evidence_pack.py`
- Create: `scripts/validate_evidence_pack.py`

- [ ] Write tests for complete pack success, missing page failure, pending visual
  failure, unknown card reference, and unresolved coverage dimension.
- [ ] Run `python3 tests/test_validate_evidence_pack.py` and confirm RED because
  the validator does not exist.
- [ ] Implement the standard-library validator and confirm GREEN.

### Task 2: RED skill contract

**Files:**
- Modify: `tests/test_agent_queries_contract.py`

- [ ] Require `page-ledger.jsonl`, `evidence-cards.jsonl`, `coverage.json`,
  default three questions, clean role contexts, cited-card evaluation, and no
  ordinary retrieval of `.wiki/output`.
- [ ] Require lightweight Wiki sections `Final answers`, `Score trajectory`, and
  `Full history`.
- [ ] Require a separate complete machine-round template.
- [ ] Run the contract test and confirm failure on missing behavior.

### Task 3: GREEN protocol and templates

**Files:**
- Modify: `SKILL.md`
- Modify: `references/agent-queries-pipeline.md`
- Rewrite: `templates/agent-queries.md`
- Create: `templates/agent-query-round.md`
- Modify: `README.md`

- [ ] Define bounded full reading, Evidence Pack schemas, completeness gate,
  role-scoped views, answer budgets, concise passing feedback, and audit-only
  history loading.
- [ ] Keep exact three-round preservation in the machine template.
- [ ] Run all unit and contract tests.

### Task 4: Behavioral regression and personal sync

**Files:**
- Modify: `tests/agent_queries_scenarios.md`
- Update personal skill copies without replacing Poppler doctor resources.

- [ ] Verify a 15-page paper produces page coverage 1-15, a complete Source Page,
  three scoped questions, and no repeated raw PDF input to subagents.
- [ ] Verify an omitted page blocks Source Page promotion even if all query scores
  pass.
- [ ] Verify normal retrieval does not load round history while audit retrieval
  does.
- [ ] Run all tests, sync personal resources, and prepare a clean PR from latest
  `main` without candidate image files.
