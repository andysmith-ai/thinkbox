---
name: publish
description: >
  Prepare cards for publication on X (Twitter).
  Outputs ready-to-copy posts into x.md at workspace root.
  Use this skill when the user says "publish", "post",
  "prepare for publication", or asks to put a card into x.md.
---

# Publish: X post preparation

Version: **0.1.0**

> **Note:** This skill is scheduled for replacement. It still describes the legacy Twitter-only flow where card files are named by Twitter status ID. The new publish flow (UUID-identified cards, pluggable platform adapters, `card_published[]` tracking) is defined in `thinkbox/ARCHITECTURE.md` under "Publish layer" and will be implemented in a follow-up step.

## Purpose

Take approved card text and prepare it for publication in `x.md` — the user's copy-paste buffer for posting to X. The user should be able to open the file, copy the text, and paste it into X with zero assembly.

## Output file

`x.md` at workspace root (not in git). Single-slot buffer — always contains only the current card to publish. Each new card replaces the previous content entirely.

## Post format

Every post has two parts: a `Reply to:` line and a code block with the tweet text.

### Root card (new thread)

```
Reply to: root

\```
Card text here.
\```
```

### Reply card

```
Reply to: https://x.com/andysmith_ai/status/<reply_to_id>

\```
Card text here.
\```
```

### Bridge card (reply with ref link)

```
Reply to: https://x.com/andysmith_ai/status/<reply_to_id>

\```
Card text here. https://x.com/andysmith_ai/status/<ref_id>
\```
```

## Rules

1. **One card at a time.** `x.md` contains only the current card to publish. When the user provides a status ID and the agent writes the next card, the previous content is replaced. The file is a single-slot buffer, not a log.
2. **Wait for dependencies.** If a card depends on a status ID that doesn't exist yet (e.g. reply_to a card not yet published), do not output it. Wait for the user to publish the dependency and provide the status ID first.
3. **Ready to paste.** The code block contains exactly what gets pasted into X. No markdown, no wikilinks. If there's a ref link or source URL, it's already appended to the text inside the code block.
4. **`Reply to: root`** for root cards — makes it explicit this is intentional, not a missing value.
5. **Character limits apply.** Body only: 280. Body + 1 URL in text: 257. Body + 2 URLs: 234.

## Workflow

1. Agent writes the first publishable card into `x.md`.
2. User publishes it on X, pastes the status ID back.
3. Agent appends `{platform: twitter, id: {status_id}, date: {today}}` to the card's `card_published` list in `content/cards/{uuid}.md`.
4. If there are more cards, agent writes the next card into `x.md` (with the real `Reply to:` URL if it depended on the previous card's ID).
5. Repeat 2–4 until all cards are published.
6. Agent updates MOCs and wiki pages (see graph integration below).
7. Agent commits all changed files and navigation updates together (`publish: ...`).

## After publishing: graph integration

### Navigation (agent's job)

Before committing, the agent updates the navigation tree:
- Add links to new cards in relevant MOCs (`content/wiki/moc-*.md`).
- Update wiki pages if the card adds a new angle to an existing topic.
- Commit everything together — cards and navigation updates — in one commit.

### Bridges (user's decision)

The agent scans existing cards and suggests potential bridges — but never creates them without the user's approval. A suggestion looks like:

> Bridge idea: this card connects to [card X text] — because [reason]. Want to create a bridge?

If the user approves, formulate the bridge card and continue the publish flow.

## What this skill does NOT do

- Does not formulate cards — that's `/card`.
- Does not publish to X — the user does that manually.
