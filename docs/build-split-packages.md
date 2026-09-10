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
FLASH providers before full pyOpenMS. It runs every registered package CTest and
the installed console numerical regression suite. Tests use the SDK's build
configuration. Compilation jobs are shared across the requested workers; choose
counts appropriate for available memory and other users on a shared machine.
Command logs, runtimes, JUnit reports and exact package pins are in `results/`.
The original Core installation is unchanged. Third-party libraries remain in the
provided dependency environment; this is not a self-contained runtime bundle.

The dependency environment also needs Qt for desktop, and pyOpenMS's build/test
requirements, including nanobind 2.10.0 and compatible PyArrow. Interactive desktop
and optional WebEngine tests are excluded by this headless profile. Optional
instrument readers require an SDK built with those features and external data.

FLASHApp is a Python/container consumer and has separate acceptance steps in its
`experimental/README.md`. Its source lock follows the current graph. A lock update
alone does not establish a deployable wheel/runtime bundle or qualify the
externally sourced FLASHTnT workflow.
