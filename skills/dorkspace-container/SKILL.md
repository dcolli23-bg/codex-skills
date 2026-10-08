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

Before execution, check that the selected container is running with the wrapper's
`--status` action below. Use the starters configuration
to resolve the full container name if needed; pass the service target above to
`ds exec`, not the full Docker container name. State the selected environment and
container in a progress update when execution is required. If it is unavailable,
report that fact rather than switching to a different system or the workspace.

## Execute through the wrapper

Invoke `/home/dcolli23/code/codex-skills/scripts/dorkspace-exec` directly for
all `ds exec` operations. Use environment `gai`, `rad-p2`, or `umi` to match the
selected entry-point skill. The wrapper reads that skill's `environment.yaml`,
runs the host guard, sets the host working directory, and selects the configured
target. Use `--system <name>` for a selected system or `--target <service>` for an
explicit user target; otherwise omit both. It never starts or restarts containers.

For example, in GAI:

```bash
/home/dcolli23/code/codex-skills/scripts/dorkspace-exec gai --status
/home/dcolli23/code/codex-skills/scripts/dorkspace-exec gai --command 'python3 -m pytest -q rad_rfm_application/test'
/home/dcolli23/code/codex-skills/scripts/dorkspace-exec gai --command 'cd "$BG_ROOT/src/.codex-worktrees/pr-review" && python3 -m pytest -q'
/home/dcolli23/code/codex-skills/scripts/dorkspace-exec gai --script src/.codex-reviews/validation.sh
/home/dcolli23/code/codex-skills/scripts/dorkspace-exec gai --interactive
```

`--command` executes in `bash -lic` after `cd "$BG_ROOT"`, so ROS setup and
aliases such as `bgbuild` are available. Pass the command as one literal,
single-quoted host argument so `$BG_ROOT`, `$PYTHONPATH`, substitutions, and
other shell syntax are evaluated inside the container. The wrapper handles the
additional quoting required because `ds exec` joins its command arguments.
For complex commands or embedded single quotes, write a script on the bind-mounted
source tree and use `--script`; paths are relative to `$BG_ROOT`, or absolute
inside the container. For `--interactive`, run `cd "$BG_ROOT"` after entering.

If interactive/login initialization is unsuitable, add `--no-init` and explicitly
source the selected container's ROS setup and `"$BG_ROOT/install/setup.bash"`
in the command or script. This selects `bash -c`; aliases are unavailable.

### Persistent approvals

Use the absolute executable path directly in the tool's `cmd`, with no outer
`bash -lc`, host variable assignments, redirections, substitutions, or compound
host commands. Keep output in tool results or write it using a separate file
operation. When escalation is needed, request this reusable `prefix_rule`, using
the selected environment as its second argument:

```python
["/home/dcolli23/code/codex-skills/scripts/dorkspace-exec", "gai"]
```

One persisted approval then covers changing command/script arguments, status,
and target selection in that environment. This authorizes arbitrary commands
in the selected environment, including writes through its host bind mounts;
it is not a read-only wrapper. Do not edit approval rules automatically or
substitute a broad Bash/Docker allow rule. Existing task authorization and the
lifecycle boundaries below still apply.

`ds bash`, `ds build`, `ds test`, and `ds pytest` aliases select the generic
workspace through `.dorkspacerc.yaml`, so they do not select a system container.
Use the wrapper with an explicit command for builds and tests; some local aliases
do not forward extra arguments.

## Lifecycle boundaries

Do not start, stop, restart, rebuild, update, or otherwise disrupt Dorkspace or
system containers unless the user requests it, or the task requires it and the
impact is stated first. An unavailable container is not authorization to start
or restart it; report the failure and ask before lifecycle actions unless those
actions are already authorized.
