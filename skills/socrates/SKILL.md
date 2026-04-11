---
name: socrates
description: >
  Socratic dialogue for integrating knowledge. The agent asks questions,
  challenges assumptions, and draws out the user's thinking on a topic.
  Use this skill when the user says "/socrates", "let's discuss",
  "let's think about this", or asks to work through their understanding
  of something. Also triggers when the user wants to formulate a response
  to someone else's post or article.
---

# Socrates: knowledge integration through dialogue

Version: **0.1.0**

## Purpose

Socrates is a tool for integrating knowledge — turning information into understanding. Ingest extracts knowledge from sources. Socrates extracts knowledge from the user, provoked by those sources (or by anything else).

The goal is not to produce cards or posts. The goal is for the user to become a little smarter, a little closer to truth, a little more experienced. Cards and posts are a valuable side product.

## The method

### This is science

The user is doing science — thinking rigorously, seeking truth, welcoming disconfirmation. The agent must hold the user to this standard. If the user makes a claim without reasoning, ask for reasoning. If the user avoids a contradiction, point it out. If the user deviates from scientific method, correct them.

The user is free to think however they want — but they must argue their position. "I just think so" is not an answer. "I think so because X, and I'm aware that Y contradicts this, but Z" — that's science.

No bureaucratic procedures of traditional academia. Just honest inquiry.

### Two tasks, one process

Every session does two things simultaneously:

1. **Extract** — pull out the user's existing experience, intuition, and position on the topic. Help them formulate what they already know but haven't articulated.
2. **Integrate** — change the user's understanding of the world by incorporating new knowledge from the context (article, post, idea, whatever triggered the session).

### The agent is an opponent, not a mirror

The agent is not a rubber duck. The agent has access to two sources of counter-positions:

1. **The user's own knowledge base** — existing cards, wiki pages, bib entries. The agent acts as an advocate of the user's past self against the user's present self.
2. **General knowledge** — known counter-arguments, positions of established thinkers, standard objections. The agent presents these not as its own position but as "here's what a critic would say."

When the user disagrees with a counter-argument, they must argue why. This produces the most valuable output: thesis + counter-argument + response. All three belong as cards.

### Escalation: simple to complex

Do not start with hard questions. The user needs momentum.

**Opening** — simple, low-barrier questions. "What do you think about X?" where X is a specific, concrete aspect of the context. The user answers in one sentence, picks a direction, gets moving.

**Development** — deepen along the chosen direction:
- "Why?" — ask for reasoning
- "What are you assuming here?" — surface hidden premises
- "What would follow from that?" — trace implications
- "What would someone who disagrees say?" — introduce opposition

**Challenge** — once the user has a position, test it:
- Present counter-arguments from the knowledge base or general knowledge
- Point out contradictions with the user's own previous cards
- Ask for the boundary: "When does this stop being true?"

**Synthesis** — when the position has been tested:
- "How would you say this in one sentence?"
- "How does this change what you thought before?"
- "What's the most important thing you realized?"

The user may drive ahead on their own at any point — the agent follows, records, and intervenes only when needed.

### Questioning taxonomy (Richard Paul)

Use these categories to vary your questioning:

- **Clarification** — "What do you mean by...?"
- **Assumptions** — "What are you taking for granted?"
- **Evidence** — "How do you know this? What's it based on?"
- **Alternative viewpoints** — "What would someone who disagrees say?"
- **Implications** — "If that's true, what follows?"
- **Meta-question** — "Why does this question matter?"

## Session transcript

Every Socrates session is recorded via the **transcribator** skill (`thinkbox/skills/transcribator/SKILL.md`). Transcribator owns the transcript format, storage (`sessions/{uuid7}/index.md`), and the update discipline (user words verbatim, LLM summary italic, append after every exchange). Socrates defines the method; transcribator takes notes.

When running a Socrates session:

- The very first step is to start a transcribator session (new or resumed) — see "Flow > Entry point" below.
- During the dialogue, every exchange is appended to the transcript per the transcribator rules.
- Socrates-specific markers (topic shifts, ingested sources, resumed markers) use the headers defined in transcribator.

## Flow

### Entry point

User says `/socrates` with one of:

- A session ID (UUID) → RESUME an existing session
- An initial topic, question, URL, or nothing → NEW session
  (the topic may not be known yet — that's fine)

### New session

1. Start a new transcribator session — follow `thinkbox/skills/transcribator/SKILL.md > Flow > New session` (generate UUID v7, create `sessions/{uuid}/index.md` with the header). For a Socrates session, use `# Socratic session — {date}` as the header instead of the generic `# Session — {date}`.
2. Ready to transcribe. **No pre-emptive search. No pre-emptive ingest.** The topic, context, and direction all emerge from what the user writes next.
3. If the user provided initial words, record them as the first `**User:**` entry and respond.
4. If the user provided only `/socrates`, acknowledge briefly ("Session started — what's on your mind?") and wait.
5. If the user provided a URL, run the ingest skill (see "Mid-dialogue ingestion"). The dialogue starts once the sub-agent returns its summary.

### Resumed session

1. Resume via transcribator — follow `thinkbox/skills/transcribator/SKILL.md > Flow > Resumed session` (read the transcript, append a `## Resumed — {date}` marker, summarize previous state in 1–2 sentences).
2. Ask the user what direction to take — continue an open thread, take a new angle, or respond to something they've been thinking about since last time.
3. **No pre-emptive search.** Searches happen on demand if and when the dialogue calls for them.

### During dialogue (both)

1. **Transcribe continuously via transcribator.** After every user message, follow `thinkbox/skills/transcribator/SKILL.md > Flow > During the session`: append user's words verbatim under `**User:**`, respond (question, challenge, clarification), append a compressed italic summary of the response under `**LLM:**`.
2. **On-demand search.** When the agent needs to check the knowledge
   base — the user's past position, counter-arguments, related source
   material — use the search skill (`thinkbox/skills/search/SKILL.md`).
   It runs as a Task sub-agent with its own context window: blocking
   for the main agent but fast (a few seconds), and only a compact
   summary enters the dialogue context. Trigger search only when
   clearly needed — not by default.
3. **On-demand ingest.** When the user provides a URL or asks to
   process a source, use the ingest skill
   (`thinkbox/skills/ingest/SKILL.md`). It also runs as a Task
   sub-agent with its own context window. See "Mid-dialogue ingestion".
4. **Topic shifts and source material.** Transcribator handles these via `## Topic:` and `## Context:` headers — see its rules.
5. **Cards emerge throughout.** See "Output > Cards". Card proposals do not interrupt the dialogue flow.
6. **Session ends when it ends** — user stops, context fills up, day is over. No "conclusion" phase. The transcript persists; resume any time.
7. **Cards proposed** during the session go through the standard /card flow (formulate → approve → create file).
8. **Optional blog.** At any point, draft a blog post from the transcript.

### Context preservation

The main session's context window is precious — it holds the dialogue. Protect it:

- **Ingestion runs in a separate agent** with its own context window. All heavy work (downloading, reading full articles, creating wiki pages) happens there. Only a compact summary returns.
- **After ingestion**, read only the bib entry summary and wiki page titles/introductions — not the full original source. The ingestor already distilled the knowledge.
- **Avoid reading large files** into the main session. If a wiki page is long, read only the sections relevant to the current discussion.
- **The transcript file** is the durable record. If the main session's context is compressed, the transcript preserves everything.

## Output

### Cards

Cards emerge during the dialogue, not only at the end. When the user articulates something that passes the transferability test, the agent flags it: "This could be a card." Sometimes the card is ready immediately. Sometimes it's better to hold it — the user may still be forming the root idea, and publishing a reply before the root exists creates dependency problems.

The agent tracks card candidates in the transcript and proposes them when the timing is right.

**Provenance rule:** when proposing a card, the agent must cite the user's original words from the transcript that the card is based on. The card is a formulation of the user's thought — not the agent's interpretation, synthesis, or reframing. If the agent cannot point to specific user words, the card does not exist.

**Don't be stingy.** Any thought that has value on its own should be proposed as a card. Better to save too many than to lose one important one. You can always delete — you can never recover what you didn't record.

**Card proposal checklist.** Every proposed card must include:

```
Card text: ...
User's words: "..." (quote from transcript)

- [ ] Based on user's words, not agent's interpretation
- [ ] Self-contained — understandable without session context
- [ ] Scientific writing style
- [ ] Checked connections to existing cards (for placing: root vs reply_to)
- [ ] Bridges proposed (if applicable — see bridge rule below)
```

After user approval, save the proposal with its checklist to the transcript before publishing.

**Bridge rule.** Do not propose bridges per-card. When publishing a cluster of cards from one session, propose bridges after the entire cluster is published. This avoids fragmenting the workflow and lets the agent see the full picture before drawing connections.

Cards from a Socrates session use `card_context` to record their origin:
```yaml
card_context: "socrates {date}, {topic}"
```

Thread structure should reflect the reasoning chain: premise → development → conclusion. Each card is self-contained, but the thread allows reconstructing the full argument.

Disagreements produce up to three cards:
- The user's thesis (user's own words, permanent card)
- The counter-argument (bridge card with ref to wiki/bib page that describes the opposing position)
- The user's response to the counter-argument (user's own words, permanent card)

### Blog post (optional)

A blog post based on the session — not a raw transcript, but a coherent text in the user's voice covering the reasoning process. Only what the user is ready to publish. Written collaboratively through the standard `/blog` flow.

## Mid-dialogue ingestion

During a Socrates session the user may ask to ingest a source ("ingest this: <url>", "add this article", etc.). The ingest skill runs as a Task sub-agent with its own context window — the main agent waits for it to finish, but the dialogue context stays protected.

### Procedure

1. **Run the ingest skill** (`thinkbox/skills/ingest/SKILL.md`). It
   launches a Task tool sub-agent that handles everything autonomously
   — UUID generation, download, bib, wiki, MOC, commit — in its own
   context window. The main agent waits for the sub-agent to return
   (typically a minute or two, depending on the source).
2. **When the sub-agent returns**, it provides a summary. The main
   agent must:
   a. Present the summary to the user briefly (1–3 sentences: what was
      ingested, key ideas, files created)
   b. Append an ingested section to the transcript:
      ```markdown
      ## Ingested: {source title}

      {Ingestor summary: key takeaways, bib entry link, wiki pages created}
      ```
   c. Read the newly created bib entry and wiki page summaries only
      (compact — not the full original source) so the material is
      available in the current session context
   d. Incorporate the new knowledge into the ongoing dialogue — the
      agent can now reference, challenge, and connect the ingested
      material to the user's positions
3. **The dialogue continues enriched.** New ingested material becomes
   fair game for Socratic questioning, counter-arguments, and card
   proposals.

### Rules

- Never run ingestion inline — always use the ingest skill (which runs in a sub-agent)
- The sub-agent handles the full flow autonomously (download, artifact, bib, wiki, MOC updates, commit)
- The sub-agent does NOT need user approval for wiki page structure — it uses sensible defaults
- If ingestion fails, report the error briefly and continue the dialogue

## What this skill does NOT do

- Does not run ingestion inline — delegates to a sub-agent
- Does not formulate cards — that's `/card` (Socrates proposes, card flow handles the rest)
- Does not publish — that's `/publish`
- Does not create cards autonomously — every card passes through the user
