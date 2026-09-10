Review complete. Everything below is from reading the pinned source and build files; no configure, build, or test was run, and no files were changed.

## 1. Verdict and corrections on the proposed boundaries

**Verdict.** The core/CLI/products/GUI/Python cut is the right one and the source largely supports it. Three things in the proposal are underweighted enough to change the plan: the CLI layer has more reverse edges into core than listed, the GUI package cannot be split into viewers and workflows without first moving application classes out of the shared library, and the test-support library is a hard build dependency of a product (FuzzyDiff), not a development nicety.

**Core to CLI edges (all of these must be resolved before `APPLICATIONS` can leave libOpenMS):**

- `src/openms/include/OpenMS/FORMAT/IndentedStream.h:9` includes ConsoleUtils and calls it at line 64. This is a real call, so ConsoleUtils must stay in core.
- `src/openms/source/CONCEPT/Colorizer.cpp:13` includes ConsoleUtils on Windows only.
- `src/openms/source/FORMAT/ParamCTDFile.cpp:114-158` and `ParamCWLFile.cpp:117-131` use the `TOPPBase::TAG_*` string constants defined inline at `TOPPBase.h:56-60`. Move the constants to a core header and alias them from TOPPBase.
- `CalibrationWorkflow.h:20` and `CalibrationWorkflow.cpp:10` include OpenSwathBase.h. I confirmed neither file references `TOPPOpenSwathBase` or `TOPPBase` symbols, so this is a stale include, as the proposal guessed.
- `src/openms/include/OpenMS/config.h.in:167` and `:171` bake `WITH_GUI` and `WITH_WNETALIGN` into the installed core config header. `ToolHandler.cpp:79` and `:205-213` branch on them. This is the concrete mechanism behind "core owns tool identity". It also means a core SDK built with GUI off silently changes which tools ExecutePipeline and ImageCreator are considered to be.
- Seven core class tests belong to the CLI layer: `src/tests/class_tests/openms/executables.cmake:665-672` (INIUpdater, SearchEngineBase, TOPPBase, TOPPExternalToolBase, ToolHandler, ParameterInformation, ConsoleUtils).

**OpenSwathBase belongs to the OpenSWATH product, not to openms-cli.** `TOPPOpenSwathBase` (`OpenSwathBase.h:79`) pulls in the whole OpenSWATH algorithm surface (`OpenSwathBase.h:14-46`) and is used by exactly three tools: `OpenSwathWorkflow.cpp:222`, `OpenSwathPeakMapExtractor.cpp:59`, `TransitionListEvidenceFilter.cpp:57`. Putting it in openms-cli makes the CLI framework depend on OpenSWATH internals for no benefit.

**GUI depends on the compiled tool catalogue, not on a "discovery interface".** `TVToolDiscovery.cpp:34`, `TOPPASBase.cpp:325`, `ToolsDialog.cpp:236` all call `ToolHandler::getTOPPToolList()`. `TOPPASToolVertex.cpp:313-326` uses the TAG constants, and `QApplicationTOPP.cpp:144` uses `TOPPBase::cite_openms`. Seven sites call `File::findSiblingTOPPExecutable`, which searches only the executable directory and macOS bundle locations, with PATH probing still a TODO (`File.cpp:851-880`).

**Viewers and workflows cannot be separate packages yet.** TOPPViewBase, TOPPASBase and INIFileEditorWindow are compiled into libOpenMS_GUI (`src/openms_gui/source/VISUAL/APPLICATIONS/sources.cmake:5-10`), so the five app targets are thin `main()` files. ExecutePipeline and ImageCreator are additionally registered as TOPP tools and appended to the `TOPP_TOOLS` cache (`src/openms_gui/CMakeLists.txt:94-106`), their tests live in the TOPP test file (`src/tests/topp/CMakeLists.txt:3637-3645`), and the documentation tools link OpenMS_GUI (`doc/CMakeLists.txt:61-66`). For phase one use one `openms-desktop` repository holding the GUI library and all five apps.

**FuzzyDiff cannot build against the installed SDK as-is.** `src/topp/CMakeLists.txt:55` links it to `OpenMSTestFramework`, which is deliberately not exported and is excluded from default installs (`src/testframework/CMakeLists.txt:44-54`). Every downstream test suite also compiles `OpenMSTestSupport.cpp` by relative path (`class_tests/openms/CMakeLists.txt:49`, `class_tests/openms_gui/CMakeLists.txt:42`). Test support must become an exported development component.

**Core class tests read TOPP fixtures beyond the Percolator case.** `FeatureFindingMetabo_test.cpp:115`, `Percolator_subprocess_parity_test.cpp:58,1010`, `IdentificationDataConverter_test.cpp:143,221` and `PercolatorAdapter_parity_test.cpp:165` all open `../../../topp/...`. A core-only repository fails these tests unless those files are copied into the core fixture directory.

**Installed SDK contract, confirmed gaps:**

- `cmake/OpenMSConfig.cmake.in:26` finds XercesC although core links it PRIVATE (`src/openms/CMakeLists.txt:88`). CURL is genuinely PUBLIC (`:78`), so that one stays.
- Arrow is declared PRIVATE (`:252-255`) but `ParquetFile.h:14-15` and `ZipRandomAccessFile.h:11` include Arrow headers, and the build comment at `:322-325` states the public API exposes `arrow::Table`. The config file has Arrow commented out (`OpenMSConfig.cmake.in:54`), so pyOpenMS rediscovers it and picks its own static/shared flavour (`src/pyOpenMS/CMakeLists.txt:311-331`). Arrow must become a PUBLIC dependency with an exact-version `find_dependency`.
- Seven installed headers include `boost/regex.hpp` (for example `QC/DBSuitability.h:20`, `METADATA/SpectrumLookup.h:15`) while `Boost::regex` is PRIVATE and the config only finds header-only Boost (`OpenMSConfig.cmake.in:35`). Three TOPP tools link `Boost::regex` themselves (`src/topp/CMakeLists.txt:56-58`), so a standalone tools repo must find Boost components on its own.
- `@_EXPORT_INCLUDE_BLOCK@` at `OpenMSConfig.cmake.in:68` has no setter anywhere in the tree. It expands to nothing today. Harmless, but the file needs a rewrite rather than patching.
- Build helper functions that every package needs are not installed: `openms_add_executable_compiler_flags` (`cmake/compiler_flags.cmake:211`), `openms_add_library` (`cmake/add_library_macros.cmake:99`), `install_tool` (`cmake/install_macros.cmake:74`), `find_boost` (`cmake/build_system_macros.cmake:22`). Only `cmake/Modules` is installed (`src/openms/CMakeLists.txt:397`).
- Version compatibility is `SameMinorVersion` (`cmake/export_macros.cmake:38`), so an `EXACT` request works but the default is loose, and the full version string depends on the git branch name (`CMakeLists.txt:265-280`).

**Runtime data.** `share/OpenMS` mixes owners: `DESKTOP/` and `GUISTYLE/` are GUI-owned, `examples/TOPPAS/` is workflow-owned, `examples/external_code/` is an SDK sample, `SCRIPTS/*.R` is used by core `RWrapper.cpp:213`. Neither `share/OpenMS/TOOLS` nor any `.ttd` file exists, so the internal-tool scan in `ToolHandler.cpp:256-300` reads an absent directory. `commonwl/` also does not exist in the tree and is generated on demand (`cmake/cwl_generation.cmake:22-30`). Data-path resolution probes the compiled-in install prefix first on Linux and macOS (`File.cpp:674-683`), then exe-relative, then the environment last (`:722`). There is no library-relative probe, so a relocated SDK on a machine that still has the original prefix silently uses stale data.

**Python.** pyOpenMS has no `APPLICATIONS` includes at all, so it never needs openms-cli. It binds OpenSWATH and TOPDOWN heavily (55 references across `bind_analysis.cpp`, `bind_misc.cpp`, `bind_kernel.cpp`, `bind_format.cpp`), which confirms that FLASH and OpenSWATH algorithms must stay in core. Fixtures come from two places: `tests/conftest.py:84-91` (TOPP data) and `tests/unittests/test_data_paths.py:24` (core class-test data). The standalone build already uses `find_package(OpenMS REQUIRED)` with no version (`src/pyOpenMS/CMakeLists.txt:67`). The wheel workflow already defines the de facto SDK component set: `library`, `OpenMS_headers`, `OpenSwathAlgo_headers`, `thirdparty_headers`, `share`, `cmake` (`.github/workflows/pyopenms-wheels-cibuildwheel.yml:183-188`).

One small defect worth citing as evidence for manifest-driven catalogues: `ToolHandler.cpp:175` registers `QCShrinker` with the description name `QCExporter`.

## 2. Dependency graph, ownership, and the implementation order

**Corrected graph (consumer to dependency):**

| Package | Depends on | Owns |
|---|---|---|
| openms-core | native closure (Boost headers, CURL, Arrow/Parquet PUBLIC; Xerces, Eigen, libSVM, LP solver, SQLite, zlib, bzip2, libzip PRIVATE; OpenMP) | OpenSwathAlgo, libOpenMS minus APPLICATIONS, ConsoleUtils (moved to SYSTEM), TAG constants (new core header), generated headers, `share/OpenMS` minus DESKTOP/GUISTYLE/examples/TOPPAS, core class tests plus copied fixtures, exported `OpenMS::TestFramework` and `OpenMSTestSupport.cpp` as a dev component, installed helper CMake module |
| openms-cli | core | TOPPBase, ParameterInformation, ToolHandler (manifest-driven), INIUpdater class, TOPPExternalToolBase, SearchEngineBase, MapAlignerBase, the seven CLI class tests, `OpenMSCLIConfig.cmake` |
| openms-topp | core, cli, test-support (FuzzyDiff only), Boost regex, Eigen | 130 tools, `FeatureLinkerBase.cpp` (textually included by five linkers, `FeatureLinkerUnlabeledKD.cpp:15`), TOPP tests minus OpenSWATH blocks, `THIRDPARTY/third_party_tests.cmake`, KNIME and CWL generation for its tools |
| openms-openswath | core, cli | 19 tools, TOPPOpenSwathBase, test blocks at `src/tests/topp/CMakeLists.txt:1661-2402` and `2404-2485`, their fixtures |
| openms-flash | core, cli | FLASHDeconv, its single TOPP test, fixtures |
| openms-desktop | core, cli, Qt | OpenMS_GUI, five apps, `share/OpenMS/DESKTOP`, `GUISTYLE`, `examples/TOPPAS`, GUI class tests, TOPPAS pipeline tests, ImageCreator/ExecutePipeline tests |
| pyopenms | core (exact pin), Arrow (same build as core), nanobind, NumPy | `src/pyOpenMS`, copied fixtures |
| openms-suite | released artifacts of all of the above | `doc/`, TOPPDocumenter, CPack recipes, KNIME packaging, THIRDPARTY submodule, installers, container images |

**Ownership decisions:**

- Runtime data stays in core except the three GUI/workflow directories. Core adds a library-relative probe and an explicit `OPENMS_DATA_PATH` precedence rule, and stops probing the compiled-in install prefix in relocatable builds.
- Executable discovery moves to openms-cli as a manifest reader. Each product installs `share/openms-manifests/<product>.json` with tool names, categories, types, product version and required core version. `ToolHandler::getTOPPToolList` becomes the union of installed manifests. TOPPBase's "official tool" check (`TOPPBase.cpp:132`) and CTD category lookup (`:2575`) read the same manifest. `findSiblingTOPPExecutable` gains a manifest-provided root list and finally the PATH probe.
- External engines stay per-tool: the test gating in `third_party_tests.cmake:50-79` already models this.
- Documentation and installers are suite-level because TOPPDocumenter enumerates every tool and links the GUI.

**Ordered plan.** Steps 0a to 0f are ordinary commits inside the monorepo and are the only real refactoring work. Everything after that is repository surgery that should not touch code.

1. **0a, core decoupling.** Move `ConsoleUtils` to `SYSTEM/`, move TAG constants to a core header with `TOPPBase` aliases, remove the OpenSwathBase include from CalibrationWorkflow, remove `WITH_GUI` and `WITH_WNETALIGN` from `config.h.in` by making ToolHandler manifest-driven. Verify with a configure-plus-build of `OpenMS` alone.
2. **0b, test ownership.** Move `PercolatorAdapter_parity_test` to the tools tests, copy the four TOPP fixtures used by core tests into `class_tests/openms/data`, and copy the fixtures pyOpenMS uses into `src/pyOpenMS/tests/data`.
3. **0c, export test support.** Install and export `OpenMSTestFramework` as `OpenMS::TestFramework` under a `dev` component together with `OpenMSTestSupport.cpp` and `test_config.h.in`. Ship `OpenMSHelpers.cmake` with the compiler-flag, `install_tool`, and `find_boost` functions.
4. **0d, SDK contract.** Rewrite `OpenMSConfig.cmake.in`: `find_dependency(Arrow ... EXACT)` and Parquet, Boost with `regex` if the public headers keep it, drop XercesC, drop `WITH_GUI`/`BUILD_TOPP_TOOLS`, add `NAMESPACE OpenMS::` to the export and legacy alias targets. Publish the SDK only from a `WITH_GUI=OFF` build so OpenMS_GUI never enters `OpenMSTargets.cmake`.
5. **0e, relocation.** Library-relative data probe, manifest-based tool roots, PATH fallback.
6. **0f, in-tree CLI library.** Create `src/openms_cli` producing `OpenMS_CLI` from the remaining APPLICATIONS sources, link it from topp, openms_gui and doc tools. Header paths stay `OpenMS/APPLICATIONS/...` so tool sources do not change. This is the compatibility bridge: libOpenMS stops exporting TOPPBase, and consumers add one link line.
7. **Split repositories** in the order core, pyopenms, cli, flash (pilot product, single tool, links only OpenMS, one test), openswath, topp, desktop, suite.

FLASHDeconv is a better pilot than FileInfo because it is a requested product, has no extra link dependencies, and has one integration test.

**Repository topology and initial contents.** Create separate repositories under the private namespace and turn `OpenMS4-tests` into the suite superproject that references them as submodules pinned by commit. Extract each with `git filter-repo --path` on a clone so history survives. Exact paths per repository:

- `openms4-core`: `CMakeLists.txt`, `CMakePresets.json`, `cmake/` minus `package_*.cmake`, `knime_package_support.cmake`, `cwl_generation.cmake`; `src/CMakeLists.txt` reduced to openswathalgo, openms, testframework, tests; `src/openswathalgo`, `src/openms` minus `source/APPLICATIONS` and `include/OpenMS/APPLICATIONS` except ConsoleUtils; `src/testframework`; `src/tests/class_tests/openswathalgo`, `src/tests/class_tests/openms` minus the CLI tests; `src/tests/external`; `share/OpenMS` minus DESKTOP, GUISTYLE, examples/TOPPAS; `contrib` and `vcpkg` submodules; `vcpkg.json`; `License.txt`; `tools/ci`.
- `openms4-cli`: `src/openms_cli` (the moved APPLICATIONS sources), the seven class tests and their data, `OpenMSCLIConfig.cmake.in`, `openms-core.lock`.
- `openms4-flash`: `src/topp/FLASHDeconv.cpp`, the FLASHDeconv test lines and fixtures from `src/tests/topp`, `manifest.json`, lock.
- `openms4-openswath`: the 19 `.cpp` files, `OpenSwathBase.h/.cpp`, the two delimited test blocks and their fixtures, lock.
- `openms4-topp`: remaining `src/topp/*.cpp`, `FeatureLinkerBase.cpp`, `src/tests/topp` minus the moved blocks, `src/tests/topp/THIRDPARTY`, `cmake/knime_package_support.cmake`, `cmake/cwl_generation.cmake`, lock.
- `openms4-desktop`: `src/openms_gui`, `src/tests/class_tests/openms_gui`, `src/tests/toppas`, the ImageCreator and ExecutePipeline tests, `share/OpenMS/DESKTOP`, `GUISTYLE`, `examples/TOPPAS`, `cmake/package_dragndrop_dmg.cmake`, `package_mac_productbuild.cmake`, lock.
- `pyopenms4`: `src/pyOpenMS` with copied fixtures and `.github/workflows/pyopenms-wheels-cibuildwheel.yml` rewritten to download the SDK artifact, lock.
- `OpenMS4-tests` (suite): submodules, `doc/`, `cmake/package_*.cmake`, `THIRDPARTY` submodule, release and container workflows, the integration test matrix.

**SDK consumption and duplication.** Each downstream repo carries one `openms-core.lock` file with version, source commit, artifact URL per platform, SHA-256, compiler and C++ runtime identity, Arrow version and linkage, and enabled core features. A short CMake script resolves the lock into `CMAKE_PREFIX_PATH` and fails if the digest does not match, with no fallback to fetching source. Source duplication is limited to the copied fixtures listed above. Nothing from `cmake/Modules` needs copying because core already installs it. The helper module from step 0c removes the temptation to copy `compiler_flags.cmake`.

## 3. Validation, risks, and what remains unproven

**Checks that run without compiling (source and configuration verification only):**

- An include-graph script over the split trees: no `OpenMS/APPLICATIONS/` include under core, no `OpenMS/VISUAL/` include outside desktop, no include of a core private header (the PIPECHO list in `src/openms/source/ANALYSIS/MAPMATCHING/PIPECHO/sources.cmake:5-16`) from any downstream repo, no `#include <arrow/` in a public header unless Arrow is PUBLIC in the config.
- Manifest parity: every tool in each product's `executables.cmake` has a `.cpp`, a manifest entry, and a matching name. Run this on the current tree first; it should flag the QCShrinker entry.
- Test ownership parity: every `TOPP_<tool>_` test name in a repo refers to a tool that repo builds, and every fixture path it references exists inside that repo.
- Fixture completeness for core: grep `../../../topp/` in core class tests returns nothing.
- Lock validation: schema check, digest present per platform, `find_package(OpenMS <version> EXACT)` string equals the lock version.
- `cmake -P` script-mode checks of `OpenMSConfig.cmake.in` after step 0d: no `WITH_GUI`, no `BUILD_TOPP_TOOLS`, no stale placeholder, Arrow and Parquet dependencies present.

**Compile and integration acceptance tests (proven binary correctness only after these pass):**

1. Core: configure with tools, GUI and Python off, build, run class tests on a machine with Percolator on PATH and one without. Install with `--component` set, relocate the prefix, delete build and source trees, build `src/tests/external` and the `external_code` example against it, including one Eigen and one Arrow consumer.
2. pyOpenMS: standalone `pip wheel` against the relocated SDK, run the wheel tests on a clean runner, confirm only one Arrow library is loaded in the process.
3. CLI then FLASH: build against the SDK only, run `-write_ini`, `-write_ctd`, `--help`, the FLASHDeconv regression test, and a deliberately wrong lock digest that must fail at configure time.
4. OpenSWATH and TOPP: same gate, plus the external-engine tests where engines are present.
5. Desktop: TOPPView starts with no tools installed, tools installed in a different prefix are found via manifest roots, ExecutePipeline runs the four example workflows, no Qt symbol appears in libOpenMS or libOpenMS_CLI.
6. Suite: installers assembled from released artifacts with no compilation of any package.

**Five largest risks and how to address them:**

1. **Arrow leaks through the public API while being declared private.** `ParquetFile.h:14`, `ZipRandomAccessFile.h:11`, the symbol-hiding comment at `src/openms/CMakeLists.txt:322-328`, and pyOpenMS linking Arrow separately at `src/pyOpenMS/CMakeLists.txt:342` make a two-Arrow process plausible. Make Arrow PUBLIC with an exact-version find, record its linkage in the lock, and prefer a shared Arrow in the SDK.
2. **The tool catalogue and GUI flag are compiled into core.** `config.h.in:167`, `ToolHandler.cpp:46-213`, `TOPPBase.cpp:132,163,2551,2575`. Until ToolHandler reads manifests, no product can add or rename a tool without a core rebuild. Do step 0a first; it unblocks everything else.
3. **Relocation semantics are wrong for a split install.** Compiled-in prefix probed first (`File.cpp:674-683`), no library-relative probe, sibling-only executable lookup (`File.cpp:851-880`). Fix in core before publishing any SDK, otherwise every downstream failure will be a data-path failure in disguise.
4. **Test support and fixtures are entangled across owners.** FuzzyDiff needs the unexported test framework, core tests read TOPP fixtures, Python reads both fixture trees. Steps 0b and 0c resolve this with small copies and one exported dev component.
5. **GUI application logic sits in the shared library.** Splitting viewers from workflows now yields two thin repos plus a third for the library, and ExecutePipeline stays registered as a TOPP tool. Ship one desktop repository first, and only separate after TOPPViewBase and TOPPASBase move into their apps.

A secondary risk is version ambiguity: several development commits declare 3.6.0 and the config accepts any same-minor version, so the lock's commit and digest, not the CMake version, must be the compatibility key.

Nothing in this review claims that any of the split repositories build or that any test passes. The evidence supports the boundaries and the order of work. Proof comes only from the acceptance gates listed above.
