# The 75 unverified high-priority C++ findings

These are the findings from the Rust port's C++ defect list that the ranking of 2026-09-14 placed at P0 or P1 and that are still present in upstream OpenMS, but whose adversarial check never ran: the workflow stopped at the spend limit before either of the two skeptics per finding reported. Another 25 P0/P1 findings were upheld by the skeptics and one was contested; they are not in this list.

- **Upstream OpenMS:** all 75 are present at `origin/develop`; each entry quotes the code with file and line.
- **OpenMS4 Core:** all 75 are fixed. The outcome of every finding is in [cpp-issues-review.md](cpp-issues-review.md).
- **Priority:** 14 P0 and 61 P1.
- **Proof:** 30 have a Core regression test that fails on the pre-fix code, 3 an executed reproduction, and 42 rest on code reading alone.
- **Classification:** one classifier agent per finding, without the skeptic pass. Treat static-only entries as the least certain.

| Impact | P0 | P1 |
| --- | ---: | ---: |
| memory-safety | 13 | 9 |
| data-loss | 0 | 13 |
| wrong-result | 1 | 31 |
| crash-valid-input | 0 | 8 |

## How the entries were ranked

- **P0:** a memory-safety defect reachable from input files or ordinary API use; a silent wrong scientific result (masses, scores, identifications, quantities, FDR, retention times) on valid, commonly used input; or silent data loss when writing a standard format from valid data.
- **P1:** a wrong result or data loss on valid but uncommon input; a crash or uncaught exception on valid input; or a memory-safety defect reachable only through API misuse.
- **Proof:** *regression-test* means a class test in OpenMS4 Core at `4f5c86f` exercises the defect and would fail on the pre-fix code; *executed-probe* means the Rust log reports a run that showed the wrong behaviour; *static-only* means a code-reading argument only.
- **Input:** *valid-common* and *valid-edge* are valid files or calls, common or unusual; *malformed* is invalid input; *api-misuse* is a call that breaks the API's preconditions.
- **Order:** priority, then impact (memory safety, data loss, wrong result, crash), then proof strength.

## Summary

| # | Finding | Title | Priority | Impact | Input | Proof |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | [CPP-089](#cpp-089) | BaseFeature::sortPeptideIdentifications comparator is not a strict weak ordering | P0 | memory-safety | valid-edge | regression-test |
| 2 | [CPP-170](#cpp-170) | mzData checks missing and short arrays after unsafe indexing | P0 | memory-safety | malformed | regression-test |
| 3 | [CPP-171](#cpp-171) | mzData writer emits scan modes its reader does not recognize | P0 | memory-safety | valid-edge | regression-test |
| 4 | [CPP-173](#cpp-173) | mzXML release decode reads beyond short peak payload | P0 | memory-safety | malformed | regression-test |
| 5 | [CPP-005](#cpp-005) | Truncated fragment distribution is indexed at full input length | P0 | memory-safety | valid-edge | static-only |
| 6 | [CPP-011](#cpp-011) | Mass trace detection reuses stale metadata-array state | P0 | memory-safety | valid-edge | static-only |
| 7 | [CPP-120](#cpp-120) | mzML list `count` attribute drives an unvalidated container reserve (the same fix closed a numpress declared-length out-of-bounds read) | P0 | memory-safety | malformed | static-only |
| 8 | [CPP-148](#cpp-148) | MzTab column-unit metadata parses its key as an index | P0 | memory-safety | malformed | static-only |
| 9 | [CPP-164](#cpp-164) | Mascot query index guard accepts one-past-end | P0 | memory-safety | malformed | static-only |
| 10 | [CPP-168](#cpp-168) | mzIdentML reader dereferences missing PeptideSequence child | P0 | memory-safety | valid-edge | static-only |
| 11 | [CPP-169](#cpp-169) | mzIdentML substitution position is used as unchecked string index | P0 | memory-safety | malformed | static-only |
| 12 | [CPP-191](#cpp-191) | Array hydration lacks pair length and role validation | P0 | memory-safety | malformed | static-only |
| 13 | [CPP-199](#cpp-199) | Metadata readers accept invalid negative activation enum values below -1 | P0 | memory-safety | malformed | static-only |
| 14 | [CPP-166](#cpp-166) | Mascot MGF loader carries precursor and RT fields between blocks | P0 | wrong-result | valid-common | regression-test |
| 15 | [CPP-207](#cpp-207) | SpectrumAccessSqMass unchecked view positions permit out-of-bounds access | P1 | memory-safety | api-misuse | regression-test |
| 16 | [CPP-224](#cpp-224) | Gumbel maximum-likelihood fitting reads beyond a short weight vector | P1 | memory-safety | api-misuse | regression-test |
| 17 | [CPP-077](#cpp-077) | rasterizeIMFrame multiplies the bin counts without an overflow check | P1 | memory-safety | api-misuse | static-only |
| 18 | [CPP-091](#cpp-091) | Mixed isHigherScoreBetter flags make the sort comparator asymmetric | P1 | memory-safety | api-misuse | static-only |
| 19 | [CPP-096](#cpp-096) | Feature::getConvexHull() is a const method that lazily mutates the object and hands out a mutable reference | P1 | memory-safety | api-misuse | static-only |
| 20 | [CPP-141](#cpp-141) | DataValue::operator double() reads the union's double member for a non-numeric value (imzML call site of CPP-058) | P1 | memory-safety | api-misuse | static-only |
| 21 | [CPP-181](#cpp-181) | SqliteConnector permits copying an owned database handle | P1 | memory-safety | api-misuse | static-only |
| 22 | [CPP-204](#cpp-204) | MSDataSqlConsumer owning raw pointer leaks during failed construction and can be shallow-copied | P1 | memory-safety | api-misuse | static-only |
| 23 | [CPP-212](#cpp-212) | OpenSwath drift filtering dereferences missing or misaligned mobility arrays | P1 | memory-safety | valid-edge | static-only |
| 24 | [CPP-147](#cpp-147) | MzTab PSM optional columns are dropped on load | P1 | data-loss | valid-common | regression-test |
| 25 | [CPP-155](#cpp-155) | qcML loses units across its own store/load | P1 | data-loss | valid-edge | regression-test |
| 26 | [CPP-156](#cpp-156) | qcML table writer discards its normalized row copy | P1 | data-loss | valid-edge | regression-test |
| 27 | [CPP-159](#cpp-159) | qcML writer and reader disagree on set-member CV accession | P1 | data-loss | valid-edge | regression-test |
| 28 | [CPP-172](#cpp-172) | Streaming mzML consumer references header entries declared only for first record | P1 | data-loss | valid-edge | regression-test |
| 29 | [CPP-214](#cpp-214) | MSDataSqlConsumer full metadata discards supplied experimental settings and addRun suppresses accumulated snapshot | P1 | data-loss | valid-edge | regression-test |
| 30 | [CPP-218](#cpp-218) | Positive-accuracy Numpress encoding destroys one- and two-point coordinate arrays | P1 | data-loss | valid-edge | regression-test |
| 31 | [CPP-219](#cpp-219) | Chromatogram precursor reload drops supplemental activation metadata | P1 | data-loss | valid-edge | regression-test |
| 32 | [CPP-145](#cpp-145) | MzTab parameter rendering fails to quote a bare comma | P1 | data-loss | valid-edge | static-only |
| 33 | [CPP-151](#cpp-151) | MzTab-M exporter changes metadata keys before lookup | P1 | data-loss | valid-edge | static-only |
| 34 | [CPP-167](#cpp-167) | mzIdentML writer places C-terminal modification at last-residue location | P1 | data-loss | valid-edge | static-only |
| 35 | [CPP-193](#cpp-193) | Spectrum/chromatogram IDs and peptide sequence remain unescaped SQL values | P1 | data-loss | valid-edge | static-only |
| 36 | [CPP-227](#cpp-227) | Download filename selection does not prevent concurrent overwrite | P1 | data-loss | valid-edge | static-only |
| 37 | [CPP-008](#cpp-008) | ProForma modified ranges omit their residue annotations | P1 | wrong-result | valid-edge | regression-test |
| 38 | [CPP-009](#cpp-009) | Ambiguous mass checks ignore modifications on candidates | P1 | wrong-result | valid-edge | regression-test |
| 39 | [CPP-012](#cpp-012) | Smoothed area accumulation uses raw peak intensities | P1 | wrong-result | valid-common | regression-test |
| 40 | [CPP-015](#cpp-015) | Cross-link mass depends on endpoint traversal order | P1 | wrong-result | valid-edge | regression-test |
| 41 | [CPP-154](#cpp-154) | pepXML fixed protein C-terminal modification misses terminal branch | P1 | wrong-result | valid-edge | regression-test |
| 42 | [CPP-157](#cpp-157) | qcML removeAllAttachments omits set-only entries | P1 | wrong-result | valid-edge | regression-test |
| 43 | [CPP-158](#cpp-158) | qcML map2csv emits misaligned rows when a column is missing | P1 | wrong-result | valid-edge | regression-test |
| 44 | [CPP-160](#cpp-160) | qcML TIC slump percentage truncates before multiplication | P1 | wrong-result | valid-common | regression-test |
| 45 | [CPP-174](#cpp-174) | mzXML precursor value and window width depend on SAX chunking | P1 | wrong-result | valid-edge | regression-test |
| 46 | [CPP-178](#cpp-178) | MSstats missing design pair silently uses sample0 | P1 | wrong-result | valid-edge | regression-test |
| 47 | [CPP-180](#cpp-180) | MSstats aggregation collapses equal intensities at distinct times | P1 | wrong-result | valid-edge | regression-test |
| 48 | [CPP-208](#cpp-208) | SpectrumAccessSqMass bulk read does not preserve the configured view order or duplicates | P1 | wrong-result | valid-edge | regression-test |
| 49 | [CPP-220](#cpp-220) | Negative initial linear-Numpress coordinates can wrap during sqMass writing | P1 | wrong-result | valid-edge | regression-test |
| 50 | [CPP-228](#cpp-228) | Squaring Gumbel negative log likelihood can change the optimum | P1 | wrong-result | valid-edge | regression-test |
| 51 | [CPP-001](#cpp-001) | DateTime ignores failed calendar conversion | P1 | wrong-result | valid-edge | executed-probe |
| 52 | [CPP-196](#cpp-196) | SWATH selection stops at a matching chromatogram precursor NULL ID | P1 | wrong-result | valid-edge | executed-probe |
| 53 | [CPP-004](#cpp-004) | trimLeft does nothing when every peak is below cutoff | P1 | wrong-result | valid-edge | static-only |
| 54 | [CPP-006](#cpp-006) | Interpolation overload resizes and then appends coordinates | P1 | wrong-result | valid-edge | static-only |
| 55 | [CPP-007](#cpp-007) | EMG tail expression overflows before its asymptotic branch | P1 | wrong-result | valid-edge | static-only |
| 56 | [CPP-016](#cpp-016) | Count-only mzML loading can still decode peak arrays | P1 | wrong-result | valid-edge | static-only |
| 57 | [CPP-072](#cpp-072) | DRange::united of two empty ranges returns the universal range | P1 | wrong-result | valid-edge | static-only |
| 58 | [CPP-080](#cpp-080) | sortByPositionPresorted trusts is_sorted and feeds std::inplace_merge an unsorted range | P1 | wrong-result | valid-edge | static-only |
| 59 | [CPP-090](#cpp-090) | The same comparator mutates its arguments, so hits are sorted only where the sort happens to compare | P1 | wrong-result | valid-edge | static-only |
| 60 | [CPP-115](#cpp-115) | ConsensusMap::appendRows pairs column headers by position, not by column index | P1 | wrong-result | valid-edge | static-only |
| 61 | [CPP-116](#cpp-116) | ConsensusMap::setPrimaryMSRunPath writes by position through a default-inserting map | P1 | wrong-result | valid-edge | static-only |
| 62 | [CPP-144](#cpp-144) | Quoted commas split a MzTab modification-list entry | P1 | wrong-result | valid-edge | static-only |
| 63 | [CPP-146](#cpp-146) | MzTab score-by-run header order differs from row order | P1 | wrong-result | valid-edge | static-only |
| 64 | [CPP-153](#cpp-153) | pepXML drops a uniquely resolved undeclared modification | P1 | wrong-result | valid-edge | static-only |
| 65 | [CPP-162](#cpp-162) | Percolator enzyme features use unmapped protein-terminal markers | P1 | wrong-result | valid-common | static-only |
| 66 | [CPP-192](#cpp-192) | Blob hydration assigns objects by SQL row encounter order instead of record identity | P1 | wrong-result | valid-edge | static-only |
| 67 | [CPP-206](#cpp-206) | MSDataSqlConsumer changes buffered records to the next run ID | P1 | wrong-result | valid-edge | static-only |
| 68 | [CPP-132](#cpp-132) | ImzMLWriter::store cannot write a metadata-only continuous dataset | P1 | crash-valid-input | valid-edge | regression-test |
| 69 | [CPP-010](#cpp-010) | Integer mass decomposition can loop without progress | P1 | crash-valid-input | valid-edge | executed-probe |
| 70 | [CPP-143](#cpp-143) | Negative CHEMMOD identifiers fail mzTab modification-cell parsing | P1 | crash-valid-input | valid-edge | static-only |
| 71 | [CPP-161](#cpp-161) | Percolator loader requires FileName through an unchecked map lookup | P1 | crash-valid-input | valid-common | static-only |
| 72 | [CPP-163](#cpp-163) | Percolator writer and loader disagree on trailing protein-list width | P1 | crash-valid-input | valid-common | static-only |
| 73 | [CPP-190](#cpp-190) | Default handler writing reads an uninitialized SQL batch size | P1 | crash-valid-input | valid-edge | static-only |
| 74 | [CPP-198](#cpp-198) | Recreating tables on a used handler retains counters from the deleted database | P1 | crash-valid-input | valid-edge | static-only |
| 75 | [CPP-200](#cpp-200) | SqMassFile transform issues an extra empty selected-read batch | P1 | crash-valid-input | valid-edge | static-only |

## P0: 14 findings

<a id="cpp-089"></a>
### CPP-089: BaseFeature::sortPeptideIdentifications comparator is not a strict weak ordering

**P0** · memory-safety · valid-edge · proof: regression-test  
**Affected:** src/openms/source/KERNEL/BaseFeature.cpp:125-143 (the lambda; the empty branch is 128-131)

**Why it is a bug.** A feature with two or more identifications, one of them without hits but carrying metadata (valid featureXML), makes the comparator read getHits()[0] of an empty vector: a null or out-of-bounds read that normally crashes. Two default-empty identifications also break asymmetry (undefined behaviour in std::sort). This is a memory-safety defect reachable from input files, hence P0.

**Who reaches it.** FeatureLinkerUnlabeledQT with algorithm:use_identifications=true (QTClusterFinder.cpp:106, run on a copy of every input feature that has IDs). ProteomicsLFQ through PipEchoAlgorithm (PIPECHO/Impl.cpp:76 prepare_feature, run on every input feature). Any C++ caller of BaseFeature::sortPeptideIdentifications; it is not bound in pyOpenMS. IDMapper itself skips hit-less IDs (IDMapper.cpp:339, :436), so the trigger is a featureXML produced or filtered elsewhere.

**Upstream evidence.** origin/develop src/openms/source/KERNEL/BaseFeature.cpp:125-143: '[](PeptideIdentification& p1, PeptideIdentification& p2) {p1.sort();p2.sort(); if (p1.empty()) { return true; } if (p2.empty()) { return false; } if (p1.isHigherScoreBetter()) { return p1.getHits()[0].getScore() < p2.getHits()[0].getScore(); } ...'. PeptideIdentification.cpp:210-217 makes empty() true only when id_, hits_ and score_type_ are all empty, so an identification with an identifier but no hits passes both checks. FeatureXMLHandler.cpp:819-822 pushes such a hit-less identification onto the feature. The pre-fix code at core-v4.0.0-ci.2 is byte-identical to develop.

**Proof.** OpenMS4 core 4f5c86f, src/tests/class_tests/openms/source/BaseFeature_test.cpp, section START_SECTION((sortPeptideIdentifications())), lines 409-437. Commit b6dd412 gives ids[2] an identifier and score type but no hits. With the pre-fix comparator (identical to develop), every comparison involving ids[2] evaluates getHits()[0] on an empty vector.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf src/openms/source/KERNEL/BaseFeature.cpp (comparator keys on getHits().empty(), 'return !p2.getHits().empty();'); test in b6dd412

<a id="cpp-170"></a>
### CPP-170: mzData checks missing and short arrays after unsafe indexing

**P0** · memory-safety · malformed · proof: regression-test  

**Why it is a bug.** A spectrum with one binary array, or with an intensity or supplemental array shorter than the m/z array, causes heap out-of-bounds reads of precisions_ and decoded arrays. OpenMS's own mzData writer can produce the short supplemental-array case. The rubric makes memory-safety reachable from input files P0, though mzData is now a rarely used format.

**Who reaches it.** MzDataFile::load and FileHandler .mzData loading; FileConverter and TOPP tools reading mzData via FileHandler; pyOpenMS MzDataFile

**Upstream evidence.** src/openms/source/FORMAT/HANDLERS/MzDataHandler.cpp: - :522 `if (precisions_[0] == "32")` and :527 `if (precisions_[1] == "32")` run before the guard at :533 `if (data_to_decode_.size() < 2) return;`. - :537-541 a length mismatch only calls error(LOAD,...); :545 then sets `peak_count_ = peak_count_mz;`. - :561 reads `decoded_list_[1][n]` past a shorter intensity array. - :572 `precisions_[2 + i] == "64" ? decoded_double_list_[2 + i][n] : decoded_list_[2 + i][n]` is unchecked. - :142 `data_to_decode_.back() += transcoded_chars;` and :482 `precisions_[i]` are also unguarded. - The writer at :1035-1046 only logs a FloatDataArray length mismatch and still writes mda.size() values.

**Proof.** MzDataFile_test.cpp, section "regression: incomplete binary arrays and MSn scan modes". The short_intensity case (2 m/z values, 1 intensity) expects 1 peak; pre-fix code reads decoded_list_[1][1] out of bounds and returns 2 peaks. The one-array case reads precisions_[1] out of bounds before the size guard.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf (array pairing, count and length checks) and c77ff14 (bounded reserve), src/openms/source/FORMAT/HANDLERS/MzDataHandler.cpp

<a id="cpp-171"></a>
### CPP-171: mzData writer emits scan modes its reader does not recognize

**P0** · memory-safety · valid-edge · proof: regression-test  

**Why it is a bug.** Take an MSn spectrum with a ScanMode value outside the reader's list, such as OpenMS's own EMC or TDF spellings, loaded as the first spectrum or after skipped ones. back() on the empty experiment writes the scan mode before the reserved buffer (heap corruption), or dereferences null when count=0. Otherwise it silently overwrites the previous spectrum's scan mode, and ABSORPTION, EMC and TDF are lost on round-trip. Memory-safety from valid files is P0, although mzData and these scan modes are rare.

**Who reaches it.** MzDataFile::load and FileHandler .mzData loading; FileConverter; pyOpenMS MzDataFile

**Upstream evidence.** src/openms/source/FORMAT/HANDLERS/MzDataHandler.cpp: - The writer at :919-929 emits value="PhotodiodeArrayDetector", "EnhancedMultiplyChargedScan" and "TimeDelayedFragmentationScan". - The reader cvParam_ at :1089-1131 lacks these three values. - The fallback at :1134-1136 is `if (spec_.getMSLevel() >= 2) { exp_->getSpectra().back().getInstrumentSettings().setScanMode(InstrumentSettings::ScanMode::MSNSPECTRUM); }`. - spec_ is only added later, at :449 `exp_->addSpectrum(spec_);`. Skipped spectra are never added (:397-400 MS-level filter).

**Proof.** MzDataFile_test.cpp, section "regression: incomplete binary arrays and MSn scan modes". The first spectrum has msLevel=2 and an unknown ScanMode and expects MSNSPECTRUM; pre-fix code calls back() on the empty experiment and leaves the current spectrum UNKNOWN. The EnhancedMultiplyChargedScan, TimeDelayedFragmentationScan and PhotodiodeArrayDetector cases expect EMC, TDF and ABSORPTION, which the pre-fix reader does not recognise.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf, src/openms/source/FORMAT/HANDLERS/MzDataHandler.cpp (reader accepts the writer's spellings; fallback sets spec_)

<a id="cpp-173"></a>
### CPP-173: mzXML release decode reads beyond short peak payload

**P0** · memory-safety · malformed · proof: regression-test  

**Why it is a bug.** Release builds define NDEBUG, so the assert disappears and a peaksCount larger than the decoded payload makes the loop read past the heap vector. The bogus values become peaks, or the read crashes. peaksCount="-1" wraps to 4294967295. This is an out-of-bounds read reachable from input files, so P0.

**Who reaches it.** MzXMLFile::load and FileHandler .mzXML loading; FileConverter and every TOPP tool that loads spectra through FileHandler; pyOpenMS MzXMLFile

**Upstream evidence.** src/openms/source/FORMAT/HANDLERS/MzXMLHandler.cpp:301 `spectrum_data_.back().peak_count_ = attributeAsInt_(attributes, s_peakscount_);`. peak_count_ is `UInt` (MzXMLHandler.h:120). At :1175 and :1202 `assert(data.size() == 2 * spectrum_data.peak_count_);` is the only check, followed at :1177 and :1204 by `for (Size n = 0; n < (2 * spectrum_data.peak_count_); n += 2)`, which indexes data[n] and data[n + 1].

**Proof.** MzXMLFile_test.cpp, section "regression : SAX chunk boundaries and mismatched peak counts". It loops over peaksCount "2", "0" and "-1" with a one-pair payload and expects Exception::ParseError. Pre-fix code throws nothing: release builds read past the vector and debug builds hit the assert abort.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf (runtime payload-length check) and c77ff14 (negative peaksCount rejected, bounded reserve), src/openms/source/FORMAT/HANDLERS/MzXMLHandler.cpp

<a id="cpp-005"></a>
### CPP-005: Truncated fragment distribution is indexed at full input length

**P0** · memory-safety · valid-edge · proof: static-only  
**Affected:** [`src/openms/source/CHEMISTRY/ISOTOPEDISTRIBUTION/CoarseIsotopePatternGenerator.cpp`, lines 450–520], `calcFragmentIsotopeDist_`.

**Why it is a bug.** If the generator's max_isotope_ is nonzero but shorter than the fragment distribution, result is resized to r_max yet written up to the fragment length. The estimateForFragmentFrom* functions build 3-peak distributions with an internal solver(max(precursor_isotopes)+1) but truncate with this->max_isotope_, so CoarseIsotopePatternGenerator(2).estimateForFragmentFromPeptideWeight(2000, 1000, {0,1,2}) writes result[2] past a 2-element vector. That is a heap out-of-bounds write through ordinary documented API with valid arguments, hence P0, although no TOPP tool calls these functions.

**Who reaches it.** CoarseIsotopePatternGenerator::calcFragmentIsotopeDist, estimateForFragmentFromPeptideWeight, ...PeptideWeightAndS, ...RNAWeight, ...DNAWeight, ...WeightAndComp, and EmpiricalFormula::getConditionalFragmentIsotopeDist with a solver whose max_isotope is below max(precursor_isotopes)+1. All are bound in pyOpenMS (bind_chemistry.cpp:338 setMaxIsotope, 372-377, 654). No in-tree TOPP caller.

**Upstream evidence.** origin/develop src/openms/source/CHEMISTRY/ISOTOPEDISTRIBUTION/CoarseIsotopePatternGenerator.cpp:461-469: `r_max = fragment_isotope_dist.size(); if (max_isotope_ != 0 && r_max > max_isotope_) r_max = max_isotope_; result.resize(r_max);` then 509-519: `for (Size i = 0; i < fragment_isotope_dist.size(); ++i) { ... result[i].setIntensity(result[i].getIntensity() + comp_fragment_isotope_dist[*precursor_itr-i].getIntensity()); ... result[i].setIntensity(result[i].getIntensity() * fragment_isotope_dist[i].getIntensity()); }`

**Proof.** The Rust log claims no sanitizer run. OpenMS4 CoarseIsotopeDistribution_test.cpp is unchanged ci.2..4f5c86f, and every existing fragment test calls setMaxIsotope(0) first (lines 360, 477, 559, 608, 669, 688), so none takes the truncating path.

**Fix in OpenMS4 Core.** OpenMS4 core 1beb468, src/openms/source/CHEMISTRY/ISOTOPEDISTRIBUTION/CoarseIsotopePatternGenerator.cpp (accumulation loop bounded by r_max)

<a id="cpp-011"></a>
### CPP-011: Mass trace detection reuses stale metadata-array state

**P0** · memory-safety · valid-edge · proof: static-only  
**Affected:** [`src/openms/source/FEATUREFINDER/MassTraceDetection.cpp`], discovery at 80–144, invocation at 482–485 and reads at 518–531; [`MassTraceDetection.h`], member initialization at 181–184 and 204–206.

**Why it is a bug.** Reuse one detector: run it on centroided data with FWHM_ppm or ion-mobility float arrays, then on spectra without them. The stale flags survive and the apex/extension reads index an absent float data array (out-of-bounds read, typically a crash). Calling run() twice on one algorithm object is ordinary API use, although no in-tree tool does it.

**Who reaches it.** C++ and pyOpenMS users who call MassTraceDetection::run more than once on one instance (bind_misc.cpp:3085). FeatureFinderMetabo.cpp:129, MassTraceExtractor.cpp:178, DDAWorkflowCommons.cpp:110, MassFeatureTrace.cpp:91 and PeakPickerIM.cpp:1266 each build a fresh detector per run, so they are not affected.

**Upstream evidence.** origin/develop src/openms/source/FEATUREFINDER/MassTraceDetection.cpp:96-110. getIMIndices_ only ever sets state (`fwhm_meta_idx = std::distance(...); has_fwhm_mz = true;`, same for IM and IM FWHM) and never resets it. validate_meta_array (116-138) only throws `if (valid_count > 0 && valid_count != spectra.size())`, so it accepts zero matches. run_ passes the members at 482-485. Reads follow at 520 `work_exp[apex_scan_idx].getFloatDataArrays()[ion_mobility_idx_][apex_peak_idx]`, 530-531 (`[fwhm_meta_idx_]`, `[im_fwhm_idx_]`) and 430/434. The members are initialised once, in MassTraceDetection.h:182-184 and 203-205.

**Proof.** Code reading of the develop source. MassTraceDetection_test.cpp is unchanged between ci.2 and 4f5c86f, and the log claims no sanitizer run.

**Fix in OpenMS4 Core.** 1beb468 MassTraceDetection.cpp getIMIndices_ (resets the three indices and flags before discovery)

<a id="cpp-120"></a>
### CPP-120: mzML list `count` attribute drives an unvalidated container reserve (the same fix closed a numpress declared-length out-of-bounds read)

**P0** · memory-safety · malformed · proof: static-only  
**Affected:** src/openms/source/FORMAT/HANDLERS/MzMLHandler.cpp:965, :978, :996, :1012, :1017; src/openms/include/OpenMS/FORMAT/HANDLERS/XMLHandler.h:393-398, :538-543; src/openms/source/FORMAT/HANDLERS/StringManager.cpp:109-112; src/openms/source/KERNEL/MSExperiment.cpp:520-523

**Why it is a bug.** The count part alone would be P2: count="-1" becomes SIZE_MAX and throws std::length_error, and a huge count reserves gigabytes before any child is parsed, instead of a ParseError. The fix recorded under this ID also removed a heap out-of-bounds read: a numpress-compressed supplementary array that decodes to fewer values than its declared length is copied or indexed up to the declared length. That read is reachable from a malformed mzML file, which the rubric rates P0.

**Who reaches it.** Every mzML load through MzMLFile or FileHandler: all TOPP tools reading mzML and pyOpenMS MzMLFile, for both spectra and chromatograms that carry supplementary arrays

**Upstream evidence.** MzMLHandler.cpp:965 `scan_count_total_ = attributeAsInt_(attributes, s_count);` then :977 `exp_->reserveSpaceSpectra(scan_count_total_);`, the same for chromatograms at :996/:1012, and :1017 `bin_data_.reserve(attributeAsInt_(attributes, s_count));`. MSExperiment.cpp:520-523 forwards the Size to vector::reserve. Numpress: MzMLHandlerHelper.cpp:175-186 calls `MSNumpressCoder().decodeNP(bindata.base64, bindata.floats_64, ...)` without the `bindata.size = bindata.floats_64.size()` reset that the other codec branches do (:190-195). size holds the declared arrayLength or defaultArrayLength (MzMLHandler.cpp:1026-1028) and bounds supplementary-array reads: :557 `Size copy_length = std::min(default_arr_length, data.size);`, :564 `data.floats_64.begin() + copy_length`, :603 `if (n < data.size)`, and :769-771 `if (n < input_data[i].size) ... input_data[i].floats_64[n]`.

**Proof.** No class test at 4f5c86f covers a negative or huge count or a numpress array that decodes short; the MzMLFile_test.cpp and MzMLSpectrumDecoder_test.cpp diffs in ci.2..4f5c86f contain neither. The Rust log is source review only.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/HANDLERS/MzMLHandler.cpp (capacityHint_) and MzMLHandlerHelper.cpp (numpress branch resets bindata.size)

<a id="cpp-148"></a>
### CPP-148: MzTab column-unit metadata parses its key as an index

**P0** · memory-safety · malformed · proof: static-only  

**Why it is a bug.** An input line keyed colunit[5]-protein parses n=5 and writes through operator[] of an empty vector (out-of-bounds write). A key starting with 'colunit' but with no hyphen (e.g. the colunit_small_molecule spelling MzTabMFile writes) reads meta_key_fields[1] past the end. Both are memory-safety defects reachable from input files: P0. On valid files, every spec colunit-<section> line makes load() throw, and the writer's missing tab makes its own colunit output unreadable.

**Who reaches it.** MzTabFile::load (TOPP FileInfo on .mzTab, pyOpenMS MzTabFile.load); the writer, via MzTabFile::store, only when colunit vectors are set, which no upstream code does

**Upstream evidence.** src/openms/source/FORMAT/MzTabFile.cpp:683-706: `else if (StringUtils::hasPrefix(meta_key, "colunit") && meta_key_fields[1] == "protein") { Int n = (Size)extractBracketIndex(meta_key_fields[0], "colunit["); const std::string& s = cells[2]; mz_tab_metadata.colunit_protein[n] = s; }`, repeated for peptide, psm and small_molecule. extractBracketIndex (29-34) ends in StringUtils::toInt32, which throws ConversionError for "colunit" (StringUtils.cpp:255-259). The colunit_* members are plain std::vector<std::string> (MzTab.h:173-176) and are never resized. The writer (1984, 1991, 1998, 2005) builds `std::string("MTD\tcolunit-protein") + md.colunit_protein[i]` with no tab, and emits "colunit-PSM" where the reader expects "psm".

**Proof.** No class test at 4f5c86f loads a colunit line. The Rust log is a source review with no C++ execution.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/MzTabFile.cpp (one colunit branch guarded by meta_key_fields.size() == 2, with a lower-cased section name and push_back; the writer now emits the tab)

<a id="cpp-164"></a>
### CPP-164: Mascot query index guard accepts one-past-end

**P0** · memory-safety · malformed · proof: static-only  

**Why it is a bug.** <peptide query> equal to NumQueries+1 passes the guard and writes one element past the end of id_data_. So does query=1 in a file exported without the header (no <NumQueries>, so id_data_ stays empty and 0 > 0 is false). That header-less export is exactly the case the guard's error message describes. A <query number> of 0 or above NumQueries also indexes out of bounds. This is heap out-of-bounds read/write reachable from an input file.

**Who reaches it.** IDFileConverter with Mascot XML input (IDFileConverter.cpp:496); MascotAdapterOnline (MascotAdapterOnline.cpp:166); pyOpenMS MascotXMLFile.load (bind_misc.cpp:4686)

**Upstream evidence.** origin/develop src/openms/source/FORMAT/HANDLERS/MascotXMLHandler.cpp:56-59 `Int attribute_value = attributeAsInt_(attributes, s_peptide_query); peptide_identification_index_ = attribute_value - 1; if (peptide_identification_index_ > id_data_.size())`. The check is off by one. id_data_ is sized only from <NumQueries> (:78-80) after MascotXMLFile::load clears it (MascotXMLFile.cpp:39). It is then written via the unchecked ExposedVector::operator[] (ExposedVector.h:144-147) at :88, :104, :148, :560, :575. <query number> is never range-checked before `id_data_[actual_query_ - 1]` at :342, :363, :365, :370, :376, and the constructor (:17-21) does not initialise actual_query_.

**Proof.** No MascotXMLFile test change in the ci.2..4f5c86f range, and no test with an out-of-range query. The Rust log entry says source review only, not executed.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf: src/openms/source/FORMAT/HANDLERS/MascotXMLHandler.cpp, checks `attribute_value <= 0 || attribute_value > id_data_.size()` before subtracting; range-checks actual_query_ in <StringTitle>/<RTINSECONDS>; initialises actual_query_

<a id="cpp-168"></a>
### CPP-168: mzIdentML reader dereferences missing PeptideSequence child

**P0** · memory-safety · valid-edge · proof: static-only  

**Why it is a bug.** An empty PeptideSequence element, which the schema allows, makes parsePeptideSiblings_ call a virtual method through a null pointer, and the process segfaults before catch(...) can act. An XML comment before the text also discards a valid sequence (empty AASequence stored). The rubric puts memory-safety defects reachable from input files at P0, although real files rarely trigger this.

**Who reaches it.** MzIdentMLFile::load and FileHandler::loadIdentifications for .mzid; IDFileConverter, IDMapper and any TOPP tool loading mzid via FileHandler; pyOpenMS MzIdentMLFile.load

**Upstream evidence.** src/openms/source/FORMAT/HANDLERS/MzIdentMLDOMHandler.cpp:2469-2470 `DOMNode* tn = element_sib->getFirstChild(); if (tn->getNodeType() == DOMNode::TEXT_NODE)` has no null check. Its else branch at :2478 is `throw std::runtime_error("ERROR : Non Text Node");`. The only caller, parsePeptideElements_ (:764-779), has `catch (...) { OPENMS_LOG_ERROR << "No amino acid sequence readable from 'Peptide'" ...}`, which cannot catch a null dereference. MzIdentMLFile::load (MzIdentMLFile.cpp:38) uses this DOM handler.

**Proof.** No regression test: no MzIdentMLFile or MzIdentMLDOMHandler test changed in core-v4.0.0-ci.2..4f5c86f, and fix 181dadf ships without one. The Rust log says the defect was not executed. The argument rests on code reading: Xerces creates no child node for <PeptideSequence/>, so getFirstChild() returns nullptr. The mzIdentML 1.1 XSD type `sequence` is `[ABCDEFGHIJKLMNOPQRSTUVWXYZ]*`, which allows an empty sequence.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf, src/openms/source/FORMAT/HANDLERS/MzIdentMLDOMHandler.cpp (uses getTextContent(); an empty sequence raises ParseError)

<a id="cpp-169"></a>
### CPP-169: mzIdentML substitution position is used as unchecked string index

**P0** · memory-safety · malformed · proof: static-only  

**Why it is a bug.** The write uses a location value straight from the file. location="0" becomes index SIZE_MAX, writing one byte before the buffer. A location past the sequence end writes beyond the string, possibly beyond the std::string object on the stack. A missing replacementResidue puts a NUL into the sequence. This is an out-of-bounds write reachable from input files, so P0.

**Who reaches it.** MzIdentMLFile::load and FileHandler .mzid loading; IDFileConverter, IDMapper; pyOpenMS MzIdentMLFile.load

**Upstream evidence.** src/openms/source/FORMAT/HANDLERS/MzIdentMLDOMHandler.cpp:2496 `char replacementResidue = StringManager::convert(element_sib->getAttribute(CONST_XMLCH("replacementResidue")))[0];` and :2500 `as[StringUtils::toInt32(location) - 1] = replacementResidue;` do no range check against as.size() and no check for an empty replacementResidue.

**Proof.** No regression test at 4f5c86f, and the Rust log says the defect was not executed. The only upstream test data with a SubstitutionModification is src/tests/class_tests/openms/data/Mascot_MSMS_example.mzid:650 (`location="7"`). It sits on a 1.0 file whose lowercase <peptideSequence> the DOM handler does not match, so `as` is empty there. That file is loaded only in a commented-out test (MzIdentMLFile_test.cpp:369), so no test runs it.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf, src/openms/source/FORMAT/HANDLERS/MzIdentMLDOMHandler.cpp (checks 1 <= location <= size and a non-empty replacementResidue; throws ParseError)

<a id="cpp-191"></a>
### CPP-191: Array hydration lacks pair length and role validation

**P0** · memory-safety · malformed · proof: static-only  

**Why it is a bug.** The copy loop walks the container's length and advances through the decoded `data` vector without a bounds check. A shorter later array reads past data.end(). In the full-meta path a crafted file can supply containers that already hold peaks (RUN_EXTRA mzML) together with short DATA blobs, so the read runs past the heap allocation. Duplicate role rows also pass the row-count check and silently leave intensities or m/z at 0. This is an out-of-bounds read reachable from an input file, which the rubric puts at P0.

**Who reaches it.** Reading .sqMass: SqMassFile::load/transform (FileConverter, OpenSwathWorkflow with sqMass input via SwathFile/SpectrumAccessSqMass), MzMLSqliteHandler::readExperiment/readSpectra/readChromatograms, pyOpenMS

**Upstream evidence.** origin/develop src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp:199-208 `if (containers[curr_id].empty()) { containers[curr_id].resize(data.size()); } std::vector< double >::iterator data_it = data.begin(); for (auto it = containers[curr_id].begin(); it != containers[curr_id].end(); ++it, ++data_it) { it->setIntensity(*data_it); } cont_data[curr_id] += 1;` (same at :219-228 and :238-244); :258 `if (cont_data[k] < 2)`; full-meta containers come from RUN_EXTRA at :313-318 `f.loadBuffer(uncompressed, exp);`

**Proof.** Source-reviewed only per the Rust log. The OpenMS 4 acceptArray check (181dadf) has no class test at 4f5c86f with unequal or duplicate arrays.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp (acceptArray length and role check, cont_data bitmask == 3)

<a id="cpp-199"></a>
### CPP-199: Metadata readers accept invalid negative activation enum values below -1

**P0** · memory-safety · malformed · proof: static-only  

**Why it is a bug.** A sqMass PRECURSOR row with ACTIVATION_METHOD -2 or lower passes the check and becomes an out-of-range enum. FileInfo on that file then indexes the activation name arrays with SIZE_MAX-1, an out-of-bounds read of a std::string. The writer only ever stores -1 or a valid value, so this needs a crafted or corrupted file; it is still a memory-safety defect reachable from an input file, which the rubric puts at P0.

**Who reaches it.** FileInfo -in file.sqMass: FileHandler, then SqMassFile::load, then readExperiment, which falls back to prepareSpectra_ when RUN_EXTRA holds no metadata; FileInfo.cpp:1584/1631/1840 then look up the names. Also TOPPView SpectraTreeTab/SpectraIDViewTab (getActivationMethodsAsString), pyOpenMS SqMassFile.load followed by Precursor.getActivationMethodsAsString, and SpectrumAccessSqMass/transform readers

**Upstream evidence.** origin/develop src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp:853-856 (prepareSpectra_; same at :709-712 in prepareChroms_) `if (sqlite3_column_type(stmt, 15) != SQLITE_NULL && sqlite3_column_int(stmt, 15) != -1 && sqlite3_column_int(stmt, 15) < static_cast<int>(OpenMS::Precursor::ActivationMethod::SIZE_OF_ACTIVATIONMETHOD)) { precursor.getActivationMethods().insert(static_cast<OpenMS::Precursor::ActivationMethod>(sqlite3_column_int(stmt, 15))); }`. The consumers index the name tables without a check: src/openms/source/FORMAT/FileInfo.cpp:1631 `Precursor::NamesOfActivationMethodShort[static_cast<size_t>(am.first.am)]` (also :1840) and src/openms/source/METADATA/Precursor.cpp:124 `NamesOfActivationMethod[static_cast<size_t>(m)]`.

**Proof.** The Rust log reports a source review only and claims no downstream crash. The FileInfo out-of-bounds chain comes from reading origin/develop. No 4f5c86f test: MzMLSqliteHandler_test.cpp is unchanged.

**Fix in OpenMS4 Core.** core 181dadf: both readers use sqlite3_column_int64 and insert only when 0 <= value < SIZE_OF_ACTIVATIONMETHOD

<a id="cpp-166"></a>
### CPP-166: Mascot MGF loader carries precursor and RT fields between blocks

**P0** · wrong-result · valid-common · proof: regression-test  

**Why it is a bug.** Any MGF block that omits an optional field a previous block set silently inherits the previous spectrum's precursor charge, retention time, precursor intensity, MS level or compound annotations. Omitting CHARGE for spectra whose charge is undetermined is valid and occurs in real converter output. The result is wrong precursor charge (and so neutral mass) and RT, both for searches and when converting MGF to mzML.

**Who reaches it.** Every tool that loads MGF through FileHandler::loadExperiment (FileHandler.cpp:926), e.g. FileConverter MGF->mzML; pyOpenMS MascotGenericFile.load (bind_misc.cpp:3053)

**Upstream evidence.** origin/develop src/openms/include/OpenMS/FORMAT/MascotGenericFile.h:92-95 creates one `typename MapType::SpectrumType spectrum;` and sets MS level, precursor and type once, before the block loop. getNextSpectrum_ (:141-154) only does `spectrum.resize(0); spectrum.setNativeID(...)` and removes TITLE and SEQ. PEPMASS m/z and intensity (:216-235), CHARGE (`setCharge`, :236-241), RTINSECONDS (`spectrum.setRT`, :245), MSLEVEL and NAME/SMILES/SCANS etc. meta values (:300-378) are assigned only when present, so they persist into later blocks.

**Proof.** packages/core@4f5c86f src/tests/class_tests/openms/source/MascotGenericFile_test.cpp, section '([EXTRA] empty MGF blocks do not consume the following spectrum)' (added 181dadf). After block 1 sets CHARGE=3+, PEPMASS intensity 25, RTINSECONDS=42 and SEQ, it asserts block 2 has charge 0, precursor intensity 0, RT -1 and no SEQ. Caveat: on the pre-fix code the section fails first at spectra.size()==2, because the old reader ignores END IONS of a block without peaks and merges it into the next. The carry-over assertions discriminate only once that companion change is in. No test covers carry-over between two non-empty blocks.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf: src/openms/include/OpenMS/FORMAT/MascotGenericFile.h, getNextSpectrum_ now calls spectrum.clear(true) and re-applies the MS2/centroid/one-precursor defaults for every block; test added in MascotGenericFile_test.cpp

## P1: 61 findings

<a id="cpp-207"></a>
### CPP-207: SpectrumAccessSqMass unchecked view positions permit out-of-bounds access

**P1** · memory-safety · api-misuse · proof: regression-test  

**Why it is a bug.** A negative position in the nested constructor, or an out-of-range id on a subset view, reads outside the std::vector<int> (undefined behaviour). The garbage id then goes to SQL and usually throws, but can silently return an unrelated spectrum. In-tree callers only pass in-range positions, so this is memory safety reachable only through API misuse (P1).

**Who reaches it.** pyOpenMS SpectrumAccessSqMass(handler, indices).getSpectrumById(id) with an out-of-range id (bind_format.cpp:2960, 2963); C++ API, including the nested constructor. Not triggered by OpenSwathWorkflow: SwathFile.cpp:356-366 builds the subsets, and positions come from getSpectraByRT and getNrSpectra.

**Upstream evidence.** src/openms/source/ANALYSIS/OPENSWATH/DATAACCESS/SpectrumAccessSqMass.cpp:43-45 `if (indices[k] >= (int)sp.sidx_.size()) throw ...; sidx_.push_back( sp.sidx_[ indices[k] ] );` has no check for negative positions. :75 `indices.push_back(sidx_[id]);` (getSpectrumById) and :106 (getSpectrumMetaById) have no bounds check at all.

**Proof.** OpenMS4 core 4f5c86f, SpectrumAccessSqMass_test.cpp, section SpectrumAccessSqMass(const SpectrumAccessSqMass& sp, const std::vector<int>& indices), lines 106-108: indices3=[-1] on a one-element subset must throw IllegalArgument. The pre-fix constructor never queries SQL, so it reads sidx_[-1] and throws nothing, and the test fails. The new getSpectrumById (lines 143-144) and getSpectrumMetaById sections cover the getters too, but on pre-fix code those would fail only by chance, because the garbage id usually makes the handler throw IllegalArgument anyway.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf: SpectrumAccessSqMass.cpp file-local storageIndex() and a negative-position check in the nested constructor, with tests in SpectrumAccessSqMass_test.cpp

<a id="cpp-224"></a>
### CPP-224: Gumbel maximum-likelihood fitting reads beyond a short weight vector

**P1** · memory-safety · api-misuse · proof: regression-test  

**Why it is a bug.** A weight vector shorter than the value vector makes the Levenberg-Marquardt objective read past the end of the weights on every evaluation (undefined behaviour). The only in-tree caller, PosteriorErrorProbabilityModel::fitGumbelGauss, always passes equal lengths: incorrect_posteriors is resized to x_scores.size(). The defect is therefore reachable only through API misuse, which is P1.

**Who reaches it.** Public C++ API Math::GumbelMaxLikelihoodFitter::fitWeighted only. The in-tree caller PosteriorErrorProbabilityModel::fitGumbelGauss passes matched lengths. Neither is bound in pyOpenMS, and no TOPP tool reaches it.

**Upstream evidence.** origin/develop src/openms/source/MATH/STATISTICS/GumbelMaxLikelihoodFitter.cpp:58-63 `auto wit = m_weights.cbegin(); for (auto it = m_data.cbegin(); it != m_data.cend(); ++it, ++wit) { double diff = (*it - x(0)) / sigma; fvec(0) += *wit * (-logsigma - diff - exp(-diff)); }`. fitWeighted at :74-82 builds `GumbelDistributionFunctor functor (x, w);` with no x.size()==w.size() check, and header GumbelMaxLikelihoodFitter.h:63-72 states no length requirement. The OpenMS4 pre-fix file at core-v4.0.0-ci.2 is identical to develop.

**Proof.** 4f5c86f src/tests/class_tests/openms/source/GumbelMaxLikelihoodFitter_test.cpp, section '[EXTRA] fitWeighted rejects a weight vector of another length'. It calls fitWeighted({1.0, 2.0}, {1.0}) and fitWeighted({1.0, 2.0}, {1.0, 1.0, 1.0}) and expects IllegalArgument. The pre-fix objective (identical to develop) never throws IllegalArgument and dereferences the end iterator of the one-element weight vector, so the section fails. No sanitizer run.

**Fix in OpenMS4 Core.** OpenMS4 core 56f5f29: src/openms/source/MATH/STATISTICS/GumbelMaxLikelihoodFitter.cpp (IllegalArgument on length mismatch and non-finite or negative weights), with a test in GumbelMaxLikelihoodFitter_test.cpp

<a id="cpp-077"></a>
### CPP-077: rasterizeIMFrame multiplies the bin counts without an overflow check

**P1** · memory-safety · api-misuse · proof: static-only  
**Affected:** src/openms/source/KERNEL/MSSpectrum.cpp:889 (`const Size total_pixels = im_bins * mz_bins;`), :892 (std::fill), :946 (pixel_idx)

**Why it is a bug.** If im_bins * mz_bins overflows size_t, the buffer is sized from the wrapped product but writes use the unwrapped counts, giving a heap out-of-bounds write. The counts must be ones no real buffer can have, so only C++ API misuse reaches it: memory safety via API misuse.

**Who reaches it.** C++ MSSpectrum::rasterizeIMFrame with caller-chosen bin counts. Not reachable from pyOpenMS, which takes mz_bins and im_bins from the numpy array shape (bind_spectrum.cpp:602-603), so the product always matches a real allocation.

**Upstream evidence.** src/openms/source/KERNEL/MSSpectrum.cpp:895 `const Size total_pixels = im_bins * mz_bins;`, :898 `std::fill(output, output + total_pixels, 0.0f);`, :951 `const Size pixel_idx = static_cast<Size>(mz_bin) * im_bins + static_cast<Size>(im_bin);`; the only bin-count checks are the zero checks at :872-881

**Proof.** No OpenMS4 class test passes overflowing bin counts: git grep in 4f5c86f src/tests finds no such case, and MSSpectrum_rasterizeIMFrame_test.cpp is unchanged. The Rust log reports no C++ run. By reading: with, for example, im_bins = mz_bins = 2^33 the product wraps to 0, while pixel_idx is computed from the unwrapped counts and writes outside the buffer.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/KERNEL/MSSpectrum.cpp (throws InvalidValue if im_bins > SIZE_MAX / sizeof(float) / mz_bins, before any write)

<a id="cpp-091"></a>
### CPP-091: Mixed isHigherScoreBetter flags make the sort comparator asymmetric

**P1** · memory-safety · api-misuse · proof: static-only  
**Affected:** src/openms/source/KERNEL/BaseFeature.cpp:136-142

**Why it is a bug.** With A higher-is-better, B lower-is-better and A's score below B's, both comp(A,B) and comp(B,A) are true. That breaks std::sort's strict-weak-ordering precondition, which is undefined behaviour: usually an arbitrary order, but libc++'s introsort can walk out of range on longer lists. Because mixed score types violate the documented precondition, this is memory-safety reachable only through API misuse, hence P1.

**Who reaches it.** FeatureLinkerUnlabeledQT with use_identifications=true (QTClusterFinder.cpp:106) and ProteomicsLFQ/PIPECHO (Impl.cpp:76), whenever a feature carries identifications with different higher_score_better flags (e.g. several search engines merged without ConsensusID).

**Upstream evidence.** origin/develop src/openms/source/KERNEL/BaseFeature.cpp:136-143: 'if (p1.isHigherScoreBetter()) { return p1.getHits()[0].getScore() < p2.getHits()[0].getScore(); } else { return p1.getHits()[0].getScore() > p2.getHits()[0].getScore(); }'. The direction comes from the left operand only. BaseFeature.h:164-165 only documents the assumption that the identifications share a score type; nothing checks it.

**Proof.** No C++ test mixes score orientations. The hit-less ids[2] in BaseFeature_test.cpp (4f5c86f) never reaches the direction branch. The Rust log reports source review only.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf src/openms/source/KERNEL/BaseFeature.cpp (orientation read once from the first identification with hits, captured by value)

<a id="cpp-096"></a>
### CPP-096: Feature::getConvexHull() is a const method that lazily mutates the object and hands out a mutable reference

**P1** · memory-safety · api-misuse · proof: static-only  
**Affected:** src/openms/include/OpenMS/KERNEL/Feature.h:99 and 175-179; src/openms/source/KERNEL/Feature.cpp:93-137

**Why it is a bug.** Two threads making the first getConvexHull() call on the same dirty Feature both write convex_hull_'s containers without synchronisation, a data race that can corrupt the heap. No upstream code shares a Feature that way (the OpenMP loop in FeatureFinderAlgorithmPicked.cpp:595/805 works on a loop-local Feature), so it is reachable only through API misuse. The mutable-reference half has no output effect; its one use, FeatureFinderCentroided.cpp:366, is a silent no-op. Note the OpenMS 4 change only made the return const and documented the race; it did not remove it.

**Who reaches it.** C++/OpenMP code calling getConvexHull() concurrently on one Feature after setConvexHulls() or a non-const getConvexHulls(). FeatureFinderCentroided (mutation via the returned reference, effect discarded). pyOpenMS returns a copy (bind_kernel.cpp:3930).

**Upstream evidence.** origin/develop src/openms/include/OpenMS/KERNEL/Feature.h:99 'ConvexHull2D& getConvexHull() const;' over ':176 mutable bool convex_hulls_modified_{};' and ':179 mutable ConvexHull2D convex_hull_;'. Feature.cpp:93-136 recomputes: 'convex_hull_ = convex_hulls_[0]; ... convex_hull_.clear(); ... convex_hull_.addPoint(...); convex_hulls_modified_ = false; return convex_hull_;'. The non-const getConvexHulls() re-marks the hull dirty (Feature.cpp:81-85), and copies keep the flag (:34). The one mutation through the returned reference is FeatureFinderCentroided.cpp:366 'ft.getConvexHull().expandToBoundingBox();', undone by the getConvexHulls() call on :367.

**Proof.** Feature_test.cpp at 4f5c86f (b6dd412) only renames the section to the const signature; there is no concurrency test. The Rust log reports source review only.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf Feature.h:103 and Feature.cpp:93 return const ConvexHull2D& (race documented, not fixed)

<a id="cpp-141"></a>
### CPP-141: DataValue::operator double() reads the union's double member for a non-numeric value (imzML call site of CPP-058)

**P1** · memory-safety · api-misuse · proof: static-only  
**Affected:** src/openms/source/DATASTRUCTURES/DataValue.cpp:466-478 (operator double()), :480-491 (operator float()), :452-464 (operator long double()); reached from src/openms/source/FORMAT/HANDLERS/ImzMLWriter.cpp:356-378

**Why it is a bug.** For a STRING_VALUE or list value the cast reads an inactive union member, which is undefined behaviour and in practice returns a pointer's bits as a double. ImzMLFile::store then silently writes a garbage pixel size and IMS:1000044/45 extent instead of raising ConversionError. Loaded files always store these keys as doubles, so the trigger is a caller setting a string MetaValue.

**Who reaches it.** ImzMLFile::store(MSExperiment) goes through ImzMLWriter::store and extractMeta_ (ImzMLWriter.cpp:1413). Also reached by ImzMLFile::buildImagingGeometry(MSExperiment) and by pyOpenMS ImzMLFile.store and buildImagingGeometry (bind_format.cpp:860, 876). FileHandler refuses to store IMZML (FileHandler.cpp:1243). The underlying DataValue defect reaches more widely under CPP-058.

**Upstream evidence.** origin/develop:src/openms/source/DATASTRUCTURES/DataValue.cpp:466-478. operator double() throws only for `value_type_ == EMPTY_VALUE` (:468) and converts `INT_VALUE` (:473). For every other type it ends with `return data_.dou_;` (:477); operator long double (:452-464) and operator float (:480-491) have the same fall-through. Call sites: ImzMLWriter.cpp:360 `meta.pixel_size_x = static_cast<double>(exp.getMetaValue("imzml:pixel_size_x"));`, the same pattern at :364, :368 and :372, and ImzMLFile.cpp:365-366.

**Proof.** No class test exercises a String or list DataValue cast to double. DataValue_test.cpp:1006-1016 covers only the Empty type, and the OpenMS4 fix (181dadf) added no test. The Rust log states no C++ execution was done.

**Fix in OpenMS4 Core.** OpenMS4 181dadf: src/openms/source/DATASTRUCTURES/DataValue.cpp (ConversionError for non-numeric types in operator long double/double/float)

<a id="cpp-181"></a>
### CPP-181: SqliteConnector permits copying an owned database handle

**P1** · memory-safety · api-misuse · proof: static-only  

**Why it is a bug.** Copying a SqliteConnector, or an OSWFile whose public defaulted copy constructor copies conn_, gives two objects the same sqlite3 handle. Both destructors then call sqlite3_close_v2 on it, a double close and use-after-free. Copy assignment also leaks the target's handle. No upstream TOPP tool, GUI code, test or pyOpenMS binding copies either class, so only a C++ caller making a copy reaches it: memory safety through API misuse.

**Who reaches it.** C++ library users copying SqliteConnector or OSWFile. OpenSwathExport, OpenSwathInfer, TOPPView (LayerDataBase, DIATreeTab) and the handlers all construct in place, and neither class is bound in pyOpenMS.

**Upstream evidence.** origin/develop src/openms/include/OpenMS/FORMAT/SqliteConnector.h:62-63 declares `~SqliteConnector();` but does not delete the copy operations, so the implicit copy duplicates `void* db_` (:132). src/openms/source/FORMAT/SqliteConnector.cpp:25: the destructor calls `sqlite3_close_v2(static_cast<sqlite3*>(db_));`. src/openms/include/OpenMS/FORMAT/OSWFile.h:55-56 declares `OSWFile(const OSWFile& rhs) = default; OSWFile& operator=(const OSWFile& rhs) = default;` over the member `SqliteConnector conn_;` (:180).

**Proof.** No class test at 4f5c86f: SqliteConnector_test.cpp has not changed since 70c8251, and the test diff ci.2..4f5c86f has no SQLite case. The Rust log records source review only, with no C++ execution. The double close follows directly from the implicit copy plus the destructor.

**Fix in OpenMS4 Core.** OpenMS4 1beb468, src/openms/include/OpenMS/FORMAT/SqliteConnector.h (copy constructor and assignment deleted)

**Note.** The Core fix deleted SqliteConnector's copy operations but left `OSWFile`'s defaulted ones, which became implicitly deleted. Clang's warning about them failed TOPP's macOS x64 cask build at ci.4; the ci.5 candidate (`ac41cc1`) deletes them too.

<a id="cpp-204"></a>
### CPP-204: MSDataSqlConsumer owning raw pointer leaks during failed construction and can be shallow-copied

**P1** · memory-safety · api-misuse · proof: static-only  

**Why it is a bug.** The implicit copy duplicates the owning pointer, so both destructors flush the same buffered records and then `delete handler_` twice (a double free). Nothing in-tree copies a consumer and pyOpenMS defines no __copy__, so this is memory safety reachable only through API misuse (P1); the leak when construction fails loses only a small handler object on an error path.

**Who reaches it.** C++ API only for the copy. The constructor-failure leak (unwritable output path, or negative buffer size from pyOpenMS) is reachable from OpenSwathWorkflow -out_chrom *.sqMass (OpenSwathBase.cpp:359), OpenSwathMzMLFileCacher (OpenSwathMzMLFileCacher.cpp:163) and pyOpenMS MSDataSqlConsumer (bind_misc.cpp:1693-1694).

**Upstream evidence.** src/openms/include/OpenMS/FORMAT/DATAACCESS/MSDataSqlConsumer.h:94 `OpenMS::Internal::MzMLSqliteHandler * handler_;`, with no deleted copy constructor or assignment anywhere in the class (h:34-103). MSDataSqlConsumer.cpp:18 `handler_(new OpenMS::Internal::MzMLSqliteHandler(filename, run_id) )`, then :22-26 `spectra_.reserve(flush_after_); ... handler_->createTables();`. createTables opens a SqliteConnector, which throws SqlOperationFailed (SqliteConnector.cpp:53); a negative buffer_size makes reserve(SIZE_MAX) throw. The only `delete handler_;` is in the destructor (:42).

**Proof.** The OpenMS 4 fix makes the copy operations `= delete` and uses a unique_ptr. Neither can be exercised by a class test: a deleted copy is a compile-time property, and the leak needs a leak checker. The [EXTRA] negative-buffer-size check in SpectrumAccessSqMass_test.cpp tests the new IllegalArgument, not the leak.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf: MSDataSqlConsumer.h (std::unique_ptr handler_, copy operations deleted) and MSDataSqlConsumer.cpp

<a id="cpp-212"></a>
### CPP-212: OpenSwath drift filtering dereferences missing or misaligned mobility arrays

**P1** · memory-safety · valid-edge · proof: static-only  

**Why it is a bug.** filterByDrift dereferences a null drift array and reads past shorter intensity or IM arrays. OpenSwathWorkflow can reach the null dereference, but only with valid-edge data in a non-default configuration: MS2 with IM, MS1 without IM arrays, an IM library, and -Scoring:spectrum_addition_method resample. So I rated it a crash on valid-edge input (P1) rather than P0. The default 'simple' method hits DIAHelper's MissingInformation throw instead, MS2 maps without IM are rejected earlier by the extractor, and the misaligned-array read needs malformed mzML that the extractor already reads unchecked.

**Who reaches it.** TOPP OpenSwathWorkflow: use_ms1_ion_mobility defaults true while im_extraction_window_ms1 defaults -1, so MS1 extraction never checks for IM. The path is calculatePrecursorDIAScores, then fetchSpectrumSwath (OpenSwathScoring.cpp:336, :748), then mergeSpectraForScoring_ (:106-111), then filterByDrift (:97). The multi-map scoring path with a non-empty IM range reaches the same code through getMultipleSpectra(..., drift_start, drift_end) (OpenSwathScoring.cpp:681/690/771/785, ISpectrumAccess.cpp:94-100). C++ API: ISpectrumAccess::getSpectrumById(id, drift_start, drift_end) on any spectrum without IM, e.g. from SpectrumAccessSqMass, and SpectrumAddition::addUpSpectra(..., im_range, ...) (SpectrumAddition.cpp:188). Not bound in pyOpenMS.

**Upstream evidence.** src/openswathalgo/include/OpenMS/OPENSWATHALGO/DATAACCESS/ISpectrumAccess.h:85-92: all guards are commented out (`//OPENMS_PRECONDITION(input->getDriftTimeArray() != nullptr, ...)`, `//throw Exception::NullPointer(...)`). :98 `OpenSwath::BinaryDataArrayPtr im_arr = input->getDriftTimeArray();` can be null (DataStructures.h:208 `return BinaryDataArrayPtr(); // return null`). :102 `auto im_it = im_arr->data.cbegin();` and :108 `im_arr_out->description = im_arr->description;` dereference it unchecked. The loop at :110-121 advances int_it and im_it once per m/z element with no length check.

**Proof.** No OpenMS 4 test exercises filterByDrift (no match under src/tests at 4f5c86f), and the Rust log says no unsafe execution was attempted.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf: ISpectrumAccess.h filterByDrift throws std::invalid_argument for null input, missing m/z, intensity or drift arrays, or unequal lengths; DataStructures.h getDriftTimeArray skips null arrays

<a id="cpp-147"></a>
### CPP-147: MzTab PSM optional columns are dropped on load

**P1** · data-loss · valid-common · proof: regression-test  

**Why it is a bug.** Loading a valid mzTab silently drops every PSM opt_ column, including the decoy flag OpenMS itself writes as opt_global_cv_MS:1002217_decoy_peptide. The loss is read-side and no values are wrong; it is reached mainly through pyOpenMS, since FileInfo only counts rows, hence P1. Porting must also bring over the bounds checks: upstream's PRT/PEP/SML opt_ reads already run past the end of `cells` on rows whose trailing empty cells load() trims away, a live out-of-bounds read from malformed files (P0 under the rubric, static-only), and the hasPrefix change alone would extend it to PSM rows.

**Who reaches it.** MzTabFile::load: pyOpenMS MzTabFile.load, TOPP FileInfo (-in with an .mzTab file)

**Upstream evidence.** src/openms/source/FORMAT/MzTabFile.cpp:1287 `else if (cells[i] == "opt_")` in the PSH parser, so psm_custom_opt_columns stays empty and the PSM loop at 1335-1338 never fills row.opt_. The protein, peptide and small molecule parsers use `StringUtils::hasPrefix(cells[i], "opt_")` (819, 1119, 1459). Related: load() trims each line in place (229 `StringUtils::trim(s)`, which strips trailing tabs), and the PRT/PEP/SML reads `s.fromCellString(cells[it->second]);` at 1014, 1191 and 1536 have no bounds check.

**Proof.** OpenMS 4 src/tests/class_tests/openms/source/MzTabFile_test.cpp, section '[EXTRA] optional PSM columns retain trailing empty cells as null' (commit b6dd412). It adds opt_global_present/opt_global_empty to the PSH line and 'kept' plus an empty trailing cell to each PSM line. On the pre-fix code opt_global_present is never registered, so TEST_TRUE(present) fails.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/MzTabFile.cpp (hasPrefix for PSH opt_ columns, plus `it->second < cells.size()` guards in all four sections); test in b6dd412

<a id="cpp-155"></a>
### CPP-155: qcML loses units across its own store/load

**P1** · data-loss · valid-edge · proof: regression-test  

**Why it is a bug.** Units are written under attribute names that neither OpenMS's reader nor the qcML 0.0.7 schema recognise, so any load/store pass drops them and the output is not schema-conformant. No OpenMS producer sets units; they come only from the C++/pyOpenMS API or external qcML files. Valid but uncommon, so P1.

**Who reaches it.** QcMLFile store/load in QCShrinker, QCMerger, QCEmbedder, QCImporter, QCExporter, QCExtractor; pyOpenMS QcMLFile

**Upstream evidence.** origin/develop src/openms/source/FORMAT/QcMLFile.cpp:88-95 (QualityParameter::toXMLString): `s += " unitRef=\"" + unitRef + "\""; ... s += " unitAcc=\"" + unitAcc + "\"";`. The Attachment writer at :199-206 is the same. The reader uses `optionalAttributeAsString_(qp_.unitAcc, attributes, "unitAccession"); optionalAttributeAsString_(qp_.unitRef, attributes, "unitCvRef");` at :825-826 and :854-855.

**Proof.** src/tests/class_tests/openms/source/QcMLFile_test.cpp, sections '[QcMLFile::QualityParameter] std::string toXMLString(UInt indentation_level) const' and '[QcMLFile::Attachment] std::string toXMLString(UInt indentation_level) const' (added in b2079fb). Pre-fix XML contains unitRef=/unitAcc=, so the unitCvRef=/unitAccession= checks fail, including after a store/load/store round trip.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/QcMLFile.cpp (writer emits unitCvRef/unitAccession; reader also accepts legacy unitRef/unitAcc)

<a id="cpp-156"></a>
### CPP-156: qcML table writer discards its normalized row copy

**P1** · data-loss · valid-edge · proof: regression-test  

**Why it is a bug.** A table cell containing a space is written as-is into a space-separated tableRowValues element. On reload it becomes two cells, and every later value in that row shifts under the wrong column. OpenMS's own QCCalculator tables are numeric or have whitespace removed (PeptideSequence via removeWhitespaces, :1711), so this needs QCEmbedder CSV tables or API-built tables with spaces. Valid but uncommon, so P1.

**Who reaches it.** QCEmbedder (CSV cells go into run/set attachments, QCEmbedder.cpp:210-252) then store; reloads in QCExtractor, QCExporter, QCShrinker; pyOpenMS QcMLFile

**Upstream evidence.** origin/develop src/openms/source/FORMAT/QcMLFile.cpp:236-242: `std::vector<std::string> copy_row = *it; for (std::string& sit : copy_row) { StringUtils::substitute(sit, std::string(" "), std::string("_")); } s += StringUtils::trimmed(ListUtils::concatenate(*it, " "));`. The reader splits rows on ' ' at :882: `StringUtils::split(s, " ", row_);`.

**Proof.** src/tests/class_tests/openms/source/QcMLFile_test.cpp, section '[QcMLFile::Attachment] std::string toXMLString(UInt indentation_level) const' (added in b2079fb). Pre-fix, the row {"hello world","x"} is written as 'hello world x' and reloads as three cells, so exportAttachment(...).find("hello_world\tx") fails.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/QcMLFile.cpp (concatenate copy_row)

<a id="cpp-159"></a>
### CPP-159: qcML writer and reader disagree on set-member CV accession

**P1** · data-loss · valid-edge · proof: regression-test  

**Why it is a bug.** OpenMS writes set membership as QC:0000005 records (for example QCMerger with setname, via merge()), but its reader does not recognise them, so a reloaded QcMLFile has no members for any set. Files using the MS:1000577 member form instead collect members across sets (names_ is never cleared), and a skipped member's value leaks into the next parameter. qcML sets are valid but uncommon input, so P1.

**Who reaches it.** QCMerger -setname output reloaded by QCExtractor, QCShrinker, QCEmbedder or QCMerger; pyOpenMS QcMLFile.load/collectSetParameter

**Upstream evidence.** origin/develop src/openms/source/FORMAT/QcMLFile.cpp. store() at :2082-2094 writes one record per member: `qp.id = *kt; qp.name = "set name"; qp.cvRef = "QC"; qp.cvAcc = "QC:0000005";`. The reader at :841-844 recognises only `if (qp_.cvAcc == "MS:1000577") { names_.insert(qp_.value); }`. At :945-949 `if (!(qp_.cvAcc == "MS:1000577" && parent_tag == "setQuality")) { qps_.push_back(qp_); qp_ = QualityParameter(); }` keeps QC:0000005 as an ordinary parameter and never resets qp_ after a skipped member. The setQuality start at :862-871 never clears names_.

**Proof.** src/tests/class_tests/openms/source/QcMLFile_test.cpp, section 'void store(const std::string &filename) const' (added in b2079fb). Pre-fix, reloaded sets s1 and s2 have no members, so collectSetParameter returns 0 values instead of 2 and 1.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/QcMLFile.cpp (QC:0000005 read as membership, names_ cleared per set, qp_ always reset, MS:1000577 names mapped to run IDs)

<a id="cpp-172"></a>
### CPP-172: Streaming mzML consumer references header entries declared only for first record

**P1** · data-loss · valid-edge · proof: regression-test  

**Why it is a bug.** When a later streamed spectrum has its own source file, a processing history that is not pointer-identical to the first spectrum's, or array-level processing, the written mzML contains undeclared IDREFs: it is schema-invalid, and the source file and history are silently lost on reload. Typical mzML-to-consumer pipelines share processing pointers and have no per-spectrum source files, so this is uncommon valid input: P1.

**Who reaches it.** MzMLFile::transform with PlainMSDataWritingConsumer; FileConverter -process_lowmemory, NoiseFilterGaussian/NoiseFilterSGolay/PeakPickerHiRes/PeakPickerIM low-memory modes, OpenSwathWorkflow, OpenSwathMzMLFileCacher, TICCalculator, CometAdapter, SageAdapter; pyOpenMS PlainMSDataWritingConsumer

**Upstream evidence.** - src/openms/source/FORMAT/DATAACCESS/MSDataWritingConsumer.cpp:76-83 does `MapType dummy; dummy = settings_; dummy.addSpectrum(scpy); ... Internal::MzMLHandler::writeHeader_(ofs_, dummy, dps_, *validator_);` once, for the first spectrum only. - MzMLHandler.cpp:4962-4966 declares `sf_sp_<i>` only for spectra in that map. - writeSpectrum_ at :5252-5254 writes `if (spec.getSourceFile() != SourceFile()) { os << " sourceFileRef=\"sf_sp_" << s << "\""; }`. - :5258-5272 is `if (s == 0 || spec.getDataProcessing() != dps[0]) { Size dp_ref_num = s; ... os << " dataProcessingRef=\"dp_sp_" << dp_ref_num << "\""; }`. - The reader at :899-906 warns 'unregistered source file reference' and drops it; :920 `processing_[data_processing_ref]` default-inserts an empty history.

**Proof.** MSDataWritingConsumer_test.cpp, sections "[EXTRA] later spectra only reference what the header written from the first spectrum declares" and "regression: streamed arrays reference only declared processing records". The first asserts no sourceFileRef="sf_sp_1" or dataProcessingRef="dp_sp_1"/"dp_sp_2" in the output and that the history reads back. The second asserts isValid and no dp_sp_1_ array references. The pre-fix code emits these dangling references.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf (spectrum source file and processing) and 63e332c (spectrum and chromatogram array processing), src/openms/source/FORMAT/DATAACCESS/MSDataWritingConsumer.cpp and MSDataWritingConsumer.h

<a id="cpp-214"></a>
### CPP-214: MSDataSqlConsumer full metadata discards supplied experimental settings and addRun suppresses accumulated snapshot

**P1** · data-loss · valid-edge · proof: regression-test  

**Why it is a bug.** With full_meta=true, the run's settings (sample, instrument, source files, contacts) are silently dropped from the RUN_EXTRA snapshot, so a reloaded sqMass has default settings. Rated P1, not P0: sqMass is an OpenMS format, only metadata is lost, and no default TOPP path triggers it. OpenSwathWorkflow uses full_meta=false; the cacher's low-memory mode skips the first pass and never forwards settings.

**Who reaches it.** Library and pyOpenMS users of MSDataSqlConsumer(full_meta=true) fed by MzMLFile::transform (MzMLFile.cpp:230), MzXMLFile::transform (:108), SqMassFile::transform (:47), IndexedMzMLFileLoader (:47), BrukerTimsFile (:2237) or SwathFile. The addRun snapshot suppression only matters for API callers using full_meta=true.

**Upstream evidence.** src/openms/source/FORMAT/DATAACCESS/MSDataSqlConsumer.cpp:107 `void MSDataSqlConsumer::setExperimentalSettings(const ExperimentalSettings& /* exp */) {;}`; :49-52 addRun `MSExperiment meta; meta.setLoadedFilePath(filename); handler_->writeRunLevelInformation(meta, full_meta_); wrote_any_run_ = true;`; :36-40 destructor `if (!wrote_any_run_) { handler_->writeRunLevelInformation(peak_meta_, full_meta_); ...}`. The file is byte-identical to the pre-fix OpenMS 4 file at core-v4.0.0-ci.2.

**Proof.** packages/core@4f5c86f src/tests/class_tests/openms/source/SpectrumAccessSqMass_test.cpp, section '[EXTRA] reading spectra written by MSDataSqlConsumer', lines 395-420: setExperimentalSettings(sample name) with full_meta=true, then readExperiment; TEST_EQUAL(getSample().getName(), ...) fails against the no-op. The addRun half was only documented in OpenMS 4 (header doc in 181dadf), not fixed or tested.

**Fix in OpenMS4 Core.** packages/core 181dadf: src/openms/source/FORMAT/DATAACCESS/MSDataSqlConsumer.cpp (setExperimentalSettings copies into peak_meta_ when full_meta_); addRun limitation documented in MSDataSqlConsumer.h

<a id="cpp-218"></a>
### CPP-218: Positive-accuracy Numpress encoding destroys one- and two-point coordinate arrays

**P1** · data-loss · valid-edge · proof: regression-test  

**Why it is a bug.** Any 1- or 2-point m/z or RT array written with lossy linear Numpress and positive accuracy gets fixed point 0, is stored as zeros and decodes as NaN. The writers skip the accuracy check, so nothing warns. Chromatogram RT always uses 0.05, and OpenSwathWorkflow hard-codes lossy output for both .sqMass and .xic. Rated P1: the input is an edge case and the formats are OpenMS/OpenSwath-specific. mzML writing is protected by the default isfinite error-tolerance check.

**Who reaches it.** OpenSwathWorkflow -out_chrom .sqMass (OpenSwathBase.cpp:357-359, lossy_compression=true) and .xic (Parquet consumer), for short chromatograms. OpenSwathMzMLFileCacher mzML->sqMass: lossy_compression defaults to true, so chromatogram RTs are always affected and spectra when -lossy_mass_accuracy > 0. In -process_lowmemory mode the constructor arguments at OpenSwathMzMLFileCacher.cpp:163 are shifted, so lossy mode with 1e-4 accuracy is always on. Also SqMassFile(use_lossy_numpress) from C++ and pyOpenMS.

**Upstream evidence.** src/openms/source/FORMAT/MSNUMPRESS/MSNumpress.cpp:242-245 `if (dataSize < 3) { return 0; // we just encode the first two points as floats }`, but encodeLinear :326 `ints[1] = static_cast<long long>(data[0] * fixedPoint + 0.5);` and decodeLinear :443 `result[0] = ints[1] / fixedPoint;`. MSNumpressCoder.cpp:135 falls back only `if (fixedPoint < 0.0)`. MzMLSqliteHandler.cpp:1079-1081 `numpressErrorTolerance = -1.0; // skip check, faster ... linear_fp_mass_acc = linear_abs_mass_acc_;` and :1322 `npconfig_mz.linear_fp_mass_acc = 0.05;` for chromatogram RT. MSChromatogramParquetConsumer.cpp:443 `const bool use_lossy_compression = true;` with :461-463 the same skipped check and 0.05 accuracy. MSNumpress.cpp differs from the pre-fix OpenMS 4 file only in CRLF line endings.

**Proof.** packages/core@4f5c86f SpectrumAccessSqMass_test.cpp section '[EXTRA] reading spectra written by MSDataSqlConsumer', lines 342-393: one- and two-peak spectra written with lossy=true, accuracy 1e-4; TEST_REAL_SIMILAR m/z 100/101 fails on pre-fix (NaN). As written it calls the new finalize(); relying on scope exit reproduces it on the old API. The Rust log also reports an executed 42-case raw-codec probe: 12 short positive-accuracy cases decoded to NaN.

**Fix in OpenMS4 Core.** packages/core 181dadf: src/openms/source/FORMAT/MSNUMPRESS/MSNumpress.cpp (optimalLinearFixedPointMass returns 0 only for dataSize == 0; optimalLinearFixedPoint guards zero leading values)

<a id="cpp-219"></a>
### CPP-219: Chromatogram precursor reload drops supplemental activation metadata

**P1** · data-loss · valid-edge · proof: regression-test  

**Why it is a bug.** An mzML round trip of a chromatogram precursor carrying supplemental activation loses those values. Because the writer replaces MS:1002631 with the supplemental term, the EThcD/ETciD activation method is lost as well, with only an 'Unhandled cvParam' warning. It is real data loss on valid input, but such chromatograms are rare, so P1 rather than P0.

**Who reaches it.** Any mzML load (MzMLFile, FileHandler, all TOPP tools reading mzML, pyOpenMS) of chromatograms with ETD-plus-supplemental activation, including files OpenMS itself wrote.

**Upstream evidence.** src/openms/source/FORMAT/HANDLERS/MzMLHandler.cpp:1990-2005 spectrum branch only: `else if (accession == "MS:1002679" || accession == "MS:1002678" || accession == "MS:1002680") { spec_.getPrecursors().back().setMetaValue(...); ... ETciD / EThcD }`. The chromatogram branch (:2033-2154) has no such route and ends `else { warning(LOAD, "Unhandled cvParam '" ...); }` (:2150-2153). The writer is shared: :5932 `writePrecursor_(os, chromatogram.getPrecursor(), validator);` and :4712-4713 suppress MS:1002631 when the supplemental meta value exists, which :4736 writeUserParam_ then emits as a cvParam.

**Proof.** packages/core@4f5c86f src/tests/class_tests/openms/source/MzMLFile_test.cpp section '[EXTRA] chromatogram precursors keep supplemental activation': store/load a chromatogram precursor with EThcD plus supplemental meta values; the metaValueExists and EThcD count checks fail on the pre-fix reader.

**Fix in OpenMS4 Core.** packages/core 56f5f29: src/openms/source/FORMAT/HANDLERS/MzMLHandler.cpp (chromatogram activation branch handles MS:1002678/1002679/1002680)

<a id="cpp-145"></a>
### CPP-145: MzTab parameter rendering fails to quote a bare comma

**P1** · data-loss · valid-edge · proof: static-only  

**Why it is a bug.** A name or value with a comma not followed by a space (e.g. '2,4-...') is written unquoted, giving a five-field cell: MzTabFile::load then throws on OpenMS's own output, and spec readers split it wrongly. Upstream exporters build their parameters through fromCellString, and QC TIC values use ', ', which does get quoted. So the trigger is valid-edge data, such as a load-then-store round trip of a file with a quoted bare-comma name: P1.

**Who reaches it.** MzTabFile::store and MzTabMFile::store, for every MzTabParameter cell (metadata, search_engine, score types); pyOpenMS MzTabFile.load followed by store

**Upstream evidence.** src/openms/source/FORMAT/MzTabBase.cpp:337 `if (StringUtils::hasSubstring(name_, ", "))` and :348 `if (StringUtils::hasSubstring(value_, ", "))` in MzTabParameter::toCellString. MzTabParameter::fromCellString in the same file (about lines 367-410) splits on every unquoted comma and throws ConversionError unless it finds exactly 4 fields.

**Proof.** No class test at 4f5c86f round-trips a bare-comma parameter. The Rust log is a source review with no C++ execution.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/MzTabBase.cpp (hasSubstring(name_, ',') and hasSubstring(value_, ','))

<a id="cpp-151"></a>
### CPP-151: MzTab-M exporter changes metadata keys before lookup

**P1** · data-loss · valid-edge · proof: static-only  

**Why it is a bug.** A feature, observation-match or compound meta value whose key contains a space still gets an opt_global_a_b column, but it is looked up as 'a_b', so every row exports null: silent data loss when writing mzTab-M. AccurateMassSearchEngine's own keys (identifier, description, modifications, chemical_formula, mz_error_ppm, mz_error_Da) contain no spaces, so it takes user or third-party meta keys to trigger: P1.

**Who reaches it.** TOPP AccurateMassSearch with featureXML input and non-legacy id_format (AccurateMassSearchEngine.cpp:889, AccurateMassSearch.cpp:204-207); pyOpenMS MzTabM.exportFeatureMapToMzTabM followed by MzTabMFile.store

**Upstream evidence.** src/openms/source/FORMAT/MzTabM.cpp:108, 118 and 137 in getFeatureMapMetaValues_: `std::transform(keys.begin(), keys.end(), keys.begin(), [&](std::string& s) { return StringUtils::substitute(s, ' ', '_'); });`, and the same for obsm_keys and compound_keys. addMetaInfoToOptionalColumns (78-93) substitutes again for the column name at line 87, then tests `meta.metaValueExists(key)` with the already-substituted key. It is called at lines 561, 614, 615 and 651.

**Proof.** No class test at 4f5c86f exports a meta key containing a space. The Rust log is a source review with no C++ execution.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/MzTabM.cpp (the three pre-lookup key substitutions removed)

<a id="cpp-167"></a>
### CPP-167: mzIdentML writer places C-terminal modification at last-residue location

**P1** · data-loss · valid-edge · proof: static-only  

**Why it is a bug.** A peptide's C-terminal modification is written at the last-residue location instead of length+1. OpenMS's own loader then puts it on the last residue, or drops it with a warning when it has no residue specificity, and spec-following consumers misplace it. This is silent corruption of a standard format, but C-terminal modifications and C_TERM cross-links are uncommon in routine searches, hence P1.

**Who reaches it.** IDFileConverter and any tool writing mzIdentML via FileHandler::storeIdentifications; OpenPepXL/cross-link mzIdentML output (OpenPepXL.cpp:252); pyOpenMS MzIdentMLFile.store (bind_misc.cpp:4735)

**Upstream evidence.** origin/develop src/openms/source/FORMAT/HANDLERS/MzIdentMLHandler.cpp:1366 `p += "\t\t<Modification location=\"" + StringUtils::toStr(hit.getSequence().size()) + "\">\n";`, :1761 `StringUtils::toStr(peptide_sequence.size())`, and :1939 `StringUtils::toStr(peptide_sequence.size() + 2)` (beta C_TERM cross-link). MzIdentMLFile::store uses this handler (MzIdentMLFile.cpp:49). The loader MzIdentMLDOMHandler (MzIdentMLFile.cpp:38) treats `index == aas.size() + 1` as C-terminal (MzIdentMLDOMHandler.cpp:2651, :2748, :2813, :2903) and otherwise calls `aas.setModification(index - 1, ...)` (:2913). The DOM writer uses size()+1 (:3024), and MzIdentMLDOMHandler.h:131 documents 'peptide_length + 1 = C-terminus'.

**Proof.** MzIdentMLFile_test.cpp is unchanged in the ci.2..4f5c86f range. The existing tests (:134-148) cover load-time inference for location-less terminal modifications, not a C-terminal store/load round trip. The Rust log entry says it was not executed.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf: src/openms/source/FORMAT/HANDLERS/MzIdentMLHandler.cpp, writePeptideHit and writeXLMSPeptideHit write size()+1, and the beta-peptide C_TERM cross-link writes size()+1 instead of size()+2

<a id="cpp-193"></a>
### CPP-193: Spectrum/chromatogram IDs and peptide sequence remain unescaped SQL values

**P1** · data-loss · valid-edge · proof: static-only  

**Why it is a bug.** A valid native ID or peptide_sequence containing an apostrophe breaks the concatenated SQL. The write then throws after the DATA blobs are already committed, leaving an orphan-row partial sqMass file. For compounds, OpenSwath stores the compound id as peptide_sequence, and metabolite names such as 5'-nucleotides contain apostrophes. Crafted IDs could also inject SQL statements into the output database.

**Who reaches it.** Writing .sqMass: OpenSwathWorkflow -out_chrom .sqMass (MSDataSqlConsumer, OpenSwathBase.cpp:359), OpenSwathMzMLFileCacher, SqMassFile::store (FileConverter), pyOpenMS MzMLSqliteHandler/SqMassFile

**Upstream evidence.** origin/develop src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp:1169-1170 `run_id_ << ",'" << spec.getNativeID() << "'," <<`; :1204 `"," << activation_method << ",'" << pepseq << "'" << "); "`; :1405 `... << run_id_ << ",'" << chrom.getNativeID() << "'); "`; :1425 same for chromatogram pepseq. These run through sqlite3_exec (SqliteConnector.cpp:134). The DATA rows are committed earlier outside the transaction (:1269/:1283, :1480/:1494, before BEGIN at :1286/:1497). Only the RUN path (:897-900) is parameterized.

**Proof.** Source-reviewed only per the Rust log. There is no OpenMS 4 test with an apostrophe in a native ID or sequence. The upstream MzMLSqliteHandler_test.cpp:508-536 injection test covers only the loaded file path (RUN row).

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp (StringUtils::quote(value, '\'', QuotingMethod::DOUBLE) for native IDs and peptide sequences)

<a id="cpp-227"></a>
### CPP-227: Download filename selection does not prevent concurrent overwrite

**P1** · data-loss · valid-edge · proof: static-only  

**Why it is a bug.** Two downloadFile calls whose URLs share a basename can both pass the fs::exists check before either opens the file. The second std::ofstream then truncates and replaces the first file, and both calls log success for the same path. A file created by another process in that gap is truncated the same way. Per the rubric, data loss on valid but uncommon concurrent use is P1. Practical urgency is low: the window is microseconds (the open happens after the transfer finishes) and nothing in OpenMS calls downloadFile.

**Who reaches it.** Public C++ API OpenMS::Network::downloadFile only. No in-tree library or TOPP caller exists (only Network_test), and there is no pyOpenMS binding.

**Upstream evidence.** origin/develop src/openms/source/SYSTEM/Network.cpp:39-46 `fs::path dest(dest_folder); if (!fs::exists(dest / basename)) return basename; ... while (fs::exists(dest / (basename + "." + std::to_string(i)))) ++i;`, then :60-61 `std::string filename = folder + "/" + saveFileName_(url, folder); std::ofstream ofs(filename, std::ios::binary);`. That is a truncating open with no exclusive create, against the promise in src/openms/include/OpenMS/SYSTEM/Network.h:36-38 that 'existing files are never overwritten'. The pre-fix file at ci.2 is identical.

**Proof.** Network_test.cpp at 4f5c86f has only the single-download section; no concurrent test was added. The Rust log reports no executed interleaving. The check-then-truncating-open race (TOCTOU) is evident from source.

**Fix in OpenMS4 Core.** OpenMS4 core 56f5f29: src/openms/source/SYSTEM/Network.cpp createUnusedFile_ (fopen "wbx" exclusive create) and Network.h docs; no test

<a id="cpp-008"></a>
### CPP-008: ProForma modified ranges omit their residue annotations

**P1** · wrong-result · valid-edge · proof: regression-test  
**Affected:** [`src/openms/source/CHEMISTRY/ProForma.cpp`]: resolution at 2113–2117, mass accumulation at 1958–1965, and mass issue checking at 2521–2532. Parser handling at 1145–1175 stores these inner annotations.

**Why it is a bug.** When a residue inside a ProForma modified range carries its own modification, e.g. (M[UNIMOD:35]A)[+1], getMonoWeight silently leaves out that modification's mass. canCalculateMass also never flags an unresolvable inner modification. The mass is silently wrong for valid but uncommon ProForma syntax, P1.

**Who reaches it.** ProForma::getMonoWeight (Peptidoform and PeptidoformIon), canCalculateMass, getMassCalculationIssues and resolveModifications, in C++ and pyOpenMS (bind_chemistry.cpp:1391-1396). No TOPP tool computes ProForma masses. The in-tree file readers (QPXFile.cpp:2006-2019, FeatureMapArrowIO.cpp:1663) go through toAASequence, which reports MODIFIED_RANGE as a conversion issue instead.

**Upstream evidence.** origin/develop src/openms/source/CHEMISTRY/ProForma.cpp. Resolution at 2115-2119 handles only the range-level list: `else if (auto* range = std::get_if<ModifiedRange>(&section)) { for (auto& mod : range->modifications) resolveModification_(mod, '\0', ...); }`. Mass at 1960-1968 adds residue masses and then only range-level mods: `for (const auto& elem : range->elements) { const Residue* res = ...; mass += res->getMonoWeight(Residue::Internal); } for (const auto& mod : range->modifications) addModMass(mod);`. The issue check at 2523-2534 validates only range->modifications. The parser does store the inner mods (1164, 1170).

**Proof.** OpenMS4 core 4f5c86f, src/tests/class_tests/openms/source/ProFormaParser_test.cpp section "regression: modifications inside ranges and ambiguous candidates" (2674-2677, added in 86f01c4): TEST_REAL_SIMILAR(ProForma::getMonoWeight(parse("(M[UNIMOD:35]A)[Formula:C]")), AASequence M(Oxidation)A + 12.0). calculateChainMass_, resolveModifications and getMassCalculationIssues are byte-identical between core-v4.0.0-ci.2 and origin/develop (diffed), and that pre-fix code reports no issue but omits the 15.995 Da oxidation, so the test fails.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf, src/openms/source/CHEMISTRY/ProForma.cpp (element mods resolved, accumulated and checked inside ranges); regression test in 86f01c4

<a id="cpp-009"></a>
### CPP-009: Ambiguous mass checks ignore modifications on candidates

**P1** · wrong-result · valid-edge · proof: regression-test  
**Affected:** [`ProForma.cpp`, lines 2506–2519], ambiguous-region mass validation; accumulation at 1949–1956.

**Why it is a bug.** Develop returns a mass for '(?I[+10]L)' that depends on candidate order (10 Da apart). For '(?I[UnknownMod999]L)' it silently counts the unresolved modification as 0 Da instead of reporting it. The result is silently wrong, but only for ambiguous regions whose candidates carry modifications, which is an uncommon ProForma construct.

**Who reaches it.** The ProForma::getMonoWeight / tryGetMonoWeight / canCalculateMass / getMZ C++ API (doc/code_examples/Tutorial_ProForma.cpp) and pyOpenMS (bind_chemistry.cpp:1391-1415). No TOPP tool calls the ProForma mass methods.

**Upstream evidence.** origin/develop (edc7aa4) src/openms/source/CHEMISTRY/ProForma.cpp:2508-2520, getMassCalculationIssues: `std::set<double> masses; for (const auto& elem : region->elements) { ... if (res != nullptr) masses.insert(res->getMonoWeight(Residue::Internal)); ...} if (masses.size() > 1) issues.push_back({...AMBIGUOUS_REGION...})`. It never calls checkModificationForMass_ on elem.modifications. The mass sum at 1951-1958 uses only the first candidate: `for (const auto& mod : region->elements[0].modifications) addModMass(mod);`. The parser attaches brackets to candidates at 1137.

**Proof.** OpenMS4 core 4f5c86f src/tests/class_tests/openms/source/ProFormaParser_test.cpp, section 'regression: modifications inside ranges and ambiguous candidates' (lines 2679-2683; test added in b2079fb). It requires canCalculateMass to be false for '(?I[+10]L)' and '(?I[UnknownMod999]L)'. The pre-fix branch is identical to develop: I and L weigh the same and candidate brackets are never checked, so both TEST_EQUALs fail.

**Fix in OpenMS4 Core.** 181dadf ProForma.cpp collectMassCalculationIssues_ (checks and sums every candidate's modifications), 86f01c4 (empty region); test b2079fb

<a id="cpp-012"></a>
### CPP-012: Smoothed area accumulation uses raw peak intensities

**P1** · wrong-result · valid-common · proof: regression-test  
**Affected:** [`src/openms/source/KERNEL/MassTrace.cpp`, lines 61–78], `computeSmoothedPeakArea`; public description in [`MassTrace.h`, lines 241–247].

**Why it is a bug.** Every smoothed trace gets an area built from raw intensities, while intervals are filtered by the smoothed values, contradicting the documented smoothed area. A trace without smoothed intensities dereferences smoothed_intensities_[0] on an empty vector. It is not P0 because no TOPP tool or library algorithm calls the method (getIntensity(true) uses computeFwhmAreaSmooth), and the deviation from a raw area is small.

**Who reaches it.** MassTrace::computeSmoothedPeakArea, public C++ API and pyOpenMS (bind_kernel.cpp:462). No in-tree caller.

**Upstream evidence.** origin/develop src/openms/source/KERNEL/MassTrace.cpp:66-76: `double int_before = smoothed_intensities_[0]; ... if (smoothed_intensities_[i] > 0.0) { ... peak_area += (int_before + trace_peaks_[i].getIntensity())/2 * rt_diff; } int_before = trace_peaks_[i].getIntensity();`. There is no empty guard. The header MassTrace.h:246 documents 'Sum all non-negative (smoothed!) intensities in the mass trace'. Develop's own MassTrace_test.cpp:495 still expects the mixed value 70303689.0475001.

**Proof.** OpenMS4 core 4f5c86f src/tests/class_tests/openms/source/MassTrace_test.cpp, section 'double computeSmoothedPeakArea() const'. Commit 181dadf changed the expectation to 70322464.7770001, the trapezoid under the smoothed intensities. The pre-fix code, like develop, returns 70303689.0475001, so this test fails on it.

**Fix in OpenMS4 Core.** 1beb468 MassTrace.cpp (smoothed intensities throughout, 0 for empty); test expectation 181dadf

<a id="cpp-015"></a>
### CPP-015: Cross-link mass depends on endpoint traversal order

**P1** · wrong-result · valid-edge · proof: regression-test  
**Affected:** [`src/openms/source/CHEMISTRY/ProForma.cpp`, lines 1927–1938], `addModMass`; modification fallback at 1889–1909 and shared cross-link set at 2589–2598.

**Why it is a bug.** When the label-only endpoint is written before the chemistry-bearing one, the linker mass is silently dropped (138.068 Da for DSS). This is valid ProForma, inter-chain or intra-chain, e.g. EMEVTK[#XL1]SESPEK[XLMOD:02001#XL1], and it changes the precursor mass and m/z from getMonoWeight/getMZ. The ordering is uncommon within an already specialised construct.

**Who reaches it.** ProForma::getMonoWeight / tryGetMonoWeight / getMZ for Peptidoform and PeptidoformIon (C++ API), and pyOpenMS getMonoWeight/getMonoWeightIon/getMZ (bind_chemistry.cpp:1395-1415). No TOPP tool.

**Upstream evidence.** origin/develop src/openms/source/CHEMISTRY/ProForma.cpp:1929-1940, addModMass: `if (!mod.alternatives.empty() && mod.alternatives[0].second.has_value()) { ... if (label.type == Label::Type::CROSSLINK) { if (counted_crosslinks.contains(label.identifier)) return; counted_crosslinks.insert(label.identifier); } } auto [has_mass, mod_mass] = getModificationMass_(mod);`. A label-only bracket parses to an empty InfoTag plus a label (1206: `InfoTag empty_tag; ... return {std::move(empty_tag), std::move(label)};`), and getModificationMass_ returns {true, 0.0} for an InfoTag (1910).

**Proof.** OpenMS4 core 4f5c86f src/tests/class_tests/openms/source/ProFormaParser_test.cpp, section 'regression: cross-link mass does not depend on endpoint order' (lines 2698-2705; added in b2079fb). Both 'K[#XL1]//K[+138.06807961#XL1]' and the reverse must equal 2*K + 138.068. The pre-fix addModMass, identical to develop, lets the label-only endpoint claim XL1 at 0 Da, so the label-first case fails.

**Fix in OpenMS4 Core.** 181dadf ProForma.cpp calculateChainMass_/addModMass (only a chemistry-defining endpoint claims the label); test b2079fb

<a id="cpp-154"></a>
### CPP-154: pepXML fixed protein C-terminal modification misses terminal branch

**P1** · wrong-result · valid-edge · proof: regression-test  

**Why it is a bug.** A fixed protein C-terminal modification in pepXML is either dropped (no aminoacid) or placed on every matching residue of every peptide. The sibling N-term branch applies fixed protein N-term mods to all peptides. Either way the reported peptide masses are wrong. Fixed protein-terminal mods are valid but uncommon, so P1. Fixing the enum alone would put the mod on every peptide; the upstream fix must also check protein boundaries via PeptideEvidence aa_before/aa_after, including pepXML's '-'.

**Who reaches it.** CometAdapter (fixed 'Protein C-term' mods become add_Cterm_protein, CometAdapter.cpp:592-596) and MSFraggerAdapter (statmod add_cterm_protein, MSFraggerAdapter.cpp:716-718), which reload their pepXML; IDFileConverter pepXML import; pyOpenMS PepXMLFile.load

**Upstream evidence.** origin/develop src/openms/source/FORMAT/PepXMLFile.cpp:2134-2135: `else if (mod.getRegisteredMod()->getTermSpecificity() == ResidueModification::C_TERM || mod.getRegisteredMod()->getTermSpecificity() == ResidueModification::PROTEIN_N_TERM)`, so PROTEIN_C_TERM (set at :213-217 from protein_terminus c/Y) falls to the `else // go through the sequence` residue loop at :2148-2164. The N-term branch at :2126-2131 sets PROTEIN_N_TERM fixed mods on every peptide without checking protein position. The warning at :2144 says 'N-terminus' where it means the C-terminus.

**Proof.** src/tests/class_tests/openms/source/PepXMLFile_test.cpp, section '[EXTRA] fixed protein-terminal modifications require terminal evidence' (added in 181dadf). On pre-fix code the protein C-term 'Amidated' never reaches the C-term branch, so the protein-C-terminal hit has no C-term mod. The protein N-term 'Acetyl' is set on all three hits. Both TEST_EQUAL checks fail.

**Fix in OpenMS4 Core.** 181dadf + e4dcc47 src/openms/source/FORMAT/PepXMLFile.cpp (PROTEIN_C_TERM in the C-term branch, protein-boundary evidence gate, '-' marker accepted)

<a id="cpp-157"></a>
### CPP-157: qcML removeAllAttachments omits set-only entries

**P1** · wrong-result · valid-edge · proof: regression-test  

**Why it is a bug.** Attachments on a set whose ID is not also a run ID are never removed, which breaks the documented all-runs/sets contract. QCShrinker without -run therefore leaves set-level tables and plots (for example from QCEmbedder addSetAttachment) in its output. Valid but uncommon input, so P1 by the rubric. Practical urgency is low: no scientific value changes, the file is just not fully shrunk.

**Who reaches it.** QCShrinker (no target run, QCShrinker.cpp:125-130); pyOpenMS QcMLFile.removeAllAttachments

**Upstream evidence.** origin/develop src/openms/source/FORMAT/QcMLFile.cpp:511-517: `void QcMLFile::removeAllAttachments(const std::string& at) { for (... it = runQualityAts_.begin(); it != runQualityAts_.end(); ++it) { removeAttachment(it->first, at); } }`. removeAttachment reaches setQualityAts_[r] only if existsSet(r) (:494), and existsRun/existsSet check the QP maps (:326, :345). QcMLFile.h:119 documents: 'Removes attachment with cv accession at from all runs/sets.'

**Proof.** src/tests/class_tests/openms/source/QcMLFile_test.cpp, section 'void removeAllAttachments(std::string at)' (added in b2079fb). Pre-fix, the set-only ID 'set' is never visited and the QP-less run 'orphan' fails existsRun. Both keep the 'remove' attachment, so two TEST_EQUAL checks fail.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/QcMLFile.cpp (remove_if over every runQualityAts_ and setQualityAts_ list)

<a id="cpp-158"></a>
### CPP-158: qcML map2csv emits misaligned rows when a column is missing

**P1** · wrong-result · valid-edge · proof: regression-test  

**Why it is a bug.** Columns come from the first row only, and a missing cell emits neither a value nor a separator. Later values shift under the wrong header, and columns absent from the first row are dropped from the CSV. The code is reached through QCExtractor's 'set id' export (exportIDstats) and pyOpenMS map2csv. No active OpenMS tool writes the QC:0000043-47/53-57 set parameters that exportIDstats reads (the QCMerger code is commented out), so the input is uncommon: P1.

**Who reaches it.** QCExtractor qp 'set id' via exportIDstats (QCExtractor.cpp:132-136); pyOpenMS QcMLFile.map2csv/exportIDstats

**Upstream evidence.** origin/develop src/openms/source/FORMAT/QcMLFile.cpp:686-689: `for (... it = cvs_table.begin()->second.begin(); it != cvs_table.begin()->second.end(); ++it) { cols.push_back(it->first); }`. At :704-709: `if (found != it->second.end()) { ret += found->second; ret += separator; } //TODO else throw error`.

**Proof.** src/tests/class_tests/openms/source/QcMLFile_test.cpp, section 'std::string map2csv(const std::map<std::string, std::map<std::string, std::string> > &cvs_table, const std::string &separator) const' (added in b2079fb). Pre-fix output for {id:{A,B}, ms2:{B,C}} is 'qp\tA\tB\t\nid\t1\t2\t\nms2\t3\t\n' instead of the expected union table.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/QcMLFile.cpp (header is the union of row keys; empty cells keep their separator)

<a id="cpp-160"></a>
### CPP-160: qcML TIC slump percentage truncates before multiplication

**P1** · wrong-result · valid-common · proof: regression-test  

**Why it is a bug.** Every run with more than 100 spectra reports a 0% TIC and RIC slump, and the value is wrong whenever the spectrum count does not divide 100. It is a qcML QC summary value, not an identification or quantification result, hence P1 rather than P0. The empty-experiment division by zero cannot be reached on its own, because collectQCData already dereferences exp.begin() for the RT range before this point.

**Who reaches it.** QCCalculator with qcML output (FileHandler::storeQC -> QcMLFile::collectQCData, FileHandler.cpp:1822); pyOpenMS QcMLFile (bind_misc.cpp:5053)

**Upstream evidence.** origin/develop src/openms/source/FORMAT/QcMLFile.cpp:1297 (QC:0000023 TIC slump) `qp.value =StringUtils::toStr((100 / exp.size()) * below_10k);` and :1371 (QC:0000057 RIC slump) the same expression, with Size operands, so integer division comes first.

**Proof.** packages/core@4f5c86f src/tests/class_tests/openms/source/QcMLFile_test.cpp, section 'regression: slump percentage for more than one hundred spectra' (added b2079fb). It builds 200 MS1 spectra plus a TIC with 100 points below 10k and expects exportQP(QC:0000023) and exportQP(QC:0000057) to be "50". The pre-fix formula gives (100/200)*100 = "0".

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf (in core-v4.0.0-ci.4 / 4f5c86f): src/openms/source/FORMAT/QcMLFile.cpp, both slump sites now `exp.empty() ? Size(0) : 100 * below_10k / exp.size()`; test added in b2079fb

<a id="cpp-174"></a>
### CPP-174: mzXML precursor value and window width depend on SAX chunking

**P1** · wrong-result · valid-edge · proof: regression-test  

**Why it is a bug.** If the precursorMz text reaches the handler in several SAX chunks (a comment, CDATA section or character reference inside it), the precursor m/z is parsed from the last chunk only. The isolation window is halved again for each chunk, and the m/z range filter can drop the wrong scan. The effect is a silently wrong precursor m/z, but common mzXML writers do not emit such text, so this is valid but uncommon input: P1.

**Who reaches it.** MzXMLFile::load and FileHandler .mzXML loading; FileConverter and TOPP tools consuming mzXML precursors; pyOpenMS MzXMLFile

**Upstream evidence.** src/openms/source/FORMAT/HANDLERS/MzXMLHandler.cpp:567-588. For each characters() chunk inside precursorMz it does `double mz_pos = asDouble_(transcoded_chars);`, calls setMZ(mz_pos), and calls `setIsolationWindowLowerOffset(0.5 * window_width); setIsolationWindowUpperOffset(0.5 * window_width);`, then applies the precursor m/z range filter to that chunk. At :597 `exp_->getInstrument().setMetaValue("#comment", transcoded_chars);` and :605 `spectrum_data_.back().spectrum.setComment(transcoded_chars);` overwrite with the current chunk. SAX2HandlerAdapter.h:55 forwards characters() without buffering.

**Proof.** MzXMLFile_test.cpp, section "regression : SAX chunk boundaries and mismatched peak counts". `<precursorMz windowWideness="10">12<!-- split -->3.<![CDATA[45]]></precursorMz>` expects m/z 123.45 with offsets 5.0/5.0; pre-fix code gives 45 with 1.25/1.25. Split scan and instrument comments expect the full text.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf, src/openms/source/FORMAT/HANDLERS/MzXMLHandler.cpp (text is accumulated in char_rest_ and parsed once in onEndElement; comments are appended)

<a id="cpp-178"></a>
### CPP-178: MSstats missing design pair silently uses sample0

**P1** · wrong-result · valid-edge · proof: regression-test  

**Why it is a bug.** When a (file, label) pair is missing from the design, operator[] silently maps it to sample row 0, fraction 0 and run 0. Those intensities are then written under another sample's Condition and BioReplicate. Two inputs trigger this: an LFQ consensusXML whose header carries channel_id 0 (label 1 by OpenMS's own convention), or a TMT design that leaves out a channel, which isValid_ accepts. Both are valid but uncommon, so this is a silent wrong result on edge-case input.

**Who reaches it.** MSstatsConverter (-method LFQ and ISO); pyOpenMS MSstatsFile.storeLFQ/storeISO. ProteomicsLFQ also calls storeLFQ, but its maps normally carry no channel_id.

**Upstream evidence.** origin/develop src/openms/source/FORMAT/MSstatsFile.cpp:439-447 (storeLFQ) reads `path_label_to_sample[tpl1]`, `path_label_to_fraction[tpl1]`, `run_map[tpl2]` and `path_label_to_fractiongroup[tpl1]` on non-const maps. storeISO does the same at :700-705 (`const unsigned sample = path_label_to_sample[tpl1];`). The LFQ label is the raw 0-based `cf_labels.push_back(Int(column.getMetaValue("channel_id")));` (:108), whereas ConsensusMap.cpp:817 converts it with `getMetaValue("channel_id")) + 1`. ExperimentalDesign::isValid_ (ExperimentalDesign.cpp:745-826) does not require every file to declare every label.

**Proof.** OpenMS4 4f5c86f src/tests/class_tests/openms/source/MSstatsFile_test.cpp, section storeLFQ: sets channel_id=2 on a design that only has label 1 and expects TEST_EXCEPTION(Exception::MissingInformation, ...). The pre-fix operator[] inserted 0 and wrote sample row 0 without throwing.

**Fix in OpenMS4 Core.** OpenMS4 181dadf, src/openms/source/FORMAT/MSstatsFile.cpp (find() + MissingInformation in storeLFQ and storeISO)

<a id="cpp-180"></a>
### CPP-180: MSstats aggregation collapses equal intensities at distinct times

**P1** · wrong-result · valid-edge · proof: regression-test  

**Why it is a bug.** With sum or mean summarization, features of the same peptide ion and run at different retention times that happen to have exactly equal intensity are merged by the std::set. The Intensity written for MSstats is therefore too low (sum) or wrong (mean). Sum and mean are non-default (MSstatsConverter defaults to max, ProteomicsLFQ uses max) and exact float ties are uncommon, so this is a wrong quantity on valid edge-case input.

**Who reaches it.** MSstatsConverter -method LFQ -retention_time_summarization_method sum|mean; pyOpenMS MSstatsFile.storeLFQ. storeISO and the max/min methods are unaffected.

**Upstream evidence.** origin/develop src/openms/source/FORMAT/MSstatsFile.cpp:146-160 declares `set<MSstatsFile::Coordinate> retention_times{}; set<MSstatsFile::Intensity> intensities{};` and adds with `intensities.insert(get<0>(p));`. :187-194 computes `meanIntensity_(intensities)` / `sumIntensity_(intensities)`. include/OpenMS/FORMAT/MSstatsFile.h:137-150 sums and divides over a `std::set<IntensityType>`.

**Proof.** OpenMS4 4f5c86f src/tests/class_tests/openms/source/MSstatsFile_test.cpp, section storeLFQ: three features at RT 10/20/30 with intensities 10, 10 and 20; expects 40 for sum and 40/3 for mean (TEST_REAL_SIMILAR on row[9]). The pre-fix set gives 30 and 15.

**Fix in OpenMS4 Core.** OpenMS4 181dadf, src/openms/source/FORMAT/MSstatsFile.cpp (vector of intensities, one per distinct RT)

<a id="cpp-208"></a>
### CPP-208: SpectrumAccessSqMass bulk read does not preserve the configured view order or duplicates

**P1** · wrong-result · valid-edge · proof: regression-test  

**Why it is a bug.** For a subset view that is not in ascending id order, getAllSpectra returns spectra in SQL order, so position k silently stops matching getSpectrumById(k); a view with a repeated id throws although the per-position getters accept it. This is a wrong result or exception on valid but uncommon views (P1). In-tree subsets come from readSpectraForWindow/readMS1Spectra: that SQL has no ORDER BY, but in practice it is ascending and unique, since only the first precursor is stored per spectrum (MzMLSqliteHandler.cpp:1177-1180).

**Who reaches it.** C++ API: SpectrumAccessSqMass::getAllSpectra, and SpectrumAccessOpenMSInMemory(SpectrumAccessSqMass&) (SpectrumAccessOpenMSInMemory.cpp:20-23), used when OpenSwath loads sqMass data into memory with custom views. pyOpenMS does not bind getAllSpectra, and its SpectrumAccessOpenMSInMemory constructor accepts only SpectrumAccessOpenMS.

**Upstream evidence.** SpectrumAccessSqMass.cpp:137 `handler_.readSpectra(tmp_spectra, sidx_, false);` passes the view unchanged. MzMLSqliteHandler.cpp:755 `select_sql +=std::string("WHERE SPECTRUM.ID IN (") + integerConcatenateHelper(indices) + ")";` has no ORDER BY, and repeated ids collapse. :398-402 `if (indices.size() != exp.size()) { throw Exception::IllegalArgument(... "Illegal spectral indices detected "`. Meanwhile getSpectrumById honours the position (`sidx_[id]`, :75).

**Proof.** OpenMS4 core 4f5c86f, SpectrumAccessSqMass_test.cpp, section void getAllSpectra(...), block starting at line 277 ('a view in reverse order and with a repeated spectrum', indices [1,0,1]). On pre-fix code readSpectra returns 2 rows for 3 ids and throws IllegalArgument, failing the section. Its per-position comparisons with getSpectrumById/getSpectrumMetaById cover the reordering. The OpenMS 4 ledger also records a read-only sqlite3 probe: IN (1,0) returns ids 0,1.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf: SpectrumAccessSqMass::getAllSpectra reads the sorted unique ids once and rebuilds the configured view (lower_bound), repeats included

<a id="cpp-220"></a>
### CPP-220: Negative initial linear-Numpress coordinates can wrap during sqMass writing

**P1** · wrong-result · valid-edge · proof: regression-test  

**Why it is a bug.** In lossy sqMass writing, a negative first or second RT (or m/z) is stored as a huge positive value because the accuracy check is skipped. The array reloads silently shifted. Negative leading RTs are valid but uncommon (for example transformed or offset RT axes), so P1.

**Who reaches it.** OpenSwathWorkflow -out_chrom .sqMass (lossy hard-coded) and .xic (MSChromatogramParquetConsumer.cpp:443-472, the same unchecked encoding). OpenSwathMzMLFileCacher mzML->sqMass (lossy by default). SqMassFile with use_lossy_numpress via C++ or pyOpenMS.

**Upstream evidence.** src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp:1111 and :1351 `if (use_lossy_compression_) { MSNumpressCoder().encodeNPRaw(data_to_encode, uncompressed_str, npconfig_mz); ...` with no domain check and :1079/:1320 `numpressErrorTolerance = -1.0; // skip check, faster`. MSNumpress.cpp:326-330 `ints[1] = static_cast<long long>(data[0] * fixedPoint + 0.5); ... result[8+i] = (ints[1] >> (i*8)) & 0xff;` stores the low 32 bits; decodeLinear :438-443 rebuilds from `unsigned int init` without sign extension.

**Proof.** packages/core@4f5c86f src/tests/class_tests/openms/source/SqMassFile_test.cpp section '[EXTRA_NEGATIVE_LINEAR] void store(...)': chromatogram RT [-100,-99,-98] stored with use_lossy_numpress=true and accuracy 1e-4 must reload unchanged. Pre-fix, the fixed point is 10 (0.05 RT accuracy), -999 wraps to 4294966297, and the first RT reloads as about 4.29e8.

**Fix in OpenMS4 Core.** packages/core 56f5f29: src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp (linearNumpressCanStore_: such arrays are stored zlib-only with compression code 1). The Parquet consumer is not covered there.

<a id="cpp-228"></a>
### CPP-228: Squaring Gumbel negative log likelihood can change the optimum

**P1** · wrong-result · valid-edge · proof: regression-test  

**Why it is a bug.** Because the fitter minimises NLL^2, it returns a wrong location and scale whenever the NLL at the maximum-likelihood estimate is negative. For Gumbel data that happens roughly when the scale b < exp(-(1+gamma)) ≈ 0.21, and the regression sample confirms it. This is a silent wrong fit on valid data. It is P1, not P0, because narrow-scale scores are uncommon: the class-test score data have b≈0.6 and are unaffected. The fitter is also reached only through C++ API: its sole caller PosteriorErrorProbabilityModel::fitGumbelGauss is used by no TOPP tool (IDPosteriorErrorProbability calls fit()) and is not bound in pyOpenMS.

**Who reaches it.** Math::GumbelMaxLikelihoodFitter::fitWeighted and PosteriorErrorProbabilityModel::fitGumbelGauss, C++ API only; the header @todo says fitGumbelGauss is not yet exposed via parameters. IDPosteriorErrorProbability uses PosteriorErrorProbabilityModel::fit, which does not use this fitter, and pyOpenMS binds neither.

**Upstream evidence.** origin/develop src/openms/source/MATH/STATISTICS/GumbelMaxLikelihoodFitter.cpp:62-66 `fvec(0) += *wit * (-logsigma - diff - exp(-diff)); } double foo = -fvec(0); fvec(0) = foo; fvec(1) = 0.0;`, minimised at :80-82 by `Eigen::LevenbergMarquardt<Eigen::NumericalDiff<GumbelDistributionFunctor>,double> lm(numDiff); ... lm.minimize(x_init);`. That is least squares on the residuals [NLL, 0], i.e. it minimises NLL^2. The pre-fix file at ci.2 is identical.

**Proof.** 4f5c86f src/tests/class_tests/openms/source/GumbelMaxLikelihoodFitter_test.cpp, section '[EXTRA] fitWeighted finds the maximum-likelihood estimate of a narrow sample'. It starts from a=1, b=2 with x={0.10,0.12,0.15,0.11,0.13} and unit weights, and expects a=0.11378962, b=0.01413100. A Python check (scratchpad b200/gumbel_check.py) gives NLL=+9.03 at the start point and -13.39 at the expected estimate, where the gradient is about 1e-5 (a stationary point). Levenberg-Marquardt never increases NLL^2, so it cannot move from NLL^2 of 81.5 to 179. The pre-fix code therefore settles on the NLL=0 contour and fails this section.

**Fix in OpenMS4 Core.** OpenMS4 core 56f5f29: src/openms/source/MATH/STATISTICS/GumbelMaxLikelihoodFitter.cpp solves the Gumbel likelihood equations directly (closed-form location, bisection for scale), with a test in GumbelMaxLikelihoodFitter_test.cpp

<a id="cpp-001"></a>
### CPP-001: DateTime ignores failed calendar conversion

**P1** · wrong-result · valid-edge · proof: executed-probe  
**Affected:** [`src/openms/source/DATASTRUCTURES/DateTime.cpp`, lines 48–83], `addSecsToFields_`.

**Why it is a bug.** On hosts whose timegm/_mkgmtime reject early dates (macOS below 1900; Windows _mkgmtime's documented range starts at 1970), addSecs silently turns a valid date into 1969-12-31 or garbage fields; glibc Linux is unaffected. By the rubric this is a wrong result on valid edge input (P1), but practical urgency is low: nothing in OpenMS calls addSecs.

**Who reaches it.** C++ API DateTime::addSecs only. No callers in src/openms, src/topp or src/openms_gui, and pyOpenMS (bind_datastructures.cpp:473-523) does not bind addSecs.

**Upstream evidence.** origin/develop src/openms/source/DATASTRUCTURES/DateTime.cpp:65-85 (addSecsToFields_, called by addSecs at 552-557): `time_t tt = _mkgmtime(&t);` / `time_t tt = timegm(&t);` (66/68), then `tt += secs;` (71), `_gmtime64_s(&result, &tt);` / `gmtime_r(&tt, &result);` (75/77), then `year = result.tm_year + 1900; ...` (80-85). Neither conversion result is checked.

**Proof.** Rust log CPP-001 reports an unmodified-source probe (Apple clang 21, arm64 macOS, UBSan). `set("0001-01-01T00:00:00"); addSecs(0)` gave 1969-12-31 23:59:59, and 35 of 301 probe rows were affected; timegm returned -1 with errno 0 for years up to 1899. OpenMS4 has no class test: DateTime_test.cpp is unchanged between core-v4.0.0-ci.2 and 4f5c86f.

**Fix in OpenMS4 Core.** OpenMS4 core 1beb468, src/openms/source/DATASTRUCTURES/DateTime.cpp (daysFromCivil_/civilFromDays_ integer arithmetic)

<a id="cpp-196"></a>
### CPP-196: SWATH selection stops at a matching chromatogram precursor NULL ID

**P1** · wrong-result · valid-edge · proof: executed-probe  

**Why it is a bug.** If a chromatogram's precursor m/z lies within 0.01 of a SWATH window centre, the loop stops at its NULL SPECTRUM_ID row. Files written by writeExperiment store chromatograms first, so OpenSwath silently gets no spectra, or only the first few, for that window and loses its quantification. Typical DIA files carry only a TIC with precursor m/z 0, so the trigger is uncommon: P1 rather than P0.

**Who reaches it.** OpenSwathWorkflow with sqMass input (OpenSwathBase.cpp:126/193, then SwathFile::loadSqMass at SwathFile.cpp:352-358, which calls readSpectraForWindow for each window)

**Upstream evidence.** origin/develop src/openms/source/FORMAT/HANDLERS/MzMLSqliteSwathHandler.cpp:92-95 `"SELECT " "SPECTRUM_ID " "FROM PRECURSOR " "WHERE ISOLATION_TARGET BETWEEN "` has no SPECTRUM_ID IS NOT NULL filter, and :101 `while (sqlite3_column_type( stmt, 0 ) != SQLITE_NULL)` treats a NULL SPECTRUM_ID as end of results. Chromatogram precursors are stored with CHROMATOGRAM_ID only (MzMLSqliteHandler.cpp ~:1417-1431 `INSERT INTO PRECURSOR (CHROMATOGRAM_ID, ...`), and writeExperiment writes chromatograms before spectra (:883-884).

**Proof.** Rust log CPP-196: an adapted C++ probe on kim (GCC 13.3, SQLite 3.45.1) ran the pinned handler source. With a matching chromatogram row first, no IDs came back; with that row between two spectrum rows, only ID 1 came back (oracle/sqlite-swath-s1-probe/result.log). There is no class test: MzMLSqliteSwathHandler_test.cpp is unchanged between ci.2 and 4f5c86f.

**Fix in OpenMS4 Core.** core 181dadf: MzMLSqliteSwathHandler.cpp adds `SPECTRUM_ID IS NOT NULL` and iterates with Sql::nextRow

<a id="cpp-004"></a>
### CPP-004: trimLeft does nothing when every peak is below cutoff

**P1** · wrong-result · valid-edge · proof: static-only  
**Affected:** [`src/openms/source/CHEMISTRY/ISOTOPEDISTRIBUTION/IsotopeDistribution.cpp`, lines 210–220].

**Why it is a bug.** trimLeft(0.5) on intensities [0.1, 0.2] returns the whole distribution instead of an empty one, contradicting its contract and trimRight. That is a wrong result on edge input (P1). The visible effect is limited to direct callers, because every in-tree caller runs trimRight at the same cutoff straight afterwards, which empties the distribution anyway.

**Who reaches it.** pyOpenMS IsotopeDistribution.trimLeft (bind_chemistry.cpp:888) and C++ API. In-tree callers are masked by a following trimRight: FeatureFinderIdentificationAlgorithm.cpp:1188/1254, FeatureFinderAlgorithmMetaboIdent.cpp:595 and IsotopeDistribution::merge:244. FeatureFinderAlgorithmPicked.cpp:372-374 would record trimmed_left=0, but the all-below case cannot occur for its normalized averagine distributions.

**Upstream evidence.** origin/develop src/openms/source/CHEMISTRY/ISOTOPEDISTRIBUTION/IsotopeDistribution.cpp:210-220: `for (auto iter = distribution_.begin(); iter != distribution_.end(); ++iter) { if (iter->getIntensity() >= cutoff) { distribution_.erase(distribution_.begin(), iter); break; } }`. Nothing is erased when no peak qualifies, whereas trimRight (194-208) empties the container in the same case.

**Proof.** The Rust log claims no C++ runtime reproduction. OpenMS4 IsotopeDistribution_test.cpp trimLeft section (191-196) is unchanged ci.2..4f5c86f and only covers a C160 distribution where a peak reaches the cutoff.

**Fix in OpenMS4 Core.** OpenMS4 core 1beb468, src/openms/source/CHEMISTRY/ISOTOPEDISTRIBUTION/IsotopeDistribution.cpp (std::find_if then erase to the first qualifying peak, or to end())

<a id="cpp-006"></a>
### CPP-006: Interpolation overload resizes and then appends coordinates

**P1** · wrong-result · valid-edge · proof: static-only  
**Affected:** [`src/openms/source/ANALYSIS/MAPMATCHING/TransformationModelInterpolated.cpp`, lines 209–234], the `vector<pair<double,double>>` constructor with `preprocess = false`.

**Why it is a bug.** With preprocess=false, N zero anchors are prepended (x=[0,0,0,1,2,3]). The default cspline passes CubicSpline2d's non-decreasing check (adjacent_find with greater, CubicSpline2d.cpp:33) and then divides by the zero interval widths (h[i-1]*h[i], line 141). Linear interpolation and the default two-point-linear extrapolation (lines 275-279) anchor at (0,0), so transformed values are wrong or non-finite: a wrong result on a legitimate but unused constructor path, P1. A related defect outside this finding: global-linear extrapolation (lines 263-268) makes the same resize-then-emplace_back mistake, padding the linear fit with (0,0) points on every constructor path, and it is still present in OpenMS4 at 4f5c86f.

**Who reaches it.** C++ API only: TransformationModelInterpolated(const std::vector<std::pair<double,double>>&, const Param&, bool preprocess=false). No in-tree caller (TransformationModelLowess.cpp:183 uses the DataPoints constructor), and pyOpenMS (bind_analysis.cpp:3289) binds only the DataPoints constructor.

**Upstream evidence.** origin/develop src/openms/source/ANALYSIS/MAPMATCHING/TransformationModelInterpolated.cpp:224-233 (vector<pair<double,double>> constructor, preprocess == false): `x_.resize(data.size()); y_.resize(data.size()); for (const std::pair<double,double>& pair : data) { x_.push_back(pair.first); y_.push_back(pair.second); }`

**Proof.** Source review only per the Rust log. OpenMS4 TransformationModelInterpolated_test.cpp is unchanged ci.2..4f5c86f and has no preprocess=false case.

**Fix in OpenMS4 Core.** OpenMS4 core 1beb468, src/openms/source/ANALYSIS/MAPMATCHING/TransformationModelInterpolated.cpp (reserve instead of resize)

<a id="cpp-007"></a>
### CPP-007: EMG tail expression overflows before its asymptotic branch

**P1** · wrong-result · valid-edge · proof: static-only  
**Affected:** [`src/openms/source/MATH/MISC/EmgGradientDescent.cpp`, lines 419–441], `emg_point`; related derivative expressions in the same file also require review.

**Why it is a bug.** The fit clamps tau to [sigma, 15*sigma] (line 706), so the overflow needs points about 37 sigma or more left of mu, which a sharp peak in a wide window, or sigma shrinking toward its 1e-4 floor, can produce. The loss then turns non-finite and gradient descent stops early (632-639), and applyEstimatedParameters (278, 317, 332) can put inf or NaN into the fitted chromatogram that PeakIntegrator integrates. EMG fitting is opt-in (fit_EMG defaults to false), so this is a wrong quantity on uncommon valid input, P1.

**Who reaches it.** PeakIntegrator with fit_EMG=true (PeakIntegrator.h:937-942), exposed as PeakIntegrator:fit_EMG by MRMTransitionGroupPicker (MRM/OpenSWATH peak picking). Also used by FeatureFinderMultiplexAlgorithm and EICExtractor, and by pyOpenMS EmgGradientDescent.fitEMGPeakModel (bind_misc.cpp:556).

**Upstream evidence.** origin/develop src/openms/source/MATH/MISC/EmgGradientDescent.cpp:435-437 (emg_point): `else if (z <= 6.71e7) { return h * std::exp(-(1.0/2.0) * std::pow(((x - u)/s),2.0)) * (s/t) * std::sqrt(PI/2.0) * std::exp(std::pow((1.0/std::sqrt(2.0) * (s/t - (x - u)/s)),2.0)) * std::erfc(1.0/std::sqrt(2.0) * (s/t - (x - u)/s)); }`

**Proof.** The Rust log claims no executed C++ comparison. OpenMS4 EmgGradientDescent_test.cpp is unchanged ci.2..4f5c86f. By IEEE-754 binary64 arithmetic, exp(z*z) overflows once z > 26.64, while the Gaussian factor and erfc(z) underflow toward 0, so the product is +inf or NaN where the true EMG value is about 0 (for example x=-40, mu=0, sigma=tau=1 gives z=29).

**Fix in OpenMS4 Core.** OpenMS4 core 1beb468, src/openms/source/MATH/MISC/EmgGradientDescent.cpp (erfcx_ scaled complementary error function in emg_point). The analogous derivative expressions in the z <= 6.71e7 branches at lines 79, 124, 169 and 215 were left unchanged.

<a id="cpp-016"></a>
### CPP-016: Count-only mzML loading can still decode peak arrays

**P1** · wrong-result · valid-edge · proof: static-only  
**Affected:** [`src/openms/source/FORMAT/HANDLERS/MzMLHandler.cpp`], normal spectrum enqueue at 1401–1427, binary population at 203–217, error propagation at 244 and accepted-RT count handling at 2341–2351.

**Why it is a bug.** MzMLFile::loadSize with an MS-level or RT filter never counts a spectrum that lacks the optional scan start time, so it under-reports what load() returns. Such spectra are fully decoded and kept in the dummy experiment, and malformed binary data makes the count-only call throw. The only reach is direct C++ use of MzMLFile::loadSize.

**Who reaches it.** MzMLFile::loadSize(filename, scount, ccount) with filters set, public C++ API only. No in-tree caller, no pyOpenMS binding (FeatureLinkerUnlabeled and MapAlignerPoseClustering call FeatureXMLFile::loadSize instead).

**Upstream evidence.** origin/develop src/openms/source/FORMAT/HANDLERS/MzMLHandler.cpp:1398-1428: `if (!skip_spectrum_) { ... if (options_.getFillData()) { tmp.data = std::move(bin_data_); } spectrum_data_.push_back(std::move(tmp)); if (spectrum_data_.size() >= options_.getMaxDataPoolSize()) { populateSpectraWithData_(); } }`, with no load_detail_ gate. In count mode, only the scan-start-time handler counts and skips (2341-2351: `skip_spectrum_ = true; ++scan_count_;`). Decode errors throw ParseError (239-243), and decoded spectra are appended to the dummy map (260-273). Count mode is selected in MzMLFile.cpp:100-103. The ms-mapping.xml:121 rule 'scan_may' makes scan start time optional.

**Proof.** Code reading. The MzMLFile_test loadSize section is unchanged at 4f5c86f (1beb468 only adds skipChromatograms checks), and the log claims no runtime reproduction.

**Fix in OpenMS4 Core.** 1beb468 MzMLHandler.cpp onEndElement (a spectrum without scan start time is counted and skipped in LD_COUNTS_WITHOPTIONS)

<a id="cpp-072"></a>
### CPP-072: DRange::united of two empty ranges returns the universal range

**P1** · wrong-result · valid-edge · proof: static-only  
**Affected:** `src/openms/include/OpenMS/DATASTRUCTURES/DRange.h`, lines 178-195.

**Why it is a bug.** Uniting two empty ranges (for example default-constructed DRange1()/DRange2(), which are empty) returns [-DBL_MAX, DBL_MAX], a non-empty range that encloses everything. That is a wrong result on valid edge-case input. Reach is narrow: develop has no in-library caller, only pyOpenMS and direct C++ API use.

**Who reaches it.** C++ DRange<D>::united and pyOpenMS DRange1.united / DRange2.united (bind_format.cpp:1721, 1773) on empty ranges. git grep at develop finds no other library caller.

**Upstream evidence.** src/openms/include/OpenMS/DATASTRUCTURES/DRange.h:187-192 `united_min[i] = min_[i] < other_min[i] ? min_[i] : other_min[i]; united_max[i] = max_[i] > other_max[i] ? max_[i] : other_max[i]; ... united_range.setMinMax(united_min, united_max);` with no empty check; DIntervalBase.h:142-146 setMinMax calls normalize_(), :346-348 `if (min_[i] > max_[i]) std::swap(min_[i], max_[i]);`, :368-369 `empty = (maxPositive, minNegative)`

**Proof.** No regression test: DRange_test.cpp is unchanged in core-v4.0.0-ci.2..4f5c86f, and its united section (lines 362-376) only unites non-empty ranges. The Rust log reports no C++ run. The OpenMS4 triage notes a clang++ mock of the templates printing min=-1.79769e+308, max=1.79769e+308, but that is not a class test. The arithmetic can be followed directly: min(DBL_MAX,DBL_MAX)=DBL_MAX and max(-DBL_MAX,-DBL_MAX)=-DBL_MAX, which normalize_ then swaps into [-DBL_MAX, DBL_MAX].

**Fix in OpenMS4 Core.** 181dadf src/openms/include/OpenMS/DATASTRUCTURES/DRange.h (`if (this->isEmpty() && other_range.isEmpty()) return DRange<D>::empty;`)

<a id="cpp-080"></a>
### CPP-080: sortByPositionPresorted trusts is_sorted and feeds std::inplace_merge an unsorted range

**P1** · wrong-result · valid-edge · proof: static-only  
**Affected:** src/openms/source/KERNEL/MSSpectrum.cpp:415-438 (per-chunk stable_sort for !is_sorted, then the recursive inplace_merge)

**Why it is a bug.** With isotope_model coarse or fine plus add_losses and add_metainfo (the metainfo creates data arrays, which selects the merge branch), TSG marks the loss chunk as sorted when it is not. For any ion with both H2O- and NH3-loss residues (for example the y2 ion EK of PEPTIDEK), the H2O isotope peak at about M-17.007 comes before the NH3 loss at about M-17.027, so inplace_merge silently returns an unsorted theoretical spectrum that breaks binary-search consumers such as SpectrumAlignment. This is valid but uncommon parameter usage.

**Who reaches it.** TheoreticalSpectrumGenerator::getSpectrum with isotope_model=coarse|fine, add_losses=true, add_metainfo=true (sort_by_position is true by default). Reached from the TOPPView 'Generate theoretical spectrum' dialog, which forces add_metainfo (TheoreticalSpectrumGenerationDialog.cpp:238), offers add_losses (:61) and coarse/fine isotope models (:155-172), and passes the spectrum to TOPPViewBase.cpp:1926-1937 without re-sorting it there. Also reached from pyOpenMS TheoreticalSpectrumGenerator and from any C++ caller that passes a false is_sorted flag.

**Upstream evidence.** src/openms/source/KERNEL/MSSpectrum.cpp:419-422 `if (!chunks[i].is_sorted) { std::stable_sort(select_indices.begin() + chunks[i].start, ...); }`, :433 std::inplace_merge over all chunks, :401 single-chunk early return that trusts the flag. The in-tree producer marks unsorted runs as sorted: TheoreticalSpectrumGenerator.cpp:876-881 and :978-983 run `addLosses_(spectrum, ion, ...)` for every ion, then `chunks.add(true);`, while addLosses_ (:470-532) walks a std::set of loss-formula strings (H2O before the NH3 formula) and emits each loss's isotope cluster

**Proof.** No OpenMS4 class test uses a false is_sorted claim: MSSpectrum_test.cpp:886-917 builds accurate chunks. The develop TSG tests that combine isotope_model with add_losses (TheoreticalSpectrumGenerator_test.cpp:749-804) leave add_metainfo=false, so the stable_sort branch without data arrays hides the problem. The Rust log reports no C++ run. The reachability below comes from reading ResidueDB.cpp:154-221 (D/E/S/T lose H2O, K/N/Q/R lose NH3) and the TSG isotope-with-losses branches.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/KERNEL/MSSpectrum.cpp (checks chunks marked sorted with std::is_sorted and stable-sorts them if not; the single-chunk shortcut also requires isSorted())

<a id="cpp-090"></a>
### CPP-090: The same comparator mutates its arguments, so hits are sorted only where the sort happens to compare

**P1** · wrong-result · valid-edge · proof: static-only  
**Affected:** src/openms/source/KERNEL/BaseFeature.cpp:126-127

**Why it is a bug.** For a feature with exactly one PeptideIdentification the hits are never sorted. QTClusterFinder then takes a non-best hit as the best for the score threshold and the RT key used in ID-based linking. It only goes wrong when that identification's hits are not already in score order (e.g. after a score switch without re-sorting), so this is a wrong result on uncommon input.

**Who reaches it.** FeatureLinkerUnlabeledQT with use_identifications=true (QTClusterFinder.cpp:99-115). Not ProteomicsLFQ/PIPECHO: Impl.cpp:71-74 sorts each identification's hits before calling sortPeptideIdentifications.

**Upstream evidence.** origin/develop src/openms/source/KERNEL/BaseFeature.cpp:126-127: '[](PeptideIdentification& p1, PeptideIdentification& p2) {p1.sort();p2.sort();'. Hits are sorted only inside the comparator, which std::sort never calls for a one-element range. Consumer: QTClusterFinder.cpp:106-115 calls 'feat.sortPeptideIdentifications(); auto& hits = pepIDs[0].getHits();', then uses hits[0] for the min_score_ test and the sequence/charge key.

**Proof.** The 4f5c86f BaseFeature_test.cpp sortPeptideIdentifications section uses three identifications, which std::sort compares, so it passes on the pre-fix code as well. No test covers a single identification with unsorted hits. The Rust log reports source review only.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf src/openms/source/KERNEL/BaseFeature.cpp (separate pep.sort() pass over peptides_, comparator takes const PeptideIdentification&)

<a id="cpp-115"></a>
### CPP-115: ConsensusMap::appendRows pairs column headers by position, not by column index

**P1** · wrong-result · valid-edge · proof: static-only  
**Affected:** src/openms/source/KERNEL/ConsensusMap.cpp:85-92

**Why it is a bug.** When the two maps have different column-index sets, sizes are summed across unrelated columns (a column only rhs has is counted twice) and the wrong columns are renamed to mergedConsensusXMLFile, losing their filenames. FileMerger accepts such inputs without complaint, and ConsensusMapNormalizer picks its reference map by header size. Identical 0..n-1 layouts, the documented use, are unaffected, so this is a wrong result on valid but uncommon input.

**Who reaches it.** FileMerger with -append_method append_rows on consensusXML (FileMerger.cpp:324 `out.appendRows(map)`) and pyOpenMS ConsensusMap.appendRows. The wrong size is read by ConsensusMapNormalizerAlgorithmMedian.cpp:50 and ConsensusMapNormalizerAlgorithmThreshold.cpp:37 and written by ConsensusXMLHandler.cpp:780.

**Upstream evidence.** src/openms/source/KERNEL/ConsensusMap.cpp:82 `column_description_.insert(rhs.column_description_.begin(), rhs.column_description_.end());` then :85-92 `for (; it != column_description_.end() && it2 != rhs.column_description_.end(); ++it, ++it2) { getColumnHeaders()[it->first].filename = "mergedConsensusXMLFile"; getColumnHeaders()[it->first].size = it->second.size + it2->second.size; }`. The headers are paired by ordinal position, not by key.

**Proof.** The ConsensusMap_test.cpp section 'ConsensusMap& appendRows(const ConsensusMap &rhs)' at 4f5c86f appends headers {0:m1} and {1:m2}. It checks only getColumnHeaders().size()==2, which also holds on the pre-fix code. The Rust log is source review only.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/KERNEL/ConsensusMap.cpp (appendRows looks each rhs key up in column_description_)

<a id="cpp-116"></a>
### CPP-116: ConsensusMap::setPrimaryMSRunPath writes by position through a default-inserting map

**P1** · wrong-result · valid-edge · proof: static-only  
**Affected:** src/openms/source/KERNEL/ConsensusMap.cpp:518-536

**Why it is a bug.** For a map keyed {5}, a single path passes the count check, column 0 is invented with the new path, and column 5 keeps its stale filename. Features are then attributed to the wrong run and an empty column appears. The in-tree TOPP callers build contiguous keys, so it is reached only through library or pyOpenMS use on sparsely keyed maps: valid but uncommon input.

**Who reaches it.** ConsensusMap::setPrimaryMSRunPath(StringList) and the (s, MSExperiment) overload, including from pyOpenMS. The TOPP callers FeatureLinkerUnlabeled.cpp:310, FeatureFinderMultiplex.cpp:387 and MassTraceExtractor.cpp:230 pass maps with keys 0..n-1.

**Upstream evidence.** src/openms/source/KERNEL/ConsensusMap.cpp:518 `else if (!column_description_.empty() && s.size() != column_description_.size())` (count check only), then :525-535 `Size i(0); for (auto const & p : s) { ... column_description_[i].filename = p; ++i; }`. std::map::operator[] default-inserts missing keys.

**Proof.** No class test at 4f5c86f calls ConsensusMap::setPrimaryMSRunPath on a map whose column keys are not 0..n-1. The Rust log is source review only.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/KERNEL/ConsensusMap.cpp (existing keys collected in order before writing)

<a id="cpp-144"></a>
### CPP-144: Quoted commas split a MzTab modification-list entry

**P1** · wrong-result · valid-edge · proof: static-only  

**Why it is a bug.** If a position parameter has a quoted name containing a comma (quoting that mzTab 1.0 requires), the cell is split into bogus pieces during load. They become silently wrong modification identifiers, or MzTabModification::fromCellString throws ConversionError. OpenMS's own exporter writes no such names (its only position parameter is 'false localization rate'), so only third-party valid-edge files trigger it: P1.

**Who reaches it.** MzTabFile::load, via TOPP FileInfo on .mzTab and pyOpenMS MzTabFile.load, for the PRT/PEP/PSM modifications columns

**Upstream evidence.** src/openms/source/FORMAT/MzTab.cpp:263 (MzTabModificationList::fromCellString): `if (ss[pos] == ',' && !in_quotes && in_param_bracket)`. A comma inside quotes is never swapped for the BEL placeholder, so the `StringUtils::split(ss, ",", fields)` that follows cuts the entry. The function's own comment (around line 234) shows this case: `8[,,"blabla, [bla]",v]`.

**Proof.** No class test at 4f5c86f covers it: b6dd412 only adds the MzTabFile_test PSM opt_ section. The Rust log is a source review with no C++ execution.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/MzTab.cpp (condition becomes `ss[pos] == ',' && (in_param_bracket || in_quotes)`)

<a id="cpp-146"></a>
### CPP-146: MzTab score-by-run header order differs from row order

**P1** · wrong-result · valid-edge · proof: static-only  

**Why it is a bug.** With at least two score types and two ms_runs, every off-diagonal search_engine_score[i]_ms_run[j] value lands under another score/run header, silently mixing up scores in the written file. Upstream's own exporters only ever fill score index 1 (MzTab.cpp:806, 859, 984, 1162; AccurateMassSearchEngine.cpp:1042), where both orders agree. It therefore needs a multi-score MzTab from third-party input or the API: P1.

**Who reaches it.** MzTabFile::store(filename, MzTab) from C++ or pyOpenMS, e.g. MzTabFile.load of a multi-score third-party mzTab followed by store. Current TOPP exporters do not reach it.

**Upstream evidence.** src/openms/source/FORMAT/MzTabFile.cpp:2034-2042, generateMzTabProteinHeader_: the outer loop is `for (Size i = 0; i != reference_row.search_engine_score_ms_run.begin()->second.size(); ++i)` and the inner loop runs over score types, pushing `search_engine_score[<score>]_ms_run[i + 1]`. The protein row (2119-2125) walks `row.search_engine_score_ms_run` score first, run second. The other sections have the same mismatch, run-major headers against score-major rows: peptide 2231-2236 vs 2334-2337, small molecule 2472-2477 vs 2540-2546, nucleic acid 2588-2593 vs 2656-2662, oligonucleotide 2718-2723 vs 2767-2773.

**Proof.** No class test at 4f5c86f writes a row with several score types and several runs. The Rust log is a source review with no C++ execution.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/MzTabFile.cpp (headers now loop score first; protein header emits the stored run keys)

<a id="cpp-153"></a>
### CPP-153: pepXML drops a uniquely resolved undeclared modification

**P1** · wrong-result · valid-edge · proof: static-only  

**Why it is a bug.** The failing case: a mod_aminoacid_mass is not declared in search_summary (lookupAddFromHeader_ fails at :1700/:1704), has no PSI-MOD id, and the ModificationsDB diff-mass search finds exactly one match. The PSM then silently loses the modification, giving a wrong sequence and mass. Undeclared modifications are valid but uncommon in pepXML, so P1 rather than P0.

**Who reaches it.** PepXMLFile::load via IDFileConverter, CometAdapter, MSFraggerAdapter, pyOpenMS PepXMLFile.load

**Upstream evidence.** origin/develop src/openms/source/FORMAT/PepXMLFile.cpp:1743-1753: `if (!mods.empty()) { if (mods.size() > 1) { warning(LOAD, ... " Using " + mods[0]->getFullId()); current_modifications_.emplace_back(mods[0], modification_position - 1); } } else { // still nothing found, register as unknown ...`. A single match appends nothing and skips the unknown-mod fallback.

**Proof.** No class test at 4f5c86f covers a mod_aminoacid_mass that is missing from the header and matches exactly one DB entry. The core git grep for the warning text and 'uniquely' found nothing. The log entry is source review only.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/PepXMLFile.cpp (emplace_back(mods[0], ...) moved after the size>1 warning)

<a id="cpp-162"></a>
### CPP-162: Percolator enzyme features use unmapped protein-terminal markers

**P1** · wrong-result · valid-common · proof: static-only  

**Why it is a bug.** For trypsin and the other enzymes, every protein N-terminal peptide gets enzN=0, and every protein C-terminal peptide not ending in a cleavage residue gets enzC=0. Percolator's convention marks both as enzymatic. The Peptide column in the same row uses the normalised flank, so the two columns disagree. These features are in PercolatorAdapter's standard set and bias scores for this small class of PSMs. Targets and decoys are affected alike, so FDR control holds, hence P1.

**Who reaches it.** PercolatorAdapter (stampPinFeaturesOnHits at PercolatorAdapter.cpp:983, store at :1162, standard feature set includes enzN/enzC); ProSE (PercolatorInfile::store at ProSE.cpp:615); pyOpenMS PercolatorInfile.store

**Upstream evidence.** origin/develop src/openms/source/FORMAT/PercolatorInfile.cpp:521-522 read aa_before/aa_after from the first PeptideEvidence. :524 `const bool enzN = isEnz_(aa_before, StringUtils::prefix(unmodified_sequence, 1)[0], enz);` and :526 compute enzC from the raw flanks. The normalisation `aa_before = aa_before == '[' ? '-' : aa_before;` / `aa_after = aa_after == ']' ? '-' : aa_after;` comes only afterwards at :534-535. isEnz_ (:621ff) treats a terminus as enzymatic only via `n == '-' || c == '-'`. PeptideIndexing.cpp:127-128 sets N_TERMINAL_AA '[' and C_TERMINAL_AA ']' (PeptideEvidence.cpp:19-20) at protein termini.

**Proof.** No PercolatorInfile_test change in the ci.2..4f5c86f range. The existing stamp/store test (PercolatorInfile_test.cpp:134-135) uses 'K'/'S' flanks, not terminal markers.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf: src/openms/source/FORMAT/PercolatorInfile.cpp, '['/']' are normalised to '-' before isEnz_ for enzN/enzC

<a id="cpp-192"></a>
### CPP-192: Blob hydration assigns objects by SQL row encounter order instead of record identity

**P1** · wrong-result · valid-edge · proof: static-only  

**Why it is a bug.** The k-th distinct ID seen in DATA insertion order is attached to the k-th metadata record. A valid sqMass file whose DATA rows are not in ID order (not written by OpenMS, whose writers insert in ID order) is either rejected with a false 'Native id ... does not match' exception or, when native IDs coincide, gets data on the wrong record.

**Who reaches it.** Reading .sqMass: SqMassFile::load/transform, SpectrumAccessSqMass (OpenSwathWorkflow sqMass input), MzMLSqliteHandler read functions, pyOpenMS

**Upstream evidence.** origin/develop src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp:130-135 `if (!sql_container_map.contains(id_orig)) { Size tmp = sql_container_map.size(); sql_container_map[id_orig] = tmp; }`; data queries without ORDER BY at :515-523 `FROM CHROMATOGRAM INNER JOIN DATA ON CHROMATOGRAM.ID = DATA.CHROMATOGRAM_ID ;`, :541-550, :563-571, :588-597; metadata queries :612-635 and :731-757 end in `select_sql += ";";`

**Proof.** No C++ execution in the Rust log and no OpenMS 4 test. Supporting SQL evidence: EXPLAIN QUERY PLAN on origin/develop SqliteMassFile_1.sqMass (SQLite 3.51.0) gives `SCAN DATA / SEARCH SPECTRUM USING INDEX sqlite_autoindex_SPECTRUM_1` for the data join, while the metadata join scans SPECTRUM. Data rows therefore arrive in DATA insertion order, not ID order.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp (ORDER BY SPECTRUM.ID / CHROMATOGRAM.ID on all metadata and data queries)

<a id="cpp-206"></a>
### CPP-206: MSDataSqlConsumer changes buffered records to the next run ID

**P1** · wrong-result · valid-edge · proof: static-only  

**Why it is a bug.** Records consumed under run A that are still buffered (flush happens every 500 records by default) are stored with run B's RUN_ID after setRunId(B) or addRun(..., B), silently linking them to the wrong run in a multi-run sqMass file. This is a silent wrong result on valid but uncommon API use (P1); it is currently latent, because no in-tree or pyOpenMS caller switches runs with data buffered.

**Who reaches it.** C++ API users writing several runs through one consumer. Not reached by OpenSwathWorkflow: the consumer is created per run at OpenSwathWorkflow.cpp:1635, and addRun (:1663) and setRunId (:1671) run while the buffers are still empty. pyOpenMS does not bind addRun or setRunId.

**Upstream evidence.** MSDataSqlConsumer.cpp:45-53 `void MSDataSqlConsumer::addRun(...) { handler_->setRunId(run_id); ... }` and :55-58 `void MSDataSqlConsumer::setRunId(const UInt64 run_id) { handler_->setRunId(run_id); }`, neither calling flush(). The buffers are written later by flush() (:60-75), and the handler binds its current id at write time: MzMLSqliteHandler.cpp:1167-1169 `INSERT INTO SPECTRUM(ID, RUN_ID, ...) VALUES (" << spec_id_ << "," << run_id_` and :1405 `INSERT INTO CHROMATOGRAM (ID, RUN_ID, NATIVE_ID) VALUES (" << chrom_id_ << "," << run_id_`.

**Proof.** No OpenMS 4 test consumes records and then switches the run (no setRunId/addRun test on MSDataSqlConsumer at 4f5c86f), and the Rust log reports no execution.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf: MSDataSqlConsumer.cpp addRun() and setRunId() call flush() before changing the id

<a id="cpp-132"></a>
### CPP-132: ImzMLWriter::store cannot write a metadata-only continuous dataset

**P1** · crash-valid-input · valid-edge · proof: regression-test  
**Affected:** src/openms/source/FORMAT/HANDLERS/ImzMLWriter.cpp:485-491 (applyStoreOptions_ clear(false)), :692-754 (spectraShareMz_ / isContinuousMode_), :1410-1415 (store)

**Why it is a bug.** A metadata-only store of any continuous dataset, including one just loaded from a continuous imzML, always throws InvalidParameter with a misleading 'must share m/z axis' message. The same store of a processed dataset succeeds. Valid but uncommon input, so P1 under the rubric, though no TOPP tool reaches it.

**Who reaches it.** ImzMLFile::store(MSExperiment) and store(MSImagingExperiment) with PeakFileOptions::setMetadataOnly(true), from C++ or pyOpenMS. FileHandler refuses imzML store and no TOPP tool uses it.

**Upstream evidence.** src/openms/source/FORMAT/HANDLERS/ImzMLWriter.cpp:485-491 `if (options.getMetadataOnly()) { for (auto& spectrum : exp.getSpectra()) { spectrum.clear(false); } }`. spectraShareMz_ :707-710 `if (ref >= exp.size() || exp[ref].empty()) { return false; }`. isContinuousMode_ :740-746 `if (meta.imaging_mode == "continuous") { if (!spectraShareMz_(exp)) { throw Exception::InvalidParameter(... "continuous imzML requires all spectra to share the same m/z axis and array length"); }`. store() calls applyStoreOptions_ at :1402 and then isContinuousMode_ at :1414.

**Proof.** src/tests/class_tests/openms/source/ImzMLFile_test.cpp, section `void store writes a metadata-only continuous dataset` (added in 181dadf). It calls f.store() with setMetadataOnly(true) on an experiment with imzml:imaging_mode=continuous, outside TEST_EXCEPTION. On the pre-fix code that call throws InvalidParameter and the section fails.

**Fix in OpenMS4 Core.** 181dadf: ImzMLWriter.cpp isContinuousMode_ skips the shared-axis check when every spectrum is empty (no_peaks); test in ImzMLFile_test.cpp

<a id="cpp-010"></a>
### CPP-010: Integer mass decomposition can loop without progress

**P1** · crash-valid-input · valid-edge · proof: executed-probe  
**Affected:** [`src/openms/include/OpenMS/CHEMISTRY/MASSDECOMPOSITION/IMS/IntegerMassDecomposer.h`], witness creation at 355–367 and consumption at 420–430.

**Why it is a bug.** For a valid sorted alphabet ([10,16,25]) and a decomposable mass (73), getDecomposition never terminates, because a zero-count witness subtracts nothing. The only reach is direct C++ use: RealMassDecomposer uses getAllDecompositions/getNumberOfDecompositions, and pyOpenMS does not bind the class. The root cause is the counter not advancing for r>=1. The OpenMS 4 fix only breaks the loop and returns an incomplete decomposition.

**Who reaches it.** IntegerMassDecomposer<>::getDecomposition, a C++ header template. No in-tree caller, no pyOpenMS binding, no TOPP tool.

**Upstream evidence.** origin/develop src/openms/include/OpenMS/CHEMISTRY/MASSDECOMPOSITION/IMS/IntegerMassDecomposer.h:358-371. In the second loop `++counters[cur];` (360) runs once per block, outside `for (size_type r = 1; r < d; ++r)` (361), which writes `_witnessVector[cur] = std::make_pair(i, counters[cur]);` (367) and resets `counters[cur] = 0;` (371). getDecomposition, lines 420-431: `while (m != 0) { ... decomposition_value_type j = witness_vector_.at(r).second; ... m -= j * alphabet_.getWeight(i); r = m % alphabet_.getWeight(0); }` has no guard for j == 0.

**Proof.** The Rust log's source-derived Python translation (OpenMS4-R/tools/probes/ims_witness_source_oracle.py, results in tests/data/ims_witness_source_oracle.json) gives, for weights [10,16,25] and mass 73: last row [0,41,32,73,64,25,16,57,48,89], exist(73)=true, witness[3]=(2,0). I re-translated the develop source independently and got the same row and witness; the getDecomposition loop leaves m=73 unchanged. This is not C++ execution. IntegerMassDecomposer_test.cpp at 4f5c86f still has only TODO sections.

**Fix in OpenMS4 Core.** 1beb468 IntegerMassDecomposer.h (break when witness count j == 0)

<a id="cpp-143"></a>
### CPP-143: Negative CHEMMOD identifiers fail mzTab modification-cell parsing

**P1** · crash-valid-input · valid-edge · proof: static-only  

**Why it is a bug.** `8-CHEMMOD:-18.010565` splits into three fields and throws. The position-less `CHEMMOD:-18.010565` throws in toInt32("CHEMMOD:"). So an mzTab that OpenMS itself exports for a non-UNIMOD mass-loss modification cannot be read back: MzTabFile::load raises ConversionError on a valid file.

**Who reaches it.** MzTabFile::load for protein, peptide and PSM modification cells (MzTabFile.cpp:976, 1154, 1317). Reached from TOPP FileInfo (FileInfo.cpp:1479) and pyOpenMS MzTabFile.load (bind_format.cpp:1273). Files that trigger it come from MzTabExporter, ProteinQuantifier and ProteomicsLFQ output for non-UNIMOD negative-mass modifications.

**Upstream evidence.** origin/develop:src/openms/source/FORMAT/MzTab.cpp. :131 `if (!StringUtils::hasSubstring(lower, "-"))`, else :140 `StringUtils::split(ss, "-", fields);` and :142-144 `if (fields.size() != 2) { throw Exception::ConversionError(... "Can't convert to MzTabModification from '"`. The position is parsed at :157 with `StringUtils::toInt32(position_fields[i])`, which is strict (StringUtils.cpp:240-270). OpenMS's own exporter writes the identifier at :1528 as `MzTabString("CHEMMOD:" + StringUtils::toStr(r.getDiffMonoMass()))` and uses it for PSM, peptide and protein modifications (:1559, :1729, :2558, :2586, :2601).

**Proof.** No test in OpenMS4 4f5c86f contains a negative CHEMMOD. The review ledger used a Python simulation of the scan, and the Rust log states no C++ execution. The upstream MzTabFile_test Cytidine cell `CHEMMOD:M-C5H8O4` is not a counter-example, because MzTabSmallMoleculeSectionRow::modifications is an MzTabString (MzTab.h:329) and never reaches this parser.

**Fix in OpenMS4 Core.** OpenMS4 181dadf: src/openms/source/FORMAT/MzTab.cpp:131-185 (separator is the first '-' outside brackets and quotes within a position list)

<a id="cpp-161"></a>
### CPP-161: Percolator loader requires FileName through an unchecked map lookup

**P1** · crash-valid-input · valid-common · proof: static-only  

**Why it is a bug.** FileName is not part of the standard PIN layout (getStandardFeatureSet has no FileName column, and the load() doc calls it optional). So any PIN without it throws std::out_of_range on the first data row, instead of loading or raising a ParseError. That is an exception on valid input. Current tool reach is nil: SageAdapter always reads Sage PINs, which include FileName.

**Who reaches it.** C++ library PercolatorInfile::load only. SageAdapter (SageAdapter.cpp:689) is unaffected because Sage writes FileName. pyOpenMS binds PercolatorInfile.store but not load (bind_format.cpp:1814).

**Upstream evidence.** origin/develop src/openms/source/FORMAT/PercolatorInfile.cpp:222-223 `std::string raw_file_name("UNKNOWN"); unordered_map<std::string, size_t> map_filename_to_idx;`. The map is filled only inside `if (file_name_column_index >= 0)` (:245-252), yet :273 unconditionally calls `pids.back().setMetaValue(Constants::UserParam::ID_MERGE_INDEX, map_filename_to_idx.at(raw_file_name));`.

**Proof.** No PercolatorInfile_test change between core-v4.0.0-ci.2 and 4f5c86f. The only load test (PercolatorInfile_test.cpp:51-66) reads sage.pin, which has a FileName column. The Rust log entry says it was not executed.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf: src/openms/source/FORMAT/PercolatorInfile.cpp, ID_MERGE_INDEX is set only when file_name_column_index >= 0

<a id="cpp-163"></a>
### CPP-163: Percolator writer and loader disagree on trailing protein-list width

**P1** · crash-valid-input · valid-common · proof: static-only  

**Why it is a bug.** load() throws ParseError on OpenMS's own store() output, and on other spec-layout PINs, as soon as one PSM maps to more than one protein. Shared peptides are routine, so valid files cannot be read. Current tool reach is nil: SageAdapter reads Sage PINs, which join accessions with ';' in one field (sage.pin).

**Who reaches it.** C++ library PercolatorInfile::load on non-Sage or OpenMS-written PINs. SageAdapter is unaffected (';'-joined). pyOpenMS does not bind load.

**Upstream evidence.** origin/develop src/openms/source/FORMAT/PercolatorInfile.cpp:549 (writer) `stamp_meta_value("Proteins", ListUtils::concatenate(proteins, "\t"));`, joined into the row with tabs by preparePin_. Reader :239 `if (row.size() != pin_header.size())` throws Exception::ParseError, and :288/:313 take the single field `row[to_idx.at("Proteins")]` and `StringUtils::split(sProteins, ';', accessions);`.

**Proof.** No store->load round-trip test with a multi-protein PSM at 4f5c86f. Percolator_subprocess_parity_test.cpp:404 only notes that Proteins 'embeds tabs and inflates the split count'. The Rust log entry says it was not executed.

**Fix in OpenMS4 Core.** OpenMS4 core 181dadf: src/openms/source/FORMAT/PercolatorInfile.cpp, the proteins_trailer flag accepts a variable-width trailing Proteins column and still splits each field on ';'

<a id="cpp-190"></a>
### CPP-190: Default handler writing reads an uninitialized SQL batch size

**P1** · crash-valid-input · valid-edge · proof: static-only  

**Why it is a bug.** Writing through a handler that never had setConfig called reads an indeterminate int, which is undefined behaviour. In practice the batch size is arbitrary. A small or negative value just flushes per spectrum. A large value never flushes, so a single INSERT for more than about 16k spectra exceeds SQLite's bound-variable limit and throws on valid data. SqMassFile and MSDataSqlConsumer always call setConfig, so only direct API users are hit.

**Who reaches it.** Direct MzMLSqliteHandler use: pyOpenMS MzMLSqliteHandler(filename, run_id).writeExperiment/writeSpectra/writeChromatograms (bind_format.cpp:2919-2924) and C++ callers. SqMassFile.cpp:25/32/40 and MSDataSqlConsumer.cpp:25 call setConfig and are unaffected.

**Upstream evidence.** origin/develop src/openms/include/OpenMS/FORMAT/HANDLERS/MzMLSqliteHandler.h:238 `int sql_batch_size_;` (no initializer; setConfig at h:121-127 is the only assignment); src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp:269-276 the init list ends at `write_full_meta_(true)`; read at cpp:1263 `if (sql_it > sql_batch_size_)` and cpp:1474. The upstream MzMLSqliteHandler_test.cpp:448-455 and :551-558 write without setConfig.

**Proof.** Only a code-reading argument. The upstream test sections that write without setConfig pass unless run under MSan or valgrind, so they are not a regression test. No OpenMS 4 test was added: MzMLSqliteHandler_test.cpp was not changed in ci.2..4f5c86f.

**Fix in OpenMS4 Core.** 181dadf src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp (constructor sql_batch_size_(500))

<a id="cpp-198"></a>
### CPP-198: Recreating tables on a used handler retains counters from the deleted database

**P1** · crash-valid-input · valid-edge · proof: static-only  

**Why it is a bug.** After createTables on a handler that has already written n spectra, the new file's ids start at n while getNrSpectra still counts from zero. Index-based reads (readSpectra with 0..count-1, SqMassFile::transform, SpectrumAccessSqMass::getSpectrumById) then throw IllegalArgument on a file produced by a documented call sequence. The failure is loud and needs a reused handler, so P1 (exception on valid use), not P0.

**Who reaches it.** C++ API and pyOpenMS MzMLSqliteHandler (bind_format.cpp:2922 createTables, plus writeExperiment/writeSpectra) when one handler is reused to rewrite its file. No TOPP tool does this: SqMassFile::store and MSDataSqlConsumer construct a fresh handler

**Upstream evidence.** origin/develop src/openms/source/FORMAT/HANDLERS/MzMLSqliteHandler.cpp:939-1023 createTables removes the file (`std::filesystem::remove(OpenMS::to_path(filename_), ec);` :943) and recreates tables and indexes but never assigns spec_id_/chrom_id_. Only the constructor sets them (`spec_id_(0), chrom_id_(0),` :271-272). The header comment in MzMLSqliteHandler.h says the ids are global to a database file and 'initialized to zero when opening a new file'.

**Proof.** The Rust log reports a source review with no C++ run. The existing MzMLSqliteHandler_test writeExperiment section (upstream :453-462) recreates tables through the same handler but checks only getNrSpectra. That test file is unchanged in 4f5c86f.

**Fix in OpenMS4 Core.** core 181dadf: createTables resets spec_id_ and chrom_id_ to 0 after createIndices_ succeeds

<a id="cpp-200"></a>
### CPP-200: SqMassFile transform issues an extra empty selected-read batch

**P1** · crash-valid-input · valid-edge · proof: static-only  

**Why it is a bug.** For a valid file with exactly 500, 1000, ... spectra or chromatograms, the final empty batch reads all records in release builds and throws IllegalArgument, aborting the conversion. Debug builds already throw Precondition whenever either count is zero. An uncaught exception on valid but uncommon input is P1.

**Who reaches it.** FileConverter sqMass to CHROMPARQUET (FileConverter.cpp:1033); SqMassFile::convertToXICParquet; OpenSwathMzMLFileCacher sqMass to sqMass with -process_lowmemory (SqMassFile::transform)

**Upstream evidence.** origin/develop src/openms/source/FORMAT/SqMassFile.cpp:52 `for (size_t batch_idx = 0; batch_idx <= (sql_mass.getNrSpectra() / batch_size); batch_idx++)`, and :74 does the same for chromatograms, so the last batch has idx_start == idx_end and an empty index list. In MzMLSqliteHandler.cpp, `OPENMS_PRECONDITION(!indices.empty(), ...)` (:392, :417) is compiled out in release builds (Macros.h:91). prepareSpectra_ applies its WHERE clause only `if (!indices.empty())` (:753), so an empty list selects every spectrum, and `if (indices.size() != exp.size())` (:398) then throws IllegalArgument.

**Proof.** The Rust log reports a source review with no C++ run. The 4f5c86f SqMassFile_test section [EXTRA_TRANSFORM_META] uses MzMLSqliteHandler_1.mzML, whose counts are not multiples of 500, so it does not reach the empty batch.

**Fix in OpenMS4 Core.** core 181dadf: SqMassFile::transform loops `for (idx_start = 0; idx_start < count; idx_start += batch_size)` with counts cached once
