# Adversarial review of the OpenMS 4 package implementation

The package split is worth keeping, but the current evidence establishes a working macOS Debug Core SDK, not independently deployable products. The highest-priority gaps are installed consumer loading, the redundant TOPP dependency lookup, binary/artifact identity, and inherited Arrow import behavior that can lose rows. The review also found test claims that are stronger than the exercised behavior, duplicated build policy, and inherited workflow resource-management defects.

This is an audit and refactoring plan. No scientific, application, packaging or vendored implementation source was changed during the audit. Ponytail was installed locally and applied as a simplification audit. Read the [implementation plan](refactoring-plan.md) and [Ponytail deletion/simplification list](ponytail-audit.md) for the proposed work.

## Snapshot and method

Reviewed parent `7fb0147c341912b36f13f2ce05ef53a192b8dfff`, Core `21b295c9ad889b402db1e3a20f13e8d08330b61b`, and the other eight exact child revisions in [reviewed-revisions.json](reviewed-revisions.json). Source stayed frozen while the independent command-line reviewers ran. OpenMS inherited code was compared with `ca32296038839459d8c9b075b759e285913d6294`; FLASHApp with imported upstream `f8e9eba435ea0843660c63fe86c58c64798e7f71`.

The same adversarial brief covered structure, consistency, duplication, tests, performance, ownership/lifetimes, bugs and documentation. The CLI reviewers had read/search tools only. Their reports are untrusted review inputs: the synthesis verifies their claims and preserves rejected claims in separate triage documents. Actual command identities, source hashes and raw-output hashes are recorded alongside each report. Raw streaming logs remain in the local review workspace; verbatim reports and compact provenance are retained with this document.

Root verification added controlled production-method probes, two configure-only dependency/metadata probes, a real installed-SDK CLI configuration, a PyArrow boundary check, and source/provenance comparisons. No new native OpenMS compilation, wheel/image build, sanitizer run or instrumented coverage collection was performed in this audit.

A late targeted check ran the existing `FeatureMapArrowIO_test` binary successfully, but attempts to obtain a macOS `leaks` allocation report were inconclusive: initial task-port access failed, a permitted attempt hit the known dependency loader issue, and the launcher-corrected test passed without a valid leak summary. The tool's zero exit code alone was not accepted as leak-check success. [Attempt records](memory-check-attempt.json) preserve all three outcomes; no dependency or test binary was modified.

## Independent review inputs and synthesis

- **Claude:** CLI 2.1.261, actual `claude-fable-5-1`, high effort, 191 read/search calls, successful completion. [Verbatim report](claude-review.md), [all 17 findings verified](claude-verification.md), [invocation and hashes](claude-metadata.json). Its fixture, dependency, identity, metadata and product-test findings contributed to the plan. Proposed permissive duplicate handling, deletion of user TTD extensions, a Qt worker-thread prohibition and removing an app test's import skip without isolating its real dependency were rejected or corrected.
- **Vibe:** CLI 2.25.1, 42 successful read/search calls, successful completion. The configured `mistral-large-4` was unavailable, so a per-invocation override used the previously working `mistral-medium-3.5` alias, configured as provider request `mistral-vibe-cli-latest`; no global model configuration changed. [Verbatim report](vibe-review.md), [all 14 IDs triaged](vibe-triage.md), [invocation and hashes](vibe-invocation.json). Nine findings were rejected, three narrowed, one retained as optional cleanup and one withdrawn by Vibe. Neither claimed P0 survived verification. Its own coverage ledger overstates some reads; the triage corrects that against actual tool evidence.
- **Kimi:** CLI 0.42.0, configured alias `kimi-code/k3` using model `k3`, 177 read/search calls, successful completion. The stream did not expose a server-resolved model/build identifier. [Verbatim report](kimi-review.md), [all 18 IDs triaged](kimi-triage.md), [invocation and hashes](kimi-invocation.json). Its unused test-hook flag, empty-fixture discovery, documentation and queue-state findings strengthened the plan. Its claimed loss of tool types is contradicted by the baseline test, which already expects empty types. Missing worker UI/preset failures, optional runtime WebEngine for a linked GUI, and claims that every crash satisfies CTest `WILL_FAIL` were rejected or narrowed. [Contract crosscheck](kimi-contract-crosscheck.md) and [FLASHApp crosscheck](kimi-ar13-crosscheck.md) retain the detailed evidence.

The plan follows source evidence and acceptance gaps, not a majority vote between models. Root/independent verification also found or reproduced the installed CLI loader-path gap, Arrow batch boundary, FLASH mode coverage defect, executor failures and version-initialization race. Each is labelled by origin and evidence below. Ponytail's locally installed instructions supplied the simplification criteria; they did not establish correctness or memory safety.

## Accepted findings

Priorities mean **P1: fix before the relevant product gate**, **P2: fix in the next refactoring iteration**, **P3: cleanup**. None is classified as a demonstrated P0. Confidence and evidence depth are separate: a clear source defect can be high confidence without a native end-to-end reproduction.

### A01 — TOPP rejects the dependency profile already accepted by Core

**P1; introduced; reproduced configuration failure.** `packages/topp/CMakeLists.txt:14–15` rediscovers Boost and Eigen after importing the pinned SDK. The explicit `find_package(Eigen3 3.4 REQUIRED CONFIG)` rejects the host's Eigen 5.0.1, even though Core was built and validated against it. An isolated project executing that exact request fails with the incompatible-version diagnostic; see [eigen-configure-probe.json](eigen-configure-probe.json). This corroborates Claude CF-04 and resolves its uncertainty on this host.

Delete the redundant discovery and use the SDK's public imported targets. A mock SDK containing Eigen 3.4 cannot expose this failure; acceptance must include the actual validated dependency profile. This is a configuration defect, not a scientific algorithm failure.

### A02 — Installed CLI/products lack a complete loader-path contract

**P1; introduced; generated-install evidence, native startup not executed.** CLI has no install RPATH in `packages/cli/CMakeLists.txt:11–20`. Configuring it against the real installed SDK generated an `install_name_tool -delete_rpath` for the Core SDK directory with no replacement. The Core install name is `@rpath/libOpenMS.dylib`. TOPP/FLASH/OpenSWATH entry points similarly lack an explicit installed runtime lookup policy.

A host executable with suitable RPATHs or a repaired deployment can supply the missing context. The default standalone package flow has not established it. The existing Core relocation checks build consumer executables; they do not install and relocate CLI/product binaries. Add relative search paths for supported co-located layouts and a deliberate policy for separate prefixes/Windows DLLs, then test actual installation and launch without incidental developer loader variables. See [root-crosscheck.md](root-crosscheck.md), section 6, and the preserved configure/install excerpts.

### A03 — Source pins are not yet bound to the artifacts that execute

**P1; introduced acceptance gap; manifest mismatch reproduced, binary substitution not executed.** Both artifact verifiers validate SHA syntax and bytes but do not compare the supplied Core revision with FLASHApp's dependency lock (`tools/verify_artifacts.py:11–42`; identical app copy). A digest-valid controlled payload labelled with `bbbb…` is accepted despite the selected Core being `21b295…`. This probe covers manifest/hash verification only; the dummy payload would fail archive extraction. See [reproduced-findings.json](reproduced-findings.json).

Core's `VersionInfo::getRevision()` does expose a short Git revision (`packages/core/src/openms/source/CONCEPT/VersionInfo.cpp:149–152`). However, the full configured `OPENMS_SOURCE_REVISION` is currently exported in CMake metadata rather than checked against a full identity obtained from the loaded binary. The acceptance probe checks version, library location and data location, not that full runtime identity. Thus Claude CF-03 is retained with that narrower wording; “the library contains no revision” would be false. Existing file hashes remain useful evidence for the particular validated files.

Compare app locks, wheel/runtime metadata and loaded-library identity. Include pyOpenMS's own source revision, ABI-relevant build settings and required features. Matching source text alone does not prove binary compatibility. Do not weaken exact native Arrow pins or hardcode the developer's Homebrew paths as a substitute.

### A04 — Arrow import assumes one nonempty batch

**P1 for possible silent row loss; P2 for empty import; inherited; source and upstream-contract evidence.** `packages/pyopenms/bindings/arrow_zerocopy.cpp:125–154` calls `combine_chunks().to_batches()`, rejects zero batches and imports only `batches[0]`. Seven public import bindings use the helper. A local PyArrow 25.0.1 probe confirms an empty table yields zero batches; Core's FeatureMap importer supports zero rows. Existing empty-export tests do not cover empty import.

Arrow explicitly allows combined binary columns to retain multiple chunks to avoid overflow. Importing only the first batch can consequently discard later rows. This is a source/control-flow conclusion grounded in [Arrow's documented `combine_chunks` contract](https://arrow.apache.org/docs/python/generated/pyarrow.Table.html#pyarrow.Table.combine_chunks), not a multi-gigabyte native reproduction. No large allocation was attempted. The file is byte-identical to the OpenMS baseline; see [inherited-source-checks.json](inherited-source-checks.json) and [arrow-boundary-probe.json](arrow-boundary-probe.json).

Fix the shared helper using existing Arrow batch/stream facilities, preserve schema and all rows, and test empty and multiple-batch round trips. `ArrowGuard`'s release handling is correct in the inspected paths; this finding does not establish a leak or double free.

### A05 — TestSupport fixtures become Python runtime payload

**P2; introduced interaction; production copy block reproduced.** Core installs optional class fixtures beneath its runtime data directory (`packages/core/src/testframework/CMakeLists.txt:61–62`). Python copies that entire directory excluding only examples (`packages/pyopenms/CMakeLists.txt:239–243`) and installs the staged share tree as wheel content. With TestSupport present, fixture files follow that path.

The validated SDK contains **579 fixture files, 237,335,914 uncompressed bytes**, within 660 data files totalling 298,366,290 bytes. These are installed-file measurements, not a compressed wheel size. A test-only marker is copied by the exact production CMake block. A runtime-only SDK does not trigger it. Exclude development data from final wheel contents, check reused staging directories as well as fresh builds, and separate fixture placement from runtime ownership without disturbing scientific resources. See [data-size-inventory.json](data-size-inventory.json).

### A06 — FLASH test labels overstate the modes exercised

**P2; inherited test defect; exact source verified.** `packages/core/src/tests/class_tests/openms/source/FLASHDeconvAlgorithm_test.cpp:115,143,219–231,297` sets legacy `FD:report_FD` and `FD:merging_method` keys. The algorithm reads `report_FDR` and `merging_method` (`FLASHDeconvAlgorithm.cpp:102–104`). Several assertions check only that a supplied key exists, which cannot prove the algorithm read it.

The 709 passing Core tests therefore do not establish the labelled FDR/merging coverage. The previous native report already disclosed this limitation; this is an explicit repair item, not a newly introduced algorithm regression. Correct the keys and assert mode-dependent behavior, then rerun the scientific tests. Do not change global parameter-validation semantics merely to repair these tests.

### A07 — FLASHApp's failure contract is inconsistent

**P2; inherited; shared batch API reproduced, full UI consequence not reproduced.** In `CommandExecutor.py:78–105`, worker exceptions prevent results being appended; joining threads does not propagate them, and `all([])` returns `True`. The exact-method probe submits two controlled failing commands and observes two exceptions plus reported success.

All four current FLASHApp `run_topp()` callers in `packages/flashapp/src/Workflow.py:141,160,182,330` pass singleton work and take `run_command()`, so this does **not** prove a missing-tool UI workflow succeeds through the batch bug. Separately, those callers ignore `False` returned for a child that exits nonzero and continue toward later tools/parsing. Later errors may still fail the workflow. Fix the shared failure contract and the callers together; test both a worker exception and a real nonzero exit through a workflow. See [root-crosscheck.md](root-crosscheck.md), section 1.

### A08 — Subprocess ownership is not exception-safe; cancellation remains unverified

**P2; inherited; missing cleanup path reproduced, no heap-leak measurement.** `CommandExecutor.py:125–148` creates a subprocess before touching its PID file without a protecting cleanup block. A controlled PID-write failure invokes neither terminate nor wait. Local startup creates the PID directory after starting the workflow process (`WorkflowManager.py:100–105`), exposing a real ordering race. A child may continue running or block on undrained pipes.

Queued stop behavior also discards bookkeeping after cancellation. Whether children survive depends on the queue's process-group behavior; Claude CF-10 remains a risk until a real cancellation test establishes it. Do not blindly kill stored numeric PIDs, which may be recycled. Establish ownership before launching work, use exception-safe cleanup and verify controlled live children stop. The probe establishes missing cleanup, not permanent zombies, native heap leakage or a measured leak size.

Kimi's PID concern survives a caller correction: the active local UI callback reaches `WorkflowManager._stop_local_workflow():218–238`, which sends SIGTERM using stored numeric PIDs. The executor's SIGKILL method is only the UI fallback. Neither verifies ownership against PID reuse. Liveness checks or command-line matching alone do not solve that identity problem. No unrelated process was signalled in this audit; see the [FLASHApp crosscheck](kimi-ar13-crosscheck.md).

### A09 — Completed tools lose their final diagnostic output

**P2; inherited; reproduced.** Both `_stream_output` readers break when `poll()` reports process exit (`CommandExecutor.py:182–202`), even if buffered output remains. Controlled streams containing three lines each capture only the first stdout/stderr line. This affects normal singleton runs too. It changes diagnostic completeness, not the checked process return code.

Drain to EOF and test a child that exits before readers start. Bound the retained stderr buffer or spill it to the existing log; the current list grows with all stderr output. This is avoidable memory growth rather than proof of an unreachable allocation leak.

### A10 — Tool metadata drift can silently reuse a previous category

**P2; introduced; actual CMake logic reproduced with a mock SDK.** TOPP's manifest loop never clears `category` (`packages/topp/CMakeLists.txt:23–31`). If a registered executable lacks a `tools.json` row, configuration succeeds and uses the preceding tool's category. Removing only `AssayGeneratorMetabo`'s metadata in a temporary source wrapper produces that behavior; see [manifest-category-probe.json](manifest-category-probe.json). The current committed lists agree; this is a demonstrated missing guard, not a claim that today's category is already wrong.

Use one validated source of tool registration and metadata, reject absent/duplicate entries and avoid the quadratic repeated JSON scan. Existing parent ownership tests compare metadata with the baseline, not both lists with each other. A missing metadata mutation must fail configuration.

### A11 — Registry errors escape application startup; repeated scanning needs measurement

**P2; introduced; source-traced.** Tool registry parsing deliberately throws for malformed or duplicate records (`ToolHandler.cpp:111–125`). `TOPPBase` queries the registry in its constructor (`TOPPBase.cpp:129`), before the ordinary tool error-handling path; representative tool `main` functions do not catch construction failures. Throwing filesystem overloads also produce a different exception type on inaccessible paths.

Rejecting ambiguous records is an intentional contract. Claude CF-01's suggested silent skip/first-prefix-wins policy is not accepted. Catch failures at the application boundary and provide a controlled diagnostic. Native tests already cover same-file duplicates, unsafe paths, missing/nonexecutable binaries and desktop filtering; they have not run in the Core-only validation, and cross-prefix/startup cases remain distinct gaps.

This finding concerns uncaught executable construction, not universal GUI termination. Desktop's `QApplicationTOPP::notify` catches OpenMS exceptions from Qt events, and viewer/workflow startup contains exception handling. Kimi's stronger Qt-slot crash claim is not supported by those callers.

`packageTools()` rebuilds its map and rereads TSV files on every query. Repeated scans are real, but no timing regression was measured. Profile an actual discovery operation before adding caching; preserve an explicit refresh policy. Claude's claim that internal TTD paths are dead is rejected: user extensions can provide them.

### A12 — Build policy is copied and obsolete suite machinery remains in Core

**P2/P3; structural debt; byte-level inventory.** Seven packages each contain the same 99-line, 4,270-byte dependency helper. Parent and FLASHApp contain identical 75-line artifact verifiers, while the parent's tests exercise its copy. Drift can change pin/validation semantics independently. Consolidate maintenance within existing repositories and have tests exercise the canonical implementation.

Ponytail identified **2,286 measured lines of obsolete code** as deletion candidates, including 1,593 Core build lines, 589 Python repair lines and 104 old release-script lines. The initial conservative Core scan counted 1,307 lines; the later inventory includes its disconnected KNIME helpers. Keep source provenance and validate configuration after deleting them. Additional consolidation could bring the reduction to roughly 3,031 lines, an estimate rather than an implemented result. Generated standalone helper copies may be the smallest transition; they reduce maintenance ownership without reducing physical LOC. Do not create another repository or general package framework solely to deduplicate these helpers. See [duplication-inventory.json](duplication-inventory.json) and [ponytail-audit.md](ponytail-audit.md).

### A13 — Version metadata has an inherited concurrent-initialization race

**P2; inherited; source-confirmed race condition, no TSAN run.** `packages/core/src/openms/source/CONCEPT/VersionInfo.cpp:112–147` uses mutable function-local result objects with separate `static bool is_initialized` guards in `getTime`, `getVersion` and `getVersionStruct`. C++ protects initialization of the static objects themselves, but not the later unsynchronized guard reads and assignments. Concurrent first calls can therefore race. All three functions are unchanged from the OpenMS baseline.

Use a `static const` result initialized directly or through a lambda. This is a small simplification with no need for a custom lock/registry abstraction. Exercise simultaneous first calls in a fresh process under a supported race detector; normal serial startup often masks this condition. Do not claim the audit observed a crash or corruption.

### A14 — Testing-hook metadata describes a flag with no implementation

**P2; inherited dead macro, introduced misleading export; exhaustive symbol search.** `packages/core/src/openms/CMakeLists.txt:369–372` defines `OPENMS_ENABLE_TESTING_HOOKS` when class tests are enabled. The macro has no users anywhere in `core/src`, including vendored text. `packages/core/cmake/OpenMSConfig.cmake.in:46` exports that class-test option as `OpenMS_TESTING_HOOKS`, and the native-validation manifest labels it `class_testing_hooks`.

The macro already exists in baseline `ca3229603`; the extraction introduced the misleading exported metadata. These fields establish that class tests were enabled, not that special hook code exists in the binary. Remove the unused definition and name the recorded build option accurately. Do not implement test hooks merely to justify the flag. This corrects the interpretation of Claude CF-07 and the historical report's terminology; the recorded 709 test passes remain valid. See Kimi AR-04 and its [triage](kimi-triage.md).

### A15 — TestSupport discovery accepts an empty fixture installation

**P2; introduced; source and existing test expectation verified.** `packages/core/cmake/OpenMSDataConfig.cmake.in:18–21` tests only whether the fixture directory exists. `packages/core/tests/sdk_contract/test_sdk_contract.py:244–247` creates an empty directory and explicitly expects successful discovery. The full TestSupport config assigns fixture paths without verifying payload content either.

Require one known owned fixture sentinel in both discovery paths, keeping data-only discovery compiler-free. Reject an empty fixture directory in the contract test. This is a minimal completeness guard, not an exhaustive digest check. Preserve the numerical suite's documented combined staging-directory contract: flat custom binary directories work; nested paths require the existing explicit tool-name override. See the [contract crosscheck](kimi-contract-crosscheck.md).

### A16 — Optional queued workflows lose job identity and disagree on success/settings

**P2; inherited; current callers source-traced, no live Redis/RQ reproduction.** `QueueManager.get_job_info():176–221` catches lookup failures as `None`; `WorkflowManager.get_workflow_status():144–162` treats that as a missing job and deletes `.job_id`. A transient lookup failure can therefore discard the handle to real work. Preserve the record on transport errors and distinguish them from the specific missing-job condition.

`tasks.py:112–125` also ignores `execution()`'s return value and reports success when no exception escapes. Current Tag/Deconv execution can return early without doing work; the local process path already checks the result. Worker reconstruction does not transfer the settings used by `_get_max_threads`, and queue-mode checks differ between managers. Pass the small execution settings explicitly and use one success/mode contract.

The default Docker flow disables online mode, so these are gates for an explicitly enabled queue deployment. Raised exceptions already produce `success=False` and are displayed as errors; do not rewrite that working path or instantiate UI objects in workers. Current execution methods do not require the allegedly missing UI, and fallback preset names already normalize correctly. See the [FLASHApp crosscheck](kimi-ar13-crosscheck.md).

### A17 — Package-local development/deployment instructions still describe removed entry points

**P2 for deployment, P3 for maintenance documentation; source-confirmed.** Core's `AGENTS.md` retains monorepo GUI/TOPP/Python paths and `-DPYOPENMS=ON` guidance that no longer applies to the SDK. FLASHApp's root README and Compose file still supply `GITHUB_TOKEN`, while its replacement Dockerfile requires `PYTHON_IMAGE` and verified local artifacts. The old documented command cannot satisfy the new inputs.

FLASHApp also has no Docker ignore file; `COPY . /app` copies the available local context. No image was built and no disclosure was observed. Its Python requirements remain partially pinned, mostly inherited from the imported snapshot. Update the actual entry-point documentation and Compose flow, filter the context narrowly, and produce a tested application dependency lock. Keep local wheel/artifact verification intact. No new workflow framework or forced native Arrow/PyArrow version equality is justified.

## Validation and documentation gaps to retain explicitly

- **Products:** CLI tests exist but were not part of the 709 Core tests. Tool write-INI/CTD smoke checks mainly assert exit status. The FLASH pilot does not compare its numeric output; the full installed-suite numerical harness exists separately and remains unexecuted. Add content assertions rather than another registration-only check.
- **Binary profiles:** the validated Core binary is Debug with class tests enabled, optional integrations disabled and specific host dependency workarounds. The unused testing-hook macro does not establish a distinct instrumented binary profile (A14). Release, Linux, Windows, GUI products, repaired wheels and a FLASHApp image remain unvalidated. This is a release gate, not evidence that the tested build is invalid.
- **Coverage:** no line/branch coverage or sanitizer evidence was collected. Code-inspected tests, registered tests, executed tests, algorithm-mode coverage and instrumented coverage are different quantities. The old suite's 709/709 remains valid within its documented profile.
- **FuzzyDiff/TestSupport:** TOPP requires TestSupport even with product testing disabled because FuzzyDiff links its comparator. Preserve the requested tool; either document the temporary development dependency or place that reusable runtime implementation appropriately. Dropping FuzzyDiff conditionally would silently change the product set.
- **Data-path API:** the inherited shared-library resolver exits the process on failure and permanently caches lookup; fixed 1,024-byte executable-path handling can truncate/fail for long paths. These are documented/tested compatibility behaviors with host-application consequences, not newly introduced leaks. Any catchable-error redesign needs a coordinated API/CLI transition.
- **Platform flags:** the inherited GCC STL-debug helper uses `/D_GLIBCXX_DEBUG`, a Windows-style option, and ABI-affecting modes need consumer agreement. Fix and validate on the relevant platform; no GCC/Windows execution was performed here.
- **Documentation:** reconcile supported CMake minimums, recommended presets versus default Boost linkage, full runtime source identity, TOPP's TestSupport need and Python source links. Preserve the historical native-validation report and its qualified results. GUI resources remaining in Core are a known unfinished ownership cut, not a hidden discovery in this review.
- **Negative tests:** inherited `WILL_FAIL` cases can pass for an unrelated ordinary nonzero exit because they omit the expected diagnostic. This does not mean every segmentation fault or timeout passes. Add failure-reason assertions to high-value cases; preserve the documented staged-suite layout and the runtime dependencies of GUI features actually compiled into the SDK.

## Memory and performance assessment

No native leak-free claim is justified. Inspected Arrow guards release unconsumed structures and avoid re-releasing consumed structures; inspected process-lifetime singletons are not automatically leaks. The subprocess cleanup gap and unbounded diagnostic buffer are concrete resource-management issues, with the limits stated above. Arrow ownership under repeated exports, allocation failures and mutation/concurrency still needs targeted native testing. Whole scientific/GUI code coverage was not attempted.

The measurable waste found here is optional fixture payload copied into runtime staging. Repeated manifest scans and one thread per submitted command are source-supported scaling costs; their production timing/memory impact was not measured. Avoid speculative caches, lock frameworks or broad smart-pointer rewrites until a failing test or profile supports the change.

## What the tests actually establish

| Area | Evidence available | Remaining evidence |
| --- | --- | --- |
| Core scientific/API and path tests | Prior macOS arm64 Debug run: 702 Core class tests, five OpenSwathAlgo tests, two path-policy tests; 709/709 passed | Corrected FLASH mode tests, other profiles/platforms; line and branch coverage |
| Installed Core SDK | Prior 26 checks across library-only/support-enabled, original/relocated SDKs, with source/build paths hidden | Full loaded-binary source identity; installed downstream executable launch |
| Package source/configuration | Prior 62 checks, including real CMake configuration against controlled SDK fixtures | These do not compile or execute the products |
| CLI registry | Native positive and negative test sources exist and are registered | Execute the native suite; add multi-prefix/startup/installed-product cases |
| Tool science | Preserved numerical fixture harness; exit-based package smoke tests | Build products, execute numerical comparisons and assert CTD/INI content |
| Python | Binding/unit test sources, configure contract, root PyArrow boundary probe | Built/repaired wheel import, true multiple-batch conversion, allocation/lifetime tests |
| FLASHApp | Existing unit test sources; root controlled executor probes | Unit tests with isolated/installed collaborators, real queue/local cancellation and workflow failure propagation |
| Memory/races | Source-supported findings; existing Arrow test passed, macOS leak-report attempts inconclusive | ASan/UBSan, valid supported leak/race runs and repeated-workload measurements |

These are evidence categories, not coverage percentages. Existing validation documents already qualify the unexecuted products; this audit does not relabel those honest limitations as fabricated test passes.

## Evidence and reproduction

Run the two small scripts with the audited checkout as their argument:

```bash
python3 reproduce_findings.py /absolute/path/to/OpenMS4-tests
python3 reproduce_manifest_category.py /absolute/path/to/OpenMS4-tests
```

They intentionally assert that the audited defects are present; they are not regression tests declaring broken behavior correct. They perform controlled method/configuration probes without building OpenMS or launching FLASHApp. After fixes, replace them with ordinary negative/positive regression expectations in the owning packages.

The separate JSON records preserve the PyArrow empty-table check, Eigen configuration failure, installed data sizes, exact source comparisons and review revisions. The CLI configure log/install excerpts record generated loader behavior. [root-crosscheck.md](root-crosscheck.md) independently checks probe claims, callers and limitations. The refactoring plan specifies the additional native tests needed to close each gap.
