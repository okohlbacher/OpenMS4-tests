# Implementation audit, 10 September 2026

Read the [verified findings](review.md), [six-phase refactoring plan](refactoring-plan.md), and [Ponytail simplification audit](ponytail-audit.md). The review retains the nine package boundaries and separates inherited defects, extraction defects, reproduced behavior and pending runtime evidence.

The source snapshot is recorded in [reviewed-revisions.json](reviewed-revisions.json). The three command-line reports are verbatim; their separate verification documents correct unsupported claims. Implementation source and package pins were unchanged during this audit. This directory publishes the findings and proposed work, not completed fixes.

| CLI input | Source verification | Invocation |
| --- | --- | --- |
| [Claude Fable 5.1](claude-review.md) | [17 findings](claude-verification.md) | [metadata](claude-metadata.json) |
| [Kimi, configured k3](kimi-review.md) | [18 findings](kimi-triage.md) | [metadata](kimi-invocation.json) |
| [Vibe](vibe-review.md) | [14 findings](vibe-triage.md) | [metadata](vibe-invocation.json) |

Vibe's configured Mistral Large 4 was unavailable. A per-invocation fallback used the configured `mistral-medium-3.5` alias, requesting `mistral-vibe-cli-latest`. Kimi/Vibe did not provide a more specific server-resolved model build. The common request and Vibe's wrapper are retained. The Ponytail installation is pinned and recorded in [its installation manifest](ponytail-installation.json).

The two reproduction scripts intentionally assert the presence of audited defects; they are not regression tests endorsing those defects. Their invocation and limits are in the [review](review.md#evidence-and-reproduction). Configure excerpts, controlled-probe records, inventories and the inconclusive memory-check attempt accompany the report. No native OpenMS compilation occurred during the audit; one existing Arrow test passed during the unsuccessful attempt to collect a valid leak report.

## Raw-stream evidence

Raw command-line streams and launcher files remain in the local exploration workspace at `/Users/kohlbach/Claude/OpenMS/OpenMS4-Exploration/reviews/2026-09-10-implementation-adversarial`. Their hashes and sizes are recorded in [raw-evidence.json](raw-evidence.json) and each CLI's metadata. Generated CMake trees are also local. They are not needed to read the verbatim final reports or the verified synthesis.

The publication adapts only navigation links in the separate Vibe triage and Codex Ponytail follow-up; no final CLI report text was edited. Source citations refer to the frozen package revisions, not later implementations. [Artifact hashes](artifact-index.json) cover the curated publication files, excluding the index itself.
