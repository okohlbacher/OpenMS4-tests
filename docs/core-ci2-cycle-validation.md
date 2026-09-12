# Core 4.0.0-ci.2 pin cycle — 2026-09-12

The package graph was advanced to Core `bc9cc12514c768385ce121d6ca4bb710fe1983c4`
(`core-v4.0.0-ci.2`) as one qualified cycle: every consumer's `dependencies.lock.json`
and generated workflows were rewritten from the parent lock in dependency order, each
package was built and tested on five platforms, and only then tagged. Fifteen releases
were published; `test-data` and FLASHApp carry no release by design.

| Package | Pinned revision | Release |
| --- | --- | --- |
| core | `bc9cc12514c7` | core-v4.0.0-ci.2 |
| cli | `d5213ff3551a` | cli-v1.0.0-ci.2 |
| test-data | `a14ecf5d5f5d` | – (fixtures) |
| topp | `c6e98a7782cc` | topp-v1.0.0-ci.4 |
| openswath | `851e8f0e0ec4` | openswath-v1.0.0-ci.2 |
| flash | `b2c6771de774` | flash-v1.0.0-ci.2 |
| prose | `828d72595677` | prose-v1.0.0-ci.2 |
| nuxl | `dc6f61c5ed8a` | nuxl-v1.0.0-ci.2 |
| nase | `a9b317b889cc` | nase-v1.0.0-ci.2 |
| comet | `c3c4d1b99a15` | comet-v1.0.0-ci.2 |
| mascot | `fcbcc61346c3` | mascot-v1.0.0-ci.2 |
| database-suitability | `c46998ff1001` | database-suitability-v1.0.0-ci.2 |
| proteomics-lfq | `cf12fe9163e3` | proteomics-lfq-v1.0.0-ci.2 |
| parquet-diff | `682f7086ebe9` | parquet-diff-v1.0.0-ci.2 |
| desktop | `717d0c63da63` | desktop-v1.0.0-ci.2 |
| pyopenms | `52f8726850cc` | pyopenms-v4.0.0.dev0-ci.2 |
| flashapp | `38aa6a6a7692` | – (frozen dependencies) |

## What changed in the packages

Desktop renders its 3D view through Qt 6.7's `QRhiWidget` instead of OpenGL, so the
same code runs on Metal, Direct3D, Vulkan and OpenGL; the Qt WebEngine sequence viewer,
the only WebEngine user and disabled in every published build, was removed. The GUI SDK
now needs Core, Gui, Widgets, Svg and GuiPrivate (plus PrintSupport on macOS).

`OpenMSInfo` reports the 40-character Core SDK and TOPP package revisions the binary was
built from, with a dirty marker, instead of the `exported` that a source archive leaves in
the Git fields.

pyOpenMS releases now carry a repaired, redistributable wheel per platform beside the
installed module tree. The driver builds it through the PEP 517 backend against the same
installed chain, repairs it with auditwheel, delocate or delvewheel, and runs the whole
test suite against it from a fresh virtual environment with no build prefix on any library
path and no `OPENMS_DATA_PATH`, so the bundled runtime data has to work. The wheels are
built for the CI interpreter (CPython 3.12); other interpreters need their own build.

Core is delivered as a Homebrew formula with bottles for arm64 Sequoia, Intel Sequoia and
x86_64 Linux, published as assets of the ci.2 release; the bottle workflow installs the
formula the way a user does and checks that the bottle was poured. Core no longer installs
its vendored `sqlite3.h` and `libsqlite3.a` into the keg — they are statically linked into
libOpenMS, nothing exported refers to them, and on Linux they collided with Homebrew's
sqlite, which is not keg-only there. All eleven console casks were regenerated from this
cycle's payloads and their install checks pass.

## Build infrastructure

GitHub's hosted-runner queue, not compute, paced earlier cycles. Package CI now routes the
`linux-x64` row of push and dispatch events to self-hosted runners on the IBMI node dax and
the `macos-arm64` row to the Mac Studio; pull requests stay on hosted runners, because the
repositories are public and a fork must never execute on either machine. macOS x64,
linux-arm64 and Windows remain hosted. One runner per repository, each with its own `HOME`
and a job-start hook that removes the previous job's micromamba, because setup-micromamba
refuses to overwrite its own binary and root. `tools/hpc/` holds the install and
registration scripts.

## Validation

The whole native graph was rebuilt from the pinned sources against the published
`OpenMS4-core-linux-x64-Release-bc9cc12514c7.tar.gz` archive on dax (384 logical CPUs,
2.2 TiB memory, load 13 at start; GCC 14.4 from the recorded conda environment, Release,
240 compilation jobs, six concurrent packages). Every registered test passed:

| Component | Tests | Failures |
| --- | ---: | ---: |
| CLI | 9 | 0 |
| TOPP | 242 | 0 |
| OpenSWATH | 38 | 0 |
| FLASH | 9 | 0 |
| ProSE | 3 | 0 |
| NuXL | 14 | 0 |
| NASE | 2 | 0 |
| Comet | 3 | 0 |
| Mascot | 4 | 0 |
| DatabaseSuitability | 4 | 0 |
| ProteomicsLFQ | 3 | 0 |
| ParquetDiff | 3 | 0 |
| Desktop | 11 | 0 |
| pyOpenMS | 4 groups | 0 |
| Installed console suite | 2041 | 0 (5 retained skips) |

150 console tools were installed and registered without a duplicate manifest entry. The
summed step time was 396 seconds; the longest single steps were the pyOpenMS build (62 s),
the FLASH algorithm test (59 s) and the desktop build (43 s). The five retained skips are
the inherited adapter tests whose external engines are not provisioned.

## Defects this cycle's benchmark exposed

A benchmark of FeatureFinderCentroided, FLASHDeconv, ProSE and NucleicAcidSearchEngine on
public PRIDE data (PXD000001, PXD063573, PXD016308) and an Orbitrap Astral excerpt found
four defects. All four are fixed on the branch tips and will be pinned by the next cycle;
none of them is in the released revisions above.

- `FragmentIndex::build` sorted its fragments with `boost::sort::block_indirect_sort`,
  whose default thread count is `std::thread::hardware_concurrency()` and which consults
  neither OpenMP nor the process CPU affinity. On a 384-core node `ProSE -threads 1` spawned
  384 sort threads and used 2092 CPU-seconds in 26 seconds of wall time; at `-threads 32` it
  collapsed to 188 seconds wall and 54797 CPU-seconds. With the sort given the same budget as
  the surrounding OpenMP regions, the same search takes 43 CPU-seconds at one thread and
  108 at 32, and 6.2 seconds wall (core `50e07ec`).
- `FeatureFinderAlgorithmPicked::abort_()` mutated the shared abort counters from inside the
  OpenMP loop over seeds without synchronisation, while every other shared write in that loop
  was protected. Most iterations end there — 41692 of 44517 seeds on the Astral input — so
  concurrent `std::map` insertion, which is undefined behaviour, was the normal case for any
  run with more than one thread (core `f743ccd`).
- The mzTab writers emitted one search-engine-score cell per score a row happened to carry,
  while the header declares one column per score type in the metadata. After a target-decoy
  FDR run the hits FalseDiscoveryRate did not score — 535 of 1240 observation matches in the
  PXD016308 search — were one column short, and NucleicAcidSearchEngine aborted with "Header
  and content differs in columns" (core `f743ccd`).
- Two user errors were reported as internal ones: profile spectra handed to
  FeatureFinderCentroided (`IllegalArgument`, now `ILLEGAL_PARAMETERS` with a message naming
  PeakPickerHiRes) and an unknown RNA modification code in a FASTA (`ElementNotFound`, now a
  parse error naming the code and `Custom_RNA_modifications.tsv`) — cli `1dafcb2`, topp
  `b485123`, core `f743ccd`.

FeatureFinderCentroided also warns now when the mass trace settings discard nearly every
seed: on the Astral excerpt the default `mass_trace:min_spectra` of 10 yields 235 features
where 5 yields 3917, because the defaults are tuned for slower instruments.

## Not claimed

Wheels are built for CPython 3.12 only. FLASHApp was not rebuilt; its lock follows the graph
but its container and web-app dependencies are frozen. The Homebrew bottles cover arm64 and
Intel Sequoia and x86_64 Linux; other platform tags fall back to a source build. Benchmark
timings are wall-clock measurements on a shared node and are not performance claims about
the instruments' data.

The [machine-readable report](core-ci2-cycle-validation.json) carries the pins, releases,
test counts and timings.
