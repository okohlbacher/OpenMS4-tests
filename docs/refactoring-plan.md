# OpenMS 4: synthesized refactoring plan and implemented experiment

**10 September 2026.** The experiment establishes an installed scientific SDK as
the boundary between OpenMS and its products. Nine private child repositories
contain the extracted sources, build entry points, tests and provenance. This is
an implemented source-level decomposition; independent native builds and binary
compatibility remain unproven because building OpenMS was not authorized.

The OpenMS baseline is
[`ca32296038839459d8c9b075b759e285913d6294`](https://github.com/OpenMS/OpenMS/commit/ca32296038839459d8c9b075b759e285913d6294),
which declares 3.6.0. The new core declares **4.0.0 experimentally**: moving CLI
symbols out of libOpenMS changes its ABI. It is not a released OpenMS 4 SDK or a
binary-compatible replacement for 3.6. Scientific algorithms, file formats and
OpenSwathAlgo remain together; this phase changes ownership and build contracts.

## Review evidence and decisions

Three command-line reviewers independently inspected the baseline and the
previous architecture proposal using restricted read/search tools:

| Reviewer | Actual requested/configured model | Review artifact |
|---|---|---|
| Claude Code | `claude-fable-5-1`, also observed in response metadata | [Claude review](reviews/claude-review.md) |
| Kimi | `k3`, configured alias `kimi-code/k3` | [Kimi review](reviews/kimi-review.md) |
| Vibe | `mistral-vibe-cli-latest`, configured alias `mistral-medium-3.5` | [Vibe review](reviews/vibe-review.md) |

Kimi and Vibe did not expose a more specific server build identifier. Invocation records accompany the unchanged reviews; raw command-line logs remain in the local exploration workspace. None of the
reviewers configured, compiled or tested OpenMS. Their recommendations were
checked against source and reconciled with the actual extraction below.

The strongest agreement concerned four dependencies: application classes inside
core, installed headers exposing native libraries, tests reaching across source
trees, and GUI implementations embedded in the shared visualization library.
The [baseline source assembly](https://github.com/OpenMS/OpenMS/blob/ca32296038839459d8c9b075b759e285913d6294/src/CMakeLists.txt),
[SDK configuration](https://github.com/OpenMS/OpenMS/blob/ca32296038839459d8c9b075b759e285913d6294/cmake/OpenMSConfig.cmake.in)
and [GUI application sources](https://github.com/OpenMS/OpenMS/blob/ca32296038839459d8c9b075b759e285913d6294/src/openms_gui/source/VISUAL/APPLICATIONS/sources.cmake)
support these conclusions.

| Topic | Decision | Implemented or deferred |
|---|---|---|
| Scientific core, including FLASH/OpenSWATH algorithms | **Accepted** | Retained together, including OpenSwathAlgo and existing Python scientific APIs. |
| Move all APPLICATIONS into CLI | **Corrected** | ConsoleUtils stays core; core ParamTags removes serializer dependencies on TOPPBase; OpenSwathBase belongs to OpenSWATH. |
| Separate GUI/viewer/workflow repositories immediately | **Corrected** | One desktop repository, with three build entry points. Shared application implementation remains in its GUI SDK. |
| Dedicated test-support repository; move FuzzyDiff there | **Deferred** | Optional exported core TestSupport component; FuzzyDiff remains among 131 TOPP targets for compatibility. |
| Assign every runtime-data directory to its final owner now | **Deferred** | Core initially ships the compatibility data bundle, including GUI data. Explicit ownership migration follows runtime tests. |
| Independent Python package using the SDK | **Accepted** | Complete nanobind package, exact SDK dependency, exported Arrow target, installed fixtures. |
| Partition the entire numerical suite during extraction | **Deferred** | Full suite and TOPP fixtures preserved in test-data; product smoke tests and selected owned tests accompany products. |
| Immutable source and binary identities | **Accepted in stages** | Source SHA/version checks implemented. Binary digests require real builds; artifact verification rejects missing/placeholder hashes. |
| Filter history into every child repository | **Changed for the experiment** | Children begin as documented source snapshots; complete upstream reachable history remains on parent `develop`. |

Several review claims require explicit correction. Vibe said Eigen discovery was
absent; the baseline already discovers Eigen in
[OpenMSConfig.cmake.in](https://github.com/OpenMS/OpenMS/blob/ca32296038839459d8c9b075b759e285913d6294/cmake/OpenMSConfig.cmake.in#L39).
The remaining issue is consistent public-header and target closure. Its example
Arrow 15 pin is unusable: baseline discovery requires
[Arrow 23 or newer](https://github.com/OpenMS/OpenMS/blob/ca32296038839459d8c9b075b759e285913d6294/cmake/cmake_findExternalLibs.cmake#L249).
Its suggested Debug/Release compatibility test is rejected: require matching
compiler, runtime and build configuration, especially on Windows. SDK feature
metadata describes the artifact and must not be consumer-overridable assertions.
Vibe's sample search script and calendar estimates are not acceptance evidence.

Kimi correctly identified conditional testing hooks, but its statement that the
tested and shipped binaries differ was not established. That is a risk to audit
in release configuration, not an observed mismatch. Likewise, the baseline
PercolatorAdapter parity test conditionally skips subprocess work; its ownership
is wrong, but no unconditional failure was demonstrated. Claude's important
OpenSwathBase ownership correction is accepted; the authoritative executable
partition is **131 + 19 + 1**, including FuzzyDiff in TOPP.

## Repository and package topology

[okohlbacher/OpenMS4-tests](https://github.com/okohlbacher/OpenMS4-tests) is the
private integration parent. The refactoring branch pins nine private Git
submodules. Each child records its upstream source and its own extracted commit;
the child commit, not the old monorepo SHA, identifies an installed package.
Child snapshots preserve source attribution and licenses. They do not claim
filtered per-file Git history; upstream history is retained on parent `develop`.

| Private child repository | Initial ownership and dependency boundary |
|---|---|
| [OpenMS4-core](https://github.com/okohlbacher/OpenMS4-core) | Scientific library, OpenSwathAlgo, native dependency configuration, generated/public headers, runtime data, core tests, optional TestSupport. |
| [OpenMS4-cli](https://github.com/okohlbacher/OpenMS4-cli) | TOPPBase, ToolHandler, parameter/application helpers and CLI tests; consumes installed core. |
| [OpenMS4-topp](https://github.com/okohlbacher/OpenMS4-topp) | 131 potential general CLI targets, including FuzzyDiff and required textual helper sources; consumes core/CLI and selected direct dependencies. |
| [OpenMS4-openswath](https://github.com/okohlbacher/OpenMS4-openswath) | 19 CLI targets and OpenSwathBase; scientific implementations remain core. |
| [OpenMS4-flash](https://github.com/okohlbacher/OpenMS4-flash) | FLASHDeconv executable; consumes core/CLI. |
| [OpenMS4-desktop](https://github.com/okohlbacher/OpenMS4-desktop) | GUI SDK plus viewers TOPPView/ImageCreator/INIFileEditor and workflows TOPPAS/ExecutePipeline; consumes core/CLI/Qt. |
| [OpenMS4-pyopenms](https://github.com/okohlbacher/OpenMS4-pyopenms) | All 13 nanobind domains, main/Arrow modules, Python addons, typing, tests and wheel configuration; consumes core directly. |
| [OpenMS4-test-data](https://github.com/okohlbacher/OpenMS4-test-data) | TOPP fixtures and original numerical regression suite; installed fixture configuration and full-suite harness. |
| [OpenMS4-flashapp](https://github.com/okohlbacher/OpenMS4-flashapp) | Separately imported FLASHApp application; consumes verified Python/tool runtime artifacts. |

Counts describe potential source targets; feature switches can reduce a concrete
build. The diagram's solid arrows mean SDK/library dependencies; dashed arrows
mean runtime or test-fixture use. Repository membership does not imply that
consumers build dependency sources.

## What the implementation changes

**Core/CLI boundary.** ConsoleUtils remains at its historical include path to
avoid unnecessary source churn. `ParamTags.h` owns metadata strings used by
CTD/CWL serializers, with CLI aliases preserving familiar TOPPBase names. Stale
OpenSwathBase includes are removed from CalibrationWorkflow. This resolves real
reverse edges without moving scientific functionality. The baseline
[parameter serializer](https://github.com/OpenMS/OpenMS/blob/ca32296038839459d8c9b075b759e285913d6294/src/openms/source/FORMAT/ParamCTDFile.cpp#L114)
shows why moving the directory wholesale would fail.

CLI publishes `OpenMS::CLI` independently. Product TSV manifests under
`share/openms4/tools` provide names, categories, product versions and relative
executable paths. Discovery supports explicit `OPENMS_TOOL_PREFIX_PATH` prefixes,
then compatibility locations/PATH; GUI callers use the CLI resolver. TOPPBase can
report product and linked-core versions separately. This replaces the core's
compiled product catalogue. Manifest schema/version negotiation, conflicting
installed product policies and platform-specific behavior still need acceptance
coverage; these manifests are not a completed general package solver.

**Installed SDK.** Core exports `OpenMS::Core`, `OpenMS::OpenSwathAlgo` and
`OpenMS::Arrow`, with historical target aliases. Public Eigen/Arrow/Parquet/Boost
requirements are reflected in its target/configuration contract; Arrow and
Parquet versions and linkage choices are explicit. The SDK stops setting broad
consumer switches such as `WITH_GUI` and stops registering its build tree in the
CMake user package registry. The original
[registry export](https://github.com/OpenMS/OpenMS/blob/ca32296038839459d8c9b075b759e285913d6294/cmake/export_macros.cmake#L56)
was a route to silently consuming a stale build tree.

Versioned data installs under `share/OpenMS/4.0.0`. An explicit data override is
authoritative; otherwise lookup starts relative to the loaded core library.
Developer compatibility fallbacks remain later in the search. GUI resources
remain in the core data bundle initially, so the final data-ownership cut is
explicitly incomplete.

**Tests and Python.** Optional TestSupport exports the framework, support source,
configuration template and class fixtures without making a runtime-only SDK
require those development files. Four core fixture dependencies formerly under
TOPP are copied with provenance; executable-dependent PercolatorAdapter parity
moves to TOPP. FuzzyDiff therefore has an explicit TestSupport build dependency.
The [baseline unexported framework](https://github.com/OpenMS/OpenMS/blob/ca32296038839459d8c9b075b759e285913d6294/src/testframework/CMakeLists.txt#L44)
explains this dependency.

pyOpenMS becomes `4.0.0.dev0`, uses exact core pins and the SDK's Arrow target,
and retains binding implementations unchanged. It no longer fetches core,
rediscovers Arrow independently or patches nanobind headers. Tests use installed
core/TOPP fixture paths. Wheels bundle compatible core data; platform repair
handles native libraries. Build provenance reports Python and core identities
separately. Arrow/PyArrow coexistence, optional Thermo assemblies and Windows DLL
loading remain important runtime checks.

Desktop keeps GUI controllers and application bases together, while exposing
`gui/`, `viewers/` and `workflows/` entry points. Viewer/workflow builds can consume
an installed GUI SDK from the same desktop revision. This gives meaningful build
boundaries without pretending the tightly coupled GUI implementation has already
been separated into three source repositories.

**FLASHApp.** The app is imported from its independent public commit
[`f8e9eba435ea0843660c63fe86c58c64798e7f71`](https://github.com/OpenMS/FLASHApp/commit/f8e9eba435ea0843660c63fe86c58c64798e7f71),
including recorded Vue-component provenance. Its experimental Docker recipe
replaces the [embedded mutable OpenMS build](https://github.com/OpenMS/FLASHApp/blob/f8e9eba435ea0843660c63fe86c58c64798e7f71/Dockerfile)
with verified wheel/runtime inputs. The app requires **FLASHTnT**, absent from the
audited OpenMS baseline: provide a separately pinned artifact or explicitly
remove that workflow in later app work. FLASHQuant here views uploaded results;
no missing executable has been invented. The image intentionally cannot complete
until actual artifacts and hashes exist.

## Release contract and next acceptance gates

Implemented dependency locks enforce exact package versions and full source
SHAs. They do not identify a binary by themselves. After authorized builds,
record artifact SHA-256, platform/architecture, compiler and standard-library ABI,
C++23 flags, build configuration, shared/static choices, native dependency
versions/flavours, optional features, testing-hook policy and data digest. The
artifact verifier requires actual matching files and rejects placeholder hashes.
Publish the artifact that passed validation, or explicitly prove equivalence to
the tested configuration.

Source/fixture checks, mock installed-SDK configurations, wrong-pin rejection and
CTest registration checks have been performed. They cannot establish compilation,
linking, ABI compatibility, relocation, GUI behavior or numerical correctness.
The original numerical suite is preserved, not yet fully assigned to independent
product suites. No native build, algorithm test run, repaired wheel or working app
image is claimed.

Proceed in this order once builds are authorized:

1. **Core identity and numerical baseline.** Build core with products absent, run
   scientific/OpenSwathAlgo tests, and exercise optional external-Percolator
   conditions. Preserve dependency-provider and testing-hook identity.
2. **Installed SDK isolation.** Install runtime/SDK/data and optional TestSupport
   separately; relocate them and make original source/build trees unavailable.
   Compile/link/run ordinary, Eigen, Arrow and test-framework consumers. Reject
   incorrect versions, revisions and dependency flavours.
3. **Python proof.** Build an sdist and wheel against that SDK, repair and relocate
   the wheel, then run complete Python tests with installed fixtures. Exercise
   chemistry resources, Arrow round trips, subprocess imports and enabled vendor
   readers on every supported platform.
4. **CLI and FLASH pilot.** Build from installed dependencies only; test manifests,
   product/core version reporting, help, INI/CTD serialization and FLASHDeconv
   numerical output. Exercise missing/duplicate tools and separate prefixes.
5. **Products and regression parity.** Build TOPP/OpenSWATH independently; run
   owned tests and the preserved full numerical suite against a staged installed
   product set. Enable external-engine tests with explicit engine artifacts.
6. **Desktop and application acceptance.** Independently install GUI, then build
   viewers/workflows against it. Test GUI startup, separate-prefix discovery,
   ImageCreator output and ExecutePipeline workflows; validate Qt plugins,
   bundles/DLLs, signing and relocation. Test FLASHApp using verified artifacts,
   including its separate FLASHTnT requirement.

After these gates, partition the remaining regression suite by owner, move GUI
runtime data out of the compatibility bundle, extract reusable GUI code from
application bases, and strengthen manifest/CTD compatibility negotiation. Only
then decide whether viewers/workflows merit separate repositories, whether
FuzzyDiff merits a test-support product, and whether scientific sublibraries
should split further. Suite installers and other webapps should consume published
artifacts without rebuilding core.


## Compiler-free fixture consumption

The core also exports `OpenMSData`, a small configuration containing the exact core version/revision, resource locations and feature metadata without importing native targets. The fixture suite verifies it against the same core source lock. This lets fixture installation and regression registration use CMake `LANGUAGES NONE`, even when the real core was built with OpenMP. TestSupport fixture availability is checked explicitly.
