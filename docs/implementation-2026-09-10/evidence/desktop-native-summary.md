# Desktop native acceptance

Clean desktop commit `b39230036c53f74b537c3683520f3ba2ef1ba963` consumes Core
`4fdec46b205459b92e7d3b9e56df5d8e912d5c85`, CLI
`51db6bbbdeba53abc57d23c664de37f9c285372e`, and TestData
`c3e52c917bc2a04e27720f5c7d8189c0f4f522da`.

The macOS arm64 Debug profile disabled WebEngine, enabled tests, and required
clean package/SDK source metadata. GUI built 173/173 steps, passed 5/5 class tests,
and installed its SDK. Independent viewer and workflow entry points then compiled
against that installed GUI SDK (9 and 6 steps). Both ImageCreator cases passed
exact BMP comparisons (4/4 CTest cases). The installed ExecutePipeline fixture
returned zero and wrote its FileInfo TSV and merged mzML outputs.

A clone of the complete installed prefix passed 10 macOS-sandbox checks: a control
proved source reads denied; all five installed programs displayed help; actual
QApplicationTOPP startup loaded its embedded stylesheet with an invalid Core-data
override; both image outputs matched exactly; and the pipeline completed. The
profile denied the original SDK, source and native build paths. Loader traces
confirmed all OpenMS/Core/CLI/GUI/OpenSwath libraries came from the relocated copy.
No active Core/Python directory was renamed. The initial harness used `-help` for
two tools; it was corrected to their documented `--help`, with the initial failed
record retained separately. This was a harness option error, not an artifact fix.

The pipeline acceptance used the installed executable. Running a build-tree tool
after installing the same product creates two distinct registries, which the agreed
duplicate-rejection policy rejects; build-tree ImageCreator tests ran before install.

External Qt/native runtimes remain prerequisites. The host's existing re2 binary
needed its installed older Abseil runtime via the recorded fallback loader path;
that path contains no OpenMS SDK. These are developer artifacts, not a self-contained
or signed/notarized distribution. WebEngine-enabled, interactive, Release,
Linux and Windows desktop profiles remain unvalidated.

`desktop-native-results.json` records the profile and binary hashes.
`desktop-relocation-results.json`, `desktop-isolation.sb`, and
`desktop-relocation.py` preserve the restricted commands and runtime evidence.
The `desktop-*-{configure,build,install,ctest}.log` files preserve native build/test
output. Relocation stdout/stderr files include the loaded-library traces.
