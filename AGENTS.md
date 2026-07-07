# AGENTS.md

## Purpose

This repository stores Dylan's personal Codex setup, including custom Codex skills and local configuration notes that should be version controlled.

## Layout

- `skills/`: source-controlled Codex skills.
- `skills/<skill-name>/`: one skill per directory, with its own `SKILL.md` and any supporting `references/`, `scripts/`, `agents/`, or assets.
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

## Virtual Environments

Store skill-specific Python environments under `.venvs/<skill-name>/`.

Do not commit virtual environments. Reference them from skill instructions with stable paths, for example:

```bash
source ~/code/codex-skills/.venvs/bg-elasticsearch/bin/activate
```

## Editing Rules

- Treat `skills/` as the source of truth for custom skills.
- Update the skill in this repository first; the `~/.codex/skills/` path should normally just be a symlink.
- Keep generated caches, local credentials, and virtual environments out of git.
- When moving an existing skill into this repo, verify the symlink with `readlink -f ~/.codex/skills/<skill-name>`.
