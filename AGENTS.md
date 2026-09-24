# AGENTS.md

## Purpose

This repository stores Dylan's personal Codex setup, including custom Codex skills and local configuration notes that should be version controlled.

The source repository is `/home/dcolli23/code/codex-skills`. These instructions
are also exposed at `~/.codex/skills/AGENTS.md`; that directory contains skill
discovery symlinks, not a separate source repository.

## Commit and Push Authorization

When Dylan requests creation or modification of a personal skill, that request
also authorizes committing and pushing the task-related changes to this
repository after appropriate validation. No separate conversational request
to commit or push is required. This includes the skill's supporting scripts,
tests, metadata, and relevant installation/instruction updates.

- Honor any explicit instruction not to commit or push.
- Review the working tree and staged diff; include only changes belonging to
  the requested task and preserve unrelated work.
- Confirm the intended branch and remote before pushing. Use a normal push;
  do not force-push, rewrite history, or include unrelated unpushed commits
  under this authorization.
- If the destination is ambiguous or the push requires reconciling divergent
  history, stop and ask rather than guessing or rewriting.
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
