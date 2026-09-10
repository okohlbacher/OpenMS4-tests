# Real FLASHApp deconvolution integration

The final local non-UI workflow passed against the repaired Python wheel and
relocated native tools. `DeconvWorkflow.execution()` returned `True` on a fresh
workspace; all following scientific and negative checks passed. The execution
and check phase took 21.616 seconds; process exit status was 0.

- App source: `3e7f53137eab8ee8c8e15a018731f624d0ff1138`, clean.
- Python source: `14d950a460636b9a8fa255b7ac657926fec403de`, clean.
- Core source: `4fdec46b205459b92e7d3b9e56df5d8e912d5c85`, clean.
- Runtime: `product runtime verified/bin` and the final repaired wheel installed
  offline without dependency resolution into `/private/tmp/openms4-flashapp-test-env`.
  This is the app's hash-locked dependency environment, including PyArrow 19.0.1,
  pandas 2.2.3 and Python 3.12.13.

## Exercised production path

1. The real `ParameterManager` invokes `FLASHDeconv -write_ini`, loads the generated
   ParamXML with pyOpenMS, saves non-default parameters from Streamlit's bare-mode
   session state, and reloads them. The current algorithm key is `FD:report_FDR`.
2. The actual workflow constructs and executes FLASHDeconv arguments through
   `CommandExecutor.run_topp`, using the genuine installed sample mzML. It yields
   four masses across four MS1 scans and one mass feature.
3. The application stores real output files, parses annotated/deconvolved mzML,
   builds cached Parquet tables, and persists workflow parameters. Scan and mass
   tables each contain four rows. The undefined density curves retain empty,
   numeric `x`/`y` frames.
4. All 18 scientific feature columns match the separately generated pre-refactor
   reference using the existing FLASH package comparator and its tolerances.
5. Real `FuzzyDiff` runs through the same INI/executor path against a distinct copy
   of the actual output. This checks that command path; independent scientific
   equivalence is established by step 4, not by the copied-file comparison.
6. Real FLASHDeconv with a missing mzML raises `CalledProcessError` with exact exit
   status 1 and the intended `Error: File not found` diagnostic. It is not mistaken
   for success. The process-record directory is empty after both command paths.

## Failure found and repaired

The original tiny fixture has identical target Qscores. The application completed
scientific execution and cached tables but its density plot called SciPy's KDE on
zero-variance data, raising `LinAlgError` at 90% of postprocessing. The fix returns
an empty curve when a group has fewer than two distinct finite scores. It creates
no artificial jitter or density and preserves normal SciPy estimates. Target and
decoy groups are handled independently. The existing viewer maps `x` and `y`
from each curve and supports empty arrays, as used for absent decoys.

Ten new numerical cases cover empty, singleton, constant and nonfinite groups,
valid variable-score estimates, and independence of the two groups. These and
three existing heatmap tests passed: **13 passed**, one existing Polars warning,
in 1.46 seconds. The fresh real workflow passed after the fix. The initial failure
is preserved in `flashapp-real-deconv-density-failure.log`.

The focused checks require the installed native wheel and app dependencies;
`tools/validate_source.py` intentionally does not include them. Their exact
command from the exploration workspace is:

```sh
env -u OPENMS_DATA_PATH -u DYLD_LIBRARY_PATH -u DYLD_FALLBACK_LIBRARY_PATH \
  PYTHONDONTWRITEBYTECODE=1 /private/tmp/openms4-flashapp-test-env/bin/python \
  -m pytest OpenMS4-tests/packages/flashapp/tests/test_deconv_density.py \
  OpenMS4-tests/packages/flashapp/tests/test_render_compression.py -q
```

## Reproduction and limits

The scripts are preserved beside this report. They use exploration-workspace
paths; place both scripts in that workspace's `implementation-build-evidence`
directory before reproduction. From the exploration workspace:

```sh
python3 implementation-build-evidence/run_flashapp_deconv_probe.py
```

The runner removes inherited `DYLD_*`, `OPENMS_DATA_PATH` and `PYTHONPATH`, selects
the relocated tools, and limits tool/postprocessing concurrency. The app initializes
in Streamlit bare mode; no GUI server, browser, queue or external service is used.
`flashapp-real-deconv.log` and `flashapp-real-deconv-result.json` record the final
run; `flashapp-deconv-density-tests.log` records the focused tests.

This app gate uses the ordinary agent sandbox, not the stricter source/SDK/Homebrew
read-denial policy. The separate native-runtime and Python-wheel gates validate
those isolation properties. This does not qualify the full Docker image, GUI,
live RQ queue, FLASHTnT or TagWorkflow. First cold imports were slow; the successful
repeat initialized promptly with no development loader overrides. Their exact
cause was not diagnosed. No dependency installation or vendored source was changed.
