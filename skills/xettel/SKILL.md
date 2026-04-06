---
name: xettel
description: >
  Write and manage Xettel cards — Twitter-native Zettelkasten notes.
  Each card is a single thought formatted as a tweet (≤280 characters).
  Use this skill whenever the user mentions "xettel", "tweet", "card",
  or asks to turn an idea into a tweet-sized note, draft a thread,
  or formulate a thought concisely. Also triggers when the user says
  "save this as a tweet" or "make a thread from this."
---

# Xettel: Twitter-native Zettelkasten

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

## Card Type

**All new xettel cards are permanent.** Xettel is the user's own voice. If a thought is inspired by an external source, it's still a permanent card — the source is tracked in `xettel_bib` metadata and the source URL can be included in the tweet.

Legacy `literature` cards exist in the archive and will be rewritten over time. Do not create new literature cards.

## Card Format

### Body

- **Clean text — exactly what gets published.** No wikilinks, no markdown. Plain text only.
- **Language: English only.** Body, context, all fields.
- **Style: write as you would in the strongest paragraph of your best paper.** Clear, precise, direct. Not Twitter-casual and not bad-academic.
- No title. The body is the entire content.

### Character Counting

1. Count all visible characters in the body.
2. Each URL appended to the tweet consumes 23 characters (t.co shortening) + 1 space separator.
3. Limits:
   - Body only: **≤280** chars
   - Body + 1 URL (ref or source URL): **≤257** chars
   - Body + 2 URLs (ref + source URL): **≤234** chars

Bridge cards always have a ref, so their limit is always 257 (or 234 if they also have a source URL).

### Frontmatter

```yaml
---
xettel_id: "2039600765296386127"
xettel_type: permanent
xettel_published_date: 2026-04-02T07:09:41.249Z
xettel_reply_to: "2039309313987187063"       # optional, thread placement
xettel_ref: "2039590834027508118"             # optional, bridge cards
xettel_bib: "069cf951-a5fa-7141-8000-..."     # optional, source that inspired the card
xettel_context: "chat 2026-04-05, ..."        # optional, what prompted the card
software_version: "0.1.0"
---
```

- **xettel_id** — Twitter status ID. Same as filename.
- **xettel_type** — always `permanent`.
- **xettel_published_date** — ISO 8601 timestamp of publication.
- **xettel_reply_to** — Twitter ID of parent card. Absent for root cards.
- **xettel_ref** — Twitter ID of referenced card/content. Only on bridge cards. Can point to any content with a twitter_id: xettel cards, wiki pages, bib entries, blog posts, or external tweets.
- **xettel_bib** — UUID of the bib entry for the source that inspired this card. Source URL comes from the bib entry's `bib_url`.
- **xettel_context** — free text describing what prompted this card.
- **software_version** — thinkbox platform version.

### File naming

`content/x/{twitter_status_id}.md` — filename IS the Twitter ID.

## Placement

### Root vs reply_to

**Root** — when the thought opens a new area. No specific existing card that this thought grows from.

**Reply_to** — when the thought grows from a specific existing card. Not "continues" — grows from the same area. The test: if a reader has just read card X, would they naturally want to explore in the direction your card goes?

### The stumble-upon test

When placing a card, ask: "In which circumstances will I want to stumble upon this card, even if I forget about it?" Place the card where it will surprise you later, not where it seems tidy now.

## Linking Principle

Cards don't link to each other directly. To connect card X and card Y, create a bridge card Z:

1. Z has `xettel_reply_to: "<X_id>"`, `xettel_ref: "<Y_id>"`
2. Z's text formulates the connection — why X relates to Y
3. Z's character limit is 257 (always has ref)

### Direction

- `xettel_reply_to` — where the conclusion flows from. Z lives in this thread.
- `xettel_ref` — where the conclusion points to. The related idea.

### Ref scope

`xettel_ref` can point to any twitter_id — xettel cards, wiki pages, bib entries, blog posts, or external tweets. If a twitter_id doesn't match any local content file, it's an external tweet.

## Threads

A thread is a chain of `xettel_reply_to` connections. No separate thread object. Threads can branch (two cards with the same `xettel_reply_to`).

## Workflow

1. **Formulate:** User provides a thought (in any language). Agent formulates it in English, ≤280 chars, proposes placement (root or reply_to).
2. **Approve:** User approves the text and placement.
3. **Publish:** User publishes to Twitter manually and provides the status ID.
4. **Create file:** Agent creates `content/x/{status_id}.md` with frontmatter and body.
5. **Commit:** `xettel: {short description}`

The agent NEVER publishes or creates the file before the user provides the Twitter ID.

## Creating a card (file-based)

```
Write content/x/{twitter_id}.md:

---
xettel_id: "{twitter_id}"
xettel_type: permanent
xettel_published_date: {ISO timestamp}
xettel_reply_to: "{parent_id}"          # if reply
xettel_ref: "{ref_id}"                  # if bridge
xettel_bib: "{bib_uuid}"               # if inspired by source
xettel_context: "chat {date}, {topic}"
software_version: "0.1.0"
---
Card text here, plain text, ≤280 chars.
```
