# Ponytail audit of the package experiment

Applied the locally installed `ponytail` and `ponytail-audit` skills from [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail/tree/356918eba965ee1eac64bd3a7f0dd02108350de5), revision `356918eba965ee1eac64bd3a7f0dd02108350de5`. The six installed skills and their file hashes are recorded in `ponytail-installation.json`. This is the skill's complexity audit: proposed cuts, with correctness findings assessed separately. It does not apply edits.

Paths below are relative to the reviewed `OpenMS4-tests` checkout. The cuts preserve the nine requested package boundaries, scientific algorithms, vendored code, validation and error handling.

- `delete:` Disconnected legacy packaging/documentation modules and their KNIME helpers in Core, **1,593 lines**. Identical copies already exist under `legacy/cmake`; no active Core replacement. `packages/core/cmake/package*.cmake`, `knime/*.cmake`, `cwl_generation.cmake`, `knime_package_support.cmake`, `doc_macros.cmake`.
- `delete:` Two obsolete Python dependency-copy/repair implementations, **589 lines**. Use the already configured wheel repair workflow. `packages/pyopenms/pyopenms_copy_deps.cmake`, `mac_fix_dependencies.rb`.
- `delete:` Monorepo release-editing scripts targeting moved/deprecated paths, **104 lines**. Keep history and edit package version/changelog directly until a real release workflow is needed. `packages/core/tools/update_version_numbers.sh`, `update_ini_files_OpenMS_version.sh`.
- `shrink:` Seven identical 99-line dependency helpers have seven maintenance locations. Make one canonical source and verify generated copies, or move the helper into the installed SDK once both ordinary and compiler-free consumers can bootstrap it. Preserve full source-pin checks and standalone repositories. `packages/{cli,test-data,topp,openswath,flash,desktop,pyopenms}/cmake/OpenMS4Dependencies.cmake`.
- `shrink:` Two identical 75-line artifact verifiers. Keep FLASHApp's verifier as the implementation; make the parent invoke and test that same file. Preserve archive validation and hash checks. `tools/verify_artifacts.py`, `packages/flashapp/experimental/verify_artifacts.py`.
- `stdlib:` Manual thread list, semaphore, lock and shared results collection. Use `concurrent.futures.ThreadPoolExecutor`, collect every result and retain explicit exception handling and logging. `packages/flashapp/src/workflow/CommandExecutor.py:78`.
- `shrink:` Whole-tree wheel resource copy. Select the runtime directories already owned by the SDK, excluding TestSupport data and examples; do not introduce another resource discovery framework. `packages/pyopenms/CMakeLists.txt:239`.

The initial conservative scan found 1,307 Core lines; the independent follow-up included nine disconnected KNIME helpers, reaching 1,593. Searches of the active Core root, source, CMake helpers and package tooling found no callers of these removed suite entry points. File hashes and identical legacy copies were cross-checked against [claude-ponytail-inventory.json](claude-ponytail-inventory.json). Confirm the inventory in the eventual deletion change with a clean Core configuration. No vendored files are included.

The measured deletion candidates total 2,286 lines. The [additional Ponytail pass](claude-ponytail-audit.md) estimates approximately 3,031 lines including helper consolidation, one JSON tool inventory, a verifier adapter and native CMake unity support. Those estimates depend on preserving standalone bootstrap and opt-in behavior. Merely generating duplicate helper copies reduces maintenance, not physical line count; estimated simplifications are excluded from the numeric total below.

net: -2286 lines, -0 deps possible.
