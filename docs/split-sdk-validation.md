# Split SDK validation — 2026-09-10

The complete native package graph at parent `c4f04c8e25` was freshly checked out
from GitHub and built in Release on IBMI dax. Every consumer used installed Core
`ff5345c68d16004fbca287fb68efb741b2ac8fcc`. No Core source/build-tree fallback or
scientific reference/tolerance change was needed.

Core's build system now uses native CMake unity support, a small Debug/Release
preset pair, and installed SDK acceptance. Obsolete suite installers, Jenkins and
KNIME helpers were removed. Unused Boost dependencies and the ineffective custom
Windows architecture checker were removed. macOS dependency discovery now prefers
normal libraries over legacy frameworks. The Core repository has a five-platform
GitHub Actions matrix and a release workflow that republishes the exact tested
SDK archives after checking their hashes and full source identities.

Eleven consumer repositories use the existing synchronized CMake helper for tool
installation, registries and INI/CTD metadata tests. Backend targets and scientific
tests remain explicit in each package. All 16 consumer locks follow the new Core
graph, including FLASHApp. The [native runner](build-split-packages.md) reproduces
the dependency order, builds, package tests and installed numerical suite.

## Linux native results

Dax had 384 logical CPUs, approximately 2.1 TiB available memory and load 6.16
(0.02/core) at selection. Builds used up to 320 compilation jobs, four concurrent
consumer builds, and up to 128 CTest jobs. The environment used GCC 14.4, shared
Core/Boost, Arrow 23.0.1, Eigen 5.0.1, COIN, Qt 6.10.1, Python 3.12 and nanobind
2.10.0. Optional instrument/ONNX/HDF5 integrations and interactive/WebEngine
desktop tests were disabled; OpenMP and OpenSWATH were enabled.

Core built in **90.77 seconds** and passed **701/701** tests in **23.35 seconds**.
Installed and relocated SDK consumers passed, including rejection of a wrong
source pin, in **17.40 seconds**. A separate installed desktop consumer passed
all nine resource, viewer, image and pipeline checks in **0.98 seconds**.

| Package | Clean build, seconds | Package tests |
| --- | ---: | --- |
| cli | 9.82 | 9 CTest entries in 0.13 s |
| test-data | 0.03 | Fixtures installed |
| topp | 16.84 | 242 CTest entries in 0.89 s |
| openswath | 12.69 | 38 CTest entries in 0.24 s |
| flash | 12.13 | 9 CTest entries in 61.53 s |
| desktop | 33.28 | 10 CTest entries in 0.78 s |
| pyopenms | 62.84 | 4 CTest entries in 10.93 s |
| nuxl | 19.33 | 13 CTest entries in 0.25 s |
| prose | 18.18 | 3 CTest entries in 7.10 s |
| nase | 13.10 | 2 CTest entries in 0.11 s |
| comet | 7.77 | 3 CTest entries in 0.15 s |
| mascot | 4.84 | 4 CTest entries in 1.76 s |
| database-suitability | 10.80 | 4 CTest entries in 0.39 s |
| proteomics-lfq | 13.02 | 3 CTest entries in 0.11 s |
| parquet-diff | 6.48 | 3 CTest entries in 0.11 s |

The installed console suite registered 2,041 tests across 150 tools:
**2,036 passed, five existing skips, zero failures**, in **10.59 seconds**.
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
in [run 34517947252](https://github.com/okohlbacher/OpenMS4-flashapp/actions/runs/34517947252).
The ordinary hash-pinned dependencies also installed and passed `pip check` in an
isolated Linux environment. The real `DeconvWorkflow.execution` path passed in
**2.11 seconds** using the new SDK: INI creation/pyOpenMS parameter parsing,
persisted settings, native FLASHDeconv and FuzzyDiff execution, cached mzML/table
parsing, and expected missing-input failure propagation. Four scan rows and four
mass-table rows were produced, and all 18 scientific reference columns matched.
This ran app source `961991c`; the subsequent `ea9d933` changes only CI files.
Bare Streamlit context and input native-ID warnings remain in the evidence.
A full image/tagging workflow still requires the
separately pinned external FLASHTnT implementation; updating source locks does not
manufacture that binary.

Core's [five-platform run](https://github.com/okohlbacher/OpenMS4-core/actions/runs/34515874932)
was still running when this Linux evidence was recorded. Hosted macOS/Windows/ARM
success and release deployment must be recorded separately after completion.
The Linux results above are not a claim that those platforms have passed.

## Evidence

Exact commands, JUnit files, source pins and Python summaries are recorded in
[the machine-readable report](split-sdk-validation.json). The local evidence
archive is `split-sdk-execution/evidence.tar.gz` in the exploration workspace;
SHA-256 `f91a6f87f32d7ad6a9168b7dd4ca03acaa6f16ce23b1d314c68a8d23a532135d`.
Scratch sources, installed products and raw logs are under
`/scratch/kohlbach/openms4-split-sdk-20260910` on dax. The original installed Core
and dependency environment were not overwritten. Runtime dependencies are
external; no repaired portable wheel or self-contained product installer is
claimed by this integration run.
