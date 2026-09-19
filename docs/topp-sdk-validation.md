# Standalone TOPP build against the installed Core SDK

*Part of the [OpenMS 4 package split](../README.md). [State of the project](project-state.md) · [Package architecture](package-architecture.svg) · [Build instructions](build-split-packages.md)*

All 130 enabled TOPP tools built and installed from a clean standalone source
archive using the pinned Core and CLI SDKs. Original repositories, Core/CLI/TOPP
build trees and the original SDK installation were inaccessible throughout
configuration, compilation and the final native tests. No Core source was built.

The subsequent [TOPP runtime report](topp-runtime-report.md) executes every runnable
registered test in this installation and records repeated reading benchmarks.
The build and subset results below remain the original validation record.

## Package contract

| Input | Exact source revision |
| --- | --- |
| TOPP 1.0.0 | `582535805581f2bdf4f3871d6802a0b45a3abe36` |
| Core SDK 4.0.0 | `4fdec46b205459b92e7d3b9e56df5d8e912d5c85` |
| CLI SDK 1.0.0 | `51db6bbbdeba53abc57d23c664de37f9c285372e` |
| Installed test-data 1.0.0 | `c3e52c917bc2a04e27720f5c7d8189c0f4f522da` |

TOPP imports `OpenMS::Core` and `OpenMS::CLI`. Its existing lock enforces both
package versions and full source revisions; CLI independently checks the same
Core revision. FuzzyDiff also imports `OpenMS::TestFramework`, so Core's optional
TestSupport component is required even with TOPP tests disabled. Ordinary TOPP
executables do not need the test fixtures at runtime.

The unused `src/CMakeLists.txt`, which still referenced the old monorepo build,
was removed. The [TOPP README](../packages/topp/README.md) now describes the exact
SDK prerequisites, matching compiler/architecture/build configuration, and
ownership of the separate FLASH/OpenSWATH executable packages. No additional
dependency mechanism or native library change was necessary.

## Actual validation

Profile: macOS arm64, AppleClang 21, C++23, Debug; shared Boost 1.90, Eigen 5.0.1,
Arrow/Parquet 25, Homebrew CURL and OpenMP. FeatureLinkerWNet is disabled because
the pinned Core profile has WNet disabled; its source remains in TOPP.

| Check | Result |
| --- | --- |
| Standalone source archive | Clean TOPP commit exported with Git; archive digest recorded. All 130 compile commands use TOPP source files and installed SDK headers, with no original repository/SDK paths. |
| Build | All 130 enabled executables compiled and linked; 168.64 seconds with two build workers. Core/CLI binaries were copied from their existing installations, not rebuilt. |
| Metadata | **258/258 tests passed**, verifying INI and CTD product version/category for all applicable tools. OpenMSInfo does not emit these metadata files. |
| Installed numerical subset | **285/285 tests passed** in 69.71 seconds, including 148 FuzzyDiff comparisons. Covers XML/SQLite/Parquet conversion, filtering, merging, smoothing, normalization, alignment, RT transformation, FASTA decoys and Unicode paths. |
| Additional installed checks | **53/53 tests passed** in 9.95 seconds: FileInfo, PeakPickerHiRes and six exact-status/diagnostic invalid-parameter cases. Combined numerical/negative selection: **338 tests**. |
| Wrong SDK | Replacing the expected Core revision with another full SHA fails configuration with the intended SDK revision mismatch. |
| Isolation controls | Reads of original Core source, Core build cache and original SDK configuration fail with permission errors. The full original parent/package tree is denied. |
| Actual loaded SDK | OpenMSInfo's loader trace resolves Core and CLI inside the copied SDK; runtime data resolves to that SDK's versioned data directory. Core/CLI/OpenSwathAlgo library bytes match the original pinned installation. |
| Source contracts | Final parent/package source and configuration validation passed; all nine gitlinks and dependency locks agree. |
| Installed package | 130 executable files and one TOPP registry installed; all 131 file hashes recorded. |

The four inherited `WILL_FAIL` tests within the 285-test group retain their
original expected-failure semantics; they do not assert exact error codes. The
six additional invalid-parameter cases do assert their intended status and
message. This is a selected numerical suite, not an exhaustive run of every TOPP
adapter or algorithm.

## Evidence and reproduction

[Command records, final logs, JUnit XML, source/archive checks and installed-file
hashes](validation/topp-sdk-2026-09-10/) preserve the run. The two Python recipes
and sandbox profile originally live under `<exploration>/topp-sdk-validation/`;
they use the `source`, `sdk`, `build`, `test-data-sdk` and `evidence` directories
there. Their absolute paths describe this machine, not portable defaults.
The source archive came from the TOPP commit above; installed Core/CLI and
fixture files were copied according to their existing install manifests.

On this host, re2 references an older Abseil library than the active Homebrew
prefix provides. The initial test attempt failed because macOS stripped the
loader setting on entry to `sandbox-exec`. The final commands apply the existing
Abseil fallback through `env` *inside* the sandbox. They remove inherited OpenMS
data/tool-prefix overrides. External Homebrew dependency reads remain allowed;
this SDK validation is not a self-contained distribution test. No system or
third-party dependency files were modified.

Run build-tree metadata tests before installing TOPP into the dependency prefix.
The final serialized metadata rerun temporarily moved only this copied SDK's
installed TOPP registry aside, then restored it, avoiding duplicate discovery
between build-tree and installed products. The subsequent numerical tests use
the installed tools and registry. Intermediate overlapping retry output is not
counted as acceptance evidence.

The tested installation is `<exploration>/topp-sdk-validation/sdk/bin`.
Linux, Windows, Release TOPP, WNet and external search-engine execution remain
separate validation profiles. Recorded elapsed times are build/test evidence,
not a controlled performance benchmark. Earlier combined-runtime artifacts and
reports retain their earlier TOPP commit and hashes.
