# Thinkbox Architecture

Version: **0.1.0** — first draft with all decisions locked.

## What is thinkbox

Thinkbox is a platform for running a personal knowledge system with LLM agents. The human curates sources, directs analysis, writes their own thoughts. The LLM does the bookkeeping — summarizing, cross-referencing, filing, maintaining consistency.

Thinkbox is not the content. It is the operating system for the content: skills, schemas, conventions. The content lives in `content/`, the renderer lives in its own repo (e.g. `andysmith.ai/`), and the platform lives in `thinkbox/`. Thinkbox is the part you can share with someone else so they can set up the same system.

### Instances

Each thinkbox instance is a fully independent deployment: its own content, its own wiki, its own index, its own infrastructure. One person may run multiple instances — e.g. a public instance for all topics they discuss openly, and a private instance for topics they're not ready to share. Instances do not share content or state. The platform code is the same; everything else is separate.

## System map

```
project-root/
├── CLAUDE.md                ← root schema: system-wide conventions
├── renderer/                ← site engine (e.g. Astro), public output
│   └── CLAUDE.md            ← build instructions
├── content/                 ← all publishable content (git repo)
│   ├── index.md             ← top-level navigation, links to MOCs
│   ├── wiki/                ← LLM-generated knowledge pages + MOCs
│   ├── cards/               ← user's atomic thoughts (one idea per card)
│   ├── blog/                ← user's long-form articles
│   └── bib/                 ← bibliography / source registry
├── sessions/                ← Socratic dialogue transcripts (private, not in git)
│   └── {uuid7}/index.md
└── thinkbox/                ← platform (shareable)
    ├── CLAUDE.md            ← platform conventions for the LLM
    ├── ARCHITECTURE.md      ← this file
    └── skills/
        ├── search/SKILL.md      ← combined search (runs in sub-agent)
        ├── ingest/SKILL.md      ← article ingestion (runs in sub-agent)
        ├── ingest-repo/SKILL.md ← repo ingestion (runs in sub-agent)
        ├── card/SKILL.md
        ├── lit-thread/SKILL.md  ← literature card thread from bib entry
        ├── wiki/SKILL.md
        ├── publish/SKILL.md
        └── socrates/SKILL.md

Artifacts (will move to S3 later, local for now):
artifacts/{uuid7}/
├── index.md                 ← manifest or content itself
└── original.*               ← source file(s)
```

## Content layers

### 1. Artifacts (private)

Immutable raw materials. Anything the user wants to process: web articles, books, PDFs, voice recordings, podcast transcripts, screenshots, notes. Each artifact is a directory identified by UUID v7.

**Current storage:** local `artifacts/{uuid7}/` directory (not in content/, not published). Will migrate to S3 later.

**Target storage:** `s3://bucket/{uuid7}/` — private, not publicly accessible.

**Structure:**
```
artifacts/{uuid7}/
├── index.md       ← manifest listing files, or the content itself
└── original.*     ← original file(s): .pdf, .md, .mp3, etc.
```

- Single-file artifact: `index.md` IS the content.
- Multi-file artifact: `index.md` is a manifest.
- Never published. Originals are copyrighted material — only LLM-generated summaries (in bib/) are public.

**Not every artifact becomes a bib entry.** Voice memos, screenshots, raw dumps — these are artifacts without bibliography records. Bib entries are created only for citable sources.

### 2. bib/ — bibliography (public)

Source registry. One entry per citable external source. The public face of an artifact.

**bib_id = artifact UUID.** The bib entry contains metadata and an LLM-generated summary. Visitors see the summary. They do NOT get access to the underlying artifact or S3 path.

**Format:**
```yaml
---
bib_id: "069cf951-a5fa-7141-8000-494f71cd145d"
bib_type: repo | article | book | paper | podcast | video | voice
bib_title: "Source Title"
bib_author: "Author Name"
bib_url: https://example.com/source
bib_added: 2026-04-01T10:34:46.851Z
software_version: "0.1.0"
---
```

Body: LLM-generated summary of the source.

### 3. wiki/ — structured knowledge (LLM-generated, public)

The LLM owns this layer entirely. It creates pages, updates them as new sources arrive, maintains cross-references, and keeps everything consistent. The human reads and guides; the LLM writes.

**Sources for wiki pages:** anything in the system.
- Artifacts — the primary input. The LLM reads the ORIGINAL artifact (not the bib summary) during ingest, extracts knowledge, and writes wiki pages that REFERENCE the bib entry.
- Cards — the user's own ideas are first-class sources. Wiki treats them like ideas from any other thinker. Specific mechanisms:
  - **Contradiction:** ingest finds an external source that contradicts a user's card. Wiki page notes the disagreement with links to both.
  - **Development:** external source extends or deepens a user's idea. Wiki page connects them.
  - **Convergence:** user independently arrived at a conclusion also found in literature. Wiki notes this.
  - **Clustering:** lint detects a dense cluster of related cards. LLM proposes a concept page synthesizing them.
- Wiki does NOT copy card text. It links to cards by relative path and writes its own synthesis.

**Page types:**
- **Source summary** — key takeaways from an ingested source, what's new, what contradicts existing knowledge.
- **Entity** — a person, project, tool, company. Aggregates everything known.
- **Concept** — an idea, principle, pattern. Synthesis across sources and cards.
- **Comparison** — structured comparison of entities or concepts.
- **Synthesis** — cross-cutting analysis connecting multiple concepts.
- **MOC (Map of Content)** — thematic navigation page. Links to wiki pages, card threads, blog posts, bib entries related to a topic. Created and maintained by the LLM.

**Format:**
```yaml
---
title: "Page Title"
wiki_type: entity | concept | source | comparison | synthesis | moc
wiki_created: 2026-04-05
wiki_updated: 2026-04-05
wiki_sources:
  - bib: "069cf951-..."
  - card: "4e74e25e-03e8-7ed3-a252-6023e2d6b6c5"
tags: [tag1, tag2]
software_version: "0.1.0"
---
```

Body: markdown with relative `.md` links.

**File naming:** slug-based. `continuous-assembly.md`, `nassim-taleb.md`, `moc-ai-agents.md`.

### 4. cards/ — atomic thoughts (user's voice, public)

The user's own atomic, transferable thoughts. 280 characters. One card = one idea. Cards are published to external platforms (currently Bluesky; historically Twitter) and on the site.

The LLM helps formulate but never writes cards autonomously — every card must pass through the user.

**Two card types:**
- **permanent** — the user's own thoughts. Default type.
- **literature** — atomic ideas extracted from external sources. Each literature card captures one key idea from a book, article, or paper in the user's own reformulation. The source is tracked in `card_bib`. Literature cards are typically created as threads: a root card with a link preview (via `card_embed_url`) followed by one card per atomic idea, each chained via `card_reply_to`.

**Cards do NOT contain links to the site.** Pure text, platform-independent. Wiki, bib, and blog posts may contain site links.

**Identity:** each card is identified by a UUID v7 generated at creation time. The filename IS the identity: there is no `card_id` field inside card files.

**Workflow:** card is drafted → user approves → file is created at `content/cards/{uuid}.md` with empty `card_published[]` → later, the `/publish` skill publishes the card to configured platforms and appends entries to `card_published[]`.

**Format:**
```yaml
---
card_type: permanent                                     # or "literature" for source-derived cards
card_created: 2026-04-02T07:09:41.249Z
card_reply_to: "4e64b031-3940-7583-8cee-4d2caaed9496"  # optional, thread placement (local UUID)
card_ref: "4e740921-63e0-7781-bff2-fb4d9c8a6186"        # optional, bridge card (local UUID)
card_bib: "069cf951-a5fa-7141-8000-..."                 # optional, external source that inspired the card
card_embed_url: "https://example.com/article"           # optional, URL for link-preview embed on publish
card_images:                                             # optional, image URLs to attach on publish
  - "https://cdn.example.com/image.png"
card_context: "chat 2026-04-05, ..."                    # optional, what prompted the card
card_published:                                          # optional, filled in by /publish
  - platform: twitter
    id: "2039600765296386127"
    date: 2026-04-02T07:09:41.249Z
software_version: "0.1.0"
---
```

Body: card text, plain text, no markdown.

**External references — law:** every external reference is a bib entry. `card_ref` is strictly local UUID → local UUID. External sources flow through `card_bib`.

**Link preview embeds:** controlled by `card_embed_url`. When present, the publish script fetches metadata for the URL and attaches a link-preview card. Typically only set on the root card of a literature thread — reply cards in the same thread have `card_bib` for provenance but no embed.

**Image attachments:** controlled by `card_images`. A list of image URLs to download and attach on publish. Up to 4 images per card. Mutually exclusive with `card_embed_url` and `card_ref` (only one embed type per post). The publish script downloads images to a temp directory at publish time — no binary files in the content repo. Typically used on literature thread reply cards to attach diagrams from the source article.

**Character limits:**
- Body only: ≤280 chars
- Body + 1 URL in body: ≤257 chars
- Body + 2 URLs in body: ≤234 chars

280 is a thinking discipline, kept regardless of target platform.

**File naming:** `{uuid7}.md`. The filename is the card ID; reply/ref fields reference other cards by UUID.

**IDs in frontmatter:** plain UUID strings. The renderer resolves links.

### 5. blog/ — user's articles (public)

Long-form articles by the user.

**Format:**
```yaml
---
title: "Article Title"
description: "One-liner"
date: 2026-01-27T10:43:54
featured_image: image.png       # optional
software_version: "0.1.0"
---
```

Body: markdown with relative `.md` links.

**Directory structure:** `blog/YYYY/MM/slug/index.md`

## Navigation

### index.md (top-level)

`content/index.md` — entry point for the entire knowledge base. Not a flat list. Links to MOCs and top-level content.

The LLM reads this first when answering queries or deciding where new content fits.

### MOCs (Maps of Content)

`wiki/moc-{topic}.md` — thematic navigation pages. Each MOC covers a topic area and links to relevant wiki pages, card threads, blog posts, and bib entries.

MOCs are created and maintained by the LLM. As content grows, the LLM splits large MOCs or creates new ones.

Navigation path: `index.md → MOC → content pages`. Can be multiple hops deep.

### No separate log

Git log IS the log. Commit messages follow a convention:

```
ingest: {source title}
wiki: create {page title}
wiki: update {page title}
card: {short description}
blog: {post title}
bib: {source title}
lint: {what was fixed}
publish: {platform} {card_id}
```

No separate `log.md`. The index and MOCs handle navigation; git handles history.

## Default mode

The agent's default behavior is **Q&A against the knowledge base.** Any question the user asks — the agent reads index, navigates MOCs, reads relevant pages, and synthesizes an answer with citations. No special command needed.

During Q&A, a thought may emerge that's worth capturing as a card. The agent can suggest it; the user can ask for it. The flow naturally transitions from Q&A to `/card` without breaking conversation.

## Skills

All operations are invoked as explicit skills. The agent also recognizes natural-language equivalents, but skills are the canonical entry points.

### /ingest — process an external source

**Trigger:** `/ingest <url>` or `/ingest <path to local file>` (articles, papers, web pages)

For GitHub repositories, use `/ingest-repo` instead.

**Flow:**
```
User: /ingest https://fleetdm.com/guides/managing-devices-with-gitops

Agent: downloads article, converts to markdown
Agent: generates UUID v7
Agent: saves to artifacts/{uuid}/index.md (+ original if applicable)
Agent: reads the original, extracts key ideas
Agent:
  "Key takeaways:
   1. GitOps for fleet management solves drift, auditability, rollback
   2. Requires cultural shift to code review
   3. ...

   Will create:
   - bib/{uuid}.md
   - wiki/gitops-fleet-management.md (source summary)
   - Update wiki/moc-devops.md

   Ok?"

User: approves / adjusts

Agent: creates files, updates index/MOCs
Agent: commits — "ingest: Managing Devices with GitOps"
```

**Rules:**
- Always reads the ORIGINAL artifact, not just metadata.
- Creates bib entry only for citable sources.
- Never creates cards — those are the user's thoughts.
- Checks existing wiki pages for contradictions/connections with the new source.

### /ingest-repo — deep analysis of a GitHub repository

**Trigger:** `/ingest-repo <github-url>` — URL matching `https://github.com/{owner}/{repo}`

Clones the repo, navigates code interactively across two axes (technical architecture + business context), creates bib entry and wiki pages. Uses a different acquisition pipeline than `/ingest`: shallow clone, file tree + key source files.

**Analysis axes:**
- **Technical:** architecture, patterns, core algorithms, extensibility
- **Business:** problem, audience, use cases, positioning, maturity

**Exploration funnel:** ORIENT (tree + README) → IDENTIFY (manifests + config) → MAP (entry points + interfaces) → DIVE (10-30 key files)

**Wiki output:** 1 source summary + 1-4 concept pages + 0-1 entity page + MOC updates.

See `skills/ingest-repo/SKILL.md` for full specification.

### /card — create an atomic thought

**Trigger:** `/card [initial thought in any language]`

Can also emerge naturally from Q&A — user says "let's capture this" or agent suggests "this could be a card."

**Flow:**
```
User: /card conflict of interest can't be resolved inside one head

Agent:
  "Variant: «Conflict of interest can't be resolved inside
   one head.» (57 chars)

   Type: permanent
   Placement: root

   Or reply_to 4e610197-... (previous thought)?"

User: "root, good"

Agent: generates UUID v7 for the new card
Agent: creates content/cards/{uuid}.md with empty card_published[]
Agent: commits — "card: conflict of interest"
```

**Rules:**
- Every card passes through the user. Agent proposes, user approves.
- Card text is always in English.
- Body: plain text, no markdown, no links.
- ≤280 chars (≤257 with 1 URL in body, ≤234 with 2).
- File is created immediately with empty `card_published[]` — no wait-for-platform-ID.
- Agent may suggest bridge cards connecting to existing cards / wiki.
- Publishing is a separate concern — use `/publish` when ready.

### /blog — create or draft a blog post

**Trigger:** `/blog [topic or title]`

**Flow varies** — sometimes the user writes alone, sometimes collaboratively.

**Scaffold mode:**
```
User: /blog "Why GitOps Matters"

Agent: creates content/blog/2026/04/why-gitops-matters/index.md
       with frontmatter + suggested outline
User: writes the post
```

**Collaborative mode:**
```
User: /blog "Why GitOps Matters"
User: "write a draft based on wiki/gitops-fleet-management.md
       and my cards about continuous assembly"

Agent: reads sources, writes draft
User: edits
Agent: updates file
Agent: commits — "blog: Why GitOps Matters"
```

**Rules:**
- Blog posts are the USER's voice. Even in collaborative mode, the agent drafts — the user decides what stays.
- Frontmatter includes software_version.

### /query — explicit knowledge base query

**Trigger:** `/query <question>` (also the default mode — any question triggers this)

**Flow:**
```
User: /query what connects continuous assembly and fleet management?
      (or just: "what connects continuous assembly and fleet management?")

Agent: searches Qdrant for semantically related content
Agent: reads content/index.md → finds relevant MOCs
Agent: reads wiki pages, cards, bib entries
Agent:
  "Both approaches apply declarative management to physical systems.
   CA targets hardware/agents, GitOps FM targets device fleets.

   Sources:
   - wiki/continuous-assembly.md
   - wiki/gitops-fleet-management.md
   - cards/4e74e25e-03e8-7ed3-a252-6023e2d6b6c5.md
   - bib/069cf951-...

   Save as wiki page (comparison/synthesis)?"

User: "yes, synthesis"

Agent: creates wiki/ca-and-gitops-synthesis.md
Agent: updates index/MOCs
Agent: commits — "wiki: create CA and GitOps synthesis"
```

**Rules:**
- Always cite sources with links.
- Use both Qdrant semantic search and structured MOC navigation — semantic search finds unexpected connections, MOCs ensure known territory is covered.
- Offer to save valuable answers as wiki pages.
- During Q&A, if a thought worth capturing emerges, suggest `/card`.

### /socrates — knowledge integration through dialogue

**Trigger:** `/socrates` or natural entry ("let's discuss", "let's think about this")

**Flow:**
```
User provides context (or context is already in chat)
Agent creates sessions/{uuid7}/index.md
Agent searches knowledge base for related content
Dialogue proceeds with escalation (simple → complex questions)
Agent records transcript continuously
Cards emerge during dialogue — proposed with provenance checklist
Session ends when it ends (user stops, context fills, day is over)
Cards go through standard /card flow
Bridges proposed after full cluster is published
```

**Rules:**
- Agent is an opponent, not a mirror — challenges with knowledge base and general knowledge
- Transcript records user's words close to verbatim, agent's words compressed
- Every card proposal includes: user's original words, card text, checklist (provenance, self-containment, scientific style, neighbors checked, bridges)
- Don't be stingy with cards — better to save too many than lose one
- Sessions stored in `sessions/` (private, not published)

See `skills/socrates/SKILL.md` for full specification.

### /lint — health check

**Trigger:** `/lint`

**Checks:**
- Contradictions between pages
- Stale claims superseded by newer sources
- Orphan pages (no inbound links)
- Concepts mentioned but lacking their own page
- Missing cross-references
- Bib entries without wiki coverage
- Dense card clusters that could become concept pages
- MOCs that need splitting or reorganizing
- Suggestions for new sources to investigate

**Flow:**
```
Agent: scans content/
Agent:
  "Found:
   - 3 orphan wiki pages (no inbound links)
   - bib/069cf951-... has no wiki coverage
   - 6 cards about 'multi-agent systems' — concept page?
   - wiki/continuous-assembly.md mentions 'Nix' but no entity page

   Fix these?"

User: selects what to fix
Agent: applies fixes, commits
```

## Publish layer

Cards are authored as UUID-identified files first, and published to external platforms later. A card may be published to zero, one, or many platforms. Each publish appends an entry to `card_published[]`:

```yaml
card_published:
  - platform: twitter
    id: "2039600765296386127"
    date: 2026-04-02T07:09:41.249Z
  - platform: bluesky
    id: "at://did:plc:.../app.bsky.feed.post/..."
    date: 2026-04-10T09:00:00.000Z
```

The publish platform is not coupled to the card's identity. If an account is lost, a card can be re-published elsewhere without changing its UUID or its local links.

**Current target platforms:** Bluesky (primary going forward). Twitter entries exist for legacy cards as a historical record; new cards do not publish to Twitter.

**Configuration:** target platforms and credentials live in `~/.config/thinkbox/config.toml` (outside the repo). The `/publish` skill reads this file.

### Local references vs external sources

Two different fields, two different meanings:

- `card_ref`: **strictly local UUID → local UUID.** Bridge between two cards in the same knowledge base.
- `card_bib`: **external source.** Points to a bib entry (by bib UUID). Every external reference is a bib entry — no exceptions.

This rule keeps local graph edges clean and separates internal structure from external citation.

### Stability rule for published content

A card with a non-empty `card_published[]` is **published and stable.** Its body must not be rewritten to contradict what was published. If new information contradicts a published card, create a new card and note the contradiction on both. Wiki pages can always be enriched, but structural positions should similarly be preserved once linked from the outside world.

## Cross-references

All internal links are relative markdown links with `.md` extensions.

- wiki → bib: `[Title](../bib/069cf951-....md)`
- wiki → wiki: `[Title](other-page.md)`
- wiki → card: `[snippet](../cards/4e74e25e-....md)`
- wiki → blog: `[Title](../blog/2026/01/slug/index.md)`
- card → card: `card_reply_to`, `card_ref` (frontmatter, local UUIDs)
- card → bib: `card_bib` (frontmatter, bib UUID — the only external reference path)
- blog → anything: relative `.md` link in body
- Backlinks: computed at build time by the renderer

## ID schemes

| Content | ID format | Example |
|---|---|---|
| Artifacts | UUID v7 | `069cf951-a5fa-7141-8000-494f71cd145d` |
| Bib entries | Same UUID as artifact | `069cf951-a5fa-7141-8000-494f71cd145d` |
| Cards | UUID v7 | `4e74e25e-03e8-7ed3-a252-6023e2d6b6c5` |
| Wiki pages | Slug | `continuous-assembly` |
| Blog posts | Path slug | `2026/01/product-over-technology` |

## Versioning

Every content file includes `software_version: "0.1.0"` — the thinkbox platform version that created/last updated it. This enables:
- Finding files created by older platform versions
- Running migrations when the platform schema changes
- Tracking what conventions were in effect when a file was written

Version follows semver. Bumped when platform conventions change.

## Search: Qdrant

All content files are indexed in a Qdrant vector database for semantic search.

### What gets indexed

Everything in `content/`: wiki pages, cards, blog posts, bib entries. NOT artifacts (private, copyrighted).

### Indexing pipeline

Runs on every commit to `content/` — including external commits (manual edits, other tools).

```
git commit in content/
       ↓
post-commit hook (or CI)
       ↓
detect changed .md files
       ↓
generate embeddings
       ↓
upsert to Qdrant
```

### Collection structure

One collection. Each point includes metadata:
- `type`: wiki | cards | blog | bib
- `path`: file path relative to content/
- `title`: page title or first line (for cards)
- `tags`: from frontmatter
- Frontmatter fields relevant to the type

### Agent search interface

`thinkbox/scripts/search.sh` — CLI wrapper around `search.py`. Embeds the query with the same model (Qwen3-Embedding-8B via OpenRouter) and searches Qdrant. Returns ranked results with path, title, score, and full file content. Supports `-t` filter (wiki/cards/bib/blog) and `-n` limit.

### Indexing pipeline (implementation)

`thinkbox-embed` (installed via `pip install git+...thinkbox.git`) — runs on push to main (GitHub Action) or locally:
1. Walks `wiki/`, `cards/`, `bib/`, `blog/` — collects all `.md` files
2. Computes SHA-256 hash per file, compares with Qdrant state
3. Embeds new/changed files via OpenRouter, upserts to Qdrant
4. Deletes points for removed files

### Search + navigation

Qdrant search complements (does not replace) the index.md → MOC → page navigation. The agent uses both:
- **Structured navigation** (index/MOC) when exploring a known topic area
- **Semantic search** (Qdrant) when the query doesn't map to a known MOC, or to find unexpected connections across topics

## Tooling (current)

Claude Code direct — Write/Edit/Grep tools on content/ and artifacts/ files. Qdrant semantic search via `thinkbox-search`. The architecture doesn't depend on tooling choice; files are files.

For web sources, the agent uses WebFetch to download articles. For local files, the user points to the path. Artifacts are stored locally in `artifacts/` (will migrate to S3).

## What thinkbox ships

For someone else to use this system:

1. `thinkbox/` — skills, conventions, scripts, this architecture doc
2. A renderer (Astro template or bring your own)
3. `content/` scaffold — empty `wiki/`, `cards/`, `blog/`, `bib/`, `index.md`
4. `artifacts/` directory (local or S3)
5. `~/.config/thinkbox/config.toml` — target platforms and credentials for publishing

The content is personal. The platform is the method.
