# Implementation of the adversarial refactoring plan

The nine package boundaries are retained. Core, CLI, TOPP, OpenSWATH, FLASH and
desktop now build independently from pinned installed SDKs. The implementation
adds runtime source/build identity, strict artifact checks, meaningful numerical
and lifecycle tests, and removes disconnected build/packaging code.

This report follows the [review and six-phase plan](../reviews/2026-09-10-implementation-adversarial/refactoring-plan.md).
The [parent lock](../../packages.lock.json) identifies the selected package commits.
The earlier [709-test Core report](../core-native-validation.md) remains historical
evidence; the results below validate the changed implementation.

## Accepted findings and changes

| Findings | Implemented change |
| --- | --- |
| A01, A02 | TOPP uses imported Core dependency targets. CLI, tools and desktop use install-relative library paths. Native builds used Eigen 5.0.1. Windows DLL co-location and separately installed Unix prefixes are documented. |
| A03 | Loaded Core exposes its full source revision, dirty state and JSON build identity. Clean-source builds reject changed HEAD/untracked inputs before compilation. Python records its own commit and checks the loaded Core before importing scientific domain modules. App verification checks hashes, native architecture, expected executables and embedded package/ABI metadata. |
| A04, A05 | Arrow imports the complete stream, preserving empty schemas and all batches. Runtime wheel staging excludes tests/examples even after reusing contaminated staging. Retired packaging scripts were removed. |
| A06 | FLASH class tests use real `report_FDR` and `merging_method` options and assert observable effects. The tool has a numerical comparison with an independently executed pre-refactor Core baseline. |
| A07–A09 | FLASHApp uses a bounded executor, observes exceptions/nonzero statuses, drains output to EOF and bounds diagnostic buffering. Cleanup reaps owned processes; cancellation verifies process creation identity. Reader-failure deadlock and lost-enqueue-acknowledgement regressions are covered. |
| A10 | `tools.json` is the single source for executable registration/category metadata. Missing/duplicate entries fail configuration, file changes trigger reconfiguration, and XML tests verify emitted version/category. |
| A11 | Registry failures become controlled startup diagnostics and library exceptions. Ambiguous registries remain errors. User TTD extensions remain supported; their initialization uses a directly initialized static value. No speculative global registry cache was introduced. |
| A12 | Consumer helpers have one parent-owned implementation with generated standalone copies and drift checks. The parent launches the app's canonical artifact verifier. Obsolete Core modules and Python packaging paths were retired with provenance retained. |
| A13, A14 | VersionInfo initialization uses `static const`. The unused testing-hook flag is removed; class-test configuration is named accurately and recorded separately from ABI compatibility. |
| A15 | Both TestSupport discovery paths require an owned fixture sentinel. Compiler-free fixture discovery and installed regression registration remain independent of native dependency discovery. |
| A16 | Queue lookups/uncertain submissions preserve job IDs. False/empty worker results fail, worker limits are explicit, and an uncertain enqueue never starts duplicate local work. |
| A17 | Core agent notes and active package entry-point documentation were rewritten. Desktop owns its embedded stylesheet/application metadata. FLASHApp Compose/Docker inputs use verified artifacts and a tested hash lock for 55 ordinary Python dependencies. |

## Native validation matrix

All native results here are **macOS arm64**, AppleClang 21, C++23. Dependencies
include shared Boost 1.90, Eigen 5.0.1, Arrow/Parquet 25.0.0, CURL 8.21 and OpenMP.
Core's minimum is CMake 3.21; consumer entry points require 3.24. Optional readers,
downloaded models, HDF5 and WNet are disabled in the tested Core profile.

| Profile | Actual result |
| --- | --- |
| Core Debug, class tests + TestSupport | **712/712 CTests passed**, 1309.82 s. The corrected FLASH test takes 1309.06 s because FDR/merging branches now execute. |
| Installed Debug Core | **8/8 checks at both original and relocated prefixes**, including loaded identity, public Eigen/Arrow APIs, mzML/Parquet round trips, chemistry/data lookup, invalid override and TestSupport. Wrong source pin rejected for the intended reason. |
| Core Release, no TestSupport/class tests | Independent build succeeded; **7/7 external SDK checks at both original and relocated prefixes**. This is Release SDK/API evidence, not a Release run of all scientific class tests. |
| CLI | Library and all test executables built; **9/9 native tests passed**, including duplicate/unreadable registries, controlled startup and emitted version behavior. |
| TOPP | **130 enabled executables built; 258/258 XML metadata tests passed**. Optional FeatureLinkerWNet is excluded by the tested SDK feature profile. |
| OpenSWATH | **19 executables built; 38/38 metadata tests passed**. |
| FLASH | Executable, INI/CTD checks and sample processing passed. Numerical comparison passes all 18 columns against the independently run pre-refactor Core reference. |
| Installed numerical suite subset | **53/53 tests passed**, including six exact-status/diagnostic invalid-parameter cases and FileInfo/PeakPickerHiRes output comparisons through FuzzyDiff. The entire preserved suite was registered, not exhaustively executed. |
| Desktop, WebEngine disabled | GUI, standalone viewers and standalone workflows built. **5/5 GUI class tests**, **4/4 ImageCreator tests** including exact BMP comparisons, and the installed pipeline passed. |
| Relocated desktop | Ten checks passed with source/build/original SDK reads denied: control denial, five launches, stylesheet startup with invalid Core-data override, two exact images and a pipeline. Loaded OpenMS libraries came from the relocated copy. Qt/native dependencies remain external. |
| Python wheel | **5,745 passed, 92 skipped, 10 expected failures, 7 unexpected passes**; complete 5,854-case suite exited successfully in 65.57 s. Original source/build/SDK/Homebrew reads were denied and developer loader/data overrides were absent. Existing skip/expected-failure markers remain unchanged. [Wheel report and limits](evidence/pyopenms-native-validation.md). |
| Relocated native runtime | All **150 tool startups**, eight selected INI/CTD checks, scientific comparisons and loaded Core/data checks passed with source/build/SDK/Homebrew reads denied. The final archive passed extraction and execution with the assembled prefix also denied. [Runtime evidence](../runtime-product-validation.md). |
| FLASHApp | **72 controlled tests + 46 subcases passed**, followed by **13 numerical parser tests**. A real `DeconvWorkflow` completed using the final wheel and relocated tools, matched 18 FLASH output columns, and propagated the intended missing-input failure. Hash-locked dependency install, imports and dataframe/parquet exchange also passed. See [controlled-test coverage](../../packages/flashapp/experimental/validation/README.md) and [real workflow evidence](evidence/flashapp-real-deconv-validation.md). |

The final source/configuration run passed 113 unit/source checks plus the Python
CMake acceptance scenarios; generated helper copies and all nine staged package
pins matched.

Raw Core/CLI/tool logs, installed-consumer command records and negative identity
fixtures are retained under [evidence](evidence/). Further binary qualification
records describe their exact sandbox/loader environments; copied SDK relocation
alone does not establish that external dependency libraries are bundled.

The final Python artifact is `pyopenms-4.0.0.dev0-cp312-cp312-macosx_26_0_arm64.whl`
(76,792,572 bytes), Python source `14d950a460636b9a8fa255b7ac657926fec403de`,
Core source `4fdec46b205459b92e7d3b9e56df5d8e912d5c85`, both clean.
Its SHA256 is `9a2150e096b7acc06562e63ee2081cdbee138b0efedcc09d756e5f8b94bdef9d`.
The repaired deployment tag reflects the actual bundled dependencies: this
artifact requires macOS 26 arm64 and CPython 3.12. The
[artifact record](evidence/pyopenms-final-wheel-artifact.json) records its 15 native
extensions and 130 bundled libraries. No Linux/Windows wheel is implied.

The native artifact is `openms4-tools-macos-arm64.tar.gz` (82,818,555 bytes),
SHA256 `16260f281af804ec8b4102c5b3203d0d250f1d1fe6245fcfb096174439ff7bb1`.
It contains the 150 selected executables, Core/CLI libraries, 128 dependency
libraries and runtime data; it requires macOS 26 arm64. All 281 distributed
native files passed strict ad-hoc signature verification. The installation
receipt checks exact source pins and installed bytes before dependency repair.
This is a trusted local incremental-builder record, not signed provenance or
proof against changes to the compiler/build tree. See the [runtime report](../runtime-product-validation.md)
for the receipt, extraction checks and reproduction commands. Neither binary
artifact is committed to Git.

The real FLASHApp workflow exposed an inherited plotting failure when all
scores were identical. Density estimation now returns the existing empty-curve
schema for fewer than two distinct finite scores and preserves the SciPy result
for variable scores. The final workflow ran without developer loader/data
overrides; source/Homebrew denial was established separately by the native and
wheel qualification gates, not by the app run itself.

## Numerical and lifetime evidence

The archived FLASH TSV was stale relative to the selected pre-refactor Core.
Both retained Core `21b295c9ad889b402db1e3a20f13e8d08330b61b` and refactored Core
`4fdec46b205459b92e7d3b9e56df5d8e912d5c85` report the same 8994.536888 Da,
charge-8 feature. The older archived TSV instead reports 17989.073405 Da at
charges 15–17 and predates the current writer's time/score conventions.
No tolerance was increased. The archived file remains untouched; the package
owns a documented equivalence reference with a real old-library load trace and
[binary/input/source hashes](evidence/flash-numerical-provenance.json).
This establishes refactoring equivalence for that input, not biological accuracy.

The compatible wrong-Core fixture reuses the actual Core object set and replaces
only VersionInfo's generated identity. It passes its own identity check and
fails against the expected Core identity with the specific contract status.
This is stronger than a configuration-only pin test or an unrelated loader failure.
Its [reproduction script](evidence/make_identity_fixture.py) and
[results](evidence/wrong-core-identity/results.json) preserve the negative control.

ThreadSanitizer and ASan/UBSan passed for the **actual production VersionInfo
translation unit** and a concurrent fresh-process probe. Coverage with atomic
counters measured 69/99 lines and 7/40 branches across that complete translation
unit; all six changed identity/time/version methods execute. Legacy parsing and
comparison error branches are outside this probe. Other Core/dependency objects
were not instrumented. [Commands, coverage and limits](evidence/versioninfo/README.md)
are retained; this is not a whole-SDK race/leak claim.

The production Arrow conversion helper passed four real empty/multi-batch,
failure/recovery and ownership tests, repeated under ASan/UBSan. Core Arrow 25
interoperates with PyArrow 23.0.1 through the C Data Interface. The separately
installed Arrow/Python binaries were not instrumented, and Darwin leak detection
was disabled. FLASHApp reports exact uncovered lines/branches rather than
inferring coverage from test counts.

## Remaining publication gates and limitations

- Linux/Docker validation could not run: the local Docker daemon returned HTTP
  500 to information/image queries. Windows is unavailable. No Linux leak-check,
  Windows ABI/DLL/path result or lowest-supported-dependency result is claimed.
- The GNU STL-debug profile needs a mixed-configuration gate: its exported debug
  definition currently follows consumer configuration. Only matching SDK/consumer
  configurations are supported by these recipes; arbitrary GNU Debug/Release
  mixing has not been established. The tested macOS profile has STL debug off.
- Release SDK checks passed, but Release tools/wheels, all optional readers/models,
  WebEngine-enabled GUI, installer/signing/notarization and full numerical suite
  coverage remain separate profiles. Developer SDK tests needed this host's old
  Abseil runtime because Homebrew re2 references it; the repaired wheel and
  native runtime passed without that environment override.
- FLASHApp still needs a compatible **FLASHTnT** binary/version and a matching
  Linux runtime/wheel pair for complete image/TagWorkflow acceptance. Its external source
  is identified separately from the nine package pins; no compatible binary or
  version is invented. Image assembly deliberately rejects an incomplete lock.
- Queue tests use fakeredis and real controlled children, not a live Redis/RQ
  deployment. The hard-kill interval between spawning a subprocess and recording
  ownership remains a live-worker acceptance gate. No universal orphan-free or
  leak-free claim is made.
- Full installed products retain strict duplicate-registry rejection. After
  installing a product beside CLI, qualify that installed executable rather than
  simultaneously exposing its build-tree and installed copies as two registries.

The experiment remains private, with Actions disabled. Tested source commits and
artifact hashes are reviewable inputs for the remaining publication gates, not
an assertion that every platform/package combination is release-ready.
