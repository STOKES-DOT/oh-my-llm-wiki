# Agent Queries Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a runtime-agnostic, three-subagent Agent Queries quality loop to every new-paper ingest, preserving three full answer/feedback rounds and knowledge-base-augmented scoring.

**Architecture:** `SKILL.md` exposes a short mandatory entry point, while `references/agent-queries-pipeline.md` owns role prompts, schemas, scoring, and orchestration. `templates/agent-queries.md` defines the durable query page. Static contract tests protect the protocol, and subagent pressure scenarios verify actual behavior. Only the Main Agent writes wiki files.

**Tech Stack:** Markdown skill instructions, Python `unittest` contract checks, existing multi-agent runtime, existing `.wiki/` Markdown schema.

---

## File map

- Create `references/agent-queries-pipeline.md`: complete role, round, scoring,
  storage, and failure protocol.
- Create `templates/agent-queries.md`: durable three-round query-page template.
- Create `tests/test_agent_queries_contract.py`: executable structural contract
  tests for skill, reference, template, and README.
- Create `tests/agent_queries_scenarios.md`: RED/GREEN behavior scenarios and
  acceptance criteria for subagent testing.
- Modify `SKILL.md`: concise trigger, routing, hard gates, and references.
- Modify `README.md`: feature summary, canonical data flow, output paths, and
  quality gate.
- Modify personal installation files under
  `/Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/` using targeted patches;
  never overwrite the personal `SKILL.md` wholesale because it already contains
  the pending Poppler-fix changes from PR #2.

## Task 1: Record RED behavior before adding the protocol

**Files:**
- Create later: `tests/agent_queries_scenarios.md`
- Read: `SKILL.md`
- Read: `docs/superpowers/specs/2026-08-26-agent-queries-pipeline-design.md`

- [ ] **Step 1: Run the baseline ingest scenario without Agent Queries instructions**

Dispatch an isolated read-only subagent with this exact scenario:

```text
You are importing a newly provided six-page method paper into an LLM wiki.
Use the current skill, but no Agent Queries protocol exists. Complete the ingest
under time pressure. State which subagents you launch, how many questions you
generate, how many answer/evaluation rounds you run, and which files you write.
Do not edit the real workspace.
```

- [ ] **Step 2: Verify RED behavior**

Expected RED evidence: the response does not independently instantiate all
three roles, does not preserve exactly three answer-score rounds, or does not
apply the approved 100-point gate. Record the exact missing behavior in the
turn notes; do not edit the skill yet.

- [ ] **Step 3: Run the baseline hallucination scenario**

```text
Question Q1 has a draft answer citing PDF p. 19, but the evidence pack reports
that the paper has only six pages. Score the answer and decide whether the query
page can be reviewed. No Agent Queries evaluator rubric is available.
```

Expected RED evidence: scoring is ad hoc or lacks an explicit critical-failure
gate.

## Task 2: Add failing structural contract tests

**Files:**
- Create: `tests/test_agent_queries_contract.py`
- Test: `tests/test_agent_queries_contract.py`

- [ ] **Step 1: Write the failing contract test**

Create the following test:

```python
#!/usr/bin/env python3
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentQueriesContractTest(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text()

    def test_reference_defines_roles_rounds_and_failure_states(self) -> None:
        text = self.read("references/agent-queries-pipeline.md")
        for role in ("Main Agent", "Organizer", "Questioner", "Evaluator"):
            self.assertIn(f"## {role}", text)
        for round_number in (1, 2, 3):
            self.assertIn(f"Round {round_number}", text)
        self.assertNotIn("Round 4", text)
        for state in ("reviewed", "review_pending", "pipeline_blocked"):
            self.assertIn(state, text)

    def test_scoring_weights_sum_to_100_and_gates_are_present(self) -> None:
        text = self.read("references/agent-queries-pipeline.md")
        weights = [int(value) for value in re.findall(r"data-score-weight=\"(\d+)\"", text)]
        self.assertEqual(sum(weights), 100)
        self.assertIn("total >= 80/100", text)
        self.assertIn("evidence_accuracy >= 20/25", text)
        self.assertIn("boundary_quality >= 11/15", text)
        self.assertIn("knowledge_base_answer >= 14/20", text)
        self.assertIn("critical_failure", text)

    def test_template_preserves_complete_three_round_history(self) -> None:
        text = self.read("templates/agent-queries.md")
        for round_number in (1, 2, 3):
            self.assertIn(f"## Round {round_number}", text)
            self.assertIn(f"### Round {round_number} answer", text)
            self.assertIn(f"### Round {round_number} evaluator feedback", text)
        self.assertIn("Paper-grounded answer", text)
        self.assertIn("Knowledge-base-augmented answer", text)

    def test_skill_and_readme_expose_the_pipeline(self) -> None:
        skill = self.read("SKILL.md")
        readme = self.read("README.md")
        self.assertIn("## Agent Queries module", skill)
        self.assertIn("references/agent-queries-pipeline.md", skill)
        self.assertIn("PDF reader + existing wiki", readme)
        self.assertIn("Round 3: Organizer revises", readme)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 tests/test_agent_queries_contract.py
```

Expected: errors for missing `references/agent-queries-pipeline.md` and
`templates/agent-queries.md`, plus missing skill/README entry points.

## Task 3: Implement the detailed protocol reference and query template

**Files:**
- Create: `references/agent-queries-pipeline.md`
- Create: `templates/agent-queries.md`
- Test: `tests/test_agent_queries_contract.py`

- [ ] **Step 1: Create the reference with exact role contracts**

`references/agent-queries-pipeline.md` must contain these top-level headings:

```markdown
# Agent Queries Pipeline
## Trigger and prerequisites
## Main Agent
## Organizer
## Questioner
## Evaluator
## Evidence pack
## Question schema
## Answer schema
## Round 1
## Round 2
## Round 3
## Scoring and verdict
## Storage and write isolation
## Failure handling
```

Under the role headings, include these executable prompt contracts:

```text
Organizer: Read the complete evidence pack. Answer every accepted question in
two sections named exactly "Paper-grounded answer" and
"Knowledge-base-augmented answer". Cite raw PDF pages in the first section and
maintained wiki pages in the second. Rewrite the complete answer in each round;
do not patch only the criticized sentence.

Questioner: Independently read the paper evidence and wiki index. Return three
to five non-duplicate questions. Each question must include question_id,
focus_type, why_this_matters, paper_evidence_hint, and knowledge_base_search.
Do not infer human interest or create topics.

Evaluator: Independently verify each citation and knowledge-base use. Score all
six dimensions, return actionable feedback, and set critical_failure=true for
fabricated pages/numbers, wrong research objects, irrelevant retrieval, or
paper/knowledge-base provenance conflation. Never write wiki files.
```

Encode the scoring weights in the reference using machine-checkable comments:

```html
<!-- data-score-weight="25" evidence_accuracy -->
<!-- data-score-weight="15" completeness -->
<!-- data-score-weight="15" boundary_quality -->
<!-- data-score-weight="10" clarity -->
<!-- data-score-weight="15" citation_reproducibility -->
<!-- data-score-weight="20" knowledge_base_answer -->
```

Include the exact gates:

```text
total >= 80/100
evidence_accuracy >= 20/25
boundary_quality >= 11/15
knowledge_base_answer >= 14/20
critical_failure == false
```

Specify that all questions must pass; a passing mean cannot hide a failed
question. Accurate `not enough maintained evidence` is a valid knowledge-base
answer when retrieval is documented.

Also specify the durable and derived storage split exactly:

```text
wiki/queries/<paper-title>-agent-queries.md
.wiki/output/agent-query-runs/<paper-sha256>/<run-date>/
```

The reference must state that a reviewed query page sets `confidence` to the
paper-level final score divided by 100, while pending/blocked pages retain a
conservative Main-Agent-assigned confidence with a reason.

- [ ] **Step 2: Create the full-history query template**

Create `templates/agent-queries.md` with this frontmatter contract:

```yaml
---
type: query
title: Agent queries for <paper title>
sources: []
query_origin: AGENT-GENERATED
question_count: 3
review_rounds: 3
final_score: 0
answer_status: review_pending
last_updated: YYYY-MM-DD
confidence: 0.0
lifecycle: draft
---
```

The body must include pipeline metadata, accepted questions, and these sections
for every generated question:

```markdown
# Agent queries for <paper title>

## Pipeline metadata
## Accepted questions

# Q1: <question>

## Round 1
### Round 1 answer
#### Paper-grounded answer
#### Knowledge-base-augmented answer
### Round 1 evaluator feedback
### Round 1 score

## Round 2
### Round 2 answer
#### Paper-grounded answer
#### Knowledge-base-augmented answer
### Round 2 evaluator feedback
### Round 2 score

## Round 3
### Round 3 answer
#### Paper-grounded answer
#### Knowledge-base-augmented answer
### Round 3 evaluator feedback
### Round 3 score

## Final verdict
```

Add an instruction comment that the Q1 block is repeated for Q2-Q5 as needed;
the generated page must contain full text rather than links to missing round
answers.

- [ ] **Step 3: Run the structural test**

Run:

```bash
python3 tests/test_agent_queries_contract.py
```

Expected at this stage: role, round, rubric, and template tests pass; skill and
README entry-point assertions still fail.

- [ ] **Step 4: Commit the protocol and template**

```bash
git add references/agent-queries-pipeline.md templates/agent-queries.md tests/test_agent_queries_contract.py
git commit -m "feat: add agent queries protocol and template"
```

## Task 4: Add the concise skill entry point

**Files:**
- Modify: `SKILL.md` after `## Human-focus capture subfunction`
- Test: `tests/test_agent_queries_contract.py`

- [ ] **Step 1: Add the routing row**

Add to the discussion routing table:

```markdown
| Agent-generated paper questions and three-round answers | `wiki/queries/<paper-title>-agent-queries.md` |
```

- [ ] **Step 2: Add the skill entry point**

Insert this concise section after Human Focus and before user-topic lifecycle:

```markdown
## Agent Queries module

For every newly ingested paper that passes identity and full-text prerequisites,
run the three-subagent Agent Queries pipeline. **REQUIRED REFERENCE:** Follow
`references/agent-queries-pipeline.md`; use
`templates/agent-queries.md` for the durable page.

- Organizer and Questioner start from the raw-PDF evidence pack; Questioner
  generates exactly 3-5 questions independently.
- Main Agent freezes 2-5 maintained wiki retrievals per question before round 1.
- Run exactly three answer-and-score rounds with the same Organizer and an
  independent Evaluator.
- Preserve complete answers, per-dimension scores, and evaluator feedback for
  every round.
- Only the Main Agent writes wiki files. Agent Queries failure never blocks an
  evidence-bounded source page.
- Promote the query page only when every question passes the 100-point gate and
  no critical failure exists; otherwise use `review_pending` or
  `pipeline_blocked`.

Agent-generated questions are `AGENT-GENERATED`, not `USER-STATED`, and never
create or activate a user topic.
```

- [ ] **Step 3: Run the contract test**

```bash
python3 tests/test_agent_queries_contract.py
```

Expected: only the README data-flow assertion remains failing.

- [ ] **Step 4: Commit the skill entry point**

```bash
git add SKILL.md tests/test_agent_queries_contract.py
git commit -m "feat: require agent queries on paper ingest"
```

## Task 5: Add README data flow and public documentation

**Files:**
- Modify: `README.md` after `## What it maintains`
- Modify: `README.md` repository layout
- Test: `tests/test_agent_queries_contract.py`

- [ ] **Step 1: Add a short feature description**

State that every new paper can run an independent Questioner/Organizer/Evaluator
quality loop, preserving all three rounds, and that Agent Queries do not imply
human interest.

- [ ] **Step 2: Add the canonical block verbatim**

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

- [ ] **Step 3: Update repository layout**

Add:

```text
references/agent-queries-pipeline.md
templates/agent-queries.md
tests/test_agent_queries_contract.py
tests/agent_queries_scenarios.md
```

- [ ] **Step 4: Run all local tests**

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Expected: all existing PDF tests and Agent Queries contract tests pass.

- [ ] **Step 5: Commit README documentation**

```bash
git add README.md
git commit -m "docs: document agent queries pipeline"
```

## Task 6: Add behavior scenarios and verify GREEN

**Files:**
- Create: `tests/agent_queries_scenarios.md`
- Modify only if a loophole is found: `SKILL.md`
- Modify only if a schema gap is found: `references/agent-queries-pipeline.md`

- [ ] **Step 1: Create the behavior scenario file**

Include these three scenarios and expected decisions:

```markdown
# Agent Queries behavior scenarios

## Scenario 1: Time pressure
New six-page paper, user asks for immediate ingest.
Expected: source ingest continues; exactly three roles and three answer-score
rounds are planned; all subagents remain read-only.

## Scenario 2: Fabricated page
Draft cites PDF p. 19 for a six-page paper.
Expected: Evaluator sets critical_failure=true, evidence score below gate, and
query cannot be reviewed.

## Scenario 3: Weak knowledge-base answer
Answer lists three backlinks without using them to answer the question.
Expected: knowledge-base score below 14/20, actionable synthesis feedback, and
review_pending if still unresolved after round 3.
```

- [ ] **Step 2: Run GREEN subagent scenario 1**

Dispatch Questioner, Organizer, and Evaluator as read-only agents with a small
fixture evidence pack. Verify three to five questions, dual answer lanes, and
three retained rounds.

- [ ] **Step 3: Run GREEN subagent scenarios 2 and 3**

Verify critical failure and low knowledge-base score are applied exactly as the
reference specifies. Capture outputs in the turn record; do not write fixture
answers into the real wiki.

- [ ] **Step 4: Refactor any loophole and re-run**

If an agent creates a fourth round, writes the wiki, treats AGENT-GENERATED as
USER-STATED, or passes a failed question through an average score, add an
explicit counter to the reference/SKILL and repeat the scenario.

- [ ] **Step 5: Commit behavior scenarios**

```bash
git add tests/agent_queries_scenarios.md SKILL.md references/agent-queries-pipeline.md
git commit -m "test: add agent queries behavior scenarios"
```

## Task 7: Sync the personal skill without overwriting the Poppler fix

**Files:**
- Modify with targeted patch: `/Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/SKILL.md`
- Create: `/Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/references/agent-queries-pipeline.md`
- Create: `/Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/templates/agent-queries.md`
- Create: `/Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/tests/agent_queries_scenarios.md`

- [ ] **Step 1: Apply only the routing row and Agent Queries section to the personal SKILL**

Do not copy repository `SKILL.md` over the personal file. Use an exact patch so
the personal Poppler doctor instructions remain intact.

- [ ] **Step 2: Copy new isolated files**

```bash
mkdir -p /Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/references
mkdir -p /Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/templates
cp references/agent-queries-pipeline.md /Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/references/
cp templates/agent-queries.md /Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/templates/
cp tests/agent_queries_scenarios.md /Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/tests/
```

- [ ] **Step 3: Verify the personal installation contains both features**

```bash
rg -n "Agent Queries module|check_dependencies.py" /Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/SKILL.md
rg -n "Round 1|Round 2|Round 3|total >= 80/100" /Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/references/agent-queries-pipeline.md
rg -n "Paper-grounded answer|Knowledge-base-augmented answer" /Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/templates/agent-queries.md
python3 /Users/jiaoyuan/.agents/skills/llm-wiki-maintainer/scripts/check_dependencies.py
```

Expected: Agent Queries and Poppler doctor references both exist; all three
rounds and both answer lanes are present; doctor reports the actual machine
state. The repository contract test remains repository-only because it also
validates `README.md`.

## Task 8: Final verification and feature PR

**Files:**
- Verify all files listed above.
- Do not stage unrelated workspace files.

- [ ] **Step 1: Run fresh full verification**

```bash
python3 -m unittest discover -s tests -p "test_*.py"
git diff --check origin/main...HEAD
git status --short
```

Expected: all tests pass; no diff-check errors; only known unrelated untracked
files remain outside the commit set.

- [ ] **Step 2: Review commit scope**

```bash
git diff --name-status origin/main...HEAD
```

Expected feature scope:

```text
README.md
SKILL.md
docs/superpowers/specs/2026-08-26-agent-queries-pipeline-design.md
docs/superpowers/plans/2026-08-26-agent-queries-pipeline.md
references/agent-queries-pipeline.md
templates/agent-queries.md
tests/agent_queries_scenarios.md
tests/test_agent_queries_contract.py
```

- [ ] **Step 3: Check Poppler-fix PR status before opening the feature PR**

If PR #2 has merged, rebase this branch onto updated `origin/main` and rerun all
tests. If PR #2 remains open, keep this PR independent and resolve only genuine
line conflicts; do not copy issue #1 files into the feature branch.

- [ ] **Step 4: Push and open the feature PR**

```bash
git push -u origin codex/agent-queries-pipeline-design
gh pr create \
  --repo STOKES-DOT/oh-my-llm-wiki \
  --base main \
  --head codex/agent-queries-pipeline-design \
  --title "feat: add three-round Agent Queries pipeline" \
  --body-file /private/tmp/agent-queries-pr-body.md
```

The PR body must summarize roles, full-history storage, the 100-point gate,
knowledge-base-augmented answers, RED/GREEN behavior testing, and relationship
to PR #2.

- [ ] **Step 5: Wait for CI and report exact status**

```bash
gh pr checks --watch --interval 10
```

Do not report completion until all configured checks pass. Do not merge without
explicit user authorization.
