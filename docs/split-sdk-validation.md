# Split SDK validation — 2026-09-11

The complete native package graph at parent `089cffa1f9f68607476f0713a334aa93bac24b71` was freshly checked out
from GitHub and built in Release on IBMI dax. Every consumer used installed Core
`94a2b114939e4c70e16b1141bd98c87b8d21d166`. No Core source/build-tree fallback or
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

Dax had 384 logical CPUs, approximately 2.1 TiB available memory and load 6.84
(0.02/core) at selection. Builds used up to 320 compilation jobs, four concurrent
consumer builds, and up to 128 CTest jobs. The environment used GCC 14.4, shared
Core/Boost, Arrow 23.0.1, Eigen 5.0.1, COIN, Qt 6.10.1, Python 3.12 and nanobind
2.10.0. Optional instrument/ONNX/HDF5 integrations and interactive/WebEngine
desktop tests were disabled; OpenMP and OpenSWATH were enabled.

Core rebuilt in **7.01 seconds** for the final build identity and CI regression change and
passed **701/701** tests in **22.39 seconds**. The Parquet ownership fix itself rebuilt in **13.47 seconds** at `8497608`.
These are incremental rebuilds; the earlier clean Core build at `39975e5` took 91.19 seconds.
Installed and relocated SDK consumers passed, including rejection of a wrong
source pin, in **17.20 seconds**. A separate installed desktop consumer passed
all nine resource, viewer, image and pipeline checks in **0.98 seconds**.

A separate clean build at preceding Core revision `74526a8`, before the Windows
test and Parquet lifetime fixes, with both
`ENABLE_CLASS_TESTING=OFF` and `OPENMS_BUILD_TEST_SUPPORT=OFF` completed in
**83.67 seconds**. Installed and relocated consumer checks passed in **14.44
seconds**, confirming Core remains independent of the test framework.

| Package | Clean build, seconds | Package tests |
| --- | ---: | --- |
| cli | 9.19 | 9 CTest entries in 0.13 s |
| test-data | 0.03 | Fixtures installed |
| topp | 17.20 | 242 CTest entries in 0.89 s |
| openswath | 12.65 | 38 CTest entries in 0.23 s |
| flash | 12.15 | 9 CTest entries in 59.33 s |
| desktop | 33.63 | 10 CTest entries in 0.72 s |
| pyopenms | 62.55 | 4 CTest entries in 10.84 s |
| nuxl | 19.38 | 13 CTest entries in 0.24 s |
| prose | 17.59 | 3 CTest entries in 7.12 s |
| nase | 13.15 | 2 CTest entries in 0.12 s |
| comet | 7.82 | 3 CTest entries in 0.16 s |
| mascot | 4.87 | 4 CTest entries in 1.77 s |
| database-suitability | 10.76 | 4 CTest entries in 0.39 s |
| proteomics-lfq | 13.13 | 3 CTest entries in 0.12 s |
| parquet-diff | 6.45 | 3 CTest entries in 0.11 s |

The complete fresh consumer build/test/install run took **176.35 seconds**.

The installed console suite registered 2,041 tests across 150 tools:
**2,036 passed, five existing skips, zero failures**, in **10.65 seconds**.
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
in [run 34572234903](https://github.com/okohlbacher/OpenMS4-flashapp/actions/runs/34572234903).
The ordinary hash-pinned dependencies also installed and passed `pip check` in an
isolated Linux environment. The real `DeconvWorkflow.execution` path passed in
**2.05 seconds** using the new SDK: INI creation/pyOpenMS parameter parsing,
persisted settings, native FLASHDeconv and FuzzyDiff execution, cached mzML/table
parsing, and expected missing-input failure propagation. Four scan rows and four
mass-table rows were produced, and all 18 scientific reference columns matched.
This ran app source `eb261e677a14de89998e03931ce9285f54d0e6f1` with the
committed `tools/test_flashapp_deconvolution.py` acceptance driver.
Bare Streamlit context and input native-ID warnings remain in the evidence.
A full image/tagging workflow still requires the
separately pinned external FLASHTnT implementation; updating source locks does not
manufacture that binary.

Core's [final five-platform run](https://github.com/okohlbacher/OpenMS4-core/actions/runs/34572051447)
passed on Linux x64/arm64, macOS x64/arm64 and Windows x64 at exact commit
`94a2b114939e4c70e16b1141bd98c87b8d21d166`. Each platform passed all 701
scientific tests, followed by installed SDK packaging and extracted/relocated
consumer acceptance. All five downloaded archives match their SHA-256 checksums
and clean full source identities.

| Platform | Clean build, seconds | 701 tests, seconds | Extracted/relocated SDK, seconds |
| --- | ---: | ---: | ---: |
| linux-arm64 | 1747.89 | 31.92 | 18.77 |
| linux-x64 | 2128.51 | 47.05 | 18.16 |
| macos-arm64 | 1688.23 | 71.72 | 23.87 |
| macos-x64 | 2887.97 | 167.93 | 56.11 |
| windows-x64 | 3832.09 | 55.72 | 142.36 |

Windows SDK acceptance includes 2,000 additional Parquet probe repetitions.
The [Core SDK prerelease `core-v4.0.0-ci.1`](https://github.com/okohlbacher/OpenMS4-core/releases/tag/core-v4.0.0-ci.1)
was published by the successful
[release workflow](https://github.com/okohlbacher/OpenMS4-core/actions/runs/34578193995).
Publication reused these exact qualified archives. The remote tag points to
`94a2b114939e4c70e16b1141bd98c87b8d21d166`; all five archive assets and all five
checksum assets match the locally verified CI files by SHA-256 and size.

### Windows Parquet file lifetime

Native Windows CI passed all 701 scientific tests but the installed Parquet
probe failed when deleting its input file immediately after `readTable(filename)`.
The instrumented probe identified an open-handle sharing violation; the original
uncaught exception appeared as exit `0xc0000409`. Arrow's
[asynchronous read task](https://github.com/apache/arrow/blob/apache-arrow-23.0.1/cpp/src/arrow/io/interfaces.cc#L165-L172)
retains shared ownership of the file, so returning from the reader did not
reliably close the filename-owned input.

The [original quiet probe](https://github.com/okohlbacher/OpenMS4-core/actions/runs/34571493775)
passed 1,000 times at the original prefix, then failed on the 479th relocated run.
Using the same actual SDK archive and identical dependency packages,
[explicit closure](https://github.com/okohlbacher/OpenMS4-core/actions/runs/34571563778)
passed 1,000 consecutive runs at each prefix. Independent Arrow-only comparison
programs had not reproduced this OpenMS integration failure.

Core now closes the input it owns on both successful and exceptional read paths.
The filename overload delegates to the existing shared-file reader, removing
its duplicated chunk-combining code. Caller-owned files remain open. Regressions
check immediate deletion while the table remains usable, caller ownership, and
cleanup after a read error. Windows CI performs 1,000 consecutive probe runs per
prefix and fails on the first error; it does not retry failures until they pass.
The separate [original quiet probe against the final Windows SDK](https://github.com/okohlbacher/OpenMS4-core/actions/runs/34577610599)
also passed 1,000 consecutive runs per prefix, with the same exact dependency
packages as its producer. Native CI and the additional quiet probe therefore
completed 4,000 successful repetitions against the fixed Core revision.

## Homebrew delivery

macOS consumers can now install the qualified SDK and the released tools from the
two repository taps. The Core formula `Formula/openms4-core.rb` builds
`core-v4.0.0-ci.1` from its published source archive; the TOPP cask
`Casks/openms4-topp.rb` installs the prebuilt Homebrew archives of
`topp-v1.0.0-ci.2` and declares the formula as its dependency. Core and TOPP
package revisions are `0715382300003c5744d31483c396eb4adf7b54ab` and
`9efa969a0414340dd871221eccf7d38714891370`.

The [cask installation run](https://github.com/okohlbacher/OpenMS4-topp/actions/runs/34597449097)
passed on both macOS architectures. Each job tapped both repositories, trusted
the Core formula, installed the cask, ran `OpenMSInfo --help` and uninstalled the
cask again. Homebrew poured bottles for all native dependencies and built Core
itself from source; the Intel job needed the raised 90-minute timeout.

| Platform | Runner | Job, seconds | Core source build, seconds |
| --- | --- | ---: | ---: |
| macos-arm64 | macos-15 | 588 | 458 |
| macos-x64 | macos-15-intel | 2112 | 1502 |

Both platforms report `Version: 1.0.0 (OpenMS core 4.0.0, revision exported)`,
which is the intended separation of product and linked-core versions. The
dependency sets differ between architectures, notably Arrow `25.0.1_5` against
`25.0.1_4` and libomp `23.1.0` against `22.1.8`. Two earlier cask runs failed
first because the cask's formula dependency came from an
[untrusted tap](https://github.com/okohlbacher/OpenMS4-topp/actions/runs/34597052500),
then on the original
[30-minute timeout](https://github.com/okohlbacher/OpenMS4-topp/actions/runs/34597220410).
Both causes are fixed in the pinned revisions rather than retried.

Six independent artifact checks were repeated locally against the published
files. The formula archive re-hashes to the `sha256` the formula declares; its
tag resolves to `94a2b114939e4c70e16b1141bd98c87b8d21d166`, the same revision the
formula asserts through `OPENMS_SOURCE_REVISION` and the revision qualified on
all five platforms. Both cask checksums match the published Homebrew release
assets, the downloaded arm64 archive re-hashes to its declared sum, and the cask
exposes exactly the 122 executables that archive contains, with `FileInfo`
installed as `OpenMSFileInfo` to avoid a generic name in a shared prefix.

Three limitations remain. `OpenMSInfo` prints the legacy Git field, which is
`exported` for any archive build, so the exact source revision is compiled in and
available through `VersionInfo::getSourceRevision()` but is not reported by the
tool whose purpose is reporting configuration. No bottle is published, so every
cask install pays for a full Core source build. Homebrew delivery covers macOS
only; Linux and Windows packaging are not addressed here.

## macOS native package build

The complete consumer graph also builds on macOS arm64 against the installed
Homebrew Core SDK. `tools/build_packages.py` ran with `--workers 1`, so the
fifteen packages were configured, built, tested and installed strictly one after
another, using Core `94a2b114939e4c70e16b1141bd98c87b8d21d166` from the
`openms4-core` formula and Homebrew for every other dependency. All fifteen
packages and all 2,369 tests passed, and the run installed 150 console tools.

| Package | Seconds | Tests |
| --- | ---: | ---: |
| topp | 66.3 | 242 |
| desktop | 79.9 | 10 |
| pyopenms | 55.0 | 4 |
| flash | 39.8 | 9 |
| openswath | 15.7 | 38 |
| nuxl | 16.1 | 13 |
| prose | 17.7 | 3 |
| the remaining eight packages | 58.3 | 28 |
| installed numerical suite | 66.2 | 2022 |

Two host provisioning requirements are not carried by the packages. Consumers of
the released Core cannot find Homebrew's keg-only OpenMP: `find_dependency(OpenMP)`
fails during the first consumer configure unless `OpenMP_ROOT` names
`/opt/homebrew/opt/libomp`. Core `29fa3be` exports it, but that commit is above
the qualified revision, so the fix is absent from `core-v4.0.0-ci.1`. pyOpenMS
needs its declared `test` extra present in the selected interpreter; without
`pytest` all four of its test targets fail immediately while the bindings
themselves build and import cleanly.

This is one host and one architecture, and it does not replace the five-platform
matrix. FLASHApp acceptance remains a separate Python step and was not run here.
Interactive desktop and WebEngine tests stay disabled in the headless profile,
and optional instrument readers and external search engines are absent from this
SDK, so their conditional tests do not execute.

## Evidence

Exact commands, source pins, test counts and Python summaries are recorded in
[the machine-readable report](split-sdk-validation.json). Raw JUnit files and logs
are retained in the local evidence
archive `split-sdk-execution/evidence-qualified-94a2b11.tar.gz` in the exploration workspace;
SHA-256 `3bef8bcdfb347c6b9edcc2f547d521d2385b77d64e6a8f10e8c902164cffff4b`. The
Homebrew job logs and the repeatable artifact verifier are archived alongside it as
`split-sdk-execution/evidence-homebrew-9efa969.tar.gz`;
SHA-256 `ab6ed17558e6497345d0d67ec5443cd44729ff36b8850132002160d43bebfd60`. The
sequential macOS package build keeps its command receipts, logs and JUnit reports in
`split-native-build-evidence.tar.gz`;
SHA-256 `2048a6e28ed175998ee303bbe55a14f348d073e2cde597eb48566ea762a0f21b`.
Scratch sources, installed products and raw logs are under
`/scratch/kohlbach/openms4-split-sdk-20260910` on dax. The original installed Core
and dependency environment were not overwritten. Runtime dependencies are
external; no repaired portable wheel or self-contained product installer is
claimed by this integration run.
