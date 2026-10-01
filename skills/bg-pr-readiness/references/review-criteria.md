# BG review criteria

Apply these to changed BG-owned code and the deployments it affects. Cite the
specific code or PR section behind each finding. Questions are preferable to
assertions when the runtime path or team convention has not been verified.

## Python packaging and package layout

- **Blocking requirement:** BG-owned Python packages added or modified by the
  PR must use the standard BG setup and package discovery layout. Flag any
  departure as a **blocker** and request correction before merge, even when
  the PR's new functionality relies on pre-existing nonstandard packaging.
  A working build does not waive this convention. Only an explicit exception
  from Dylan permits a deviation; keep unrelated legacy and third-party
  packages outside the review's scope.
- Keep `setup.py` to the standard helper invocation, apart from normal headers:

  ```python
  from setuptools import setup

  from bg_build.python_setup import generate_setuptools_setup

  setup(**generate_setuptools_setup())
  ```

  Assigning the helper result to a variable and passing it unchanged to
  `setup()` is equivalent. Custom keyword arguments or mutations of that
  result are nonstandard, including `install_requires`, `tests_require`,
  `packages`, `package_dir`, `scripts`, and duplicated package metadata.
  Do not assume a special build need grants an exception.
- Use package-root discovery supplied by the helper. When Python sources live
  under `src/<package_name>/`, require a tracked relative symlink
  `<package_name> -> src/<package_name>` inside the ROS package directory.
  Verify the symlink target and Python package contents at the reviewed
  revision. Do not retain `find_packages("src")` or `package_dir` overrides
  to compensate for a missing symlink, and do not recommend deleting those
  overrides without supplying the discoverable layout.
- **Blocking requirement: no import-path manipulation.** Application code,
  scripts, tests, and `conftest.py` must import modules through the correctly
  configured package and required `bg_build` setup. Disallow `sys.path`
  insertion, appending, extension, or reassignment, and manually extending
  `PYTHONPATH` to reach checkout, `src/`, or `scripts/` directories. Constructing
  import paths from `__file__`, parent-directory traversal, the working
  directory, or hard-coded filesystem locations is a packaging workaround,
  not an acceptable test or runtime convenience. For example, flag this:

  ```python
  module_path = Path(__file__).resolve().parents[1] / "scripts" / "episode_to_mcap.py"
  sys.path.insert(0, str(module_path.parent))
  ```

  Also reject loading the constructed path with
  `importlib.util.spec_from_file_location`, `SourceFileLoader`, or
  `runpy.run_path` as a substitute for a normal package import. A different
  filesystem loader does not fix the packaging issue.
- Request the actual packaging fix: put reusable implementation in importable
  package modules, keep executable scripts as thin entry points, declare the
  dependencies, and use ordinary imports from application code and tests.
  Validate in the normally built/installed and sourced BG environment without
  an extra import-path workaround. Ordinary paths for data/resources and the
  standard generated environment setup are outside this import-specific rule.
- Declare runtime, build, and test dependencies in `package.xml`, including
  `<buildtool_depend>bg_build</buildtool_depend>` for the helper import and
  the appropriate test dependencies. Use valid dependency keys; do not copy
  pip requirement strings into XML or invent mappings. Container dependency
  installation and version pins belong in the appropriate image/starters
  configuration, not custom `setup.py` dependency lists. For extracted shared
  code, the shared package owns its dependencies and callers depend on that
  package.
- Let BG tooling discover scripts and generate setup metadata. Read the
  selected checkout's `bg_build/python_setup.py` when discovery is uncertain.
  Examples of the minimal setup and source symlink pattern are
  `bg_core/perception/dimension_estimator` and
  `bg_rad_core/generalist_rfm_application`; `bg_rad_core#104` exposed the
  dependency and source-layout overrides this check is intended to catch.

## Configuration and deployment

- New BG application/cell settings should come from ZooKeeper through BG's
  parameter tooling (`bg_param`), not new ROS node parameters or ROS parameter
  files. ROS framework or third-party settings can be exceptions; call them
  out rather than silently treating them as BG application configuration.
  Existing ROS-to-ZooKeeper migration may be a separate task.
- Do not add code-level defaults for BG-owned ZooKeeper settings. Treat a
  setting as required unless its optional behavior is explicitly specified
  and agreed to. Watch for `.get(key, fallback)`, optional constructor
  arguments, hard-coded addresses, and duplicated defaults that make a
  missing cell config look valid. Prefer a startup error that identifies the
  missing key and deployment context. Test missing-key behavior and
  explicitly provide the key in test fixtures.
- Compare affected cell overlays with shared configuration. Check naming,
  scope, units, tolerance, and whether a parameter is already supplied by a
  shared configmap or parameter file. Do not duplicate settings merely to
  make one deployment pass. Ask for evidence from an affected deployment
  before claiming it works everywhere.
- Examples from Dylan's reviews: redundant/default parameters in
  `bg_rad_core#88` and `#91`; host settings and measured position tolerance in
  `bg_rad_billerica#85`; parameter-sourced IP in `bg_rad_core#94`.

## Bootstrap and operational logging

- **Blocking requirement:** BG-owned production paths affected by the PR must
  use appropriate BG bootstrapping (`bg_bootstrap`) and Python's standard
  `logging` logger or the C++ `bg_logging` logger, as applicable. Report verified
  non-adherence as a **blocker** and request correction before merge. Do not
  downgrade it to a nit or optional follow-up because the noncompliant helper
  predates the PR when new functionality relies on that helper. Keep unrelated
  legacy code outside the review's scope.
- Find the *actual process entry point*. Determine whether it invokes an
  appropriate BG bootstrap path (such as `bootstrap_default`) and which
  logging handlers it enables. `bootstrap_default` may use
  `/system/log/handlers`; an explicit `logging_handlers=()` disables handlers
  in that bootstrap call. A wrapper may rely on logging initialized elsewhere,
  so trace the whole startup sequence before flagging it.
- In Python, use the standard `logging` logger in production code; in C++,
  follow the repository's `bg_logging` setup and logging API. Check that
  warnings/errors needed for operations reach configured sinks, rather than
  disappearing into `print`, a bare exit, or an unconfigured logger. Log
  actionable failures once, without leaking secrets or flooding the sink.
- When operational visibility matters, request evidence that a representative
  error is emitted to the intended sink (for example the deployment's Elastic
  pipeline). A call to `SystemExit` alone is not evidence of that.
- Evidence: `bg_core/tools/bg_bootstrap/src/bg_bootstrap/helpers.py` configures
  handlers after ROS/parameters; `bg_core/logging/bg_logging/README.md` describes
  C++ setup; Dylan asked about Elastic visibility in `bg_sumi#54`.

## Tests and evidence

- A new test should protect a user-visible or operational behavior: name
  which regression it detects. Test the failure condition the change fixes
  **and** a valid case that must keep working when feasible. Cover missing
  parameters, rejected bad data, valid data, and important error logging where
  those behaviors are in scope.
- Mock external boundaries when necessary, but avoid tests that only assert
  an import, a stub call, or a particular implementation shape. Remove
  temporary exploratory tests/scripts before PR submission; keep genuine
  regression tests even if fixing them takes work. Record which tests were
  actually run and what still needs real-data or robot validation.
- Example: `bg_sumi#54` asked for bad-recording and good-recording checks;
  testing reported on `bg_rad_core#102` was explicit rather than inferred.

## API clarity and scope

- Give public or non-obvious APIs docstrings that explain behavior, return
  semantics, side effects, or failure modes; use the target repository's
  docstring style and type annotations. Do not demand boilerplate for obvious
  helpers or assume the RPS-specific docstrings skill governs every BG repo.
- Prefer accurate types to broad `Any` plus defensive `hasattr` when the input
  contract is known. Question redundant validation or duplicate checks when
  they do not catch an additional failure mode (`bg_sumi#54`).
- Look for duplicated cronjob scripts, unnecessary parameter declarations,
  pass-through wrappers, commented-out files, and unrelated generated
  artifacts. Suggest reuse or deletion only when behavior remains intact
  (`bg_rad_billerica#81`, `bg_rad_core#88`).

## PR description and release readiness

- Read the **current template in the target repo/base branch**. Check its
  required description, ticket, dependencies, workflow impact, and test
  procedure; preserve required markers and remove placeholders. Do not paste
  a template from another repo or invent a ticket.
- State how the behavior was tested and what remains untested on physical
  systems. A check that a PR description follows its template is distinct
  from validating the implementation.
- Dylan requested a template-compliant description before approval on
  `bg_rad_core#93`. SKU naming also needed owner confirmation on
  `bg_rad_billerica#65`: seek the actual convention instead of guessing.
