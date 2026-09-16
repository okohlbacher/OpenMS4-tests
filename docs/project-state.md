# OpenMS 4 package split — state of the project, 2026-09-16

*Part of the [OpenMS 4 package split](../README.md). [Package architecture](package-architecture.svg) · [Build instructions](build-split-packages.md)*

One document for someone arriving at this repository: what exists, what is proven,
what is delivered, and what is explicitly not qualified yet. The dated reports keep
the detail; this page keeps the current picture and links to them.

## What this is

OpenMS was split into one Core SDK and seventeen consumer repositories. Each consumer
builds against an **installed** Core — never a Core build tree — and pins the exact
Core revision it was built and tested against. This parent repository is the
integration point: it holds the submodules, `packages.lock.json`, the dependency-order
build runner, and the contract tests that keep the graph honest.

![Package architecture](package-architecture.svg)

Eighteen repositories, `123 + 19 + 9 = 151` installed console tools, one GUI SDK with
five applications, one Python binding package and one Streamlit application.

## The eighteen packages

Each package counts its own releases: the number in `topp-v1.0.0-ci.5` is TOPP's fifth
release, not the Core cycle it was built against, because a package can be re-released
against one Core (TOPP ci.1 to ci.3 all shipped against the same one) or sit out a cycle.

| Package | Visibility | Pinned revision | Release | Contents |
| --- | --- | --- | --- | --- |
| core | public | `ac41cc177023` | `core-v4.0.0-ci.5` | scientific library, OpenSwathAlgo, readers/writers, runtime data, optional TestSupport |
| cli | public | `6f50080aa391` | – (consumed by revision; `cli-v1.0.0-ci.2` is the last release) | TOPPBase, tool registration and discovery |
| test-data | public | `1c24a5e0e15d` | – | versioned fixtures and the installed numerical suite |
| topp | public | `0206f6e17541` | `topp-v1.0.0-ci.5` | 123 console tools |
| openswath | public | `2ac1cca68c65` | `openswath-v1.0.0-ci.3` | 19 executables and OpenSwathBase |
| flash | public | `0b0dfe14e4c4` | `flash-v1.0.0-ci.3` | FLASHDeconv and the `OpenMS::FLASH` backend |
| prose | public | `b056c8639269` | `prose-v1.0.0-ci.3` | ProSE and the `OpenMS::ProSE` backend |
| nuxl | public | `d3038ba1a222` | `nuxl-v1.0.0-ci.3` | OpenNuXL |
| nase | public | `0b272c6dfd10` | `nase-v1.0.0-ci.3` | NucleicAcidSearchEngine |
| comet | public | `a8e676d23764` | `comet-v1.0.0-ci.3` | CometAdapter |
| mascot | public | `70d3a423623c` | `mascot-v1.0.0-ci.3` | MascotAdapterOnline |
| database-suitability | public | `79021a07180d` | `database-suitability-v1.0.0-ci.3` | DatabaseSuitability |
| proteomics-lfq | public | `953ccc18ab40` | `proteomics-lfq-v1.0.0-ci.3` | ProteomicsLFQ |
| parquet-diff | public | `e576c1d1364b` | `parquet-diff-v1.0.0-ci.3` | ParquetDiff |
| desktop | public | `f3592559f020` | `desktop-v1.0.0-ci.3` | GUI SDK, TOPPView, ImageCreator, INIFileEditor, TOPPAS, ExecutePipeline |
| pyopenms | public | `d3e6867135eb` | `pyopenms-v4.0.0.dev0-ci.4` | nanobind bindings, installed module tree and repaired wheels |
| flashtnt | public | `f956a6ddb67f` | `flashtnt-v1.0.0-ci.2` | FLASHTnT tagging executable |
| flashapp | private | `8bdcc0516611` | – (no release; the app consumes the pyOpenMS wheel) | Streamlit application and Vue component |

Every revision above has a green push run on all of its platforms (test-data has no
CI of its own; each consumer checks it out at that revision), and every release was
published from that run. This is the Core ci.5 cycle, closed on 2026-09-16.

The next Core candidate is `codex/p0-followups` at `df065dc`: the P0 follow-up fixes
from the [P0 walkthrough](cpp-p0-walkthrough.md), green on all seven native/Homebrew
CI jobs (run 34882958117) and on the 32 integration tests on dax. It is not the
released Core pin above.

pyOpenMS ci.4 and FLASHTnT ci.2 are published for all five platforms. FLASHApp pins
FLASHTnT `f956a6ddb67f` and runs its app tests against the published pyOpenMS ci.4 Linux
wheel, whose SHA-256 its lock records.

## Building and testing

The parent's contract tests need nothing but Python:

```bash
python3 -m unittest discover -s tests      # 65 tests: pins, boundaries, tool metadata, receipts
```

The whole native graph is built from the installed Core with one runner; see
[the build instructions](build-split-packages.md) for prerequisites and flags:

```bash
python3 tools/build_packages.py --core-prefix <installed core> \
  --dependencies <dependency prefix> --work-dir <empty dir> --jobs N --workers M
```

It refuses to start unless every submodule is clean and equal to `packages.lock.json`
and the installed Core's recorded revision matches the lock, then builds in dependency
order, runs each package's tests, installs into one prefix and finally runs the
installed console suite against the registered tools of every product.

Per-package CI builds each package on five platforms (Linux x64/arm64, macOS x64/arm64,
Windows x64) against the published Core release archive; a tag triggers a release
workflow that republishes exactly the artifacts of that green run.

## Current verification

Rebuilt from a fresh clone on IBMI dax on 2026-09-13 at the pins above, against the
published `core-v4.0.0-ci.2` Linux archive:

| Suite | Result |
| --- | --- |
| Installed console regression suite | 2,044 entries, 5 external-engine skips, **0 failures** |
| TOPP / OpenSWATH / NuXL / FLASH / CLI | 242 / 38 / 14 / 9 / 9, all pass |
| desktop (headless Linux suite) | 11, all pass |
| FLASHTnT | 4, all pass |
| pyOpenMS | four groups, all pass |
| Parent contracts at the earlier snapshot | 64, all pass |

The real QRhi frame was checked separately on macOS; the Linux headless run does
not establish Cocoa or interactive Windows acceptance. The current working tree
has 64/65 parent contracts passing: the pin gate rejects the review Core checkout
while the integration lock retains released Core. Generated child documentation
also awaits the coordinated commit/pin cycle.

151 console tools were installed with no duplicate registration. Receipts are under
`/scratch/kohlbach/openms4-verify-20260913/work/results` on dax; the
[port resumption report](port-resumption-2026-09-12.md) carries the per-command receipt
and the FLASHTnT sanitizer, repeatability and cross-platform evidence.

## Delivery

- **Core** — Homebrew formula `okohlbacher/openms4-core` with bottles for arm64 Sequoia,
  Intel Sequoia and x86_64 Linux, published as assets of the ci.5 release.
- **Console products** — eleven Homebrew casks (`openms4-topp`, `openms4-openswath`,
  `openms4-flash`, `openms4-prose`, `openms4-nuxl`, `openms4-nase`, `openms4-comet`,
  `openms4-mascot`, `openms4-database-suitability`, `openms4-proteomics-lfq`,
  `openms4-parquet-diff`), each pointing at this cycle's payloads and verified by an
  install workflow that installs the cask from the tap on both macOS architectures.
  Every generated cask refuses to install unless
  the installed Core carries the payload's source revision, and lists only the tools its
  Homebrew payload actually ships: the Homebrew Core is built without WNetAlign, so
  `FeatureLinkerWNet` is in `tools.json` but not in a cask.
- **pyOpenMS** — installed module trees plus repaired wheels (CPython 3.12) for five
  platforms, tested from a clean environment.
- **desktop** — five platform archives; no installer, signing or notarization.
- **FLASHTnT** — five native platform archives, requiring the pinned SDK dependencies.
- **FLASHApp** — locally tested image; no published artifact.

## Build infrastructure

Package CI routes the `linux-x64` row of push and dispatch events to self-hosted
runners on the IBMI node dax and the `macos-arm64` row to a Mac Studio; pull requests
always stay on hosted runners, because the repositories are public and a fork must
never execute on either machine. Windows x64 push/dispatch jobs also use the dedicated workstation runners. macOS
x64 and Linux arm64 remain hosted. Core currently retains its own hosted matrix.
`tools/hpc/` holds the runner install and registration scripts, one runner per
repository, each with its own `HOME` and a job-start hook that clears the previous
job's micromamba.

FLASHApp's hosted jobs were refused by GitHub's billing/spending-limit gate. A
dedicated private-repository runner on dax now runs both application CI jobs:
run `34756837299` passes at `57be473`. The Linux wheel/application job passes
134 tests and 52 subtests (three skips), and isolated lifecycle/artifact contracts
pass 61 tests and 52 subtests (two skips). FLASHTnT is public and its five-platform
CI is green. No repository visibility was changed during this resumption.

The Windows cleanup hooks now use PowerShell's JSON serializer for paths. Native
PowerShell/Node testing verified both target directories are removed and an unrelated
sibling is retained; the corrected hooks were applied to all sixteen existing runners.

## Not qualified

- **FLASHTnT numerical parity.** The port executes and is sanitizer-clean at
  `4ca4e73`, but the strict comparison against the retained May 2025 AQPZ outputs
  fails (698 tags versus 2,968, 10 proteins versus 17). The upstream algorithm changed
  between those dates; this is an open question, not a passing check.
- **FLASHApp deployment.** The image, its Vue bundle and the queue lifecycle have
  evidence, and the final image rerun passes native loading and both workflow forms. No image
  has been published or deployed, and historical numerical equivalence remains unqualified. `packages/flashapp/experimental/validation/current-status.md`
  is the live checklist.
- **Desktop beyond macOS rendering.** Interactive behaviour on Windows and Linux, Qt
  plugin deployment, signing, notarization and installers have no acceptance.
- **Wheels** are built for CPython 3.12 only; **bottles** cover three platform tags.
- Source pins establish provenance, not binary compatibility: consumers must use the
  same compiler, runtime and dependency profile as the installed Core.

## Backlog

- **Warnings as errors.** The CI scripts of twelve packages (CLI, Comet,
  DatabaseSuitability, desktop, FLASH, Mascot, NASE, NuXL, OpenSWATH, ParquetDiff,
  ProSE, ProteomicsLFQ) pass `-DOPENMS4_WARNINGS_AS_ERRORS=ON`, but only TOPP and
  FLASHTnT define that option, so the others' CMake reports it as unused and their
  warnings stay warnings. At ci.4, OpenSWATH's macOS x64 cask build showed the same
  `OSWFile.h` warning that failed TOPP's. Defining the option may surface new failures,
  so it waits for a cycle of its own.
- **CPP-042 re-land.** Re-apply only the one-line suffix-loss fix in both cross-link
  spectrum generators, with absolute m/z tests for both, a CPP-042-only OpenPepXL_1 run
  and a reviewed reference update (decided 2026-09-14; kept out of ci.5 and the P0 branches).
- **Pre-existing defects found while reviewing the P0 follow-ups** (not fixed on those branches):
  - `StringUtils::skipNonWhitespace(string_view)` returns `int`, so `removeWhitespaces`
    can write before the buffer for strings over 2 GiB. Base64 no longer calls it; the
    mzML handler's default whitespace stripping still does.
  - `MzMLSqliteHandler`: a read that throws skips `sqlite3_finalize`; `sqlite3_close_v2`
    then leaves a zombie connection that keeps the file open for the process lifetime.
  - `MascotXMLHandler`: a negative `<NumQueries>` throws `std::length_error` instead of
    ParseError, and a huge one allocates and constructs one identification per declared
    query (about 5.5 GB for 5e7) before any query number is checked. Query numbers above
    the Int range are truncated by Xerces `parseInt` (4294967297 becomes 1), so the hit is
    attributed to another spectrum without an error. Confirmed again by the ci.6
    pre-release review; ci.5 behaves the same.
  - Activation-method name tables are indexed without bounds checks by `Precursor`,
    FileInfo, the mzXML writer, `RangeUtils` and `IsobaricChannelExtractor`; an
    out-of-range enum set through the API reaches them.
  - FileConverter passes `exp.size()` (the spectrum count) as the peak limit `n` of
    `MapConversion::convert`, which looks unintended.
  - The mzTab writer spells `colunit-PSM`; the specification uses `colunit-psm`.
  - `MzXMLHandler`: a scan with two `<peaks>` elements after one `<precursorMz>` fails the
    whole load ("Error during parsing of binary data"), because both payloads are buffered
    into one base64 string; the schema allows repeated `<peaks>`.
  - `MzTabFile::load` cannot read mzTab-M files (ConversionError on the SML section; ci.5
    crashed on their metadata keys instead). Use `MzTabMFile`.
- **Base64 check cost in released Core.** The CPP-055 alphabet check in core-v4.0.0-ci.3 to
  ci.5 makes decoding the arrays of a 1.77 GB uncompressed mzML (astral_7x60) take 1.57 s
  instead of 0.35 s (ci.2), about 23% of that file's 5.3 s load. The reworked check on
  `codex/p0-base64-design` decodes them in 0.45 s.
- **Casks and Core upgrades.** libOpenMS has no versioned install name, and the casks
  depend on the unversioned tap formula, so a payload built against one Core can run
  against another and corrupt memory (shown for ci.2-built TOPP tools on ci.4). The 11
  ci.2-built casks were disabled (2026-09-14) and republished for ci.5
  (2026-09-15/16); casks generated by `tools/ci-templates/update_cask.py` refuse to install
  unless the installed Core has the payload's source revision, which the cask workflow
  now exercises by installing from the tap on both macOS architectures. Upgrading
  `openms4-core` after a cask is installed is
  still not caught: a SOVERSION or install name carrying the Core cycle, or a startup
  check in the CLI that compares the linked Core revision with the one built against,
  is still needed.
- **Long paths on the self-hosted Windows box.** `DESKTOP-POHV0H0` does not have
  `LongPathsEnabled`, so creating a conda environment fails whenever a package extracts a
  path past 260 characters: Qt's headers for the desktop (261 characters) and
  `libopentelemetry-cpp-headers` for database-suitability. Both leave an unusable package
  cache behind, which micromamba reports as invalid instead of re-extracting. Both
  packages' Windows rows are generated hosted (`pool_for` in `tools/scaffold_package_ci.py`)
  until the setting is on and the two caches
  (`C:\actions-runners\OpenMS4-{desktop,database-suitability}\home\micromamba\pkgs`)
  are cleared; then that exception can go.
- **Heap-overflow regression tests outside glibc.** The CPP-005 test fails on the old code
  only under glibc malloc checking on Linux; Core CI has no AddressSanitizer job.
- **Rust port follow-up.** `OpenMS4-R` `tests/map_operations.rs` (`cm_split_error_paths`)
  still expects `ConsensusMap::split` to fail for an identification from an unknown map;
  the P0 follow-up drops such identifications with a warning instead.

## Where the documents are

| Document | Scope |
| --- | --- |
| [cpp-issues-review.md](cpp-issues-review.md) | the outcome of every C++ finding from the Rust port, CPP-001 to CPP-229 |
| [port-resumption-2026-09-13.md](port-resumption-2026-09-13.md) | Core review completion, pyOpenMS ci.3, final app image and runner fixes |
| [port-resumption-2026-09-12.md](port-resumption-2026-09-12.md) | previous: FLASHTnT integration, app runtime, fresh graph acceptance |
| [core-ci2-cycle-validation.md](core-ci2-cycle-validation.md) | the Core ci.2 release cycle, its releases and the defects it exposed |
| [build-split-packages.md](build-split-packages.md) | how to reproduce the installed-SDK build and tests |
| [split-sdk-validation.md](split-sdk-validation.md) | the first full split-SDK validation |
| [linux-hpc-validation.md](linux-hpc-validation.md) | the Linux HPC build that found the integer `abs` defect |
| [core-native-validation.md](core-native-validation.md), [topp-sdk-validation.md](topp-sdk-validation.md), [topp-runtime-report.md](topp-runtime-report.md) | earlier Core and TOPP acceptance |
| [tool-backend-refactoring.md](tool-backend-refactoring.md), [refactoring-plan.md](refactoring-plan.md) | how the boundaries were chosen |
| [reviews/](reviews/) | the adversarial cross-model reviews behind the plan |

`doc/` and `legacy/` retain the pre-split upstream documentation and packaging recipes
for reference; they are not build entry points.
