# Would splitting OpenMS into packages help with the documented maintenance issues?

## 1. Answer

**As built on 14 September 2026, the split would make the documented maintenance problems worse overall.** The package boundary itself prevents very few of the incidents in the review.

**What the boundary genuinely prevents:**
- pyOpenMS modules can no longer leak unsigned into the desktop installer (#9827).
- A change in how Qt is packaged can no longer reach Core, TOPP or wheel CI (#8368).
- A product can publish while a sibling product is broken.

**Why most other incidents are missing from the split's record:** the split made choices the monorepo could make just as well.
- It turned features off: Thermo RAW, OpenTIMS, WNETALIGN, TDL, ONNX and HDF5.
- It dropped whole delivery channels: installers, signing, Bioconda, containers and a nightly package index.
- It uses conda-forge and GitHub release assets instead of vcpkg and university servers.

**What the split adds.** It brings maintenance costs of its own that the monorepo does not have. They grow with the number of packages and with how fast upstream changes:
- Every Core change triggers a re-pin across the whole package graph.
- No cross-package test runs before Core is tagged.
- Binaries are released independently with no binary-compatibility identity. A pairing currently served by the Homebrew tap was shown to crash.
- Every CI change has to be copied into each repository.
- Upstream changes have to be ported by hand.

**Confidence.** Medium to high on the direction of the effect for the current design. Low on its size, because the split's record covers five days of bring-up that overlapped a large C++ fix campaign.

Section 6 lists design changes that could bring the net effect to roughly neutral. Even with all of them, the case for the split would have to rest on other goals, such as independent release cadence or smaller contributor builds. It does not rest on this incident record.

## 2. Scorecard

Verdicts describe what the split does to each incident class. "Intrinsic" means the effect comes from the package boundary itself. "Choice" means a monorepo could make the same decision. "Maturity" means a gap that a more mature split would close. Rows marked **corrected** changed after verification or after removing double counting.

| Incidents | Issue | Verdict | Cause | Conf. |
|---|---|---|---|---|
| #9721, #9814, #9897 | Bioconda fork overlay conflicts, duplicate lint key | neutral | none | medium |
| #9905, #9907 | Stale tooling pin; ICU/xerces and percolator/gnuplot solve failures | **n-a (corrected from worse)**. The split publishes no conda packages. The remaining cost (conda-forge migrations need a Core cycle) is counted in the dependency-profile row | none | medium |
| #10078, #10111 | Per-output lint on openms-thirdparty; 9 nights blocked on fork access | neutral | choice | medium |
| #9914 | `\|\| true` masked build failures | n-a | none | high |
| #10114, #10113 | Same-soname libcurl chosen at link time; no dependency RPATH | mixed. More exercise, more places a provider gets chosen. Recurred in split CI (pyopenms a82f852) | intrinsic | low |
| #8880 | VCRUNTIME140.dll found in two directories during installer collection | n-a | choice | medium |
| #8797, #9444 | Conda as rescue provider | neutral | choice | medium |
| #9687, #9725 | Two Arrow runtimes in one Python process | neutral. Unchanged: conda libarrow 23.0.1 ships next to PyPI pyarrow 25.0.1 | none | medium |
| #8701 | Windows DLL load failure on a user machine | neutral. The class recurred in split CI (STATUS_DLL_NOT_FOUND) | none | low |
| #7271, #8910 | zlib-ng changes compressed output bytes | **latent (corrected from worse)**. HAVE_ZLIB_NG is never exported to test-data, but no split CI host uses zlib-ng | intrinsic | medium |
| #9057, #9061, #9064 | OpenTIMS on MSVC | n-a. Feature is OFF | choice | high |
| #9392, #9389 | Thermo bridge changed exception matching in libOpenMS | n-a. Feature is OFF and would return into Core | choice | medium |
| #8485 | Homebrew static Arrow targets | neutral | choice | low |
| #8369, #8614, #8624 | fix_dependencies.rb could not relocate Brotli | n-a. No bundle is built | none | medium |
| #9065 | Spack Arrow built without CSV | neutral | none | medium |
| #9196 | Runner image shipped Arrow 24 | mixed. Pinning prevents overnight breaks (a choice); any Arrow move needs a whole-graph cycle | intrinsic | medium |
| #8776 | Homebrew LLVM with system libc++ | neutral | none | low |
| #9039, #9076 | Boost minimum too low; contrib Boost | neutral | choice | medium |
| #8368 (Qt), #8598 | Qt repackaging; distro Qt too old | **helps**. Qt exists only in desktop | intrinsic | medium |
| #8368 (libomp) | Keg-only libomp must be named explicitly | worse. Recurred at the first consumer configure; the hint is now copied into 27 driver files in 16 repositories | intrinsic | low |
| #8482 | Vendored sqlite3.h collided with another provider | neutral. Recurred in the Homebrew bottle | choice | medium |
| #8346, #8530 | Isolated pyOpenMS build lacked NumPy | neutral | choice | medium |
| #8236 | Monolithic Homebrew Arrow pulls in LLVM | mixed. Returns in 22 cask jobs per cycle | choice | medium |
| #9827 | pyOpenMS modules leaked unsigned into the macOS .pkg | **helps** | intrinsic | medium |
| #9480 | Thermo bridge installed outside the signed components | neutral | choice | medium |
| #8506, #8527 | Unsigned third-party files; missing timestamps | neutral. Nothing is signed | choice | low |
| #8723 | Sporadic notarization rejection | n-a | none | low |
| #9457, #9467 | Apple agreement lapse blocked all deploys | neutral. Isolation helps only if signing is kept out of the release gates | intrinsic | low |
| #9969, #9978, #9991, #10009 | NSIS path-length chain | mixed. Other packages keep releasing; path-length failures recurred in the nested test-data checkout | intrinsic | low |
| #9458 | Tarball archived its own output directory | neutral | none | high |
| #8463, #8477 | Cocoa plugin shipped as a link; pkg relocation | n-a. No installer | none | medium |
| #8749, #9631, #9626 | Tübingen PyPI flakiness and migration | neutral | choice | medium |
| #9762 | Full disk; incomplete nightly set | mixed. Each package's set is complete; the set of packages at one Core version is not | intrinsic | low |
| #9702, #9863 | Deploy host unreachable | mixed. Self-hosted runners now sit inside the release gate | choice | low |
| #9284, #9845 | Stale docs and archive pointers | mixed. CI catches a stale Core pointer quickly; user-facing pointers (tap, attached formula, docs) are stale now | intrinsic | medium |
| #9938 | Secret-backed cache unavailable to fork PRs | **helps (plausible) (single ruling)**. A cold fork PR builds only its package. No fork PR has run yet | intrinsic | low |
| #9951, #9954 | Mutable reference resolves to the wrong content | worse. The tap serves an older Core (same mechanism as the tap row below) | choice amplified by intrinsic | medium |
| #9899, #9906 | Unpinned tool drift | lint incident n-a. **Propagating CI fixes across repositories is worse (single ruling)** | intrinsic | low |
| #9717 | Vendor NuGet feed flake | mixed | intrinsic | low |
| #10105 | vcpkg cache invalidation, source download timeout | neutral | choice | medium |
| #9890, #9891 | Build and runtime stages used different Arrow pins | mixed. EXACT versions checked within a channel; conda and Homebrew profiles differ | intrinsic | low |
| #10015 | Artifact download silently missing a wheel | mixed. The generated gate counts `.sha256` files with `-ge` | choice | low |
| #9785 | pull_request_target broke on fork PRs | neutral | choice | medium |
| #9729, #9750, #10022 | APT key rotation | neutral | choice | medium |
| #9599, #9598 | Agentic automation quota | n-a | none | medium |
| #9792, #9947 | pyOpenMS ownership regression | neutral | none | high |
| #9515, #9583 | LogStream races | neutral | none | high |
| #8681, #8689 | Base64 strict-aliasing SIGBUS | neutral | none | medium |
| #9946, #9957 | pyOpenMS import failure with WNETALIGN=OFF | **worse, latent (corrected from mixed)**. `WITH_WNETALIGN` is gone from split config.h, so the pyOpenMS guard is always false and the green import test proves nothing | intrinsic | medium |
| #10048, #10057 | Assertion aborts only in Debug builds | neutral. Release-only CI in both | none | medium |
| #10053; split ci.3 | Core fixes that change tool outputs | worse today. Linux share cheap to fix (check 2); macOS/Homebrew share intrinsic | intrinsic | medium |
| #10050, #10055 | 1x1 matrix assertion | neutral | none | medium |
| #9671 | Intermittent NuXL failures on macOS ARM | mixed | intrinsic | low |
| #9925 | Windows nightly no output on one machine | neutral | none | low |
| #8952, #8916 | Wrong compiler attribution; unverified failure count | neutral | none | high / medium |
| #7600, #7886 | Incident dates vs update dates | neutral | choice | low |
| #8369/#8614 (closure), #9899 (tracker) | Closed or released is not resolved | worse. ci.3 page still claims a full pass | intrinsic | medium |
| Split: cask/formula pairing | TOPP ci.4 cask built on Core ci.2, now installed on Core ci.4 | **worse, demonstrated (corrected from latent risk)**. Crashes and silent memory overwrite (check 3) | intrinsic | high |
| Split: tap follows Core's branch | Cask jobs build the wrong Core | worse. 59 first-attempt cask failures | choice amplified by intrinsic | high |
| Split: Boost/Arrow profile drift | dax Boost 1.92; Homebrew vs conda profiles | worse | intrinsic | medium |
| Split: whole-graph re-pin | Every Core change reaches 14 to 17 repositories | worse | intrinsic | high |
| Split: upstream porting | 19 upstream commits not carried | worse | intrinsic | medium |

Several split costs showed up in four to eight review clusters: the tap, ci.3, and the re-pin. This table counts each once.

## 3. Where the split helps, and why

### 3.1 Products cannot leak into each other's payloads

Upstream productbuild packaged every CPack component the configure knew about. pyOpenMS's `python_modules` component therefore entered the macOS installer unsigned, and notarization rejected the whole installer (#9827). Keeping that out needs a denylist, which already needed a second entry for `OpenMSTestFramework` (#9929).

In the split, pyOpenMS is a separate CMake project. `packages/desktop/CMakeLists.txt` never mentions it. The mechanism is removed by construction. The benefit is modest, though: upstream's fix changed one file and merged about 10 hours after it was opened.

### 3.2 Qt is confined to the desktop repository

`tools/scaffold_package_ci.py` adds `qt6-main>=6.7` only for desktop, and the shared environment template contains no Qt. A Homebrew or conda Qt repackaging like #8368 cannot touch the CI of Core, TOPP or pyOpenMS. Upstream's #8368 had to edit the wheel workflow too.

Desktop's Qt 6.7 minimum also turns #8598 (distro Qt 6.2) into a clear configure error. A monorepo could declare an accurate minimum as well, so that part is weaker.

### 3.3 Products release independently of failing siblings

Upstream's `release.yml` fans in: `deploy-installer` and `deploy-docs` need every build leg, and `publish-release` needs all of them. So one bad platform or service withholds every deliverable:
- Run 32798490849 (Windows NSIS failure) skipped all deploys.
- Run 28835615666 (Apple agreement lapse, #9457) did the same.
- Release run 34425622414, from the review window itself (10 Sep, a transient Windows link failure), skipped all deploys and was never filed as an issue.

In the split, pyOpenMS ci.3 and FLASHTnT ci.1 were published on 13 Sep while the other products stayed at ci.2.

The benefit has two limits:
- Within a package, the gate is still all-or-nothing. It requires exactly 7 archives when casks exist (`scaffold_package_ci.py:262-310`). TOPP run 34852655247 had five green native jobs and still could not be released because both cask jobs failed.
- A Core-level failure blocks every consumer. The ci.3, ci.4 and ci.5 cycles produced no consumer releases at all.

### 3.4 Mismatches fail loudly and early

`cmake/OpenMS4Dependencies.cmake:62-63` fails with "SDK revision mismatch", and the installed `OpenMSConfig.cmake` pins Boost, Arrow and Parquet as EXACT. Mismatches become one-line configure errors within minutes:
- The dax Boost 1.92 drift.
- Every stale-tap cask job.

Every consumer is also an installed-SDK consumer, so the installed-consumer setup behind #10114 is exercised on every push. Upstream only added such a test with #10103.

Other diagnostic aids help too: provenance files (`OpenMSBuildInfo.json`, `dependencies.txt`, `_build_provenance.json`), the loaded-library check in Core acceptance, and wheel tests in a fresh virtual environment with library paths stripped. All of those are choices a monorepo could adopt. Only the revision guard is exclusive to the split, and it mostly catches mismatches the split itself creates.

### 3.5 Smaller builds for consumers

A consumer builds against a prebuilt Core:
- A package builds on dax in about a minute.
- TOPP's hosted linux-x64 job took 140 s, and CLI's 88 s.
- Upstream PR CI rebuilds all of OpenMS.

That should make cold-cache fork PRs much cheaper (#9938), and would keep vendor fetches out of consumer jobs if Thermo came back inside the SDK (#9717). Neither effect has been exercised: no fork PR has run against a split consumer, and Thermo is OFF.

## 4. Where it makes things worse

### 4.1 Whole-graph pin cycles against upstream's rate of change

Exact source pins are enforced in three places: parent `packages.lock.json`, each consumer's `dependencies.lock.json`, and the CMake revision guard. `tools/repin_packages.py` rewrites consumers in topological order, so one Core move becomes 14 to 27 commits, a CI run in every consumer repository, and a release chain.

**Cost of one cycle.** The ci.5 consumer cycle took 13 runs and about 820 job-minutes (two measurements: 814 and about 825). More than half of that went to cask jobs that failed.

**Mid-cycle state.** The invariant cannot hold during a cycle. Running `tests/test_package_pins.py` on today's working tree fails 2 of 3 tests. Desktop, FLASHTnT and FLASHApp still pin Core ci.2, while the other 14 packages pin ci.5, and phase 2 has not run since ci.2.

**Upstream's rate** (check 1: first-parent diffs over the 8 complete weeks the shallow clone covers):

| Upstream commits per week | Mean | Median |
|---|---:|---:|
| Touching Core | 14.9 | – |
| Touching public headers | 9.0 | – |
| Changing Core together with a consumer | 6.9 | 5 |

The last 30 days had 74 Core commits, 43 of them header-touching, and 29 changes spanning Core and a consumer. In the split, each of those 29 would be a multi-repository change with no combined CI.

Section 4.3 shows that a public-header change can break already-published binaries. Core changes therefore cannot be released one by one. They must be batched, or the graph rebuilt about weekly at roughly 820 job-minutes per round.

**Caveat (check 8).** The five cycles in three days were driven mostly by Homebrew bring-up (ci.1 to ci.2) and by the C++ fix campaign and its side effects (ci.2 to ci.5). That count should not be extrapolated; the weekly rate above is the better basis.

### 4.2 No cross-package test before a Core tag

The installed TOPP regression suite lives in `test-data`, which has no GitHub workflow. It runs only in manual `tools/build_packages.py` rebuilds on dax.

**What happened with ci.3.**
- `core-v4.0.0-ci.3` passed all seven Core CI jobs and was tagged at 20:53 CEST on 13 Sep.
- At 21:04 the dax rebuild reported 107 of 2,047 installed tests failing; 89 of the failures came from CPP-026. Core class tests "do not compare those outputs" (`docs/cpp-issues-review.md:78-85`).
- The prerelease page still says the archives "passed the full enabled scientific test suite", and ci.4's notes are identical boilerplate.
- Real scientific fixes (CPP-026, CPP-042, CPP-043) were reverted instead of landing together with updated references. CPP-042 is still in the backlog.

**Upstream comparison.** PR CI runs the TOPP suite by default: `_openms_topp_testing_default ON`. PR job 104074820362 ran 2,877 tests, 1,650 of them TOPP tests, in 331 s. #10053, a comparable output-changing fix, landed its source change and 41 reference updates in one PR about 13 hours after the report.

**Check 2: much of this gap is cheap to close.**
- On dax, the regression suite's total test time was 10.8 s at parallel 160, the CLI build 9.4 s and the TOPP build 28 s.
- A Linux-only canary would add an estimated 10 to 15 minutes to hosted Core CI, and it would have caught ci.3.
- It would not catch failures that appear only on macOS or in Homebrew. CPP-181 was one: a Core header change that made `OSWFile`'s defaulted copy constructor implicitly deleted. It failed only in TOPP's "Homebrew cask payload / macos-x64" job (run 34810509107) and cost a whole extra cycle (ci.5).

So the Linux part of this gap is a maturity issue; the gap for distribution profiles is intrinsic.

### 4.3 Independently released binaries with no ABI identity: a demonstrated crash

**How the mismatch arises.**
- The published TOPP cask (`Casks/openms4-topp.rb`, version `1.0.0-ci.4,c6e98a7782cc`) was built against Core ci.2 (`topp-v1.0.0-ci.4:dependencies.lock.json` pins `bc9cc12`).
- It declares `depends_on formula: "okohlbacher/openms4-core/openms4-core"` with no version.
- The tap's default-branch formula now builds Core ci.4.
- `libOpenMS` has no SOVERSION (compatibility version 0.0.0).
- `homebrew-cask.yml` triggers only on `Casks/**`. It last ran on 12 Sep, before the formula moved.
- 43 public headers changed between ci.2 and ci.4.

**Result (check 3).** Linking succeeds: all 1,628 imported libOpenMS symbols exist in ci.4. Runtime does not:
- `MSDataWritingConsumer` grew from 3,784 to 3,816 bytes, because ci.4 added `first_spectrum_data_processing_` and `warned_undeclared_references_`.
- `ConsensusFeature::Ratio` shrank from 88 to 80 bytes.

The ci.2-built TOPP binaries were then run against ci.4 libOpenMS in six low-memory test cases (NoiseFilterGaussian, NoiseFilterSGolay and PeakPickerHiRes, `_3` and `_4` variants). Every case crashed with a bus error or segfault; all exit 0 against ci.2. lldb shows `EXC_BAD_ACCESS` inside `vector<shared_ptr<...>>::__assign_with_size`, consistent with the ci.4 base class writing its new member past an object laid out for ci.2.

`FileConverter` in low-memory mode exits 0 with identical output. That means the extra 32 bytes are written into memory silently.

**Scope of the test.** It used a local ci.4 build from the formula's tarball (sha256 matches) with the formula's flags, not the published bottle. Object layout is determined by the headers, so the result should carry over.

This is intrinsic to independent release streams without versioned dependencies or SOVERSION. A monorepo ships all components from one build.

**A related cost: two dependency profiles per release.**
- Conda archives: Arrow 23.0.1 and Boost 1.89.
- Homebrew cask payloads: Arrow 25.0.1 and Boost 1.92 (run 34852655247).
- dax's Boost 1.92 drift broke every consumer configure in the ci.4 graph check, and a round of receipts had to be discarded.

Provider hints such as `OpenMP_ROOT` are not carried by the SDK. They sit in 27 driver files across 16 repositories.

### 4.4 Feature information lost at the SDK boundary

**WNETALIGN (check 6).** Upstream fixed #9946 with `#cmakedefine WITH_WNETALIGN` in `config.h` (#9957). Split Core's `config.h.in` has had no such line since the first extraction commit. Core defines `OPENMS_HAS_WNETALIGN` only as a PRIVATE compile definition. As a result:
- `packages/pyopenms/bindings/bind_misc.cpp:43,847` (`#ifdef WITH_WNETALIGN`) can never compile the WNet bindings. If Core re-enables WNETALIGN, pyOpenMS will silently lack them.
- TOPP is not affected. It reads the exported `OpenMS_WITH_WNETALIGN` through the tool manifest. The earlier claim about `executables.cmake`, which no CMake file includes, is withdrawn.

**zlib-ng.** `HAVE_ZLIB_NG` is set only in Core's `cmake_findExternalLibs.cmake:161-166` and read only in `test-data/topp/CMakeLists.txt:68`. The #8910 accommodation is therefore lost across the boundary, though latently: none of the seven jobs in Core run 34837442481 detects zlib-ng.

### 4.5 CI and release work multiplied per repository

**Volume.**
- 377 of 602 package commits made on 10 to 14 Sep changed only CI, lock, Cask or Formula files.
- There are 48 self-hosted runner registrations.
- Generated drivers are copied into each repository with no "do not edit" marker.

**Generator and copy failures.**
- The generator put `runner.name` into job env, producing zero-job failed runs in 13 repositories (fixed in 888fdf5d87).
- The ci.4 re-pin re-copied templates and removed the `OPENMS4_SERIAL_TESTS` switch from 9 repositories (mascot 55978bc). The session then concluded wrongly that "the serial-ctest fix did not work"; correcting that took about 5 hours.
- A Windows DLL-path fix (STATUS_DLL_NOT_FOUND) was committed separately across the consumer repositories within 15 seconds. The verification gives "9" but lists ten names.

**Drift that is already visible.**
- The template fixes (888fdf5d87, 25cc7b7b59, a13e846baf) are among 13 unpushed parent commits. The pushed template still lacks the serial-test switch.
- TOPP's hand-written `topp.yml` still runs Windows on hosted runners.
- `topp.yml` still references a deploy-key secret made unnecessary when CLI became public.
- Twelve packages pass `OPENMS4_WARNINGS_AS_ERRORS`, but only TOPP and FLASHTnT define it.

### 4.6 The Homebrew tap and formula lag behind Core

Consumer cask jobs run `brew tap` on Core's default branch without a ref (`scaffold_package_ci.py:243-246`), build from source for 10 to 35 minutes, and are then rejected by the revision guard:
- 59 first-attempt cask failures across ci.3 to ci.5.
- 22 of 22 cask jobs failed at ci.5, and 30 of all 92 failed split runs involve Homebrew jobs.
- Every cycle needs a human merge of a Core PR; PR #2 is still open.

**Ruling (check 4).** The formula inside every tag names the previous release, because formula commits land after the tag. A tap pinned to a tag would therefore still install the previous Core. The lag comes from keeping the formula in the source repository, which is a choice. The formula attached to each release is fixable in the workflow: `tools/ci/prepare_homebrew_formula.py` already generates a formula for an exact revision.

What the split adds is 11 exact-revision consumers that depend on that formula, plus the ABI coupling shown in 4.3.

### 4.7 Upstream sync debt

`origin/develop` has 19 commits after the baseline `ca32296038`. Only one fix has a split equivalent: the FragmentIndex fix (#10129 upstream, `50e07ec` in split Core). Check 10 path-mapped three upstream PRs and tested them with `git apply --check`:

| Upstream PR | Files | Split repos reached | Clean | Only with `-C1` | Fail |
|---|---:|---:|---:|---:|---:|
| #10100 (dc17149b06) | 96 | 10 | 90 | 1 | 2 (3 doc files had no home) |
| #10103 (f97bc89d90) | 9 | 1 (Core) | 4 | 1 | 4 |
| #10113 (c621aaff7c) | 8 | – | 1 | 1 | 6 (partly cascading from #10103) |

Source-level API changes mostly apply mechanically, but each one becomes a change across several repositories plus a pin cycle. Build-system fixes, including the #10114/#10113 installed-consumer RPATH work that split Core lacks, have to be redone by hand. The split's own Core fixes (229 CPP rows) are not upstreamed, so the two trees diverge in both directions.

### 4.8 Operational record, normalised

Check 5 compared both sides over 10 to 14 Sep.

**Upstream:**
- Build and Test failed 7 of 76 runs and pyopenms-wheels 5 of 76 (with 32 cancelled), all on pull requests.
- After merge, 6 failures from two causes: one transient Windows link in Release, and 5 Bioconda nights. The Bioconda failure was filed as #10111 and is already in the review.

**Split:**
- 92 failures in 402 runs; 89 were not on pull requests (83 push, 6 dispatch).
- Failures per day: 3, 15, 25, 20, 29. They did not fall after bring-up, and 49 fell on 13 and 14 Sep.

**Recurrences (check 9).** Several review incident classes recurred in the split and were fixed quickly without being recorded as incidents:
- Windows DLL loading (#8701 class).
- Path length: "Filename too long" in the nested test-data checkout (#9969 class).
- A duplicate library provider in the wheel: delocate's "Already planning to copy library with same basename as: libzstd.1.5.7.dylib" (#8880 class).
- Installed-SDK `@rpath` resolution (#10114/#10113 class).
- A package-cache failure, still present on the Windows workstation.

The #8482 SQLite header collision and #8236's LLVM-heavy Arrow also came back through the Homebrew channel.

## 5. What the split does not touch

**External accounts, services and ecosystems.**
- Apple Developer agreement lapses (#9457) are account events.
- Bioconda recipes must live in `bioconda-recipes` whatever the source layout, and the fork access boundary that stalled #9721 and #10078 is unchanged.
- conda-forge migrations (#9905), PyPI pyarrow releases (#9725), runner-image updates (#9196, #10105) and GitHub billing limits (FLASHApp's refused hosted jobs) all arrive the same way.

**Core-internal defects.**
- LogStream races (#9515), Base64 aliasing (#8681), Debug-only assertions (#10048, #10057), the 1x1 matrix (#10055) and binding ownership (#9792) all land in one repository in either layout.
- Both layouts run Release-only CI with no sanitizer lane; project-state.md records "Core CI has no AddressSanitizer job".
- The detection for #10048 needs one Core Debug job in either layout.

**Two Arrow runtimes in the wheel (#9687, #9725).** The split wheel still bundles conda libarrow 23.0.1 and is tested beside PyPI pyarrow 25.0.1. The mitigations in use are inherited from upstream.

**Diagnosis quality (#8952, #8916).** These were reasoning errors. The split's record contains the same kind: the serial-ctest misdiagnosis, and five withdrawn explanations for the Studio launch stall.

**Removed features and channels.** A large share of the review's installer, signing, native-reader and university-server incidents cannot occur because the split lacks the feature or channel involved.
- The split's own plan brings Thermo and optional readers back into Core. That would restore the #9392 and #9057 blast radius inside the one library all 17 consumers load.
- Check 7 found that upstream's move to vcpkg was about consolidating six dependency mechanisms (#9451), not about package boundaries, and that #9451 keeps system packages as the fallback for conda packagers. The conda-forge path is therefore not something only a split can take.

## 6. Deciding conditions: what would make the net effect positive

These are mapped to the review's eight priorities. The first two items under P1 and the first item under P6 decide most of the verdict.

**P1. Validate the delivered artifact and publication set.**
- Give casks a versioned Core dependency (`openms4-core@<cycle>`), or bundle the Core runtime in each payload.
- Set a SOVERSION or install name that includes the Core cycle, and add a startup check in CLI that compares the linked Core revision with the one recorded at build. The pairing in 4.3 would then fail loudly instead of corrupting memory.
- Have a formula change trigger install tests for every cask.
- Change the generated release gate to require `-eq` for `.sha256` files too, closing the #10015 gap.
- Gate native archives separately from cask payloads.

**P2. Make dependency provenance explicit.**
- Create consumer environments from Core's `dependencies.txt` instead of re-solving them.
- Record a binary-profile hash (compiler, flags, provider, key dependency builds, features) and compare it in `openms4_find_package`.
- Restore `#cmakedefine WITH_WNETALIGN` and export `HAVE_ZLIB_NG`.
- Carry provider hints such as the OpenMP location in the SDK config, not in 27 driver copies.

**P3. Separate the reproducible release environment from update detection.**
- Pin the release environment fully.
- Add a scheduled job, run in no package workflow today, that floats dependencies without gating releases.
- Use one dependency provider per release set, or name the provider in artifact names.

**P4. Give deployment services explicit ownership.**
- Move the formula to a separate tap repository that Core's release workflow updates, or attach the output of `prepare_homebrew_formula.py` at tag time.
- Tag releases only from the default branch.
- Move to an organization with runner groups and automatic fallback to hosted runners.
- Push the parent at every cycle step, and give it a workflow that runs the pin and doc checks.

**P5. Cache dependency bytes and verify alternate sources.**
- Keep the checksum-verified SDK download, add retries (FLASHTnT run 34741104219 hit HTTP 500), and let integration CI consume dependency artifacts by CI run instead of by published tag.

**P6. Run a targeted configuration matrix.**
- Add a required downstream canary before any Core tag: candidate SDK, CLI and TOPP build, and the installed regression suite on linux-x64 (about 10 to 15 minutes by check 2).
- Add one macOS consumer build with the strictest consumer warning policy.
- Add a Core Debug/UBSan lane and a feature ON/OFF matrix before re-enabling Thermo, OpenTIMS or WNETALIGN. This applies equally to a monorepo.

**P7. Treat signing as an inventory of final payloads.**
- Sign in one suite-level step that consumes published artifacts and walks every Mach-O and PE file.
- Keep that step out of the per-package release gates, so that an account lapse (#9457) blocks only signed deliverables.

**P8. Preserve the first real failure and require closure evidence.**
- Replace copied drivers with reusable workflows pinned by SHA.
- Mark generated files as generated.
- Mark disqualified and superseded prereleases (ci.3, ci.4) on their release pages.
- Route issues to one public tracker.

**Structural conditions beyond the review's list.**
- Replace whole-graph lockstep with a compatibility range checked by an ABI tool, so Core fixes that keep compatibility need no consumer commit.
- Reduce the graph: merge the six one-tool repositories, and consider keeping CLI with Core.
- Decide which tree is authoritative. If both stay alive, build path-mapped patch transport with a ledger of carried upstream PRs.

Meeting all of these would remove most of the "worse" rows. It would not turn the neutral rows into benefits, because those incidents do not depend on the package boundary. The expected best case is a roughly neutral maintenance picture with modest wins (3.1 to 3.5), at the continuing cost of the pin and porting work in 4.1 and 4.7.

## 7. Limits of this review

**Record length and composition.**
- The split's history is five days (10 to 14 Sep 2026) of bring-up by one maintainer, overlapping a 229-row C++ fix campaign.
- The review is a curated 12-month issue sample that explicitly excludes a census of CI failures.
- Check 5 normalised post-merge failure counts over the same window, but steady-state behaviour is unknown.
- Durations are wall-clock, not person-hours.

**Crash test (check 3).**
- It used a local ci.4 build from the identical tarball, not the published bottle.
- Linux and Windows pairings, PeakPickerIM low-memory mode and the `ConsensusFeature::Ratio` size change were not tested at runtime.

**Other checks.**
- **WNETALIGN (check 6):** the ON build was not run, because it would download dependencies through FetchContent; the finding comes from reading code.
- **Upstream change rate (check 1):** the local clone is shallow (from 19 Jul 2026), so only 8 complete weeks were counted.
- **Porting (check 10):** only `git apply --check` was run on three PRs. Hand-resolution time was not measured, and a three-way merge was impossible because the children have no upstream history.
- **Monorepo on conda-forge (check 7):** not built. That the conda-forge path is feasible for the monorepo is inferred from upstream's stated rationale, not tested.
- **Unclassified failures:** 14 failed split runs listed no failed job.
- **Unverified claim:** the claim that 29 of the last 30 merged upstream PRs were fully green was not re-verified.
- **Cluster matrix:** the incident-by-mechanism matrix was not rebuilt from the cluster files. Double counting was removed by hand in this report.

**Disagreements left open.**
- Whether the tap lag is a choice or intrinsic. This report calls it a choice (the formula lives in the source repository) amplified by intrinsic exact-revision consumers.
- Whether a complete release set per Core version is a goal of the split. That decides whether #9762 is an improvement or a regression.
- Why the OSWFile warning failed only the Homebrew macos-x64 layout.
- Whether the Windows libmamba package-cache failure comes from `LongPathsEnabled=0`.
- Whether fork PRs to public consumers actually work without secrets.

**Not assessed.** Scientific correctness. The split's fix campaign found real defects, for example the sqMass chromatogram and spectrum settings loss (`docs/cpp-issues-review.md:83-88`). That is a separate question from maintenance cost.