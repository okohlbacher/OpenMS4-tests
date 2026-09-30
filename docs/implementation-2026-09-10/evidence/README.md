# Native evidence archive

These are command records and outputs from the local macOS validation workspace.
Absolute paths record what actually ran; they are not proposed portable install
paths. Empty sanitizer diagnostic files are intentionally retained.

The one-off `make_identity_fixture.py` script originally lived in
`<workspace>/implementation-build-evidence/`. The `versioninfo/` files originally
lived in `<workspace>/core-instrumented-contracts/`. To rerun those probes, copy
them to those respective locations beside the matching `core-build` and installed
SDK acceptance directories. They reuse the recorded Core compile/link inputs,
write independent output artifacts, and do not modify the production SDK.
The Python wheel build/repair/qualification scripts likewise originally lived
in `<workspace>/implementation-build-evidence/` and use the documented local
validation environments. They are retained as exact-machine recipes.

The reusable macOS product qualification entry point lives in the parent
repository's `tools/qualify_macos_runtime.py`; use its explicit path arguments
instead of transplanting an evidence log into a build recipe.

Failed initial experiments are retained where they explain a corrected test or
qualification boundary. The implementation report identifies final passes and
does not count unrelated failures as successful negative tests.
