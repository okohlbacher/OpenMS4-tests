# Kimi AR-11 / AR-16 contract crosscheck

Read-only verification of the reviewed checkout at parent `7fb0147c341912b36f13f2ce05ef53a192b8dfff`. No source edits, configuration, builds or tests were run. This assessment is separate from Kimi's verbatim report and applies Ponytail's minimal-change rule to its proposed fixes.

## AR-11: narrow the layout claim; retain the negative-test concern

**A flat custom binary directory already works.** The harness searches `${OPENMS4_TOOLS_BIN}/../share/openms4/tools/*.tools.tsv` at `packages/test-data/CMakeLists.txt:39`. Path resolution gives:

| Binary directory | Manifest directory searched | Result |
| --- | --- | --- |
| `/stage/bin` | `/stage/share/openms4/tools` | Intended layout |
| `/stage/custom-bin` | `/stage/share/openms4/tools` | Same successful lookup; the basename need not be `bin` |
| `/stage/libexec/openms4` | `/stage/libexec/share/openms4/tools` | Does not find manifests installed under `/stage/share/openms4/tools` |

Kimi's cited `tests/test_consumer_configure.py:37,43–44` covers the flat `custom-bin` case, so it does not demonstrate the reported incompatibility. It is a product configure/manifest test, not a test-data harness registration test. A flat-custom harness test would usefully cover the existing behavior. The nested-directory discovery limitation is real, although it can already be bypassed with the documented `OPENMS4_TOOL_NAMES` input if all suite binaries reside in that nested directory.

**The harness deliberately consumes a staged suite directory, not arbitrary executable locations from manifests.** `packages/test-data/README.md:17–30` explicitly requires the complete suite's binary directory, permits a staging prefix combining separately built products, and says manifests determine tool **names**. The CMake implementation checks FuzzyDiff in that directory at `34–35`, reads the first manifest column at `41–44`, validates every name there at `53–56`, and sets `CMAKE_RUNTIME_OUTPUT_DIRECTORY` to it at `58`. The preserved numerical suite then derives `TOPP_BIN_PATH` at `topp/CMakeLists.txt:50` and uses `${TOPP_BIN_PATH}/ToolName` throughout, including FuzzyDiff at `59` and INI/CTD tests at `83,97`.

Ignoring the fourth column is therefore an explicit transitional staging limitation, not an undisclosed promise that arbitrary per-tool paths work. Changing only manifest parsing would not make the numerical suite accept dispersed product directories: its many direct executable paths would still use the single staging directory. Keep the existing contract, add a flat-custom registration case, and document the nested-directory override. Introduce arbitrary executable mapping only if that acceptance mode is required, with corresponding changes across the preserved suite. Do not infer that a new manifest resolver is necessary merely from the existing product-side path flexibility.

**`WILL_FAIL` accepts the wrong ordinary failure, but does not universally accept crashes.** The cited `topp/CMakeLists.txt:111–134` registers direct executable commands and inverts their exit status without checking the expected diagnostic. An unrelated ordinary nonzero exit can satisfy these tests. There are 27 `WILL_FAIL` declarations in the top-level preserved numerical harness; this is a source count, not a count of tests run or a complete inventory of included files.

Kimi's claim that these tests pass on “any failure including segfaults” is too broad. CTest documents that timeouts still fail and system-level failures such as segmentation faults or signal aborts may fail despite `WILL_FAIL`. Wrapping a process can convert its crash into an ordinary wrapper exit code and lose that distinction; the cited numerical tests directly invoke the tool, while runtime data is supplied through the test's `ENVIRONMENT` property at the end of the file. [CMake WILL_FAIL documentation](https://cmake.org/cmake/help/latest/prop_test/WILL_FAIL.html), inspected 10 September 2026.

The retained gap is failure **reason**: wrong input/setup errors, and loader failures that return an ordinary nonzero status, can be false positives. Progressively require the expected status and a distinctive diagnostic for high-value negative tests. Reuse the exact-assertion pattern from `ExpectInvalidDataOverride.cmake`, with each TOPP test's own expected error; do not reuse that wrapper's literal data-override diagnostic for unrelated tests. A useful gate deliberately substitutes an unrelated ordinary failure and proves the test rejects it. No such substitution was executed here.

## AR-16: accept the fixture guard issue; reject optional runtime WebEngine

**An empty fixture directory is currently accepted.** `packages/core/cmake/OpenMSDataConfig.cmake.in:18–21` sets `OpenMSData_TestSupport_FOUND` solely through `IS_DIRECTORY`. The existing contract test actually creates an empty `test-data/core` directory and expects success (`packages/core/tests/sdk_contract/test_sdk_contract.py:244–247`). This proves the weakness is encoded in the test, rather than being a hypothetical reading of CMake behavior. The harness references real Core fixtures, for example `MSPGenericFile_input.msp` in its FileConverter case; directory existence does not establish that payload.

Kimi's comparison with the full SDK config is inaccurate: `OpenMSTestSupportConfig.cmake.in:3–6` **sets paths**, then unconditionally sets `OpenMS_TestSupport_FOUND TRUE` at `7`. Those assignments do not check that the support source, header template, or fixture files exist. Including `OpenMSTestSupportTargets.cmake` validates whatever that export checks, but it is not fixture-content validation. The separate installed acceptance project adds explicit `EXISTS` checks for three exported paths (`tests/installed_sdk_acceptance/CMakeLists.txt:65–69`); even its fixture-directory check does not prove a nonempty payload.

The smallest justified correction is a known owned fixture sentinel, checked in both TestSupport discovery paths, with a regression that rejects an empty fixture directory and accepts one containing the sentinel. `MSPGenericFile_input.msp` is an existing real Core fixture used by the downstream suite and is a possible choice. Keep the data-only package compiler-free. A sentinel proves the installation is not empty; do not describe it as an exhaustive fixture-integrity check. Full content integrity, when needed, belongs to the artifact manifest/digest contract.

**A GUI SDK built with WebEngine must continue to require it.** `packages/desktop/gui/CMakeLists.txt:14–25` optionally discovers WebEngine while **building** the GUI. When available, it appends `WebEngineWidgets` to `_qt_components`, then publicly links every selected Qt component at `41–43`. The generated `OpenMSGUIConfig.cmake.in:11` correctly rediscovers those dependencies before importing `OpenMS::GUI`.

This is not merely an unnecessary discovered package: `SequenceVisualizer.cpp:9–26` conditionally includes QtWebEngineWidgets and constructs `QWebEngineView`, and related GUI code is compiled under `QT_WEBENGINEWIDGETS_LIB`. An installed binary compiled with that feature depends on it. Quietly ignoring the absent WebEngine package at consumer configure time cannot remove compiled symbol references or the public target dependency, and can move a useful configure failure to link/load time.

Reject Kimi's proposed gate that a consumer without WebEngine should accept a GUI SDK built with it. The correct two-profile gate is: a GUI built with `OPENMS_GUI_WEBENGINE=OFF` remains discoverable without WebEngine; a GUI built with it enabled and linked requires WebEngine in its consumer environment. Exporting a resolved `OpenMSGUI_WITH_WEBENGINE` feature value could improve introspection if consumers need it, but it is not necessary to fix the alleged contradiction. The upstream “optional/warning” guidance applies to selecting a build feature, not to removing dependencies from an already-built library.

## Disposition

| Subclaim | Verdict |
| --- | --- |
| Flat `custom-bin` breaks harness discovery | Rejected by the path expression |
| Nested bindir breaks automatic manifest discovery | Supported; explicit tool names remain an existing workaround |
| Fourth manifest column is ignored | True, within the documented complete-suite staging contract |
| All segfaults pass with `WILL_FAIL` | Rejected as universal claim |
| Unrelated ordinary failures can satisfy negative tests | Supported inherited test-quality limitation |
| Empty fixture directory passes TestSupport discovery | Supported, including the current regression-test expectation |
| Full TestSupport config verifies listed fixture paths | Rejected; it assigns them |
| WebEngine may be made optional for a binary linked against it | Rejected; retain the recorded runtime dependency |

Parent, Core, test-data and desktop Git status remained clean after this crosscheck. Only this review artifact was written.
