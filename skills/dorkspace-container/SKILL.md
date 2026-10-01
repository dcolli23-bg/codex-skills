---
name: dorkspace-container
description: Shared host-source and ds container execution workflow for configured BG Dorkspaces. Use with the environment.yaml selected by rad-p2-dorkspace, gai-dorkspace, or umi-dorkspace; those skills select the environment from the user's request.
---

# Dorkspace Container Workflow

Use this workflow with the calling skill's `environment.yaml`. Keep the selected
environment active until the user selects another. Environment-specific notes in
the calling skill supplement this shared workflow.

## Host boundary

Honor the home AGENTS.md host-guard exceptions for explicitly selected standalone
clones under `~/code/`, direct `bil-cell-*` work, and `kubectl`; do not route those
tasks into this Dorkspace workflow merely because they mention a related product.

Before inspecting a Dorkspace or operating on its containers, run the host guard
if it has not already passed for this task:

```bash
~/code/codex-skills/scripts/require-container-host.sh
```

If it fails, stop Dorkspace work and report the error. Do not inspect the host
workspace or operate on its containers after a failed guard.

## Environment configuration

Read the calling skill's `environment.yaml` as declarative data:

| Field | Meaning |
| --- | --- |
| `starters_root` | Absolute host path to the starters repository / Dorkspace root; run `ds` here. |
| `execution` | `workspace` or `system`. |
| `default_system` | Default system name for `system` execution; omitted for `workspace`. |

The host source tree is `<starters_root>/src`. The container workspace is
`$BG_ROOT`, and its source tree is `$BG_ROOT/src`. Trust `BG_ROOT` as part of the
container environment contract: use it directly inside container commands,
without a separate lookup, validation, hardcoded fallback, or config entry.

## Read and edit on the host

The source tree is bind-mounted. Perform code and repository reads on the host,
including source searches, file inspection, `AGENTS.md` discovery, and Git
inspection. Make normal source edits there as well. Before editing, read every
applicable repository `AGENTS.md`, inspect Git status, and preserve unrelated work.
Do not enter a container merely to read the bind-mounted source.

Use the container for builds, tests, ROS commands, environment-dependent
dependency checks, and runtime inspection. Host-side results are not evidence
that a build or test works in the container.

## Select the container

- For `execution: workspace`, use the `ds exec` target `workspace`.
- For `execution: system`, use `<system>-bg-processes`. Use the user's selected
  system when provided; otherwise use `default_system`. An explicit user target
  overrides the configured default. Ask only if the target remains ambiguous.

Before execution, check that the selected container is running, for example with
`docker ps --format 'table {{.Names}}\t{{.Status}}'`. Use the starters configuration
to resolve the full container name if needed; pass the service target above to
`ds exec`, not the full Docker container name. State the selected environment and
container in a progress update when execution is required. If it is unavailable,
report that fact rather than switching to a different system or the workspace.

## Execute through ds

Set the host working directory to `starters_root`. Prefer explicit `ds exec`
targets rather than SSH or workspace-targeting aliases.

For an interactive terminal, run `ds exec <target>`, then `cd "$BG_ROOT"` inside
the container.

For a one-shot command requiring ROS setup or aliases such as `bgbuild`, use
this host-shell pattern, substituting the selected target and command:

```bash
ds exec <target> "bash -lic 'cd \"\$BG_ROOT\" && <command>'"
```

`ds exec` joins command arguments into a shell command. Preserve the inner
single quotes around the `bash -lic` payload; the escaped double quotes and
dollar sign make `"$BG_ROOT"` expand inside the initialized container shell.
Apply the same care to other container variables and shell substitutions.
For example, a read-only command in a workspace target is:

```bash
ds exec workspace "bash -lic 'cd \"\$BG_ROOT\" && pwd'"
```

Without a terminal, plain `ds exec` uses `bash -c` and does not ensure interactive
shell initialization. If login/interactive initialization is unsuitable,
explicitly source the selected container's ROS setup and
`"$BG_ROOT/install/setup.bash"`, using executable commands rather than aliases.

In these environments, `ds bash` selects the generic workspace through
`container_name: workspace` in `.dorkspacerc.yaml`. The `ds build`, `ds test`,
and any `ds pytest` aliases also route through `ds bash`. They therefore do not
select a system container. For workspace execution, `ds bash` is a valid
interactive shortcut, but prefer explicit commands for builds and tests:
some local aliases do not forward extra arguments.

## Lifecycle boundaries

Do not start, stop, restart, rebuild, update, or otherwise disrupt Dorkspace or
system containers unless the user requests it, or the task requires it and the
impact is stated first. An unavailable container is not authorization to start
or restart it; report the failure and ask before lifecycle actions unless those
actions are already authorized.
