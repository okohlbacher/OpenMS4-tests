# Standalone tool backends: implementation plan

This plan supersedes the earlier ownership proposal where it suggested moving file writers out of Core. Requested on 2026-09-10: retain file-format support in the SDK; extract NuXL, ProSE, NASE and FLASH tools, with independent repositories and maximum-parallel native validation.

## Ownership

| Package/repository | Executable and implementation ownership |
| --- | --- |
| OpenMS4-nuxl | OpenNuXL, NuXL search algorithms, presets and algorithm tests. NuXLReport, its marker-ion support and report tests remain Core. |
| OpenMS4-prose | ProSE, exported ProSEAlgorithm backend, search/report tests and optional Bruker search integration. Generic Bruker reader tests remain Core. |
| OpenMS4-nase | NucleicAcidSearchEngine (executable name preserved). NASequence, ModifiedNASequenceGenerator and chemistry/file support remain Core. |
| OpenMS4-flash | Existing FLASHDeconv executable, exported deconvolution/trace/FDR/quantification backend and algorithm tests. FLASH records, file writers and their required scoring primitives remain Core. Web applications are outside this change. |
| OpenMS4-comet | CometAdapter and native-ID remapping. Comet modification parameter representation/serialization remains Core. |
| OpenMS4-mascot | MascotAdapterOnline and MascotRemoteQuery service transport. Mascot format codecs, generic CURL initialization and HTTP utilities remain Core. |
| OpenMS4-database-suitability | DatabaseSuitability and its DBSuitability workflow, including TOPP adapter invocation. Shared FDR/identification/file primitives remain Core. |
| OpenMS4-proteomics-lfq | ProteomicsLFQ and DDAWorkflowCommons recipes. Scientific calibration/feature-finding primitives remain Core. |
| OpenMS4-parquet-diff | ParquetDiff and comparison logic. Arrow schemas, Parquet readers/writers and generic I/O remain Core. |

MQ, GNPS, SIRIUS, MSstats and all other reusable format readers/writers stay in Core. Product-specific CLI report rendering may accompany its algorithm; an existing reusable serializer stays in Core. No implementation is copied into two library providers. The remaining TOPP manifest must own each remaining tool exactly once.

FLASHDeconv is the only FLASH executable present in the audited source snapshot. FLASH modes do not imply additional executable sources; absent FLASHTnT/FLASHQuant tools will not be invented or fetched from an unpinned branch. Existing FLASHApp code is unchanged.

## Package and API contract

Products consume only installed, exactly pinned SDKs. ProSE and FLASH export independently versioned shared backend targets usable without CLI/executables. Existing Python APIs link these providers; full Python builds retain those APIs, with explicitly selectable backend features for a Core-only Python build. Core never depends on a product library.

The experimental C++ API/ABI change is explicit: moved installed headers/symbols are provided by their new developer package or become private tool code. Existing experimental tags remain unchanged. Core source revision, downstream locks, library identities and parent gitlinks must agree. A combined fresh install prefix prevents stale Core headers from hiding missing dependencies.

Private helpers use ordinary sources or a private static target shared with their unit tests. Existing standalone CMake metadata, tool manifests, TestSupport and fixture packages are reused. No new repository per helper or generic workflow framework is needed.

## Implementation and acceptance sequence

1. Move algorithms, helpers, tests and product resources; retain codec/data dependencies in Core. Cut FLASH's reverse scoring edge by placing shared numerical primitives in the existing Core scoring class, preserving FLASH API wrappers. Preserve Core NuXL report assertions using generic modification fixtures.
2. Create the eight new private repositories and add them as parent submodules; extend the existing FLASH repository. Update ownership/source checks, provenance and tool manifests. Preserve licenses and original source paths/hashes.
3. Commit the reduced Core, build it in Debug with 16 jobs and run its independent class/SDK tests. Install to a fresh SDK prefix. Commit and build pinned CLI/TestData next.
4. Commit/build the separate backends and tools, remaining TOPP/OpenSWATH and affected Python/desktop consumers from installed dependencies. Use a global budget of 16 parallel compilation jobs; independent build processes divide that budget rather than multiplying it. Record actual elapsed times and results.
5. Run relocated class tests, tool metadata checks and installed numerical regressions. Preserve format round-trip tests in Core. Exercise ProSE/FLASH Python APIs after rebuilding bindings. External-engine/server and optional vendor-reader cases remain explicitly reported according to available dependencies.
6. Verify reduced SDK installation, exact-pin rejection, unique executable ownership and retained format support. Update/publish dependency commits in order and parent locks/gitlinks last. Preserve published tags; report actual native results and any remaining platform/external-service limits.

DBSuitability's ordinary tests disable external correction; existing configured third-party tests and a local adapter contract cover that distinct path. Mascot transport likewise requires bounded local-server validation in addition to its default-state class tests; live Mascot integration is separately gated.

This file records the plan. Completed changes, source pins, commands, elapsed times and acceptance outcomes belong in the accompanying execution report; planned checks are not claimed as passes.
