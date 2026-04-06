---
name: ingest
description: >
  Process an external source into the knowledge base. Downloads the source,
  saves it as an artifact, creates a bib entry and wiki pages, updates
  navigation. Use this skill when the user says "/ingest" or asks to
  process, summarize, or add an article, paper, book, video, or any
  external source to the system.
---

# Ingest: process an external source

Version: **0.1.0**

## Trigger

`/ingest <url>` or `/ingest <path to local file>`

## Flow

```
1. Download/read the source
2. Generate UUID v7
3. Save to artifacts/{uuid}/
   ├── index.md       ← content (or manifest for multi-file)
   └── original.*     ← original file if applicable
4. Read the original, extract key ideas
5. Present takeaways to user, propose:
   - bib/{uuid}.md
   - wiki page(s)
   - MOC updates
6. User approves / adjusts
7. Create files, update index/MOCs
8. Commit: "ingest: {source title}"
```

## Rules

- Always read the ORIGINAL artifact, not just metadata. Extract knowledge from the full source.
- Create a bib entry only for citable sources. Voice memos, screenshots, raw dumps — artifacts without bib records.
- Never create xettel cards during ingest. Those are the user's thoughts, not the agent's.
- Check existing wiki pages for contradictions and connections with the new source. Note them.
- If the source contradicts an existing xettel card, the wiki page must note the disagreement with links to both.

## Bib entry format

```yaml
---
bib_id: "{uuid}"
bib_type: repo | article | book | paper | podcast | video | voice
bib_title: "Source Title"
bib_author: "Author Name"
bib_url: https://example.com/source
bib_added: {ISO timestamp}
software_version: "0.1.0"
---

LLM-generated summary of the source. Key takeaways, what's new,
what connects to existing knowledge.
```

## Wiki pages created during ingest

Typically a **source summary** page (wiki_type: source). May also create or update:
- Entity pages for people/tools/projects mentioned
- Concept pages if the source introduces new ideas
- MOCs if the topic area needs one

All wiki pages follow the format in `skills/wiki/SKILL.md`.

## Artifacts

- Single-file artifact: `index.md` IS the content
- Multi-file artifact: `index.md` is a manifest listing files
- Never published — originals may be copyrighted
- Only LLM-generated summaries (in bib/) are public
