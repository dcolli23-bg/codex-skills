---
name: umi-dorkspace
description: Work safely in Dylan's UMI/SUMI Dorkspace. Use when the user says “work in UMI,” “work in SUMI,” “work in the UMI container,” or asks to build, test, debug, inspect, or run software in `/home/dcolli23/dorkspaces/umi_ws`.
---

# UMI / SUMI Dorkspace

Use the UMI Dorkspace as the active development environment until the user selects another environment.

## Required host check

Before any other inspection or command for this skill, run:

```bash
~/code/codex-skills/scripts/require-container-host.sh
```

If the guard fails, stop immediately and report its error. Do not continue with host workspace inspection or container operations.

## Workspace map

- Host workspace: `/home/dcolli23/dorkspaces/umi_ws`
- Container workspace: `/opt/bg/ws`
- Host source tree: `/home/dcolli23/dorkspaces/umi_ws/src`
- Container source tree: `/opt/bg/ws/src`

The workspace is bind-mounted, so edits in either location affect the same files. Perform all code and repository reads directly on the host source tree, including source searches, file inspection, `AGENTS.md` discovery, and Git inspection. Make normal source edits there as well. Do not connect to a container merely to read the bind-mounted source.

Use the relevant running system container only for builds, tests, ROS commands, environment-dependent dependency checks, and runtime inspection.

## Use the system container for execution

Run Dorkspace commands from `/home/dcolli23/dorkspaces/umi_ws`. Prefer the
relevant system's `bg-processes` container. Do not default to SSH or the generic
`workspace` container.

1. Determine the target UMI system from the user's request, the relevant
   `docker/systems/` configuration, and the currently running containers.
   Do not guess when it is ambiguous. Inspect running containers without
   changing state:

   ```bash
   docker ps --format 'table {{.Names}}\t{{.Status}}'
   ```

2. For interactive development with a terminal, use:

   ```bash
   cd /home/dcolli23/dorkspaces/umi_ws
   ds exec <system>-bg-processes
   ```

   For the `bg_sumi_6` system, use:

   ```bash
   cd /home/dcolli23/dorkspaces/umi_ws
   ds exec bg_sumi_6-bg-processes
   ```

   Do not assume this system is appropriate for every task or that its container
   is running. After entering, verify that the working directory is `/opt/bg/ws`.

3. For a one-shot command that needs ROS initialization or shell aliases, use:

   ```bash
   cd /home/dcolli23/dorkspaces/umi_ws
   ds exec <system>-bg-processes "bash -lic 'cd /opt/bg/ws && <command>'"
   ```

   For example, verify access and shell initialization in `bg_sumi_6` with:

   ```bash
   cd /home/dcolli23/dorkspaces/umi_ws
   ds exec bg_sumi_6-bg-processes "bash -lic 'cd /opt/bg/ws && pwd && whoami && printenv ROS_DISTRO && type bgbuild && test -d src'"
   ```

`ds exec` joins its command arguments into a shell command; preserve the inner
quotes so the entire payload reaches `bash -lic`. Quote literal `$` expressions
for the container rather than allowing host-shell expansion. Without a terminal,
plain `ds exec` uses `bash -c` and does not ensure interactive shell initialization.
Alternatively, explicitly source the system's ROS and workspace setup before
running executable commands that do not depend on shell aliases.

The current `.dorkspacerc.yaml` sets `container_name: workspace`, so `ds bash`
targets the generic workspace. The `ds build` and `ds test` aliases also route
through `ds bash`; use explicit `ds exec <system>-bg-processes` commands for
system-container builds and tests.

## Work safely

- State the selected UMI system container in the first substantive progress update when container execution is required.
- Before editing under the host `src/`, discover and follow every applicable nested `AGENTS.md`.
- Inspect repository status on the host before changing files and preserve unrelated modifications. The top-level `umi_ws` workspace may contain local, uncommitted changes.
- Do not use host tools as evidence that a ROS build or test works in a container.
- Do not start, stop, restart, rebuild, or update the Dorkspace or system containers unless the user explicitly requests it, or the task requires it and the impact is stated first.
- If no suitable container is running, report that fact and ask before lifecycle actions. Do not silently start a container.
