# Resumption of Claude's split-package work — 2026-09-13

This resumes the interrupted Core review and closes the previous session's pyOpenMS
and FLASHApp qualification work. The released graph retains Core `bc9cc12514c7`;
the new Core and TOPP branches remain review candidates until their coordinated
consumer and platform checks complete.

## Initial Core review validation

First validated source: `9b568722aee9040b5aa010d2ff4dd0b68357e6dd`, branch
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

## Integration with Claude's newer Core branch

The current review HEAD is `df774c1f88bef0cf314047fb33f75bce6994f86d`. Merge
`268ebb6` also brings in Claude's already-pushed default-branch work through
`ef71b05`: the FragmentIndex thread budget, synchronized FeatureFinder abort
accounting and trace warning, invalid RNA-modification diagnostics, declared
mzTab score columns, and the ci.2 Homebrew formula/bottle workflow. Both histories
are preserved. The earlier `9b56872` results above do not qualify this merge.

The former Homebrew job tapped the default repository and built the released
formula. Its green status therefore did not test the review revision. Commit
`df774c1` now generates a disposable formula from the checked-out formula, pins
the exact Git archive and checksum, removes released bottle entries, builds it,
and verifies the installed source revision and clean flag. The published formula
is unchanged. Three CI helper tests, nineteen SDK contracts and Ruby syntax checks
pass locally. Native and Homebrew qualification is rerunning at this revision.

The exact merged source now passes Linux validation on dax:

| Check at `df774c1` | Result | Wall time |
| --- | --- | --- |
| Release class suite, slow test enabled | 702/702 passed | 22.49 s |
| Targeted Debug suite, including the merged algorithm changes | 16/16 passed | 1.34 s |
| Installed and relocated SDK consumer suites | 8/8 each passed | see acceptance receipt |
| Wrong source revision | rejected with expected diagnostic | see acceptance receipt |

The incremental Release and Debug builds took 19.52 s and 23.25 s respectively,
with zero warning lines in either incremental log. This does not supersede the
vendor-warning limitations of the earlier fresh builds.
[Release XML](port-resumption-2026-09-13/core-merged-release-tests.xml),
[Debug XML](port-resumption-2026-09-13/core-merged-debug-tests.xml),
[SDK acceptance](port-resumption-2026-09-13/core-merged-sdk-acceptance.json),
[build identity](port-resumption-2026-09-13/core-merged-build-info.json), and
[summary](port-resumption-2026-09-13/core-merged-validation-summary.json).

An attempt to register persistent Core runners on dax and the Mac Studio was
rejected by automatic approval review: authorization covered builds, not installing
an ongoing remote-execution service. No new Core runner was installed. The build
continues through existing SSH access to scratch and hosted GitHub Actions.

## TOPP compatibility branch

Source `de96e4a2efedc1cde14a9be6c6811a18540ca0c0`, branch
`codex/core-compatibility`, [draft PR](https://github.com/okohlbacher/OpenMS4-topp/pull/1).
FeatureFinderCentroided no longer mutates the cached overall hull just before
invalidating it. Its individual mass-trace hulls are still expanded. The package
continues to pin released Core `bc9cc12514c7` and CLI `d5213ff3551a`.

| Linux installed-package check | Result | Wall time |
| --- | --- | --- |
| Package metadata tests | 242/242 passed | 0.60 s |
| Combined installation numerical suite | 1,952 passed, five skipped, zero failed | 12.46 s |

[Metadata XML](port-resumption-2026-09-13/topp-metadata-tests.xml) and
[numerical XML](port-resumption-2026-09-13/topp-combined-regressions.xml) retain the
individual results. The five skips need external MSGFPlus, Sage, Comet or MSFragger
executables. The combined prefix has updated TOPP and unchanged previously qualified
sibling products, so the 1,957 entries are not exclusively TOPP tests.

The fresh source checkout and test outputs are under
`/scratch/kohlbach/openms4-topp-de96e4a` on dax. Compilation took 13.20 s after
configuration against a disposable copy of the earlier complete SDK. That copy's
old TOPP registration was removed before metadata tests to avoid duplicate discovery;
installing the new TOPP into the copy then provided its normal CLI/Core runtime
dependencies for numerical tests. The original qualified SDK was untouched.
These checks establish compatibility with released Core; they do not qualify the
pending new Core dependency pin.

All five native platform jobs also passed in push run
[34757301717](https://github.com/okohlbacher/OpenMS4-topp/actions/runs/34757301717).
The two Homebrew payload jobs are still running at the recorded snapshot;
[platform receipt](port-resumption-2026-09-13/topp-platform-ci.json).

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
both manual run `34747196117` and rerun push `34743012215`.
[flashtnt-v1.0.0-ci.1](https://github.com/okohlbacher/OpenMS4-flashtnt/releases/tag/flashtnt-v1.0.0-ci.1)
is published. Release workflow `34757106299` succeeded after the exact-source push
gate passed. All ten asset digests, five archive checksums, executable architectures,
source revisions and Core/CLI/FLASH dependency pins were verified;
[receipt](port-resumption-2026-09-13/flashtnt-ci1-artifacts.json).
These are native package archives that need the matching installed SDK dependencies,
not self-contained application images. The app image above retains its independently
tested FLASHTnT `4ca4e73` runtime pin.

Core's current push CI is
[34757972524](https://github.com/okohlbacher/OpenMS4-core/actions/runs/34757972524),
covering five native platforms and both macOS Homebrew checks. It is still in
progress. Superseded runs and duplicate PR runs were cancelled. Core remains a draft pending those checks,
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

An additional inspection of the MSstats, mzData, mzXML and qcML changes found a
retained-test gap: `MSstatsFile_test` contains no assertions, and many relevant
qcML methods remain `NOT_TESTABLE`. The inherited mzData/mzXML malformed-input
checks were temporary scratch programs. Existing suite success therefore does not
exercise the new rejection and SAX chunk-boundary paths. Preserve those regression
cases in Core's class tests before closing these review groups; no independent
closure is claimed here.
