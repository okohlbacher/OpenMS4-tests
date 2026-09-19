**Corrections and missed coupling I would add to the proposal:**

1. **The GUI library contains the application implementations — this is the single biggest under-specified obstacle.** `src/openms_gui/includes.cmake:5-6` folds `source/VISUAL/APPLICATIONS/sources.cmake` and `APPLICATIONS/MISC/sources.cmake` into `OpenMSVisual_sources`, i.e. `TOPPViewBase`, `TOPPASBase`, `TOPPASScene`, etc. are compiled *into libOpenMS_GUI*, not into the executables. The proposal's step 6 ("move application-specific implementation toward product ownership") acknowledges this, but the subrepository topology must reflect it: **`openms-viewers` and `openms-workflows` cannot be separate repos on day one without source moves inside the GUI library.** A combined `openms-desktop` repo (library + five apps) is the honest first extraction; the viewers/workflows split is a second phase. The current diagram (`viewers --> gui`, `workflows --> gui`) depicts an end state, not an extractable one.

2. **The tested core binary is not the shipped core binary.** `src/openms/CMakeLists.txt:363-366` adds `OPENMS_ENABLE_TESTING_HOOKS=1` to libOpenMS only when class testing is enabled. If CI tests a hooks-enabled build but publishes a hooks-disabled artifact (or vice versa), the published artifact is not the tested artifact. For an "installed SDK consumed by downstream packages" contract this must be resolved: either always compile the hooks in, or publish exactly the tested binary. The proposal's pinning section (version+commit+digest) does not mention build-flag identity of the *tested* artifact.

3. **`export(PACKAGE OpenMS)` registers the build tree in the CMake user package registry** (`cmake/export_macros.cmake:56`). A consumer machine that ever configured the build tree can silently resolve `find_package(OpenMS)` to the stale build tree instead of the pinned installed SDK. The existing external test already defends against this with `NO_CMAKE_PACKAGE_REGISTRY` (`src/tests/external/CMakeLists.txt:28`). The SDK work should remove or gate this registration; it directly undermines the "hidden source/build tree" acceptance gate.

4. **`OPENMS_ADDCXX_FLAGS` is part of the de-facto ABI contract.** `cmake/OpenMSConfig.cmake.in:70` exports core's compile flags for consumers to apply. Combined with the PUBLIC `cxx_std_23` compile feature (`cmake/add_library_macros.cmake:150`), SDK consumers are locked to a C++23-capable toolchain and core-chosen flags. pyOpenMS nominally sets C++17 (`src/pyOpenMS/CMakeLists.txt:18`) but inherits C++23 via the link interface. The pin/lock file must record this; the proposal's lock list (compiler/C++ runtime ABI) covers it implicitly but the flags variable deserves explicit naming.

5. **ToolHandler reads runtime data, coupling CLI identity to core's data path.** Beyond the compiled catalogue, `ToolHandler.cpp:215-224` parses `.ttd` configuration files found via the data path for "internal tools". So the registry is not purely compile-time; the CLI package's manifest discovery design must subsume this file-based mechanism, and `share/OpenMS` ownership (currently wholesale core, `src/openms/CMakeLists.txt:374-394`) must explicitly assign tool descriptor files.

6. **Minor numerical confirmation, not correction**: the TOPP suite is far more entangled than "integration tests" suggests — 1634 `add_test` calls in one file (`src/tests/topp/CMakeLists.txt`), all addressing executables via the shared `${CMAKE_RUNTIME_OUTPUT_DIRECTORY}` (`:50`) and comparing via a sibling `FuzzyDiff` binary (`:57`), with `TOPPWRITEINI_*`/`TOPPWRITECTD_*` loops over the global `TOPP_TOOLS` cache variable (`:78-95`). Splitting this by owning package is real work, not bookkeeping.

Everything else I checked in the proposal verified cleanly: Xerces still discovered in the SDK config despite PRIVATE linkage (`cmake/OpenMSConfig.cmake.in:26` vs `src/openms/CMakeLists.txt:88`); installed `MatrixEigen.h` marked INTERNAL but including `<Eigen/Core>` (`src/openms/include/OpenMS/DATASTRUCTURES/MatrixEigen.h:11-16`); installed `ParquetFile.h` including `<arrow/api.h>` (`src/openms/include/OpenMS/FORMAT/ParquetFile.h:14-15`) while Arrow is PRIVATE (`src/openms/CMakeLists.txt:251-255`) and undiscovered by the config (`OpenMSConfig.cmake.in:45-54` has Arrow commented out); pyOpenMS's compensating Arrow re-discovery (`src/pyOpenMS/CMakeLists.txt:309-342`); the reverse includes `ParamCTDFile.cpp:11,114-158`, `ParamCWLFile.cpp:8`, `IndentedStream.cpp:22`; the TOPPBase↔ToolHandler registry check (`src/openms/source/APPLICATIONS/TOPPBase.cpp:129-140`); version from core (`TOPPBase.cpp:119-125`); sibling-only executable discovery with a PATH TODO (`src/openms/source/SYSTEM/File.cpp:851-880`, esp. `:877`) and TOPPView's error text advertising a PATH workaround the helper doesn't implement (`src/openms_gui/source/VISUAL/APPLICATIONS/TOPPViewBase.cpp:1774-1781`); the PercolatorAdapter parity-test leak (registered unconditionally at `src/tests/class_tests/openms/executables.cmake:283`, adapter path set without checking `BUILD_TOPP_TOOLS` at `src/tests/class_tests/openms/CMakeLists.txt:91-108`, test invoking the adapter and reading a TOPP fixture at `.../PercolatorAdapter_parity_test.cpp:154-175`); the unexported test framework (`src/testframework/CMakeLists.txt:44-55`); ExecutePipeline's Qt/TOPPASScene dependency (`ExecutePipeline.cpp:10-18`); the wheel CI building core from the same checkout (`.github/workflows/pyopenms-wheels-cibuildwheel.yml:166-189`); the monolithic unnamespaced export (`cmake/export_macros.cmake:14,42-43`); `SameMinorVersion` versioning (`:35-38`); unprefixed consumer variable pollution (`OpenMSConfig.cmake.in:78-82`); the deb recipe's missing SDK component and unconditional Qt deps (`cmake/package_deb.cmake:39-40,50-51`); and test suppression under packaging (`src/tests/CMakeLists.txt:31-45`).

## 2. Dependency graph and ownership decisions

Verified build-time dependency edges (all confirmed in source):

```
pyopenms ──links──> OpenMS, OpenSwathAlgo, Eigen, Arrow   (src/pyOpenMS/CMakeLists.txt:243-247,342)
TOPP tools ──link──> OpenMS (+Boost::regex/Eigen for 5 tools; FuzzyDiff +OpenMSTestFramework)
                     (src/topp/CMakeLists.txt:42,55-60)
OpenMS_GUI ──links──> OpenMS + Qt6 Gui/Widgets/Svg/OpenGLWidgets(+/WebEngine,PrintSupport)
                     (cmake/cmake_findExternalLibs.cmake:458-481)
GUI apps ──link──> OpenMS_GUI; ExecutePipeline/ImageCreator also OpenMS
                     (src/openms_gui/CMakeLists.txt:90-96)
OpenMS ──public──> OpenSwathAlgo, CURL, Boost::boost, OpenMP
                   ──private──> Xerces, Eigen, libSVM, LP solver, z/bz2/libzip, SQLiteCpp,
                       nlohmann_json, IsoSpec, eol-bspline, GTE, Evergreen, Quadtree, SIMDe,
                       vendored Percolator, Arrow/Compute/Parquet(/Dataset), opentims,
                       Thermo bridge, ONNX, tdl   (src/openms/CMakeLists.txt:77-109,251-275,296-307)
OpenSwathAlgo ──private──> Eigen, OpenMP; Boost headers  (src/openswathalgo/CMakeLists.txt:32-33)
OpenMSTestFramework: standard library only  (src/testframework/CMakeLists.txt:34-40)
```

Runtime (not link) edges that the package design must honor: TOPPView/TOPPAS → tool executables via `File::findSiblingTOPPExecutable` (6 GUI files, incl. `TOPPASToolVertex.cpp:662`, `TOPPViewBase.cpp:1774`); core → `share/OpenMS` data via the cached resolver (`File.cpp:659-757`, validity check = existence of `CHEMISTRY/unimod.xml` only, `:769-772`); adapter tools → external engines (Sage, MSGFPlus/Java, external Percolator subprocess modes); pyOpenMS → bundled `share/OpenMS` + optional Thermo managed runtime (`src/pyOpenMS/pyopenms/__init__.py:38-92`).

**Ownership decisions I endorse, with refinements:**

| Asset | Owner | Evidence / rationale |
|---|---|---|
| Scientific library, formats, data model | openms-core | unanimous; includes FLASH/OpenSWATH algorithms initially |
| OpenSwathAlgo | openms-core | no OpenMS includes outside `OPENSWATHALGO/`; publicly linked by core (`src/openms/CMakeLists.txt:304`) |
| `share/OpenMS`: CHEMISTRY, CV, MAPPING, SCHEMAS | openms-core (exact-version-coupled) | core resolver checks `CHEMISTRY/unimod.xml` (`File.cpp:771`) |
| `share/OpenMS`: GUISTYLE, DESKTOP | openms-gui/desktop | GUI-only consumers |
| `share/OpenMS`: SCRIPTS (R scripts), NUXL presets | owning tool packages (InternalCalibration, OpenNuXL) | tool-specific |
| `share/OpenMS/examples` | suite/docs package, optional | already excluded from default install (`src/openms/CMakeLists.txt:385`) and from wheels (`src/pyOpenMS/CMakeLists.txt:380`) |
| APPLICATIONS framework (TOPPBase, ToolHandler, Param* serializers, SearchEngineBase, TOPPExternalToolBase, MapAlignerBase, INIUpdater, OpenSwathBase) | openms-cli | `src/openms/source/APPLICATIONS/sources.cmake:5-15` |
| ConsoleUtils, parameter TAG constants | **stay in core** (downgrade to core utilities) | reverse includes from `IndentedStream.cpp:22` and `ParamCTDFile.cpp:114-158` make moving them a cycle |
| OpenMSTestFramework + comparison tooling | openms-test-support (dev-only) | already isolated, deliberately unexported (`src/testframework/CMakeLists.txt:44-55`) |
| FuzzyDiff | openms-test-support (not TOPP) | it links core + test framework (`src/topp/CMakeLists.txt:42,55`); every tool family's test suite needs it, so leaving it in TOPP would force all tool packages to depend on the TOPP product. The proposal's "leave FuzzyDiff in TOPP for compatibility" is the weaker option; moving it to test-support is cleaner and equally compatible since it is a dev tool |
| THIRDPARTY engines | per-tool extras / suite distribution | submodule (`.gitmodules`), redistributed via `SEARCH_ENGINES_DIRECTORY` (`CMakeLists.txt:617`) |
| KNIME + CWL generation | suite/distribution repo | both hard-require `BUILD_TOPP_TOOLS=ON` (`CMakeLists.txt:621-626,111-116`) |
| Webapps | one repo/container each, outside this tree | only documentation links exist in-tree (`doc/openms/docs/getting-started/webapps.rst`); the FLASHApp evidence is second-hand from the parent audit |

## 3. Ordered implementation plan (source-complete subrepos)

Ordering principle: every step must end with a *runnable* state, and the CLI extraction is the critical path because everything except pyOpenMS depends on it.

**Phase 0 — baseline and hygiene (in the experiment repo, no moves yet)**
1. Add a core-only preset (`BUILD_TOPP_TOOLS=OFF WITH_GUI=OFF PYOPENMS=OFF`); none exists in `CMakePresets.json` today.
2. Fix the known core-only test leak: gate `PercolatorAdapter_parity_test` on the adapter target existing, or move it to the TOPP suite (`src/tests/class_tests/openms/CMakeLists.txt:91-108`).
3. Resolve the testing-hooks artifact question (`src/openms/CMakeLists.txt:363-366`): pick one binary identity for "tested = shipped".
4. Remove/gate `export(PACKAGE OpenMS)` (`cmake/export_macros.cmake:56`).
5. Extract `ConsoleUtils` console-width helper and TOPPBase `TAG_*` constants into core-owned low-level headers; remove the stale `OpenSwathBase.h` include from `CalibrationWorkflow` after compile-check. These are the only code-level prerequisites for moving APPLICATIONS out of core, and they are small.
6. Record the dependency/feature lock schema (JSON): version, commit, artifact digest, platform/arch, compiler+stdlib ABI, C++ standard/flags (`OPENMS_ADDCXX_FLAGS`), shared/static, dependency versions and linkage (contrib commit `e127deaf…` or vcpkg pin), feature flags (`WITH_HDF5/OPENTIMS/THERMO_RAW/ONNX/WNETALIGN/TDL`), data digest.

**Phase 1 — SDK contract (still in the monorepo)**
7. Fix the export surface: `NAMESPACE OpenMS::` in `install(EXPORT)` with compatibility aliases; remove `find_dependency(XercesC)` after an installed-header scan confirms no installed header includes Xerces (mirror the existing nlohmann guard at `cmake/install_macros.cmake:44-49`); decide Eigen (either stop installing `MatrixEigen.h` or accept Eigen as a public dependency); **export an explicit Arrow component** so consumers stop re-selecting an Arrow build (`src/pyOpenMS/CMakeLists.txt:309-342` is the current workaround); replace `BUILD_TOPP_TOOLS`/`WITH_GUI` exports with `OPENMS_*`-prefixed feature metadata (`OpenMSConfig.cmake.in:78-82`).
8. Add a library-relative data probe to `File::resolveOpenMSDataPath_` and a data-version sanity check beyond `unimod.xml` presence (`File.cpp:659-772`).
9. Acceptance gate: install to a clean prefix, hide source/build trees, build `src/tests/external` plus new header-probe consumers (ordinary API, Eigen, Arrow) against it. This is a *compile* gate, not runnable today.

**Phase 2 — first two subrepos (proof of the pattern)**
10. **openms-test-support**: `src/testframework` + FuzzyDiff + a fixture manifest. Cheap, no reverse dependencies, gives every later repo its test harness.
11. **pyopenms**: `src/pyOpenMS` verbatim plus owned copies of the small fixtures its tests pull from `src/tests/topp` and `src/tests/class_tests/openms/data` (`src/pyOpenMS/tests/conftest.py:67-110`). Build standalone (PEP 517 path already exists, `pyproject.toml:13-24`) against the pinned SDK artifact. Own release version replacing the shared `3.6.0` (`pyproject.toml:29`). Acceptance: sdist → wheel on a clean runner with no OpenMS source tree; resource-dependent tests via explicit `OPENMS_DATA_PATH`.

**Phase 3 — CLI framework + pilot tool**
12. **openms-cli**: APPLICATIONS sources minus what stayed in core; replace the compiled ToolHandler catalogue with manifest files (name, version, category, CTD schema version, compatible core version) installed per tool package and discovered at runtime; TOPPBase reports tool-product version + linked core version instead of `VersionInfo::getVersion()` alone (`TOPPBase.cpp:119-125`). Keep a compatibility shim: an in-core generated manifest listing the legacy tools so unconverted consumers keep working.
13. **openms-topp pilot**: extract one small tool (FileInfo) with its tests and fixtures, built against installed core+CLI. Extend `File::findSiblingTOPPExecutable` (or its CLI-package replacement) with manifest/PATH/registry probing — implement the PATH fallback that TOPPView's error message already advertises (`TOPPViewBase.cpp:1779` vs `File.cpp:877`).

**Phase 4 — executable families**
14. Split `src/topp` and `src/tests/topp` by manifest into openms-topp (131), openms-openswath (19), openms-flash (1). The 1634-test monolith (`src/tests/topp/CMakeLists.txt`) is partitioned per package; cross-tool pipelines move to a distribution integration suite. Per-tool extras declare external engines (Sage, MSGFPlus/Java, external Percolator).

**Phase 5 — desktop**
15. **openms-desktop** (single repo initially): `src/openms_gui` whole — library + 5 apps + GUI class tests (`src/tests/class_tests/openms_gui`, gated at `src/tests/class_tests/CMakeLists.txt:26-30`) + GUISTYLE/DESKTOP resources. Only after extraction, separate reusable widgets from `TOPPViewBase`/`TOPPASBase` implementations, then split into openms-gui / openms-viewers / openms-workflows per the end-state diagram. Do not create empty viewers/workflows repos first.

**Phase 6 — suite and apps**
16. **openms-suite**: CPack/KNIME/CWL/THIRDPARTY composition from released artifacts; per-package deb metadata (current recipe lacks headers and hard-requires Qt, `package_deb.cmake:39-51`); no recompilation. Webapps consume pinned wheels/tool packages; the FLASHApp migration (replace embedded OpenMS build with pinned artifacts) is justified but rests on evidence I could not independently re-verify from this tree.

## 4. Recommended subrepository topology and initial contents

```
okohlbacher/OpenMS4-tests            (parent experiment: monorepo mirror + sync tooling + lock files)
├── subrepo openms-core              src/openms, src/openswathalgo, cmake/ build system,
│                                    share/OpenMS/{CHEMISTRY,CV,MAPPING,SCHEMAS},
│                                    src/tests/class_tests/{openms,openswathalgo},
│                                    src/tests/external, doc/doxygen core config
├── subrepo openms-cli               src/openms/source/APPLICATIONS + include/OpenMS/APPLICATIONS
│                                    (post-Phase-0 moves), manifest schema, discovery runtime
├── subrepo openms-test-support      src/testframework, FuzzyDiff (from src/topp), FuzzyDiff.ini,
│                                    hashed fixture registry
├── subrepo openms-topp              131 tools from src/topp/executables.cmake minus families,
│                                    per-tool test slices + fixtures from src/tests/topp
├── subrepo openms-flash             FLASHDeconv.cpp + its 5 test blocks and fixtures
├── subrepo openms-openswath         the 19 targets + their tests
├── subrepo openms-desktop           src/openms_gui complete + GUI class tests + GUISTYLE/DESKTOP
├── subrepo pyopenms                 src/pyOpenMS complete + owned fixtures
└── subrepo openms-suite             packaging (cmake/package_*, knime_package_support.cmake,
                                     cwl_generation.cmake), THIRDPARTY pin, installer composition
```

**Core SDK consumption contract.** Every consumer does `find_package(OpenMS <ver> EXACT CONFIG REQUIRED COMPONENTS Core)` plus a digest check against the lock file; the lock — not the version string — is authoritative, because `SameMinorVersion` (`export_macros.cmake:38`) cannot distinguish develop snapshots all labeled 3.6.0 and no SOVERSION exists. Consumers never add core source or build directories; no `FetchContent` fallback for core.

**Source duplication — the honest trade-off.** The `cmake/` build infrastructure (macros, find modules) is needed by core at build time and partly by consumers. Do not create a separate "cmake support repo" during the experiment — that adds a moving dependency before the boundaries stabilize. Instead: (a) each subrepo vendors the minimal macro set it needs, copied from the pinned parent commit with a `SOURCE_PIN` file recording parent commit SHA and copy date; (b) the installed SDK already ships `cmake/Modules` to consumers (`src/openms/CMakeLists.txt:397-398`), so downstream repos need only thin entry CMakeLists plus the vendored macros; (c) deduplicate into a shared support repo only after two or more subrepos have drifted once — then you know the actual reuse surface. This is deliberate temporary duplication, not an oversight.

**Reproducible pins.** Follow the `repository-provenance.json` pattern per repo: upstream commit, tree hash, submodule pins (contrib `e127deaf…`, THIRDPARTY `306efdbd…`, vcpkg `f9ffbaa4…` — already recorded), and for binary dependencies the contrib/vcpkg commit plus feature flags. Submodules in subrepos: core keeps `contrib` and optionally `vcpkg`; `THIRDPARTY` belongs only to tool packages/suite. History: extract subrepos with `git filter-repo`/subtree from the parent so blame history survives; the parent remains the integration mirror synced from upstream develop.

**Bridges that must exist before extraction (not after):** core-owned TAG constants/ConsoleUtils (Phase 0.5), manifest-based ToolHandler replacement with a legacy-catalog shim (Phase 3), PATH/manifest executable discovery (Phase 3.13), data path library-relative probe (Phase 1.8). Without these, "extracted" repos would be empty scaffolding around an unbroken monolith.

## 5. Validation

**Tier A — source/configuration verification, runnable now without compiling the large project:**

1. **Include-graph lint.** Script over `#include` directives asserting the allowed edge set (core may not include APPLICATIONS after Phase 0.5; GUI may include CLI/core; tools only CLI/core; pyOpenMS bindings only core/OpenSwathAlgo/Eigen/Arrow). The boundary violations found in this review (ParamCTDFile→TOPPBase, IndentedStream→ConsoleUtils, CalibrationWorkflow→OpenSwathBase) are exactly what this catches. Baseline the current violations as the allowed-exception list and ratchet.
2. **Manifest consistency.** Cross-check `src/topp/executables.cmake` ↔ `ToolHandler.cpp` map ↔ `src/tests/topp/CMakeLists.txt` registrations ↔ the proposed 131/19/1 partition; fail on orphan tools or tests.
3. **Installed-header closure scan (static).** Extend the existing configure-time nlohmann guard (`cmake/install_macros.cmake:44-49`) into a standalone script that walks the installable header list and flags `arrow/`, `Eigen/`, `xercesc/` includes against the *declared* public dependency set. Would have flagged `ParquetFile.h:14` and `MatrixEigen.h:16` automatically.
4. **pyOpenMS sdist completeness (static).** Verify every file imported by `pyopenms/__init__.py`/addons and every `bindings/*.cpp` in `PYOPENMS_DOMAINS` is covered by the `[tool.py-build-cmake.sdist] include` list (`pyproject.toml:118-136`); verify `conftest.py` fixture references against an owned-fixture manifest.
5. **Lock/provenance schema validation.** JSON-schema-check lock files; verify submodule SHAs against `.gitmodules` and the recorded pins.
6. **CMake structural checks without full configure:** parse-level validation of the new subrepo CMakeLists (e.g. `cmake -P` lint of included manifests), and a dry-run consumer-config test using a *stub* installed-SDK tree (hand-assembled config + empty imported targets) to prove `find_package` logic and component names resolve before any real build exists. This validates configuration logic, not binaries.

Tier A proves source completeness and configuration consistency only. It cannot prove ABI compatibility, link correctness, runtime data discovery, or numerical behavior.

**Tier B — compile/integration acceptance (requires authorized builds):** the proposal's seven-step gate table is sound; I would amend step 1 to include "the published core artifact is bit-identical to the class-tested binary (or hooks policy documented)" per finding 2 above, and step 2 to include "consumer configured with a poisoned CMake user package registry still resolves the pinned prefix" per finding 3. Explicitly: these are proposed gates; no build or test was run for this review.

## 6. Five largest risks

1. **Pinning theater.** A lock file saying "3.6.0" plus `SameMinorVersion` config gives false confidence across moving develop commits and across compiler/flag/ABI differences; the tested binary currently isn't even the shipped binary (testing hooks, `src/openms/CMakeLists.txt:363-366`). *Mitigation:* artifact digest + feature/flags/ABI manifest as the only accepted identity; publish only CI-tested binaries; integration matrix before allowing multi-core-version support.
2. **The installed SDK does not work as advertised today.** Arrow exposed in installed headers but not exported; Xerces over-required; Eigen ambiguous; unprefixed variables clobber consumer options; package-registry shadowing. If Phase 1 is skipped or declared done on the basis of in-tree builds, every downstream repo will silently depend on the monorepo. *Mitigation:* the hide-the-source-tree and relocation gates are mandatory exit criteria, with the external-code test as the seed.
3. **Test/fixture entanglement is the schedule risk, not the code moves.** 1634 TOPP tests in one file, global `TOPP_TOOLS` loops, shared `FuzzyDiff` binary, pyOpenMS reading sibling-package fixtures, and the PercolatorAdapter leak into core tests. Partitioning this without losing coverage is where the effort concentrates. *Mitigation:* fixture inventory + hashed test-data artifact early (Phase 2); move FuzzyDiff to test-support; keep the monolithic suite running in the parent until per-package suites reach parity, then flip.
4. **The GUI split is oversimplified in the target diagram.** Application classes are inside the GUI library (`src/openms_gui/includes.cmake:5-6`); ExecutePipeline needs QApplication+TOPPASScene; tool discovery assumes a sibling layout and even advertises a nonexistent PATH fallback. Extracting "viewers" and "workflows" as separate repos now would produce scaffolding, not products. *Mitigation:* one openms-desktop repo first; library/app source separation as an in-repo refactor; then split. Treat the diagram as end-state.
5. **Organizational divergence.** This is a hard copy outside the GitHub fork network syncing only upstream develop; every month of experiment drift makes upstream reconciliation harder, and N repos multiply release/CI maintenance (per-platform core matrix × consumers). *Mitigation:* keep subrepos mechanically synced from the single pinned parent (filter-repo extraction is repeatable), avoid semantic forking of core code, time-box the experiment to the Phase 1–3 proof (SDK + pyOpenMS + one tool), and only then decide whether upstream adoption, a permanent multi-repo org, or monorepo-with-real-package-contracts is the right end state. The evidence supports the package *contracts* regardless of the repository count; be willing to keep the monorepo with enforced contracts if the sync cost dominates.

**Limits of this review:** no configure/build/test was executed; all "works today" statements about the standalone pyOpenMS path and external-code consumer are source-level inferences, not observed behavior. FLASHApp and webapp claims rest on the parent audit's second-hand evidence (`tools-gui.md:56`, `repository-provenance.json:35-40`). Line numbers refer to the pinned commit `ca3229603` in the local checkout.
