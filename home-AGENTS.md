# Home Directory AGENTS.md

## Obsidian Journal Vault

Dylan's Obsidian vault is at `/home/dcolli23/journal` (`~/journal`). When a prompt is ambiguous or needs additional personal or work context, consult the vault for relevant dev logs, meeting notes, TODOs, acronym definitions, and informal thoughts before guessing or asking for clarification.

If it is unclear which resource to search first—such as Slack, Box, or another connected source—searching the journal is a strong default first step. Use clues from the prompt to narrow the journal search, and consult more authoritative or current sources afterward when appropriate.

## Shared Acronym Knowledge Base

For unfamiliar work acronyms, shorthand, people abbreviations, product names, customer/site labels, or domain terms, consult the journal knowledge base before guessing:

- Glossary: `/home/dcolli23/journal/acronyms/`
- Unresolved terms: `/home/dcolli23/journal/UNKNOWN_ACRONYMS.md`

Search `acronyms/` first. If a term remains unresolved, use the context available or ask Dylan; do not guess. When Dylan clarifies a term, update the appropriate concise note in `journal/acronyms/` and resolve or update its entry in `journal/UNKNOWN_ACRONYMS.md`.

Do not treat standalone first names in `UNKNOWN_ACRONYMS.md` as blocking unless their identity is necessary for the task.

## Container Skill Host Guard

Before doing any work with containers or invoking a container-oriented skill, run:

```bash
~/code/codex-skills/scripts/require-container-host.sh
```

Run the guard before any other inspection or command for GAI, UMI/SUMI, RAD P2, or another container environment. If it fails, stop immediately and report its error. Do not inspect, enter, start, stop, build, test, or otherwise operate on containers from that host.

## Personal Codex Skills

Keep the source of personal, version-controlled skills in `/home/dcolli23/code/codex-skills/skills/<skill-name>/`. Expose each to Codex using a symlink at `/home/dcolli23/.codex/skills/<skill-name>`; do not create standalone copied skill directories under `.codex/skills`.

When creating or moving a skill:

```bash
ln -sfn /home/dcolli23/code/codex-skills/skills/<skill-name> /home/dcolli23/.codex/skills/<skill-name>
readlink -f /home/dcolli23/.codex/skills/<skill-name>
```

## RAD P2 Dorkspace

When Dylan says “work in the RAD P2 container,” “work in rad p2,” or equivalent, treat `/home/dcolli23/dorkspaces/rad_p2` as the active development environment until he changes it.

- The host source tree `/home/dcolli23/dorkspaces/rad_p2/src` maps to `/opt/bg/ws/src` in the container.
- Perform all code and repository reads directly on the host source tree, including source searches, file inspection, `AGENTS.md` discovery, and Git inspection. Make normal source edits there as well.
- Use the container only for builds, tests, ROS commands, environment-dependent dependency checks, and runtime inspection. Do not SSH into it merely to read the bind-mounted source.
- Prefer SSH to `robot@localhost`; obtain the host SSH port from `dorkspaces/rad_p2/docker/docker-compose.yml` (currently 5828 by default).
- Use a login/interactive shell or explicitly source the ROS and workspace setup before environment-sensitive commands.
- Read applicable repository `AGENTS.md` files beneath the host `src/` before editing.
- Do not start, stop, rebuild, or otherwise disrupt the container or system unless Dylan asks, or the task requires it and the impact is stated first.

## GAI Dorkspace

When Dylan says “work in GAI,” references `/home/dcolli23/dorkspaces/gai`, or equivalent, use the `gai-dorkspace` skill and treat that path as the active development environment until he changes it.

- The host source tree `/home/dcolli23/dorkspaces/gai/src` maps to `/opt/bg/ws/src` in the containers.
- Perform all code and repository reads directly on the host source tree, including source searches, file inspection, `AGENTS.md` discovery, and Git inspection. Make normal source edits there as well.
- Use the relevant running system container only for builds, tests, ROS commands, environment-dependent dependency checks, and runtime inspection. Do not enter it merely to read the bind-mounted source.
- Prefer `ds exec <system>-bg-processes`; do not default to SSH or the generic workspace container.
- For the RAD ABB FA system, use `ds exec rad_abb_fa-bg-processes`.
- Determine the relevant running system container from the request and current state rather than guessing.
- Read applicable repository `AGENTS.md` files beneath the host `src/` before editing.
- Do not start, stop, restart, rebuild, update, or otherwise disrupt workspace or system containers unless Dylan asks, or the task requires it and the impact is stated first.

## UMI Dorkspace

When Dylan says “work in UMI,” “work in SUMI,” “work in the UMI container,” or equivalent, treat `/home/dcolli23/dorkspaces/umi_ws` as the active development environment until he changes it.

- The host source tree `/home/dcolli23/dorkspaces/umi_ws/src` maps to `/opt/bg/ws/src` in the containers.
- Perform all code and repository reads directly on the host source tree, including source searches, file inspection, `AGENTS.md` discovery, and Git inspection. Make normal source edits there as well.
- UMI system work can use multiple containers. Determine the relevant running system container before choosing one; `bg-processes` is generally appropriate for system build, test, ROS, and runtime work.
- For workspace-container access, prefer SSH to `robot@localhost`; obtain the host SSH port from `dorkspaces/umi_ws/docker/docker-compose.yml` (currently 5830 by default).
- Use a login/interactive shell or explicitly source the ROS and workspace setup before environment-sensitive commands.
- Use the relevant container only for builds, tests, ROS commands, environment-dependent dependency checks, and runtime inspection. Do not enter it merely to read the bind-mounted source.
- Read applicable repository `AGENTS.md` files beneath the host `src/` before editing.
- Do not start, stop, restart, rebuild, update, or otherwise disrupt workspace or system containers unless Dylan asks, or the task requires it and the impact is stated first.
