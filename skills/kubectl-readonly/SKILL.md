---
name: kubectl-readonly
description: Inspect RAD Billerica Kubernetes resources, logs, metrics, and rollout status through a fail-closed read-only kubectl wrapper with a reusable executable-prefix approval. Does not support other clusters, mutations, or container execution.
---

# Billerica Kubernetes Reads

Use this wrapper for read-only Kubernetes inspection in RAD Billerica. Invoke the
installed executable directly:

```bash
/home/dcolli23/.codex/skills/kubectl-readonly/scripts/kubectl-readonly get pods -n cell9 -o wide
/home/dcolli23/.codex/skills/kubectl-readonly/scripts/kubectl-readonly get pods -A --field-selector=metadata.name=sumi-2204-0 -o json --save-output /tmp/bil-sumi-pods.json
/home/dcolli23/.codex/skills/kubectl-readonly/scripts/kubectl-readonly describe pod sumi-2204-0 -n cell13
/home/dcolli23/.codex/skills/kubectl-readonly/scripts/kubectl-readonly logs sumi-2204-0 -n cell9 -c procman --tail=100 --timestamps
```

The target is fixed to `k8s/bg-rad-bill1-context` and
`https://k8s.rad-bill1.bg.bgrey.io:6443`, using the managed
`/home/dcolli23/.kube/config-auto`. No context argument is needed. The identical
`--context` is accepted; every other context is rejected. The wrapper validates
the selected context, user, cluster, and TLS settings before a read, pins the
server again on the actual invocation, and does not change the current context.
It uses a private, allowlisted certificate-only kubeconfig snapshot for the read
and deletes it afterward; a concurrent credential refresh cannot introduce a
different context, proxy, or credential helper between validation and use.
Kubernetes operations through this wrapper are exempt from the container host
guard, just like direct `kubectl`.

## Supported operations

- `get`, `describe`, `logs`, `events`, `top pod`, `top node`
- `api-resources`, `api-versions`, `explain`, `version`
- `cluster-info`, `cluster-info dump` (stdout only)
- `wait`, `rollout history`, `rollout status`

Use `COMMAND --help` for accepted flags. Put the command/subcommand first;
namespace, selector, and other supported flags can follow in any order.
Boolean flags accept `--flag` or `--flag=true/false`. Output supports standard
formats and inline JSONPath/custom-column/Go templates, not template files.
`events` maps to `get events` for the installed kubectl 1.22 client rather than
relying on a newer builtin or an external plugin.

All namespaces and readable resource types, **including Secrets and custom
resources**, are permitted under the existing credentials' RBAC. Read-only is
not redaction: pod specs, logs, ConfigMaps, and Secrets may expose credentials.
Keep sensitive output out of chat unless necessary.

The wrapper deliberately has no arbitrary passthrough. It rejects unknown
commands/flags, raw API URLs, subresource paths, file/kustomize inputs,
template-file outputs, plugins, credential/server overrides, impersonation,
profiling, and credential-helper execution. In particular, `exec` is never
read-only merely because the proposed shell command is `cat` or a version check.
`auth` review requests, `diff`, and dry-run writes are not included.

An otherwise read-only option not yet supported still fails closed: report the
limitation or request a separately approved direct command. Do not broaden the
wrapper or bypass its checks to complete an investigation. Writes, other
clusters, and execution require separate authorization outside the wrapper.

## Reusable approval

For sandbox network escalation, invoke the executable directly with
`sandbox_permissions: require_escalated` and suggest **only** this prefix:

```json
["/home/dcolli23/.codex/skills/kubectl-readonly/scripts/kubectl-readonly"]
```

Do not include a command, namespace, or resource in the reusable prefix. Avoid
shell wrappers, environment assignments, pipes, and redirection in the network
command; use `--save-output` and process the saved response separately.
It creates a new mode-0600 file only after success and never overwrites files or
symlinks. Watches and log-follow streams can be interrupted; prefer bounded
`--tail`, `--since`, or explicit timeouts when appropriate.

Do not automatically edit approval rules. Persisted approval may still be
subject to managed policy. This wrapper constrains only its own invocations;
it does not remove write permissions from the existing Kubernetes identity.

On authentication failure, report it and ask Dylan to refresh credentials; do
not print or export kubeconfig credentials. No cluster-side RBAC changes or
automatic retries are performed.
