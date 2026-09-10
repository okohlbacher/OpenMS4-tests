# Validation recorded on 10 September 2026

The stripped Core SDK and scientific tests built on **macOS arm64, Debug**, and the full suite passed **709/709 CTests in 311.29 seconds**. The final committed SDK also passed 26 consumer runtime checks across library-only/TestSupport and original/relocated installations, with Core source/build paths hidden. See [Core native validation](core-native-validation.md) for the observed dependency issues, exact profile and continuing acceptance results.

Source/configuration validation passed **62 checks**: the original 53 plus nine regressions for the exact invalid-data-override assertion. These checks are separate from native CTest results.

| Check group | Result |
| --- | --- |
| Suite source ownership, artifact verification and consumer CMake configuration | 19 passed |
| Parent/submodule and consumer dependency pin consistency | 2 passed |
| Core SDK contracts and compiler-free data metadata | 10 passed |
| Invalid-data-override subprocess assertion | 9 passed |
| Test-data installation, relocation and suite registration | 7 passed |
| Desktop source/resource boundaries | 9 passed |
| Standalone Python source and fixture contracts | 6 passed |

The suite confirms that all 151 baseline CLI targets have exactly one owner: 131 TOPP, 19 OpenSWATH and FLASHDeconv. FeatureLinkerWNet remains conditional. Textually included tool helper files resolve after extraction. Core has no dependency on moved CLI headers, and core fixtures no longer escape into the TOPP tree. All 2,297 vendored extern/thirdparty files checked against the baseline remain byte-identical.

Actual CLI, TOPP, FLASH and OpenSWATH CMake projects configured against isolated mock installed SDKs. Wrong or shortened source pins are rejected; build and install manifests retain correct paths with a custom install binary directory. Artifact checks reject changed binaries, duplicate or unlisted files, unresolved hashes, archive traversal and escaping links.

The Python package configured with tests disabled and enabled against fake installed SDK/nanobind metadata; all four original CTest groups registered, and an incorrect core revision failed. Binding implementations remain unchanged. The SDK fixture package installed and relocated without a compiler; its harness registered 1,940 tests against 119 manifest-listed mock executables, with no executable run. This count describes that configuration, not a claimed numerical pass count.

Desktop additionally passed six configuration/generation scenarios with **real Qt 6.11.1** and mock Core/CLI SDKs, including standalone viewers/workflows using an installed GUI export, a source tree without GUI sources, multi-configuration generation and WebEngine. Twelve desktop tests registered; wrong core/GUI pins failed. See [the detailed report](desktop-configuration-validation.md).

The Core runtime pass includes the slow realistic PipEcho test (55.73 seconds) and FLASH algorithm test (205.26 seconds); it does not build the FLASH executable package. The portable profile disables optional native readers/models, and unavailable external Percolator subprocess sections remain outside the claim. The invalid-data-override assertion requires exit code 1 and the exact OpenMS diagnostic, rejecting unrelated crashes or loader failures.

CLI/product native builds and numerical suites, Python extension imports/wheel repair, GUI execution, platform packaging and ABI/dependency identity acceptance remain pending. Core consumers passed with original source/build paths unavailable; both SDK configurations passed relocation and rejected incorrect source pins. Configure-time mock/Qt probes above do not satisfy those gates. See [the ordered plan](refactoring-plan.md).

Reproduce the source/configuration checks with `python3 tools/validate_source.py` (Python 3.12+). GitHub Actions remain disabled. Binary artifact digests must be generated from actual built products; the app's example artifact lock is intentionally unusable until supplied with verified products.
