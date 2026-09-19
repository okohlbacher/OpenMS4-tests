# Triage of Vibe's implementation review

The verbatim [Vibe report](vibe-review.md) is preserved separately. Its two P0 findings are contradicted by the implementation. None of its numbered findings establishes a new P0/P1 defect. Useful remnants are the already documented GUI data boundary, downstream runtime acceptance work, and narrower test/documentation improvements. This conclusion concerns Vibe's claims; it does not establish that the implementation is defect-free.

## Invocation and evidence limits

- Reviewed parent commit: `7fb0147c341912b36f13f2ce05ef53a192b8dfff`; all nine package pins and file hashes are recorded in [vibe-invocation.json](vibe-invocation.json).
- Actual CLI: Vibe **2.25.1**, plan agent, only `read_file` and `grep` enabled, 150-turn ceiling, streaming output. The run completed with exit 0 and unchanged source status.
- The user's current configured alias `mistral-4-large` resolved to `mistral-large-4`, which the provider rejected as unavailable. That failed attempt is preserved. The completed review used the per-invocation override `VIBE_ACTIVE_MODEL=mistral-medium-3.5`, resolving to configured provider name **`mistral-vibe-cli-latest`**. No global configuration was changed. No separate server-resolved model build was exposed.
- The completed run made **42 successful calls: 33 file reads and nine searches**, with nine failed calls. Its 31 successfully read unique files are hashed in the invocation record. Unsupported write/shell attempts failed; they did not expand the permitted tools.
- This triage read source and existing test/acceptance documentation. It did **not** execute native tests, build, install, modify implementation files, or read the other reviewers' new reports. Test existence below is distinguished from execution evidence.

All source references below are relative to `OpenMS4-tests/` and refer to the recorded snapshot. The separate evidence inventory hashes the additional files inspected during triage.

## Every numbered finding

### VIBE-001 — Rejected: cross-package duplicate tools are rejected globally

`packages/cli/source/APPLICATIONS/ToolHandler.cpp:87–130` constructs `result` once, before the prefix loop and the manifest-file loop. Every record uses the same map. At line 125, failed `emplace(...).second` calls the exception-throwing `fail()` lambda. A duplicate in another file or prefix therefore reaches the same rejection as a duplicate in one file. `emplace` does not overwrite an existing value. Vibe's classification as an inherited registry defect is also unsupported: this TSV registry is part of the extraction.

The native fixture currently tests duplicates in one file, not two separate files/prefixes. A cross-file regression test would improve coverage of the intended behavior, but its absence does not establish the alleged P0 behavior. Do not add a second global registry or the proposed uniqueness abstraction.

### VIBE-002 — Rejected: the Arrow 23/25 mismatch is invented

`packages/core/cmake/OpenMSConfig.cmake.in:15–16` substitutes the **version used to build Core** into the exact Arrow/Parquet dependency requirement. It does not hardcode 23.0.0. `docs/core-native-validation.md:16` records the actual 25.0.0 build. The 23.0.0 value in `packages/core/tests/sdk_contract/test_sdk_contract.py:27–28` belongs to a controlled mock test.

`docs/refactoring-plan.md:52–61` explicitly corrects the *earlier Vibe review's* unusable Arrow 15 example. That paragraph is not a claim that the current SDK uses Arrow 15. Exact native dependency version/linkage agreement is intentional. No version-pin change or deletion of the historical correction is justified.

### VIBE-003 — Retained as an acknowledged transitional boundary

The central observation is correct: GUI startup resources still belong to the versioned Core compatibility data bundle. This is explicitly documented in `docs/refactoring-plan.md:125–129,209–211` and `packages/desktop/README.md:49–53`. Independently evolving those resources will require a later ownership cut and runtime acceptance.

This is known incomplete decomposition, not a newly discovered P1 regression. Keep it on the planned follow-up list. Vibe's proposed shared layered lookup and directory arrangement are unvalidated design suggestions; they should not be implemented solely because of this review. `OpenMSData` already exists and provides data metadata, not a GUI resource overlay policy.

### VIBE-004 — Broad claim rejected; narrow generation and runtime-coverage gaps remain

Contrary to “no test-time validation exists,” `packages/cli/tests/source/ToolManifest_test.cpp:84–120` contains native C++ negative assertions for same-file duplicate names, parent traversal, absolute paths, an extra trailing field, Windows drive-relative paths, missing binaries, directories masquerading as executables, and nonexecutable files. Lines 124–150 cover desktop category filtering and valid executable resolution. `packages/cli/CMakeLists.txt:32–44` discovers and registers these tests when testing is enabled.

These are **runtime parser/discovery test sources**, not evidence that the CLI native suite has run. They are distinct from the parent mock-SDK configure tests that inspect generated manifests. The parent validation runner does not compile or execute the CLI suite.

Vibe correctly observes that the TOPP generator does not itself perform comprehensive four-column/metadata validation before writing TSV (`packages/topp/CMakeLists.txt:16–52`). Separate-file/prefix duplicate fixtures and malformed generator metadata tests are reasonable targeted additions. Do not characterize existing coverage as absent, or infer a demonstrated parser failure from these gaps. CLI installed-prefix acceptance is already a gate in `docs/refactoring-plan.md:197–199`.

### VIBE-005 — Rejected: dependency guards and a negative linkage test already exist

Every mock consumer calls `find_package(OpenMS ... REQUIRED)` at `packages/core/tests/sdk_contract/test_sdk_contract.py:96`, executing the actual generated configuration. That configuration rejects missing selected Arrow/Parquet targets before importing the SDK (`packages/core/cmake/OpenMSConfig.cmake.in:55–61`). The test therefore cannot bypass the dependency guard merely because its later assertions name OpenMS targets.

The same test module explicitly replaces the required shared Arrow target with a static target and asserts failure naming `arrow_shared` at lines 144–148. Wrong Arrow version rejection is tested at lines 138–142. Adding the proposed duplicate assertions to the consumer would mostly mirror the implementation. A distinct negative Parquet-case test could extend coverage, but no current missing-target acceptance is established.

### VIBE-006 — Downgraded to optional minimum-version documentation cleanup

Core's root still declares CMake 3.21 (`packages/core/CMakeLists.txt:10`), while the new consumer entry points declare 3.24. The claim that desktop or standalone GUI lacks an explicit minimum is false: both `packages/desktop/CMakeLists.txt:1` and `packages/desktop/gui/CMakeLists.txt:1`, as well as viewers/workflows, declare 3.24.

Different independently built packages may legitimately require different CMake versions; Core configuring on an older version does not imply every consumer supports that version. Core's own README already instructs use of CMake 3.24 or newer (`packages/core/README.md:11`). Aligning the inherited declaration with the supported documented baseline is possible cleanup, but no introduced P1 failure or evidence that the declared 3.21 path succeeds/fails was provided.

### VIBE-007 — Rejected: TestSupport cases are deliberately separate

The general target loop at `packages/core/tests/sdk_contract/test_sdk_contract.py:106–110` does **not** include `OpenMS::TestFramework`. The library-only test separately requires its absence (117–119). Another test installs mock support metadata and explicitly requests `Core TestSupport`, then requires its presence (126–132). A third rejects a required but missing component (121–124).

The opposing expectations belong to distinct fixtures and component requests. They are the separation Vibe proposes, already implemented. No test restructuring is justified by this claim.

### VIBE-008 — Rejected: desktop has explicit checked dependency pins

`packages/desktop/dependencies.lock.json` exists and pins Core, CLI and test-data with full revisions. `tests/test_package_pins.py:21–27` iterates every owner package, including desktop. Its `names` dictionary maps **dependency CMake names** to package owners; omission of `desktop` from that dictionary does not skip desktop's dependencies.

Standalone viewer/workflow builds require `OpenMSGUI 1.0.0 EXACT` and compare its exported source revision to the owning desktop repository revision (`packages/desktop/cmake/DesktopDependencies.cmake:7–18`). This intentionally avoids a self-referential GUI source hash in the same commit. The file also explicitly selects desktop's lock at line 5. Do not add a fictitious `OpenMSDesktop` dependency mapping.

### VIBE-009 — Rejected: automated relocation includes TestSupport

`packages/core/tests/installed_sdk_acceptance/CMakeLists.txt:7` defaults TestSupport acceptance to **ON**, not OFF. Its lines 65–79 compile/register the installed TestSupport consumer. The runner configures and runs the same project and command-line options for both prefixes (`run_acceptance.py:56–85`); no branch disables support at relocation.

`docs/core-native-validation.md:34–36,103–107` records both library-only 6/6-per-prefix and support-enabled 7/7-per-prefix runs, with automated results/logs. This triage verifies that the code and documentation agree; it does not rerun those native checks. No third loop that repeats the support case is needed.

### VIBE-010 — Partly retained: runtime artifact compatibility is still an acceptance gate

The absence of CMake is appropriate for a Streamlit Python application with Vue components (`packages/flashapp/Dockerfile:15`), not evidence of missing integration. Source pins are checked by the parent all-package pin test. Artifact digest/schema/extraction checks exist in `packages/flashapp/experimental/verify_artifacts.py`; the parent equivalent has negative tests in `tests/test_split.py:65–100`, included through `tools/validate_source.py:10`.

Nevertheless, hashing a supplied wheel/runtime archive is not a binary ABI or provenance compatibility check. The verifier checks that the supplied Core revision has the form of a full SHA; it does not compare binary-embedded identities with all dependency locks. The parent artifact tests exercise the parent verifier with artificial files, not a real FLASHApp image. A pinned pyOpenMS import, resource lookup and actual required executable workflow remain unvalidated here.

Retain this narrower runtime/artifact acceptance gap. It is already acknowledged in `docs/refactoring-plan.md:153–161,203–207`, including the separately required FLASHTnT artifact. Vibe's “no validation” statement is too broad; neither CMake scaffolding nor placeholder artifacts would close the real gap.

### VIBE-011 — Withdrawn by Vibe; excluded from actionable counts

The final report explicitly withdraws its assertion that `emplace` silently overwrites duplicates. The withdrawal is correct. The report nevertheless repeatedly describes “14 substantive issues”; there are only 13 non-withdrawn numbered assertions before this triage, and most of those are rejected or narrowed here.

### VIBE-012 — Rejected: existing probes prevent the claimed fallback false positive

`packages/core/tests/installed_sdk_acceptance/data.cpp:16–21` compares the canonical resolved data directory to the expected installed/relocated directory. Lines 25–47 also locate the **loaded Core library** and reject it if outside the expected prefix. CMake passes the expected SDK data and prefix at lines 52–53; the runner supplies a distinct expected prefix for each copy at lines 66,76–85.

A fallback to a different development or original-install data directory fails the existing assertion. `docs/core-native-validation.md:36,103–107` further records acceptance while original Core source/build paths were unavailable. Checking a human-readable lookup-source label could provide extra diagnostics, but is unnecessary to establish the concrete path property Vibe says is missing. The compatibility fallbacks themselves are a documented policy, not a newly discovered regression.

### VIBE-013 — Rejected as stated: data lookup precedence is documented

`packages/core/src/openms/include/OpenMS/SYSTEM/File.h:235–241` explicitly documents the authoritative environment override, loaded-library/executable lookup before compiled developer paths, and caching on first use. Lines 244–249 document the diagnostic source API. `docs/refactoring-plan.md:125–129` also explains the important SDK precedence and compatibility policy.

A full platform-specific fallback diagram could add detail, but the claims “File.h: No documentation” and “no results” are false. There is no need to create another document solely to satisfy that premise.

### VIBE-014 — Rejected as a defect: missing sources already fail generation

`packages/topp/CMakeLists.txt:19` passes each source directly to `add_executable`; CMake rejects missing sources before any compilation. `tests/test_split.py:21–30` also verifies tool source existence, unique ownership and baseline coverage. Vibe acknowledges the existing CMake failure and source test in its own finding.

An explicit earlier existence check could customize the diagnostic, but it would not fix a missing failure or demonstrated build inefficiency. The suggested `executables.cmake` location was marked “assumed” despite the report's ledger claiming inspection. No change is recommended for this finding.

## Coverage correction and resulting use

Vibe's coverage ledger overstates the tool evidence. There was no successful read of `tools/verify_artifacts.py`, `packages/topp/executables.cmake`, `packages/pyopenms/dependencies.lock.json`, or `packages/test-data/CMakeLists.txt`, despite the ledger naming those files. Some successful reads were bounded ranges, not full-file inspection. The exact calls are preserved in [local raw-stream evidence](README.md#raw-stream-evidence); successfully read file hashes are in the invocation record.

The review did not meaningfully inspect scientific allocation/lifetime paths, Python binding ownership, FLASHApp queue/resource behavior, or desktop implementation. It establishes no leak, race, scalability conclusion, or numerical-correctness assessment. The claimed “all nine packages” scope describes the requested task more accurately than the achieved depth.

Use this review as limited independent input: preserve its evidence trail, reject its unsupported blockers, retain the known GUI resource transition and downstream runtime gates, and consider small distinct test cases for manifest generators and multi-prefix discovery. There are **nine rejected findings, three narrowed/retained items (003, 004, 010), one optional cleanup (006), and one withdrawn finding (011)**. Implementation and prioritization should follow reproduced defects and acceptance evidence rather than this report's original severity labels.
