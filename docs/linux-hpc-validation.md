# Linux HPC validation of the extracted packages

*Part of the [OpenMS 4 package split](../README.md). [State of the project](project-state.md) · [Package architecture](package-architecture.svg) · [Build instructions](build-split-packages.md)*

The complete native package graph was checked out from GitHub and built on IBMI's `dax` node, using node-local `/scratch` for sources, builds and temporary files. The initial input was parent `5d1e2391167dbb16c8ea6cd1001393bf5609e296`. Linux testing exposed an inherited numerical defect; its corrections and all dependent pins were committed and pushed as parent `afeceb45805f6aeeb349a4902b136fbd705a461b` before a second, fresh build.

## Profile

- Ubuntu 24.04.4, x86_64; two AMD EPYC 9654 CPUs, 384 logical CPUs and approximately 2.2 TiB RAM.
- Up to 320 compilation jobs, leaving capacity for other users on this shared node. Independent products used four workers with 80 compiler jobs each; Python and desktop used 160 jobs each.
- GCC 14.4, C++23, Debug (`CMAKE_CXX_FLAGS_DEBUG=-g`), shared Core and Boost, OpenMP enabled, STL debug mode disabled, COIN solver.
- Arrow/Parquet 23.0.1, Boost 1.89.0, Eigen 5.0.1, Qt 6.10.1, Python 3.12.14 and nanobind 2.10.0. Dependencies were installed in an isolated task environment; no shared environment, system installation, contrib or vendored sources were changed.
- Core tests used 128 CTest jobs and the installed console suite used 128. Numerical runs used `OMP_NUM_THREADS=1`; direct FLASH class tests used 16. Tools can override this through their own thread options.
- Optional HDF5, ONNX, WNetAlign, OpenTIMS, Thermo RAW and TDL were disabled. Desktop WebEngine and interactive-display tests were disabled. FLASHApp and its frozen web-app dependency graph were not rebuilt.

These are observed Debug build/test wall times, not Release performance benchmarks. Concurrent durations cannot be added to infer total elapsed time. The earlier macOS Core number was an incremental build, so it is not directly comparable to these fresh builds.

## Numerical defect found and corrected

In the affected translation units, GCC resolved unqualified `abs(double)` calls to integer `::abs`, truncating fractional isotope, retention-time and precursor-mass differences. Peaks outside the configured tolerance were recruited as signal, and distinct precursors could be combined.

An isolated checkout of the exact pre-extraction Core/CLI/FLASH/TestData graph reproduced the Linux result. Its eight spectrum rows matched the extracted graph in every column except the input filename. Both graphs produced no final features for the small fixture. The recorded old and new Core build metadata differed only in source revision, and loader traces confirmed that the baseline really loaded the old libraries. This established that the split did not introduce the defect.

The correction explicitly includes `<cmath>` and uses `std::abs` in two Core `PeakGroup` comparisons, three FLASH spectral comparisons and four FLASH isobaric-quantification comparisons. Integer comparisons and scientific references remain unchanged. A fresh macOS replay and the corrected Linux diagnostic both matched the existing reference, including all 18 scientific columns and the 8994.536888 Da, charge-8 feature.

Two focused regressions independently fail before the correction and pass afterward:

- Core recruitment/noise reporting: four input peaks should produce two isotope signals and two off-grid noise peaks. The old GCC binary reported four signals and no noise; the corrected implementation reports two/two and preserves the const noise-query behavior.
- FLASH isobaric quantification: two precursors separated by 0.25 Da should retain reporter intensities of 100 and 300. The old binary incorrectly reported 400 for both; the corrected implementation keeps them separate.

The FLASH scientific test now requests an output even when no features are found, so a stale TSV cannot conceal an empty result. No reference value or numerical tolerance was relaxed. File-format support remains in Core; the shared PeakGroup correction does not change API signatures.

## Validation results

All final registered native checks passed, with the explicitly retained skips below. Each package was compiled in a new build directory against the newly installed, corrected SDK. The short and long FLASH invocations have disjoint test names; their union covers all nine registered cases.

| Component | Fresh build (seconds) | Final test result |
| --- | ---: | --- |
| Core SDK | 52.00 | 700/700 in 49.47 s |
| CLI | 7.05 | 9/9 in 0.36 s |
| Remaining TOPP | 13.85 | 242/242 in 1.13 s (metadata) |
| OpenSWATH | 9.45 | 38/38 in 0.28 s (metadata) |
| ProSE | 13.52 | 3/3 in 49.89 s |
| NuXL | 14.73 | 13/13 in 1.20 s |
| NASE | 11.88 | 2/2 in 0.16 s |
| Comet | 6.00 | 3/3 in 0.34 s |
| Mascot | 4.42 | 4/4 in 1.78 s |
| DatabaseSuitability | 9.60 | 4/4 in 1.22 s |
| ProteomicsLFQ | 11.90 | 3/3 in 0.14 s |
| ParquetDiff | 5.11 | 3/3 in 0.13 s |
| FLASH | 11.42 | 9/9 unique checks: eight in 28.21 s; long algorithm test 508.56 s |
| Desktop | 33.28 | 10/10 in 1.77 s; installed consumer 9/9 |
| pyOpenMS | 52.30 | Four groups in 27.69 s: 5,749 passed, 92 skipped, 10 xfailed, 7 xpassed |

The corrected installed console suite passed **2,036 tests**, with **five existing skips and zero failures**, in **166.85 seconds** across 150 tools. Core SDK consumer acceptance passed **8/8 before relocation and 8/8 after relocation**, with a separate successful rejection of a wrong source pin; its driver took **19.917 seconds**. The new PeakGroup regression is a section within the same 700 Core tests.

Installed Python also passed three independent provenance/data-override checks. Actual Core, ProSE and FLASH library paths and hashes came from `sdk-fixed/lib`, with no CLI/GUI library loaded. Provider source IDs remain build metadata; the path/hash checks identify loaded files without independently attesting provider source. The full Python run preserves the existing skip/xfail/xpass markers. Desktop's nine installed checks cover repeated SDK discovery, resource access, viewer help, exact ImageCreator outputs and an installed pipeline. A collection filename collision required a documented repeat of those nine checks; it is not counted as nine additional unique tests.

The final source/configuration validator passed in **103.22 seconds**, including parent pins, package boundaries, full/reduced Python configuration and wrong-identity rejection. The source graph is committed and clean; no references or tolerances were relaxed to obtain these results.


The initial installed console run registered 2,041 tests: 2,036 passed and five retained legacy tests were skipped, in 158.18 seconds. This is 19 more registered checks than the macOS arm64 run: 16 NuXL cases and three PeakPickerIM output comparisons, selected by the inherited platform conditions. The final run uses the same registered scope against the corrected, separately installed products.

The five skips are `TOPP_MSGFPlusAdapter_missing`, `TOPP_SageAdapter_missing`, `TOPP_CometAdapter_missing`, `TOPP_CometAdapter_failing` and `TOPP_MSFraggerAdapter_missing`. Their inherited `SKIP_RETURN_CODE` properties classify those deliberately requested failure statuses as skipped. No new numerical test was disabled. Real external proprietary engines and services were not provisioned.

The initial 700-test Core run internally skipped the opt-in slow PipEcho section. That section was subsequently run explicitly and passed in 47.47 seconds. The final Core run enables `OPENMS_RUN_SLOW_TESTS=1` from the start and verifies the full 10,000-feature section.

## Reproduction and evidence

The parent lock identifies all 17 private source repositories. Initialize the immediate submodules at their locked commits; nested contrib and web-app dependencies are unnecessary for this native profile. Configure/install Core, CLI and TestData, then the product providers/tools, then desktop and full Python. Each consumer uses the installed SDK and rejects a mismatched source pin. Test metadata before installing a second manifest for the same product into a discovered prefix.

The exact command receipts, compiler/dependency inventory, source pins, original failures, diagnostic replays, complete test logs and final JUnit results are preserved with the build artifacts. Core installed-consumer acceptance also tests relocation while the external dependency environment remains available; it is not a self-contained-distribution claim. Python acceptance checks actual loaded Core/ProSE/FLASH library paths and absence of CLI/GUI libraries.

The SDK and its dependency environment are recovery archives with recorded hashes. The dependency environment contains absolute prefixes; restoring those paths or recreating the recorded environment is required for faithful replay. This work does not qualify a repaired portable wheel or an installer.

The [machine-readable report](linux-hpc-validation.json), [exact Conda dependency inventory](linux-hpc-dependencies.json) and [Python package inventory](linux-hpc-pip-freeze.txt) accompany this page. Initial environment setup required the LibXml2 and OpenGL development packages; source-contract subprocesses required explicit Conda compiler paths. These setup failures and their corrections are preserved separately from executed scientific tests.

Persistent artifacts are in `/ceph/ibmi/abi/oliver/AI/OpenMS4-tests/afeceb45805f6aeeb349a4902b136fbd705a461b-dax-20260910`. The working installation is `/scratch/kohlbach/openms4-5d1e239-20260910/sdk-fixed`; the checkout and build directories are `source-fixed` and `build-fixed` beside it. Command runners and raw evidence are retained locally under `hpc-build-execution/` and in the Ceph evidence archive, including the initial failing run and exact old-graph replay. The complete raw evidence archive is `evidence-complete.tar.zst`; its SHA256 is `56adf1373283cc8dcc139652779684dc932753ba2715f1888dfb685fc5558a5b`. Binary/dependency archive hashes are recorded in the machine-readable report.
