---
name: umi-dorkspace
description: Work safely in Dylan's UMI/SUMI Dorkspace. Use when the user says “work in UMI,” “work in SUMI,” “work in the UMI container,” or asks to build, test, debug, inspect, or run software in `/home/dcolli23/dorkspaces/umi_ws`.
---

# UMI / SUMI Dorkspace

Use the UMI Dorkspace as the active development environment until the user selects another environment.

## Workspace map

- Host workspace: `/home/dcolli23/dorkspaces/umi_ws`
- Container workspace: `/opt/bg/ws`
- Host source tree: `/home/dcolli23/dorkspaces/umi_ws/src`
- Container source tree: `/opt/bg/ws/src`

The workspace is bind-mounted, so edits in either location affect the same files. Perform all code and repository reads directly on the host source tree, including source searches, file inspection, `AGENTS.md` discovery, and Git inspection. Make normal source edits there as well. Do not connect to a container merely to read the bind-mounted source.

Use a container only for builds, tests, ROS commands, environment-dependent dependency checks, and runtime inspection.

## Connect when container execution is required

1. Read `docker/docker-compose.yml` and the relevant `docker/systems/` configuration before connecting.
2. Verify whether appropriate workspace or system containers are already running without changing state:

   ```bash
   cd /home/dcolli23/dorkspaces/umi_ws
   docker compose ps
   docker ps --format 'table {{.Names}}\t{{.Status}}'
   ```

3. The workspace container's SSH mapping is `${BG_SSH_PORT:-5830}:${BG_SSH_PORT:-5824}`: use the host-side value, normally port `5830`. Verify access with:

   ```bash
   ssh -p 5830 -o BatchMode=yes -o ConnectTimeout=5 robot@localhost 'printf "user=%s BG_ROOT=%s\n" "$USER" "$BG_ROOT"; test -d /opt/bg/ws/src'
   ```

4. For interactive workspace development, use:

   ```bash
   ssh -tt -p 5830 robot@localhost
   cd /opt/bg/ws
   ```

5. For a one-shot workspace command that needs aliases and ROS initialization, use a login interactive shell:

   ```bash
   ssh -p 5830 robot@localhost "bash -lic 'cd /opt/bg/ws && <command>'"
   ```

6. For system work, use the relevant running system container. The documented system is `bg_sumi_6`; `bg-processes` is usually the appropriate container:

   ```bash
   cd /home/dcolli23/dorkspaces/umi_ws
   ds exec bg_sumi_6-bg-processes
   ```

   Do not assume this container is running or that it is appropriate for every task.

## Work safely

- Before editing under the host `src/`, discover and follow every applicable nested `AGENTS.md`.
- Inspect repository status on the host before changing files and preserve unrelated modifications. The top-level `umi_ws` workspace may contain local, uncommitted changes.
- Do not use host tools as evidence that a ROS build or test works in a container.
- Do not start, stop, restart, rebuild, or update the Dorkspace or system containers unless the user explicitly requests it, or the task requires it and the impact is stated first.
- If no suitable container is running, report that fact and ask before lifecycle actions. Do not silently start a container.
