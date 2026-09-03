---
name: rad-p2-dorkspace
description: Work safely in Dylan's RAD P2 Dorkspace container. Use when the user says “work in RAD P2,” “work in the RAD P2 container,” or asks to build, test, debug, inspect, or run ROS 2 software in `/home/dcolli23/dorkspaces/rad_p2`.
---

# RAD P2 Dorkspace

Use the RAD P2 container as the active development environment until the user selects another environment.

## Workspace map

- Host workspace: `/home/dcolli23/dorkspaces/rad_p2`
- Container workspace: `/opt/bg/ws`
- Host source tree: `/home/dcolli23/dorkspaces/rad_p2/src`
- Container source tree: `/opt/bg/ws/src`

The workspace is bind-mounted, so edits in either location affect the same files. Perform all code and repository reads directly on the host source tree, including source searches, file inspection, `AGENTS.md` discovery, and Git inspection. Make normal source edits there as well. Do not connect to the container merely to read the bind-mounted source.

Use the container only for builds, tests, ROS commands, environment-dependent dependency checks, and runtime inspection.

## Connect when container execution is required

1. Read the host-side `docker/docker-compose.yml` before connecting. Its SSH mapping is currently `${BG_SSH_PORT:-5828}:${BG_SSH_PORT:-5824}`: use the host-side value, normally port `5828`.
2. Verify access without changing state:

   ```bash
   ssh -p 5828 -o BatchMode=yes -o ConnectTimeout=5 robot@localhost 'printf "user=%s BG_ROOT=%s\\n" "$USER" "$BG_ROOT"; test -d /opt/bg/ws/src'
   ```

3. For interactive development, use:

   ```bash
   ssh -tt -p 5828 robot@localhost
   cd /opt/bg/ws
   ```

4. For a one-shot command that needs aliases and ROS initialization, use a login interactive shell:

   ```bash
   ssh -p 5828 robot@localhost "bash -lic 'cd /opt/bg/ws && <command>'"
   ```

A plain non-interactive SSH command does not fully initialize the ROS environment. In a fully initialized shell, `ROS_DISTRO` is `humble`; `bgbuild` is available as a shell alias. If shell initialization is unsuitable, explicitly source `/opt/ros/humble/setup.bash` and `/opt/bg/ws/install/setup.bash` before running the command.

## Work safely

- Before editing under the host `src/`, discover and follow every applicable nested `AGENTS.md`; notably, `src/bg_p2/AGENTS.md` has mandatory harness-instruction startup steps.
- Inspect repository status on the host before changing files and preserve unrelated modifications. The top-level `rad_p2` workspace may contain local, uncommitted changes.
- Do not use host tools as evidence that a ROS build or test works in the container.
- Do not start, stop, restart, rebuild, or update the Dorkspace or system containers unless the user explicitly requests it, or the task requires it and the impact is stated first.
- Prefer SSH. Use `ds bash` only as a fallback when SSH is unavailable; run Dorkspace commands from within `/home/dcolli23/dorkspaces/rad_p2`.
- If SSH verification fails, report the failure and ask before lifecycle actions. Do not silently restart the container.
