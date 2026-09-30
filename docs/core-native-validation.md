# Core SDK native validation

*Part of the [OpenMS 4 package split](../README.md). [State of the project](project-state.md) · [Package architecture](package-architecture.svg) · [Build instructions](build-split-packages.md)*

This is the historical Debug validation of Core `21b295c`. For the current
build-system cleanup, pinned package graph and platform CI results, see
[the current SDK validation report](split-sdk-validation.md).

**Passed on macOS arm64 Debug: standalone Core compilation, 709/709 scientific CTests, and installed SDK acceptance before and after relocation.** The final SDK embeds Core commit `21b295c9ad889b402db1e3a20f13e8d08330b61b`; its library hashes and build identity are recorded in [core-sdk-manifest.json](core-sdk-manifest.json).

**Subsequent audit clarification, 10 September 2026:** the runtime revision API returns a short Git revision; full configured source identity was not compared with the loaded binary by these acceptance tests. The manifest's `class_testing_hooks` field records class-test enablement through an unused macro, not implemented hook code. These terminology corrections leave the recorded compilation, test results and artifact hashes intact. See [A03 and A14 in the implementation audit](reviews/2026-09-10-implementation-adversarial/review.md) for the evidence and follow-up gates.

## Scope and configuration

The source is [packages/core](../packages/core), backed by [OpenMS4-core](https://github.com/okohlbacher/OpenMS4-core). It builds the scientific Core library, OpenSwathAlgo, development TestSupport and their tests. No Qt GUI, TOPP executable, CLI package or Python binding sources are compiled.

| Setting | Observed value |
|---|---|
| Core version / platform | Experimental 4.0.0 / macOS arm64 |
| Compiler / language | AppleClang 21.0.0.21000101 / C++23 |
| Configuration | Debug, shared Core libraries, Ninja, `core-debug` preset |
| Dependencies | Installed Homebrew/system libraries; vcpkg disabled |
| Boost / Eigen | 1.90.0 shared / 5.0.1 |
| Arrow / Parquet | 25.0.0 shared / 25.0.0 shared |
| Corrected CURL | 8.21.0, `/opt/homebrew/opt/curl/lib/libcurl.dylib` |
| OpenMP / LP solver | Homebrew libomp discovered through prefix / COIN-OR |
| Enabled | OpenSWATH algorithms, class tests, TestSupport |
| Disabled | HDF5, ONNX, WNetAlign, TDL, opentims, Thermo RAW and their downloaded integration fixtures |

The compile database contains **1,523 unique source compilations**: 1,522 C++ files and one C file, including unchanged vendored code and scientific tests. A path audit found zero product/GUI/Python source entries. CTest registers **709 tests**: 702 Core class tests, five OpenSwathAlgo tests and two data-path policy tests. OpenSwathAlgo tests link without libOpenMS; Core test initialization is compiled once as an object library and included in every Core test executable.

## Observed results

| Stage | Result |
|---|---|
| Complete package source/configuration validation | **Passed: 62/62**, including 10 Core SDK contracts and nine negative-assertion regressions. |
| Initial native compilation | **Completed.** Incremental invocation ended at 1,790/1,790 steps. |
| Corrected dependency rebuild | **Completed: 2,160/2,160 steps**, ending with `CoreDataPath_probe` in `build-curl.log`. |
| Invalid-override assertion regressions | **Passed: 9/9.** Controlled subprocess tests reject unrelated errors, crashes and loader failures. |
| Final metadata rebuild and focused native rerun | **Passed: 7/7.** Version/build metadata, File, CTD, Percolator PIN checks and both data-path cases after embedding the committed revision. |
| Complete scientific suite | **Passed: 709/709, zero failed, 311.29 seconds.** Slow PipEcho: 55.73 seconds; FLASH algorithm: 205.26 seconds. Optional subprocess coverage is qualified below. |
| SDK without TestSupport | **Passed: 6/6 at the original prefix and 6/6 after relocation.** Explicitly requiring absent TestSupport was rejected. |
| SDK with TestSupport | **Passed: 7/7 at each prefix.** Installed fixtures, headers and deterministic test initialization were exercised. |
| Source/build isolation and pin enforcement | **Passed in both SDK runs.** Original Core source/build paths were absent; paths were restored afterward. Wrong source revisions were rejected. |
| Final Core source identity | **Verified:** `21b295c9ad889b402db1e3a20f13e8d08330b61b` in installed configs and all four consumer metadata records. All eight consumer locks and nine parent gitlinks were updated. |
| Local installed SDK | `core-sdk/`, with SHA-256 hashes for all five installed libraries/archives in the [manifest](core-sdk-manifest.json). No bundled distribution archive or binary release was published. |

Two host dependency issues were observed. First, CMake selected an older `/Library/Frameworks/libcurl.framework` (7.61.1); libOpenMS consumers then aborted in dyld before assertions. Selecting Homebrew CURL and `CMAKE_FIND_FRAMEWORK=LAST` corrected discovery, followed by the completed rebuild. The interrupted first runtime attempt is preserved separately and is not a full-suite result.

Second, this host's installed re2 expects Abseil **2601**, while the Homebrew `opt` link resolves to **2605**. The already installed `/opt/homebrew/Cellar/abseil/20260107.1/lib` supplies the required libraries. An explicit `DYLD_FALLBACK_LIBRARY_PATH` to that directory allows the full suite and installed/relocated SDK consumers to run. No dependency, system framework, Homebrew link or third-party source was modified. This host-specific runtime dependency remains part of the validation environment, not a self-contained redistribution solution.

Invalid-data-override tests now use an automated subprocess assertion requiring **exit code 1 and the exact OpenMS diagnostic naming the rejected override**. The wrapper rejects loader/crash diagnostics even when mixed with expected text. It replaces generic `WILL_FAIL`, which could count an unrelated loader failure as success; manual log inspection is not the acceptance criterion.

## Reproduce the build and runtime suite

Start in the exploration workspace containing `OpenMS4-tests`. Use fresh build/install directories, or clear cached CURL discovery as shown. Adapt dependency prefixes to another host and match the compiler, architecture and configuration of all consumers.

```bash
openms4_workspace="$PWD"
openms4_core="$openms4_workspace/OpenMS4-tests/packages/core"
openms4_build="$openms4_workspace/core-build"
openms4_sdk="$openms4_workspace/core-sdk"
openms4_abseil=/opt/homebrew/Cellar/abseil/20260107.1/lib
cd "$openms4_core"
cmake --preset core-debug -G Ninja -B "$openms4_build" -U 'CURL_*' \
  -DCMAKE_INSTALL_PREFIX="$openms4_sdk" \
  -DCMAKE_PREFIX_PATH="/opt/homebrew;/opt/homebrew/opt/libomp" \
  -DLP_SOLVER=COIN -DCURL_ROOT=/opt/homebrew/opt/curl \
  -DCMAKE_FIND_FRAMEWORK=LAST
cmake --build "$openms4_build" --parallel 12

env -u OPENMS_DATA_PATH -u OPENMS_HOME_PATH -u DYLD_LIBRARY_PATH \
  -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  -u http_proxy -u https_proxy -u all_proxy \
  DYLD_FALLBACK_LIBRARY_PATH="$openms4_abseil" \
  OPENMS_RUN_SLOW_TESTS=1 OMP_NUM_THREADS=2 \
  ctest --test-dir "$openms4_build" -C Debug \
  --parallel 8 --timeout 1800 --output-on-failure
```

Run one suite at a time: some older tests retain fixed temporary filenames. Proxy removal preserves reserved `.invalid` DNS-failure expectations. `OPENMS_RUN_SLOW_TESTS=1` enables realistic PipEcho numerical work; `OMP_NUM_THREADS=2` limits oversubscription without imposing a thread limit on tests requesting more threads. External Percolator subprocess sections require PATH discovery or `PERCOLATOR_BINARY_FOR_TEST`; absent sections report their skipped dependency, while in-process/PIN-stamp checks remain active. Disabled integrations are outside this profile.

## Install and accept independent consumers

To validate component separation, first install into a fresh prefix without TestSupport:

```bash
for component in library OpenMS_headers OpenSwathAlgo_headers thirdparty_headers cmake share; do
  cmake --install "$openms4_build" --prefix "$openms4_sdk" --config Debug --component "$component"
done
```

Run the [installed acceptance project](../packages/core/tests/installed_sdk_acceptance) with `--cmake-argument=-DOPENMS_ACCEPTANCE_TEST_SUPPORT=OFF` and a fresh work directory; requiring absent TestSupport must fail discovery. Then add `--component TestSupport` and run the full acceptance. A default install includes TestSupport and cannot demonstrate its absence.

After committing the final Core source, set `openms4_revision=$(git -C "$openms4_core" rev-parse HEAD)`, reconfigure with `-DOPENMS_SOURCE_REVISION="$openms4_revision"`, rebuild affected metadata/library objects, reinstall and repeat acceptance against that identity. The development build initially embedded the preceding commit `7c029e8cdba6abab503708ecdd56f6ab55e38ce4`; that alone does not identify the uncommitted changes under test.

```bash
openms4_probe_source="$openms4_workspace/core-sdk-consumer-source"
cp -R "$openms4_core/tests/installed_sdk_acceptance" "$openms4_probe_source"
env -u OPENMS_DATA_PATH -u DYLD_LIBRARY_PATH \
  DYLD_FALLBACK_LIBRARY_PATH="$openms4_abseil" OMP_NUM_THREADS=2 \
  python3 "$openms4_probe_source/run_acceptance.py" \
  --sdk-prefix "$openms4_sdk" \
  --work-dir "$openms4_workspace/core-sdk-acceptance" \
  --dependency-prefix /opt/homebrew --dependency-prefix /opt/homebrew/opt/libomp \
  --configuration Debug --jobs 2 --expected-revision "$openms4_revision" \
  --cmake-argument=-DCURL_ROOT=/opt/homebrew/opt/curl \
  --cmake-argument=-DCMAKE_FIND_FRAMEWORK=LAST
```

Use new/empty probe and acceptance directories. The driver compiles independent public-API, Eigen, Arrow/Parquet, data-path and TestSupport consumers, then repeats after copying the SDK. It checks both the loaded library and resolved data location, and rejects the wrong source revision. Native dependencies remain installed at their original locations; these checks address SDK relocation, not a fully bundled distribution. Its `results.json` and numbered logs capture command-level evidence.

## Evidence and remaining scope

Evidence is in the workspace's `core-build-evidence/`: `source-validation-final.log`, `source-boundary.json`, `ctest.log`, `ctest-results.xml`, `configure-final.log`, `build-final.log`, `ctest-final-focused.log`, `installed-acceptance-library.log`, `installed-acceptance-support.log`, `isolation-library.json`, `isolation-support.json`, and `library-dependencies.txt`. Earlier compile/loader failures remain in their separate attempt logs. The acceptance directories `core-sdk-acceptance-library/` and `core-sdk-acceptance-support/` contain original and relocated consumer builds, seven command results each, and detailed CTest logs.

The final installed `OpenMS_SOURCE_REVISION` and every consumer `accepted-sdk.txt` match the committed Core SHA. Library dependency inspection found no Qt, CLI, Python or obsolete curl-framework linkage. The manifest hashes the actual tested installed files. Source pins were propagated through CLI/test-data, dependent tools/desktop/Python, FLASHApp and the parent lock/gitlinks; these updates do not establish downstream runtime acceptance. macOS Debug results do not establish Linux, Windows, Release, optional-reader/model, Python-wheel or fully bundled deployment acceptance.

An existing FLASH test coverage limitation was observed: some FDR/merging-labelled sections still set legacy parameter keys, while the algorithm reads `report_FDR` and `merging_method`. Those labels should not be treated as proof of the intended modes; correcting that upstream test coverage is separate from this extraction. No scientific algorithm or vendored dependency source was changed in this build-hardening step.
