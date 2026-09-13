# C++ findings from the Rust port — how each was addressed

*Part of the [OpenMS 4 package split](../README.md). [State of the project](project-state.md) · [Package architecture](package-architecture.svg) · [Build instructions](build-split-packages.md)*

The Rust port keeps a log of candidate defects in the C++ SDK,
`OpenMS4-R/OpenMS_CPP_ISSUES.md`. It now holds 229 entries, CPP-001 to CPP-229, written
against Core `82ce5b3` and later `bc9cc12`. This page records the outcome of every entry.

**Where they are.** Every finding is in the `core` package (the scientific library, readers
and writers, OpenSwathAlgo and the test framework). One follow-up reached other packages: the
OpenSwathMzMLFileCacher tool in `openswath` passed its sqMass writer arguments one place off, and
`test-data` gains the tests that catch it.

**How they were checked.** No entry was taken on trust: the log calls them candidates, and some
were wrong, intentional or already fixed. Each was read against the current source first.

1. Thirty-two entries were verified and fixed by hand: CPP-001 to CPP-028 except the four ProForma entries, CPP-048, and CPP-181 to CPP-187.
2. The remaining 185 went to 31 subsystem passes with exclusive file ownership, each followed by
   two adversarial reviews (does the fix hold; what does it risk). The reviews overturned or
   completed several fixes; those corrections are the outcomes recorded below, not the first verdicts.
3. The follow-up session in `codex/cpp-review-completion` added three independent command-line
   reviews (Claude, Kimi, Vibe), traced their claims against saved native libraries and fixed what
   held up; see the [review synthesis](port-resumption-2026-09-13/review-synthesis.md).
4. CPP-219 to CPP-229 were added to the log after that and fixed on the same branch.

## Outcome

| State | Findings |
| --- | ---: |
| fixed | 200 |
| documented | 20 |
| not a defect | 1 |
| not reachable | 1 |
| open | 6 |
| no finding | 1 |

*Documented* means the behaviour is intended or cannot change without breaking callers, and the
header now states it. *Not reachable* means the described input cannot occur with what OpenMS ships.
*Open* entries are real and listed with the reason they are not fixed yet.

## Corrections made after review

Several first verdicts were wrong or incomplete, and the deferred cross-file edits have since landed; the table below records the final outcome, not the first verdict. The corrections that prevented a shipped regression:

- **CPP-117** changed what `getPrimaryMSRunPath` returns, which search adapters, NucleicAcidSearchEngine and pyOpenMS write straight into their output, and turned every POSIX URI into a relative path.
- **CPP-096** (fixed as reported) made `Feature::getConvexHull()` read-only, which breaks TOPP's FeatureFinderCentroided; TOPP's `codex/core-compatibility` branch removes that call, whose effect was discarded anyway.
- **CPP-046** relaxed date validation for every dateTime term the vocabularies ship.
- **CPP-154** applied protein-terminal fixed modifications to every peptide, a silent mass shift for Comet, IDFileConverter and MSFraggerAdapter.
- **CPP-147** activated an out-of-bounds read in the mzTab reader; **CPP-066** still cast `inf` to an index; **CPP-118** threw for seeded generators; **CPP-054** made OpenMS's own indexed mzML invalid.

## Findings outside the log

Tracing the entries surfaced these; each is fixed unless marked open.

| Finding | Package | Outcome |
| --- | --- | --- |
| `.oms` consensus ratios were stored under the id of the feature's last handle and loaded into a local copy after it had been appended, so every ratio was lost | core | fixed, with a round-trip test |
| `SimpleTSGXLMS` divides charge-two suffix losses by the charge twice (the sibling of CPP-042) | core | **open**: fixed in core-v4.0.0-ci.3, reverted for ci.4 with CPP-042 and CPP-043 because it changed OpenPepXL identification output |
| `SqMassFile::transform` rebuilt chromatograms from the SQL tables alone, so SRM chromatograms lost their type in the low-memory sqMass-to-sqMass conversion, while `load()` kept it | core | fixed for ci.4; found by the new OpenSwath cacher test, covered by `SqMassFile_test` |
| `FeatureFinderAlgorithm.h` and `FeatureFinderDefs.h` were installed but included by nothing, and the second duplicates a struct `FeatureFinderAlgorithmPicked.h` defines | core | deleted |
| OpenSwathMzMLFileCacher's low-memory sqMass conversions shifted the writer's arguments and wrote mzML under a `.sqMass` name | openswath, test-data | fixed, with two round-trip tests |
| `IDFilter`'s in-silico digestion passes `end - start` as the peptide length, but evidence ends are inclusive, so every length is one short | core | **open**: five TOPP references were produced with the current length and need analysis before it changes |
| A full-metadata sqMass file whose native ids lack `=` cannot be read back: the mzML snapshot renames them to `spectrum=<index>` while the SQL tables keep the original | core | **open** |
| A later spectrum without processing history is written with the first spectrum's history in streaming mzML output | core | **open**, documented fallback |
| The mzXML and mzData readers reserve memory from a file's declared `peaksCount`, `scanCount` or `count`; `peaksCount="-1"` wraps and requests about 34 GB, so a corrupt file fails as OutOfMemory instead of ParseError, or passes on a host large enough to grant it | core | fixed; `MzXMLFile_test` covers it |

## Validation

The branch with every change above passes all 702 Core class tests on dax (GCC 14.4, the Core CI
dependency environment), and the CI driver's own reproduction at `5f7d33f` also passed installed and
relocated SDK acceptance there. The follow-up session's receipts cover its own revisions: 702 tests on
each of five platforms at `df774c1`, and 702 Release plus targeted Debug tests, installed and relocated
SDK acceptance at `63e332c`. The five-platform run for `63e332c` failed on Linux x64, Linux arm64 and
Windows, all on one assertion: `MzXMLFile_test` expected a ParseError for `peaksCount="-1"` and got
OutOfMemory, the allocation defect in the last row above. dax can satisfy that reservation, which is
why it passed there; under a 12 GB `ulimit -v` it fails the same way, and it passes with the fix in
`c77ff14`. The five-platform run for `c77ff14` passed all seven jobs, the two Homebrew formula builds
included, and that revision was released as `core-v4.0.0-ci.3`. That qualification was incomplete:
rebuilding the package graph on dax against the ci.3 SDK, the installed console regression suite
(2041 tests passing at ci.2) failed 107 of 2047 tests, because several fixes here change what the
console tools write and the Core class tests do not compare those outputs. 89 failures come from
CPP-026, 14 from the `dataProcessingList` count correction in `63e332c`, one from the `indexList`
count correction in `181dadf`, three from the cross-link generator fixes (CPP-042, its SimpleTSGXLMS
sibling, CPP-043), and one from a new OpenSwath cacher test that found the sqMass chromatogram-type
loss listed above. For ci.4, CPP-026 and the cross-link fixes are reverted and recorded as open, the
two count corrections stay with their references regenerated after checking each diff, and the
sqMass loss is fixed (`23944b6`). ci.4 is not qualified yet: its class suite passes on dax, but its
CI run, SDK, graph rebuild and regression suite are still to come.

## Every finding

| ID | Finding | Outcome | How it was addressed |
| --- | --- | --- | --- |
| CPP-001 | DateTime ignores failed calendar conversion | **fixed** | timegm/gmtime replaced by days-from-civil integer arithmetic, so dates before the libc epoch survive addSecs |
| CPP-002 | Fractional seconds overflow signed int during normalization | **fixed** | one parseMillis_ helper reads the fractional digits from the text; |
| CPP-003 | Configuration repair is computed and discarded | **fixed** | File::getSystemParameters returns the repaired parameters instead of the unrepaired ones |
| CPP-004 | trimLeft does nothing when every peak is below cutoff | **fixed** | IsotopeDistribution::trimLeft erases everything when no peak reaches the cutoff |
| CPP-005 | Truncated fragment distribution is indexed at full input length | **fixed** | calcFragmentIsotopeDist_ accumulates over r_max, not the full input: it wrote past the end of the result |
| CPP-006 | Interpolation overload resizes and then appends coordinates | **fixed** | the non-preprocessing interpolation constructor reserves instead of resizing, so no zero anchors are prepended |
| CPP-007 | EMG tail expression overflows before its asymptotic branch | **fixed** | the EMG tail uses a scaled complementary error function instead of exp(z*z) * erfc(z), which was inf * 0 = NaN |
| CPP-008 | ProForma modified ranges omit their residue annotations | **fixed** | resolveModifications now resolves each range element's modifications with that element's residue (2195-2197). |
| CPP-009 | Ambiguous mass checks ignore modifications on candidates | **fixed** | The mass-issue collector (now collectMassCalculationIssues_, 2618-2643) runs checkModificationForMass_ on every candidate's modifications. |
| CPP-010 | Integer mass decomposition can loop without progress | **fixed** | a witness count of zero now breaks the decomposition loop instead of repeating forever |
| CPP-011 | Mass trace detection reuses stale metadata-array state | **fixed** | getIMIndices_ resets its flags and indices, so a second run cannot read a float array that is not there |
| CPP-012 | Smoothed area accumulation uses raw peak intensities | **fixed** | computeSmoothedPeakArea uses the smoothed intensities throughout, and returns 0 for an empty trace |
| CPP-013 | Feature finding does not guard zero normalization intensity | **fixed** | FeatureFindingMetabo scores 0 instead of NaN when the summed intensity is zero |
| CPP-014 | Addition can reduce the cached maximum residue count | **fixed** | MassDecomposition::operator+ compares against the result's running maximum |
| CPP-015 | Cross-link mass depends on endpoint traversal order | **fixed** | addModMass (1945-1965) lets only an endpoint that defines chemistry claim a label (resolved_mod != nullptr or carriesChemistry_). |
| CPP-016 | Count-only mzML loading can still decode peak arrays | **fixed** | a spectrum without a scan start time is counted, not decoded, in count-only mode |
| CPP-017 | The chromatogram skip option activates a global callback guard | **fixed** | skip_chromatograms no longer suppresses the file description and every spectrum; |
| CPP-018 | Centroid inspection leaves reader options changed after failure | **fixed** | getCentroidInfo restores FillData when transform throws |
| CPP-019 | Declared processing count includes records that are not written | **fixed** | dataProcessingList count only counts arrays that get a record of their own |
| CPP-020 | Formula interning can separate mass validation from calculation | **fixed** | The body of getMassCalculationIssues moved into collectMassCalculationIssues_, which works on an already resolved peptidoform (2590). |
| CPP-021 | CV XML formatting ignores the value's actual unit | **fixed** | the unit written is the value's own unit; |
| CPP-022 | Legacy binary xref parsing removes the wrong prefix length | **fixed** | the binary-data-type xref trims the prefix that actually matched |
| CPP-023 | Vocabulary printing splits output between two streams | **fixed** | the vocabulary stream operator writes is_a lines to its own stream |
| CPP-024 | CV parameter rendering does not escape every XML attribute | **fixed** | accession, cvRef and unit accession are XML-escaped |
| CPP-025 | A later processing method can omit its required action term | **fixed** | the fallback data-transformation term is decided per processing method |
| CPP-026 | Processing step order is always written as zero | **open** | Real: the mzML schema orders consecutive steps by it. Fixed in core-v4.0.0-ci.3 and reverted for ci.4, because 210 of the 267 TOPP reference mzML files record 0 for every step and the change failed 89 installed regression tests; it needs a coordinated reference update |
| CPP-027 | mzML writing discards processing completion seconds | **documented** | mzML records the completion time to the minute; |
| CPP-028 | Recognized software metadata can throw during mzML writing | **fixed** | software metadata is validated against the mapping's own path, and locateTerm reports an unmapped path instead of throwing std::out_of_range |
| CPP-029 | Annotation-only brackets pass conversion checks but fail conversion | **fixed** | The attachment throw now uses the same predicate: policy == FAIL_ON_LOSS && carriesChemistry_(mod) (2399). |
| CPP-030 | Strict AASequence conversion silently drops terminal crosslinks | **fixed** | Both terminal loops now push a CROSS_LINK issue when crossLinkLabel_(mod) is non-null (2322-2323, 2346-2347). |
| CPP-031 | An empty ambiguous region shifts the conversion attachment index | **fixed** | The cursor now advances only for a non-empty region (2424-2427), mirroring the emission rule. |
| CPP-032 | CV mapping namespace stripping mishandles path segments | **fixed** | CVMappingFile.cpp:96 now keeps any segment with fewer than 2 ':'-parts unchanged. |
| CPP-033 | Failed CV mapping loads contaminate later loads | **fixed** | load() now clears cv_references_, rules_ and actual_rule_ before parse_ (CVMappingFile.cpp:36-42), with a comment explaining the empty reset(). |
| CPP-034 | CV reference bulk assignment can invalidate its input iterator | **fixed** | The loop now runs over a local copy of the input (CVMappings.cpp:73), with a comment about the aliasing. |
| CPP-035 | Invalid CV mapping enums silently select different rules | **fixed** | The two empty branches now call fatalError(LOAD, ...), naming the attribute, the bad value and the rule id (CVMappingFile.cpp:147 and :177). |
| CPP-036 | XML compression sniffing reads uninitialized short-file bytes | **fixed** | The buffer is now zero-initialized, and bz takes only file.gcount() bytes (XMLFile.cpp:145-151). |
| CPP-037 | ProForma combination discards a formula's charge contribution | **fixed** | combineOnOneResidue_ takes the formula route only when the summed formula agrees and getCharge() == 0 (1736-1746). |
| CPP-038 | ProForma crosslink spectra count resolved linker mass twice | **fixed** | generateSpectrum now resolves copies of both chains, locates each endpoint with findCrossLink (which returns a CrossLinkEndpoint_ struct), and erases the selected linker bracket from each copy before BEST_EFFORT conversion (2949-2966). |
| CPP-039 | SemanticValidator compares descendant units with the measured term | **fixed** | The lambda now compares with parsed_term.unit_accession (SemanticValidator.cpp:405), with a comment. |
| CPP-040 | Failed semantic validation contaminates later document paths | **fixed** | validate() now also clears open_tags_ and fulfilled_ before parsing (SemanticValidator.cpp:155-160), with a comment explaining why. |
| CPP-041 | The mzML header writer does not escape several string attributes | **fixed** | All of these sites now go through writeXMLAttribute_: software version (MzMLHandler.cpp:3800), SHA-1 and MD5 checksum text (:3832, :3836), fraction identifier (:5268), externalSpectrumID (:5481) and the non-standard array names in the spectrum and chromatogra… |
| CPP-042 | XLMS linear suffix losses divide the mass by charge twice | **open** | Real. Fixed in core-v4.0.0-ci.3 (with the same double division in the sibling SimpleTSGXLMS generator, which OpenPepXL uses for its main score) and reverted for ci.4: it changed OpenPepXL scores and fragment annotations, failing three installed regression tests. It needs a reviewed reference update |
| CPP-043 | XLMS precursor isotope companions omit charge normalization | **open** | Real. Fixed in core-v4.0.0-ci.3 and reverted for ci.4 together with CPP-042, so that ci.4 restores the ci.2 cross-link spectra exactly; reverting it with the suffix losses was a scoping decision, not a finding that the fix was wrong |
| CPP-044 | Unmapped CV lookup depends on earlier validation calls | **fixed** | Both callbacks now look rules up with rules_.find() and fall back to a local empty vector, so they no longer insert (SemanticValidator.cpp:209-214 and 344-347), with a comment. |
| CPP-045 | PeptideEvidence misclassifies valid and invalid position limits | **fixed** | hasValidLimits now returns start >= 0 && end >= 0 && start <= end (PeptideEvidence.cpp:86), with a comment explaining the inclusive contract and why end == N_TERMINAL_POSITION is a valid endpoint. |
| CPP-046 | Semantic date validation applies date-time syntax to xsd:date | **not reachable** | Every shipped term the loader classifies as XSD_DATE is an xsd:dateTime (e.g. MS:1000747 completion time), so a date without a time is correctly invalid. The first fix relaxed validation for those terms and was reverted; the branch now documents why. |
| CPP-047 | ProForma XLMS link positions ignore preceding flattened sections | **fixed** | findCrossLink now counts positions exactly as toAASequence emits residues: +1 per SequenceElement, +1 per non-empty AmbiguousRegion, +elements.size() per ModifiedRange (2060-2108). |
| CPP-048 | Zero centroid-inspection limit depends on the first spectrum type | **fixed** | getCentroidInfo(.., 0) inspects nothing instead of wrapping its unsigned counter |
| CPP-049 | Indexed mzML output writes a constant placeholder checksum | **open** | The writer still emits a literal 0 checksum. A real SHA-1 over the stream changes 194 reference documents whose FuzzyDiff whitelist does not cover fileChecksum, so it needs its own output-changing change. |
| CPP-050 | Empty indexed mzML declares zero indices but emits a dummy index | **fixed** | The declared count is now the number of index elements actually written, including the dummy: '(indexlists == 0 ? 1 : indexlists)' at MzMLHandlerHelper.cpp:98, with a comment. |
| CPP-051 | mzML semantic validation reuses parameter groups from earlier documents | **fixed** | In MzMLValidator::onStartElement (MzMLValidator.cpp:41-52) I added an else branch. |
| CPP-052 | mzML schema selection depends on the first four physical lines | **fixed** | In MzMLFile.cpp I replaced the line sniffing. |
| CPP-053 | Chromatogram array promotion mismatches values and their physical role | **fixed** | populateChromatogramsWithData_ (MzMLHandler.cpp:648-668) promotes a physical array only when no canonical 'intensity array' is present, and then only the first one in document order. |
| CPP-054 | Shipped indexed mzML schema leaves index references unchecked | **open** | The corrected identity constraints reject the dummy index entry the writer must emit for an empty file (CPP-050): three files MzMLFile_test writes stopped validating, so the schema change was reverted. Schema and writer have to change together. |
| CPP-055 | Base64 SIMD decoding does not validate its alphabet | **fixed** | New private helper Base64::checkNumericInput_ (declared at Base64.h:157, defined at Base64.cpp:213). |
| CPP-056 | Synthetic mzML scans omit spectrum ion mobility | **fixed** | The first-scan RT and mobility output (including the FAIMS signed-value rule and the rule that an unset drift time is not written) is now a single local lambda, write_first_scan_rt_and_mobility (MzMLHandler.cpp:5438). |
| CPP-057 | Spectrum equality ignores ion-mobility format and peak type | **fixed** | SpectrumSettings.cpp operator== now also compares im_type_ and im_peak_type_. |
| CPP-058 | Nonnumeric DataValue casts read an inactive union member | **fixed** | Each of the three operators gets `else if (value_type_ != DOUBLE_VALUE) throw Exception::ConversionError(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION, "Could not convert non-numeric DataValue of type '" + NamesOfDataType[value_type_] + "' and value '" + this->t… |
| CPP-059 | Short experimental-design rows are read past the end of the row vector | **fixed** | ExperimentalDesignFile.cpp, one-table parser: n_col is now the header width as written, taken at :200 before the implicit Label/Sample columns are appended. |
| CPP-060 | Negative design indices wrap to large unsigned values | **fixed** | ExperimentalDesignFile.cpp: the one-table parser now rejects label/fraction/fraction_group < 0 with parseErrorIf_ right after they are read (:243-245), before the 'Label > 1' check and before assignment. |
| CPP-061 | SpectrumHelper::makePeakPositionUnique discards the whole spectrum record | **fixed** | p_new now starts as a copy of p followed by `p_new.clear(false)`. |
| CPP-062 | SpectrumRangeManager::byMSLevel(0) can only throw | **fixed** | Removed the default argument (`byMSLevel(UInt ms_level)`). |
| CPP-063 | MSExperiment::updateRanges registers no per-level entry for MS level 0 | **documented** | No behaviour change: a level-0 entry would break SpectrumRangeManager's convention that level 0 means the global ranges, and that file is not mine. |
| CPP-064 | RangeBase accepts NaN and infinity and breaks its own emptiness invariant | **fixed** | Non-finite values are rejected by both value constructors and by extendLeftRight, minSpanIfSingular, scaleBy and shift, not only by setMin/setMax as first fixed; no in-tree code passes an infinite bound. |
| CPP-065 | RangeUtils energy and isolation predicates contradict their own notes for MS1 spectra | **documented** | Changed only the documentation. |
| CPP-066 | BinnedSpectrum default construction leaves a null bin matrix | **fixed** | getBinIntensity returns 0 without a bin layout or beyond the last bin; the first fix still converted floor(mz / 0) to an index, which aborted a Debug build. |
| CPP-067 | BinnedSpectrum::getBinIntensity mutates the spectrum it reads | **fixed** | getBinIntensity now calls bins_->coeff() and is declared const (h:113, cpp:199-204), with a comment explaining why coeffRef must not be used. |
| CPP-068 | BinnedSpectrum::operator== ignores the bin offset | **fixed** | Added offset_ to both std::tie tuples in operator== (cpp:134-140), with a comment saying the offset belongs to the bin layout and matches isCompatible(). |
| CPP-069 | BinnedSpectrum left-boundary guard relies on unsigned wraparound | **fixed** | Replaced the guard with `if (idx > j)`, which compares before subtracting. |
| CPP-070 | FeatureHandle::asMutable casts away constness of a possibly const object | **documented** | Replaced the stale TODO with a comment saying why the cast exists (std::set hands out const iterators; |
| CPP-071 | DRange default constructor contradicts its documentation | **documented** | Rewrote the constructor doc (DRange.h 69-75). |
| CPP-072 | DRange::united of two empty ranges returns the universal range | **fixed** | DRange.h:185 adds `if (this->isEmpty() && other_range.isEmpty()) return DRange<D>::empty;` before the corner computation. |
| CPP-073 | DRange::extend comment contradicts the collapse it performs | **documented** | Rewrote the @param text (DRange.h 317-318): a dimension that would become inverted (min > max) is collapsed to its centre point, so min <= max always holds afterwards. |
| CPP-074 | DIntervalBase default constructor documented as infinite corners | **documented** | Rewrote the constructor doc (DIntervalBase.h 48-54). |
| CPP-075 | Class tests with unreachable or duplicated assertions | **fixed** | FeatureHandle_test's assertions, StandardTypes_test (Chromatogram typedef instead of a duplicated pair) and the BinnedSpectrum_test section title are all corrected; the first fix covered one of the three. |
| CPP-076 | rasterizeIMFrame clears the caller's image before the check that can throw | **fixed** | The size check now sits directly after getIMData(), before any write, guarded by `!this->empty()` so an empty spectrum still just zero-fills and returns, as MSSpectrum_rasterizeIMFrame_test.cpp:101-123 expects. |
| CPP-077 | rasterizeIMFrame multiplies the bin counts without an overflow check | **fixed** | Before any write, the call now throws Exception::InvalidValue (with OPENMS_PRETTY_FUNCTION) when `im_bins > numeric_limits<Size>::max() / sizeof(float) / mz_bins`. |
| CPP-078 | rasterizeIMFrame casts a non-finite coordinate to Int64 | **fixed** | Peaks with a non-finite m/z or IM value are now skipped before the range filter (std::isfinite). |
| CPP-079 | sortByPositionPresorted handles an incomplete chunk list differently in its two branches | **fixed** | A non-empty chunk list is now checked up front. |
| CPP-080 | sortByPositionPresorted trusts is_sorted and feeds std::inplace_merge an unsorted range | **fixed** | In the merge branch, a chunk marked sorted is now checked with std::is_sorted using the same comparator, and stable-sorted if the claim is false, so inplace_merge always gets sorted inputs. |
| CPP-081 | Chunks::add can record a chunk whose start exceeds its end | **fixed** | MSSpectrum.h:87-101: `add()` now hoists the start into a local and throws Exception::Precondition (OPENMS_PRETTY_FUNCTION, message carrying both sizes) when `spec_.size() < start`, so an inverted or past-the-end chunk can never be recorded; |
| CPP-082 | An empty ion-mobility array makes isSortedByIM report true and sortByIonMobility a silent no-op | **fixed** | sortByIonMobility and isSortedByIM require the ion-mobility array to have one entry per peak; a longer, sorted array had let reshapeIMFrameToMany read past the peaks. |
| CPP-083 | mergePeaks leaves the inherited range cache too narrow, undocumented | **fixed** | MSChromatogram.cpp:571-574: call updateRanges() at the end of the merge, with a comment saying why recomputation is preferred over leaving stale values that still look current (unlike select(), a merge can only lose data this way). |
| CPP-084 | mergePeaks leaves the destination's data arrays mis-sized, so a later sort or select throws | **fixed** | MSChromatogram.cpp:565-569: clear the three peak-parallel arrays inside mergePeaks, with a comment saying why (they describe the pre-merge peaks and the size mismatch would make the chromatogram's own sort()/select() throw), mirroring clear() at MSChromatogra… |
| CPP-085 | setSumSimilarUnion has external linkage at global namespace scope | **fixed** | MSChromatogram.cpp:482: the definition is now `static`, with a comment saying why internal linkage is required (detail of mergePeaks in this TU; |
| CPP-086 | mergePeaks takes a non-const reference to a chromatogram it only reads | **fixed** | MSChromatogram.h:484 and MSChromatogram.cpp:557: the parameter is now `const MSChromatogram& other` and the tag `@param[in] ... |
| CPP-087 | The chromatogram stream operator prints an always-empty settings block | **fixed** | ChromatogramSettings.cpp:149-168: the parameter is named (matching the header declaration's `spec`, ChromatogramSettings.h:153) and the block now prints native ID, the chromatogram type name via the house idiom `ChromatogramSettings::ChromatogramNames[static_… |
| CPP-088 | updateRanges warns that ranges were already up to date on its very first call | **fixed** | MSChromatogram.cpp:525-528: capture `const bool had_ranges = !RangeRT::isEmpty() && !RangeIntensity::isEmpty();` before clearing, with a comment saying why the numeric comparison alone cannot tell 'no range yet' from 'range unchanged', and require it in the w… |
| CPP-089 | BaseFeature::sortPeptideIdentifications comparator is not a strict weak ordering | **fixed** | The comparator keys on hit presence rather than PeptideIdentification::empty(), which is false for a hit-less identification read from featureXML and left the out-of-bounds read in place. |
| CPP-090 | The same comparator mutates its arguments, so hits are sorted only where the sort happens to compare | **fixed** | BaseFeature.cpp:126-131: hits are now sorted in a pass of their own over peptides_ before std::sort runs, and the comparator (BaseFeature.cpp:145) takes 'const PeptideIdentification&' so it can no longer modify what it compares. |
| CPP-091 | Mixed isHigherScoreBetter flags make the sort comparator asymmetric | **fixed** | BaseFeature.cpp:135-143: the flag is read once, from the first identification that has hits (default true when none has hits), captured by value in the lambda (BaseFeature.cpp:145) and used for every comparison. |
| CPP-092 | updateIDReferences / updateAllIDReferences lose identification matches on a throwing translation | **fixed** | BaseFeature.cpp:272-292: the primary ID and the match set are translated into a local std::optional and a local std::set and only committed (assign / swap) after every translation has succeeded. |
| CPP-093 | ConsensusFeature::Ratio default constructor leaves ratio_value_ indeterminate | **fixed** | Ratio's value is initialised. Tracing it exposed that .oms ratios were never stored under their consensus feature nor loaded into the map; both halves are fixed separately (see findings outside the log). |
| CPP-094 | ConsensusFeature::setRatios takes a non-const lvalue reference for a copy-in setter | **fixed** | ConsensusFeature.h:264 and ConsensusFeature.cpp:321 now take 'const std::vector<Ratio>&'. |
| CPP-095 | getAnnotationState reports MULTIPLE_SAME when only one identification actually has hits | **documented** | No logic change. |
| CPP-096 | Feature::getConvexHull() is a const method that lazily mutates the object and hands out a mutable reference | **fixed** | Feature.h:103 and Feature.cpp:93 now return 'const ConvexHull2D&', which closes the mutate-through-a-const-Feature path at compile time. |
| CPP-097 | MRMFeature lookup by unknown key mutates the map and returns the first feature | **fixed** | Added a file-local helper, featureIndex_(map, key, OPENMS_PRETTY_FUNCTION), in MRMFeature.cpp. |
| CPP-098 | MRMFeature::addFeature strands a feature when a key repeats, while the sibling class throws | **fixed** | On a repeated key, both overloads of each function now overwrite the feature at the index already stored, using map::emplace and assigning in place on a hit. |
| CPP-099 | MRMTransitionGroup::isInternallyConsistent cannot report an inconsistent group in a release build | **fixed** | The function now tests the transition and chromatogram counts, then the map sizes, then isMappingConsistent_(), and returns the result. |
| CPP-100 | IDScoresAsMetaValue writes the transition_names meta value twice | **fixed** | Deleted the duplicate write at the former line 152. |
| CPP-101 | getLibraryIntensity clamps entries the caller already had in the output vector | **fixed** | The function records result.size() before appending and clamps from that index, with a comment on why. |
| CPP-102 | subset re-keys precursor chromatograms by nativeID and throws on a group the class's own test builds | **fixed** | subset() now inverts precursor_chromatogram_map_ into a per-index key list (map values are storage indices by construction) and copies each precursor chromatogram in storage order under its original key. |
| CPP-103 | subsetDependent indexes chromatogram_map_.at() without the guard subset uses | **fixed** | subsetDependent now checks hasChromatogram before copying and throws Exception::ElementNotFound(__FILE__, __LINE__, OPENMS_PRETTY_FUNCTION, nativeID), with a comment on why. |
| CPP-104 | The subsetDependent class-test section tests subset, leaving subsetDependent with no coverage | **fixed** | Rewrote the section to call subsetDependent. |
| CPP-105 | IndexedMzMLHandler copy constructor silently drops both native-id maps | **fixed** | Added spectra_native_ids_(source.spectra_native_ids_) and chromatograms_native_ids_(source.chromatograms_native_ids_) to the copy constructor in declaration order, with a comment saying why. |
| CPP-106 | IndexedMzMLHandler::openFile accumulates index state instead of replacing it | **fixed** | parseFooter_ now starts by clearing both offset vectors and both native-id maps, and resets index_offset_ to -1, spectra_before_chroms_ to true and parsing_success_ to false. |
| CPP-107 | Record read length is unchecked in both directions and the read result is never inspected | **fixed** | Added an anonymous-namespace helper readRecord_(stream, filename, start, end, index_offset), used by both helpers. |
| CPP-108 | Chromatogram out-of-range message reports the spectrum count | **fixed** | The chromatogram message now says 'number of chromatograms' and interpolates getNrChromatograms(). |
| CPP-109 | Record XML parse errors are discarded, and the handler always feeds the parser ill-formed input for the last record | **fixed** | Malformed XML inside an mzML record raises a ParseError instead of surfacing later as a ConversionError from the partial record. |
| CPP-110 | getMSChromatogramById(int) recomputes ranges twice | **fixed** | Removed the redundant c.updateRanges() and left a trailing comment noting that the callee already updates ranges. |
| CPP-111 | MapConversion::convert(PeakMap) sorts and indexes past the end of its vector | **fixed** | ConversionHelper.cpp: the clamp (and output_map.reserve(n)) now runs after get2DData(tmp) and uses tmp.size(), with a comment explaining why. |
| CPP-112 | FeatureMap::swap and ConsensusMap::swap do not swap the meta values | **fixed** | Both swap() functions exchange meta values; FeatureGroupingAlgorithmUnlabeled::group restores the caller's meta values, which the new swap would otherwise have discarded. |
| CPP-113 | ConsensusMap::split indexes its result vector with the map index | **fixed** | split() now builds an index-to-position map from column_description_'s keys. |
| CPP-114 | ConsensusMap::split dereferences an empty map in the isobaric branch | **not a defect** | None. |
| CPP-115 | ConsensusMap::appendRows pairs column headers by position, not by column index | **fixed** | Replaced the insert and lockstep loop with one loop over rhs's headers that looks each key up in column_description_. |
| CPP-116 | ConsensusMap::setPrimaryMSRunPath writes by position through a default-inserting map | **fixed** | The existing keys are collected in order first. |
| CPP-117 | MSExperiment::getPrimaryMSRunPath joins using the unstripped file:/// path | **fixed** | getPrimaryMSRunPath keeps the URI form tools write to their output; the new File::localPath() converts it only where File::exists is checked. The first fix changed the returned path, stripped the POSIX root and broke two NucleicAcidSearchEngine references. |
| CPP-118 | UniqueIdIndexer::resolveUniqueIdConflicts can loop forever | **fixed** | Redraws are bounded by the ids in use plus 64; a fixed cap of 64 fired whenever a seeded generator (every TOPP -test run) merged maps written under the same seed. |
| CPP-119 | FeatureMap::getPrimaryMSRunPath does not clear its output argument | **fixed** | toFill.clear() on entry, with a comment explaining why. |
| CPP-120 | mzML list `count` attribute drives an unvalidated container reserve | **fixed** | New file-local capacityHint_ (MzMLHandler.cpp:112) returns 0 for a count of zero or less and otherwise at most a limit. |
| CPP-121 | rasterizeRTMZ's SUM aggregation is not reproducible across thread counts | **documented** | Added a @note to the rasterizeRTMZ doc in MSExperiment.h. |
| CPP-122 | rasterizeRTMZ's two negative-bin guards are dead code that mask an unchecked precondition | **documented** | Made the header @note concrete: sortedness is not checked, and on unsorted data spectra and peaks in the window may be missed, those below min are silently skipped, those above max are piled into the last RT column / m/z row, and no error is reported. |
| CPP-123 | None found — no new C++ source defect | **no finding** | The log's own entry records that this review pass found no new C++ defect. |
| CPP-124 | .ibd array reads are sized from the declared count with no comparison against the file's length | **fixed** | The .ibd length comes from fstat on the open handle; the first fix did two path lookups per array read, roughly seven times slower random reads. |
| CPP-125 | ImzMLMeta::mz_data_type and int_data_type stay empty on an index-only load | **fixed** | Moved dtStr_ out of ImzMLInterceptConsumer into the file's anonymous namespace. |
| CPP-126 | An unnamed external auxiliary array vanishes from the index with no trace | **fixed** | Added `uint32_t unnamed_aux {0}` to ImzMLSpectrumIndex (documented in the header). |
| CPP-127 | verifyIbdUuid_ carries two contradictory doc comments, one describing behaviour the function does not have | **documented** | Deleted the superseded first block. |
| CPP-128 | The declared .ibd checksums are parsed and mirrored but never verified on any read path | **documented** | The declared SHA-1/MD5 of the .ibd are documented as never recomputed; only the UUID header is checked while loading. No opt-in verification API was added. |
| CPP-129 | OnDiscImzMLExperiment::open re-derives the .ibd path in a branch that cannot be taken | **fixed** | Replaced the ternary and the dead block with `pimpl_->ibd_path_ = pimpl_->meta_.ibd_file_path;` plus a comment explaining that loadSpectraIndex resolves and records the path before parsing, so a second derivation could only drift. |
| CPP-130 | IonImage allocates width * height from unvalidated file-supplied image dimensions | **fixed** | The ion image pixel ceiling is 2^31; the first fix's 4096 x 4096 refused real whole-slide rasters. |
| CPP-131 | MSImagingRegion::fromMask computes the far corner in wrapping UInt arithmetic | **fixed** | After the mask check, fromMask throws Exception::InvalidValue ("mask extends past the coordinate range") if origin_x > UINT_MAX - (width-1) or origin_y > UINT_MAX - (height-1). |
| CPP-132 | ImzMLWriter::store cannot write a metadata-only continuous dataset | **fixed** | isContinuousMode_ now works out no_peaks with std::all_of over exp.getSpectra(). |
| CPP-133 | ImzMLWriter::store leaks the ProgressLogger recursion depth on every throw | **fixed** | Wrapped everything after startProgress in try { ... |
| CPP-134 | A failed ImzMLWriter::store leaves a truncated .ibd with no .imzML | **fixed** | Same try/catch as CPP-133. |
| CPP-135 | ImzMLFile_1_Example_Continuous.imzML is not schema-valid mzML 1.1.0, so ImzMLFile::isValid would reject its own reference fixture | **open** | Making the continuous imzML fixture schema-valid means adding cvRef to 109 cvParams and reordering elements; the tests do not validate the fixture, so it was left for a fixture-only change. |
| CPP-136 | ImzMLFile_2_Example_Processed.imzML declares mzML version="1.1" instead of 1.1.0 and is ISO-8859-1 with Latin-1 bytes | **fixed** | The processed imzML fixture declares mzML 1.1.0 and is stored as UTF-8. |
| CPP-137 | ImzMLFile's two buildImagingGeometry overloads, documented as the same source of truth, disagree on the pixel-size condition and on the skip-reason ordering | **fixed** | The experiment overload skips off-plane pixels before the coordinate check and sets the pixel size only when positive, as the index overload does. |
| CPP-138 | ClassTest::isRealSimilar reports any two infinities as similar, including +inf against -inf | **fixed** | Added an infinity branch right after the NaN guards (ClassTest.cpp:387-412). |
| CPP-139 | ClassTest::isRealSimilar is asymmetric — the quotient underflows to -0.0 and defeats its own opposite-sign branch | **fixed** | Replaced 'if (ratio < 0.)' with 'if (std::signbit(number_1) != std::signbit(number_2))' (ClassTest.cpp:477), with a comment explaining why the operands are tested rather than the quotient. |
| CPP-140 | ImzMLHandler's non-external peak fill is dead code: MzMLHandler throws first on a mixed spectrum | **fixed** | A spectrum with only one external peak array is rejected at parse time, and the unreachable inline fallbacks are removed. |
| CPP-141 | DataValue::operator double() reads the union's double member for a non-numeric value | **fixed** | No change in ImzMLWriter.cpp, which belongs to imzml-b. |
| CPP-142 | ImzMLWriter::store treats one misaligned FloatDataArray as skippable or fatal depending on an unrelated PeakFileOptions flag | **fixed** | Added dropMisalignedDataArrays_(MSExperiment&) in ImzMLWriter.cpp. |
| CPP-143 | Negative CHEMMOD identifiers fail modification-cell parsing | **fixed** | MzTab.cpp:131-185. |
| CPP-144 | Quoted commas split a MzTab modification-list entry | **fixed** | MzTab.cpp:298-301: the condition is now `ss[pos] == ',' && (in_param_bracket \|\| in_quotes)`, with a comment explaining why. |
| CPP-145 | MzTab parameter rendering fails to quote a bare comma | **fixed** | MzTabBase.cpp:337-354: both checks now use `hasSubstring(name_, ',')` / `hasSubstring(value_, ',')` (the existing char overload), with a comment. |
| CPP-146 | MzTab score-by-run header order differs from row order | **fixed** | The protein header now iterates the reference row's own map score-major and emits the stored run keys, so it no longer renumbers runs as 1..N; |
| CPP-147 | MzTab PSM optional columns are dropped on load | **fixed** | PSM opt_ columns load, and all four mzTab sections bounds-check them: the fix had activated an out-of-bounds read for rows whose trailing empty cells load() trims away. |
| CPP-148 | MzTab column-unit metadata parses its key as an index | **fixed** | Reader (MzTabFile.cpp:683-709): one branch `meta_key == "colunit" && meta_key_fields.size() == 2` lower-cases the section name and push_backs cells[2] into the matching vector; |
| CPP-149 | MzTab-M assay custom metadata is written under ms_run | **fixed** | MzTabMFile.cpp:228-234: the key prefix is now "MTD\tassay[", with a comment. |
| CPP-150 | MzTab-M column-unit families share an incorrect output key | **fixed** | MzTabMFile.cpp:355-367: the feature and evidence loops now write colunit_small_molecule_feature and colunit_small_molecule_evidence, keeping the file's existing underscore after 'colunit'. |
| CPP-151 | MzTab-M exporter changes metadata keys before lookup | **fixed** | MzTabM.cpp:96-140: removed the three pre-substitution transforms and added one comment on why raw keys are kept. |
| CPP-152 | pepXML end_scan mismatch check reads start_scan twice | **fixed** | endscan is now read from "end_scan" with optionalAttributeAsInt_, defaulting to start_scan. |
| CPP-153 | pepXML drops a uniquely resolved undeclared modification | **fixed** | The emplace_back(mods[0], position-1) now sits after the size>1 check, so the first match is used whether there is one match or several. |
| CPP-154 | pepXML fixed protein C-terminal modification misses terminal branch | **fixed** | A protein-terminal fixed modification is applied only to hits at a matching protein boundary, including pepXML's '-' marker; correcting the enum alone applied it to every peptide. |
| CPP-155 | qcML loses units across its own store/load | **fixed** | Writer now emits the schema names unitCvRef/unitAccession (QcMLFile.cpp:93,97,205,209). |
| CPP-156 | qcML table writer discards its normalized row copy | **fixed** | Write copy_row instead of *it (QcMLFile.cpp:248), with a comment. |
| CPP-157 | qcML removeAllAttachments omits set-only entries | **fixed** | removeAllAttachments now erases matching attachments (std::remove_if on cvAcc) straight from every list in runQualityAts_ and setQualityAts_ (QcMLFile.cpp:516-531, plus #include <algorithm>). |
| CPP-158 | qcML map2csv emits misaligned rows when a column is missing | **fixed** | The header is now the union of all row keys, collected in a std::set (same ordering as a single std::map row). |
| CPP-159 | qcML writer and reader disagree on set-member CV accession | **fixed** | onStartElement: under setQuality, QC:0000005 adds qp_.id (the run ID) to names_ (:879-883). |
| CPP-160 | qcML TIC slump percentage truncates before multiplication | **fixed** | Both sites now compute `exp.empty() ? Size(0) : 100 * below_10k / exp.size()` (QcMLFile.cpp:1354, :1429): multiply first, guard empty, and keep the existing integer-percentage string format. |
| CPP-161 | Percolator loader requires FileName through an unchecked map lookup | **fixed** | The ID_MERGE_INDEX meta value is now set only when a FileName column exists (now around lines 277-282). |
| CPP-162 | Percolator enzyme features use unmapped protein-terminal markers | **fixed** | Moved the terminus normalisation up to just after aa_before/aa_after are read, before enzN/enzC. |
| CPP-163 | Percolator writer and loader disagree on trailing protein-list width | **fixed** | load() now reads Proteins as a variable-width last column when the header's last column is "Proteins" (flag proteins_trailer). |
| CPP-164 | Mascot query index guard accepts one-past-end | **fixed** | MascotXMLHandler.cpp:57-64 now checks the 1-based value before subtracting: `if (attribute_value <= 0 \|\| static_cast<Size>(attribute_value) > id_data_.size()) fatalError(...)`, then assigns the index. |
| CPP-165 | Mascot RT failure test treats zero as failure and NaN as success | **fixed** | Line 120 now reads `if (!id_data_[peptide_identification_index_].hasRT())`, with a comment that a failed look-up leaves NaN and 0 is a valid RT. |
| CPP-166 | Mascot MGF loader carries precursor and RT fields between blocks | **fixed** | The MGF loader resets precursor and RT fields between blocks, and an empty block ends before the next spectrum's metadata is parsed. |
| CPP-167 | mzIdentML writer places C-terminal modification at last-residue location | **fixed** | MzIdentMLHandler.cpp: now writes `size() + 1` in writePeptideHit (:1368) and writeXLMSPeptideHit (:1764). |
| CPP-168 | mzIdentML reader dereferences missing PeptideSequence child | **fixed** | The sequence is now read with `StringManager::convert(element_sib->getTextContent())` (:2471). |
| CPP-169 | mzIdentML substitution position is used as unchecked string index | **fixed** | The 1-based position is now checked as `1 <= pos <= as.size()` before indexing, and a violation throws Exception::ParseError with OPENMS_PRETTY_FUNCTION (:2508-2514). |
| CPP-170 | mzData checks missing and short arrays after unsafe indexing | **fixed** | MzDataHandler.cpp, all in the one owned file. |
| CPP-171 | mzData writer emits scan modes its reader does not recognize | **fixed** | MzDataHandler.cpp, reader side only. |
| CPP-172 | Streaming mzML consumer references header entries declared only for first record | **fixed** | Streaming output declares what it references, extended to integer and string arrays and to chromatograms; later array histories that cannot be declared are omitted with a warning. |
| CPP-173 | mzXML release decode reads beyond short peak payload | **fixed** | New lines 1199-1211 compute `expected_values = 2 * static_cast<Size>(peak_count_)`, which cannot wrap. |
| CPP-174 | mzXML precursor value and window width depend on SAX chunking | **fixed** | onCharacters (line 621) now appends precursorMz chunks to the scan's char_rest_. |
| CPP-175 | SVOutStream probe stream remains poisoned after non-newline manipulator | **fixed** | SVOutStream.cpp:108-118: before each probe the buffer is now emptied and its error state cleared (ss_.str(""); |
| CPP-176 | TrafoXML omits unsupported parameter types after a non-fatal diagnostic | **fixed** | TransformationXMLFile.cpp:161-164: error(LOAD, ...) is now fatalError(LOAD, ...), so Exception::ParseError is thrown as the header already documents. |
| CPP-177 | Linear transformation accepts symmetric_regression but never uses it | **documented** | symmetric_regression is documented as accepted for compatibility but ignored, in the header and in the parameter description; the fit stays an ordinary regression of y on x. |
| CPP-178 | MSstats missing design pair silently uses sample0 | **fixed** | In storeLFQ (MSstatsFile.cpp:455-473) and storeISO (726-740), the (file, label) pair is now looked up with find() in path_label_to_sample. |
| CPP-179 | MSstats unknown summarization method writes zero intensities | **fixed** | storeLFQ now checks the method against manual,max,min,mean,sum with ListUtils::create/ListUtils::contains. |
| CPP-180 | MSstats aggregation collapses equal intensities at distinct times | **fixed** | intensities is now a vector<MSstatsFile::Intensity>, filled once per distinct retention time (MSstatsFile.cpp:148-165). |
| CPP-181 | SqliteConnector permits copying an owned database handle | **fixed** | SqliteConnector's copy constructor and assignment are deleted: it owns its handle |
| CPP-182 | SqliteConnector does not close a handle when opening fails | **fixed** | a failed sqlite3_open_v2 closes the handle it still allocates before throwing |
| CPP-183 | SQLite bound statements leak on bind or step errors | **fixed** | executeBindStatement finalises its statement through a guard on every exit |
| CPP-184 | SQLite table-name helpers interpolate names as SQL syntax | **fixed** | table names are bound or quoted as identifiers instead of interpolated as SQL |
| CPP-185 | SQLite query helpers ignore step errors and can leak statements | **fixed** | countTableRows, tableExists and columnExists check the step status and finalise through a guard |
| CPP-186 | SQLite string extraction truncates embedded NUL bytes | **fixed** | TEXT is extracted with its declared byte length, so an embedded NUL no longer truncates it |
| CPP-187 | SQLite integer-to-string extraction narrows to 32 bits | **fixed** | extractValueIntStr reads sqlite3_column_int64; |
| CPP-188 | MSDataWritingConsumer class test is disabled and calls a nonexistent constructor | **fixed** | MSDataWritingConsumer_test is rewritten against the current API and enabled. |
| CPP-189 | SqliteConnector row-count documentation names the wrong exception | **documented** | Documentation corrected in the one file I own (src/openms/include/OpenMS/FORMAT/SqliteConnector.h:79-83): the single `@throws Exception::SqlOperationFailed if table is unknown` line is replaced by two `@throws` lines that name IllegalArgument for the unknown-… |
| CPP-190 | Default handler writing reads an uninitialized SQL batch size | **fixed** | Added `sql_batch_size_(500)` to the constructor init list (MzMLSqliteHandler.cpp:304, in declaration order), matching setConfig's default. |
| CPP-191 | Array hydration lacks pair length and role validation | **fixed** | Added an acceptArray lambda in populateContainer_sub_ (cpp:139-159). |
| CPP-192 | Blob hydration assigns objects by SQL row encounter order instead of record identity | **fixed** | Every metadata and data query now ends in ORDER BY SPECTRUM.ID / CHROMATOGRAM.ID (cpp:553, 580, 601, 627, 665, 793). |
| CPP-193 | Spectrum/chromatogram IDs and peptide sequence remain unescaped SQL values | **fixed** | Each text value is quoted with the existing StringUtils::quote(s, '\'', OpenMS::QuotingMethod::DOUBLE), which doubles apostrophes and wraps the value, the same SQL-literal quoting OpenSwathOSWWriter uses. |
| CPP-194 | Metadata failures leave committed DATA rows and advanced writer counters | **fixed** | The bodies moved into protected writeRunLevelInformation_/writeSpectra_/writeChromatograms_(SqliteConnector&, ...), declared in the header; |
| CPP-195 | Product and precursor indexes are accidentally built on DATA | **fixed** | Moved the four indexes to PRODUCT(CHROMATOGRAM_ID/SPECTRUM_ID) and PRECURSOR(CHROMATOGRAM_ID/SPECTRUM_ID) (cpp:1139-1145), keeping their names. |
| CPP-196 | SWATH selection stops at a matching chromatogram precursor NULL ID | **fixed** | The WHERE clause now filters `SPECTRUM_ID IS NOT NULL` (cpp:106), and the loop uses Sql::nextRow instead of a NULL sentinel (see CPP-203). |
| CPP-197 | SWATH window docs promise distinct centers but query deduplicates full bounds tuples | **documented** | Documented the tuple semantics: two windows with the same centre and different widths are two entries, and readSpectraForWindow returns the same spectra for both because it only uses the centre. |
| CPP-198 | Recreating tables on a used handler retains counters from the deleted database | **fixed** | After createIndices_() succeeds, createTables sets both counters to 0 (cpp:1108-1114). |
| CPP-199 | Metadata readers accept invalid negative activation enum values below -1 | **fixed** | Both readers now read sqlite3_column_int64 and insert only when 0 <= value < SIZE_OF_ACTIVATIONMETHOD (cpp:739-749, 889-897). |
| CPP-200 | SqMassFile transform issues an extra empty selected-read batch | **fixed** | Counts are taken once and reused for setExpectedSize. |
| CPP-201 | Full metadata recovery promise omits auxiliary-array loss | **documented** | Rewrote @param write_full_meta: settings and all spectrum/chromatogram metadata are recovered, but only m/z-or-RT and intensity arrays are stored, so float/integer/string arrays (e.g. |
| CPP-202 | Read accessors create an empty database when the input path is missing | **fixed** | All ten read paths now pass SqliteConnector::SqlOpenMode::READ_ONLY (MzMLSqliteHandler.cpp 312, 396, 426, 451, 470, 487, 529; |
| CPP-203 | SWATH accessors can return partial success after SQLite step errors | **fixed** | Each loop now uses the existing Sql::nextRow (SqliteConnector.cpp:243-272), which returns ROW/DONE and throws SqlOperationFailed on any other status. |
| CPP-204 | MSDataSqlConsumer owning raw pointer leaks during failed construction and can be shallow-copied | **fixed** | handler_ is now std::unique_ptr<MzMLSqliteHandler> (MSDataSqlConsumer.h:134, <memory> included). |
| CPP-205 | MSDataSqlConsumer destructor lets I/O exceptions escape noexcept destruction | **fixed** | Added a public, idempotent finalize() (h:82-91, cpp:57-69). |
| CPP-206 | MSDataSqlConsumer changes buffered records to the next run ID | **fixed** | addRun() and setRunId() call flush() before changing the run id (cpp:73-74, 86-87), with a comment explaining that the buffers do not record their run. |
| CPP-207 | SpectrumAccessSqMass unchecked view positions permit out-of-bounds access | **fixed** | Added a file-local storageIndex(sidx, id) (cpp:15-34). |
| CPP-208 | SpectrumAccessSqMass bulk read does not preserve the configured view order or duplicates | **fixed** | getAllSpectra (cpp:146-168) now sorts and deduplicates sidx_, reads each distinct id once, and rebuilds the configured view with lower_bound, repeats included. |
| CPP-209 | SpectrumAccessSqMass metadata index stays zero for every spectrum | **fixed** | getSpectrumMetaById sets index to the view position id (cpp:122-123), and getAllSpectra sets it to k (cpp:184). |
| CPP-210 | SpectrumAccessSqMass class test repeats one out-of-range index instead of testing 50 | **fixed** | The test now passes indices2 (test:104) and adds a negative case, indices3=[-1] (test:106-108). |
| CPP-211 | SpectrumAccessSqMass installed example omits required handler run ID | **documented** | The example now reads `MzMLSqliteHandler handler(file, 0); |
| CPP-212 | OpenSwath drift filtering dereferences missing or misaligned mobility arrays | **fixed** | filterByDrift (ISpectrumAccess.h:108-139) now throws std::invalid_argument for a null input, a missing m/z or intensity array, a missing drift-time array, or arrays of unequal length. |
| CPP-213 | SqMassFile store documentation hides unconditional replacement of an existing database | **documented** | store() docs (SqMassFile.h:93-104) now say a new database is written, with an @warning: an existing file is deleted before writing starts, nothing is appended or kept, the replacement is not atomic, and a failed write leaves the old file gone and possibly a p… |
| CPP-214 | MSDataSqlConsumer full metadata discards supplied experimental settings and addRun suppresses accumulated snapshot | **fixed** | setExperimentalSettings now stores the settings into peak_meta_ via static_cast<ExperimentalSettings&> when full_meta_ is set (cpp:138-146), the same idiom the handler uses. |
| CPP-215 | MSDataSqlConsumer accepts negative signed buffer size before unsigned allocation | **fixed** | The constructor throws Exception::IllegalArgument for flush_after < 0 before reserve() and createTables() (cpp:24-30), so an existing file is not replaced. |
| CPP-216 | SpectrumAccessSqMass zero-width RT documentation differs from delegated first-at-or-after behavior | **documented** | Documented the zero-width behaviour, which getMultipleSpectra depends on, in SpectrumAccessSqMass.h (deltaRT param) and in the base ISpectrumAccess.h getSpectraByRT doc. |
| CPP-217 | OpenSwath getMultipleSpectra count parameter can return more than requested | **documented** | The count getMultipleSpectra returns is documented in ISpectrumAccess and OpenSwathScoring. |
| CPP-218 | Positive-accuracy Numpress encoding destroys one- and two-point coordinate arrays | **fixed** | optimalLinearFixedPointMass special-cases only dataSize == 0 (MSNumpress.cpp:242-248). |
| CPP-219 | Chromatogram precursor reload drops supplemental activation metadata | **fixed** | Chromatogram precursors read the supplemental activation terms MS:1002678/1002679/1002680 and the ETciD/EThcD methods they imply, with a round-trip test. |
| CPP-220 | Negative initial linear-Numpress coordinates can wrap during sqMass writing | **fixed** | A lossy sqMass m/z or retention-time array whose first two values linear Numpress cannot hold is stored with zlib only, with a negative-RT round-trip test. |
| CPP-221 | Gumbel result declares eval without defining it | **fixed** | GumbelDistributionFitResult::eval is defined and exported, with a test. |
| CPP-222 | Gumbel least-squares fitter advertises an undefined weighted fit | **fixed** | The never-defined GumbelDistributionFitter::fitWeighted declaration is removed; nothing referred to it, and GumbelMaxLikelihoodFitter provides the weighted fit. |
| CPP-223 | Distribution-fitter documentation names nonexistent gnuplot members | **fixed** | Gauss and both Gumbel fitters no longer promise getGnuplotFormula(); IDDecoyProbability's debug output builds the formula from the fitted parameters. |
| CPP-224 | Gumbel maximum-likelihood fitting reads beyond a short weight vector | **fixed** | fitWeighted rejects a weight vector of another length and non-finite or negative weights. |
| CPP-225 | Memory-usage delta overwrites its minus sign | **fixed** | Memory-usage deltas keep their minus sign, with a test. |
| CPP-226 | Update notification announces the local version instead of the offered update | **fixed** | The update notice names the version the server offers. |
| CPP-227 | Download filename selection does not prevent concurrent overwrite | **fixed** | A download claims its file name by exclusive creation, so concurrent downloads cannot truncate each other. |
| CPP-228 | Squaring Gumbel negative log likelihood can change the optimum | **fixed** | Confirmed: a five-value sample at scale 0.014 has NLL -13.4 at the estimate, while the squared objective is zero along a whole contour elsewhere. The fitter now solves the Gumbel likelihood equations directly; unweighted data still returns the initial parameters. |
| CPP-229 | Download collision-suffix counter lacks an overflow guard | **fixed** | The collision suffix counter is bounded at 10000 and the download then fails. |
