# Relocated native tool runtime — 2026-09-10

The installed Core, CLI and 150 TOPP/OpenSWATH/FLASH tools passed a macOS arm64 runtime qualification after dependency bundling and relocation. The final archive was safely extracted into another directory containing spaces and executed with access to both the original SDK and the assembled runtime denied.

Archive: `openms4-tools-macos-arm64.tar.gz`, **82,818,555 bytes** (79.0 MiB).
SHA-256: `16260f281af804ec8b4102c5b3203d0d250f1d1fe6245fcfb096174439ff7bb1`.
The local artifact is in the experiment workspace beside the repository; binaries are not committed here.

| Package | Version | Clean source revision |
| --- | --- | --- |
| Core | 4.0.0 | `4fdec46b205459b92e7d3b9e56df5d8e912d5c85` |
| CLI | 1.0.0 | `51db6bbbdeba53abc57d23c664de37f9c285372e` |
| TOPP | 1.0.0 | `94e997007b7af9adbaee95d144324276e9fa56ee` |
| OpenSWATH tools | 1.0.0 | `c7901a79cc27463968ec335b6d04894b05b98339` |
| FLASH tools | 1.0.0 | `a6ee68f8589e3dd7eb8cb10b0ea7f3b790e72a4c` |

## What the archive contains

The three installed package TSVs select exactly 150 executables. The archive includes Core, OpenSwathAlgo and CLI shared libraries, 128 copied dependency libraries, and versioned Core runtime data. Test fixtures, examples, GUI products, development headers and the diagnostic SDK probe are excluded. Available dependency license files were retained.

The actual Core is **Debug**, AppleClang 21, C++23, libc++, with OpenMP and OpenSWATH enabled. Its full build information, including disabled optional features and dependency versions, is preserved in the [runtime identity](validation/native-runtime/runtime-identity.json). Every native file has an arm64 slice. The highest recorded Mach-O minimum OS is **macOS 26.0**, arising from the actual dependency build requirements.

## Results and evidence

| Check | Result |
| --- | --- |
| Original installation paths before repair | All 150 tools use `@loader_path/../lib`; CLI uses `@loader_path/`. Absolute external dependency references were captured before repair. |
| Dependency closure after repair | 128 external libraries copied using delocate 0.13. Dependency references and library IDs rewritten; no SDK/Homebrew load paths or absolute RPATHs remain. |
| Signatures | `codesign --verify --strict` passed for 282 files: 150 tools, 131 libraries and the diagnostic probe. The probe is excluded from the archive. Signatures are ad hoc. |
| Isolated startup | All 150 product `--help` commands completed successfully. This exercises startup and option registration, not every tool's algorithm or external engine. |
| Product metadata | Eight strict checks: INI and CTD for FileInfo, PeakPickerHiRes, FLASHDeconv and DecoyDatabase. Product name/version and CTD category were checked. |
| Actual loaded Core | An independently compiled installed-SDK consumer used `dladdr` and `getBuildInfo()` to verify the moved library and exact clean Core JSON. Data discovery and FileInfo discovery resolved inside the moved prefix; the registry contained 150 tools. |
| Chemistry and I/O | Glucose monoisotopic mass, methionine oxidation mass shift, spectrum sorting and a two-peak mzML round trip passed. |
| FileInfo | Parsed the pinned DTA fixture successfully. |
| PeakPickerHiRes | Processed the pinned mzML fixture; FuzzyDiff passed with the original offset/index whitelist. The produced file is also byte-identical to the expected fixture. |
| DecoyDatabase | Generated the pinned FASTA result and passed exact FuzzyDiff comparison. |
| FLASHDeconv | All 18 scientific columns passed the package's numerical comparator against the selected pre-refactor implementation reference. |
| Negative comparison | FuzzyDiff rejected a deliberately different file with its expected comparison-failure exit code, 10. |
| Archive extraction | The app's canonical safe extractor accepted the actual tar. Its executable set is exactly the declared 150 products. An independent probe then loaded the extracted Core and data, repeated chemistry/mzML/discovery checks, and FileInfo started successfully. |
| Receipt contract | 13 isolated tests passed, including mandatory receipt input, stale source pin, wrong/replaced bytes, missing files, dirty/version mismatches, traversal and altered symlinks. |

All runtime executions removed `DYLD_*`, `OPENMS_DATA_PATH`, `OPENMS_HOME_PATH`, `OPENMS_TOOL_PREFIX_PATH`, `TOOL_PREFIX_PATH` and `CMAKE_PREFIX_PATH`; runtime `PATH` was `/usr/bin:/bin`, and OpenMP was limited to two threads. The macOS sandbox denied network access and reads from source, build and SDK trees, `/opt/homebrew`, and `/usr/local/opt`. Negative controls confirmed that original SDK, source and Homebrew files were unreadable. The archive test additionally denied the assembled runtime prefix.

The FLASH reference is from the unchanged front end using Core `21b295c9ad889b402db1e3a20f13e8d08330b61b`, with the prior library identity independently recorded. Its comparator keeps the existing mass and numeric tolerances. It is an equivalence check against that selected implementation, not biological validation or equivalence to the older archived FLASH output; see the [reference provenance](../packages/flash/tests/data/README.md).

Primary records: [summary](validation/native-runtime/summary.json), [original dependencies](validation/native-runtime/before-repair.json), [repaired dependencies](validation/native-runtime/after-repair.json), [signatures](validation/native-runtime/signature-verification.json), [extracted-library identity](validation/native-runtime/archive-verification.json), [narrower PeakPicker comparison](validation/native-runtime/peakpicker-strict-fuzzy.log), and [receipt tests](validation/native-runtime/receipt-tests.log). Tool output, metadata, processing results and fresh installation logs are retained in the same evidence directory. Earlier harness attempts are retained where relevant: the correct help option is `--help`, and copied library install IDs require an explicit rewrite in addition to delocate's dependency rewrites.

## Source attribution

[record_native_install.py](../tools/record_native_install.py) reran the five existing guarded incremental builds and installs with at most two jobs. It verified exact configured revisions and clean source states before and after, checked install-manifest ownership, and recorded 235 installed file hashes plus cache, Ninja, command and manifest evidence. Every one of the 153 regular native files copied before repair matched that fresh receipt; symlinks, data, TSVs and Core JSON were also checked.

The [receipt](validation/native-runtime/native-install-receipt.json) has SHA-256 `e3fc18fcb778c6852fda12d4936ba724640029323df4149ae2b92308452bdcce`. It is included in the archive, and runtime provenance records its digest. [qualify_macos_runtime.py](../tools/qualify_macos_runtime.py) requires this receipt and rejects missing or mismatched files and source identities. It cannot assign a newer clean checkout pin to an older receipt.

This is a **trusted local incremental-builder attestation**, not signed provenance or proof against tampering with both the receipt and the compiler/build tree. The loaded Core's own identity is checked independently at execution time.

## Reproduce

Use the experiment's Python environment containing delocate 0.13, existing configured Ninja build directories, and a new output directory. The first command deliberately refreshes the existing guarded builds and installations; the second modifies only new runtime/evidence copies and builds one small installed-SDK consumer.

```bash
runtime_python=/path/to/experiment/pyopenms-validation-venv/bin/python
runtime_workspace=/path/to/experiment
runtime_run=/path/to/new-runtime-run
mkdir -p "$runtime_run"

"$runtime_python" tools/record_native_install.py \
  --sdk "$runtime_workspace/product-sdk" --build-root "$runtime_workspace" \
  --evidence "$runtime_run/install-evidence" --output "$runtime_run/install-receipt.json"

"$runtime_python" tools/qualify_macos_runtime.py \
  --sdk "$runtime_workspace/product-sdk" --receipt "$runtime_run/install-receipt.json" \
  --stage "$runtime_run/staging" --moved "$runtime_run/runtime moved" \
  --evidence "$runtime_run/evidence" \
  --abseil-fallback /opt/homebrew/Cellar/abseil/20260107.1/lib

"$runtime_python" -m unittest discover -s tests -p test_runtime_receipt.py -v
```

The old Abseil fallback is set inside the packaging process only, to resolve this host's re2 dependency. Runtime tests receive no loader fallback. `--verify-only` can resume validation of a repaired runtime before archive release, using its unchanged native hashes and existing evidence; an existing archive causes a refusal instead of being overwritten.

This archive does not include FLASHTnT, GUI products, external search-engine executables, Developer ID signing or notarization. Windows, Linux and container execution are untested here. These native checks do not establish complete FLASHApp compatibility; its separate wheel, workflow, live-queue and external-tool gates remain separate acceptance work.
