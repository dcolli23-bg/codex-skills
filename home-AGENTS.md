# Home Directory AGENTS.md

## Source and Editing Workflow

`~/AGENTS.md` is installed as a symlink to `~/code/codex-skills/home-AGENTS.md`. Before editing these instructions, read `~/code/codex-skills/AGENTS.md` and follow its repository workflow, including validation, committing, and pushing requested changes unless Dylan explicitly says otherwise. Edit the tracked source and preserve the symlink.

## Obsidian Journal Vault

Dylan's Obsidian vault is at `/home/dcolli23/journal` (`~/journal`). When a prompt is ambiguous or needs additional personal or work context, consult the vault for relevant dev logs, meeting notes, TODOs, acronym definitions, and informal thoughts before guessing or asking for clarification.

If it is unclear which resource to search first—such as Slack, Box, or another connected source—searching the journal is a strong default first step. Use clues from the prompt to narrow the journal search, and consult more authoritative or current sources afterward when appropriate.

## Shared Acronym Knowledge Base

For unfamiliar work acronyms, shorthand, people abbreviations, product names, customer/site labels, or domain terms, consult the journal knowledge base before guessing:

- Glossary: `/home/dcolli23/journal/acronyms/`
- Unresolved terms: `/home/dcolli23/journal/UNKNOWN_ACRONYMS.md`

Search `acronyms/` first. If a term remains unresolved, use the context available or ask Dylan; do not guess. When Dylan clarifies a term, update the appropriate concise note in `journal/acronyms/` and resolve or update its entry in `journal/UNKNOWN_ACRONYMS.md`.

Do not treat standalone first names in `UNKNOWN_ACRONYMS.md` as blocking unless their identity is necessary for the task.

## Official OpenAI Documentation Access

For OpenAI Docs requests, open a known relevant official documentation page directly when its URL is already available from the conversation or a trusted reference. Search the official documentation only when the page is unknown, may be outdated, or does not answer the question. This overrides the bundled `openai-docs` skill's search-first step for known pages; still read the actual page and cite it when making documentation claims.

If the in-app browser is unavailable, use direct retrieval from an official OpenAI documentation domain. Do not retry that browser or probe a sitemap URL as a routine fallback. If sandbox networking blocks the direct retrieval, request the required escalation for that command.

## Berkshire Grey GitHub, Jira, and Confluence Access

Never use the Atlassian Rovo legacy connection or its tools, including tool names containing `atlassian_rovo__legacy` or `atlassian_rovo_legacy`. This prohibition applies to reads, writes, discovery, permission checks, and fallback access. If BG AI Gateway lacks a required capability, report that limitation or use its endpoint-request workflow; do not fall back to Rovo legacy.

For GitHub access involving Berkshire Grey repositories or Dylan's `dcolli23-bg` account, and for Berkshire Grey Jira and Confluence access, prefer BG AI Gateway over the general GitHub or Atlassian connectors. Use the personal `bga-readonly` skill for connection discovery, permission inspection, and approved provider GET requests, including GitHub PR descriptions, reviews, comments, and files; Jira issues and comments; and Confluence pages and comments. Read its instructions and the organization-managed `bga-connections` skill's access guidance; the wrapper delegates to that client without modifying it.

Invoke `/home/dcolli23/.codex/skills/bga-readonly/scripts/bga-readonly` directly. When network escalation is needed, suggest that executable alone as the reusable approval prefix, without a connection UUID or endpoint. Use `--output` to save complete responses instead of shell redirection, which can prevent prefix matching.

Inspect the relevant connection's permissions and try its approved read-only GitHub, Jira, or Confluence endpoints before concluding that a repository, PR review, Jira issue, or Confluence page is inaccessible. If that route is unavailable or lacks access, report the specific limitation rather than assuming that an app installation or connection grants effective access. For writes or operations the wrapper does not support, use `bga-connections` and follow its authorization requirements. Read-only approval does not authorize posting reviews, comments, or other changes.

When drafting, creating, or editing Berkshire Grey Jira issues, follow the journal-local `jira-ticket-authoring` skill at `/home/dcolli23/journal/.codex/skills/jira-ticket-authoring/SKILL.md` for shared ticket text and clickable references.

## BG Source Context

When a BG task associated with a configured Dorkspace needs additional source
code or deployment context, use the container workflow explicitly selected by
Dylan. A still-active selection from earlier in the conversation applies; if
none exists, ask which workflow to use. Do not infer it from repository names,
changed files, products, or robot/system names.

Follow that workflow for source access: read the host-mounted checkout and use
the selected container for dependency and runtime inspection. Use GitHub for PR
metadata, diffs, discussions, and checks. Do not substitute GitHub source reads
for workspace context when the selected workflow is unavailable; report the
limitation. The explicit standalone `~/code/` exception below still applies.

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

## Dorkspace Workflows

Use the matching entry-point skill when Dylan selects an environment by name or
workspace path, and keep that environment active until he changes it:

- RAD P2 / “work in the RAD P2 container” / `/home/dcolli23/dorkspaces/rad_p2`:
  [rad-p2-dorkspace](/home/dcolli23/.codex/skills/rad-p2-dorkspace/SKILL.md).
- GAI / “work in GAI” / `/home/dcolli23/dorkspaces/gai`:
  [gai-dorkspace](/home/dcolli23/.codex/skills/gai-dorkspace/SKILL.md).
- UMI / SUMI / “work in the UMI container” / `/home/dcolli23/dorkspaces/umi_ws`:
  [umi-dorkspace](/home/dcolli23/.codex/skills/umi-dorkspace/SKILL.md).

Each entry point supplies `environment.yaml` to the
[shared Dorkspace container workflow](/home/dcolli23/.codex/skills/dorkspace-container/SKILL.md),
which owns source access, container selection, execution, and lifecycle rules.
Keep environment settings in those configuration files and shared behavior in
that skill rather than duplicating them here.
