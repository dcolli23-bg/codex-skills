---
name: rad-p2-dorkspace
description: Work safely in Dylan's RAD P2 Dorkspace container. Use when the user says “work in RAD P2,” “work in the RAD P2 container,” or asks to build, test, debug, inspect, or run ROS 2 software in `/home/dcolli23/dorkspaces/rad_p2`.
---

# RAD P2 Dorkspace

Use the RAD P2 `workspace` container as the active development environment until the user selects another environment.

## Required host check

Before any other inspection or command for this skill, run:

```bash
~/code/codex-skills/scripts/require-container-host.sh
```

If the guard fails, stop immediately and report its error. Do not continue with host workspace inspection or container operations.

## Workspace map

- Host workspace: `/home/dcolli23/dorkspaces/rad_p2`
- Container workspace: `/opt/bg/ws`
- Host source tree: `/home/dcolli23/dorkspaces/rad_p2/src`
- Container source tree: `/opt/bg/ws/src`

The workspace is bind-mounted, so edits in either location affect the same files. Perform all code and repository reads directly on the host source tree, including source searches, file inspection, `AGENTS.md` discovery, and Git inspection. Make normal source edits there as well. Do not connect to the container merely to read the bind-mounted source.

Use the container only for builds, tests, ROS commands, environment-dependent dependency checks, and runtime inspection.

## Use the workspace container for execution

Run Dorkspace commands from `/home/dcolli23/dorkspaces/rad_p2`. Prefer
`ds exec workspace`, targeting the running workspace container (currently
`rad_p2-workspace-1`). Unlike GAI, RAD P2 uses the workspace rather than a
system's `bg-processes` container. Do not default to SSH.

1. Verify access and shell initialization without changing container state:

   ```bash
   cd /home/dcolli23/dorkspaces/rad_p2
   ds exec workspace "bash -lic 'cd /opt/bg/ws && pwd && whoami && printenv ROS_DISTRO && type bgbuild && test -d src'"
   ```

2. For interactive development with a terminal, use:

   ```bash
   cd /home/dcolli23/dorkspaces/rad_p2
   ds exec workspace
   # Inside the container:
   cd /opt/bg/ws
   ```

   `ds bash` is also valid: it expands to `ds exec ${DS_CONTAINER_NAME}`,
   and this workspace's `.dorkspacerc.yaml` sets `container_name: workspace`.

3. For a one-shot command that needs aliases and ROS initialization, use:

   ```bash
   cd /home/dcolli23/dorkspaces/rad_p2
   ds exec workspace "bash -lic 'cd /opt/bg/ws && <command>'"
   ```

`ds exec` joins its command arguments into a shell command; preserve the inner
quotes shown above so the entire payload reaches `bash -lic`. Quote literal
`$` expressions for the container rather than allowing host-shell expansion.
A plain noninteractive `ds exec` uses `bash -c` and does not load the `bgbuild`
alias. In a fully initialized shell, `ROS_DISTRO` is `humble` and `bgbuild` is
available as a shell alias. If shell initialization is unsuitable, explicitly
source `/opt/ros/humble/setup.bash` and `/opt/bg/ws/install/setup.bash` before
running the command, using executable commands rather than shell aliases.

The current `ds build` and `ds test` aliases also select the workspace through
`ds bash`, but their RAD P2 definitions do not forward extra arguments. For
targeted builds or tests, use the explicit one-shot form above.

## Work safely

- Before editing under the host `src/`, discover and follow every applicable nested `AGENTS.md`; notably, `src/bg_p2/AGENTS.md` has mandatory harness-instruction startup steps.
- Inspect repository status on the host before changing files and preserve unrelated modifications. The top-level `rad_p2` workspace may contain local, uncommitted changes.
- Do not use host tools as evidence that a ROS build or test works in the container.
- Do not start, stop, restart, rebuild, or update the Dorkspace or system containers unless the user explicitly requests it, or the task requires it and the impact is stated first.
- If workspace access fails or the container is not running, report the failure and ask before lifecycle actions. Do not silently start or restart the container.
