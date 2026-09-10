# OpenMS 4 Decomposition — Independent Source-Level Review

**Review date:** 10 September 2026
**Baseline:** OpenMS/OpenMS `develop` @ ca32296038839459d8c9b075b759e285913d6294 (declares v3.6.0)
**Scope:** Read-only inspection of source, CMake, packaging and test infrastructure.
**No compilation, testing, code changes or Git operations were performed.**

---

## 1. Verdict on Proposed Boundaries

### ✅ Well-founded

The proposal correctly identifies that the existing build already has the key seams:
- `BUILD_TOPP_TOOLS=OFF`, `WITH_GUI=OFF`, `PYOPENMS=OFF` enable core-only builds (root `CMakeLists.txt:75-78`)
- Qt is already factored out of core (`src/openms/CMakeLists.txt` has no Qt dependencies)
- OpenSwathAlgo is a separate library (`src/CMakeLists.txt:16`)
- pyOpenMS already has a standalone build path using `find_package(OpenMS REQUIRED)` (`src/pyOpenMS/CMakeLists.txt:67`)
- External code example validates the SDK consumer mechanism (`src/tests/external/CMakeLists.txt:28`)

### ⚠️ Corrections and Missed Coupling

| **Issue** | **Evidence** | **Severity** | **Impact on Decomposition** |
|---|---|---|---|
| **Core embeds tool registry** | `ToolHandler::getTOPPToolList()` (line 18-46) compiles a **static map of all 151 TOPP tools** into `libOpenMS`. `TOPPBase::TOPPBase()` (line 132) **validates official tools against this compiled list** at runtime. | **Critical** | Any downstream package adding a new tool or releasing independently **must patch core**. This is the single biggest boundary violation. |
| **`findSiblingTOPPExecutable` hardcodes layout** | `File::findSiblingTOPPExecutable()` (line 851-880) probes: `<executablePath>/<toolName>`, macOS bundle-relative paths (`../../../TOPP/`, `../../../bin/`), but **no PATH lookup** (line 877 TODO). | **Critical** | **Prevents independent installation** of tools and consumers into different prefixes. TOPPView, TOPPAS, ExecutePipeline all depend on this (7 call sites in GUI, 2 in TOPP). |
| **Eigen leaks into installed headers** | `MatrixEigen.h` (line 16) includes `<Eigen/Core>`, is **marked INTERNAL** (line 11) but **is installed** (evidence: it is in `OpenMS_sources_h` via `includes.cmake`). `OpenMSConfig.cmake.in` does **not** discover Eigen (line 47-54 commented out), but installed headers require it. | **High** | Consumers compiling against installed SDK will fail unless Eigen is on their path. The header claims "should NOT be included in public headers" but is in the install set. |
| **Arrow leaks similarly** | `ParquetFile.h` (line 14-15) includes `<arrow/api.h>` and `<arrow/io/interfaces.h>`. Core's CMake lists Arrow as **PRIVATE** (`src/openms/CMakeLists.txt:83,88-109`), but **installed header exposes Arrow**. pyOpenMS must **manually rediscover Arrow** (`src/pyOpenMS/CMakeLists.txt:306-331`). | **High** | Same problem: SDK consumers need Arrow but core export doesn't provide it. |
| **PercolatorAdapter test in core** | `PercolatorAdapter_parity_test` (class test, `src/tests/class_tests/openms/CMakeLists.txt:91`) **invokes the TOPP `PercolatorAdapter` executable** and reads TOPP fixtures. Even with `BUILD_TOPP_TOOLS=OFF`, CMake supplies the adapter path if present (`src/tests/class_tests/openms/CMakeLists.txt:95-104`). | **High** | **Core tests depend on TOPP tooling.** Violates the "core-only preset" requirement. |
| **Core data discovery is install-path aware** | `File::getShareDir()` (used in `File.cpp` around line 669) probes: compiled install paths, source paths, and **executable-relative** locations. No library-relative lookup. | **High** | Relocatable core install with separate consumers **not validated** by current paths. |
| **Xerces discovered but marked private** | `OpenMSConfig.cmake.in:26` calls `find_dependency(XercesC)` but comments claim it is "fully encapsulated" (`src/openms/CMakeLists.txt:68-71`). However, `config.h` (included by public headers) **includes Boost** (`src/openms/CMakeLists.txt:72-76` acknowledges Boost::boost is PUBLIC). | **Medium** | Xerces is truly private; Boost headers leak via config.h. |
| **CLI framework is inside core** | `TOPPBase`, `ToolHandler`, `ConsoleUtils`, `IndentedStream`, `WindowsColorizer` all live in `src/openms/source/APPLICATIONS/` and are **compiled into libOpenMS** (`src/openms/source/APPLICATIONS/sources.cmake`). | **Medium** | These are **executable support**, not core scientific library. |
| **ExecutePipeline depends on GUI** | `ExecutePipeline.cpp:11` includes Qt (`#include <QApplication>`), depends on `TOPPASScene`. Belongs in `openms-workflows` per proposal, but **current location forces GUI dependency**. | **Medium** | Proposal correctly identifies this; current code proves it. |

### 📊 Boundary Corrections Required

1. **Move `APPLICATIONS/` out of core** → new `openms-cli` package
   - Current: `src/openms/source/APPLICATIONS/` → libOpenMS
   - Target: `openms-cli/src/` with its own library `OpenMS::CLI`
   - Contains: `TOPPBase`, `ToolHandler`, `ParameterInformation`, `ConsoleUtils`, `INIUpdater` logic
   - **Keep** generic utilities (`IndentedStream`, `WindowsColorizer`) if they have non-TOPP consumers; otherwise move them too

2. **Extract executable discovery** → `openms-cli` responsibility
   - Replace `File::findSiblingTOPPExecutable` with **manifest-based discovery**
   - New interface: `CLI::ToolResolver::findTool(string name, string versionConstraint)`
   - Uses installed package manifests, not filesystem probing

3. **Fix header visibility**
   - Remove `MatrixEigen.h` from installed headers **OR** promote Eigen to PUBLIC dependency in SDK
   - Same for `ParquetFile.h` → must either hide Arrow types behind PIMPL **OR** add Arrow to public SDK interface

4. **Move PercolatorAdapter test** → `openms-topp` package
   - Remove from `src/tests/class_tests/openms/CMakeLists.txt`
   - Add to TOPP integration tests

---

## 2. Dependency Graph and Ownership Decisions

### 📈 Actual Dependency Graph (from source inspection)

```
───────────────────────────────────────────────────────────────────────────────
LEGEND:  → = links against   │   ( ) = conditional   │   [ ] = runtime only
───────────────────────────────────────────────────────────────────────────────

NATIVE DEPENDENCIES (Core closure)
├── Boost::boost (PUBLIC, via config.h)  [src/openms/CMakeLists.txt:72-76]
├── CURL::libcurl (PUBLIC)                [src/openms/CMakeLists.txt:78]
├── Eigen3::Eigen (PRIVATE, but leaks)    [src/openms/CMakeLists.txt:83, MatrixEigen.h:16]
├── XercesC::XercesC (PRIVATE)           [src/openms/CMakeLists.txt:88]
├── Arrow/Parquet (PRIVATE, but leaks)   [src/openms/CMakeLists.txt:252-260, ParquetFile.h:14-15]
├── ZLIB, BZip2, libzip, SQLite, LibSVM, Evergreen, GTE, IsoSpec, nlohmann_json (PRIVATE)
└── Optional: HDF5, opentims, Thermo bridge, ONNX, WNetAlign

CORE LIBRARY (openms-core)
├── Scientific algorithms & data model
├── File formats (MzML, mzXML, etc.)
├── OpenSwathAlgo (already separate lib, linked by core) [src/CMakeLists.txt:16]
├── FLASH algorithms (keep in core for phase 1) [per proposal §75]
├── OpenSWATH algorithms (keep in core for phase 1) [per proposal §75]
├── Runtime data (share/OpenMS)           [src/openms/CMakeLists.txt:374-386]
├── **INCORRECTLY INCLUDES:**
│   ├── APPLICATIONS/ (TOPPBase, ToolHandler, etc.) → should be CLI
│   └── ParquetFile.h, MatrixEigen.h (leak Arrow/Eigen)
└── Generates: libOpenMS + OpenMSConfig.cmake + headers

CLI FRAMEWORK (openms-cli) ← NEW PACKAGE
├── TOPPBase (version, parameter handling)
├── ToolHandler (tool registry, metadata)
├── ParameterInformation
├── ConsoleUtils, IndentedStream
├── Tool discovery interface (replaces File::findSiblingTOPPExecutable)
└── Links: OpenMS::Core (PUBLIC)

TOPP TOOLS (openms-topp)
├── 131 general TOPP executables        [src/topp/executables.cmake:5-158]
├── Links: OpenMS::Core + OpenMS::CLI
├── Some tools have direct dependencies:
│   ├── FileMerger → Boost::regex      [src/topp/CMakeLists.txt:56]
│   ├── DecoyDatabase → Boost::regex    [src/topp/CMakeLists.txt:57]
│   ├── NucleicAcidSearchEngine → Boost::regex [src/topp/CMakeLists.txt:58]
│   ├── IsobaricWorkflow → Eigen3::Eigen [src/topp/CMakeLists.txt:59]
│   └── MetaProSIP → Eigen3::Eigen      [src/topp/CMakeLists.txt:60]
└── FuzzyDiff → OpenMSTestFramework     [src/topp/CMakeLists.txt:55]

OPENSWATH EXECUTABLES (openms-openswath)
├── 19 tools: OpenSwathAnalyzer, OpenSwathAssayGenerator, OpenSwathChromatogramExtractor,
│     OpenSwathConfidenceScoring, OpenSwathDecoyGenerator, OpenSwathFeatureXMLToTSV,
│     OpenSwathExport, OpenSwathInfer, OpenSwathPercolatorScoring, OpenSwathRTNormalizer,
│     TargetedFileConverter, OpenSwathDIAPreScoring, OpenSwathMzMLFileCacher,
│     OpenSwathPeakMapExtractor, TransitionListEvidenceFilter, OpenSwathWorkflow,
│     OpenSwathFileSplitter, OpenSwathRewriteToFeatureXML, MRMTransitionGroupPicker
├── Links: OpenMS::Core + OpenMS::CLI
└── Depends on OpenSwathAlgo (already in core)

FLASH EXECUTABLE (openms-flash)
├── FLASHDeconv (only one in baseline) [src/topp/executables.cmake:42]
├── Links: OpenMS::Core + OpenMS::CLI
└── Python bindings for FLASH output already in pyOpenMS [src/pyOpenMS/bindings/bind_format.cpp:379]

GUI LIBRARY (openms-gui)
├── Qt widgets, visualization
├── Links: OpenMS::Core + Qt6::Core/Gui/Widgets/Svg/OpenGLWidgets
├── Optional: Qt6::WebEngineWidgets
└── Uses CLI discovery interface for tool invocation

VIEWERS (openms-viewers)
├── TOPPView, ImageCreator, INIFileEditor
├── Links: OpenMS::GUI
└── Optional: processing tools (runtime dependency on openms-topp)

WORKFLOWS (openms-workflows)
├── TOPPAS, ExecutePipeline
├── Links: OpenMS::GUI + OpenMS::CLI
├── Runtime dependency: selected TOPP/OpenSWATH tools
└── ExecutePipeline currently in GUI dir, uses Qt [src/openms_gui/CMakeLists.txt:94-96]

PYOPENMS (pyopenms)
├── 13 nanobind domain modules          [src/pyOpenMS/CMakeLists.txt:33-37]
├── main_module, _arrow_zerocopy
├── Links: OpenMS::Core + OpenMS::OpenSwathAlgo + Eigen3::Eigen + Arrow
├── Standalone build: find_package(OpenMS REQUIRED) [src/pyOpenMS/CMakeLists.txt:67]
├── Bundle mode: copies OpenMS libs into wheel [src/pyOpenMS/CMakeLists.txt:406-451]
└── Tests: discover data from TOPP and core test dirs [src/pyOpenMS/CMakeLists.txt:516]

WEB APPS (per-app repos)
├── FLASHApp (already separate repo) [proposal §142]
├── Consumes: pyopenms wheel + specific tool packages
└── Currently builds TOPP from source (needs migration) [FLASHApp/Dockerfile]
```

### 🏛️ Ownership Matrix

| **Resource Type** | **Owner Package** | **Consumption Rule** | **Current Issue** | **Fix** |
|---|---|---|---|---|
| **Public C++ Headers** | openms-core | SDK via `find_package` | MatrixEigen.h, ParquetFile.h expose private deps | Remove from install OR promote deps to PUBLIC |
| **Runtime Data** | openms-core | Bundled with SDK, versioned | share/OpenMS installed with core | ✅ Correct; keep version-locked |
| **TOPP Executables** | openms-topp, openms-openswath, openms-flash | Installed binaries, discovered via manifests | findSiblingTOPPExecutable hardcodes layout | New manifest-based discovery in openms-cli |
| **GUI Executables** | openms-viewers, openms-workflows | Installed binaries | Some in GUI dir (ExecutePipeline) | Move to respective packages |
| **Python Modules** | pyopenms | Wheel with bundled native libs OR separate install | Currently copies libs into wheel | ✅ Standalone path exists; needs pinned core |
| **Test Fixtures** | Each package | Co-located with tests | PercolatorAdapter test in core | Move integration tests to owning package |
| **External Tools** | Tool-specific packages | Runtime PATH or manifest | Percolator, MSGFPlus, Sage invoked by tools | Each tool package declares runtime deps |
| **Qt Plugins** | openms-gui | Installed with GUI | macOS/Windows plugin handling in GUI CMake | Keep with GUI package |

### 🔐 SDK Contract (What `find_package(OpenMS)` Must Provide)

```cmake
# REQUIRED targets (namespaced):
OpenMS::Core          # Main scientific library
OpenMS::OpenSwathAlgo # DIA algorithms (separate lib, already exists)

# REQUIRED variables:
OPENMS_VERSION        # Version string
OPENMS_DATA_DIR       # Path to runtime data (share/OpenMS)
OPENMS_ADDCXX_FLAGS   # Compiler flags for consumers

# REQUIRED public dependencies (must be findable):
Boost::boost         # Header-only, required by config.h
CURL::libcurl         # PUBLIC link dependency
Eigen3::Eigen        # MUST be promoted to PUBLIC (currently leaks via headers)

# OPTIONAL components (for future):
OpenMS::CLI          # When extracted; currently part of Core
```

**Critical:** The current `OpenMSConfig.cmake.in` **does NOT export namespaced targets** (line 84-85 just includes the targets file). It also **exports build options** like `BUILD_TOPP_TOOLS` and `WITH_GUI` (line 78-82) which **should not control consumer builds**.

---

## 3. Practical Implementation Plan

### 📅 Phase 0: Baseline Validation (Week 1-2)

**Goal:** Prove core can build and test without TOPP, GUI, or Python.

| **Task** | **Action** | **Evidence Required** |
|---|---|---|
| 0.1 | Configure core-only build | `cmake -DBUILD_TOPP_TOOLS=OFF -DWITH_GUI=OFF -DPYOPENMS=OFF ...` |
| 0.2 | Verify core class tests pass | `ctest -R class_tests` with TOPP/GUI absent |
| 0.3 | **Fix PercolatorAdapter test leak** | Remove from core tests OR gate on explicit adapter path. Must pass on machines **without** external Percolator. | [src/tests/class_tests/openms/CMakeLists.txt:91] |
| 0.4 | Document core public API | Audit all installed headers for private dependency includes |
| 0.5 | Record exact dependency closure | Capture all native lib versions, compiler, C++ std lib ABI |

**Blockers:** PercolatorAdapter test currently fails the "core-only" requirement.

### 📦 Phase 1: Publish Installable Core SDK (Week 3-6)

**Goal:** Install core, hide source/build tree, consumers compile against it.

| **Task** | **Action** | **Files to Modify** | **Evidence** |
|---|---|---|---|
| 1.1 | **Add namespaced targets** | Modify export to create `OpenMS::Core`, `OpenMS::OpenSwathAlgo` | Currently only raw targets exported [cmake/export_macros.cmake:42] |
| 1.2 | **Promote Eigen to PUBLIC** OR remove MatrixEigen.h from install | Either: (a) add `find_dependency(Eigen3)` to OpenMSConfig.cmake.in AND uncomment, OR (b) remove MatrixEigen.h from header install list | [OpenMSConfig.cmake.in:36-43], [MatrixEigen.h:16] |
| 1.3 | **Same for Arrow** | Either hide behind PIMPL in ParquetFile.h OR add Arrow to PUBLIC deps | [ParquetFile.h:14-15], [pyOpenMS workaround:306-331] |
| 1.4 | **Remove build options from SDK** | Strip `BUILD_TOPP_TOOLS`, `WITH_GUI` from OpenMSConfig.cmake.in; export core feature flags with package-specific names | [OpenMSConfig.cmake.in:78-82] |
| 1.5 | **Validate installed SDK** | Build small external consumer (use `src/tests/external/` as template) against installed core; verify Eigen/Arrow resolution | [src/tests/external/CMakeLists.txt] |
| 1.6 | **Test relocation** | Install core to `/tmp/core-install`, delete source tree, build consumer | Validates data/path discovery |

**Deliverable:** `find_package(OpenMS 4.0 CONFIG REQUIRED COMPONENTS Core)` works with namespaced targets.

### 🐍 Phase 2: Standalone pyOpenMS (Week 5-8, parallel with Phase 1)

**Goal:** Build pyOpenMS wheel against installed core SDK.

| **Task** | **Action** | **Files** | **Evidence** |
|---|---|---|---|
| 2.1 | **Pin core version** | Use exact version in pyOpenMS standalone build; record core artifact digest | [pyOpenMS/CMakeLists.txt:67] |
| 2.2 | **Fix Arrow discovery** | Remove pyOpenMS Arrow workaround; rely on core's PUBLIC Arrow dep | [pyOpenMS/CMakeLists.txt:306-331] |
| 2.3 | **Bundle vs. link decision** | Choose: (a) bundle core libs into wheel with NO_DEPENDENCIES=OFF, OR (b) require system install of OpenMS SDK | Currently supports both [pyOpenMS/CMakeLists.txt:28,406] |
| 2.4 | **Fix test fixture discovery** | Copy small owned fixtures into pyOpenMS OR publish hashed test-data artifact | [pyOpenMS/conftest.py:67], [pyOpenMS/CMakeLists.txt:516] |
| 2.5 | **Test wheel on clean runner** | Build wheel, install into clean Python env, run tests | Validates no source-tree pollution |

**Deliverable:** `pip install pyopenms` from wheel built against installed core.

### ⚡ Phase 3: Extract CLI Framework (Week 7-10)

**Goal:** Remove tool registry from core; CLI framework builds against installed core.

| **Task** | **Action** | **Files** | **Evidence** |
|---|---|---|---|
| 3.1 | **Create openms-cli package** | New repo/layout: `openms-cli/src/`, `openms-cli/CMakeLists.txt` | |
| 3.2 | **Move APPLICATIONS sources** | Move `src/openms/source/APPLICATIONS/` to `openms-cli/src/` | [sources.cmake] |
| 3.3 | **Remove ToolHandler from core** | Delete `ToolHandler.cpp/h`, update core CMakeLists | [ToolHandler.cpp], [src/openms/source/APPLICATIONS/sources.cmake] |
| 3.4 | **New CLI library** | `OpenMS::CLI` target with TOPPBase, parameter handling | |
| 3.5 | **New tool discovery** | Implement manifest-based `CLI::ToolResolver` | Replaces [File::findSiblingTOPPExecutable:851-880] |
| 3.6 | **Update TOPPBase version** | TOPPBase reports **both** product version AND linked core version | [TOPPBase.cpp:119-120] |
| 3.7 | **Extract one pilot tool** | Move FileInfo or similar to validate the boundary | [FileInfo.cpp] |
| 3.8 | **Test standalone tool** | Build tool with only installed core + CLI available | Tool compiles, runs, reports versions correctly |

**Deliverable:** `FileInfo` builds in `openms-cli` against installed `OpenMS::Core`.

### 🔨 Phase 4: Extract Executable Families (Week 9-14)

**Goal:** TOPP, FLASH, OpenSWATH as independent packages.

| **Family** | **Tools** | **Tasks** | **Dependencies** |
|---|---|---|---|
| **openms-topp** | 131 general tools | Move `src/topp/` to package, update CMake to link OpenMS::Core + OpenMS::CLI | [src/topp/CMakeLists.txt] |
| **openms-openswath** | 19 OpenSWATH tools | Move tools, keep OpenSwathAlgo in core | [executables.cmake:94-115] |
| **openms-flash** | FLASHDeconv | Move FLASHDeconv, update Python bindings reference | [FLASHDeconv.cpp], [bind_format.cpp:379] |

**Key changes per package:**
- Replace hardcoded tool lists with **package manifests**
- Each tool links `OpenMS::Core` + `OpenMS::CLI`
- Direct Boost/Eigen deps stay on tools that need them
- FuzzyDiff stays in TOPP for now (uses OpenMSTestFramework)

### 🖥️ Phase 5: Separate GUI (Week 12-16)

**Goal:** GUI library and viewers as independent packages.

| **Task** | **Action** | **Files** |
|---|---|---|
| 5.1 | **Create openms-gui package** | Move `src/openms_gui/` | [src/openms_gui/CMakeLists.txt] |
| 5.2 | **Move GUI tools** | TOPPView, ImageCreator, INIFileEditor to openms-viewers | [src/openms_gui/CMakeLists.txt:68-91] |
| 5.3 | **Create openms-workflows** | Move TOPPAS, ExecutePipeline | [src/openms_gui/CMakeLists.txt:94-101] |
| 5.4 | **Fix tool discovery** | GUI uses new CLI resolver instead of findSiblingTOPPExecutable | 7 GUI call sites to update |
| 5.5 | **Remove Qt from core** | Verify core consumers don't need Qt | Already done per proposal |

### 🌐 Phase 6: Web Apps (Week 15-18)

**Goal:** FLASHApp and other webapps consume released packages.

| **Task** | **Action** | **Target** |
|---|---|---|
| 6.1 | **Migrate FLASHApp** | Replace embedded OpenMS build with pinned pyopenms wheel + openms-flash executables | [FLASHApp/Dockerfile] |
| 6.2 | **Pin all dependencies** | Python wheel version, executable versions, container base | [FLASHApp/requirements.txt] |
| 6.3 | **Validate compatibility** | Check CLI/INI/output-schema compatibility during migration | |

### 🎯 Phase 7: Suite and Integration (Week 16-20)

| **Task** | **Action** |
|---|---|
| 7.1 | **Create openms-suite** | Distribution manifest with tested package version combinations |
| 7.2 | **CI matrix** | Core CI publishes artifacts; each consumer CI downloads pinned artifacts |
| 7.3 | **Integration tests** | Cross-package pipelines (e.g., TOPP tool → pyOpenMS processing) |

---

## 4. Subrepository Topology and Initial Contents

### 📁 Recommended Repository Structure

```
okohlbacher/
├── OpenMS4-tests/                    # THIS REPO - experiment coordination
│   ├── OpenMS4-package-architecture.md  # This proposal (live)
│   ├── OpenMS4-package-architecture.mmd
│   ├── subrepos/                      # Git submodules OR cloned repos
│   │   ├── openms-core/               # First extraction target
│   │   ├── pyopenms/                  # Standalone validation
│   │   └── ...
│   └── validation/                    # Source-level verification scripts
│       ├── check_boundaries.py
│       └── verify_sdk_contract.sh
│
├── openms-core/                      # Separate repo (Phase 1 target)
│   ├── src/                          # From OpenMS/src/openms (minus APPLICATIONS)
│   ├── cmake/                        # Minimal CMake for core
│   │   ├── OpenMSConfig.cmake.in     # Fixed: namespaced targets, no build options
│   │   └── ...                      # Only core-relevant modules
│   ├── include/OpenMS/               # Public headers (audited)
│   ├── share/OpenMS/                # Runtime data
│   └── tests/class_tests/           # Core unit tests only
│
├── openms-cli/                       # Separate repo (Phase 3)
│   ├── src/                          # From openms-core/src/APPLICATIONS
│   ├── include/OpenMS/              # CLI public headers (new)
│   └── tests/                        # CLI framework tests
│
├── openms-topp/                      # Separate repo
│   ├── src/                          # TOPP tool sources
│   └── tests/                        # TOPP integration tests
│
├── openms-flash/                     # Separate repo
│   └── src/FLASHDeconv/               # Single tool initially
│
├── openms-openswath/                 # Separate repo
│   └── src/                          # OpenSWATH executables
│
├── openms-gui/                      # Separate repo
│   ├── src/                          # GUI library sources
│   └── cmake/                        # Qt handling
│
├── openms-viewers/                   # Separate repo
│   └── src/                          # TOPPView, ImageCreator, INIFileEditor
│
├── openms-workflows/                 # Separate repo
│   └── src/                          # TOPPAS, ExecutePipeline
│
└── pyopenms/                        # Already has standalone path
    ├── src/pyOpenMS/                 # Existing
    └── pyproject.toml                 # Existing
```

### 📦 Exact Initial Contents per Repo (Phase 1-2 Focus)

**openms-core (Phase 1):**
```
From OpenMS @ ca32296:
src/openms/ (EXCLUDE source/APPLICATIONS/)
├── include/OpenMS/        # All headers MINUS MatrixEigen.h, ParquetFile.h
│                            # OR: keep them but fix Eigen/Arrow promotion
├── source/               # All sources MINUS APPLICATIONS/
├── extern/               # Vendored: SQLiteCpp, nlohmann_json, Evergreen, etc.
├── thirdparty/           # Percolator, IsoSpec, GTE, etc.
├── cmake/                # Core-only modules:
│   ├── OpenMSConfig.cmake.in (modified)
│   ├── setup_lib_find_paths.cmake
│   ├── compiler_flags.cmake
│   ├── multithreading.cmake
│   └── ... (only what core needs)
├── share/OpenMS/         # Runtime data
├── configh.cmake         # Version/config generation
├── includes.cmake        # Header/source lists (audited)
└── CMakeLists.txt         # Minimal core-only build

tests/class_tests/openms/  # Core unit tests MINUS PercolatorAdapter_parity_test
```

**Changes required in openms-core:**
1. Remove `APPLICATIONS/` from `includes.cmake` and `sources.cmake`
2. Fix `OpenMSConfig.cmake.in`: add Eigen/Arrow to PUBLIC deps
3. Remove `BUILD_TOPP_TOOLS`, `WITH_GUI` from config
4. Export `OpenMS::Core`, `OpenMS::OpenSwathAlgo` targets
5. Ensure all installed headers pass dependency audit

**pyopenms (Phase 2 - use existing repo or new standalone):**
```
From OpenMS/src/pyOpenMS:
├── bindings/            # Nanobind binding sources
├── pyopenms/            # Python package
├── tests/               # Python tests
├── CMakeLists.txt        # Use standalone path (already supports it)
├── pyproject.toml        # Existing
└── README_WRAPPING_NEW_CLASSES.md
```

**Changes required in pyopenms:**
1. Update CMakeLists.txt to expect namespaced `OpenMS::Core`
2. Remove Arrow workaround (lines 306-331) - rely on core's PUBLIC Arrow
3. Add exact core version pin in standalone mode
4. Fix test fixture paths (copy small fixtures OR use test-data artifact)

### 🔗 Source Duplication and Reproducible Pins

| **Concern** | **Solution** |
|---|---|
| **Header duplication** | Core repo contains canonical headers; consumers include via `find_package` |
| **CMake module duplication** | Each package has minimal CMake; avoid duplicating find modules |
| **Version pins** | Use triplet: `<version>+<git-commit>+<artifact-digest>` (e.g., `4.0.0+ca32296+sha256:abc123...`) |
| **Reproducible dependency baselines** | Record: platform, arch, compiler, C++ runtime ABI, build config, all native dep versions |
| **Submodule preservation** | In experiment repo, preserve `.gitmodules` but don't download contrib (large) |

**Pin format recommendation:**
```json
{
  "package": "openms-core",
  "version": "4.0.0-pre-experiment",
  "git_commit": "ca32296038839459d8c9b075b759e285913d6294",
  "artifact_digest": "sha256:...",
  "platform": "linux-x86_64",
  "compiler": "gcc-13.2",
  "stdcxx": "libstdc++6",
  "build_type": "Release",
  "shared_libs": true,
  "features": {
    "hdf5": false,
    "opentims": true,
    "thermo_raw": true,
    "wnetalign": false
  },
  "native_deps": {
    "boost": "1.85.0",
    "eigen": "3.4.0",
    "arrow": "15.0.0",
    ...
  }
}
```

---

## 5. Validation Without Compilation

### 🔍 Source/Configuration Verification (Can Run Now)

**Category A: Boundary Audits (greppable, no compilation needed)**

| **ID** | **Check** | **Command** | **Pass Criteria** | **Current Status** |
|---|---|---|---|---|
| A1 | No TOPP tool names in core library sources | `grep -r "AccurateMassSearch\|CometAdapter\|FeatureFinder" src/openms/include/ src/openms/source/ --exclude-dir=APPLICATIONS` | Only APPLICATIONS dir should have tool names | ❌ FAIL: ToolHandler has all names |
| A2 | No `findSiblingTOPPExecutable` in core | `grep -r "findSiblingTOPPExecutable" src/openms/` | Zero matches | ❌ FAIL: 1 match in File.cpp |
| A3 | `MatrixEigen.h` not in installed headers | Check `includes.cmake` for MatrixEigen.h in header lists | Not present OR Eigen promoted to PUBLIC | ❌ FAIL: Installed, Eigen not PUBLIC |
| A4 | `ParquetFile.h` not in installed headers | Same check | Not present OR Arrow promoted to PUBLIC | ❌ FAIL: Installed, Arrow not PUBLIC |
| A5 | No tool executable invocations in core tests | `grep -r "PercolatorAdapter\|TOPP" src/tests/class_tests/openms/` | Only data files, no executable paths | ❌ FAIL: PercolatorAdapter test |
| A6 | Core CMake doesn't reference TOPP/GUI | `grep -r "BUILD_TOPP_TOOLS\|WITH_GUI" src/openms/CMakeLists.txt` | Zero matches | ✅ PASS (options set in root) |
| A7 | OpenMSConfig.cmake.in exports namespaced targets | `grep "OpenMS::" cmake/OpenMSConfig.cmake.in` | At least `OpenMS::Core` | ❌ FAIL: No namespaced targets |
| A8 | pyOpenMS can find OpenMS via find_package | `grep "find_package(OpenMS" src/pyOpenMS/CMakeLists.txt` | Present and uncommented | ✅ PASS |
| A9 | External test uses find_package | `grep "find_package(OpenMS" src/tests/external/CMakeLists.txt` | Present | ✅ PASS |
| A10 | All public headers have OPENMS_DLLAPI | `grep -L "OPENMS_DLLAPI" src/openms/include/OpenMS/**/*.h` | Empty result (all have it) | ⚠️ PARTIAL: Templates may not need it |

**Category B: Dependency Closure Audits**

| **ID** | **Check** | **Command** | **Pass Criteria** |
|---|---|---|---|
| B1 | Eigen includes only in internal headers | `grep -r "#include.*Eigen" src/openms/include/OpenMS/` | Only internal/non-public headers |
| B2 | Arrow includes only in internal headers | `grep -r "#include.*arrow" src/openms/include/OpenMS/` | Same |
| B3 | Boost includes audit | `grep -r "#include.*boost" src/openms/include/OpenMS/` | Only headers that are truly public API |
| B4 | Xerces not in public API | `grep -r "Xerces" src/openms/include/OpenMS/` | Zero matches (encapsulated) |
| B5 | All `find_dependency` in SDK config are satisfied | Check each in OpenMSConfig.cmake.in | All target names exist |

**Category C: Packaging/Install Audits**

| **ID** | **Check** | **Command** | **Pass Criteria** |
|---|---|---|---|
| C1 | All installed headers listed explicitly | Check includes.cmake header variables | No globs, all explicit |
| C2 | Share data installed | `grep "install.*share/OpenMS" src/openms/CMakeLists.txt` | Present |
| C3 | CMake config installed | `grep "install.*OpenMSConfig" cmake/export_macros.cmake` | Present |
| C4 | No source files in install | `grep -r "install.*\\.cpp" src/openms/CMakeLists.txt` | Zero matches |

**Provided validation script (can run immediately):**

```bash
#!/bin/bash
# validation/check_boundaries.sh
REPO_ROOT="/Users/kohlbach/Claude/OpenMS/OpenMS4-Exploration/OpenMS4-tests"

echo "=== A1: Tool names in core (excluding APPLICATIONS) ==="
grep -r --include="*.h" --include="*.cpp" -L "AccurateMassSearch\|CometAdapter\|FeatureFinderCentroided" \
  "$REPO_ROOT/src/openms/include/" "$REPO_ROOT/src/openms/source/" \
  2>/dev/null | head -20

echo -e "\n=== A2: findSiblingTOPPExecutable in core ==="
grep -r "findSiblingTOPPExecutable" "$REPO_ROOT/src/openms/" || echo "PASS: None found"

echo -e "\n=== A3: MatrixEigen.h in install lists ==="
grep -r "MatrixEigen" "$REPO_ROOT/configh.cmake" "$REPO_ROOT/includes.cmake" || echo "Check manually in includes.cmake"

echo -e "\n=== A5: Percolator in core tests ==="
grep -r "PercolatorAdapter" "$REPO_ROOT/src/tests/class_tests/openms/"

echo -e "\n=== A7: Namespaced targets in config ==="
grep "OpenMS::" "$REPO_ROOT/cmake/OpenMSConfig.cmake.in" || echo "FAIL: No namespaced targets"

echo -e "\n=== B1: Eigen includes in public headers ==="
grep -r --include="*.h" "#include.*Eigen" "$REPO_ROOT/src/openms/include/OpenMS/"

echo -e "\n=== B2: Arrow includes in public headers ==="
grep -r --include="*.h" "#include.*arrow" "$REPO_ROOT/src/openms/include/OpenMS/"
```

### 🏗️ Compile/Integration Acceptance Tests (Require Build)

**Category D: Build-time Verification**

| **ID** | **Test** | **How to Run** | **Pass Criteria** |
|---|---|---|---|
| D1 | Core-only build configures | `cmake -DBUILD_TOPP_TOOLS=OFF -DWITH_GUI=OFF -DPYOPENMS=OFF ...` | Configures without error |
| D2 | Core-only build compiles | `cmake --build . -j` | libOpenMS builds |
| D3 | Core class tests pass | `ctest -R class_tests` | All core tests pass |
| D4 | Core installs cleanly | `make install DESTDIR=/tmp/core-install` | No errors, all files in expected locations |
| D5 | Installed SDK finds itself | Create minimal consumer, `find_package(OpenMS REQUIRED)` | Configures successfully |
| D6 | Consumer compiles against installed SDK | Build external_code example against installed core | Links and compiles |
| D7 | Consumer runs against installed SDK | Run external_code executable | Runs without missing symbols |
| D8 | pyOpenMS standalone configures | `cmake -DPYOPENMS=ON -DOPENMS_DIR=/tmp/core-install ...` | Finds OpenMS, configures |
| D9 | pyOpenMS standalone builds | `cmake --build . --target pyopenms` | All modules compile |
| D10 | pyOpenMS tests pass | `ctest -R pyopenms` | All Python tests pass |

**Category E: Runtime Verification**

| **ID** | **Test** | **Pass Criteria** |
|---|---|---|
| E1 | Relocated core works | Install core to /opt/openms-core, delete build tree, consumer still works |
| E2 | Version reporting | Tool reports both its version and linked core version |
| E3 | Tool discovery | Tools can find each other via new manifest system |
| E4 | Data file resolution | Core finds share/OpenMS data from any install location |
| E5 | ABI compatibility | Different build configs (Debug/Release) of same version are compatible |

### ✅ Explicit Distinction

| **Verification Type** | **What It Proves** | **What It Does NOT Prove** | **When to Run** |
|---|---|---|---|
| **Source/Config Audit (A-C)** | Boundaries are correctly drawn in code/CMake | Code compiles, tests pass, runtime works | Immediately, pre-implementation |
| **Build Verification (D1-D4)** | Core can be built independently | SDK is usable by consumers | After Phase 0 |
| **Install Verification (D5-D7)** | SDK can be installed and found | Full consumer pipelines work | After Phase 1 |
| **Standalone Consumer (D8-D10)** | pyOpenMS can use installed SDK | All TOPP tools work independently | After Phase 2 |
| **Runtime Verification (E1-E5)** | Installed artifacts are relocatable and compatible | Full distribution works | After Phase 1-2 |

**Critical:** Source audits **cannot substitute** for install/consumer tests. The proposal correctly notes: "Do not substitute building one tool target within the monorepo for proof of package independence."

---

## 6. Top Five Risks and Objections

### 🚨 Risk 1: Tool Registry in Core (CRITICAL)

**Description:** `ToolHandler::getTOPPToolList()` compiles a complete map of all 151 TOPP tools directly into libOpenMS. `TOPPBase` validates official tools against this list.

**Evidence:**
- `src/openms/source/APPLICATIONS/ToolHandler.cpp:18-207` — static initialization of all tools
- `src/openms/source/APPLICATIONS/TOPPBase.cpp:132` — runtime check `!ToolHandler::getTOPPToolList().count(tool_name_)`

**Impact:** Any new tool, tool removal, or independent tool release **requires core recompilation**. This fundamentally breaks the independence goal.

**Mitigation:**
1. **Short-term (Phase 3):** Remove `ToolHandler` from core; move to `openms-cli`
2. **Tool validation:** Change TOPPBase to accept a **tool manifest** from the CLI package instead of hardcoded list
3. **Version reporting:** TOPPBase reports its own version separately from core version
4. **Backward compatibility:** Keep `ToolHandler` in core temporarily with deprecation warning, but make it **opt-in** via a feature flag

**Residual risk:** Existing code that calls `ToolHandler::getTOPPToolList()` from non-TOPP contexts (e.g., INIUpdater in TOPP uses it). Must audit all callers.

### 🚨 Risk 2: Filesystem-Based Tool Discovery (CRITICAL)

**Description:** `File::findSiblingTOPPExecutable()` uses hardcoded relative paths that assume tools and consumers are co-located or in specific bundle layouts.

**Evidence:**
- `src/openms/source/SYSTEM/File.cpp:851-880` — probes `<executablePath>/<toolName>`, macOS bundle paths
- **7 call sites in GUI** (TOPPASToolVertex, TOPPASToolConfigDialog, GUIHelpers, TOPPViewBase, TOPPASScene)
- **2 call sites in TOPP** (ProSE.cpp, INIUpdater.cpp)
- **TODO comment at line 877:** "probe in PATH" — never implemented

**Impact:** **Cannot install tools and consumers into different prefixes.** This is the single biggest practical blocker.

**Mitigation:**
1. **New abstraction:** `CLI::ToolResolver` in `openms-cli` with:
   - Manifest file per package declaring provided tools
   - Search path configuration (OPENMS_TOOL_PATH environment variable)
   - Version compatibility checking
   - Fallback to PATH lookup
2. **Replace all call sites** with new resolver
3. **Backward compatibility:** Keep old function but deprecate; emit warning on use

**Residual risk:** Bundle layouts on macOS may still need special handling. The new system must support:
   - Standard install prefixes
   - macOS .app bundles
   - Portable/zip distributions
   - Containerized deployments

### ⚠️ Risk 3: Public Headers Expose Private Dependencies (HIGH)

**Description:** Installed public headers include Eigen and Arrow, but core's CMake lists these as PRIVATE dependencies.

**Evidence:**
- `MatrixEigen.h:16` — `#include <Eigen/Core>` in INTERNAL header that is **installed**
- `ParquetFile.h:14-15` — `#include <arrow/api.h>` in public header
- `OpenMSConfig.cmake.in:47-54` — Eigen/Arrow discovery commented out
- pyOpenMS must manually rediscover Arrow (`src/pyOpenMS/CMakeLists.txt:306-331`)

**Impact:** Consumers of the SDK will fail to compile unless they independently find Eigen and Arrow.

**Mitigation Options:**

| **Option** | **Pros** | **Cons** | **Recommendation** |
|---|---|---|---|
| A. Promote Eigen/Arrow to PUBLIC | Simple, honest | Forces Eigen/Arrow on all consumers | ✅ **Recommended for Eigen** (already leaks) |
| B. Remove MatrixEigen.h from install | Clean separation | Breaks any consumer using it | ⚠️ Requires deprecation period |
| C. Hide Arrow types behind PIMPL | Clean ABI | Major refactor of ParquetFile | ❌ Too invasive for Phase 1 |
| D. Add Eigen/Arrow to SDK config | Fixes immediate problem | Doesn't address header audit | ✅ **Recommended as Phase 1 fix** |

**Phase 1:** Add Eigen and Arrow to `OpenMSConfig.cmake.in` PUBLIC dependencies.
**Phase 2:** Audit all installed headers for private includes; remove or PIMPL-wrap.
**Phase 3:** Consider splitting core into `openms-core` (no Eigen/Arrow) and `openms-core-ext` (with).

**Residual risk:** Other headers may have similar issues. Need comprehensive audit.

### ⚠️ Risk 4: Test Ownership Leakage (HIGH)

**Description:** Core tests invoke TOPP tools and depend on TOPP fixtures.

**Evidence:**
- `PercolatorAdapter_parity_test` in core class tests invokes `PercolatorAdapter` executable
- Test path set to `${CMAKE_BINARY_DIR}/bin/PercolatorAdapter` even when `BUILD_TOPP_TOOLS=OFF`
- pyOpenMS tests discover fixtures from TOPP and core test directories

**Impact:** Core cannot be tested in environments without TOPP tools built.

**Mitigation:**
1. **Immediate (Phase 0):** Move `PercolatorAdapter_parity_test` to TOPP integration tests
2. **Phase 2:** Move all TOPP-dependent tests out of core
3. **Phase 2:** Copy small owned fixtures into pyOpenMS OR publish test-data artifact
4. **CI:** Core CI runs **only** core unit tests; integration tests in consumer packages

**Residual risk:** Some core functionality may legitimately need to invoke tools (e.g., file format round-trip tests). These should be **explicitly gated** on tool availability.

### ⚠️ Risk 5: CMake Config Pollution (MEDIUM)

**Description:** `OpenMSConfig.cmake.in` exports build options (`BUILD_TOPP_TOOLS`, `WITH_GUI`) that control consumer behavior.

**Evidence:**
- `OpenMSConfig.cmake.in:78-82` — sets `BUILD_TOPP_TOOLS`, `WITH_GUI`, `WITH_HDF5`, etc.
- These are **build-time options** for OpenMS itself, not runtime features of the SDK
- Consumers don't want OpenMS's build options affecting their configuration

**Impact:** Consumer builds may be affected by OpenMS build configuration. Violates separation of concerns.

**Mitigation:**
1. **Phase 1:** Remove all build option exports from OpenMSConfig.cmake.in
2. **Replace with:** Core feature metadata with package-specific names:
   ```cmake
   set(OpenMS_HAS_HDF5 @WITH_HDF5@)
   set(OpenMS_HAS_OPENTIMS @WITH_OPENTIMS@)
   ```
3. **Feature flags:** Export as cache variables that consumers can override:
   ```cmake
   set(OpenMS_HAS_HDF5 @WITH_HDF5@ CACHE BOOL "OpenMS was built with HDF5 support")
   ```

**Residual risk:** Some consumers may depend on current behavior. Need deprecation period.

---
---
---

## 📌 Summary and Recommendations

### ✅ What the Proposal Gets Right

1. **Core SDK as the boundary** — Correct fundamental insight
2. **Existing seams** — Accurately identifies `BUILD_TOPP_TOOLS=OFF`, Qt removal, OpenSwathAlgo separation
3. **pyOpenMS standalone path** — Already exists and is the best first validation
4. **Phase ordering** — SDK first, then CLI, then tools, then GUI — correct dependency order
5. **Version pinning requirements** — Triple pin (version + commit + digest) is necessary

### 🎯 What Must Change for Success

| **Priority** | **Action** | **Timeline** |
|---|---|---|
| **P0 (Blocker)** | Extract CLI framework (APPLICATIONS/) from core; remove ToolHandler | Phase 3 |
| **P0 (Blocker)** | Replace `findSiblingTOPPExecutable` with manifest-based discovery | Phase 3 |
| **P0 (Blocker)** | Fix PercolatorAdapter test ownership | Phase 0 |
| **P1 (Critical)** | Promote Eigen to PUBLIC SDK dependency OR remove MatrixEigen.h from install | Phase 1 |
| **P1 (Critical)** | Same for Arrow (via ParquetFile.h) | Phase 1 |
| **P1 (Critical)** | Remove build options from OpenMSConfig.cmake.in | Phase 1 |
| **P2 (High)** | Export namespaced targets (`OpenMS::Core`) | Phase 1 |
| **P2 (High)** | Audit all installed headers for private dependency includes | Phase 1-2 |
| **P2 (High)** | Move all tool-dependent tests out of core | Phase 2 |
| **P3 (Medium)** | Fix data file discovery to be install-path independent | Phase 1 |

### 🏆 First Experiment (Proves the Concept)

**Target:** Standalone pyOpenMS build against installed core SDK.

**Steps:**
1. Fix core SDK install (Phase 1 tasks P1)
2. Install core to a clean prefix
3. Configure pyOpenMS standalone with `OpenMS_DIR=<install-prefix>`
4. Build pyOpenMS
5. Run pyOpenMS tests

**Success criteria:**
- pyOpenMS builds without OpenMS source tree
- pyOpenMS tests pass (with copied fixtures)
- Consumer can import and use pyopenms

**If this succeeds:** The core boundary is proven. All other extractions build on this foundation.

**If this fails:** The SDK contract is still broken; don't proceed to CLI extraction.

### 📦 Subrepository Topology Recommendation

**Start with 2 repos in okohlbacher/OpenMS4-tests:**
1. `openms-core/` — For Phase 1 SDK validation
2. `pyopenms/` — Fork or mirror of existing, configured for standalone build

**Add repos incrementally:**
3. `openms-cli/` — After core SDK proven
4. `openms-topp/`, `openms-flash/`, `openms-openswath/` — Parallel extraction
5. `openms-gui/`, `openms-viewers/`, `openms-workflows/` — After CLI proven

**Keep as submodules** in OpenMS4-tests for coordination, OR use **git subtrees** for simpler history tracking.

### 🔄 Recommended Iteration Model

1. **Experiment in OpenMS4-tests** with the full source history
2. **Validate each phase** with source audits AND compile tests
3. **Create standalone repos** only after validation passes
4. **Use immutable artifacts** with full provenance for each phase

**Do NOT:**
- Create empty scaffold repos
- Move code without validation
- Assume header audit is complete without checking
- Skip the pyOpenMS standalone proof

### 🎯 Final Assessment

The proposal is **architecturally sound** and identifies the correct boundaries. The **implementation will succeed** if:

1. The **two critical blockers** (tool registry in core, filesystem discovery) are addressed **before** any code moves
2. The **SDK contract** (namespaced targets, public dependencies) is fixed **first**
3. Each phase is **validated with real builds** against installed artifacts
4. **Source audits** are used to guide but not replace compile/integration tests

**Estimated effort:** 4-6 months for full decomposition with a team of 2-3, assuming Phase 1-2 validation succeeds quickly.

**Biggest unknown:** The scale of header audits (MatrixEigen.h, ParquetFile.h, and potentially others) may reveal more coupling than anticipated. A comprehensive header-by-header audit should be the **first concrete task** after this review.
