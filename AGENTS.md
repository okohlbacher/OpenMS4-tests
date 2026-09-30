# OpenMS 4 package experiment

- Never build OpenMS or native products unless explicitly asked. Source/configuration checks are allowed.
- Do not edit vendored code, contrib, or third-party dependencies.
- Do not commit secrets, credentials, or .env files.
- Run relevant checks for code changes; `python3 tools/validate_source.py` runs source/configuration tests without native compilation.
- Each package is an independent Git submodule; Core is public and the other packages are private. Commit a changed dependency first, then update consumer dependency locks, then the parent gitlink and packages.lock.json.
- Use branches prefixed `codex/`. Keep the original develop branch as the baseline.
- Keep core independent of CLI, GUI and Python. Consumers find installed, exactly pinned SDKs; no parent source/build-tree fallbacks.
- Preserve original C++ conventions, license notices, tests and source provenance. No using-directives in headers.
- Binary/ABI/runtime claims require actual build and acceptance results; source/configuration checks alone are insufficient.

The original contributor notes are preserved in legacy/AGENTS.md. The synthesized plan and limitations are in docs/refactoring-plan.md.
