# Core follow-up review synthesis

The three requested command-line reviews completed. Claude ran as
`claude-fable-5-1` with read-only file tools; Kimi used its configured model and
read-only instructions; Vibe received the relevant source in its prompt with tools
disabled. None performed native tests. The supplied comparison was released Core
`bc9cc12` to candidate `df774c1`.

Kimi's late reads overlapped commits `b2079fb`, `86f01c4` and `63e332c`. Its final
claim that the filesystem still matched the original revision is inaccurate. The
accepted findings below were independently traced and tested against saved native
libraries. This is not a claim that all 185 inherited verdicts were verified.

| Finding | Disposition and evidence |
| --- | --- |
| Missing retained MSstats/mzData/mzXML/qcML/ProForma regressions | Added in `b2079fb`; corrected a ProForma fixture assumption in `86f01c4`. All pass in final Release and targeted Debug suites. |
| ProForma cross-linked spectra silently lose unsupported chain chemistry | Fixed in `86f01c4`: validate the chains after removing linker brackets and require lossless conversion. Reject a linker with no chemistry. Positive modified-chain generation still passes. |
| ProForma mass accepts an empty ambiguous region | Fixed in `86f01c4`; nonthrowing mass calculation now reports failure. BEST_EFFORT conversion retains its documented lossy behavior. |
| Rounded linker mass differs between mass and spectrum APIs | Fixed in `86f01c4` by sharing resolved modification mass semantics. Charge-two precursor tests check agreement within 1e-8 m/z. |
| mzML processing references are missing or collide between supplemental arrays | Fixed in `63e332c`. Collect spectrum/chromatogram float, integer and string histories once; use distinct IDs for header declarations and references. Six histories and their values survive a file round trip. |
| Streamed later array histories refer to unwritten header declarations | Fixed in `63e332c` for all three array types and both record types. Preserve first-record histories; omit later array histories with a warning without modifying callers. Both streaming orders pass schema validation. |
| String/number concatenation does not compile (Vibe; repeated by Kimi for another diagnostic) | Rejected. The source starts with `std::string`, and `StringUtils.h` defines the numeric overloads. The same implementation compiled on all five native platforms at `df774c1`. |
| MSExperiment-to-ExperimentalSettings cast is unsafe (Vibe) | Rejected. `MSExperiment final : public ExperimentalSettings`; this is an ordinary base-class conversion. |
| Negative sqMass buffer size deletes the output before validation (Vibe) | Rejected. `MzMLSqliteHandler` construction only initializes fields. `createTables()` follows validation; the retained negative-buffer test checks existing data remain readable. |

The final source `63e332c8dbc653769de3cf291c2fd54c86ddacd1` passes 702 Release tests,
22 targeted Debug tests, installed/relocated SDK acceptance and wrong-pin rejection
on GCC 14.4. ProForma's new assertions fail against the saved `df774c1` library;
the mzML assertions fail against `86f01c4`, including incorrect history values and
schema errors for undeclared references. See the sibling XML, log and JSON receipts.

The first attempted ProForma comparison used LD_LIBRARY_PATH, which DT_RPATH
overrode; that run is not regression evidence. The recorded failure uses explicit
LD_PRELOAD of the saved library, with library-selection output retained.

Remaining work, in dependency order:

1. Keep SQLite step-status handling, allocation-error diagnostics, real mzML
   checksums and empty indexed-file access on the unresolved ledger. Kimi's source
   review supports the existing Base64/decoder/sqMass fixes but supplies no new
   execution evidence for these deferrals.
2. Revisit streaming history semantics: a later spectrum without processing can
   inherit the first spectrum's history. This existing, documented fallback is
   still lossy and can misattribute provenance; full `MzMLFile::store` retains
   per-record and per-array declarations.
3. Finish the current seven-job Core CI matrix, then release its exact SDK. The
   preceding `df774c1` matrix is completely green but does not qualify later fixes.
4. Correct OpenSwathMzMLFileCacher's shifted SQL-consumer arguments and wrong writer
   in its sqMass-to-sqMass path; add numerical package tests. Add pyOpenMS explicit
   finalization and mass-validation coverage with the new Core pin.
5. Correct generated documentation's parent-branch links, commit the retained child
   documentation, and update consumer locks/workflows in dependency order. Rebuild
   the entire installed graph and rerun the numerical suite before release.

The parent still pins Core `bc9cc12`. Its mixed working checkout passes 64 of 65
contracts; the exact-source pin gate deliberately rejects the candidate checkout.
No new released graph or binary compatibility is claimed.
