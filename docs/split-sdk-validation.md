# Split SDK validation — 2026-09-11

The complete native package graph at parent `e548e405d55f374f548cdee62be6e13740ea1abe` was freshly checked out
from GitHub and built in Release on IBMI dax. Every consumer used installed Core
`82ce5b373c97f934ffd9b1ffd80215ca66473d0b`. No Core source/build-tree fallback or
scientific reference/tolerance change was needed.

Core's build system now uses native CMake unity support, a small Debug/Release
preset pair, and installed SDK acceptance. Obsolete suite installers, Jenkins and
KNIME helpers were removed. Unused Boost dependencies and the ineffective custom
Windows architecture checker were removed. macOS dependency discovery now prefers
normal libraries over legacy frameworks. Windows binaries and tests share the
normal runtime output directory instead of copying third-party DLLs. MSVC compiles
as UTF-8 so XML handling preserves Unicode characters. Core and the independent
test framework share one standard-library-only numeric formatter, including the
Intel macOS extended-long-double fix. The Core repository has a five-platform
GitHub Actions matrix and a release workflow that republishes the exact tested
SDK archives after checking their hashes and full source identities.

Eleven consumer repositories use the existing synchronized CMake helper for tool
installation, registries and INI/CTD metadata tests. Backend targets and scientific
tests remain explicit in each package. All 16 consumer locks follow the new Core
graph, including FLASHApp. The [native runner](build-split-packages.md) reproduces
the dependency order, builds, package tests and installed numerical suite.

## Linux native results

Dax had 384 logical CPUs, approximately 2.1 TiB available memory and load 6.34
(0.02/core) at selection. Builds used up to 320 compilation jobs, four concurrent
consumer builds, and up to 128 CTest jobs. The environment used GCC 14.4, shared
Core/Boost, Arrow 23.0.1, Eigen 5.0.1, COIN, Qt 6.10.1, Python 3.12 and nanobind
2.10.0. Optional instrument/ONNX/HDF5 integrations and interactive/WebEngine
desktop tests were disabled; OpenMP and OpenSWATH were enabled.

Core rebuilt in **6.93 seconds** after the Windows test and acceptance changes and
passed **701/701** tests in **22.46 seconds**. This is an incremental rebuild;
the earlier clean Core build at `39975e5` took 91.19 seconds.
Installed and relocated SDK consumers passed, including rejection of a wrong
source pin, in **17.24 seconds**. A separate installed desktop consumer passed
all nine resource, viewer, image and pipeline checks in **0.98 seconds**.

A separate clean build at preceding Core revision `74526a8`, before the Windows
test/CI-only changes, with both
`ENABLE_CLASS_TESTING=OFF` and `OPENMS_BUILD_TEST_SUPPORT=OFF` completed in
**83.67 seconds**. Installed and relocated consumer checks passed in **14.44
seconds**, confirming Core remains independent of the test framework.

| Package | Clean build, seconds | Package tests |
| --- | ---: | --- |
| cli | 9.20 | 9 CTest entries in 0.13 s |
| test-data | 0.03 | Fixtures installed |
| topp | 16.76 | 242 CTest entries in 0.91 s |
| openswath | 12.82 | 38 CTest entries in 0.23 s |
| flash | 12.24 | 9 CTest entries in 59.78 s |
| desktop | 33.84 | 10 CTest entries in 0.77 s |
| pyopenms | 66.21 | 4 CTest entries in 10.88 s |
| nuxl | 20.09 | 13 CTest entries in 0.24 s |
| prose | 17.67 | 3 CTest entries in 7.11 s |
| nase | 13.16 | 2 CTest entries in 0.11 s |
| comet | 7.79 | 3 CTest entries in 0.15 s |
| mascot | 4.85 | 4 CTest entries in 1.74 s |
| database-suitability | 10.74 | 4 CTest entries in 0.38 s |
| proteomics-lfq | 13.05 | 3 CTest entries in 0.11 s |
| parquet-diff | 6.45 | 3 CTest entries in 0.10 s |

The complete fresh consumer build/test/install run took **180.73 seconds**.

The installed console suite registered 2,041 tests across 150 tools:
**2,036 passed, five existing skips, zero failures**, in **10.71 seconds**.
The retained skips are the inherited MSGFPlus, Sage, Comet and MSFragger
missing/failing-engine cases. External proprietary services/engines were not
provisioned.

The four pyOpenMS groups contain **5,749 passed, 92 skipped, 10 xfailed and seven
xpassed** tests. Installed Python additionally verified loaded Core, ProSE and
FLASH paths and hashes, clean pinned provenance, runtime data and absence of CLI
or GUI libraries. Provider source IDs are build metadata; runtime paths/hashes
identify actual loaded files without independently attesting their source.

These are single Release build/test wall times, not statistical benchmarks.
They are not directly comparable with the earlier Debug measurements or builds
at different parallelism. Concurrent component durations cannot be summed.

## FLASHApp and hosted validation

FLASHApp's old OpenMS 3.5 Windows installers and unrelated template workflow were
removed. Its artifact checks and ordinary dependency tests now run on the current
branch under an allowlist of three exact GitHub action commits. Both jobs passed
in [run 34571043061](https://github.com/okohlbacher/OpenMS4-flashapp/actions/runs/34571043061).
The ordinary hash-pinned dependencies also installed and passed `pip check` in an
isolated Linux environment. The real `DeconvWorkflow.execution` path passed in
**2.17 seconds** using the new SDK: INI creation/pyOpenMS parameter parsing,
persisted settings, native FLASHDeconv and FuzzyDiff execution, cached mzML/table
parsing, and expected missing-input failure propagation. Four scan rows and four
mass-table rows were produced, and all 18 scientific reference columns matched.
This ran app source `941ac78e18313296d01dc4320b6b11e1cfed60d5` with the
committed `tools/test_flashapp_deconvolution.py` acceptance driver.
Bare Streamlit context and input native-ID warnings remain in the evidence.
A full image/tagging workflow still requires the
separately pinned external FLASHTnT implementation; updating source locks does not
manufacture that binary.

Core's [five-platform run](https://github.com/okohlbacher/OpenMS4-core/actions/runs/34565642540)
at `82ce5b373c97f934ffd9b1ffd80215ca66473d0b` has passed on Linux and macOS,
both x64 and arm64. Each passed all 701 scientific tests and installed/relocated
SDK acceptance. The four downloaded SDK archives match their SHA-256 checksums
and full clean source identities. Windows is still running at this evidence
capture; no release is published yet.

| Platform | Clean build, seconds | 701 tests, seconds | Extracted/relocated SDK, seconds |
| --- | ---: | ---: | ---: |
| linux-arm64 | 1777.25 | 31.83 | 18.98 |
| linux-x64 | 2429.58 | 50.02 | 20.74 |
| macos-arm64 | 1666.81 | 97.98 | 28.48 |
| macos-x64 | 3011.34 | 241.27 | 90.14 |

An earlier Windows run passed all 701 scientific tests but its relocated Parquet
SDK probe exited with `0xc0000409`. Core CI now retains failed SDK archives,
prints probe stages and runs the Windows probe 50 consecutive times per prefix,
stopping on the first failure. A separate diagnostic branch can reuse the actual
Windows archive with the original quiet probe for 1,000 runs per prefix. These
are diagnostic and regression checks, not an established root-cause fix. The
independent Arrow-only comparison programs did not reproduce the failure.

## Evidence

Exact commands, source pins, test counts and Python summaries are recorded in
[the machine-readable report](split-sdk-validation.json). Raw JUnit files and logs
are retained in the local evidence
archive `split-sdk-execution/evidence-release.tar.gz` in the exploration workspace;
SHA-256 `8e0001de63987f2dcff96ec690bce330291be1e28da0fd57d4200ed32c8b6d7a`.
Scratch sources, installed products and raw logs are under
`/scratch/kohlbach/openms4-split-sdk-20260910` on dax. The original installed Core
and dependency environment were not overwritten. Runtime dependencies are
external; no repaired portable wheel or self-contained product installer is
claimed by this integration run.
