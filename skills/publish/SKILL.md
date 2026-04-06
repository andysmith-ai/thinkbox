---
name: publish
description: >
  Prepare xettel cards for publication on X (Twitter).
  Outputs ready-to-copy posts into x.md at workspace root.
  Use this skill when the user says "publish", "post",
  "prepare for publication", or asks to put a card into x.md.
---

# Publish: X post preparation

Version: **0.1.0**

## Purpose

Take approved xettel card text and prepare it for publication in `x.md` — the user's copy-paste buffer for posting to X. The user should be able to open the file, copy the text, and paste it into X with zero assembly.

## Output file

`x.md` at workspace root (not in git). The file has a template/instructions section at the top separated from content by `===============================`. **Never modify anything above the separator.**

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

1. **Append only.** Always append below the `===============================` separator. Never overwrite or delete existing content above it.
2. **One card at a time.** If a card depends on a status ID that doesn't exist yet (e.g. reply_to a card not yet published), do not output it. Wait for the user to publish the dependency and provide the status ID first.
3. **Ready to paste.** The code block contains exactly what gets pasted into X. No markdown, no wikilinks. If there's a ref link or source URL, it's already appended to the text inside the code block.
4. **`Reply to: root`** for root cards — makes it explicit this is intentional, not a missing value.
5. **Character limits apply.** Body only: 280. Body + 1 URL in text: 257. Body + 2 URLs: 234.

## Workflow

1. Agent writes the first publishable card into `x.md`.
2. User publishes it on X, pastes the status ID back.
3. Agent creates `content/x/{status_id}.md` with proper frontmatter.
4. If there are more cards, agent writes the next card into `x.md` (with the real `Reply to:` URL if it depended on the previous card's ID).
5. Repeat 2–4 until all cards are published.
6. Agent commits all created files (`xettel: ...`).

## What this skill does NOT do

- Does not formulate cards — that's `/xettel`.
- Does not publish to X — the user does that manually.
