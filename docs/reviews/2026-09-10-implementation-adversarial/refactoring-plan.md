# Refactoring plan after the implementation audit

Keep the nine package boundaries. The next milestone is an installed Core + CLI + representative tool + Python wheel that agree on source/build identity, run from a moved prefix, and fail predictably. A further split of the scientific Core or another build-framework repository is not justified by the current evidence.

This plan is implementation work proposed by the audit, not work already performed. Each phase should be a small reviewable change in its owning repository; update the parent gitlinks and dependency locks only after its acceptance checks pass. Preserve the OpenMS and FLASHApp baselines, third-party code, scientific APIs except where explicitly listed, and current exact dependency pins.

## 1. Repair false assurances and data boundaries

**Owners:** Core tests, pyOpenMS, FLASHApp, parent validation.

- Correct the FLASH algorithm test parameter names to `report_FDR` and `merging_method`. Assert the effective configuration and an observable result of each mode. Stop treating a parameter's mere presence in an extensible parameter map as mode coverage.
- Make Arrow import preserve a valid zero-row schema and consume every batch. Use the existing Arrow batch/stream APIs instead of assuming `combine_chunks()` returns one batch. Retain `ArrowGuard`'s ownership handling. State which conversion steps copy buffers; do not describe the entire path as guaranteed zero-copy.
- Filter Python wheel resources to runtime data immediately, including when reusing a staging directory that previously contained fixtures. Consider relocating optional TestSupport fixtures only if broader SDK package ownership needs it; that would require updating all exported test-data paths together. Preserve chemistry/schema resources and fixtures needed by tests.
- Replace FLASHApp's manual batch-thread coordination with a bounded standard-library executor that observes every result and exception. Propagate failed tool statuses through workflow callers. Give each subprocess a defined cleanup owner; drain pipes to EOF, keep diagnostic buffering bounded, and remove PID records in cleanup after the process has been handled.
- Require a known owned fixture sentinel when discovering either TestSupport component. Reject an empty fixture directory while preserving compiler-free data discovery; use artifact digests for exhaustive integrity rather than expanding this guard into a second manifest system.
- Preserve queue job IDs on lookup/transport errors and clear them only for a confirmed missing job. Make queued tasks observe the workflow's success result, pass the required execution limit explicitly, and unify the two mode checks. Preserve existing exception-to-error handling and the non-UI worker path.

**Gate:** targeted tests must fail with the old wrong FLASH keys, an empty Arrow input, a test-only marker in a candidate wheel, an empty installed fixture directory, a worker exception, a nonzero tool exit, a PID-record write failure and buffered output after process exit. Queue tests must preserve `.job_id` during a simulated lookup outage, reject an early/false execution result and honor the configured worker limit. The Arrow multiple-batch test must force more than one batch at the conversion boundary; ordinary small chunked tables can be combined into one and pass the old broken helper. Existing happy-path tests must still pass. Use controlled child processes for lifecycle tests; mocked cleanup observations alone do not prove no live children remain. Run the affected scientific class tests after changing their configuration; the previous 709-pass report cannot validate those changes.

## 2. Establish an installed product, not just an SDK consumer

**Owners:** CLI, TOPP, OpenSWATH, FLASH, desktop entry points, parent acceptance.

- Delete TOPP's redundant Boost/Eigen discovery and use the public targets supplied by the pinned SDK. Exercise the actual validated Eigen 5 installation as well as the supported minimum dependency profile.
- Define installed library lookup for each supported packaging layout. Unix products need appropriate install RPATHs; Windows packages need an explicit DLL placement/discovery policy. Keep build directories and dependency prefixes out of relocatable product paths. Do not paper over this with a developer's environment variables.
- Build/install CLI and a small representative executable first. Then build the requested tool families. Preserve FuzzyDiff availability and document TOPP's current TestSupport build prerequisite. Package its required runtime libraries appropriately; moving the comparator is not required to establish the first installed product.
- Preserve rejection of ambiguous or malformed tool registries. Catch errors at executable/application boundaries and return a useful diagnostic instead of allowing constructor exceptions to abort the process. Do not silently skip broken rows or adopt first-prefix-wins semantics without an explicit change to the registry contract.
- Generate tool source registration and metadata from one validated tool list. Reject absent/duplicate metadata before writing TSV; remove the stale per-loop category variable and quadratic rescans. Keep one small helper if needed, not a general package framework.

**Gate:** configure against Core with Eigen 5; install CLI and a tool, move the whole product prefix, hide source/build paths and run with developer loader-path overrides absent. Verify `-help`, `-write_ini`, CTD contents and the selected product version/category. Test malformed records, two manifests/prefixes containing a duplicate, inaccessible directories, and paths containing spaces. Execute the existing native ToolManifest negative tests rather than merely registering them. Add a real FLASH numerical comparison; an exit-only pilot is insufficient. Make selected negative tests reject an unrelated ordinary failure by checking the intended diagnostic. Keep the suite's combined staging-directory contract, add a flat-custom-directory registration case, and document the existing explicit-name override for nested directories.

## 3. Bind package pins to the binaries that run

**Owners:** Core version/config exports, pyOpenMS provenance, FLASH runtime artifacts, FLASHApp verifier.

- Expose the full configured Core source revision from the loaded library. Retain the existing short Git revision API for compatibility. Make installed acceptance compare the loaded binary identity with the expected package lock, in addition to checking configuration text, data path and library location.
- Record a compact build identity: source revision, platform/architecture, compiler/runtime ABI, configuration where ABI-relevant, public dependency versions/linkage and actual feature flags. Enforce actual incompatibilities; do not demand identical incidental compiler paths or claim a source hash proves ABI compatibility. Remove the unused `OPENMS_ENABLE_TESTING_HOOKS` definition and rename the exported class-test option accurately. Do not invent hook implementations or infer an ABI difference from this unused macro.
- Produce publishable artifacts from the clean, exact source commit being recorded; mark development builds with uncommitted changes explicitly. An override string alone does not attest the source that was compiled.
- Record pyOpenMS's own source revision as well as Core's. Compare wheel/runtime embedded metadata with the selected package locks before assembling FLASHApp. Validate the expected executable set and runnable permissions. Maintain hashes for the exact artifacts tested.
- Keep native Arrow/Parquet linkage pins. The Arrow C Data Interface can bridge separate Arrow versions; do not replace that interface or impose same-version PyArrow solely on a speculative ABI claim. Test the declared wheel/PyArrow combinations.
- Make native dependency selection reproducible, including CURL. Prefer validated dependency targets/build metadata and actionable diagnostics over hardcoded Homebrew paths or an arbitrary major-version compatibility rule.

**Gate:** a same-version artifact from another Core commit, wrong wheel provenance, wrong architecture/configuration, mismatched required feature set, missing runtime executable, and altered artifact bytes each fail for the intended reason. A correctly matched installed bundle passes import, chemistry-data lookup and a minimal executable workflow. Test a swapped library using a compatible test fixture; configuration-only wrong-pin tests remain useful but are a separate check.

## 4. Reduce duplicated and obsolete code

**Owners:** Core build files, all consumer build entry points, FLASHApp/parent verifier.

- Remove the disconnected legacy modules listed in the [Ponytail audit](ponytail-audit.md), after confirming no active configuration references them. Preserve history in the upstream baseline.
- Choose one canonical `OpenMS4Dependencies.cmake`. During transition, generate standalone copies and check their hashes; this removes independent maintenance, not physical duplication. Only move it into the installed SDK after ordinary and compiler-free data consumers can bootstrap it cleanly.
- Keep one artifact verifier implementation and have the parent validation exercise the FLASHApp implementation. Retain standalone usability; a thin launcher is sufficient if the old command path must remain.
- Remove dead legacy Python packaging scripts after checking external entry points and updating provenance. Retain a useful leak-check recipe; do not delete validation merely because the current runner omits it.
- Profile registry scans before introducing a cache. If repeated parsing matters, share a snapshot within one discovery operation with a defined refresh policy. Avoid a global cache plus test-only invalidation hooks by default.

**Gate:** clean configure and source-contract checks pass; standalone repositories need no sibling source trees; helper/verifier drift is detected. Native installed-product tests from phase 2 remain green. Compare package contents and dependency graphs before/after deletion. No added runtime dependency or repository is needed for this phase.

## 5. Close lifetime, coverage and platform evidence gaps

**Owners:** Core/CLI tests, pyOpenMS, desktop and FLASHApp runtime tests.

- Establish line/branch coverage for the changed package contracts and selected scientific hot paths. Report uncovered branches and excluded profiles explicitly; do not derive a coverage percentage from CTest counts.
- Replace the three manual VersionInfo initialization guards with directly initialized `static const` results, using a lambda where needed. Exercise simultaneous first calls in a fresh process with a supported race detector; retain the user-extension registry API while assessing its separate first-call synchronization.
- Run targeted ASan/UBSan builds and repeated Python/Arrow import/export cycles; use a separate supported Linux leak check for native lifetime paths. Exercise allocation/conversion failures.
- Verify local and queued cancellation against actual child processes. Ensure cancellation does not discard ownership records before children are confirmed stopped; reject reused process identities. PID liveness or matching a command line alone does not prove ownership. Check the queue implementation's process-group behavior before choosing the smallest correct fix; use existing process handles and dependencies rather than a new supervisor framework.
- Replace fixed-size executable-path handling and test long/non-ASCII paths on supported platforms. Correct the inherited GCC STL-debug option and propagate ABI-affecting settings appropriately to consumers.
- Decide how a library data-path failure becomes a catchable exception without changing CLI diagnostics unexpectedly. The current explicit exit policy is tested; change API, wrappers and negative tests together.
- Run Release and Linux/Windows acceptance before publishing those products. Treat disabled readers/models, GUI applications and wheel builds as separate unvalidated profiles until exercised. The current Debug results and unused testing-hook flag do not establish Release behavior. For GUI, a WebEngine-disabled build must work without that dependency; a GUI actually linked against WebEngine must continue to require it.

**Gate:** no unsuppressed issue in the selected sanitizer/lifecycle runs; repeated workloads show stable retained resources after warmup; changed critical branches have explicit positive/negative evidence. Publish a matrix of actual results, skips and exclusions rather than a universal leak-free or fully-covered claim.

## 6. Complete ownership and documentation

**Owners:** desktop, Core resources, package READMEs and parent reports.

- Move GUI resources to desktop once a viewer can locate its own installed resources independently. Keep Core scientific resource lookup unchanged; avoid a generalized overlay system for this one ownership cut.
- Align documented and enforced build minimums and distinguish recommended presets from alternative defaults. State TOPP's TestSupport dependency until removed. Update Python package source links and retire misleading legacy build instructions.
- Rewrite Core's package-local agent instructions around the SDK's real paths and options, preserving its vendored-code and test constraints. Update FLASHApp's root README and Compose inputs to the verified artifact flow, add a narrowly scoped Docker ignore file, and lock/test its application dependencies. Keep required artifacts in the build context and the local pyOpenMS wheel separate from dependency resolution.
- Document actual runtime identity, the class-test build option, versioned-data lookup and artifact verification guarantees. Keep the prior native report as dated evidence and link this audit's test-hook terminology correction and newer matrix; do not silently rewrite historical results as broader validation.

**Completion gate:** an independent checkout of each released package can build against its pinned installed dependencies, run its own meaningful tests, and install/launch from a supported layout. The parent locks identify those tested commits/artifacts. Known optional and platform limitations remain explicit.
