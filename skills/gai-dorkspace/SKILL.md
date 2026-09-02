---
name: gai-dorkspace
description: Work safely in Dylan's GAI Dorkspace through the relevant running system container. Use when the user says “work in GAI,” references `/home/dcolli23/dorkspaces/gai`, or asks to build, test, debug, inspect, or run GAI software.
---

# GAI Dorkspace

Use the GAI Dorkspace as the active development environment until the user
selects another environment.

## Workspace map

- Host workspace: `/home/dcolli23/dorkspaces/gai`
- Container workspace: `/opt/bg/ws`
- Host source tree: `/home/dcolli23/dorkspaces/gai/src`
- Container source tree: `/opt/bg/ws/src`

The workspace is bind-mounted, so edits in either location affect the same
files.

## Use the system container

Run GAI repository inspection, Git commands, builds, tests, ROS commands,
dependency work, and runtime inspection inside the relevant running system
container. Do not default to SSH or the generic `workspace` container.

1. Determine the target GAI system from the user's request and the currently
   running containers. Do not guess when it is ambiguous.
2. Prefer the system's `bg-processes` service:

   ```bash
   cd /home/dcolli23/dorkspaces/gai
   ds exec <system>-bg-processes
   ```

3. For the RAD ABB FA system, use:

   ```bash
   cd /home/dcolli23/dorkspaces/gai
   ds exec rad_abb_fa-bg-processes
   ```

4. After entering, verify that the working directory is `/opt/bg/ws` before
   operating on the source tree.

Host-side `apply_patch` edits are acceptable because the workspace is
bind-mounted, but inspect and validate the resulting repository state from
the system container.

## Work safely

- State the selected GAI system container in the first substantive progress
  update.
- Read every applicable repository `AGENTS.md` beneath `src/` before editing.
- Inspect repository status before changing files and preserve unrelated work.
- Do not use host-side builds or tests as evidence that GAI software works.
- Do not start, stop, restart, rebuild, update, or otherwise disrupt a
  workspace or system container unless the user explicitly requests it, or
  the task requires it and the impact is stated first.
- If no suitable system container is running, report that fact and ask before
  taking lifecycle actions.
