# AGENTS.md

## Purpose

This repository stores Dylan's personal Codex setup, including custom Codex skills and local configuration notes that should be version controlled.

## Layout

- `skills/`: source-controlled Codex skills.
- `skills/<skill-name>/`: one skill per directory, with its own `SKILL.md` and any supporting `references/`, `scripts/`, `agents/`, or assets.
- `journal/skills/`: source-controlled skills that should be installed project-locally into Dylan's journal vault.
- `journal/AGENTS.md`: the source-controlled AGENTS instructions for Dylan's journal vault.
- `.venvs/`: local virtual environments used by skills. This directory is intentionally ignored by git.

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

## Virtual Environments

Store skill-specific Python environments under `.venvs/<skill-name>/`.

Do not commit virtual environments. Reference them from skill instructions with stable paths, for example:

```bash
source ~/code/codex-skills/.venvs/bg-elasticsearch/bin/activate
```

## Editing Rules

- Treat `skills/` as the source of truth for custom skills.
- Treat `journal/skills/` and `journal/AGENTS.md` as the source of truth for journal-local Codex behavior.
- Update the skill in this repository first; the `~/.codex/skills/` path should normally just be a symlink.
- For journal-local skills, update this repository first; `~/journal/.codex/skills/` should normally just contain symlinks.
- Keep generated caches, local credentials, and virtual environments out of git.
- When moving an existing skill into this repo, verify the symlink with `readlink -f ~/.codex/skills/<skill-name>`.
- For journal-local skills and instructions, verify symlinks with `readlink -f ~/journal/.codex/skills/<skill-name>` and `readlink -f ~/journal/AGENTS.md`.
