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
│   ├── x/                   ← xettel: user's atomic thoughts
│   ├── blog/                ← user's long-form articles
│   └── bib/                 ← bibliography / source registry
├── sessions/                ← Socratic dialogue transcripts (private, not in git)
│   └── {uuid7}/index.md
└── thinkbox/                ← platform (shareable)
    ├── CLAUDE.md            ← platform conventions for the LLM
    ├── ARCHITECTURE.md      ← this file
    └── skills/
        ├── xettel/SKILL.md
        ├── ingest/SKILL.md
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
- Xettel cards — the user's own ideas are first-class sources. Wiki treats them like ideas from any other thinker. Specific mechanisms:
  - **Contradiction:** ingest finds an external source that contradicts a user's xettel card. Wiki page notes the disagreement with links to both.
  - **Development:** external source extends or deepens a user's idea. Wiki page connects them.
  - **Convergence:** user independently arrived at a conclusion also found in literature. Wiki notes this.
  - **Clustering:** lint detects a dense cluster of related xettel cards. LLM proposes a concept page synthesizing them.
- Wiki does NOT copy xettel card text. It links to cards (`[[twitter_id]]`) and writes its own synthesis.

**Page types:**
- **Source summary** — key takeaways from an ingested source, what's new, what contradicts existing knowledge.
- **Entity** — a person, project, tool, company. Aggregates everything known.
- **Concept** — an idea, principle, pattern. Synthesis across sources and xettel.
- **Comparison** — structured comparison of entities or concepts.
- **Synthesis** — cross-cutting analysis connecting multiple concepts.
- **MOC (Map of Content)** — thematic navigation page. Links to wiki pages, xettel threads, blog posts, bib entries related to a topic. Created and maintained by the LLM.

**Format:**
```yaml
---
title: "Page Title"
wiki_type: entity | concept | source | comparison | synthesis | moc
wiki_created: 2026-04-05
wiki_updated: 2026-04-05
wiki_sources:
  - bib: "069cf951-..."
  - xettel: "2039600765296386127"
tags: [tag1, tag2]
software_version: "0.1.0"
---
```

Body: markdown with `[[wikilinks]]`.

**File naming:** slug-based. `continuous-assembly.md`, `nassim-taleb.md`, `moc-ai-agents.md`.

### 4. x/ — xettel cards (user's thoughts, public)

The user's own atomic, transferable thoughts. 280 characters. One card = one tweet = one thought. Published on Twitter/X and on the site.

The LLM helps formulate but never writes cards autonomously — every card must pass through the user.

**All xettel cards are permanent.** There is no literature or fleeting type. Recording external knowledge is wiki's job. Xettel is always the user's own voice. If a thought is inspired by an external source, it's still a permanent card — the source is tracked in metadata and can be included as a URL in the tweet.

**Cards do NOT contain links to the site.** Pure text + Twitter threading. Wiki, bib, and blog posts may contain site links when announced on Twitter.

**Workflow:** card is created → published to Twitter → Twitter status ID becomes the file name and xettel_id.

**Format:**
```yaml
---
xettel_id: "2039600765296386127"
xettel_type: permanent
xettel_published_date: 2026-04-02T07:09:41.249Z
xettel_reply_to: "2039309313987187063"    # optional, thread placement
xettel_ref: "2039590834027508118"          # optional, bridge cards (xettel→xettel)
xettel_bib: "069cf951-a5fa-7141-8000-..."  # optional, source that inspired the card
xettel_context: "chat 2026-04-05, ..."     # optional, what prompted the card
software_version: "0.1.0"
---
```

Body: card text, plain text, no markdown.

**Character limits and URLs in tweets:**
- Body only: ≤280 chars
- Body + source URL (bib_url): ≤257 chars — source URL is appended to tweet so readers can find the original. Used when the card is inspired by an external source.
- Body + ref (bridge card): ≤257 chars — ref resolves to another tweet's URL
- Body + ref + source URL: ≤234 chars — both URLs in tweet (rare, tight)

The source URL comes from `bib_url` of the referenced bib entry. It is appended at publish time, not stored in the card body.

**File naming:** `{twitter_status_id}.md`. Filename IS the Twitter ID — direct bidirectional mapping without storing URLs.

**IDs in frontmatter:** plain strings, not `[[wikilinks]]`. The renderer resolves links.

### 5. blog/ — user's articles (public)

Long-form articles by the user.

**Format:**
```yaml
---
title: "Article Title"
description: "One-liner"
date: 2026-01-27T10:43:54
featured_image: image.png       # optional
twitter_discussion: "url"        # optional
software_version: "0.1.0"
---
```

Body: markdown with `[[wikilinks]]`.

**Directory structure:** `blog/YYYY/MM/slug/index.md`

## Navigation

### index.md (top-level)

`content/index.md` — entry point for the entire knowledge base. Not a flat list. Links to MOCs and top-level content.

The LLM reads this first when answering queries or deciding where new content fits.

### MOCs (Maps of Content)

`wiki/moc-{topic}.md` — thematic navigation pages. Each MOC covers a topic area and links to relevant wiki pages, xettel threads, blog posts, and bib entries.

MOCs are created and maintained by the LLM. As content grows, the LLM splits large MOCs or creates new ones.

Navigation path: `index.md → MOC → content pages`. Can be multiple hops deep.

### No separate log

Git log IS the log. Commit messages follow a convention:

```
ingest: {source title}
wiki: create {page title}
wiki: update {page title}
xettel: {short description}
blog: {post title}
bib: {source title}
lint: {what was fixed}
```

No separate `log.md`. The index and MOCs handle navigation; git handles history.

## Default mode

The agent's default behavior is **Q&A against the knowledge base.** Any question the user asks — the agent reads index, navigates MOCs, reads relevant pages, and synthesizes an answer with citations. No special command needed.

During Q&A, a thought may emerge that's worth capturing as a xettel card. The agent can suggest it; the user can ask for it. The flow naturally transitions from Q&A to `/xettel` without breaking conversation.

## Skills

All operations are invoked as explicit skills. The agent also recognizes natural-language equivalents, but skills are the canonical entry points.

### /ingest — process an external source

**Trigger:** `/ingest <url>` or `/ingest <path to local file>`

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
- Never creates xettel cards — those are the user's thoughts.
- Checks existing wiki pages for contradictions/connections with the new source.

### /xettel — create an atomic thought

**Trigger:** `/xettel [initial thought in any language]`

Can also emerge naturally from Q&A — user says "let's capture this" or agent suggests "this could be a card."

**Flow:**
```
User: /xettel conflict of interest can't be resolved inside one head

Agent:
  "Variant: «Conflict of interest can't be resolved inside
   one head.» (57 chars)

   Type: permanent
   Placement: root

   Or reply_to [[2039242733743927461]]?"

User: "root, good"

Agent:
  "Ready to publish:

   Conflict of interest can't be resolved inside one head.

   Type: permanent | Root | 57 chars
   Publish to Twitter and give me the ID."

User: ... publishes manually ...
User: "2039700000000000000"

Agent: creates content/x/2039700000000000000.md
Agent: commits — "xettel: conflict of interest"
```

**Rules:**
- Every card passes through the user. Agent proposes, user approves.
- Card text is always in English.
- Body: plain text, no markdown, no links.
- ≤280 chars (≤257 with ref).
- File is created only AFTER the user provides the Twitter status ID.
- Agent may suggest bridge cards connecting to existing xettel/wiki.

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
       and my xettel cards about continuous assembly"

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
Agent: reads wiki pages, xettel cards, bib entries
Agent:
  "Both approaches apply declarative management to physical systems.
   CA targets hardware/agents, GitOps FM targets device fleets.

   Sources:
   - wiki/continuous-assembly.md
   - wiki/gitops-fleet-management.md
   - xettel [[2039242733743927461]]
   - bib [[069cf951-...]]

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
- During Q&A, if a thought worth capturing emerges, suggest `/xettel`.

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
Cards go through standard /xettel flow
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
- Dense xettel clusters that could become concept pages
- MOCs that need splitting or reorganizing
- Suggestions for new sources to investigate

**Flow:**
```
Agent: scans content/
Agent:
  "Found:
   - 3 orphan wiki pages (no inbound links)
   - bib/069cf951-... has no wiki coverage
   - 6 xettel cards about 'multi-agent systems' — concept page?
   - wiki/continuous-assembly.md mentions 'Nix' but no entity page

   Fix these?"

User: selects what to fix
Agent: applies fixes, commits
```

## Twitter as the universal link layer

All content is announced on Twitter at creation. Every content file stores its `twitter_id`. This makes Twitter the universal entry point — anyone can find any piece of content via a tweet link.

**Xettel:** tweet IS the content. `twitter_id` = filename = `xettel_id`.

**Wiki / bib / blog:** tweet is an announcement with a link to the site page. `twitter_id` stored in frontmatter.

```yaml
# wiki frontmatter
twitter_id: "2039800000000000000"

# bib frontmatter
twitter_id: "2039800000000000000"

# blog frontmatter (rename twitter_discussion → twitter_id)
twitter_id: "2039800000000000000"
```

### ref scope: any content with a twitter_id

`xettel_ref` can point to ANY content that has been announced on Twitter — xettel cards, wiki pages, bib entries, blog posts. Ref always stores a twitter_id. At publish time, it resolves to the tweet URL.

This means bridge cards can connect the user's thoughts to anything on Twitter:
- xettel → xettel (thought connects to thought)
- xettel → wiki (thought connects to structured knowledge)
- xettel → bib (thought connects to a source)
- xettel → blog (thought connects to an article)
- xettel → external tweet (thought connects to someone else's idea)

If a twitter_id doesn't match any local content file, it's an external tweet. No special flag needed.

### Stability rule for published content

A wiki page (or any content) that has a `twitter_id` is **published and stable.** Bridge cards and other tweets may reference it. The content can be enriched (new sources, additional detail), but must not be rewritten to contradict its original position. If new information fundamentally contradicts a published page, create a new page with the new position and note the contradiction on both pages.

## Cross-references

- wiki → bib: `[[069cf951-...]]`
- wiki → wiki: `[[slug]]`
- wiki → xettel: `[[2039600765296386127]]`
- wiki → blog: `[[2026/01/slug]]`
- xettel → xettel: `xettel_reply_to`, `xettel_ref` (frontmatter, twitter_ids)
- xettel → any content: `xettel_ref` (frontmatter, twitter_id of target)
- xettel → bib: `xettel_bib` (frontmatter, artifact UUID)
- blog → anything: `[[target]]` in body
- Backlinks: computed at build time by the renderer

## ID schemes

| Content | ID format | Example |
|---|---|---|
| Artifacts | UUID v7 | `069cf951-a5fa-7141-8000-494f71cd145d` |
| Bib entries | Same UUID as artifact | `069cf951-a5fa-7141-8000-494f71cd145d` |
| Xettel cards | Twitter status ID | `2039600765296386127` |
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

Everything in `content/`: wiki pages, xettel cards, blog posts, bib entries. NOT artifacts (private, copyrighted).

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
- `type`: wiki | xettel | blog | bib
- `path`: file path relative to content/
- `title`: page title or first line (for xettel)
- `tags`: from frontmatter
- Frontmatter fields relevant to the type

### Agent search interface

`thinkbox/scripts/search.sh` — CLI wrapper around `search.py`. Embeds the query with the same model (Qwen3-Embedding-8B via OpenRouter) and searches Qdrant. Returns ranked results with path, title, score, and full file content. Supports `-t` filter (wiki/x/bib/blog) and `-n` limit.

### Indexing pipeline (implementation)

`thinkbox-embed` (installed via `pip install git+...thinkbox.git`) — runs on push to main (GitHub Action) or locally:
1. Walks `wiki/`, `x/`, `bib/`, `blog/` — collects all `.md` files
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

## Reconciling SKILL.md

The xettel SKILL.md (v1.2.0) will be rewritten to match actual format:

| Change | Detail |
|---|---|
| Nested `meta: {}` → flat frontmatter | `xettel_type`, `xettel_reply_to`, etc. |
| `[[wikilink]]` in meta → plain strings | `xettel_reply_to: "id"` |
| `scope`, `version` per card → dropped | Replaced by `software_version` |
| `url` field → dropped | Filename IS the Twitter ID |
| `source`/`link` → `xettel_bib` | Bib entry holds source details |
| `context` → `xettel_context` | Optional field |
| Method and philosophy sections | Preserved as-is |

## What thinkbox ships

For someone else to use this system:

1. `thinkbox/` — skills, conventions, this architecture doc
2. A renderer (Astro template or bring your own)
3. `content/` scaffold — empty `wiki/`, `x/`, `blog/`, `bib/`, `index.md`
4. `artifacts/` directory (local or S3)

The content is personal. The platform is the method.
