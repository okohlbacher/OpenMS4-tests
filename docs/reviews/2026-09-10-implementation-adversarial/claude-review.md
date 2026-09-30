Review complete. Everything below comes from reading the checkout at the pinned commits; I ran no builds, tests, sanitizers or coverage tools.

## Findings

Priorities: P0 blocks, P1 must fix before the next gate, P2 fix during the next iteration, P3 hygiene. Confidence reflects how directly the code supports the claim.

**CF-01. One bad manifest row aborts every CLI tool and desktop app.** P1, high confidence.
- Where: `packages/cli/source/APPLICATIONS/ToolHandler.cpp:111-125` (throwing `fail` lambda, duplicate `emplace`), `packages/cli/source/APPLICATIONS/TOPPBase.cpp:129` (constructor calls `getToolVersion`), `packages/topp/src/FileInfo.cpp:195-199` (no try/catch around construction).
- Trigger and consequence: any `*.tsv` under `share/openms4/tools` in any discovered prefix that is malformed, or two prefixes that publish the same tool name (two TOPP versions on `OPENMS_TOOL_PREFIX_PATH`, or a staging prefix plus the executable's own prefix reached via a non-canonical path). `packageTools()` throws `InvalidValue` from inside every `TOPPBase` constructor, before argument parsing, so even `-help` terminates via `std::terminate`. The GUI paths (`TOPPASBase.cpp:325`, `ToolsDialog.cpp:236`) are hit the same way.
- Evidence and check: `ToolManifest_test.cpp:84-102` asserts the throw for a duplicate inside one file, so the test pins the failure mode rather than the product behaviour. No test constructs a `TOPPBase` against a conflicting registry. Reproduce by writing two manifests with the same name into two prefixes and running any tool with `-help`.
- Classification: introduced regression. The upstream compiled-in catalogue could not fail at construction.
- Fix and acceptance: make the registry tolerant. Skip and log malformed rows, resolve duplicates by prefix order (first wins, PATH semantics) and expose conflicts through `OpenMSInfo`. `getToolVersion` must be `noexcept` in effect. Add a CLI test that installs two conflicting manifests and asserts `TOPPBase::main` returns `EXECUTION_OK` for `-write_ini` and reports the first prefix's version.

**CF-02. Test fixtures live inside the versioned runtime data bundle and get copied into wheels.** P1, high confidence.
- Where: `packages/core/src/testframework/CMakeLists.txt:61-62` installs class-test data to `${INSTALL_SHARE_DIR}/test-data/core`; `packages/core/cmake/OpenMSTestSupportConfig.cmake.in:6` and `OpenMSDataConfig.cmake.in:9,19-21` build on that location; `packages/pyopenms/CMakeLists.txt:239-243,270-273` copy and install `${OPENMS_SHARE_DIR}/` excluding only `examples`.
- Trigger and consequence: the validated SDK was installed with TestSupport, and `PYOPENMS_BUILD_TESTING` requires it. A wheel built against it bundles the fixtures. The manifest already records the effect.

| Item | Value in `docs/core-sdk-manifest.json` |
|---|---|
| `data_digest.includes_optional_test_fixtures` | true |
| `data_digest.files` | 660 |
| `data_digest.bytes` | 298,366,290 |

- Evidence and check: list the pyopenms build tree after configure against the validated SDK and look for `pyopenms/share/OpenMS/test-data`.
- Classification: introduced regression (a placement decision with an unintended product effect).
- Fix and acceptance: install fixtures under `${INSTALL_CMAKE_DIR}/TestSupport/data` or `share/openms4-test-support/<version>`, update both config templates, and exclude `test-data` in the wheel copy as belt and braces. Add an `sdk_contract` assertion that `OpenMS_TEST_DATA_DIR` is not below `OpenMS_DATA_DIR`, and a pyopenms check that the assembled package contains no `test-data` directory. Recompute the data digest with fixtures excluded.

**CF-03. The installed library does not carry the source revision, so "wrong revision" checks only test CMake text.** P2, high confidence.
- Where: `packages/core/src/openms/source/CONCEPT/VersionInfo.cpp:149-152` returns `OPENMS_GIT_SHA1` (short working-tree SHA from `GIT_TRACKING`); no source under `packages/core/src/openms` references `OPENMS_SOURCE_REVISION`. `packages/core/tests/installed_sdk_acceptance/CMakeLists.txt:19-22` and `run_acceptance.py:67-73` compare configuration variables only; `data.cpp` and `api.cpp` never read a runtime revision.
- Trigger and consequence: replace `libOpenMS.dylib` with one built from another commit while keeping the config files. All 26 consumer checks still pass. The validation report's own note that the first build embedded the preceding commit and needed a metadata rebuild shows the identity is loosely coupled.
- Classification: test-quality issue and unvalidated risk.
- Fix and acceptance: configure `OPENMS_SOURCE_REVISION` into `openms_package_version.h.in`, add `VersionInfo::getSourceRevision()`, and have the data probe compare it against the value passed from CMake. Acceptance: the acceptance runner fails when the library is swapped for one from a different commit. TOPPBase's verbose version should print the same value.

**CF-04. TOPP rediscovers Boost and Eigen with a different contract than the SDK, and the Eigen request may not configure against Eigen 5.** P2, medium confidence.
- Where: `packages/topp/CMakeLists.txt:14-15` versus `packages/core/cmake/OpenMSConfig.cmake.in:10-14` and the explanatory comment at `packages/core/cmake/cmake_findExternalLibs.cmake:204-218`. `packages/pyopenms/CMakeLists.txt:35-39` instead relies on the SDK's `Eigen3::Eigen`.
- Trigger and consequence: the validated host has Eigen 5.0.1 (manifest). A plain `find_package(Eigen3 3.4 REQUIRED CONFIG)` depends on Eigen 5's version-compatibility policy, which the core deliberately avoids trusting. Both calls are redundant because `Boost::regex` and `Eigen3::Eigen` are PUBLIC interface dependencies of `OpenMS::Core` (`packages/core/src/openms/CMakeLists.txt:77-83`).
- Evidence and check: `tests/test_consumer_configure.py:26` mocks Eigen at 3.4.0, so the suite cannot observe the mismatch. Configure TOPP against a mock Eigen3 5.0.1 whose version file uses `SameMajorVersion`.
- Classification: consistency issue and unvalidated risk.
- Fix and acceptance: delete both `find_package` calls in TOPP and link the SDK-provided targets. Extend the consumer-configure test with an Eigen 5 mock.

**CF-05. The SDK pins Boost, Arrow and Parquet exactly but leaves CURL unpinned, and CURL is the dependency that actually broke.** P2, high confidence.
- Where: `packages/core/cmake/OpenMSConfig.cmake.in:9` (`find_dependency(CURL)` without version or hints) while `CURL::libcurl` is PUBLIC (`packages/core/src/openms/CMakeLists.txt:78`). `docs/core-native-validation.md:40,99-100` shows consumers needed `-DCURL_ROOT` and `CMAKE_FIND_FRAMEWORK=LAST` by hand.
- Consequence: a consumer configured without those flags can silently bind to the 7.61.1 framework, then abort in the loader. The acceptance passed only because the runner was fed the workaround.
- Classification: introduced inconsistency and unvalidated risk.
- Fix and acceptance: record `CURL_VERSION_STRING` and the resolved library path in the config, require the same major version, and emit the hint automatically. Add an `sdk_contract` case "wrong CURL version rejected" alongside the existing Arrow cases at `test_sdk_contract.py:138-148`.

**CF-06. Manifest discovery re-scans the filesystem on every call, and uses throwing filesystem overloads.** P2, high confidence.
- Where: `packages/cli/source/APPLICATIONS/ToolHandler.cpp:87-130` (`packageTools()` rebuilt per call), callers at `TOPPBase.cpp:129,159,2547,2571`, `packages/desktop/gui/source/VISUAL/TVToolDiscovery.cpp:34,87`. Lines 96 and 99 call `directory_iterator` and `weakly_canonical` without `error_code`, so permission errors surface as `std::filesystem::filesystem_error`, not an OpenMS exception.
- Consequence: a single `-write_ctd` run parses every manifest four times and walks the internal-tool directories twice. TOPPView discovery does it once per tool in 131 worker threads, serialized by a mutex.
- Classification: introduced inefficiency and poor practice.
- Fix and acceptance: cache the parsed registry behind `std::call_once` with an explicit reload hook for tests, and use `error_code` overloads. A registry class with an injectable prefix list makes this unit-testable without environment variables.

**CF-07. Testing hooks are compiled into the exported library whenever class tests are enabled, so the tested SDK is not a hook-free SDK.** P2, high confidence.
- Where: `packages/core/src/openms/CMakeLists.txt:370-372` adds `OPENMS_ENABLE_TESTING_HOOKS=1` to the `OpenMS` target itself; `docs/core-sdk-manifest.json` records `class_testing_hooks: true`; `OpenMSConfig.cmake.in:46` exports it.
- Consequence: the 709 passes and the installed hashes describe a library with hooks. A release build without hooks is a different binary that has not run the suite. The refactoring plan calls this "a risk to audit" but the build system makes it structural.
- Classification: deliberate transitional boundary with an unstated consequence.
- Fix and acceptance: either ship with hooks and say so in the release contract, or move the hooks behind a runtime seam registered by `OpenMSTestSupport.cpp`. The artifact verifier should reject a manifest that claims a test pass while `class_testing_hooks` is false.

**CF-08. Build logic is duplicated seven ways and the manifest loop has a stale-variable bug.** P2, high confidence.
- Where: `OpenMS4Dependencies.cmake` appears in seven packages with identical function line numbers (grep output). The manifest and smoke-test blocks are near-identical in `packages/topp/CMakeLists.txt:16-39`, `packages/flash/CMakeLists.txt:10-33`, `packages/openswath/CMakeLists.txt:16-40`. `tools/verify_artifacts.py` and `packages/flashapp/experimental/verify_artifacts.py` are the same text, with tests only for the parent copy.
- Bug: in `packages/topp/CMakeLists.txt:23-31` the `category` variable is never reset per tool. A tool present in `executables.cmake` but absent from `tools.json` silently inherits the previous tool's category. The parent test `test_split.py:21-30` compares `tools.json` with the inventory, not with `executables.cmake`. The JSON scan is also quadratic (131 tools times 131 lookups per configure).
- Classification: consistency and duplication, introduced.
- Fix and acceptance: publish the dependency helper from the core SDK's cmake directory or a tiny `openms4-cmake` package, add one `openms4_add_tool_package()` function, `unset(category)` per iteration with `FATAL_ERROR` when missing, and a parent test that hashes all helper copies until consolidation lands.

**CF-09. Product smoke tests assert exit codes only, including the "FLASH pilot".** P2, high confidence.
- Where: `packages/flash/CMakeLists.txt:43-44` runs FLASHDeconv to a TSV and compares nothing; `_write_ini`/`_write_ctd` tests in all three product packages check only exit status. The numerical comparison exists only in `packages/test-data/topp/CMakeLists.txt:59` and requires a complete installed suite with FuzzyDiff (`packages/test-data/CMakeLists.txt:34-36`).
- Gaps: no test asserts product-version reporting, CTD category, or prefix precedence. `TOPPBase_test.cpp` contains no `getToolVersion` or `write_ctd` assertion; `ToolManifest_test.cpp` never touches `TOPPBase`.
- Classification: test-quality issue.
- Fix and acceptance: give the FLASH package a reference-output comparison that does not require FuzzyDiff (a small comparator linked to `OpenMS::TestFramework`'s `FuzzyStringComparator`), and add a CLI test that writes a mock manifest, runs `-write_ctd`, and asserts version `7.2.1` and the category appear in the CTD.

**CF-10. Cancelling a queued FLASHApp workflow discards recorded tool PIDs instead of killing them.** P2, medium confidence.
- Where: `packages/flashapp/src/workflow/WorkflowManager.py:207-213` removes `pid_dir` after `cancel_job`; `CommandExecutor.py:133-138` records child TOPP PIDs there for exactly this purpose; `QueueManager.py:271-282` only signals the RQ work-horse.
- Consequence: whether FLASHDeconv or FLASHTnT children die depends on RQ's process-group handling, which I could not verify here. If they survive, they keep consuming CPU and memory in the shared container after "Stop". `tests/test_workflow_manager_stop.py:118-123` cements deletion of the directory without any kill.
- Related inherited race: `_start_workflow_local` creates `pid_dir` after `Process.start()` (`WorkflowManager.py:101-105`) while the child writes into it.
- Classification: inherited upstream defect inside the FLASHApp boundary; unvalidated risk.
- Fix and acceptance: signal every recorded PID (TERM, then KILL after a grace period) before removing the directory, or start tools with `start_new_session=True` and kill the group. Extend the stop test with a fake `os.kill` recorder that must see each PID.

**CF-11. Artifact verification never links the wheel, the runtime archive and the pinned core revision.** P2, medium confidence.
- Where: `tools/verify_artifacts.py:15` validates `core_source_revision` by regex only; nothing reads `pyopenms/_build_provenance.py` inside the wheel or `OpenMSConfig.cmake` inside the runtime tarball. `packages/flashapp/Dockerfile:8-13` installs a repaired wheel (own bundled `libOpenMS`) and a separate runtime under `/opt/openms4`. `packages/pyopenms/pyopenms/__init__.py:44-46` exports `OPENMS_DATA_PATH` pointing at the wheel's data, which child TOPP processes inherit through `CommandExecutor`.
- Consequence: two cores in one container with no proof they match, and tools reading the wheel's data rather than the runtime's. `packages/flashapp/dependencies.lock.json` is consumed by nothing in the app and omits CLI, although the experimental README says the runtime must include CLI libraries.
- Classification: unvalidated risk and documentation inconsistency.
- Fix and acceptance: the verifier opens the wheel zip and the tarball, reads both revisions, and fails on mismatch with the lock; `CommandExecutor` passes an explicit environment with the runtime's data directory. Add a parent `ArtifactValidation` case with a fake wheel carrying a mismatching provenance module.

**CF-12. The internal `.ttd` tool path is dead code with unsynchronized static state.** P3, high confidence.
- Where: `packages/cli/source/APPLICATIONS/ToolHandler.cpp:196-247,259-260`. The core bundle has no `share/OpenMS/TOOLS` (glob), and `docs/baseline-inventory.json` lists none either, so upstream never shipped it.
- Consequence: `getTOPPToolList` scans two nonexistent directories per call and mutates two statics without a lock. Not a demonstrated race today, since the async discovery threads only call `findExecutable`.
- Classification: inherited upstream dead code; latent concurrency hazard.
- Fix: delete the path, or make it a `call_once` initialized constant.

**CF-13. Documentation states contracts the code does not implement.** P3, high confidence.
- `packages/core/README.md:11` requires CMake 3.24; `packages/core/CMakeLists.txt:10` accepts 3.21 and sub-projects 3.15.
- `packages/core/CMakeLists.txt:69` defaults `BOOST_USE_STATIC` to ON while the preset and manifest use OFF, so a plain `cmake -S .` produces a different Boost contract from the validated one.
- `docs/core-native-validation.md:3` says the SDK "embeds the verified Core commit"; see CF-03.
- `docs/refactoring-plan.md:125` says data is versioned under `share/OpenMS/4.0.0`, but the macOS bundle fallback in `packages/core/src/openms/source/SYSTEM/File.cpp:743` still probes unversioned `share/OpenMS`.
- `packages/desktop/README.md:42-44` advertises bundle-aware discovery (`ToolHandler.cpp:56-63`) that no test exercises.
- `packages/pyopenms/pyproject.toml:69` points "Source Code" at the parent repository.

**CF-14. TOPP always requires the TestSupport component, so a runtime-only SDK cannot build the main product.** P3, high confidence.
- Where: `packages/topp/CMakeLists.txt:13,40` (FuzzyDiff links `OpenMS::TestFramework` unconditionally).
- Classification: deliberate transitional boundary, undocumented in the TOPP README.
- Fix: build FuzzyDiff only when TestSupport is present, or move `FuzzyStringComparator` into core.

**CF-15. Data-path resolution inherits fragile behaviour that the new contract now depends on.** P3, medium confidence.
- `File.cpp:106-146`: a 1024-byte buffer; Linux `readlink` truncation yields a wrong, permanently cached executable path, which feeds both `OPENMS_DATA_PATH_FROM_EXECUTABLE` and ToolHandler prefixes.
- `File.cpp:775-790`: `exit(1)` inside a function-local static initializer in a shared library. For pyopenms and GUI hosts an invalid override kills the interpreter or app with no catchable error. The acceptance wrapper hardcodes this exit code.
- Classification: inherited upstream, now foundational.
- Fix: throw for library hosts and keep `exit(1)` only in CLI `main` wrappers, and use a growable buffer.

**CF-16. Test suites that cannot run in the validated environment are counted as coverage.** P3, high confidence.
- `packages/flashapp/tests/test_workflow_manager_stop.py:31` does `importorskip("pyopenms")` although the test never uses it, so the lifecycle tests skip anywhere pyopenms is not built, and `tools/validate_source.py` never invokes them.
- `packages/pyopenms/tools/check_cmake_contract.py:20-31` hand-writes a fake `OpenMSConfig.cmake` rather than rendering `OpenMSConfig.cmake.in`, so a template rename would pass the Python contract check.
- Fix: drop the spurious skip, run the FLASHApp unit tests from the parent validator with `fakeredis`, and render the real template as `test_sdk_contract.py:61-83` already does.

**CF-17. Legacy files carried into pyopenms are dead.** P3, high confidence.
- `pyopenms_copy_deps.cmake`, `mac_fix_dependencies.rb`, `run_valgrind.sh`, `valgrind-python.supp` are referenced only by `source-provenance.json`; `NO_DEPENDENCIES` is forced ON (`CMakeLists.txt:21-23`), so the copy script can never run. Remove them or mark them archived.

**Memory and resource ownership, selectively inspected.** No statically supported leak or use-after-free was found in the areas I read.
- `packages/pyopenms/bindings/arrow_zerocopy.cpp:34-155`: `ArrowGuard` correctly distinguishes consumed structs (release nulled) from unconsumed ones on every exception path.
- `packages/core/src/openms/source/FORMAT/ParquetFile.cpp:52-95`: the abandon path closes and removes partial output. `rowCount` (line 453) lets `parquet::ParquetException` escape, an inconsistent exception contract, inherited.
- CONCEPT singletons (`GlobalExceptionHandler`, `UniqueIdGenerator`, `LogConfigHandler`) are process-lifetime with no growth path. `File::TemporaryFiles_` (`FileTemp.cpp:170-191`) grows one string per temporary file for the process lifetime; in a long-lived GUI or notebook that is bounded growth of names, not a leak.
- FLASH TOPDOWN sources contain no raw `new`/`delete`.
- Sanitizer-dependent suspicion: `TVToolDiscovery.cpp:107` calls `QCoreApplication::processEvents()` from worker threads, which Qt does not permit. Inherited; needs a runtime check under TSAN or Qt debug assertions.

## Refactoring sequence

Ordered by dependency; each step has a gate that can be checked without trusting prose.

1. **Registry hardening (CF-01, CF-06, CF-12).** Introduce a cached, non-throwing `ToolRegistry` in CLI with prefix-order precedence; TOPPBase never throws during construction. Gate: new CLI tests for conflicting prefixes, malformed rows and permission errors pass; `-help` works with a deliberately broken manifest on the path.
2. **Fixture relocation (CF-02, CF-14).** Move TestSupport data out of `share/OpenMS/<version>`; update both config templates, test-data harness and pyopenms exclusion. Gate: `sdk_contract` asserts disjoint directories; a wheel assembled against a TestSupport-enabled SDK contains no fixture files; manifest `data_digest` recomputed with `includes_optional_test_fixtures: false`.
3. **Runtime identity (CF-03, CF-07, CF-11).** Embed the source revision in `VersionInfo`; make the acceptance probe and the artifact verifier compare embedded values, not configuration text; decide and document the hook policy. Gate: acceptance fails on a swapped library; verifier rejects a wheel whose provenance disagrees with the lock.
4. **Dependency contract cleanup (CF-04, CF-05).** Pin CURL, remove product-side rediscovery, extend mock consumers with Eigen 5 and a wrong-CURL case. Gate: `test_consumer_configure` and `sdk_contract` cover both; the acceptance runner needs no manual CURL flags on the validated host.
5. **Consolidate build logic (CF-08, CF-17).** Single helper module and a shared tool-package function; delete dead pyopenms scripts. Gate: parent test proves one source of truth; a tool missing from `tools.json` fails configure.
6. **Real product assertions (CF-09, CF-16).** FLASH reference comparison, CLI CTD content assertions, FLASHApp tests runnable from the parent validator. Gate: each new test has a demonstrated failing variant (mutated reference or manifest) recorded in the validation doc.
7. **FLASHApp lifecycle (CF-10).** Kill recorded PIDs on cancel and close the local-mode race. Gate: stop test observes a kill per PID; a manual run shows no orphaned FLASHDeconv after cancel.
8. **Documentation reconciliation (CF-13, CF-15).** Align README minimums, defaults and the bundle fallback with the versioned data design; state the hook and TestSupport requirements in product READMEs.

## Coverage ledger and uncertainties

Inspected in full or in the cited ranges: `packages.lock.json`, all parent tests and tools, all `docs/*.md` except the reviewer reports, all nine package top-level CMake files and dependency locks, core `cmake/` config and export templates, `src/CMakeLists.txt`, `src/openms/CMakeLists.txt`, `configh.cmake`, testframework and class-test CMake, `SYSTEM/File.cpp`, `SYSTEM/FileTemp.cpp`, `FORMAT/ParquetFile.*`, `ParamTags.h`, `VersionInfo.cpp`, `OpenMSTestSupport.cpp`, the installed-acceptance project, the SDK contract tests, `CMakePresets.json`, core README and implementation notes; CLI `ToolHandler.*`, `TOPPBase.cpp` (constructor, main preamble, update check, write commands), `TOPPBase_defs.h`, both manifest tests, registry fixture, CLI config template; TOPP, FLASH and OpenSWATH CMake, tool lists, Percolator parity test; desktop root, gui, viewers, workflows, dependency helpers, test CMake, source-boundary tests, GUI config template, `TVToolDiscovery.cpp`, ToolHandler call sites; pyopenms CMake, pyproject, `__init__.py`, both check scripts, provenance template, `arrow_zerocopy.cpp`, fixture path helper, OWNERSHIP and VALIDATION notes; test-data CMake, config template, packaging test, harness head; FLASHApp Dockerfiles, entrypoint, artifact lock example, requirements, `QueueManager`, `WorkflowManager`, `CommandExecutor`, `tasks`, `Logger`, two lifecycle tests.

Not inspected: the 13 nanobind domain binding files and type casters beyond the zero-copy module, the OpenSwathBase implementation, the remaining 130 TOPP tool sources, GUI widget implementations, FLASH algorithm internals, the full test-data harness beyond its first 120 lines, `ClassTest.cpp`, `UpdateCheck.cpp`, vendored code (excluded by scope), and every Windows-specific branch at runtime.

Uncertainties and possible false positives:
- CF-04 depends on how Eigen 5's package version file answers a `3.4` request. If it declares any-newer compatibility the configure passes, and the finding reduces to redundancy.
- CF-10 depends on whether RQ kills the work-horse's process group. If it does, the orphan consequence disappears, but the discarded PID list remains dead state.
- CF-12's concurrency hazard is latent; I found no code path that currently mutates the statics from two threads.
- Counts of tools in `executables.cmake` and `tools.json` match today (131 and 19 by grep); the finding in CF-08 is about the absence of a guard, not a present mismatch.
- I did not confirm whether Windows `GetModuleHandleExA` with the function-pointer anchor in `ToolHandler.cpp:66-67` behaves under incremental linking; the same pattern in `File.cpp` uses a data anchor, which is the safer choice.