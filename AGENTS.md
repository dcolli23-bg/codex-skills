# AGENTS.md

## Purpose

This repository stores Dylan's personal Codex setup, including custom Codex skills and local configuration notes that should be version controlled.

The source repository is `/home/dcolli23/code/codex-skills`. These instructions
are also exposed at `~/.codex/skills/AGENTS.md`; that directory contains skill
discovery symlinks, not a separate source repository.

## Commit and Push Authorization

When Dylan requests any change to this `code/codex-skills` repository, commit
and push the task-related changes after appropriate validation. No separate
conversational request to commit or push is required. This applies to every
file in the repository, including skills, scripts, tests, metadata, and
instruction files.

- Honor any explicit instruction not to commit or push.
- Review the working tree and staged diff; include only changes belonging to
  the requested task and preserve unrelated work.
- Confirm the intended branch and remote before pushing. Use a normal push;
  do not force-push, rewrite history, or include unrelated unpushed commits
  under this authorization.
- If the destination is ambiguous, stop and ask rather than guessing.
- Before pushing, pull the confirmed remote branch with merge semantics
  (`git pull --no-rebase --no-autostash <remote> <branch>`). If the remote has
  new commits, integrate them by fast-forward or a normal merge; no separate
  conversational permission is needed for a conflict-free merge. Do not rebase
  or rewrite existing commits.
- Before pulling, commit validated task-related changes and preserve unrelated
  work. If remaining local changes prevent a safe pull, stop and ask; do not
  automatically stash, discard, or commit unrelated changes.
- If pulling or merging produces conflicts, stop immediately and report the
  conflicted paths. Leave the conflict state intact for Dylan; do not resolve
  conflicts, choose either side, abort the merge, or push without his direction.
- After a conflict-free pull, review the integrated changes and rerun appropriate
  validation before pushing. If the remote advances again and rejects the push,
  repeat the pull-and-merge procedure, with the same conflict stop condition.
- Filesystem/network tool approvals still apply. This permission does not
  authorize commits or pushes in other repositories.

## Layout

- `skills/`: source-controlled Codex skills.
- `skills/<skill-name>/`: one skill per directory, with its own `SKILL.md` and any supporting `references/`, `scripts/`, `agents/`, or assets.
- `scripts/`: shared scripts used by multiple skills or home-directory instructions.
- `journal/skills/`: source-controlled skills that should be installed project-locally into Dylan's journal vault.
- `journal/AGENTS.md`: the source-controlled AGENTS instructions for Dylan's journal vault.
- `.venvs/`: local virtual environments used by skills. This directory is intentionally ignored by git.
- `SYSTEMD_JOURNAL_SUMMARY_JOBS.md`: setup and troubleshooting instructions for the user-level systemd jobs that run scheduled journal daily and weekly summaries.

## Skill Symlink Pattern

Codex discovers personal skills from `~/.codex/skills/`.

Keep the real, git-tracked skill source in this repository under `skills/<skill-name>/`, then expose it to Codex with a symlink:

```bash
ln -sfn ~/code/codex-skills/skills/<skill-name> ~/.codex/skills/<skill-name>
```

For example, the `bg-elasticsearch` skill should be tracked at:

```text
~/code/codex-skills/skills/bg-elasticsearch
```

and visible to Codex at:

```text
~/.codex/skills/bg-elasticsearch
```

Expose these source-controlled instructions in the discovery directory:

```bash
ln -sfn ~/code/codex-skills/AGENTS.md ~/.codex/skills/AGENTS.md
readlink -f ~/.codex/skills/AGENTS.md
```

## BGA Read-only Wrapper Installation

The personal wrapper for the organization-managed `bga-connections` client lives
in `skills/bga-readonly/`. Install it using the personal-skill symlink pattern:

```bash
ln -sfn ~/code/codex-skills/skills/bga-readonly ~/.codex/skills/bga-readonly
readlink -f ~/.codex/skills/bga-readonly
```

Use `$bga-readonly` for provider GET requests, connection discovery, and restricted
Elasticsearch POST searches, counts, and field-capability queries. The `elastic`
subcommand verifies the provider and enabled endpoint, accepts JSON query files,
and supports complete response downloads with `--output`. Invoke
`~/.codex/skills/bga-readonly/scripts/bga-readonly` directly so one persisted
executable-prefix approval can cover changing UUIDs and endpoint paths. It
delegates to the organization client without modifying it. Writes continue
through the organization skill's normal authorization workflow.

The `bg-elasticsearch` skill selects the site/index and uses this wrapper as its
preferred query transport. Its local Python/Vault setup is a fallback for sites
without an available gateway connection; it is not required for gateway queries.

## Codex Session Release Installation

The session-release skill lives in `skills/codex-session-release/`. Install it
with the personal-skill symlink pattern:

```bash
ln -sfn ~/code/codex-skills/skills/codex-session-release ~/.codex/skills/codex-session-release
readlink -f ~/.codex/skills/codex-session-release
```

Invoke `$codex-session-release` with a session UUID, rollout path, title, or
active-writer error. It verifies and stops only the requested session's writer,
then prints the terminal resume command; it does not launch another CLI.

## PR Review Follow-up Installation

The PR feedback audit skill lives in `skills/pr-review-followup/`. Install it
with the same personal-skill symlink pattern:

```bash
ln -sfn ~/code/codex-skills/skills/pr-review-followup ~/.codex/skills/pr-review-followup
readlink -f ~/.codex/skills/pr-review-followup
```

Invoke `$pr-review-followup` with a PR and desired scope. Audits are read-only
unless posting is explicitly requested. Keep downloaded discussions, reply
plans, and receipts outside this repository.
Install `github-pr-comments` below as well; it owns the shared helper and
posting workflow, including the compatibility `pr_review.py` entry point.

## BG PR Readiness Installation

The standalone personal review skill lives in `skills/bg-pr-readiness/`. Expose
it through the personal-skill symlink:

```bash
ln -sfn ~/code/codex-skills/skills/bg-pr-readiness ~/.codex/skills/bg-pr-readiness
readlink -f ~/.codex/skills/bg-pr-readiness
```

Use `$bg-pr-readiness` for a fresh review of a BG PR or proposed change.
It drafts findings without editing or posting unless explicitly requested;
`pr-review-followup` is for auditing existing review feedback instead.
Install `github-pr-comments` below for its shared posting workflow.

## GitHub PR Comments Installation

Both PR review skills use `skills/github-pr-comments/` for posting standalone
PR discussion comments, inline review comments, replies, and review summaries.
Every posted comment begins with `[codex]`.
Default to one submitted review per PR posting batch, grouping inline findings
and general feedback to reduce notifications. Standalone comments and existing
thread replies remain available when explicitly requested.

```bash
ln -sfn ~/code/codex-skills/skills/github-pr-comments ~/.codex/skills/github-pr-comments
readlink -f ~/.codex/skills/github-pr-comments
```

Use `$github-pr-comments` when posting is requested. The shared
`scripts/pr_comments.py` helper retains discussion collection and reply-plan
posting with preview, duplicate checks, and receipts; the old follow-up command
delegates to it. Posting still requires explicit user authorization.

## Journal-Local Skills

Some skills are specific to Dylan's journal vault and should remain project-local rather than user-global. Track those sources under:

```text
~/code/codex-skills/journal/skills/<skill-name>
```

Expose them to the journal vault with symlinks under:

```text
~/journal/.codex/skills/<skill-name>
```

Use this pattern:

```bash
ln -sfn ~/code/codex-skills/journal/skills/<skill-name> ~/journal/.codex/skills/<skill-name>
```

The installed `~/journal/AGENTS.md` begins with a source and editing workflow note
that points back to this repository and its validation, commit, and push
requirements for that instruction file. Preserve that note and the symlink when
updating the journal instructions.

Track the journal vault instructions at:

```text
~/code/codex-skills/journal/AGENTS.md
```

and expose them to the journal repo as:

```text
~/journal/AGENTS.md
```

using:

```bash
ln -sfn ~/code/codex-skills/journal/AGENTS.md ~/journal/AGENTS.md
```

## Home Directory Instructions

The installed `~/AGENTS.md` begins with a source and editing workflow note that
points back to this repository and its validation, commit, and push requirements.
Preserve that note and the symlink when updating the home instructions.

The home instructions route BG GitHub, Jira, and Confluence reads through
`bga-readonly`; install its symlink as described above alongside the
organization-managed `bga-connections` skill so both the wrapper and its upstream
client are available.

Track home-directory-wide Codex instructions at:

```text
~/code/codex-skills/home-AGENTS.md
```

Expose them at the home-directory root as:

```text
~/AGENTS.md
```

using:

```bash
ln -sfn ~/code/codex-skills/home-AGENTS.md ~/AGENTS.md
```

Verify the symlink with:

```bash
readlink -f ~/AGENTS.md
```

## Dorkspace Skill Installation

Shared container behavior is maintained in `skills/dorkspace-container/SKILL.md`.
The named skills in `skills/rad-p2-dorkspace/`, `skills/gai-dorkspace/`, and
`skills/umi-dorkspace/` are entry points, each with an `environment.yaml` containing
`starters_root`, `execution`, and (for system workflows) `default_system`.
Keep environment settings in those configs, shared behavior in the shared skill,
and only environment-specific guidance in the entry points. `home-AGENTS.md`
routes requests to the entry points without duplicating their workflows.

Install the shared skill alongside all three entry points; their relative links
require it. The container workspace comes directly from `BG_ROOT`; system targets
use the fixed `bg-processes` service, with no config field for either value.

Expose and verify these skills using the tracked-source symlink pattern:

```bash
ln -sfn ~/code/codex-skills/skills/dorkspace-container ~/.codex/skills/dorkspace-container
ln -sfn ~/code/codex-skills/skills/rad-p2-dorkspace ~/.codex/skills/rad-p2-dorkspace
ln -sfn ~/code/codex-skills/skills/gai-dorkspace ~/.codex/skills/gai-dorkspace
ln -sfn ~/code/codex-skills/skills/umi-dorkspace ~/.codex/skills/umi-dorkspace
readlink -f ~/.codex/skills/dorkspace-container
readlink -f ~/.codex/skills/rad-p2-dorkspace
readlink -f ~/.codex/skills/gai-dorkspace
readlink -f ~/.codex/skills/umi-dorkspace
readlink -f ~/AGENTS.md
```

## Shared Container Host Guard

Container-oriented skills and home-directory instructions use:

```text
~/code/codex-skills/scripts/require-container-host.sh
```

Run this guard before any container-related work. It permits container skills
only when the hostname is `dylan-lambda`.

## Scheduled Journal Summary Jobs

When creating, repairing, or documenting Dylan's scheduled journal daily/weekly summary jobs, use `SYSTEMD_JOURNAL_SUMMARY_JOBS.md` as the source of truth. In particular, preserve the explicit `EnvironmentFile=%h/.config/environment.d/bg-ai-gateway.conf` service setting so timer-triggered jobs do not depend on API keys imported from an interactive shell.

## Virtual Environments

Store skill-specific Python environments under `.venvs/<skill-name>/`.

Do not commit virtual environments. Reference them from skill instructions with stable paths, for example:

```bash
source ~/code/codex-skills/.venvs/bg-elasticsearch/bin/activate
```

## Editing Rules

- Treat `skills/` as the source of truth for custom skills.
- Treat `journal/skills/` and `journal/AGENTS.md` as the source of truth for journal-local Codex behavior.
- When adding or changing a source-controlled configuration, skill, or instruction file that is installed or exposed elsewhere, update this document's installation and symlink instructions in the same change.
- Update the skill in this repository first; the `~/.codex/skills/` path should normally just be a symlink.
- For journal-local skills, update this repository first; `~/journal/.codex/skills/` should normally just contain symlinks.
- Keep generated caches, local credentials, and virtual environments out of git.
- When moving an existing skill into this repo, verify the symlink with `readlink -f ~/.codex/skills/<skill-name>`.
- For journal-local skills and instructions, verify symlinks with `readlink -f ~/journal/.codex/skills/<skill-name>` and `readlink -f ~/journal/AGENTS.md`.
