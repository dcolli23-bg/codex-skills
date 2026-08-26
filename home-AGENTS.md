# Home Directory AGENTS.md

## Shared Acronym Knowledge Base

For unfamiliar work acronyms, shorthand, people abbreviations, product names, customer/site labels, or domain terms, consult the journal knowledge base before guessing:

- Glossary: `/home/dcolli23/journal/acronyms/`
- Unresolved terms: `/home/dcolli23/journal/UNKNOWN_ACRONYMS.md`

Search `acronyms/` first. If a term remains unresolved, use the context available or ask Dylan; do not guess. When Dylan clarifies a term, update the appropriate concise note in `journal/acronyms/` and resolve or update its entry in `journal/UNKNOWN_ACRONYMS.md`.

Do not treat standalone first names in `UNKNOWN_ACRONYMS.md` as blocking unless their identity is necessary for the task.

## Personal Codex Skills

Keep the source of personal, version-controlled skills in `/home/dcolli23/code/codex-skills/skills/<skill-name>/`. Expose each to Codex using a symlink at `/home/dcolli23/.codex/skills/<skill-name>`; do not create standalone copied skill directories under `.codex/skills`.

When creating or moving a skill:

```bash
ln -sfn /home/dcolli23/code/codex-skills/skills/<skill-name> /home/dcolli23/.codex/skills/<skill-name>
readlink -f /home/dcolli23/.codex/skills/<skill-name>
```

## RAD P2 Dorkspace

When Dylan says “work in the RAD P2 container,” “work in rad p2,” or equivalent, treat `/home/dcolli23/dorkspaces/rad_p2` as the active development environment until he changes it.

- The host workspace maps into the container as `/opt/bg/ws`.
- The ROS 2 source tree is `/opt/bg/ws/src` in the container.
- For builds, tests, ROS commands, dependency work, or runtime inspection, use the container rather than the host environment.
- Prefer SSH to `robot@localhost`; obtain the host SSH port from `dorkspaces/rad_p2/docker/docker-compose.yml` (currently 5828 by default).
- Use a login/interactive shell or explicitly source the ROS and workspace setup before environment-sensitive commands.
- Read applicable repository `AGENTS.md` files beneath `src/` before editing.
- Do not start, stop, rebuild, or otherwise disrupt the container or system unless Dylan asks, or the task requires it and the impact is stated first.

## UMI Dorkspace

When Dylan says “work in UMI,” “work in the UMI container,” or equivalent, treat `/home/dcolli23/dorkspaces/umi_ws` as the active development environment until he changes it.

- The workspace maps into containers as `/opt/bg/ws`; the ROS 2 source tree is `/opt/bg/ws/src`.
- UMI system work can use multiple containers. Determine the relevant running system container before choosing one; `bg-processes` is generally appropriate for system build, test, ROS, and runtime work.
- For workspace-container access, prefer SSH to `robot@localhost`; obtain the host SSH port from `dorkspaces/umi_ws/docker/docker-compose.yml` (currently 5830 by default).
- Use a login/interactive shell or explicitly source the ROS and workspace setup before environment-sensitive commands.
- For builds, tests, ROS commands, dependency work, or runtime inspection, use the relevant container rather than the host environment.
- Read applicable repository `AGENTS.md` files beneath `src/` before editing.
- Do not start, stop, restart, rebuild, update, or otherwise disrupt workspace or system containers unless Dylan asks, or the task requires it and the impact is stated first.
