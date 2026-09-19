# Independent OpenMS 4 decomposition review

Review the actual OpenMS code and the proposed decomposition. This is a READ-ONLY REVIEW. Do not edit any project files, install dependencies, configure or build OpenMS, run Git mutations, push, create worktrees or delegate to background agents. Do not read credentials or unrelated user files. Return your complete review in the final response, with evidence from files and line numbers. The calling process will save your output.

Source checkout: /Users/kohlbach/Claude/OpenMS/OpenMS4-Exploration/OpenMS4-tests
Pinned upstream source commit: ca32296038839459d8c9b075b759e285913d6294 (develop, declares OpenMS 3.6.0).
Proposal: /Users/kohlbach/Claude/OpenMS/OpenMS4-Exploration/OpenMS4-package-architecture.md
Editable diagram: /Users/kohlbach/Claude/OpenMS/OpenMS4-Exploration/OpenMS4-package-architecture.mmd

The user wants an independently buildable and testable scientific core, executables compiled using a pinned installed core, separate TOPP, FLASH, OpenSWATH, viewers/workflows, webapps, and a separately packaged pyOpenMS. They now ask for a synthesized refactoring plan and implementation as subrepositories in their private okohlbacher/OpenMS4-tests experiment.

Inspect the build code yourself, including root CMake, cmake/OpenMSConfig.cmake.in, src/openms and openswathalgo, src/topp, src/openms_gui, src/pyOpenMS and test/packaging infrastructure. Prior audit notes may be consulted but independently check important claims.

Deliver:
1. A verdict on the proposed boundaries, with any concrete corrections and missed coupling (cite paths/lines).
2. A dependency graph and ownership decisions that permit independent build/test/release, especially installed SDK, CLI/core cycles, public headers, GUI implementation, Python fixtures, runtime data and external tools.
3. A practical, ordered implementation plan for source-complete subrepos, including which boundaries can be extracted now and which require compatibility bridges. Avoid empty scaffolding presented as a completed refactor.
4. A recommended subrepository topology and exact initial contents per repo. Evaluate core SDK consumption, source duplication and reproducible pins.
5. Validation that can be run without compiling the large project, plus later compile/integration acceptance tests. Explicitly distinguish source/configuration verification from proven binary correctness.
6. The five largest risks or objections to the current proposal, and how to address them.

Prioritize concrete evidence and implementation decisions over generic microservices advice. Do not claim tests or builds were run. A review may recommend a different package boundary when supported by evidence.
