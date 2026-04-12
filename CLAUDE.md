# Thinkbox — platform conventions

Version: **0.1.0**

See `ARCHITECTURE.md` for the full system design. This file covers conventions the LLM must follow when creating and editing content.

## Formatting rules by content type

### Wiki (`content/wiki/`)
- Frontmatter: `title`, `wiki_type`, `wiki_created`, `wiki_updated`, `wiki_sources`, `tags`, `software_version`
- `wiki_type`: entity | concept | source | comparison | synthesis | moc
- Body: markdown with relative `.md` links
- File naming: `slug.md` (e.g. `continuous-assembly.md`, `moc-ai-agents.md`)

### Cards (`content/cards/`)
- Frontmatter: `card_type`, `card_created`, `card_reply_to`, `card_ref`, `card_bib`, `card_embed_url`, `card_images`, `card_context`, `card_published`, `software_version`
- `card_type`: `permanent` (user's thoughts) or `literature` (source-derived ideas)
- Filename IS the card ID — no `card_id` field inside the file.
- Body: plain text, no markdown, no wikilinks, no URLs, English only
- Character limit: 300 chars (matches Bluesky). URLs never appear in the body — external refs flow through `card_bib` for provenance. Link previews are controlled by `card_embed_url`.
- File naming: `{uuid7}.md`
- `card_published` is a list of per-platform publication records. Bluesky entries carry `{platform, id, cid, date}`; legacy Twitter entries in the archive carry `{platform, id, date}`. Empty/absent until first publish.

### Blog (`content/blog/`)
- Frontmatter: `title`, `description`, `date`, `featured_image`, `software_version`
- Body: markdown with relative `.md` links
- File naming: `YYYY/MM/slug/index.md`

### Bib (`content/bib/`)
- Frontmatter: `bib_id`, `bib_type`, `bib_title`, `bib_author`, `bib_url`, `bib_added`, `card_id`, `software_version`
- `card_id` optionally points to the local card that discusses this source.
- Body: LLM-generated summary
- File naming: `{uuid7}.md`

## Wiki writing style

- Clear, precise, factual. No hedging, no filler.
- Cite sources with relative markdown links (see linking rule below).
- Wiki pages synthesize — they don't copy. Link to cards, don't reproduce their text.
- Every claim should be traceable to a source (bib entry or card).

## MOC conventions

- Filename: `moc-{topic}.md`, wiki_type: `moc`
- Links to wiki pages, card threads, blog posts, bib entries related to the topic
- Split large MOCs when they exceed ~30 links
- `content/index.md` links to top-level MOCs

## Stability rule

A card with a non-empty `card_published` list is **published and stable**. It can be enriched by linking from other content but its body must not be rewritten to contradict what was published. If new information contradicts a published card, create a new card and note the contradiction on both.

## Linking rule

**All internal links use relative markdown links with `.md` extensions.** No wikilinks, no absolute URLs. This ensures links work on GitHub, in Obsidian, and on the site (the renderer strips `.md` at build time).

Paths are relative to the source file's location within `content/`.

| From | To | Link |
|---|---|---|
| index.md | wiki page | `[Title](wiki/slug.md)` |
| wiki | wiki | `[Title](other-page.md)` |
| wiki | card | `[snippet](../cards/4e74e25e-03e8-7ed3-a252-6023e2d6b6c5.md)` |
| wiki | blog | `[Title](../blog/2026/01/slug/index.md)` |
| wiki | bib | `[Title](../bib/069cf951-....md)` |
| blog | wiki | `[Title](../../wiki/slug.md)` |

Card bodies never contain links — all linking is via frontmatter fields (`card_reply_to`, `card_ref`, `card_bib`).

## Search

All content is indexed in Qdrant (collection: `content`, 4096-dim Qwen3-Embedding-8B vectors). Each point carries payload: `path`, `type` (wiki/cards/bib/blog), `content_hash`, plus all frontmatter fields.

**In the main session:** use the search skill (`thinkbox/skills/search/SKILL.md`). It launches a sub-agent that combines semantic (Qdrant), full-text (grep), and MOC navigation, returning a compact summary. This protects the main session's context window.

**Inside a sub-agent:** use `thinkbox/scripts/search.sh` directly, since you're already in an isolated context.

**Search script:** `thinkbox/scripts/search.sh '<query>' [-n limit] [-t wiki|cards|bib|blog]`

## Sub-agent skills

Some skills run their work in a Task tool sub-agent to protect the main session's context window. Each skill's SKILL.md contains the full sub-agent prompt inlined — no extra file reads needed.

| Skill | Purpose | Model |
|---|---|---|
| `search` | Combined search (semantic + full-text + MOC) — returns compact summary | Sonnet |
| `ingest` | Full ingestion flow (download, artifact, bib, wiki, MOC, commit) | Opus |
| `ingest-repo` | Full repo analysis and ingestion | Opus |

**Key rules:**
- Sub-agents generate their own UUIDs via `thinkbox/scripts/uuid7.sh`
- Sub-agents run search directly via `search.sh` (they have their own context window)
- Sub-agents cannot spawn other sub-agents (no nesting)
- All heavy work stays in the sub-agent's context — only compact summaries return to the main session

## Character counting for cards

`len(body) ≤ 300`. Plain and flat (matches Bluesky's real limit).

Cards never contain URLs. External references live in `card_bib` and become a link-preview embed (Bluesky external card) on publish. This means:

- For cards with `card_embed_url` set, the reader sees the source URL — not as raw text inside the post, but as a link-preview card rendered by the platform from metadata fetched via CardyB. Typically only the root card of a literature thread has this field.
- The card file itself stays portable, searchable, and URL-free.
- The whole 300 chars are available for prose.

`publish.py` enforces the 300-char limit on the card body before any network call and errors out with `error: card over limit (body=X, limit=300)` if you're over.
