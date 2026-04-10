---
name: wiki
description: >
  Create and maintain wiki pages — structured knowledge pages owned by the LLM.
  Wiki pages synthesize knowledge from artifacts, bib entries, cards,
  and other wiki pages. Use this skill when creating concept pages, entity pages,
  source summaries, comparisons, syntheses, or maps of content (MOCs).
---

# Wiki: structured knowledge pages

Version: **0.1.0**

## Page types

| Type | Purpose | Example |
|---|---|---|
| `source` | Key takeaways from an ingested source | `gitops-fleet-management.md` |
| `entity` | A person, project, tool, company | `nassim-taleb.md` |
| `concept` | An idea, principle, pattern | `continuous-assembly.md` |
| `comparison` | Structured comparison | `kanban-vs-scrum.md` |
| `synthesis` | Cross-cutting analysis | `ca-and-gitops-synthesis.md` |
| `moc` | Map of Content — thematic navigation | `moc-ai-agents.md` |

## Format

```yaml
---
title: "Page Title"
wiki_type: entity | concept | source | comparison | synthesis | moc
wiki_created: 2026-04-05
wiki_updated: 2026-04-05
wiki_sources:
  - bib: "069cf951-a5fa-7141-8000-494f71cd145d"
  - card: "4e74e25e-03e8-7ed3-a252-6023e2d6b6c5"
tags: [tag1, tag2]
software_version: "0.1.0"
---

Markdown body with [relative links](path.md).
```

## File naming

Slug-based: `content/wiki/{slug}.md`

- Concepts: `continuous-assembly.md`
- Entities: `nassim-taleb.md`
- Source summaries: `gitops-fleet-management.md`
- MOCs: `moc-{topic}.md`

## Writing style

- Clear, precise, factual. No hedging, no filler.
- **All internal links use relative markdown links with `.md` extensions.** No wikilinks. See `thinkbox/CLAUDE.md` for the linking rule and format table.
- Synthesize, don't copy. Link to cards — don't reproduce their text.
- Every claim should be traceable to a source.
- **Search:** use the search skill (`thinkbox/skills/search/SKILL.md`). It runs in a sub-agent combining semantic, full-text, and MOC search. When running inside a sub-agent (e.g. the ingestor), use `thinkbox/scripts/search.sh` directly instead.
- **Concept pages derive authority from bib entries (original sources), not cards.** Cards are the user's thoughts — cite them as "see also" or note agreement/disagreement, but the wiki's claims must stand on published sources. This ensures wiki can surface contradictions when the user's thinking diverges from the literature.

## wiki_sources

The `wiki_sources` array tracks where the page's knowledge comes from:

```yaml
wiki_sources:
  - bib: "069cf951-..."       # bib entry (and its underlying artifact)
  - card: "4e74e25e-..."      # card
  - wiki: "other-page"        # another wiki page (for syntheses)
```

This is metadata for provenance tracking, separate from wikilinks in the body.

## MOC conventions

- Filename: `moc-{topic}.md`, wiki_type: `moc`
- Links to wiki pages, card threads, blog posts, bib entries related to the topic
- Organized by subtopic with brief annotations
- Split when exceeding ~30 links
- `content/index.md` links to top-level MOCs

## Stability rule

A wiki page linked from published cards or external discussion is **stable.** Content can be enriched (new sources, additional detail), but must not be rewritten to contradict its original position. If new information contradicts a published page, create a new page with the new position and note the contradiction on both.

## Relationship to other content

- Wiki reads artifacts (via bib) — the primary knowledge source
- Wiki references cards — treats user's thoughts as first-class sources
- Wiki does NOT copy card text — it links and synthesizes
- Contradiction: wiki notes when sources disagree
- Convergence: wiki notes when user independently arrived at a literature conclusion
- Development: wiki connects when external source extends a user's idea
