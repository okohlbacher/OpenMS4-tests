# Upstream patch offers (refreshed 2026-09-27, develop a2bfec75a1)

Six branches carry the remaining P0 fixes of the first offer onto current upstream OpenMS `develop`. Nothing is pushed and no pull request exists. What to send, and when, is your decision.

- **Nothing pushed.** On 2026-09-27 GitHub had no branch starting with `p0` on OpenMS/OpenMS or on okohlbacher/OpenMS. The dax clone's push URL is the guard value `DISABLED-phase4-no-push`. To undo it: `git -C /scratch/kohlbach/openms-upstream-p0 config --unset remote.origin.pushurl`.
- **Branches:** `p0v2/<area>` in the clone `/scratch/kohlbach/openms-upstream-p0` on dax. Worktrees are in `/scratch/kohlbach/openms-upstream-p0-wt/v2/<area>`, and build dirs and logs in `/scratch/kohlbach/openms-upstream-p0-wt/v2/<area>-build/`.
- **Patch series:** `/scratch/kohlbach/openms-upstream-p0-wt/v2/patches/<area>/` (`git format-patch` output). Apply them with `git am --keep-non-patch` (or `-k`). Plain `git am` strips "[FIX]" or "[TEST]" from the subject.
- **Base:** develop a2bfec75a1, "[FIX] FileConverter: read Thermo .raw in-process by default on Linux and macOS (#10274)" (2026-09-27 08:34 +0200). All branches were built and tested on it.
- **Newest develop checked:** develop was fetched again at 12:10 UTC and was still a2bfec75a1, so it is 0 commits past the base. Every commit of every branch applies in order, and no touched file has drifted. The record is `/scratch/kohlbach/openms-upstream-p0-wt/v2/final-recheck.txt`. develop moves daily, so re-run `v2/bin/applycheck.sh origin/develop <commits>` after a fetch before you send anything.
- **First offer:** `p0/<area>` on 3befd8ed77, described in `docs/reviews/2026-09-14-p0-upstream-patch-sets.md`. Tracking issue #10148 lists these branches as "prepared in the fork". The `p0/*` branches and their worktrees are unchanged.

## Overview

| Branch | Head | Commits | Findings | Tests | Each commit's test fails without its fix | Applies to newest develop | Dropped since the first offer |
|---|---|---|---|---|---|---|---|
| p0v2/mzdata-mzxml | e25b6955b4 | 2 | CPP-170, CPP-171, CPP-173 | 8/8 | yes | yes | none |
| p0v2/mzml-sqmass | ed70cdc834 | 4 | CPP-120 (2 commits), CPP-191, CPP-199 | 11/11 | yes | yes | none |
| p0v2/algorithms | f48678e573 | 2 | CPP-005, CPP-011 | 6/6 | yes (CPP-005 only through ctest's glibc malloc check) | yes | none |
| p0v2/mascot-mzidentml | 69a3e7fe05 | 3 | CPP-164, CPP-169, plus a test fix | 2/2 | yes for both fixes (they crash); the ABORT_IF commit is test-only, so there is no control | yes | CPP-168 (landed as #10154) |
| p0v2/mgf-mztab | 92456efd86 | 2 | CPP-148 | 7/7 | yes | yes | CPP-166 (landed as #10151) |
| p0v2/base64-design | 6a8141d089 | 2 | CPP-055, plus the missing-sample error | 12/12 | yes | yes | CPP-059 (#10152 took the opposite policy) |

"Tests" counts the area's class tests. They ran twice at each head on dax, and all passed both times. Evidence columns below use these terms:
- **NEG** is the commit's tests built against its parent's library sources. It must fail.
- **POS** is all area tests at the commit.
- **capped** is a run under the hosted-runner memory cap.

## p0v2/mzdata-mzxml (head e25b6955b4)

| Commit | Subject | Finding | Severity | Upstream | Evidence |
|---|---|---|---|---|---|
| cfe04586cc | [FIX] mzData reader: array bounds and MSn scan mode (CPP-170, CPP-171) | CPP-170, CPP-171 | P0 | not upstream | NEG fails lines 879, 884 and 885, then a SegFault in the next section. POS 8/8 |
| e25b6955b4 | [FIX] mzXML reader: out-of-bounds read on short peaks payload (CPP-173) | CPP-173 | P0 | not upstream | NEG fails lines 743, 746 and 747. POS 8/8. Capped MzXMLFile_test: NEG rc 1, POS rc 0, head rc 0 |

- **Changed since the first offer:**
  - Rebased over 94 develop commits with no conflict. None of the six touched files changed upstream.
  - The code is identical except for one MzXMLFile_test comment, which now reads "an MS2 scan with <precursorMz> before <peaks> is checked like any other scan".
  - The subjects carry the CPP ids.
  - Two overclaims in the mzData message are fixed: "(and no supplemental array)" is added, and "next to a complete spectrum" now names only the cases it covers.
- **Behaviour changes:**
  - Valid files load as before, with one exception: the mzData ScanModes that OpenMS writes for ABSORPTION, EMC and TDF now load back.
  - Corrupt mzData: unpaired, missing or `<data>`-less arrays load without peaks, and a short intensity array limits the peaks. A negative spectrumList count no longer reserves billions of spectra.
  - Corrupt mzXML: a peaksCount above the decoded payload loads the decoded pairs and logs one new OPENMS_LOG_WARN per scan. Out-of-range counts no longer wrap, and the reserves are clamped to [0, 1e5]. A non-integer peaksCount still throws a ParseError, which now names the scan.
- **Independence:** each commit applies alone to develop, so this can be one PR or two.
- **Notes for sending:** use each commit subject as the PR title, and end the body with "Tracked in #10148.". Draft CHANGELOG lines:
  - `MzDataFile: a spectrum with a missing, short or <data>-less binary array, or a <data> element outside an array, is no longer read past its arrays; it loads without peaks, and a negative spectrumList count no longer requests billions of spectra. The ScanModes written for ABSORPTION, EMC and TDF load back, and the MSn fallback applies to the spectrum being read, not the previous one (#10148).`
  - `MzXMLFile: a scan whose peaksCount exceeds its decoded <peaks> payload is no longer read past the payload; the decoded pairs are loaded with one warning per scan, and negative or out-of-range counts no longer wrap or drive unbounded reserves (#10148).`
- **Open points:**
  - The scan numbers in MzXMLFile_test have gaps (27, 42, 43, 30, …) and were not renumbered.
  - The mzData "array missing" message stays at debug level, as you decided on 2026-09-14.
  - The c2 negative control stops at an ABORT_IF before the peaksCount="-1" case. The reserve clamp is therefore shown only by the capped runs passing.

## p0v2/mzml-sqmass (head ed70cdc834)

| Commit | Subject | Finding | Severity | Upstream | Evidence |
|---|---|---|---|---|---|
| 2f2eae2e4e | [FIX] MzMLHandler: use list counts only as a capacity hint (CPP-120) | CPP-120 | P0 | not upstream | NEG fails lines 1669-1671, 1685-1687 and 1701-1703. POS 11/11. Capped: NEG rc 1 (OutOfMemory), POS rc 0 |
| 07657baf15 | [FIX] MzMLHandlerHelper: bound numpress arrays by decoded size (CPP-120) | CPP-120 | P0 | not upstream | NEG fails lines 1757, 1765, 1782, 1828, 1833, 1834, 1838, 1842 and 1843. POS 11/11. Capped: NEG rc 1, POS rc 0 |
| 0784a8417e | [FIX] sqMass reader: reject unequal or duplicate data arrays (CPP-191) | CPP-191 | P0 | not upstream | NEG fails lines 848, 859, 870, 897, 907, 942, 944, 957, 959 and 1032. POS 11/11 |
| ed70cdc834 | [FIX] sqMass reader: ignore activation codes outside the enum (CPP-199) | CPP-199 | P0 | not upstream. Third-party #10160 was closed by the maintainer | NEG fails lines 1121, 1122, 1124, 1125, 1131, 1132, 1134 and 1135. POS 11/11 |

The capped MzMLFile_test passes at the head (rc 0).

- **Changed since the first offer:**
  - Rebased over 94 develop commits.
  - Commit 1 conflicted with #8691 (psi-ms.obo 4.2.2) in MzMLHandler.cpp. Both add a helper at the same spot. The resolution keeps develop's `legacy_analyzer_type_param` and `hasLegacyAnalyzerType()` complete and adds `capacityHint_()` after them. range-diff shows that only context lines differ.
  - The code is otherwise identical, except for one CPP-191 test comment, which now ends "the RUN_EXTRA cases below also insert a RUN_EXTRA row".
  - Subjects carry the CPP ids, and bodies end with "Tracked in #10148.".
- **Behaviour changes:**
  - CPP-120: a list count of 0 or less reserves nothing. Reservations are capped at 65536 spectra or chromatograms and 16 arrays per record, and a negative or huge count no longer throws std::length_error. A numpress array shorter than its declared length gets the decoded size and a warning.
  - CPP-191 rejects input that develop accepted. A sqMass record whose arrays differ in length, repeat a role, or lack the intensity or m/z/RT role now throws Exception::IllegalArgument. Before, it was read past its end, truncated, or loaded with zero intensities.
  - CPP-199: an activation code outside the enum, read as 64 bits, loads without an activation method. No exception is added.
  - Files written by OpenMS read as before.
- **Independence:** commits 1, 3 and 4 each apply alone. Commit 2 needs commit 1's test include and helper, so send CPP-120 as one PR of two commits.
- **CPP-199 flag:** the maintainer closed #10160 (the same sqMass mechanism, narrower) on 2026-09-18 with "thanks but this can not happen".
  - About six hours before, he had asked for `sqlite3_column_int64()` and a helper, and written "No test needed for this one".
  - This commit does the 64-bit read. It also adds a 98-line test, and it repeats the range check at two sites instead of using a helper.
  - Send it only with the truncation argument: 4294967294 is read as -2, and 4294967297 as a valid method. His own comment made the same point ("2^32 + 5 becomes 5").
  - It is the last commit and applies alone, so it can be sent, held back or dropped.
- **Notes for sending:** use each commit subject as the PR title, and end the body with "Tracked in #10148.". Draft CHANGELOG lines:
  - `mzML reader: the count attributes of spectrumList, chromatogramList and binaryDataArrayList are only a capacity hint; a negative or huge count no longer throws std::length_error or reserves memory before any element is read (#10148)`
  - `mzML reader: numpress-compressed data arrays are bounded by their decoded length like other arrays; a shorter array is no longer read past its end and logs a warning (#10148)`
  - `sqMass reader: spectra and chromatograms whose data arrays differ in length, repeat a role or lack one are rejected with Exception::IllegalArgument instead of being read past their end, truncated or loaded with zero intensities (#10148)`
  - `sqMass reader: activation method codes outside the enum (negative, or 64-bit values that a 32-bit read truncated) are ignored instead of yielding an invalid activation method (#10148)`
- **Open points:**
  - Test size: MzMLFile_test +227 lines, MzMLSqliteHandler_test +469 lines.
  - The RUN_EXTRA "unaltered" case still uses the shared peak values. This is optional and was not changed.
  - Issues outside the findings, not fixed: the count=-1 sentinel; a statement leak on a rejected read; the missing-role message gives an index, not the native id; invalid activation codes are dropped silently; unguarded users of the activation-name tables; an uninitialised `sql_batch_size_`; no ORDER BY (CPP-192).

## p0v2/algorithms (head f48678e573)

| Commit | Subject | Finding | Severity | Upstream | Evidence |
|---|---|---|---|---|---|
| c9f60593eb | [FIX] Stop isotope accumulation at the truncated result length (CPP-005) | CPP-005 | P0 | not upstream | NEG: "free(): invalid pointer" and Subprocess aborted, under ctest's glibc malloc check. POS 6/6 |
| f48678e573 | [FIX] Reset MassTraceDetection float data array state per run (CPP-011) | CPP-011 | P0 | not upstream | NEG fails lines 217-219, 222 and 225-232, then SEGFAULT. POS 6/6 |

- **Changed since the first offer:**
  - Rebased with no conflict. The code is identical: the patch-ids equal the first offer's.
  - The test CMakeLists hunk is now at line 363 (+19). The MassTraceDetection_test hunk moved 2 lines after #10225.
  - Messages: subjects carry the CPP ids, and bodies end with "Tracked in #10148.". The CPP-011 overclaim is fixed: the message now says every run "that reaches detection" starts fresh, and it names the two early exits.
- **Behaviour changes:** none for valid input. The out-of-bounds heap write is gone, and so is the stale state of a reused detector.
- **Independence:** each commit applies alone.
- **Notes for sending:** use each commit subject as the PR title, and end the body with "Tracked in #10148.". Draft CHANGELOG lines (3.6.0 "Robustness:"):
  - `CoarseIsotopePatternGenerator with a nonzero max_isotope wrote past the end of its result when a fragment distribution was longer than max_isotope, corrupting the heap; the accumulation now stops at the truncated length, and returned values do not change (#10148).`
  - `MassTraceDetection kept the float data array flags and indices of its previous run, so a reused detector read the wrong array or crashed; every run that reaches detection now starts from the state of a fresh detector (#10148).`
- **Open points:**
  - The CPP-005 test sees the old write only through glibc's malloc check under ctest, which the CMake hunk sets. The bare binary and non-glibc platforms do not see it.
  - Open PRs #10290 (MassTraceDetection.cpp) and #9720 (CoarseIsotopePatternGenerator.cpp and its test) touch other regions of the same files. A merge with them was not tested.
  - Issues outside the findings, not fixed:
    - the broken release-flag restore in class_tests/openms/CMakeLists.txt:363
    - `*std::max_element` on a possibly empty set, at CoarseIsotopePatternGenerator.cpp:199 and :286 and EmpiricalFormula.cpp:205

## p0v2/mascot-mzidentml (head 69a3e7fe05)

| Commit | Subject | Finding | Severity | Upstream | Evidence |
|---|---|---|---|---|---|
| 049be2b99a | [FIX] MascotXMLHandler: check query numbers before indexing (CPP-164) | CPP-164 | P0 | not upstream. Third-party #10163 was closed unmerged by its author on 2026-09-17 | NEG: SIGSEGV in the new section; the backtrace runs onEndElement → insertHit. POS 2/2 |
| 99d7739edd | [TEST] MzIdentMLFile_test: call ABORT_IF outside of a loop | none | test-only | not upstream | no control, since there is no library change. POS 2/2 |
| 69a3e7fe05 | [FIX] MzIdentMLDOMHandler: check substitution locations (CPP-169) | CPP-169 | P0 | not upstream | NEG: SIGSEGV in the new section; the backtrace runs parsePeptideSiblings_ → AASequence::fromString. POS 2/2 |

- **Dropped:** 64498dce6a (CPP-168) landed as #10154 (37057b2d53) with the same code change: getTextContent(), a trim before the substitutions, and a ParseError when the sequence is empty. Only the ParseError's expression argument differs, and the fixture path collides. Evidence: `/scratch/kohlbach/openms-upstream-p0-wt/v2/mascot-mzidentml-build/dropped-64498dce6a.txt`.
- **Changed since the first offer:**
  - Rebased over #10154 and #8691.
  - The ABORT_IF commit's include block was re-resolved: `<algorithm>` now sits before develop's `<set>`.
  - The CPP-169 test section now sits after upstream's "store and load a PeptideHit with an empty sequence".
  - Four new doc parameters in MascotXMLHandler.h use `@param[in]`, as upstream AGENTS.md requires.
  - Subjects carry the CPP ids, and both CPP commits end with "Tracked in #10148.".
- **Behaviour changes:**
  - CPP-164: a query number of 0 or above `<NumQueries>`, or a peptide in an export without `<NumQueries>`, now raises a ParseError. Before, the reader indexed past the identification list.
  - CPP-164: stray pep_*, StringTitle and RTINSECONDS elements, and a repeated NumQueries, are now ignored with a warning. Before, they silently changed an identification.
  - CPP-169: a substitution location outside 1..length, or a missing replacementResidue, is now logged, and the Peptide is stored with an empty sequence. Before, this was an out-of-bounds write.
- **Independence:** each commit applies alone. Commit 3's test uses `std::all_of`, and the explicit `<algorithm>` include is in commit 2. Commit 3 compiles alone only through a transitive include, so send commits 2 and 3 together, or add the include to commit 3.
- **Notes for sending:** use each commit subject as the PR title, and end the body with "Tracked in #10148." (not for the test commit). Draft CHANGELOG lines:
  - `MascotXMLFile: query numbers are checked against NumQueries before they are used as indices; a number of 0 or above NumQueries, or a peptide in an export without header, raises a ParseError instead of reading or writing past the identification list, and pep_*, StringTitle and RTINSECONDS elements outside their element are ignored with a warning (#10148).`
  - `MzIdentMLFile: a SubstitutionModification whose location is outside the PeptideSequence, or that has no replacementResidue, no longer writes outside the sequence string; the Peptide is reported as unreadable and stored with an empty sequence (#10148).`
- **Open points:**
  - The negative controls crash, so they have no failing line numbers. Cite the section names and backtraces instead (`v2/mascot-mzidentml-build/logs/negbt/NOTE.txt`).
  - IDFileConverter TOPP tests were not run.
  - Issues outside the findings, not fixed:
    - the missing-replacementResidue test does not tell old and new code apart
    - no test combines a padded sequence with a substitution
    - originalResidue is not compared
    - the writer emits an empty `<PeptideSequence>`
    - Xerces truncates huge query numbers

## p0v2/mgf-mztab (head 92456efd86)

| Commit | Subject | Finding | Severity | Upstream | Evidence |
|---|---|---|---|---|---|
| 2916a1e06c | [FIX] Read mzTab column-unit metadata, and write it with a tab (CPP-148) | CPP-148 | P0 | not upstream | NEG: the section aborts with ConversionError "Could not convert string 'colunit' to an integer value". POS 7/7 |
| 92456efd86 | [FIX] Check mzTab metadata keys before reading them (CPP-148) | CPP-148 | P0 | not upstream | NEG: SegFault on the empty key, where develop reads past an empty vector. POS 7/7. The first-offer reader fails the new warning section (lines 317, 318, 323 ×10 and 332) |

- **Dropped:** 925833510a (CPP-166) landed as #10151 (975b6509fb) with the same code statements, and upstream added more tests. Evidence: `/scratch/kohlbach/openms-upstream-p0-wt/v2/mgf-mztab-build/dropped-925833510a.txt`.
- **Folded in:** the mzTab hunks of Core's own correction of this patch (add998c, db05058 and 8484713).
  - Why: the first offer's key check rejected keys that develop ignores (`instrument-name`, `software[1]-setting`, an empty field). Loads that develop completes therefore failed.
  - Now: such keys are ignored with a warning, and a malformed index is still a ParseError.
  - The Core references in the comments were removed.
- **Changed since the first offer:**
  - Rebased with no conflict.
  - Comment overclaims fixed: `ms_run[n]-hash` is "accepted but not stored", and the whitespace grouping comment and its section title were corrected.
  - Message 2 was rewritten to match the final code. The first-offer message was wrong about `contact-name`.
- **Behaviour changes** (compared with develop; a per-key probe was run against both libraries):
  - Files with column units now load. Develop threw a ConversionError.
  - An empty key is a ParseError. Develop crashed on it.
  - A malformed index is a ParseError that names the key.
  - Newly rejected: a whitespace-only key, `instrument[1-name`, and a malformed `ms_run[n]-hash` index.
  - Keys with extra fields are ignored. Develop read them as the shorter key.
  - Keys with a missing index or an empty field are ignored with a warning. Develop ignored them silently, except `contact-name`, `-affiliation` and `-email`, which failed and now load.
  - None of the 46 mzTab test files in develop has a newly rejected key.
- **Independence:** commit 2 needs commit 1, so send them together.
- **Notes for sending:** use each commit subject as the PR title, and end the body with "Tracked in #10148.". Draft CHANGELOG lines:
  - `The mzTab reader (MzTabFile) loads files with column-unit metadata (colunit-protein, colunit-peptide, colunit-PSM, colunit-small_molecule), which failed with a ConversionError, and the writer puts a tab between a colunit key and its value (#10148).`
  - `The mzTab reader (MzTabFile) checks the form of every metadata key before reading it: an empty key or a malformed index is a ParseError naming the key, a key that lacks an index or has an empty field is ignored with a warning, and a key with extra fields is no longer read as the shorter mzTab 1.0 key (#10148).`
- **Open points:**
  - Message 1 keeps the first-offer body verbatim. Three of its lines are wider than 72 columns (80, 73 and 74; one is a quoted MTD example).
  - The writer still spells `colunit-PSM` in upper case. That was fixed later in Core and is deferred.
  - The mzTab-M colunit keys were not covered, and neither were TOPP tests.

## p0v2/base64-design (head 6a8141d089)

| Commit | Subject | Finding | Severity | Upstream | Evidence |
|---|---|---|---|---|---|
| cc5f0a21df | [FIX,TEST] Validate Base64 input in the numeric decoders (CPP-055) | CPP-055 | P0 | not upstream | NEG fails lines 403, 431-434, 443, 447, 475 and 528 ("no exception thrown!"). POS 12/12 |
| 6a8141d089 | [FIX,TEST] Name a design sample missing from the sample table | none | P2 | not upstream | NEG fails lines 162, 169, 179 and 189 (std::out_of_range "map::at"). POS 12/12 |

- **Dropped:** d3ccbb6228 (CPP-059, which padded short rows). Upstream #10152 (033123d26e) rejects wrong-width rows instead. This is a deliberate difference, not an offer item. Evidence: `/scratch/kohlbach/openms-upstream-p0-wt/v2/base64-design-build/dropped-d3ccbb6228.txt`.
- **Changed since the first offer:**
  - c1: the code is unchanged.
    - The '=' docs are corrected at two Base64.h sites, and the test comment now reads "'|', two above 'z'".
    - The message has a new subject with the CPP id, a rewritten '=' bullet, a new bullet for 1-3 characters plus whitespace (example `" A   "`) and "Tracked in #10148.".
  - c2 is hand-ported onto develop's reworked ExperimentalDesignFile (#10152).
    - The code, the ExperimentalDesign.h rule and the 52-line test are byte-identical to the first offer.
    - Only the ExperimentalDesignFile.h doc clause moved onto develop's wording.
    - The message is unchanged.
- **Behaviour changes:**
  - Corrupt numeric Base64 now throws ConversionError from all four decoders. This covers a byte outside the alphabet, data after '=', more than two '=', and a bare length that is not a multiple of 4. Before, such input gave wrong values, or the integer decoder read outside its table.
  - Wrapped Base64 is accepted, because whitespace is skipped.
  - A two-table design whose file section names a missing Sample throws a ParseError that names it. Before, it threw std::out_of_range.
  - Cost: about 0.09 s of a 5.86 s median MzMLFile::load (1.6%, 1.77 GB mzML, GCC 14 -O3). MSVC was not measured.
- **Independence:** each commit applies alone.
- **Notes for sending:** use each commit subject as the PR title. Only c1 ends with "Tracked in #10148.", because c2 has no CPP id. Draft CHANGELOG lines:
  - `Base64::decode()/decodeIntegers() check their input: a byte outside the Base64 alphabet, data after '=', more than two '=' or a length that is not a multiple of 4 throw ConversionError instead of decoding to wrong values or reading outside the lookup table; ASCII whitespace (line-wrapped xs:base64Binary) is skipped (#10148).`
  - `ExperimentalDesignFile throws a ParseError naming the sample when the file section of a two-table design uses a Sample that the sample section does not define, instead of a bare std::out_of_range ("map::at") (#10148).`
- **Open points:**
  - c2's test designs keep their rows at header width, so that #10152's check does not fire first. You may want to mention the CPP-059 policy difference when sending c2.
  - Eight unchanged first-offer message lines are 73 columns wide.

## Decisions to confirm (provisional defaults; you can overturn them)

1. **Naming.** The new branches are called `p0v2/<area>`. The `p0/*` branches stay as the first-offer record, unchanged.
2. **CPP-199 is kept** as the separate last commit of p0v2/mzml-sqmass, although the maintainer closed #10160 with "thanks but this can not happen". The argument to send with it is the truncation examples (4294967294 read as -2, 4294967297 as a valid method). Alternatively, hold it back or drop it; commits 1-3 do not depend on it.
3. **mzTab fold-in.** Core's correction (add998c, db05058, 8484713; mzTab hunks only) is folded into the second CPP-148 commit. It corrects the offered patch, which without it fails loads that develop completes. It is not a new finding.
4. **Two commits without a CPP id are kept:** 99d7739edd (the ABORT_IF test fix, test-only) and 6a8141d089 (the missing-sample ParseError, P2). Both apply alone and can be left out.
5. **Message conventions.**
   - Titles end in "(CPP-xxx)", and CPP commits end with "Tracked in #10148.", as in the maintainer's own merges.
   - The first offer's minor review points are fixed in comments and messages only. No test logic changed; one mzTab test section title was reworded.
6. **No CHANGELOG commits.** Draft lines are given per branch instead, and you or the maintainer add them with the PR number.
7. **The Claude co-author trailer is kept.**
   - The policy is KEEP: every ported commit keeps its one existing line `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`. That is 15 of 15 patches, with no second trailer and no Claude-Session line.
   - develop has 3119 `Co-authored-by: Claude` lines in the messages of commits since 2026-01-01, and 823 first-parent commits carry one.
   - The maintainer's own CPP merges #10151, #10152 and #10154 carry `Co-authored-by: Claude <noreply@anthropic.com>`.
   - You can strip or rename the line before sending. That changes the message only.
8. **Test size.** On #10160 the maintainer objected to "a lot of bloat in the test for something that might never happen". Test lines added per branch:

   | Branch | Test lines added |
   |---|---|
   | mzdata-mzxml | 418 |
   | mzml-sqmass | 696 (MzMLSqliteHandler_test 469, of which 98 are CPP-199's) |
   | algorithms | 151, plus 35 CMake lines |
   | mascot-mzidentml | 480, plus a 166-line .mzid fixture |
   | mgf-mztab | 413 |
   | base64-design | 290 |

   Trimming before sending is your call.

## Not in this offer

- **p0/kernel** landed in full through #10153 (CPP-113), #10155 (CPP-111) and #10156 (CPP-089, 090 and 091). Its extra [DOC,TEST] commit was not re-checked.
- **CPP-166 (#10151), CPP-168 (#10154) and CPP-059 (#10152)** have landed upstream. CPP-059 differs on purpose: upstream rejects wrong-width rows, while the first offer padded them. It is not an offer item.
- **Fixes made after the first list** (Core ci.6 to ci.11) are deferred. The only exception is the mzTab fold-in, which corrects the offered CPP-148 patch itself.
- **Optional items not done:**
  - distinct values for the sqMass RUN_EXTRA "unaltered" test
  - renumbering the mzXML test scan numbers
  - raising the mzData "array missing" message level

## Evidence and limits

- **Setup.** All builds and tests ran on dax (Linux x86-64, glibc), in the conda env core-ci (CMake 3.31.8, GCC 14.4.0) with Ninja. Logs are in `/scratch/kohlbach/openms-upstream-p0-wt/v2/<area>-build/logs/`.
- **Tests.** Only the area class tests ran: 46 tests over the six branches, and develop's baseline passed all of them. Not run:
  - TOPP tests
  - the full class-test suite
  - macOS, clang, arm64, MSVC and AddressSanitizer
- **Per-commit controls.** Each commit's tests were run against its parent's library sources (NEG, must fail) and at the commit (POS, all area tests). The results are in `v2/<area>-build/logs/percommit/summary.txt`.
- **Capped runs.** MzMLFile_test (CPP-120) and MzXMLFile_test (CPP-173) also ran with `ulimit -v 12000000` and `OMP_NUM_THREADS=4`, as on hosted runners. Both pass at every commit and at each head.
- **Warnings.** Each branch adds 0 new compiler warnings compared with develop's baseline build.
- **Exports.** The patch-ids of the 15 exported patches equal those of the branch commits. A scan of the exports for internal paths, Core release names and token patterns gives 0 hits.
- clang-format: not run (no clang-format on dax; not copied to the Mac)
- **doxygen: not run.** It is optional, and dax has none. Since the first offer, the headers changed only in comments and `@param` direction tags.
- **Core evidence, not upstream evidence.** The Core counterparts of these fixes shipped in core-v4.0.0-ci.6, and its installed console suite passed 2047/2047.
- **Authorship.** Commits keep their author (Oliver) and the first-offer author dates. The committer is the dax identity, and `git format-patch` uses the author.
- **Your upstream tree on the Mac was only read.** HEAD, branch, stash count, the HEAD reflog entry, origin/develop and the FETCH_HEAD mtime are identical before (11:28 UTC) and after (12:11 UTC) this refresh. No checkout, fetch, reset or stash happened there.
