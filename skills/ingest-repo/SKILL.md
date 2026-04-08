---
name: ingest-repo
description: >
  Deep analysis of a GitHub repository. Clones the repo, navigates code
  interactively across two axes (technical architecture + business context),
  creates a bib entry and wiki pages, updates navigation. Use this skill when
  the user says "/ingest-repo" or asks to analyze, study, or add a GitHub
  repository to the knowledge base.
---

# Ingest-repo: deep analysis of a GitHub repository

Version: **0.1.0**

## Trigger

`/ingest-repo <github-url>` — URL matching `https://github.com/{owner}/{repo}`

## Flow

```
1. Generate UUID v7
2. Clone repo (shallow) into artifacts/{uuid}/repo/
3. Generate tree.txt + scaffold original.txt (README, tree, commit SHA)
4. Extract links.csv from README/docs
5. Interactive analysis — LLM navigates code:
   a. ORIENT:  tree + README → language, structure, purpose, audience
   b. IDENTIFY: manifests + config → deps, build, ecosystem positioning
   c. MAP:     entry points + interfaces → module boundaries, API surface, features
   d. DIVE:    10-30 key files → patterns, algorithms, interesting approaches
   e. Append each key file read to original.txt
6. Cross-reference: Qdrant search for connections/contradictions
7. Present findings to user, propose bib + wiki pages
8. User approves/adjusts
9. Archive: tar.gz repo (exclude .git), delete repo/ and tree.txt
10. Create bib + wiki files, update MOCs
11. Pre-commit check: verify original.txt AND original.tar.gz exist
12. Commit: "ingest: {repo name}"
```

## Rules

- Always read from the original clone, not just README. Extract knowledge from actual source code.
- Create a bib entry only for citable sources.
- Never create xettel cards during ingest. Those are the user's thoughts, not the agent's.
- Check existing wiki pages for contradictions and connections with the new source. Use Qdrant semantic search with `-t` filter to target specific content types:
  ```
  thinkbox/scripts/search.sh '<key concept>' -t wiki   # existing wiki coverage
  thinkbox/scripts/search.sh '<key concept>' -t x      # user's existing thoughts
  thinkbox/scripts/search.sh '<key concept>' -t bib    # related sources already ingested
  ```
- If the source contradicts an existing xettel card, the wiki page must note the disagreement with links to both.

## Artifacts

Artifacts preserve the original source material as faithfully as possible. Same three-file structure as `/ingest`:

```
artifacts/{uuid}/
├── original.txt       ← structured manifest (tree + README + key files appended during analysis)
├── links.csv          ← external hyperlinks from README/docs
└── original.tar.gz    ← archived repo (excluding .git)
```

### Download procedure

Single chained command:
```bash
cd artifacts/{uuid} \
  && nix-shell -p git --run "git clone --depth 1 'https://github.com/{owner}/{repo}.git' repo" \
  && find repo -type f \
       \( -path '*/.git/*' -o -path '*/node_modules/*' -o -path '*/dist/*' \
       -o -path '*/build/*' -o -path '*/vendor/*' -o -path '*/__pycache__/*' \
       -o -path '*/.venv/*' -o -path '*/target/*' \) -prune \
       -o -type f -print | sort > tree.txt \
  && { echo "=== REPO: {owner}/{repo} ==="; \
       echo "URL: https://github.com/{owner}/{repo}"; \
       echo "Cloned: $(date -Iseconds)"; \
       echo "Commit: $(cd repo && git rev-parse HEAD)"; \
       echo ""; \
       echo "=== FILE TREE ==="; \
       cat tree.txt; \
       echo ""; \
       echo "=== README ==="; \
       cat repo/README.md 2>/dev/null || cat repo/readme.md 2>/dev/null || echo "(no README)"; \
     } > original.txt
```

### Links extraction

Separate chained command after clone:
```bash
cd artifacts/{uuid} \
  && nix-shell -p python3 --run "python3 -c \"
import os, re, csv
links = []
for root, dirs, files in os.walk('repo'):
    dirs[:] = [d for d in dirs if d not in ('.git','node_modules','dist','build','vendor','__pycache__','.venv','target')]
    for f in files:
        if f.lower().startswith('readme'):
            with open(os.path.join(root,f)) as fh:
                for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', fh.read()):
                    if m.group(2).startswith(('http://','https://')):
                        links.append((m.group(1), m.group(2)))
with open('links.csv','w',newline='') as f:
    csv.writer(f).writerows(links)
\""
```

### Post-analysis cleanup

After analysis is complete and user has approved:
```bash
cd artifacts/{uuid} \
  && tar czf original.tar.gz --exclude='.git' repo \
  && rm -rf repo tree.txt
```

## Analysis strategy — two axes

### Technical axis (how it works inside)

- **Architecture:** module organization, key abstractions, dependency flow
- **Patterns:** design patterns, interesting approaches to common problems
- **Core algorithms:** the distinctive "interesting part"
- **Extensibility:** plugin systems, middleware, hooks, API design

### Business axis (why it exists)

- **Problem:** what specific problem does this solve?
- **Audience:** who is this for? What persona/role?
- **Use cases:** concrete scenarios where you'd reach for this
- **Positioning:** what alternatives exist? How is this different?
- **Maturity:** production-ready? Experimental? Active development?

### Exploration funnel

| Step | What to read | Technical signal | Business signal |
|---|---|---|---|
| ORIENT | tree.txt, README | Language, structure, repo size | Problem statement, audience, stated use cases |
| IDENTIFY | manifests, config, ARCHITECTURE.md, docs/ | Dependencies, build pipeline, monorepo | Ecosystem positioning, what it replaces |
| MAP | Entry points, interfaces, type defs | Module boundaries, API contracts | Feature surface, what users can do |
| DIVE | 10-30 selected files | Patterns, algorithms, extensibility | Domain model, business logic |

### File reading budget

- Small repo (<50 files): most files
- Medium repo (50-500): 10-30 files
- Large repo (500+): 5-15 files

Each key file read during DIVE gets appended to `original.txt` with a `--- {path} ---` separator.

## Bib entry format

```yaml
---
bib_id: "{uuid}"
bib_type: repo
bib_title: "{repo name}"
bib_author: "{owner or organization}"
bib_url: https://github.com/{owner}/{repo}
bib_added: {ISO timestamp}
software_version: "0.1.0"
---

LLM-generated summary covering both axes:
what it does, who it's for, how it works inside.
```

## Wiki pages created during ingest

Every repo ingest MUST produce:

1. **Source summary** (`wiki_type: source`) — the main deliverable. Covers both axes:
   - Problem and audience
   - Architecture overview
   - Notable patterns and approaches
   - Key dependencies and what they reveal
   - Connections to existing knowledge

2. **Concept pages** (`wiki_type: concept`) for generalizable ideas — technical or business. Test: "Would someone who never uses this repo still find this useful?"

3. **Entity page** (`wiki_type: entity`) — only for significant/notable projects.

4. **MOC updates** linking the new pages.

Typical yield: 1 source summary + 1-4 concept pages + 0-1 entity page.

All wiki pages follow the format in `skills/wiki/SKILL.md`.
