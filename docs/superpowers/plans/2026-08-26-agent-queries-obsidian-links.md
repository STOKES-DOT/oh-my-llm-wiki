# Agent Queries Obsidian Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect each paper-level Agent Queries page to the existing Obsidian wiki graph with minimal wikilinks and reciprocal backlinks.

**Architecture:** Keep one Agent Queries page per paper. Add one graph-links section, update linked maintained pages with backlinks, and mirror supported cross-paper/method edges in `relations.md`; do not add new node types or scoring behavior.

**Tech Stack:** Markdown, Obsidian wikilinks, Python `unittest` static contracts.

---

### Task 1: RED contract

**Files:**
- Modify: `tests/test_agent_queries_contract.py`

- [ ] Add `test_agent_queries_define_minimal_obsidian_network` that requires:

```python
for fragment in (
    "## Knowledge graph links",
    "Source page",
    "Concepts",
    "Shared topics",
    "Related papers",
    "Related queries",
    "## Agent Queries backlinks",
    "relations.md",
    "must not create or activate a personal topic",
):
    self.assertIn(fragment, combined_skill_reference_template)
```

- [ ] Run `python3 tests/test_agent_queries_contract.py`.

Expected: FAIL because `## Knowledge graph links` is absent.

### Task 2: Minimal GREEN implementation

**Files:**
- Modify: `SKILL.md`
- Modify: `references/agent-queries-pipeline.md`
- Modify: `templates/agent-queries.md`
- Modify: `README.md`
- Test: `tests/test_agent_queries_contract.py`

- [ ] Add a concise graph-links rule to `SKILL.md`: use evidence-backed
  `[[wikilinks]]`, update reciprocal `## Agent Queries backlinks`, update
  `relations.md`, and never create/activate a personal topic.
- [ ] Add `## Knowledge graph links` to the protocol with the same ownership and
  missing-target boundaries.
- [ ] Add this template block:

```markdown
## Knowledge graph links

- Source page: [[{{source_page}}]]
- Concepts: {{existing_concept_wikilinks_or_none}}
- Shared topics: {{existing_shared_topic_wikilinks_or_none}}
- Related papers: {{existing_paper_wikilinks_or_none}}
- Related queries: {{existing_query_wikilinks_or_none}}
```

- [ ] Add one README sentence describing the Obsidian network.
- [ ] Run `python3 -m unittest discover -s tests -p 'test_*.py'`.

Expected: all tests pass.

### Task 3: Sync and deliver

**Files:**
- Update personal copies of `SKILL.md`, `references/agent-queries-pipeline.md`,
  and `templates/agent-queries.md` without replacing Poppler doctor files.

- [ ] Confirm personal copies contain Agent Queries graph links and the Poppler
  doctor entry.
- [ ] Run all tests and `git diff --check origin/main...HEAD`.
- [ ] Commit with `feat: connect Agent Queries to Obsidian graph`.
- [ ] Push `codex/agent-queries-pipeline` so PR #3 updates.
