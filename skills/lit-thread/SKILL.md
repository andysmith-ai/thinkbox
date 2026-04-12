---
name: lit-thread
description: >
  Create and publish a literature card thread from a bib entry. Reads the
  bib entry's ingestion manifest, extracts one atomic idea per wiki concept
  page, drafts a card thread (root summary + one card per idea), shows
  it for approval, then publishes in order. Use this skill when the user
  says "/lit-thread", "create literature cards from", "make a thread from
  this article", or asks to turn an ingested source into publishable cards.
---

# Literature Thread

Version: **0.1.0**

Create a thread of literature cards from an ingested source. Each card captures one atomic idea from the source in ≤300 characters. The thread is published to Bluesky as a root post with link preview + reply chain.

## Trigger

`/lit-thread <bib-uuid>`

## Prerequisites

The source must already be ingested (`/ingest`). A bib entry and wiki concept pages must exist.

## Flow

### 1. Load the source

Read `content/bib/{bib-uuid}.md`. Extract:
- `bib_title`, `bib_author`, `bib_url`
- The **Ingestion manifest** section — list of wiki pages linked from the bib body

### 2. Read wiki pages

Read each wiki page listed in the ingestion manifest. Focus on:
- **Source summary page** (wiki_type: source) — for the root card
- **Concept pages** (wiki_type: concept) — one card per concept

### 3. Extract images

Read `artifacts/{bib-uuid}/original.md` and identify diagrams/figures. For each `<figure>` or `![](...)` in the source:
- Extract the CDN URL (may be double-encoded; decode `%252F` → `/`)
- Match the figure to a concept by its caption and surrounding text

**Image-to-card mapping:** assign each image URL to the concept card it illustrates. Not every card will have an image — only cards where the source contains a relevant diagram. The URLs go into the card's `card_images` field; the publish script downloads them at publish time.

### 4. Draft the thread

Create a draft thread. Every card follows the standard card rules (plain text, ≤300 chars, English, no URLs in body).

**Root card:**
```yaml
card_type: literature
card_bib: "{bib-uuid}"
card_embed_url: "{bib_url}"    # link preview on publish
card_context: "lit-thread from {bib_title}"
```
Body: a one-sentence summary of the source's central argument or contribution. This is what readers see first, with a link preview card attached. No images on root (link preview uses the embed slot).

**Idea cards** (one per concept page):
```yaml
card_type: literature
card_bib: "{bib-uuid}"
card_reply_to: "{previous-card-uuid}"    # chains to previous card
card_images:                              # optional, if source has a matching diagram
  - "https://cdn.example.com/diagram.png"
card_context: "lit-thread from {bib_title}"
```
Body: one atomic idea from the concept page. Not a summary of the page — extract the single most transferable insight.

**Thread order:** root → idea cards in a logical reading order (typically: foundational concepts first, specific patterns/applications after, meta-insights last).

### 5. Present for approval

Show the complete draft thread to the user:

```
## Literature thread: {bib_title}

**Root** (with link preview → {bib_url}):
> {root card body} ({char count} chars)

**Card 2** (from: {concept page title}) [image: {slug}.png]:
> {card body} ({char count} chars)

**Card 3** (from: {concept page title}):
> {card body} ({char count} chars)

...

{N} cards total, {M} with images. Approve to create files and publish?
```

Wait for the user to approve, request edits, or reject.

### 6. Create card files

After approval, for each card in the thread:

1. Generate UUID v7: `thinkbox/scripts/uuid7.sh`
2. Generate ISO timestamp: `date -u +"%Y-%m-%dT%H:%M:%S.000Z"`
3. Write `content/cards/{uuid}.md` (with `card_images: ["<url>"]` if image was mapped)

The root card is created first. Each subsequent card's `card_reply_to` points to the previous card's UUID. Images are not downloaded yet — the publish script handles that at publish time.

Commit all card files together: `card: lit-thread: {bib_title}`

### 7. Publish

Publish cards in order, root first, each reply after its parent:

```sh
./thinkbox/scripts/publish.sh --card {root-uuid} --no-commit
./thinkbox/scripts/publish.sh --card {card-2-uuid} --no-commit
./thinkbox/scripts/publish.sh --card {card-3-uuid} --no-commit
...
```

Use `--no-commit` for each individual publish, then commit all updated card files together:

```sh
git -C content add cards/
git -C content commit -m "publish: bluesky: lit-thread: {bib_title}"
```

### 8. Report

After publishing, show:
- Link to the root post on Bluesky (construct from the AT URI)
- Count of cards published
- Count of images attached
- Any errors encountered

## Rules

- Every card ≤300 characters, plain text, no URLs in body
- `card_bib` on every card (provenance)
- `card_embed_url` on root card only (link preview)
- `card_images` on reply cards only (mutually exclusive with `card_embed_url`)
- `card_reply_to` chains each card to the previous (reply-to-previous, not reply-to-root)
- One card per concept — if a wiki concept page has multiple distinct ideas, pick the most transferable one
- The thread should cover all concept pages from the ingestion manifest
- Do not skip concept pages unless the user explicitly asks
- Do not create permanent cards — all cards in a literature thread are `card_type: literature`
- The user must approve the draft before any files are created or published
- Images come from the source article's diagrams/figures, stored as URLs in `card_images` (downloaded at publish time)
- Up to 4 images per card (Bluesky limit), but typically 1 diagram per concept
