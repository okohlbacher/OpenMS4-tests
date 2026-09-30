# Vibe review triage

This is the calling agent's verification note, separate from Vibe's unchanged response in `vibe-review.md`.

## Provenance

Vibe 2.25.0 ran its configured active alias `mistral-medium-3.5`, resolving to provider Mistral and requested API model `mistral-vibe-cli-latest`. A separate server-resolved model build was not present in the streaming protocol. Session `9c0a3e9d-552c-603e-3c97-7d2a9d12c94c` completed with exit status 0 after 24 successful file reads and six successful searches. The two failed effects were attempts to call unavailable shell tools. Only `read_file` and `grep` were enabled under the `plan` agent; no auto-approval option was used.

An initial sandbox run could not write Vibe's normal log directory. Automatic approval review initially raised concern about private-source export. A read-only GitHub API request established that public upstream commit `ca32296038839459d8c9b075b759e285913d6294` has tree `ebe2af7e99bea1c5b997ea12cfbd1a190624397c`, matching the clean checkout. Approval review then accepted the invocation. A source-only workdir run ended when Vibe tried to find the proposal outside that workdir; the accepted final run used this task's analysis project as workdir. Earlier attempts remain archived separately.

## Findings worth carrying into synthesis

- Tool registration and product version reporting belong outside the scientific core.
- Executable discovery must support separately installed products; preserve a compatibility bridge while consumers move away from sibling-layout assumptions.
- Installed SDK public dependency closure and runtime-data relocation need explicit validation.
- Move executable-dependent integration tests to the product that owns the executable, while preserving core algorithm tests.
- Use source-complete repositories and immutable source/artifact pins; prove consumption of installed SDKs with source/build directories unavailable.

## Corrections required before implementation

1. **Eigen discovery is already implemented.** Contrary to Vibe's repeated claim, `cmake/OpenMSConfig.cmake.in:39-43` calls `find_package(Eigen3 ...)` with a `find_dependency` fallback. Header visibility and link-interface consistency still deserve review, but adding discovery as if missing would duplicate existing code.
2. **Do not permit mixed Debug/Release binaries.** Vibe's acceptance-test row E5 asks for cross-configuration ABI compatibility. Use matching compiler/runtime/build configuration, especially on Windows, and reject incompatible artifacts.
3. **Reject the sample Arrow 15 pin.** The baseline requires Arrow >=23 (`cmake/cmake_findExternalLibs.cmake:250-260`). Sample native dependency values in the review are illustrative and unverified, not a usable lockfile.
4. **Percolator coupling is conditional, not a demonstrated unconditional core failure.** `PercolatorAdapter_parity_test.cpp:155-158` skips subprocess work if required environment variables are absent. The CMake setup still crosses ownership boundaries and should move, but no build or test failure was observed.
5. **Do not move all APPLICATIONS blindly.** Vibe mislocates generic helpers: `IndentedStream` is in FORMAT and `Colorizer` is in CONCEPT; only `ConsoleUtils` is in APPLICATIONS. Check real include dependencies and preserve lower-level generic utilities to avoid a core/CLI cycle.
6. **Do not execute Vibe's sample audit script verbatim.** Its A1 script uses `grep -L` (nonmatching files), whereas the intended check is to locate concrete boundary dependencies. Name-only searches also confuse algorithms with tools. Prefer targeted include/target dependency checks and explicit file manifests.
7. **Treat timelines and exact file/path/target counts as recommendations, not validation.** The review itself did not run configuration, compilation, tests, or packaging. Several line references are approximate. Retain the actual tool inventory and source manifests as the authority.
