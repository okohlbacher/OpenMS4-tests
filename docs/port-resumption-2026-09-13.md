# Resumption of Claude's split-package work — 2026-09-13

This resumes the interrupted Core review and closes the previous session's pyOpenMS
and FLASHApp qualification work. The released graph retains Core `bc9cc12514c7`;
the new Core and TOPP branches remain review candidates until their coordinated
consumer and platform checks complete.

## Core review branch

Source: `9b568722aee9040b5aa010d2ff4dd0b68357e6dd`, branch
`codex/cpp-review-completion`, [draft PR](https://github.com/okohlbacher/OpenMS4-core/pull/1).
Claude's first committed batch was `1beb468`; this resumption preserved his remaining
121-file working change and then corrected the review findings and added tests.

The [inherited review ledger](port-resumption-2026-09-13/inherited-core-review.json)
contains 185 candidate verdicts: 156 originally called fixed, 17 documented, 11
deferred and one not-a-defect. These are inherited classifications, not independently
verified closure counts. Eight groups had no completed independent review:
MSstats, mzData, mzML handler, mzXML, ProForma, qcML and the two sqMass groups.

Corrections completed here:

- Apply implicit protein-terminal pepXML modifications only at a matching boundary,
  including pepXML's `-` marker. Preserve explicit per-hit modifications.
- Reject list-valued metadata in numeric filters instead of throwing through the GUI.
- End empty MGF blocks before parsing the next spectrum's metadata.
- Exercise seeded unique-ID collisions, metadata-only peptide identifications,
  mismatched ion-mobility arrays and trailing optional mzTab cells.
- Enable the rewritten `MSDataWritingConsumer_test` (previously commented out).
- Check process timer accounting without assuming a fixed CPU/wall-time ratio.
- Correct the sibling `SimpleTSGXLMS` charge-two suffix-loss calculation; its new
  regression fails against the earlier `e4dcc47` library and passes against `9b56872`.
- Initialize ten test pointers flagged by the clean GCC build and document public API changes.

| Exact-revision check | Result | Wall time |
| --- | --- | --- |
| Full Release class suite, slow test enabled | 702/702 passed | 22.49 s |
| Targeted Debug class suite | 13/13 passed | 0.75 s |
| Installed SDK consumer suite | 8/8 passed | recorded in acceptance logs |
| Relocated SDK consumer suite | 8/8 passed | recorded in acceptance logs |
| Incorrect source-pin rejection | expected diagnostic and failure | recorded in acceptance logs |
| Source SDK contracts | 19 passed | 4.23 s |
| Acceptance-wrapper contracts | 9 passed | 0.25 s |

[Release XML](port-resumption-2026-09-13/core-release-tests.xml),
[Debug XML](port-resumption-2026-09-13/core-debug-tests.xml),
[SDK acceptance](port-resumption-2026-09-13/core-sdk-acceptance.json),
[complete build identity](port-resumption-2026-09-13/core-build-info.json), and
[build timings/warnings](port-resumption-2026-09-13/core-validation-summary.json)
retain the exact evidence. Builds used node-local scratch on dax, GCC 14.4, 192
build jobs, and 96 Release test jobs with one OpenMP/OpenBLAS thread per test.
The node was initially at 0.02 load/core with roughly 2.2 TB free memory.

The first fresh Release compile took 85.97 s but failed to link test executables:
the standalone invocation omitted the dependency loader path supplied by Core CI.
After using the same dependency environment as CI, the build and tests passed.
Subsequent source revisions were built incrementally; the last update took 13.54 s.
The clean Debug library plus thirteen test targets took 44.93 s. These are build
measurements, not a single clean final Release build time. The final incremental
Release build has no warnings; remaining Debug warnings come from untouched
Percolator/Quadtree vendor sources.

The scratch checkout is `/scratch/kohlbach/openms4-core-181dadf/source`; despite the
workspace name it is clean at `9b56872`. Installed output is its sibling `sdk`.
The review changes are not a new released ABI, and optional integrations disabled
in the Core presets were not qualified by these tests.

## Published pyOpenMS and final app image

[pyOpenMS ci.3](https://github.com/okohlbacher/OpenMS4-pyopenms/releases/tag/pyopenms-v4.0.0.dev0-ci.3)
is published at `b7edae7a89d902727e0cd50ff488fefc60e011e0`. Source CI `34720130408`
and release workflow `34756250759` succeeded. All twenty artifacts (native archives,
wheels and both checksums for five platforms) were verified against the producer
outputs; [verification receipt](port-resumption-2026-09-13/pyopenms-ci3-artifacts.json).
The wheels require CPython 3.12; Linux x64 requires glibc 2.39 and macOS ARM requires
macOS 26.

FLASHApp `c8a28307e92d9128f22d4ca6aa527018311a3ffa` pins ci.3. Local macOS tests
pass 136 tests and 52 subtests in 39.91 s, with one skip. The final local image is
`openms4-flashapp:c8a2830-ci3`, image digest
`sha256:5d0ac4f6d179afbc3e481c9e4ea3abc1e942f691bca01dadd76d3527d2e5bbc7`.
It includes the static/header-only dependency notices added in `b551a67`, as well
as the dynamic dependency closure and independently built Vue component.

[Artifact lock](port-resumption-2026-09-13/flashapp-image-artifacts.lock.json):
Core `bc9cc12`, CLI `d5213ff`, TOPP `c6e98a7`, FLASH `b2c6771`, FLASHTnT `4ca4e73`.
Runtime archive SHA-256:
`a1d8e46ddf28e15e0be925d87910a93ea4de2b8431a6d7e898aa284ff8d15d4f`.

All image checks ran without network access or host SDK mounts:

| Check | Result | Wall time |
| --- | --- | --- |
| Native loading, help/INI generation, Streamlit landing and both workflow controls | passed | 4.96 s |
| AQPZ tagging and app parsers | execution and positive scientific checks passed | 11.00 s |
| AQPZ full raw-data workflow | execution and positive scientific checks passed | 12.96 s |

[Smoke receipt](port-resumption-2026-09-13/flashapp-image-smoke.json),
[tagging report](port-resumption-2026-09-13/flashapp-image-tagging.json),
[raw-workflow report](port-resumption-2026-09-13/flashapp-image-raw.json).
Both scientific commands deliberately return failure for the historical comparison:
698 tags versus 2968, ten proteins/PrSMs versus seventeen, score 559 versus 505.
Both match the full 240-residue AQPZ sequence. This repeats the corrected native
port's results but does not establish equivalence to the May 2025 retained outputs.
No image has been published or deployed.

## CI infrastructure and outstanding gates

FLASHApp's hosted jobs were refused before execution by GitHub's billing/spending
limit. Commit `57be473c38b78551ab920cbaac0a8f34617c81a5` permits a repository-selected
Linux runner, and its dedicated dax runner is online. Run
[34756837299](https://github.com/okohlbacher/OpenMS4-flashapp/actions/runs/34756837299)
is green: 134 application tests plus 52 subtests (three skips), and 61 isolated
contract tests plus 52 subtests (two skips). This commit changes only CI routing
relative to the tested image source.

The sixteen Windows runner cleanup hooks now serialize paths with `ConvertTo-Json`.
A native PowerShell/Node test generated the actual hook in a temporary directory,
removed its two designated caches, and retained an unrelated sibling. The corrected
hooks were deployed without restarting running jobs. No credentials were recorded.

FLASHTnT `b0cf76d19340c824d51d3c403c609e11eda7a72e` passes all five platforms in
manual run `34747196117`. Publication requires a successful **push** run, so the
cancelled push run `34743012215` is being rerun at the same source. The annotated
`flashtnt-v1.0.0-ci.1` tag is created; the first release attempt correctly refused
publication while that gate was missing. Publication will be retried after it passes.

Core's final push CI is
[34756983410](https://github.com/okohlbacher/OpenMS4-core/actions/runs/34756983410),
covering five native platforms and both macOS Homebrew checks. It is still in
progress. Superseded runs were cancelled. Core remains a draft pending those checks,
additional review coverage and the coordinated consumer pin/rebuild cycle.

The working integration checkout deliberately still rejects the reviewed Core HEAD
against the released Core lock: 64/65 parent tests passed, with the source-pin test
failing. Claude's generated documentation in the other package checkouts is retained
for the next dependency-order commit cycle. Do not claim this mixed working tree is
a qualified full-graph snapshot. The last complete graph evidence remains the
2026-09-12 report (151 tools, 2039 passing regression entries and five external skips).

Next: finish the incomplete review groups and retained checksum/schema/decoder
follow-ups; qualify Core on all platforms; update consumer locks and generated CI
in dependency order; rebuild and rerun the complete installed-tool suite before
releasing a new consumer graph. TOPP's hull-cache change is prepared on
`codex/core-compatibility` and is independently checked against released Core first.
