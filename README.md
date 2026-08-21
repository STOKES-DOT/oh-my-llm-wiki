# oh-my-llm-wiki

A local-first agent skill for turning paper reading and research conversations
into an evidence-bounded Markdown wiki.

The repository contains the reusable skill only. It does not publish the local
wiki corpus or original papers.

![Obsidian knowledge graph showing a selected method topic and its connected literature](examples/knowledge-graph.png)

## What it maintains

- Immutable local source provenance with SHA-256 and direct PDF links.
- One source page per paper, named by the paper title.
- Full-paper Methods/Results/Limitations review before promotion to `reviewed`.
- General method-family topics, method-improvement tables, and cross-paper
  relations.
- Human-focus queries that preserve what the user actually asked.
- User-aware topic lifecycles without mixing one person's interests into
  another person's topic graph.
- Explicit `VERIFIED`, `EXTRACTED`, `INFERRED`, `AMBIGUOUS`, and `STALE`
  evidence boundaries.

## Install

```bash
git clone https://github.com/STOKES-DOT/oh-my-llm-wiki.git
mkdir -p ~/.agents/skills
ln -s "$PWD/oh-my-llm-wiki" ~/.agents/skills/llm-wiki-maintainer
```

The repository root is the skill directory and contains `SKILL.md`.

### One-paste agent install

Paste one prompt into your agent.

**Codex**

```text
Install or update https://github.com/STOKES-DOT/oh-my-llm-wiki as my personal Codex skill at ~/.agents/skills/llm-wiki-maintainer. Clone it if missing; if it is already the same Git repo, use git pull --ff-only. If the target has local changes or unrelated files, stop and ask me. Run python3 tests/test_read_pdf.py and report the install path and test result.
```

**Claude Code**

```text
Install or update https://github.com/STOKES-DOT/oh-my-llm-wiki as my personal Claude Code skill at ~/.claude/skills/llm-wiki-maintainer. Clone it if missing; if it is already the same Git repo, use git pull --ff-only. If the target has local changes or unrelated files, stop and ask me. Run python3 tests/test_read_pdf.py and report the install path and test result.
```

## Use

Invoke the skill explicitly or discuss a paper in a workspace that uses a
`.wiki/` knowledge base:

```text
$llm-wiki-maintainer

Here is a paper. What does "real space" mean, and how does it differ from
Hamiltonian learning? Update the wiki with the answer.
```

The skill routes durable knowledge into:

```text
.wiki/
├── raw/       immutable local sources; never published by this repository
├── wiki/
│   ├── sources/
│   ├── concepts/
│   ├── topics/
│   ├── queries/
│   ├── relations.md
│   └── method-improvements.md
└── output/    derived local artifacts
```

## Generic PDF reader

The bundled reader uses Poppler to produce deterministic evidence artifacts:

```bash
python3 scripts/read_pdf.py paper.pdf \
  --output-dir /private/tmp/paper-read \
  --render 1,4-5
```

Outputs:

- `metadata.json` with SHA-256, page count, PDF metadata, and selected pages.
- `layout_text_page_marked.txt` with explicit PDF page boundaries.
- `section_index.json` and `section_index.md` for conservative navigation.
- Optional rendered PNG pages for figures, tables, equations, and multi-column
  layout checks.

The section index is a navigation hint, not scientific evidence. A paper is
only promoted after the relevant source sections and visual pages are reviewed.

## Shared evidence, personalized attention

Shared topics describe source-supported method families. User-specific topics
live under a separate namespace and require confirmation, recurrent interest,
or explicit delegation. A single paper question becomes a human-focus record or
query, not an automatic topic subscription.

```text
wiki/topics/<slug>.md                    shared method topic
wiki/topics/users/<user-key>/index.md   one user's topic index
wiki/topics/users/<user-key>/<slug>.md  one user's interest topic
```

## Repository layout

```text
SKILL.md
scripts/read_pdf.py
tests/test_read_pdf.py
examples/knowledge-graph.png
```

Run the PDF reader tests with:

```bash
python3 tests/test_read_pdf.py
```

## Privacy and copyright boundary

The skill is designed for local research libraries. Original PDFs, personal
queries, project instructions, and local Obsidian workspace state stay outside
this repository. Publish only material you have the right to share.
