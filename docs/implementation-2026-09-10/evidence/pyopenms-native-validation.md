# Native pyOpenMS wheel validation, 2026-09-10

The standalone Python package built all 15 native extension modules and generated
its stubs against the installed Core SDK. The final repaired wheel imported while
the original source/build trees, installed development SDKs and Homebrew were
inaccessible. The complete suite collected 5,854 tests and exited successfully:
5,745 passed, 92 skipped, 10 expected failures and seven unexpected passes of
existing non-strict expected-failure markers.

## Artifact and source identity

- Python: `14d950a460636b9a8fa255b7ac657926fec403de`, clean;
  package version `4.0.0.dev0`.
- Core: `4fdec46b205459b92e7d3b9e56df5d8e912d5c85`, clean;
  version `4.0.0`.
- TOPP fixtures: `c3e52c917bc2a04e27720f5c7d8189c0f4f522da`, clean;
  version `1.0.0`.
- Wheel: `pyopenms-wheel-final-repaired/pyopenms-4.0.0.dev0-cp312-cp312-macosx_26_0_arm64.whl`.
- SHA-256: `9a2150e096b7acc06562e63ee2081cdbee138b0efedcc09d756e5f8b94bdef9d`.
- Size: 76,792,572 bytes; 15 Python extensions and 130 bundled dynamic libraries.

`pyopenms-final-wheel-artifact.json` records the full embedded Core build identity,
artifact size, inventory and digest. This validation record was produced before repository publication.

## Build profile and reproduction

AppleClang 21.0.0.21000101, arm64, Debug, C++23 and libc++; shared Core and Boost
1.90.0; Arrow/Parquet 25.0.0; Eigen 5.0.1; curl 8.21.0; OpenMP 5.1. OpenSWATH and
OpenMP are enabled. HDF5, ONNX, WNetAlign, OpenTIMS, Thermo RAW and TDL are disabled.

Python 3.12.9 runs in `pyopenms-validation-venv`; nanobind 2.10.0,
py-build-cmake 0.5.1 and delocate 0.13.0 are the build tools. Runtime/test packages
include PyArrow 23.0.1, NumPy 2.5.3, pandas 3.0.5, matplotlib 3.11.1, pytest 9.1.1,
pytest-cov 7.1.0 and docutils 0.23. Build concurrency was limited to three jobs.

From the exploration workspace, after provisioning the pinned SDK:

```sh
python3 implementation-build-evidence/run_pyopenms_wheel_build.py
pyopenms-validation-venv/bin/python implementation-build-evidence/repair_pyopenms_wheel.py
uv pip install --offline --reinstall --no-deps \
  --cache-dir pyopenms-package-cache --python pyopenms-wheel-venv/bin/python \
  pyopenms-wheel-final-repaired/pyopenms-4.0.0.dev0-cp312-cp312-macosx_26_0_arm64.whl
python3 implementation-build-evidence/qualify_pyopenms_wheel.py
```

The build script records all CMake overrides, including strict clean-source
checking, an external build directory, Debug and the Homebrew OpenMP/curl search
prefixes. The final build reused compiled modules whose sources were unchanged;
configuration regenerated the final clean Python source identity.

Initial configuration missed Homebrew OpenMP until the Core build's separate
libomp prefix was supplied. The first full compilation found an unconditional
`BrukerTimsFile.h` include, although the SDK omits that optional header when
OpenTIMS is disabled. The include now has the same feature guard as its bindings;
a native test checks both Bruker and Thermo binding availability against Core's
reported features.

This host's re2 requires the still-installed Abseil 2601 ABI while its active
Homebrew alias points to 2605. Ninja's shell discarded an inherited loader
fallback, so build-time stub generation used the task-local
`pyopenms-build-python` launcher. It sets the old ABI fallback immediately before
starting Python. The repair script uses that same existing library directory only
to locate and bundle dependencies. It changes no Homebrew installation.

The raw backend selected a macOS 11.0 wheel tag. Delocate inspected the native
dependencies and raised it to **macOS 26.0**, which is the qualified wheel's minimum
target. This is not a macOS 11.0 compatibility result.

## Completed checks

- Source/configuration checks: six standalone tests, three runtime-identity
  checks, one wheel-content check, and six CMake configure scenarios passed.
- Fixture package: all 14 source/controlled-child tests passed, including exact
  diagnostic/status checking and flat custom executable-directory registration.
- Production Arrow helper: four normal native cases and the same four cases
  with AddressSanitizer plus UndefinedBehaviorSanitizer passed. They force multiple
  C-stream batches, preserve an empty schema, verify producer lifetime and repeated
  exception cleanup, and reject malformed capsules. The unchanged probe moved to
  `tools/native_arrow` so wheel discovery never expects its private extension.
- Actual reused staging: deliberately inserted `test-data` and `examples` markers
  were removed on a repeated backend build. Both raw and repaired ZIP checks reject
  these resources and verify the exact clean Python/Core source identities.
- Initial raw wheel: all 32 selected native provenance/Arrow IO cases passed,
  including catchable invalid-data import and a successful corrected retry.
- Actual wrong-Core binary: a compatible full Core library relinked with a
  different embedded source revision was rejected with the specific
  `source_revision` identity diagnostic, before scientific domain modules loaded.
  The test rejects loader crashes or unrelated exceptions as failures. This was
  repeated successfully against the final clean source identity using
  `validate_pyopenms_wrong_core.py` and the parent's `make_identity_fixture.py`.
- Repaired import: explicit open attempts proved source/SDK/Homebrew read denials
  were active. No `DYLD_*` variables or initial `OPENMS_DATA_PATH` were present.
  Import succeeded and Core resolved the data bundled in the installed wheel.

- Source distribution: the final clean source archive was inspected, extracted,
  and configured successfully against the installed SDK. Its SHA-256 is
  `ca5fd4706e8b08d1268a80d9c3ffb9fa738bb61bc47081a71a8aea31d5bde9dc`;
  size 5,408,382 bytes. This is configure/inventory validation, not a second native
  compilation from the archive. `pyopenms-sdist-artifact.json` records this limit.

## Complete repaired-wheel suite

Exit status **0**: **5,745 passed, 92 skipped, 10 xfailed, seven xpassed**,
757 warnings, in **65.57 seconds**. `pyopenms-final-wheel-tests.log` and
`pyopenms-final-wheel-tests.xml` preserve the output and JUnit result.
The existing skip/expected-failure markers were retained. Skips include disabled
optional readers, unavailable private test files and unsupported copy constructors;
expected failures cover previously unbound APIs and type-caster limitations. The
seven non-strict unexpected passes identify older expected-failure markers whose
APIs now work. No new skip or expected-failure marker was added for this work.
The suite collected 5,854 tests without excluding scientific, feature, integration
or documentation tests. Tests and installed Core/TOPP fixtures were copied to the
neutral `pyopenms-wheel-tests` directory before read restrictions were applied.

The first full run (preserved in `pyopenms-initial-full-wheel-tests-f4404c4.log`
and its JUnit XML) found one inherited ambiguous fixture: bare `Oxidation` resolves
to an aspartate modification in this database, then the test tried to attach it
to methionine. A fresh process reproduced the mismatch without prior test
mutation. The existing Core Debug precondition correctly rejected it. The
fixture now requests the methionine-specific modification and additionally
checks the residue and full modification identities; all 63 borrowed-reference
cases passed before rebuilding the final wheel. No runtime assertion or test
marker was weakened.

`qualify_pyopenms_wheel.py` records the sandbox policy in
`pyopenms-wheel-sandbox.sb`. The surrounding agent sandbox cannot create another
Seatbelt sandbox; the qualification command therefore needed scoped execution
approval, after which the stricter child sandbox was active. The installed wheel
is in a different prefix from both the SDK and all build outputs.

## Limits

This is one native macOS arm64 / CPython 3.12 / Debug configuration, not validation
of every supported platform or optional reader. The isolated sanitizer run
instruments the shared production helper and nanobind, not the separately built
Arrow, PyArrow or Python binaries. Darwin leak detection was disabled, so no leak
coverage is claimed. Test counts describe executed cases, not line/branch coverage.
The final wheel is an experimental local artifact; Linux, Windows, other Python
versions, Release, optional readers and clean-runner source-distribution builds
still need their own qualification before a broad release.
