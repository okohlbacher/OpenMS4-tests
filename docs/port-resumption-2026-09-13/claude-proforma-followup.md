# Claude Fable 5.1 review of Core df774c1

Read-only CLI review; no runtime validation by the reviewer. Findings require the maintainer synthesis.

Review complete. No new actionable correctness regression found in the ProForma.cpp diff between bc9cc12 and df774c1. All ten inherited claims hold against the code paths I traced.

**Verified paths (by reading, not building):**

- CPP-015: `calculateChainMass_` (ProForma.cpp:1945-1965) lets only a chemistry-carrying endpoint claim the label. A leading `[#XL1]` yields `{true, 0.0}` from `getModificationMass_` and does not insert into the map, so `K[#XL1]PEPK[-2.01565#XL1]` now counts the linker once. Existing tests at 2638, 2658, 2859, 2926 keep the chemistry-first shape and are unaffected.
- CPP-047 and CPP-031: `findCrossLink` (2065-2105), the emission loop (2373-2382) and the cursor loop (2423-2428) all count one residue per non-empty ambiguous region and `elements.size()` per range. `(?)` is reachable from `parseAmbiguousRegion_` (1123-1142), which has no empty check, and no longer misplaces a following modification.
- CPP-038: `removeLinker` erases by the `section`/`modification` indices taken from the same resolved copy (2955-2966). The XLMS generator adds `cross_linker_mass` to both chain masses itself (TheoreticalSpectrumGeneratorXLMS.cpp:904-905, 924-927, 971-975), so stripping the bracket is the right contract. `CrossLinkEndpoint_` holds no pointers, and `alpha_seq`/`beta_seq` outlive the generator calls.
- CPP-037: `EmpiricalFormula::operator+=` sums `charge_` (EmpiricalFormula.cpp:323) and `toString()` omits it (258-267), so the `getCharge() == 0` gate at ProForma.cpp:1741 is necessary and sufficient. Cancelling charges still take the formula route.
- CPP-020: `getMonoWeight`, `tryGetMonoWeight` and the ion overloads validate and calculate the same resolved copy (2715-2725, 2785-2795, 2673-2687).
- CPP-008, CPP-009, CPP-029, CPP-030: resolution, validation and accumulation are consistent for range-element and candidate modifications; the terminal loops and the attachment throw use the same `carriesChemistry_`/`crossLinkLabel_` predicates as the residue loop. QPXFile.cpp:2007-2019 only warns and uses BEST_EFFORT, so the new terminal CROSS_LINK issue cannot break imports.

**Pre-existing deferrals worth recording (not regressions of this diff):**

1. **Empty ambiguous region passes mass validation.** `collectMassCalculationIssues_` (2606-2643) reports nothing for zero candidates, and `calculateChainMass_` (1977) adds nothing. Input `PEP(?)TIDE`: expected an issue or nullopt; actual mass equals PEPTIDE. HEAD behaved the same.
2. **Two label-only endpoints give a silent 0 Da linker.** `collectCrossLinkIssues_` (2125) only fires when an endpoint defines chemistry, and `linker_mass` falls back to `beta.mass` (2972). Input `PEPK[#XL1]IDE//ANOK[#XL1]THER`: `canGenerateSpectrum` is true and the precursor omits any linker. Same at HEAD.
3. **BEST_EFFORT drops modifications inside ranges and ambiguous regions** (2373-2382 emit only letters) while `getMonoWeight` now counts them (1981, 1991). CPP-008 widens this gap but it is covered by the reported MODIFIED_RANGE and AMBIGUOUS_REGION issues. It is silent only in the two-chain `generateSpectrum`, which never runs `collectConversionIssues_` on the chains (2165-2169), so `(M[UNIMOD:35]A)[+1]K[+138.068#XL1]//...` loses both masses from the fragment spectrum without any issue. Same at HEAD for the range-level bracket.
4. **Endpoint mass source differs between the two consumers.** `findCrossLink` prefers the MassDelta text (2084-2088) while `calculateChainMass_` prefers the resolved database mass (1908). For `+138.068` resolving to Xlink:DSS the spectrum uses 138.068 and the precursor mass API uses 138.06808. Sub-millidalton, pre-existing.

**Test coverage:** none of the ten fixes has a regression test in ProFormaParser_test.cpp at df774c1. Grep found no label-first two-chain input, no `(?)`, no modification inside a range, no charged formula sum, and no assertion on cross-link precursor m/z. The fixture files at 2250-2261 are parse-only, so the label-first line in the positive fixture (`SEK[XLMOD:02001#XL1]UENCE//EMEVTK[#XL1]SESPEK`) exercises nothing beyond parsing.

**Limits:** read-only review without build or test execution. No git access in this session, so I relied on the supplied diff for the assertion that AASequence.cpp and EmpiricalFormula.cpp are unchanged. I did not check whether the JSON round-trip preserves modifications on range or region elements; that code is outside the diff.
