# Packaging rule regression checks

Use these cases when changing the packaging criteria or readiness instructions.
Evaluate both the readiness skill and its shared criteria; `bg-pr-review` uses
the same criteria.

Each case is a BG-owned package using `bg_build`, with valid `package.xml`
dependencies, the tracked `<package> -> src/<package>` symlink, and helper-based
script discovery. Unless specified, Dylan has not authorized an exception.

| Change | Packaging rule triggered? | Expected packaging result |
| --- | --- | --- |
| Add `pyproject.toml` with `[build-system]` and `[project]`, leaving legacy `setup.py` unchanged. | Yes | Block parallel packaging metadata and require the standard BG helper/layout. A successful wheel build does not waive this. |
| Remove that TOML packaging and replace custom setup overrides with `setup(**generate_setuptools_setup())`. | Yes | No packaging blocker when the remaining layout and dependency declarations meet the criteria. |
| Change only `[tool.ruff]` in TOML; leave legacy setup customization unchanged. | No | Do not demand unrelated setup migration. |
| Change only application source; leave legacy packaging untouched. | No | Do not demand unrelated setup migration. |
| Add `[metadata]`/`[options]` packaging in `setup.cfg`, leaving standard `setup.py` unchanged. | Yes | Block the new parallel metadata/discovery path. |
| Add only `[build-system]` to TOML, leaving standard `setup.py` unchanged. | Yes | Block the alternate build declaration unless Dylan authorizes it. `[project]` is not required to trigger review. |
| Correct only conventional ament `[develop] script_dir` and `[install] install_scripts` destinations in `setup.cfg`. | No | Do not treat standard ament script destinations as alternate packaging metadata. |
| Add TOML packaging with Dylan's explicit exception covering that build/project metadata; otherwise meet the criteria. | Yes | Honor the scoped exception rather than flagging the authorized deviation. |

For behavioral validation, give an independent evaluator synthetic base/head
file contents, applicable instructions, and any explicit owner exception without
the expected results above. Compare its rule-applicability and blocker decisions
with this table. Do not claim an entire PR passes from these packaging-only
cases. Use offline fixtures; do not execute sample setup files, access production,
or publish reviews. A frontmatter validator alone does not test these decisions.
