# TOPP runtime evidence — 10 September 2026

See [the report](../../topp-runtime-report.md) for measured results and scope.

- `results.json` and `execution-plan.json` are the final aggregate and selection.
- Four JUnit files and `logs/` preserve every test outcome and CTest wall time.
- `benchmark-runs.json`, `benchmark-summary.json` and `benchmarks/` preserve all 72 validated invocations, plus separate cache preparation.
- `environment.json` records build identity; its `tool_omp_threads` field is the runner environment setting, not a claim that every test uses two threads.
- `regression-selection.json` and `regression-excluded.tsv` preserve the initial numerical-only selection. Their 389 metadata exclusions were subsequently executed; `execution-plan.json` supersedes that part of the initial selection.
- `benchmark-input.json` includes planning notes written before cache creation. Final cache results are in `cache-creation.json`.
- Run recipes and `metadata-CTestTestfile.cmake` use the original local directory layout and absolute paths. They are evidence, not portable package defaults.
- Fixtures, generated test outputs, metadata products, SDK binaries and the benchmark cache are omitted to avoid duplicating package data. The pinned test-data package provides the benchmark fixture.

`SHA256SUMS.json` covers every evidence file except itself.
