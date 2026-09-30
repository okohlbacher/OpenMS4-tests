# Targeted VersionInfo instrumentation

The unmodified production `VersionInfo.cpp` from clean Core commit
`4fdec46b205459b92e7d3b9e56df5d8e912d5c85` and the existing concurrent identity probe
were compiled with the actual Core build compiler, headers and flags. Each profile
links the otherwise uninstrumented Core library and native dependencies. No Core,
vendor, dependency or installed artifact was modified.

- ThreadSanitizer: compile, link and runtime passed; runtime stderr empty.
- AddressSanitizer + UndefinedBehaviorSanitizer: compile, link and runtime passed;
  runtime stderr empty. This is not a leak-detector or whole-SDK result.
- LLVM source coverage used atomic counters for the concurrent workload. Across
  this entire translation unit: 69/99 lines (69.70%), 7/40 branches (17.5%),
  10/14 functions. The changed getters and local-static initializer ran; legacy
  parsing-error, comparison and short-revision/branch paths remain uncovered by
  this probe. Coverage is not a percentage of scientific Core or its tests.

Each of the six changed methods ran 1,600 times across 16 simultaneous workers
(`getVersion()` ran 1,601 times because `getVersionStruct()` initializes through it).
The version-string initialization lambda ran once. Runtime JSON matched generated
metadata. Independent full-SDK runtime acceptance remains necessary: this executable
contains its own instrumented copies of these production methods.

`results.json` records the commands, source hashes, exit statuses and durations.
`coverage-export.stdout` and `coverage-lines.stdout` contain machine-readable and
annotated coverage. `*-run.stderr` preserve sanitizer diagnostics (empty on success).
The machine's existing re2 binary required the installed older Abseil runtime via
an explicitly recorded fallback loader path; no dependency was changed.

Reproduce from the workspace with `python3 core-instrumented-contracts/run_versioninfo.py`.
Optional profile arguments select `tsan`, `asan-ubsan` or `coverage`. The script reads
the coordinated `core-build` compile/link commands and writes only this evidence
directory. It requires a completed compatible native Core build and Xcode LLVM tools.
