---
name: ingest
description: >
  Process an external source into the knowledge base. Downloads the source,
  saves it as an artifact, creates a bib entry and wiki pages, updates
  navigation. Use this skill when the user says "/ingest" or asks to
  process, summarize, or add an article, paper, book, video, or any
  external source to the system.
---

# Ingest: process an external source

Version: **0.1.0**

## Trigger

`/ingest <url>` or `/ingest <path to local file>`

## Flow

```
1. Generate UUID v7
2. Download the source — ORIGINAL, not a summary
   a. wget -p -k into artifacts/{uuid}/raw/
   b. pandoc the HTML to artifacts/{uuid}/index.md
   c. tar.gz raw/ into artifacts/{uuid}/original.tar.gz, delete raw/
   Principle: better to save too much than lose something.
   All commands in a single chained shell call (cwd resets between calls).
3. Read the full index.md, extract key ideas
4. Present takeaways to user, propose:
   - bib/{uuid}.md
   - wiki page(s)
   - MOC updates
5. User approves / adjusts
6. Create files, update index/MOCs
7. **Pre-commit check:** verify artifacts/{uuid}/index.md AND original.tar.gz exist on disk
8. Commit: "ingest: {source title}" (content + artifacts repos)
```

## Rules

- Always read the ORIGINAL artifact, not just metadata. Extract knowledge from the full source.
- Create a bib entry only for citable sources. Voice memos, screenshots, raw dumps — artifacts without bib records.
- Never create xettel cards during ingest. Those are the user's thoughts, not the agent's.
- Check existing wiki pages for contradictions and connections with the new source. Note them.
- If the source contradicts an existing xettel card, the wiki page must note the disagreement with links to both.

## Bib entry format

```yaml
---
bib_id: "{uuid}"
bib_type: repo | article | book | paper | podcast | video | voice
bib_title: "Source Title"
bib_author: "Author Name"
bib_url: https://example.com/source
bib_added: {ISO timestamp}
software_version: "0.1.0"
---

LLM-generated summary of the source. Key takeaways, what's new,
what connects to existing knowledge.
```

## Wiki pages created during ingest

Every ingest MUST produce:

1. **One source summary page** (wiki_type: source) — overview of the article, key contributions, connections to existing knowledge.
2. **One concept page per distinct idea** introduced or developed in the source. Ask: "would this concept make sense as a standalone page that other sources could also reference?" Typical: 3–7 concept pages per substantial article.
3. **MOC updates** linking the new pages.
4. Optionally: entity pages for people/tools/projects, comparisons, syntheses.

Concept pages cite the bib entry as their authority. Xettel cards appear only as cross-references ("the user independently noted X") or contradictions ("the user claims X, but the source argues Y"). Wiki must be able to challenge the user's thinking, not just confirm it.

All wiki pages follow the format in `skills/wiki/SKILL.md`.

## Artifacts

Artifacts preserve the original source material as faithfully as possible.

```
artifacts/{uuid}/
├── index.md           ← markdown conversion (full content, not a summary)
└── original.tar.gz    ← archived wget download (HTML + all assets)
```

### Download procedure

```bash
# All in one chained command (cwd resets between Bash calls!)
cd artifacts/{uuid} \
  && nix-shell -p wget --run "wget -p -k -nH --no-parent '{url}' -P raw" \
  && nix-shell -p pandoc --run "pandoc raw/.../index.html -f html -t gfm --wrap=none -o index.md" \
  && tar czf original.tar.gz raw \
  && rm -rf raw
```

### Rules

- `original.tar.gz` is the full wget download — never processed by LLM
- `index.md` is a faithful pandoc conversion — all text, headings, lists, code blocks preserved verbatim. NO summarization, NO extraction, NO LLM rewriting.
- Never published — originals may be copyrighted
- Only LLM-generated summaries (in bib/) are public
- NixOS: use `nix-shell -p wget` and `nix-shell -p pandoc`
- Never create temp dirs outside the artifact directory
