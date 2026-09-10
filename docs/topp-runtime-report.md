# TOPP test and benchmark runtimes — 10 September 2026

**1,948 checks passed, five skipped and none failed.** The four test batches
consumed **342.03 seconds (5 minutes 42 seconds)** of CTest wall time. All 1,695
runnable registered tests in this TOPP-only installation were executed, plus 258
strict package metadata checks. This extends the earlier 338-case numerical
subset in the [standalone SDK build report](topp-sdk-validation.md).

The existing installed Debug binaries were used without rebuilding. The
TICCalculator benchmark completed all 72 invocations: 12 discarded warmups and
60 measured runs. Every invocation produced the expected spectrum count, peak
count and total ion current at the tool's printed precision.

## Test runtimes and coverage

| Batch | Passed | Skipped | CTest wall time |
| --- | ---: | ---: | ---: |
| Strict metadata validation | 258 | 0 | 113.46 s |
| Numerical, negative and helper tests | 1,291 | 5 | 217.15 s |
| Shared-output numerical cases | 10 | 0 | 1.50 s |
| Registered metadata and overwrite tests | 389 | 0 | 9.92 s |
| **Total** | **1,948** | **5** | **342.03 s** |

Batches ran sequentially, normally with four CTest workers. Ten cases ran with
one worker because inherited DTAExtractor and MassTraceExtractor tests share
output names. Declared test dependencies were checked before execution, and the
numerical harness used fresh output directories. These are integration and
metadata checks, including comparison helpers; the total is not a count of
independent scientific algorithms.

The table uses CTest's `Total Test time (real)` values from the logs. External
launcher wall times total 342.134 seconds. Configuration took another 0.771
seconds. Setup, gaps between batches and benchmark work are excluded. JUnit's
suite-level time truncates to whole seconds; the logs preserve finer precision.
Strict metadata checks include Python validation and startup overhead.

Five inherited external-adapter cases returned their configured skip status:
`TOPP_MSGFPlusAdapter_missing`, `TOPP_SageAdapter_missing`,
`TOPP_CometAdapter_missing`, `TOPP_CometAdapter_failing`, and
`TOPP_MSFraggerAdapter_missing`. `TOPP_PercolatorAdapter_missing` passed through
successful in-process execution; it does not demonstrate missing-executable
error handling.
Twenty-one inherited negative tests retain broad `WILL_FAIL` semantics; six
additional parameter-error cases assert exact status and diagnostic text.

The installed harness registered 1,962 tests. **267 were excluded**: 137 commands
need absent executables, 129 helpers/comparisons belong to those other product
families, and one AssayGeneratorMetabo comparison depends on an excluded producer
that invokes OpenSwathDecoyGenerator. Eleven external-engine positive groups
were not registered because their engines were unavailable. Separate
FLASH/OpenSWATH executables, GUI, WNet and unavailable search engines are outside
this TOPP run. Platform guards also omit some upstream tests, including expensive
OpenNuXL search cases on macOS. This does not establish whole-project coverage.

The slowest numerical cases were:

| Test | Observed duration |
| --- | ---: |
| `TOPP_PeakPickerIM_1` | 69.26 s |
| `TOPP_PeakPickerIM_3` | 60.97 s |
| `TOPP_ProteomicsLFQ_biosaur2_seeds` | 25.59 s |
| `TOPP_ProteomicsLFQ_fraction_fwhm` | 19.27 s |
| `TOPP_ProteomicsLFQ_qpx_seeds` | 18.93 s |

These single observations were collected during a four-worker regression run;
they are not isolated performance benchmarks.

## Repeated reading benchmark

TICCalculator read `THIRDPARTY/MaRaClusterAdapter_1_in_1.mzML`: **13,607,928 bytes
(12.98 MiB), 1,684 spectra and 479,455 peaks**. The fixture SHA-256 is
`733d655721611b584e2fef550ae3ee282dd2c1d4a4ec9b290ae0d5f4c32ca48f`.
An independent XML/base64/float decoding check computed total ion current
4,294,999,079.090091; every tool run printed `4.295e+09`.

Each method/thread pair received one warmup and five measured repetitions. Runs
were serial, after all tests completed, with order rotated between rounds.
`-loadData true` and explicit `-threads 1` or `-threads 2` were used. Times include
process startup and captured output, measured with Python's monotonic
`time.perf_counter`. The range is the minimum–maximum of the five measured runs.

| Reading method | Median, 1 thread | Range, 1 thread | Median, 2 threads | Range, 2 threads |
| --- | ---: | ---: | ---: | ---: |
| `regular` | 0.799 s | 0.782–0.811 s | 0.722 s | 0.712–0.943 s |
| `streaming` | 0.776 s | 0.766–0.971 s | 0.723 s | 0.715–0.852 s |
| `indexed` | 1.130 s | 1.122–1.215 s | 1.139 s | 1.124–1.168 s |
| `indexed_parallel` | 0.519 s | 0.508–0.542 s | 0.356 s | 0.349–0.365 s |
| `cached` | 0.086 s | 0.085–0.091 s | 0.087 s | 0.084–0.091 s |
| `cached_parallel` | 0.088 s | 0.084–0.090 s | 0.088 s | 0.086–0.089 s |

FileConverter cache preparation took **1.528 seconds**, excluded from the read
measurements. It generated a 7,718,452-byte binary cache plus a 4,579,695-byte
metadata mzML. The 60 measured process durations sum to 33.213 seconds; including
all 12 warmups and cache creation gives **44.099 seconds**. This sum excludes
runner bookkeeping and log writes outside the timed sections.

These are warm-filesystem-cache measurements of a small fixture in a **Debug
build**. They provide a baseline for this installation, not a before/after
refactoring comparison or Release/full-acquisition performance result. A second
requested thread does not imply every method uses two threads effectively.

The methods also do different work: regular/streaming skip XML checks;
`indexed_parallel` skips metadata loading and XML checks that `indexed` performs.
Cached methods read binary data and omit XML/metadata loading. Differences across
methods cannot be attributed solely to parallelism, and cached read times omit
conversion cost. All modes ignore chromatograms for these counts/TIC.

The runner checks scientific output and error diagnostics in addition to exit
status because the existing TICCalculator entry point discards the return value
of `tool.main()`. Equality of total ion current is verified at the printed six
significant digits, with exact spectrum and peak counts. No source fix or new
benchmark framework was introduced for this measurement run.

## Machine, build and package identity

Apple M4 Max, 16 physical/logical CPUs, 128 GiB RAM; macOS 26.5.1 (25F80), arm64.
AppleClang 21.0.0.21000101, C++23, libc++, Debug; shared Boost 1.90, Eigen 5.0.1,
Arrow/Parquet 25 and OpenMP 5.1. The Core profile disables WNet and HDF5; 130 TOPP
executables are installed. Test runners set `OMP_NUM_THREADS=2`, but TOPP's own
thread option can override this and normally defaults to one. Benchmarks set
that option explicitly.

| Package | Exact source revision |
| --- | --- |
| Core SDK 4.0.0 | `4fdec46b205459b92e7d3b9e56df5d8e912d5c85` |
| CLI SDK 1.0.0 | `51db6bbbdeba53abc57d23c664de37f9c285372e` |
| TOPP 1.0.0 | `582535805581f2bdf4f3871d6802a0b45a3abe36` |
| Test-data 1.0.0 | `c3e52c917bc2a04e27720f5c7d8189c0f4f522da` |

The tested tools live in `<exploration>/topp-sdk-validation/sdk/bin`. Original
repositories, Core/CLI/TOPP build trees, the original SDK and network access were
denied by the same sandbox profile used for the standalone build validation.
Homebrew dependencies remained accessible. This host needs the existing Abseil
fallback `/opt/homebrew/Cellar/abseil/20260107.1/lib`, applied after entering the
sandbox because macOS strips loader environment settings at entry. This remains
a developer SDK installation with external dependencies, not a self-contained
binary distribution. No dependency or system files were modified.

## Evidence and reproduction

[Run records, per-case JUnit output, benchmark logs, exact commands, selection
lists, environment and checksums](validation/topp-runtime-2026-09-10/) preserve
the measurements. `results.json` records final totals; `execution-plan.json`
records final selection and exclusions; `benchmark-summary.json` contains full
precision medians, ranges and standard deviations. Independent reviews
recomputed all benchmark statistics and reconciled the test inventory.

The scripts are machine-specific run records. Their working layout is
`<exploration>/topp-runtime-report` alongside `topp-sdk-validation`; recorded
absolute paths are intentional. `run_numerical.py` configures the installed
fixture harness and executes the two numerical selection lists; `run_metadata.py`
uses the preserved metadata CTest registration. The registered metadata command
is in `legacy-metadata-run.json`. Run `run_benchmarks.py` under the recorded
sandbox with its loader setting applied inside the sandbox, after test completion.
The input/expected-output record is `benchmark-input.json`. Preserve the stated
SDK and fixture pins when reproducing these results.
