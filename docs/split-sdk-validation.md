# Split SDK validation — 2026-09-10

The complete native package graph at parent `a5b67b7f79` was freshly checked out
from GitHub and built in Release on IBMI dax. Every consumer used installed Core
`74526a865953865d61321482bafbececfc7e0b9f`. No Core source/build-tree fallback or
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

Dax had 384 logical CPUs, approximately 2.1 TiB available memory and load 7.97
(0.02/core) at selection. Builds used up to 320 compilation jobs, four concurrent
consumer builds, and up to 128 CTest jobs. The environment used GCC 14.4, shared
Core/Boost, Arrow 23.0.1, Eigen 5.0.1, COIN, Qt 6.10.1, Python 3.12 and nanobind
2.10.0. Optional instrument/ONNX/HDF5 integrations and interactive/WebEngine
desktop tests were disabled; OpenMP and OpenSWATH were enabled.

Core rebuilt in **63.41 seconds** after the shared formatter/header change and
passed **701/701** tests in **22.44 seconds**. This is an incremental rebuild;
the earlier clean Core build at `39975e5` took 91.19 seconds.
Installed and relocated SDK consumers passed, including rejection of a wrong
source pin, in **17.48 seconds**. A separate installed desktop consumer passed
all nine resource, viewer, image and pipeline checks in **0.97 seconds**.

A separate clean build of the same Core revision with both
`ENABLE_CLASS_TESTING=OFF` and `OPENMS_BUILD_TEST_SUPPORT=OFF` completed in
**83.67 seconds**. Installed and relocated consumer checks passed in **14.44
seconds**, confirming Core remains independent of the test framework.

| Package | Clean build, seconds | Package tests |
| --- | ---: | --- |
| cli | 9.26 | 9 CTest entries in 0.13 s |
| test-data | 0.03 | Fixtures installed |
| topp | 17.03 | 242 CTest entries in 0.90 s |
| openswath | 12.86 | 38 CTest entries in 0.23 s |
| flash | 12.16 | 9 CTest entries in 57.24 s |
| desktop | 33.62 | 10 CTest entries in 0.75 s |
| pyopenms | 62.58 | 4 CTest entries in 10.98 s |
| nuxl | 19.30 | 13 CTest entries in 0.25 s |
| prose | 17.75 | 3 CTest entries in 7.14 s |
| nase | 13.11 | 2 CTest entries in 0.12 s |
| comet | 7.84 | 3 CTest entries in 0.17 s |
| mascot | 4.85 | 4 CTest entries in 1.76 s |
| database-suitability | 10.70 | 4 CTest entries in 0.41 s |
| proteomics-lfq | 13.05 | 3 CTest entries in 0.11 s |
| parquet-diff | 6.45 | 3 CTest entries in 0.11 s |

The complete fresh consumer build/test/install run took **174.67 seconds**.

The installed console suite registered 2,041 tests across 150 tools:
**2,036 passed, five existing skips, zero failures**, in **10.57 seconds**.
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
in [run 34529420192](https://github.com/okohlbacher/OpenMS4-flashapp/actions/runs/34529420192).
The ordinary hash-pinned dependencies also installed and passed `pip check` in an
isolated Linux environment. The real `DeconvWorkflow.execution` path passed in
**2.08 seconds** using the new SDK: INI creation/pyOpenMS parameter parsing,
persisted settings, native FLASHDeconv and FuzzyDiff execution, cached mzML/table
parsing, and expected missing-input failure propagation. Four scan rows and four
mass-table rows were produced, and all 18 scientific reference columns matched.
This ran app source `43335129e513b66374c7f4beeb52f5c54e40d959` with the
committed `tools/test_flashapp_deconvolution.py` acceptance driver.
Bare Streamlit context and input native-ID warnings remain in the evidence.
A full image/tagging workflow still requires the
separately pinned external FLASHTnT implementation; updating source locks does not
manufacture that binary.

Core's [five-platform run](https://github.com/okohlbacher/OpenMS4-core/actions/runs/34529087385)
was still running when this Linux evidence was recorded. Hosted macOS/Windows/ARM
success and release deployment must be recorded separately after completion.
The Linux results above are not a claim that those platforms have passed.

## Evidence

Exact commands, source pins, test counts and Python summaries are recorded in
[the machine-readable report](split-sdk-validation.json). Raw JUnit files and logs
are retained in the local evidence
archive is `split-sdk-execution/evidence-portable.tar.gz` in the exploration workspace;
SHA-256 `87766d7f84a294645afb74795d71343bb9297b89d3bba217c95542bf5d8f0222`.
Scratch sources, installed products and raw logs are under
`/scratch/kohlbach/openms4-split-sdk-20260910` on dax. The original installed Core
and dependency environment were not overwritten. Runtime dependencies are
external; no repaired portable wheel or self-contained product installer is
claimed by this integration run.
