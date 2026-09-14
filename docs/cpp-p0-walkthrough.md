# P0 C++ findings: walkthrough and decisions

Each entry explains one priority-0 finding from the Rust port's C++ defect list, shows the OpenMS4 Core fix as a diff taken directly from git, and records a skeptic's check of the explanation and the fix. Upstream means OpenMS `origin/develop`; Core diffs run from `core-v4.0.0-ci.2` (before the review fixes) to `4f5c86f` (`core-v4.0.0-ci.4`), except where a fix was reverted.

| Finding | Title | Ranking check | Real upstream | P0 holds | Fix complete |
| --- | --- | --- | --- | --- | --- |
| [CPP-089](#cpp-089) | BaseFeature::sortPeptideIdentifications comparator is not a strict weak ordering | unverified | yes | yes | yes |
| [CPP-170](#cpp-170) | mzData checks missing and short arrays after unsafe indexing | unverified | yes | yes | yes |
| [CPP-171](#cpp-171) | mzData writer emits scan modes its reader does not recognize | unverified | yes | yes | yes |
| [CPP-173](#cpp-173) | mzXML release decode reads beyond short peak payload | unverified | yes | yes | yes |
| [CPP-005](#cpp-005) | Truncated fragment distribution is indexed at full input length | unverified | yes | yes | yes |
| [CPP-011](#cpp-011) | Mass trace detection reuses stale metadata-array state | unverified | yes | yes | yes |
| [CPP-055](#cpp-055) | Base64 SIMD decoding does not validate its alphabet | upheld | yes | yes | yes |
| [CPP-059](#cpp-059) | Short experimental-design rows are read past the end of the row vector | upheld | yes | yes | yes |
| [CPP-111](#cpp-111) | MapConversion::convert(PeakMap) sorts and indexes past the end of its vector | upheld | yes | yes | yes |
| [CPP-113](#cpp-113) | ConsensusMap::split indexes its result vector with the map index | upheld | yes | yes | yes |
| [CPP-120](#cpp-120) | mzML list `count` attribute drives an unvalidated container reserve (the same fix closed a numpress declared-length out-of-bounds read) | unverified | yes | yes | yes |
| [CPP-148](#cpp-148) | MzTab column-unit metadata parses its key as an index | unverified | yes | yes | yes |
| [CPP-164](#cpp-164) | Mascot query index guard accepts one-past-end | unverified | yes | yes | partly |
| [CPP-168](#cpp-168) | mzIdentML reader dereferences missing PeptideSequence child | unverified | yes | yes | yes |
| [CPP-169](#cpp-169) | mzIdentML substitution position is used as unchecked string index | unverified | yes | yes | yes |
| [CPP-191](#cpp-191) | Array hydration lacks pair length and role validation | unverified | yes | yes | yes |
| [CPP-199](#cpp-199) | Metadata readers accept invalid negative activation enum values below -1 | unverified | yes | yes | yes |
| [CPP-166](#cpp-166) | Mascot MGF loader carries precursor and RT fields between blocks | unverified | yes | yes | yes |
| [CPP-042](#cpp-042) | XLMS linear suffix losses divide the mass by charge twice | upheld | yes | yes | yes |

## Implementation status (14 September 2026)

- **OpenMS4 Core.** Each area has a branch `codex/p0-<area>` on dax that went through three implement-and-review rounds; all seven are marked ready. They merge without conflicts into `codex/p0-followups` (48 commits, 30 files), which is pushed to OpenMS4-core for CI. On dax its 15 changed class tests and 17 neighbouring ones pass (32 of 32). CPP-042 is not included; it is re-landed in a later cycle.
- **Upstream OpenMS.** One patch branch per area, `p0/<area>` in `/scratch/kohlbach/openms-upstream-p0` on dax (series under `/scratch/kohlbach/openms-upstream-p0-wt/patches/<area>`), built and tested against `develop` 3befd8ed77, where every touched file matched `core-v4.0.0-ci.2`. Nothing is pushed.
- **Measured.** Decoding the arrays of a 1.77 GB uncompressed mzML takes 0.35 s with the ci.2 decoder, 1.57 s with the released CPP-055 check (ci.3 to ci.5, about 23% of that file's 5.3 s load) and 0.45 s with the reworked check.

<a id="cpp-089"></a>
## CPP-089: BaseFeature::sortPeptideIdentifications comparator is not a strict weak ordering

**BaseFeature::sortPeptideIdentifications reads the first hit of an identification that has no hits, and its comparator is not a valid ordering, so sorting a feature's identifications can crash.**

- **Mechanism:** origin/develop src/openms/source/KERNEL/BaseFeature.cpp:125-143 (byte-identical to core-v4.0.0-ci.2, blob e303b92). The std::sort lambda guards with `if (p1.empty()) return true;` (:128-131) and `if (p2.empty()) return false;` (:132-135), then reads `p1.getHits()[0].getScore()` and `p2.getHits()[0].getScore()` (:138, :142). PeptideIdentification::empty() (PeptideIdentification.cpp:210-217) is true only when the identifier, hits, significance threshold and score type are all empty and higher_score_better is true. An identification that carries an identifier or score type but no hits therefore passes both guards, and the comparator indexes element 0 of an empty std::vector. This is undefined behaviour: a null-pointer read when the vector never allocated, a stale read when it did. Separately, two fully default identifications give comp(a,b) == comp(b,a) == true, which breaks the asymmetry std::sort requires (also undefined behaviour). FeatureXMLHandler.cpp:819-822 pushes the parsed PeptideIdentification onto the feature whether or not it had PeptideHit children, and the element always carries identification_run_ref and score_type, so empty() is false for such an element.
- **Trigger:** featureXML containing a feature with two or more <PeptideIdentification> elements, one of them with identification_run_ref/score_type attributes but no <PeptideHit> children, run through FeatureLinkerUnlabeledQT with -algorithm:use_identifications true (QTClusterFinder.cpp:99-106 copies each feature with IDs and calls sortPeptideIdentifications). Direct API case: BaseFeature f; auto& ids = f.getPeptideIdentifications(); ids.resize(2); ids[0].insertHit(PeptideHit(...)); ids[1].setIdentifier("x"); f.sortPeptideIdentifications(); the comparator then evaluates ids[1].getHits()[0].
- **Consequence:** An out-of-bounds or null read inside std::sort. A hit-less identification loaded from a file has never allocated hit storage, so this normally ends in a segmentation fault in the linker. If hits were cleared at runtime, capacity remains and the read returns stale memory, which silently mis-orders the identifications; downstream code takes pepIDs[0] as the best hit (QTClusterFinder.cpp:107-115). The two-empty-identifications case is undefined behaviour, but with a handful of elements the practical effect is usually an arbitrary order rather than a crash.
- **Who hits it:** Low in practice. Reachable only through C++ code paths, not pyOpenMS (BaseFeature::sortPeptideIdentifications is not bound; only ConsensusMap::sortPeptideIdentificationsByMapIndex is). There are two callers: QTClusterFinder (FeatureLinkerUnlabeledQT, with use_identifications, default false, QTClusterFinder.cpp:34) and PipEcho prepare_feature (PIPECHO/Impl.cpp:68-77, run on every feature of every map at :495-503), which ProteomicsLFQ uses only with -pip_echo true (default false, ProteomicsLFQ.cpp:325, :707). The usual producers of annotated features avoid the trigger: IDMapper skips hit-less identifications (IDMapper.cpp:339, :436), and IDFilter calls removeEmptyIdentifications (IDFilter.cpp:817). The trigger therefore needs a featureXML produced or filtered by other means (hand-made, third-party, or a pipeline that strips hits without removing the identification). The input is valid, and the defect is memory-unsafe when it fires, but few users will hit it.

> **Skeptic's correction:** (1) Reach cites IDMapper.cpp:339 and :436 as the reason annotated features avoid hit-less IDs. Both lines are in IDMapper::annotate(ConsensusMap&), which starts at :285. The featureXML path is annotate(FeatureMap&) at :685, and its skip is at :793 (`if (id_it.getHits().empty()) continue;`). (2) "IDFilter calls removeEmptyIdentifications (IDFilter.cpp:817)" refers to the TOPP tool src/topp/IDFilter.cpp. That tool accepts only idXML, consensusXML, idparquet and consensusparquet (:125) and never filters featureXML, so it only cleans idXML before mapping. (3) The caller list is incomplete. ProteomicsLFQ reaches QTClusterFinder on its default path (no pip_echo): it sets Linking use_identifications=true (ProteomicsLFQ.cpp:399) and runs FeatureGroupingAlgorithmQT (:723-730). So the sort runs on every ID-carrying feature in a default ProteomicsLFQ run, not only with -pip_echo true. Those features come from FeatureFinderIdentification, whose addPeptideToMap_ drops hit-less IDs (FeatureFinderIdentificationAlgorithm.cpp:1611). The trigger is therefore still not reached there, and "Low" reach stands. (4) FeatureLinkerUnlabeledQT also accepts consensusXML (FeatureLinkerBase.cpp:69), and QTClusterFinder::run_<ConsensusMap> sorts ConsensusFeature copies the same way, so a consensusXML with a hit-less identification is a second file route. ProteomicsLFQ's own -out_cxml is not such a file: IDConflictResolverAlgorithm::resolve at :2648 leaves one identification per consensus feature.

### The fix

181dadf rewrites the function (4f5c86f BaseFeature.cpp:123-167). The CPP-089 part is the comparator: it keys on `p1.getHits().empty()` and returns `!p2.getHits().empty()` (:151-154), then returns false when `p2.getHits().empty()` (:155-158). Hit presence is now the guard, so getHits()[0] is only evaluated when both operands have hits, and two hit-less identifications compare as equivalent, which restores strict weak ordering. In the same hunk, two neighbouring findings are fixed: CPP-090 moves hit sorting into a separate pass (:125-131) and makes the comparator take const references (:147), and CPP-091 reads the score orientation once, from the first identification with hits (:132-145, :159), instead of from the left operand. b6dd412 changes the class test (BaseFeature_test.cpp:428-436): ids[2] gets an identifier, a score type and higher_score_better=false but no hits. With the pre-fix comparator this makes every comparison involving ids[2] index an empty vector. The test now asserts the sort completes, the best hit is 0.9, and the hit-less identification keeps its identifier. The failure of this test against the pre-fix code was not demonstrated by an actual run here.

*State:* Released in 4f5c86f (core-v4.0.0-ci.4). Fix committed in 181dadf, regression test in b6dd412; both are ancestors of 4f5c86f and neither was touched by the ci.4 reverts in 23944b6.

**Fix:** `src/openms/source/KERNEL/BaseFeature.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/KERNEL/BaseFeature.cpp
+++ b/src/openms/source/KERNEL/BaseFeature.cpp
@@ -122,18 +122,41 @@ namespace OpenMS
 
   void BaseFeature::sortPeptideIdentifications()
   {
+    // the hits are sorted in a pass of their own: doing it from inside the comparator would modify
+    // the objects std::sort is comparing, and would leave the hits of any element that the sort
+    // never happens to compare (e.g. the only identification of a feature) unsorted
+    for (PeptideIdentification& pep : peptides_)
+    {
+      pep.sort();
+    }
+    // the score orientation is taken from the first identification that has hits and then used for
+    // every comparison: reading it from the left operand would make the comparator asymmetric as
+    // soon as two identifications disagree, which breaks the strict weak ordering std::sort requires
+    bool higher_score_better = true;
+    for (const PeptideIdentification& pep : peptides_)
+    {
+      // hits, not PeptideIdentification::empty(): that is false for a hit-less identification
+      // read from featureXML, which carries its identifier and score type
+      if (!pep.getHits().empty())
+      {
+        higher_score_better = pep.isHigherScoreBetter();
+        break;
+      }
+    }
     std::sort(peptides_.rbegin(),peptides_.rend(),
-              [](PeptideIdentification& p1, PeptideIdentification& p2)
-              {p1.sort();p2.sort();
-              if (p1.empty())
+              [higher_score_better](const PeptideIdentification& p1, const PeptideIdentification& p2)
+              {
+              // two identifications without hits are equivalent; returning true for both orders
+              // would violate asymmetry (undefined behaviour in std::sort)
+              if (p1.getHits().empty())
               {
-                return true;
+                return !p2.getHits().empty();
               }
-              if (p2.empty())
+              if (p2.getHits().empty())
               {
-                return false;
+                return false; // getHits()[0] below would read past the end of an empty vector
               }
-              if (p1.isHigherScoreBetter())
+              if (higher_score_better)
               {
                 return p1.getHits()[0].getScore() < p2.getHits()[0].getScore();
               }
```

**Test:** `src/tests/class_tests/openms/source/BaseFeature_test.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/tests/class_tests/openms/source/BaseFeature_test.cpp
+++ b/src/tests/class_tests/openms/source/BaseFeature_test.cpp
@@ -425,11 +425,15 @@ START_SECTION((sortPeptideIdentifications()))
     hit.setScore(0.9);
     ids[1].getHits().push_back(hit); // different to first hit
 
-    //ids[2] is empty.
+    // An identification loaded from featureXML can have metadata but no hits.
+    ids[2].setIdentifier("hitless");
+    ids[2].setScoreType("score");
+    ids[2].setHigherScoreBetter(false);
 
     tmp.sortPeptideIdentifications();
     TEST_EQUAL(ids[0].getHits()[0].getScore(), 0.9);
-    TEST_EQUAL(ids[2].empty(), true);
+    TEST_TRUE(ids[2].getHits().empty());
+    TEST_EQUAL(ids[2].getIdentifier(), "hitless");
 END_SECTION
 
 /////////////////////////////////////////////////////////////
```

### Assessment

- **Behaviour change:** None for input that previously worked: identifications with hits still come first, ordered best score first, and hit-less identifications still go to the end. Input that previously read past the end of an empty vector (a hit-less identification with metadata) now sorts cleanly, with such identifications placed last. std::sort remains unstable, so the relative order of equal-scoring or hit-less identifications is unspecified before and after. The accompanying CPP-091 change can reorder features whose identifications disagree on higher_score_better, because orientation now comes from the first identification with hits; that is a separate finding.
- **Concerns:** None for the CPP-089 lines. When reviewing, note that the released hunk mixes three findings: the CPP-091 choice of taking orientation from the first identification with hits silently applies one direction to mixed-engine identifications instead of rejecting them (the Rust port returns an error there). The regression test covers one hit-less identification with metadata, not the case of two fully default identifications.
- **Skeptic on the fix (yes):** (1) behavior_change says "None for input that previously worked" and names only CPP-091. It misses a visible CPP-090 effect of the same released hunk: hits are now sorted for every identification, including a feature's only one, which std::sort never passed to the comparator before. QTClusterFinder reads pepIDs[0].getHits()[0] right after the sort (QTClusterFinder.cpp:107-115). FeatureLinkerUnlabeledQT with use_identifications on featureXML whose hits are not score-ordered can therefore get a different sequence/charge key and threshold decision. ProteomicsLFQ and PipEcho sort hits beforehand (IDConflictResolver; Impl.cpp:71-74), so they are unchanged. (2) Minor: the fixed comparator is still not a strict weak ordering if a score is NaN. This is not a regression, and it is harmless under libc++'s guarded insertion sort below 24 elements.
- **Upstream patch:** Applies cleanly: origin/develop BaseFeature.cpp and BaseFeature_test.cpp are byte-identical to core-v4.0.0-ci.2 (blobs e303b92 and 962f142). The CPP-089 change is self-contained: replacing the two empty() guards with getHits().empty() and returning !p2.getHits().empty() works with the existing non-const lambda signature. It can be submitted alone or together with the CPP-090/CPP-091 parts of the same hunk. No dependency on other OpenMS4 changes.
- **Skeptic's notes:** Verified: develop BaseFeature.cpp and BaseFeature_test.cpp blobs equal ci.2 (e303b92, 962f142). PeptideIdentification::empty() at :210-217 and FeatureXMLHandler :553-573 and :819-822 behave as described. 181dadf changes only BaseFeature.cpp; b6dd412 changes only the test. Tag core-v4.0.0-ci.4 points at 4f5c86f, and 23944b6 touches neither file. Target lines 149-158 (guards) and 428-436 (test) are correct. The pre-fix test would evaluate ids[2].getHits()[0] in every comparison involving ids[2]. The claim that two default-empty identifications "usually" give only an arbitrary order holds for libc++: ranges under 24 elements use the guarded __insertion_sort (sort.h:757-759). BaseFeature::sortPeptideIdentifications is not bound in pyOpenMS.

**Decision (confirmed 2026-09-14):** Keep the fix as it is. Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-170"></a>
## CPP-170: mzData checks missing and short arrays after unsafe indexing

**Loading an mzData spectrum with a missing binary array, or with an intensity or supplemental array shorter than its m/z array, makes the reader index past the end of heap vectors.**

- **Mechanism:** All line numbers are for origin/develop. MzDataHandler.cpp and its test are byte-identical to core-v4.0.0-ci.2 (bc9cc12), the revision the Rust report cites. MzDataHandler::fillData_ trusts the structure of the spectrum: (1) :522 `precisions_[0] == "32"` and :527 `precisions_[1] == "32"` run before the guard at :533 `if (data_to_decode_.size() < 2) return;`. A spectrum with only an mzArrayBinary reads precisions_[1] from a one-element vector. (2) :537-541: when the m/z and intensity lengths differ, the code calls error(LOAD, ...). At XMLHandler.cpp:71-87 that only writes a log line. :542-546 then sets peak_count_ to the m/z length, and the loop at :558-561 reads decoded_list_[1][n] (or decoded_double_list_[1][n]) past a shorter intensity array. (3) :572 reads precisions_[2+i] and decoded_*_list_[2+i][n] for each FloatDataArray without checking how many arrays exist or how long they are. FloatDataArrays are created at the supDataArrayBinary start tag (:323-340), but data slots only at its arrayName child (:426-430). (4) :476/:482 index precisions_[i] (and endians_[i]) for every data slot, assuming each array element holds exactly one <data>. An empty <intenArrayBinary/> opens a slot (:422-425) with no precision. (5) :142 `data_to_decode_.back() += transcoded_chars;` runs on an empty vector when a <data> element is not inside any array element. That is undefined behaviour and a write. (6) The decode loop treats any precision other than "64" as 32-bit (:482/:500), but :522/:527 treat any precision other than "32" as 64-bit, so a nonstandard precision on the intensity array makes the loop read an empty double vector. OpenMS's own writer can produce case (3): writeTo at :1035-1046 logs a FloatDataArray whose length differs from the spectrum and still writes all mda.size() values.
- **Trigger:** A spectrum whose arrays are `<mzArrayBinary><data precision="32" endian="little" length="2">AADwQgAA+kI=</data></mzArrayBinary><intenArrayBinary><data precision="32" endian="little" length="1">AADIQg==</data></intenArrayBinary>` (two m/z values, one intensity). Pre-fix, the reader reads decoded_list_[1][1] out of bounds and returns 2 peaks, the second with a garbage intensity. The same spectrum with only the mzArrayBinary reads precisions_[1] out of bounds. Through the API: an MSSpectrum with 3 peaks and a FloatDataArray of 2 values, saved with MzDataFile::store (only an error is logged) and loaded again.
- **Consequence:** Heap out-of-bounds reads. Garbage intensities or supplemental values silently become peak data, or the process crashes. The stray-<data> case appends to a std::string object located before the vector's buffer, or near null: memory corruption or a segfault. There is no exception and no failed load, only log lines.
- **Who hits it:** MzDataFile::load; FileHandler loading of .mzData files (FileConverter, FileInfo and any TOPP tool that reads spectra through FileHandler); pyOpenMS MzDataFile.load (bind_misc.cpp:4701-4712). mzData is a legacy PSI format, replaced by mzML in 2008, and few current tools write it. Correct files with paired arrays of equal length never trigger it. All 18 upstream mzData test files use precision 32 or 64 with consistent arrays. Real triggers are corrupt or hand-edited files, non-conforming third-party writers, and OpenMS-written mzData whose FloatDataArray length drifted from the peak count. Likelihood for real users is low. It is P0 only because the rubric counts memory safety reachable from input files.

> **Skeptic's correction:** (a) Mechanism (1) is incomplete. A spectrum with no binary arrays at all also reads precisions_[0] from an empty vector at :522, not only precisions_[1] from a one-element vector. (b) Mechanism (2): :542-546 only reassigns peak_count_ when the `length` attribute differs. In the trigger length="2" already equals the m/z length, so the out-of-bounds loop bound comes from the attribute. The result is the same. (c) Consequence and mechanism (5): back() on a vector with no buffer computes nullptr minus one element. That wraps to the top of the address space, not "near null". It is still a segfault. (d) Reach understates the writer path. PeakFileOptions write_supplemental_data_ defaults to true (PeakFileOptions.h:226). Besides a drifted length, an empty FloatDataArray on a non-empty spectrum is written as length="0" with no text and reloads as an empty decoded vector, so :572 reads element 0 through a null data pointer (a crash, not a garbage value). Unfilled float arrays are a more ordinary API trigger than the draft suggests. (e) Concern (4) is wrong as stated. A supDataArrayBinary without arrayName but with <data> makes precisions_ one longer than data_to_decode_. After the fix the whole spectrum loads with zero peaks and an error. Before the fix its base64 text was appended to the intensity slot (data_to_decode_.back()), corrupting the intensity array. Arrays shift into the wrong FloatDataArray only when a sup array lacks both arrayName and <data>. Both variants violate the schema, which requires arrayName (mzData_1_05.xsd:313) and allows only precision 32 or 64 (:341-346). (f) The c77ff14 reserve cap also bounds large positive counts, not only negative (wrapped) ones.

### The fix

181dadf changes MzDataHandler::fillData_ and onCharacters (line numbers at 4f5c86f): (a) 476-485: if precisions_.size() != data_to_decode_.size(), it logs an error and keeps the spectrum without peaks. (b) 534-543: the guard for fewer than two arrays now runs before precisions_[0] and [1] are read, and logs a warning when exactly one array is present. (c) 548 and 553: the precision tests become `!= "64"`, matching the decode loop. (d) 570-575: peak_count_ is clamped to the intensity array length. (e) 601-613: supplemental arrays stop at a missing slot and take values only while n is below that array's decoded length, as MzMLHandler does. (f) 141-144: <data> text is appended only if a slot exists. c77ff14 (core-v4.0.0-ci.3) separately caps `exp_->reserve(count)` from spectrumList count at 1e5 (356-357, with #include <algorithm> at 12-13), so a negative count, which wraps in the UInt, cannot request a huge allocation. That is hardening against a different malformed attribute and is not needed for the out-of-bounds fix. Regression test (b2079fb): MzDataFile_test section "regression: incomplete binary arrays and MSn scan modes". It covers only the m/z array (0 peaks expected), a short intensity array (1 peak, m/z 120, intensity 100) and an empty <intenArrayBinary/> (0 peaks).

*State:* Released in 4f5c86f (core-v4.0.0-ci.4): 181dadf (reader checks), c77ff14 (bounded spectrumList reserve, the ci.3 tag commit) and b2079fb (test) are all ancestors of 4f5c86f. Not reverted; 23944b6 does not touch mzData or mzXML files.

**Fix:** `src/openms/source/FORMAT/HANDLERS/MzDataHandler.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FORMAT/HANDLERS/MzDataHandler.cpp
+++ b/src/openms/source/FORMAT/HANDLERS/MzDataHandler.cpp
@@ -136,9 +138,10 @@ namespace OpenMS::Internal
       {
         spec_.setComment(transcoded_chars);
       }
-      else if (current_tag == "data")
+      else if (current_tag == "data" && !data_to_decode_.empty())
       {
         //chars may be split to several chunks => concatenate them
+        // (a stray <data> before any binary array has no slot; fillData_ reports the unpaired precision)
         data_to_decode_.back() += transcoded_chars;
       }
       else if (current_tag == "arrayName" && parent_tag == "supDataArrayBinary")
@@ -469,6 +473,16 @@ namespace OpenMS::Internal
       std::vector<float> decoded;
       std::vector<double> decoded_double;
 
+      // Each binary array opens one data_to_decode_ entry and must hold exactly one <data> element,
+      // which opens the matching precisions_/endians_ entry. In a malformed spectrum that pairing is
+      // lost, the encoding of an array cannot be recovered, and the loops below would index past
+      // precisions_, so the spectrum is kept without peaks.
+      if (precisions_.size() != data_to_decode_.size())
+      {
+        error(LOAD, std::string("Spectrum '") + spec_.getNativeID() + "' has " + data_to_decode_.size() + " binary data arrays but " + precisions_.size() + " <data> elements. Its peaks are not loaded.");
+        return;
+      }
+
       // data_to_decode is an encoded spectrum, represented as
       // vector of base64-encoded strings:
       // Each string represents one property (e.g. mzData) and decodes
@@ -517,21 +531,30 @@ namespace OpenMS::Internal
 
       // this works only if MapType::PeakType is a Peak1D or derived from it
       {
+        // mzData requires an m/z and an intensity array. Check this before precisions_[0] and
+        // precisions_[1] are read: a spectrum lacking either has no peaks to build.
+        if (data_to_decode_.size() < 2)
+        {
+          if (!data_to_decode_.empty())
+          {
+            warning(LOAD, std::string("The m/z or intensity array of spectrum '") + spec_.getNativeID() + "' is missing. Its peaks are not loaded.");
+          }
+          return;
+        }
+
         //store what precision is used for intensity and m/z
+        // (anything but "64" was decoded as 32 bit above, so read it from the same list)
         bool mz_precision_64 = true;
-        if (precisions_[0] == "32")
+        if (precisions_[0] != "64")
         {
           mz_precision_64 = false;
         }
         bool int_precision_64 = true;
-        if (precisions_[1] == "32")
+        if (precisions_[1] != "64")
         {
           int_precision_64 = false;
         }
 
-        // no data was decoded?
-        if (data_to_decode_.size() < 2) return;
-
         const size_t peak_count_mz = mz_precision_64 ? decoded_double_list_[0].size() : decoded_list_[0].size();
         const size_t peak_count_int = int_precision_64 ? decoded_double_list_[1].size() : decoded_list_[1].size();
         if (peak_count_mz != peak_count_int)
@@ -544,6 +567,12 @@ namespace OpenMS::Internal
           warning(LOAD,std::string("Length of data arrays (m/z and int) differs from value in attribute 'length': ") + peak_count_mz + " vs. " + peak_count_ + ".");
           peak_count_ = peak_count_mz;
         }
+        // the length mismatch above is only logged, so stop at the end of a shorter intensity array
+        // instead of reading past it
+        if (peak_count_int < peak_count_)
+        {
+          peak_count_ = peak_count_int;
+        }
 
         // reserve space for spectrum
         spec_.reserve(peak_count_);
@@ -569,7 +598,19 @@ namespace OpenMS::Internal
             //load data from meta data arrays
             for (Size i = 0; i < spec_.getFloatDataArrays().size(); ++i)
             {
-              spec_.getFloatDataArrays()[i].push_back(precisions_[2 + i] == "64" ? decoded_double_list_[2 + i][n] : decoded_list_[2 + i][n]);
+              // A supDataArrayBinary may lack its <data>, or be shorter than the m/z array (writeTo only
+              // logs that mismatch). As in MzMLHandler, such an array ends early instead of being read
+              // past its end.
+              const Size sup_index = 2 + i;
+              if (sup_index >= data_to_decode_.size())
+              {
+                break;
+              }
+              const bool sup_precision_64 = (precisions_[sup_index] == "64");
+              if (n < (sup_precision_64 ? decoded_double_list_[sup_index].size() : decoded_list_[sup_index].size()))
+              {
+                spec_.getFloatDataArrays()[i].push_back(sup_precision_64 ? decoded_double_list_[sup_index][n] : decoded_list_[sup_index][n]);
+              }
             }
           }
         }
```

**Test:** `src/tests/class_tests/openms/source/MzDataFile_test.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/tests/class_tests/openms/source/MzDataFile_test.cpp
+++ b/src/tests/class_tests/openms/source/MzDataFile_test.cpp
@@ -11,9 +11,10 @@
 #include <OpenMS/test_config.h>
 ///////////////////////////
 
-#include <OpenMS/FORMAT/MzDataFile.h>
 #include <OpenMS/FORMAT/FileHandler.h>
+#include <OpenMS/FORMAT/MzDataFile.h>
 #include <OpenMS/KERNEL/MSExperiment.h>
+#include <fstream>
 
 using namespace OpenMS;
 using namespace std;
@@ -848,11 +849,56 @@ END_SECTION
 
 START_SECTION(bool isSemanticallyValid(const std::string& filename, StringList& errors, StringList& warnings))
 {
-  //This is not officially supported - the mapping file was hand-crafted by Marc Sturm
+  // This is not officially supported - the mapping file was hand-crafted by Marc Sturm
   NOT_TESTABLE
 }
 END_SECTION
 
+START_SECTION((regression: incomplete binary arrays and MSn scan modes))
+{
+  MzDataFile file;
+  const std::string mz = "<mzArrayBinary><data precision=\"32\" endian=\"little\" length=\"2\">AADwQgAA+kI=</data></mzArrayBinary>";
+  const std::string intensity = "<intenArrayBinary><data precision=\"32\" endian=\"little\" length=\"1\">AADIQg==</data></intenArrayBinary>";
+  auto load = [&](const std::string& arrays, const std::string& mode) {
+    std::string input;
+    NEW_TMP_FILE(input)
+    std::ofstream(input) << "<?xml version=\"1.0\"?><mzData version=\"1.05\" accessionNumber=\"test\">"
+                            "<spectrumList count=\"1\"><spectrum id=\"1\"><spectrumDesc><spectrumSettings>"
+                            "<spectrumInstrument msLevel=\"2\"><cvParam cvLabel=\"psi\" accession=\"PSI:1000036\" name=\"ScanMode\" value=\""
+                         << mode << "\"/></spectrumInstrument></spectrumSettings></spectrumDesc>" << arrays << "</spectrum></spectrumList></mzData>";
+    PeakMap result;
+    file.load(input, result);
+    // These deliberately incomplete reader fixtures are not writer-schema tests.
+    File::remove(input);
+    return result;
+  };
+  const auto missing = load(mz, "unknown");
+  TEST_EQUAL(missing.size(), 1)
+  ABORT_IF(missing.size() != 1)
+  TEST_EQUAL(missing[0].size(), 0)
+  TEST_EQUAL(missing[0].getInstrumentSettings().getScanMode(), InstrumentSettings::ScanMode::MSNSPECTRUM)
+
+  const auto short_intensity = load(mz + intensity, "EnhancedMultiplyChargedScan");
+  TEST_EQUAL(short_intensity.size(), 1)
+  ABORT_IF(short_intensity.size() != 1)
+  TEST_EQUAL(short_intensity[0].size(), 1)
+  ABORT_IF(short_intensity[0].size() != 1)
+  TEST_REAL_SIMILAR(short_intensity[0][0].getMZ(), 120.0)
+  TEST_REAL_SIMILAR(short_intensity[0][0].getIntensity(), 100.0)
+  TEST_EQUAL(short_intensity[0].getInstrumentSettings().getScanMode(), InstrumentSettings::ScanMode::EMC)
+
+  const auto unpaired = load(mz + "<intenArrayBinary/>", "TimeDelayedFragmentationScan");
+  TEST_EQUAL(unpaired.size(), 1)
+  ABORT_IF(unpaired.size() != 1)
+  TEST_EQUAL(unpaired[0].size(), 0)
+  TEST_EQUAL(unpaired[0].getInstrumentSettings().getScanMode(), InstrumentSettings::ScanMode::TDF)
+  const auto absorption = load(mz + intensity, "PhotodiodeArrayDetector");
+  TEST_EQUAL(absorption.size(), 1)
+  ABORT_IF(absorption.size() != 1)
+  TEST_EQUAL(absorption[0].getInstrumentSettings().getScanMode(), InstrumentSettings::ScanMode::ABSORPTION)
+}
+END_SECTION
+
 /////////////////////////////////////////////////////////////
 /////////////////////////////////////////////////////////////
 /// check the temporary files written above against their XML schema (types without a validator are skipped)
```

### Assessment

- **Behaviour change:** None for valid files, where every array holds one <data> with precision 32 or 64 and the arrays have equal lengths: the same peaks and FloatDataArrays load, with no new exceptions. Malformed spectra behave differently: - Unpaired arrays, or a missing m/z or intensity array: the spectrum now loads with zero peaks and a logged error or warning. Before, the reader read out of bounds. - An intensity array shorter than the m/z array: only the paired peaks load. - A short supplemental array: the FloatDataArray comes back shorter. - A nonstandard precision string now decodes consistently as 32-bit. Before, it silently gave zero peaks or read out of bounds. The 1e5 reserve cap only changes allocation for files with more than 100000 spectra (extra reallocation, same output).
- **Concerns:** (1) The reader stays lenient. A corrupt spectrum loads empty or truncated with only a log line and no exception, whereas the Rust port rejects it with a structured error. The owner may prefer a ParseError. (2) A short supplemental array now yields a FloatDataArray shorter than the spectrum. Code that indexes float arrays by peak index must cope (the same contract as MzMLHandler). (3) Only the reader is fixed. writeTo (:1035-1046) still writes mismatched FloatDataArrays with just a logged error. (4) A supDataArrayBinary without arrayName still shifts later arrays into the wrong slots. That was already true before and is no longer memory-unsafe. (5) The spectrumList reserve cap is separate hardening bundled into c77ff14 and can be split off. (6) The test section also asserts CPP-171 scan modes, so the two findings share one test.
- **Skeptic on the fix (yes):** (1) Hunks 12-13 (#include <algorithm>) and 356-357 belong to c77ff14's spectrumList reserve cap. By the draft's own account they are not part of the out-of-bounds fix, so they should not be listed as its hunks. None of 181dadf's MzDataHandler changes use <algorithm>. (2) Test hunk 13-17 includes a cosmetic swap of the FileHandler and MzDataFile includes (14-15). Only line 17 (<fstream>) is needed, for the same reason the draft drops the comment reformat at 852. (3) upstream_patch is wrong that dropping the scan-mode assertions makes the test usable without CPP-171. Every fixture spectrum has msLevel="2" and a ScanMode the old reader does not know ("unknown", EnhancedMultiplyChargedScan, TimeDelayedFragmentationScan, PhotodiodeArrayDetector). Without CPP-171, every load() first calls exp_->getSpectra().back() on the empty experiment, a write before the reserve(1) buffer. A CPP-170-only test must change the fixture itself (msLevel 1 or ScanMode MassScan), not just delete assertions. For the same reason the pre-fix "returns 2 peaks" outcome cannot be observed through this test; it is an analytical claim. (4) After the fix, a spectrum rejected for mismatched array and <data> counts keeps its FloatDataArrays (names and meta) with no values, next to zero peaks. (5) Untested paths: a spectrum with no arrays, a stray <data>, a short or empty supplemental array, and a nonstandard precision. The code change itself closes every out-of-bounds path I traced: equal slot and precision counts bound every precisions_[i], the <2 guard runs first, the precision tests are consistent, the intensity read is clamped, and supplemental reads are bounds-checked. It applies upstream: all touched files are byte-identical at origin/develop, and VALIDATE_TMP_FILES skips removed files (TestFileValidation.h:54).
- **Upstream patch:** It applies cleanly. At origin/develop (3cee4c0c25, 2026-09-14), MzDataHandler.cpp and MzDataFile_test.cpp are byte-identical to core-v4.0.0-ci.2, so the defect is still present upstream and these hunks apply without change. The test uses only upstream facilities (NEW_TMP_FILE, File::remove, PeakMap; VALIDATE_TMP_FILES is already in the upstream file). Two adjustments for an upstream PR: leave out the unrelated comment reformat at test line 852, and either submit together with CPP-171 or drop the scan-mode assertions from the shared test section.
- **Skeptic's notes:** Verified: MzDataHandler.cpp, MzDataHandler.h, XMLHandler.cpp and MzDataFile_test.cpp at origin/develop (3cee4c0c25) are byte-identical to core-v4.0.0-ci.2, which is bc9cc12. XMLHandler::error only logs (XMLHandler.cpp:71-87). The ci.2..4f5c86f diff is exactly 181dadf plus the c77ff14 reserve cap. 181dadf, c77ff14 and b2079fb are ancestors of 4f5c86f, and no other commit touches these files. All 18 upstream .mzData files decode with equal m/z and intensity lengths, supplemental arrays at least as long, arrayName present, and precision 32 or 64 (checked with a script). bind_misc.cpp:4711-4712 are the pyOpenMS load bindings. MzMLHandler bounds short float arrays similarly (MzMLHandler.cpp:613). P0 holds: the heap out-of-bounds read comes from input files and from a default store/load round-trip of spectra with short or empty float arrays.

**Decision (provisional: recommended default, not yet confirmed; overrule here):** Keep lenient loading; add tests for the untested paths (no arrays, stray data, short supplemental array, nonstandard precision). Upstream: included in the grouped patch set for its area, for your review (confirmed). **Owner, 2026-09-14:** the missing-array message stays at debug level (accepted as implemented).

<a id="cpp-171"></a>
## CPP-171: mzData writer emits scan modes its reader does not recognize

**The mzData reader does not recognise three scan-mode values its own writer emits, and for MS2+ spectra its fallback writes to the previously stored spectrum, or to memory before an empty spectrum vector.**

- **Mechanism:** All line numbers are for origin/develop, identical to ci.2. MzDataHandler::writeTo writes ScanMode ABSORPTION, EMC and TDF as value="PhotodiodeArrayDetector" (:919-921), "EnhancedMultiplyChargedScan" (:923-925) and "TimeDelayedFragmentationScan" (:927-929). The reader, cvParam_ (:1089-1131), only knows Zoom, MassScan, SelectedIonDetection, SelectedReactionMonitoring, ConsecutiveReactionMonitoring, ConstantNeutralGainScan, ConstantNeutralLossScan, ProductIonScan, PrecursorIonScan and EnhancedResolutionScan. For any other value: at MS level 1 it sets MASSSPECTRUM and logs a warning (:1138-1142). At MS level 2 or higher, :1136 runs `exp_->getSpectra().back().getInstrumentSettings().setScanMode(MSNSPECTRUM)`. The spectrum being parsed is spec_ (reset at :343), which is only appended at </spectrum> (:446-450), so back() is the previously stored spectrum and spec_ keeps UNKNOWN. Spectra removed by the MS-level filter are never added (:397-400; their child tags are skipped at :214-217), so exp_ can still be empty: when the first spectrum is MSn, or when all earlier spectra were filtered out. back() on an empty std::vector is undefined behaviour. When spectrumList count is at least 1, :352-353 has reserved a buffer and the write lands in the MSSpectrum-sized slot just before it, which is heap corruption. With count=0 there is no buffer, and it dereferences near null.
- **Trigger:** A file whose first spectrum is `<spectrumInstrument msLevel="2"><cvParam cvLabel="psi" accession="PSI:1000036" name="ScanMode" value="TimeDelayedFragmentationScan"/></spectrumInstrument>`, under `<spectrumList count="1">`: back() is called on the empty experiment. The same result follows from any other unknown value, such as "unknown", or from loading with PeakFileOptions MS levels {2} when MS1 spectra come first. As a round-trip: store an MSExperiment holding an MS1 spectrum followed by an MS2 spectrum with ScanMode TDF, then load it. The MS1 spectrum comes back as MSNSPECTRUM and the MS2 spectrum as UNKNOWN. An MS1 spectrum stored as ABSORPTION or EMC reloads as MASSSPECTRUM, with a warning.
- **Consequence:** When the experiment is still empty: a heap write before the vector buffer (silent corruption, possibly a later crash) or a segfault. Otherwise the scan-mode metadata is silently wrong: the previous spectrum is marked MSNSPECTRUM, the current one stays UNKNOWN, and ABSORPTION, EMC and TDF are lost on round-trip. Peak data is unaffected, and scan mode is metadata that few algorithms act on. It is mainly carried into written mzML.
- **Who hits it:** MzDataFile::load; FileHandler .mzData loading (FileConverter and others); pyOpenMS MzDataFile.load. A trigger needs an mzData file with an MSn spectrum whose ScanMode value is outside the reader's list. The three OpenMS spellings only appear when OpenMS stored mzData from spectra marked ABSORPTION, EMC or TDF, for example converted from mzML carrying SCIEX QTrap EMC or TDF terms. Other writers may use any text, because the CV leaves the value free. The upstream mzData test files use only MassScan, SelectedIonDetection and Zoom. Real-world likelihood is low: mzData is legacy and these scan modes are rare. It is P0 because a valid file can cause the memory-unsafe write.

> **Skeptic's correction:** (a) The mzData 1.05 schema declares cvParam value as an optional xs:string (mzData_1_05.xsd:183). That confirms a first MSn spectrum with any unrecognised ScanMode is schema-valid, so P0 rests on a valid file, as the draft says. (b) With count=0, back() on a vector with no buffer wraps to just below the top of the address space, not "near null". It is still a segfault. (c) The mechanism names only the MS-level filter as a reason for skipped earlier spectra. The RT-range filter in cvParam_ (:1148-1159) also leaves spectra out of exp_; the fix's own comment mentions both. (d) Concern (3) is accurate but incomplete. The Rust reader also warns on the MSn fallback (mzdata.rs:1738-1741), where Core stays silent. The Rust writer refuses MS1SPECTRUM, MSNSPECTRUM, ABSORPTION, EMC and TDF (ROUND_TRIP_SCAN_MODES, mzdata.rs:2418-2427), so a Core-vs-Rust comparison diverges on more than these three spellings.

### The fix

181dadf changes MzDataHandler::cvParam_ (line numbers at 4f5c86f). It adds branches that map PhotodiodeArrayDetector, EnhancedMultiplyChargedScan and TimeDelayedFragmentationScan to ABSORPTION, EMC and TDF (1173-1186). The MS2+ fallback now sets MSNSPECTRUM on spec_ instead of exp_->getSpectra().back() (1191-1193). Regression test (b2079fb): the MzDataFile_test section shared with CPP-170 loads a single msLevel=2 spectrum. With value "unknown" it expects MSNSPECTRUM, where pre-fix code calls back() on the empty experiment. With the three writer spellings it expects TDF, EMC and ABSORPTION.

*State:* Released in 4f5c86f (core-v4.0.0-ci.4), first shipped in ci.3. Fix 181dadf and test b2079fb are both ancestors of 4f5c86f. Not reverted.

**Fix:** `src/openms/source/FORMAT/HANDLERS/MzDataHandler.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FORMAT/HANDLERS/MzDataHandler.cpp
+++ b/src/openms/source/FORMAT/HANDLERS/MzDataHandler.cpp
@@ -1129,11 +1170,27 @@ namespace OpenMS::Internal
             spec_.getInstrumentSettings().setZoomScan(true);
             spec_.getInstrumentSettings().setScanMode(InstrumentSettings::ScanMode::MASSSPECTRUM);
           }
+          // the next three are the spellings writeTo() emits; the CV leaves ScanMode values free,
+          // so without them a stored ABSORPTION/EMC/TDF spectrum would not load back as such
+          else if (value == "PhotodiodeArrayDetector")
+          {
+            spec_.getInstrumentSettings().setScanMode(InstrumentSettings::ScanMode::ABSORPTION);
+          }
+          else if (value == "EnhancedMultiplyChargedScan")
+          {
+            spec_.getInstrumentSettings().setScanMode(InstrumentSettings::ScanMode::EMC);
+          }
+          else if (value == "TimeDelayedFragmentationScan")
+          {
+            spec_.getInstrumentSettings().setScanMode(InstrumentSettings::ScanMode::TDF);
+          }
           else
           {
             if (spec_.getMSLevel() >= 2)
             {
-              exp_->getSpectra().back().getInstrumentSettings().setScanMode(InstrumentSettings::ScanMode::MSNSPECTRUM);
+              // the spectrum being parsed is spec_; it is not in exp_ yet, and exp_ may still be
+              // empty (first spectrum, or earlier ones skipped by MS-level/RT options)
+              spec_.getInstrumentSettings().setScanMode(InstrumentSettings::ScanMode::MSNSPECTRUM);
             }
             else
             {
```

**Test:** `src/tests/class_tests/openms/source/MzDataFile_test.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/tests/class_tests/openms/source/MzDataFile_test.cpp
+++ b/src/tests/class_tests/openms/source/MzDataFile_test.cpp
@@ -11,9 +11,10 @@
 #include <OpenMS/test_config.h>
 ///////////////////////////
 
-#include <OpenMS/FORMAT/MzDataFile.h>
 #include <OpenMS/FORMAT/FileHandler.h>
+#include <OpenMS/FORMAT/MzDataFile.h>
 #include <OpenMS/KERNEL/MSExperiment.h>
+#include <fstream>
 
 using namespace OpenMS;
 using namespace std;
@@ -848,11 +849,56 @@ END_SECTION
 
 START_SECTION(bool isSemanticallyValid(const std::string& filename, StringList& errors, StringList& warnings))
 {
-  //This is not officially supported - the mapping file was hand-crafted by Marc Sturm
+  // This is not officially supported - the mapping file was hand-crafted by Marc Sturm
   NOT_TESTABLE
 }
 END_SECTION
 
+START_SECTION((regression: incomplete binary arrays and MSn scan modes))
+{
+  MzDataFile file;
+  const std::string mz = "<mzArrayBinary><data precision=\"32\" endian=\"little\" length=\"2\">AADwQgAA+kI=</data></mzArrayBinary>";
+  const std::string intensity = "<intenArrayBinary><data precision=\"32\" endian=\"little\" length=\"1\">AADIQg==</data></intenArrayBinary>";
+  auto load = [&](const std::string& arrays, const std::string& mode) {
+    std::string input;
+    NEW_TMP_FILE(input)
+    std::ofstream(input) << "<?xml version=\"1.0\"?><mzData version=\"1.05\" accessionNumber=\"test\">"
+                            "<spectrumList count=\"1\"><spectrum id=\"1\"><spectrumDesc><spectrumSettings>"
+                            "<spectrumInstrument msLevel=\"2\"><cvParam cvLabel=\"psi\" accession=\"PSI:1000036\" name=\"ScanMode\" value=\""
+                         << mode << "\"/></spectrumInstrument></spectrumSettings></spectrumDesc>" << arrays << "</spectrum></spectrumList></mzData>";
+    PeakMap result;
+    file.load(input, result);
+    // These deliberately incomplete reader fixtures are not writer-schema tests.
+    File::remove(input);
+    return result;
+  };
+  const auto missing = load(mz, "unknown");
+  TEST_EQUAL(missing.size(), 1)
+  ABORT_IF(missing.size() != 1)
+  TEST_EQUAL(missing[0].size(), 0)
+  TEST_EQUAL(missing[0].getInstrumentSettings().getScanMode(), InstrumentSettings::ScanMode::MSNSPECTRUM)
+
+  const auto short_intensity = load(mz + intensity, "EnhancedMultiplyChargedScan");
+  TEST_EQUAL(short_intensity.size(), 1)
+  ABORT_IF(short_intensity.size() != 1)
+  TEST_EQUAL(short_intensity[0].size(), 1)
+  ABORT_IF(short_intensity[0].size() != 1)
+  TEST_REAL_SIMILAR(short_intensity[0][0].getMZ(), 120.0)
+  TEST_REAL_SIMILAR(short_intensity[0][0].getIntensity(), 100.0)
+  TEST_EQUAL(short_intensity[0].getInstrumentSettings().getScanMode(), InstrumentSettings::ScanMode::EMC)
+
+  const auto unpaired = load(mz + "<intenArrayBinary/>", "TimeDelayedFragmentationScan");
+  TEST_EQUAL(unpaired.size(), 1)
+  ABORT_IF(unpaired.size() != 1)
+  TEST_EQUAL(unpaired[0].size(), 0)
+  TEST_EQUAL(unpaired[0].getInstrumentSettings().getScanMode(), InstrumentSettings::ScanMode::TDF)
+  const auto absorption = load(mz + intensity, "PhotodiodeArrayDetector");
+  TEST_EQUAL(absorption.size(), 1)
+  ABORT_IF(absorption.size() != 1)
+  TEST_EQUAL(absorption[0].getInstrumentSettings().getScanMode(), InstrumentSettings::ScanMode::ABSORPTION)
+}
+END_SECTION
+
 /////////////////////////////////////////////////////////////
 /////////////////////////////////////////////////////////////
 /// check the temporary files written above against their XML schema (types without a validator are skipped)
```

### Assessment

- **Behaviour change:** Yes, for valid files that use these values. Spectra marked PhotodiodeArrayDetector, EnhancedMultiplyChargedScan or TimeDelayedFragmentationScan now load as ABSORPTION, EMC or TDF. Before, MS1 spectra got MASSSPECTRUM with a warning, and MSn spectra stayed UNKNOWN while the previous spectrum was changed. MSn spectra with other unknown values now get MSNSPECTRUM and no longer modify the previous spectrum. Recognised values, and unknown values at MS level 1, behave as before. Peaks are unchanged. Metadata that tools write onward, such as the mzML spectrum-type terms from FileConverter, can differ for such files. No upstream mzData test data contains these values, so TOPP reference outputs are unaffected.
- **Concerns:** (1) The reader now accepts OpenMS's own spellings, which are not standard psi-mzdata terms. This is a pragmatic round-trip fix, not the shared bidirectional table the Rust report proposed, so the writer and reader lists can drift apart again. (2) The MSn fallback stays silent, unlike the MS1 fallback, which warns. (3) Core and the Rust port now read these values differently. The Rust port does not recognise the three spellings and instead refuses to write modes that cannot round-trip. Core reads TDF where Rust reads MSNSPECTRUM (MSn) or MASSSPECTRUM (MS1), so a differential comparison on such files would disagree. (4) The shared test's "missing" and "unpaired" cases also need the CPP-170 fix, so this test cannot run cleanly with CPP-171 applied alone.
- **Skeptic on the fix (yes):** (1) Test hunk 13-17 includes an unrelated swap of two includes (14-15). Only <fstream> at 17 is needed. The fix hunks are correct. (2) The fix closes the undefined behaviour and the three spellings, but another writer/reader mismatch remains, which concern (1) only hints at. writeTo writes MASSSPECTRUM, MS1SPECTRUM and MSNSPECTRUM all as "MassScan" or "Zoom" (:882-893), and the reader maps both to MASSSPECTRUM. An mzML "MSn spectrum" (MS:1000580, MzMLHandler.cpp:1587) or "MS1 spectrum" therefore still comes back from mzData as MASSSPECTRUM and is rewritten as MS:1000294 "mass spectrum" (MzMLHandler.cpp:5303-5313). That is far more common than ABSORPTION, EMC or TDF. (3) upstream_patch: "cut the section down to the scan-mode cases with a complete m/z and intensity pair" needs a new intensity fixture. The existing `intensity` string is deliberately shorter than `mz` (1 value against 2), so the EMC and PhotodiodeArrayDetector cases read out of bounds without CPP-170. The "unknown" and TDF cases (a single array, or an empty <intenArrayBinary/>) also read precisions_[1] out of bounds. (4) The MSn fallback still logs nothing, as the draft notes. Behaviour-change claims check out: the upstream test data uses only MassScan, SelectedIonDetection and Zoom, so no reference output changes.
- **Upstream patch:** Both handler hunks apply cleanly: origin/develop (3cee4c0c25) MzDataHandler.cpp is byte-identical to core-v4.0.0-ci.2, so the defect is still upstream. The test section is shared with CPP-170. Submit the two together, or cut the section down to the scan-mode cases with a complete m/z and intensity pair.
- **Skeptic's notes:** Verified at origin/develop: writer :919-929, reader list :1089-1131, fallback :1134-1142, spec_ reset at :343 and appended at :446-450. The MS-level skip at :397-400 returns before cvParam_ (:214-217, :253-258). MzDataFile::load calls map.reset(), which keeps capacity, and spectrumList count calls MSExperiment::reserve, which reserves spectra_, so with count>=1 the write lands just before a live heap buffer. The round-trip trigger holds: an MS1 spectrum with UNKNOWN scan mode gets no cvParam (:878-880), so the following MS2 TDF spectrum sets MSNSPECTRUM on it and itself stays UNKNOWN. 181dadf and b2079fb are in both ci.3 and ci.4.

**Decision (provisional: recommended default, not yet confirmed; overrule here):** Keep the fix; leave the MS1/MSn spectrum-type round trip through mzData as a documented limitation of the legacy format. Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-173"></a>
## CPP-173: mzXML release decode reads beyond short peak payload

**When an mzXML scan's peaksCount is larger than its decoded peak payload, release builds read past the end of the decoded vector.**

- **Mechanism:** All line numbers are for origin/develop; MzXMLHandler.cpp/.h are identical to ci.2. - MzXMLHandler.cpp:301 `spectrum_data_.back().peak_count_ = attributeAsInt_(attributes, s_peakscount_);` stores the file's attribute in SpectrumData::peak_count_, which is a UInt (MzXMLHandler.h:120). - :302 reserves peak_count_/2+1 peaks from the same attribute. - In doPopulateSpectraWithData_ (:1148), only an empty payload is skipped (:1153). After base64 decoding (and zlib, if set), the only length check is `assert(data.size() == 2 * spectrum_data.peak_count_);` at :1175 (64-bit) and :1202 (32-bit). NDEBUG release builds compile that out. - The loops at :1177 and :1204 run `for (Size n = 0; n < (2 * spectrum_data.peak_count_); n += 2)` and read data[n] and data[n + 1]. - peaksCount="-1" wraps to 4294967295. 2*peak_count_ is computed in 32-bit unsigned arithmetic and wraps to 4294967294, and :302 asks for about 2.1e9 Peak1D, roughly 34 GB. - Decoding runs in an OpenMP loop (:1224-1247) whose catch(...) turns exceptions into a ParseError, but an out-of-bounds read raises none.
- **Trigger:** `<scan num="1" msLevel="1" peaksCount="2" retentionTime="PT1S"><peaks precision="32" byteOrder="network" contentType="m/z-int">QvAAAELIAAA=</peaks></scan>`: the payload holds one pair (m/z 120, intensity 100). - Release build: 2 peaks load, and the second is built from bytes past the vector. - Debug build: the assert aborts the process. - peaksCount="-1": the 34 GB reserve throws OutOfMemory on most machines. Where the allocation succeeds, the loop runs billions of steps past the vector; a scratch NDEBUG build crashed with SIGBUS. - peaksCount smaller than the payload (e.g. "0" with one pair): release builds silently drop peaks.
- **Consequence:** Heap out-of-bounds read in release builds. Made-up peaks with garbage m/z and intensity silently enter the spectrum and flow into downstream analysis, or the tool crashes. A peaksCount below the payload silently truncates the spectrum. Debug builds abort the whole process.
- **Who hits it:** MzXMLFile::load and transform, FileHandler .mzXML loading in every TOPP tool that reads spectra, and pyOpenMS MzXMLFile (bind_misc.cpp). mzXML is still widely used (msconvert, TPP). Files from msconvert, ReAdW and OpenMS's own writer, which writes peaksCount = spec.size() (:891), always match their payload. Empty scans use a nil payload, which is skipped before the loop; both upstream peaksCount="0" files are like that. Correct files therefore never trigger it. Triggers are corrupt, hand-edited or script-filtered files and non-conforming writers. Uncommon, but the input comes straight from user files and the effect is silent in release builds.

> **Skeptic's correction:** (a) Reach says "both upstream peaksCount="0" files". There are three: src/pyOpenMS/tests/test.mzXML and src/pyOpenMS/tests/unittests/test.mzxML (identical blobs) and src/tests/topp/FileConverter_6_output.mzXML. All have empty payloads. A script check finds no scan in any of the 22 upstream mzXML files whose payload disagrees with peaksCount. (b) behavior_change overstates the new strictness. The length check only runs for a non-empty payload; an empty payload with any peaksCount of 0 or more still returns early (:1198-1201 at ci.4). So "a scan whose decoded length differs from 2 x peaksCount, in either direction, now fails" applies only to scans that carry peak data. (c) The negative-peaksCount check runs after the MS-level, RT and LD_RAWCOUNTS skip (:285-291), so a negative count on a filtered scan still loads. It also runs when fill-data is off, so a negative count with an empty payload, or in a no-data load, now fails where it used to load with zero peaks. (d) upstream_patch: the prefix's split msInstrument comment does not need CPP-174 for the peaksCount loop to pass (the old reader just keeps the last chunk). Only the first-half precursorMz and comment assertions need CPP-174. A plain prefix is still cleaner.

### The fix

181dadf replaces both asserts with a runtime check (line numbers at 4f5c86f). expected_values = 2 * static_cast<Size>(peak_count_) is computed in 64 bits, so it cannot wrap (1207-1219). If the decoded length differs, fatalError(LOAD, ...) logs the scan's native ID and throws ParseError. The OpenMP loop catches it and throws ParseError for the whole load. The loops now run to data.size() (1234-1236, 1261-1263). c77ff14 (the core-v4.0.0-ci.3 tag commit) followed after the hosted Linux and Windows runners ran out of memory on the "-1" test. It rejects a negative peaksCount with fatalError at the scan start tag (309-313) and caps the peak reserve at 1e5 (314-317). It also caps the msRun scanCount reserve at 1e5 and clamps negative values to 0 (135-136); that is related hardening, not the out-of-bounds fix. #include <algorithm> is added at line 15. Regression test (b2079fb): MzXMLFile_test section "regression : SAX chunk boundaries and mismatched peak counts". The CPP-173 part loops over peaksCount "2", "0" and "-1" with a one-pair payload and expects Exception::ParseError. The first half of the section tests CPP-174.

*State:* Released in 4f5c86f (core-v4.0.0-ci.4): 181dadf (runtime length check), c77ff14 (negative peaksCount rejected, bounded reserves; tagged ci.3) and b2079fb (test) are ancestors of 4f5c86f. Not reverted.

**Fix:** `src/openms/source/FORMAT/HANDLERS/MzXMLHandler.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FORMAT/HANDLERS/MzXMLHandler.cpp
+++ b/src/openms/source/FORMAT/HANDLERS/MzXMLHandler.cpp
@@ -12,6 +12,7 @@
 #include <OpenMS/INTERFACES/IMSDataConsumer.h>
 #include <OpenMS/FORMAT/Base64.h>
 
+#include <algorithm>
 #include <atomic>
 #include <stack>
 #include <xercesc/util/XMLString.hpp>
@@ -297,9 +306,15 @@ namespace OpenMS::Internal
         spectrum_data_.back().spectrum.setMSLevel(ms_level);
         spectrum_data_.back().spectrum.setRT(retention_time);
         spectrum_data_.back().spectrum.setNativeID(std::string("scan=") + attributeAsString_(attributes, s_num_));
-        //peak count == twice the scan size
-        spectrum_data_.back().peak_count_ = attributeAsInt_(attributes, s_peakscount_);
-        spectrum_data_.back().spectrum.reserve(spectrum_data_.back().peak_count_ / 2 + 1);
+        const Int peak_count = attributeAsInt_(attributes, s_peakscount_);
+        if (peak_count < 0)
+        {
+          fatalError(LOAD, std::string("Scan '") + spectrum_data_.back().spectrum.getNativeID() + "' declares peaksCount=" + peak_count + ".");
+        }
+        spectrum_data_.back().peak_count_ = peak_count;
+        // peaksCount is only checked against the decoded payload later, so it must not size an allocation
+        // directly: a corrupt count has to fail as a ParseError, not as OutOfMemory on a smaller machine.
+        spectrum_data_.back().spectrum.reserve(std::min(Size(1e5), static_cast<Size>(peak_count)));
         spectrum_data_.back().spectrum.setDataProcessing(data_processing_);
 
         //centroided, chargeDeconvoluted, deisotoped, collisionEnergy are ignored
@@ -1159,6 +1204,20 @@ namespace OpenMS::Internal
       //this should not be necessary, but line breaks inside the base64 data are unfortunately no exception
       StringUtils::removeWhitespaces(spectrum_data.char_rest_);
 
+      // peaksCount is read from the file, so the decoded length must be checked at runtime before the
+      // loops below index the values: an assert is compiled out of release builds, which then read past
+      // a payload that is shorter than declared.
+      const Size expected_values = 2 * static_cast<Size>(spectrum_data.peak_count_);
+      auto checkDecodedValues = [&](const Size decoded_values)
+      {
+        if (decoded_values != expected_values)
+        {
+          fatalError(LOAD, std::string("The peaks of scan '") + spectrum_data.spectrum.getNativeID() + "' decode to "
+                           + decoded_values + " values, but peaksCount=" + spectrum_data.peak_count_ + " requires "
+                           + expected_values + ".");
+        }
+      };
+
       if (spectrum_data.precision_ == "64")
       {
         std::vector<double> data;
@@ -1172,9 +1231,9 @@ namespace OpenMS::Internal
         }
         spectrum_data.char_rest_ = "";
         PeakType peak;
-        assert(data.size() == 2 * spectrum_data.peak_count_);
+        checkDecodedValues(data.size());
         //push_back the peaks into the container
-        for (Size n = 0; n < (2 * spectrum_data.peak_count_); n += 2)
+        for (Size n = 0; n < data.size(); n += 2)
         {
           // check if peak in in the specified m/z  and intensity range
           if ((!options_.hasMZRange() || options_.getMZRange().encloses(DPosition<1>(data[n])))
@@ -1199,9 +1258,9 @@ namespace OpenMS::Internal
         }
         spectrum_data.char_rest_ = "";
         PeakType peak;
-        assert(data.size() == 2 * spectrum_data.peak_count_);
+        checkDecodedValues(data.size());
         //push_back the peaks into the container
-        for (Size n = 0; n < (2 * spectrum_data.peak_count_); n += 2)
+        for (Size n = 0; n < data.size(); n += 2)
         {
           if ((!options_.hasMZRange() || options_.getMZRange().encloses(DPosition<1>(data[n])))
              && (!options_.hasIntensityRange() || options_.getIntensityRange().encloses(DPosition<1>(data[n + 1]))))
```

**Test:** `src/tests/class_tests/openms/source/MzXMLFile_test.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/tests/class_tests/openms/source/MzXMLFile_test.cpp
+++ b/src/tests/class_tests/openms/source/MzXMLFile_test.cpp
@@ -12,10 +12,11 @@
 
 ///////////////////////////
 
-#include <OpenMS/FORMAT/MzXMLFile.h>
 #include <OpenMS/FORMAT/FileTypes.h>
+#include <OpenMS/FORMAT/MzXMLFile.h>
 #include <OpenMS/KERNEL/MSExperiment.h>
 #include <OpenMS/KERNEL/StandardTypes.h>
+#include <fstream>
 
 using namespace OpenMS;
 using namespace std;
@@ -646,6 +647,47 @@ END_SECTION
 
 /////////////////////////////////////////////////////////////
 /////////////////////////////////////////////////////////////
+START_SECTION((regression : SAX chunk boundaries and mismatched peak counts))
+{
+  MzXMLFile file;
+  std::string input;
+  NEW_TMP_FILE(input)
+  const std::string prefix = "<?xml version=\"1.0\"?><mzXML><msRun scanCount=\"1\">"
+                             "<msInstrument><comment>Instr<!-- split -->ument <![CDATA[Comment]]></comment></msInstrument>";
+  const std::string suffix = "</scan></msRun></mzXML>";
+  std::ofstream(input) << prefix
+                       << "<scan num=\"1\" msLevel=\"2\" peaksCount=\"1\" retentionTime=\"PT1S\">"
+                          "<precursorMz precursorIntensity=\"5\" windowWideness=\"10\">12<!-- split -->3.<![CDATA[45]]></precursorMz>"
+                          "<peaks precision=\"32\" byteOrder=\"network\" contentType=\"m/z-int\">QvAAAELIAAA=</peaks>"
+                          "<comment>Scan<!-- split --> Comment</comment>"
+                       << suffix;
+  PeakMap result;
+  file.load(input, result);
+  TEST_EQUAL(result.size(), 1)
+  ABORT_IF(result.size() != 1)
+  TEST_EQUAL(result[0].getPrecursors().size(), 1)
+  ABORT_IF(result[0].getPrecursors().size() != 1)
+  TEST_REAL_SIMILAR(result[0].getPrecursors()[0].getMZ(), 123.45)
+  TEST_REAL_SIMILAR(result[0].getPrecursors()[0].getIsolationWindowLowerOffset(), 5.0)
+  TEST_REAL_SIMILAR(result[0].getPrecursors()[0].getIsolationWindowUpperOffset(), 5.0)
+  TEST_STRING_EQUAL(result[0].getComment(), "Scan Comment")
+  TEST_STRING_EQUAL(result.getInstrument().getMetaValue("#comment").toString(), "Instrument Comment")
+
+  for (const std::string count : {"2", "0", "-1"})
+  {
+    std::string malformed;
+    NEW_TMP_FILE(malformed)
+    std::ofstream(malformed) << prefix << "<scan num=\"1\" msLevel=\"1\" peaksCount=\"" << count
+                             << "\" retentionTime=\"PT1S\"><peaks precision=\"32\" byteOrder=\"network\" contentType=\"m/z-int\">QvAAAELIAAA=</peaks>"
+                             << suffix;
+    TEST_EXCEPTION(Exception::ParseError, file.load(malformed, result))
+    File::remove(malformed);
+  }
+  // Deliberately incomplete reader fixtures are excluded from writer-schema checks.
+  File::remove(input);
+}
+END_SECTION
+
 /// check the temporary files written above against their XML schema (types without a validator are skipped)
 VALIDATE_TMP_FILES
 
```

### Assessment

- **Behaviour change:** None for valid files, where peaksCount equals the number of decoded pairs or the payload is empty. Stricter on malformed files: a scan whose decoded length differs from 2 x peaksCount, in either direction, now fails the entire load with ParseError, and a negative peaksCount fails at the scan tag. Before, release builds read out of bounds when peaksCount was too large and silently truncated when it was too small, so files of the second kind that used to load in release builds now do not load at all. The reserve caps only change allocation for scans with more than 100000 peaks and runs with more than 100000 scans.
- **Concerns:** (1) All or nothing. One inconsistent scan makes the whole file unloadable, with no option to skip it. Inside the parallel decode the specific message (scan ID, counts) is only logged (XMLHandler.cpp:67), and the exception the caller sees says "Error during parsing of binary data." (:1246). (2) Third-party files with peaksCount smaller than the payload, which release builds used to load truncated, now fail. No such file is in the upstream test data. (3) The msRun scanCount reserve cap is related hardening bundled in c77ff14 and could be split off. (4) The fix agrees with the Rust port, which also rejects the mismatch.
- **Skeptic on the fix (yes):** (1) Hunk 135-136 is c77ff14's msRun scanCount reserve cap. The draft itself calls it unrelated to the out-of-bounds fix, so it should not be a hunk here. Keep line 15 (#include <algorithm>), which the std::min at 317 needs. (2) The test hunks do not compile on their own. The loop at 676-685 calls file.load(malformed, result), but `PeakMap result;` is declared at 664, which no hunk covers. The section's end (686-689: File::remove(input), closing brace, END_SECTION) is also missing, although its start (650-651) is included. (3) Test hunk 14-19 includes a cosmetic swap of the FileTypes and MzXMLFile includes. Only <fstream> at 19 is needed. (4) Behaviour: a ParseError inside the OpenMP decode fails the whole file, and its detailed message is only logged (XMLHandler.cpp:67-68, caught at :1238-1246), as the draft says. No upstream test file changes behaviour. The code closes the out-of-bounds read: data.size() must equal 2*peaksCount (computed in 64 bits) before a loop that now runs to data.size(), and fatalError always throws. It applies upstream; MzXMLHandler.cpp/.h and MzXMLFile_test.cpp are byte-identical at origin/develop.
- **Upstream patch:** The handler hunks apply cleanly: origin/develop (3cee4c0c25) MzXMLHandler.cpp, MzXMLHandler.h and MzXMLFile_test.cpp are byte-identical to core-v4.0.0-ci.2, so the defect is still upstream. The test section is shared with CPP-174: its first half and the prefix string exercise SAX-chunked precursorMz and comment text, which needs CPP-174's handler changes. A CPP-173-only patch should cut the test down to the peaksCount loop with a plain prefix. Cases "2" and "0" need only the 181dadf check. Case "-1" also needs c77ff14 to fail as ParseError rather than OutOfMemory on machines that refuse the 34 GB reserve.
- **Skeptic's notes:** Verified at origin/develop: SpectrumData::peak_count_ is a UInt (MzXMLHandler.h:120); :301-302 take peaksCount unchecked; the asserts at :1175 and :1202 are the only guard; the loops at :1177 and :1204 bound on 2*peak_count_ in unsigned int arithmetic; empty payloads are skipped at :1153; the writer emits peaksCount=spec.size() at :891. The c77ff14 commit message confirms the "-1" OutOfMemory on hosted runners. The SIGBUS from a scratch build could not be re-checked. P0 holds: a heap out-of-bounds read from input files that silently makes up peaks in release builds.

**Decision (confirmed 2026-09-14):** Rework: bound each scan to the decoded peaks and log the scan id and counts instead of failing the whole file. Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-005"></a>
## CPP-005: Truncated fragment distribution is indexed at full input length

**If a CoarseIsotopePatternGenerator has a nonzero max_isotope that is shorter than the fragment distribution, the fragment isotope calculation writes past the end of its truncated result vector.**

- **Mechanism:** Paths are at origin/develop, in src/openms/source/CHEMISTRY/ISOTOPEDISTRIBUTION/CoarseIsotopePatternGenerator.cpp, function calcFragmentIsotopeDist_ (:450). - :461-466 set r_max = fragment_isotope_dist.size(), capped to max_isotope_ when that is nonzero. - :469 resizes the result to r_max. - The accumulation loop at :509 still runs `for (Size i = 0; i < fragment_isotope_dist.size(); ++i)`. It reads and writes result[i] at :516 and :519. - IsotopeDistribution::operator[] does no bounds check (IsotopeDistribution.h:198). So every index from r_max to size-1 is a heap read and write past the end of the vector. The public entry points make this easy to hit. estimateForFragmentFromWeightAndComp (:284-304) builds both distributions with an internal `solver(max_depth, false)`, where max_depth = max(precursor_isotopes)+1 (:286, :289). It then calls this->calcFragmentIsotopeDist (:301 -> :308), which truncates with the outer object's own max_isotope_. estimateForFragmentFromPeptideWeightAndS (:199, :205, :215) and EmpiricalFormula::getConditionalFragmentIsotopeDist (EmpiricalFormula.cpp:205, :210-213, which uses the caller's solver) work the same way. The generator run() truncates to its own max_isotope (convolve, :331-336), so the internal distributions really are max_depth peaks long.
- **Trigger:** C++: `CoarseIsotopePatternGenerator gen(2); gen.estimateForFragmentFromPeptideWeight(2000.0, 1000.0, {0,1,2});` pyOpenMS: `pyopenms.CoarseIsotopePatternGenerator(2).estimateForFragmentFromPeptideWeight(2000.0, 1000.0, {0,1,2})`. The internal solver(3) yields a 3-peak fragment distribution. The outer max_isotope 2 sizes the result to 2 elements, and the loop then reads and writes result[2]. Also triggered by EmpiricalFormula.getConditionalFragmentIsotopeDist(precursor, {0,1,2}, CoarseIsotopePatternGenerator(2)), and by calcFragmentIsotopeDist on distributions longer than the generator's nonzero max_isotope.
- **Consequence:** Out-of-bounds heap read and write of (fragment length - r_max) Peak1D slots, 16 bytes each, just past a buffer of r_max elements. This is undefined behaviour. Typically it silently corrupts the neighbouring heap chunk, which can later abort inside the allocator or damage unrelated data. AddressSanitizer would report a heap-buffer-overflow. The r_max values actually returned are computed correctly, so the scientific result is not wrong; the danger is memory corruption.
- **Who hits it:** API only: C++ and pyOpenMS. The bindings are bind_chemistry.cpp:372-377 (calcFragmentIsotopeDist and the five estimateForFragmentFrom* methods) and :654 (EmpiricalFormula.getConditionalFragmentIsotopeDist). No TOPP tool or library algorithm calls these functions at origin/develop. The default max_isotope is 0 (CoarseIsotopePatternGenerator.h:84), which never truncates. A user therefore has to set a nonzero max_isotope below max(precursor_isotopes)+1, or below the length of the distributions passed in. That is a natural choice for someone who limits isotope peaks, but the fragment-isotope API itself is niche. Likelihood: low. The existing class tests never take this path. Every fragment section calls setMaxIsotope(0) first (CoarseIsotopeDistribution_test.cpp at 4f5c86f: 608, 669, 688). The setMaxIsotope(2) calls at 593 and 642 come after the fragment call and only affect estimateFrom*Weight.

> **Skeptic's correction:** No factual errors in the core claim; the trigger holds at origin/develop. Minor fixes: - Test-line citation is incomplete. The fragment sections that call setMaxIsotope(0) first are at 360 (PeptideWeightAndS), 477 (PeptideWeight), 559 (DNA), 608 (RNA), 669 and 688 (calcFragmentIsotopeDist). The draft cites only 608, 669 and 688. EmpiricalFormula_test.cpp:494-570 only passes CoarseIsotopePatternGenerator() or (0,true), so it never truncates either. - 'getConditionalFragmentIsotopeDist ... uses the caller's solver' needs sharpening. It builds both input distributions with a fresh CoarseIsotopePatternGenerator(max_depth) (EmpiricalFormula.cpp:210-211) and uses the caller's solver only for the truncating calcFragmentIsotopeDist call (:213). The EmpiricalFormula trigger also needs a fragment with at least max_depth isotope peaks; a formula such as 'C' has only 2. - Consequence detail: each stray iteration reads and writes the 4-byte float intensity at offset 8 of a 16-byte Peak1D slot, not the whole slot. The IsotopeDistribution default constructor emplaces one peak (IsotopeDistribution.cpp:35). resize(r_max) on that leaves capacity exactly r_max on both libstdc++ and libc++, so result[r_max] is past the allocation itself, not only past size(). - fix_state: 1beb468 first shipped in core-v4.0.0-ci.3 (tag commit c77ff14) and was kept in ci.4 (4f5c86f). 'Released in 4f5c86f' is true but leaves out that ci.3 already had the fix.

### The fix

Commit 1beb468 bounds the accumulation loop by r_max instead of by the input length: `for (Size i = 0; i < r_max; ++i)`, with a two-line comment. The complementary-index check is unchanged. Since r_max <= fragment_isotope_dist.size(), fragment_isotope_dist[i] also stays in bounds.

*State:* Released in 4f5c86f. Fix commit 1beb468 (part of the first tranche of review fixes). The ci.4 reverts in 23944b6 did not touch it. No regression test was added: CoarseIsotopeDistribution_test.cpp is unchanged between ci.2 and 4f5c86f.

**Fix:** `src/openms/source/CHEMISTRY/ISOTOPEDISTRIBUTION/CoarseIsotopePatternGenerator.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/CHEMISTRY/ISOTOPEDISTRIBUTION/CoarseIsotopePatternGenerator.cpp
+++ b/src/openms/source/CHEMISTRY/ISOTOPEDISTRIBUTION/CoarseIsotopePatternGenerator.cpp
@@ -506,7 +506,9 @@ namespace OpenMS
     //
     // normalization is needed to get true conditional probabilities if desired.
     //
-    for (Size i = 0; i < fragment_isotope_dist.size(); ++i)
+    // max_isotope_ truncates the result to r_max entries, so the accumulation has to stop
+    // there too: iterating over the full input wrote past the end of the result container.
+    for (Size i = 0; i < r_max; ++i)
     {
       for (std::set<UInt>::const_iterator precursor_itr = precursor_isotopes.begin(); precursor_itr != precursor_isotopes.end(); ++precursor_itr)
       {
```

### Assessment

- **Behaviour change:** None for valid input. - Untruncated case (max_isotope 0, or at least the fragment length): r_max equals the fragment length, so the loop is identical. - Truncated case: iterations i < r_max compute exactly as before. The removed iterations only wrote outside the returned vector. Outputs, accepted inputs and exceptions are unchanged; only the undefined behaviour is gone.
- **Concerns:** - No regression test. None exercises max_isotope smaller than the fragment distribution, with or without a sanitizer. - Adjacent issue, not covered by this fix: estimateForFragmentFromPeptideWeightAndS (:199), estimateForFragmentFromWeightAndComp (:286) and EmpiricalFormula::getConditionalFragmentIsotopeDist (EmpiricalFormula.cpp:205) dereference std::max_element over precursor_isotopes. With an empty set that dereferences end(), which is undefined behaviour. The Rust report's suggested regression list mentions empty precursor selections. - Semantics are unchanged: results are still truncated to the outer generator's max_isotope, even though the inputs were computed at max(precursor_isotopes)+1. That looks intended, but it is undocumented.
- **Skeptic on the fix (yes):** None beyond what the draft lists. - The r_max bound also keeps fragment_isotope_dist[i] in range. convolve and convolveSquare_ already stop at r_max through their min(r_max - i, ...) inner bounds, so no sibling loop in the class has the same overrun. - Still unaddressed and pre-existing, as the draft says: *max_element on an empty precursor_isotopes set at CoarseIsotopePatternGenerator.cpp:199 and :286 and EmpiricalFormula.cpp:205. - No regression test in any Core commit between ci.2 and 4f5c86f. I grepped the test diffs of 1beb468, 181dadf, b6dd412, 9b56872 and the later commits; none adds a truncating fragment test.
- **Upstream patch:** Applies verbatim. CoarseIsotopePatternGenerator.cpp at origin/develop is byte-identical to core-v4.0.0-ci.2; the loop is at line 509. A pull request upstream should add a regression test, for example gen(2).estimateForFragmentFromPeptideWeight(2000, 1000, {0,1,2}) under ASan, or a check of result size and values.
- **Skeptic's notes:** Verified at origin/develop, byte-identical to ci.2. - :461-469 size the result to min(size, max_isotope_); the loop at :509 runs to fragment_isotope_dist.size(); IsotopeDistribution.h:198 does no bounds check. - The internal solver(max_depth, false) at :205 and :289 truncates via convolve (:333-336), so gen(2).estimateForFragmentFromPeptideWeight(2000,1000,{0,1,2}) builds 3-peak inputs, sizes the result to 2, and touches result[2]. - pyOpenMS reach confirmed: bind_chemistry.cpp:371 (init with max_isotope), :372-377 and :654. nanobind/stl/set.h is included via type_casters/all_casters.h:18, so a Python set converts. - Only in-tree caller is EmpiricalFormula::getConditionalFragmentIsotopeDist; no TOPP or library callers. - Hunk 509-511 at 4f5c86f matches the diff exactly (two comment lines plus the new loop header). - P0 per rubric: heap out-of-bounds write through documented public API with valid, non-default arguments.

**Decision (confirmed 2026-09-14):** Keep the fix; add a regression test (truncating max_isotope below the fragment length). Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-011"></a>
## CPP-011: Mass trace detection reuses stale metadata-array state

**Reusing one MassTraceDetection object keeps the previous run's float-data-array flags and indices, so a later run on spectra without those arrays reads arrays that are not there.**

- **Mechanism:** Paths are at origin/develop. - The metadata state lives in detector members, initialised only once: MassTraceDetection.h:182-184 (has_fwhm_mz_, has_fwhm_im_, has_centroid_im_ = false) and :203-205 (fwhm_meta_idx_, ion_mobility_idx_, im_fwhm_idx_ = -1). - Every run() reaches run_, which calls getIMIndices_ with these members (MassTraceDetection.cpp:482-485). - getIMIndices_ (:80-144) sets an index and flag only when it finds an array (:96-110). It never clears them. - Its consistency check validate_meta_array (:116-138) counts spectra whose array at the (possibly stale) index has the expected name. It throws only if 0 < count < spectra (:133), so zero matches passes. The stale flags then drive unchecked reads of getFloatDataArrays()[stale_idx]: - apex ion mobility at :520 and :523 - apex FWHM values at :530 and :531 - candidate search at :326 - trace extension in processPeak_ at :430 and :434 The input copy at :256-258 keeps whatever float arrays the second input has, which may be none.
- **Trigger:** Use one detector object for two runs. Run 1: at least 3 MS1 centroided spectra carrying a FWHM_ppm float array (PeakPickerHiRes with report_FWHM) or an ion-mobility array (PeakPickerIM output). Run 2, same object: MS1 spectra without float arrays, for example a vendor-centroided mzML. In pyOpenMS: `mtd = MassTraceDetection(); mtd.run(exp_with_fwhm, ...); mtd.run(exp_plain, ...)`. Silent variant: run 1 has arrays [IonMobility, FWHM_ppm]; run 2 has only [FWHM_ppm]. The FWHM index is updated to 0, but the stale ion-mobility index 0 now points at the FWHM array. Validation passes because no spectrum has an IonMobility array at index 0.
- **Consequence:** Main case: run 2 indexes an empty float-array vector at the stale index, then indexes into whatever garbage it gets back. That is an out-of-bounds read and in practice usually a segmentation fault; with pyOpenMS the Python process dies. Silent variant: FWHM ppm values are used as ion mobility. The ion-mobility window test (:369-377) and the candidate search (:324-330) then accept or reject the wrong peaks. Mass traces and their IM centroid and FWHM metadata come out wrong with no error. The public getters hasFwhmMz(), hasFwhmIm() and hasCentroidIm() (header :79-81) also report stale values.
- **Who hits it:** Not reachable from TOPP tools. Every in-tree caller constructs a fresh detector per invocation: FeatureFinderMetabo.cpp:129, MassTraceExtractor.cpp:178, DDAWorkflowCommons.cpp:110, MassFeatureTrace.cpp:91 and PeakPickerIM.cpp:1266. Reachable from C++ and pyOpenMS (bind_misc.cpp:3085 run) when one configured object is reused across inputs that differ in their float data arrays. Reusing an algorithm object in a script loop is common. Mixing inputs with and without FWHM or ion-mobility arrays in one loop is less common. Likelihood: low to moderate for scripting users, none for TOPP users.

> **Skeptic's correction:** - The trigger example 'or an ion-mobility array (PeakPickerIM output)' is wrong. - PeakPickerIM names its IM array Constants::UserParam::ION_MOBILITY_CENTROID = "Ion Mobility Centroid" and deletes every other float array (PeakPickerIM.cpp:1225/1228, 1321/1324). - getIMIndices_ looks for the exact name ION_MOBILITY = "Ion Mobility" (MassTraceDetection.cpp:93, Constants.h:251). getDataArrayByName compares names exactly (SpectrumHelper.h:32). - So PeakPickerIM output never sets has_centroid_im_. The IM path needs an array named exactly "Ion Mobility", e.g. Mobi-DIK-style exports (IMDataArrayUtils.cpp:70) or Biosaur2's internal centroiding (Biosaur2Algorithm.cpp:1159). - The FWHM_ppm route is valid: PeakPickerHiRes report_FWHM with the default relative unit names the array "FWHM_ppm" (PeakPickerHiRes.cpp:144). The IM-FWHM array name is "IM Peak FWHM". - In the silent variant, 'IonMobility' must be exactly "Ion Mobility". - The draft misses a more realistic silent variant: run 1 on PeakPickerHiRes report_FWHM output ([FWHM_ppm] at index 0), then run 2 on PeakPickerIM output ([Ion Mobility Centroid] at index 0, same length as the peaks). The stale has_fwhm_mz_ and index 0 pass validation (zero name matches), so IM centroid values are read as FWHM ppm (:430, :530). The medians written to MassTrace::fwhm_mz_avg (:666) are silently wrong, with no crash. - Main-case consequence: a spectrum copied without float arrays has an empty vector with a null data pointer. getFloatDataArrays()[stale_idx][peak] therefore dereferences near-null memory, a near-deterministic segfault (or abort under a hardened STL), not a 'garbage' read. It also needs run 2 to produce at least one apex above noise_threshold_int*chrom_peak_snr (:248); otherwise no read happens. - The header difference is one line replaced by a comment plus [[maybe_unused]]; trivial, but not 'one line'.

### The fix

Commit 1beb468 resets all three indices to -1 and all three flags to false at the top of getIMIndices_, before discovery: `fwhm_meta_idx = im_idx = im_fwhm_idx = -1; has_fwhm_mz = has_centroid_im = has_fwhm_im = false;`. A comment explains why. Every run therefore starts from the same state as a freshly constructed detector.

*State:* Released in 4f5c86f. Fix commit 1beb468; the ci.4 reverts in 23944b6 did not touch it. No regression test was added: MassTraceDetection_test.cpp is unchanged between ci.2 and 4f5c86f.

**Fix:** `src/openms/source/FEATUREFINDER/MassTraceDetection.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FEATUREFINDER/MassTraceDetection.cpp
+++ b/src/openms/source/FEATUREFINDER/MassTraceDetection.cpp
@@ -84,6 +84,12 @@ namespace OpenMS
       int& im_fwhm_idx, bool& has_fwhm_im
     ) const
     {
+      // Reset first: these are members of the detector, and a second run over spectra
+      // without the arrays would otherwise keep the previous run's flags and indices and
+      // read a float data array that is not there.
+      fwhm_meta_idx = im_idx = im_fwhm_idx = -1;
+      has_fwhm_mz = has_centroid_im = has_fwhm_im = false;
+
       for (const auto& spec : spectra)
       {
         const auto& fda = spec.getFloatDataArrays();
```

### Assessment

- **Behaviour change:** None for a freshly constructed detector, and none for repeated runs over inputs with the same arrays at the same positions. Only reuse across inputs with different arrays changes, from a crash or silently wrong ion-mobility handling to the result a fresh detector would give. The getters now describe the latest run.
- **Concerns:** - No regression test. The Rust report proposed repeated runs with arrays, without arrays, and with the array order changed. - Flags are still stored before validate_meta_array runs. If validation throws, or run() throws InvalidValue for fewer than 3 MS1 spectra (:263-267, before run_ is reached), the getters keep partial or previous values until the next run. That is not a memory-safety problem, because the next run resets first. - Pre-existing and unchanged: mutable members are modified inside a const function, so concurrent runs on one object are still unsafe.
- **Skeptic on the fix (yes):** None material. - After the reset, validate_meta_array accepting zero matches becomes harmless: any discovered index matches at least the first spectrum with arrays. So the fix also closes the silent stale-name variants, not only the crash. - The draft's residual note is accurate: getters keep the previous run's values if run() throws InvalidValue (fewer than 3 MS1 spectra, :263-267) before run_ (:283), or partial values if validation throws. - No behaviour change for fresh detectors, no API change, negligible cost. - No regression test: MassTraceDetection_test.cpp is identical at origin/develop, ci.2 and 4f5c86f, and no review commit adds one elsewhere.
- **Upstream patch:** Applies verbatim. MassTraceDetection.cpp at origin/develop is byte-identical to core-v4.0.0-ci.2; the insertion point is the top of getIMIndices_ at line 86. The header differs by one unrelated line (mass_error_da_ marked [[maybe_unused]] in Core) that the fix does not touch. An upstream pull request should add a two-run test.
- **Skeptic's notes:** Verified at origin/develop, byte-identical to ci.2. - getIMIndices_ (:80-144) only ever sets state. - The members are initialised once (header :182-184, :203-205) and passed to getIMIndices_ from run_ (:482-485). - Unchecked reads: :326, :430, :434, :520, :523, :530, :531. - All in-tree callers build a fresh detector per call: FeatureFinderMetabo.cpp:129, MassTraceExtractor.cpp:178, DDAWorkflowCommons.cpp:110, MassFeatureTrace.cpp:91, PeakPickerIM.cpp:1266 (constructed inside the per-frame function). - pyOpenMS: bind_misc.cpp:3085 run(input, max_traces), same object reusable. - Hunk 87-92 at 4f5c86f matches the six added lines. - P0 holds under the rubric: an out-of-bounds read via ordinary reuse of a DefaultParamHandler algorithm object, plus silent wrong IM and FWHM results.

**Decision (confirmed 2026-09-14):** Keep the fix; add a regression test (one detector reused across inputs with different arrays). Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-055"></a>
## CPP-055: Base64 SIMD decoding does not validate its alphabet

**The numeric Base64 decoders never check that the input uses only Base64 characters. Corrupt array data decodes to garbage numbers, and the integer decoder reads outside its lookup table and past the end of the string.**

- **Mechanism:** Float path: origin/develop src/openms/include/OpenMS/FORMAT/Base64.h:309-346 decodeUncompressed_ checks only `in.size() < 4` and `% 4 != 0`, then calls stringSimdDecoder_ (Base64.cpp:166-208). registerDecoder_ (Base64.cpp:80-114) classifies bytes by upper bounds only; for example :95 treats everything below '9'+1 as a digit. So '!', '=', spaces and UTF-8 bytes (negative as signed char) each become some 6-bit value. There is no out-of-bounds access on this path, but also no error. Integer path: decodeIntegersUncompressed_ (Base64.h:506ff.) checks only `in.size() < 4` (:513-516), with no multiple-of-4 check. It looks up the static 81-byte table decoder_ (Base64.cpp:211) as `decoder_[(int)in[i] - 43]` at :561, :562, :590 and :618 without a range check: - a byte below '+' gives a negative index ('!' gives -10; a UTF-8 byte as signed char goes down to -171) - a byte above '{' reads past the end ('|' gives 81) - an unpadded length that is not a multiple of 4 makes the loop read in[i+1..i+3] beyond size() The compressed paths (decodeCompressed_ :276-307, decodeIntegersCompressed_ :410-423) pass the string unchecked to decodeSingleString and then stringSimdDecoder_, so invalid bytes become garbage that zlib usually rejects. The code is identical at core-v4.0.0-ci.2.
- **Trigger:** An mzML binaryDataArray with MS:1000519 (32-bit integer), no compression, and <binary>AAAA!AAA</binary>: decodeIntegers reads decoder_[-10]. <binary>AAAAA</binary> on the same array reads past the string. The same '!' inside a 64-bit float m/z array yields a plausible but wrong double, with no error. Whitespace removal (MzMLHandlerHelper.cpp:145-148) does not remove these characters.
- **Consequence:** - Integer arrays: undefined behaviour, namely an out-of-bounds read of static data before or after decoder_, and a read of up to 2 bytes past the string terminator. In practice this gives garbage integers; a crash is unlikely, and AddressSanitizer reports it. - Float arrays: silently wrong m/z or intensity values instead of a ConversionError.
- **Who hits it:** Every load of an uncompressed numeric array: - mzML: MzMLHandlerHelper.cpp:189/199 (Base64::decode) and :229/239 (decodeIntegers) - mzXML: MzXMLHandler.cpp:1167-1198 - mzData: MzDataHandler.cpp:487-510 This covers all TOPP tools and pyOpenMS reading these formats, plus direct Base64 API use. The out-of-bounds read needs an integer-typed binary array, which is rare in mzML (m/z and intensity are floats), with corrupt content. Garbage floats need corrupt base64 text inside otherwise well-formed XML: bit flips, a buggy writer, or a bad text-encoding conversion. Truncated files usually fail XML parsing first. Real users are very unlikely to hit either case.

> **Skeptic's correction:** 1. behavior_change says "A compressed float string of 1-3 characters now yields an empty array instead of going to zlib". That is wrong: decodeSingleString (Base64.cpp:274-277) already returned before zlib for input shorter than 4, so such strings already gave an empty array. The real change in the compressed float path is all-'=' input such as "====": it used to decode to one garbage byte handed to zlib, and now returns an empty array. For compressed integers, input of 1-3 characters or all '=' ends in "Decompression error?" before and after. 2. "skip_xml_checks enabled (set only by TICCalculator)" is incomplete. pyOpenMS exposes the setter on PeakFileOptions, OnDiscMSExperiment, IndexedMzMLHandler and MzMLSpectrumDecoder (bind_format.cpp:979/1223/1679, bind_kernel.cpp:1905). SpectrumMetaDataLookup.cpp:320 also sets it, but together with setFillData(false), so it decodes no arrays. 3. The trigger misses the most plausible out-of-bounds path on input that is not corrupt. xs:base64Binary allows whitespace, so a schema-valid, line-wrapped uncompressed integer array loaded with skip_xml_checks sends '\n' (index -33) or ' ' (index -11) into decoder_. 4. Minor: the unpadded-length case also indexes decoder_[-43] for the NUL terminator. Where char is unsigned (aarch64 Linux), high bytes read past the end of the table (up to +212) instead of before it.

### The fix

181dadf adds a private static Base64::checkNumericInput_ (Base64.h:157, Base64.cpp:213-247). - It returns false for input shorter than 4 characters or made only of '='. The caller then returns an empty result, as before. - It throws ConversionError when the length is not a multiple of 4, when a byte lies outside '+'..'z' or maps to '$' in decoder_, when a non-'=' byte follows padding, or when there are more than two '='. It is called first in all four numeric decoders: decodeCompressed_, decodeUncompressed_ (replacing its own length checks), decodeIntegersCompressed_ (before decodeSingleString) and decodeIntegersUncompressed_. The table lookups therefore only ever see valid bytes in complete 4-character groups.

*State:* Released. Committed in 181dadf and unchanged in 4f5c86f (core-v4.0.0-ci.4).

**Fix:** `src/openms/include/OpenMS/FORMAT/Base64.h` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/include/OpenMS/FORMAT/Base64.h
+++ b/src/openms/include/OpenMS/FORMAT/Base64.h
@@ -143,6 +143,19 @@ private:
 
     static const char encoder_[];
     static const char decoder_[];
+
+    /**
+        @brief Rejects malformed Base64 before it is decoded into numbers
+
+        The decoders map every input byte to some 6-bit value, so a byte outside the alphabet or padding
+        inside the data would otherwise come back as plausible numeric values instead of an error.
+
+        @return false if @p in carries nothing to decode (shorter than one group, or padding only)
+        @throws Exception::ConversionError if the length is not a multiple of 4, a byte is outside the
+                Base64 alphabet, or padding is anything but a trailing run of at most two '='
+    */
+    static bool checkNumericInput_(const std::string& in);
+
     /// Decodes a Base64 string to a vector of floating point numbers
     template <typename ToType>
     static void decodeUncompressed_(const std::string & in, ByteOrder from_byte_order, std::vector<ToType> & out);
@@ -276,7 +289,7 @@ private:
   void Base64::decodeCompressed_(const std::string& in, ByteOrder from_byte_order, std::vector<ToType>& out)
   {
     out.clear();
-    if (in.empty())
+    if (!checkNumericInput_(in))
     {
       return;
     }
@@ -313,14 +326,10 @@ private:
 
     // The length of a base64 string is always a multiple of 4 (always 3
     // bytes are encoded as 4 characters)
-    if (in.size() < 4)
+    if (!checkNumericInput_(in))
     {
       return;
     }
-    if (in.size() % 4 != 0)
-    {
-      throw Exception::ConversionError(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION, "Malformed base64 input, length is not a multiple of 4.");
-    }
 
     Size src_size = in.size();
     // last one or two '=' are skipped if contained
@@ -416,7 +425,10 @@ private:
     constexpr Size element_size = sizeof(ToType);
 
     std::string decompressed;
-    Base64::decodeSingleString(in, decompressed, true);
+    if (checkNumericInput_(in))
+    {
+      Base64::decodeSingleString(in, decompressed, true);
+    }
     if (decompressed.empty())
     {
       throw Exception::ConversionError(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION, "Decompression error?");
@@ -509,8 +521,9 @@ private:
     out.clear();
 
     // The length of a base64 string is a always a multiple of 4 (always 3
-    // bytes are encoded as 4 characters)
-    if (in.size() < 4)
+    // bytes are encoded as 4 characters). The check also keeps every byte
+    // inside the range that decoder_ below is indexed with.
+    if (!checkNumericInput_(in))
     {
       return;
     }
```

**Fix:** `src/openms/source/FORMAT/Base64.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FORMAT/Base64.cpp
+++ b/src/openms/source/FORMAT/Base64.cpp
@@ -210,6 +210,42 @@ namespace OpenMS
   const char Base64::encoder_[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
   const char Base64::decoder_[] = "|$$$}rstuvwxyz{$$$$$$$>?@ABCDEFGHIJKLMNOPQRSTUVW$$$$$$XYZ[\\]^_`abcdefghijklmnopq";
 
+  bool Base64::checkNumericInput_(const std::string& in)
+  {
+    // shorter input has always decoded to nothing
+    if (in.size() < 4)
+    {
+      return false;
+    }
+    if (in.size() % 4 != 0)
+    {
+      throw Exception::ConversionError(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION, "Malformed base64 input, length is not a multiple of 4.");
+    }
+    Size padding = 0;
+    for (const char c : in)
+    {
+      if (c == '=')
+      {
+        ++padding;
+      }
+      // decoder_ covers '+' to 'z' and marks the bytes in that range that are not Base64 with '$'
+      else if (padding != 0 || c < '+' || c > 'z' || decoder_[c - '+'] == '$')
+      {
+        throw Exception::ConversionError(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION,
+          padding != 0 ? "Malformed base64 input, data after padding." : "Malformed base64 input, invalid character.");
+      }
+    }
+    if (padding == in.size())
+    {
+      return false; // e.g. "====": nothing to decode
+    }
+    if (padding > 2)
+    {
+      throw Exception::ConversionError(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION, "Malformed base64 input, more than two padding characters.");
+    }
+    return true;
+  }
+
   void Base64::encodeStrings(const std::vector<std::string>& in, std::string& out, bool zlib_compression, bool append_null_byte)
   {
     out.clear();
```

### Assessment

- **Behaviour change:** No change for well-formed, padded Base64 without whitespace: the check passes and the decoders run as before. Input that used to decode silently now throws ConversionError and aborts the whole file load: a non-alphabet byte, '=' inside the data, more than two '=', or integer data whose length is not a multiple of 4. The mzML, mzXML and mzData handlers still strip whitespace before decoding. The one exception is a load with skip_xml_checks enabled (set only by TICCalculator): line-wrapped base64 now throws there, where it used to return garbage. A compressed float string of 1-3 characters now yields an empty array instead of going to zlib.
- **Concerns:** 1. No regression test. Base64_test.cpp is unchanged in core-v4.0.0-ci.2..4f5c86f, and no other test feeds invalid characters. 2. The check is a scalar per-byte pass over every numeric array before the SIMD decoder. It adds load time on uncompressed data, and that cost was not measured. 3. decodeStrings and decodeSingleString are not validated. String arrays and numpress arrays (MSNumpressCoder.cpp:65 calls decodeSingleString directly) still turn invalid characters into garbage silently. Those paths use only the SIMD decoder, so there is no out-of-bounds read. 4. One bad array aborts the whole load instead of skipping the spectrum.
- **Skeptic on the fix (yes):** 1. The misstated compressed-path behaviour change (point 1 above). 2. Besides TICCalculator, pyOpenMS users who enable skip_xml_checks and read line-wrapped base64 now get ConversionError on every numeric array. 3. Because the check throws, one bad array also makes random access through OnDiscMSExperiment and IndexedMzMLHandler's getSpectrum throw, not only a full load. 4. The existing Base64_test expectations ("==", "Q==" and "====" give empty results; the corrupted string throws ConversionError) are compatible with the check, so they neither contradict nor test it. The file is unchanged in the range. 5. The Base64.decodeIntegers and Base64.decodeStrings static methods are bound in pyOpenMS (bind_format.cpp:151, :177). The Python API reaches the fixed integer decoder directly, while decodeStrings stays unvalidated. The patch applies cleanly (blobs 66d4ba4 and fef2ddf are identical).
- **Upstream patch:** Applies cleanly. Base64.h and Base64.cpp are byte-identical at origin/develop and core-v4.0.0-ci.2 (blobs 66d4ba4 and fef2ddf), and every hunk in both files belongs to this fix.
- **Skeptic's notes:** Hunks checked at 4f5c86f: Base64.h 146-158 (declaration), 292, 329-333, 428-431, 524-526; Base64.cpp 213-248. All of them are the checkNumericInput_ change. After the check the length is a multiple of 4 and every byte is in the alphabet or trailing '=', so i+3 < size() and every decoder_ index lies in 0..79; the out-of-bounds read is closed. P0 holds only under the literal rubric (out-of-bounds read of static data reachable from files). Practical impact is garbage integers, and the trigger needs integer arrays, which are rare.

**Decision (confirmed 2026-09-14):** Rework: skip ASCII whitespace in the check and decoders, keep rejecting other invalid bytes; measure the check's cost on a large mzML; add tests. Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-059"></a>
## CPP-059: Short experimental-design rows are read past the end of the row vector

**The experimental-design reader indexes a data row before checking that it is as wide as its header, so a short row is read past the end of a std::vector. Short sample rows are also stored and read past their end later by getFactorValue.**

- **Mechanism:** origin/develop src/openms/source/FORMAT/ExperimentalDesignFile.cpp, one-table layout (parseOneTableFile_): when absent, Label and Sample are appended to the header map (:198-210). In RUN_CONTENT a label-free design appends "1" to the row (:229). The code then reads cells[Label], cells[Fraction] and cells[Fraction_Group] (:232-234) and cells[Sample] (:247) through std::vector::operator[]. The only width check, `parseErrorIf_(n_col != cells.size(), ...)`, comes after these reads, at :248. Two-table layout (parseTwoTableFile_): SAMPLE_HEADER sets n_col (:418), but SAMPLE_CONTENT (:421-430) never compares it. It reads cells[Sample] and stores the row as it is (:429). src/openms/source/METADATA/ExperimentalDesign.cpp: both SampleSection::getFactorValue overloads (:971-985 and :987-1008) check the row index with content_.at() but read `sample_row[col_index]` without a check (:984, :1007). Every line is trimmed before it is split (:173, :336), and StringUtils::trim strips '\t' (StringUtils.h:395-408). So an empty last cell disappears and the row comes out one cell short. Both files are identical at core-v4.0.0-ci.2.
- **Trigger:** Two-table design whose sample table has an empty last value. File section: header "Fraction_Group Fraction Spectra_Filepath Label Sample", row "1 1 a.mzML 1 S1". Then a blank line. Sample section: header "Sample MSstats_Condition MSstats_BioReplicate", row "S1<TAB>A<TAB>" (empty BioReplicate). All separators are tabs. The S1 row is stored with 2 cells. MSstatsConverter, or ProteomicsLFQ's MSstats export, then calls getFactorValue for MSstats_BioReplicate (MSstatsFile.cpp:45-46), which reads sample_row[2] out of bounds. One-table, label-free: header "Fraction_Group Fraction Spectra_Filepath Sample Condition" and row "1 1 a.mzML S1<TAB>" (empty Condition). After trimming and appending "1", the row has 5 cells, and cells[5] (Label) is read at :232, before the check at :248.
- **Consequence:** Undefined behaviour on a std::vector<std::string>: a string object is read from memory past the row's size, either unconstructed capacity or a neighbouring allocation. In practice this crashes (segfault, or an exception when toInt32 parses garbage). In the sample-section case it can instead put a garbage string into the condition or bioreplicate labels of MSstats or Triqler output. One-table rows whose missing cells all come after the Label, Fraction, Fraction_Group and Sample columns still get a clean ParseError from the late check.
- **Who hits it:** ExperimentalDesignFile::load is called by: - ProteomicsLFQ (:2403, :2420) - ProteinQuantifier (:873, :886, :899) - MSstatsConverter (:142) - IsobaricWorkflow (:889) - MapAlignerIdentification (:380) - Epifany (:465) - pyOpenMS ExperimentalDesignFile.load (bind_format.cpp:374) getFactorValue is reached from the MSstatsFile export (:45-46, :461-462, :706). Designs generated by sdrf-pipelines or quantms are complete and unaffected. The realistic trigger is a hand-made design exported from a spreadsheet with an empty trailing value. That is uncommon but plausible. Such rows are malformed, with fewer values than columns.

> **Skeptic's correction:** None of substance. Both triggers were re-derived at origin/develop. One-table: header 5 wide, Label appended at index 5, the row trims to 4 cells and grows to 5 with the appended "1", so cells[5] is read at :232, before the check at :248. Two-table: the sample row trims to 2 cells, is stored at :429, and is read at [2] by getFactorValue at :1007 from MSstatsFile.cpp:45-46. MSstatsConverter loads with require_spectra_file=false (:142), so a.mzML need not exist. All seven reach line numbers match. Wording nit: concern 3 calls the CPP-060 checks "negative-index checks"; they reject negative Label, Fraction and Fraction_Group values. Its ranges 241-245 and 389-403 are correct. The trailing-empty-cell trigger is arguably valid TSV (an empty value), which makes P0 stronger, not weaker.

### The fix

ExperimentalDesignFile.cpp in 181dadf: - One-table parser: n_col becomes the header width as written (`n_col = cells.size()`, 4f5c86f:200), taken before Label and Sample are appended. The width check moves to the start of RUN_CONTENT (:231), before the row is extended or indexed. The old check after the Sample read is removed. - Two-table parser: SAMPLE_CONTENT gets the same check (:444) before it reads the Sample cell or stores the row. ExperimentalDesign.cpp: both getFactorValue overloads throw Exception::MissingInformation when col_index >= the row size (:986-993, :1019-1026). This also covers sections built with the public constructor or with addSample(), whose row defaults to empty.

*State:* Released. Committed in 181dadf and unchanged in 4f5c86f (core-v4.0.0-ci.4).

**Fix:** `src/openms/source/FORMAT/ExperimentalDesignFile.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FORMAT/ExperimentalDesignFile.cpp
+++ b/src/openms/source/FORMAT/ExperimentalDesignFile.cpp
@@ -195,6 +195,10 @@ namespace OpenMS
           has_label = fs_column_header_to_index.contains("Label");
           has_sample = fs_column_header_to_index.contains("Sample");
 
+          // Width of a content row as written, i.e. without the Label/Sample columns appended below:
+          // RUN_CONTENT checks each row against it before it reads a cell or appends those columns.
+          n_col = cells.size();
+
           if (!has_label) // add label column to end of header
           {
             size_t hs = fs_column_header_to_index.size();
@@ -208,8 +212,6 @@ namespace OpenMS
             fs_column_header_to_index["Sample"] = hs;
             cells.push_back("Sample");
           }
-    
-          n_col = fs_column_header_to_index.size();
 
           // determine columns with sample metainfo like condition or replication
           for (size_t i = 0; i != cells.size(); ++i)
@@ -224,6 +226,10 @@ namespace OpenMS
         }
         else if (state == RUN_CONTENT)
         {
+          // Check the width before any cell is read: the lookups below index the row unchecked,
+          // so a row shorter than the header would otherwise be read past its end.
+          parseErrorIf_(n_col != cells.size(), tsv_file, "Wrong number of records in line");
+
           // if no label column exists -> label free
           // -> add label column with label 1 at the end of every row
           if (!has_label) { cells.push_back("1"); }
@@ -245,7 +256,6 @@ namespace OpenMS
           }
 
           samplename = cells[fs_column_header_to_index["Sample"]];
-          parseErrorIf_(n_col != cells.size(), tsv_file, "Wrong number of records in line");
 
           const auto& [it, inserted] = samplename_to_index.emplace(samplename, samplename_to_index.size());
           sample = it->second;
@@ -420,6 +439,10 @@ namespace OpenMS
         // Parse Sample Row
         else if (state == SAMPLE_CONTENT)
         {
+          // Same width check as the file section: the Sample lookup below indexes the row
+          // unchecked, and a short row stored here would be read past its end by getFactorValue().
+          parseErrorIf_(n_col != cells.size(), tsv_file, "Wrong number of records in line");
+
           // Parse Error if sample appears multiple times
           const std::string& sample = cells[sample_columnname_to_columnindex_["Sample"]];
           parseErrorIf_(sample_sample_to_rowindex_.contains(sample),
```

**Fix:** `src/openms/source/METADATA/ExperimentalDesign.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/METADATA/ExperimentalDesign.cpp
+++ b/src/openms/source/METADATA/ExperimentalDesign.cpp
@@ -981,6 +981,16 @@ namespace OpenMS
       }
       const StringList& sample_row = content_.at(sample_idx);
       const Size col_index = columnname_to_columnindex_.at(factor);
+      // Neither the constructor nor addSample() (whose row defaults to empty) reconciles a row
+      // with the column map, so a row can be shorter than the factor's column index.
+      if (col_index >= sample_row.size())
+      {
+        throw Exception::MissingInformation(
+          __FILE__,
+          __LINE__,
+          OPENMS_PRETTY_FUNCTION,
+          "Sample row " + StringUtils::toStr(sample_idx) + " has no value for factor " + factor);
+      }
       return sample_row[col_index];
     }
 
@@ -1004,6 +1014,16 @@ namespace OpenMS
      }
      const StringList& sample_row = content_.at(sample_to_rowindex_.at(sample_name));
      const Size col_index = columnname_to_columnindex_.at(factor);
+     // A row can be shorter than the column map (see the overload above); report it instead of
+     // reading past the end of the row.
+     if (col_index >= sample_row.size())
+     {
+      throw Exception::MissingInformation(
+                  __FILE__,
+                  __LINE__,
+                  OPENMS_PRETTY_FUNCTION,
+                  "Sample " + sample_name + " has no value for factor " + factor);
+     }
      return sample_row[col_index];
     }
 
```

### Assessment

- **Behaviour change:** Designs whose rows match their header width load exactly as before. parseHeader_ (:104) already rejects duplicate headers, so the header width and the column-map size agree. One-table rows of the wrong width were already rejected. They are now rejected before any cell is read, with the same message. New: two-table sample rows whose width differs from the sample header fail with "Wrong number of records in line". That includes rows with an empty last value and rows with extra trailing cells. Both loaded before: extra cells were ignored, and short rows only misbehaved when the missing factor was queried. getFactorValue now throws MissingInformation instead of reading out of bounds.
- **Concerns:** 1. No regression test covers any of the three sites. The ExperimentalDesign(File) tests are unchanged in the range, and the SampleSection built in the new MSstatsFile test has a complete row. 2. A two-table design whose sample table has an empty last cell or an extra column now gets a hard parse error. The message names the file but not the line. Because lines are trimmed first, an empty trailing cell cannot be told apart from a missing one. 3. In the same functions, the fix is interleaved with the CPP-060 negative-index checks (4f5c86f lines 241-245 and 389-403). The hunks listed here exclude them. 4. addSample() still accepts rows of any width (its "check content size" TODO remains). Only getFactorValue guards the read.
- **Skeptic on the fix (yes):** 1. The new SAMPLE_CONTENT check rejects any sample table with an optional last column left blank. An example is an MSstats_Mixture or other factor column left empty for LFQ, which loaded before and worked whenever that factor was never queried. Concern 2 mentions this, but frames such rows as malformed. Padding short sample rows with empty strings would have kept them loadable and still closed the out-of-bounds read. 2. One-table rows of the wrong width that used to fail in toInt32 with ConversionError now fail with ParseError. This is trivial. 3. The claim that sdrf-pipelines and quantms designs are unaffected is not verified in the draft. All 12 bundled design TSVs (share/OpenMS/examples and class_tests data) do have header-width rows, so the bundled examples and tests are not broken. The patch applies: blobs 3555e90 and f18c4e5 are identical, the CPP-060 hunks do not overlap, and Exception::MissingInformation is already used in the file.
- **Upstream patch:** Applies. ExperimentalDesignFile.cpp and ExperimentalDesign.cpp are byte-identical at origin/develop and core-v4.0.0-ci.2 (blobs 3555e90 and f18c4e5). The CPP-059 hunks can be taken without the CPP-060 ones. The nearest CPP-060 insertion, after base line 234, lies outside the 3-line context of the check inserted after base line 226, so either set applies on its own.
- **Skeptic's notes:** All seven hunks were checked against the 4f5c86f line numbers: 198-201, 214-215 (removal point), 229-232, 258-259 (removal point), 442-445, and ExperimentalDesign.cpp 984-993 and 1017-1026. None of them includes CPP-060 lines. The only other row access in ExperimentalDesign.cpp (:209-211) is already bounds-checked. No test covers the new checks: ExperimentalDesign(File)_test.cpp are unchanged in the range, and the SampleSection added to MSstatsFile_test.cpp in b2079fb has a complete 3-cell row.

**Decision (confirmed 2026-09-14):** Rework: pad short sample rows with empty cells and ignore extra cells; keep the getFactorValue bounds check; add tests. Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-111"></a>
## CPP-111: MapConversion::convert(PeakMap) sorts and indexes past the end of its vector

**MapConversion::convert(PeakMap) caps the number of peaks by a total that includes MS2 peaks and chromatogram points, then partially sorts and reads a vector that holds only MS1 peaks, going past its end.**

- **Mechanism:** origin/develop src/openms/source/KERNEL/ConversionHelper.cpp:24-27 clamps `n` to `input_map.getSize()`. MSExperiment.cpp:744-750 shows getSize() sums the peaks of all spectra, at every MS level, plus all chromatogram points. :33 fills `tmp` with `input_map.get2DData(tmp)`, which (MSExperiment.h:171-188) skips every spectrum whose MS level is not 1 and never looks at chromatograms. :35-38 then call `std::partial_sort(tmp.begin(), tmp.begin() + n, tmp.end(), ...)`, and :40-44 read `tmp[element_index]` for element_index < n. Whenever n > tmp.size(), `tmp.begin() + n` lies past end(). In libc++ (the macOS SDK partial_sort.h:41-50), __make_heap runs over [first, middle), which reads and swaps heap memory past the buffer. The loop `for (__i = __middle; __i != __last; ++__i)` starts beyond __last and never meets it, so it keeps walking and swapping through memory. Any standard library gives undefined behaviour here, because [middle, last) is not a valid range. The loop at :40-44 then reads past the end again and copies garbage Peak2D values into ConsensusFeatures. ConversionHelper.cpp and its test are byte-identical at develop and core-v4.0.0-ci.2 (blob e08fe92), and ConversionHelper_test uses MS1-only data.
- **Trigger:** MapAlignerPoseClustering -in a.mzML b.mzML -algorithm:max_num_peaks_considered -1 on any DDA run. The reference is loaded with all levels (MapAlignerPoseClustering.cpp:201), and so is every other map (:283); setReference (MapAlignmentAlgorithmPoseClustering.h:63-64) and align (.cpp:55-56) call convert with n = Size(-1), clamped to getSize() = MS1 + MS2 peaks + chromatogram points > MS1 peaks. With the default of 1000, it triggers only when a run has fewer than 1000 MS1 peaks but at least that many in total. FileConverter from mzML/MGF to consensusXML (FileConverter.cpp:894, n = exp.size(), the spectrum count) triggers on MS2-only input, where tmp is empty. pyOpenMS: MapConversion.convert(0, exp, cmap, n) with an explicit n larger than the MS1 peak count, on data that contains MS2 spectra or chromatograms.
- **Consequence:** Heap buffer overflow: out-of-bounds reads and writes inside partial_sort, plus a runaway loop in libc++. Typically a segmentation fault or heap corruption. If the process survives, the consensus map contains features built from uninitialised or foreign memory, and the column header size (:47) is set to the too-large n, so the alignment silently runs on garbage points.
- **Who hits it:** Moderate-to-low. The usual MapAlignerPoseClustering input is featureXML, which goes through the FeatureMap overload of convert, and that overload is correct (clamps to input_map.size(), ConversionHelper.cpp:89-92). The mzML input mode exists and is documented, but with the default max_num_peaks_considered=1000 it only fires for very sparse runs. It fires deterministically for anyone who sets -1 ('use all', as the parameter description advertises) on mzML that contains MS2 spectra or chromatograms, which is nearly all real data. FileConverter to consensusXML fires on MS2-only peak files, an uncommon conversion. pyOpenMS exposes the overload (bind_kernel.cpp:434) with n required, so script users who pass a large n on DDA data hit it. When it fires, it is memory corruption, not a clean error.

> **Skeptic's correction:** (1) The trigger with the default of 1000 is misstated. n = min(1000, getSize()), so the overflow fires whenever a run has fewer than 1000 MS1 peaks and holds at least one MS2 peak or chromatogram point. "At least that many in total" is too narrow: 500 MS1 plus 100 MS2 peaks gives n = 600 > 500. (2) Mechanism and consequence are wrong in detail. tmp.reserve(input_map.getSize()) (:30) and n <= getSize() put [begin, begin+n) inside tmp's allocation. __make_heap and the copy loop at :40-44 touch reserved but unconstructed slots, not memory past the buffer. On libc++ the only access outside the allocation is the tail loop `for (; __i != __last; ++__i)` (partial_sort.h:45). It starts past end() and has no exit short of a fault, so the process cannot survive to build garbage features. On libstdc++ (GCC 14.2 and 16.2, stl_algo.h:1594) __heap_select loops `__i < __last`, so that loop never runs. There is no crash and no access outside the allocation. The consensus map silently receives n minus the MS1 count of uninitialised Peak2D entries, the column size is set to n, and pose clustering aligns on them. On Linux/GCC builds the defect is a silent wrong result, not a segfault; P0 holds on either platform. (3) Reach omits the C++ default argument: ConversionHelper.h:61-64 declares `Size n = -1`, so any C++ caller that omits n on data with MS2 spectra or chromatograms triggers it. No in-tree caller relies on the default.

### The fix

181dadf moves the clamp after get2DData and clamps against tmp.size(): `if (n > tmp.size()) n = tmp.size(); output_map.reserve(n);` (4f5c86f ConversionHelper.cpp:30-37, with a comment saying why getSize() is the wrong bound). partial_sort's middle and the copy loop now always stay inside tmp. The same commit adds an @note to MSExperiment::get2DData (MSExperiment.h:169-173) stating that only MS1 spectra contribute and that getSize() must not be used as a bound for the filled container. No C++ regression test was added: ConversionHelper_test.cpp and MapAlignmentAlgorithmPoseClustering_test.cpp are unchanged between ci.2 and 4f5c86f. The Rust port has a matching test (tests/conversion_helper.rs::peak_map_to_consensus_clamps_against_collected_points).

*State:* Released in 4f5c86f (core-v4.0.0-ci.4). Fix committed in 181dadf (ancestor of 4f5c86f, not touched by the ci.4 reverts in 23944b6). No C++ test.

**Fix:** `src/openms/include/OpenMS/KERNEL/MSExperiment.h` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/include/OpenMS/KERNEL/MSExperiment.h
+++ b/src/openms/include/OpenMS/KERNEL/MSExperiment.h
@@ -166,6 +166,11 @@ public:
 
       Container can be a PeakArray or an STL container of peaks which
       supports push_back(), end() and back()
+
+      @note Only MS level 1 spectra contribute; MS2 (and higher) spectra and all
+            chromatograms are skipped. The number of appended peaks is therefore in
+            general smaller than getSize(), which counts those as well -- callers must
+            not use getSize() as a bound for the filled container.
     */
     template <class Container>
     void get2DData(Container& cont) const
```

**Fix:** `src/openms/source/KERNEL/ConversionHelper.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/KERNEL/ConversionHelper.cpp
+++ b/src/openms/source/KERNEL/ConversionHelper.cpp
@@ -21,17 +21,21 @@ namespace OpenMS
     output_map.setUniqueId();
 
     input_map.updateRanges();
-    if (n > input_map.getSize())
-    {
-      n = input_map.getSize();
-    }
-    output_map.reserve(n);
     std::vector<Peak2D> tmp;
     tmp.reserve(input_map.getSize());
 
     // TODO Avoid tripling the memory consumption by this call
     input_map.get2DData(tmp);
 
+    // Clamp against what get2DData() actually collected, not against getSize(): the latter
+    // counts MS2 peaks and chromatogram points as well, which get2DData() never emits, so
+    // with any non-MS1 data the partial_sort middle and the loop below would leave tmp.
+    if (n > tmp.size())
+    {
+      n = tmp.size();
+    }
+    output_map.reserve(n);
+
     std::partial_sort(tmp.begin(),
                       tmp.begin() + n,
                       tmp.end(),
```

### Assessment

- **Behaviour change:** None for input that previously worked. For MS1-only experiments, or when n is at most the MS1 peak count, the output is identical. The only changed cases are those that were undefined behaviour before: they now produce the n most intense MS1 points, capped at the number of MS1 points, and set the column header size to that capped count.
- **Concerns:** None found in the fix itself. There is no C++ regression test, so the clamp is only protected by the Rust test and by review; a small ConversionHelper_test case (MS1 spectrum plus an MS2 spectrum or chromatogram, default n) would lock it in. tmp.reserve(input_map.getSize()) still over-reserves by the MS2/chromatogram count; that costs memory only. Unrelated but adjacent: FileConverter passes exp.size() (number of spectra) as n, which limits the output to that many peaks, which looks unintended; it is not part of this finding.
- **Skeptic on the fix (yes):** (1) "None for input that previously worked" holds only for libc++/macOS, where these inputs crashed. On GCC builds, MapAlignerPoseClustering on mzML with -1, or on sparse runs with the default, completed silently. The fix changes those alignment results (correctly), because the uninitialised points and the inflated column size are gone. (2) The MSExperiment.h hunk is documentation only. (3) MSExperiment.h at origin/develop is byte-identical to ci.2 (blob ec8950e), so the hunk applies with no offset; "at most a line offset" is overcautious. (4) No C++ regression test, as the draft says. ConversionHelper_test's fixture (lines 62-78) is three MS1 spectra with no chromatograms, confirmed.
- **Upstream patch:** Applies cleanly: origin/develop ConversionHelper.cpp is byte-identical to core-v4.0.0-ci.2. The MSExperiment.h doc note sits in a file that 181dadf also changed elsewhere for other findings, but the get2DData hunk itself is independent and would apply with at most a line offset. The code fix needs nothing beyond the file itself.
- **Skeptic's notes:** Verified: ConversionHelper.cpp develop blob equals ci.2 (e08fe92); getSize() is at MSExperiment.cpp:744-750 and get2DData at MSExperiment.h:171-188. MapAlignerPoseClustering loads mzML with default options at :201 and :283. max_num_peaks_considered has a minimum of -1 and is stored as Int, so it converts to SIZE_MAX. FileConverter.cpp:894 passes exp.size(), and MGF spectra are MS level 2. pyOpenMS binds this overload with n required (bind_kernel.cpp:434). Only 181dadf touches these files in ci.2..4f5c86f. Target 23-38 covers the removed clamp and the new clamp at 30-37; target 169-173 covers the added @note.

**Decision (confirmed 2026-09-14):** Keep the fix; add a regression test (MS1 plus MS2 or chromatogram, default n). Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-113"></a>
## CPP-113: ConsensusMap::split indexes its result vector with the map index

**ConsensusMap::split sizes its output by the number of column headers but indexes it with the raw map index, so a consensusXML whose map ids are not exactly 0..n-1 makes it write past the end of the vector.**

- **Mechanism:** origin/develop src/openms/source/KERNEL/ConsensusMap.cpp:706-707 creates `std::vector<FeatureMap> fmaps(column_description_.size())`. :780 does `fmaps[it->first].emplace_back(...)`, where it->first is the FeatureHandle map index (:719-722). :801 does `fmaps[upep_id.getMetaValue("map_index")]...push_back(...)`, and :788-789 write `fmaps[0]` with no size check in the isobaric branch. Column headers are a std::map<UInt64, ColumnHeader> (ConsensusMap.h:110) keyed by map index, and nothing requires the keys to be contiguous. ConsensusXMLHandler.cpp:150-152 accepts any <map id>, and ConsensusXMLFile.cpp:95-100 only logs a warning when isMapConsistent fails. With headers {0, 3}, fmaps has size 2, and a handle with map index 3 calls emplace_back on a FeatureMap object that does not exist (heap memory past the vector). A handle or map_index meta value that is not a header key but is below the vector size is silently filed under the wrong column. The split() documentation (ConsensusMap.h:326-338) states no contiguity precondition. ConsensusMap.cpp is byte-identical at develop and core-v4.0.0-ci.2 (blob 4552311).
- **Trigger:** FileFilter -in linked.consensusXML -out subset.consensusXML -consensus:map 0 3. FileFilter.cpp:1292-1296 creates column headers only for the selected keys 0 and 3 and keeps the handles' original map indices (:1311-1313). Then QualityControl -in_cm subset.consensusXML ... without -in_postFDR: QualityControl.cpp:176 calls cmap.split(COPY_ALL) right after loading, before any label or consistency check, and fmaps[3] is written with fmaps.size() == 2. A hand-edited or third-party consensusXML with <map id="1"> and <map id="2"> (no id 0) does the same. Unassigned peptide identifications whose map_index meta value is at least the header count trigger the write at :801.
- **Consequence:** Out-of-bounds heap write: emplace_back or push_back on a FeatureMap object that lies in unallocated or foreign memory past the vector, which usually crashes or corrupts the heap. Where the stray index happens to be below the vector size, features and peptide identifications are silently assigned to the wrong feature map, and QualityControl then annotates the wrong run. In the isobaric branch, an empty column set with no consensus features makes fmaps[0] an out-of-bounds write on an empty vector.
- **Who hits it:** Low. The standard producers (FeatureLinker*, IsobaricAnalyzer, ProteomicsLFQ) write map ids 0..n-1, and QualityControl, the only TOPP caller of split(), is rarely run on FileFilter-subset consensusXML. It also throws NotImplemented for unlabeled data right after the split (QualityControl.cpp:188-192), but the out-of-bounds write happens before that. For isobaric data, the existing min_index != 0 check throws first when map 0 is missing from a feature, so the overflow there needs map 0 kept plus a sparse higher id (e.g., -consensus:map 0 3). split() is not bound in pyOpenMS, so otherwise only C++ API users are affected. The input is valid, and the defect is memory-unsafe when it fires, but few real workflows produce it.

> **Skeptic's correction:** (1) The trigger is broader than sparse header keys. FileFilter -consensus:map copies each consensus feature and calls ConsensusFeature::clear() (FileFilter.cpp:1304-1305), which clears only the handles (ConsensusFeature.cpp:381-383). Peptide identifications therefore keep the map_index of dropped maps. split() puts each one in new_feats[map_index] (ConsensusMap.cpp:751) and then writes fmaps[map_index] (:780). Even a contiguous selection such as -consensus:map 0 1 from a three-map linked file writes fmaps[2] out of bounds whenever a kept feature carries an identification from map 2. isMapConsistent checks only handles (:668-680), so such a file loads without a warning. (2) The isobaric reach example is wrong. FileFilter's cm_new starts empty and gets only FileFilter's own FILTERING DataProcessing (:1341). hasIsobaricAnalyzer is therefore false for any -consensus:map output: split() never takes the isobaric branch, and QCBase::isLabeledExperiment (QCBase.cpp:83-86) returns false. The isobaric-branch overflow ("map 0 kept plus a sparse higher id") needs a hand-made or third-party isobaric file, not -consensus:map 0 3. (3) "Line offsets of roughly -23" is misleading. Develop's ConsensusMap.cpp is byte-identical to ci.2, so the old-side line numbers of the CPP-113 hunks (706, 777, 798) match develop exactly and apply without offset. The -23 is only relative to 4f5c86f line numbers.

### The fix

181dadf builds `std::map<UInt64, Size> index_to_position` from column_description_'s keys in key order, and a `positionOf(map_index)` lambda. The lambda returns the position, or throws Exception::ElementNotFound("Map index N does not name a column of this ConsensusMap. Check Input!") (4f5c86f ConsensusMap.cpp:732-753). Every former raw index goes through it: feature placement `fmaps[positionOf(it->first)]` (:826), the isobaric branch `const Size first = positionOf(0)` for unassigned peptide and protein IDs (:833-837), and unassigned peptide IDs `fmaps[positionOf(static_cast<UInt64>(upep_id.getMetaValue("map_index")))]` (:849). fmaps[k] now corresponds to the k-th column header in key order, so sparse keys work, and an index without a header raises a clean error instead of an out-of-bounds write. There is no regression test: ConsensusMap_test.cpp is unchanged between ci.2 and 4f5c86f, and its split() section (lines 696-790) only uses headers 0 and 1. The Rust port covers it in tests/map_operations.rs::cm_split_error_paths.

*State:* Released in 4f5c86f (core-v4.0.0-ci.4). Fix committed in 181dadf (ancestor of 4f5c86f, not touched by the ci.4 reverts in 23944b6). No C++ test.

**Fix:** `src/openms/source/KERNEL/ConsensusMap.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/KERNEL/ConsensusMap.cpp
+++ b/src/openms/source/KERNEL/ConsensusMap.cpp
@@ -706,6 +729,29 @@ OPENMS_THREAD_CRITICAL(LOGSTREAM)
     Size numbr_exps = column_description_.size();
     std::vector<FeatureMap>fmaps(numbr_exps);
 
+    // A map index is not a position in fmaps: the column headers are keyed by map index and
+    // nothing requires those keys to be 0..n-1, so an index has to be resolved through the
+    // header keys -- indexing fmaps with it directly would read and write past the end.
+    std::map<UInt64, Size> index_to_position;
+    {
+      Size position(0);
+      for (const auto& cd : column_description_)
+      {
+        index_to_position[cd.first] = position;
+        ++position;
+      }
+    }
+    auto positionOf = [&index_to_position](UInt64 map_index) -> Size
+    {
+      auto it = index_to_position.find(map_index);
+      if (it == index_to_position.end())
+      {
+        throw Exception::ElementNotFound(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION,
+          "Map index " + StringUtils::toStr(map_index) + " does not name a column of this ConsensusMap. Check Input!");
+      }
+      return it->second;
+    };
+
     // Check for Isobaric Analyzer
     bool iso_analyze = DataProcessingUtils::hasIsobaricAnalyzer(getDataProcessing());
 
@@ -777,16 +823,18 @@ OPENMS_THREAD_CRITICAL(LOGSTREAM)
       // Add new Features to corresponding FeatureMap.
       for (auto it = new_feats.begin(); it != new_feats.end(); ++it)
       {
-        fmaps[it->first].emplace_back(std::move(it->second));
+        fmaps[positionOf(it->first)].emplace_back(std::move(it->second));
       }
     }
 
     // Add unassigned PeptideIdentifications to ...
     if (iso_analyze)
     {
-      // ... the first FeatureMap.
-      fmaps[0].getUnassignedPeptideIdentifications() = this->getUnassignedPeptideIdentifications();
-      fmaps[0].getProteinIdentifications() = this->getProteinIdentifications(); // wrong! improve: only copy the ProtID which belongs to this FMap!
+      // ... the first FeatureMap, i.e. the one belonging to map index 0 (see the min_index
+      // check above); resolving it keeps a map without that column from being indexed blindly
+      const Size first = positionOf(0);
+      fmaps[first].getUnassignedPeptideIdentifications() = this->getUnassignedPeptideIdentifications();
+      fmaps[first].getProteinIdentifications() = this->getProteinIdentifications(); // wrong! improve: only copy the ProtID which belongs to this FMap!
     }
     else
     {
@@ -798,7 +846,7 @@ OPENMS_THREAD_CRITICAL(LOGSTREAM)
           throw Exception::MissingInformation(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION,
             "File did not undergo IsobaricAnalyzer, but no map index was found at PeptideIdentifications. Check Input!");
         }
-        fmaps[upep_id.getMetaValue("map_index")].getUnassignedPeptideIdentifications().push_back(upep_id);
+        fmaps[positionOf(static_cast<UInt64>(upep_id.getMetaValue("map_index")))].getUnassignedPeptideIdentifications().push_back(upep_id);
       }
     }
 
```

### Assessment

- **Behaviour change:** None for contiguous headers 0..n-1, the normal case: the mapping is the identity, so output is identical. For sparse but consistent keys (e.g., {0, 3}), split now returns maps in key order instead of overflowing. Inconsistent input changes from undefined behaviour or silent misassignment to an Exception::ElementNotFound: a handle, peptide ID, or unassigned ID whose index is not a header key, or an isobaric map without a column 0. That includes an isobaric map with no consensus features whose headers lack key 0, which previously wrote fmaps[0] silently when some header existed.
- **Concerns:** (1) With sparse keys, fmaps[k] is the k-th column in key order, not map index k; callers that pair fmaps[i] with column header i (or with the i-th -in_raw/-in_trafo file, as QualityControl.cpp:298 does) must be aware of that. The split() doc comment in ConsensusMap.h was not updated to say so. (2) Previously 'working' inconsistent files, where a stray index was below the header count and features were silently misfiled, now throw; this is the correct behaviour, but it is a visible change for such files. (3) No C++ regression test; a sparse-key case and an unknown-index exception case in ConsensusMap_test would protect it. (4) positionOf(0) in the isobaric branch now throws for an isobaric map that has headers but none keyed 0 and no features, where the old code silently used the first map; this is an edge case, but it is new.
- **Skeptic on the fix (yes):** The inputs that now throw include files written by a standard TOPP tool: FileFilter -consensus:map output whose consensus features keep identifications from dropped maps (correction 1). Those files pass isMapConsistent, so concern (2)'s framing as hand-edited inconsistent files understates the change. split() now raises ElementNotFound for them. For QualityControl the result is an exception either way, because NotImplemented follows for unlabeled input. For C++ API callers it is a new hard failure; moving such identifications to the unassigned list, or dropping them, would be the lenient alternative. There is still no C++ regression test, as the draft says.
- **Upstream patch:** Applies to origin/develop: ConsensusMap.cpp there is byte-identical to core-v4.0.0-ci.2. The four CPP-113 hunks are independent of the other 181dadf hunks in the same file (CPP-112 swap, the operator+=/appendColumns header pairing, the setPrimaryMSRunPath renaming, File::localPath). Applied alone they would land with line offsets of roughly -23, which git apply/patch handles. The patch uses only StringUtils::toStr and Exception::ElementNotFound, which already exist in that file at develop.
- **Skeptic's notes:** Verified: ConsensusMap.cpp develop blob equals ci.2 (4552311). Column headers are a std::map (ConsensusMap.h:110). ConsensusXMLHandler :150-152 accepts any map id, and ConsensusXMLFile :95-100 only warns. QualityControl :173-176 splits before the label check, throws NotImplemented at :192, and uses fmaps[i] at :298. QualityControl is the only split() caller in src/, and split() is not bound in pyOpenMS. ConsensusMap.h and ConsensusMap_test.cpp are unchanged between ci.2 and 4f5c86f, and the test's split section uses headers 0 and 1. Hunk targets 732-753, 826, 833-837 and 849 match the 4f5c86f diff exactly. The fix replaces every raw index in split(); new_feats is keyed by map, so it needs no change. StringUtils::toStr and Exception::ElementNotFound are already used in that file at develop.

**Decision (confirmed 2026-09-14):** Rework: move peptide identifications from unknown maps to the unassigned list with a warning; keep throwing for feature handles; add tests. **Refinement (provisional, 2026-09-14):** `split()` has no result-level unassigned list, and filing these identifications under map 0 misfiles them, so they are dropped with one warning that lists each unknown map index and how many identifications it had. Upstream: included in the grouped patch set for its area, for your review (confirmed). **Owner, 2026-09-14:** the drop behaviour is accepted as implemented.

<a id="cpp-120"></a>
## CPP-120: mzML list `count` attribute drives an unvalidated container reserve (the same fix closed a numpress declared-length out-of-bounds read)

**When loading an mzML file, OpenMS uses the file's list `count` attributes to reserve memory without checking them. In the same reader, a numpress-compressed extra data array that decodes to fewer values than its declared length is copied past the end of its buffer.**

- **Mechanism:** There are two defects here, both fixed by the same commit. (1) Count attribute. XMLHandler.h:393-398 `attributeAsInt_` returns the signed Int from `sm_.parseInt` without any sign or range check. MzMLHandler.cpp:965 stores it in `scan_count_total_`, and :977 calls `exp_->reserveSpaceSpectra(scan_count_total_)`, which forwards the Size to `spectra_.reserve` (MSExperiment.cpp:520-523). Chromatograms take the same route (:996, :1012, MSExperiment.cpp:525-528). For every spectrum and chromatogram, :1017 calls `bin_data_.reserve(attributeAsInt_(attributes, s_count))`. A negative Int converts to SIZE_MAX, so `vector::reserve` throws `std::length_error`. XMLFile.cpp:109-112 rethrows anything that is not a Xerces exception. TOPPBase::main catches only OpenMS `BaseException` (TOPPBase.cpp:437-507), so the exception leaves main and the process aborts via `std::terminate`. A large positive count reserves count x sizeof(MSSpectrum) before any child element has been read. (2) Numpress length (the part that makes this P0). MzMLHandler.cpp:1026-1028 sets `bin_data_.back().size` to arrayLength, or to defaultArrayLength when arrayLength is absent. Both values come from the file. In `MzMLHandlerHelper::decodeBase64Arrays`, the numpress branch (MzMLHandlerHelper.cpp:175-186) decodes into `floats_64` but never resets `size` to the decoded length; every other codec branch does (:190-195, :200-205). The handler checks only m/z and intensity against their decoded sizes (MzMLHandler.cpp:407-429). Supplementary arrays are bounded by the stale `size`: - Fast path: :557 `copy_length = std::min(default_arr_length, data.size)`, then :564 `insert(..., data.floats_64.begin(), data.floats_64.begin() + copy_length)`. - Filtered path: :603-606 `if (n < data.size) ... data.floats_64[n]`. - Chromatograms: :769-771. When the decoded array is shorter than the declared length, these reads run past the end of the heap buffer of `floats_64`. The on-disc MzMLSpectrumDecoder path copies by the decoded `.size()` (MzMLSpectrumDecoder.cpp:78-90), so it is not affected. Core core-v4.0.0-ci.2 has identical code at the same lines. The finding was found by source review only; nothing was executed.
- **Trigger:** Count part: in an otherwise valid mzML, change the list tag to `<spectrumList count="-1" defaultDataProcessingRef="...">` (or `count="2000000000"`). Loading with MzMLFile or any TOPP tool aborts with an uncaught std::length_error or fails to allocate. Numpress part: a spectrum with defaultArrayLength="100" whose m/z and intensity arrays hold 100 values each, plus a third binaryDataArray (for example MS:1000786 non-standard data array, 64-bit float). That third array is compressed with MS:1002312 (MS-Numpress linear), holds only 10 values, and has no arrayLength attribute. The load then copies 100 doubles out of a 10-element buffer.
- **Consequence:** Count part: the tool aborts (std::terminate), or in pyOpenMS raises a generic exception, instead of reporting a ParseError. A huge count either fails to allocate or reserves a large block of virtual memory, depending on the OS. No data is corrupted. Numpress part: a heap out-of-bounds read (undefined behaviour). For a small mismatch, heap garbage lands silently in the loaded supplementary float data array (for example ion mobility values). For a large mismatch the process can crash.
- **Who hits it:** Every mzML load through MzMLFile or FileHandler: all TOPP tools that read mzML, TOPPView, and pyOpenMS MzMLFile.load. The numpress read affects spectra and chromatograms with numpress-compressed supplementary arrays. Real users are very unlikely to hit either part. Common writers (ProteoWizard, ThermoRawFileParser, OpenMS) write correct counts. A numpress array whose decoded length differs from its declared length comes only from a buggy writer or a crafted or corrupted file; a file truncated mid-array fails XML parsing first. The P0 rating rests on the out-of-bounds read being reachable from an input file. The count part alone would be P2.

> **Skeptic's correction:** (1) The P0 rating comes from a defect the Rust port never reported. Its CPP-120 text covers only the count attribute, which is P2. The numpress out-of-bounds read was found during classification and bundled in. The draft does admit this, but the owner should get it as a split: CPP-120 at P2, plus a separate numpress entry at P0. (2) The numpress read is misdescribed. `decodeNPInternal_` does not produce a 10-element buffer. It first resizes `floats_64` to a value-initialized capacity, then shrinks it to the decoded count (MSNumpressCoder.cpp:310-343). That capacity is 2 x compressed bytes for linear and pic, and bytes/2 for slof. With the draft's trigger (linear, 10 values, declared length 100), the compressed payload is about 20-52 bytes, so capacity is about 40-104 doubles. - Reads between the decoded length and the capacity return zeros, not heap garbage. - Only reads beyond the capacity leave the allocation, and with these numbers there may be none. - It is always out of the vector's range (undefined behaviour), but for a small mismatch the likely outcome is silent zeros. - A reliable heap over-read needs slof (MS:1002314, capacity is only count+4) or a declared length far above 2x the compressed bytes, for example defaultArrayLength 1000 with 10 values. (3) Missed consequence: the stale declared size also sizes reserves before anything is copied. - MzMLHandler.cpp:472/:482 for spectra and :703/:712 for chromatograms reserve by `input_data[i].size`. - MzMLSpectrumDecoder.cpp:72/:100 reserve by `data.size`, which :582 sets to defaultArrayLength. - So a numpress supplementary array with arrayLength="-1", or a negative or huge defaultArrayLength on the on-disc path, throws std::length_error (process abort in TOPP) or allocates a huge block. - "The on-disc MzMLSpectrumDecoder path ... is not affected" holds for the out-of-bounds read only, not for the reserve. (4) Minor: for count="2000000000", a failed allocation throws std::bad_alloc, which is also uncaught (MzMLFile::load and TOPPBase catch only BaseException), so it aborts too.

### The fix

Commit 181dadf makes three changes: 1. Adds a file-local `capacityHint_(Int count, Size limit)` (MzMLHandler.cpp:112-115 at 4f5c86f). It returns 0 for count <= 0 and otherwise min(count, limit). 2. Uses it for the reserves. spectrumList and chromatogramList are capped at 1<<16 = 65,536 (:1006, :1041). binaryDataArrayList is capped at 16 (:1047); a comment notes that bin_data_ moves into each buffered record together with its capacity. Beyond the cap, containers grow as elements arrive. 3. In the numpress branch of MzMLHandlerHelper::decodeBase64Arrays (MzMLHandlerHelper.cpp:188-195), logs the same length-mismatch warning as the other codecs and resets `bindata.size` to `floats_64.size()`. Every later use of `size` (copy_length, `n < data.size`, reserves) is then bounded by the decoded data.

*State:* Released in 4f5c86f. Committed in 181dadf; these lines were not touched again by 63e332c, 56f5f29, 23944b6 or 4f5c86f (git log -S on capacityHint_ and the new helper comment finds only 181dadf).

**Fix:** `src/openms/source/FORMAT/HANDLERS/MzMLHandler.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FORMAT/HANDLERS/MzMLHandler.cpp
+++ b/src/openms/source/FORMAT/HANDLERS/MzMLHandler.cpp
@@ -100,6 +100,19 @@ namespace OpenMS::Internal
         StringUtils::substitute(result, "\t", "&#9;");
         return result;
       }
+
+      /**
+        @brief Capacity to pre-allocate for a list from the @c count attribute of the file being read
+
+        The attribute is only a hint and comes from the input: a negative value would convert to SIZE_MAX
+        (std::length_error instead of a parse error) and a huge one would allocate before a single child
+        has been read. So at most @p limit entries are reserved; the container grows beyond that as the
+        children actually arrive.
+      */
+      Size capacityHint_(Int count, Size limit)
+      {
+        return count <= 0 ? 0 : std::min(static_cast<Size>(count), limit);
+      }
     }
 
 
@@ -974,7 +1003,7 @@ namespace OpenMS::Internal
         }
         else
         {
-          exp_->reserveSpaceSpectra(scan_count_total_);
+          exp_->reserveSpaceSpectra(capacityHint_(scan_count_total_, 1 << 16));
         }
       }
       else if (tag == "chromatogramList")
@@ -1009,12 +1038,13 @@ namespace OpenMS::Internal
         }
         else
         {
-          exp_->reserveSpaceChromatograms(chrom_count_total_);
+          exp_->reserveSpaceChromatograms(capacityHint_(chrom_count_total_, 1 << 16));
         }
       }
       else if (tag == "binaryDataArrayList" /* && in_spectrum_list_*/)
       {
-        bin_data_.reserve(attributeAsInt_(attributes, s_count));
+        // small limit: the vector moves into each buffered record together with its capacity
+        bin_data_.reserve(capacityHint_(attributeAsInt_(attributes, s_count), 16));
       }
       else if (tag == "binaryDataArray" /* && in_spectrum_list_*/)
       {
```

**Fix:** `src/openms/source/FORMAT/HANDLERS/MzMLHandlerHelper.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FORMAT/HANDLERS/MzMLHandlerHelper.cpp
+++ b/src/openms/source/FORMAT/HANDLERS/MzMLHandlerHelper.cpp
@@ -183,6 +184,15 @@ namespace OpenMS::Internal
           // Next, ensure that we only look at the float array even if the
           // mzML tags say 32 bit data (I am looking at you, proteowizard)
           bindata.precision = BinaryData::PRE_64;
+
+          // As in the other branches, the declared length (arrayLength/defaultArrayLength from the file)
+          // must not outlive decoding: the handlers size and copy supplemental arrays by it.
+          if (bindata.size != bindata.floats_64.size())
+          {
+            MzMLHandlerHelper::warning(0,std::string("Float binary data array '") + bindata.meta.getName() +
+                "' has length " + bindata.floats_64.size() + ", but should have length " + bindata.size + ".");
+            bindata.size = bindata.floats_64.size();
+          }
         }
         else if (bindata.precision == BinaryData::PRE_64)
         {
```

### Assessment

- **Behaviour change:** Valid files load exactly the same data. Files with more than 65,536 spectra or chromatograms, or more than 16 arrays per record, get a smaller up-front reserve and a few extra vector reallocations. Going by the declarations at origin/develop (not compiled), the moves of MSSpectrum and MSChromatogram are defaulted over noexcept members, so those reallocations move elements rather than copy them. Malformed input changes in two ways: a negative count no longer aborts the load, and a numpress array whose decoded length differs from its declared length now logs a warning and is bounded by the decoded length. If the declared length was shorter than the data, more values are now kept, up to the peak count.
- **Concerns:** - The negative count is only ignored for the reserve. `scan_count_total_` and `chrom_count_total_` keep the bogus value for the progress logger and for count-only loading, where -1 is also the "not yet seen" sentinel (origin/develop :971, :1003). So `count="-1"` can still confuse the LD_RAWCOUNTS early exit. - The numpress length reset is really a separate defect (the declared length outlives decoding) recorded under this ID. An upstream report should describe it on its own. - No regression test exists for either part. The MzMLFile_test and MzMLSpectrumDecoder_test changes in ci.2..4f5c86f belong to other findings.
- **Skeptic on the fix (yes):** - The numpress size reset also closes the reserve(size) std::length_error and huge-allocation path for numpress supplementary arrays, in both MzMLHandler and MzMLSpectrumDecoder. The draft does not mention this. - New log noise: a numpress array whose decoded length differs from the declared one now warns. On the on-disc decoder, size is always defaultArrayLength, so a numpress supplementary array legitimately shorter than the peak count warns there. Non-numpress arrays already warned the same way. - The noexcept-move claim for reallocations past 1<<16 is consistent with the develop declarations: MSSpectrum and MSChromatogram moves are defaulted; SpectrumSettings, Precursor, CVTermList and MetaInfoInterface are noexcept; the other members are defaulted. It matters because OpenSWATH chromatogram mzML often has more than 65,536 chromatograms. - The concern about -1 being the LD_RAWCOUNTS sentinel is accurate (develop :971, :1003). - No regression test: the ci.2..4f5c86f test diffs contain none. The MzMLSpectrumDecoder_test change comes from 5f7d33f and only changes an expected exception type.
- **Upstream patch:** The patch applies as is. The files at origin/develop are identical to core-v4.0.0-ci.2 (MzMLHandler.cpp and MzMLHandlerHelper.cpp diff empty), so the hunks apply at the ci.2 positions: - `capacityHint_` goes into the anonymous namespace after line 102. - The reserves are at 977, 1012 and 1017. - The numpress size reset goes after MzMLHandlerHelper.cpp:185. Take only these hunks. The combined ci.2..4f5c86f diff of the two files also carries other findings: skip-chromatograms and count-only fixes, processing IDs, XML escaping, and the indexList count.
- **Skeptic's notes:** Verified at origin/develop: - MzMLHandler.cpp, MzMLHandlerHelper.cpp and MzMLSqliteHandler.cpp are byte-identical to core-v4.0.0-ci.2. - All cited lines check out: XMLHandler.h:393-398, MzMLHandler.cpp:965/977/996/1012/1017/1026-1028/407-429/557/564/603-606/769-771, MSExperiment.cpp:520-523, XMLFile.cpp:109-113, TOPPBase.cpp:437-507 (no std::exception catch), MzMLHelper numpress branch :175-186. - Hunks are correct at 4f5c86f: capacityHint_ at 103-115, :1006, :1041-1047, and helper :187-195. - git log -S finds capacityHint_ and the helper comment only in 181dadf. Later commits (63e332c, 56f5f29, 23944b6, 4f5c86f) touch other hunks. - The upstream insertion points (after develop :102 and after helper :185) are correct. Process note: at the start of this review I ran `git show origin/develop:... >` into three existing files in the session scratchpad: dev_MzMLHandler.cpp, dev_MzMLHandlerHelper.cpp and dev_MzMLSqliteHandler.cpp. That breaks the read-only rule, but nothing in either repository was touched.

**Decision (confirmed 2026-09-14):** Keep the fix; add regression tests for a negative list count and a short numpress array. Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-148"></a>
## CPP-148: MzTab column-unit metadata parses its key as an index

**The mzTab reader treats the column-unit key as an indexed key. Every standard colunit-<section> line aborts the load, and a non-standard colunit[N]-<section> key writes into an empty vector.**

- **Mechanism:** origin/develop src/openms/source/FORMAT/MzTabFile.cpp:257-258 splits the MTD key on '-', and meta_key is the first field. Four branches at :683-706 test `hasPrefix(meta_key, "colunit") && meta_key_fields[1] == "protein"` (or "peptide", "psm", "small_molecule"). Each calls `extractBracketIndex(meta_key_fields[0], "colunit[")` (:29-34), which strips "colunit[" and "]" and runs StringUtils::toInt32 on the rest. - Spec key "colunit-protein": the rest is "colunit", so toInt32 throws ConversionError. MzTabFile::load (:97) has no try/catch, so the load fails. - Key "colunit[5]-protein": the rest is "5", and `mz_tab_metadata.colunit_protein[n] = s` (:687, also :693, :699, :705) assigns through operator[] of a std::vector<std::string> (MzTab.h:173-176) that nothing ever resizes. That is an out-of-bounds write. - Key starting with "colunit" but without '-' (e.g. "colunit_small_molecule", which MzTabMFile.cpp:349/355 writes for mzTab-M): `meta_key_fields[1]` reads past a one-element vector. The reader compares "psm", but the writer emits "colunit-PSM". The writer (:1981-2007) also joins key and value without a tab ("MTD\tcolunit-protein" + value). Its own output therefore has two cells and fails the `cells.size() < 3` check (:247-250) on reload. The file is identical at core-v4.0.0-ci.2.
- **Trigger:** - A valid mzTab 1.0 line "MTD<TAB>colunit-small_molecule<TAB>retention_time=[UO, UO:0000031, minute, ]" makes MzTabFile().load throw ConversionError. - A crafted line "MTD<TAB>colunit[3]-protein<TAB>x" writes colunit_protein[3] of an empty vector. - "MTD<TAB>colunit_small_molecule<TAB>x" reads meta_key_fields[1] out of bounds.
- **Consequence:** - Valid files that carry column units cannot be loaded at all: the load throws and returns no partial result. - Malformed keys cause undefined behaviour. The indexed form writes through the data pointer of an empty vector and in practice crashes. The hyphen-less form reads an out-of-bounds std::string. - Writer: colunit lines, if ever set, lack the tab between key and value, and the reader rejects the file.
- **Who hits it:** MzTabFile::load is reachable only from pyOpenMS (MzTabFile.load, bind_format.cpp:1273) and direct C++ use. At origin/develop no TOPP tool or FileHandler path calls it: neither FileInfo.cpp nor FileHandler.cpp references MzTabFile. The classification's "TOPP FileInfo" reach does not hold. colunit lines are optional and uncommon; they occur mainly in third-party mzTab 1.0 files with small-molecule sections. The memory-safety trigger needs a key form that no spec-conforming writer produces. The writer path is dead upstream, because nothing fills the colunit_* vectors. Likelihood is low: mainly pyOpenMS users loading mzTab files produced elsewhere.

> **Skeptic's correction:** The reach section is wrong. A TOPP tool does reach MzTabFile::load. src/topp/FileInfo.cpp lists "mzTab" among its input types (:83) and calls OpenMS::FileInfo::run (:139). run calls report_ (src/openms/source/FORMAT/FileInfo.cpp:637), and the MZTAB branch of report_ runs `MzTabFile().load(in, mztab)` (:1476-1479). The draft looked only at the TOPP wrapper src/topp/FileInfo.cpp and missed the library class src/openms/source/FORMAT/FileInfo.cpp. So the classification's "TOPP FileInfo" reach holds. `FileInfo -in x.mzTab` fails with ConversionError on any spec colunit line, and crashes the tool on a crafted colunit[N]-<section> key. The likelihood paragraph should name FileInfo users as well as pyOpenMS users; likelihood is still low. The rest checks out: extractBracketIndex :29-34; toInt32 throws ConversionError (StringUtils.cpp:258); colunit_* are std::vector<std::string> (MzTab.h:173-176); split with a string separator returns a one-element vector when there is no '-' (StringUtils.h:666-688); 52 occurrences of meta_key_fields[1]; MzTabMFile.cpp:349/355 write colunit_small_molecule. Nothing outside the MzTab files fills the colunit vectors.

### The fix

181dadf replaces the four branches with one: `meta_key == "colunit" && meta_key_fields.size() == 2`. It lower-cases the section field (so the writer's "PSM" is accepted) and appends cells[2] to colunit_protein, colunit_peptide, colunit_psm or colunit_small_molecule. Indexed keys, hyphen-less keys and unknown sections match nothing and are skipped. The writer now emits a tab between key and value for all four sections.

*State:* Released. Committed in 181dadf and present unchanged in 4f5c86f (core-v4.0.0-ci.4). The other MzTabFile.cpp changes in the range (f743ccd, merge 268ebb6) belong to other findings and do not touch these lines.

**Fix:** `src/openms/source/FORMAT/MzTabFile.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FORMAT/MzTabFile.cpp
+++ b/src/openms/source/FORMAT/MzTabFile.cpp
@@ -680,29 +680,32 @@ namespace OpenMS
         mz_tab_metadata.study_variable[n].description = p;
         count_study_variable_description = std::max((Size)n, count_study_variable_description);
       }
-      else if (StringUtils::hasPrefix(meta_key, "colunit") && meta_key_fields[1] == "protein")
-      {
-        Int n = (Size)extractBracketIndex(meta_key_fields[0], "colunit[");
-        const std::string& s = cells[2];
-        mz_tab_metadata.colunit_protein[n] = s;
-      }
-      else if (StringUtils::hasPrefix(meta_key, "colunit") && meta_key_fields[1] == "peptide")
-      {
-        Int n = (Size)extractBracketIndex(meta_key_fields[0], "colunit[");
-        const std::string& s = cells[2];
-        mz_tab_metadata.colunit_peptide[n] = s;
-      }
-      else if (StringUtils::hasPrefix(meta_key, "colunit") && meta_key_fields[1] == "psm")
-      {
-        Int n = (Size)extractBracketIndex(meta_key_fields[0], "colunit[");
-        const std::string& s = cells[2];
-        mz_tab_metadata.colunit_psm[n] = s;
-      }
-      else if (StringUtils::hasPrefix(meta_key, "colunit") && meta_key_fields[1] == "small_molecule")
-      {
-        Int n = (Size)extractBracketIndex(meta_key_fields[0], "colunit[");
+      else if (meta_key == "colunit" && meta_key_fields.size() == 2)
+      {
+        // the column-unit keys carry no index (colunit-protein, colunit-peptide,
+        // colunit-PSM, colunit-small_molecule), so there is nothing to extract from the key
+        // and the definition is appended - reading an index out of the key threw on every
+        // such line, and the section vectors are never resized to hold one
+        std::string section_key = meta_key_fields[1];
+        StringUtils::toLower(section_key); // the PSM key is written in upper case
         const std::string& s = cells[2];
-        mz_tab_metadata.colunit_small_molecule[n] = s;
+
+        if (section_key == "protein")
+        {
+          mz_tab_metadata.colunit_protein.push_back(s);
+        }
+        else if (section_key == "peptide")
+        {
+          mz_tab_metadata.colunit_peptide.push_back(s);
+        }
+        else if (section_key == "psm")
+        {
+          mz_tab_metadata.colunit_psm.push_back(s);
+        }
+        else if (section_key == "small_molecule")
+        {
+          mz_tab_metadata.colunit_small_molecule.push_back(s);
+        }
       }
     }
 
@@ -1981,28 +2005,28 @@ namespace OpenMS
   // colunit-protein
   for (Size i = 0; i != md.colunit_protein.size(); ++i)
   {
-    std::string s =std::string("MTD\tcolunit-protein") + md.colunit_protein[i];
+    std::string s =std::string("MTD\tcolunit-protein\t") + md.colunit_protein[i];
     sl.push_back(s);
   }
 
   // colunit-peptide
   for (Size i = 0; i != md.colunit_peptide.size(); ++i)
   {
-    std::string s =std::string("MTD\tcolunit-peptide") + md.colunit_peptide[i];
+    std::string s =std::string("MTD\tcolunit-peptide\t") + md.colunit_peptide[i];
     sl.push_back(s);
   }
 
   // colunit-PSM
   for (Size i = 0; i != md.colunit_psm.size(); ++i)
   {
-    std::string s =std::string("MTD\tcolunit-PSM") + md.colunit_psm[i];
+    std::string s =std::string("MTD\tcolunit-PSM\t") + md.colunit_psm[i];
     sl.push_back(s);
   }
 
   // colunit-small_molecule
   for (Size i = 0; i != md.colunit_small_molecule.size(); ++i)
   {
-    std::string s =std::string("MTD\tcolunit-small_molecule") + md.colunit_small_molecule[i];
+    std::string s =std::string("MTD\tcolunit-small_molecule\t") + md.colunit_small_molecule[i];
     sl.push_back(s);
   }
   }
```

### Assessment

- **Behaviour change:** Yes. - Files with spec colunit lines now load (they used to throw), and the unit strings are kept in MzTabMetaData. - Malformed colunit keys are ignored silently instead of crashing. - The writer's colunit lines get the missing tab. Upstream never fills these vectors, so files written by OpenMS tools do not change. Nothing else in load changes.
- **Concerns:** 1. No test loads or round-trips a colunit line. b6dd412 changed MzTabFile_test.cpp for other findings; "colunit" appears nowhere in the test diff. 2. Unknown section names and malformed colunit keys are dropped silently instead of being reported. 3. The same unchecked `meta_key_fields[1]` access remains in sibling branches (52 occurrences in the file, e.g. the instrument[ branches at :295, :302, :317). A hyphen-less key from those families can still read past the vector. The fix covers colunit only. 4. The writer still spells the key "colunit-PSM". Only OpenMS's own reader became case-insensitive.
- **Skeptic on the fix (yes):** 1. A sibling crash in the same function is not mentioned. For an MTD line with an empty key cell ("MTD<TAB><TAB>x" passes the cells.size() >= 3 check), StringUtils::split returns an empty vector because s.empty() returns early, so `meta_key_fields[0]` at :258 reads an empty vector. That is undefined behaviour on any MTD line, and 181dadf leaves it as it is. Concern 3 covers only the [1] reads. 2. Once loading works, a pyOpenMS load->store round trip of a third-party file fills colunit_* and writes the lines back as "colunit-PSM". The writer path is therefore no longer dead for such files, and the upper-case key goes into files other tools read. 3. mzTab-M keys such as colunit-small_molecule_feature and colunit-small_molecule_evidence are now ignored silently. The patch applies upstream: StringUtils::toLower(std::string&) exists at origin/develop (StringUtils.h:419), and blob 3d4f506 is identical.
- **Upstream patch:** Applies cleanly. MzTabFile.cpp is byte-identical at origin/develop and core-v4.0.0-ci.2 (blob 3d4f506). Take only the colunit hunks of 181dadf (base lines 683-705 and 1984-2005). The other hunks of that commit and of f743ccd belong to CPP-146, CPP-147 and the score-column fix.
- **Skeptic's notes:** P0 holds under the literal rubric: a crafted colunit[N]-protein key writes out of bounds, with an address that depends on N, from an input file, and FileInfo makes that reachable from TOPP. On spec-valid files alone this would be P1 (uncaught exception on valid input). Hunks checked at 4f5c86f: reader 683-708 (26 added lines) and writer tabs at 2008, 2015, 2022 and 2029. The other MzTabFile.cpp hunks in the range (opt_ bounds checks, opt_ prefix, score-column layout) belong to other findings. No test at 4f5c86f mentions colunit; MzTabFile_test.cpp changed only in b6dd412.

**Decision (provisional: recommended default, not yet confirmed; overrule here):** Harden the MTD parser: reject an empty key and route indexed keys through one checked accessor raising ParseError; add tests. Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-164"></a>
## CPP-164: Mascot query index guard accepts one-past-end

**The Mascot XML reader accepts a peptide query number one past <NumQueries>, and never checks <query number> at all, so a bad or header-less file makes it write outside the list of peptide identifications.**

- **Mechanism:** origin/develop src/openms/source/FORMAT/HANDLERS/MascotXMLHandler.cpp:56-62 does `peptide_identification_index_ = attribute_value - 1; if (peptide_identification_index_ > id_data_.size()) fatalError(...)`. The comparison should be `>=`. MascotXMLFile::load clears id_data_ (MascotXMLFile.cpp:39), and only the <NumQueries> end tag gives it a size (MascotXMLHandler.cpp:78-80). Both indices are UInt (MascotXMLHandler.h:62, :66), so query 0 or a negative query wraps to about 4e9 and is rejected by accident. Exactly one bad value gets through: NumQueries+1. For a header-less file that value is 1, because id_data_ is empty and `0 > 0` is false. `attribute_value - 1` on INT_MIN is also signed overflow. The accepted index goes into the unchecked ExposedVector::operator[] (ExposedVector.h:144-147) at :88 (pep_exp_mz), :97/:104/:108/:117 (pep_scan_title), :148/:157/:163 (pep_homol/pep_ident), :541-566 (</peptide>) and :573-575 (</u_peptide>, </q_peptide>). Separately, <query number> is stored at :52 without any check and used as `id_data_[actual_query_ - 1]` at :342, :363, :365, :370 (</StringTitle>) and :376 (</RTINSECONDS>). Number 0 wraps to index 4294967295. The constructor (:17-21) never initialises actual_query_, so a <StringTitle> before any <query> reads an indeterminate index.
- **Trigger:** A Mascot XML file with <header><NumQueries>1</NumQueries></header> followed by <hits><hit number="1"><protein accession="P1"><peptide query="2"><pep_exp_mz>500.0</pep_exp_mz>...</peptide></protein></hit></hits>. The guard passes (index 1 is not > size 1), and pep_exp_mz writes id_data_[1]. Also: a Mascot export made without show_header=1 (no <NumQueries>) whose first peptide has query="1". Also: <queries><query number="0"><StringTitle>x</StringTitle></query></queries>, or a number above NumQueries.
- **Consequence:** The NumQueries+1 case writes a whole PeptideIdentification just past the end of the heap allocation: setMZ writes a double, then setIdentifier and insertHit write into memory that was never allocated. The result is undefined: heap corruption, a crash later, or a load that seems to succeed. In the header-less case with a fresh output list, the vector has no buffer, so the tool segfaults instead of showing the intended 'use show_header=1' error. If the caller reuses a list that held data before, clear() keeps the capacity. The write then lands on a destroyed element, which corrupts the heap without a crash. <query number> 0 or far out of range indexes about 4e9 elements away and normally segfaults.
- **Who hits it:** Users hit this through IDFileConverter with a Mascot XML input (IDFileConverter.cpp:496), MascotAdapterOnline (MascotAdapterOnline.cpp:166) and pyOpenMS MascotXMLFile.load (bind_misc.cpp:4695). MascotAdapterOnline always asks the server for show_header=1 (MascotRemoteQuery.cpp:356), and Mascot keeps query numbers within NumQueries, so that path needs a truncated or corrupted server response. The realistic case is a user who exported Mascot XML by hand without show_header=1 and runs IDFileConverter. Even then the tool crashes only if the first peptide it reads has query="1"; any other first query hits the guard and gives the intended error. Mascot XML is a legacy format with little current use. Likelihood for real users is low; mostly malformed or hand-edited files. The P0 rests on memory safety reachable from input files, not on frequency.

> **Skeptic's correction:** (1) The consequence understates the <query number> path. It only mentions number 0 or 'far out of range' and says that normally segfaults. A number just above NumQueries, say NumQueries+k, is not rejected anywhere. <RTINSECONDS> then writes a double taken from the file k elements past the heap block (setRT at :376), and </StringTitle> does the same via setHits/setRT at :363/:370. That is silent heap corruption at an offset the file chooses, not a likely segfault. It is worse than the peptide path, which lets only NumQueries+1 through. (2) 'clear() keeps the capacity ... the write then lands on a destroyed element, which corrupts the heap without a crash' is wrong on the last part. setIdentifier and insertHit on a destroyed std::string and vector either reuse their freed buffers (use-after-free) or free them a second time when growing (double free). glibc usually aborts on a double free, so a crash is likely. (3) In the NumQueries+1 case the first touch of the phantom element at </peptide> is the getHits() copy at :541, before setIdentifier. The handler treats the bytes past the allocation as live string and vector objects and follows whatever pointers are there (wild reads and frees). It is not simply 'writing into memory that was never allocated'. A load that seems to succeed also silently drops that hit, because the phantom element never becomes part of id_data. (4) Minor: 'crashes only if the first peptide it reads has query=1' holds only because <hits> comes before <queries>. A header-less export with no hits but a <queries> section crashes on the first </StringTitle> whatever the number, because that path had no guard at all. All line references check out: MascotXMLHandler.cpp:52/56-62/78-80/88/97/104/108/117/148/157/163/541-566/573-575/342/363/365/370/376, h:62/66, MascotXMLFile.cpp:39, ExposedVector.h:144-147, IDFileConverter.cpp:496, MascotAdapterOnline.cpp:166, MascotRemoteQuery.cpp:356 (src/openms/source/FORMAT/), bind_misc.cpp:4695, XMLHandler.cpp:41-69, TOPPBase.cpp:467-471. The INT_MIN remark is also right: StringManager::parseInt is xercesc::XMLString::parseInt, which does strtol then casts to int, so it can return INT_MIN.

### The fix

Commit 181dadf makes three changes. (1) At <peptide>/<u_peptide>/<q_peptide> start tags it checks the 1-based value before subtracting: `if (attribute_value <= 0 || static_cast<Size>(attribute_value) > id_data_.size()) fatalError(...)`, and only then sets the index (4f5c86f MascotXMLHandler.cpp:57-64). (2) Before <query number> is first used, in </StringTitle> and </RTINSECONDS>, it checks `actual_query_ == 0 || actual_query_ > id_data_.size()` and calls fatalError (:341-347, :386-390). (3) It initialises actual_query_(0) in the constructor (:19), so a <StringTitle> outside any <query> is caught by the 0 check. fatalError logs the problem and throws Exception::ParseError (XMLHandler.cpp:41-69). TOPP tools report that as 'Unable to read file' and exit with INPUT_FILE_CORRUPT (TOPPBase.cpp:467-471). The same commit also changes this file's RT test to hasRT() (4f5c86f :118-120). That hunk belongs to CPP-165, not to this finding.

*State:* Released in 4f5c86f (core-v4.0.0-ci.4). It was committed in 181dadf ('[FIX,TEST] Complete inherited Core review fixes for validation'), which is an ancestor of 4f5c86f. No other commit in core-v4.0.0-ci.2..4f5c86f touches MascotXMLHandler.cpp, and nothing was reverted. There is no regression test: the only Mascot test change in 181dadf is MascotGenericFile_test.cpp (CPP-166), and MascotXMLFile_test.cpp is unchanged.

**Fix:** `src/openms/source/FORMAT/HANDLERS/MascotXMLHandler.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FORMAT/HANDLERS/MascotXMLHandler.cpp
+++ b/src/openms/source/FORMAT/HANDLERS/MascotXMLHandler.cpp
@@ -16,7 +16,7 @@ namespace OpenMS::Internal
 
     MascotXMLHandler::MascotXMLHandler(ProteinIdentification& protein_identification, PeptideIdentificationList& id_data, const std::string& filename, map<std::string, vector<AASequence> >& modified_peptides, const SpectrumMetaDataLookup& lookup):
       XMLHandler(filename, ""), protein_identification_(protein_identification),
-      id_data_(id_data), peptide_identification_index_(0), actual_title_(""),
+      id_data_(id_data), peptide_identification_index_(0), actual_query_(0), actual_title_(""),
       modified_peptides_(modified_peptides), lookup_(lookup),
       no_rt_error_(false)
     {
@@ -54,12 +54,14 @@ namespace OpenMS::Internal
       else if (tag_ == "peptide" || tag_ == "u_peptide" || tag_ == "q_peptide")
       {
         Int attribute_value = attributeAsInt_(attributes, s_peptide_query);
-        peptide_identification_index_ = attribute_value - 1;
-
-        if (peptide_identification_index_ > id_data_.size())
+        // query numbers are 1-based indices into the <NumQueries> entries: validate before subtracting,
+        // so that 0 or a negative number cannot wrap around and query == NumQueries + 1 (one past the
+        // end of id_data_) is rejected instead of being used as an index later on
+        if (attribute_value <= 0 || static_cast<Size>(attribute_value) > id_data_.size())
         {
           fatalError(LOAD, "No or conflicting header information present (make sure to use the 'show_header=1' option in the ./export_dat.pl script)");
         }
+        peptide_identification_index_ = attribute_value - 1;
       }
     }
 
@@ -335,6 +338,13 @@ namespace OpenMS::Internal
         std::string title = StringUtils::trim(character_buffer_);
         vector<std::string> parts;
 
+        // <query number> is 1-based and not checked at its start tag; it is first used as an index here
+        // (0 would wrap around, a number beyond <NumQueries> would run past the end of id_data_)
+        if (actual_query_ == 0 || actual_query_ > id_data_.size())
+        {
+          fatalError(LOAD, "No or conflicting header information present (make sure to use the 'show_header=1' option in the ./export_dat.pl script)");
+        }
+
         actual_title_ = title;
         if (modified_peptides_.contains(title))
         {
@@ -373,6 +383,11 @@ namespace OpenMS::Internal
       }
       else if (tag_ == "RTINSECONDS")
       {
+        // same 1-based <query number> range check as for <StringTitle>
+        if (actual_query_ == 0 || actual_query_ > id_data_.size())
+        {
+          fatalError(LOAD, "No or conflicting header information present (make sure to use the 'show_header=1' option in the ./export_dat.pl script)");
+        }
         id_data_[actual_query_ - 1].setRT(StringUtils::toDouble(StringUtils::trimmed(character_buffer_)));
       }
       else if (tag_ == "MascotVer")
```

### Assessment

- **Behaviour change:** None for valid files. In an export with show_header=1, every peptide query and query number lies in 1..NumQueries and runs exactly the same code as before. The existing MascotXMLFile test data have NumQueries and in-range query numbers, so they exercise the unchanged path. The only inputs that behave differently are those that used to index out of bounds: a header-less export with query 1 read first, a query above NumQueries, a query number of 0 or out of range, and <StringTitle>/<RTINSECONDS> outside a <query>. They now throw ParseError, with the same 'No or conflicting header information present (show_header=1)' message the guard already used.
- **Concerns:** No regression test exists; the checks were verified only by reading the code. The pep_* uses (4f5c86f :90-166 and :556-590) still depend on the check made when the enclosing <peptide> element opened. Two malformed-input paths therefore remain. (a) A pep_* element outside any peptide element, in a file without <NumQueries>: the index starts at 0 and id_data_ is empty. (b) A second <NumQueries> inside a peptide that shrinks id_data_ after the check. Both need deliberately broken XML. For a corrupt <query number> the reused error text points at missing header information, which is misleading there. 181dadf mixes this fix with CPP-165 (hasRT) in the same file, so cherry-picking needs care.
- **Skeptic on the fix (partly):** The fix closes every trigger the draft names. The gaps the draft lists itself remain: (a) a pep_* element outside any peptide element when there is no <NumQueries>; (b) a second <NumQueries> that shrinks id_data_ between the peptide check and later uses. Both are out-of-bounds paths from malformed input, so 'partly' rather than 'yes'. behavior_change item 'StringTitle/RTINSECONDS outside a <query> now throw' is only true before the first <query>. After one, actual_query_ keeps the last number and a stray element silently updates that query, as before. Xerces parseInt truncates a long to int, so query="4294967297" parses as 1 and passes. That index is in range, so there is no memory issue, just a wrong query. No new exceptions for valid files: all four Mascot XML test inputs (MascotXMLFile_test_1/2/3, IDFileConverter_1_input1) have <NumQueries> and every query number within range. The ParseError path is the same one the existing guard already used. No API change.
- **Upstream patch:** It applies unchanged. origin/develop MascotXMLHandler.cpp is byte-identical to core-v4.0.0-ci.2, so the four hunks (19, 57-64, 341-347, 386-390) apply verbatim. Leave out the hasRT hunk at 118-120 unless CPP-165 goes upstream in the same patch. Upstream would expect a class test, for example a small mascotXML with query=NumQueries+1 and one without <NumQueries>, each asserting ParseError. Core has no such test to offer.
- **Skeptic's notes:** Verified: origin/develop and core-v4.0.0-ci.2 MascotXMLHandler.cpp have the same SHA (422e306). 181dadf is the only commit in ci.2..4f5c86f that touches the file, and it is an ancestor of 4f5c86f, which is tagged core-v4.0.0-ci.4. The hunks at 19, 57-64, 341-347 and 386-390 match the 4f5c86f diff exactly. Hunk 118-120 (hasRT) is CPP-165 per ranked.json and is correctly left out. MascotXMLFile_test.cpp is unchanged in the range, so there is no regression test. P0 holds: file-driven heap out-of-bounds writes, including writes at a file-chosen offset through <query number>.

**Decision (provisional: recommended default, not yet confirmed; overrule here):** Close both remaining gaps (check the query index at each pep_* use, ignore a repeated NumQueries), give corrupt query numbers their own message, add tests for all triggers. Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-168"></a>
## CPP-168: mzIdentML reader dereferences missing PeptideSequence child

**An mzIdentML Peptide with an empty <PeptideSequence/> makes the reader call a method through a null pointer and crash.**

- **Mechanism:** origin/develop src/openms/source/FORMAT/HANDLERS/MzIdentMLDOMHandler.cpp:2469-2470 does `DOMNode* tn = element_sib->getFirstChild(); if (tn->getNodeType() == DOMNode::TEXT_NODE)` with no null check. Xerces creates no child node for an element without content, so getFirstChild() returns nullptr and the virtual getNodeType() call dereferences it. The only caller, parsePeptideElements_ (:762-779), wraps the call in try/catch(...). A null dereference is a signal, not a C++ exception, so its fallback never runs; that fallback would log 'No amino acid sequence readable' and store an empty AASequence. There is a related data-loss path: when the first child is a comment or a CDATA section, :2478 throws 'Non Text Node', and a valid sequence is thrown away. The same file already reads <Seq> safely with getTextContent() (:727). The DOM parser runs without validation (:196-199), so nothing rejects the file earlier.
- **Trigger:** <Peptide id="PEP_1"><PeptideSequence></PeptideSequence></Peptide> (or <PeptideSequence/>) in the SequenceCollection of an otherwise normal .mzid, loaded with MzIdentMLFile::load, FileHandler::loadIdentifications or IDFileConverter. The element is schema-valid: mzIdentML 1.1 type `sequence` is `[ABCDEFGHIJKLMNOPQRSTUVWXYZ]*` (mzIdentML1.1.0.xsd:1454-1457). OpenMS's own writer can produce it. MzIdentMLHandler.cpp:1350 and :1729 write `<PeptideSequence>` + toUnmodifiedString() + `</PeptideSequence>` with no guard for an empty sequence, and the loop at :890-906 writes every hit. So storing any PeptideHit with an empty AASequence as .mzid, then loading that file, crashes. This reader itself stores empty AASequences for Peptides it cannot read (:776-781).
- **Consequence:** A segmentation fault: the TOPP tool or Python process dies with no error message and no output. In the comment or CDATA variant, the peptide silently loses its sequence: one error line is logged, and every PSM that references it gets an empty sequence.
- **Who hits it:** Users hit this through MzIdentMLFile::load (MzIdentMLFile.cpp:32-40) and FileHandler::loadIdentifications for .mzid (FileHandler.cpp:1537-1541). That covers IDFileConverter, IDMapper and every TOPP tool that reads identifications through FileHandler, plus pyOpenMS MzIdentMLFile (bind_misc.cpp:4735). Mainstream exports (MS-GF+, Mascot, Comet, PeptideShaker) always write a non-empty sequence, so ordinary users rarely meet it. The most plausible route is an OpenMS round trip of identifications that contain an empty-sequence hit. Likelihood is low, but the result is a hard crash, not an error.

> **Skeptic's correction:** (1) Round-trip trigger: the writer is MzIdentMLHandler, reached through MzIdentMLFile::store (MzIdentMLFile.cpp:49). writePeptideHit computes getMZ(hit.getCharge()) at MzIdentMLHandler.cpp:1494, which throws InvalidValue for charge 0. So 'storing any PeptideHit with an empty AASequence' needs a non-zero charge. Everything else on that path accepts an empty sequence, so the claim holds for normal PSMs. (2) The consequence calls the comment/CDATA variant 'silent' while saying an error line is logged; it is logged but not reported as a failure. The draft also misses a variant that really is silent. With a comment inside the text, e.g. <PeptideSequence>PEP<!--x-->TIDE</PeptideSequence>, the first child is a text node, and getWholeText() returns only the text before the comment. The peptide silently becomes 'PEP' with no log line: a wrong sequence, not an empty one. getTextContent() fixes this too. (3) Verified correct: :2469-2470 has no null check, :2478 throws, the only caller is parsePeptideElements_ (:764, catch(...) at :776-779), <Seq> is read with getTextContent at :727, validation is off at :196-199, the XSD 'sequence' pattern allows an empty sequence (:1454-1458, PeptideSequence required at :1026), writer lines :1350/:1729 and the loop at :890-906, pep_map_ feeds the PSMs at :2171, MzIdentMLFile.cpp:32-40, FileHandler.cpp:1537-1541, IDMapper accepts mzid (:108, :169), bind_misc.cpp:4735.

### The fix

Commit 181dadf replaces the getFirstChild()/DOMText branch with `as = StringManager::convert(element_sib->getTextContent());` (4f5c86f :2469-2471). Per the DOM Level 3 contract documented in Xerces DOMNode.hpp, an element's text content joins its children's text, including CDATA and excluding comments and processing instructions. It is an empty string, not null, when there are no children. The commit then trims the sequence, moving that step up from the modifications stage, and throws Exception::ParseError('Peptide has no amino acid sequence.') if the result is empty (:2475-2482). parsePeptideElements_ catches that in its catch(...), logs 'No amino acid sequence readable from Peptide' and stores an empty AASequence. That is the same fallback the file already uses for other unreadable peptides.

*State:* Released in 4f5c86f (core-v4.0.0-ci.4). It was committed in 181dadf, an ancestor of 4f5c86f. No other commit in core-v4.0.0-ci.2..4f5c86f touches MzIdentMLDOMHandler.cpp, and nothing was reverted. There is no regression test: no MzIdentMLFile test or .mzid test data changed in the range.

**Fix:** `src/openms/source/FORMAT/HANDLERS/MzIdentMLDOMHandler.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FORMAT/HANDLERS/MzIdentMLDOMHandler.cpp
+++ b/src/openms/source/FORMAT/HANDLERS/MzIdentMLDOMHandler.cpp
@@ -2466,20 +2466,20 @@ namespace OpenMS::Internal
           DOMElement* element_sib = dynamic_cast<xercesc::DOMElement*>(current_sib);
           if (XMLString::equals(element_sib->getTagName(), CONST_XMLCH("PeptideSequence")))
           {
-            DOMNode* tn = element_sib->getFirstChild();
-            if (tn->getNodeType() == DOMNode::TEXT_NODE)
-            {
-              DOMText* data = dynamic_cast<DOMText*>(tn);
-              const XMLCh* val = data->getWholeText();
-              as = StringManager::convert(val);
-            }
-            else
-            {
-              throw std::runtime_error("ERROR : Non Text Node");
-            }
+            // An empty <PeptideSequence/> has no child node, so getFirstChild() would be null here;
+            // getTextContent() yields "" for it (and skips comments), as for <Seq> in parseDBSequenceElements_.
+            as = StringManager::convert(element_sib->getTextContent());
           }
         }
       }
+      // Trim before substitutions: their 'location' counts residues, which surrounding whitespace would shift.
+      StringUtils::trim(as);
+      // An empty or missing sequence cannot carry substitutions or modifications; reject it so the caller
+      // reports the Peptide as unreadable instead of indexing into an empty string.
+      if (as.empty())
+      {
+        throw Exception::ParseError(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION, "PeptideSequence", "Peptide has no amino acid sequence.");
+      }
       //2. Substitutions
       for (XMLSize_t c = 0; c < node_count; ++c)
       {
```

### Assessment

- **Behaviour change:** A normal <PeptideSequence>PEPTIDE</PeptideSequence> is read exactly as before. What changes: (1) An empty element no longer crashes; the peptide is stored with an empty sequence and one error line is logged. (2) A whitespace-only or missing PeptideSequence used to give an empty AASequence silently. It now also logs that error; the stored result is the same. (3) A sequence preceded by a comment, or written as CDATA, is now read instead of discarded. (4) mzIdentML 1.0 files use lowercase <peptideSequence>, which this reader never matches. They used to get silent empty sequences and now log one error per Peptide, for example src/tests/class_tests/openms/data/Mascot_MSMS_example.mzid, whose load is commented out at MzIdentMLFile_test.cpp:369-370.
- **Concerns:** No regression test exists, and the fix was never run against a crafted file in the C++ suite. A peptide with an empty sequence still enters pep_map_ with an empty AASequence, so its PSMs keep an empty sequence. The writer will again emit <PeptideSequence></PeptideSequence>; that is now readable, but the data loss is only logged, and the writer side is not addressed. Logging is per Peptide, which is noisy for 1.0 files. getTextContent() allocates its result on the DOM document heap until the document is released; that is negligible next to the <Seq> protein sequences read the same way. The trim move is shared with CPP-169: lines 2475-2476 here, and the removal of the old trim at 2527-2528 is listed under CPP-169. Applying this hunk alone would leave a harmless second trim.
- **Skeptic on the fix (yes):** None material beyond what the draft says. Nuances: getTextContent() also concatenates the text of any child elements, which are schema-invalid and harmless. The logged message 'No amino acid sequence readable from Peptide' does not name the peptide id, so the 40 error lines for Mascot_MSMS_example.mzid (40 Peptide elements, all with lowercase <peptideSequence>) give no locator. That file does reach parsePeptideElements_: it has SpectraData, SpectrumIdentification and SpectrumIdentificationProtocol, so the earlier 'No ... nodes' throws at :261/:277/:285 do not fire, and behaviour_change (4) is plausible. The trim hunk at 2475-2476 is shared with CPP-169, as the draft says.
- **Upstream patch:** It applies unchanged. origin/develop MzIdentMLDOMHandler.cpp is byte-identical to core-v4.0.0-ci.2. 181dadf's changes to this file cover only CPP-168 and CPP-169, so the whole file diff can be taken as one upstream patch. Upstream would likely ask for a test, such as a minimal .mzid with <PeptideSequence/> that loads without crashing.
- **Skeptic's notes:** Priority is borderline. By the rubric's letter this is P0: a null-pointer virtual call is undefined behaviour reachable from a schema-valid file. In practice it is a deterministic fault on the null page, with no corruption or write primitive, so it behaves like the P1 'crash on valid input'. The owner may reasonably downgrade it. Hunks 2469-2471 and 2475-2482 match the 4f5c86f diff. origin/develop and ci.2 MzIdentMLDOMHandler.cpp have the same SHA (33a84f8). 181dadf is the only commit touching this file in the range, and its diff of this file covers only CPP-168/169. 181dadf also changes MzIdentMLHandler.cpp (C-terminal modification location), which is unrelated and correctly not listed. No mzid tests or test data changed in the range.

**Decision (confirmed 2026-09-14):** Keep the fix; add a regression test (empty PeptideSequence). Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-169"></a>
## CPP-169: mzIdentML substitution position is used as unchecked string index

**A SubstitutionModification whose location is 0 or beyond the peptide length makes the mzIdentML reader write a character outside the sequence string.**

- **Mechanism:** origin/develop src/openms/source/FORMAT/HANDLERS/MzIdentMLDOMHandler.cpp:2494-2496 reads the location, originalResidue and replacementResidue attributes. :2500 then does `as[StringUtils::toInt32(location) - 1] = replacementResidue;` without checking against as.size(). For location="0", the int -1 becomes size_type SIZE_MAX, and std::string::operator[] writes one byte before the character buffer. A location past the end writes beyond it. Both are undefined behaviour. `as` is also empty whenever no PeptideSequence element matched, as in mzIdentML 1.0 files with lowercase <peptideSequence>, so any location of 1 or more writes out of bounds there. Surrounding whitespace was trimmed only after the substitutions (:2514), so a padded sequence got its substitution at a shifted residue. A missing replacementResidue gives `convert(...)[0]` == '\0', which was written into the sequence. AASequence::fromString later rejects that with 'unexpected character' (AASequence.cpp:1400-1401), and the caller catches it.
- **Trigger:** <Peptide id="PEP_1"><PeptideSequence>PEPTIDE</PeptideSequence><SubstitutionModification location="0" originalResidue="P" replacementResidue="A"/></Peptide>, or location="12" on the 7-residue PEPTIDE. Upstream test data contains a real instance: src/tests/class_tests/openms/data/Mascot_MSMS_example.mzid:650 (location="7"). It is an mzIdentML 1.0 file whose <peptideSequence> the reader ignores, so `as` is empty and the write is out of bounds. Its load at MzIdentMLFile_test.cpp:369-370 is commented out, so no test runs it.
- **Consequence:** One byte is written out of bounds: on the heap for sequences longer than the small-string buffer, or inside the std::string object on the stack for short ones. The effect ranges from allocator or string-length corruption and a later crash to nothing visible. A write past size() but within capacity is invisible, so the substitution is silently lost. None of these outcomes gives an error message, and the caller's catch(...) cannot intercept memory corruption.
- **Who hits it:** The load paths are the same as CPP-168: MzIdentMLFile::load, FileHandler::loadIdentifications for .mzid, IDFileConverter, IDMapper and pyOpenMS MzIdentMLFile. SubstitutionModification appears only in files from engines that report amino-acid substitutions, such as Mascot error-tolerant search. OpenMS's own writer never emits it (MzIdentMLHandler.cpp has no occurrence). An out-of-range location needs a writer bug, such as 0-based positions, or a substitution in a 1.0 file. Likelihood for real users is very low.

> **Skeptic's correction:** (1) The consequence understates the write. location is an arbitrary Int from the file, so `as[toInt32(location) - 1] = replacementResidue` writes one byte chosen by the file (replacementResidue) at an offset chosen by the file. Forward, that offset reaches up to about 2 GB past the buffer. Negative locations such as "-5" (the draft only covers 0) reach backwards. For short sequences, `as` is a stack local in parsePeptideSiblings_. Moderate offsets therefore land in the caller frames: parsePeptideElements_, readMzIdentMLFile and above, including saved return addresses. That is a controlled write primitive, not just 'one byte out of bounds ... inside the std::string object'. (2) The draft's own trigger, location="12" on the 7-residue PEPTIDE, stays inside the small-string buffer (15 chars in libstdc++, 22 in libc++). It is undefined behaviour by the standard, but in practice the substitution is simply lost and nothing is corrupted. The corrupting example is location="0". On a short string that overwrites the string's own length or mode byte: the top byte of _M_string_length in libstdc++, or the size/is-long byte in libc++. The later trim and fromString then read far out of bounds. (3) Likewise, the 'real instance' Mascot_MSMS_example.mzid:650 (location="7" on an empty `as`) lands inside the small-string buffer. It is formally out of bounds but harmless in practice, so it is not evidence of observable corruption. (4) Verified correct: :2494-2496, :2500, the late trim at :2514, AASequence.cpp:1400-1401, the commented-out load at MzIdentMLFile_test.cpp:369-370, and that MzIdentMLHandler.cpp never writes SubstitutionModification.

### The fix

Commit 181dadf changes the substitution step (4f5c86f :2496-2514). It reads replacementResidue into a string and throws Exception::ParseError('Missing replacementResidue attribute') if it is empty. It parses location once and throws ParseError unless 1 <= pos <= as.size(), and only then writes as[pos-1]. Trimming now runs before the substitutions (:2475-2476), and the late trim before the modifications step is removed (around :2527), so positions count residues. The empty-sequence check added for CPP-168 (:2479-2482) also stops the empty-`as` case earlier. parsePeptideElements_'s catch(...) catches every ParseError, logs it and stores an empty AASequence.

*State:* Released in 4f5c86f (core-v4.0.0-ci.4). It was committed in 181dadf, an ancestor of 4f5c86f. No other commit in core-v4.0.0-ci.2..4f5c86f touches the file, and nothing was reverted. There is no regression test.

**Fix:** `src/openms/source/FORMAT/HANDLERS/MzIdentMLDOMHandler.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FORMAT/HANDLERS/MzIdentMLDOMHandler.cpp
+++ b/src/openms/source/FORMAT/HANDLERS/MzIdentMLDOMHandler.cpp
@@ -2466,20 +2466,20 @@ namespace OpenMS::Internal
           DOMElement* element_sib = dynamic_cast<xercesc::DOMElement*>(current_sib);
           if (XMLString::equals(element_sib->getTagName(), CONST_XMLCH("PeptideSequence")))
           {
-            DOMNode* tn = element_sib->getFirstChild();
-            if (tn->getNodeType() == DOMNode::TEXT_NODE)
-            {
-              DOMText* data = dynamic_cast<DOMText*>(tn);
-              const XMLCh* val = data->getWholeText();
-              as = StringManager::convert(val);
-            }
-            else
-            {
-              throw std::runtime_error("ERROR : Non Text Node");
-            }
+            // An empty <PeptideSequence/> has no child node, so getFirstChild() would be null here;
+            // getTextContent() yields "" for it (and skips comments), as for <Seq> in parseDBSequenceElements_.
+            as = StringManager::convert(element_sib->getTextContent());
           }
         }
       }
+      // Trim before substitutions: their 'location' counts residues, which surrounding whitespace would shift.
+      StringUtils::trim(as);
+      // An empty or missing sequence cannot carry substitutions or modifications; reject it so the caller
+      // reports the Peptide as unreadable instead of indexing into an empty string.
+      if (as.empty())
+      {
+        throw Exception::ParseError(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION, "PeptideSequence", "Peptide has no amino acid sequence.");
+      }
       //2. Substitutions
       for (XMLSize_t c = 0; c < node_count; ++c)
       {
@@ -2493,11 +2493,25 @@ namespace OpenMS::Internal
 
             std::string location = StringManager::convert(element_sib->getAttribute(CONST_XMLCH("location")));
             char originalResidue = StringManager::convert(element_sib->getAttribute(CONST_XMLCH("originalResidue")))[0];
-            char replacementResidue = StringManager::convert(element_sib->getAttribute(CONST_XMLCH("replacementResidue")))[0];
+            const std::string replacement = StringManager::convert(element_sib->getAttribute(CONST_XMLCH("replacementResidue")));
+            // a missing replacementResidue would otherwise put a NUL character into the sequence
+            if (replacement.empty())
+            {
+              throw Exception::ParseError(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION, "SubstitutionModification", "Missing 'replacementResidue' attribute.");
+            }
+            char replacementResidue = replacement[0];
 
             if (!location.empty())
             {
-              as[StringUtils::toInt32(location) - 1] = replacementResidue;
+              // 'location' is a 1-based residue position from the file: 0 or anything past the sequence
+              // end would index outside the string (location - 1 wraps around for 0).
+              const Int pos = StringUtils::toInt32(location);
+              if (pos < 1 || static_cast<Size>(pos) > as.size())
+              {
+                throw Exception::ParseError(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION, location,
+                  "SubstitutionModification 'location' is outside of PeptideSequence '" + as + "'.");
+              }
+              as[static_cast<Size>(pos) - 1] = replacementResidue;
             }
             else if (StringUtils::hasSubstring(as, originalResidue)) //no location - every occurrence will be replaced
             {
@@ -2511,7 +2525,6 @@ namespace OpenMS::Internal
         }
       }
       //3. Modifications
-      StringUtils::trim(as);
       AASequence aas = AASequence::fromString(as);
       for (XMLSize_t c = 0; c < node_count; ++c)
       {
```

### Assessment

- **Behaviour change:** Valid substitutions give the same sequence as before. Valid here means a location between 1 and the length, with both residues present; the XSD makes both residues required and location an optional xsd:int. What changes: (1) An out-of-range location now makes the whole Peptide unreadable (error logged, empty AASequence stored) instead of causing undefined behaviour. (2) A missing replacementResidue now fails at this step instead of later in AASequence::fromString; the end result is the same, an empty sequence with a logged error. (3) A sequence with surrounding whitespace, which is schema-invalid, now gets the substitution at the correct residue instead of a shifted one. (4) A substitution with no matched PeptideSequence (1.0 files) is now reported instead of written out of bounds.
- **Concerns:** No regression test exists. Rejecting the whole peptide for one bad substitution empties the sequence of every PSM that references it. Ignoring just that substitution, with a warning, would keep more data, but the chosen behaviour matches the file's existing policy for unreadable peptides. originalResidue is still read with [0], possibly from an empty string (defined, yields '\0'), and never compared with the residue at location, so a mismatch is silently accepted. That gap predates the fix. A non-numeric location still throws ConversionError, which the same catch(...) handles. The trim move is shared with CPP-168 (lines 2475-2476).
- **Skeptic on the fix (yes):** The check `pos < 1 || pos > as.size()` also rejects negative locations, which the draft does not mention. Behaviour change the draft files only under concerns: a location of size()+1 up to the small-string or heap capacity used to load the peptide with just that substitution silently dropped. Now the whole Peptide becomes an empty AASequence and every PSM that references it loses its sequence. The 2475-2476 trim move sits in the same diff hunk as CPP-168's getTextContent and empty-check changes. Sending CPP-169 upstream alone therefore means splitting that hunk by hand, not taking it verbatim. The misleading 'ERROR : Non Text Node' message in the branch without a location predates the fix and is unchanged.
- **Upstream patch:** It applies unchanged: origin/develop MzIdentMLDOMHandler.cpp is byte-identical to core-v4.0.0-ci.2. These hunks can go upstream without CPP-168, because the range check alone also catches an empty sequence, but the trim move should go with them. Upstream would expect a test, for example a .mzid with location="0" and one with location past the sequence length, each loading without memory errors under ASan.
- **Skeptic's notes:** The hunks 2475-2476, 2496-2502, 2506-2514 and 2527-2528 (the removal of the old trim sits between 2527 and 2528) match the 4f5c86f diff exactly. P0 holds: a file-controlled out-of-bounds write on the stack or heap. There is no regression test in the range. The Rust report and ranked.json agree on the trigger.

**Decision (provisional: recommended default, not yet confirmed; overrule here):** Keep rejecting the whole peptide; add a regression test. Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-191"></a>
## CPP-191: Array hydration lacks pair length and role validation

**When reading a sqMass file, OpenMS copies each stored data array into its spectrum or chromatogram without checking that the arrays match in length or that each role appears once. A shorter array is read past its end, and a duplicated role leaves the other coordinate at zero.**

- **Mechanism:** `populateContainer_sub_` (MzMLSqliteHandler.cpp:114-264 at origin/develop) walks the rows of a DATA join. It decodes each blob into one reused `std::vector<double> data` (:123, cleared per row at :159). For an intensity row (:196-209), an m/z row (:210-229) or an RT row (:230-245), it resizes the container to `data.size()` only if the container is still empty (:199-202, :219-222, :238). It then loops over the container and advances `data_it` with no check against `data.end()` (:203-207, :223-227, :239-243). So only the first array sets the length: a shorter later array is read past its end, and a longer one is silently truncated. Completeness is counted by rows (`cont_data[curr_id] += 1` at :208/:228/:244, and `if (cont_data[k] < 2)` at :258). Two m/z rows and no intensity row therefore pass. In the full-metadata path of readExperiment, containers come from the mzML stored in RUN_EXTRA (:309-318). OpenMS's writer clears their peaks (:913-921), but a RUN_EXTRA that still carries peaks skips the resize entirely, so even equal-length DATA arrays shorter than that peak count are over-read. Because `data` keeps its capacity across rows, a moderate over-read usually picks up stale values from an earlier, longer array. Beyond that capacity it is a true heap out-of-bounds read. Core core-v4.0.0-ci.2 has identical code. The finding was found by source review only.
- **Trigger:** Take a sqMass file (for example one written by SqMassFile::store) and edit the DATA table for SPECTRUM.ID 0 (a sketch of the rows follows this list). - Out-of-bounds read: the m/z row (DATA_TYPE 0, COMPRESSION 1, zlib-compressed bytes of 2 doubles) is returned first, then an intensity row (DATA_TYPE 1) holding 1 double. The second copy loop reads `data[1]` past the end. - Silent zeros: replace the intensity row with a second DATA_TYPE 0 row. The file loads, and every intensity is 0. Then load with SqMassFile::load, FileConverter, or SpectrumAccessSqMass.
- **Consequence:** A heap out-of-bounds read (undefined behaviour). The values read become peak m/z or intensity values, often stale data from another spectrum; a large mismatch can crash the process. Duplicate-role rows load with no error, and the missing dimension is all zeros, which is a silently wrong spectrum or chromatogram.
- **Who hits it:** Every sqMass read goes through this code: SqMassFile::load (FileHandler, so FileConverter, FileInfo, TOPPView and other tools that accept sqMass), SqMassFile::transform, SpectrumAccessSqMass (OpenSwathWorkflow with sqMass input via SwathFile), MzMLSqliteHandler::readExperiment/readSpectra/readChromatograms, and pyOpenMS SqMassFile. Real users are very unlikely to hit it. OpenMS writers always store exactly one m/z-or-RT array and one intensity array of equal length per record. A corrupted blob makes zlib decompression throw rather than decode short. The trigger needs a crafted or hand-edited file, or a buggy third-party writer.

> **Skeptic's correction:** (1) The draft overstates the out-of-bounds read on the common path. In populateContainer_sub_, `data` never loses capacity: `data.clear()` and `assign` (:159, :174) and `decodeNPInternal_`'s resize (MSNumpressCoder.cpp:291-342) never shrink it. Every container that starts empty gets its length from a decode into that same vector (:199-202, :219-222, :238). So on the DATA-only route the over-read can never leave data's allocation. This route covers readSpectra and readChromatograms, SpectrumAccessSqMass, SqMassFile::transform, the readExperiment fallback, and readExperiment with an OpenMS-written RUN_EXTRA whose peaks were cleared (:913-921). There it yields stale values from an earlier array or zeros. It is undefined behaviour, but only an ASan build with container-overflow annotations would flag it, and it cannot crash. (2) The draft's "beyond that capacity" case and "a large mismatch can crash the process" apply only when RUN_EXTRA's embedded mzML supplies containers that already hold peaks. That needs a crafted zlib-compressed mzML blob. (3) The concrete trigger (a 2-value m/z row, then a 1-value intensity row in DATA) reads data[1] inside capacity: the intensity silently becomes the stale m/z[1], with no heap over-read. A heap out-of-bounds trigger would be a RUN_EXTRA mzML with, for example, 1000 peaks per spectrum, and DATA arrays of 2 values each. P0 still holds, through that crafted RUN_EXTRA route and through the undefined behaviour itself.

### The fix

Commit 181dadf adds an `acceptArray(curr_id, role)` lambda (4f5c86f MzMLSqliteHandler.cpp:139-159), called before each copy loop (:235 intensity, :251 m/z, :266 RT). `cont_data` becomes a bitmask, 1 = intensity and 2 = m/z or RT (:127). The lambda: - throws Exception::IllegalArgument if the role was already seen for that container; - resizes an empty container only for its first array; - throws if `data.size()` differs from the container size, naming the native ID. The final check requires both roles (`cont_data[k] != 3`, :285). The copy loops can therefore no longer run past `data` or silently truncate, and duplicate or missing roles are rejected.

*State:* Released in 4f5c86f. Committed in 181dadf (git log -S acceptArray finds only 181dadf); unchanged afterwards.

**Fix:** `src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp
+++ b/src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp
@@ -117,11 +124,40 @@ namespace OpenMS::Internal
       // perform first step
       sqlite3_step(stmt);
 
+      // the data arrays read so far per container, as bits: 1 = intensity, 2 = m/z or RT
       std::vector<int> cont_data;
       cont_data.resize(containers.size());
       std::map<Size,Size> sql_container_map;
       std::vector<double> data;
       std::string stemp;
+
+      // Accepts the array just decoded into 'data' as the one of 'role' for container 'curr_id'.
+      // The copy loops below walk the container and advance through 'data' unchecked, so the
+      // first array sets the container's length and every further one has to match it (a
+      // shorter one was read past its end, a longer one truncated). A container also needs one
+      // array per role: counting rows accepted two m/z arrays in place of the intensities.
+      auto acceptArray = [&](Size curr_id, int role)
+      {
+        const std::string& cont_native_id = containers[curr_id].getNativeID();
+        if (cont_data[curr_id] & role)
+        {
+          const std::string role_name = (role == 1) ? "intensity" : "m/z or retention time";
+          throw Exception::IllegalArgument(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION,
+              std::string("Spectrum/Chromatogram ") + cont_native_id + " has more than one " + role_name + " data array.");
+        }
+        if (cont_data[curr_id] == 0 && containers[curr_id].empty())
+        {
+          containers[curr_id].resize(data.size());
+        }
+        const Size cont_size = containers[curr_id].size();
+        if (data.size() != cont_size)
+        {
+          throw Exception::IllegalArgument(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION,
+              std::string("Data arrays of spectrum/chromatogram ") + cont_native_id + " differ in length: " + data.size() + " != " + cont_size);
+        }
+        cont_data[curr_id] |= role;
+      };
+
       while (sqlite3_column_type( stmt, 0 ) != SQLITE_NULL)
       {
         Size id_orig = sqlite3_column_int( stmt, 0 );
@@ -196,16 +232,12 @@ namespace OpenMS::Internal
         if (data_type == 1)
         {
           // intensity
-          if (containers[curr_id].empty())
-          {
-            containers[curr_id].resize(data.size());
-          }
+          acceptArray(curr_id, 1);
           std::vector< double >::iterator data_it = data.begin();
           for (auto it = containers[curr_id].begin(); it != containers[curr_id].end(); ++it, ++data_it)
           {
             it->setIntensity(*data_it);
           }
-          cont_data[curr_id] += 1;
         }
         else if (data_type == 0)
         {
@@ -216,16 +248,12 @@ namespace OpenMS::Internal
                 "Found m/z data type for chromatogram (instead of retention time)");
           }
 
-          if (containers[curr_id].empty())
-          {
-            containers[curr_id].resize(data.size());
-          }
+          acceptArray(curr_id, 2);
           std::vector< double >::iterator data_it = data.begin();
           for (auto it = containers[curr_id].begin(); it != containers[curr_id].end(); ++it, ++data_it)
           {
             it->setPos(*data_it);
           }
-          cont_data[curr_id] += 1;
         }
         else if (data_type == 2)
         {
@@ -235,13 +263,12 @@ namespace OpenMS::Internal
             throw Exception::IllegalArgument(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION, 
                 "Found retention time data type for spectrum (instead of m/z)");
           }
-          if (containers[curr_id].empty()) containers[curr_id].resize(data.size());
+          acceptArray(curr_id, 2);
           std::vector< double >::iterator data_it = data.begin();
           for (auto it = containers[curr_id].begin(); it != containers[curr_id].end(); ++it, ++data_it)
           {
             it->setPos(*data_it);
           }
-          cont_data[curr_id] += 1;
         }
         else
         {
@@ -255,7 +282,7 @@ namespace OpenMS::Internal
       // ensure that all spectra/chromatograms have their data: we expect two data arrays per container (int and mz/rt)
       for (Size k = 0; k < cont_data.size(); k++)
       {
-        if (cont_data[k] < 2)
+        if (cont_data[k] != 3)
         {
           throw Exception::IllegalArgument(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION,
               std::string("Spectrum/Chromatogram ") + k + " does not have 2 data arrays.");
```

### Assessment

- **Behaviour change:** Files written by OpenMS read the same, including records with zero peaks: two empty arrays still pass. Malformed files that used to load with garbage or zero coordinates now throw Exception::IllegalArgument. One more case is now rejected: an empty first array followed by a non-empty one (upstream built peaks with one coordinate 0). A RUN_EXTRA that carries peaks of a different count than DATA also throws now; no known writer produces that.
- **Concerns:** - Each new throw, like the existing throws in the same loop, leaves `populateContainer_sub_` before the caller's `sqlite3_finalize` (4f5c86f :559-560, :585-586, :606-607, :632-633). SqliteConnector then closes with `sqlite3_close_v2`, which leaves a zombie connection, so each failed read leaks a statement and a handle. The pattern already existed; it is not new with this fix. - For a missing role, the final message still says "does not have 2 data arrays" and gives the container index rather than the native ID. - No regression test exists. The SpectrumAccessSqMass_test and SqMassFile_test additions in ci.2..4f5c86f cover other findings.
- **Skeptic on the fix (yes):** None substantive beyond the draft. - The claim that the fix does not need ORDER BY is correct: develop already throws on a container-index overflow (:140-144) and on a native-ID mismatch (:145-149) before any copy. - The rejection cases listed (an empty first array followed by a non-empty one; RUN_EXTRA peaks whose count differs from DATA) are correct. - The zombie-connection concern is accurate: SqliteConnector's destructor uses sqlite3_close_v2 (SqliteConnector.cpp:25), and the finalize calls sit after populateContainer_sub_ (4f5c86f :559-560, :585-586, :606-607, :632-633). - No regression test: the SqMassFile_test and SpectrumAccessSqMass_test additions exercise indices, RT lookup, the consumer, and negative linear numpress, never mismatched or duplicate arrays. MzMLSqliteHandler_test.cpp is unchanged.
- **Upstream patch:** The patch applies as is. MzMLSqliteHandler.cpp at origin/develop is identical to core-v4.0.0-ci.2 (diff empty). The acceptArray hunks apply at develop :120-125, :199-208, :219-228, :238-244 and :258. They stand alone: they do not need the ORDER BY changes (CPP-192) or the transaction, READ_ONLY-open, SQL quoting and index changes in the same file diff, so take only these hunks. Upstream already throws on a native-ID mismatch before the copy, so adding the length check without ORDER BY does not break correctly ordered valid files.
- **Skeptic's notes:** Verified at origin/develop: - Develop code matches the draft's line references: :114-264, :123, :159, :196-245, :258, :309-318, :341-351, :913-921. - Hunks at 4f5c86f are correct: 127-160 (comment and lambda), 235-241, 251-257, 266-272, 285. They correctly exclude the ORDER BY doc comment at 113-119, which belongs to CPP-192. - git log -S acceptArray finds only 181dadf. 56f5f29 changes only writer lines (1149 onward). - The upstream line mapping (develop :120-125, :199-208, :219-228, :238-244, :258) is correct. - SwathFile::loadSqMass does use SpectrumAccessSqMass, so the reach claim holds.

**Decision (confirmed 2026-09-14):** Keep the fix; add regression tests for mismatched and duplicate sqMass arrays. Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-199"></a>
## CPP-199: Metadata readers accept invalid negative activation enum values below -1

**When reading a sqMass file, OpenMS accepts activation-method codes of -2 or lower as valid. They become out-of-range enum values that later index the activation-method name tables out of bounds.**

- **Mechanism:** `prepareChroms_` (MzMLSqliteHandler.cpp:709-713 at origin/develop) and `prepareSpectra_` (:853-857) insert `static_cast<Precursor::ActivationMethod>(sqlite3_column_int(stmt, col))` whenever the column is not NULL, is not -1, and is below SIZE_OF_ACTIVATIONMETHOD (19). There is no lower bound, so -2 down to INT_MIN pass. `sqlite3_column_int` also keeps only the low 32 bits, so a stored 4294967294 becomes -2 as well. The writer only ever stores -1 (no method) or the enum value of the first method (:1188-1191, :1409-1412). Several consumers index the static name tables with the enum value and no check: - Precursor.cpp:124 (`NamesOfActivationMethod[static_cast<size_t>(m)]`, used by getActivationMethodsAsString) - FileInfo.cpp:1631-1632, :1657, :1840 - MzXMLHandler.cpp:1021 (mzXML writer) - RangeUtils.h:331 - IsobaricChannelExtractor.h:249 For -2 the index is SIZE_MAX-1, which addresses the std::string object two slots before the array. Larger negative values point far outside mapped memory. prepareSpectra_ and prepareChroms_ are reached two ways. readExperiment uses them when RUN_EXTRA holds no metadata blob (:341-351); when it does, precursors come from the embedded mzML instead. readSpectra and readChromatograms always use them; their callers include SpectrumAccessSqMass and SqMassFile::transform (SqMassFile.cpp:63, :85). Core core-v4.0.0-ci.2 has identical code. The finding was found by source review only.
- **Trigger:** A sqMass file without RUN_EXTRA metadata, or one read through readSpectra or transform, whose PRECURSOR row for a spectrum has ACTIVATION_METHOD = -2. Then run `FileInfo -in file.sqMass`, or in pyOpenMS call `exp.getSpectrum(i).getPrecursors()[0].getActivationMethodsAsString()`, or convert to mzXML.
- **Consequence:** An out-of-bounds read of a std::string from static data (undefined behaviour). Printing or copying that object dereferences a garbage pointer and length, which typically crashes the tool or prints garbage. Nothing is written back.
- **Who hits it:** Only sqMass readers whose output is later looked at for activation methods: FileInfo, conversion to mzXML, pyOpenMS Precursor.getActivationMethodsAsString, and (per the earlier classification) TOPPView spectrum views, plus SpectrumAccessSqMass and transform consumers that inspect precursors. Real users are very unlikely to hit it. OpenMS writers never store a value below -1, so the trigger needs a crafted or corrupted PRECURSOR row or a foreign writer that uses its own codes. For files that do have RUN_EXTRA metadata, SqMassFile::load takes precursors from the embedded mzML and is not affected.

> **Skeptic's correction:** (1) Wrong file for the FileInfo lines. :1631-1632, :1657 and :1840 are in the library class src/openms/source/FORMAT/FileInfo.cpp (2447 lines). src/topp/FileInfo.cpp is a 201-line wrapper with no activation-method code. (2) The trigger is incomplete. - prepareSpectra_ attaches a precursor only when PRECURSOR.ISOLATION_TARGET is not NULL (:862-865). - prepareChroms_ uses INNER JOINs, so it needs both a PRECURSOR row and a PRODUCT row (:628-629). - SqMassConfig defaults to write_full_meta{true} (SqMassFile.h:44), so OpenMS-written files usually carry RUN_EXTRA. The FileInfo and load route therefore needs a file written without full metadata, or with RUN_EXTRA removed. The transform, readSpectra and SpectrumAccessSqMass routes are always affected. (3) For -2, the slot two before NamesOfActivationMethod depends on how the linker lays out static data. It may hold a valid std::string (for example from the adjacent NamesOfActivationMethodShort), so the result can also be a silently wrong method name, not only garbage or a crash. (4) Consumer list: - Missing: Precursor::getActivationMethodsAsShortString (Precursor.cpp:135) and Ms2SpectrumStats.cpp:66. - The TOPPView calls are confirmed at develop (SpectraTreeTab.cpp:281, SpectraIDViewTab.cpp:1072), so "per the earlier classification" can be stated as verified. - RangeUtils.h:331 is reached through FileFilter, which accepts only mzML, featureXML and consensusXML, so it is not reachable directly from sqMass.

### The fix

Commit 181dadf changes both readers (4f5c86f MzMLSqliteHandler.cpp:739-748 in prepareChroms_ and :889-896 in prepareSpectra_). They now read the value with `sqlite3_column_int64` and insert it only when 0 <= value < SIZE_OF_ACTIVATIONMETHOD. -1, all other negative values, and values too large for the enum are skipped. Reading 64 bits stops large stored values from wrapping into the valid range. A comment explains both points.

*State:* Released in 4f5c86f. Committed in 181dadf (git log -S on the new sqlite3_column_int64 reads finds only 181dadf); unchanged afterwards.

**Fix:** `src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp
+++ b/src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp
@@ -706,10 +736,16 @@ namespace OpenMS::Internal
             product.setIsolationWindowUpperOffset(offset_value);
           }
         }
-        if (sqlite3_column_type(stmt, 12) != SQLITE_NULL && sqlite3_column_int(stmt, 12) != -1
-            && sqlite3_column_int(stmt, 12) < static_cast<int>(OpenMS::Precursor::ActivationMethod::SIZE_OF_ACTIVATIONMETHOD))
+        if (sqlite3_column_type(stmt, 12) != SQLITE_NULL)
         {
-          precursor.getActivationMethods().insert(static_cast<OpenMS::Precursor::ActivationMethod>(sqlite3_column_int(stmt, 12)));
+          // -1 is written for "no activation method"; excluding only it let every other negative
+          // value become an enum value outside the range Precursor's name tables are indexed with.
+          // Read as 64 bit, since the 32 bit read wraps a larger value into that range.
+          const Int64 activation_method = sqlite3_column_int64(stmt, 12);
+          if (activation_method >= 0 && activation_method < static_cast<Int64>(OpenMS::Precursor::ActivationMethod::SIZE_OF_ACTIVATIONMETHOD))
+          {
+            precursor.getActivationMethods().insert(static_cast<OpenMS::Precursor::ActivationMethod>(activation_method));
+          }
         }
         if (sqlite3_column_type(stmt, 13) != SQLITE_NULL)
         {
@@ -850,10 +886,14 @@ namespace OpenMS::Internal
             spec.getInstrumentSettings().setPolarity(IonSource::Polarity::POSITIVE);
           }
         }
-        if (sqlite3_column_type(stmt, 15) != SQLITE_NULL && sqlite3_column_int(stmt, 15) != -1
-            && sqlite3_column_int(stmt, 15) < static_cast<int>(OpenMS::Precursor::ActivationMethod::SIZE_OF_ACTIVATIONMETHOD))
+        if (sqlite3_column_type(stmt, 15) != SQLITE_NULL)
         {
-          precursor.getActivationMethods().insert(static_cast<OpenMS::Precursor::ActivationMethod>(sqlite3_column_int(stmt, 15)));
+          // only [0, SIZE_OF_ACTIVATIONMETHOD) names a method, see prepareChroms_
+          const Int64 activation_method = sqlite3_column_int64(stmt, 15);
+          if (activation_method >= 0 && activation_method < static_cast<Int64>(OpenMS::Precursor::ActivationMethod::SIZE_OF_ACTIVATIONMETHOD))
+          {
+            precursor.getActivationMethods().insert(static_cast<OpenMS::Precursor::ActivationMethod>(activation_method));
+          }
         }
         if (sqlite3_column_type(stmt, 16) != SQLITE_NULL)
         {
```

### Assessment

- **Behaviour change:** Files written by OpenMS read the same (-1 or 0..18). Invalid codes now load with no activation method instead of an out-of-range one. One narrow change for malformed values: a stored integer of 2^32 or more, which used to wrap into a valid method, is now ignored. No exception is added.
- **Concerns:** - Invalid codes are dropped silently, with no warning. That matches how -1 was already handled, but the owner may prefer a warning. - The consumers that index the name tables (Precursor.cpp:124, FileInfo, the MzXMLHandler writer, RangeUtils, IsobaricChannelExtractor, FLASHDeconvSpectrumFile) still do so without a bounds check. An out-of-range enum inserted through the API, for example an integer cast in pyOpenMS, still reaches them. That is P1 API-misuse territory and not addressed here. - No regression test exists; MzMLSqliteHandler_test.cpp is unchanged in ci.2..4f5c86f.
- **Skeptic on the fix (yes):** None beyond the draft. - Values that are TEXT or REAL convert the same way under sqlite3_column_int64 as they did under sqlite3_column_int, so there is no new regression. - Only MzMLSqliteHandler reads ACTIVATION_METHOD (grep of src/openms and src/topp), so no other file reader is left unfixed. - Int64 exists upstream (Types.h:40). - The silent drop and the unchecked name-table consumers are correctly listed as open.
- **Upstream patch:** The patch applies as is. MzMLSqliteHandler.cpp at origin/develop is identical to core-v4.0.0-ci.2 (diff empty). The two hunks replace develop :709-713 and :853-857, and `Int64` is already available from OpenMS/CONCEPT/Types.h. Take only these hunks from the combined file diff, which also carries CPP-191, CPP-192 and the writer, transaction and quoting fixes.
- **Skeptic's notes:** Verified at origin/develop: - MzMLSqliteHandler.cpp:709-713 and :853-857 are as quoted. - SIZE_OF_ACTIVATIONMETHOD is 19 (Precursor.h:60-81). - The writer stores -1 or the first method's value (:1188-1191, :1409-1412). - SqMassFile.cpp:63 and :85 call readSpectra and readChromatograms. - Precursor.cpp:124, MzXMLHandler.cpp:1021, RangeUtils.h:331 and IsobaricChannelExtractor.h:249 index the name tables unchecked. - Hunks at 4f5c86f are correct: 739-748 and 889-896. - git log -S sqlite3_column_int64 finds only 181dadf.

**Decision (confirmed 2026-09-14):** Keep the fix; add a regression test for activation codes below -1. Upstream: included in the grouped patch set for its area, for your review (confirmed).

<a id="cpp-166"></a>
## CPP-166: Mascot MGF loader carries precursor and RT fields between blocks

**The MGF reader reuses one spectrum object for every BEGIN IONS block and never fully resets it, so a block that leaves out CHARGE, RTINSECONDS, the PEPMASS intensity, MSLEVEL or a compound field silently gets the previous block's value.**

- **Mechanism:** origin/develop src/openms/include/OpenMS/FORMAT/MascotGenericFile.h:92-95 creates one `spectrum` in load() and sets MS level 2, one precursor and centroid type once, before the loop at :96. Each block is then read by getNextSpectrum_ (:141-154), which resets only the peaks (`spectrum.resize(0)`), the native ID and the TITLE and SEQ meta values. Every other field is assigned only when its line is present: - PEPMASS m/z and intensity (:216-235; the intensity only when a second number is given) - CHARGE (:236-241) - RTINSECONDS (:242-246), and RT from a TITLE containing "min" (:268) - MSLEVEL (:325-343) - the meta values NAME, COMPOUND_NAME, INCHI, SMILES, IONMODE, SOURCE_INSTRUMENT, ORGANISM, PI, DATACOLLECTOR, LIBRARYQUALITY, SPECTRUMID and SCANS (:300-378) exp.addSpectrum copies the object (:98), and the old values stay on it for the next block. Lines outside a block are skipped by the outer loop (:159-166), so leaked values always come from the previous block, never from the file header. A related defect is fixed in the same place. The only END IONS test is inside the peak loop (:205-210), so a block with no peak lines runs on through the next BEGIN IONS and merges with the following block. If the empty block is the last one, it is dropped at end of file (:399). The file is byte-identical at origin/develop and core-v4.0.0-ci.2.
- **Trigger:** BEGIN IONS / TITLE=s1 / PEPMASS=500.25 12000 / CHARGE=2+ / RTINSECONDS=1200 / 100 10 / END IONS, followed by BEGIN IONS / TITLE=s2 / PEPMASS=612.8 / 150 20 / END IONS. Spectrum s2 loads with charge 2, precursor intensity 12000 and RT 1200 s, although its block gives none of them. Real files look like this when a converter omits CHARGE for precursors whose charge was not determined, or when library entries differ in which fields they list.
- **Consequence:** Silently wrong metadata, with no error or warning: - wrong precursor charge, so a wrong neutral precursor mass for searches and charge filters - wrong RT, precursor intensity and MS level - in spectral libraries, the previous entry's compound name, SMILES or InChI attached to an entry that lacks them The wrong values are written on unchanged when MGF is converted to mzML. The empty-block merge also puts an empty block's fields onto the next spectrum and changes the spectrum count.
- **Who hits it:** Callers: - FileHandler::loadExperiment for MGF (FileHandler.cpp:924-930), so every TOPP tool that reads MGF through FileHandler - FileConverter with MGF input - MetaboliteSpectralMatcher's spectral library (MetaboliteSpectralMatcher.cpp:154 accepts MGF, e.g. GNPS libraries) - pyOpenMS MascotGenericFile.load (bind_misc.cpp:3070) Most OpenMS proteomics workflows read mzML, so MGF input is a minority path. Files in which every block lists the same fields are unaffected, which is common for fully charge-annotated converter output and for GNPS libraries. Files that mix blocks with and without CHARGE (or RT, or compound fields) are affected every time. Likelihood is moderate for MGF users. Empty blocks are rare.

> **Skeptic's correction:** None of substance. Re-reading origin/develop MascotGenericFile.h confirms every line reference: the object is set up once at :92-95; getNextSpectrum_ resets only peaks, native ID, TITLE and SEQ (:143-154); the fields at :216-378 are set only when their line is present; END IONS is tested only inside the peak loop (:205-207); the function returns false at :399. The s1/s2 trigger is right: s2 gets charge 2, precursor intensity 12000 and RT 1200. One small gap: behavior_change leaves out that a block without PEPMASS now gets precursor m/z 0 instead of the previous block's m/z. Concern 1 is accurate but understates the test: once the END IONS change is in, the test does assert the reset (charge 0, intensity 0, RT -1, no SEQ). What it cannot do on the old code is tell the two changes apart.

### The fix

181dadf moves the per-block initialisation into getNextSpectrum_: - It calls `spectrum.clear(true)`. At 4f5c86f, MSSpectrum.cpp:206-230 clears peaks, data arrays and SpectrumSettings (precursors and meta values included), and sets RT to -1, the drift time to unset and the MS level to 1. - It then sets MS level 2, one empty precursor, centroid type and the native ID. - load() now only declares the spectrum. - The explicit TITLE and SEQ removal is dropped as redundant. A new `if (line == "END IONS") return true;` after the empty-line skip ends a block that has no peaks, so it becomes its own empty spectrum instead of absorbing the next block. The class documentation gains a paragraph: blocks are independent, and header parameters are not applied. The regression test is section "[EXTRA] empty MGF blocks do not consume the following spectrum" in MascotGenericFile_test.cpp.

*State:* Released. Committed in 181dadf and unchanged through 4f5c86f (core-v4.0.0-ci.4). The ci.4 reverts in 23944b6 do not touch it.

**Fix:** `src/openms/include/OpenMS/FORMAT/MascotGenericFile.h` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/openms/include/OpenMS/FORMAT/MascotGenericFile.h
+++ b/src/openms/include/OpenMS/FORMAT/MascotGenericFile.h
@@ -36,6 +36,11 @@ namespace OpenMS
     the MSSpectrum via the "SEQ" meta value as a StringList (always, even for a single SEQ)
     and written back out as one SEQ= line per entry.
 
+    When loading, every BEGIN IONS ... END IONS block yields an independent spectrum: a field that
+    a block omits keeps its default (MS level 2, centroided, one empty precursor, no meta value) and
+    is never taken over from the preceding block. Parameters in the file header, outside of any
+    block, are not applied to the spectra.
+
     @htmlinclude OpenMS_MascotGenericFile.parameters
 
     @ingroup FileIO
@@ -89,10 +94,7 @@ public:
       UInt spectrum_number(0);
       Size line_number(0); // carry line number for error messages within getNextSpectrum()
 
-      typename MapType::SpectrumType spectrum;
-      spectrum.setMSLevel(2);
-      spectrum.getPrecursors().resize(1);
-      spectrum.setType(SpectrumSettings::SpectrumType::CENTROID); // MGF is always centroided, by definition
+      typename MapType::SpectrumType spectrum; // (re)initialised for every block by getNextSpectrum_()
       while (getNextSpectrum_(is, spectrum, line_number, spectrum_number))
       {
         exp.addSpectrum(spectrum);
@@ -140,18 +142,16 @@ protected:
     template <typename SpectrumType>
     bool getNextSpectrum_(std::ifstream& is, SpectrumType& spectrum, Size& line_number, const Size& spectrum_number)
     {
-      spectrum.resize(0);
+      // Every BEGIN IONS block is an independent query, and most of its fields (RTINSECONDS, CHARGE,
+      // the PEPMASS intensity, MSLEVEL, TITLE, SEQ, NAME, ...) may be omitted. The same spectrum object
+      // is reused for every block, so reset peaks *and* meta data here; otherwise a block that omits
+      // a field would silently inherit the value of the previous block.
+      spectrum.clear(true);
+      spectrum.setMSLevel(2); // MGF default unless MSLEVEL says otherwise
+      spectrum.getPrecursors().resize(1);
+      spectrum.setType(SpectrumSettings::SpectrumType::CENTROID); // MGF is always centroided, by definition
       spectrum.setNativeID(std::string("index=") + (spectrum_number));
 
-      if (spectrum.metaValueExists("TITLE"))
-      {
-        spectrum.removeMetaValue("TITLE");
-      }
-      if (spectrum.metaValueExists("SEQ"))
-      {
-        // SEQ is a per-query field; do not let it bleed across spectra
-        spectrum.removeMetaValue("SEQ");
-      }
       typename SpectrumType::PeakType p;
 
       std::string line;
@@ -172,6 +172,11 @@ protected:
 
             if (line.empty()) continue;
 
+            if (line == "END IONS")
+            {
+              return true; // an empty spectrum still ends this block
+            }
+
             if (isdigit(line[0])) // actual data .. this comes first, since its the most common case
             {
               std::vector<std::string> split;
```

**Test:** `src/tests/class_tests/openms/source/MascotGenericFile_test.cpp` (core-v4.0.0-ci.2 → 4f5c86f)

```diff
--- a/src/tests/class_tests/openms/source/MascotGenericFile_test.cpp
+++ b/src/tests/class_tests/openms/source/MascotGenericFile_test.cpp
@@ -422,4 +422,27 @@ delete ptr;
 
 /////////////////////////////////////////////////////////////
 /////////////////////////////////////////////////////////////
+START_SECTION(([EXTRA] empty MGF blocks do not consume the following spectrum))
+  std::string filename;
+  NEW_TMP_FILE(filename)
+  {
+    std::ofstream output(filename);
+    output << "BEGIN IONS\nPEPMASS=500 25\nCHARGE=3+\nRTINSECONDS=42\nSEQ=FIRST\nEND IONS\n"
+              "BEGIN IONS\nPEPMASS=600\n100 200\nEND IONS\n";
+  }
+  PeakMap spectra;
+  MascotGenericFile().load(filename, spectra);
+  TEST_EQUAL(spectra.size(), 2)
+  ABORT_IF(spectra.size() != 2)
+  TEST_TRUE(spectra[0].empty())
+  TEST_EQUAL(spectra[0].getRT(), 42)
+  TEST_TRUE(spectra[0].metaValueExists("SEQ"))
+  TEST_EQUAL(spectra[1].size(), 1)
+  TEST_EQUAL(spectra[1].getPrecursors()[0].getMZ(), 600)
+  TEST_EQUAL(spectra[1].getPrecursors()[0].getIntensity(), 0)
+  TEST_EQUAL(spectra[1].getPrecursors()[0].getCharge(), 0)
+  TEST_EQUAL(spectra[1].getRT(), -1)
+  TEST_FALSE(spectra[1].metaValueExists("SEQ"))
+END_SECTION
+
 END_TEST
```

### Assessment

- **Behaviour change:** Yes, as intended. - A block that omits a field now gets the default (charge 0, precursor intensity 0, RT -1, MS level 2, no meta value) instead of the previous block's value. - A block with no peaks now yields an empty spectrum. Before, it was merged into the next block, or dropped if it was last. For such files the spectrum count changes, and so do the index=N native IDs of all later spectra. Files in which every block lists the same fields and no block is empty load exactly as before. Header-level parameters were ignored before and still are.
- **Concerns:** 1. The test does not isolate the carry-over. Its first block has no peaks, so on the old code it fails at the size check (the two blocks merge) before the carry-over assertions run. No test has two non-empty blocks where the second omits CHARGE or RT. 2. The empty-block change is a second behaviour change filed under this finding. It shifts native IDs for files with empty blocks, which matters if results from an earlier OpenMS conversion are matched by index. 3. clear(true) calls shrink_to_fit, so the peak vector is reallocated for every block. This is a small cost, not a correctness problem. 4. Global MGF header parameters, such as a file-wide CHARGE, are still not applied as defaults (now documented). This is unchanged from before.
- **Skeptic on the fix (yes):** None missed. Checks: MSSpectrum::clear(bool) at origin/develop is identical to 4f5c86f, so clear(true) resets the same state upstream (SpectrumSettings including precursors and meta values, RT -1, MS level 1). 181dadf changes only MascotGenericFile.h and the test for this finding, and changes no reference output. All 3 .mgf files under src/tests and share at 4f5c86f were scanned: none has a block that omits a field an earlier block set, and none has an empty block. So no existing output changes, and there is also no TOPP-level coverage of the carry-over. The native ID shift only affects files with empty blocks, as the draft says.
- **Upstream patch:** Applies cleanly. MascotGenericFile.h and MascotGenericFile_test.cpp are byte-identical at origin/develop and core-v4.0.0-ci.2 (blobs 93b6bcf and 7a598a8), so the 181dadf hunks apply without offset.
- **Skeptic's notes:** P0 holds. msconvert-style MGF leaves out CHARGE for spectra whose charge was not determined. That is valid, common input, and the result is a silently wrong charge and RT. Reach lines checked: FileHandler.cpp:924-930, MetaboliteSpectralMatcher.cpp:154 (MGF accepted), bind_misc.cpp:3070. Hunk ranges checked at 4f5c86f: doc 39-43, load 97, reset 145-152 plus context 153-155 around the removed TITLE/SEQ block, END IONS 175-179, test 425-446 plus a trailing blank line at 447. Blobs 93b6bcf and 7a598a8 are identical at origin/develop and ci.2.

**Decision (provisional: recommended default, not yet confirmed; overrule here):** Keep the fix; replace the test with two non-empty blocks where the second omits CHARGE and RTINSECONDS. Upstream: included in the grouped patch set for its area, for your review (confirmed). **Owner, 2026-09-14:** accepted as implemented; the empty-block test is kept next to the new two-block test because it is the only coverage of the END IONS change.

<a id="cpp-042"></a>
## CPP-042: XLMS linear suffix losses divide the mass by charge twice

**Both cross-link spectrum generators put the water and ammonia loss peaks of linear x/y/z ions at charge 2 or higher at (M/z - L)/z instead of (M - L)/z, so OpenPepXL scores and annotates against wrong theoretical peaks.**

- **Mechanism:** Paths are at origin/develop. TheoreticalSpectrumGeneratorXLMS.cpp, addLinearPeaks_ (:214): - The suffix loop computes the m/z `double pos(mono_weight / charge)` at :305. - It passes pos to `addLinearIonLosses_(..., pos, ...)` at :311. - That helper (:560) expects the charged mass. It computes `mass_with_loss = mono_weight - loss_H2O_` and `setMZ(mass_with_loss / charge)` (:567, :570), and the same for NH3 (:586, :589). - The prefix loop passes mono_weight (:277), as do all cross-link loss calls (:487, :527, :1038, :1081). Only :311 is wrong. SimpleTSGXLMS.cpp has the same defect: - `pos(mono_weight / charge)` at :226, then `addLosses_(spectrum, pos, charge, ...)` at :230. - The helper emits `(mono_weight - loss) / charge` (:460, :465). - The prefix branch (:197) and the other loss calls (:349, :385, :634, :674) pass mono_weight. For charged mass M, loss L and charge z the emitted m/z is (M/z - L)/z. That is correct only for z = 1.
- **Trigger:** Example: peptide KS, link position 0, y ions, charge 2, losses enabled. y1 (S) at z=2 has its intact peak at 53.5286. The water-loss peak is emitted at 17.7590 instead of 44.5233. In practice, any OpenPepXL search with default parameters triggers it: - ions:neutral_losses defaults to true (OpenPepXLAlgorithm.cpp:102, :155) and is passed to both generators (:348, :365). - Linear ions are generated with charge 2, which loops z = 1..2 (SimpleTSGXLMS.cpp:121; TheoreticalSpectrumGeneratorXLMS.cpp:159). The calls are at OpenPepXLAlgorithm.cpp:471 and :475 (SimpleTSGXLMS, main score) and :625 and :630 (TheoreticalSpectrumGeneratorXLMS). - Every charge-2 y/x/z ion that contains S, T, E or D (water) or R, K, Q or N (ammonia) gets a misplaced loss peak.
- **Consequence:** Charge-2 suffix loss peaks land at roughly half their correct m/z. Real loss peaks in the spectrum go unmatched, and occasional random matches appear. The number of theoretical peaks stays the same. The OpenPepXL main score (match-odds from SimpleTSGXLMS) and the full-spectrum sub-scores and fragment annotations are silently distorted, with no error. Intact, prefix, charge-1 and cross-link ions are correct, so the distortion is systematic but limited in scope. Measured evidence: the ci.3 fix, applied together with CPP-043, changed OpenPepXL scores and fragment annotations in 3 installed TOPP regression tests (23944b6). CPP-042's effect alone on identifications was never measured.
- **Who hits it:** TOPP OpenPepXL: every default search on ordinary cross-link data. OpenPepXLAlgorithm.cpp is the only in-tree caller of getLinearIonSpectrum. It is likely to hit every OpenPepXL user, but that user base is small. Two reach paths claimed earlier are wrong: - ProForma cross-link spectra call only getXLinkIonSpectrum (ProForma.cpp:2851-2852). That path never reaches addLinearPeaks_, which is called only from getLinearIonSpectrum (TheoreticalSpectrumGeneratorXLMS.cpp:163-183; SimpleTSGXLMS.cpp:125-145). - The pyOpenMS getLinearIonSpectrum bindings (bind_misc.cpp:3658, :4466) build an empty AASequence inside the lambda and take no peptide argument. Python users therefore cannot reach the defect with a real sequence. Otherwise reachable only from the C++ API.

> **Skeptic's correction:** - Reach is wrong on pyOpenMS. The direct getLinearIonSpectrum bindings are unusable, as the draft says. But pyOpenMS binds OpenPepXLAlgorithm with run() (bind_misc.cpp:3162-3183), so Python users hit the defect through the algorithm. 'Otherwise reachable only from the C++ API' should say C++ API and pyOpenMS OpenPepXLAlgorithm.run. - Consequence understates the effect. - The SimpleTSGXLMS linear spectra also drive the candidate pre-filter: candidates with fewer than 2 matched linear peaks are dropped (OpenPepXLAlgorithm.cpp:496-504) before match-odds (:545, :553). Misplaced loss peaks can therefore remove or keep candidates, not only shift scores and annotations. - 'Roughly half their correct m/z' is imprecise: correct is M/2 - L/2 and buggy is M/4 - L/2, always below half (40% in the KS example). - Default scope: OpenPepXL generates only b and y ions by default (ions:x_ions and ions:z_ions false, :99, :101), so default runs are affected only through y-ion H2O/NH3 losses. The residue sets (D/E/S/T water, K/N/Q/R ammonia) are confirmed by ResidueDB.cpp:154-221 and the loss_db_ build at TheoreticalSpectrumGeneratorXLMS.cpp:88-119. - The '3 installed TOPP regression tests' are the three output diffs (_out_1, _out_3, _out_4) of one TOPP_OpenPepXL_1 run (src/tests/topp/CMakeLists.txt:3415-3421), not three independent inputs. - The attribution caveat is justified. OpenPepXL sets add_isotopes=true, max_isotope=2 and add_precursor_peaks=true on TheoreticalSpectrumGeneratorXLMS (:350-352), so CPP-043's precursor isotope-spacing change is live in the same run. - Existing class tests already run add_losses on charge-3 linear spectra in both generators (TheoreticalSpectrumGeneratorXLMS_test.cpp:132-197; SimpleTSGXLMS_test.cpp:137-152, 196-214). They assert only peak counts, ion names and charge counts, which is why the bug went uncaught and why the fix keeps them passing.

### The fix

The fix passes the charged mass (mono_weight) instead of the m/z (pos) to the loss helper in the suffix branch, exactly as the prefix branch already does. - 181dadf: TheoreticalSpectrumGeneratorXLMS.cpp:311-312, a comment plus `addLinearIonLosses_(..., mono_weight, ...)`. - 9b56872: SimpleTSGXLMS.cpp:230, `addLosses_(spectrum, mono_weight, charge, backward_losses[i])`. - 9b56872 also added the SimpleTSGXLMS_test section '[EXTRA] charge-two suffix losses use neutral masses' (lines 20-21 includes, 599-623 section). For PEPTIDES with y ions and losses at charge 2, it checks that every charge-2 peak has a charge-1 counterpart at 2*mz - proton mass. The buggy code fails this for the loss peaks. 181dadf also changed three precursor isotope-companion lines in the same file. Those belong to CPP-043 and are not part of this fix.

*State:* Not in 4f5c86f; reverted, finding kept open. - Committed in 181dadf (TheoreticalSpectrumGeneratorXLMS.cpp) and 9b56872 (SimpleTSGXLMS.cpp plus test), and shipped in core-v4.0.0-ci.3. - Reverted in 23944b6 together with CPP-043 and the charge-two test. - Reason: against ci.3 the installed console regression suite failed 107 of 2047 tests, which had passed at ci.2. Three of those failures were OpenPepXL score and fragment-annotation changes. The maintainer chose to restore the ci.2 OpenPepXL output exactly for ci.4 until a coordinated, reviewed reference update. Including CPP-043 in the revert was a scoping call. - The 23944b6 message says the installed regression suite had not yet been rerun against that revision. - The 4f5c86f CHANGELOG (lines 9-11, 23-25) records the revert. - The Rust port currently reproduces the buggy expression for compatibility.

**Fix:** `src/openms/source/CHEMISTRY/SimpleTSGXLMS.cpp` (9b56872^ → 9b56872)

```diff
--- a/src/openms/source/CHEMISTRY/SimpleTSGXLMS.cpp
+++ b/src/openms/source/CHEMISTRY/SimpleTSGXLMS.cpp
@@ -227,7 +227,7 @@ namespace OpenMS
 
         if (add_losses_)
         {
-          addLosses_(spectrum, pos, charge, backward_losses[i]);
+          addLosses_(spectrum, mono_weight, charge, backward_losses[i]);
         }
         spectrum.emplace_back(pos, charge);
 
```

**Fix:** `src/openms/source/CHEMISTRY/TheoreticalSpectrumGeneratorXLMS.cpp` (181dadf^ → 181dadf)

```diff
--- a/src/openms/source/CHEMISTRY/TheoreticalSpectrumGeneratorXLMS.cpp
+++ b/src/openms/source/CHEMISTRY/TheoreticalSpectrumGeneratorXLMS.cpp
@@ -308,7 +308,8 @@ namespace OpenMS
         addPeak_(spectrum, charges, ion_names, pos, intensity, res_type, frag_index, charge, ion_type);
         if (add_losses_)
         {
-          addLinearIonLosses_(spectrum, charges, ion_names, pos, res_type, frag_index, intensity, charge, ion_type, backward_losses[i]);
+          // pass the charged mass as in the prefix branch, not pos: the helper subtracts the loss and divides by charge itself
+          addLinearIonLosses_(spectrum, charges, ion_names, mono_weight, res_type, frag_index, intensity, charge, ion_type, backward_losses[i]);
         }
         if (add_isotopes_ && max_isotope_ >= 2) // add second isotopic peak with fast method, if two or more peaks are asked for
         {
```

**Test:** `src/tests/class_tests/openms/source/SimpleTSGXLMS_test.cpp` (9b56872^ → 9b56872)

```diff
--- a/src/tests/class_tests/openms/source/SimpleTSGXLMS_test.cpp
+++ b/src/tests/class_tests/openms/source/SimpleTSGXLMS_test.cpp
@@ -17,6 +17,8 @@
 #include <OpenMS/CONCEPT/Constants.h>
 #include <OpenMS/ANALYSIS/XLMS/OPXLDataStructs.h>
 #include <iostream>
+#include <algorithm>
+#include <cmath>
 
 
 START_TEST(SimpleTSGXLMS, "$Id$")
@@ -594,4 +596,30 @@ END_SECTION
 
 delete ptr;
 
+START_SECTION(([EXTRA] charge-two suffix losses use neutral masses))
+  SimpleTSGXLMS generator;
+  Param parameters = generator.getParameters();
+  parameters.setValue("add_b_ions", "false");
+  parameters.setValue("add_y_ions", "true");
+  parameters.setValue("add_losses", "true");
+  generator.setParameters(parameters);
+  AASequence sequence = AASequence::fromString("PEPTIDES");
+  vector<SimpleTSGXLMS::SimplePeak> peaks;
+  generator.getLinearIonSpectrum(peaks, sequence, 0, 2);
+  Size checked = 0;
+  for (const auto& peak : peaks)
+  {
+    if (peak.charge != 2) continue;
+    // Charge-one and charge-two versions of the same fragment differ by one proton.
+    const double charge_one_mz = 2 * peak.mz - Constants::PROTON_MASS_U;
+    const bool found = std::any_of(peaks.begin(), peaks.end(), [&](const auto& candidate)
+    {
+      return candidate.charge == 1 && std::abs(candidate.mz - charge_one_mz) < 1e-6;
+    });
+    TEST_TRUE(found)
+    ++checked;
+  }
+  TEST_EQUAL(checked > sequence.size() - 1, true) // neutral-loss peaks were included
+END_SECTION
+
 END_TEST
```

### Assessment

- **Behaviour change:** Yes, deliberately. In both generators, H2O and NH3 loss peaks of x/y/z ions at charge 2 or higher move to the correct (M - L)/z. Intact, prefix, charge-1 and cross-link ion peaks are unchanged. OpenPepXL scores, candidate rankings and fragment annotations change for default runs, and the OpenPepXL TOPP reference outputs must be regenerated. No change to accepted inputs or exceptions.
- **Concerns:** - The patch itself is minimal and algebraically correct: it matches the prefix branch, every other loss call, and the header documentation of the helper argument as the ion's mass. - It was bundled with CPP-043 in 181dadf and reverted together with it, so the 3 regression changes were never attributed to one finding. Re-landing CPP-042 alone needs its own regression run. - Test coverage is incomplete: the only test covered SimpleTSGXLMS, not TheoreticalSpectrumGeneratorXLMS, and the revert deleted it. - The test checks charge-1 versus charge-2 consistency, not absolute m/z values. Adding the KS worked example would pin both generators. - Re-landing requires a reviewed update of the OpenPepXL references, not a bulk regeneration. The Rust port's compatibility behaviour must follow.
- **Skeptic on the fix (yes):** - The formula fix is complete for both generators. Every other loss call already passes the charged mass (TSG-XLMS :277, :487, :527, :1038, :1081; SimpleTSGXLMS :197, :349, :385, :634, :674), and both header docs call the argument the ion's monoisotopic mass (TheoreticalSpectrumGeneratorXLMS.h:185, SimpleTSGXLMS.h:182). - Gaps the draft only partly states: - The upstream PR's reference update must be generated for the CPP-042-only change. The ci.3 outputs also contain CPP-043's precursor isotope change, which is active in OpenPepXL, so they cannot be reused. The affected references are OpenPepXL_output.xquest.xml, OpenPepXL_output.mzid and OpenPepXL_output.idXML. - Review should cover changed candidate survival at the <2 linear-match pre-filter, not only score deltas. - The removed 9b56872 test covers only SimpleTSGXLMS y ions. It checks charge-2 against charge-1 consistency (the buggy code does fail it), so it cannot catch an error shared by both charges. An absolute m/z check such as the KS example (water-loss peak at 44.5233, not 17.7590) should be added for both generators. - Confirmed: 181dadf and 9b56872 are ancestors of core-v4.0.0-ci.3 (tag commit c77ff14), whose files carry the fixed lines. 23944b6 is not in ci.3 and restores ci.2 bytes in 4f5c86f.
- **Upstream patch:** Applies verbatim. TheoreticalSpectrumGeneratorXLMS.cpp, SimpleTSGXLMS.cpp and SimpleTSGXLMS_test.cpp at origin/develop are byte-identical to core-v4.0.0-ci.2, which matches the fix commits' parents in these regions. The defect sits at lines 311 and 230 upstream too. An upstream pull request should: - take only 181dadf's line-311 hunk, leaving the CPP-043 isotope hunks out or proposing them separately - take 9b56872's source and test hunks, and add a TheoreticalSpectrumGeneratorXLMS test - include the regenerated OpenPepXL TOPP test references, because upstream OpenPepXL output changes the same way
- **Skeptic's notes:** Verified at origin/develop. - TheoreticalSpectrumGeneratorXLMS.cpp:305/311 passes pos into a helper that does (arg - loss)/charge (:567/:570, :586/:589). SimpleTSGXLMS.cpp:226/230 does the same with the helper at :460/:465. - OpenPepXL defaults ions:neutral_losses=true (:102, :155), passed to both generators (:348, :365), with charge-2 linear calls at :471, :475, :625 and :630. - getLinearIonSpectrum has no other in-tree caller (OpenPepXLLF does not call it). The ProForma cross-link path uses only getXLinkIonSpectrum (ProForma.cpp:2851-2852), and addLinearPeaks_ is reached only from getLinearIonSpectrum. - Byte identity: TSG-XLMS.cpp is equal at origin/develop, ci.2, 181dadf^ and 4f5c86f. SimpleTSGXLMS.cpp and SimpleTSGXLMS_test.cpp are equal at origin/develop, ci.2, 9b56872^ and 4f5c86f. So all hunks apply upstream verbatim. - Hunk ranges checked against the diffs: 181dadf 311-312 (CPP-043 hunks at 621/652/682 correctly excluded); 9b56872 SimpleTSGXLMS.cpp 230; test 20-21 (includes) and 599-624 (section 599-623 plus a trailing blank line). - KS worked example recomputed: intact 53.5286, correct water loss 44.5233, buggy 17.7590. - P0 holds: silent wrong theoretical spectra in every default OpenPepXL search.

**Decision (confirmed 2026-09-14):** Re-land alone in a later cycle: only the one-line fix in both generators, absolute m/z tests for both, a CPP-042-only OpenPepXL_1 run and a reviewed reference update.
