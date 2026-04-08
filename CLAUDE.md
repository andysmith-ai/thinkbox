# Thinkbox — platform conventions

Version: **0.1.0**

See `ARCHITECTURE.md` for the full system design. This file covers conventions the LLM must follow when creating and editing content.

## Formatting rules by content type

### Wiki (`content/wiki/`)
- Frontmatter: `title`, `wiki_type`, `wiki_created`, `wiki_updated`, `wiki_sources`, `tags`, `software_version`
- `wiki_type`: entity | concept | source | comparison | synthesis | moc
- Body: markdown with relative `.md` links
- File naming: `slug.md` (e.g. `continuous-assembly.md`, `moc-ai-agents.md`)

### Xettel (`content/x/`)
- Frontmatter: `xettel_id`, `xettel_type`, `xettel_published_date`, `xettel_reply_to`, `xettel_ref`, `xettel_bib`, `xettel_context`, `software_version`
- Body: plain text, no markdown, no wikilinks, English only
- Character limits: 280 (body only), 257 (with ref or source URL), 234 (ref + source URL)
- File naming: `{twitter_status_id}.md`

### Blog (`content/blog/`)
- Frontmatter: `title`, `description`, `date`, `featured_image`, `twitter_id`, `software_version`
- Body: markdown with relative `.md` links
- File naming: `YYYY/MM/slug/index.md`

### Bib (`content/bib/`)
- Frontmatter: `bib_id`, `bib_type`, `bib_title`, `bib_author`, `bib_url`, `bib_added`, `twitter_id`, `software_version`
- Body: LLM-generated summary
- File naming: `{uuid7}.md`

## Wiki writing style

- Clear, precise, factual. No hedging, no filler.
- Cite sources with relative markdown links (see linking rule below).
- Wiki pages synthesize — they don't copy. Link to xettel cards, don't reproduce their text.
- Every claim should be traceable to a source (bib entry or xettel card).

## MOC conventions

- Filename: `moc-{topic}.md`, wiki_type: `moc`
- Links to wiki pages, xettel threads, blog posts, bib entries related to the topic
- Split large MOCs when they exceed ~30 links
- `content/index.md` links to top-level MOCs

## Stability rule

A page with a `twitter_id` is **published and stable**. It can be enriched but must not be rewritten to contradict its original position. If new information contradicts a published page, create a new page and note the contradiction on both.

## Linking rule

**All internal links use relative markdown links with `.md` extensions.** No wikilinks, no absolute URLs. This ensures links work on GitHub, in Obsidian, and on the site (the renderer strips `.md` at build time).

Paths are relative to the source file's location within `content/`.

| From | To | Link |
|---|---|---|
| index.md | wiki page | `[Title](wiki/slug.md)` |
| wiki | wiki | `[Title](other-page.md)` |
| wiki | xettel | `[snippet](../x/2039600765296386127.md)` |
| wiki | blog | `[Title](../blog/2026/01/slug/index.md)` |
| wiki | bib | `[Title](../bib/069cf951-....md)` |
| blog | wiki | `[Title](../../wiki/slug.md)` |

Xettel card bodies never contain links — all linking is via frontmatter fields (`xettel_reply_to`, `xettel_ref`, `xettel_bib`).

## Semantic search

All content is indexed in Qdrant (collection: `content`, 4096-dim Qwen3-Embedding-8B vectors). Each point carries payload: `path`, `type` (wiki/x/bib/blog), `content_hash`, plus all frontmatter fields.

**Search command:** `thinkbox/scripts/search.sh '<query>' [-n limit] [-t wiki|x|bib|blog]`

Use semantic search to:
- Find related content when creating/updating wiki pages
- Discover connections during `/ingest` (existing pages that relate to new source)
- Answer `/query` questions alongside structured MOC navigation
- Detect near-duplicates and contradictions during `/lint`

## Character counting for xettel

1. Count all visible characters in the body
2. Each URL appended to the tweet consumes 23 characters (t.co shortening) + 1 space separator
3. Limits:
   - Body only: **280** chars
   - Body + 1 URL (ref or source): **257** chars (280 - 23)
   - Body + 2 URLs (ref + source): **234** chars (280 - 23 - 23)
