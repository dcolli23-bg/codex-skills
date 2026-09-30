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

## Berkshire Grey GitHub, Jira, and Confluence Access

For GitHub access involving Berkshire Grey repositories or Dylan's `dcolli23-bg` account, and for Berkshire Grey Jira and Confluence access, prefer BG AI Gateway over the general GitHub or Atlassian connectors. Use the personal `bga-readonly` skill for connection discovery, permission inspection, and approved provider GET requests, including GitHub PR descriptions, reviews, comments, and files; Jira issues and comments; and Confluence pages and comments. Read its instructions and the organization-managed `bga-connections` skill's access guidance; the wrapper delegates to that client without modifying it.

Invoke `/home/dcolli23/.codex/skills/bga-readonly/scripts/bga-readonly` directly. When network escalation is needed, suggest that executable alone as the reusable approval prefix, without a connection UUID or endpoint. Use `--output` to save complete responses instead of shell redirection, which can prevent prefix matching.

Inspect the relevant connection's permissions and try its approved read-only GitHub, Jira, or Confluence endpoints before concluding that a repository, PR review, Jira issue, or Confluence page is inaccessible. If that route is unavailable or lacks access, report the specific limitation rather than assuming that an app installation or connection grants effective access. For writes or operations the wrapper does not support, use `bga-connections` and follow its authorization requirements. Read-only approval does not authorize posting reviews, comments, or other changes.

## Container Skill Host Guard

Repositories that Dylan explicitly points to beneath `~/code/` are standalone clones for file inspection and small local commits. They are not associated with development containers. For work scoped to one of these repositories:

- Do not run the container host guard.
- Do not invoke container-oriented skills or container workflows.
- Inspect and edit files directly in the repository.
- Do not build, test, run, or otherwise execute repository code unless Dylan explicitly provides a non-container workflow.

This exception applies based on the explicitly requested repository path, even when its name or contents refer to GAI, UMI/SUMI, RAD P2, or another container-backed application.

Direct remote work involving the `bil-cell-*` SSH hosts is completely exempt from
the container host guard. Do not run the guard before `ssh`, `scp`, or related
commands targeting a `bil-cell-*` host, regardless of what is being inspected or
executed remotely. A previous guard failure does not prohibit subsequent work on
these hosts.

`kubectl` commands are completely exempt from the container host guard. Do not run
the guard before any command invoked through `kubectl`, regardless of the cluster,
context, namespace, resource, or subcommand (including `exec`). A previous guard
failure does not prohibit subsequent `kubectl` work.

Before doing any non-`kubectl` work with containers or invoking a
container-oriented skill, run:

```bash
~/code/codex-skills/scripts/require-container-host.sh
```

Except for `kubectl`, run the guard before any other inspection or command for
GAI, UMI/SUMI, RAD P2, or another container environment. If it fails, stop
immediately and report its error. Do not inspect, enter, start, stop, build, test,
or otherwise operate on containers from that host, except through `kubectl`.

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
