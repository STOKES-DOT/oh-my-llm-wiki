# Agent Queries Obsidian Links Design

Date: 2026-08-26
Status: approved

## Goal

Make the paper-level Agent Queries page participate in the Obsidian graph with
a minimal, evidence-bounded set of wikilinks and reciprocal backlinks.

## Minimal behavior

Every durable Agent Queries page contains `## Knowledge graph links` with:

- its source page;
- relevant existing concepts;
- relevant existing shared topics;
- compared or closely related papers;
- existing related query pages.

The Main Agent adds an `## Agent Queries backlinks` entry to each linked
maintained page and records supported cross-paper or cross-method edges in
`relations.md`. Links use ordinary Obsidian `[[wikilinks]]`.

## Boundaries

- Link only existing pages or pages independently justified by normal paper
  ingest; do not create a page merely to make the graph denser.
- Do not create one page per generated question.
- Do not create, activate, or modify personal user topics from Agent Queries.
- A missing or unsupported connection is recorded as `none-found` or an
  unresolved check, not as a dangling wikilink.
- Existing three-round answers, scoring, storage, and lifecycle rules remain
  unchanged.

## Validation

A static contract test must fail before the change and then require the graph
section, five link groups, reciprocal backlinks, `relations.md`, and the
personal-topic prohibition.
