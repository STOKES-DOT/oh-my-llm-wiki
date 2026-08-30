#!/usr/bin/env python3
import re
import unicodedata
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE = REPO_ROOT / "references" / "agent-queries-pipeline.md"
TEMPLATE = REPO_ROOT / "templates" / "agent-queries.md"
RUN_TEMPLATE = REPO_ROOT / "templates" / "agent-query-round.md"
SKILL = REPO_ROOT / "SKILL.md"
README = REPO_ROOT / "README.md"


class AgentQueriesContractTest(unittest.TestCase):
    def test_pipeline_reference_defines_roles_rounds_states_and_weights(self) -> None:
        text = REFERENCE.read_text(encoding="utf-8")

        for heading in ("Main Agent", "Organizer", "Questioner", "Evaluator"):
            self.assertRegex(text, rf"(?m)^#+\s+{re.escape(heading)}\s*$")
        for heading in ("Round 1", "Round 2", "Round 3"):
            self.assertRegex(text, rf"(?m)^#+\s+{re.escape(heading)}\s*$")
        self.assertNotRegex(text, r"(?m)^#+\s+Round 4\s*$")
        self.assertRegex(
            text,
            r"(?m)^answer_status: reviewed \| review_pending \| pipeline_blocked$",
        )

        pairs = re.findall(
            r'<!--\s*data-score-weight="(\d+)"\s+([A-Za-z][A-Za-z0-9_]*)\s*-->',
            text,
        )
        self.assertTrue(pairs, "no data-score-weight comments found")
        keys = [key for _, key in pairs]
        self.assertEqual(len(keys), len(set(keys)), "duplicate score-weight keys")
        weights = {key: int(value) for value, key in pairs}
        self.assertEqual(
            weights,
            {
                "evidence_accuracy": 25,
                "completeness": 15,
                "boundary_quality": 15,
                "clarity": 10,
                "citation_reproducibility": 15,
                "knowledge_base_answer": 20,
            },
        )
        self.assertEqual(sum(weights.values()), 100)

        normalized = unicodedata.normalize("NFKC", text)
        normalized = normalized.replace("≥", ">=")
        normalized = normalized.replace("`", "")
        normalized = re.sub(r"\s+", " ", normalized)
        for metric, minimum, maximum in (
            ("total", 80, 100),
            ("evidence_accuracy", 20, 25),
            ("boundary_quality", 11, 15),
            ("knowledge_base_answer", 14, 20),
        ):
            self.assertRegex(
                normalized,
                rf"(?<![A-Za-z0-9_]){metric}(?![A-Za-z0-9_])\s*>=\s*{minimum}\s*/\s*{maximum}",
            )
        self.assertRegex(
            normalized,
            r"(?<![A-Za-z0-9_])critical_failure(?![A-Za-z0-9_])\s*==\s*false",
        )
        for fragment in (
            "MUST equal the exact sum of the six subscores",
            "inclusive range from zero to its declared weight",
            "missing citation for a claim that requires one",
            "Reconcile the final answers and evaluator corrections",
            "unique run identifier",
            "<run-date> maps exactly to the template field run_id",
            "complete-input hash",
            "Render frontmatter through a YAML serializer",
            "For a blocked run",
            "Main Agent's full-paper reading notes",
            "terminal_reason: input_changed",
            "superseded_by: <new-run-id>",
            "No Agent Queries question, answer, score, feedback, or inferred relation",
            "relative to the host workspace root",
            "create no role attempt records",
            "is a content critical failure, not an invocation failure",
            "must not trigger an invocation retry",
        ):
            self.assertIn(fragment, normalized)

    def test_machine_run_template_contains_three_round_answer_feedback_contract(self) -> None:
        self.assertTrue(RUN_TEMPLATE.exists(), "missing complete machine-run template")
        text = RUN_TEMPLATE.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"(?m)^## Round 4$")

        frontmatter = text.split("---", 2)[1]
        self.assertRegex(frontmatter, r"(?m)^confidence: \{\{final_confidence\}\}$")
        self.assertRegex(
            frontmatter,
            r'(?m)^answer_status: "\{\{final_answer_status\}\}"$',
        )
        self.assertRegex(
            frontmatter,
            r'(?m)^lifecycle: "\{\{final_lifecycle\}\}"$',
        )
        self.assertIn(
            'run_path: ".wiki/output/agent-query-runs/{{paper_sha256}}/{{run_id}}/"',
            frontmatter,
        )
        self.assertNotRegex(frontmatter, r"(?m)^run_path: .*\{\{run_date\}\}")
        normalized_template = re.sub(r"\s+", " ", text)
        self.assertIn(
            "frontmatter with the Final verdict values",
            normalized_template,
        )
        for mapping in (
            "`reviewed` -> `lifecycle: reviewed`",
            "`review_pending` -> `lifecycle: draft`",
            "`pipeline_blocked` -> `lifecycle: quarantined`",
            "remove this entire",
            "`## Pipeline block record` section",
        ):
            self.assertIn(mapping, text)

        for round_name in ("Round 1", "Round 2", "Round 3"):
            round_number = round_name[-1]
            start = re.search(rf"(?m)^## {round_name}$", text)
            self.assertIsNotNone(start, f"missing exact {round_name} heading")
            next_boundary = re.search(
                rf"(?m)^## (?:Round {int(round_number) + 1}|Final verdict)$",
                text[start.end() :],
            )
            end = start.end() + next_boundary.start() if next_boundary else len(text)
            section_text = text[start.start() : end]
            self.assertRegex(
                section_text,
                rf"(?m)^### {re.escape(round_name)} answer$",
            )
            self.assertRegex(section_text, rf"(?m)^### {round_name} evaluator feedback$")
            self.assertRegex(section_text, r"(?m)^### Paper-grounded answer$")
            self.assertRegex(section_text, r"(?m)^### Knowledge-base-augmented answer$")
            for required_field in (
                "Uncertainties",
                "Evidence accuracy",
                "Completeness",
                "Boundary quality",
                "Clarity",
                "Citation reproducibility",
                "Knowledge-base answer",
                "Total",
                "Critical failure",
                "Gate verdict",
                "Full feedback",
            ):
                self.assertRegex(
                    section_text,
                    rf"(?m)^- {re.escape(required_field)}:",
                    f"{round_name} missing {required_field}",
                )
            for score_label, maximum in (
                ("Evidence accuracy", 25),
                ("Completeness", 15),
                ("Boundary quality", 15),
                ("Clarity", 10),
                ("Citation reproducibility", 15),
                ("Knowledge-base answer", 20),
            ):
                self.assertRegex(
                    section_text,
                    rf"(?m)^- {re.escape(score_label)}: \{{\{{score\}}\}}/{maximum}$",
                    f"{round_name} has wrong denominator for {score_label}",
                )

        for required_fragment in (
            "Repeat the complete Q1 question block for Q2 and Q3, and optionally Q4 and Q5.",
            "Original PDF:",
            "Paper SHA-256:",
            "## Pipeline block record",
            "Unstarted artifacts omitted:",
            "Final average: `not_applicable`",
            ".wiki/output/agent-query-runs/{{paper_sha256}}/{{run_id}}/",
            "Render YAML with a serializer",
            "Total must equal the",
            "## Final verdict",
            "## Links and unresolved checks",
        ):
            self.assertIn(required_fragment, text)

    def test_durable_query_template_is_lightweight(self) -> None:
        text = TEMPLATE.read_text(encoding="utf-8")
        for heading in (
            "## Frozen questions",
            "## Final answers",
            "## Score trajectory",
            "## Full history",
            "## Knowledge graph links",
            "## Final verdict",
        ):
            self.assertIn(heading, text)
        self.assertNotRegex(text, r"(?m)^## Round [123]$")
        for fragment in (
            "round-1/answers.md",
            "round-1/evaluator-feedback.md",
            "round-2/answers.md",
            "round-2/evaluator-feedback.md",
            "round-3/answers.md",
            "round-3/evaluator-feedback.md",
        ):
            self.assertIn(fragment, text)

    def test_token_efficient_full_paper_contract(self) -> None:
        combined = "\n".join(
            (
                SKILL.read_text(encoding="utf-8"),
                REFERENCE.read_text(encoding="utf-8"),
                README.read_text(encoding="utf-8"),
            )
        )
        normalized = re.sub(r"\s+", " ", combined)
        for fragment in (
            "page-ledger.jsonl",
            "evidence-cards.jsonl",
            "coverage.json",
            "4-8 PDF pages",
            "exactly three questions by default",
            "must not inherit the whole conversation",
            "cited Evidence Cards and disputed Evidence Cards",
            "600-1000 Chinese characters",
            "Ordinary Wiki retrieval must not load `.wiki/output`",
            "scripts/validate_evidence_pack.py",
            "retrieval_mode: ordinary | audit | recheck | round-history",
            "must exclude `.wiki/wiki/topics/users/**`",
            "rendered_path",
        ):
            self.assertIn(fragment, normalized)

    def test_skill_exposes_agent_queries_module_and_reference(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("## Agent Queries module", text)
        self.assertIn("references/agent-queries-pipeline.md", text)
        normalized = re.sub(r"\s+", " ", text)
        for fragment in (
            "every new-paper ingest",
            "sole orchestrator and sole wiki writer",
            "three read-only roles",
            "Questioner** creates exactly three questions by default",
            "exactly three answer-score rounds",
            "Paper-grounded answer",
            "Knowledge-base-augmented answer",
            "Use `reviewed` only when every question passes every Round 3 gate",
            "Use `review_pending` only after all three rounds complete",
            "including a scoreable critical citation failure",
            "Use `pipeline_blocked` when prerequisites are unmet",
            ".wiki/wiki/queries/<paper-title>-agent-queries.md",
            "No generated question, answer, score, feedback, or",
        ):
            self.assertIn(fragment, normalized)

    def test_agent_queries_define_minimal_obsidian_network(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")
        template = TEMPLATE.read_text(encoding="utf-8")

        for fragment in (
            "## Knowledge graph links",
            "Source page",
            "Concepts",
            "Shared topics",
            "Related papers",
            "Related queries",
        ):
            self.assertIn(fragment, template)

        for text in (skill, reference):
            normalized = re.sub(r"\s+", " ", text)
            for fragment in (
                "## Agent Queries backlinks",
                "relations.md",
                "must not create or activate a personal topic",
            ):
                self.assertIn(fragment, normalized)

    def test_readme_documents_agent_queries_entry_points(self) -> None:
        text = README.read_text(encoding="utf-8")
        expected_flow = """PDF reader + existing wiki
        |
        v
Evidence Pack
        |
        +--> Organizer: source draft
        |
        +--> Questioner: 3 questions by default
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
source page + agent-queries page + relations/topic/index/log"""
        self.assertIn(expected_flow, text)
        normalized = re.sub(r"\s+", " ", text)
        for entry_point in (
            "references/agent-queries-pipeline.md",
            "templates/agent-queries.md",
            ".wiki/wiki/queries/<paper-title>-agent-queries.md",
            ".wiki/output/agent-query-runs/<paper-sha256>/<run-date>/",
            "Here `<run-date>` is the unique run identifier",
        ):
            self.assertIn(entry_point, normalized)


if __name__ == "__main__":
    unittest.main()
