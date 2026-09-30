# Independent cross-check of the root audit probes

The probes identify real local failure paths, with important limits on caller reachability and what was executed. The strongest extraction-specific issues are the missing installed CLI loader-path policy and the artifact verifier's failure to bind its claimed Core identity to the app's dependency lock. Python fixture copying is also confirmed for a Core SDK containing TestSupport. The FLASHApp executor and Arrow conversion defects are inherited code, not regressions introduced by the package split.

This cross-check read `reproduce_findings.py`, `reproduced-findings.json`, `arrow-boundary-probe.json`, the generated CLI install script, affected source/callers, and official Arrow documentation. It did not rerun the probes, launch FLASHApp, compile/install native products, allocate large Arrow buffers, inspect other models' current reports, or modify source. Locations below are relative to `OpenMS4-tests/` unless explicitly identified as review evidence.

## 1. Worker exceptions can produce a successful batch result

**Confirmed in the shared batch API; P2 for the current app's demonstrated call graph.** `packages/flashapp/src/workflow/CommandExecutor.py:82–86` appends a result only when `run_command()` returns. An exception terminates that worker before appending, while `thread.join()` does not transfer the exception to the caller. Line 105 uses `all(results)`, so two failing workers leave an empty list and produce `True`. The AST-extracted production-method probe accurately demonstrates this behavior; it does not substitute a different implementation.

**Important caller qualification:** the four current `run_topp()` call sites in `packages/flashapp/src/Workflow.py:141,160,182,330` all process one input file at a time and pass singleton argument lists. `run_topp()` selects `run_command()` for those calls (`CommandExecutor.py:348–352`). A missing executable on that single-command path raises into the workflow's exception handling. The probe therefore does **not** establish that today's missing-FLASHDeconv/FLASHTnT UI workflow is incorrectly marked successful through `all([])`.

The same callers independently ignore the Boolean returned by `run_topp()`. A child that launches and exits nonzero returns `False` at `CommandExecutor.py:159–164`, but the caller proceeds to the next tool or result parsing. For example, `Workflow.py:330–374` continues after FLASHDeconv failure. Subsequent missing-result/parser errors may still make the workflow fail (`Workflow.py:392–397`); unconditional end-to-end success is **not** established. A nonzero exit with usable partial outputs could reach the final `True`, which remains a possible consequence requiring a workflow-level test.

**Smallest correction direction:** establish one consistent failure contract across `run_command`, its batch wrapper and the existing call sites. Ensure every submitted command contributes either a failure result or a propagated exception. Do not fix only `all([])` and leave single-command `False` returns ignored. One regression should exercise a raised worker exception; another should exercise a normally launched command with a nonzero exit through a workflow caller.

## 2. Completed child processes lose buffered output

**Confirmed; P2 diagnostic loss, not a process-success reproduction.** Both stream readers break after one processed line whenever `poll()` reports exit (`CommandExecutor.py:182–186,195–202`). A process can exit while its pipes still contain unread lines. The controlled completed-process streams therefore correctly reproduce loss of `out2/out3` and `err2/err3`. This affects both singleton and batch executions because both use `run_command()` and `_stream_output()`.

`run_command()` still waits for and checks the exit code. The consequence demonstrated here is missing detailed output and incomplete failure diagnostics in the minimal log, not a changed return code or proof of data corruption. Drain each pipe to EOF; the existing iterator and concurrent readers already provide the needed structure. Test a process that completes before the readers begin and verify the final lines from both streams.

## 3. Failure after spawning a child leaves no cleanup path

**Confirmed; P2 resource/process-lifetime defect with potentially expensive consequences.** `CommandExecutor.py:125–138` launches the child before writing its PID record, and there is no `try/finally` covering that transition or the later streaming/wait/unlink sequence. The injected PID-touch failure accurately proves that neither `wait()` nor `terminate()` is called. It is not a native heap-leak measurement.

This failure is reachable when the PID directory disappears, permissions change, or the filesystem refuses the record. Local workflow startup also creates the PID directory only after starting the workflow process (`packages/flashapp/src/workflow/WorkflowManager.py:100–105`), exposing an ordering race. Cancellation removes the PID directory (`WorkflowManager.py:228–238`), another relevant boundary. The workflow's final directory removal at line 124 does not terminate or wait for an unrecorded subprocess.

A child may continue consuming resources or block on its undrained pipe. Eventual interpreter cleanup may reap an already exited process; that does not guarantee termination of a live child. Do not claim that the probe measured a permanent zombie, retained native heap, or leak size. Put child ownership and PID cleanup under an exception-safe lifecycle, and create required bookkeeping before starting work. Preserve the existing normal-completion behavior.

The executor file is byte-identical to the preserved `implementation/upstream/flashapp` import snapshot. `packages/flashapp/source-provenance.json` records that snapshot as public FLASHApp commit `f8e9eba435ea0843660c63fe86c58c64798e7f71`. Findings 1–3 are inherited in the imported application code.

## 4. Artifact hashes are not bound to the app's source pins

**Confirmed; P1 for the experiment's claimed pinned-artifact acceptance contract.** `tools/verify_artifacts.py:11–42` validates that the supplied `core_source_revision` has SHA syntax and that artifacts match the hashes in that same supplied manifest. It does not read `packages/flashapp/dependencies.lock.json` or compare the claimed revision to the selected Core commit. The app's `experimental/verify_artifacts.py` is byte-identical to the parent copy, and the Dockerfile invokes it at lines 7 and 10.

The probe's different, syntactically valid revision is accepted even though it disagrees with the app lock. Its `runtime.tar` payload is deliberately not an archive: that is sufficient to demonstrate **identity-verification** acceptance, but would fail the later extraction stage. Do not describe the probe as a successful image build, usable substituted runtime, or a broken hash check.

The verifier also does not inspect binary-embedded build provenance or wheel/core compatibility. Matching the manifest revision to the dependency lock closes the explicit source-pin gap; agreeing text alone still cannot prove the actual wheel/native ABI. This is extraction-specific packaging work. Keep the source-pin comparison and the later actual-artifact import/loader acceptance distinct; neither needs a new package manager or abstraction layer.

## 5. Python's data staging copies installed test fixtures

**Confirmed conditionally; P2 package-content and reproducibility defect.** With `NO_SHARE=OFF` (the default), `packages/pyopenms/CMakeLists.txt:239–243` copies the entire installed Core data directory while excluding only `examples`. Core installs development fixtures beneath that same directory when TestSupport is installed (`packages/core/src/testframework/CMakeLists.txt:61–62`). Thus `test-data/core` is included in Python staging.

The probe executes the exact production CMake copy block with an isolated marker SDK and demonstrates the test-only file in staging. The subsequent install at `packages/pyopenms/CMakeLists.txt:270–272` installs that entire staged `share` tree as `python_modules`; `pyproject.toml:154` selects that component. This establishes the packaging path, but no wheel was built and no wheel-size measurement was made.

The old monolithic Python build also copied the shared data tree, excluding examples. The new installed-SDK layout puts optional class fixtures beneath that tree, making this an extraction interaction rather than a newly invented copying technique. A runtime-only SDK without TestSupport does not trigger it. Exclude development fixtures from the wheel's final content and check both clean and reused staging directories; do not split the whole data system merely to fix this exclusion.

## 6. CLI installation strips its only generated Core search path

**Confirmed in generated macOS installation instructions; P1 default installed-product readiness issue, not an executed loader failure.** `reviews/2026-09-10-implementation-adversarial/cli-configure/cmake_install.cmake:51–53` invokes `install_name_tool -delete_rpath` for the configured Core SDK's library directory and adds no replacement. The CLI package sets no install RPATH in `packages/cli/CMakeLists.txt`. The actual installed Core target advertises `@rpath/libOpenMS.dylib` (`core-sdk/lib/cmake/OpenMS/OpenMSTargets-debug.cmake:38–43`). This confirms that build-tree resolution is not automatically retained in the installed CLI library.

The runtime consequence is conditional on the loader context: a host executable with a suitable RPATH, loader environment variables, or explicit deployment repair could still resolve Core. CMake target discovery alone does not supply such a runtime search path. In the default separately installed product flow, no such context is established. The install script proves the path loss, while actual installed/relocated CLI and tool startup remain acceptance tests to execute.

This is a new standalone-consumer deployment responsibility introduced by extraction. Core's own relocation test does not cover it. Choose and implement an explicit supported layout: relative paths for co-located packages and a deliberate policy for separate prefixes. Do not describe a retained absolute build-machine path as a relocation solution. Verify installation and relocation with source/build paths unavailable and no incidental loader variables.

## 7. Arrow import wrongly assumes exactly one nonempty batch

**Confirmed source defect with separately qualified consequences.** `packages/pyopenms/bindings/arrow_zerocopy.cpp:125–130` calls `combine_chunks().to_batches()`, throws for zero batches, and otherwise imports only `batches[0]`. Lines 152–154 construct the C++ table using only that first batch. Seven public binding functions call the helper: FeatureMap feature/PSM imports, ConsensusMap feature/PSM imports, and ProteinIdentification search-parameter/protein/group imports (lines 339,353,405,419,491,511,530).

**Empty tables — P2:** the recorded PyArrow 25.0.1 probe confirms that an empty table yields zero batches. The C++ source consequently throws before reaching importers that accept empty data; for example, `packages/core/src/openms/source/FORMAT/FeatureMapArrowIO.cpp:1334–1338,1487` handles zero rows successfully. Existing Python tests check empty *export* and small nonempty import round trips, not this empty-import boundary. This is source plus PyArrow behavior evidence, not a native binding execution.

**Multiple batches — P1 conditional scientific data-loss risk:** Arrow explicitly permits `combine_chunks()` to retain multiple chunks for binary columns to avoid overflow. Consequently, a single record batch is not guaranteed. Importing only the first can silently discard later rows. This follows from the documented contract and the helper's control flow; no multi-GB allocation or native binding reproduction was performed. [Official Arrow `Table.combine_chunks` documentation](https://arrow.apache.org/docs/python/generated/pyarrow.Table.html#pyarrow.Table.combine_chunks).

The entire `arrow_zerocopy.cpp` file is byte-identical to OpenMS baseline commit `ca32296038839459d8c9b075b759e285913d6294`, verified against the original Git blob. Both boundaries are inherited. Correct the shared helper once using Arrow's existing batch/stream facilities while preserving schema and all rows; a guard rejecting extra batches can prevent silent loss temporarily but is not complete import support. Actual native round-trip coverage is still required, and this cross-check does not certify that downstream Core importers handle all large/chunked schemas correctly.

## Recommended use of these results

Keep the extraction defects, inherited defects, and unexecuted acceptance gates separate. The artifact-pin and generated CLI loader-path findings justify concrete packaging fixes. The process-output/lifecycle probes support focused inherited executor fixes. The worker-success claim must retain its current-callsite limit, and Arrow's multi-batch consequence must retain its documentation/source-only evidence level. None of these probes establishes native memory-leak measurements, a successful FLASHApp container, a built wheel, or a compiled Python binding reproduction.
