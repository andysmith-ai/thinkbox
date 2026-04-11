---
name: transcribator
description: >
  Transcribe a session — record the user's words close to verbatim and a
  compressed italic summary of the agent's contributions to
  sessions/{uuid7}/index.md. Use this skill at the start of every Claude
  Code session to open a transcript, and append to it after every exchange.
  Triggers: "transcribe this session", "start a session", "resume session
  {uuid}", or automatic invocation at session start.
---

# Transcribator: session transcription

Version: **0.1.0**

## Purpose

Transcribator records a session as a readable markdown transcript. Every session becomes a durable external record — what the user thought, what got done, what remains open. The transcript survives context compression and allows resumption across days.

This is a standalone skill. It is the first skill to run in a session — before any other work begins — and it keeps running (by appending after every exchange) for the whole session.

## Storage

One directory per session:

```
sessions/{uuid7}/index.md
```

UUID v7 generated via `thinkbox/scripts/uuid7.sh`.

A session ID, once generated, is sticky for the remainder of the Claude Code session. Every exchange appends to the same file until the session ends or the user explicitly starts a new one.

## Format

A new session starts with just a header:

```markdown
# Session — {date}

```

The body is a sequence of `**User:**` / `**LLM:**` exchanges:

```markdown
**User:** {user's words, close to verbatim — fix spelling, punctuation,
remove filler words, but preserve meaning and phrasing exactly}

**LLM:** *{agent's contribution compressed to a few words —
just enough to understand the direction of the session}*

**User:** {next user message}

...
```

Optional H2 headers are inserted into the transcript as the session develops — never pre-filled, only added when there's something to record:

- `## Topic: {label}` — when a topic becomes clear, or shifts
- `## Context: {source label}` — when source material is introduced
  (followed by the material, verbatim or lightly edited)
- `## Ingested: {title}` — when something is ingested mid-session
  (followed by the ingestor summary and links to bib/wiki)
- `## Resumed — {date}` — when the session is resumed after a break

## Rules

1. **Context is written when it appears.** A session may start with no context at all — the user may be thinking out loud, or opening a task. When source material is introduced mid-session (pasted text, ingested article, quoted post), write a `## Context:` section before continuing. Self-contained transcripts matter for resumption, but only record context that actually exists — never pre-fill.
2. **User's words are sacred.** Record close to verbatim. Fix spelling, punctuation, remove filler words ("uh", "like", "well"). Do NOT rephrase, summarize, or interpret. The user owns the transcript.
3. **Agent's words are compressed.** The agent's contributions are reduced to a brief italic summary — just enough to follow the flow. The transcript is about the user's thinking and the work produced, not the agent's exact responses or tool calls.
4. **Update after every exchange.** Do not wait until the end of the session. Write to the transcript continuously so nothing is lost if the session ends unexpectedly or context is compressed.
5. **One session per Claude Code session.** Do not create multiple transcripts for the same continuous session. Reuse the same `{uuid}/index.md` until the user explicitly starts a new one or resumes a different one.

## Flow

### Entry point

At the start of every Claude Code session, or when the user says "transcribe this", "start a session", or similar:

- If no session is already active → **NEW** session
- If the user provides a UUID → **RESUME** that session
- If a session is already active → just keep appending

### New session

1. Generate UUID v7:
   ```bash
   thinkbox/scripts/uuid7.sh
   ```
2. Create the directory and file:
   ```bash
   mkdir -p sessions/{uuid}
   ```
3. Write `sessions/{uuid}/index.md` with just a header:
   ```markdown
   # Session — {date}

   ```
4. Remember the session ID for the rest of the Claude Code session — every subsequent exchange appends to this same file.
5. If the user already provided an opening message, record it as the first `**User:**` entry.

### Resumed session

When the user references an existing session ID (UUID), or says "resume session {uuid}":

1. Read `sessions/{uuid}/index.md` — the full transcript, to restore context.
2. Append a continuation marker:
   ```markdown

   ## Resumed — {date}

   ```
3. Summarize the previous state in 1–2 sentences before responding, so the user can confirm the right thread was picked up.

### During the session

After every user message:

1. Append the user's words verbatim (lightly cleaned) under `**User:**`
2. Do the work (respond, run tools, delegate to other skills)
3. Append a compressed italic summary of what the agent did under `**LLM:**` — not the full response, just a few words describing the direction/outcome

Never skip an exchange. Never batch multiple exchanges into one update.

### Topic shifts and context

- **Topic shift.** If the user changes topic mid-session, insert a `## Topic: {new topic}` header before the next exchange.
- **Source material appears.** If the user pastes source material (article text, quoted post, code snippet under discussion), write it into a `## Context: {label}` section before continuing.
- **Source fully processed.** If a source is fully processed during the session (downloaded, summarized, linked into the knowledge base), append a `## Ingested: {title}` section with a short summary and the relative paths of any files created.

## What this skill does NOT do

- Does not interpret, analyze, or judge the content — it just records
- Does not propose cards, blog posts, or next actions
- Does not require the session to have a topic or direction — a session may start empty and find its shape as it goes
- Does not call any other skill. Transcribator runs independently. Other work (dialogue methods, ingestion, publishing, card creation) is started by the user as separate skills and simply appears in the transcript as LLM-summary lines or dedicated `## Context:` / `## Ingested:` sections.
