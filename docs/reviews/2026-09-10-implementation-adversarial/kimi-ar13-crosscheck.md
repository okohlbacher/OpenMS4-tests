# Independent cross-check: Kimi AR-13 (FLASHApp)

AR-13 contains valid documentation/deployment and process-ownership findings, but its missing-UI and preset-name claims are not current defects. Its queue-error claim becomes more concrete when traced to the caller: a lookup error can delete the stored job ID. Worker settings and success flags have additional source-confirmed inconsistencies worth addressing without introducing a general workflow factory.

This check read only AR-13, affected source/callers and the preserved import snapshot. No CLI review was rerun, no application/container/native build was executed, no processes were signalled, and no implementation files were edited. Unless stated otherwise, paths below are relative to `OpenMS4-tests/packages/flashapp/`. Runtime consequences are source-traced, not end-to-end reproductions.

## Disposition

| Subclaim | Result | Priority and limit |
|---|---|---|
| README uses the former token-based Docker build | Accepted | P2; current instructions omit mandatory image/artifact inputs |
| No Docker ignore file; broad context copying | Accepted with qualification | P2 packaging hygiene; contents depend on the local build context |
| Requirements are only partly pinned | Accepted, inheritance corrected | P2 reproducibility gap; most unpinned entries predate extraction |
| PyArrow 19/Core Arrow 25 implies incompatibility | Rejected as a demonstrated incompatibility | The combination is unvalidated, not proved invalid; exact PyArrow exclusions are patch releases |
| Raw PID stop can target a reused PID | Accepted, current caller corrected | P2 ownership risk; active local stop uses SIGTERM, not the fallback's SIGKILL |
| `run_python` continues after missing-script log | Accepted, current impact narrowed | No current call sites found; explicit failure is preferable to silently returning |
| PATH `python` can select another interpreter | Accepted as limited hardening | No current caller or wrong-interpreter container reproduction |
| Worker omission of `workflow_name` breaks presets | Rejected for current workflows | Fallback name normalizes to the same preset key |
| Worker omission of `ui` breaks current execution | Rejected for current workflows | Execution methods do not access UI |
| Queue failures become indistinguishable from missing state | Accepted and strengthened by caller trace | Transient job lookup errors can remove `.job_id` |
| A new shared workflow factory is necessary | Not justified by these findings | Fix explicit state/result contracts first |

## (a) Docker documentation and build context

`README.md:49` still instructs a build using `GITHUB_TOKEN`. The new `Dockerfile:3–7` instead requires `PYTHON_IMAGE` and copies/validates `artifacts.lock.json` plus `artifacts/`. With the documented command alone, the required base-image value is absent. `experimental/README.md:3–7` explains the new artifact flow; the root README does not link readers to it. The same stale token-only build arguments remain in `docker-compose.yml:3–7`, so correcting only the README leaves an existing entry point inconsistent.

Neither `.dockerignore` nor a Dockerfile-specific ignore file exists in the package. `COPY . /app` copies the available local context wholesale. In this parent checkout `.git` is a submodule pointer file; in a standalone clone it can be a directory containing history. Do not claim this audit built an image containing all Git history or observed credential disclosure. The absence of filtering is real, and the README explicitly uses a local `.` context.

The upstream README and absence of a Docker ignore file are unchanged from the preserved import. The Docker instructions became incompatible when the experiment replaced the primary Dockerfile. The new Dockerfile directly starts Streamlit, with `settings.json:26` setting online deployment to false; it does not invoke the inherited Redis/RQ entrypoint. Queue findings below therefore concern explicitly enabled online deployments, not a demonstrated default-image queue execution.

**Small fix:** replace the obsolete Docker instructions with a short link to the accurate artifact guide, reconcile or mark the old Compose file unsupported, and add a narrow ignore file for VCS/development/runtime-workspace material. Keep the required `artifacts/` inputs available. Validate the actual documented build path once real artifacts exist; do not add another image framework.

## (b) Requirements and Arrow compatibility

Kimi correctly identifies unconstrained or lower-bounded dependencies: `xlsxwriter`, `scipy`, `polars`, `redis`, `rq` at `requirements.txt:139–145`, plus `numpy>=2.0` at line 53. They appear under a pip-compile-generated header. Comparing against the preserved upstream file shows that **the only requirements edit in this extraction replaces `pyopenms==3.5.0` with the local-wheel comment**. The open-ended requirements and `pyarrow==19.0.1` are inherited; they should not be labelled newly introduced pinning regressions.

The Python package excludes **24.0.0 and 25.0.0 specifically**, not all PyArrow 24/25 releases (`packages/pyopenms/pyproject.toml:75–84`, relative to the parent checkout). PyArrow 19.0.1 is not excluded by that declaration. Different native Arrow versions across the C Data Interface do not by themselves prove an ABI mismatch. The assembled image/wheel combination still requires import and Arrow round-trip acceptance, which has not occurred here.

**Small fix:** regenerate a complete, tested application lock from an explicit dependency input; include hashes if the deployment contract requires byte-reproducible Python inputs. Preserve the separately verified local pyOpenMS wheel. Do not force native Arrow and PyArrow to the same version merely to remove a numerical version difference.

## (c) PID ownership and `run_python`

### Raw PID stop: valid risk, different active path

`CommandExecutor.stop():356–370` sends SIGKILL to numeric PID filenames without identity verification. Its only call site is the fallback in `StreamlitUI.py:1445–1449`. Current `WorkflowManager.show_execution_section()` supplies its own stop callback (`WorkflowManager.py:259–262`), so normal current UI execution instead reaches `_stop_local_workflow():218–238`, which also signals raw PIDs, using SIGTERM.

Thus the ownership flaw survives the caller correction. Stale PID files can arise from failures/crashes; an unrelated process reusing that PID and signalable by the same user can receive the signal. The check did not cause PID reuse, signal another process, prove exploitability, or establish that it happens routinely.

Kimi's suggested `os.kill(pid, 0)` plus command-line matching is insufficient as an ownership guarantee: liveness is not identity, and matching/checking before signalling still permits reuse between operations. A matching command line is not unique ownership either. Retain owned process handles while available; persisted recovery records need process identity beyond PID and identity-aware signalling/verification. The existing `psutil` dependency may support the small implementation; no new supervision framework is required. Extend cancellation tests to reject a simulated reused identity and separately verify real owned child termination.

### `run_python`: defect/hardening in an unused current path

After both script locations fail, `CommandExecutor.py:394–405` logs and continues into module loading, which raises. The observation is correct; “graceful-degradation intent” is an inference. A silent `return` would risk making a future workflow appear successful without doing its work. Prefer a clear missing-script exception consistent with the shared failure contract.

Lines 410 and 425 use PATH `python`; using the already imported `sys.executable` is a small way to retain the running environment. However, repository-wide Python-source search found **no current `run_python()` callers**. The current Docker command itself starts via PATH `python`, so a mismatch inside that exact default environment has not been demonstrated. Keep these as inherited low-impact API repairs, not current FLASHApp workflow failures.

`run_python` also discards `run_command`'s Boolean result; address that if retaining the API, alongside the shared failure contract already recorded in A07/root-crosscheck. Do not implement a missing-script silent return while leaving nonzero statuses ignored.

## (d) Worker reconstruction, settings and result state

### Rejected: missing `workflow_name` causes the current preset failure

`tasks.py:80` omits the optional constructor argument, but `ParameterManager.py:74` intentionally falls back to `workflow_dir.stem`. Its only functional use is preset lookup, normalized at lines 265–267. `WorkflowManager.py:18` already creates the directory from the lowercased, hyphenated display name. For the current workflows, `FLASHTnT → flashtnt`, `FLASHDeconv → flashdeconv`, and `FLASHQuant → flashquant` are identical keys in both paths.

No current incorrect preset key is established. Do not add a factory or extra serialized name solely to fix this claim.

### Rejected: missing `ui` breaks current worker execution

`tasks.py:88–95` reconstructs the execution state and omits UI deliberately. AST/source inspection shows current Tag/Deconv `execution()` methods use only `executor`, `file_manager`, `logger`, `params`, and `workflow_dir`, all of which are set. Their UI use is confined to upload/configure methods. Quant inherits the base execution method, which also does not use UI. The omitted `tool_name` is not used by these execution methods either.

A future execution method using an omitted attribute would fail, but this is a future-contract risk, not a current missing-UI defect. Importing the worker dependencies still imports Streamlit, so the module header's “without Streamlit” aspiration is inaccurate; the application package already depends on Streamlit. Fix the comment or deliberately narrow worker dependencies only if that becomes a real packaging need. Do not instantiate GUI objects in a background worker.

### Accepted adjacent issue: worker settings are not transferred

`CommandExecutor._get_max_threads():39–47` reads mode/thread settings only from `st.session_state`. `tasks.execute_workflow()` receives workflow directory/class/module and rebuilds components, but does not transfer deployment settings. In a fresh RQ worker without the GUI session, the helper selects the local defaults or saved `max_threads`, rather than the configured online limit (the supplied settings use local 4 versus online 2).

Mode checks also differ: `QueueManager._check_online_mode():79–85` treats `REDIS_URL` as enabling online mode, while `WorkflowManager._is_online_mode():37–39` checks only the GUI settings flag before creating a queue manager. Setting `REDIS_URL` alone therefore does not enable queueing through the normal manager path. These are source-traced configuration inconsistencies; no live RQ resource-limit violation was measured.

**Small fix:** pass the required execution limit/mode explicitly to the worker or load the same authoritative configuration there. Use one mode rule at both call sites. Do not mirror the whole GUI session or create a general dependency-injection layer.

### Accepted: lookup failures can discard a real queue job's identity

`QueueManager.get_job_info():176–221` catches any failure as `None`. `WorkflowManager.get_workflow_status():144–162` treats that `None` as proof the job does not exist and deletes `.job_id`. A transient Redis lookup failure after queue initialization can therefore discard the persistent handle to a real queued/running job, then fall back to local PID status. Initial Redis unavailability and submit failures also select fallback behavior; `WorkflowManager.py:88–90` does show a warning for a failed submission, so the aggregate claim that all queue errors are silently indistinguishable is too broad.

**Small fix:** distinguish the specific missing-job condition from a connection/lookup error. Preserve `.job_id` on transport errors and report temporary unavailability. Existing return conventions can be kept where their callers handle them correctly; a wholesale queue API rewrite is unnecessary.

### Accepted adjacent issue: task success ignores the execution return value

`tasks.py:112–125` ignores `workflow.execution()`'s result, logs completion and returns `success=True` if no exception escaped. Current Tag/Deconv execution can return `None` after an empty input selection (`src/Workflow.py:79–90,287–293`). That is handled differently from local `workflow_process()`, which checks the result before logging success (`WorkflowManager.py:117–119`). For such an early-return case, the queued task can report success without execution. This was source-traced, not exercised through the UI or RQ.

Raised exceptions are **not** universally presented as success: `tasks.py:128–155` returns `success=False`, and `StreamlitUI.py:1552–1562` explicitly checks that result and shows an error despite RQ's finished function status. Preserve that working path. Normalize the execution success contract and require success before writing the completion marker; add a task-level early-return/false-result test. This is separate from the batch `all([])` bug.

## Inheritance and recommended scope

Byte comparison with the preserved upstream FLASHApp snapshot confirms that `README.md`, `CommandExecutor.py`, `tasks.py`, `WorkflowManager.py`, `QueueManager.py`, `ParameterManager.py`, and `src/Workflow.py` are unchanged. The source provenance records public commit `f8e9eba435ea0843660c63fe86c58c64798e7f71`. Requirements changed only at the pyOpenMS wheel handoff. Do not classify inherited application behavior or existing unpinned requirements as newly introduced extraction defects.

Prioritize the actual new deployment entry-point mismatch, narrow build-context filtering, explicit artifact/dependency acceptance, safe process ownership, preserved queue identity on lookup errors, and consistent worker settings/results. Retain the current non-UI worker path. `run_python` hardening can stay small and lower priority because it is unused by current workflows. No new repository, worker factory framework, GUI reconstruction or forced Arrow-version alignment is justified by AR-13.
