# Desktop configure-only validation

*Part of the [OpenMS 4 package split](../README.md). [State of the project](project-state.md) · [Package architecture](package-architecture.svg) · [Build instructions](build-split-packages.md)*

The final desktop package CMake files were copied into a temporary directory and configured with the real Homebrew Qt 6.11.1 installation. OpenMS core/CLI SDKs were deliberately fake imported targets with revision `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`. The installed GUI export was produced by the GUI CMake configuration, with an empty placeholder library file; it is not a built binary.

## Passed configuration/generation cases

- Aggregate desktop root, with ordinary GUI, interactive GUI, ImageCreator and pipeline tests enabled: twelve tests registered.
- Standalone GUI with WebEngine disabled.
- Standalone viewers consuming the generated installed GUI SDK export.
- Standalone workflows consuming the generated installed GUI SDK export.
- Standalone viewers with Ninja Multi-Config.
- Standalone GUI with real Qt WebEngineWidgets enabled.

The standalone viewer/workflow source directory contains no GUI source directory. Generated package exports, the GUI export header, autogen metadata (141 headers and 141 C++ sources), native app-bundle paths and all five TSV records were inspected. Generated UIC headers are absent from installed GUI interfaces.

## Negative checks

- A GUI SDK source revision different from the desktop source revision is rejected.
- A core SDK source revision different from the dependency lock is rejected.

## Limits

No OpenMS source was compiled, linked or executed. No native library was installed. CTest was used only to list registered tests. Compiler feature metadata was preseeded for the configure-only harness; this does not validate toolchain compatibility. The first harness setup inadvertently allowed Qt's small HAVE_STDATOMIC configure probe, then failed because the fake compiler metadata omitted cxx_decltype. The probe was subsequently preseeded and complete feature metadata supplied; all six successful runs recorded zero try_compile events. The initial failure was in the deliberately incomplete mock toolchain, not the desktop package.

These checks validate CMake graph generation and real Qt package discovery. They do not establish C++ correctness, ABI compatibility, Qt plugin deployment, GUI behavior, pipeline results, relocation or installer readiness. No desktop code change was required by these checks. All modifications to locks and mocks were confined to the temporary copy.
