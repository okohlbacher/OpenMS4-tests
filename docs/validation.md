# Validation recorded on 10 September 2026

The extraction has passed **53 source, configuration and packaging tests**. These checks do not establish native binary correctness.

| Check group | Result |
| --- | --- |
| Suite source ownership, artifact verification and consumer CMake configuration | 19 passed |
| Parent/submodule and consumer dependency pin consistency | 2 passed |
| Core SDK contracts and compiler-free data metadata | 10 passed |
| Test-data installation, relocation and suite registration | 7 passed |
| Desktop source/resource boundaries | 9 passed |
| Standalone Python source and fixture contracts | 6 passed |

The suite confirms that all 151 baseline CLI targets have exactly one owner: 131 TOPP, 19 OpenSWATH and FLASHDeconv. FeatureLinkerWNet remains conditional. Textually included tool helper files resolve after extraction. Core has no dependency on moved CLI headers, and core fixtures no longer escape into the TOPP tree. All 2,297 vendored extern/thirdparty files checked against the baseline remain byte-identical.

Actual CLI, TOPP, FLASH and OpenSWATH CMake projects configured against isolated mock installed SDKs. Wrong or shortened source pins are rejected; build and install manifests retain correct paths with a custom install binary directory. Artifact checks reject changed binaries, duplicate or unlisted files, unresolved hashes, archive traversal and escaping links.

The Python package configured with tests disabled and enabled against fake installed SDK/nanobind metadata; all four original CTest groups registered, and an incorrect core revision failed. Binding implementations remain unchanged. The SDK fixture package installed and relocated without a compiler; its harness registered 1,940 tests against 119 manifest-listed mock executables, with no executable run. This count describes that configuration, not a claimed numerical pass count.

Desktop additionally passed six configuration/generation scenarios with **real Qt 6.11.1** and mock Core/CLI SDKs, including standalone viewers/workflows using an installed GUI export, a source tree without GUI sources, multi-configuration generation and WebEngine. Twelve desktop tests registered; wrong core/GUI pins failed. See [the detailed report](desktop-configuration-validation.md).

No OpenMS/native product build, numerical test, extension import, wheel repair or GUI execution was performed. Configure-time compiler feature probes are distinct from an OpenMS build; the desktop harness documents one initial Qt atomic probe. Required binary acceptance remains: real core build/test/install/relocation; installed SDK consumers with original trees unavailable; CLI/product numerical tests; Python wheel/runtime checks; desktop tool discovery/pipelines; platform packaging and ABI/dependency identity checks. See [the ordered plan](refactoring-plan.md).

Reproduce the source/configuration checks with `python3 tools/validate_source.py` (Python 3.12+). GitHub Actions remain disabled. Binary artifact digests must be generated from actual built products; the app's example artifact lock is intentionally unusable until supplied with verified products.
