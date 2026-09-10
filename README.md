# OpenMS 4 package experiment

The [current SDK integration report](docs/split-sdk-validation.md) records the simplified Core build, platform CI and the freshly tested package graph. Use the [installed-SDK build instructions](docs/build-split-packages.md) to reproduce the consumer build and tests.

The [tool backend extraction plan](docs/tool-backend-refactoring.md) describes the current 17-package layout and retained Core format support. The [build and test report](docs/tool-backend-validation.md) records the implemented boundaries and native validation. ProSE and FLASH provide optional installed backend SDKs for Python; FLASHApp now follows the same SDK graph; its external FLASHTnT dependency remains a separate deployment gate.

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

Clone with access to the private child repositories, then initialize the immediate package submodules. Core's contrib/vcpkg and FLASHApp's Vue component retain their upstream pins; initialize those nested dependencies only when needed.

```sh
git clone --branch codex/package-split https://github.com/okohlbacher/OpenMS4-tests.git
cd OpenMS4-tests
git submodule update --init packages/core packages/cli packages/test-data packages/topp packages/openswath packages/flash packages/desktop packages/pyopenms packages/flashapp packages/nuxl packages/prose packages/nase packages/comet packages/mascot packages/database-suitability packages/proteomics-lfq packages/parquet-diff
python3 tools/validate_source.py  # Python 3.12+
```

The [current Release integration report](docs/split-sdk-validation.md) records fresh builds and numerical tests against the simplified SDK. Use [the package build runner](docs/build-split-packages.md) to reproduce the installed dependency graph.

Each package has its own CMake or Python entry point. Install the core SDK first, then CLI and fixtures, then the products. Set `CMAKE_PREFIX_PATH` to installed dependencies. Consumers require the exact version and full source commit in `dependencies.lock.json`; they never build core through `add_subdirectory`. GUI/viewer/workflow entry points share one desktop source revision initially because controllers remain intertwined. See individual package READMEs for configuration options.

Before the backend extraction, Core passed **712/712 Debug CTests** and installed/relocated SDK checks in Debug and Release. CLI, all enabled TOPP/OpenSWATH/FLASH tools and desktop products build against installed dependencies and have native acceptance evidence. See the [current implementation report](docs/implementation-2026-09-10/README.md) for exact tests, wheel/runtime artifacts and limitations; the [earlier Core report](docs/core-native-validation.md) remains historical. Core is public; the other package repositories remain private. Core native CI and FLASHApp contract CI are enabled. Source pins alone do not establish binary compatibility; the runtime and artifact checks validate additional identity and ABI metadata.

Before this backend extraction, the [standalone TOPP SDK build](docs/topp-sdk-validation.md) validated the earlier TOPP pin with the original repositories and build trees inaccessible: 130 tools, 258 metadata tests and 338 installed numerical/negative tests passed. Its subsequent [complete runnable TOPP test and runtime report](docs/topp-runtime-report.md) records 1,948 checks passed, five skipped and zero failures in 342.03 seconds, plus repeated TICCalculator reading benchmarks.

The original documentation and historical packaging/deployment files are retained for reference under `doc/` and `legacy/`. Those recipes are not active package build entry points. Original file provenance is retained in each child repository; complete pre-extraction history is in this parent repository.
