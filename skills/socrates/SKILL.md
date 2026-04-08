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

1. **The user's own knowledge base** — existing xettel cards, wiki pages, bib entries. The agent acts as an advocate of the user's past self against the user's present self.
2. **General knowledge** — known counter-arguments, positions of established thinkers, standard objections. The agent presents these not as its own position but as "here's what a critic would say."

When the user disagrees with a counter-argument, they must argue why. This produces the most valuable output: thesis + counter-argument + response. All three belong in xettel.

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

Every Socrates session is recorded in a transcript file.

### Storage

`sessions/{uuid7}/index.md` — one directory per session, UUID v7 as identifier.

### Format

```markdown
# Socratic session — {date}

Topic: {brief topic description}

## Dialogue

**User:** {user's words, close to verbatim — fix spelling, punctuation,
remove filler words, but preserve meaning and phrasing exactly}

**LLM:** *{agent's contribution compressed to a few words —
just enough to understand the direction of the dialogue}*

**User:** {next user message}

...
```

### Rules

1. **User's words are sacred.** Record close to verbatim. Fix spelling, punctuation, remove filler words ("uh", "like", "well"). Do NOT rephrase, summarize, or interpret. The user owns the transcript.
2. **Agent's words are compressed.** The agent's contributions are reduced to a brief italic summary — just enough to follow the flow. The transcript is about the user's thinking, not the agent's questions.
3. **Update after every exchange.** Do not wait until the end of the session. Write to the transcript continuously so nothing is lost if the session ends unexpectedly or context is compressed.

## Flow

```
1. User provides context (or context is already in chat)
2. User says "/socrates" or equivalent
3. Agent:
   a. Generates UUID v7
   b. Creates sessions/{uuid}/index.md with header
   c. Searches knowledge base for related content
      (existing xettel cards, wiki pages, bib entries)
   d. Reads related content to understand user's existing position
4. Agent asks the first simple question
5. Dialogue proceeds with escalation
   - Agent records transcript continuously
   - Agent searches knowledge base as needed during dialogue
6. Cards may emerge at any point during the dialogue:
   - When the user articulates a transferable insight, agent flags it
   - Some cards can be published immediately
   - Others are held back until the root card is fully formed
   - Card proposals do not interrupt the dialogue flow
7. Session ends when it ends — user stops, context fills up,
   day is over. There is no "conclusion" phase.
   The transcript persists; a future session can continue.
8. Cards proposed during the session go through standard /xettel flow
   (formulate → approve → publish → create file)
9. Optionally at any point: agent drafts a blog post from the transcript
```

## Output

### Xettel cards

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
- [ ] Checked connections to existing xettel (for placing: root vs reply_to)
- [ ] Bridges proposed (if applicable — see bridge rule below)
```

After user approval, save the proposal with its checklist to the transcript before publishing.

**Bridge rule.** Do not propose bridges per-card. When publishing a cluster of cards from one session, propose bridges after the entire cluster is published. This avoids fragmenting the workflow and lets the agent see the full picture before drawing connections.

Cards from a Socrates session use `xettel_context` to record their origin:
```yaml
xettel_context: "socrates {date}, {topic}"
```

Thread structure should reflect the reasoning chain: premise → development → conclusion. Each card is self-contained, but the thread allows reconstructing the full argument.

Disagreements produce up to three cards:
- The user's thesis (user's own words, permanent card)
- The counter-argument (bridge card with ref to wiki/bib page that describes the opposing position)
- The user's response to the counter-argument (user's own words, permanent card)

### Blog post (optional)

A blog post based on the session — not a raw transcript, but a coherent text in the user's voice covering the reasoning process. Only what the user is ready to publish. Written collaboratively through the standard `/blog` flow.

## What this skill does NOT do

- Does not extract knowledge from sources — that's `/ingest`
- Does not formulate cards — that's `/xettel` (Socrates proposes, xettel flow handles the rest)
- Does not publish — that's `/publish`
- Does not create cards autonomously — every card passes through the user
