# Build the split packages against Core

Each repository remains independently configurable with CMake and an installed
SDK. `dependencies.lock.json` selects exact source revisions. The parent runner
provides the build order and a combined installation for integration testing; it
never adds Core's source or build directories to a consumer project.

First initialize the immediate package submodules at `packages.lock.json` and
install or extract the matching Core SDK. Provision compatible dependencies and
select the same compiler and ABI as Core. Then run with that environment's Python:

```sh
python tools/build_packages.py \
  --core-prefix /path/to/core-sdk \
  --dependencies /path/to/dependency-environment \
  --work-dir /path/to/empty-build-workspace \
  --jobs 32 --workers 4
```

The runner checks clean source revisions, copies Core into its own installation,
builds CLI and fixture packages before their consumers, and builds the ProSE and
FLASH providers before full pyOpenMS, and FLASH before FLASHTnT. It runs every registered package CTest and
the installed console numerical regression suite. Tests use the SDK's build
configuration and recorded MSVC runtime. Windows Python tests explicitly register
the dependency DLL directory, as required by Python 3.8 and newer. Compilation jobs are shared across the requested workers; choose
counts appropriate for available memory and other users on a shared machine.
Command logs, runtimes, JUnit reports and exact package pins are in `results/`.
The original Core installation is unchanged. Third-party libraries remain in the
provided dependency environment; this is not a self-contained runtime bundle.

For a later standalone rebuild of one product, use provider-only SDK prefixes
(Core, CLI and any backend it needs). Reusing the combined installation after
that same product is already installed can expose both its installed and
build-tree tool registries; CLI deliberately rejects duplicate registrations.
Keep the existing combined installation intact and use a separate build/test
prefix for that rebuild.

The dependency environment also needs Qt for desktop, and pyOpenMS's build/test
requirements, including nanobind 2.10.0 and compatible PyArrow. Interactive desktop
and optional WebEngine tests are excluded by this headless profile. Optional
instrument readers require an SDK built with those features and external data.

FLASHApp is a Python/container consumer and has separate acceptance steps in its
`experimental/README.md`. Its source lock follows the current graph. A lock update
alone does not establish a deployable wheel/runtime bundle or qualify the
FLASHTnT workflow. FLASHTnT now has its own installed-SDK repository and follows
the same native build order; it is no longer built through its upstream monorepo.

After the native build, use a Python environment with FLASHApp's hash-pinned
requirements to exercise the actual installed deconvolution workflow:

```sh
python tools/test_flashapp_deconvolution.py \
  --sdk-prefix /path/to/empty-build-workspace/sdk \
  --work-dir /path/to/new-app-test-workspace
```

This loads pyOpenMS from the selected SDK, checks its runtime identity against
the app lock, creates and reloads INI/settings files, runs FLASHDeconv and FuzzyDiff,
compares the 18 scientific reference columns, and verifies missing-input failure
propagation and process-record cleanup. The work directory must not exist; outputs
and `result.json` remain there for inspection. The immediate FLASH and FLASHApp
source checkouts and installed test-data fixtures are test inputs. This is a local
application check; it does not exercise a browser, Redis worker, container image,
or the FLASHTnT tagging workflow. The app's
`experimental/accept_flashtnt.py` exercises native tagging and its result parsers
using the bundled AQPZ reference. Its `--raw-workflow` option also runs the
complete FLASHDeconv-to-FLASHTnT workflow; see the app's acceptance report for
the exact tested SDK revisions and remaining deployment gates.
