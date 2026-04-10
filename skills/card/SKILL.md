---
name: card
description: >
  Write and manage cards — Zettelkasten-style atomic notes. Each card is a
  single thought formatted to fit in 280 characters. Use this skill whenever
  the user mentions "card", asks to turn an idea into a note, draft a
  thread, or formulate a thought concisely. Also triggers when the user
  says "save this as a card" or "make a thread from this."
---

# Card: atomic thought notes

Version: **0.1.0**

## The Method

### The box is a thinking tool, not an archive

The purpose of the box is not to store information. It is to think. Every card exists because it contributes to thinking — it connects to something, challenges something, or develops something. Cards that don't connect to anything are dead weight. Don't save things "just in case." The box is not a collection — it is a conversation partner.

### Transferability — the master criterion

A thought belongs in the box if it is transferable: it can be useful in a context different from the one where it was born. This is the single test. Everything else follows from it.

A transferable thought has legs — it can walk from one domain to another and still mean something. A thought trapped in one context is not a card, it's a diary entry.

How to test: take the thought and mentally place it in a conversation about a completely different topic. Does it still contribute? Does it provoke a question, offer a lens, suggest a mechanism? If yes — it's transferable.

What makes a thought transferable: it captures a mechanism (why something works), a principle (a pattern that recurs), a distinction (how two things that look the same are different), a contradiction (how two things that seem compatible aren't), or a question that opens inquiry across domains.

What is NOT transferable: a fact bound to one context (a version number, a date, a config setting). A decision without the reasoning behind it. A feeling without analysis. A quote without your reaction. A reminder. Anything saved "just in case."

### A card is a thought, not a reminder of a thought

The card must contain the actual thought in written form — not a pointer to a thought you once had. If reading the card six months later, you should not need to reconstruct what you meant. The thought is right there, fully formed. A reminder ("look into X", "interesting idea from Y") is not a card.

### Own words

Every card is in the user's own words. Never a copy, never a quote-as-content. Writing in your own words forces understanding — if you can't reformulate it, you haven't processed it.

### Atomicity

One card = one thought. The 280-character limit is not a suggestion — it is the mechanism that enforces this. If you can't say it in 280 characters, either you haven't found the core yet, or it's more than one thought.

The title test (from Luhmann): if you can give two parts of a card different titles, they are two cards.

### Self-containment

Every card must be understandable without context. A stranger reading just this one card — with no access to the thread, no knowledge of the conversation it came from — should understand the idea.

No "as discussed above." No implicit references. No cards that only make sense as part of a sequence. If a card needs its parent to be understood, it's not a card — it's a fragment.

### Contradictions are especially valuable

The box should actively seek disagreement. Dis-confirming data is more valuable than confirming data, because it opens more possible connections and discussions. A card that contradicts an existing card is not a problem — it is an opportunity.

## Card type

**All new cards are permanent.** Cards are the user's own voice. If a thought is inspired by an external source, it's still a permanent card — the source is tracked in `card_bib` metadata.

Legacy `literature` cards exist in the archive from an earlier convention. Do not create new literature cards.

## Card format

### Body

- **Clean text — exactly what gets published.** No wikilinks, no markdown. Plain text only.
- **Language: English only.** Body, context, all fields.
- **Style: write as you would in the strongest paragraph of your best paper.** Clear, precise, direct. Not social-media-casual and not bad-academic.
- No title. The body is the entire content.

### Character counting

280 characters is a thinking discipline, not a platform constraint. It is kept regardless of target platform.

1. Count all visible characters in the body.
2. Any URL appearing in the body counts as 23 characters + 1 space separator (the historic t.co budget — kept as a uniform rule so cards stay portable across platforms).
3. Limits:
   - Body only: **≤280** chars
   - Body + 1 URL in body: **≤257** chars
   - Body + 2 URLs in body: **≤234** chars

Card bodies normally do NOT contain URLs — external references flow through `card_bib`, and bridge refs through `card_ref`. URLs in the body are only for rare cases where the URL is an essential part of the thought.

### Frontmatter

```yaml
---
card_type: permanent
card_created: 2026-04-05T12:34:56.000Z
card_reply_to: "4e6101fa-c998-7b33-a2e2-621a532edee3"   # optional, thread placement
card_ref: "4e72ff2a-2008-7132-a43b-0a2a4ed04ce0"         # optional, bridge cards
card_bib: "069cf951-a5fa-7141-8000-494f71cd145d"         # optional, source that inspired the card
card_context: "chat 2026-04-05, knowledge integration"   # optional, what prompted the card
card_published: []                                        # filled in by /publish
software_version: "0.1.0"
---
```

- **filename IS the card ID** — a UUID v7 string. There is no `card_id` field inside the file.
- **card_type** — always `permanent`.
- **card_created** — ISO 8601 timestamp when the card file was created.
- **card_reply_to** — UUID of parent card. Absent for root cards. LOCAL only (must point to another card file in `content/cards/`).
- **card_ref** — UUID of referenced local content. Only on bridge cards. LOCAL only — must point to another card, wiki page, bib entry, or blog post in this knowledge base. External sources go through `card_bib`.
- **card_bib** — UUID of the bib entry for the source that inspired this card.
- **card_context** — free text describing what prompted this card.
- **card_published** — list of `{platform, id, date}` entries, one per platform the card has been published on. Starts empty and is populated by `/publish`. Empty/absent until first publish.
- **software_version** — thinkbox platform version.

### File naming

`content/cards/{uuid7}.md` — filename is a UUID v7 string. Generate via `thinkbox/scripts/uuid7.sh`.

## Placement

### Root vs reply_to

**Root** — when the thought opens a new area. No specific existing card that this thought grows from.

**Reply_to** — when the thought grows from a specific existing card. Not "continues" — grows from the same area. The test: if a reader has just read card X, would they naturally want to explore in the direction your card goes?

### The stumble-upon test

When placing a card, ask: "In which circumstances will I want to stumble upon this card, even if I forget about it?" Place the card where it will surprise you later, not where it seems tidy now.

## Linking principle

Cards don't link to each other directly. To connect card X and card Y, create a bridge card Z:

1. Z has `card_reply_to: "<X_uuid>"`, `card_ref: "<Y_uuid>"`
2. Z's text formulates the connection — why X relates to Y
3. Z's character limit is 280 (bridge refs are in frontmatter, not the body)

### Direction

- `card_reply_to` — where the conclusion flows from. Z lives in this thread.
- `card_ref` — where the conclusion points to. The related idea.

### Ref scope

`card_ref` is strictly local — it must point to a file in `content/` (card, wiki page, bib entry, or blog post) by its local identifier. External sources are never referenced by `card_ref`; they flow through `card_bib`.

## Threads

A thread is a chain of `card_reply_to` connections. No separate thread object. Threads can branch (two cards with the same `card_reply_to`).

## Workflow

1. **Formulate:** User provides a thought (in any language). Agent formulates it in English, ≤280 chars, proposes placement (root or reply_to).
2. **Approve:** User approves the text and placement.
3. **Create file:** Agent generates a UUID v7 (`thinkbox/scripts/uuid7.sh`) and creates `content/cards/{uuid}.md` with frontmatter and body. `card_published` starts empty.
4. **Commit:** `card: {short description}`

The card file exists as soon as it is written — there is no "wait for platform ID" step. Publication is a separate concern handled by `/publish`.

## Creating a card (file-based)

```
1. Run: thinkbox/scripts/uuid7.sh  →  {uuid}
2. Write content/cards/{uuid}.md:

---
card_type: permanent
card_created: {ISO timestamp}
card_reply_to: "{parent_uuid}"          # if reply
card_ref: "{ref_uuid}"                  # if bridge
card_bib: "{bib_uuid}"                  # if inspired by source
card_context: "chat {date}, {topic}"
card_published: []
software_version: "0.1.0"
---
Card text here, plain text, ≤280 chars.
```
