# FLASHTnT 250debb semantic comparison

Compared port `250debbc26565b51ef861ccaa8132b9e11b4f8d9` with public upstream
`t0mdavid-m/OpenMS@3f508829ad81c91354d397966f28d428e29e5329`. All 12 imported
source/license blobs match their recorded Git objects; detailed checks and
fixture numeric evidence are in `flashtnt250-semantic-review.json`.

The initial source comparison found no remaining text-level port change that
explained the May 2025 cache discrepancy. Follow-up runtime and compiler checks
then identified two inherited memory errors and a platform-dependent absolute-value
overload. Fixes and causal regression evidence are recorded below. The historical
cache remains numerically different and is not established as an equivalent baseline.

- `FLASHTaggerAlgorithm.cpp`: identical after mechanical String/API renaming,
  lowercase-copy and reverse-string translations.
- `FLASHExtenderAlgorithm.cpp`: explicit `std::string(1, aa)` preserves the old
  one-character String conversion; otherwise algorithm body unchanged.
- `FLASHTnTHelpers`: upstream uppercase mutation is restored; Tag and DAG bodies
  match. Initializing the previously uninitialized tag index and vertex count
  does not alter the normal assignment/construction path.
- `FLASHTnTAlgorithm.cpp`: added guards and explicit parsing reject malformed
  metadata. The actual AQPZ input has a nonempty native ID, 215 peaks and complete
  215-value qscore/SNR lists, tolerance 5 and precursor scan 0. All 215 SNR values
  have identical float bits under old direct float parsing versus double parsing
  followed by float conversion; PeakGroup still stores SNR as float. The missing
  native-ID fallback and absent-target checks do not trigger on this fixture.
- `FLASHTnTFile.cpp`: numeric metadata now renders through `toString()`. The
  ProForma AST migration, candidate-name normalization and range validation run
  after identification/scoring and cannot alter tag counts or hit scores.
  Changing a negative sequence-start fallback from 1 to 0 is confined to this
  renderer; writer callers already supply nonnegative offsets.

The pre-cache Tagger revision `b19d12d2831eb90e34a92eb113608d57bf36da8f`
(2025-04-30) differs substantially from the pinned upstream source: protein
vectorization changed from bitsets to unordered sets; score selection changed
the matching-count comparison from `>=` to `>`; FASTA/vectorization and candidate
matching were reorganized. The pinned history also contains the December 2025
inverse-tag-direction fix. These changes predate the port and invalidate an
assumption that the unversioned May cache is an exact same-source baseline.
They have not been experimentally assigned responsibility for individual values.

Existing older installed SDKs inspected on dax under `openms4-5d1e239-20260910`,
`openms4-core-runtime-20260910` and `openms4-split-sdk-20260910` expose the newer
API and contain no legacy `OpenMS/DATASTRUCTURES/String.h`. Reusing them cannot
compile unmodified upstream FLASHTnT. A controlled comparison would require a
matching old Core build, or another compatibility port (which would not be an
independent unmodified baseline). No full old Core build was started.


## Follow-up sanitizer and compiler evidence

AQPZ AddressSanitizer runs confirmed two reads already present in exact upstream
3f508: an endpoint of -1 dereferenced before its guard (fixed 709de5e), then a
reverse iterator dereferenced after reaching rend() in precursor calculation
(fixed 93eb47c). These are inherited defects. The corrected source passes all
four Release tests and all four ASan/UBSan/leak tests on Linux.

The unqualified abs calls at Tagger lines 516/536 resolve differently in the port
environments: GCC 14.4 tree dumps show integer truncation before absolute value;
Apple Clang 21 AST selects double(double). Fix 93eb47c selects std::abs and adds
a public-API regression with two PET mass ladders separated by 0.5 Da. This is a
confirmed portability defect in the port. Original upstream include/compiler
overload resolution was not tested. Compiler evidence is retained in
`flashtnt-abs-gcc-updateTagSet.txt` and `flashtnt-abs-macos-ast.txt`.

The same committed regression object fails against unchanged 709de5e backend and
passes against 93eb47c. A PET-only diagnostic additionally prints the retained
masses: old [100], corrected [100, 100.5]. Both archive hashes were unchanged.
The detailed receipts are `flashtnt-pet-negative-control.json` and
`flashtnt-pet-only-negative-control.json`.

All three corrected 93eb47c scientific TSV outputs are byte-identical between
Linux x64 and Mac ARM: 698 tags, 114 AQPZ tags, 10 protein rows and 10 PrSM rows.
Best AQPZ score 559, fragments 79, mass 24633.174543367222, coverage 32.9167% and
positions 1–240 agree. The unchanged Mac baseline already had these values; the
Linux integer-overload correction restores agreement. Detailed hashes and zero
field differences are in `flashtnt93-crossplatform-comparison.json`.
The historical 2025 cache still differs (2,968 tags, 17 hits, score 505, fragments
69), and no golden values were adjusted to fit current outputs.
