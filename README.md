# OpenMS 4 package experiment

A private, source-complete decomposition of OpenMS develop at `ca32296038839459d8c9b075b759e285913d6294`. The original OpenMS 3.6 history remains on `develop`; this experimental branch replaces the shared source build with pinned package submodules.

Read [the synthesized refactoring plan](docs/refactoring-plan.md), [the package diagram](docs/package-architecture.svg), and [validation results](docs/validation.md). The plan incorporates actual command-line reviews from Claude Fable 5.1, Kimi and Vibe; verbatim reviews and invocation metadata are in [docs/reviews](docs/reviews/).

| Submodule | Responsibility |
| --- | --- |
| [core](https://github.com/okohlbacher/OpenMS4-core) | OpenMS 4.0.0 scientific SDK, OpenSwathAlgo, versioned runtime data, core tests and optional TestSupport |
| [cli](https://github.com/okohlbacher/OpenMS4-cli) | TOPP framework, independent tool registration/versioning and executable discovery |
| [topp](https://github.com/okohlbacher/OpenMS4-topp) | 131 existing TOPP tools, including optional FeatureLinkerWNet and development utility FuzzyDiff |
| [openswath](https://github.com/okohlbacher/OpenMS4-openswath) | 19 executable front ends and their OpenSwathBase helper |
| [flash](https://github.com/okohlbacher/OpenMS4-flash) | FLASHDeconv executable and pilot regression |
| [desktop](https://github.com/okohlbacher/OpenMS4-desktop) | GUI SDK, independently configurable viewer and workflow products |
| [pyopenms](https://github.com/okohlbacher/OpenMS4-pyopenms) | Python package and unchanged nanobind implementations, consuming installed core |
| [test-data](https://github.com/okohlbacher/OpenMS4-test-data) | Versioned TOPP fixtures and preserved full numerical acceptance suite |
| [flashapp](https://github.com/okohlbacher/OpenMS4-flashapp) | Public FLASHApp snapshot migrated to verified runtime/wheel inputs |

Clone with access to the private child repositories, then initialize the immediate package submodules. Core's contrib/vcpkg and FLASHApp's Vue component retain their upstream pins; initialize those nested dependencies only when needed.

```sh
git clone --branch codex/package-split https://github.com/okohlbacher/OpenMS4-tests.git
cd OpenMS4-tests
git submodule update --init packages/core packages/cli packages/test-data packages/topp packages/openswath packages/flash packages/desktop packages/pyopenms packages/flashapp
python3 tools/validate_source.py  # Python 3.12+
```

Each package has its own CMake or Python entry point. Install the core SDK first, then CLI and fixtures, then the products. Set `CMAKE_PREFIX_PATH` to installed dependencies. Consumers require the exact version and full source commit in `dependencies.lock.json`; they never build core through `add_subdirectory`. GUI/viewer/workflow entry points share one desktop source revision initially because controllers remain intertwined. See individual package READMEs for configuration options.

The stripped Core SDK and its scientific tests now build independently on macOS arm64 in Debug mode: **709/709 CTests passed in 311.29 seconds**. The installed SDK passed with source/build paths hidden, both with and without TestSupport, and again after relocation; see the [Core native validation report](docs/core-native-validation.md) for dependency settings and coverage limits. Native validation of CLI/products, Python and desktop applications remains pending. All repositories are private and GitHub Actions are disabled. The artifact verifier rejects placeholder hashes; source pins alone do not establish binary compatibility.

The original documentation and historical packaging/deployment files are retained for reference under `doc/` and `legacy/`. Those recipes are not active package build entry points. Original file provenance is retained in each child repository; complete pre-extraction history is in this parent repository.
