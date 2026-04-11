---
name: publish
description: >
  Publish a card to Bluesky (and any other configured platforms). Uses
  thinkbox/scripts/publish.sh — a real script that really authenticates
  and really posts. Handles root cards, replies at any depth, bridge
  cards (quote posts), literature cards with link-preview embeds, and
  auto-commits the updated card file back to the content/ repo.
  Use this skill when the user says "publish", "post to bluesky", or
  asks to publish a card.
---

# Publish

Version: **0.1.0**

One card, one invocation, one post per target platform.

The script reads `content/cards/<uuid>.md`, resolves its link graph
(`card_reply_to`, `card_ref`, `card_bib`) against sibling cards'
`card_published[]` entries, posts the body via a per-platform wrapper,
appends a `card_published[]` entry back to the card file, and
(by default) commits that change to the `content/` git repo.

## Pipeline

1. **Load** the card file (round-trip YAML so comments and key order
   survive writeback).
2. **Validate** the body: `len(body) ≤ 300`. Cards never contain URLs —
   external refs live in `card_bib` and become a link preview embed.
3. **Resolve the link graph**:
   - `card_reply_to` → parent's `card_published[]` entry for the target
     platform. Walks the chain up to find the thread root, so deep
     threads (C → B → A) work too. If any ancestor isn't yet on the
     target platform, the script refuses and tells you to publish it
     first.
   - `card_ref` → referenced card's `card_published[]` entry (becomes
     a quote post on Bluesky).
   - `card_bib` → bib entry's `bib_url` + `bib_title` + first paragraph
     of the bib body (becomes an external link preview card).
4. **Fan out** to every platform in the orchestrator's `PLATFORMS`
   list (currently: `bluesky`). Each target already present in
   `card_published[]` is skipped per-platform (double-post refusal).
5. **Dispatch** to `publishers/<platform>.sh`. Parses the JSON
   `{id, cid}` line it returns on stdout.
6. **Write back**: append `{platform, id, cid, date}` to
   `card_published[]` via round-trip YAML. The body is preserved
   byte-for-byte by splitting the file on the YAML fence.
7. **Auto-commit** (default): stage the card in the `content/` git
   repo and commit with message
   `publish: <platforms>: <body preview>`. `--no-commit` opts out.

The whole resolve step happens **before** any network call. If a
parent is missing or a ref is unpublished, the script fails loudly
and nothing gets posted.

## What works

- **Root cards** — plain post, no parents, no refs.
- **Replies at any depth** — parent ref + root ref if needed. The
  resolver walks `card_reply_to` to the topmost ancestor.
- **Bridge cards** — `card_ref` becomes a quote post (Bluesky record
  embed).
- **Literature cards with link previews** — `card_bib` drives an
  external embed (`uri` = `bib_url`, `title` = `bib_title`,
  `description` = first paragraph of bib body).
- **Reply + quote combined** — a reply card with `card_ref` posts as
  a reply to its parent AND quotes the referenced card.
- **Clickable URLs in text** — `publishers/bluesky.py` builds rich-text
  facets with byte offsets (defensive: card bodies shouldn't carry
  URLs, but legacy cards and raw hello-world text still render them).
- **Dry-run** — prints the resolved plan, never calls a publisher,
  never writes to the card file, never touches git.
- **Double-post refusal** — if a card already has a `card_published`
  entry for a platform, that platform is silently skipped.
- **Auto-commit** — successful publish stages and commits the card
  file in the `content/` repo. Opt out with `--no-commit`.

## What is not supported

- **Batch mode.** No "publish every unpublished card in this MOC" or
  topological walk of a thread. One card, one invocation.
- **Quote + external embed in a single post.** AT Protocol requires
  `recordWithMedia` to combine them; `publishers/bluesky.py` refuses
  the combo. Bridge cards win: if `card_ref` is set, the bib link
  preview is skipped.
- **Twitter / other adapters.** Not implemented; the Twitter account
  is suspended and the architecture has moved on. Legacy Twitter
  entries in `card_published[]` are read (for double-post refusal
  and resolver lookups) but never written.

## Queue — seeing what's publishable

`thinkbox/scripts/queue.sh <platform>` is a read-only report: one
line per card, indented to show `card_reply_to` trees, with `→ <uuid>`
for `card_ref` and `[ready]` / `[blocked: <reason>]` status.

```sh
./thinkbox/scripts/queue.sh bluesky
```

Use this to decide which card to publish next. A card is `[ready]`
when every dependency it needs (parent chain, thread root, ref target)
is already on the target platform. Anything else is `[blocked]` with
an explanation.

## Invocation

Run from the repository root:

```sh
# See what's publishable
./thinkbox/scripts/queue.sh bluesky

# Dry-run a card (no network, no file write, no commit)
./thinkbox/scripts/publish.sh --card <uuid> --dry-run

# Publish the card (posts, writes back, auto-commits)
./thinkbox/scripts/publish.sh --card <uuid>

# Publish but skip the git commit (rare — e.g. inspecting the diff
# before committing manually together with MOC/wiki updates)
./thinkbox/scripts/publish.sh --card <uuid> --no-commit
```

| Flag | Meaning |
|---|---|
| `--card <uuid>` | Card at `content/cards/<uuid>.md` to publish. Required. |
| `--dry-run` | Resolve the plan, print it, exit 0. No network, no writes, no commit. |
| `--no-commit` | Publish and write back the card file, but do not auto-commit. |

## Credentials

The wrapper sources `.env` at the repository root. Required for
Bluesky:

```
BLUESKY_HANDLE=<your.handle.bsky.social>
BLUESKY_APP_PASSWORD=<app password from https://bsky.app/settings/app-passwords>
```

**Never use your main account password.** Create a dedicated app
password. `.env` is gitignored.

If either variable is missing, `publishers/bluesky.py` exits with a
clear error before touching the network.

## File layout

- `thinkbox/scripts/publish.sh` — bash wrapper. Runs `publish.py`
  under `nix-shell -p "python3.withPackages(ps: [ps.ruamel-yaml])"`.
- `thinkbox/scripts/publish.py` — card orchestrator. Parses args,
  reads/writes card files via round-trip YAML, resolves the link
  graph, dispatches to per-platform wrappers, appends
  `card_published[]` entries, auto-commits.
- `thinkbox/scripts/publishers/bluesky.sh` — bash wrapper for the
  Bluesky adapter. Sources `.env`, runs `bluesky.py` under its own
  `nix-shell` with the `atproto` package.
- `thinkbox/scripts/publishers/bluesky.py` — Bluesky adapter. Takes
  `--text`, optional `--reply-to-uri/--reply-to-cid`,
  `--root-uri/--root-cid`, `--quote-uri/--quote-cid`,
  `--embed-uri/--embed-title/--embed-description`. Writes `{id, cid}`
  as a single JSON line on stdout.
- `thinkbox/scripts/queue.sh` / `queue.py` — read-only queue report.

Per-platform scripts are standalone: they accept `--text` + link args
on the CLI and print `{id, cid}` as JSON. That means each one can be
tested in isolation (hello-world post via `bluesky.sh --text "…"`),
and the orchestrator knows nothing about AT Protocol internals.

## Character counting

`len(body) ≤ 300`. Plain and flat.

Cards must not contain URLs in the body. External references flow
through `card_bib` and become a link preview embed on publish. The
URL facet detector in `publishers/bluesky.py` exists only as a
defensive fallback for legacy cards and raw text posts.

A card over the budget errors out before any network call:

```
error: card over limit (body=312, limit=300)
```

## Card frontmatter write-back

On a successful publish, `publish.py` appends one entry to the card's
`card_published[]`:

```yaml
card_published:
  - platform: bluesky
    id: at://did:plc:.../app.bsky.feed.post/...
    cid: bafyrei...
    date: 2026-04-11T12:34:56.789Z
```

- `id` — the post's AT URI.
- `cid` — Bluesky-specific. AT Protocol needs both `uri` and `cid`
  to build strong references (for replies and quote posts), so we
  persist both.
- `date` — ISO 8601 UTC millisecond precision, the moment of
  publishing (not `card_created`).

Legacy Twitter entries in the archive carry `{platform, id, date}`
only (no `cid`). The resolver reads both shapes; the writer only
produces the new shape.

`ruamel.yaml`'s round-trip mode preserves comments, key order, and
existing quoting. The body of the card is preserved byte-for-byte by
splitting the file on the YAML fence rather than re-serializing
through a parser.

## Auto-commit

By default, a successful publish runs:

```
git -C content add cards/<uuid>.md
git -C content commit -m "publish: <platforms>: <body preview>"
```

The body preview is the card body with newlines collapsed,
truncated to 72 chars with an ellipsis. Example messages:

```
publish: bluesky: A desired state system wraps a mutable, imperative interface with…
publish: bluesky: Continuous Assembly is CI/CD for the physical world.
```

Failure modes:

- If `content/` is not a git working tree, auto-commit is skipped
  with a warning. The card file is still updated.
- If `git add` / `git commit` fails for any other reason (pre-commit
  hook, nothing staged, detached HEAD), the warning is printed and
  the script exits successfully — the card file is already updated
  on disk, commit it manually.

`--no-commit` skips the whole block. Use it when you want to bundle
the card file change with MOC/wiki updates or bridge cards in a
single commit.

## Workflow

1. **See what's publishable.** `./thinkbox/scripts/queue.sh bluesky`.
2. **Pick a `[ready]` card.** Normally the oldest thread root first,
   then its replies in order. The queue report shows the tree.
3. **Dry-run.** `./thinkbox/scripts/publish.sh --card <uuid> --dry-run`.
   Confirm body, parent/root/quote refs, embed target, character count.
4. **Publish.** `./thinkbox/scripts/publish.sh --card <uuid>`. The
   script posts, writes back the `card_published` entry, and commits
   the card file.
5. **Manual verification.** Open https://bsky.app, confirm the post
   rendered as intended (thread placement, quote post, link preview).
6. **Graph integration (agent).** Update MOCs and wiki pages if the
   card opens a new angle on an existing topic. Suggest bridge cards
   if the published card lands near another idea — never create
   bridges unilaterally.
7. **Follow-up commit.** The publish commit is just the card file.
   MOC/wiki/bridge updates land in a separate commit with an
   appropriate prefix (`wiki:` / `card:`).

## Failure modes

| Condition | Exit | Message |
|---|---|---|
| Missing `BLUESKY_HANDLE` / `BLUESKY_APP_PASSWORD` | non-zero | `error: missing environment variable ...` |
| Card file not found | non-zero | `error: card not found: ...` |
| Card body over 300 chars | non-zero | `error: card over limit (body=X, limit=300)` |
| Parent card missing from disk | non-zero | `error: card_reply_to=<uuid> — parent card file missing` |
| Parent not yet on target platform | non-zero | `error: parent card <uuid> is not yet on <platform>. Publish the parent first.` |
| Thread root not yet on target platform | non-zero | `error: thread root <uuid> is not yet on <platform>. Publish the root first.` |
| `card_ref` target missing or unpublished | non-zero | `error: referenced card <uuid> is not yet on <platform>. Publish the ref target first.` |
| Cycle in `card_reply_to` chain | non-zero | `error: cycle detected in card_reply_to chain at <uuid>` |
| Card already on target platform | success | skipped silently (per-platform double-post refusal); visible in the plan as `skipped: <platform>` |
| Platform wrapper exits non-zero | non-zero | stderr passed through + `error: <platform> publisher exited <code>` |
| Auto-commit fails | success (0) | `warning: auto-commit failed ...` — card file is updated; commit manually |

## What this skill does NOT do

- Does not formulate cards — that is `/card`.
- Does not update MOCs, wiki pages, or create bridge cards
  automatically — the agent does that in a separate editing pass
  after publishing.
- Does not delete posts. Bluesky's UI handles deletion; the script
  is append-only on purpose.
- Does not support raw text posts. That mode was scaffolding for
  the initial hello-world; hello-world is now done via
  `./thinkbox/scripts/publishers/bluesky.sh --text "…"` directly,
  bypassing the orchestrator.

## Invocation convention

Like other thinkbox skills, `/publish` is **not** a registered Skill.
It is a set of instructions that the agent follows manually. When the
user says "publish this card", the agent reads this file and executes
`./thinkbox/scripts/publish.sh` directly.
