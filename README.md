# OpenMS 4 package experiment

**[State of the project](docs/project-state.md)** — the current picture in one page:
the eighteen packages and their pins, what is released and delivered, what the last
verification proved, what is not qualified, and where every other report fits.

The [latest port review and acceptance report](docs/port-resumption-2026-09-12.md) records the remaining work, new FLASHTnT package and fresh consumer tests. The [Core ci.2 integration report](docs/core-ci2-cycle-validation.md) records the released SDK graph, five-platform CI and 2,041 installed-tool regression checks. Use the [installed-SDK build instructions](docs/build-split-packages.md) to reproduce the consumer build and tests.

The [tool backend extraction plan](docs/tool-backend-refactoring.md) describes the original 17-package layout and retained Core format support. The additional FLASHTnT package ports FLASHApp's previously external tagging executable. ProSE and FLASH provide installed backend SDKs for Python. Complete FLASHApp runtime/image acceptance remains separate from the native package and wheel tests.

A source-complete decomposition of OpenMS develop at `ca32296038839459d8c9b075b759e285913d6294`. The original OpenMS 3.6 history remains on `develop`; this experimental branch replaces the shared source build with pinned package submodules.

Read [the synthesized refactoring plan](docs/refactoring-plan.md), [the package diagram](docs/package-architecture.svg), and [validation results](docs/validation.md). The plan incorporates actual command-line reviews from Claude Fable 5.1, Kimi and Vibe; verbatim reviews and invocation metadata are in [docs/reviews](docs/reviews/).

The subsequent [implementation audit](docs/reviews/2026-09-10-implementation-adversarial/review.md) cross-checks fresh Claude, Kimi and Vibe reviews against the extracted packages. The resulting [refactoring implementation and validation matrix](docs/implementation-2026-09-10/README.md) records the fixes, removed obsolete code, native builds, numerical tests, source identity and remaining publication gates. The original audit and plan are retained as dated evidence.

| Submodule | Responsibility |
| --- | --- |
| [core](https://github.com/okohlbacher/OpenMS4-core) | OpenMS 4.0.0 scientific SDK, OpenSwathAlgo, versioned runtime data, core tests and optional TestSupport |
| [cli](https://github.com/okohlbacher/OpenMS4-cli) | TOPP framework, independent tool registration/versioning and executable discovery |
| [topp](https://github.com/okohlbacher/OpenMS4-topp) | 123 remaining TOPP tools, including optional FeatureLinkerWNet and development utility FuzzyDiff |
| [openswath](https://github.com/okohlbacher/OpenMS4-openswath) | 19 executable front ends and their OpenSwathBase helper |
| [flash](https://github.com/okohlbacher/OpenMS4-flash) | FLASHDeconv, independently linkable FLASH backend and algorithm/format-contract regressions |
| [flashtnt](https://github.com/okohlbacher/OpenMS4-flashtnt) | Experimental FLASHTnT tagging executable consuming installed Core, CLI and FLASH SDKs |
| [desktop](https://github.com/okohlbacher/OpenMS4-desktop) | GUI SDK, independently configurable viewer and workflow products |
| [pyopenms](https://github.com/okohlbacher/OpenMS4-pyopenms) | Python bindings, complete Arrow stream conversion and runtime-only wheels consuming installed Core |
| [nuxl](https://github.com/okohlbacher/OpenMS4-nuxl) | OpenNuXL search algorithms, executable, presets and tests; format writers remain Core |
| [prose](https://github.com/okohlbacher/OpenMS4-prose) | ProSE executable and standalone scientific backend usable by Python |
| [nase](https://github.com/okohlbacher/OpenMS4-nase) | NucleicAcidSearchEngine executable; shared NA chemistry remains Core |
| [comet](https://github.com/okohlbacher/OpenMS4-comet) | CometAdapter and native-ID adaptation |
| [mascot](https://github.com/okohlbacher/OpenMS4-mascot) | MascotAdapterOnline and service transport |
| [database-suitability](https://github.com/okohlbacher/OpenMS4-database-suitability) | DatabaseSuitability and its search-adapter workflow |
| [proteomics-lfq](https://github.com/okohlbacher/OpenMS4-proteomics-lfq) | ProteomicsLFQ and workflow recipes |
| [parquet-diff](https://github.com/okohlbacher/OpenMS4-parquet-diff) | ParquetDiff comparison; generic Parquet I/O remains Core |
| [test-data](https://github.com/okohlbacher/OpenMS4-test-data) | Versioned TOPP fixtures and preserved full numerical acceptance suite |
| [flashapp](https://github.com/okohlbacher/OpenMS4-flashapp) | Public FLASHApp snapshot migrated to verified runtime/wheel inputs |

The integration, FLASHApp and experimental FLASHTnT repositories require access; the released native package repositories are public. Initialize the immediate package submodules below. Core's contrib/vcpkg and FLASHApp's Vue component retain their upstream pins; initialize those nested dependencies only when needed.

```sh
git clone --branch codex/package-split https://github.com/okohlbacher/OpenMS4-tests.git
cd OpenMS4-tests
git submodule update --init packages/core packages/cli packages/test-data packages/topp packages/openswath packages/flash packages/flashtnt packages/desktop packages/pyopenms packages/flashapp packages/nuxl packages/prose packages/nase packages/comet packages/mascot packages/database-suitability packages/proteomics-lfq packages/parquet-diff
python3 tools/validate_source.py  # Python 3.12+
```

The [Core ci.2 Release integration report](docs/core-ci2-cycle-validation.md) records the qualified release cycle. Use [the package build runner](docs/build-split-packages.md) to reproduce the installed dependency graph, including additional packages in the current lock.

Each package has its own CMake or Python entry point. Install the core SDK first, then CLI and fixtures, then the products. Set `CMAKE_PREFIX_PATH` to installed dependencies. Consumers require the exact version and full source commit in `dependencies.lock.json`; they never build core through `add_subdirectory`. GUI/viewer/workflow entry points share one desktop source revision initially because controllers remain intertwined. See individual package READMEs for configuration options.

Before the backend extraction, Core passed **712/712 Debug CTests** and installed/relocated SDK checks in Debug and Release. Native CI now covers the released consumers on Linux x64/ARM64, macOS x64/ARM64 and Windows x64. FLASHApp CI exercises its frozen dependencies and a verified released pyOpenMS wheel. See the dated reports for exact revisions and limitations; the [earlier Core report](docs/core-native-validation.md) remains historical. Source pins alone do not establish binary compatibility; the runtime and artifact checks validate additional identity and ABI metadata.

Before this backend extraction, the [standalone TOPP SDK build](docs/topp-sdk-validation.md) validated the earlier TOPP pin with the original repositories and build trees inaccessible: 130 tools, 258 metadata tests and 338 installed numerical/negative tests passed. Its subsequent [complete runnable TOPP test and runtime report](docs/topp-runtime-report.md) records 1,948 checks passed, five skipped and zero failures in 342.03 seconds, plus repeated TICCalculator reading benchmarks.

The original documentation and historical packaging/deployment files are retained for reference under `doc/` and `legacy/`. Those recipes are not active package build entry points. Original file provenance is retained in each child repository; complete pre-extraction history is in this parent repository.
